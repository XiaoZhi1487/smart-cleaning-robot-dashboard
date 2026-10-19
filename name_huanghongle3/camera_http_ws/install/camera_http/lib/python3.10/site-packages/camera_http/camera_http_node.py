#!/usr/bin/env python3
"""
HTTP MJPEG Camera Server for ROS2
==================================
订阅彩色/深度/红外话题，分别通过 HTTP MJPEG 提供 /camera /depth /ir 三个流。
前端用 <img> 直连，不经过 rosbridge，避免视频占用 rosbridge 内存/CPU。

彩色: /camera/color/image_raw（YOLO 推理本地运行，设备端不再发布 /detection/image）
深度: /camera/depth/image_raw (16UC1) -> 归一化灰度
红外: /camera/left_ir/image_raw (16UC1/8UC1) -> 归一化灰度
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import threading
import socketserver
from http.server import BaseHTTPRequestHandler
import time
import numpy as np
from urllib.parse import urlparse


class MJPEGHandler(BaseHTTPRequestHandler):
    """HTTP Handler for MJPEG streaming"""

    # 各流最新帧(已可编码的 8bit 灰度 / BGR)与锁,跨线程共享
    color_frame = None
    depth_frame = None
    ir_frame = None
    frame_lock = threading.Lock()

    _STREAMS = {'/camera': 'color', '/depth': 'depth', '/ir': 'ir'}

    def do_GET(self):
        # 剥离查询串(前端 <img> 会追加 ?t=...&r=... 时间戳强制刷新),只取纯路径
        path = urlparse(self.path).path
        mode = self._STREAMS.get(path)
        if path in ('/', ''):
            mode = 'color'
        if mode is None:
            self.send_response(404)
            self.end_headers()
            return

        self.send_response(200)
        self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        self.server.node.get_logger().info(f'Client connected to {self.path}')

        try:
            while True:
                with MJPEGHandler.frame_lock:
                    frame = getattr(MJPEGHandler, f'{mode}_frame')
                if frame is not None:
                    ret, jpeg = cv2.imencode('.jpg', frame)
                    if ret:
                        self.wfile.write(b'--jpgboundary\r\n')
                        self.send_header('Content-type', 'image/jpeg')
                        self.send_header('Content-length', len(jpeg))
                        self.end_headers()
                        self.wfile.write(jpeg.tobytes())
                        self.wfile.write(b'\r\n')
                time.sleep(0.1)
        except (BrokenPipeError, ConnectionResetError):
            self.server.node.get_logger().info(f'Client disconnected: {self.path}')

    def log_message(self, format, *args):
        pass  # 抑制默认 HTTP 日志


class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def _norm_to_8bit(cvimg, max_val):
    """把 16 位灰度归一化为 8 位(0..max_val -> 0..255),max_val<=0 时用 min/max 自适应"""
    if cvimg is None:
        return None
    if cvimg.dtype != np.uint8:
        f = cvimg.astype(np.float32)
        if max_val and max_val > 0:
            np.clip(f, 0, max_val, out=f)
            f /= max_val
        else:
            mn, mx = float(f.min()), float(f.max())
            if mx - mn < 1e-3:
                f = np.zeros_like(f)
            else:
                f = (f - mn) / (mx - mn)
        return (f * 255).astype(np.uint8)
    return cvimg


class CameraHTTPServer(Node):
    def __init__(self):
        super().__init__('camera_http_server')

        # 参数
        self.declare_parameter('primary_topic', '/camera/color/image_raw')
        self.declare_parameter('fallback_topic', '/camera/color/image_raw')
        self.declare_parameter('fallback_timeout', 3.0)
        self.declare_parameter('port', 8082)
        self.declare_parameter('host', '0.0.0.0')
        self.declare_parameter('resize_width', 1280)
        self.declare_parameter('resize_height', 720)
        self.declare_parameter('jpeg_quality', 80)
        self.declare_parameter('depth_topic', '/camera/depth/image_raw')
        self.declare_parameter('ir_topic', '/camera/left_ir/image_raw')
        self.declare_parameter('depth_max_mm', 4000.0)
        self.declare_parameter('ir_max', 1023.0)

        self.primary_topic = self.get_parameter('primary_topic').value
        self.fallback_topic = self.get_parameter('fallback_topic').value
        self.fallback_timeout = self.get_parameter('fallback_timeout').value
        port = self.get_parameter('port').value
        host = self.get_parameter('host').value
        self.resize_width = self.get_parameter('resize_width').value
        self.resize_height = self.get_parameter('resize_height').value
        self.depth_max = self.get_parameter('depth_max_mm').value
        self.ir_max = self.get_parameter('ir_max').value

        self.bridge = CvBridge()
        self.frame_count = 0
        self.last_frame_time = None
        self.current_topic = self.primary_topic
        self.subscription = None
        self.fallback_timer = None

        self.server = ThreadedHTTPServer((host, port), MJPEGHandler)
        self.server.node = self
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

        self.get_logger().info('=' * 50)
        self.get_logger().info('HTTP MJPEG Server started!')
        self.get_logger().info(f'URLs: /camera(彩色) /depth(深度) /ir(红外) -> http://{host}:{port}')
        self.get_logger().info('=' * 50)

        self._subscribe_topic(self.primary_topic)
        self.fallback_timer = self.create_timer(self.fallback_timeout, self._check_and_fallback)

        # 深度/红外常驻订阅
        self.depth_sub = self.create_subscription(
            Image, self.get_parameter('depth_topic').value, self.depth_callback, 10)
        self.ir_sub = self.create_subscription(
            Image, self.get_parameter('ir_topic').value, self.ir_callback, 10)

    def _subscribe_topic(self, topic_name):
        if self.subscription is not None:
            self.destroy_subscription(self.subscription)
            self.subscription = None
        self.current_topic = topic_name
        self.subscription = self.create_subscription(
            Image, topic_name, self.image_callback, 10)
        self.last_frame_time = self.get_clock().now()
        self.get_logger().info(f'已订阅话题: {topic_name}')

    def _check_and_fallback(self):
        if self.current_topic == self.fallback_topic:
            return
        now = self.get_clock().now()
        elapsed = (now - self.last_frame_time).nanoseconds / 1e9
        if self.frame_count == 0 and elapsed > self.fallback_timeout:
            self.get_logger().warn(f'话题 {self.primary_topic} 无数据,回退到 {self.fallback_topic}')
            self._subscribe_topic(self.fallback_topic)
            if self.fallback_timer is not None:
                self.fallback_timer.cancel()

    def image_callback(self, msg):
        # 彩色流
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            resized = cv2.resize(cv_image, (self.resize_width, self.resize_height))
            with MJPEGHandler.frame_lock:
                MJPEGHandler.color_frame = resized
            self.frame_count += 1
            self.last_frame_time = self.get_clock().now()
        except Exception as e:  # noqa: BLE001
            self.get_logger().error(f'color_callback: {e}')

    def depth_callback(self, msg):
        try:
            cvimg = self.bridge.imgmsg_to_cv2(msg)
            gray = _norm_to_8bit(cvimg, self.depth_max)
            with MJPEGHandler.frame_lock:
                MJPEGHandler.depth_frame = gray
        except Exception as e:  # noqa: BLE001
            self.get_logger().error(f'depth_callback: {e}')

    def ir_callback(self, msg):
        try:
            cvimg = self.bridge.imgmsg_to_cv2(msg)
            gray = _norm_to_8bit(cvimg, self.ir_max)
            with MJPEGHandler.frame_lock:
                MJPEGHandler.ir_frame = gray
        except Exception as e:  # noqa: BLE001
            self.get_logger().error(f'ir_callback: {e}')

    def destroy_node(self):
        self.get_logger().info('Shutting down HTTP server...')
        self.server.shutdown()
        self.server.server_close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = CameraHTTPServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
