<template>
  <div class="radar-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">📡 {{ $t('radar.pageTitle') }}</h1>
    </div>
    
    <!-- 连接状态面板 -->
    <div class="connection-panel">
      <div class="status-group">
        <div class="status-dot" :class="{ connected: isConnected }"></div>
        <span class="status-text">{{ connectionStatus }}</span>
      </div>
      
      <div class="config-group">
        <label>{{ $t('radar.deviceIp') }}</label>
        <input v-model="serverIp" :disabled="isConnected" class="server-input" placeholder="192.168.0.3" />
        <label>{{ $t('radar.port') }}</label>
        <input v-model="serverPort" :disabled="isConnected" class="port-input" placeholder="9090" />
        <button @click="connectROS" :disabled="isConnected" class="btn btn-connect">{{ $t('radar.connect') }}</button>
        <button @click="disconnectROS" :disabled="!isConnected" class="btn btn-disconnect">{{ $t('radar.disconnect') }}</button>
      </div>
    </div>

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
                <div class="sensor-icon">📡</div>
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

        <!-- STM32 控制面板 -->
         <!-- <div class="card control-card">
          <div class="card-header">
            <span class="card-title">机器人控制</span>
            <span class="control-status" :class="{connectde: stm32Connected}">
              {{ stm32tatus }}
            </span>
          </div>
          <div class="card-body control-body">
            <div class="currenr-status">
              <span class="=status-label">当前指令：</span>
              <span class="status-value" :class="{active: currentCommand !== '待机中'}">

              </span>
            </div>
          </div>
         </div> -->
        <div class="card control-card">
          <div class="card-header">
            <span class="card-title">🎮 {{ $t('radar.robotControl') }}</span>
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
              <button class="btn-control btn-dir" @mousedown="sendStm32Cmd('forward')" @mouseup="sendStm32Cmd('stop')" @mouseleave="sendStm32Cmd('stop')">▲<br>{{ $t('radar.forward') }}</button>
              <div></div>
              
              <button class="btn-control btn-dir" @mousedown="sendStm32Cmd('turn_left')" @mouseup="sendStm32Cmd('stop')" @mouseleave="sendStm32Cmd('stop')">◀<br>{{ $t('radar.turnLeft') }}</button>
              <button class="btn-control btn-stop" @click="sendStm32Cmd('stop')">⏹<br>{{ $t('radar.stop') }}</button>
              <button class="btn-control btn-dir" @mousedown="sendStm32Cmd('turn_right')" @mouseup="sendStm32Cmd('stop')" @mouseleave="sendStm32Cmd('stop')">▶<br>{{ $t('radar.turnRight') }}</button>
              
              <div></div>
              <button class="btn-control btn-dir" @mousedown="sendStm32Cmd('backward')" @mouseup="sendStm32Cmd('stop')" @mouseleave="sendStm32Cmd('stop')">▼<br>{{ $t('radar.backward') }}</button>
              <div></div>
            </div>

            <!-- 无刷电机控制 -->
            <div class="brushless-section">
              <div class="section-title">⚙️ {{ $t('radar.brushControl') }}</div>
              <div class="brushless-control">
                <button class="btn-control btn-brushless" @click="sendStm32Cmd('brushless_stop')">
                  🛑 {{ $t('radar.stop') }}
                </button>
                <button class="btn-control btn-brushless-start" @click="sendStm32Cmd('brushless_start')">
                  ⚡ {{ $t('radar.start') }}
                </button>
              </div>
            </div>

            <!-- 急停按钮 -->
            <div class="emergency-section">
              <button class="btn-emergency" @click="emergencyStop">
                🚨 {{ $t('radar.emergency') }}
              </button>
            </div>

            <!-- 操作日志 -->
            <div class="control-log">
              <div class="log-title">📋 {{ $t('radar.operationLog') }}</div>
              <div class="log-list">
                <div v-if="stm32Logs.length === 0" class="empty-log">{{ $t('radar.waitingOp') }}</div>
                <div v-for="(log, index) in stm32Logs" :key="index" class="log-item" :class="{ error: log.isError }">
                  <span class="log-time">{{ log.time }}</span>
                  <span class="log-msg">{{ log.message }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="right-section">
        <!-- 雷达可视化 - 使用 Canvas 绘制三个方向的雷达图 -->
        <div class="card radar-card">
          <div class="card-header">
            <span class="card-title">{{ $t('radar.radarVisual') }}</span>
          </div>
          <div class="card-body radar-body">
            <canvas ref="radarCanvas" class="radar-canvas"></canvas>
          </div>
        </div>

        <!-- 调试信息面板 -->
        <div class="card">
          <div class="card-header">
            <span class="card-title">{{ $t('radar.debugInfo') }}</span>
          </div>
          <div class="card-body">
            <div class="debug-list">
              <div class="debug-item">
                <span class="debug-label">{{ $t('radar.rawData') }}</span>
                <span class="debug-value">{{ rawDataHex }}</span>
              </div>
              <div class="debug-item">
                <span class="debug-label">{{ $t('radar.dataLen') }}</span>
                <span class="debug-value">{{ rawDataLength }}</span>
              </div>
              <div class="debug-item">
                <span class="debug-label">{{ $t('radar.parseStatus') }}</span>
                <span class="debug-value" :class="{ success: parseSuccess, error: !parseSuccess }">{{ parseStatus }}</span>
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
import ROSLIB from 'roslib'
import { useI18n } from 'vue-i18n'
import { updateRosState } from '@/store/rosState'

const { t, locale } = useI18n()

// 语言切换后重绘雷达方向标签
watch(locale, () => renderRadar())

// ===== 配置区域 =====
const serverIp = ref('192.168.0.3')
const serverPort = ref('9090')
const isConnected = ref(false)
const ros = ref(null)
const waveLengthListener = ref(null)
const radarCanvas = ref(null)
let canvasCtx = null
let radarSize = 0

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

// ROS 话题
const stm32CmdTopic = ref(null)
const stm32ResultTopic = ref(null)
const stm32StatusTopic = ref(null)

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
const addStm32Log = (message, isError = false) => {
  const now = new Date()
  const timeStr = now.toLocaleTimeString()
  stm32Logs.value.unshift({ time: timeStr, message, isError })
  if (stm32Logs.value.length > 15) stm32Logs.value.pop()
}

// 发送 STM32 控制指令（ROS 话题方式）
const sendStm32Cmd = (command) => {
  if (!isConnected.value || !stm32CmdTopic.value) {
    addStm32Log(t('radar.notConnectedLog'), true)
    return
  }
  
  const cmdValue = CMD_MAP[command]
  if (cmdValue === undefined) {
    addStm32Log(t('radar.unknownCmd', { cmd: command }), true)
    return
  }
  
  stm32CmdTopic.value.publish(new ROSLIB.Message({ data: cmdValue }))
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

// ===== 计算属性 =====
// 原始数据十六进制显示，用于调试
const rawDataHex = computed(() => {
  if (!rawData.value || rawData.value.length === 0) return '--'
  return rawData.value.map(b => b.toString(16).padStart(2, '0').toUpperCase()).join(' ')
})

// 原始数据长度
const rawDataLength = computed(() => rawData.value ? rawData.value.length : 0)

// 连接状态文本
const connectionStatus = computed(() => {
  if (isConnected.value) return t('radar.connected')
  return t('radar.notConnected')
})

// ===== 生命周期钩子 =====
onMounted(() => {
  initCanvas()
  window.addEventListener('resize', resizeCanvas)
  window.addEventListener('keydown', handleKeyDown)
  window.addEventListener('keyup', handleKeyUp)
})

onUnmounted(() => {
  disconnectROS()
  window.removeEventListener('resize', resizeCanvas)
  window.removeEventListener('keydown', handleKeyDown)
  window.removeEventListener('keyup', handleKeyUp)
})

// ===== Canvas 初始化和绘制 =====
// 初始化 Canvas，设置尺寸并开始绘制雷达图
const initCanvas = () => {
  resizeCanvas()
}

// 调整 Canvas 尺寸以适应容器，并适配高 DPI 屏幕
const resizeCanvas = () => {
  if (!radarCanvas.value) return
  const container = radarCanvas.value.parentElement
  const avail = Math.min(container.clientWidth - 40, container.clientHeight - 40, 400)
  // 容器尚未完成布局时跳过，避免出现 0 或负尺寸
  if (avail <= 0) return
  radarSize = avail
  const dpr = window.devicePixelRatio || 1
  radarCanvas.value.style.width = radarSize + 'px'
  radarCanvas.value.style.height = radarSize + 'px'
  radarCanvas.value.width = Math.round(radarSize * dpr)
  radarCanvas.value.height = Math.round(radarSize * dpr)
  canvasCtx = radarCanvas.value.getContext('2d')
  if (canvasCtx) {
    canvasCtx.setTransform(dpr, 0, 0, dpr, 0, 0)
  }
  renderRadar()
}

// 绘制雷达图 - 包含同心圆、十字线、方向标记和传感器数据（仅在尺寸或数据变化时调用）
const renderRadar = () => {
  if (!canvasCtx || !radarSize) return

  const ctx = canvasCtx
  const centerX = radarSize / 2
  const centerY = radarSize / 2
  const maxRadius = Math.min(centerX, centerY) - 34

  // 清空画布
  ctx.fillStyle = '#0a101f'
  ctx.fillRect(0, 0, radarSize, radarSize)

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
}

// ===== 【演示代码2】ROS 2 桥接连接 =====
// 使用 WebSocket 建立与 ROS 2 系统的连接
// 通过 rosbridge_server 将 ROS 话题数据转发到前端
const connectROS = () => {
  // 防止重复连接
  if (isConnected.value) return
  
  const url = `ws://${serverIp.value}:${serverPort.value}`
  ros.value = new ROSLIB.Ros({ url })
  
  // 连接成功回调
  ros.value.on('connection', () => {
    console.log('✅ Connected to ROS 2 bridge')
    isConnected.value = true
    updateRosState(url, true)
    subscribeToTopic()
  })
  
  // 连接错误回调
  ros.value.on('error', (error) => {
    console.error('❌ ROS Connection Error:', error)
    alert(t('radar.connFail', { error }))
  })
  
  // 连接关闭回调
  ros.value.on('close', () => {
    console.log('🔌 ROS Connection Closed')
    isConnected.value = false
    updateRosState(null, false)
  })
}

// 断开 ROS 连接并清理资源
const disconnectROS = () => {
  // 清理超声波话题
  if (waveLengthListener.value) {
    waveLengthListener.value.unsubscribe()
    waveLengthListener.value = null
  }
  
  // 清理 STM32 话题
  if (stm32ResultTopic.value) {
    stm32ResultTopic.value.unsubscribe()
    stm32ResultTopic.value = null
  }
  if (stm32StatusTopic.value) {
    stm32StatusTopic.value.unsubscribe()
    stm32StatusTopic.value = null
  }
  
  stm32CmdTopic.value = null
  
  if (ros.value) {
    ros.value.close()
    ros.value = null
  }
  
  isConnected.value = false
  stm32Connected.value = false
  updateRosState(null, false)
  
  // 重置传感器数据
  sensors.value.forEach(s => s.distance = 0)
}

// 订阅 ROS 话题 /wave_length，接收超声波传感器数据
const subscribeToTopic = () => {
  waveLengthListener.value = new ROSLIB.Topic({
    ros: ros.value,
    name: '/wave_length',
    messageType: 'std_msgs/UInt8MultiArray'
  })
  
  waveLengthListener.value.subscribe(processSensorData)
  
  // ===== STM32 控制话题 =====
  
  // 发布控制指令
  stm32CmdTopic.value = new ROSLIB.Topic({
    ros: ros.value,
    name: '/stm32_cmd',
    messageType: 'std_msgs/Int32'
  })
  
  // 订阅执行结果
  stm32ResultTopic.value = new ROSLIB.Topic({
    ros: ros.value,
    name: '/stm32_result',
    messageType: 'std_msgs/String'
  })
  
  stm32ResultTopic.value.subscribe((msg) => {
    console.log('STM32 Result:', msg.data)
    if (msg.data.startsWith('success')) {
      addStm32Log(`✅ ${msg.data}`)
    } else if (msg.data.startsWith('error')) {
      addStm32Log(`❌ ${msg.data}`, true)
      
    }
  })
  
  // 订阅 STM32 状态（1Hz 心跳）
  stm32StatusTopic.value = new ROSLIB.Topic({
    ros: ros.value,
    name: '/stm32_status',
    messageType: 'std_msgs/String'
  })
  
  stm32StatusTopic.value.subscribe((msg) => {
    const wasOffline = !stm32Connected.value
    stm32Connected.value = (msg.data === 'online')
    
    if (stm32Connected.value && wasOffline) {
      addStm32Log(t('radar.stm32Online'))
    } else if (!stm32Connected.value && !wasOffline) {
      addStm32Log(t('radar.stm32Offline'), true)
    }
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
  flex: 1.35;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

.right-section {
  flex: 0.85;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 280px;
  max-width: 360px;
}

/* ===== 卡片样式 ===== */
.card {
  background: rgba(10, 16, 31, 0.8);
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(22, 93, 255, 0.2);
  display: flex;
  flex-direction: column;
}

.card-header {
  min-height: 34px;
  display: flex;
  align-items: center;
  padding: 0 12px;
  font-size: 0.875rem;
  font-weight: 600;
  color: #00E5FF;
  background: rgba(22, 93, 255, 0.1);
  border-bottom: 1px solid rgba(22, 93, 255, 0.2);
}

.card-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #00E5FF;
}

.card-body {
  padding: 14px;
  flex: 1;
  overflow: auto;
}

/* ===== 传感器网格 - 3个传感器 ===== */
.sensor-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.sensor-item {
  background: rgba(22, 93, 255, 0.05);
  border: 1px solid rgba(22, 93, 255, 0.2);
  border-radius: 8px;
  padding: 14px 10px;
  text-align: center;
  transition: all 0.3s;
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
  flex: 1;
  /* 高度下限，避免窗口过矮时雷达被压成 0 */
  min-height: 240px;
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
  max-width: 100%;
  max-height: 100%;
}

/* ===== 调试列表 ===== */
.debug-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.debug-item {
  display: flex;
  gap: 10px;
  font-family: 'Consolas', monospace;
  font-size: 0.8125rem;
  flex-wrap: wrap;
}

.debug-label {
  color: #888;
  min-width: 68px;
}

.debug-value {
  color: #00E5FF;
  word-break: break-all;
  flex: 1;
}

.debug-value.success { color: #00FF96; }
.debug-value.error { color: #FF3366; }

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
  max-height: 84px;
  overflow-y: auto;
}

.log-title {
  color: #8b9bb4;
  font-size: 0.75rem;
  margin-bottom: 6px;
}

.log-list {
  font-family: 'Consolas', monospace;
  font-size: 0.75rem;
}

.log-item {
  display: flex;
  gap: 8px;
  padding: 3px 0;
  border-bottom: 1px solid rgba(22, 93, 255, 0.1);
  color: #e6f7ff;
}

.log-item.error {
  color: #FF3366;
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
@media (max-width: 1024px) {
  .content-area {
    flex-direction: column;
  }
  
  .right-section {
    max-width: none;
    min-width: auto;
  }
  
  .sensor-grid {
    grid-template-columns: 1fr;
  }
}
</style>
