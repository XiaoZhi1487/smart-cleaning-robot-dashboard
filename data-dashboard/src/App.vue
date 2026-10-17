<template>
  <router-view v-slot="{ Component }">
    <transition name="fade" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
</template>

<script setup>
// 应用入口组件
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
  background: #0a101f;
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
  background: rgba(0, 229, 255, 0.5);
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
  background: rgba(10, 16, 31, 0.8);
  border: 1px solid rgba(0, 229, 255, 0.2);
  border-radius: 8px;
  padding: 16px;
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
