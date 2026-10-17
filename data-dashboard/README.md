# 智能清洁机器人数据可视化系统（data-dashboard）

基于 **Vue 3 + ROS 2** 的清洁机器人数据可视化监控平台。系统通过 WebSocket 实时接收传感器数据，提供数据大屏、超声波雷达监控、工业相机（YOLO 污渍标注）监控，并支持 Web 端遥控机器人。

## 功能

- 📊 **数据大屏**：设备状态总览、机器人作业视图、今日作业统计（ECharts）、实时工作日志
- 🎮 **机器人控制**：方向键 / WASD 遥控机器人
- 📡 **超声波雷达**：4 路超声波数据 + Canvas 雷达可视化 + STM32 指令下发
- 📷 **工业相机**：YOLO 污渍识别，前端显示带标注视频流
- 🌐 **多语言**：中文 / English / ไทย / Bahasa Melayu / Bahasa Indonesia / Tiếng Việt

## 技术栈

Vue 3 · Vue CLI · Pinia · vue-i18n · ECharts 6 · roslib · YOLO (Flask/OpenCV) · ROS 2 Humble

## 快速开始

```bash
# 前端（端口 8081）
npm install
npm run serve

# 超声波 UDP + WebSocket 转发服务
python sensor_server.py

# 工业相机 YOLO 标注服务（端口 8083）
cd src/camera_yolo_server
python camera_yolo_server.py --camera http://192.168.0.3:8082/camera --port 8083
```

浏览器访问 `http://localhost:8081`。

## 目录结构

```
src/
├── views/        # 页面组件（Layout / Screen1 / UltrasonicRadar / DepthCamera）
├── store/        # 全局 ROS 连接状态
├── locales/      # 六语言词条
├── router/       # 路由配置
└── camera_yolo_server/   # YOLO 相机标注服务
```

## 生产构建

```bash
npm run build
```

详见 [项目书.md](./项目书.md)。
