#!/usr/bin/env python3
"""
Jetson 服务启动管理器
一键启动：rosbridge + 相机 + 视频流 + 超声波 + STM32控制
作者: Jetson Engineer
日期: 2026-03-02
更新: 2026-03-09 - 添加 STM32 控制节点
"""

import subprocess
import time
import sys
import os
import signal
import psutil
from datetime import datetime

# 配置
SERVICES = {
    "camera": {
        "name": "相机 (Orbbec Gemini 336)",
        "process_patterns": ["gemini_330_series", "component_container", "orbbec_camera"],
        "port": None,  # 相机不监听端口
        "topic": "/camera/color/image_raw",
        "launch_cmd": [
            "ros2", "launch", "orbbec_camera", "gemini_330_series.launch.py",
            "color_width:=1280",
            "color_height:=720",
            "color_fps:=10",
            "enable_depth:=false",
            "enable_point_cloud:=false"
        ],
        "log_file": "/tmp/camera.log",
        "startup_delay": 15,  # 相机启动慢
    },
    "http_server": {
        "name": "HTTP 视频流服务器",
        "process_patterns": ["camera_http_node"],
        "port": 8082,
        "launch_cmd": None,  # 用函数启动
        "log_file": "/tmp/http_server.log",
        "startup_delay": 3,
    },
    "rosbridge": {
        "name": "ROS Bridge Server",
        "process_patterns": ["rosbridge_websocket"],
        "port": 9090,
        "launch_cmd": [
            "ros2", "launch", "rosbridge_server", "rosbridge_websocket_launch.xml"
        ],
        "log_file": "/tmp/rosbridge.log",
        "startup_delay": 3,
    },
    "ultrasonic": {
        "name": "超声波传感器",
        "process_patterns": ["wave_length_node"],
        "port": None,
        "topic": "/wave_length",
        "launch_cmd": None,  # 用函数启动
        "log_file": "/tmp/ultrasonic.log",
        "startup_delay": 3,
    },
    "stm32_control": {
        "name": "STM32 控制节点",
        "process_patterns": ["stm32_control_node"],
        "port": None,
        "topic": "/stm32_cmd",
        "launch_cmd": None,  # 用函数启动
        "log_file": "/tmp/stm32_control.log",
        "startup_delay": 3,
    }
}

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def log(msg, level="INFO"):
    """打印带时间戳的日志"""
    now = datetime.now().strftime("%H:%M:%S")
    color = {
        "INFO": Colors.BLUE,
        "OK": Colors.GREEN,
        "ERROR": Colors.RED,
        "WARN": Colors.YELLOW
    }.get(level, Colors.BLUE)
    print(f"{color}[{now}] [{level}] {msg}{Colors.END}")

def find_processes(patterns):
    """根据模式查找进程"""
    found = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            for pattern in patterns:
                if pattern in cmdline or pattern in proc.info['name']:
                    found.append(proc)
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return found

def kill_processes(patterns, service_name):
    """杀死匹配的进程"""
    procs = find_processes(patterns)
    if not procs:
        return False
    
    log(f"发现 {len(procs)} 个 {service_name} 进程，正在停止...", "WARN")
    for proc in procs:
        try:
            log(f"  停止 PID {proc.pid}")
            proc.terminate()
            proc.wait(timeout=3)
        except psutil.TimeoutExpired:
            proc.kill()
            proc.wait()
        except Exception as e:
            log(f"  停止失败: {e}", "ERROR")
    
    # 再次检查
    time.sleep(1)
    remaining = find_processes(patterns)
    if remaining:
        log(f"强制杀死 {len(remaining)} 个残留进程", "WARN")
        for proc in remaining:
            try:
                os.kill(proc.pid, signal.SIGKILL)
            except:
                pass
    
    return True

def check_port(port):
    """检查端口是否被占用"""
    if port is None:
        return False
    for conn in psutil.net_connections():
        if conn.laddr.port == port:
            return True
    return False

