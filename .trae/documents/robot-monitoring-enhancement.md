# 机器人实时监控平台增强：三项可落地模块

## Context（背景）

用户把 PPT、现有可视化平台、ROS2 话题清单给 GPT，GPT 建议将平台升级为"机器人实时监控与作业管理"，提出 6 类数据。经评估并**通过 rosbridge 实际采集设备（192.168.0.2）19 个话题的真实数据**后确认：

**可直接落地（有真实数据）：**
- 视觉识别增强（YOLO 后端已在跑，可补检测统计）
- 设备健康诊断（`/camera/device_status` 帧率/延迟/在线、`/diagnostics` 温度）
- 告警中心升级（基于现有订阅 + `/diagnostics` level）

**不可落地（无数据源，违反"用真实数据、不做模拟"约束）：**
- 吸附安全防坠监控 —— 设备端**没有**吸附压力/防坠张力话题，仅列为待接入，本次**不做**。
- 位置/路径/清洁进度 —— `/ultrasonic_position` 6 值含义不明，`/tf` 只有相机坐标系，暂不可靠，本次**不做**。

用户选择：实现前三项，**暂不改 Screen1 大屏布局**。改动全部为"现有页面内新增卡片 + 复用现有订阅/轮询机制"，遵循增量升级，不引入新依赖、不新增后端服务（仅扩展现有 YOLO 后端接口）。

---

## 模块 1：视觉识别增强（工业相机页 DepthCamera.vue）

**数据缺口：** YOLO 后端 `camera_yolo_server.py` 的 `/camera` 只输出标注帧，`/status` 只返回模型加载状态，未暴露检测明细。

**后端改动（扩展现有服务，非新增服务）：**
- 在 `process_jpeg()` 里从 `results[0]` 提取检测明细：`results[0].boxes`（`cls`、`conf`），统计各类别出现次数、最高置信度、总检出数，写入全局 `_latest_detections`（只保留最新帧）。
- 新增路由 `/detections`：`jsonify(_latest_detections)`。结构建议：`{ model_loaded, total, items: [{ name, count, max_conf }] }`。
- 复用已有 `_model_status["names"]` 做类别名映射（用索引取类名）。

**前端改动（DepthCamera.vue）：**
- 在右侧栏新增"检测统计"卡片（`sourceMode === 'python'` 时启用）。
- `setInterval` 轮询 `http://localhost:8083/detections`（可复用状态栏 CAM 地址拼 `host`），显示：总检出数、各类别名称 + 数量 + 最高置信度；未检出显示"当前无污渍"。
- 复用现有 `.card` / `.card-title` / `.stats-grid` / `.stat-item` 样式，不新增设计语言。

---

## 模块 2：设备健康诊断（工业相机页 DepthCamera.vue）

**数据来源（真实话题）：**
- `/camera/device_status`（`orbbec_camera_msgs/msg/DeviceStatus`）：`color_frame_rate_cur`、`color_delay_ms_cur`、`device_online`、`connection_type`、`depth_frame_rate_cur`。
- `/diagnostics`（`diagnostic_msgs/msg/DiagnosticArray`）：`status[].values` 含 `CPU Temperature`、`RGB Temperature`、`MainBoard Temperature`、`IR Temperature`（level=0 正常）。

**前端改动：**
- DepthCamera.vue 中新增订阅 `subscribeTopic('/camera/device_status', ...)` 与 `subscribeTopic('/diagnostics', ...)`（复用 store 的 `subscribeTopic`）。
- 右侧栏新增"设备健康"卡片：相机在线状态、实时帧率、延迟、连接类型、CPU/RGB 温度；`device_online === false` 或 `level > 0` 时高亮告警色。
- 复用 `.stats-card` / `.stat-item` 样式；订阅逻辑沿用页面现有的 `onMounted`/`onUnmounted` 模式。

---

## 模块 3：告警中心升级（超声波雷达页 UltrasonicRadar.vue）

**现状：** 操作日志只显示 STM32 指令执行结果（success/error），无等级/来源/筛选。

**前端改动：**
- 将操作日志升级为"事件列表"：每条含 时间、来源（STM32 / 相机 / 系统）、等级标签（提示/警告/严重）、消息。
- 新增订阅 `/diagnostics`：`level > 0` 时插入系统告警事件（来源=相机温度，等级按 level 映射）。
- 顶部加小筛选（可选）：全部 / 告警。不新增后端，纯前端。
- 复用现有 `.log-list` / `.log-item` 结构，扩展 `log.type` 字段驱动等级样式（`error`/`warning`/`info`）。

---

## 不做的内容（明确排除）
- 吸附安全防坠监控：无真实数据源，仅预留，本次不实现任何模拟/占位数据。
- 位置 / 路径 / 清洁进度、任务统计：数据不可靠，不实现。
- Screen1 大屏布局重构：用户明确"暂不改布局"。

## 涉及文件
- `data-dashboard/src/camera_yolo_server/camera_yolo_server.py`（新增 `/detections` 接口 + 检测统计）
- `data-dashboard/src/views/DepthCamera.vue`（模块 1、2 新卡片 + 订阅）
- `data-dashboard/src/views/UltrasonicRadar.vue`（模块 3 事件中心升级）
- 六语言 locale 文件（`zh/en/th/ms/id/vi.js`，新增新卡片标题文案）

## 验证
- `npm run build` 通过。
- 浏览器打开 DepthCamera 页：确认"检测统计"卡片随 YOLO 流刷新、显示检测数量/置信度；"设备健康"卡片显示相机帧率/延迟/温度。
- UltrasonicRadar 页：操作日志显示等级标签，温度告警事件按等级着色。
- 断开 YOLO（停 serve-all 中后端）验证无报错、卡片显示未就绪态。
