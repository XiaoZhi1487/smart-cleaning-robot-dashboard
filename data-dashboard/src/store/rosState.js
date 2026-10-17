import { reactive } from 'vue'
import ROSLIB from 'roslib'

// 全局连接状态（各页面与底部状态栏共享）
export const rosState = reactive({
  connected: false,
  url: localStorage.getItem('rosServerUrl') || 'ws://192.168.0.2:9090',
  cameraUrl: localStorage.getItem('cameraUrl') || 'http://localhost:8083/camera',
  videoSource: localStorage.getItem('videoSource') || 'ros'
})

// 共享的单个 ROS 连接实例（由底部状态栏统一管理，各页面只负责订阅/发布）
let ros = null

function getRos() {
  if (ros) return ros
  ros = new ROSLIB.Ros({ url: rosState.url })
  ros.on('connection', () => { rosState.connected = true })
  ros.on('close', () => { rosState.connected = false; ros = null })
  ros.on('error', () => { rosState.connected = false })
  return ros
}

// 连接 ROS（底部状态栏调用；已有连接则复用并可用新地址重连）
export function connectRos() {
  const r = getRos()
  if (!rosState.connected) {
    try { r.connect(rosState.url) } catch (e) { /* ignore */ }
  }
  return r
}

// 断开 ROS（底部状态栏调用）
export function disconnectRos() {
  if (ros) { ros.close(); ros = null }
  rosState.connected = false
}

// 订阅话题（各页面使用）
export function subscribeTopic(name, messageType, callback) {
  const topic = new ROSLIB.Topic({ ros: getRos(), name, messageType })
  topic.subscribe(callback)
  return topic
}

// 发布话题（各页面使用）
export function publishTopic(name, messageType, msg) {
  const topic = new ROSLIB.Topic({ ros: getRos(), name, messageType })
  topic.publish(msg)
}

// 更新全局连接地址；url 为 null 时表示断开（保留原地址）
export function updateRosState(url, connected) {
  rosState.connected = connected
  if (url) {
    rosState.url = url
    localStorage.setItem('rosServerUrl', url)
  }
}

// 更新相机（YOLO 带标注流）地址
export function updateCameraUrl(url) {
  rosState.cameraUrl = url
  localStorage.setItem('cameraUrl', url)
}

// 切换视频源：'ros' = ROS2 话题；'python' = Python YOLO HTTP 流
export function updateVideoSource(mode) {
  rosState.videoSource = mode === 'python' ? 'python' : 'ros'
  localStorage.setItem('videoSource', rosState.videoSource)
}
