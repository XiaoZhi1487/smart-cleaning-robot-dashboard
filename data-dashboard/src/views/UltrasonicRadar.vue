<template>
  <div class="radar-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <svg class="icon-svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12 2 12"/><path d="M22 12a10 10 0 0 0-20 0"/><path d="M6 12a6 6 0 0 1 12 0"/><path d="M10 12a2 2 0 0 1 4 0"/></svg>
        {{ $t('radar.pageTitle') }}
      </h1>
    </div>

    <!-- 连接设置已移至左下角状态栏统一管理 -->

    <div class="content-area">
      <div class="left-section">
        <div class="card">
          <div class="card-header">
            <span class="card-title">{{ $t('radar.sensorData') }}</span>
          </div>
          <div class="card-body">
            <div class="sensor-grid">
              <div v-for="(sensor,index) in sensors" 
              :key="index"
              class="sensor-item"
              :class="{warning : sensor.distance > 0 && sensor.distance < WARNING_THRESHOLD}">
                <div class="sensor-icon"><svg class="icon-svg" :style="{ transform: index === 0 ? 'rotate(-90deg)' : index === 2 ? 'rotate(90deg)' : 'none' }" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12 2 12"/><path d="M22 12a10 10 0 0 0-20 0"/><path d="M6 12a6 6 0 0 1 12 0"/><path d="M10 12a2 2 0 0 1 4 0"/></svg></div>
                <div class="sensor-name">{{ $t(sensor.positionKey) }}</div>
                <div class="sensor-value">  
                  <span class="value-num">{{ sensor.distance > 0 ? sensor.distance : '--' }}</span>
                  <span class="value-unit">mm</span>  
                </div>
                <div class="sensor-status" :class="getSensorStatusClass(sensor)">
                  {{ getSensorStatusText(sensor) }}
                </div>
              </div>
            </div>
          </div>
        </div> 

        <!-- 雷达可视化 - 使用 Canvas 绘制三个方向的雷达图 -->
        <div class="card radar-card">
          <div class="card-header">
            <span class="card-title">{{ $t('radar.radarVisual') }}</span>
          </div>
          <div class="card-body radar-body">
            <canvas ref="radarCanvas" class="radar-canvas"></canvas>
          </div>
        </div>
      </div>

      <div class="right-section">
        <!-- STM32 控制面板 -->
        <div class="card control-card">
          <div class="card-header">
            <span class="card-title"><svg class="icon-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v4"/><path d="m17 5-2 2"/><path d="m7 5 2 2"/><path d="M9 14a3 3 0 0 0 6 0"/><path d="M5 13a7 7 0 0 1 14 0"/></svg> {{ $t('radar.robotControl') }}</span>
            <span class="control-status" :class="{ connected: stm32Connected }">
              {{ stm32Status }}
            </span>
          </div>
          <div class="card-body control-body">
           
            <div class="current-status">
              <span class="status-label">{{ $t('radar.currentCmd') }}</span>
              <span class="status-value" :class="{ active: currentCommand !== $t('radar.standby') }">
                {{ currentCommand }}
              </span>
            </div>

            <!-- 控制按钮区域 -->


            <div class="control-grid">
              <div></div>
              <button class="btn-control btn-dir" @mousedown="sendStm32Cmd('forward')" @mouseup="sendStm32Cmd('stop')" @mouseleave="sendStm32Cmd('stop')"><svg class="icon-svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m12 19 0-14"/><path d="m6 11 6-6 6 6"/></svg><span>{{ $t('radar.forward') }}</span></button>
              <div></div>
              
              <button class="btn-control btn-dir" @mousedown="sendStm32Cmd('turn_left')" @mouseup="sendStm32Cmd('stop')" @mouseleave="sendStm32Cmd('stop')"><svg class="icon-svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12 5 12"/><path d="m11 18-6-6 6-6"/></svg><span>{{ $t('radar.turnLeft') }}</span></button>
              <button class="btn-control btn-stop" @click="sendStm32Cmd('stop')"><svg class="icon-svg" viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg><span>{{ $t('radar.stop') }}</span></button>
              <button class="btn-control btn-dir" @mousedown="sendStm32Cmd('turn_right')" @mouseup="sendStm32Cmd('stop')" @mouseleave="sendStm32Cmd('stop')"><svg class="icon-svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12 19 12"/><path d="m13 6 6 6-6 6"/></svg><span>{{ $t('radar.turnRight') }}</span></button>
              
              <div></div>
              <button class="btn-control btn-dir" @mousedown="sendStm32Cmd('backward')" @mouseup="sendStm32Cmd('stop')" @mouseleave="sendStm32Cmd('stop')"><svg class="icon-svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m12 5 0 14"/><path d="m18 13-6 6-6-6"/></svg><span>{{ $t('radar.backward') }}</span></button>
              <div></div>
            </div>

            <!-- 无刷电机控制 -->
            <div class="brushless-section">
              <div class="section-title"><svg class="icon-svg" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33h.01a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82v.01a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg> {{ $t('radar.brushControl') }}</div>
              <div class="brushless-control">
                <button class="btn-control btn-brushless" @click="sendStm32Cmd('brushless_stop')">
                  <svg class="icon-svg" viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg> {{ $t('radar.stop') }}
                </button>
                <button class="btn-control btn-brushless-start" @click="sendStm32Cmd('brushless_start')">
                  <svg class="icon-svg" viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M13 2 3 14h7l-1 8 10-12h-7z"/></svg> {{ $t('radar.start') }}
                </button>
              </div>
            </div>

            <!-- 急停按钮 -->
            <div class="emergency-section">
              <button class="btn-emergency" @click="emergencyStop">
                <svg class="icon-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg> {{ $t('radar.emergency') }}
              </button>
            </div>

            <!-- 操作日志 -->
            <div class="control-log">
              <div class="log-title"><svg class="icon-svg" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 6h13"/><path d="M8 12h13"/><path d="M8 18h13"/><path d="M3 6h.01"/><path d="M3 12h.01"/><path d="M3 18h.01"/></svg> {{ $t('radar.operationLog') }}</div>
              <div class="log-filter">
                <button :class="{ active: logFilter === 'all' }" @click="logFilter = 'all'">{{ $t('radar.logFilterAll') }}</button>
                <button :class="{ active: logFilter === 'alarm' }" @click="logFilter = 'alarm'">{{ $t('radar.logFilterAlarm') }}</button>
              </div>
              <div class="log-list">
                <div v-if="filteredLogs.length === 0" class="empty-log">{{ $t('radar.waitingOp') }}</div>
                <div v-for="log in filteredLogs" :key="log.id" class="log-item" :class="log.level">
                  <span class="log-level" :class="log.level">{{ logLevelText(log.level) }}</span>
                  <span class="log-src">{{ logSrcText(log.source) }}</span>
                  <span class="log-time">{{ log.time }}</span>
                  <span class="log-msg">{{ log.message }}</span>
                </div>
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
import { rosState, subscribeTopic, publishTopic, connectRos } from '@/store/rosState'