def wait_for_topic(topic, timeout=30):
    """等待 ROS 话题出现"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            result = subprocess.run(
                ["ros2", "topic", "list"],
                capture_output=True, text=True, timeout=5
            )
            if topic in result.stdout:
                return True
        except:
            pass
        time.sleep(1)
    return False

def wait_for_port(port, timeout=10):
    """等待端口监听"""
    start = time.time()
    while time.time() - start < timeout:
        if check_port(port):
            return True
        time.sleep(0.5)
    return False

def start_service(service_key, config):
    """启动单个服务"""
    log(f"\n{'='*50}")
    log(f"启动: {config['name']}")
    log(f"{'='*50}")
    
    # 1. 检查并停止旧进程
    if kill_processes(config['process_patterns'], config['name']):
        log("旧进程已清理")
    else:
        log("无旧进程")
    
    # 2. 检查端口
    if config['port'] and check_port(config['port']):
        log(f"端口 {config['port']} 仍被占用！", "ERROR")
        return False
    
    # 3. 启动服务
    log("正在启动...")
    
    if service_key == "http_server":
        # 特殊处理 HTTP 服务器
        # 用 python3 直接运行源码，绕过 ament 可执行索引缺失导致的 ros2 run "No executable found"
        cmd = """
        cd /home/nvidia/name_huanghongle3/camera_http_ws &&
        source /opt/ros/humble/setup.bash &&
        source install/setup.bash &&
        python3 src/camera_http/camera_http/camera_http_node.py
        """
        process = subprocess.Popen(
            cmd, shell=True, executable='/bin/bash',
            stdout=open(config['log_file'], 'w'),
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )
    elif service_key == "ultrasonic":
        # 特殊处理超声波节点
        cmd = """
        cd /home/nvidia/name_ranhongmei/ws &&
        source /opt/ros/humble/setup.bash &&
        source install/setup.bash &&
        ros2 run fist_demo_uart wave_length_node
        """
        process = subprocess.Popen(
            cmd, shell=True, executable='/bin/bash',
            stdout=open(config['log_file'], 'w'),
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )
    elif service_key == "stm32_control":
        # 特殊处理 STM32 控制节点
        cmd = """
        cd /home/nvidia/name_zhoushifei/WS &&
        source /opt/ros/humble/setup.bash &&
        source install/setup.bash &&
        ros2 run stm32_control stm32_control_node
        """
        process = subprocess.Popen(
            cmd, shell=True, executable='/bin/bash',
            stdout=open(config['log_file'], 'w'),
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid
        )
    else:
        # 标准 ROS2 launch
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        process = subprocess.Popen(
            config['launch_cmd'],
            stdout=open(config['log_file'], 'w'),
            stderr=subprocess.STDOUT,
            env=env,
            preexec_fn=os.setsid
        )
    
    # 4. 等待启动
    log(f"等待 {config['startup_delay']} 秒初始化...")
    time.sleep(config['startup_delay'])
    
    # 5. 验证启动
    success = True
    
    # 检查进程是否还在
    if not find_processes(config['process_patterns']):
        log("进程已退出！", "ERROR")
        success = False
    
    # 检查端口
    if config['port'] and not check_port(config['port']):
        log(f"端口 {config['port']} 未监听！", "ERROR")
        success = False
    
    # 检查话题
    if config.get('topic') and not wait_for_topic(config['topic'], timeout=10):
        log(f"话题 {config['topic']} 未出现！", "WARN")
        # 不判定失败，继续等待
    
    if success:
        log(f"✓ {config['name']} 启动成功！", "OK")
        if config['port']:
            log(f"  端口: {config['port']}")
        if config.get('topic'):
            log(f"  话题: {config['topic']}")
        log(f"  日志: {config['log_file']}")
    else:
        log(f"✗ {config['name']} 启动失败！", "ERROR")
    
    return success

def check_all_status():
    """检查所有服务状态"""
    log("\n" + "="*50)
    log("当前服务状态")
    log("="*50)
    
    for key, config in SERVICES.items():
        procs = find_processes(config['process_patterns'])
        port_ok = check_port(config['port']) if config['port'] else None
        
        status = "🟢 运行中" if procs else "🔴 未运行"
        if port_ok is not None:
            port_status = f"端口{'正常' if port_ok else '异常'}"
            log(f"{config['name']}: {status} ({port_status})")
        else:
            log(f"{config['name']}: {status}")
        
        for proc in procs:
            log(f"  PID: {proc.pid}")

def stop_all_services():
    """停止所有服务"""
    log("\n" + "="*50)
    log("停止所有服务")
    log("="*50)
    
    for key, config in SERVICES.items():
        kill_processes(config['process_patterns'], config['name'])
    
    log("✓ 所有服务已停止", "OK")

def main():
    """主函数"""
    print(f"\n{Colors.BOLD}{'='*60}")
    print("Jetson 服务启动管理器")
    print(f"{'='*60}{Colors.END}")
    print("功能: 一键启动相机 + HTTP服务器 + ROS桥 + 超声波 + STM32控制")
    print("作者: Jetson Engineer")
    print("")
    
    # 参数处理
    if len(sys.argv) > 1:
        if sys.argv[1] in ['stop', 'kill', 'down']:
            stop_all_services()
            return
        elif sys.argv[1] in ['status', 'check']:
            check_all_status()
            return
        elif sys.argv[1] in ['help', '-h', '--help']:
            print("用法:")
            print("  python3 start_all_services.py       # 启动所有服务")
            print("  python3 start_all_services.py stop  # 停止所有服务")
            print("  python3 start_all_services.py status # 查看状态")
            return
    
    # 启动所有服务
    log("开始启动服务...")
    log(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # 1. 启动相机（必须先启动）
    results['camera'] = start_service('camera', SERVICES['camera'])
    if not results['camera']:
        log("相机启动失败，终止后续启动", "ERROR")
        return 1
    
    # 2. 启动 HTTP 视频流服务器
    results['http_server'] = start_service('http_server', SERVICES['http_server'])
    
    # 3. 启动 ROS Bridge
    results['rosbridge'] = start_service('rosbridge', SERVICES['rosbridge'])
    
    # 4. 启动超声波
    results['ultrasonic'] = start_service('ultrasonic', SERVICES['ultrasonic'])
    
    # 5. 启动 STM32 控制节点
    results['stm32_control'] = start_service('stm32_control', SERVICES['stm32_control'])
    
    # 最终状态
    log("\n" + "="*60)
    log("启动结果汇总")
    log("="*60)
    
    for key, success in results.items():
        name = SERVICES[key]['name']
        status = "✓ 成功" if success else "✗ 失败"
        level = "OK" if success else "ERROR"
        log(f"{name}: {status}", level)
    
    all_success = all(results.values())
    
    log("\n" + "="*60)
    if all_success:
        log("🎉 所有服务启动成功！", "OK")
    else:
        log("⚠️ 部分服务启动失败", "WARN")
    log("="*60)
    
    # 显示访问地址
    log("\n服务地址:")
    log("  📹 视频流: http://192.168.0.2:8082/camera")
    log("  🔌 ROS:    ws://192.168.0.2:9090")
    log("  📡 超声波: /wave_length (ROS Topic)")
    log("  🎮 控制:   /stm32_cmd, /stm32_result, /stm32_status")
    
    log("\n日志文件:")
    for key, config in SERVICES.items():
        log(f"  {config['name']}: {config['log_file']}")
    
    log("\n按 Ctrl+C 停止所有服务")
    log("或运行: python3 start_all_services.py stop")
    
    # 保持运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log("\n收到中断信号，正在停止服务...")
        stop_all_services()
    
    return 0 if all_success else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        log(f"发生错误: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
