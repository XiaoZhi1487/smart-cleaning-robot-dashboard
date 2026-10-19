# 幕墙清洗机器人控制系统 - 技术实现文档

> **更新到最新版**：相机已启用深度/点云/双目红外；HTTP 视频伺服现提供 /camera、/depth、/ir 三路 MJPEG 流（前端 `<img>` 直连，不经过 rosbridge）；推荐使用交互式管理器 `robot_service_manager.py`（v2.0）。

## 📖 文档概述

本文档详细描述了幕墙清洗机器人控制系统的前后端通讯架构、ROS2 节点封装、数据流设计以及各模块的实现原理。

**系统架构概览**:
```
┌─────────────────────────────────────────────────────────────────────────┐
│                           前端 (Frontend)                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  视频显示    │  │  运动控制    │  │  传感器显示  │  │  状态监控    │     │
│  │  HTTP/MJPEG │  │  WebSocket  │  │  WebSocket  │  │  WebSocket  │     │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘     │
└─────────┼────────────────┼────────────────┼────────────────┼───────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          后端 (Backend)                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ HTTP Server │  │ ROS Bridge  │  │  STM32控制   │  │  超声波节点  │     │
│  │  8082端口   │  │  9090端口   │  │  串口通信    │  │  /dev/ttyACM │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
          │                │                │                │
          ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          硬件层 (Hardware)                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │ Orbbec相机  │  │   STM32     │  │  超声波模组  │  │   执行机构   │     │
│  │  USB3.0    │  │  /dev/ttyACM│  │   UART     │  │  电机/刷子   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 1. 通讯架构设计

### 1.1 为什么采用混合通讯方式？

| 数据类型 | 协议选择 | 原因 |
|---------|---------|------|
| **视频流** | HTTP/MJPEG | 降低带宽压力，浏览器原生支持，无需额外库 |
| **控制指令** | WebSocket/ROS | 双向实时通信，低延迟(<10ms) |
| **传感器数据** | WebSocket/ROS | 实时推送，避免轮询开销 |

### 1.2 三种通讯方式对比

```
┌────────────────────────────────────────────────────────────────┐
│  HTTP API (方案一 - 已废弃)                                     │
│  ─────────────────────────                                      │
│  前端 ──HTTP POST──► Flask ──串口──► STM32                      │
│                                                                  │
│  缺点: 单向通信、延迟高(50-200ms)、无法推送传感器数据             │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  WebSocket + ROS (方案二 - 当前采用)                            │
│  ───────────────────────────────────                            │
│  前端 ──WebSocket──► ROS Bridge ──ROS Topic──► STM32控制节点     │
│         ws://:9090                  /stm32_cmd                  │
│                                                                  │
│  优点: 双向实时、延迟低(<10ms)、统一消息总线                     │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│  HTTP MJPEG (视频流专用)                                        │
│  ───────────────────────                                        │
│  前端 ◄──HTTP GET── MJPEG Stream ◄──ROS Topic──► 相机节点        │
│       http://:8082/camera        /camera/color/image_raw        │
│                                                                  │
│  优点: 浏览器原生支持<img>标签、自动重连、带宽可控               │
└────────────────────────────────────────────────────────────────┘
```

---

## 2. ROS2 系统架构

### 2.1 ROS2 核心概念

```
ROS2 (Robot Operating System 2)
├── 节点 (Node)        - 独立运行的进程
├── 话题 (Topic)       - 发布/订阅的消息总线
├── 消息 (Message)     - 数据结构定义
└── 启动文件 (Launch)  - 批量启动配置
```

### 2.2 本项目 ROS2 节点拓扑

```
                            ┌──────────────────┐
                            │   rosbridge_server│
                            │   (WebSocket桥接) │
                            │   端口: 9090      │
                            └────────┬─────────┘
                                     │
            ┌────────────────────────┼────────────────────────┐
            │                        │                        │
            ▼                        ▼                        ▼
   ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
   │  stm32_control  │     │  camera_http    │     │  wave_length    │
   │   控制节点       │     │   视频流节点     │     │   超声波节点     │
   │                 │     │                 │     │                 │
   │  /stm32_cmd ◄───┼─────┤                 │     │  /wave_length ──┼──►
   │  /stm32_result ─┼────►│                 │     │                 │
   │  /stm32_status ─┼────►│  /camera/color  │     │                 │
   │                 │     │  /image_raw ◄───┼─────┘                 │
   │    /dev/ttyACM3 │     │                 │                       │
   │        ▼        │     │   端口: 8082    │                       │
   │   ┌─────────┐   │     │        ▼        │                       │
   └───┤  STM32  ├───┘     │   ┌─────────┐   │                       │
       └─────────┘         └───┤  浏览器  ├───┘                       │
                               └─────────┘                             │
                               http://:8082/camera                     │
                                                                      │
                                                                      ▼
                                                            ┌─────────────────┐
                                                            │   前端浏览器     │
                                                            │  (Vue + roslib) │
                                                            │                 │
                                                            │  ws://:9090    │
                                                            │  http://:8082  │
                                                            └─────────────────┘
