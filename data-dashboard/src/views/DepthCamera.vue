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
              :src="cameraUrl" 
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
                <div class="stat-value">{{ $t('camera.industrialCamera') }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">{{ $t('camera.resolution') }}</div>
                <div class="stat-value">{{ resolution }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">{{ $t('camera.frameRate') }}</div>
                <div class="stat-value">{{ fps }} FPS</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">{{ $t('camera.format') }}</div>
                <div class="stat-value">MJPEG</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">{{ $t('camera.connState') }}</div>
                <div class="stat-value" :class="{ warning: !cameraConnected }">
                  {{ cameraConnected ? $t('camera.connected') : $t('camera.disconnected') }}
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-label">{{ $t('camera.videoAddr') }}</div>
                <div class="stat-value" style="font-size: 0.625rem;">localhost:8083</div>
              </div>
            </div>
            
            <!-- 连接说明 -->
            <div class="depth-legend">
              <div class="legend-title">{{ $t('camera.connInfo') }}</div>
              <div class="legend-bar" style="padding: 10px;">
                <div style="font-size: 0.6875rem; color: #8b9bb4; line-height: 1.6;">
                  {{ $t('camera.streamAddr') }}<br/>
                  http://localhost:8083/camera<br/><br/>
                  {{ $t('camera.serverNote') }}<br/>
                  {{ $t('camera.protocolNote') }}
                </div>
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
                <span class="live-label">{{ $t('camera.depthFilter') }}</span>
                <span class="live-value" :class="depthFilterOk ? 'ok' : 'warn'">{{ depthFilterStatus }}</span>
              </div>
              <div class="live-row">
                <span class="live-label">{{ $t('camera.deviceStatus') }}</span>
                <span class="live-value" :class="deviceOk ? 'ok' : 'warn'">{{ deviceStatus }}</span>
              </div>
              <div class="live-row">
                <span class="live-label">{{ $t('camera.resolution') }}</span>
                <span class="live-value">{{ resolution }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部连接日志 -->
    <div class="bottom-section">
      <div class="card">
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
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import ROSLIB from 'roslib'
import { useI18n } from 'vue-i18n'
import { rosState, updateRosState } from '@/store/rosState'

const { t } = useI18n()

// ===== 工业相机（MJPEG 视频流）=====
const cameraConnected = ref(false)
const cameraError = ref('')
const cameraUrl = ref('http://localhost:8083/camera')
const cameraRetryCount = ref(0)
const maxRetries = 3

// ===== 真实相机话题数据（来自 /camera/*）=====
// 分辨率 / 帧率（来自 /camera/color/camera_info）
const resolution = ref('--')
// 帧率：由 camera_info 消息到达间隔计算得到（真实值）
const fps = ref(0)
const fpsDisplay = computed(() => fps.value ? fps.value.toFixed(1) : '--')
// 深度滤波状态（/camera/depth_filter_status, std_msgs/String）
const depthFilterStatus = ref('--')
const depthFilterOk = computed(() => depthFilterStatus.value === 'active' || depthFilterStatus.value === 'enabled' || depthFilterStatus.value.toLowerCase().includes('active'))
// 相机设备状态（/camera/device_status, orbbec_camera_msgs/DeviceStatus）
const deviceStatus = ref('--')
const deviceOk = computed(() => cameraConnected.value && /ok|online|normal/i.test(deviceStatus.value))

// ===== ROS 连接 =====
const isConnected = ref(false)
const ros = ref(null)
let cameraInfoListener = null
let depthFilterListener = null
let deviceStatusListener = null
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
  connectROS()
})

onUnmounted(() => {
  if (cameraRetryTimer) clearTimeout(cameraRetryTimer)
  disconnectROS()
  window.removeEventListener('resize', handleResize)
})

// ===== 处理窗口大小变化 =====
const handleResize = () => {}

// ===== 工业相机加载失败 =====
const onCameraError = () => {
  // MJPEG 流加载阶段会触发 error，但连接后忽略（可能是流短暂中断后正常重连）
  if (cameraConnected.value) return

  cameraRetryCount.value++
  if (cameraRetryCount.value <= maxRetries) {
    addLogEntry(t('camera.loadRetry', { count: cameraRetryCount.value, max: maxRetries }))
    // 添加时间戳防止缓存
    cameraRetryTimer = setTimeout(() => {
      cameraUrl.value = `http://localhost:8083/camera?t=${Date.now()}`
    }, 1000)
  } else {
    cameraConnected.value = false
    cameraError.value = t('camera.loadFail')
    addLogEntry(t('camera.loadFail'))
  }
}

// ===== 工业相机加载成功 =====
const onCameraLoad = () => {
  cameraConnected.value = true
  cameraError.value = ''
  cameraRetryCount.value = 0
  addLogEntry(t('camera.loadSuccess'))
}

// ===== ROS 连接（自动连接，复用全局保存的地址）=====
const connectROS = () => {
  if (isConnected.value) return

  const url = rosState.url
  ros.value = new ROSLIB.Ros({ url })

  ros.value.on('connection', () => {
    isConnected.value = true
    updateRosState(url, true)
    addLogEntry(t('camera.rosConnected'))
    subscribeToTopics()
  })
  ros.value.on('error', (error) => {
    console.error('ROS Connection Error:', error)
    addLogEntry(t('radar.connFail', { error }))
  })
  ros.value.on('close', () => {
    isConnected.value = false
    cameraConnected.value = false
    updateRosState(null, false)
    addLogEntry(t('camera.rosClosed'))
  })
}

const disconnectROS = () => {
  if (cameraInfoListener) { cameraInfoListener.unsubscribe(); cameraInfoListener = null }
  if (depthFilterListener) { depthFilterListener.unsubscribe(); depthFilterListener = null }
  if (deviceStatusListener) { deviceStatusListener.unsubscribe(); deviceStatusListener = null }

  if (ros.value) {
    ros.value.close()
    ros.value = null
  }

  isConnected.value = false
  updateRosState(null, false)
}

// ===== 订阅真实相机话题 =====
const subscribeToTopics = () => {
  // 相机内参：分辨率与消息时间戳（用于实时帧率）
  cameraInfoListener = new ROSLIB.Topic({
    ros: ros.value,
    name: '/camera/color/camera_info',
    messageType: 'sensor_msgs/CameraInfo'
  })
  cameraInfoListener.subscribe((msg) => {
    if (msg.width && msg.height) {
      resolution.value = `${msg.width} x ${msg.height}`
    }
    updateFps()
  })

  // 深度滤波状态
  depthFilterListener = new ROSLIB.Topic({
    ros: ros.value,
    name: '/camera/depth_filter_status',
    messageType: 'std_msgs/String'
  })
  depthFilterListener.subscribe((msg) => {
    depthFilterStatus.value = msg.data
  })

  // 相机设备状态
  deviceStatusListener = new ROSLIB.Topic({
    ros: ros.value,
    name: '/camera/device_status',
    messageType: 'orbbec_camera_msgs/DeviceStatus'
  })
  deviceStatusListener.subscribe((msg) => {
    const raw = msg && msg.data ? msg.data : JSON.stringify(msg || {})
    deviceStatus.value = typeof raw === 'string' ? raw : String(raw)
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
  justify-content: center;
  align-items: center;
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
