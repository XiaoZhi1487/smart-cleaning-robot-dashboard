#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
# 避免 anaconda 中 MKL 与 torch 重复加载 OpenMP 导致 libiomp5md.dll 冲突崩溃
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
"""
工业相机 MJPEG 视频流 YOLO 目标检测服务
=======================================
读取原始相机视频流(http://192.168.0.2:8082/camera)
使用 tesch_yolo_server.pt 逐帧做目标检测并绘制标注框
输出带标注的 MJPEG 流,供前端 <img> 显示(替换原始无标注画面)

启动:
    python camera_yolo_server.py

带标注流地址:
    http://localhost:8083/camera
"""

import argparse
import io
import logging
import os
import time
import threading
import urllib.request

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, Response, jsonify

# paramiko 用于查询设备开机时长(/proc/uptime);缺失时 /uptime 返回不可用
try:
    import paramiko
except Exception:  # noqa: BLE001
    paramiko = None

# 抑制 Flask 每帧访问日志(GET /camera 200 会刷屏),仅保留 ERROR 级别
logging.getLogger("werkzeug").setLevel(logging.ERROR)

# ===== 配置 =====
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _parse_args():
    parser = argparse.ArgumentParser(description="工业相机 MJPEG 视频流 YOLO 标注服务")
    parser.add_argument("--camera", default="http://192.168.0.2:8082/camera",
                        help="原始相机 MJPEG 流地址(在相机所在设备上运行可填 http://127.0.0.1:8082/camera)")
    parser.add_argument("--port", type=int, default=8083,
                        help="带标注流服务端口(默认 8083)")
    parser.add_argument("--model", default=None,
                        help="YOLO 模型路径(默认取脚本目录下的 tesch_yolo_server.pt)")
    parser.add_argument("--device", default=None,
                        help="推理设备 auto/cuda:0/cpu(默认 auto,有 GPU 自动启用)")
    parser.add_argument("--imgsz", type=int, default=0,
                        help="推理输入尺寸,0=使用模型默认(调小可明显提速)")
    return parser.parse_args()


ARGS = _parse_args()
CAMERA_URL = ARGS.camera            # 原始相机 MJPEG 流
PORT = ARGS.port                    # 带标注流服务端口
HOST = "0.0.0.0"


def _pick_model_path():
    """选择模型文件:优先 --model,否则从脚本目录挑选实际存在的 .pt 文件"""
    if ARGS.model:
        return ARGS.model
    for name in ("tesch_yolo_server.pt", "tesch_yolo.pt", "zsl_yolo.pt", "yolo11n.pt"):
        p = os.path.join(_SCRIPT_DIR, name)
        if os.path.exists(p):
            return p
    return os.path.join(_SCRIPT_DIR, "tesch_yolo_server.pt")


MODEL_PATH = _pick_model_path()

# ===== 推理设备(自动检测 GPU) =====
def _pick_device():
    if ARGS.device in ("cpu", "cuda:0", "cpu:0"):
        return ARGS.device
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda:0"
    except Exception:          # noqa: BLE001
        pass
    return "cpu"


DEVICE = _pick_device()
IMGSZ = ARGS.imgsz or None     # None = 用模型默认 imgsz

# 检测置信度阈值
CONF_THRESHOLD = 0.7
# 像素 -> 厘米换算系数(每厘米对应的像素数),用于把框面积显示为 cm²;请按实际相机标定调整
PX_PER_CM = 20.0
# 每帧处理的 JPEG 质量(0-100)
JPEG_QUALITY = 100

app = Flask(__name__)

# 全局最新一帧(已标注)以及当前模型是否加载成功
_latest_raw = None              # 最新原始帧(仅保留最新,推理忙时自动丢帧)
_latest_jpg = None              # 最新已标注帧
_latest_lock = threading.Lock()
_model = None
_model_status = {"loaded": False, "error": None, "names": []}
# 最新一帧检测统计(供前端展示污渍类型/数量/置信度)
_latest_detections = {"model_loaded": False, "total": 0, "items": []}


def load_model():
    """加载 tesch_yolo_server.pt 模型(仅调用一次)"""
    global _model, _model_status
    try:
        from ultralytics import YOLO
        _model = YOLO(MODEL_PATH)
        _model_status["loaded"] = True
        _model_status["names"] = list(_model.names.values()) if _model.names else []
        print(f"[OK] 模型加载成功: {MODEL_PATH}")
        print(f"[OK] 类别: {_model.names}")
    except Exception as e:          # noqa: BLE001
        _model_status["loaded"] = False
        _model_status["error"] = str(e)
        print(f"[ERROR] 模型加载失败: {e}")


