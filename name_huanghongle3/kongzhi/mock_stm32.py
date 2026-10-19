#!/usr/bin/env python3
"""
模拟STM32 - 假机器人
用于前端测试，不依赖真实硬件
打印接收到的命令，模拟真实响应
"""

import time
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/mock_stm32.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('MockSTM32')


class MockSerial:
    """模拟串口对象"""
    
    def __init__(self, port, baudrate, timeout, write_timeout):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._is_open = True
        msg = f"[MockSTM32] 模拟串口已打开: {port}, 波特率 {baudrate}"
        print(msg)
        logger.info(msg)
    
    def is_open(self):
        return self._is_open
    
    def write(self, data):
        """模拟写入数据"""
        cmd = data.decode('utf-8').strip()
        self._print_command(cmd)
        return len(data)
    
    def flush(self):
        """模拟刷新"""
        pass
    
    def close(self):
        """模拟关闭"""
        self._is_open = False
        msg = "[MockSTM32] 模拟串口已关闭"
        print(msg)
        logger.info(msg)
    
    def _print_command(self, cmd_num):
        """打印命令信息"""
        cmd_map = {
            "1": "停止 (STOP)",
            "2": "前进 (FORWARD)",
            "3": "后退 (BACKWARD)",
            "4": "左转 (TURN_LEFT)",
            "5": "右转 (TURN_RIGHT)",
            "6": "无刷停止 (BRUSHLESS_STOP)",
            "7": "无刷中速 (BRUSHLESS_MID)"
        }
        
        desc = cmd_map.get(cmd_num, f"未知命令({cmd_num})")
        log_msg = f"[MockSTM32] 收到命令: {cmd_num} | {desc} | 原始数据: {repr(cmd_num + chr(10))}"
        print(f"\n{'='*40}")
        print(f"[MockSTM32] 收到命令: {cmd_num}")
        print(f"[MockSTM32] 命令含义: {desc}")
        print(f"[MockSTM32] 原始数据: {repr(cmd_num + chr(10))}")
        print(f"{'='*40}\n")
        logger.info(log_msg)


def create_mock_serial(port, baudrate, timeout, write_timeout):
    """创建模拟串口"""
    return MockSerial(port, baudrate, timeout, write_timeout)