const { t, locale } = useI18n()

// 语言切换后重绘雷达方向标签
watch(locale, () => renderRadar())

// ===== 配置区域（连接地址由左下角状态栏统一管理）=====
const waveLengthListener = ref(null)
const radarCanvas = ref(null)
let canvasCtx = null
let radarSize = 0
// 扫描动画状态：扫描光束角度（弧度）与 RAF 句柄
let scanAngle = 0
let scanRafId = null

// 警告阈值 (mm) - 距离小于此值时显示红色警告
const WARNING_THRESHOLD = 200

// 传感器数据 - 三个超声波传感器：左、前、右
const sensors = ref([
  { positionKey: 'radar.left', distance: 0 },
  { positionKey: 'radar.front', distance: 0 },
  { positionKey: 'radar.right', distance: 0 }
])

// 调试信息
const rawData = ref([])
const parseSuccess = ref(false)
const parseStatus = ref(t('radar.waitingData'))

// ===== STM32 控制模块（ROS 话题方式） =====
const stm32Connected = ref(false)
const stm32Logs = ref([])
const currentCommandKey = ref(null)
const currentCommand = computed(() => {
  return currentCommandKey.value ? t(CMD_LABEL_KEYS[currentCommandKey.value]) : t('radar.standby')
})

// ROS 话题句柄（使用全局共享连接）
let stm32ResultTopic = null
let stm32StatusTopic = null
let diagnosticsTopic = null
let lastDiagKey = ''

// 指令映射：命令名 -> Int32 值
const CMD_MAP = {
  'stop': 1,
  'forward': 3,
  'backward': 2,
  'turn_left': 4,
  'turn_right': 5,
  'brushless_stop': 6,
  'brushless_start': 7
}

// 命令名 -> i18n 键
const CMD_LABEL_KEYS = {
  stop: 'radar.stop',
  forward: 'radar.forward',
  backward: 'radar.backward',
  turn_left: 'radar.turnLeft',
  turn_right: 'radar.turnRight',
  brushless_stop: 'radar.brushStop',
  brushless_start: 'radar.brushStart'
}

// STM32 连接状态文本
const stm32Status = computed(() => {
  return stm32Connected.value ? t('radar.online') : t('radar.offline')
})



// 添加 STM32 日志
let eventSeq = 0
const addStm32Log = (message, isError = false) => {
  const timeStr = new Date().toLocaleTimeString()
  const level = isError ? 'error' : 'info'
  stm32Logs.value.unshift({ id: ++eventSeq, time: timeStr, message, level, source: 'stm32' })
  if (stm32Logs.value.length > 15) stm32Logs.value.pop()
}

// 添加系统/相机告警事件（等级：warning / error）
const addSystemEvent = (message, level = 'warning', source = 'camera') => {
  const timeStr = new Date().toLocaleTimeString()
  stm32Logs.value.unshift({ id: ++eventSeq, time: timeStr, message, level, source })
  if (stm32Logs.value.length > 15) stm32Logs.value.pop()
}

// 日志筛选：全部 / 仅告警
const logFilter = ref('all')
const filteredLogs = computed(() => {
  if (logFilter.value === 'all') return stm32Logs.value
  return stm32Logs.value.filter(l => l.level === 'warning' || l.level === 'error')
})

// 等级/来源文案
const logLevelText = (lvl) =>
  lvl === 'error' ? t('radar.lvlError') : lvl === 'warning' ? t('radar.lvlWarning') : t('radar.lvlInfo')
const logSrcText = (src) =>
  src === 'camera' ? t('radar.srcCamera') : src === 'system' ? t('radar.srcSystem') : t('radar.srcStm32')

// 发送 STM32 控制指令（ROS 话题方式）
const sendStm32Cmd = (command) => {
  if (!rosState.connected) {
    addStm32Log(t('radar.notConnectedLog'), true)
    return
  }
  
  const cmdValue = CMD_MAP[command]
  if (cmdValue === undefined) {
    addStm32Log(t('radar.unknownCmd', { cmd: command }), true)
    return
  }
  
  publishTopic('/stm32_cmd', 'std_msgs/Int32', { data: cmdValue })
  const cmdName = t(CMD_LABEL_KEYS[command] || 'radar.stop')
  addStm32Log(t('radar.sendLog', { cmd: cmdName, value: cmdValue }))
  currentCommandKey.value = command
}

// 急停按钮
const emergencyStop = () => {
  sendStm32Cmd('stop')
  addStm32Log(t('radar.emergencyTriggered'))
}

// 当前按下的键
const pressedKey = ref(null)

