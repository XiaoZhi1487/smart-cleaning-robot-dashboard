<template>
  <div class="layout-container">
    <!-- 顶部导航栏 -->
    <header class="layout-header">
      <div class="header-left">
        <button
          class="sidebar-toggle"
          :title="sidebarCollapsed ? $t('nav.expand') : $t('nav.collapse')"
          :aria-label="sidebarCollapsed ? $t('nav.expand') : $t('nav.collapse')"
          @click="toggleSidebar"
        >
          <svg v-if="!sidebarCollapsed" class="icon-svg" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
          <svg v-else class="icon-svg" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6h16"/><path d="M4 12h16"/><path d="M4 18h16"/></svg>
        </button>
        <h1 class="header-title">{{ headerTitle }}</h1>
      </div>
      
      <div class="header-right">
        <!-- 系统状态指示 -->
        <span class="status-badge"><svg class="icon-svg" viewBox="0 0 24 24" width="10" height="10" fill="currentColor"><circle cx="12" cy="12" r="8"/></svg> {{ $t('app.running') }}</span>

        <!-- 语言切换 -->
        <div class="lang-switch">
          <select
            class="lang-select"
            :value="locale"
            aria-label="Language"
            @change="setLocale($event.target.value)"
          >
            <option v-for="lang in languages" :key="lang.value" :value="lang.value">
              {{ lang.label }}
            </option>
          </select>
        </div>
      </div>
    </header>
    
    <!-- 主体区域 -->
    <div class="layout-body">
      <!-- 左侧导航菜单 -->
      <aside class="layout-sidebar" :class="{ collapsed: sidebarCollapsed }">
        <nav class="sidebar-nav">
          
          <router-link
            v-for="route in accessibleRoutes"
            :key="route.path"
            :to="route.path"
            class="nav-item"
            :class="{ active: $route.name === route.name }"
          >
            <span class="nav-icon" v-html="route.meta.icon"></span>
            <span class="nav-text">{{ $t(route.titleKey) }}</span>
          </router-link>
        </nav>
        
        <!-- 系统信息 -->
        <div class="sidebar-footer">
          <h4 class="footer-title">{{ $t('sys.info') }}</h4>
          <div class="footer-info">
            <div class="info-item">
              <span class="info-label">{{ $t('sys.platform') }}</span>
              <span class="info-value">RK3588</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ $t('sys.rosVersion') }}</span>
              <span class="info-value">Humble</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ $t('sys.frontend') }}</span>
              <span class="info-value">Vue 3</span>
            </div>
          </div>
        </div>
      </aside>
      
      <!-- 主内容区 -->
      <main class="layout-main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <!-- keep-alive 缓存页面实例,切换路由不销毁,保留终端/图表/日志等状态 -->
            <keep-alive>
              <component :is="Component" />
            </keep-alive>
          </transition>
        </router-view>
      </main>
    </div>
    
    <!-- 底部状态栏（左下角连接设置） -->
    <footer class="layout-footer">
      <div class="footer-left">
        <span class="status-item">
          <span class="status-dot" :class="{ active: rosState.connected }"></span>
          ROS:
          <input v-model="rosIp" :disabled="rosState.connected" class="mini-input ip-input" spellcheck="false" @keyup.enter="toggleRos" />
          :
          <input v-model="rosPort" :disabled="rosState.connected" class="mini-input port-input" spellcheck="false" @keyup.enter="toggleRos" />
          <button class="mini-btn" :class="{ danger: rosState.connected }" @click="toggleRos">
            {{ rosState.connected ? $t('footer.disconnect') : $t('footer.connect') }}
          </button>
        </span>
        <span class="status-item">
          <span class="status-dot" :class="{ active: rosState.connected }"></span>
          CAM:
          <input v-model="cameraIp" class="mini-input cam-input" spellcheck="false" @change="applyCamera" @keyup.enter="applyCamera" />
        </span>
        <span class="status-item">
          <span class="status-dot" :class="{ active: rosState.connected }"></span>
          {{ $t('footer.status') }}: {{ rosStatus }}
        </span>
      </div>
      <div class="footer-right">
        <span>{{ $t('footer.copyright') }}</span>
      </div>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'MainLayout'
}
</script>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { rosState, connectRos, disconnectRos, updateRosState, updateCameraUrl } from '@/store/rosState'

