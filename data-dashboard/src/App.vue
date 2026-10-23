<template>
  <router-view v-slot="{ Component }">
    <transition name="fade" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>

  <!-- 全屏启动加载层：跟随懒加载路由初始化，完成后平滑淡出 -->
  <RobotLoading
    :visible="isLoading"
    :status="loadingStatus"
    :progress="loadingProgress"
  />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import router from './router'
import RobotLoading from './components/RobotLoading.vue'

const starting = Date.now()
const isLoading = ref(true)
const loadingStatus = ref('正在初始化监控系统...')
const loadingProgress = ref(null)

// 阶段式视觉进度（非真实下载百分比，仅作阶段提示）
const stages = [
  { min: 0, label: '正在加载系统资源...' },
  { min: 25, label: '正在初始化监控组件...' },
  { min: 50, label: '正在加载设备状态...' }
]

function animateProgress() {
  // 视觉进度：0 -> 90（不伪装到 100，留待真正 finished 再补满淡出）
  if (loadingProgress.value == null) loadingProgress.value = 0
  const timer = setInterval(() => {
    if (loadingProgress.value >= 90) { clearInterval(timer); return }
    loadingProgress.value += 4 + Math.random() * 4
    if (loadingProgress.value > 90) loadingProgress.value = 90
    const s = stages.filter(x => x.min <= loadingProgress.value).slice(-1)[0]
    if (s) loadingStatus.value = s.label
  }, 160)
  return timer
}

onMounted(async () => {
  // 移除 index.html 里的静态启动层，交棒给 Vue 内的加载层
  const el = document.getElementById('app-loader')
  if (el && el.parentNode) el.parentNode.removeChild(el)

  const timer = animateProgress()

  try {
    loadingStatus.value = '正在初始化监控组件...'
    // 等待懒加载路由及首屏组件就绪（真正的初始化完成信号）
    await router.isReady()

    // 首次加载保留最小展示时长，手动刷新时加载完成即直接显示，不等待
    const nav = performance.getEntriesByType('navigation')[0]
    const isRefresh = nav && nav.type === 'reload'
    const elapsed = Date.now() - starting
    if (!isRefresh && elapsed < 1200) {
      await new Promise(r => setTimeout(r, 1200 - elapsed))
    }
  } catch (error) {
    // 初始化异常不阻塞进入监控页，允许继续并提示
    console.warn('初始化完成（有非关键错误）:', error)
    loadingStatus.value = '部分模块初始化完成，正在进入监控页面...'
  } finally {
    clearInterval(timer)
    loadingProgress.value = 100
    // 等进度条渲染到 100% 后再淡出
    setTimeout(() => { isLoading.value = false }, 200)
  }
})
</script>

<style>
/* 全局样式 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  font-size: 100%;
}

html, body {
  width: 100%;
  height: 100%;
  font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
  background:
    radial-gradient(1200px 600px at 80% -10%, rgba(22, 93, 255, 0.12), transparent 60%),
    radial-gradient(900px 500px at 0% 110%, rgba(0, 229, 255, 0.08), transparent 60%),
    #0a101f;
  color: #e6f7ff;
  overflow: hidden;
}

#app {
  width: 100%;
  height: 100%;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
}

::-webkit-scrollbar-thumb {
  background: rgba(0, 229, 255, 0.3);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 229, 255, 0.6);
}

/* 数字/数据等宽字体，提升数据可读性 */
.num,
.stat-value,
.coord-value,
.log-time,
.metric-value {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
}

/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 通用按钮样式 */
.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.3s;
}

.btn-primary {
  background: linear-gradient(135deg, #00E5FF 0%, #00B8D4 100%);
  color: #0a101f;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 229, 255, 0.4);
}

.btn-danger {
  background: rgba(255, 51, 102, 0.2);
  color: #FF3366;
  border: 1px solid rgba(255, 51, 102, 0.3);
}

.btn-danger:hover {
  background: rgba(255, 51, 102, 0.3);
}

/* 通用卡片样式 */
.card {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.03), transparent 30%),
    rgba(10, 16, 31, 0.8);
  border: 1px solid rgba(0, 229, 255, 0.2);
  border-radius: 8px;
  padding: 16px;
}

/* 统一表单控件（输入框/下拉/数字） */
input,
select,
textarea {
  font-family: inherit;
}

/* 禁用状态 */
[disabled] {
  opacity: 0.5;
  cursor: not-allowed !important;
}

/* 字体平滑，提升深色主题下文字清晰度 */
body,
button,
select,
input {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 文本选中配色，贴合科技感主题 */
::selection {
  background: rgba(0, 229, 255, 0.3);
  color: #e6f7ff;
}

/* 键盘焦点态统一 */
:focus-visible {
  outline: 2px solid rgba(0, 229, 255, 0.6);
  outline-offset: 2px;
}
</style>
