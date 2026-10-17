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
              <div class="state-item-row">
                <span class="state-icon">🔵</span>
                <span class="state-name">{{ $t('screen.vacuum') }}</span>
                <span class="state-value normal">8/8{{ $t('screen.normal') }}</span>
              </div>
              <div class="state-item-row">
                <span class="state-icon">🔵</span>
                <span class="state-name">{{ $t('screen.servo') }}</span>
                <span class="state-value normal">4/4{{ $t('screen.running') }}</span>
              </div>
              <div class="state-item-row">
                <span class="state-icon">🔵</span>
                <span class="state-name">{{ $t('screen.cleaning') }}</span>
                <span class="state-value normal">{{ $t('screen.normal') }}</span>
              </div>
              <div class="state-item-row">
                <span class="state-icon">🔵</span>
                <span class="state-name">{{ $t('screen.antiFall') }}</span>
                <span class="state-value normal">{{ $t('screen.normal') }}</span>
              </div>
              <div class="state-item-row">
                <span class="state-icon">🔵</span>
                <span class="state-name">{{ $t('screen.fillLight') }}</span>
                <span class="state-value normal">{{ $t('screen.on') }}</span>
              </div>
              <div class="state-item-row">
                <span class="state-icon">🔵</span>
                <span class="state-name">{{ $t('screen.edgeDetect') }}</span>
                <span class="state-value normal">{{ $t('screen.noWarning') }}</span>
              </div>
              <div class="state-item-row">
                <span class="state-icon">🔵</span>
                <span class="state-name">{{ $t('screen.spray') }}</span>
                <span class="state-value normal">0.4MPa</span>
              </div>
              <div class="state-item-row">
                <span class="state-icon">🔵</span>
                <span class="state-name">{{ $t('screen.posture') }}</span>
                <span class="state-value normal">{{ $t('screen.tilt') }}2°</span>
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
              
              <!-- 坐标信息 -->
              <div class="position-info">
                <div class="coord-item">X: <span class="coord-value">128.5</span> m</div>
                <div class="coord-item">Y: <span class="coord-value">86.3</span> m</div>
                <div class="coord-item">Z: <span class="coord-value">45.2</span> m</div>
              </div>
            </div>

            <!-- 机器人状态 -->
            <div class="robot-state">
              <div class="state-badge">
                <span class="badge-icon">📡</span>
                <span class="badge-label">{{ $t('screen.comm') }}</span>
                <span class="badge-value" :class="getStateClass(realTimeData.connect)">{{ realTimeData.connect === '正常' ? $t('screen.normal') : realTimeData.connect }}</span>
              </div>
              <div class="state-badge">
                <span class="badge-icon">⚠️</span>
                <span class="badge-label">{{ $t('screen.fault') }}</span>
                <span class="badge-value" :class="realTimeData.fault === '无' ? 'normal' : 'error'">{{ realTimeData.fault === '无' ? $t('screen.noFault') : realTimeData.fault }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧区域：今日统计和故障预警 -->
      <div class="right-section">
        <!-- 今日作业统计 -->
        <div class="card">
          <div class="card-header">
            <span class="card-title">{{ $t('screen.todayStats') }}</span>
          </div>
          <div class="card-body">
            <div ref="todayChart" class="chart-container"></div>
          </div>
        </div>

        <!-- 机器人控制 -->
        <div class="card control-card" tabindex="0" @keydown="handleKeyDown" @keyup="handleKeyUp">
          <div class="card-header control-header">
            <span class="card-title">🎮 {{ $t('screen.robotControl') }}</span>
            <span class="control-status-badge" :class="robotControlStatus">{{ robotControlStatusText }}</span>
          </div>
          <div class="card-body control-body">
            <div class="control-grid-compact">
              <div class="control-row-compact">
                <button 
                  class="control-btn-compact" 
                  @click="moveRobot('left')" 
                  :title="$t('screen.turnLeft') + ' (A)'"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M19 12H5M12 19l-7-7 7-7"/>
                  </svg>
                </button>
                <button 
                  class="control-btn-compact forward" 
                  @click="moveRobot('forward')" 
                  :title="$t('screen.forward') + ' (W/↑)'"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 19V5M5 12l7-7 7 7"/>
                  </svg>
                </button>
                <button 
                  class="control-btn-compact" 
                  @click="moveRobot('right')" 
                  :title="$t('screen.turnRight') + ' (D)'"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M5 12h14M12 5l7 7-7 7"/>
                  </svg>
                </button>
              </div>
              <div class="control-row-compact">
                <button 
                  class="control-btn-compact backward" 
                  @click="moveRobot('backward')" 
                  :title="$t('screen.backward') + ' (S/↓)'"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 5v14M19 12l-7 7-7-7"/>
                  </svg>
                </button>
                <button 
                  class="control-btn-compact stop" 
                  @click="moveRobot('stop')" 
                  :title="$t('screen.stop') + ' (Space)'"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="6" y="6" width="12" height="12" rx="2"/>
                  </svg>
                </button>
              </div>
            </div>
            <div class="keyboard-hint">
              <span>{{ $t('screen.keyboardHint') }}</span>
            </div>
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
            <!-- 今日统计 -->
            <div class="daily-stats">
              <div class="log-section-title">{{ $t('screen.todayStats') }}</div>
              <div class="stats-grid">
                <div class="stat-box">
                  <div class="stat-icon">⏱️</div>
                  <div class="stat-info">
                    <div class="stat-label">{{ $t('screen.runTime') }}</div>
                    <div class="stat-value">{{ dailyStats.runTime }}<span class="unit">h</span></div>
                  </div>
                </div>
                <div class="stat-box">
                  <div class="stat-icon">📏</div>
                  <div class="stat-info">
                    <div class="stat-label">{{ $t('screen.cleanArea') }}</div>
                    <div class="stat-value">{{ dailyStats.cleanArea }}<span class="unit">㎡</span></div>
                  </div>
                </div>
                <div class="stat-box">
                  <div class="stat-icon">🔄</div>
                  <div class="stat-info">
                    <div class="stat-label">{{ $t('screen.cycles') }}</div>
                    <div class="stat-value">{{ dailyStats.cycles }}<span class="unit">{{ $t('screen.unitTimes') }}</span></div>
                  </div>
                </div>
                <div class="stat-box">
                  <div class="stat-icon">💧</div>
                  <div class="stat-info">
                    <div class="stat-label">{{ $t('screen.waterUsed') }}</div>
                    <div class="stat-value">{{ dailyStats.waterUsed }}<span class="unit">L</span></div>
                  </div>
                </div>
                <div class="stat-box">
                  <div class="stat-icon">⚡</div>
                  <div class="stat-info">
                    <div class="stat-label">{{ $t('screen.powerUsed') }}</div>
                    <div class="stat-value">{{ dailyStats.powerUsed }}<span class="unit">kWh</span></div>
                  </div>
                </div>
                <div class="stat-box highlight">
                  <div class="stat-icon">✅</div>
                  <div class="stat-info">
                    <div class="stat-label">{{ $t('screen.completion') }}</div>
                    <div class="stat-value">{{ dailyStats.completion }}<span class="unit">%</span></div>
                  </div>
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
import { ref, onMounted, onUnmounted, watch } from 'vue';
import * as echarts from 'echarts/core';
import { BarChart, LineChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import { LegacyGridContainLabel } from 'echarts/features';
import { getStateClass } from '@/utils';
import { useI18n } from 'vue-i18n';

defineOptions({ name: 'DataScreen' }) // eslint-disable-line no-undef

echarts.use([BarChart, LineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer, LegacyGridContainLabel]);

// 本地模拟数据
const mockData = {
  realTime: {
    code: 200,
    data: {
      connect: "正常",
      fault: "无",
      cleanArea: 128.6,
      vacuum: -75.2,
      coverRate: 92.5,
      brushSpeed: 300
    }
  },
  todayStat: {
    code: 200,
    data: {
      labels: ['08:00', '10:00', '12:00', '14:00', '16:00'],
      area: [25, 45, 38, 52, 48],
      time: [1.2, 2.1, 1.8, 2.5, 2.2]
    }
  },
  faultList: {
    code: 200,
    data: []
  }
};

// 模拟 API 请求
const requestMock = (key) => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(mockData[key] || { code: 200, data: {} });
    }, 100);
  });
};