def _load_chinese_font(size):
    """加载系统中文字体;OpenCV 的 Hershey 字体不含中文,需用 PIL 才能正确渲染"""
    font_dir = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    for name in ("simhei.ttf", "msyh.ttc", "simsun.ttc"):
        path = os.path.join(font_dir, name)
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:  # noqa: BLE001
                continue
    return None


# 类别 -> 框/文字颜色(BGR):保证同一类别的框和标签文字同色
_CLASS_COLORS = {
    "contusion": (255, 144, 30),    # 橙
    "scratches": (0, 215, 255),     # 黄
    "crack": (255, 0, 0),           # 蓝
    "spot": (203, 192, 255),        # 粉紫
}


def _cls_color(name):
    return _CLASS_COLORS.get(name, (0, 255, 0))


def _cls_name(names, idx):
    """从模型 names 中取类别名;兼容 dict/list/缺失场景"""
    if isinstance(names, dict):
        return str(names.get(idx, f"class_{idx}"))
    if isinstance(names, (list, tuple)) and idx < len(names):
        return str(names[idx])
    return f"class_{idx}"


def draw_status_overlay(frame):
    """在画面左上角叠加'YOLO11N 识别中'字样(用 PIL 绘制,避免 cv2.putText 中文乱码成问号)"""
    h, w = frame.shape[:2]
    # 半透明黑底条,保证文字在任何画面上都清晰可读
    bar_w, bar_h = min(230, w), 36
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (bar_w, bar_h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    font = _load_chinese_font(22)
    if font is not None:
        # OpenCV(BGR) -> PIL(RGB) 绘制中文 -> 再转回 BGR
        pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil)
        draw.text((10, (bar_h - 22) // 2), "YOLO11N 识别中", font=font, fill=(0, 255, 0))
        frame = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    else:
        # 找不到中文字体时回退为纯英文,避免出现问号乱码
        cv2.putText(frame, "YOLO11N YOLO RUNNING", (10, bar_h - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 0), 2, cv2.LINE_AA)

    # 左下角:显示 YOLO 推理参数(置信度/输入尺寸/设备),便于确认当前检测配置
    info = f"YOLO  conf {CONF_THRESHOLD}  imgsz {IMGSZ if IMGSZ else 'default'}  {DEVICE}"
    font2 = _load_chinese_font(16)
    if font2 is not None:
        h_, w_ = frame.shape[:2]
        b2_h = 26
        pil = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        bbox = ImageDraw.Draw(pil).textbbox((10, h_ - b2_h), info, font=font2)
        bg_w = (bbox[2] - bbox[0]) + 12
        overlay = pil.copy()
        ImageDraw.Draw(overlay).rectangle([0, h_ - b2_h, bg_w, h_], fill=(0, 0, 0))
        pil = Image.blend(pil, overlay, 0.55)
        ImageDraw.Draw(pil).text((10, h_ - b2_h + 3), info, font=font2, fill=(0, 255, 255))
        frame = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    return frame


def process_jpeg(jpg_bytes):
    """对单个 JPEG 帧做检测标注并更新最新标注帧"""
    global _latest_jpg, _latest_detections
    frame = cv2.imdecode(np.frombuffer(jpg_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        return

    # 目标检测
    if _model is not None:
        try:
            kwargs = dict(conf=CONF_THRESHOLD, verbose=False, device=DEVICE)
            if IMGSZ:
                kwargs["imgsz"] = IMGSZ
            results = _model.predict(frame, **kwargs)
            annotated = frame.copy()          # 自定义绘制,完全控制框/文字颜色
            boxes = results[0].boxes
            names = getattr(_model, "names", None)

            # 统计本帧检测明细:各类别数量与最高置信度
            stat = {}

            # 每个目标:统一颜色画框 + 框上方标签一行(类别 置信度 中心坐标 面积)
            if boxes is not None and len(boxes) > 0:
                font = _load_chinese_font(20)
                xyxy = boxes.xyxy.cpu().numpy()
                for (x1, y1, x2, y2), cls_id, conf in zip(xyxy, boxes.cls.tolist(), boxes.conf.tolist()):
                    idx = int(cls_id)
                    cls_name = _cls_name(names, idx)
                    color = _cls_color(cls_name)
                    # 画框线
                    cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                    # 画标签文字(与框同色,带半透明黑底),优先画在框正上方,框贴顶时改到框内顶部
                    cx, cy = int(round((x1 + x2) / 2)), int(round((y1 + y2) / 2))
                    area_cm = round((x2 - x1) * (y2 - y1) / (PX_PER_CM ** 2), 1)
                    label = f"{cls_name} {conf:.2f} 中心({cx},{cy}) 面积{area_cm}cm²"
                    if font is not None:
                        pil = Image.fromarray(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB))
                        ty = int(y1) - 26
                        if ty < 0:
                            ty = int(y1) + 4
                        # 先按文字尺寸画半透明黑底,再写字,保证在任意画面上清晰可读
                        bbox = ImageDraw.Draw(pil).textbbox((int(x1), ty), label, font=font)
                        bg_w, bg_h = (bbox[2] - bbox[0]) + 8, (bbox[3] - bbox[1]) + 4
                        overlay = pil.copy()
                        ImageDraw.Draw(overlay).rectangle(
                            [bbox[0] - 3, bbox[1] - 2, bbox[0] - 3 + bg_w, bbox[1] - 2 + bg_h], fill=(0, 0, 0))
                        pil = Image.blend(pil, overlay, 0.55)
                        ImageDraw.Draw(pil).text((int(x1), ty), label, font=font, fill=(color[2], color[1], color[0]))
                        annotated = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)

            if boxes is not None and len(boxes) > 0:
                for cls_id, conf in zip(boxes.cls.tolist(), boxes.conf.tolist()):
                    idx = int(cls_id)
                    key = _cls_name(names, idx)
                    cur = stat.get(key)
                    if cur is None:
                        stat[key] = {"count": 1, "max_conf": round(conf, 3)}
                    else:
                        cur["count"] += 1
                        if conf > cur["max_conf"]:
                            cur["max_conf"] = round(conf, 3)
            items = [{"name": k, **v} for k, v in stat.items()]
            with _latest_lock:
                _latest_detections = {
                    "model_loaded": True,
                    "total": len(boxes) if boxes is not None else 0,
                    "items": items,
                }
        except Exception as e:                  # noqa: BLE001
            annotated = frame
            _latest_detections["model_loaded"] = True
    else:
        annotated = frame

    # 叠加左上角状态标签(始终显示,用于确认识别服务状态)
    annotated = draw_status_overlay(annotated)

    ok_jpg, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    if ok_jpg:
        with _latest_lock:
            _latest_jpg = buf.tobytes()


def _grab_loop():
    """
    采集线程:以浏览器 <img> 相同方式拉取 multipart/x-mixed-replace 原始
    MJPEG 流,按 JPEG 帧边界切帧,只保留最新一帧(推理忙时后面的帧覆盖旧帧,即自动丢帧)。
    断流自动重连。
    """
    global _latest_raw
    print(f"[INFO] 正在连接相机流: {CAMERA_URL}")
    while True:
        try:
            req = urllib.request.Request(CAMERA_URL, headers={"User-Agent": "Mozilla/5.0"})
            stream = urllib.request.urlopen(req, timeout=10)
            ctype = stream.headers.get("Content-Type", "")
            print(f"[OK] 已连接相机流: {CAMERA_URL} ({ctype}), 推理设备: {DEVICE}")
            _model_status["error"] = None

            buf = b""
            while True:
                chunk = stream.read(65536)
                if not chunk:
                    print("[WARN] 流已结束(相机断开),尝试重连...")
                    break
                buf += chunk

                while True:
                    start = buf.find(b"\xff\xd8")
                    if start < 0:
                        buf = b""
                        break
                    end = buf.find(b"\xff\xd9", start + 2)
                    if end < 0:
                        buf = buf[start:]
                        break
                    jpg = buf[start:end + 2]
                    buf = buf[end + 2:]
                    # 只保留最新原始帧
                    with _latest_lock:
                        _latest_raw = jpg
        except Exception as e:                   # noqa: BLE001
            _model_status["error"] = f"无法连接相机: {CAMERA_URL} ({e})"
            print(f"[ERROR] 相机连接失败: {e}, 3 秒后重试")
        finally:
            try:
                if "stream" in dir():
                    stream.close()
            except Exception:                    # noqa: BLE001
                pass
        time.sleep(3.0)


def _infer_loop():
    """
    推理线程:不断取最新原始帧做检测。取走即标记已消费,若推理期间又来了新帧,
    下一次循环直接取最新一帧,旧的丢弃,保证永远处理最新帧、延迟不累积。
    """
    while True:
        global _latest_raw
        with _latest_lock:
            raw = _latest_raw
            _latest_raw = None
        if raw is None:
            time.sleep(0.005)
            continue
        try:
            process_jpeg(raw)
        except Exception as e:                   # noqa: BLE001
            print(f"[WARN] 处理帧异常: {e}")


def gen_mjpeg():
    """MJPEG 生成器:按帧输出 multipart/x-mixed-replace"""
    boundary = b"--boundary"
    while True:
        with _latest_lock:
            jpg = _latest_jpg
        if jpg is None:
            # 尚未就绪,短暂等待
            time.sleep(0.2)
            continue
        yield (boundary + b"\r\n"
               b"Content-Type: image/jpeg\r\n"
               + ("Content-Length: %d\r\n\r\n" % len(jpg)).encode()
               + jpg + b"\r\n")
        # 与原流相近的帧率(约 10 FPS)
        time.sleep(0.1)


@app.route("/camera")
def camera_stream():
    """带标注的 MJPEG 流,前端 <img> 直接引用"""
    return Response(gen_mjpeg(), mimetype="multipart/x-mixed-replace; boundary=--boundary")


# ===== 设备开机时长查询(SSH 读 /proc/uptime,带缓存)=====
_DEVICE_HOST = "192.168.0.2"
_DEVICE_USER = "nvidia"
_DEVICE_PASS = "nvidia"
_uptime_cache = {"value": 0, "ts": 0}
_uptime_lock = threading.Lock()
_UPTIME_TTL = 10  # 秒,避免频繁 SSH


def _get_uptime_seconds():
    """返回设备开机秒数;失败返回 -1。结果缓存 _UPTIME_TTL 秒。"""
    global _uptime_cache
    now = time.time()
    with _uptime_lock:
        if now - _uptime_cache["ts"] < _UPTIME_TTL and _uptime_cache["value"] > 0:
            return _uptime_cache["value"]
    if paramiko is None:
        return -1
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(_DEVICE_HOST, username=_DEVICE_USER, password=_DEVICE_PASS, timeout=4)
        _, stdout, _ = client.exec_command("cat /proc/uptime", timeout=6)
        out = stdout.read().decode("utf-8", "replace").strip()
        client.close()
        secs = float(out.split()[0])
        with _uptime_lock:
            _uptime_cache = {"value": secs, "ts": now}
        return secs
    except Exception:  # noqa: BLE001
        return -1


@app.route("/uptime")
def uptime():
    """设备开机时长(秒);设备不可达时返回 -1"""
    return jsonify({"uptime": _get_uptime_seconds()})


@app.route("/status")
def status():
    """健康状况接口"""
    return jsonify(**_model_status)


@app.route("/info")
def info():
    """服务配置信息:暴露原始相机 HTTP 基址,供前端定位深度/红外流(/depth /ir)"""
    return jsonify({
        "camera_url": CAMERA_URL,      # 原始相机流地址,如 http://192.168.0.2:8082/camera
        "port": PORT,
        "device": DEVICE,
    })


@app.after_request
def add_cors_headers(resp):
    """允许前端跨端口(8081->8083) fetch 检测统计接口"""
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


@app.route("/detections")
def detections():
    """最新一帧检测统计(污渍类型/数量/置信度)"""
    with _latest_lock:
        return jsonify(**_latest_detections)


if __name__ == "__main__":
    load_model()
    print(f"[OK] 推理设备: {DEVICE}{'  imgsz=' + str(IMGSZ) if IMGSZ else ''}")

    # 启动后台采集 / 推理两线程(各自独立,推理忙时丢帧以降低延迟)
    threading.Thread(target=_grab_loop, daemon=True).start()
    threading.Thread(target=_infer_loop, daemon=True).start()

    print(f"\n[OK] 带标注视频流服务已启动: http://localhost:{PORT}/camera")
    print(f"     健康状况:     http://localhost:{PORT}/status")
    print("按 Ctrl+C 停止服务...\n")

    try:
        app.run(host=HOST, port=PORT, threaded=True, debug=False)
    except KeyboardInterrupt:
        print("\n[OK] 服务已停止")