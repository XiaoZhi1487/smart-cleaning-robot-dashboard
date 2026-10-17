<template>
  <div class="screen1-container">
    <div class="screen-title">{{ $t('screen.pageTitle') }}</div>
    
    <!-- 主内容区 - 使用 flex 布局 -->
    <div class="content-area">
      <!-- 左侧区域：设备状态 -->
      <div class="left-section">
        <!-- 设备状态总览 -->
        <div class="card">
          <div class="card-header">
            <span class="card-title">{{ $t('screen.deviceStatus') }}</span>
          </div>
          <div class="card-body">
            <div class="state-list">
              <div v-for="item in deviceItems" :key="item.key" class="state-item-row">
                <span class="state-icon" v-html="item.icon"></span>
                <span class="state-name">{{ item.name }}</span>
                <span class="state-value" :class="item.stateClass">{{ item.value }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 中间区域：机器人运行视图 -->
      <div class="center-section">
        <div class="card main-card">
          <div class="card-header">
            <span class="card-title">{{ $t('screen.robotView') }}</span>
          </div>
          <div class="card-body robot-body">
            <div class="robot-map-container">
              <!-- 地图网格背景 -->
              <div class="grid-background">
                <svg viewBox="0 0 400 300" class="grid-svg">
                  <defs>
                    <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                      <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(0,229,255,0.15)" stroke-width="0.5"/>
                    </pattern>
                    <linearGradient id="buildingGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" style="stop-color:#1a3a5c;stop-opacity:0.6" />
                      <stop offset="100%" style="stop-color:#0d2137;stop-opacity:0.8" />
                    </linearGradient>
                  </defs>
                  
                  <rect width="400" height="300" fill="url(#grid)" />
                  
                  <rect x="50" y="40" width="300" height="220" fill="url(#buildingGradient)" stroke="#165DFF" stroke-width="1" rx="4"/>
                  
                  <g stroke="rgba(22,93,255,0.3)" stroke-width="0.5">
                    <line v-for="i in 10" :key="'h'+i" :x1="50" :y1="40 + i * 20" :x2="350" :y2="40 + i * 20" />
                    <line v-for="i in 14" :key="'v'+i" :x1="50 + i * 20" :y1="40" :x2="50 + i * 20" :y2="260" />
                  </g>
                  
                  <path d="M 70 60 Q 150 80 200 70 T 330 90" fill="none" stroke="#00E5FF" stroke-width="2" stroke-dasharray="5,5" opacity="0.6">
                    <animate attributeName="stroke-dashoffset" values="0;20" dur="2s" repeatCount="indefinite"/>
                  </path>
                  <path d="M 70 100 Q 180 120 250 110 T 330 130" fill="none" stroke="#00E5FF" stroke-width="2" stroke-dasharray="5,5" opacity="0.6">
                    <animate attributeName="stroke-dashoffset" values="0;20" dur="2s" repeatCount="indefinite"/>
                  </path>
                  
                  <circle cx="200" cy="150" r="25" fill="rgba(0,229,255,0.2)" stroke="#00E5FF" stroke-width="1">
                    <animate attributeName="r" values="25;30;25" dur="2s" repeatCount="indefinite"/>
                    <animate attributeName="opacity" values="0.2;0.4;0.2" dur="2s" repeatCount="indefinite"/>
                  </circle>
                </svg>
              </div>
              
              <!-- 幕墙清洁机器人 -->
              <div class="robot-model">
                <svg viewBox="0 0 120 160" class="robot-svg">
                  <defs>
                    <linearGradient id="robotBody" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" style="stop-color:#f5f5f5" />
                      <stop offset="50%" style="stop-color:#e0e0e0" />
                      <stop offset="100%" style="stop-color:#c0c0c0" />
                    </linearGradient>
                    <linearGradient id="robotShadow" x1="0%" y1="0%" x2="100%" y2="100%">
                      <stop offset="0%" style="stop-color:#00E5FF;stop-opacity:0.3" />
                      <stop offset="100%" style="stop-color:#165DFF;stop-opacity:0.1" />
                    </linearGradient>
                    <filter id="glow">
                      <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                      <feMerge>
                        <feMergeNode in="coloredBlur"/>
                        <feMergeNode in="SourceGraphic"/>
                      </feMerge>
                    </filter>
                  </defs>
                  
                  <ellipse cx="60" cy="150" rx="45" ry="8" fill="url(#robotShadow)" />
                  
                  <rect x="45" y="5" width="30" height="15" fill="#666" rx="2"/>
                  <rect x="50" y="0" width="20" height="8" fill="#888" rx="1"/>
                  
                  <line x1="55" y1="0" x2="55" y2="20" stroke="#FF6B35" stroke-width="2"/>
                  <line x1="65" y1="0" x2="65" y2="20" stroke="#FF6B35" stroke-width="2"/>
                  
                  <rect x="20" y="20" width="80" height="100" rx="12" fill="url(#robotBody)" stroke="#999" stroke-width="1"/>
                  
                  <ellipse cx="60" cy="18" rx="8" ry="4" fill="#FF4444">
                    <animate attributeName="opacity" values="1;0.3;1" dur="1s" repeatCount="indefinite"/>
                  </ellipse>
                  <rect x="56" y="14" width="8" height="6" fill="#CC0000" rx="1"/>
                  
                  <rect x="30" y="35" width="60" height="50" rx="8" fill="#1a1a2e" stroke="#333" stroke-width="1"/>
                  
                  <ellipse cx="45" cy="55" rx="8" ry="10" fill="#00E5FF" filter="url(#glow)">
                    <animate attributeName="ry" values="10;2;10" dur="3s" repeatCount="indefinite"/>
                  </ellipse>
                  <ellipse cx="75" cy="55" rx="8" ry="10" fill="#00E5FF" filter="url(#glow)">
                    <animate attributeName="ry" values="10;2;10" dur="3s" repeatCount="indefinite"/>
                  </ellipse>
                  
                  <rect x="50" y="72" width="20" height="3" rx="1" fill="#00E5FF" opacity="0.8"/>
                  
                  <rect x="35" y="92" width="50" height="12" rx="2" fill="#0a0a0a"/>
                  <text x="60" y="101" text-anchor="middle" fill="#00FF96" font-size="8" font-family="monospace">RUNNING</text>
                  
                  <rect x="22" y="40" width="4" height="8" rx="1" fill="#666"/>
                  <rect x="22" y="52" width="4" height="8" rx="1" fill="#666"/>
                  <rect x="94" y="40" width="4" height="8" rx="1" fill="#666"/>
                  <rect x="94" y="52" width="4" height="8" rx="1" fill="#666"/>
                  
                  <rect x="25" y="125" width="70" height="20" rx="4" fill="#444"/>
                  <rect x="28" y="128" width="12" height="14" rx="2" fill="#666"/>
                  <rect x="45" y="128" width="12" height="14" rx="2" fill="#666"/>
                  <rect x="62" y="128" width="12" height="14" rx="2" fill="#666"/>
                  <rect x="79" y="128" width="12" height="14" rx="2" fill="#666"/>
                  
                  <circle cx="25" cy="135" r="8" fill="#333" stroke="#555" stroke-width="1"/>
                  <circle cx="95" cy="135" r="8" fill="#333" stroke="#555" stroke-width="1"/>
                  
                  <rect x="35" y="148" width="50" height="8" rx="2" fill="#FFCC00"/>
                  <line x1="40" y1="148" x2="40" y2="156" stroke="#E6B800" stroke-width="1"/>
                  <line x1="50" y1="148" x2="50" y2="156" stroke="#E6B800" stroke-width="1"/>
                  <line x1="60" y1="148" x2="60" y2="156" stroke="#E6B800" stroke-width="1"/>
                  <line x1="70" y1="148" x2="70" y2="156" stroke="#E6B800" stroke-width="1"/>
                  <line x1="80" y1="148" x2="80" y2="156" stroke="#E6B800" stroke-width="1"/>
                  
                  <circle cx="30" cy="145" r="3" fill="#00E5FF" opacity="0.8">
                    <animate attributeName="opacity" values="0.8;0.4;0.8" dur="0.5s" repeatCount="indefinite"/>
                  </circle>
                  <circle cx="90" cy="145" r="3" fill="#00E5FF" opacity="0.8">
                    <animate attributeName="opacity" values="0.8;0.4;0.8" dur="0.5s" repeatCount="indefinite"/>
                  </circle>
                  
                  <circle cx="60" cy="28" r="3" fill="#00FF96" filter="url(#glow)">
                    <animate attributeName="opacity" values="1;0.5;1" dur="1.5s" repeatCount="indefinite"/>
                  </circle>
                </svg>
              </div>
              
            </div>

            <!-- 机器人状态 -->
            <div class="robot-state">
              <div class="state-badge">
                <span class="badge-icon"><svg class="icon-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12 2 12"/><path d="M22 12a10 10 0 0 0-20 0"/><path d="M6 12a6 6 0 0 1 12 0"/><path d="M10 12a2 2 0 0 1 4 0"/></svg></span>
                <span class="badge-label">{{ $t('screen.comm') }}</span>
                <span class="badge-value" :class="commStateClass">{{ commStateText }}</span>
              </div>
              <div class="state-badge">
                <span class="badge-icon"><svg class="icon-svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg></span>
                <span class="badge-label">{{ $t('screen.fault') }}</span>
                <span class="badge-value" :class="faultStateClass">{{ faultStateText }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧区域：今日统计和故障预警 -->
      <div class="right-section">
        <!-- 实时超声波距离趋势 -->
        <div class="card">
          <div class="card-header">
            <span class="card-title">{{ $t('screen.ultrasonicTrend') }}</span>
          </div>
          <div class="card-body">
            <div ref="todayChart" class="chart-container"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部区域：设备工作日志 -->
    <div class="bottom-section">
      <div class="card">
        <div class="card-header">
          <span class="card-title">{{ $t('screen.deviceLog') }}</span>
        </div>
        <div class="card-body log-body">
          <div class="log-container">
            <!-- 实时日志 -->
            <div class="realtime-log">
              <div class="log-section-title">
                <span class="pulse-dot"></span>
                {{ $t('screen.realtimeLog') }}
              </div>
              <div class="log-list" ref="realtimeLogList">
                <div v-for="(log, idx) in realtimeLogs" :key="idx" class="log-item" :class="log.type">
                  <span class="log-time">{{ log.time }}</span>
                  <span class="log-type">[{{ log.typeText }}]</span>
                  <span class="log-content">{{ log.content }}</span>
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
/* eslint-disable vue/multi-word-component-names */
import { ref, onMounted, onUnmounted, computed } from 'vue';
import * as echarts from 'echarts/core';
import { LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { rosState, subscribeTopic, connectRos } from '@/store/rosState';
import { useI18n } from 'vue-i18n';

defineOptions({ name: 'DataScreen' }) // eslint-disable-line no-undef

echarts.use([LineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer]);

const { t } = useI18n();
const todayChart = ref(null);
const realtimeLogList = ref(null);

// ===== ROS 连接（使用全局共享连接）=====
let waveListener = null;
let stm32StatusListener = null;
let clientCountListener = null;
let camOnlineListener = null;
let diagListener = null;
let uptimeTimer = null;

// ===== 真实数据状态 =====
// 超声波距离 [左, 前, 右]（来自 /wave_length，单位 mm）
const sensors = ref([0, 0, 0]);
// STM32 在线状态（来自 /stm32_status）
const stm32Online = ref(false);
// 在线终端数（来自 /client_count）
const clientCount = ref(0);
// CPU / 相机 RGB 温度（来自 /diagnostics）与相机在线状态（来自 /camera/device_status）
const cpuTemp = ref(0);
const rgbTemp = ref(0);
const camOnline = ref(false);
// 设备开机时长（秒，来自 YOLO 后端 /uptime）
const devUptime = ref(0);
// 是否已收到过数据
const hasData = computed(() => rosState.connected && sensors.value.some(v => v > 0));

// ===== 设备状态总览（真实数据）=====
const deviceItems = computed(() => [
  { key: 'ros', icon: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="12" rx="2"/><path d="m7 20 10 0"/><path d="M12 16v4"/></svg>', name: t('screen.rosComm'), value: rosState.connected ? t('screen.online') : t('screen.offline'), stateClass: rosState.connected ? 'normal' : 'error' },
  { key: 'stm32', icon: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="2" width="16" height="8" rx="2"/><rect x="4" y="14" width="16" height="8" rx="2"/><path d="M2 6h.01"/><path d="M22 6h.01"/><path d="M2 18h.01"/><path d="M22 18h.01"/></svg>', name: t('screen.stm32'), value: stm32Online.value ? t('screen.online') : t('screen.offline'), stateClass: stm32Online.value ? 'normal' : (rosState.connected ? 'warning' : 'error') },
  { key: 'front', icon: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12 2 12"/><path d="M22 12a10 10 0 0 0-20 0"/><path d="M6 12a6 6 0 0 1 12 0"/><path d="M10 12a2 2 0 0 1 4 0"/></svg>', name: t('screen.ultrasonicFront'), value: sensors.value[1] > 0 ? `${sensors.value[1]}mm` : t('screen.noData'), stateClass: sensors.value[1] > 0 && sensors.value[1] < 200 ? 'warning' : 'normal' },
  { key: 'left', icon: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="transform: rotate(-90deg)"><path d="M22 12 2 12"/><path d="M22 12a10 10 0 0 0-20 0"/><path d="M6 12a6 6 0 0 1 12 0"/><path d="M10 12a2 2 0 0 1 4 0"/></svg>', name: t('screen.ultrasonicLeft'), value: sensors.value[0] > 0 ? `${sensors.value[0]}mm` : t('screen.noData'), stateClass: sensors.value[0] > 0 && sensors.value[0] < 200 ? 'warning' : 'normal' },
  { key: 'right', icon: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="transform: rotate(90deg)"><path d="M22 12 2 12"/><path d="M22 12a10 10 0 0 0-20 0"/><path d="M6 12a6 6 0 0 1 12 0"/><path d="M10 12a2 2 0 0 1 4 0"/></svg>', name: t('screen.ultrasonicRight'), value: sensors.value[2] > 0 ? `${sensors.value[2]}mm` : t('screen.noData'), stateClass: sensors.value[2] > 0 && sensors.value[2] < 200 ? 'warning' : 'normal' },
  { key: 'camOnline', icon: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>', name: t('screen.cameraOnline'), value: camOnline.value ? t('screen.online') : t('screen.offline'), stateClass: camOnline.value ? 'normal' : (rosState.connected ? 'warning' : 'error') },
  { key: 'cpuTemp', icon: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/><path d="M9 14.3a2.5 2.5 0 1 0 6 0"/></svg>', name: t('screen.cpuTemp'), value: cpuTemp.value > 0 ? `${cpuTemp.value}°C` : t('screen.noData'), stateClass: cpuTemp.value >= 85 ? 'warning' : 'normal' },
  { key: 'rgbTemp', icon: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 2a14 14 0 0 0 0 20 14 14 0 0 0 0-20z"/><path d="M2 12h20"/></svg>', name: t('screen.rgbTemp'), value: rgbTemp.value > 0 ? `${rgbTemp.value}°C` : t('screen.noData'), stateClass: rgbTemp.value >= 85 ? 'warning' : 'normal' },
  { key: 'uptime', icon: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>', name: t('screen.deviceUptime'), value: devUptime.value > 0 ? formatUptime(devUptime.value) : t('screen.noData'), stateClass: 'normal' },
  { key: 'clients', icon: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M8 12a2 2 0 1 0 0-4 2 2 0 0 0 0 4z"/><path d="m22 15-4-4-4 4"/></svg>', name: t('screen.clients'), value: clientCount.value > 0 ? `${clientCount.value}` : t('screen.noData'), stateClass: 'normal' }
]);

// ===== 通信 / 故障 徽标 =====
const commStateClass = computed(() => rosState.connected ? 'normal' : 'error');
const commStateText = computed(() => rosState.connected ? t('screen.online') : t('screen.offline'));
const faultStateClass = computed(() => !rosState.connected ? 'error' : (stm32Online.value ? 'normal' : 'warning'));
const faultStateText = computed(() => !rosState.connected ? t('screen.offline') : (stm32Online.value ? t('screen.noFault') : t('screen.offline')));

// ===== 设备工作日志（真实事件）=====
const realtimeLogs = ref([]);

const addLog = (type, typeText, content) => {
  const now = new Date();
  realtimeLogs.value.unshift({ time: now.toTimeString().slice(0, 8), type, typeText, content });
  if (realtimeLogs.value.length > 20) realtimeLogs.value.pop();
  if (realtimeLogList.value) realtimeLogList.value.scrollTop = 0;
};

// ===== 超声波实时趋势图（真实数据）=====
const chartLabels = ref([]);
const chartData = ref([[], [], []]); // [左, 前, 右]
const MAX_POINTS = 20;

const initChart = () => {
  if (!todayChart.value) return;
  const chart = echarts.init(todayChart.value);
  chart.setOption({
    color: ['#00E5FF', '#FFCC00', '#00FF96'],
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(10,16,31,0.9)', borderColor: 'rgba(0,229,255,0.3)', textStyle: { color: '#e6f7ff' } },
    legend: { data: [t('radar.left'), t('radar.front'), t('radar.right')], textStyle: { color: '#8b9bb4', fontSize: 11 }, top: 5 },
    grid: { left: '5%', right: '5%', bottom: '5%', top: '20%', containLabel: true },
    xAxis: { type: 'category', data: chartLabels.value, axisLabel: { color: '#8b9bb4', fontSize: 10 }, axisLine: { lineStyle: { color: 'rgba(0,229,255,0.2)' } } },
    yAxis: { type: 'log', logBase: 10, min: 10, max: 70000, name: 'mm', nameTextStyle: { color: '#8b9bb4' }, axisLabel: { color: '#8b9bb4', formatter: (v) => (v >= 1000 ? (v/1000) + 'k' : v) }, axisLine: { lineStyle: { color: 'rgba(0,229,255,0.2)' } }, splitLine: { lineStyle: { color: 'rgba(0,229,255,0.1)' } } },
    series: [
      { name: t('radar.left'), type: 'line', data: chartData.value[0], smooth: true, lineStyle: { width: 2 } },
      { name: t('radar.front'), type: 'line', data: chartData.value[1], smooth: true, lineStyle: { width: 2 } },
      { name: t('radar.right'), type: 'line', data: chartData.value[2], smooth: true, lineStyle: { width: 2 } }
    ]
  });
  return chart;
};

let chartInstance = null;
const pushChartPoint = () => {
  if (hasData.value) {
    chartLabels.value.push(new Date().toTimeString().slice(0, 8));
    // 对数轴不接受 0/负值，0 替换为 null（断点）
    for (let i = 0; i < 3; i++) chartData.value[i].push(sensors.value[i] > 0 ? sensors.value[i] : null);
    if (chartLabels.value.length > MAX_POINTS) {
      chartLabels.value.shift();
      chartData.value.forEach(arr => arr.shift());
    }
  }
  if (chartInstance) chartInstance.setOption({
    xAxis: { data: chartLabels.value },
    series: chartData.value.map(d => ({ data: d }))
  });
};

const handleResize = () => chartInstance?.resize();

// ===== ROS 订阅（使用全局共享连接）=====
const subscribeTopics = () => {
  // 超声波距离
  waveListener = subscribeTopic('/wave_length', 'std_msgs/UInt8MultiArray', processWave);

  // STM32 在线状态
  stm32StatusListener = subscribeTopic('/stm32_status', 'std_msgs/String', (msg) => {
    const was = stm32Online.value;
    stm32Online.value = msg.data === 'online';
    if (stm32Online.value && !was) addLog('success', 'STM32', t('screen.logStm32On'));
    else if (!stm32Online.value && was) addLog('warning', 'STM32', t('screen.logStm32Off'));
  });

  // 在线终端数
  clientCountListener = subscribeTopic('/client_count', 'std_msgs/Int32', (msg) => { clientCount.value = msg.data; });

  // 相机在线状态（来自 /camera/device_status）
  camOnlineListener = subscribeTopic('/camera/device_status', 'orbbec_camera_msgs/DeviceStatus', (msg) => {
    camOnline.value = !!msg.device_online;
  });

  // CPU / 相机 RGB 温度（来自 /diagnostics）
  diagListener = subscribeTopic('/diagnostics', 'diagnostic_msgs/DiagnosticArray', (msg) => {
    if (!msg.status || !msg.status.length) return;
    const values = msg.status[0].values || [];
    values.forEach((v) => {
      if (v.key === 'CPU Temperature' && v.value) { cpuTemp.value = Number(v.value) || 0; }
      if (v.key === 'RGB Temperature' && v.value) { rgbTemp.value = Number(v.value) || 0; }
    });
  });
};

// ===== 设备开机时长（轮询 YOLO 后端 /uptime）=====
// 从状态栏 CAM 地址提取后端服务主机（如 http://localhost:8083/camera -> http://localhost:8083）
const getYoloHost = () => {
  const m = rosState.cameraUrl.match(/^(https?:\/\/[^/]+)/);
  return m ? m[1] : '';
};

const formatUptime = (secs) => {
  const d = Math.floor(secs / 86400);
  const h = Math.floor((secs % 86400) / 3600);
  const m = Math.floor((secs % 3600) / 60);
  if (d > 0) return t('screen.uptimeFmt', { d, h, m });
  if (h > 0) return t('screen.uptimeFmt', { d: 0, h, m });
  return t('screen.uptimeFmt', { d: 0, h: 0, m: Math.floor(secs / 60) || 1 });
};

const pollUptime = async () => {
  const host = getYoloHost();
  if (!host) return;
  try {
    const res = await fetch(`${host}/uptime`);
    const data = await res.json();
    const u = Number(data.uptime);
    devUptime.value = u > 0 ? u : 0;
  } catch (e) { /* 设备不可达时保持 0(显示 noData) */ }
};

const processWave = (message) => {
  let data = message.data;
  if (data && typeof data === 'object' && !Array.isArray(data)) data = data.data || data;
  if (typeof data === 'string') {
    try {
      const binaryString = atob(data);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) bytes[i] = binaryString.charCodeAt(i);
      data = Array.from(bytes);
    } catch (e) { return; }
  }
  if (!data || !Array.isArray(data) || data.length < 6) return;
  // ROS 顺序 [前方, 左边, 右边] → 映射为 [左, 前, 右]
  const mapping = [1, 0, 2];
  for (let i = 0; i < 3; i++) {
    const idx = mapping[i];
    const high = Number(data[idx * 2]) & 0xFF;
    const low = Number(data[idx * 2 + 1]) & 0xFF;
    sensors.value[i] = (high << 8) | low;
  }
  // 限频采样入趋势图（约 2 秒一个点）
  const now = Date.now();
  if (now - lastSampleAt >= 2000) {
    lastSampleAt = now;
    pushChartPoint();
  }
};

let lastSampleAt = 0;

onMounted(() => {
  chartInstance = initChart();
  connectRos();
  subscribeTopics();
  addLog('success', 'ROS', t('screen.logRosConnected'));
  // 设备开机时长轮询（约 15 秒一次，后端带缓存）
  pollUptime();
  uptimeTimer = setInterval(pollUptime, 15000);
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  if (uptimeTimer) { clearInterval(uptimeTimer); uptimeTimer = null; }
  if (waveListener) { waveListener.unsubscribe(); waveListener = null; }
  if (stm32StatusListener) { stm32StatusListener.unsubscribe(); stm32StatusListener = null; }
  if (clientCountListener) { clientCountListener.unsubscribe(); clientCountListener = null; }
  if (camOnlineListener) { camOnlineListener.unsubscribe(); camOnlineListener = null; }
  if (diagListener) { diagListener.unsubscribe(); diagListener = null; }
  window.removeEventListener('resize', handleResize);
  chartInstance?.dispose();
  chartInstance = null;
});
</script>

<style scoped>
.screen1-container {
  width: 100%;
  height: 100%;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow-y: auto;
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

/* 主内容区 - flex 布局 */
.content-area {
  display: flex;
  gap: 12px;
  flex: 1;
  min-height: 0;
}

.left-section {
  flex: 0.9;
  min-width: 260px;
  max-width: 320px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.center-section {
  flex: 1.5;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.right-section {
  flex: 0.9;
  min-width: 260px;
  max-width: 320px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 卡片样式（基础 .card/.card-header/.card-title/.card-body 已上提 common.css） */
.main-card {
  flex: 1;
}
.chart-container {
  width: 100%;
  height: 200px;
}

/* 设备状态列表 */
.state-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.state-item-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 4px;
  font-size: 0.75rem;
  color: #e6f7ff;
}

.state-item-row:hover {
  background: rgba(0, 229, 255, 0.1);
}

.state-icon {
  font-size: 0.875rem;
}

.state-name {
  flex: 1;
  color: #8b9bb4;
}

.state-value {
  font-weight: 600;
}

.state-value.normal {
  color: #00FF96;
}

.state-value.warning {
  color: #FFCC00;
}

.state-value.error {
  color: #FF3366;
}

/* 机器人视图 */
.robot-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
}

.robot-map-container {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 250px;
}

.grid-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1;
}

.grid-svg {
  width: 100%;
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(135deg, rgba(10,16,31,0.9) 0%, rgba(22,93,255,0.1) 100%);
}

.robot-model {
  position: relative;
  z-index: 2;
  width: 120px;
  filter: drop-shadow(0 0 15px rgba(0,229,255,0.4));
  animation: robotFloat 3s ease-in-out infinite;
}

@keyframes robotFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

.robot-svg {
  width: 100%;
  height: auto;
}

/* 机器人状态 */
.robot-state {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

.state-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(0, 229, 255, 0.1);
  border: 1px solid rgba(0, 229, 255, 0.2);
  border-radius: 20px;
  font-size: 0.8125rem;
}

.badge-icon {
  font-size: 0.875rem;
}

.badge-label {
  color: #8b9bb4;
}

.badge-value {
  color: #00E5FF;
  font-weight: 600;
}

.badge-value.normal {
  color: #00FF96;
}

.badge-value.error {
  color: #FF3366;
}

/* 权限警告 */
.permission-warning {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 12px;
  margin-bottom: 10px;
  background: rgba(255, 193, 7, 0.1);
  border: 1px solid rgba(255, 193, 7, 0.3);
  border-radius: 6px;
  font-size: 0.75rem;
  color: #FFC107;
}

.warning-icon {
  font-size: 0.875rem;
}

/* 故障预警 */
.alert-card {
  flex: 0.6;
}

.alert-body {
  padding: 12px;
}

.alert-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px;
  background: rgba(255, 51, 102, 0.1);
  border-left: 3px solid #FF3366;
  border-radius: 4px;
  font-size: 0.8125rem;
  color: #e6f7ff;
}

.alert-item.none {
  background: rgba(0, 255, 150, 0.1);
  border-left-color: #00FF96;
  justify-content: center;
}

.alert-icon {
  font-size: 1rem;
}

/* 底部日志区域 */
.bottom-section {
  flex-shrink: 0;
  height: 230px;
}

.bottom-section .card {
  height: 100%;
}

.log-body {
  padding: 12px;
}

.log-container {
  display: flex;
  gap: 16px;
  height: 100%;
}

/* 实时日志 */
.realtime-log {
  flex: 1.2;
  display: flex;
  flex-direction: column;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  border: 1px solid rgba(22, 93, 255, 0.15);
}

.log-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  font-size: 0.8125rem;
  font-weight: 600;
  color: #00E5FF;
  border-bottom: 1px solid rgba(22, 93, 255, 0.2);
  background: rgba(22, 93, 255, 0.05);
  flex-shrink: 0;
}

.pulse-dot {
  width: 8px;
  height: 8px;
  background: #00FF96;
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

.log-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.75rem;
}

.log-item {
  display: flex;
  gap: 10px;
  padding: 5px 8px;
  border-radius: 3px;
  margin-bottom: 3px;
  color: #e6f7ff;
}

.log-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.log-time {
  color: #8b9bb4;
  min-width: 65px;
  font-size: 0.6875rem;
}

.log-type {
  min-width: 40px;
  font-weight: 600;
  font-size: 0.625rem;
}

.log-item.info .log-type {
  color: #00E5FF;
}

.log-item.success .log-type {
  color: #00FF96;
}

.log-item.warning .log-type {
  color: #FFCC00;
}

.log-item.error .log-type {
  color: #FF3366;
}

.log-content {
  flex: 1;
  color: #e6f7ff;
}

/* 响应式 */
@media (max-width: 1200px) {
  .content-area {
    flex-direction: column;
    /* 纵向堆叠时不再参与高度分配，否则各分区会被压扁互相重叠 */
    flex: none;
  }

  .left-section,
  .right-section {
    max-width: none;
    flex: none;
    flex-direction: row;
  }

  .center-section {
    flex: none;
    min-height: 400px;
  }

  .bottom-section {
    height: auto;
    min-height: 200px;
  }
}

@media (max-width: 768px) {
  .left-section,
  .right-section {
    flex-direction: column;
  }
  
  .log-container {
    flex-direction: column;
  }
}

/* ===== 统一数据展示增强 ===== */
.badge-value {
  font-family: 'Consolas', 'Monaco', monospace;
  text-shadow: 0 0 8px rgba(0, 229, 255, 0.3);
}

.alert-item {
  transition: background 0.2s, transform 0.2s;
}

.alert-item:hover {
  transform: translateX(2px);
  background: rgba(255, 51, 102, 0.15);
}

.alert-item.none:hover {
  background: rgba(0, 255, 150, 0.15);
}

.robot-state-value,
.stat-value,
.metric-value {
  font-family: 'Consolas', 'Monaco', monospace;
  color: #00E5FF;
  text-shadow: 0 0 8px rgba(0, 229, 255, 0.3);
}

/* 图表容器层次：柔和内衬 */
.chart-container,
.echart-container {
  position: relative;
}

.chart-container::after,
.echart-container::after {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: 6px;
  box-shadow: inset 0 0 24px rgba(0, 229, 255, 0.04);
}
</style>