const { t, locale } = useI18n();
const todayChart = ref(null);
const realtimeLogList = ref(null);

let todayChartInstance = null;
let refreshTimer = null;
let logTimer = null;

const realTimeData = ref({
      connect: "正常",
      fault: "无",
      cleanArea: 128.6,
      vacuum: -75.2,
      coverRate: 92.5,
      brushSpeed: 300
    });

    const faultList = ref([]);

    const buildInitialLogs = () => [
      { time: '14:32:15', type: 'info', typeText: 'INFO', content: t('screen.logStart', { area: 'A3' }) },
      { time: '14:31:08', type: 'success', typeText: 'OK', content: t('screen.logDone', { area: 'A2', size: '45.2' }) },
      { time: '14:28:42', type: 'info', typeText: 'INFO', content: t('screen.logSprayStart', { pressure: '0.4' }) },
      { time: '14:25:18', type: 'warning', typeText: 'WARN', content: t('screen.logTiltAdjust') },
      { time: '14:22:05', type: 'info', typeText: 'INFO', content: t('screen.logBrushSpeed', { speed: '300' }) },
      { time: '14:18:33', type: 'success', typeText: 'OK', content: t('screen.logDone', { area: 'A1', size: '38.6' }) },
      { time: '14:15:20', type: 'info', typeText: 'INFO', content: t('screen.logStart', { area: 'A1' }) },
      { time: '14:12:00', type: 'info', typeText: 'INFO', content: t('screen.logSelfCheck') }
    ];

    const realtimeLogs = ref(buildInitialLogs());

    const dailyStats = ref({
      runTime: '6.5',
      cleanArea: '128.6',
      cycles: '12',
      waterUsed: '45.8',
      powerUsed: '3.2',
      completion: '92.5'
    });

    // 机器人控制状态
    const robotControlStatus = ref('idle');
    const robotControlStatusText = ref(t('screen.standby'));

    // 机器人控制方法 - 点击执行，不点击立即停止
    const moveRobot = (direction) => {
      switch(direction) {
        case 'forward':
          robotControlStatus.value = 'moving';
          robotControlStatusText.value = t('screen.movingForward');
          break;
        case 'backward':
          robotControlStatus.value = 'moving';
          robotControlStatusText.value = t('screen.movingBackward');
          break;
        case 'left':
          robotControlStatus.value = 'turning';
          robotControlStatusText.value = t('screen.turningLeft');
          break;
        case 'right':
          robotControlStatus.value = 'turning';
          robotControlStatusText.value = t('screen.turningRight');
          break;
        case 'stop':
          robotControlStatus.value = 'idle';
          robotControlStatusText.value = t('screen.stopped');
          break;
      }
    };

    // 停止机器人
    const stopRobot = () => {
      robotControlStatus.value = 'idle';
      robotControlStatusText.value = t('screen.standby');
    };

    // 键盘按下 - 开始移动
    const handleKeyDown = (event) => {
      // 防止重复触发
      if (event.repeat) return;
      
      switch(event.key) {
        case 'ArrowUp':
        case 'w':
        case 'W':
          event.preventDefault();
          moveRobot('forward');
          break;
        case 'ArrowDown':
        case 's':
        case 'S':
          event.preventDefault();
          moveRobot('backward');
          break;
        case 'ArrowLeft':
        case 'a':
        case 'A':
          event.preventDefault();
          moveRobot('left');
          break;
        case 'ArrowRight':
        case 'd':
        case 'D':
          event.preventDefault();
          moveRobot('right');
          break;
        case ' ':
        case 'Space':
          event.preventDefault();
          moveRobot('stop');
          break;
      }
    };

    // 键盘释放 - 立即停止
    const handleKeyUp = (event) => {
      // 释放方向键或WASD时停止
      const key = event.key;
      if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'w', 'W', 'a', 'A', 's', 'S', 'd', 'D'].includes(key)) {
        stopRobot();
      }
    };

    const logTypes = [
      { type: 'info', typeText: 'INFO', key: 'logCleaning' },
      { type: 'success', typeText: 'OK', key: 'logCleanDone' },
      { type: 'warning', typeText: 'WARN', key: 'logEdgeWarning' },
      { type: 'info', typeText: 'INFO', key: 'logSpraying' },
      { type: 'success', typeText: 'OK', key: 'logSuctionOk' },
      { type: 'info', typeText: 'INFO', key: 'logPathAdjust' }
    ];

    const addNewLog = () => {
      const now = new Date();
      const timeStr = now.toTimeString().slice(0, 8);
      const randomLog = logTypes[Math.floor(Math.random() * logTypes.length)];
      const areas = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3'];
      const area = areas[Math.floor(Math.random() * areas.length)];
      
      let content = t(`screen.${randomLog.key}`);
      if (randomLog.key === 'logCleanDone') {
        content = t('screen.logDone', { area, size: (Math.random() * 20 + 30).toFixed(1) });
      } else if (randomLog.key === 'logCleaning') {
        content = t('screen.logStart', { area });
      }
      
      const newLog = {
        time: timeStr,
        type: randomLog.type,
        typeText: randomLog.typeText,
        content: content
      };
      
      realtimeLogs.value.unshift(newLog);
      if (realtimeLogs.value.length > 20) {
        realtimeLogs.value.pop();
      }
      
      if (realtimeLogList.value) {
        realtimeLogList.value.scrollTop = 0;
      }
    };

    const initTodayChart = (data) => {
      if (!todayChart.value) return;
      if (!todayChartInstance) {
        todayChartInstance = echarts.init(todayChart.value);
      }
      const option = {
        color: ['#00E5FF', '#00FF96'],
        tooltip: { 
          trigger: 'axis',
          backgroundColor: 'rgba(10, 16, 31, 0.9)',
          borderColor: 'rgba(0, 229, 255, 0.3)',
          textStyle: { color: '#e6f7ff' }
        },
        legend: { 
          data: [t('screen.area'), t('screen.workTime')],
          textStyle: { color: '#8b9bb4', fontSize: 11 },
          top: 5
        },
        grid: { left: '5%', right: '5%', bottom: '5%', top: '20%', containLabel: true },
        xAxis: { 
          type: 'category', 
          data: data.labels, 
          axisLabel: { color: '#8b9bb4', fontSize: 11 },
          axisLine: { lineStyle: { color: 'rgba(0, 229, 255, 0.2)' } }
        },
        yAxis: [
          { 
            type: 'value', 
            name: t('screen.areaUnit'), 
            axisLabel: { color: '#8b9bb4', fontSize: 12 },
            nameTextStyle: { color: '#8b9bb4', fontSize: 12 },
            axisLine: { lineStyle: { color: 'rgba(0, 229, 255, 0.2)' } },
            splitLine: { lineStyle: { color: 'rgba(0, 229, 255, 0.1)' } }
          },
          { 
            type: 'value', 
            name: t('screen.timeUnit'), 
            axisLabel: { color: '#8b9bb4', fontSize: 12 },
            nameTextStyle: { color: '#8b9bb4', fontSize: 12 },
            position: 'right',
            axisLine: { lineStyle: { color: 'rgba(0, 229, 255, 0.2)' } },
            splitLine: { show: false }
          }
        ],
        series: [
          {
            name: t('screen.area'),
            type: 'bar',
            yAxisIndex: 0,
            data: data.area,
            barWidth: '30%',
            itemStyle: { color: '#00E5FF' },
            label: { show: true, position: 'top', color: '#e6f7ff', fontSize: 12 }
          },
          {
            name: t('screen.workTime'),
            type: 'line',
            yAxisIndex: 1,
            data: data.time,
            smooth: true,
            lineStyle: { width: 2 },
            itemStyle: { color: '#00FF96' }
          }
        ]
      };
      todayChartInstance.setOption(option, { notMerge: true });
    };

    const loadData = async () => {
      try {
        const realTimeRes = await requestMock('realTime');
        const todayStatRes = await requestMock('todayStat');
        const faultListRes = await requestMock('faultList');

        if (realTimeRes.code === 200) {
          realTimeData.value = realTimeRes.data;
        }
        if (faultListRes.code === 200) {
          faultList.value = faultListRes.data || [];
        }

        if (todayStatRes.code === 200) {
          initTodayChart(todayStatRes.data);
        }
      } catch (error) {
        console.error('加载数据失败:', error);
      }
    };

    const refreshRealTimeData = async () => {
      try {
        const res = await requestMock('realTime');
        if (res.code === 200) {
          realTimeData.value = res.data;
        }
      } catch (error) {
        console.error('刷新数据失败:', error);
      }
    };

    const handleResize = () => {
      todayChartInstance?.resize();
    };

    watch(locale, () => {
      realtimeLogs.value = buildInitialLogs();
      if (robotControlStatus.value === 'idle') {
        robotControlStatusText.value = t('screen.standby');
      }
      loadData();
    });

    onMounted(() => {
      loadData();
      refreshTimer = setInterval(refreshRealTimeData, 5000);
      logTimer = setInterval(addNewLog, 3000);
      window.addEventListener('resize', handleResize);
    });

    onUnmounted(() => {
      if (refreshTimer) clearInterval(refreshTimer);
      if (logTimer) clearInterval(logTimer);
      window.removeEventListener('resize', handleResize);
      todayChartInstance?.dispose();
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

.position-info {
  position: absolute;
  bottom: 10px;
  left: 10px;
  z-index: 3;
  background: rgba(10,16,31,0.9);
  border: 1px solid rgba(0,229,255,0.3);
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 0.6875rem;
  color: #e6f7ff;
}

.coord-item {
  margin: 2px 0;
}

.coord-value {
  color: #00E5FF;
  font-weight: 600;
  font-family: monospace;
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

/* 机器人控制面板 - 右侧卡片 */
.control-card {
  flex: 0.6;
  outline: none;
}

.control-card:focus {
  box-shadow: 0 0 0 2px rgba(0, 229, 255, 0.3);
}

.control-header {
  background: linear-gradient(90deg, rgba(0, 229, 255, 0.15) 0%, transparent 100%);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.control-status-badge {
  font-size: 0.6875rem;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}

.control-status-badge.idle {
  background: rgba(0, 255, 150, 0.2);
  color: #00FF96;
}

.control-status-badge.moving {
  background: rgba(0, 229, 255, 0.2);
  color: #00E5FF;
}

.control-status-badge.turning {
  background: rgba(255, 204, 0, 0.2);
  color: #FFCC00;
}

.control-body {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.control-grid-compact {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.control-row-compact {
  display: flex;
  gap: 6px;
  justify-content: center;
}

.control-btn-compact {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 6px;
  background: rgba(0, 229, 255, 0.1);
  border: 1px solid rgba(0, 229, 255, 0.3);
  color: #00E5FF;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
  outline: none;
}

.control-btn-compact:hover {
  background: rgba(0, 229, 255, 0.25);
  border-color: rgba(0, 229, 255, 0.6);
  transform: scale(1.1);
}

.control-btn-compact:active {
  transform: scale(0.95);
}

.control-btn-compact:focus {
  outline: none;
  box-shadow: none;
}

.control-btn-compact svg {
  width: 16px;
  height: 16px;
}

.control-btn-compact.forward {
  background: rgba(0, 229, 255, 0.15);
}

.control-btn-compact.backward {
  background: rgba(0, 229, 255, 0.15);
}

.control-btn-compact.stop {
  background: rgba(255, 51, 102, 0.15);
  border-color: rgba(255, 51, 102, 0.4);
  color: #FF3366;
}

.control-btn-compact.stop:hover {
  background: rgba(255, 51, 102, 0.25);
  border-color: rgba(255, 51, 102, 0.6);
}

.keyboard-hint {
  text-align: center;
  font-size: 0.625rem;
  color: #8b9bb4;
  margin-top: 4px;
}

.keyboard-hint.disabled {
  color: #5a6a7f;
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

/* 禁用状态的控制按钮 */
.control-grid-compact.disabled .control-btn-compact {
  opacity: 0.4;
  cursor: not-allowed;
  background: rgba(90, 106, 127, 0.1);
  border-color: rgba(90, 106, 127, 0.3);
  color: #5a6a7f;
}

.control-grid-compact.disabled .control-btn-compact:hover {
  transform: none;
  background: rgba(90, 106, 127, 0.1);
  border-color: rgba(90, 106, 127, 0.3);
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

/* 今日统计 */
.daily-stats {
  flex: 0.8;
  display: flex;
  flex-direction: column;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  border: 1px solid rgba(22, 93, 255, 0.15);
}

.stats-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  padding: 12px;
  overflow-y: auto;
}

.stat-box {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: rgba(22, 93, 255, 0.05);
  border-radius: 6px;
  border: 1px solid rgba(22, 93, 255, 0.1);
}

.stat-box.highlight {
  background: rgba(0, 229, 255, 0.1);
  border-color: rgba(0, 229, 255, 0.3);
}

.stat-box .stat-icon {
  font-size: 1.25rem;
}

.stat-box .stat-info {
  display: flex;
  flex-direction: column;
}

.stat-box .stat-label {
  font-size: 0.6875rem;
  color: #8b9bb4;
  margin-bottom: 2px;
}

.stat-box .stat-value {
  font-size: 1rem;
  font-weight: 700;
  color: #00E5FF;
}

.stat-box.highlight .stat-value {
  color: #00FF96;
}

.stat-box .unit {
  font-size: 0.6875rem;
  color: #8b9bb4;
  margin-left: 2px;
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
  
  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
