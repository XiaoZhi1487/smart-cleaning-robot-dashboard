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
          {{ sidebarCollapsed ? '☰' : '◀' }}
        </button>
        <img src="@/assets/logo.png" alt="Logo" class="header-logo" v-if="false">
        <h1 class="header-title">{{ $t('app.title') }}</h1>
      </div>
      
      <div class="header-right">
        <!-- 系统状态指示 -->
        <span class="status-badge">🟢 {{ $t('app.running') }}</span>

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
            :class="{ active: $route.path === route.path }"
          >
            <span class="nav-icon">{{ route.meta.icon }}</span>
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
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
    
    <!-- 底部状态栏 -->
    <footer class="layout-footer">
      <div class="footer-left">
        <span class="status-item">
          <span class="status-dot" :class="{ active: rosState.connected }"></span>
          ROS: {{ rosState.url }}
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
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { rosState } from '@/store/rosState'

const router = useRouter()
const { t, locale } = useI18n()

// 侧边栏折叠状态
const sidebarCollapsed = ref(false)
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

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
  DepthCamera: 'nav.camera'
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
  // 可以在这里检查 ROS 连接状态
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
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
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
  background: rgba(10, 16, 31, 0.8);
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
  border-radius: 6px;
  color: #8b9bb4;
  text-decoration: none;
  transition: all 0.3s;
  cursor: pointer;
  min-width: 0;
}

.nav-item:hover {
  background: rgba(0, 229, 255, 0.05);
  color: #e6f7ff;
}

.nav-item.active {
  background: rgba(0, 229, 255, 0.1);
  color: #00E5FF;
  border-left: 3px solid #00E5FF;
  margin-left: 9px;
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
  .layout-sidebar {
    width: 60px;
  }
  
  .nav-text,
  .sidebar-footer {
    display: none;
  }
  
  .nav-item {
    justify-content: center;
    padding: 12px;
  }

  .layout-footer {
    padding: 0 12px;
  }

  .footer-left {
    gap: 12px;
  }

  .footer-right {
    display: none;
  }
}
</style>