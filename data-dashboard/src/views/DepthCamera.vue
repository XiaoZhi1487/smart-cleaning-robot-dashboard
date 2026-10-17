<template>
  <div class="camera-container">
    <!-- 页面标题 -->
    <div class="screen-title">📷 {{ $t('camera.pageTitle') }}</div>
    
    <!-- 连接状态面板 -->
    <div class="connection-panel">
      <div class="status-group">
        <div class="status-dot" :class="{ connected: isConnected }"></div>
        <span class="status-text">{{ connectionStatus }}</span>
      </div>
      
      <div class="config-group">
        <label>{{ $t('radar.deviceIp') }}</label>
        <input 
          v-model="serverIp" 
          type="text" 
          placeholder="192.168.0.3"
          :disabled="isConnected"
          class="server-input"
        />
        <label>{{ $t('radar.port') }}</label>
        <input 
          v-model="serverPort" 
          type="text" 
          placeholder="9090"
          :disabled="isConnected"
          class="port-input"
        />
        <button 
          @click="connectROS" 
          :disabled="isConnected"
          class="btn btn-connect"
        >
          {{ $t('radar.connect') }}
        </button>
        <button 
          @click="disconnectROS" 
          :disabled="!isConnected"
          class="btn btn-disconnect"
        >
          {{ $t('radar.disconnect') }}
        </button>
      </div>
    </div>

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
<!-- <div>📷🔄</div> -->
          <!-- <div class="card-body image-body">
            <div class="image-wrapper">
              <img
                :src="cameraUrl"
                alt="Camera Stream"
                class="camera-stream"
                @load="onCameraLoad"
                @error="onCameraError"
              />
              <div v-if="!cameraConnected && cameraRetryCount === 0" class="no-image">
                <div class="placeholder-icon">📷</div>
                <div>等待工业相机连接...</div>
              </div>
              <div v-else-if="!cameraConnected && cameraRetryCount > 0" class="no-image">
                <div class="placeholder-icon">🔄</div>
                <div>正在连接工业相机 ({{ cameraRetryCount }}/{{ maxRetries }})...</div>
              </div>
            </div>
          </div> -->
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
                <div class="stat-value">640 x 360</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">{{ $t('camera.frameRate') }}</div>
                <div class="stat-value">10 FPS</div>
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

        <!-- 清洁评估 -->
        <div class="card clean-card">
          <div class="card-header">
            <span class="card-title">🧽 {{ $t('camera.cleanAssess') }}</span>
          </div>
          <div class="card-body clean-body">
            <div class="clean-value" :class="{ 'not-qualified': !cleanQualified }">
              {{ cleanRatingDisplay }}%
            </div>
            <div class="clean-status" :class="{ 'not-qualified': !cleanQualified }">
              {{ cleanQualified ? $t('camera.cleanQualified') : $t('camera.cleanUnqualified') }}
            </div>
            <div class="clean-bar">
              <div class="clean-bar-fill" :class="{ 'not-qualified': !cleanQualified }" :style="{ width: cleanRating + '%' }"></div>
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
import { updateRosState } from '@/store/rosState'

const { t } = useI18n()


// ===== 配置 =====
const serverIp = ref('192.168.0.3')
const serverPort = ref('9090')
const isConnected = ref(false)
const ros = ref(null)
const depthListener = ref(null)

// 工业相机配置
const cameraConnected = ref(false)
const cameraError = ref('')
// 摄像头显示改为指向本机 YOLO 识别服务输出的带标注流(原流 192.168.0.3:8082 由本机后端做标注)
const cameraUrl = ref('http://localhost:8083/camera')
const cameraRetryCount = ref(0)
const maxRetries = 3

// 清洁评估百分比（91.5% ~ 92.5% 循环动画，每秒递增 0.1）
const cleanRating = ref(91.5)
// 清洁达标阈值（最低标准）
const CLEAN_THRESHOLD = 91.5
const CLEAN_MIN = 91.5
const CLEAN_MAX = 92.5
const CLEAN_STEP = 0.1 // 每秒递增 0.1
let cleanAnimFrame = null
let cameraRetryTimer = null
const cleanQualified = computed(() => cleanRating.value >= CLEAN_THRESHOLD)