// 键盘按下：发送指令
const handleKeyDown = (e) => {
  if (e.repeat) return

  // 毛刷启停快捷键：T 启动，C 停止（忽略大小写）
  const brushKey = e.key.toLowerCase()
  if (brushKey === 't') {
    e.preventDefault()
    sendStm32Cmd('brushless_start')
    return
  }
  if (brushKey === 'c') {
    e.preventDefault()
    sendStm32Cmd('brushless_stop')
    return
  }

  const keyMap = {
    'w': 'forward',
    's': 'backward',
    'a': 'turn_left',
    'd': 'turn_right',
    'ArrowUp': 'forward',
    'ArrowDown': 'backward',
    'ArrowLeft': 'turn_left',
    'ArrowRight': 'turn_right'
  }
  
  if (e.key === ' ') {
    e.preventDefault()
    sendStm32Cmd('stop')
    return
  }
  
  if (keyMap[e.key]) {
    e.preventDefault()
    pressedKey.value = e.key
    sendStm32Cmd(keyMap[e.key])
  }
}

// 键盘松开：发送停止
const handleKeyUp = (e) => {
  const moveKeys = ['w', 's', 'a', 'd', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight']
  
  if (moveKeys.includes(e.key) && pressedKey.value === e.key) {
    pressedKey.value = null
    sendStm32Cmd('stop')
  }
}

// ===== 生命周期钩子 =====
onMounted(() => {
  initCanvas()
  startScanAnimation()
  connectRos()
  subscribeToTopic()
  window.addEventListener('resize', resizeCanvas)
  window.addEventListener('keydown', handleKeyDown)
  window.addEventListener('keyup', handleKeyUp)
})

onUnmounted(() => {
  stopScanAnimation()
  if (waveLengthListener.value) { waveLengthListener.value.unsubscribe(); waveLengthListener.value = null }
  if (stm32ResultTopic) { stm32ResultTopic.unsubscribe(); stm32ResultTopic = null }
  if (stm32StatusTopic) { stm32StatusTopic.unsubscribe(); stm32StatusTopic = null }
  if (diagnosticsTopic) { diagnosticsTopic.unsubscribe(); diagnosticsTopic = null }
  window.removeEventListener('resize', resizeCanvas)
  window.removeEventListener('keydown', handleKeyDown)
  window.removeEventListener('keyup', handleKeyUp)
})

// ===== Canvas 初始化和绘制 =====
// 初始化 Canvas，设置尺寸并开始绘制雷达图
const initCanvas = () => {
  resizeCanvas()
}

// 启动扫描动画：驱动扫描光束角度并持续重绘雷达图
const startScanAnimation = () => {
  stopScanAnimation()
  const tick = () => {
    // 每帧旋转一个固定角度，形成从中心向外扫描的效果
    scanAngle += 0.01
    if (scanAngle > Math.PI * 2) scanAngle -= Math.PI * 2
    renderRadar()
    scanRafId = requestAnimationFrame(tick)
  }
  scanRafId = requestAnimationFrame(tick)
}

// 停止扫描动画
const stopScanAnimation = () => {
  if (scanRafId) {
    cancelAnimationFrame(scanRafId)
    scanRafId = null
  }
}

// 调整 Canvas 绘图缓冲区尺寸以适配容器，并适配高 DPI 屏幕；显示尺寸由 CSS 控制（不设置固定宽高）
const resizeCanvas = () => {
  if (!radarCanvas.value) return
  const container = radarCanvas.value.parentElement
  const w = container.clientWidth || 0
  const h = container.clientHeight || 0
  // 容器尚未完成布局时跳过，避免出现 0 或负尺寸
  if (w <= 0 || h <= 0) return
  radarSize = Math.min(w, h)
  const dpr = window.devicePixelRatio || 1
  // 仅设置绘图缓冲区尺寸，CSS 负责实际显示尺寸（自适应容器）
  radarCanvas.value.width = Math.round(w * dpr)
  radarCanvas.value.height = Math.round(h * dpr)
  canvasCtx = radarCanvas.value.getContext('2d')
  if (canvasCtx) {
    canvasCtx.setTransform(dpr, 0, 0, dpr, 0, 0)
  }
  renderRadar()
}

// 绘制雷达图 - 包含同心圆、十字线、方向标记和传感器数据（仅在尺寸或数据变化时调用）
const renderRadar = () => {
  if (!canvasCtx || !radarCanvas.value) return
  const dpr = window.devicePixelRatio || 1
  const cssW = radarCanvas.value.width / dpr
  const cssH = radarCanvas.value.height / dpr
  radarSize = Math.min(cssW, cssH)
  if (!radarSize) return

  const ctx = canvasCtx
  const centerX = cssW / 2
  const centerY = cssH / 2
  const maxRadius = Math.min(centerX, centerY) - 34

  // 清空画布
  ctx.fillStyle = '#0a101f'
  ctx.fillRect(0, 0, cssW, cssH)

  // 绘制同心圆和距离刻度（125mm, 250mm, 375mm, 500mm）
  ctx.strokeStyle = 'rgba(0, 229, 255, 0.2)'
  ctx.lineWidth = 1
  const rings = [125, 250, 375, 500]

  for (let i = 1; i <= 4; i++) {
    const radius = maxRadius * i / 4
    ctx.beginPath()
    ctx.arc(centerX, centerY, radius, 0, Math.PI * 2)
    ctx.stroke()

    // 标注距离刻度：沿左上对角线排布，避免四个刻度挤在水平轴上重叠
    ctx.fillStyle = 'rgba(0, 229, 255, 0.6)'
    ctx.font = '12px Consolas'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    const labelAngle = -Math.PI * 3 / 4
    ctx.fillText(
      rings[i-1] + 'mm',
      centerX + Math.cos(labelAngle) * radius,
      centerY + Math.sin(labelAngle) * radius
    )
  }

  // 绘制十字线
  ctx.beginPath()
  ctx.moveTo(centerX, centerY - maxRadius)
  ctx.lineTo(centerX, centerY + maxRadius)
  ctx.moveTo(centerX - maxRadius, centerY)
  ctx.lineTo(centerX + maxRadius, centerY)
  ctx.stroke()

  // 绘制方向标记 - 左、前、右
  const directions = [t('radar.left'), t('radar.front'), t('radar.right')]
  const positions = [
    { x: centerX - maxRadius - 18, y: centerY },      // 左 - 9点钟方向
    { x: centerX, y: centerY - maxRadius - 18 },      // 前 - 12点钟方向
    { x: centerX + maxRadius + 18, y: centerY }       // 右 - 3点钟方向
  ]
  ctx.fillStyle = '#00E5FF'
  ctx.font = '14px Microsoft YaHei'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  positions.forEach((pos, i) => ctx.fillText(directions[i], pos.x, pos.y))

  // 绘制传感器数据扇形
  const maxDistance = 500  // 最大显示距离 500mm
  const angles = [Math.PI, -Math.PI / 2, 0]  // 左、前、右的角度

  sensors.value.forEach((sensor, i) => {
    if (sensor.distance > 0) {
      // 计算显示半径（不超过最大半径）
      const displayDistance = Math.min(sensor.distance, maxDistance)
      const radius = (displayDistance / maxDistance) * maxRadius
      const angle = angles[i]

      // 绘制扇形区域
      ctx.beginPath()
      ctx.moveTo(centerX, centerY)
      ctx.arc(centerX, centerY, radius, angle - Math.PI / 6, angle + Math.PI / 6)
      ctx.closePath()

      // 根据距离设置颜色：过近红色，正常青色
      if (sensor.distance < WARNING_THRESHOLD) {
        ctx.fillStyle = 'rgba(255, 51, 102, 0.6)'
        ctx.strokeStyle = '#FF3366'
      } else {
        ctx.fillStyle = 'rgba(0, 229, 255, 0.4)'
        ctx.strokeStyle = '#00E5FF'
      }

      ctx.fill()
      ctx.lineWidth = 2
      ctx.stroke()

      // 绘制距离数值
      const textRadius = radius + 16
      const textX = centerX + Math.cos(angle) * textRadius
      const textY = centerY + Math.sin(angle) * textRadius
      ctx.fillStyle = sensor.distance < WARNING_THRESHOLD ? '#FF3366' : '#00E5FF'
      ctx.font = 'bold 14px Consolas'
      ctx.fillText(sensor.distance + 'mm', textX, textY)
    }
  })

  // 绘制中心点（代表机器人位置）
  ctx.beginPath()
  ctx.arc(centerX, centerY, 7, 0, Math.PI * 2)
  ctx.fillStyle = '#00E5FF'
  ctx.fill()

  // 绘制扫描光束：从中心向外扫描的扇形
  const sweepHalf = Math.PI / 12 // 光束半角（15°）
  // 径向渐变：中心强、边缘淡出，模拟雷达扫描光束
  const beam = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, maxRadius)
  beam.addColorStop(0, 'rgba(0, 229, 255, 0.55)')
  beam.addColorStop(0.6, 'rgba(0, 229, 255, 0.28)')
  beam.addColorStop(1, 'rgba(0, 229, 255, 0)')
  ctx.beginPath()
  ctx.moveTo(centerX, centerY)
  ctx.arc(centerX, centerY, maxRadius, scanAngle - sweepHalf, scanAngle + sweepHalf)
  ctx.closePath()
  ctx.fillStyle = beam
  ctx.fill()

  // 扫描光束前缘亮线
  ctx.beginPath()
  ctx.moveTo(centerX, centerY)
  ctx.lineTo(
    centerX + Math.cos(scanAngle) * maxRadius,
    centerY + Math.sin(scanAngle) * maxRadius
  )
  ctx.strokeStyle = 'rgba(0, 229, 255, 0.9)'
  ctx.lineWidth = 2
  ctx.stroke()
}

