#!/usr/bin/env python3
"""
机器人服务管理器 - 交互式版本
支持选择性启动/停止服务，防止冲突和资源耗尽

作者: Jetson Engineer
日期: 2026-03-09
版本: 2.0
"""

import subprocess
import time
import sys
import os
import signal
import psutil
from datetime import datetime

# 颜色输出
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def log(msg, level="INFO"):
    """打印带时间戳的日志"""
    now = datetime.now().strftime("%H:%M:%S")
    color = {
        "INFO": Colors.BLUE,
        "OK": Colors.GREEN,
        "ERROR": Colors.RED,
        "WARN": Colors.YELLOW,
        "CYAN": Colors.CYAN
    }.get(level, Colors.BLUE)
    print(f"{color}[{now}] [{level}] {msg}{Colors.END}")

# ==================== 服务配置 ====================
# 编号: [名称, 进程标识, 端口, 话题, 启动命令, 工作目录, 日志文件, 启动延迟]
SERVICES = {
    1: {
        "name": "ROS Bridge (WebSocket桥接)",
        "id": "rosbridge",
        "process_patterns": ["rosbridge_websocket"],
        "port": 9090,
        "topic": None,
        "launch_cmd": ["ros2", "launch", "rosbridge_server", "rosbridge_websocket_launch.xml"],
        "work_dir": None,
        "log_file": "/tmp/rosbridge.log",
        "delay": 3,
        "description": "前端WebSocket连接必需"
    },
    2: {
        "name": "Orbbec相机 (图像采集)",
        "id": "camera",
        "process_patterns": ["gemini_330_series", "component_container", "orbbec_camera"],
        "port": None,
        "topic": "/camera/color/image_raw",
        "launch_cmd": [
            "ros2", "launch", "orbbec_camera", "gemini_330_series.launch.py",
            "color_width:=1280", "color_height:=720", "color_fps:=30",
            "enable_depth:=true", "enable_point_cloud:=false", "enable_left_ir:=true", "enable_right_ir:=false", "depth_width:=640", "depth_height:=400", "depth_fps:=10", "left_ir_width:=640", "left_ir_height:=400", "left_ir_fps:=10", "right_ir_width:=640", "right_ir_height:=400", "right_ir_fps:=10"
        ],
        "work_dir": None,
        "log_file": "/tmp/camera.log",
        "delay": 15,
        "description": "视频流数据源"
    },
    3: {
        "name": "HTTP视频流 (MJPEG服务器)",
        "id": "http_stream",
        "process_patterns": ["camera_http_node"],
        "port": 8082,
        "topic": None,
        "launch_cmd": None,  # 特殊处理
        "work_dir": "/home/nvidia/name_huanghongle3/camera_http_ws",
        "log_file": "/tmp/http_server.log",
        "delay": 3,
        "description": "前端<img>标签直接访问"
    },
    4: {
        "name": "STM32控制 (机器人控制)",
        "id": "stm32_control",
        "process_patterns": ["stm32_control_node"],
        "port": None,
        "topic": "/stm32_cmd",
        "launch_cmd": None,  # 特殊处理
        "work_dir": "/home/nvidia/name_zhoushifei/WS",
        "log_file": "/tmp/stm32_control.log",
        "delay": 3,
        "description": "控制指令转发到STM32"
    },
    5: {
        "name": "超声波传感器 (距离检测)",
        "id": "ultrasonic",
        "process_patterns": ["wave_length_node"],
        "port": None,
        "topic": "/wave_length",
        "launch_cmd": None,  # 特殊处理
        "work_dir": "/home/nvidia/name_ranhongmei/ws",
        "log_file": "/tmp/ultrasonic.log",
        "delay": 3,
        "description": "3路超声波距离数据"
    },
    6: {
        "name": "定位节点 (位置计算)",
        "id": "localization",
        "process_patterns": ["curtain_wall_nav_node"],
        "port": None,
        "topic": "/ultrasonic_position",
        "launch_cmd": None,  # 特殊处理
        "work_dir": "/home/nvidia/name_huangguozhou/ws",
        "log_file": "/tmp/localization.log",
        "delay": 3,
        "description": "基于超声波的定位计算"
    }
}

