# 幕墙清洗机器人控制系统 - 技术实现详解

> **更新到最新版**：相机已启用深度/点云/双目红外（640x400@10fps）；HTTP 视频节点升级为 /camera、/depth、/ir 三路 MJPEG 流（前端 `<img>` 直连，不经过 rosbridge）；推荐使用交互式管理器 `robot_service_manager.py`（v2.0）。

> **文档目的**: 详细记录前后端通讯架构、ROS2 节点封装原理、数据流设计
> 
> **核心设计理念**:
> - 视频流使用 **HTTP/MJPEG** - 降低带宽压力，浏览器原生支持
> - 控制/传感器使用 **WebSocket/ROS** - 降低延迟，实时双向通信

---

## 目录

1. [系统架构总览](#1-系统架构总览)
2. [通讯协议选择与对比](#2-通讯协议选择与对比)
3. [STM32 控制节点封装详解](#3-stm32-控制节点封装详解)
4. [ROS Bridge 启动全流程](#4-ros-bridge-启动全流程)
5. [视频流实现 (HTTP/MJPEG)](#5-视频流实现-httpmjpeg)
6. [传感器数据实现 (WebSocket/ROS)](#6-传感器数据实现-websocketros)
7. [前端对接指南](#7-前端对接指南)
8. [故障排查手册](#8-故障排查手册)

---

## 1. 系统架构总览

### 1.1 三层架构模型

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              表示层 (Presentation)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   视频显示   │  │   控制面板   │  │  传感器仪表  │  │   状态监控   │        │
│  │  <img>标签  │  │    按钮组    │  │   实时图表   │  │   连接状态   │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
└─────────┼────────────────┼────────────────┼────────────────┼────────────────┘
          │                │                │                │
          │ HTTP/MJPEG     │   WebSocket    │   WebSocket    │   WebSocket
          │ (端口8082)     │   (端口9090)   │   (端口9090)   │   (端口9090)
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              服务层 (Service)                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  HTTP Server    │  │  rosbridge_server│  │  ROS2 Node      │             │
│  │  (MJPEG Stream) │  │  (WebSocket Bridge)│  │  (Various)      │             │
│  │                 │  │                  │  │                  │             │
│  │  输入: ROS Topic │  │  输入: WebSocket │  │  输入: 硬件设备   │             │
│  │  输出: HTTP流   │  │  输出: ROS Topic │  │  输出: ROS Topic │             │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘             │
└───────────┼────────────────────┼────────────────────┼────────────────────────┘
            │                    │                    │
            │ ROS Topic          │                    │ ROS Topic
            ▼                    │                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              数据层 (Data)                                   │
│  ┌─────────────────┐                         ┌─────────────────┐           │
│  │   /camera/color │◄───────────────────────►│   相机驱动       │           │
│  │   /image_raw    │                         │   (Orbbec)      │           │
│  └─────────────────┘                         └─────────────────┘           │
│  ┌─────────────────┐                         ┌─────────────────┐           │
│  │   /stm32_cmd    │◄───────────────────────►│   STM32控制     │           │
│  │   /stm32_result │                         │   (串口通信)     │           │
│  └─────────────────┘                         └─────────────────┘           │
│  ┌─────────────────┐                         ┌─────────────────┐           │
│  │   /wave_length  │◄───────────────────────►│   超声波模组     │           │
│  │   /ultrasonic_  │                         │   (UART)        │           │
│  │   position      │                         └─────────────────┘           │
│  └─────────────────┘                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 数据流向图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              控制指令流向                                    │
└─────────────────────────────────────────────────────────────────────────────┘

前端点击"前进"按钮
        │
        │ 1. WebSocket 发送 JSON
        │    { "op": "publish", "topic": "/stm32_cmd", "msg": { "data": 3 } }
        ▼
┌───────────────┐
│ rosbridge_server│
│   :9090       │  2. 协议转换: JSON → ROS Message
└───────┬───────┘
        │
        │ 3. ROS Topic 发布
        ▼
┌───────────────┐
│ stm32_control │
│   _node       │  4. 接收 Int32 消息
└───────┬───────┘
        │
        │ 5. 串口发送 ASCII
        │    "3\n"
        ▼
┌───────────────┐
│     STM32     │  6. 解析指令，驱动电机
└───────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                              传感器数据流向                                  │
└─────────────────────────────────────────────────────────────────────────────┘

超声波模组
        │
        │ 1. UART 发送原始数据
        │    [帧头, 距离高字节, 距离低字节, ...]
        ▼
┌───────────────┐
│ wave_length   │
│   _node       │  2. 解析数据，组装 ROS Message
└───────┬───────┘
        │
        │ 3. ROS Topic 发布
        │    /wave_length (UInt8MultiArray)
        ▼
┌───────────────┐
│ rosbridge_server│
│   :9090       │  4. 协议转换: ROS Message → JSON
└───────┬───────┘
        │
        │ 5. WebSocket 推送
        │    { "data": [1200, 800, 950, 0, 0, 0, 0, 0] }
        ▼
┌───────────────┐
│     前端       │  6. 解析并显示距离值
└───────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                              视频流向                                        │
└─────────────────────────────────────────────────────────────────────────────┘

Orbbec 相机
        │
        │ 1. USB3.0 传输原始图像
        ▼
┌───────────────┐
│ orbbec_camera │
│   _node       │  2. 发布 ROS Image 消息
└───────┬───────┘
        │
        │ 3. ROS Topic 订阅
        │    /camera/color/image_raw
        ▼
┌───────────────┐
│ camera_http   │
│   _node       │  4. 图像编码为 JPEG
│               │    resize: 1280x720
│               │    quality: 80%
└───────┬───────┘
        │
        │ 5. HTTP MJPEG Stream
        │    Content-Type: multipart/x-mixed-replace
        ▼
┌───────────────┐
│     前端       │  6. <img> 标签直接显示
│  <img src=...>│    浏览器自动处理缓冲和解码
└───────────────┘
```

---

## 2. 通讯协议选择与对比

### 2.1 为什么必须采用混合架构？

| 考量因素 | 视频流 | 控制指令 | 传感器数据 |
|---------|:------:|:--------:|:----------:|
| **数据量** | 大 (MB/s) | 小 (字节) | 小 (字节) |
| **实时性要求** | 中 (100-500ms) | 高 (<50ms) | 高 (<100ms) |
| **传输方向** | 单向 (下行为主) | 双向 | 单向 (上行为主) |
| **浏览器支持** | 原生 <img> | 需 WebSocket | 需 WebSocket |
| **带宽压力** | 需优化 | 可忽略 | 可忽略 |

### 2.2 三种协议详细对比

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        协议对比表                                            │
├──────────────┬──────────────┬──────────────┬──────────────┬────────────────┤
│    特性      │  HTTP REST   │  WebSocket   │  HTTP/MJPEG  │    ROS2 Topic  │
├──────────────┼──────────────┼──────────────┼──────────────┼────────────────┤
│  连接方式    │   短连接     │   长连接     │   长连接     │   进程间通信   │
│  头部开销    │    大        │    小        │    中        │     无         │
│  服务器推送  │    不支持    │    支持      │    支持      │     支持       │
│  延迟        │   50-200ms   │    <10ms     │   50-100ms   │     <1ms       │
│  并发处理    │    弱        │    强        │    中        │     强         │
│  浏览器支持  │    原生      │    需库      │    原生      │    需桥接      │
│  适用场景    │   API调用    │  实时双向    │  视频流传输  │   机器人内部   │
└──────────────┴──────────────┴──────────────┴──────────────┴────────────────┘
```

### 2.3 本项目协议选择原理

#### 视频流 → HTTP/MJPEG

```
优势分析:
┌────────────────────────────────────────────────────────────────┐
│ 1. 带宽优化                                                     │
│    • MJPEG 只传输帧间变化小的 JPEG 图像                         │
│    • 相比原始视频流，压缩率可达 10:1 ~ 50:1                    │
│    • 1280x720@10fps 原始: ~265 Mbps                            │
│    • 1280x720@10fps MJPEG: ~2-4 Mbps (质量80%)                 │
│                                                                │
│ 2. 浏览器原生支持                                               │
│    • <img src="http://..."> 直接渲染                           │
│    • 自动处理分包、缓冲、解码                                   │
│    • 无需额外 JavaScript 库 (节省 ~100KB)                      │
│                                                                │
│ 3. 与 ROS 解耦                                                  │
│    • HTTP 服务独立运行，不依赖 ROS 网络                         │
│    • 前端可直接访问，无需 roslibjs                             │
│    • 即使 ROS 故障，视频仍可查看                                │
└────────────────────────────────────────────────────────────────┘

劣势及解决方案:
┌────────────────────────────────────────────────────────────────┐
│ • 单向传输 (无法通过视频流发送控制指令)                         │
│   → 解决方案: 控制指令走单独的 WebSocket 连接                   │
│                                                                │
│ • 延迟较高 (50-100ms)                                          │
│   → 解决方案: 降低分辨率/帧率，或改用 WebRTC (未来优化)         │
│                                                                │
│ • 连接断开需手动重连                                           │
│   → 解决方案: 前端添加 onerror 事件自动重连                     │
└────────────────────────────────────────────────────────────────┘
```

#### 控制/传感器 → WebSocket/ROS

```
优势分析:
┌────────────────────────────────────────────────────────────────┐
│ 1. 实时性                                                       │
│    • WebSocket 长连接，无需每次建立 TCP 握手                    │
│    • 控制指令延迟 < 10ms (实测)                                │
│    • 传感器数据实时推送，无需轮询                               │
│                                                                │
│ 2. 双向通信                                                     │
│    • 同一条连接既可发送控制，也可接收状态                       │
│    • 支持请求-响应模式 (可确认指令执行结果)                     │
│                                                                │
│ 3. ROS 生态集成                                                 │
│    • 直接使用 ROS 话题机制，标准统一                            │
│    • 便于扩展新的传感器或执行器                                 │
│    • 可利用 ROS 的录制、回放、调试工具                          │
└────────────────────────────────────────────────────────────────┘

劣势及解决方案:
┌────────────────────────────────────────────────────────────────┐
│ • 需引入 roslibjs 库 (~100KB)                                  │
│   → 解决方案: 使用 CDN 加载，或本地缓存                         │
│                                                                │
│ • 需理解 ROS 概念 (Topic/Message)                              │
│   → 解决方案: 提供封装好的 API 层，前端无需关心底层             │
│                                                                │
│ • 依赖 rosbridge_server 运行                                   │
│   → 解决方案: 监控连接状态，断线时提示用户                      │
└────────────────────────────────────────────────────────────────┘
```

---

## 3. STM32 控制节点封装详解

### 3.1 原始程序分析

**原始文件**: `com_with_stm.py`

```python
#!/usr/bin/env python3
"""
原始 STM32 串口控制程序
功能: 手动输入数字指令，通过串口发送给 STM32
"""

import serial

# 串口配置 (硬编码)
PORT = "/dev/ttyACM3"
BAUD = 115200

# 指令映射 (通过注释说明)
# 1 = 停止
# 2 = 前进
# 3 = 后退
# 4 = 左转
# 5 = 右转
# 6 = 无刷停止
# 7 = 无刷中速

ser = serial.Serial(PORT, BAUD, timeout=1)

while True:
    user_input = input("请输入数字: ")
    if user_input == 'exit':
        break
    ser.write(f"{user_input}\n".encode('utf-8'))

ser.close()
```

**存在的问题**:
1. ❌ 无法与 ROS 系统集成
2. ❌ 前端无法直接调用
3. ❌ 无反馈机制，不知道指令是否执行成功
4. ❌ 无状态监控，不知道 STM32 是否在线
5. ❌ 硬编码配置，不灵活

### 3.2 封装设计思路

```
封装目标:
┌────────────────────────────────────────────────────────────────┐
│ 1. ROS2 节点化                                                  │
│    • 继承 rclpy.node.Node                                       │
│    • 使用 ROS 参数系统管理配置                                  │
│    • 使用 ROS 日志系统记录信息                                  │
│                                                                │
│ 2. WebSocket 接口                                               │
│    • 通过 rosbridge_server 暴露为 WebSocket 服务               │
│    • 前端可直接订阅/发布 ROS 话题                               │
│                                                                │
│ 3. 双向通信                                                     │
│    • 订阅 /stm32_cmd 接收控制指令                              │
│    • 发布 /stm32_result 反馈执行结果                           │
│    • 发布 /stm32_status 心跳状态                               │
│                                                                │
│ 4. 容错处理                                                     │
│    • 串口断开自动重连                                           │
│    • 指令验证，防止非法值                                       │
│    • 异常捕获，不导致节点崩溃                                   │
└────────────────────────────────────────────────────────────────┘
```

### 3.3 完整封装代码

```python
#!/usr/bin/env python3
"""
STM32 控制节点 - ROS2 封装实现
路径: /home/nvidia/name_zhoushifei/WS/src/stm32_control/stm32_control/stm32_control_node.py

功能:
    1. 订阅 ROS Topic /stm32_cmd 接收前端控制指令
    2. 通过串口 /dev/ttyACM3 发送指令给 STM32
    3. 发布 /stm32_result 反馈执行结果
    4. 发布 /stm32_status 节点在线状态(1Hz)

通讯协议:
    - ROS Topic: std_msgs/Int32 (指令), std_msgs/String (反馈)
    - 串口: ASCII 文本, 格式 "{数字}\n", 波特率 115200
    
指令映射:
    1 = 停止
    2 = 后退 (注: 硬件接线反向，软件层保持与前端一致)
    3 = 前进
    4 = 左转
    5 = 右转
    6 = 无刷停止
    7 = 无刷中速
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, String
import serial
import threading


class STM32ControlNode(Node):
    """
    STM32 控制节点类
    
    继承自 rclpy.node.Node，实现 ROS2 标准节点接口
    """
    
    def __init__(self):
        """
        节点初始化
        
        步骤:
            1. 调用父类构造函数，设置节点名称
            2. 声明 ROS 参数 (可运行时配置)
            3. 初始化串口连接
            4. 创建 ROS 订阅者和发布者
            5. 创建定时器
        """
        # 1. 调用父类构造函数
        # 参数: 节点名称，用于 ROS 网络标识
        super().__init__('stm32_control_node')
        
        # 2. 声明 ROS 参数
        # 优点: 可在 launch 文件或命令行覆盖，无需修改代码
        self.declare_parameter('port_name', '/dev/ttyACM3')
        self.declare_parameter('baud_rate', 115200)
        self.declare_parameter('status_publish_rate', 1.0)  # Hz
        
        # 获取参数值
        self.port_name = self.get_parameter('port_name').value
        self.baud_rate = self.get_parameter('baud_rate').value
        
        # 3. 指令映射表
        # 将数字指令映射为可读名称，用于日志和反馈
        self.cmd_names = {
            1: '停止',
            2: '后退',      # 注意: 实际硬件可能是前进，前端显示为"后退"
            3: '前进',      # 注意: 实际硬件可能是后退，前端显示为"前进"
            4: '左转',
            5: '右转',
            6: '无刷停止',
            7: '无刷中速'
        }
        
        # 4. 串口连接 (复用原始代码逻辑)
        self.ser = None
        self.connect_serial()
        
        # 5. 创建 ROS 订阅者 (输入)
        # QoS (Quality of Service): depth=10 表示队列深度为10
        self.cmd_subscription = self.create_subscription(
            Int32,                      # 消息类型
            '/stm32_cmd',               # 话题名称
            self.cmd_callback,          # 回调函数
            10                          # QoS 队列深度
        )
        
        # 6. 创建 ROS 发布者 (输出)
        self.result_publisher = self.create_publisher(
            String,
            '/stm32_result',
            10
        )
        
        self.status_publisher = self.create_publisher(
            String,
            '/stm32_status',
            10
        )
        
        # 7. 创建定时器 (1Hz 发布状态)
        status_rate = self.get_parameter('status_publish_rate').value
        self.status_timer = self.create_timer(1.0 / status_rate, self.publish_status)
        
        # 8. 节点启动日志
        self.get_logger().info('=' * 50)
        self.get_logger().info('STM32 控制节点已启动')
        self.get_logger().info(f'串口: {self.port_name}')
        self.get_logger().info(f'波特率: {self.baud_rate}')
        self.get_logger().info('订阅话题: /stm32_cmd')
        self.get_logger().info('发布话题: /stm32_result, /stm32_status')
        self.get_logger().info('=' * 50)
    
    def connect_serial(self):
        """
        连接串口
        
        复用原始 com_with_stm.py 的串口连接逻辑
        添加异常处理，防止程序崩溃
        """
        try:
            self.ser = serial.Serial(
                port=self.port_name,
                baudrate=self.baud_rate,
                timeout=1,              # 读取超时1秒
                write_timeout=1         # 写入超时1秒
            )
            self.get_logger().info(f'串口 {self.port_name} 连接成功')
        except serial.SerialException as e:
            self.get_logger().error(f'串口连接失败: {e}')
            self.ser = None
    
    def cmd_callback(self, msg):
        """
        接收控制指令的回调函数
        
        这是核心处理函数，每当有前端发送指令时自动调用
        
        参数:
            msg: std_msgs/Int32 类型，data 字段包含指令值 (1-7)
        
        处理流程:
            1. 提取指令值
            2. 验证指令有效性
            3. 发送到 STM32
            4. 发布执行结果
        """
        cmd = msg.data
        
        # 步骤1: 验证指令有效性
        if cmd not in self.cmd_names:
            error_msg = f'无效指令: {cmd}'
            self.get_logger().warn(error_msg)
            self.publish_result(f'error: {error_msg}')
            return
        
        cmd_name = self.cmd_names[cmd]
        self.get_logger().info(f'收到指令: {cmd} ({cmd_name})')
        
        # 步骤2: 发送到 STM32 (复用原始代码的发送逻辑)
        if self.ser and self.ser.is_open:
            try:
                # 格式: "{数字}\n"
                data_to_send = f'{cmd}\n'.encode('utf-8')
                self.ser.write(data_to_send)
                self.ser.flush()  # 确保数据立即发送
                
                self.get_logger().info(f'已发送到 STM32: {cmd}')
                
                # 发布成功反馈
                self.publish_result(f'success: {cmd_name}')
                
            except serial.SerialException as e:
                error_msg = f'串口发送失败: {e}'
                self.get_logger().error(error_msg)
                self.publish_result(f'error: {error_msg}')
                
                # 尝试重新连接
                self.connect_serial()
        else:
            error_msg = '串口未连接'
            self.get_logger().error(error_msg)
            self.publish_result(f'error: {error_msg}')
            
            # 尝试重新连接
            self.connect_serial()
    
    def publish_result(self, result):
        """
        发布执行结果
        
        参数:
            result: 字符串，格式 "success: xxx" 或 "error: xxx"
        """
        msg = String()
        msg.data = result
        self.result_publisher.publish(msg)
    
    def publish_status(self):
        """
        发布节点在线状态 (心跳)
        
        每秒执行一次，用于前端判断后端是否在线
        """
        msg = String()
        if self.ser and self.ser.is_open:
            msg.data = 'online'
        else:
            msg.data = 'offline'
            # 如果离线，尝试重连
            if not self.ser:
                self.connect_serial()
        
        self.status_publisher.publish(msg)
    
    def destroy_node(self):
        """
        节点销毁时的清理工作
        
        在节点关闭前发送停止指令，确保机器人安全
        """
        self.get_logger().info('正在关闭节点...')
        
        # 发送停止指令 (安全第一)
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(b'1\n')  # 停止指令
                self.ser.flush()
                self.get_logger().info('已发送停止指令')
            except:
                pass
            
            # 关闭串口
            self.ser.close()
            self.get_logger().info('串口已关闭')
        
        # 调用父类销毁方法
        super().destroy_node()


def main(args=None):
    """
    主函数 - ROS2 节点入口
    
    标准 ROS2 Python 节点入口函数格式
    """
    # 1. 初始化 ROS2
    rclpy.init(args=args)
    
    # 2. 创建节点实例
    node = STM32ControlNode()
    
    # 3. 进入事件循环 (阻塞，直到节点关闭)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('收到中断信号')
    finally:
        # 4. 清理资源
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
```

### 3.4 配置文件详解

#### setup.py - Python 包配置

```python
from setuptools import setup
import os

package_name = 'stm32_control'

setup(
    name=package_name,
    version='0.0.1',
    
    # Python 包列表
    packages=[package_name],
    
    # 数据文件安装位置
    data_files=[
        # ROS 包索引
        ('share/ament_index/resource_index/packages', 
         ['resource/' + package_name]),
        
        # package.xml
        ('share/' + package_name, ['package.xml']),
        
        # launch 文件
        (os.path.join('share', package_name, 'launch'), 
         ['launch/stm32_control_launch.py']),
    ],
    
    install_requires=['setuptools'],
    zip_safe=True,
    
    maintainer='nvidia',
    maintainer_email='nvidia@todo.todo',
    description='STM32 Control Node for ROS2',
    license='Apache-2.0',
    
    # 入口点 - 定义可执行命令
    entry_points={
        'console_scripts': [
            'stm32_control_node = stm32_control.stm32_control_node:main',
        ],
    },
)
```

#### package.xml - ROS 包配置

```xml
<?xml version="1.0"?>
<?xml-model href="http://download.ros.org/schema/package_format3.xsd" 
            schematypens="http://www.w3.org/2001/XMLSchema"?>
<package format="3">
  <!-- 包名称 -->
  <name>stm32_control</name>
  
  <!-- 版本号 -->
  <version>0.0.1</version>
  
  <!-- 描述 -->
  <description>STM32 Control Node for ROS2</description>
  
  <!-- 维护者 -->
  <maintainer email="nvidia@todo.todo">nvidia</maintainer>
  
  <!-- 许可证 -->
  <license>Apache-2.0</license>
  
  <!-- 依赖项 -->
  <depend>rclpy</depend>          <!-- ROS2 Python 客户端库 -->
  <depend>std_msgs</depend>       <!-- 标准消息类型 -->
  
  <!-- 构建工具 -->
  <exec_depend>python3-serial</exec_depend>
  
  <!-- 测试依赖 -->
  <test_depend>ament_copyright</test_depend>
  <test_depend>ament_flake8</test_depend>
  <test_depend>ament_pep257</test_depend>
  <test_depend>python3-pytest</test_depend>
  
  <!-- 导出 -->
  <export>
    <build_type>ament_python</build_type>
  </export>
</package>
```

#### stm32_control_launch.py - 启动文件

```python
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    """
    生成启动描述
    
    使用方式: ros2 launch stm32_control stm32_control_launch.py
    """
    return LaunchDescription([
        Node(
            package='stm32_control',           # 包名
            executable='stm32_control_node',   # 可执行文件名
            name='stm32_control_node',         # 节点名称
            output='screen',                   # 输出到屏幕
            
            # 参数 (可覆盖默认值)
            parameters=[{
                'port_name': '/dev/ttyACM3',
                'baud_rate': 115200,
                'status_publish_rate': 1.0,
            }],
        ),
    ])
```

### 3.5 编译和安装流程

```bash
# ========== 步骤 1: 进入工作空间 ==========
cd /home/nvidia/name_zhoushifei/WS

# ========== 步骤 2: 加载 ROS2 环境 ==========
source /opt/ros/humble/setup.bash

# ========== 步骤 3: 编译包 ==========
# --packages-select 只编译指定包，加快速度
colcon build --packages-select stm32_control

# 预期输出:
# Starting >>> stm32_control
# Finished <<< stm32_control [2.5s]
# Summary: 1 package finished

# ========== 步骤 4: 加载编译结果 ==========
source install/setup.bash

# ========== 步骤 5: 验证安装 ==========
# 查看可执行文件
ros2 pkg executables stm32_control
# 预期输出: stm32_control stm32_control_node

# ========== 步骤 6: 运行节点 ==========
ros2 run stm32_control stm32_control_node

# 或使用 launch 文件
ros2 launch stm32_control stm32_control_launch.py
```

---

## 4. ROS Bridge 启动全流程

### 4.1 什么是 ROS Bridge?

```
ROS Bridge 架构:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                            │
│    前端 (JavaScript)                    ROS2 网络                          │
│    ┌─────────────┐                     ┌─────────────┐                     │
│    │   Web页面   │◄────WebSocket─────►│ rosbridge   │◄────ROS Topic────►│
│    │             │     ws://:9090     │   server    │                     │
│    │  roslibjs   │                     │             │    /stm32_cmd      │
│    │             │    JSON 消息        │  Protocol   │    /stm32_result   │
│    │ {           │◄──────────────────►│  Converter  │    /stm32_status   │
│    │   op:       │                     │             │                     │
│    │   topic:    │                     │  ROS Message│                     │
│    │   msg:      │                     │  (C++结构)  │                     │
│    │ }           │                     │             │                     │
│    └─────────────┘                     └─────────────┘                     │
│                                                                            │
│  协议转换过程:                                                              │
│  1. 前端发送 JSON:  {"op": "publish", "topic": "/stm32_cmd", ...}           │
│  2. rosbridge 解析 JSON，提取 topic 和 msg                                  │
│  3. 根据 topic 找到对应的 ROS 消息类型定义                                   │
│  4. 将 JSON 字段映射到 ROS Message 字段                                     │
│  5. 通过 DDS 发布到 ROS 网络                                                │
│                                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 完整启动流程

```bash
#!/bin/bash
# 完整启动脚本: start_all_services.sh

# ========== 环境配置 ==========
export ROS_DOMAIN_ID=30
export PYTHONUNBUFFERED=1

source /opt/ros/humble/setup.bash

echo "🚀 启动幕墙清洗机器人控制系统..."

# ========== 步骤 1: 启动 ROS Bridge (必须最先启动) ==========
echo "[1/5] 启动 ROS Bridge Server (端口 9090)..."
ros2 launch rosbridge_server rosbridge_websocket_launch.xml &
ROSBRIDGE_PID=$!
sleep 3

# 验证启动
if ss -tlnp | grep -q ":9090"; then
    echo "✅ ROS Bridge 启动成功 (PID: $ROSBRIDGE_PID)"
else
    echo "❌ ROS Bridge 启动失败"
    exit 1
fi

# ========== 步骤 2: 启动相机 ==========
echo "[2/5] 启动 Orbbec 相机..."
ros2 launch orbbec_camera gemini_330_series.launch.py \
    color_width:=1280 \
    color_height:=720 \
    color_fps:=10 \
    enable_depth:=true \
    enable_point_cloud:=true \
    enable_left_ir:=true \
    enable_right_ir:=true \
    depth_width:=640 \
    depth_height:=400 \
    depth_fps:=10 \
    left_ir_width:=640 \
    left_ir_height:=400 \
    left_ir_fps:=10 \
    right_ir_width:=640 \
    right_ir_height:=400 \
    right_ir_fps:=10 &
CAMERA_PID=$!
sleep 15

echo "✅ 相机启动完成 (PID: $CAMERA_PID)"
# 注意: 相机已启用深度/点云/双目红外，分辨率 640x400@10fps；
#       相应发布 /camera/depth/image_raw、/camera/left_ir/image_raw、/camera/right_ir/image_raw

# ========== 步骤 3: 启动 HTTP 视频流 ==========
echo "[3/5] 启动 HTTP 视频流服务 (端口 8082)..."
cd /home/nvidia/name_huanghongle3/camera_http_ws
source install/setup.bash
ros2 run camera_http camera_http_node &
HTTP_PID=$!
sleep 3

if ss -tlnp | grep -q ":8082"; then
    echo "✅ HTTP 视频流启动成功 (PID: $HTTP_PID)"
else
    echo "❌ HTTP 视频流启动失败"
fi

# ========== 步骤 4: 启动 STM32 控制节点 ==========
echo "[4/5] 启动 STM32 控制节点..."
cd /home/nvidia/name_zhoushifei/WS
source install/setup.bash
ros2 run stm32_control stm32_control_node &
STM32_PID=$!
sleep 3

echo "✅ STM32 控制节点启动完成 (PID: $STM32_PID)"

# ========== 步骤 5: 启动超声波节点 (可选) ==========
echo "[5/5] 启动超声波传感器节点..."
cd /home/nvidia/name_ranhongmei/ws
source install/setup.bash
ros2 run fist_demo_uart wave_length_node &
ULTRA_PID=$!
sleep 3

echo "✅ 超声波节点启动完成 (PID: $ULTRA_PID)"

# ========== 服务状态汇总 ==========
echo ""
echo "========================================"
echo "📊 所有服务启动完成"
echo "========================================"
echo "ROS Bridge:      ws://192.168.0.2:9090"
echo "视频流:          http://192.168.0.2:8082/camera（另提供 /depth、/ir）"
echo "STM32 控制:      /stm32_cmd, /stm32_result"
echo "超声波数据:      /wave_length"
echo "========================================"

# 等待用户中断
trap "echo '正在停止所有服务...'; kill $ROSBRIDGE_PID $CAMERA_PID $HTTP_PID $STM32_PID $ULTRA_PID; exit" SIGINT
wait
```

### 4.3 启动依赖关系

```
启动顺序依赖图:

rosbridge_server (端口 9090)
        │
        ├──► 后续所有 ROS 节点都依赖此服务
        │
        ├─────────────────┬─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│  orbbec_camera │  │ stm32_control │  │ wave_length   │
│   (相机驱动)   │  │   (串口控制)   │  │  (超声波)     │
└───────┬───────┘  └───────────────┘  └───────────────┘
        │
        │ 订阅 /camera/color/image_raw
        ▼
┌───────────────┐
│ camera_http   │
│  (HTTP服务)    │
└───────────────┘

启动顺序规则:
1. rosbridge_server 必须最先启动
2. camera_http 必须在 orbbec_camera 之后启动
3. stm32_control 和 wave_length 无相互依赖
4. 所有节点都依赖 ROS_DOMAIN_ID 环境变量
```

---

## 5. 视频流实现 (HTTP/MJPEG)

### 5.1 为什么视频流使用 HTTP?

```
带宽对比分析:

原始视频流 (未压缩):
┌─────────────────────────────────────────────────────────────┐
│ 分辨率: 1280 × 720                                          │
│ 帧率: 30 fps                                                │
│ 位深: 24 bit (RGB)                                          │
│ 计算: 1280 × 720 × 3 bytes × 30 fps = 82,944,000 bytes/s    │
│       ≈ 663 Mbps                                            │
│                                                              │
│ 问题: 远超千兆网卡带宽，无法传输                              │
└─────────────────────────────────────────────────────────────┘

MJPEG 压缩流:
┌─────────────────────────────────────────────────────────────┐
│ 分辨率: 1280 × 720                                          │
│ 帧率: 10 fps (降低帧率减少带宽)                              │
│ 压缩: JPEG 质量 80%                                         │
│ 单帧大小: ~50 KB (平均)                                      │
│ 计算: 50 KB × 10 fps = 500 KB/s ≈ 4 Mbps                    │
│                                                              │
│ 优势: 带宽降低 165 倍，可在局域网流畅传输                     │
└─────────────────────────────────────────────────────────────┘

浏览器兼容性:
┌─────────────────────────────────────────────────────────────┐
│ <img src="http://...">                                       │
│                                                              │
│ 优势:                                                        │
│ • 所有浏览器原生支持，无需插件                                │
│ • 自动处理缓冲、解码、显示                                    │
│ • 断开自动重连 (配合 onerror 事件)                           │
│ • 硬件加速渲染                                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 视频流节点架构

```python
# camera_http_node.py 核心逻辑

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import threading
import socketserver
from http.server import BaseHTTPRequestHandler


class MJPEGHandler(BaseHTTPRequestHandler):
    """
    HTTP 请求处理器
    
    处理浏览器对 /camera 路径的 GET 请求
    返回 MJPEG 流 (multipart/x-mixed-replace)
    """
    
    # 类变量 - 所有客户端共享同一帧数据
    latest_frame = None
    frame_lock = threading.Lock()
    
    def do_GET(self):
        if self.path == '/camera':
            # 设置响应头 - 关键: multipart/x-mixed-replace 实现流式传输
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=--jpgboundary')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            try:
                while True:
                    # 获取最新帧 (线程安全)
                    with MJPEGHandler.frame_lock:
                        frame = MJPEGHandler.latest_frame
                    
                    if frame is not None:
                        # OpenCV 编码为 JPEG
                        ret, jpeg = cv2.imencode('.jpg', frame)
                        if ret:
                            # 发送 MJPEG 帧
                            self.wfile.write(b'--jpgboundary\r\n')
                            self.send_header('Content-type', 'image/jpeg')
                            self.send_header('Content-length', len(jpeg))
                            self.end_headers()
                            self.wfile.write(jpeg.tobytes())
                            self.wfile.write(b'\r\n')
                    
                    # 控制帧率 (10fps = 100ms)
                    import time
                    time.sleep(0.1)
                    
            except (BrokenPipeError, ConnectionResetError):
                # 客户端断开连接
                pass


class CameraHTTPServer(Node):
    """
    ROS2 节点 + HTTP 服务器
    
    订阅 ROS 相机话题，通过 HTTP 提供 MJPEG 流
    """
    
    def __init__(self):
        super().__init__('camera_http_server')
        
        # 参数配置
        self.declare_parameter('port', 8082)
        self.declare_parameter('host', '0.0.0.0')
        
        port = self.get_parameter('port').value
        host = self.get_parameter('host').value
        
        # ROS 订阅者 - 接收相机图像
        self.subscription = self.create_subscription(
            Image,
            '/camera/color/image_raw',  # 订阅原始相机话题
            self.image_callback,
            10
        )
        
        # HTTP 服务器 - 在独立线程运行
        self.server = ThreadedHTTPServer((host, port), MJPEGHandler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        
        self.get_logger().info(f'HTTP MJPEG Server: http://{host}:{port}/camera')
    
    def image_callback(self, msg):
        """
        接收 ROS 图像消息
        
        将 ROS Image 转换为 OpenCV 格式，更新共享帧
        """
        try:
            # ROS Image → OpenCV
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            
            # 调整分辨率 (降低带宽)
            resized = cv2.resize(cv_image, (1280, 720))
            
            # 更新共享帧 (线程安全)
            with MJPEGHandler.frame_lock:
                MJPEGHandler.latest_frame = resized
                
        except Exception as e:
            self.get_logger().error(f'图像处理错误: {e}')
```

**更新说明（最新版）**：`camera_http_node.py` 已升级为 **3 路 MJPEG 流**：
- `/camera`：彩色，订阅 `/camera/color/image_raw`
- `/depth`：深度，`/camera/depth/image_raw`（16UC1）→ 按 `depth_max_mm=4000` 归一化灰度
- `/ir`：红外，`/camera/left_ir/image_raw`（16UC1/8UC1）→ 按 `ir_max=1023` 归一化灰度

关键变化：
1. 三个流共享同一 `MJPEGHandler`，通过 `urlparse(self.path).path` 只取纯路径进行路由，**剥离 URL 查询串**——前端 `<img>` 追加 `?t=...&r=...` 时间戳也能正确匹配，不会 404。
2. 深度/红外为常驻订阅，`depth_callback` / `ir_callback` 分别更新 `depth_frame` / `ir_frame`。
3. 输出统一 `resize 1280x720`，`jpeg_quality=80`，端口 `8082`。
4. 前端 `<img>` 三路均直连 HTTP，**不经过 rosbridge 转发视频**，避免视频占用 rosbridge 内存/CPU。

### 5.3 前端视频流接入

```html
<!-- 最简单的方式: 直接使用 img 标签 -->
<img src="http://192.168.0.2:8082/camera" alt="Camera Stream">
```

```javascript
// 增强版: 添加错误处理和重连
class VideoStream {
    constructor(url, imgElement) {
        this.url = url;
        this.img = imgElement;
        this.reconnectInterval = 5000; // 5秒重连
        
        this.setupEventHandlers();
    }
    
    setupEventHandlers() {
        // 加载成功
        this.img.onload = () => {
            console.log('视频流连接成功');
        };
        
        // 加载失败 - 自动重连
        this.img.onerror = () => {
            console.error('视频流断开，尝试重连...');
            setTimeout(() => {
                // 添加时间戳防止缓存
                this.img.src = `${this.url}?t=${Date.now()}`;
            }, this.reconnectInterval);
        };
        
        // 初始连接
        this.img.src = this.url;
    }
}

// 使用
const video = new VideoStream(
    'http://192.168.0.2:8082/camera',
    document.getElementById('camera')
);
```

---

## 6. 传感器数据实现 (WebSocket/ROS)

### 6.1 为什么传感器使用 WebSocket?

```
实时性对比:

HTTP 轮询方式 (不推荐):
┌─────────────────────────────────────────────────────────────┐
│ 前端                     后端                                │
│   │                      │                                  │
│   │────GET /api/sensor──►│                                  │
│   │◄─────JSON 数据───────│  ← 往返延迟 50-200ms            │
│   │                      │                                  │
│   │────GET /api/sensor──►│  ← 1秒后再次请求                 │
│   │◄─────JSON 数据───────│                                  │
│                                                              │
│ 问题:                                                        │
│ • 每次请求都需建立 TCP 连接                                  │
│ • HTTP 头部开销大                                            │
│ • 数据更新不及时 (取决于轮询间隔)                             │
│ • 服务器无法主动推送                                         │
└─────────────────────────────────────────────────────────────┘

WebSocket 推送方式 (推荐):
┌─────────────────────────────────────────────────────────────┐
│ 前端                     后端                                │
│   │                      │                                  │
│   │────WebSocket 握手───►│  ← 一次握手，长期连接            │
│   │◄────连接成功─────────│                                  │
│   │                      │                                  │
│   │◄────传感器数据───────│  ← 服务器主动推送，延迟 <10ms    │
│   │◄────传感器数据───────│  ← 数据变化立即推送              │
│   │◄────传感器数据───────│                                  │
│                                                              │
│ 优势:                                                        │
│ • 长连接，无需重复握手                                        │
│ • 头部开销极小                                               │
│ • 实时推送，延迟低                                           │
│ • 服务器可主动发送数据                                        │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 前端 ROS 连接实现

```javascript
// 引入 roslibjs (ROS JavaScript 库)
// CDN: https://static.robotwebtools.org/roslibjs/current/roslib.min.js

class RobotROSInterface {
    constructor(url = 'ws://192.168.0.2:9090') {
        this.url = url;
        this.ros = null;
        this.connected = false;
        this.topics = {};
    }
    
    // ========== 1. 连接管理 ==========
    connect() {
        this.ros = new ROSLIB.Ros({
            url: this.url
        });
        
        this.ros.on('connection', () => {
            console.log('✅ 已连接到 ROS Bridge');
            this.connected = true;
            this.onConnect && this.onConnect();
        });
        
        this.ros.on('error', (error) => {
            console.error('❌ 连接错误:', error);
            this.connected = false;
        });
        
        this.ros.on('close', () => {
            console.warn('⚠️ 连接已关闭');
            this.connected = false;
            // 自动重连
            setTimeout(() => this.connect(), 5000);
        });
    }
    
    disconnect() {
        if (this.ros) {
            this.ros.close();
        }
    }
    
    // ========== 2. 控制指令发布 ==========
    sendCommand(cmd) {
        if (!this.connected) {
            console.error('未连接，无法发送指令');
            return;
        }
        
        // 指令映射
        const CMD_MAP = {
            'stop': 1,
            'backward': 2,    // 后退
            'forward': 3,     // 前进
            'turn_left': 4,
            'turn_right': 5,
            'brushless_stop': 6,
            'brushless_start': 7
        };
        
        const cmdValue = CMD_MAP[cmd];
        if (cmdValue === undefined) {
            console.error('未知指令:', cmd);
            return;
        }
        
        // 创建或复用 Topic
        if (!this.topics.cmd) {
            this.topics.cmd = new ROSLIB.Topic({
                ros: this.ros,
                name: '/stm32_cmd',
                messageType: 'std_msgs/Int32'
            });
        }
        
        // 发布消息
        const msg = new ROSLIB.Message({
            data: cmdValue
        });
        this.topics.cmd.publish(msg);
        
        console.log('发送指令:', cmd, '(', cmdValue, ')');
    }
    
    // ========== 3. 传感器数据订阅 ==========
    subscribeUltrasonic(callback) {
        const topic = new ROSLIB.Topic({
            ros: this.ros,
            name: '/wave_length',
            messageType: 'std_msgs/UInt8MultiArray'
        });
        
        topic.subscribe((msg) => {
            // 解析数据
            // 数据格式: [左前高, 左前低, 正前高, 正前低, 右前高, 右前低, 0, 0]
            const data = msg.data;
            const distances = {
                left: (data[0] << 8) | data[1],      // 左前距离 (mm)
                center: (data[2] << 8) | data[3],    // 正前距离 (mm)
                right: (data[4] << 8) | data[5]     // 右前距离 (mm)
            };
            
            callback(distances);
        });
        
        return topic; // 返回 topic 对象以便后续取消订阅
    }
    
    subscribePosition(callback) {
        const topic = new ROSLIB.Topic({
            ros: this.ros,
            name: '/ultrasonic_position',
            messageType: 'std_msgs/Float32MultiArray'
        });
        
        topic.subscribe((msg) => {
            // 数据格式: [垂直距离, 偏移量, 偏移角度, 左前, 正前, 右前]
            const data = msg.data;
            const position = {
                vertical: data[0],        // 垂直距离 (m)
                offset: data[1],          // 偏移量 (m)
                angle: data[2] * 180 / Math.PI  // 偏移角度 (度)
            };
            
            callback(position);
        });
        
        return topic;
    }
    
    subscribeStatus(callback) {
        const topic = new ROSLIB.Topic({
            ros: this.ros,
            name: '/stm32_status',
            messageType: 'std_msgs/String'
        });
        
        topic.subscribe((msg) => {
            callback(msg.data); // "online" or "offline"
        });
        
        return topic;
    }
    
    subscribeResult(callback) {
        const topic = new ROSLIB.Topic({
            ros: this.ros,
            name: '/stm32_result',
            messageType: 'std_msgs/String'
        });
        
        topic.subscribe((msg) => {
            // 格式: "success: 前进" 或 "error: ..."
            const [status, message] = msg.data.split(': ');
            callback({
                success: status === 'success',
                message: message || msg.data
            });
        });
        
        return topic;
    }
}

// 使用示例
const robot = new RobotROSInterface();

// 连接
robot.connect();

// 订阅传感器数据
robot.subscribeUltrasonic((distances) => {
    console.log('超声波距离:', distances);
    // 更新 UI
    document.getElementById('dist-left').textContent = distances.left;
    document.getElementById('dist-center').textContent = distances.center;
    document.getElementById('dist-right').textContent = distances.right;
});

robot.subscribePosition((pos) => {
    console.log('定位信息:', pos);
});

// 发送控制指令
robot.sendCommand('forward');  // 前进
robot.sendCommand('stop');     // 停止
```

---

## 7. 前端对接指南

### 7.1 完整前端示例

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>幕墙清洗机器人控制台</title>
    <script src="https://static.robotwebtools.org/roslibjs/current/roslib.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #1a1a2e;
            color: #fff;
            margin: 0;
            padding: 20px;
        }
        .container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }
        .panel {
            background: #16213e;
            border-radius: 10px;
            padding: 20px;
        }
        .video-container img {
            width: 100%;
            border-radius: 8px;
        }
        .control-pad {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            max-width: 300px;
            margin: 20px auto;
        }
        button {
            padding: 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
        }
        .btn-move { background: #0f3460; color: #fff; }
        .btn-move:hover { background: #e94560; }
        .btn-stop { background: #e94560; grid-column: 2; }
        .sensor-display {
            display: flex;
            justify-content: space-around;
            margin: 20px 0;
        }
        .sensor-value {
            text-align: center;
        }
        .sensor-value .value {
            font-size: 32px;
            color: #e94560;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #ef4444;
        }
        .status-indicator.online {
            background: #10b981;
            box-shadow: 0 0 10px #10b981;
        }
    </style>
</head>
<body>
    <h1>🤖 幕墙清洗机器人控制台</h1>
    
    <div style="margin-bottom: 20px;">
        ROS连接: <span id="rosStatus" class="status-indicator"></span>
        STM32状态: <span id="stm32Status">离线</span>
        <button onclick="robot.connect()">连接</button>
    </div>

    <div class="container">
        <!-- 左侧：视频和控制 -->
        <div class="panel">
            <h2>📹 实时视频</h2>
            <div class="video-container">
                <img id="camera" src="http://192.168.0.2:8082/camera" alt="Camera">
            </div>
            
            <h2>🎮 运动控制</h2>
            <div class="control-pad">
                <div></div>
                <button class="btn-move" 
                        onmousedown="robot.sendCommand('forward')" 
                        onmouseup="robot.sendCommand('stop')">⬆️ 前进</button>
                <div></div>
                
                <button class="btn-move" 
                        onmousedown="robot.sendCommand('turn_left')" 
                        onmouseup="robot.sendCommand('stop')">⬅️ 左转</button>
                <button class="btn-stop" onclick="robot.sendCommand('stop')">⏹️ 停止</button>
                <button class="btn-move" 
                        onmousedown="robot.sendCommand('turn_right')" 
                        onmouseup="robot.sendCommand('stop')">➡️ 右转</button>
                
                <div></div>
                <button class="btn-move" 
                        onmousedown="robot.sendCommand('backward')" 
                        onmouseup="robot.sendCommand('stop')">⬇️ 后退</button>
                <div></div>
            </div>
            
            <h2>🔄 刷子控制</h2>
            <button onclick="robot.sendCommand('brushless_start')">启动刷子</button>
            <button onclick="robot.sendCommand('brushless_stop')">停止刷子</button>
        </div>

        <!-- 右侧：传感器数据 -->
        <div class="panel">
            <h2>📡 超声波传感器</h2>
            <div class="sensor-display">
                <div class="sensor-value">
                    <div class="value" id="dist-left">--</div>
                    <div>左前 (mm)</div>
                </div>
                <div class="sensor-value">
                    <div class="value" id="dist-center">--</div>
                    <div>正前 (mm)</div>
                </div>
                <div class="sensor-value">
                    <div class="value" id="dist-right">--</div>
                    <div>右前 (mm)</div>
                </div>
            </div>
            
            <h2>🎯 定位信息</h2>
            <p>垂直距离: <span id="pos-vertical">--</span> m</p>
            <p>偏移量: <span id="pos-offset">--</span> m</p>
            <p>偏移角度: <span id="pos-angle">--</span> °</p>
            
            <h2>📝 操作日志</h2>
            <div id="log" style="background: #0f3460; padding: 10px; height: 200px; overflow-y: auto; font-family: monospace; font-size: 12px;"></div>
        </div>
    </div>

    <script>
        // 机器人 ROS 接口类
        class RobotROSInterface {
            constructor(url = 'ws://192.168.0.2:9090') {
                this.url = url;
                this.ros = null;
                this.connected = false;
                this.topics = {};
            }
            
            connect() {
                this.ros = new ROSLIB.Ros({ url: this.url });
                
                this.ros.on('connection', () => {
                    console.log('✅ 已连接到 ROS');
                    this.connected = true;
                    document.getElementById('rosStatus').classList.add('online');
                    this.initSubscriptions();
                    this.log('ROS 连接成功');
                });
                
                this.ros.on('error', (error) => {
                    console.error('❌ 连接错误:', error);
                    this.log('ROS 连接错误: ' + error);
                });
                
                this.ros.on('close', () => {
                    console.warn('⚠️ 连接已关闭');
                    this.connected = false;
                    document.getElementById('rosStatus').classList.remove('online');
                    this.log('ROS 连接已关闭');
                    setTimeout(() => this.connect(), 5000);
                });
            }
            
            sendCommand(cmd) {
                if (!this.connected) {
                    this.log('错误: 未连接到 ROS');
                    return;
                }
                
                const CMD_MAP = {
                    'stop': 1,
                    'backward': 2,
                    'forward': 3,
                    'turn_left': 4,
                    'turn_right': 5,
                    'brushless_stop': 6,
                    'brushless_start': 7
                };
                
                const cmdValue = CMD_MAP[cmd];
                if (cmdValue === undefined) return;
                
                if (!this.topics.cmd) {
                    this.topics.cmd = new ROSLIB.Topic({
                        ros: this.ros,
                        name: '/stm32_cmd',
                        messageType: 'std_msgs/Int32'
                    });
                }
                
                this.topics.cmd.publish(new ROSLIB.Message({ data: cmdValue }));
                this.log(`发送指令: ${cmd}`);
            }
            
            initSubscriptions() {
                // 订阅 STM32 状态
                const statusTopic = new ROSLIB.Topic({
                    ros: this.ros,
                    name: '/stm32_status',
                    messageType: 'std_msgs/String'
                });
                statusTopic.subscribe((msg) => {
                    const status = msg.data;
                    document.getElementById('stm32Status').textContent = 
                        status === 'online' ? '在线 🟢' : '离线 🔴';
                });
                
                // 订阅超声波数据
                const ultraTopic = new ROSLIB.Topic({
                    ros: this.ros,
                    name: '/wave_length',
                    messageType: 'std_msgs/UInt8MultiArray'
                });
                ultraTopic.subscribe((msg) => {
                    const d = msg.data;
                    document.getElementById('dist-left').textContent = (d[0] << 8) | d[1];
                    document.getElementById('dist-center').textContent = (d[2] << 8) | d[3];
                    document.getElementById('dist-right').textContent = (d[4] << 8) | d[5];
                });
                
                // 订阅定位数据
                const posTopic = new ROSLIB.Topic({
                    ros: this.ros,
                    name: '/ultrasonic_position',
                    messageType: 'std_msgs/Float32MultiArray'
                });
                posTopic.subscribe((msg) => {
                    document.getElementById('pos-vertical').textContent = msg.data[0].toFixed(2);
                    document.getElementById('pos-offset').textContent = msg.data[1].toFixed(2);
                    document.getElementById('pos-angle').textContent = (msg.data[2] * 180 / Math.PI).toFixed(1);
                });
                
                // 订阅执行结果
                const resultTopic = new ROSLIB.Topic({
                    ros: this.ros,
                    name: '/stm32_result',
                    messageType: 'std_msgs/String'
                });
                resultTopic.subscribe((msg) => {
                    this.log('执行结果: ' + msg.data);
                });
            }
            
            log(message) {
                const logDiv = document.getElementById('log');
                const time = new Date().toLocaleTimeString();
                logDiv.innerHTML += `[${time}] ${message}<br>`;
                logDiv.scrollTop = logDiv.scrollHeight;
            }
        }
        
        // 创建实例
        const robot = new RobotROSInterface();
        
        // 自动连接
        robot.connect();
        
        // 视频流错误处理
        const cameraImg = document.getElementById('camera');
        cameraImg.onerror = () => {
            console.log('视频流断开，尝试重连...');
            setTimeout(() => {
                cameraImg.src = 'http://192.168.0.2:8082/camera?t=' + Date.now();
            }, 5000);
        };
        
        // 键盘控制
        document.addEventListener('keydown', (e) => {
            if (e.repeat) return;
            switch(e.key) {
                case 'w': case 'ArrowUp': robot.sendCommand('forward'); break;
                case 's': case 'ArrowDown': robot.sendCommand('backward'); break;
                case 'a': case 'ArrowLeft': robot.sendCommand('turn_left'); break;
                case 'd': case 'ArrowRight': robot.sendCommand('turn_right'); break;
                case ' ': robot.sendCommand('stop'); break;
            }
        });
        
        document.addEventListener('keyup', (e) => {
            if (['w','s','a','d','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.key)) {
                robot.sendCommand('stop');
            }
        });
    </script>
</body>
</html>
```

---

## 8. 故障排查手册

### 8.1 连接问题

#### ROS Bridge 连接失败

```bash
# 检查 ROS Bridge 是否运行
ss -tlnp | grep 9090

# 检查防火墙
sudo ufw status
sudo ufw allow 9090

# 查看日志
tail -f /tmp/rosbridge.log
```

#### 视频流无法显示

```bash
# 检查 HTTP 服务
ss -tlnp | grep 8082

# 测试视频流
curl http://192.168.0.2:8082/camera

# 检查相机话题
ros2 topic echo /camera/color/image_raw
```

#### STM32 控制无响应

```bash
# 检查串口设备
ls -la /dev/ttyACM*

# 检查权限
sudo chmod 666 /dev/ttyACM3

# 查看控制节点日志
tail -f /tmp/stm32_control.log

# 测试指令发送
ros2 topic pub /stm32_cmd std_msgs/Int32 "{data: 1}"
```

### 8.2 性能优化

#### 降低视频流延迟

```python
# camera_http_node.py
# 1. 降低分辨率
self.resize_width = 640   # 原为 1280
self.resize_height = 360  # 原为 720

# 2. 降低 JPEG 质量
ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])

# 3. 提高帧率 (降低 sleep 时间)
time.sleep(0.05)  # 20fps，原为 0.1 (10fps)
```

#### 优化传感器数据频率

```python
# STM32 控制节点
# 降低状态发布频率
self.status_timer = self.create_timer(2.0, self.publish_status)  # 0.5Hz

# 超声波节点
# 降低采集频率
timer_period = 1.0  # 1秒一次，原为 0.5
```

---

## 附录: 关键文件位置

| 文件 | 路径 | 说明 |
|------|------|------|
| STM32控制节点源码 | `/home/nvidia/name_zhoushifei/WS/src/stm32_control/stm32_control/stm32_control_node.py` | 核心控制封装 |
| 视频流节点源码 | `/home/nvidia/name_huanghongle3/camera_http_ws/src/camera_http/camera_http/camera_http_node.py` | HTTP视频服务（/camera、/depth、/ir 三路流） |
| 交互式管理器（推荐） | `/home/nvidia/name_huanghongle3/robot_service_manager.py` | 服务一键/分项管理 v2.0 |
| 前端示例 | `/home/nvidia/name_zhoushifei/frontend_example/robot_control.html` | 完整前端实现 |
| 一键启动脚本 | `/home/nvidia/name_huanghongle3/start_all_services.py` | 批量启动所有服务（已非首选） |
| 本技术文档 | `/home/nvidia/name_huanghongle3/TECHNICAL_IMPLEMENTATION.md` | 本文档 |

---

**文档版本**: v1.0（更新到最新版，深度/红外已启用）  
**最后更新**: 2026-03-09  
**作者**: Jetson Engineer
