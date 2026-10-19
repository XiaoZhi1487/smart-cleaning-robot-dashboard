#!/usr/bin/env python3
"""
Jetson端配置文件
"""

# 串口配置
SERIAL_CONFIG = {
    "port": "/dev/ttyACM3",
    "baudrate": 115200,
    "timeout": 1,
    "write_timeout": 1
}

# 服务器配置
SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": False
}

# 心跳配置
HEARTBEAT_CONFIG = {
    "interval_ms": 100,      # 前端心跳间隔100ms
    "timeout_ms": 500,       # 后端超时500ms自动停止
    "stop_delay_ms": 100     # 超时后延迟停止时间
}

# STM32命令映射
cmd_map = {
    "stop": "1",
    "forward": "2",
    "backward": "3",
    "turn_left": "4",
    "turn_right": "5",
    "brushless_stop": "6",
    "brushless_mid": "7"
}