// 数值显示（保留 1 位小数，避免出现超长小数）
const cleanRatingDisplay = computed(() => cleanRating.value.toFixed(1))

// 循环动画：91.5 -> 92.5，达到上限后立即重置为 91.5 重新增长
const startCleanAnim = () => {
  let cycleStart = null
  const step = (timestamp) => {
    if (cycleStart === null) cycleStart = timestamp
    const elapsed = (timestamp - cycleStart) / 1000 // 秒
    let value = CLEAN_MIN + CLEAN_STEP * elapsed
    if (value >= CLEAN_MAX) {
      value = CLEAN_MAX
      cycleStart = timestamp // 达到上限，立即开启新一轮
    }
    cleanRating.value = value
    cleanAnimFrame = requestAnimationFrame(step)
  }
  cleanAnimFrame = requestAnimationFrame(step)
}

// 数据日志
const logs = ref([])

// 连接状态文本
const connectionStatus = computed(() => {
  if (isConnected.value) return t('radar.connected')
  return t('radar.notConnected')
})

// 工业相机状态文本
const cameraStatus = computed(() => {
  if (cameraConnected.value) return t('camera.live')
  return t('camera.cameraNotConnected')
})

// ===== 生命周期 =====
onMounted(() => {
  window.addEventListener('resize', handleResize)
  startCleanAnim()
})

onUnmounted(() => {
  if (cleanAnimFrame) cancelAnimationFrame(cleanAnimFrame)
  if (cameraRetryTimer) clearTimeout(cameraRetryTimer)
  disconnectROS()
  window.removeEventListener('resize', handleResize)
})

// ===== 处理窗口大小变化 =====
const handleResize = () => {
  // 可以在这里添加响应式调整逻辑
}

// ===== 工业相机加载成功 ===== 第三处
// const onCameraLoad = () => {
//   cameraConnected.value = true
//   cameraError.value = ''
//   cameraRetryCount.value = 0
//   addLogEntry('工业相机视频流连接成功')
// }

// ===== 工业相机加载失败 ===== 第四处
const onCameraError = () => {
  // MJPEG 流可能会在加载过程中触发 error，但不一定是真正的错误
  // 只记录日志，不立即标记为失败
  console.warn('工业相机视频流加载事件触发')
  
  // 如果已经连接成功，忽略错误（可能是流中断后的正常重连）
  if (cameraConnected.value) {
    console.log('忽略错误：工业相机已经连接')
    return
  }
  
  // 限制重试次数 第五处
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

// ===== ROS 连接 =====第六处
const connectROS = () => {
  if (isConnected.value) return       // 防止重复连接
  
  const url = `ws://${serverIp.value}:${serverPort.value}`
  
  ros.value = new ROSLIB.Ros({ url })       // 创建 ROS 连接对象
  // 连接成功回调
  ros.value.on('connection', () => {
    console.log('✅ Connected to ROS 2 bridge')
    isConnected.value = true
    updateRosState(url, true)
    subscribeToTopics()         // 订阅话题
  })
    // 错误回调
  ros.value.on('error', (error) => {
    console.error('❌ ROS Connection Error:', error)
    alert(t('radar.connFail', { error }))
  })
    // 关闭回调
  ros.value.on('close', () => {
    console.log('🔌 ROS Connection Closed')
    isConnected.value = false
    updateRosState(null, false)
  })
}

const disconnectROS = () => {
  if (depthListener.value) {
    depthListener.value.unsubscribe()
    depthListener.value = null
  }
  
  if (ros.value) {
    ros.value.close()
    ros.value = null
  }
  
  isConnected.value = false
  updateRosState(null, false)
}

// ===== 订阅话题 ===== 第七处
// const subscribeToTopics = () => {
//   // 深度图像话题（保留ROS连接，但不再处理深度图像）
//   depthListener.value = new ROSLIB.Topic({
//     ros: ros.value,
//     name: '/camera/depth/image_rect_raw',
//     messageType: 'sensor_msgs/Image'
//   })
  
//   depthListener.value.subscribe(() => {
//     console.log('收到深度图像数据，但当前使用RK3588工业相机视频流')
//   })
// }

// ===== 添加日志 =====
const addLogEntry = (message) => {
  const now = new Date()
  const timeStr = now.toLocaleTimeString()
  
  logs.value.unshift({
    time: timeStr,
    message: message
  })
  
  // 限制日志数量
  if (logs.value.length > 20) {
    logs.value.pop()
  }
}




// ===== 工业相机加载成功 ===== 第三处
const onCameraLoad = () => {
  cameraConnected.value = true
  cameraError.value = ''
  cameraRetryCount.value = 0
  addLogEntry(t('camera.loadSuccess'))
}



const subscribeToTopics = () => {
  depthListener.value = new ROSLIB.Topic({
    ros: ros.value,
    name: '/camera/depth/image_rect_raw',
    messageType: 'sensor_msgs/Image'
  })
  depthListener.value.subscribe(() => {
    console.log('收到深度图像数据,但当前使用RK3588工业相机数据流')
  })
}



// const subscribeToTopics = () => {
//   // 深度图像话题（保留ROS连接，但不再处理深度图像）
//   depthListener.value = new ROSLIB.Topic({
//     ros: ros.value,
//     name: '/camera/depth/image_rect_raw',
//     messageType: 'sensor_msgs/Image'
//   })
  
//   depthListener.value.subscribe(() => {
//     console.log('收到深度图像数据，但当前使用RK3588工业相机视频流')
//   })
// }










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

/* 连接面板 */
.connection-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(10, 16, 31, 0.8);
  border: 1px solid rgba(22, 93, 255, 0.3);
  border-radius: 8px;
  padding: 12px 16px;
  flex-wrap: wrap;
  gap: 12px;
  flex-shrink: 0;
}

