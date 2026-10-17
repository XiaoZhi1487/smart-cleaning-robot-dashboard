<template>
  <div class="camera-container">
    <!-- 页面标题 -->
    <div class="screen-title"><svg class="icon-svg" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg> {{ $t('camera.pageTitle') }}</div>

    <!-- 主内容区 - 使用 flex 布局 -->
    <div class="content-area">
      <!-- 左侧区域：工业相机视频显示 -->
      <div class="left-section">
        <!-- 工业相机视频流 -->
        <div class="card main-image-card">
          <div class="card-header">
            <span class="card-title"><svg class="icon-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg> {{ $t('camera.cameraView') }}</span>
            <span class="camera-status" :class="{ active: cameraConnected }">
              {{ cameraStatus }}
            </span>
          </div>
          <div class="card-body image-body">
            <div class="image-wrapper">
              <img 
              v-show="cameraConnected"
              :src="displayUrl" 
              alt="camera stream"
              class="camera-stream"
              @load="onCameraLoad"
              @error="onCameraError"
              >
              <div v-if="!cameraConnected && cameraRetryCount === 0 " class="no-image">
                <div class="placeholder-icon"><svg class="icon-svg" viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg></div>
                <div>{{ $t('camera.waiting') }}</div>
              </div>
              <div v-else-if="!cameraConnected && cameraRetryCount > 0 " class="no-image">
                <div class="placeholder-icon"><svg class="icon-svg spin" viewBox="0 0 24 24" width="34" height="34" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.22-8.56"/></svg></div>
                <div >{{ $t('camera.loadRetry', { count: cameraRetryCount, max: maxRetries }) }}</div>
              </div>
            </div>
            <!-- 视频源切换：默认 ROS 话题，可切换到 YOLO HTTP 流 -->
            <div class="source-toggle">
              <button class="mini-btn" :class="{ active: sourceMode === 'ros' }" @click="setSource('ros')">
                ROS2 话题 ({{ $t('camera.rosTopic') }})
              </button>
              <button class="mini-btn" :class="{ active: sourceMode === 'python' }" @click="setSource('python')">
                {{ $t('camera.httpStream') }} (http://localhost:8083/camera)
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧区域：工业相机信息 -->
      <div class="right-section">
        <!-- 工业相机信息 -->
        <div class="card stats-card">
          <div class="card-header">
            <span class="card-title"><svg class="icon-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m22 8-6 4 6 4V8z"/><rect x="2" y="6" width="14" height="12" rx="2" ry="2"/></svg> {{ $t('camera.cameraInfo') }}</span>
          </div>
          <div class="card-body">
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-label">{{ $t('camera.videoSource') }}</div>
                <div class="stat-value">RK3588 工业相机</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">{{ $t('camera.resolution') }}</div>
                <div class="stat-value">{{ resolution }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">{{ $t('camera.frameRate') }}</div>
                <div class="stat-value">{{ fpsDisplay }} FPS</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">{{ $t('camera.format') }}</div>
                <div class="stat-value">MJPEG</div>
              </div>
            </div>
          </div>
        </div>

        <!-- 相机实时运行状态（基于真实 ROS 相机话题数据） -->
        <div class="card clean-card">
          <div class="card-header">
            <span class="card-title"><svg class="icon-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/><path d="M20 3v4"/><path d="M22 5h-4"/></svg> {{ $t('camera.liveStatus') }}</span>
          </div>
          <div class="card-body clean-body">
            <div class="clean-value" :class="{ 'not-qualified': !cameraConnected }">
              {{ fpsDisplay }}
            </div>
            <div class="clean-status" :class="{ 'not-qualified': !cameraConnected }">
              {{ cameraConnected ? $t('camera.liveFps') : $t('camera.noFrame') }}
            </div>
            <div class="live-rows">
              <div class="live-row">
                <span class="live-label">{{ $t('camera.videoAddr') }}</span>
                <span class="live-value">{{ videoSourceAddr }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 连接日志（与相机信息、相机实时运行状态并列） -->
        <div class="card log-card">
          <div class="card-header">
            <span class="card-title"><svg class="icon-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 6h13"/><path d="M8 12h13"/><path d="M8 18h13"/><path d="M3 6h.01"/><path d="M3 12h.01"/><path d="M3 18h.01"/></svg> {{ $t('camera.connLog') }}</span>
          </div>
          <div class="card-body log-body">
            <div v-if="logs.length === 0" class="empty-log">
              {{ cameraConnected ? $t('camera.cameraNormal') : $t('camera.waiting') }}
            </div>
            <div v-else class="log-list">
              <div v-for="(log, index) in logs" :key="index" class="log-item">
                <span class="log-time">{{ log.time }}</span>
                <span class="log-data">{{ log.message }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { rosState, subscribeTopic, connectRos, updateVideoSource } from '@/store/rosState'

const { t } = useI18n()

// ===== 工业相机（视频源：默认 ROS 话题，可切换 YOLO HTTP 流）=====
const cameraConnected = ref(false)
const cameraError = ref('')
const cameraUrl = ref(rosState.cameraUrl)
const cameraRetryCount = ref(0)
const maxRetries = 3

// 视频源模式：'ros' = /camera/color/image_raw/compressed 话题；'python' = YOLO HTTP 流
// 与底部状态栏全局切换联动
const sourceMode = computed({
  get: () => rosState.videoSource,
  set: (mode) => updateVideoSource(mode)
})
// ROS 压缩图像帧的对象 URL
const rosFrameUrl = ref('')
let lastFrameObjectUrl = ''
// 当前显示地址
const displayUrl = computed(() => sourceMode.value === 'python' ? cameraUrl.value : rosFrameUrl.value)

// 当前视频源显示地址（随切换的真实地址变化）
const videoSourceAddr = computed(() => {
  if (sourceMode.value === 'python') return rosState.cameraUrl
  const host = rosState.url.replace(/^wss?:\/\//, '')
  return `${host} /camera/color/image_raw/compressed`
})

// 将 ROS 压缩图像(base64 JPEG)转成可显示的 Blob URL
const base64ToBlobUrl = (b64) => {
  const binary = atob(b64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
  const blob = new Blob([bytes], { type: 'image/jpeg' })
  return URL.createObjectURL(blob)
}

// 切换视频源
const setSource = (mode) => {
  sourceMode.value = mode
  cameraRetryCount.value = 0
  if (mode === 'python') {
    cameraUrl.value = `${rosState.cameraUrl}?t=${Date.now()}`
    // 切换后需要等待 HTTP 流加载判断连接状态
    cameraConnected.value = false
    cameraError.value = ''
  } else {
    // ROS 话题模式：已有帧则保持连接
    cameraConnected.value = !!rosFrameUrl.value
  }
  addLogEntry(mode === 'python' ? t('camera.switchHttp') : t('camera.switchRos'))
}

// ===== 真实相机话题数据（来自 /camera/*）=====
// 分辨率 / 帧率（来自 /camera/color/camera_info）
const resolution = ref('--')
// 帧率：由 camera_info 消息到达间隔计算得到（真实值）
const fps = ref(0)
const fpsDisplay = computed(() => fps.value ? fps.value.toFixed(1) : '--')

// 订阅句柄
let cameraInfoListener = null
let compressedListener = null
let cameraRetryTimer = null

// 数据日志
const logs = ref([])

// 工业相机状态文本
const cameraStatus = computed(() => {
  if (cameraConnected.value) return t('camera.live')
  return t('camera.cameraNotConnected')
})

// ===== 生命周期 =====
// 监听状态栏 CAM 地址变化：python 模式下重新加载相机流（加时间戳防缓存）
watch(() => rosState.cameraUrl, (newUrl) => {
  if (sourceMode.value !== 'python') return
  cameraConnected.value = false
  cameraError.value = ''
  cameraRetryCount.value = 0
  cameraUrl.value = `${newUrl}?t=${Date.now()}`
  addLogEntry(t('camera.switchHttp'))
})

onMounted(() => {
  window.addEventListener('resize', handleResize)
  connectRos()
  subscribeToTopics()
  addLogEntry(t('camera.rosConnected'))
})

onUnmounted(() => {
  if (cameraRetryTimer) clearTimeout(cameraRetryTimer)
  if (cameraInfoListener) { cameraInfoListener.unsubscribe(); cameraInfoListener = null }
  if (compressedListener) { compressedListener.unsubscribe(); compressedListener = null }
  if (lastFrameObjectUrl) { URL.revokeObjectURL(lastFrameObjectUrl); lastFrameObjectUrl = '' }
  window.removeEventListener('resize', handleResize)
})

// ===== 处理窗口大小变化 =====
const handleResize = () => {}

// ===== 工业相机加载失败 =====
const onCameraError = () => {
  // ROS 话题模式下由收到帧判定连接，不触发 HTTP 重试
  if (sourceMode.value !== 'python') return
  // MJPEG 流加载阶段会触发 error，但连接后忽略（可能是流短暂中断后正常重连）
  if (cameraConnected.value) return

  cameraRetryCount.value++
  if (cameraRetryCount.value <= maxRetries) {
    addLogEntry(t('camera.loadRetry', { count: cameraRetryCount.value, max: maxRetries }))
    // 添加时间戳防止缓存
    cameraRetryTimer = setTimeout(() => {
      cameraUrl.value = `${rosState.cameraUrl}?t=${Date.now()}`
    }, 1000)
  } else {
    cameraConnected.value = false
    cameraError.value = t('camera.loadFail')
    addLogEntry(t('camera.loadFail'))
  }
}

// ===== 工业相机加载成功 =====
const onCameraLoad = () => {
  // 只在断开→连接首次成功时记一次日志,避免每帧重复记录
  const wasConnected = cameraConnected.value
  cameraConnected.value = true
  cameraError.value = ''
  cameraRetryCount.value = 0
  if (!wasConnected) addLogEntry(t('camera.loadSuccess'))
}

// ===== 订阅真实相机话题（使用全局共享连接）=====
const subscribeToTopics = () => {
  // 相机内参：分辨率与消息时间戳（用于实时帧率）
  cameraInfoListener = subscribeTopic('/camera/color/camera_info', 'sensor_msgs/CameraInfo', (msg) => {
    if (msg.width && msg.height) {
      resolution.value = `${msg.width} x ${msg.height}`
    }
    updateFps()
  })

  // 压缩图像话题：默认视频源（实时显示相机画面）
  compressedListener = subscribeTopic('/camera/color/image_raw/compressed', 'sensor_msgs/CompressedImage', (msg) => {
    if (!msg.data) return
    try {
      const url = base64ToBlobUrl(msg.data)
      if (lastFrameObjectUrl) URL.revokeObjectURL(lastFrameObjectUrl)
      lastFrameObjectUrl = url
      rosFrameUrl.value = url
      cameraConnected.value = true
      cameraError.value = ''
      cameraRetryCount.value = 0
    } catch (e) {
      // base64 解析失败则忽略本帧
    }
  })
}

// ===== 实时帧率计算 =====
let lastInfoTime = null
const updateFps = () => {
  const now = Date.now()
  if (lastInfoTime !== null) {
    const diff = now - lastInfoTime
    // 计算瞬时帧率并做轻微平滑，避免抖动
    const inst = 1000 / diff
    fps.value = fps.value === 0 ? inst : fps.value * 0.7 + inst * 0.3
  }
  lastInfoTime = now
}

// ===== 添加日志 =====
const addLogEntry = (message) => {
  const timeStr = new Date().toLocaleTimeString()
  logs.value.unshift({ time: timeStr, message })
  if (logs.value.length > 20) logs.value.pop()
}
</script>

<style scoped>
.camera-container {
  width: 100%;
  height: 100%;
  padding: 14px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.screen-title {
  height: 40px;
  line-height: 40px;
  text-align: center;
  font-size: 1.25rem;
  font-weight: 700;
  color: #00E5FF;
  text-shadow: 0 0 10px rgba(0, 229, 255, 0.5);
  letter-spacing: 2px;
  flex-shrink: 0;
}

/* 连接面板（已移除，相机页 ROS 连接改为自动连接） */

/* 主内容区 - flex 布局 */
.content-area {
  display: flex;
  gap: 16px;
  flex: 1;
  min-height: 0;
}

.left-section {
  flex: 1.2;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.main-image-card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.main-image-card .card-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.right-section {
  flex: 0.8;
  min-width: 300px;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 卡片样式（基础 .card/.card-header/.card-title/.card-body 已上提 common.css） */
.image-body {
  padding: 12px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 10px;
}

/* 视频源切换按钮 */
.source-toggle {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
  width: 100%;
}

.source-toggle .mini-btn {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(22, 93, 255, 0.3);
  color: #8b9bb4;
  border-radius: 4px;
  padding: 5px 10px;
  font-size: 0.75rem;
  cursor: pointer;
  white-space: nowrap;
}

.source-toggle .mini-btn.active {
  background: rgba(0, 229, 255, 0.15);
  border-color: rgba(0, 229, 255, 0.5);
  color: #00E5FF;
}

.image-wrapper {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 100%;
  min-height: 0;
  flex: 1;
}

.camera-canvas {
  max-width: 100%;
  max-height: 100%;
  border-radius: 4px;
  box-shadow: 0 0 15px rgba(0, 229, 255, 0.2);
}

.no-image {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: rgba(10, 16, 31, 0.92);
  border: 1px dashed rgba(22, 93, 255, 0.3);
  border-radius: 4px;
  color: #8b9bb4;
  font-size: 0.875rem;
}

/* 工业相机信息卡片：去掉滚动条 */
.stats-card .card-body {
  overflow: hidden;
}

/* 统计信息网格 */
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 15px;
}

.stat-item {
  background: rgba(22, 93, 255, 0.05);
  border-radius: 6px;
  padding: 12px;
  text-align: center;
  border: 1px solid rgba(22, 93, 255, 0.1);
}

.stat-label {
  font-size: 0.6875rem;
  color: #8b9bb4;
  margin-bottom: 6px;
}

.stat-value {
  font-size: 0.9375rem;
  font-weight: bold;
  color: #00E5FF;
}

.stat-value.warning {
  color: #FF3366;
}

/* 深度图例 */
.depth-legend {
  margin-top: 10px;
}

.legend-title {
  font-size: 0.6875rem;
  color: #8b9bb4;
  margin-bottom: 6px;
}

.legend-bar {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 4px;
  padding: 8px;
}

.legend-gradient {
  height: 16px;
  background: linear-gradient(to right, 
    rgb(0, 0, 255) 0%,
    rgb(0, 255, 255) 25%,
    rgb(0, 255, 0) 50%,
    rgb(255, 255, 0) 75%,
    rgb(255, 0, 0) 100%
  );
  border-radius: 3px;
  margin-bottom: 4px;
}

.legend-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.625rem;
  color: #8b9bb4;
}

/* 底部日志区域 */
.bottom-section {
  flex-shrink: 0;
  height: 140px;
}

.bottom-section .card {
  height: 100%;
}

.log-body {
  padding: 10px;
}

.empty-log {
  text-align: center;
  color: #8b9bb4;
  padding: 30px;
  font-size: 0.8125rem;
}

.log-list {
  font-family: 'Consolas', monospace;
  font-size: 0.6875rem;
}

.log-item {
  display: flex;
  gap: 12px;
  padding: 5px 0;
  border-bottom: 1px solid rgba(22, 93, 255, 0.1);
  color: #e6f7ff;
}

.log-time {
  color: #8b9bb4;
  min-width: 70px;
}

.log-data {
  color: #00E5FF;
}

/* 工业相机样式 */
.camera-status {
  font-size: 0.75rem;
  color: #888;
  margin-left: auto;
}

.camera-status.active {
  color: #00FF96;
}

.camera-stream {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
  border-radius: 4px;
  box-shadow: 0 0 15px rgba(0, 229, 255, 0.2);
}

.placeholder-icon {
  font-size: 2.5rem;
  opacity: 0.5;
}

/* 清洁评估（已改为真实相机运行状态） */
.clean-card {
  flex: none;
}

.clean-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  padding: 20px 16px;
}

.clean-value {
  font-size: 2.75rem;
  font-weight: 700;
  color: #00FF96;
  text-shadow: 0 0 16px rgba(0, 255, 150, 0.4);
  line-height: 1;
}

.clean-value.not-qualified {
  color: #FF3366;
  text-shadow: 0 0 16px rgba(255, 51, 102, 0.4);
}

.clean-status {
  font-size: 0.8125rem;
  font-weight: 600;
  color: #00FF96;
}

.clean-status.not-qualified {
  color: #FF3366;
}

/* 实时运行状态行 */
.live-rows {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border-top: 1px solid rgba(22, 93, 255, 0.15);
  padding-top: 10px;
}

.live-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8125rem;
}

.live-label {
  color: #8b9bb4;
}

.live-value {
  color: #00E5FF;
  font-weight: 600;
  font-family: 'Consolas', monospace;
  word-break: break-all;
  text-align: right;
  max-width: 70%;
}

.live-value.ok {
  color: #00FF96;
}

.live-value.warn {
  color: #FFCC00;
}

/* 响应式 */
@media (max-width: 1200px) {
  .content-area {
    flex-direction: column;
  }
  
  .right-section {
    max-width: none;
    flex: none;
  }
  
  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }
}

/* ============ 视觉美化增强（覆盖/强化 common.css 基础样式，纯 scoped CSS） ============ */

/* 卡片：玻璃质感渐变背景 + 顶部高光 + 青色边框 + hover 发光 */
.card {
  background: linear-gradient(180deg, rgba(13, 20, 33, 0.82) 0%, rgba(10, 16, 31, 0.55) 100%);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 229, 255, 0.2);
  border-radius: 8px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

/* 卡片顶部高光 */
.card::after {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0, 229, 255, 0.55), transparent);
  opacity: 0.75;
  pointer-events: none;
}

.card:hover {
  border-color: rgba(0, 229, 255, 0.45);
  box-shadow: 0 0 12px rgba(0, 229, 255, 0.2), 0 4px 24px rgba(0, 0, 0, 0.35);
}

/* 卡片标题：加粗青色 + 轻微发光 */
.card-header {
  font-weight: 700;
  color: #00E5FF;
  background: linear-gradient(90deg, rgba(22, 93, 255, 0.16), rgba(22, 93, 255, 0.04));
  text-shadow: 0 0 8px rgba(0, 229, 255, 0.35);
}

.card-title {
  font-weight: 700;
  color: #00E5FF;
}

/* 视频流容器：圆角 + 内发光边框 + hover 轻微发光 */
.image-wrapper {
  border-radius: 8px;
  padding: 6px;
  background: rgba(0, 0, 0, 0.25);
  box-shadow: inset 0 0 0 1px rgba(0, 229, 255, 0.12), inset 0 0 24px rgba(0, 229, 255, 0.06), 0 0 10px rgba(0, 229, 255, 0.08);
  transition: box-shadow 0.3s ease;
}

.image-wrapper:hover {
  box-shadow: inset 0 0 0 1px rgba(0, 229, 255, 0.3), inset 0 0 24px rgba(0, 229, 255, 0.08), 0 0 14px rgba(0, 229, 255, 0.18);
}

.camera-stream {
  border-radius: 6px;
  border: 1px solid rgba(0, 229, 255, 0.15);
  box-shadow: 0 0 16px rgba(0, 229, 255, 0.18);
  transition: box-shadow 0.3s ease, border-color 0.3s ease;
}

.image-wrapper:hover .camera-stream {
  border-color: rgba(0, 229, 255, 0.35);
  box-shadow: 0 0 22px rgba(0, 229, 255, 0.3);
}

.no-image {
  border-radius: 8px;
  border-color: rgba(0, 229, 255, 0.25);
  background: rgba(10, 16, 31, 0.92);
}

/* 状态标签：胶囊样式 + hover 微高亮 */
.camera-status {
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.5px;
  color: #8b9bb4;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  transition: all 0.25s ease;
}

.camera-status:hover {
  background: rgba(0, 229, 255, 0.12);
  border-color: rgba(0, 229, 255, 0.35);
  box-shadow: 0 0 8px rgba(0, 229, 255, 0.2);
}

.camera-status.active {
  color: #00FF96;
  border-color: rgba(0, 255, 150, 0.35);
  background: rgba(0, 255, 150, 0.08);
  text-shadow: 0 0 8px rgba(0, 255, 150, 0.4);
  box-shadow: 0 0 8px rgba(0, 255, 150, 0.15);
}

.camera-status.active:hover {
  background: rgba(0, 255, 150, 0.14);
  box-shadow: 0 0 12px rgba(0, 255, 150, 0.25);
}

/* 视频源切换按钮：渐变主色 + hover/active/disabled 反馈 */
.source-toggle .mini-btn {
  border-radius: 6px;
  padding: 6px 14px;
  background: linear-gradient(135deg, rgba(22, 93, 255, 0.12), rgba(0, 229, 255, 0.06));
  border: 1px solid rgba(22, 93, 255, 0.3);
  color: #8b9bb4;
  font-weight: 600;
  letter-spacing: 0.3px;
  transition: all 0.25s ease;
}

.source-toggle .mini-btn:hover {
  color: #e6f7ff;
  border-color: rgba(0, 229, 255, 0.5);
  background: linear-gradient(135deg, rgba(22, 93, 255, 0.35), rgba(0, 229, 255, 0.15));
  box-shadow: 0 0 10px rgba(0, 229, 255, 0.25);
  transform: translateY(-1px);
}

.source-toggle .mini-btn:active {
  transform: scale(0.96);
  box-shadow: none;
}

.source-toggle .mini-btn.active {
  background: linear-gradient(135deg, rgba(22, 93, 255, 0.85), rgba(0, 229, 255, 0.7));
  border-color: rgba(0, 229, 255, 0.6);
  color: #ffffff;
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.4);
  box-shadow: 0 0 12px rgba(0, 229, 255, 0.35);
}

.source-toggle .mini-btn.active:hover {
  background: linear-gradient(135deg, rgba(22, 93, 255, 0.95), rgba(0, 229, 255, 0.85));
  box-shadow: 0 0 16px rgba(0, 229, 255, 0.45);
}

.source-toggle .mini-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* 日志条：hover 微高亮 + 时间戳等宽字体 */
.log-item {
  border-radius: 4px;
  padding: 5px 6px;
  transition: background 0.25s ease, box-shadow 0.25s ease;
}

.log-item:hover {
  background: rgba(0, 229, 255, 0.07);
  box-shadow: inset 0 0 0 1px rgba(0, 229, 255, 0.15);
}

.log-time {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.6875rem;
  color: #5a6a7f;
  letter-spacing: 0.3px;
}

/* 数值：等宽字体 + 发光青色数字 */
.stat-item {
  background: linear-gradient(180deg, rgba(22, 93, 255, 0.1), rgba(22, 93, 255, 0.03));
  border: 1px solid rgba(22, 93, 255, 0.15);
  border-radius: 8px;
}

.stat-value {
  font-family: 'Consolas', 'Monaco', monospace;
  font-weight: 700;
  color: #00E5FF;
  text-shadow: 0 0 10px rgba(0, 229, 255, 0.5);
}

.clean-value {
  font-family: 'Consolas', 'Monaco', monospace;
}

.live-value {
  color: #00E5FF;
  text-shadow: 0 0 8px rgba(0, 229, 255, 0.3);
}
</style>