// 订阅 ROS 话题 /wave_length（使用全局共享连接）
const subscribeToTopic = () => {
  waveLengthListener.value = subscribeTopic('/wave_length', 'std_msgs/UInt8MultiArray', processSensorData)

  // 订阅执行结果
  stm32ResultTopic = subscribeTopic('/stm32_result', 'std_msgs/String', (msg) => {
    if (msg.data.startsWith('success')) {
      addStm32Log(`✅ ${msg.data}`)
    } else if (msg.data.startsWith('error')) {
      addStm32Log(`❌ ${msg.data}`, true)
    }
  })

  // 订阅 STM32 状态（1Hz 心跳）
  stm32StatusTopic = subscribeTopic('/stm32_status', 'std_msgs/String', (msg) => {
    const wasOffline = !stm32Connected.value
    stm32Connected.value = (msg.data === 'online')

    if (stm32Connected.value && wasOffline) {
      addStm32Log(t('radar.stm32Online'))
    } else if (!stm32Connected.value && !wasOffline) {
      addStm32Log(t('radar.stm32Offline'), true)
    }
  })

  // 订阅设备诊断：level > 0 时生成告警事件（只在状态变化时记录一次，避免刷屏）
  diagnosticsTopic = subscribeTopic('/diagnostics', 'diagnostic_msgs/DiagnosticArray', (msg) => {
    if (!msg.status || !msg.status.length) return
    msg.status.forEach((diag) => {
      if (diag.level > 0) {
        const key = `${diag.name}|${diag.level}`
        if (key === lastDiagKey) return
        lastDiagKey = key
        const lvl = diag.level >= 2 ? 'error' : 'warning'
        addSystemEvent(`${diag.name}: ${diag.message}`, lvl, 'camera')
      }
    })
  })
}

