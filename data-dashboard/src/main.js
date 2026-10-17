import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import i18n from './locales'

const app = createApp(App)

// 使用 Vue Router
app.use(router)

// 使用 vue-i18n 国际化
app.use(i18n)

// 全局错误处理
app.config.errorHandler = (err, vm, info) => {
  console.error('Vue Error:', err)
  console.error('Component:', vm)
  console.error('Info:', info)
}

app.mount('#app')