# 依赖关系: 服务 -> 依赖的服务编号
DEPENDENCIES = {
    3: [2],      # HTTP视频流依赖相机
    4: [1],      # STM32控制依赖ROS Bridge
    5: [1],      # 超声波依赖ROS Bridge
    6: [1, 5],   # 定位节点依赖ROS Bridge和超声波
}

# ==================== 工具函数 ====================

def get_service_status(service_id):
    """获取服务状态"""
    config = SERVICES[service_id]
    
    # 检查进程
    procs = find_processes(config["process_patterns"])
    process_running = len(procs) > 0
    
    # 检查端口
    port_listening = False
    if config["port"]:
        port_listening = check_port(config["port"])
    
    # 检查话题
    topic_available = False
    if config["topic"]:
        topic_available = check_topic_quick(config["topic"])
    
    # 综合状态
    if process_running:
        if config["port"] and not port_listening:
            return "异常", "进程在但端口未监听"
        if config["topic"] and not topic_available:
            return "启动中", "进程在但话题未就绪"
        return "运行中", f"PID: {procs[0].pid if procs else 'N/A'}"
    else:
        return "已停止", ""

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

def check_port(port):
    """检查端口是否被监听"""
    for conn in psutil.net_connections():
        if conn.laddr.port == port:
            return True
    return False

def check_topic_quick(topic):
    """快速检查话题是否存在"""
    try:
        result = subprocess.run(
            ["ros2", "topic", "list"],
            capture_output=True, text=True, timeout=2
        )
        return topic in result.stdout
    except:
        return False