.status-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #e74c3c;
  box-shadow: 0 0 8px rgba(231, 76, 60, 0.5);
  transition: all 0.3s;
}

.status-dot.connected {
  background: #00FF96;
  box-shadow: 0 0 8px rgba(0, 255, 150, 0.5);
}

.status-text {
  font-size: 0.8125rem;
  color: #e6f7ff;
}

.config-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.config-group label {
  color: #8b9bb4;
  font-size: 0.8125rem;
}

.server-input, .port-input {
  padding: 6px 10px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(22, 93, 255, 0.3);
  border-radius: 4px;
  color: #fff;
  font-size: 0.8125rem;
}

.server-input {
  width: 148px;
}

.port-input {
  width: 76px;
}

.btn {
  padding: 6px 14px;
  border: none;
  border-radius: 4px;
  font-size: 0.8125rem;
  cursor: pointer;
  transition: all 0.3s;
  font-weight: 600;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-connect {
  background: #00E5FF;
  color: #0a101f;
}

.btn-connect:hover:not(:disabled) {
  background: #00B8D4;
  box-shadow: 0 0 12px rgba(0, 229, 255, 0.4);
}

.btn-disconnect {
  background: #FF3366;
  color: #fff;
}

.btn-disconnect:hover:not(:disabled) {
  background: #E53950;
}

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

/* 卡片样式 */
.card {
  background: rgba(10, 16, 31, 0.8);
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(22, 93, 255, 0.2);
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.card-header {
  min-height: 36px;
  display: flex;
  align-items: center;
  padding: 0 12px;
  font-size: 0.8125rem;
  font-weight: 600;
  color: #00E5FF;
  background: rgba(22, 93, 255, 0.1);
  border-bottom: 1px solid rgba(22, 93, 255, 0.2);
  flex-shrink: 0;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 6px;
}

.card-body {
  flex: 1;
  padding: 12px;
  overflow: auto;
  min-height: 0;
}

/* 图像容器 */
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

/* 清洁评估 */
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

.clean-bar {
  width: 100%;
  height: 8px;
  background: rgba(22, 93, 255, 0.15);
  border-radius: 4px;
  overflow: hidden;
}

.clean-bar-fill {
  height: 100%;
  background: linear-gradient(to right, #00E5FF, #00FF96);
  border-radius: 4px;
  transition: width 0.5s;
}

.clean-bar-fill.not-qualified {
  background: linear-gradient(to right, #FF3366, #FF9933);
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
  .connection-panel {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
