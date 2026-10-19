#!/usr/bin/env python3
"""
STM32串口控制器
负责与STM32F103C8T6的串口通信
"""

import serial
import threading
import time
from config import SERIAL_CONFIG, cmd_map
from mock_stm32 import create_mock_serial


class STM32Controller:
    """STM32串口控制器 - 线程安全"""
    
    def __init__(self, mock_mode=False):
        self.serial = None
        self.lock = threading.Lock()
        self.connected = False
        self.current_command = None
        self.last_error = None
        self.mock_mode = mock_mode  # 模拟模式
        
    def connect(self):
        """连接串口（或模拟串口）"""
        with self.lock:
            if self.connected and self.serial:
                return True
            
            # 模拟模式
            if self.mock_mode:
                self.serial = create_mock_serial(
                    port=SERIAL_CONFIG["port"],
                    baudrate=SERIAL_CONFIG["baudrate"],
                    timeout=SERIAL_CONFIG["timeout"],
                    write_timeout=SERIAL_CONFIG["write_timeout"]
                )
                self.connected = True
                self.last_error = None
                print("[STM32] 模拟模式已启动")
                return True
            
            # 真实串口模式
            try:
                self.serial = serial.Serial(
                    port=SERIAL_CONFIG["port"],
                    baudrate=SERIAL_CONFIG["baudrate"],
                    timeout=SERIAL_CONFIG["timeout"],
                    write_timeout=SERIAL_CONFIG["write_timeout"]
                )
                self.connected = True
                self.last_error = None
                print(f"[STM32] 串口已连接: {SERIAL_CONFIG['port']}")
                return True
            except serial.SerialException as e:
                self.connected = False
                self.last_error = str(e)
                print(f"[STM32] 串口连接失败: {e}")
                return False
    
    def disconnect(self):
        """断开串口"""
        with self.lock:
            if self.serial:
                if self.mock_mode:
                    self.serial.close()
                elif self.serial.is_open:
                    self.serial.close()
            self.serial = None
            self.connected = False
            self.current_command = None
            mode_str = "[模拟]" if self.mock_mode else ""
            print(f"[STM32] {mode_str} 串口已断开")
    
    def send_raw(self, cmd_num):
        """
        发送原始命令到STM32
        cmd_num: 命令数字字符串 (如 "1", "2" 等)
        返回: (success: bool, message: str)
        """
        with self.lock:
            if not self.connected or not self.serial:
                return False, "串口未连接"
            
            try:
                # 严格按照原文档格式: (str(number) + '\n').encode('utf-8')
                data = (str(cmd_num) + '\n').encode('utf-8')
                self.serial.write(data)
                self.serial.flush()
                mode_str = "[模拟]" if self.mock_mode else ""
                return True, f"{mode_str}OK"
            except Exception as e:
                self.connected = False
                self.last_error = str(e)
                return False, f"发送失败: {e}"
    
    def send_command(self, command):
        """
        发送命令
        command: 命令名称 (如 "forward", "stop" 等)
        返回: (success: bool, message: str)
        """
        if command not in cmd_map:
            return False, f"未知命令: {command}"
        
        # 自动连接
        if not self.connected:
            if not self.connect():
                return False, "串口连接失败"
        
        cmd_num = cmd_map[command]
        success, msg = self.send_raw(cmd_num)
        
        if success:
            self.current_command = command
            print(f"[STM32] 发送命令: {command} ({cmd_num})")
        
        return success, msg
    
    def stop(self):
        """发送停止命令"""
        success, msg = self.send_command("stop")
        if success:
            self.current_command = "stop"
        return success, msg
    
    def get_status(self):
        """获取控制器状态"""
        return {
            "connected": self.connected,
            "mock_mode": self.mock_mode,
            "port": SERIAL_CONFIG["port"] if self.connected else None,
            "baudrate": SERIAL_CONFIG["baudrate"] if self.connected else None,
            "current_command": self.current_command,
            "last_error": self.last_error
        }


class AutoStopManager:
    """自动停止管理器 - 用于duration > 0的命令"""
    
    def __init__(self, controller):
        self.controller = controller
        self.timer = None
        self.lock = threading.Lock()
    
    def schedule_stop(self, duration):
        """调度自动停止"""
        with self.lock:
            # 取消之前的定时器
            if self.timer:
                self.timer.cancel()
            
            if duration > 0:
                self.timer = threading.Timer(duration, self._do_stop)
                self.timer.daemon = True
                self.timer.start()
                print(f"[AutoStop] 已调度 {duration}秒后自动停止")
    
    def cancel(self):
        """取消自动停止"""
        with self.lock:
            if self.timer:
                self.timer.cancel()
                self.timer = None
    
    def _do_stop(self):
        """执行停止"""
        print("[AutoStop] 执行自动停止")
        self.controller.stop()