def get_system_resources():
    """获取系统资源使用情况"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    return {
        "cpu": cpu_percent,
        "memory": memory.percent,
        "available_memory": memory.available / (1024**3)  # GB
    }

def kill_service(service_id, show_log=True):
    """停止指定服务"""
    config = SERVICES[service_id]
    if show_log:
        log(f"正在停止: {config['name']}", "INFO")
    
    procs = find_processes(config["process_patterns"])
    if not procs:
        if show_log:
            log(f"  服务未运行", "WARN")
        return True
    
    for proc in procs:
        try:
            proc.terminate()
            proc.wait(timeout=3)
            if show_log:
                log(f"  已停止 PID {proc.pid}", "OK")
        except psutil.TimeoutExpired:
            proc.kill()
            proc.wait()
            if show_log:
                log(f"  强制停止 PID {proc.pid}", "WARN")
        except Exception as e:
            if show_log:
                log(f"  停止失败: {e}", "ERROR")
            return False
    
    return True

def start_service_single(service_id, auto_deps=True):
    """启动单个服务"""
    config = SERVICES[service_id]
    
    log(f"\n{'='*60}")
    log(f"启动服务 [{service_id}]: {config['name']}")
    log(f"{'='*60}")
    
    # 1. 检查是否已运行
    status, info = get_service_status(service_id)
    if status == "运行中":
        log(f"⚠️  服务已在运行! ({info})", "WARN")
        log(f"如需重启，请先停止该服务", "WARN")
        return True
    
    # 2. 检查依赖
    if auto_deps and service_id in DEPENDENCIES:
        deps = DEPENDENCIES[service_id]
        log(f"检查依赖服务: {[SERVICES[d]['name'] for d in deps]}")
        for dep_id in deps:
            dep_status, _ = get_service_status(dep_id)
            if dep_status != "运行中":
                log(f"依赖服务 [{dep_id}] 未运行，自动启动...", "WARN")
                if not start_service_single(dep_id, auto_deps=False):
                    log(f"依赖服务启动失败，中止", "ERROR")
                    return False
    
    # 3. 资源检查
    resources = get_system_resources()
    if resources["memory"] > 90:
        log(f"⚠️  内存使用率过高 ({resources['memory']:.1f}%)!", "WARN")
        log(f"可用内存: {resources['available_memory']:.1f} GB", "WARN")
        response = input("内存不足，是否继续启动? (y/n): ")
        if response.lower() != 'y':
            return False
    
    # 4. 启动服务
    log(f"正在启动...")
    
    env = os.environ.copy()
    env['PYTHONUNBUFFERED'] = '1'
    env['ROS_DOMAIN_ID'] = '30'
    
    try:
        if config["id"] == "http_stream":
            # HTTP视频流特殊启动（用 python3 直接运行源码，绕过 ament 可执行索引缺失导致的 ros2 run "No executable found"）
            cmd = f"""
            cd {config['work_dir']} &&
            source /opt/ros/humble/setup.bash &&
            source install/setup.bash &&
            python3 src/camera_http/camera_http/camera_http_node.py
            """
            process = subprocess.Popen(
                cmd, shell=True, executable='/bin/bash',
                stdout=open(config['log_file'], 'w'),
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid,
                env=env
            )
        elif config["id"] == "stm32_control":
            # STM32控制特殊启动
            cmd = f"""
            cd {config['work_dir']} &&
            source /opt/ros/humble/setup.bash &&
            source install/setup.bash &&
            ros2 run stm32_control stm32_control_node
            """
            process = subprocess.Popen(
                cmd, shell=True, executable='/bin/bash',
                stdout=open(config['log_file'], 'w'),
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid,
                env=env
            )
        elif config["id"] == "ultrasonic":
            # 超声波特殊启动
            cmd = f"""
            cd {config['work_dir']} &&
            source /opt/ros/humble/setup.bash &&
            source install/setup.bash &&
            ros2 run fist_demo_uart wave_length_node
            """
            process = subprocess.Popen(
                cmd, shell=True, executable='/bin/bash',
                stdout=open(config['log_file'], 'w'),
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid,
                env=env
            )
        elif config["id"] == "localization":
            # 定位节点特殊启动
            cmd = f"""
            cd {config['work_dir']} &&
            source /opt/ros/humble/setup.bash &&
            source install/setup.bash &&
            ros2 run fist_demo_uart curtain_wall_nav_node
            """
            process = subprocess.Popen(
                cmd, shell=True, executable='/bin/bash',
                stdout=open(config['log_file'], 'w'),
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid,
                env=env
            )
        else:
            # 标准ROS launch
            process = subprocess.Popen(
                config["launch_cmd"],
                stdout=open(config['log_file'], 'w'),
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid,
                env=env
            )
        
        # 5. 等待初始化
        log(f"等待 {config['delay']} 秒初始化...")
        time.sleep(config['delay'])
        
        # 6. 验证启动
        status, info = get_service_status(service_id)
        if status == "运行中":
            log(f"✅ 启动成功! ({info})", "OK")
            if config["port"]:
                log(f"   端口: {config['port']}")
            if config["topic"]:
                log(f"   话题: {config['topic']}")
            return True
        else:
            log(f"❌ 启动失败或异常 ({status}: {info})", "ERROR")
            log(f"   查看日志: {config['log_file']}")
            return False
            
    except Exception as e:
        log(f"❌ 启动异常: {e}", "ERROR")
        return False

# ==================== 菜单功能 ====================

def show_main_menu():
    """显示主菜单"""
    print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}         机器人服务管理器 - 主菜单{Colors.END}")
    print(f"{Colors.BOLD}{'='*70}{Colors.END}")
    print()
    
    # 显示所有服务状态
    print(f"{Colors.CYAN}当前服务状态:{Colors.END}")
    print(f"{'编号':<4} {'服务名称':<30} {'状态':<12} {'信息'}")
    print("-" * 70)
    
    for id, config in SERVICES.items():
        status, info = get_service_status(id)
        status_color = Colors.GREEN if status == "运行中" else (
            Colors.YELLOW if status == "启动中" else (
                Colors.RED if status == "异常" else Colors.BLUE
            )
        )
        print(f"{id:<4} {config['name']:<30} {status_color}{status:<12}{Colors.END} {info}")
    
    print()
    
    # 系统资源
    resources = get_system_resources()
    mem_color = Colors.GREEN if resources["memory"] < 70 else (
        Colors.YELLOW if resources["memory"] < 85 else Colors.RED
    )
    print(f"系统资源: CPU {resources['cpu']:.1f}% | "
          f"内存 {mem_color}{resources['memory']:.1f}%{Colors.END} | "
          f"可用 {resources['available_memory']:.1f}GB")
    
    print()
    print(f"{Colors.CYAN}操作选项:{Colors.END}")
    print("  [1-6]    启动/停止对应编号的服务")
    print("  [s1-s6]  仅启动服务 (如: s3 启动HTTP视频流)")
    print("  [k1-k6]  仅停止服务 (如: k4 停止STM32控制)")
    print("  [a]      启动所有服务")
    print("  [o]      停止所有服务")
    print("  [r]      重启所有服务")
    print("  [l]      查看日志")
    print("  [q]      退出")
    print()

def show_logs():
    """查看日志菜单"""
    print(f"\n{Colors.CYAN}选择要查看的日志:{Colors.END}")
    for id, config in SERVICES.items():
        print(f"  [{id}] {config['name']}")
    print("  [0] 返回")
    
    choice = input("\n输入编号: ").strip()
    if choice.isdigit() and int(choice) in SERVICES:
        config = SERVICES[int(choice)]
        log_file = config["log_file"]
        print(f"\n{Colors.CYAN}=== {config['name']} 日志 (最后20行) ==={Colors.END}")
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                print(''.join(lines[-20:]))
        except:
            print("日志文件不存在或无法读取")
        input("\n按回车继续...")

def start_all_services():
    """启动所有服务"""
    log("\n启动所有服务...", "INFO")
    
    # 按依赖顺序启动
    start_order = [1, 2, 3, 4, 5, 6]  # 合理的启动顺序
    
    success_count = 0
    for service_id in start_order:
        if start_service_single(service_id, auto_deps=False):
            success_count += 1
    
    log(f"\n{'='*60}")
    log(f"启动完成: {success_count}/{len(start_order)} 个服务成功", 
        "OK" if success_count == len(start_order) else "WARN")
    show_service_summary()

def stop_all_services():
    """停止所有服务"""
    log("\n停止所有服务...", "INFO")
    
    # 反向停止
    stop_order = [6, 5, 4, 3, 2, 1]
    
    for service_id in stop_order:
        kill_service(service_id)
    
    log("\n所有服务已停止", "OK")

def restart_all_services():
    """重启所有服务"""
    stop_all_services()
    time.sleep(2)
    start_all_services()

def show_service_summary():
    """显示服务摘要"""
    print(f"\n{Colors.CYAN}服务访问信息:{Colors.END}")
    print(f"  📹 视频流: http://192.168.0.2:8082/camera")
    print(f"  🔌 ROS Bridge: ws://192.168.0.2:9090")
    print(f"  📡 ROS话题:")
    print(f"     - /camera/color/image_raw (相机图像)")
    print(f"     - /wave_length (超声波数据)")
    print(f"     - /ultrasonic_position (定位数据)")
    print(f"     - /stm32_cmd (控制指令输入)")
    print(f"     - /stm32_result (执行结果)")
    print(f"     - /stm32_status (在线状态)")
    print()
    print(f"{Colors.CYAN}日志文件位置:{Colors.END}")
    for id, config in SERVICES.items():
        print(f"  [{id}] {config['log_file']}")

def main():
    """主函数"""
    # 设置ROS环境
    os.environ['ROS_DOMAIN_ID'] = '30'
    
    while True:
        show_main_menu()
        choice = input(f"{Colors.BOLD}请输入操作: {Colors.END}").strip().lower()
        
        if choice == 'q':
            print("再见!")
            break
        
        elif choice == 'a':
            start_all_services()
            input("\n按回车继续...")
        
        elif choice == 'o':
            stop_all_services()
            input("\n按回车继续...")
        
        elif choice == 'r':
            restart_all_services()
            input("\n按回车继续...")
        
        elif choice == 'l':
            show_logs()
        
        elif choice.startswith('s') and choice[1:].isdigit():
            # 启动指定服务 s1, s2, ...
            service_id = int(choice[1:])
            if service_id in SERVICES:
                start_service_single(service_id)
                input("\n按回车继续...")
            else:
                log("无效的服务编号", "ERROR")
        
        elif choice.startswith('k') and choice[1:].isdigit():
            # 停止指定服务 k1, k2, ...
            service_id = int(choice[1:])
            if service_id in SERVICES:
                kill_service(service_id)
                input("\n按回车继续...")
            else:
                log("无效的服务编号", "ERROR")
        
        elif choice.isdigit() and int(choice) in SERVICES:
            # 切换服务状态
            service_id = int(choice)
            status, _ = get_service_status(service_id)
            
            if status == "运行中":
                confirm = input(f"服务已在运行，是否停止? (y/n): ")
                if confirm.lower() == 'y':
                    kill_service(service_id)
            else:
                start_service_single(service_id)
            
            input("\n按回车继续...")
        
        else:
            log("无效的操作", "ERROR")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(0)
    except Exception as e:
        log(f"发生错误: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        sys.exit(1)
