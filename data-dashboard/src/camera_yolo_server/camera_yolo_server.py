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
import os
import time
import threading
import urllib.request

import cv2
import numpy as np
from flask import Flask, Response, jsonify

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
CONF_THRESHOLD = 0.6
# 每帧处理的 JPEG 质量(0-100)
JPEG_QUALITY = 80

app = Flask(__name__)

# 全局最新一帧(已标注)以及当前模型是否加载成功
_latest_raw = None              # 最新原始帧(仅保留最新,推理忙时自动丢帧)
_latest_jpg = None              # 最新已标注帧
_latest_lock = threading.Lock()
_model = None
_model_status = {"loaded": False, "error": None, "names": []}


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


def draw_status_overlay(frame):
    """在画面左上角叠加'YOLO11N 识别中'字样,便于确认检测服务是否在运行"""
    h, w = frame.shape[:2]
    # 半透明黑底条,保证文字在任何画面上都清晰可读
    bar_w, bar_h = min(300, w), 36
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (bar_w, bar_h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)
    cv2.putText(frame, "YOLO11N 识别中", (10, bar_h - 12), cv2.FONT_HERSHEY_SIMPLEX,
                0.85, (0, 255, 0), 2, cv2.LINE_AA)
    return frame


def process_jpeg(jpg_bytes):
    """对单个 JPEG 帧做检测标注并更新最新标注帧"""
    global _latest_jpg
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
            annotated = results[0].plot()       # 绘制标注框/类别/置信度
        except Exception as e:                  # noqa: BLE001
            annotated = frame
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


@app.route("/status")
def status():
    """健康状况接口"""
    return jsonify(**_model_status)


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