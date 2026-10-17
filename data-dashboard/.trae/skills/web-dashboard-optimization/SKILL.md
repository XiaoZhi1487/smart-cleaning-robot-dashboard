---
name: web-dashboard-optimization
description: Optimize this Vue 3 data dashboard web visualizations and frontend performance. Use when improving ECharts charts, Canvas radar drawing, ROS data pipelines, MJPEG streams, or applying performance and cleanup fixes to this repo. Do not use for Python/ROS backend changes.
---

# Web 可视化平台优化

本项目是「智能清洁机器人监控系统」数据大屏，跑在 RK3588 + ROS 2 Humble 上。前端 Vue 3（vue-cli 5 / webpack）。优化可视化平台时遵循本文件。

## 技术栈与结构

- 前端：Vue 3（Composition API 优先）、vue-router（hash 模式，路由懒加载）、Pinia、vue-i18n、axios、ECharts 6、Three.js + TresJS、roslib
- 关键文件：
  - `src/views/Screen1.vue` — 数据大屏首页（ECharts 图表 + SVG 设备图 + 日志 + 控制）
  - `src/views/UltrasonicRadar.vue` — 超声波雷达（Canvas 绘制三方向扇形 + STM32 控制 + ROS 话题）
  - `src/views/DepthCamera.vue` — 工业相机（MJPEG 流 + 清洁评估动画）
  - `src/store/rosState.js` — 全局 ROS 连接状态（reactive）
  - `src/locales/*.js` — 中/英/泰/马来/印尼/越 六语言
  - `vue.config.js` — `@` 别名指向 `src`，devServer 端口 8081

## 优化重点（按优先级）

### 1. ECharts 按需引入（缩小 bundle）
`Screen1.vue` 当前 `import * as echarts from 'echarts'` 会打进全部图表，`dist/js/chunk-vendors` 明显偏大。改为：

```js
import * as echarts from 'echarts/core'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
echarts.use([BarChart, LineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])
```

只注册实际用到的图表与组件，新增图表时同步补充注册。

### 2. ECharts 实例复用，不要反复 dispose+init
`Screen1.vue` 的 `initTodayChart` 每次调用（语言切换 watch、loadData）都 `dispose()` 后重新 `echarts.init()`。改为：
- 首次挂载时 `init`，之后用 `chart.setOption(option, { notMerge: true })` 更新
- `onUnmounted` 再 `dispose()`；窗口 resize 时 `chart.resize()`（已实现）
- 语言切换只需用新的文案重设 `setOption`，无需重建实例

### 3. Canvas 雷达按需重绘 + 高 DPI
`UltrasonicRadar.vue` 的 `drawRadar` 通过 `requestAnimationFrame(drawRadar)` 无条件以 ~60fps 重绘相同内容，即使传感器数据没变。优化：
- 仅在 `sensors` 改变时（`watch`）触发单次重绘，或对数据变化做节流
- `resizeCanvas` 需乘 `devicePixelRatio`，再 `ctx.scale(dpr, dpr)`，否则高分屏发虚
- `onUnmounted` 中已有 `cancelAnimationFrame`，保留

### 4. 资源生命周期（rAF / 定时器 / setTimeout / ROS 话题）
所有异步资源必须在 `onUnmounted` 清理：
- `setInterval` / `setTimeout` / `requestAnimationFrame` 都要持句柄并清除
- 已知隐患：`DepthCamera.vue` 的 `onCameraError` 里 `setTimeout` 重试没保存句柄，切走页面触发 error 时会泄漏，需加清理
- ROSLIB：全局只允许一个 `Ros` 实例；断开时先 `unsubscribe()` 所有 Topic、设 null，再 `ros.close()`；连接前判重防重复连接（`UltrasonicRadar.vue` 已做，`DepthCamera.vue` 也需一致）

### 5. 高频回调里去掉多余 console.log
`processSensorData`、`drawRadar` 等每条消息/每帧都 `console.log`，生产会拖慢。保留关键报错，去掉或改为 `console.debug` 级别。

## 编码规范

- 组件统一用 `<script setup>`；目前 `Screen1.vue` 还是 Options API `export default { setup() }`，改造时向另外两个页面看齐
- 所有用户可见文本必须走 `$t`/`t()`，并在 `src/locales` 全部六个语言文件里同步新增 key；不要在模板里硬编码中文
- 深色主题配色常量：背景 `#0a101f`、主青色 `#00E5FF`、成功 `#00FF96`、警告 `#FFCC00`、错误 `#FF3366`、正文 `#e6f7ff`、次要 `#8b9bb4`
- 卡片为统一结构 `.card > .card-header + .card-body`，多页重复的卡片样式可上提到 `src/assets/css/common.css`，页面特有样式保留 `scoped`
- 日志/列表类高频数据保持“上限截断”（当前 20 条），避免无限增长

## 数据流说明
- 首页（Screen1）目前为 mock 数据（`requestMock`），接入真实接口时保持同样的 `{ code, data }` 结构
- 雷达页通过 rosbridge `ws://<ip>:9090` 订阅 `/wave_length`（UInt8MultiArray，3 传感器 × 2 字节），并发布 `/stm32_cmd`（Int32）、订阅 `/stm32_result`、`/stm32_status`
- 相机页 MJPEG 由本机后端标注后输出 `http://localhost:8083/camera`，重试时用 `?t=Date.now()` 防缓存

## 改动后自测
1. `npm run serve`，确认首页/雷达/相机三页正常渲染，无控制台报错
2. `npm run build`，观察 `dist/js/chunk-vendors` 体积是否下降
3. 三页间来回切换，确认无定时器/rAF 仍在跑（可在 onUnmounted 打点或 DevTools Performance 观察）