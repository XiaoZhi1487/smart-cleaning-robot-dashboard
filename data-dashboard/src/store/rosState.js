import { reactive } from 'vue'

// 全局 ROS 连接状态（各页面与底部状态栏共享）
export const rosState = reactive({
  connected: false,
  url: localStorage.getItem('rosServerUrl') || 'ws://192.168.0.2:9090'
})

// 更新全局连接状态；url 为 null 时表示断开（保留原地址）
export function updateRosState(url, connected) {
  rosState.connected = connected
  if (url) {
    rosState.url = url
    localStorage.setItem('rosServerUrl', url)
  }
}