// ===== 【演示代码3】数据解析算法 =====
// 解析 ROS 传来的原始字节数据为距离值
// 数据格式：每2个字节代表一个传感器的距离值（高字节 + 低字节）
// 使用位运算组合16位数值：(highByte << 8) | lowByte
const processSensorData = (message) => {
  // UInt8MultiArray 的数据在 data 字段中
  let data = message.data
  
  // 如果数据是对象，尝试获取 data 属性
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    data = data.data || data
  }
  
  // 检查数据是否为 Base64 编码的字符串，进行解码
  if (typeof data === 'string') {
    try {
      const binaryString = atob(data)
      const bytes = new Uint8Array(binaryString.length)
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i)
      }
      data = Array.from(bytes)
    } catch (error) {
      console.error('Base64 decode error:', error)
      parseSuccess.value = false
      parseStatus.value = t('radar.base64Error')
      return
    }
  }
  
  // 确保数据是数组且长度至少为6字节（3个传感器 × 2字节）
  if (!data || !Array.isArray(data) || data.length < 6) {
    console.error('Invalid data format:', data)
    parseSuccess.value = false
    parseStatus.value = t('radar.dataTooShort', { len: data?.length || 0 })
    return
  }
  
  // 保存原始数据用于调试显示
  rawData.value = [...data]
  
  try {
    // 调整数据顺序：ROS 传来的是 [前方, 左边, 右边]，映射到 [左边, 前方, 右边]
    const sensorMapping = [1, 0, 2] // 索引映射
    // 解析数据：每2个字节代表一个传感器的距离值
    for (let i = 0; i < 3; i++) {
      const index = sensorMapping[i]
      const byte1 = data[index * 2]      // 高字节
      const byte2 = data[index * 2 + 1]  // 低字节
      
      // 转换为数字并确保是无符号字节（0-255）
      const highByte = Number(byte1) & 0xFF
      const lowByte = Number(byte2) & 0xFF
      
      // 使用位运算组合16位数值
      // 例如: high=0x01, low=0x0A → (0x01 << 8) | 0x0A = 0x010A = 266
      const distance = (highByte << 8) | lowByte
      
      // 检查是否为有效数字，防止 NaN 污染数据
      if (isNaN(distance)) {
        console.error(`Sensor ${i}: Calculated distance is NaN!`)
        sensors.value[i].distance = 0
      } else {
        sensors.value[i].distance = distance
      }
    }
    
    parseSuccess.value = true
    parseStatus.value = t('radar.parseSuccess')
  } catch (error) {
    console.error('Error parsing data:', error)
    parseSuccess.value = false
    parseStatus.value = t('radar.parseError', { error: error.message })
  }
  
  // 数据更新后重新绘制雷达
  renderRadar()
}

// ===== 辅助函数 =====
// 获取传感器状态样式类名
const getSensorStatusClass = (sensor) => {
  if (sensor.distance === 0) return 'error'
  if (sensor.distance < WARNING_THRESHOLD) return 'warning'
  return 'normal'
}

// 获取传感器状态文本
const getSensorStatusText = (sensor) => {
  if (sensor.distance === 0) return t('radar.noData')
  if (sensor.distance < WARNING_THRESHOLD) return t('radar.tooClose')
  return t('radar.normal')
}
</script>

<style scoped>
/* ===== 页面布局 ===== */
.radar-page {
  width: 100%;
  height: 100%;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
  overflow-x: hidden;
  min-width: 0;
}

.page-header {
  text-align: center;
  padding: 2px 0;
}

.page-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #00E5FF;
  text-shadow: 0 0 10px rgba(0, 229, 255, 0.5);
  letter-spacing: 2px;
  margin: 0;
}

/* ===== 连接面板 ===== */
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
}

.status-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #e74c3c;
  box-shadow: 0 0 10px rgba(231, 76, 60, 0.5);
  transition: all 0.3s;
}

.status-dot.connected {
  background: #00FF96;
  box-shadow: 0 0 10px rgba(0, 255, 150, 0.5);
}

.status-text {
  font-size: 0.875rem;
  color: #ccc;
}

.config-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.config-group label {
  color: #888;
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

.server-input { width: 140px; }
.port-input { width: 76px; }

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
  box-shadow: 0 0 15px rgba(0, 229, 255, 0.4);
}

.btn-disconnect {
  background: #FF3366;
  color: #fff;
}

.btn-disconnect:hover:not(:disabled) {
  background: #E53950;
}

/* ===== 主内容区 ===== */
.content-area {
  display: flex;
  gap: 12px;
  flex: 1;
  min-height: 0;
}

.left-section {
  flex: 1.1;
  display: grid;
  grid-template-columns: 1fr;
  grid-template-rows: 1fr 2fr;
  gap: 12px;
  min-width: 0;
  min-height: 0;
}

.right-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 300px;
  max-width: 420px;
}

/* ===== 卡片样式（基础 .card/.card-header/.card-title/.card-body 已上提 common.css） ===== */
/* ===== 传感器网格 - 3个传感器 ===== */
.sensor-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: 1fr;
  gap: 12px;
  width: 100%;
  flex: 1;
}

/* 传感器数据卡片：占 grid 第一行，宽度高度拉满 */
.left-section > .card:first-child {
  width: 100%;
  height: 100%;
}

.left-section > .card:first-child .card-body {
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
  box-sizing: border-box;
}

/* 传感器卡片占满 grid 第一行 */
.left-section > .card:first-child {
  grid-row: 1;
}

.sensor-item {
  background: rgba(22, 93, 255, 0.05);
  border: 1px solid rgba(22, 93, 255, 0.2);
  border-radius: 8px;
  padding: 14px 10px;
  text-align: center;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-evenly;
}

.sensor-item:hover {
  border-color: rgba(0, 229, 255, 0.5);
  box-shadow: 0 0 20px rgba(0, 229, 255, 0.2);
}

/* 警告状态样式 */
.sensor-item.warning {
  background: rgba(255, 51, 102, 0.1);
  border-color: rgba(255, 51, 102, 0.3);
}

.sensor-item.warning:hover {
  border-color: rgba(255, 51, 102, 0.5);
  box-shadow: 0 0 20px rgba(255, 51, 102, 0.2);
}