```

---

## 3. STM32 控制节点封装详解

### 3.1 原始控制方式

原始 `com_with_stm.py` 是一个简单的串口通信脚本：

```python
# 原始代码逻辑
ser = serial.Serial('/dev/ttyACM3', 115200)
user_input = input("请输入数字: ")  # 手动输入 1-7
ser.write(f"{user_input}\n".encode())  # 发送到 STM32
```

**问题**: 无法与 ROS 系统集成，前端无法直接调用。

### 3.2 封装为 ROS2 节点

#### 步骤 1: 创建 ROS2 包结构

```
stm32_control/                      # 包根目录
├── stm32_control/                  # Python 模块
│   ├── __init__.py
│   └── stm32_control_node.py       # 主节点代码
├── resource/
│   └── stm32_control               # 空文件，标记为 ament 包
├── launch/
│   └── stm32_control_launch.py     # 启动文件
├── setup.py                        # Python 包配置
└── package.xml                     # ROS 包配置
```

#### 步骤 2: 核心节点代码实现

```python
#!/usr/bin/env python3
"""
STM32 控制节点 - ROS2 封装
功能: 将原始串口控制程序封装为 ROS2 节点，实现 WebSocket 远程控制
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32, String
import serial


class STM32ControlNode(Node):
    def __init__(self):
        super().__init__('stm32_control_node')
        
        # ========== 1. 串口配置（来自原始 com_with_stm.py）==========
        self.port_name = '/dev/ttyACM3'
        self.baud_rate = 115200
        self.ser = None
        
        # 指令映射表（来自原始代码的注释说明）
        self.cmd_names = {
            1: '停止',
            2: '后退',      # 注意: 硬件接线反了，软件层修正
            3: '前进',      # 前端发送前进(3) -> 实际对应后退指令(3)
            4: '左转',
            5: '右转',
            6: '无刷停止',
            7: '无刷中速'
        }
        
        # ========== 2. 连接串口（复用原始代码逻辑）==========
        self.connect_serial()
        
        # ========== 3. 创建 ROS 订阅者（接收前端指令）==========
        self.cmd_subscription = self.create_subscription(
            Int32,              # 消息类型: 整数
            '/stm32_cmd',       # 话题名称
            self.cmd_callback,  # 回调函数
            10                  # 队列大小
        )
        
        # ========== 4. 创建 ROS 发布者（反馈执行结果）==========
        self.result_publisher = self.create_publisher(
            String,
            '/stm32_result',
            10
        )
        
        # 状态发布者（1Hz心跳）
        self.status_publisher = self.create_publisher(
            String,
            '/stm32_status',
            10
        )
        self.status_timer = self.create_timer(1.0, self.publish_status)
        
        self.get_logger().info('STM32 控制节点已启动')
    
    def connect_serial(self):
        """连接串口（来自原始 com_with_stm.py）"""
        try:
            self.ser = serial.Serial(
                port=self.port_name,
                baudrate=self.baud_rate,
                timeout=1
            )
            self.get_logger().info(f'串口 {self.port_name} 连接成功')
        except serial.SerialException as e:
            self.get_logger().error(f'串口连接失败: {e}')
    
    def cmd_callback(self, msg):
        """接收前端指令并转发给 STM32"""
        cmd = msg.data
        
        # 验证指令有效性
        if cmd not in self.cmd_names:
            self.publish_result(f'error: 无效指令 {cmd}')
            return
        
        cmd_name = self.cmd_names[cmd]
        self.get_logger().info(f'收到指令: {cmd} ({cmd_name})')
        
        # 发送到 STM32（复用原始代码的发送逻辑）
        if self.ser and self.ser.is_open:
            try:
                data_to_send = f'{cmd}\n'.encode('utf-8')
                self.ser.write(data_to_send)
                self.publish_result(f'success: {cmd_name}')
            except serial.SerialException as e:
                self.publish_result(f'error: {e}')
        else:
            self.publish_result('error: 串口未连接')
    
    def publish_result(self, result):
        """发布执行结果给前端"""
        msg = String()
        msg.data = result
        self.result_publisher.publish(msg)
    
    def publish_status(self):
        """发布节点在线状态（1Hz心跳）"""
        msg = String()
        msg.data = 'online' if (self.ser and self.ser.is_open) else 'offline'
        self.status_publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = STM32ControlNode()
    try:
        rclpy.spin(node)  # 进入事件循环
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
```

#### 步骤 3: 配置文件

**setup.py** - Python 包配置:
```python
from setuptools import setup
import os

package_name = 'stm32_control'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), ['launch/stm32_control_launch.py']),
    ],
    install_requires=['setuptools'],
    entry_points={
        'console_scripts': [
            'stm32_control_node = stm32_control.stm32_control_node:main',
        ],
    },
)
```

**package.xml** - ROS 包配置:
```xml
<?xml version="1.0"?>
<package format="3">
  <name>stm32_control</name>
  <version>0.0.1</version>
  <description>STM32 Control Node for ROS2</description>
  
  <depend>rclpy</depend>
  <depend>std_msgs</depend>
  
  <export>
    <build_type>ament_python</build_type>
  </export>
</package>
```

#### 步骤 4: 编译和安装

```bash
# 1. 进入工作空间
cd /home/nvidia/name_zhoushifei/WS

# 2. 编译包
source /opt/ros/humble/setup.bash
colcon build --packages-select stm32_control

# 3. 加载环境
source install/setup.bash

# 4. 运行节点
ros2 run stm32_control stm32_control_node
```

---

## 4. ROS Bridge 启动全流程

### 4.1 什么是 ROS Bridge?

ROS Bridge 是 ROS2 与 Web 应用之间的桥梁：
- **输入**: WebSocket 连接 (ws://localhost:9090)
- **输出**: ROS2 Topic 发布/订阅
- **协议转换**: JSON ↔ ROS Message

### 4.2 启动顺序（重要！）

```bash
# ========== 步骤 1: 设置环境变量 ==========
export ROS_DOMAIN_ID=30  # 防止与其他ROS网络冲突

# ========== 步骤 2: 加载ROS环境 ==========
source /opt/ros/humble/setup.bash

# ========== 步骤 3: 启动ROS Bridge（必须最先启动）==========
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
# 输出: WebSocket server started on port 9090

# ========== 步骤 4: 启动相机（基础服务）==========
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
    right_ir_fps:=10
# 深度/点云/双目红外均已启用，分辨率 640x400@10fps

# ========== 步骤 5: 启动HTTP视频流（依赖相机）==========
cd /home/nvidia/name_huanghongle3/camera_http_ws
source install/setup.bash
ros2 run camera_http camera_http_node
# 输出: URL: http://0.0.0.0:8082/camera（同时提供 /depth、/ir 两路流）
# 三路流: /camera(彩色) /depth(深度, 16UC1归一化) /ir(红外, 16UC1归一化)

# ========== 步骤 6: 启动STM32控制节点（依赖串口）==========
cd /home/nvidia/name_zhoushifei/WS
source install/setup.bash
ros2 run stm32_control stm32_control_node
# 输出: 串口 /dev/ttyACM3 连接成功

# ========== 步骤 7: 启动超声波节点（可选）==========
cd /home/nvidia/name_ranhongmei/ws
source install/setup.bash
ros2 run fist_demo_uart wave_length_node
```

### 4.3 启动依赖关系图

```
rosbridge_server (9090)
        │
        ├─────────────────────────────────────┐
        │                                     │
        ▼                                     ▼
Orbbec相机 ──► camera_http_node (8082)   stm32_control_node
                    │                           │
                    ▼                           ▼
              HTTP视频流                    /dev/ttyACM3
              (前端<img>)                    STM32
```

---

## 5. 视频流 (HTTP) vs 传感器数据 (ROS)

### 5.1 为什么视频用 HTTP/MJPEG？

```
┌─────────────────────────────────────────────────────────────┐
│  视频流特点                                                  │
│  ─────────                                                   │
│  • 数据量大 (1280x720@10fps ≈ 2-4 Mbps)                      │
│  • 单向传输 (相机 → 前端)                                    │
│  • 允许一定延迟 (100-500ms 可接受)                           │
│  • 需要自动重连机制                                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  HTTP/MJPEG 优势                                             │
│  ───────────────                                             │
│  ✅ 浏览器原生支持 <img src="...">                            │
│  ✅ 自动处理分包、缓冲、重连                                  │
│  ✅ 无需额外JavaScript库                                     │
│  ✅ 带宽压力小 (流式传输，无需一次性加载)                      │
│  ✅ 与ROS解耦，独立运行                                       │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 为什么传感器用 WebSocket/ROS？

```
┌─────────────────────────────────────────────────────────────┐
│  传感器数据特点                                              │
│  ───────────────                                             │
│  • 数据量小 (几十字节)                                        │
│  • 需要实时性 (<100ms)                                        │
│  • 双向通信 (控制指令 + 状态反馈)                              │
│  • 多数据源 (超声波、定位、状态)                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  WebSocket/ROS 优势                                          │
│  ──────────────────                                          │
│  ✅ 双向实时通信 (<10ms延迟)                                  │
│  ✅ 服务器主动推送 (无需轮询)                                  │
│  ✅ 统一消息总线 (多话题管理)                                  │
│  ✅ 一条连接多用途 (视频+控制+传感器)                          │
│  ✅ 与ROS生态无缝集成                                         │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 两种协议的实现对比

#### 视频流 - HTTP/MJPEG

**后端实现** (`camera_http_node.py`):
```python
# 订阅ROS相机话题
self.subscription = self.create_subscription(
    Image,
    '/camera/color/image_raw',  # 输入: ROS话题
    self.image_callback,
    10
)

# HTTP服务器提供MJPEG流
self.server = ThreadedHTTPServer((host, port), MJPEGHandler)
# 输出: http://192.168.0.2:8082/camera
```

**前端实现**:
```html
<!-- 原生img标签即可 -->
<img src="http://192.168.0.2:8082/camera" alt="Camera Stream">
```

```javascript
// 错误处理和自动重连
const img = document.getElementById('camera');
img.onerror = () => {
    console.log('视频流断开，5秒后重连...');
    setTimeout(() => {
        img.src = 'http://192.168.0.2:8082/camera?' + Date.now();
    }, 5000);
};
```

**更新说明（最新版）**：HTTP 视频节点已升级为 **3 路 MJPEG 流**：
- `/camera`（彩色，订阅 `/camera/color/image_raw`）
- `/depth`（深度，`/camera/depth/image_raw` 16UC1 → 归一化灰度）
- `/ir`（红外，`/camera/left_ir/image_raw`）

节点通过 `urlparse(self.path).path` **剥离 URL 查询串**，因此前端追加 `?t=...&r=...` 时间戳强制刷新也能正确匹配，不会 404。三个流均由前端 `<img>` 直连 HTTP，**不经过 rosbridge 转发视频**，避免视频占用 rosbridge 内存/CPU。工业相机页可一键切换 彩色/YOLO识别/深度图/红外图，全部走 HTTP 直连。

#### 传感器数据 - WebSocket/ROS

**后端实现** (`stm32_control_node.py`):
```python
# ROS发布者 (数据会转发到WebSocket)
self.status_publisher = self.create_publisher(
    String,
    '/stm32_status',  # 输出: ROS话题 → WebSocket
    10
)
```

**前端实现**:
```javascript
// 引入 roslibjs
import ROSLIB from 'roslib';

// 连接ROS Bridge
const ros = new ROSLIB.Ros({
    url: 'ws://192.168.0.2:9090'
});

// 订阅传感器话题
const statusTopic = new ROSLIB.Topic({
    ros: ros,
    name: '/stm32_status',
    messageType: 'std_msgs/String'
});

// 实时接收数据（无需轮询）
statusTopic.subscribe((msg) => {
    console.log('STM32状态:', msg.data);  // "online" or "offline"
});
```

---

## 6. 前端与后端的数据流

### 6.1 控制指令流

```
┌──────────┐      ┌──────────────┐      ┌──────────────┐      ┌─────────┐
│  前端     │      │  ROS Bridge  │      │  STM32控制   │      │  STM32  │
│  (Vue)   │      │   :9090      │      │   节点       │      │         │
└────┬─────┘      └──────┬───────┘      └──────┬───────┘      └────┬────┘
     │                   │                     │                   │
     │  1. 点击前进按钮   │                     │                   │
     │  {data: 3}        │                     │                   │
     ├──────────────────►│                     │                   │
     │   WebSocket       │                     │                   │
     │                   │  2. 转发ROS消息      │                   │
     │                   │  /stm32_cmd          │                   │
     │                   ├────────────────────►│                   │
     │                   │                     │  3. 串口发送       │
     │                   │                     │  "3\n"            │
     │                   │                     ├──────────────────►│
     │                   │                     │                   │
     │                   │  4. 返回执行结果     │                   │
     │                   │  /stm32_result       │                   │
     │                   │◄────────────────────┤                   │
     │  5. 前端接收反馈   │                     │                   │
     │  "success: 前进"  │                     │                   │
     │◄──────────────────┤                     │                   │
     │                   │                     │                   │
```

### 6.2 传感器数据流

```
┌──────────┐      ┌──────────────┐      ┌──────────────┐      ┌─────────┐
│  前端     │      │  ROS Bridge  │      │  超声波节点   │      │ 传感器  │
│  (Vue)   │      │   :9090      │      │              │      │         │
└────┬─────┘      └──────┬───────┘      └──────┬───────┘      └────┬────┘
     │                   │                     │                   │
     │  1. 订阅话题       │                     │                   │
     │  /wave_length     │                     │                   │
     ├──────────────────►│                     │                   │
     │                   │                     │                   │
     │                   │  2. 串口读取数据     │                   │
     │                   │                     │◄──────────────────┤
     │                   │                     │                   │
     │                   │  3. 发布ROS消息      │                   │
     │                   │  /wave_length       │                   │
     │                   │◄────────────────────┤                   │
     │                   │                     │                   │
     │  4. 实时推送前端   │                     │                   │
     │  [1200, 800, ...] │                     │                   │
     │◄──────────────────┤                     │                   │
     │                   │                     │                   │
```

---

## 7. 常见问题排查

### 7.1 前端无法连接 ROS Bridge

```bash
# 检查ROS Bridge是否运行
ss -tlnp | grep 9090

# 检查防火墙
sudo ufw allow 9090

# 查看ROS Bridge日志
tail -f /tmp/rosbridge.log
```

### 7.2 视频流显示不出来

```bash
# 检查HTTP服务
ss -tlnp | grep 8082

# 测试视频流
curl http://192.168.0.2:8082/camera

# 检查相机话题
ros2 topic echo /camera/color/image_raw
```

### 7.3 STM32控制无响应

```bash
# 检查串口设备
ls -la /dev/ttyACM*

# 检查串口权限
sudo chmod 666 /dev/ttyACM3

# 查看控制节点日志
tail -f /tmp/stm32_control.log

# 测试指令发送
ros2 topic pub /stm32_cmd std_msgs/Int32 "{data: 1}"
```

### 7.4 方向控制反了

在 `stm32_control_node.py` 中添加映射修正：

```python
def cmd_callback(self, msg):
    cmd = msg.data
    
    # 软件修正：交换前进和后退
    if cmd == 2:
        cmd = 3
    elif cmd == 3:
        cmd = 2
    
    # ... 后续发送逻辑
```

---

## 8. 扩展开发指南

### 8.1 添加新的传感器话题

**后端** (新建节点):
```python
# new_sensor_node.py
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32

class NewSensorNode(Node):
    def __init__(self):
        super().__init__('new_sensor_node')
        self.publisher = self.create_publisher(Float32, '/new_sensor', 10)
        self.timer = self.create_timer(0.1, self.publish_data)  # 10Hz
    
    def publish_data(self):
        msg = Float32()
        msg.data = read_sensor()  # 读取传感器
        self.publisher.publish(msg)
```

**前端**:
```javascript
const sensorTopic = new ROSLIB.Topic({
    ros: ros,
    name: '/new_sensor',
    messageType: 'std_msgs/Float32'
});

sensorTopic.subscribe((msg) => {
    console.log('传感器数据:', msg.data);
});
```

### 8.2 添加新的控制指令

**后端**:
```python
# 在 cmd_names 中添加新指令
self.cmd_names = {
    # ... 原有指令
    8: '自动清洗模式',  # 新增
}

# 在 cmd_callback 中处理
if cmd == 8:
    self.start_auto_clean()
```

**前端**:
```javascript
// 添加新按钮
<button @click="sendCmd(8)">自动清洗</button>
```

---

## 9. 总结

### 核心技术要点

1. **混合通讯架构**: 视频用 HTTP/MJPEG，控制用 WebSocket/ROS
2. **ROS2 封装**: 将原始串口程序封装为标准 ROS 节点
3. **WebSocket 桥接**: rosbridge_server 实现 Web 与 ROS 的无缝连接
4. **实时性设计**: 控制指令延迟 <10ms，传感器数据推送机制

### 关键文件位置

| 文件 | 路径 | 说明 |
|------|------|------|
| STM32控制节点 | `/home/nvidia/name_zhoushifei/WS/src/stm32_control/` | 核心控制封装 |
| 视频流节点 | `/home/nvidia/name_huanghongle3/camera_http_ws/` | HTTP视频服务（/camera、/depth、/ir 三路流） |
| 交互式管理器（推荐） | `/home/nvidia/name_huanghongle3/robot_service_manager.py` | 服务一键/分项管理 v2.0 |
| 旧启动脚本 | `/home/nvidia/name_huanghongle3/start_all_services.py` | 批量启动所有服务（已非首选） |
| 前端示例 | `/home/nvidia/name_zhoushifei/frontend_example/` | 参考实现 |

---

**文档版本**: v1.0（更新到最新版，深度/红外已启用）  
**创建日期**: 2026-03-09  
**作者**: Jetson Engineer + 前端工程师
