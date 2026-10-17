import { createI18n } from 'vue-i18n'
import zh from './zh'
import en from './en'
import th from './th'
import ms from './ms'
import id from './id'
import vi from './vi'

// 从本地存储读取上次选择的语言，默认中文
const savedLocale = localStorage.getItem('locale') || 'zh'

const i18n = createI18n({
  legacy: false, // 使用 Composition API 模式
  globalInjection: true,
  locale: savedLocale,
  fallbackLocale: 'zh',
  messages: {
    zh,
    en,
    th,
    ms,
    id,
    vi
  }
})

export default i18n