.sensor-icon {
  font-size: 1.5rem;
  margin-bottom: 6px;
}

.sensor-name {
  font-size: 0.8125rem;
  color: #888;
  margin-bottom: 6px;
}

.sensor-value {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 4px;
  margin-bottom: 6px;
}

.value-num {
  font-size: 1.75rem;
  font-weight: bold;
  color: #00E5FF;
  font-family: 'Consolas', monospace;
}

.sensor-item.warning .value-num {
  color: #FF3366;
}

.value-unit {
  font-size: 0.8125rem;
  color: #666;
}

.sensor-status {
  font-size: 0.75rem;
  color: #00FF96;
}

.sensor-status.warning {
  color: #FF3366;
}

.sensor-status.error {
  color: #888;
}

/* ===== 雷达图容器 ===== */
.radar-card {
  /* 占两行，让雷达图更大 */
  grid-row: span 2;
  min-height: 0;
}

.radar-body {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 0;
  padding: 10px;
}

.radar-canvas {
  border-radius: 8px;
  box-shadow: 0 0 30px rgba(0, 229, 255, 0.2);
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* ===== STM32 控制面板样式 ===== */
.control-card {
  min-height: 0;
}

.control-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.control-status {
  font-size: 0.75rem;
  color: #888;
  margin-left: auto;
}

.control-status.connected {
  color: #00FF96;
}

/* 当前状态显示 */
.current-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
}

.status-label {
  color: #8b9bb4;
  font-size: 0.8125rem;
}

.status-value {
  color: #8b9bb4;
  font-size: 0.875rem;
  font-weight: bold;
}

.status-value.active {
  color: #00E5FF;
}

/* 控制按钮网格 */
.control-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
  max-width: 320px;
  margin: 0 auto;
  width: 100%;
}

.btn-control {
  padding: 8px 6px;
  border: none;
  border-radius: 6px;
  font-size: 0.8125rem;
  font-weight: bold;
  line-height: 1.3;
  cursor: pointer;
  transition: all 0.2s;
  background: rgba(22, 93, 255, 0.2);
  border: 1px solid rgba(22, 93, 255, 0.3);
  color: #fff;
}

.btn-control:hover {
  background: rgba(22, 93, 255, 0.4);
  box-shadow: 0 0 10px rgba(0, 229, 255, 0.3);
}

.btn-control:active {
  transform: scale(0.95);
}

.btn-dir {
  background: linear-gradient(135deg, rgba(0, 229, 255, 0.2), rgba(22, 93, 255, 0.2));
}

.btn-stop {
  background: linear-gradient(135deg, rgba(255, 51, 102, 0.3), rgba(229, 57, 80, 0.3));
  border-color: rgba(255, 51, 102, 0.5);
}

.btn-stop:hover {
  background: linear-gradient(135deg, rgba(255, 51, 102, 0.5), rgba(229, 57, 80, 0.5));
  box-shadow: 0 0 10px rgba(255, 51, 102, 0.4);
}

/* 刷子控制区域 */
.brushless-section {
  margin-top: 6px;
}

.section-title {
  font-size: 0.75rem;
  color: #8b9bb4;
  margin-bottom: 6px;
  padding-left: 5px;
  border-left: 3px solid #FFC107;
}

.brushless-control {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  max-width: 320px;
  margin: 0 auto;
  width: 100%;
}

.btn-brushless {
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.2), rgba(255, 152, 0, 0.2));
  border-color: rgba(255, 193, 7, 0.5);
  font-size: 0.8125rem;
}

.btn-brushless:hover {
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.4), rgba(255, 152, 0, 0.4));
}

.btn-brushless-start {
  background: linear-gradient(135deg, rgba(0, 255, 150, 0.2), rgba(0, 229, 255, 0.2));
  border-color: rgba(0, 255, 150, 0.5);
  font-size: 0.8125rem;
}

.btn-brushless-start:hover {
  background: linear-gradient(135deg, rgba(0, 255, 150, 0.4), rgba(0, 229, 255, 0.4));
}

/* 急停按钮 */
.emergency-section {
  margin-top: 6px;
  max-width: 320px;
  margin-left: auto;
  margin-right: auto;
  width: 100%;
}

