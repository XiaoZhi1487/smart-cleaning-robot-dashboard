#!/usr/bin/env python3
"""
停止所有 Jetson 服务
用于清理残留进程
"""

import subprocess
import time
import sys
import os
import signal

print("="*60)
print("停止所有 Jetson 服务")
print("="*60)

services = [
    ("相机", ["gemini_330_series", "component_container", "orbbec_camera"]),
    ("HTTP 服务器", ["camera_http_node"]),
    ("ROS Bridge", ["rosbridge_websocket"]),
    ("超声波", ["wave_length_node"]),
]

for name, patterns in services:
    print(f"\n停止 {name}...")
    for pattern in patterns:
        try:
            result = subprocess.run(
                ["pkill", "-9", "-f", pattern],
                capture_output=True
            )
        except:
            pass
    time.sleep(0.5)

print("\n✓ 所有服务已停止")
print("\n验证:")

# 验证
for name, patterns in services:
    try:
        result = subprocess.run(
            ["pgrep", "-f", patterns[0]],
            capture_output=True
        )
        if result.returncode == 0:
            print(f"  ⚠️ {name} 仍有残留进程")
        else:
            print(f"  ✓ {name} 已清理")
    except:
        print(f"  ? {name} 状态未知")

print("\n可以重新启动服务了")
