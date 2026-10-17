<template>
  <div class="camera-container">
    <!-- 页面标题 -->
    <div class="screen-title">📷 {{ $t('camera.pageTitle') }}</div>

    <!-- 主内容区 - 使用 flex 布局 -->
    <div class="content-area">
      <!-- 左侧区域：工业相机视频显示 -->
      <div class="left-section">
        <!-- 工业相机视频流 -->
        <div class="card main-image-card">
          <div class="card-header">
            <span class="card-title">📷 {{ $t('camera.cameraView') }}</span>
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
                <div class="placeholder-icon">📷</div>
                <div>{{ $t('camera.waiting') }}</div>
              </div>
              <div v-else-if="!cameraConnected && cameraRetryCount > 0 " class="no-image">
                <div class="placeholder-icon">🔄</div>
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
            <span class="card-title">📹 {{ $t('camera.cameraInfo') }}</span>
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
            <span class="card-title">🧽 {{ $t('camera.liveStatus') }}</span>
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
            <span class="card-title">📋 {{ $t('camera.connLog') }}</span>
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
import { ref, onMounted, onUnmounted, computed } from 'vue'
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
  min-height: 260px;
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
  width: 100%;
  height: auto;
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
</style>