const router = useRouter()
const { t, locale } = useI18n()

// 底部连接设置：ROS 服务器（拆分为 IP + 端口）
const rosIp = ref('192.168.0.2')
const rosPort = ref('9090')
// 相机（YOLO 带标注流）地址
const cameraIp = ref('http://localhost:8083/camera')

const parseRosUrl = () => {
  const m = rosState.url.match(/^ws:\/\/([^:]+):(\d+)/)
  if (m) {
    rosIp.value = m[1]
    rosPort.value = m[2]
  }
}

// 切换 ROS 连接
const toggleRos = () => {
  if (rosState.connected) {
    disconnectRos()
  } else {
    updateRosState(`ws://${rosIp.value}:${rosPort.value}`, false)
    connectRos()
  }
}

// 应用相机流地址
const applyCamera = () => {
  updateCameraUrl(cameraIp.value.trim())
}

// 侧边栏折叠状态（桌面端手动折叠；手机端按钮隐藏）
const sidebarCollapsed = ref(false)
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

// 移动端适配:底部导航模式 + 顶部标题切换
const isMobile = ref(typeof window !== 'undefined' && window.innerWidth <= 768)
const mobileMq = typeof window !== 'undefined' ? window.matchMedia('(max-width: 768px)') : null
const onMobileMq = (e) => { isMobile.value = e.matches }
mobileMq?.addEventListener('change', onMobileMq)
onUnmounted(() => mobileMq?.removeEventListener('change', onMobileMq))
const headerTitle = computed(() => (isMobile.value ? t('app.titleMobile') : t('app.title')))

// 支持的语言列表（用于切换按钮）
const languages = [
  { value: 'zh', label: '中文' },
  { value: 'en', label: 'English' },
  { value: 'th', label: 'ไทย' },
  { value: 'ms', label: 'Bahasa Melayu' },
  { value: 'id', label: 'Bahasa Indonesia' },
  { value: 'vi', label: 'Tiếng Việt' }
]

// 切换语言并持久化到 localStorage
const setLocale = (value) => {
  locale.value = value
  localStorage.setItem('locale', value)
}

// ROS 连接状态（使用全局状态，与各页面连接面板联动）
const rosStatus = computed(() => {
  return rosState.connected ? t('footer.connected') : t('footer.disconnected')
})

// 路由名称 -> 翻译键映射
const titleKeyMap = {
  Dashboard: 'nav.dashboard',
  UltrasonicRadar: 'nav.ultrasonic',
  DepthCamera: 'nav.camera',
  Console: 'nav.console'
}

// 获取所有路由（移除权限过滤）
const accessibleRoutes = computed(() => {
  const layoutRoute = router.getRoutes().find(r => r.name === 'Layout')
  if (!layoutRoute || !layoutRoute.children) return []
  
  return layoutRoute.children.map((r) => ({
    ...r,
    titleKey: titleKeyMap[r.name] || r.meta.title
  }))
})

onMounted(() => {
  parseRosUrl()
  cameraIp.value = rosState.cameraUrl
  // 页面挂载时自动建立 ROS 连接（左下角状态栏统一管理）
  connectRos()
})
</script>

<style scoped>
.layout-container {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #0a101f;
  overflow: hidden;
}

/* 顶部导航栏 */
.layout-header {
  height: 60px;
  background: linear-gradient(90deg, rgba(10, 16, 31, 0.95) 0%, rgba(22, 93, 255, 0.1) 100%);
  border-bottom: 1px solid rgba(0, 229, 255, 0.2);
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
  position: relative;
  z-index: 10;
}

/* 顶部导航底部发光线条 */
.layout-header::after {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  bottom: -1px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0, 229, 255, 0.5), transparent);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

