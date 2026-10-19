#!/usr/bin/env python3
"""
机器人Web控制服务器 - Jetson端
HTTP + WebSocket 混合方案
"""

import json
import threading
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, disconnect

import sys
from config import SERVER_CONFIG, HEARTBEAT_CONFIG, cmd_map
from stm32_controller import STM32Controller, AutoStopManager

# 全局控制器（初始化时会根据参数设置模式）
controller = None
auto_stop = None

def init_controller(mock_mode=False):
    """初始化控制器"""
    global controller, auto_stop
    controller = STM32Controller(mock_mode=mock_mode)
    auto_stop = AutoStopManager(controller)
    return controller

app = Flask(__name__)
app.config['SECRET_KEY'] = 'robot-secret-key'
CORS(app, origins=["http://localhost:8080", "http://localhost:8081", "http://127.0.0.1:8080", "http://127.0.0.1:8081"])
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# WebSocket客户端管理
ws_clients = {}
ws_lock = threading.Lock()


# ============ HTTP API ============

@app.route('/')
def index():
    """服务状态"""
    return jsonify({
        "service": "Robot Control Server",
        "version": "1.0.0",
        "serial_status": controller.get_status()
    })


@app.route('/api/status', methods=['GET'])
def get_status():
    """获取系统状态"""
    return jsonify(controller.get_status())


@app.route('/api/connect', methods=['POST'])
def connect_serial():
    """手动连接串口"""
    success = controller.connect()
    return jsonify({
        "success": success,
        "message": "已连接" if success else "连接失败",
        "status": controller.get_status()
    })


@app.route('/api/disconnect', methods=['POST'])
def disconnect_serial():
    """断开串口"""
    auto_stop.cancel()
    controller.disconnect()
    return jsonify({
        "success": True,
        "message": "已断开",
        "status": controller.get_status()
    })


@app.route('/api/control', methods=['POST'])
def control():
    """
    基础控制接口
    请求体: {"command": "forward", "duration": 0}
    """
    data = request.get_json()
    
    if not data or 'command' not in data:
        return jsonify({
            "success": False,
            "message": "请求格式错误，需要 {'command': 'xxx', 'duration': 0}"
        }), 400
    
    command = data['command']
    duration = data.get('duration', 0)
    
    # 验证命令
    if command not in cmd_map:
        return jsonify({
            "success": False,
            "message": f"未知命令: {command}",
            "available_commands": list(cmd_map.keys())
        }), 400
    
    # 发送命令
    success, msg = controller.send_command(command)
    
    if success and duration > 0:
        # 调度自动停止
        auto_stop.schedule_stop(duration)
    else:
        auto_stop.cancel()
    
    return jsonify({
        "status": "ok" if success else "error",
        "success": success,
        "command": command,
        "duration": duration,
        "message": msg,
        "device_status": controller.get_status()
    })


@app.route('/api/stop', methods=['POST'])
def emergency_stop():
    """紧急停止"""
    auto_stop.cancel()
    success, msg = controller.stop()
    return jsonify({
        "success": success,
        "message": msg,
        "status": controller.get_status()
    })


# ============ WebSocket API ============

@socketio.on('connect')
def ws_connect():
    """客户端连接"""
    sid = request.sid
    with ws_lock:
        ws_clients[sid] = {
            "connected_at": time.time(),
            "last_heartbeat": time.time(),
            "current_command": None
        }
    
    print(f"[WebSocket] 客户端连接: {sid}")
    emit('connected', {
        "sid": sid,
        "server_time": time.time(),
        "status": controller.get_status()
    })


@socketio.on('disconnect')
def ws_disconnect():
    """客户端断开"""
    sid = request.sid
    with ws_lock:
        if sid in ws_clients:
            del ws_clients[sid]
    
    # 如果没有客户端了，发送停止命令
    with ws_lock:
        if len(ws_clients) == 0:
            print("[WebSocket] 所有客户端断开，自动停止")
            controller.stop()
    
    print(f"[WebSocket] 客户端断开: {sid}")


