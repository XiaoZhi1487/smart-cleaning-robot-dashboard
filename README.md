# 智能清洁机器人数据可视化监控大屏

面向智能清洁机器人的实时数据可视化监控系统。前端通过 **ROS2 (roslib WebSocket)** 订阅机器人话题，直连设备端 **HTTP MJPEG** 视频流，配合 **YOLO 目标检测** 在视频上叠加识别结果，以数据大屏方式呈现设备状态、传感器数据与相机画面。

> 支持 6 种语言：简体中文 / English / Tiếng Việt / Bahasa Melayu / ไทย / Bahasa Indonesia。

## 项目结构

```
shujudaping/
├── data-dashboard/               # 前端 + YOLO 标注后端
│   ├── serve-all.js              # 并行启动脚本（前端 + YOLO 后端）
│   ├── package.json
│   ├── public/
│   └── src/
│       ├── views/                # 页面组件
│       │   ├── Layout.vue            # 布局（侧边栏 + 状态栏：ROS IP/端口/CAM 地址）
│       │   ├── Screen1.vue           # 数据大屏（设备状态总览、波形、日志）
│       │   ├── UltrasonicRadar.vue   # 超声波传感器（距离趋势 + 雷达扫描）
│       │   └── DepthCamera.vue       # 工业相机（彩色/YOLO/深度/红外视图切换）
│       ├── router/index.js       # 路由配置
│       ├── store/rosState.js     # ROS WebSocket 连接与话题订阅状态管理
│       ├── locales/              # 6 种语言国际化文案
│       ├── assets/css/           # 全局样式
│       └── camera_yolo_server/   # YOLO 标注后端（Flask）
│           └── camera_yolo_server.py
├── camera_http_node_v2.py        # 设备端相机 HTTP 节点（彩色/深度/红外 MJPEG 流）本地参考副本
└── README.md
```

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + vue-router + Pinia + ECharts + vue-i18n |
| ROS 通信 | roslib（WebSocket，默认 `ws://192.168.0.2:9090`） |
| 视频流 | 设备端 HTTP MJPEG 直连（不经 rosbridge，降低设备负载） |
| 目标检测 | YOLO 后端（Flask + Ultralytics + PyTorch，GPU） |
| 目标设备 | ROS 2 Humble / Ubuntu（Jetson），Orbbec 奥比中光 Gemini 336（G40155-180）双目相机 |

> 项目不依赖 MySQL，也无需独立的业务后端服务；实时数据全部来自 ROS 话题与设备 HTTP 流。

## 后端环境配置（YOLO / GPU）

YOLO 标注后端依赖 **系统 Python 3.9 + GPU 版 PyTorch**。项目**不使用 venv**，依赖直接装到系统 Python 环境。

已装核心依赖（torch 2.8.0+cu128、torchvision 0.23.0+cu128、ultralytics 8.4.180、opencv-python、Pillow、flask、paramiko 等），管理员 PowerShell 下安装命令：

```powershell
# 1) 卸载可能残留的 CPU torch
& "E:\python\Python39\python.exe" -m pip uninstall -y torch torchvision

# 2) 装官方 GPU 版 torch+torchvision（cu128，GPU 加速）
& "E:\python\Python39\python.exe" -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128

# 3) 装 ultralytics 及剩余依赖（普通源即可）
& "E:\python\Python39\python.exe" -m pip install ultralytics
```

> 注意：`--index-url https://download.pytorch.org/whl/cu128` 为官方 GPU wheel 源；阿里云 `cu128` 索引源无可用版本，不要用 `--index-url https://mirrors.aliyun.com/pytorch-wheel/cu128/`。

## 功能模块

- **数据大屏（Dashboard）**：设备状态总览（ROS 通信、STM32、前/左/右超声波、在线终端、相机在线、CPU/相机 RGB 温度、设备开机时长）、波形趋势、运行日志。
- **超声波传感器**：前/左/右超声波距离实时趋势图（对数 y 轴，覆盖 100mm–70 000mm 大跨度）、带旋转扫描动效的雷达图。
- **工业相机**：彩色原图 / YOLO 识别 / 深度图 / 红外图一键切换，视频流参数与设备信息展示、YOLO 检测统计。

## 安装运行

前置：设备端已启动相机 HTTP 服务（8082）与 ROS 话题；本机已装系统 Python 3.9 + GPU 版 PyTorch。

```bash
cd data-dashboard
npm install
npm run serve    # 一键同时启动前端(8080) + YOLO 后端(8083)，Ctrl+C 一起关
```

前端访问 `http://localhost:8080`，YOLO 标注流 `http://localhost:8083/camera`。

## 关键端口

| 端口 | 服务 |
|---|---|
| 8080 | 前端 dev server |
| 8083 | YOLO 标注后端（/camera 流、/info、/uptime、/status） |
| 9090 | 设备端 rosbridge_websocket（ROS WebSocket） |
| 8082 | 设备端相机 HTTP MJPEG 流（/camera 彩色、/depth 深度、/ir 红外） |

## 主要 ROS 话题

- `/camera/color/image_raw`、`/camera/depth/image_raw`、`/camera/left_ir/image_raw`：相机彩色/深度/红外
- `/camera/device_status`、`/camera/color/camera_info`、`/diagnostics`：相机状态、分辨率、温度
- `/wave_length`：超声波距离（前/左/右）
- `/stm32_status`、`/stm32_result`：STM32 控制状态与执行结果
- `/client_count`：在线终端数

## 构建部署

```bash
cd data-dashboard
npm run build   # 输出到 dist/
```

## 作者

胡钰迈 (hu-yumai) · 黄鸿乐 (huangongle) · 蒙虹伶 (mon-ling)
