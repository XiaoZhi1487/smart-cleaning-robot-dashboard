<template>
  <Transition name="loading-fade">
    <div v-if="visible" class="robot-loading">
      <div class="loading-content">
        <!-- 机器人扫描图标 -->
        <div class="robot-core">
          <div class="scan-ring ring-one"></div>
          <div class="scan-ring ring-two"></div>

          <div class="robot-icon">
            <svg viewBox="0 0 64 64" fill="none">
              <path
                d="M32 8V16M27 8H37"
                stroke="currentColor"
                stroke-width="2.5"
                stroke-linecap="round"
              />
              <rect
                x="13" y="17" width="38" height="35" rx="8"
                stroke="currentColor"
                stroke-width="2.5"
              />
              <rect
                x="19" y="24" width="26" height="16" rx="4"
                fill="#0A101F"
                stroke="#00E5FF"
                stroke-width="1.5"
              />
              <circle cx="25" cy="32" r="2.5" fill="#00E5FF" />
              <circle cx="39" cy="32" r="2.5" fill="#00E5FF" />
              <path
                d="M26 45H38"
                stroke="#00E5FF"
                stroke-width="2"
                stroke-linecap="round"
              />
            </svg>
          </div>

          <div class="scan-line"></div>
        </div>

        <div class="system-name">
          高空玻璃幕墙清洁机器人
        </div>
        <div class="system-subtitle">
          SMART CLEANING MONITORING SYSTEM
        </div>

        <div class="loading-status">
          <span class="status-dot"></span>
          {{ status }}
        </div>

        <!-- 阶段式视觉进度，不伪装真实下载百分比；progress 为 null 时用不确定动画 -->
        <div class="progress-track">
          <div
            class="progress-bar"
            :class="{ indeterminate: progress == null }"
            :style="progress == null ? {} : { width: `${progress}%` }"
          ></div>
        </div>

        <div class="loading-footer">
          <span>MONITORING SYSTEM</span>
          <span>{{ progress == null ? 'INITIALIZING' : `STEP ${Math.round(progress / 25)} / 4` }}</span>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
/* eslint-disable no-undef */
defineProps({
  visible: { type: Boolean, default: true },
  status: { type: String, default: '正在初始化监控系统...' },
  // null 表示使用不确定进度动画
  progress: { type: Number, default: null }
})
</script>

<style scoped>
.robot-loading {
  position: fixed;
  inset: 0;
  z-index: 99999;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  color: #e6f7ff;
  background:
    radial-gradient(1200px 600px at 80% -10%, rgba(22, 93, 255, 0.18), transparent 60%),
    radial-gradient(900px 500px at 0% 110%, rgba(0, 229, 255, 0.12), transparent 60%),
    #0a101f;
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
}

.robot-loading::before {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none;
  background-image:
    linear-gradient(rgba(0, 229, 255, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 229, 255, 0.04) 1px, transparent 1px);
  background-size: 32px 32px;
  mask-image: linear-gradient(to bottom, transparent, black 25%, black 75%, transparent);
}

.loading-content {
  position: relative;
  z-index: 1;
  width: min(420px, 86vw);
  text-align: center;
}

.robot-core {
  position: relative;
  width: 150px;
  height: 150px;
  margin: 0 auto 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.robot-icon {
  z-index: 2;
  width: 74px;
  height: 74px;
  color: #00e5ff;
  filter: drop-shadow(0 0 12px rgba(0, 229, 255, 0.4));
  animation: robot-breathe 2s ease-in-out infinite;
}

.robot-icon svg {
  width: 100%;
  height: 100%;
}

.scan-ring {
  position: absolute;
  inset: 8px;
  border: 1px solid rgba(0, 229, 255, 0.4);
  border-radius: 50%;
}

.ring-one {
  animation: ring-pulse 2.5s ease-out infinite;
}

.ring-two {
  inset: 24px;
  border-style: dashed;
  animation: ring-rotate 12s linear infinite;
}

.scan-line {
  position: absolute;
  left: 15%;
  right: 15%;
  height: 1px;
  top: 20%;
  z-index: 3;
  background: #00e5ff;
  box-shadow: 0 0 12px #00e5ff;
  opacity: 0.7;
  animation: scan 2.5s ease-in-out infinite;
}

.system-name {
  font-size: 21px;
  font-weight: 600;
  letter-spacing: 2px;
  color: #39e1f4;
  text-shadow: 0 0 16px rgba(0, 229, 255, 0.22);
}

.system-subtitle {
  margin-top: 10px;
  font-size: 10px;
  letter-spacing: 2.5px;
  color: #607d9c;
}

.loading-status {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 9px;
  margin-top: 35px;
  font-size: 13px;
  color: #a6c3db;
}

.status-dot {
  width: 6px;
  height: 6px;
  flex-shrink: 0;
  border-radius: 50%;
  background: #00e5ff;
  box-shadow: 0 0 8px rgba(0, 229, 255, 0.7);
  animation: dot-blink 1.2s infinite;
}

.progress-track {
  height: 3px;
  margin-top: 18px;
  overflow: hidden;
  background: #16243a;
  border-radius: 4px;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #1685ff, #00e5ff);
  box-shadow: 0 0 10px rgba(0, 229, 255, 0.5);
  transition: width 0.35s ease;
}

.progress-bar.indeterminate {
  width: 35%;
  animation: progress-move 1.5s ease-in-out infinite;
}

.loading-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
  color: #526984;
  font-size: 9px;
  letter-spacing: 1px;
}

.loading-fade-leave-active {
  transition: opacity 0.45s ease, visibility 0.45s ease;
}

.loading-fade-leave-to {
  opacity: 0;
  visibility: hidden;
}

@keyframes robot-breathe {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}

@keyframes ring-pulse {
  0% { transform: scale(0.8); opacity: 0.8; }
  100% { transform: scale(1.2); opacity: 0; }
}

@keyframes ring-rotate {
  to { transform: rotate(360deg); }
}

@keyframes scan {
  0%, 100% { top: 20%; opacity: 0; }
  15%, 85% { opacity: 0.8; }
  50% { top: 80%; }
}

@keyframes progress-move {
  0% { transform: translateX(-110%); }
  100% { transform: translateX(320%); }
}

@keyframes dot-blink {
  50% { opacity: 0.35; }
}

@media (prefers-reduced-motion: reduce) {
  .robot-icon,
  .scan-ring,
  .ring-two,
  .scan-line,
  .status-dot,
  .progress-bar.indeterminate {
    animation: none;
  }

  .loading-fade-leave-active {
    transition: none;
  }
}
</style>