@socketio.on('heartbeat')
def ws_heartbeat(data):
    """
    心跳处理
    前端每100ms发送一次
    """
    sid = request.sid
    
    with ws_lock:
        if sid in ws_clients:
            ws_clients[sid]['last_heartbeat'] = time.time()
    
    emit('heartbeat_ack', {"server_time": time.time()})


@socketio.on('control')
def ws_control(data):
    """
    实时控制命令
    用于键盘/手柄等实时控制场景
    """
    sid = request.sid
    command = data.get('command')
    
    if not command:
        emit('error', {"message": "缺少command字段"})
        return
    
    if command not in cmd_map:
        emit('error', {"message": f"未知命令: {command}"})
        return
    
    # 更新客户端当前命令
    with ws_lock:
        if sid in ws_clients:
            ws_clients[sid]['current_command'] = command
    
    # 发送命令到STM32
    success, msg = controller.send_command(command)
    
    # 广播状态给所有客户端
    status = controller.get_status()
    socketio.emit('status_update', {
        "source": "websocket",
        "command": command,
        "success": success,
        "message": msg,
        "status": status
    })
    
    emit('control_ack', {
        "command": command,
        "success": success,
        "message": msg
    })


@socketio.on('stop')
def ws_stop():
    """WebSocket紧急停止"""
    success, msg = controller.stop()
    emit('stop_ack', {"success": success, "message": msg})


# ============ 心跳超时检测线程 ============

def heartbeat_checker():
    """
    心跳超时检测
    500ms未收到心跳则自动停止
    """
    timeout = HEARTBEAT_CONFIG["timeout_ms"] / 1000.0
    
    while True:
        time.sleep(0.1)  # 100ms检查一次
        
        now = time.time()
        with ws_lock:
            for sid, client in list(ws_clients.items()):
                elapsed = now - client['last_heartbeat']
                if elapsed > timeout:
                    print(f"[Heartbeat] 客户端 {sid} 超时 ({elapsed:.2f}s)")
                    # 超时自动停止
                    if controller.current_command != "stop":
                        controller.stop()


# ============ 启动函数 ============

def main():
    """启动服务器"""
    # 检查启动参数
    mock_mode = '--mock' in sys.argv or '-m' in sys.argv
    
    print("=" * 60)
    print("机器人Web控制服务器 - Jetson端")
    print("=" * 60)
    
    # 初始化控制器
    init_controller(mock_mode=mock_mode)
    
    if mock_mode:
        print("\n[启动] 模拟模式已启用（假机器人）")
        print("[启动] 所有串口操作将被模拟，控制台会显示命令")
    
    # 尝试自动连接STM32
    print("\n[启动] 尝试连接STM32...")
    if controller.connect():
        if mock_mode:
            print("[启动] 模拟STM32连接成功")
        else:
            print("[启动] STM32连接成功")
    else:
        print("[警告] STM32连接失败，服务将继续运行")
        print(f"[提示] 请检查设备 {controller.get_status()['port']} 是否存在")
        print("[提示] 如需测试，可使用 --mock 参数启动模拟模式")
    
    # 启动心跳检测线程
    checker = threading.Thread(target=heartbeat_checker, daemon=True)
    checker.start()
    
    print("\n[启动] 服务器配置:")
    mode_str = "[模拟模式]" if mock_mode else "[真实硬件]"
    print(f"  - 运行模式: {mode_str}")
    print(f"  - HTTP API: http://{SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}/api/control")
    print(f"  - WebSocket: ws://{SERVER_CONFIG['host']}:{SERVER_CONFIG['port']}/")
    print(f"  - 心跳超时: {HEARTBEAT_CONFIG['timeout_ms']}ms")
    print("\n[启动] 按 Ctrl+C 停止服务器\n")
    
    try:
        socketio.run(
            app,
            host=SERVER_CONFIG['host'],
            port=SERVER_CONFIG['port'],
            debug=SERVER_CONFIG['debug'],
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        print("\n[关闭] 正在关闭服务器...")
    finally:
        auto_stop.cancel()
        controller.disconnect()
        print("[关闭] 服务器已停止")


if __name__ == '__main__':
    main()