.btn-emergency {
  width: 100%;
  padding: 10px;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: bold;
  cursor: pointer;
  background: linear-gradient(135deg, #ff0000, #cc0000);
  color: #fff;
  box-shadow: 0 0 20px rgba(255, 0, 0, 0.4);
  transition: all 0.2s;
}

.btn-emergency:hover {
  background: linear-gradient(135deg, #ff3333, #ff0000);
  box-shadow: 0 0 30px rgba(255, 0, 0, 0.6);
  transform: scale(1.02);
}

.btn-emergency:active {
  transform: scale(0.98);
}

/* 操作日志 */
.control-log {
  margin-top: 6px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 6px;
  padding: 8px;
}

.log-title {
  color: #8b9bb4;
  font-size: 0.75rem;
  margin-bottom: 6px;
}

/* 日志筛选按钮 */
.log-filter {
  display: flex;
  gap: 6px;
  margin-bottom: 6px;
}
.log-filter button {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(22, 93, 255, 0.3);
  color: #8b9bb4;
  border-radius: 4px;
  padding: 3px 10px;
  font-size: 0.6875rem;
  cursor: pointer;
  transition: all 0.2s;
}
.log-filter button.active {
  color: #00E5FF;
  border-color: rgba(0, 229, 255, 0.5);
  background: rgba(0, 229, 255, 0.1);
}

.log-list {
  font-family: 'Consolas', monospace;
  font-size: 0.75rem;
}

.log-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 0;
  border-bottom: 1px solid rgba(22, 93, 255, 0.1);
  color: #e6f7ff;
}

/* 等级徽标 */
.log-level {
  flex-shrink: 0;
  padding: 1px 6px;
  border-radius: 3px;
  font-size: 0.625rem;
  color: #0a101f;
}
.log-level.info {
  background: rgba(139, 155, 180, 0.8);
}
.log-level.warning {
  background: #FFCC00;
}
.log-level.error {
  background: #FF3366;
}

.log-item.error {
  color: #FF3366;
}
.log-item.warning {
  color: #FFCC00;
}

/* 来源 */
.log-src {
  flex-shrink: 0;
  color: #8b9bb4;
  font-size: 0.6875rem;
  min-width: 44px;
}

.log-time {
  color: #8b9bb4;
  min-width: 60px;
}

.empty-log {
  text-align: center;
  color: #8b9bb4;
  padding: 8px;
}



/* ===== 响应式布局 ===== */
@media (max-width: 1280px) {
  .content-area {
    flex-direction: column;
  }

  .right-section {
    max-width: none;
    min-width: auto;
  }

  .left-section {
    flex: none;
  }

  /* 窄屏/手机端超声波数据监控仍保持 3 列排版 */
  .sensor-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* ============================================================
   视觉美化增强（深色科技风：玻璃拟态 + 青色发光）——纯样式叠加覆盖
   ============================================================ */

/* ---- 页面背景光晕 ---- */
.radar-page {
  background:
    radial-gradient(900px 480px at 50% -8%, rgba(22, 93, 255, 0.14), transparent 60%),
    radial-gradient(700px 420px at 90% 110%, rgba(0, 229, 255, 0.08), transparent 60%),
    #0a101f;
}

/* ---- 卡片：玻璃质感渐变 + 顶部高光 + 青色边框发光 ---- */
.card {
  background: linear-gradient(165deg, rgba(22, 93, 255, 0.1) 0%, rgba(10, 16, 31, 0.85) 32%, rgba(13, 20, 33, 0.78) 100%);
  border: 1px solid rgba(0, 229, 255, 0.2);
  border-radius: 8px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(0, 229, 255, 0.08);
}

/* 卡片顶部高光扫描线 */
.card::after {
  content: "";
  position: absolute;
  top: 0;
  left: 10%;
  right: 10%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0, 229, 255, 0.55), transparent);
  pointer-events: none;
}

.card:hover {
  border-color: rgba(0, 229, 255, 0.55);
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.45), 0 0 20px rgba(0, 229, 255, 0.18), inset 0 1px 0 rgba(0, 229, 255, 0.12);
}

/* ---- 卡片标题：左侧发光指示条 + 加粗青色 ---- */
.card-header {
  background: linear-gradient(90deg, rgba(0, 229, 255, 0.12), rgba(22, 93, 255, 0.05) 60%, transparent);
  border-bottom: 1px solid rgba(0, 229, 255, 0.16);
}

.card-header::before {
  width: 3px;
  background: linear-gradient(180deg, #00E5FF, #165DFF);
  box-shadow: 0 0 10px rgba(0, 229, 255, 0.75), 0 0 20px rgba(0, 229, 255, 0.35);
}

.card-title {
  font-weight: 700;
  color: #00E5FF;
  text-shadow: 0 0 8px rgba(0, 229, 255, 0.45);
}

/* ---- 传感器卡片项：玻璃渐变 ---- */
.sensor-item {
  background: linear-gradient(160deg, rgba(0, 229, 255, 0.07), rgba(22, 93, 255, 0.04) 55%, rgba(13, 20, 33, 0.4));
  border: 1px solid rgba(0, 229, 255, 0.16);
}

.sensor-item:hover {
  border-color: rgba(0, 229, 255, 0.6);
  box-shadow: 0 0 22px rgba(0, 229, 255, 0.22), inset 0 0 12px rgba(0, 229, 255, 0.06);
  transform: translateY(-2px);
}

.sensor-item.warning {
  background: linear-gradient(160deg, rgba(255, 51, 102, 0.12), rgba(255, 51, 102, 0.04) 60%, rgba(13, 20, 33, 0.4));
  border-color: rgba(255, 51, 102, 0.35);
}

.sensor-item.warning:hover {
  border-color: rgba(255, 51, 102, 0.6);
  box-shadow: 0 0 22px rgba(255, 51, 102, 0.22);
}

.sensor-icon {
  filter: drop-shadow(0 0 6px rgba(0, 229, 255, 0.4));
}

.sensor-name {
  color: #8b9bb4;
}

/* ---- 传感器数值：等宽字体 + 青色发光大数字 ---- */
.value-num {
  letter-spacing: 1px;
  font-variant-numeric: tabular-nums;
  text-shadow: 0 0 10px rgba(0, 229, 255, 0.55), 0 0 26px rgba(0, 229, 255, 0.25);
}

.sensor-item.warning .value-num {
  text-shadow: 0 0 10px rgba(255, 51, 102, 0.6), 0 0 26px rgba(255, 51, 102, 0.28);
}

.value-unit {
  color: #5a6a7f;
}

/* ---- 状态标签：胶囊化 + hover 微高亮 ---- */
.sensor-status {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  line-height: 1.5;
  background: rgba(0, 255, 150, 0.08);
  border: 1px solid rgba(0, 255, 150, 0.22);
  transition: all 0.25s;
}

.sensor-status.warning {
  background: rgba(255, 51, 102, 0.1);
  border-color: rgba(255, 51, 102, 0.28);
}

.sensor-status.error {
  color: #5a6a7f;
  background: rgba(90, 106, 127, 0.08);
  border-color: rgba(90, 106, 127, 0.2);
}

.sensor-status:hover {
  text-shadow: 0 0 8px currentColor;
  filter: brightness(1.2);
}

/* ---- 雷达 Canvas 容器：圆角 + 内发光边框 + hover 微发光 ---- */
.radar-body {
  border: 1px solid rgba(0, 229, 255, 0.25);
  border-radius: 10px;
  background: radial-gradient(circle at 50% 50%, rgba(0, 229, 255, 0.07), rgba(10, 16, 31, 0.55) 70%);
  box-shadow: inset 0 0 26px rgba(0, 229, 255, 0.08);
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

.radar-body:hover {
  border-color: rgba(0, 229, 255, 0.5);
  box-shadow: inset 0 0 30px rgba(0, 229, 255, 0.14), 0 0 18px rgba(0, 229, 255, 0.12);
}

.radar-canvas {
  border-radius: 8px;
  border: 1px solid rgba(0, 229, 255, 0.2);
  box-shadow: 0 0 30px rgba(0, 229, 255, 0.2), inset 0 0 18px rgba(0, 229, 255, 0.12);
  width: 100%;
  height: 100%;
}

/* ---- 控制按钮：渐变主色 + hover/active/disabled 状态反馈 ---- */
.btn-control {
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(0, 229, 255, 0.2), rgba(22, 93, 255, 0.24));
  border: 1px solid rgba(0, 229, 255, 0.35);
  color: #e6f7ff;
}

.btn-control:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(0, 229, 255, 0.36), rgba(22, 93, 255, 0.42));
  border-color: rgba(0, 229, 255, 0.75);
  box-shadow: 0 0 14px rgba(0, 229, 255, 0.4), 0 4px 18px rgba(0, 229, 255, 0.15);
  color: #fff;
}