/* 侧边栏折叠按钮 */
.sidebar-toggle {
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  background: rgba(0, 229, 255, 0.1);
  border: 1px solid rgba(0, 229, 255, 0.3);
  border-radius: 6px;
  color: #00E5FF;
  font-size: 0.9375rem;
  line-height: 1;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.sidebar-toggle:hover {
  background: rgba(0, 229, 255, 0.2);
  box-shadow: 0 0 8px rgba(0, 229, 255, 0.3);
}

.header-logo {
  width: 40px;
  height: 40px;
}

.header-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #00E5FF;
  text-shadow: 0 0 10px rgba(0, 229, 255, 0.5);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-subtitle {
  font-size: 0.75rem;
  color: #8b9bb4;
  padding-left: 12px;
  border-left: 1px solid rgba(139, 155, 180, 0.3);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.status-badge {
  padding: 6px 12px;
  background: rgba(0, 255, 150, 0.15);
  border: 1px solid rgba(0, 255, 150, 0.3);
  border-radius: 4px;
  font-size: 0.75rem;
  color: #00FF96;
}

/* 语言切换下拉选择器 */
.lang-switch {
  display: flex;
  align-items: center;
}

.lang-select {
  padding: 5px 10px;
  border: 1px solid rgba(0, 229, 255, 0.3);
  border-radius: 4px;
  background: rgba(10, 16, 31, 0.9);
  color: #e6f7ff;
  font-size: 0.75rem;
  cursor: pointer;
  outline: none;
  transition: all 0.3s;
}

.lang-select:hover,
.lang-select:focus {
  border-color: rgba(0, 229, 255, 0.6);
  box-shadow: 0 0 6px rgba(0, 229, 255, 0.3);
}

.lang-select option {
  background: #0a101f;
  color: #e6f7ff;
}

/* 主体区域 */
.layout-body {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 左侧边栏 */
.layout-sidebar {
  width: 220px;
  background:
    linear-gradient(180deg, rgba(13, 20, 33, 0.9), rgba(10, 16, 31, 0.8));
  border-right: 1px solid rgba(0, 229, 255, 0.1);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow: hidden;
  transition: width 0.3s ease;
}

/* 折叠状态：完全隐藏 */
.layout-sidebar.collapsed {
  width: 0;
  border-right: none;
}

.sidebar-nav {
  flex: 1;
  padding: 16px 0;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  margin: 4px 12px;
  border-radius: 8px;
  color: #8b9bb4;
  text-decoration: none;
  transition: all 0.3s;
  cursor: pointer;
  min-width: 0;
  position: relative;
}

.nav-item:hover {
  background: rgba(0, 229, 255, 0.06);
  color: #e6f7ff;
}

.nav-item.active {
  background: linear-gradient(90deg, rgba(0, 229, 255, 0.12), rgba(0, 229, 255, 0.03));
  color: #00E5FF;
  border-left: 3px solid #00E5FF;
  margin-left: 9px;
  box-shadow: inset 0 0 12px rgba(0, 229, 255, 0.08);
}

.nav-item.active .nav-icon {
  filter: drop-shadow(0 0 6px rgba(0, 229, 255, 0.6));
}

.nav-item:active {
  transform: scale(0.98);
}

.nav-icon {
  font-size: 1.125rem;
  flex-shrink: 0;
}

.nav-text {
  font-size: 0.875rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 侧边栏底部信息 */
.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(0, 229, 255, 0.1);
}

.footer-title {
  font-size: 0.8125rem;
  color: #00E5FF;
  margin-bottom: 12px;
  font-weight: 600;
}

.footer-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  font-size: 0.6875rem;
}

.info-label {
  color: #5a6a7f;
}

.info-value {
  color: #8b9bb4;
}

/* 主内容区 */
.layout-main {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  background: #0d1421;
}

/* 底部状态栏 */
.layout-footer {
  height: 44px;
  background: rgba(10, 16, 31, 0.95);
  border-top: 1px solid rgba(0, 229, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
  position: relative;
}

.layout-footer::before {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  top: -1px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(0, 229, 255, 0.4), transparent);
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 24px;
}

.footer-right {
  color: #8b9bb4;
  font-size: 0.6875rem;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.6875rem;
  color: #e6f7ff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #e74c3c;
  flex-shrink: 0;
}

.status-dot.active {
  background: #00FF96;
  box-shadow: 0 0 6px rgba(0, 255, 150, 0.6);
}

.status-dot.active.pulse {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 4px rgba(0, 255, 150, 0.4); }
  50% { box-shadow: 0 0 10px rgba(0, 255, 150, 0.9); }
}

/* 左下角连接设置：紧凑输入与按钮 */
.mini-input {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(22, 93, 255, 0.3);
  border-radius: 3px;
  color: #e6f7ff;
  font-size: 0.6875rem;
  padding: 2px 6px;
  width: 92px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.mini-input:focus {
  outline: none;
  border-color: rgba(0, 229, 255, 0.6);
  box-shadow: 0 0 6px rgba(0, 229, 255, 0.25);
}

.mini-input::placeholder {
  color: #5a6a7f;
}

.mini-input.port-input {
  width: 52px;
}

/* CAM 地址输入框加宽到 180px */
.mini-input.cam-input {
  width: 180px;
}

.mini-btn {
  background: rgba(0, 229, 255, 0.15);
  border: 1px solid rgba(0, 229, 255, 0.4);
  color: #00E5FF;
  border-radius: 3px;
  padding: 2px 8px;
  font-size: 0.6875rem;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.mini-btn:hover {
  background: rgba(0, 229, 255, 0.3);
  border-color: rgba(0, 229, 255, 0.7);
  box-shadow: 0 0 8px rgba(0, 229, 255, 0.3);
}

.mini-btn:active {
  transform: scale(0.96);
}

.mini-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}

/* 折叠按钮 */

.mini-btn.danger {
  border-color: rgba(255, 51, 102, 0.4);
  color: #FF3366;
}

.mini-btn.active {
  background: rgba(0, 229, 255, 0.3);
  border-color: rgba(0, 229, 255, 0.7);
  color: #00E5FF;
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

/* 响应式 */
@media (max-width: 768px) {
  /* 顶部:隐藏折叠按钮与状态徽标,h1 保持显示(文案由 headerTitle 切换) */
  .sidebar-toggle,
  .status-badge {
    display: none;
  }

  /* 左侧边栏改为底部导航栏 */
  .layout-sidebar {
    position: fixed;
    left: 0;
    right: 0;
    bottom: 0;
    top: auto;
    width: 100%;
    height: 56px;
    flex-direction: row;
    border-right: none;
    border-top: 1px solid rgba(0, 229, 255, 0.2);
    z-index: 20;
  }

  .sidebar-nav {
    flex: none;
    display: flex;
    flex-direction: row;
    width: 100%;
    padding: 0;
    overflow-x: auto;
  }

  .nav-item {
    flex: 1;
    flex-direction: column;
    justify-content: center;
    gap: 2px;
    padding: 6px 4px;
    margin: 0;
    border-radius: 0;
    text-align: center;
  }

  .nav-item.active {
    border-left: none;
    border-top: 2px solid #00E5FF;
    margin-left: 0;
    background: linear-gradient(180deg, rgba(0,229,255,0.32), rgba(0,229,255,0.10));
    color: #00E5FF;
    box-shadow: inset 0 0 0 1px rgba(0,229,255,0.4);
  }

  .nav-item.active .nav-icon {
    filter: drop-shadow(0 0 6px rgba(0,229,255,0.9));
  }

  .nav-item.active .nav-text {
    color: #00E5FF;
    font-weight: 700;
  }

  .nav-text {
    font-size: 0.625rem;
    color: inherit;
  }

  /* 底部导航不展示系统信息 */
  .sidebar-footer {
    display: none;
  }

  /* 主内容区为底部导航留出空间,并允许纵向滚动 */
  .layout-main {
    padding-bottom: 56px;
    overflow: auto;
  }

  /* 手机端隐藏整个底部连接状态栏 */
  .layout-footer {
    display: none;
  }
}
</style>