.btn-control:active:not(:disabled) {
  transform: scale(0.93);
  box-shadow: 0 0 8px rgba(0, 229, 255, 0.45);
}

.btn-control:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  filter: saturate(0.3);
  transform: none;
}

.btn-stop {
  background: linear-gradient(135deg, rgba(255, 51, 102, 0.35), rgba(201, 30, 69, 0.35));
  border-color: rgba(255, 51, 102, 0.55);
  color: #fff;
}

.btn-stop:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(255, 51, 102, 0.55), rgba(201, 30, 69, 0.55));
  border-color: rgba(255, 51, 102, 0.85);
  box-shadow: 0 0 14px rgba(255, 51, 102, 0.45);
}

.btn-brushless {
  background: linear-gradient(135deg, rgba(255, 204, 0, 0.18), rgba(255, 152, 0, 0.18));
  border-color: rgba(255, 204, 0, 0.45);
}

.btn-brushless:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(255, 204, 0, 0.36), rgba(255, 152, 0, 0.36));
  border-color: rgba(255, 204, 0, 0.7);
  box-shadow: 0 0 12px rgba(255, 204, 0, 0.35);
}

.btn-brushless-start {
  background: linear-gradient(135deg, rgba(0, 255, 150, 0.22), rgba(0, 229, 255, 0.22));
  border-color: rgba(0, 255, 150, 0.5);
}

.btn-brushless-start:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(0, 255, 150, 0.4), rgba(0, 229, 255, 0.4));
  border-color: rgba(0, 255, 150, 0.75);
  box-shadow: 0 0 12px rgba(0, 255, 150, 0.35);
}

/* ---- 急停按钮：主题红色 + 呼吸发光 ---- */
@keyframes emergencyPulse {
  0%, 100% { box-shadow: 0 0 18px rgba(255, 51, 102, 0.45); }
  50% { box-shadow: 0 0 32px rgba(255, 51, 102, 0.75); }
}

.btn-emergency {
  background: linear-gradient(135deg, #FF3366, #c81e45);
  border: 1px solid rgba(255, 51, 102, 0.6);
  border-radius: 8px;
  animation: emergencyPulse 2s ease-in-out infinite;
}

.btn-emergency:hover {
  background: linear-gradient(135deg, #ff5588, #ff3366);
  transform: scale(1.03);
}

.btn-emergency:active {
  transform: scale(0.96);
}

/* ---- 当前指令状态 ---- */
.current-status {
  background: linear-gradient(90deg, rgba(0, 229, 255, 0.07), rgba(22, 93, 255, 0.04));
  border: 1px solid rgba(0, 229, 255, 0.16);
  border-radius: 8px;
}

.status-value.active {
  color: #00E5FF;
  text-shadow: 0 0 10px rgba(0, 229, 255, 0.6);
}

/* ---- 连接状态：状态圆点 + hover 微高亮 ---- */
.control-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: #5a6a7f;
}

.control-status::before {
  content: "";
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #FF3366;
  box-shadow: 0 0 8px rgba(255, 51, 102, 0.6);
  transition: all 0.3s;
}

.control-status.connected {
  color: #00FF96;
}

.control-status.connected::before {
  background: #00FF96;
  box-shadow: 0 0 8px rgba(0, 255, 150, 0.7);
}

.control-status:hover {
  text-shadow: 0 0 8px currentColor;
}

/* ---- 控制面板分区标题 ---- */
.section-title {
  border-left: 3px solid #FFCC00;
  color: #e6f7ff;
  text-shadow: 0 0 6px rgba(255, 204, 0, 0.25);
}

/* ---- 操作日志 ---- */
.control-log {
  border: 1px solid rgba(0, 229, 255, 0.14);
  border-radius: 8px;
  background: linear-gradient(180deg, rgba(0, 229, 255, 0.04), rgba(0, 0, 0, 0.3));
}

.log-title {
  letter-spacing: 1px;
}

.log-item:hover {
  background: rgba(0, 229, 255, 0.05);
  text-shadow: 0 0 6px rgba(0, 229, 255, 0.35);
}

.log-item.error:hover {
  background: rgba(255, 51, 102, 0.06);
  text-shadow: 0 0 6px rgba(255, 51, 102, 0.35);
}

/* ---- 调试信息 ---- */
.debug-label {
  color: #5a6a7f;
}

.debug-value {
  text-shadow: 0 0 8px rgba(0, 229, 255, 0.3);
}

.debug-value.success { text-shadow: 0 0 8px rgba(0, 255, 150, 0.35); }
.debug-value.error { text-shadow: 0 0 8px rgba(255, 51, 102, 0.35); }

.debug-item:hover .debug-value {
  filter: brightness(1.25);
}
</style>
