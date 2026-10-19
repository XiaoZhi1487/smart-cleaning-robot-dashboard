<template>
  <div class="terminal-page">
    <!-- 顶部连接工具栏 -->
    <div class="term-toolbar">
      <div class="toolbar-left">
        <label class="field">
          <span>{{ $t('console.host') }}</span>
          <input v-model="form.host" class="t-input host" spellcheck="false" :disabled="connected" @keyup.enter="onConnect" />
        </label>
        <label class="field">
          <span>{{ $t('console.port') }}</span>
          <input v-model.number="form.port" type="number" class="t-input port" spellcheck="false" :disabled="connected" @keyup.enter="onConnect" />
        </label>
        <label class="field">
          <span>{{ $t('console.username') }}</span>
          <input v-model="form.username" class="t-input" spellcheck="false" :disabled="connected" @keyup.enter="onConnect" />
        </label>
        <label class="field">
          <span>{{ $t('console.password') }}</span>
          <input v-model="form.password" type="password" class="t-input pw" spellcheck="false" :disabled="connected" @keyup.enter="onConnect" />
        </label>
        <button v-if="!connected" class="t-btn primary" :disabled="connecting" @click="onConnect">
          {{ connecting ? $t('console.connecting') : $t('console.connect') }}
        </button>
        <button v-else class="t-btn danger" @click="onDisconnect">
          {{ $t('console.disconnect') }}
        </button>
        <span v-if="statusMsg" class="status-msg" :class="{ ok: connected, err: connectError }">{{ statusMsg }}</span>
      </div>
      <div class="toolbar-right">
        <span class="hint">{{ $t('console.hint') }}</span>
      </div>
    </div>

    <!-- 交互式终端(左) + 快捷命令栏(右, 150px) -->
    <div class="term-area">
      <div ref="termWrap" class="term-wrap" :class="{ connected }">
        <div ref="termBox" class="term-box"></div>
      </div>
      <aside class="quickbar">
        <div class="q-title">快捷命令</div>
        <div class="q-scroll">
          <div v-for="group in quickGroups" :key="group.title" class="q-group">
            <div class="q-group-title">{{ group.title }}</div>
            <button
              v-for="item in group.cmds"
              :key="item.label"
              class="q-btn"
              :disabled="!connected"
              :title="item.cmd"
              @click="runQuick(item.cmd)"
            >{{ item.label }}</button>
          </div>
        </div>
        <div class="q-foot" :class="{ off: !connected }">
          {{ connected ? $t('console.quickReady') : $t('console.quickWait') }}
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
/* eslint-disable no-empty */   // 多个守卫性空 catch(忽略连接/解码异常不计日志)
import { reactive, ref, nextTick, onMounted, onBeforeUnmount, onActivated } from 'vue'
import { useI18n } from 'vue-i18n'
import { Terminal } from '@xterm/xterm'
import '@xterm/xterm/css/xterm.css'
import { FitAddon } from '@xterm/addon-fit'
import { WebglAddon } from '@xterm/addon-webgl'
import { CanvasAddon } from '@xterm/addon-canvas'

const { t } = useI18n()

// —— 连接表单(与 localStorage 联动实现记住) ——
const form = reactive({
  host: localStorage.getItem('sshHost') || '192.168.0.2',
  port: Number(localStorage.getItem('sshPort') || 22),
  username: localStorage.getItem('sshUser') || 'nvidia',
  password: localStorage.getItem('sshPass') || ''
})

const connected = ref(false)
const connecting = ref(false)
const connectError = ref(false)
const statusMsg = ref('')

// —— 终端引用 ——
const termWrap = ref(null)
const termBox = ref(null)
let term = null
let fitAddon = null
let ws = null
let disposed = false
const WS_URL = `ws://${location.hostname}:8084/`

// —— base64(UTF-8) 编解码，与后端 paramiko 桥协议一致 ——
function b64Encode(str) {
  const bytes = new TextEncoder().encode(str)
  let bin = ''
  for (const b of bytes) bin += String.fromCharCode(b)
  return btoa(bin)
}

function send(type, payload = {}) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type, ...payload }))
  }
}

function writeText(text) {
  if (term && !disposed) term.write(text)
}

// —— 右侧快捷命令栏:分组展示,点击即在终端执行 ——
// 实时资源占用:优先 htop,未安装则退回 top(两者均为实时 CPU/内存/进程监控)
const SYS_MONITOR = 'command -v htop >/dev/null 2>&1 && htop || top'
const quickGroups = [
  { title: '服务', cmds: [
    { label: '机器人服务管理器', cmd: 'python /home/nvidia/name_huanghongle3/robot_service_manager.py' }
  ]},
  { title: 'ROS 运维', cmds: [
    { label: '查看 ros2 话题', cmd: 'ros2 topic list' },
    { label: '查看节点', cmd: 'ros2 node list' },
    { label: '查看服务', cmd: 'ros2 service list' },
    { label: '相机帧率', cmd: 'ros2 topic hz /camera/color/image_raw' },
    { label: '定位数据', cmd: 'timeout 3 ros2 topic echo /ultrasonic_position' }
  ]},
  { title: '系统 / 硬件', cmds: [
    { label: '实时资源占用 htop/top', cmd: SYS_MONITOR },
    { label: 'GPU 状态 nvidia-smi', cmd: 'nvidia-smi' },
    { label: '内存 free -h', cmd: 'free -h' },
    { label: '磁盘 df -h', cmd: 'df -h' },
    { label: '关机 shutdown', cmd: 'sudo shutdown -h now' }
  ]}
]

function runQuick(cmd) {
  if (!connected.value) return
  // 模拟在终端输入该命令并按回车;PTY 中回车为 \r
  send('input', { data: b64Encode(cmd + '\r') })
}

function initTerm() {
  term = new Terminal({
    cursorBlink: true,
    fontSize: 14,
    fontFamily: '"Sarasa Mono SC", "Microsoft YaHei Mono", "Cascadia Mono", Consolas, monospace',
    lineHeight: 1.2,
    letterSpacing: 0,
    theme: {
      background: '#0d1421',
      foreground: '#e6f7ff',
      cursor: '#00E5FF',
      selectionBackground: 'rgba(0,229,255,0.3)'
    }
  })
  fitAddon = new FitAddon()
  term.loadAddon(fitAddon)
  term.open(termBox.value)
  fitAddon.fit()

  // 使用 GPU(WebGL) 渲染器:整行一起绘制,避免默认逐字符 DOM 渲染导致的字符间距错位
  // WebGL 创建失败(无 GPU 上下文)时回退到 Canvas 渲染器
  try {
    const webgl = new WebglAddon()
    webgl.onContextLoss(() => webgl.dispose())
    term.loadAddon(webgl)
  } catch (e) {
    try { term.loadAddon(new CanvasAddon()) } catch (e2) {}
  }

  // 输入 -> 后端
  term.onData((data) => send('input', { data: b64Encode(data) }))
  // 尺寸变化 -> 后端 resize
  term.onResize(({ cols, rows }) => send('resize', { cols, rows }))
}

function onConnect() {
  if (connecting.value) return
  // 记住凭据(用户已确认)
  localStorage.setItem('sshHost', form.host)
  localStorage.setItem('sshPort', String(form.port))
  localStorage.setItem('sshUser', form.username)
  localStorage.setItem('sshPass', form.password)

  connecting.value = true
  connectError.value = false
  statusMsg.value = t('console.connecting')

  try {
    ws = new WebSocket(WS_URL)
  } catch (e) {
    connecting.value = false
    statusMsg.value = t('console.wsFail')
    connectError.value = true
    return
  }

  ws.onopen = () => {
    send('connect', {
      host: form.host, port: Number(form.port) || 22,
      username: form.username, password: form.password
    })
  }
  ws.onmessage = (ev) => {
    let frame
    try { frame = JSON.parse(ev.data) } catch (e) { return }
    if (frame.type === 'ready') {
      connected.value = true
      connecting.value = false
      connectError.value = false
      statusMsg.value = frame.msg || t('console.connected')
    } else if (frame.type === 'output') {
      let bytes
      try { bytes = Uint8Array.from(atob(frame.data), (c) => c.charCodeAt(0)) }
      catch (e) { return }
      writeText(new TextDecoder('utf-8').decode(bytes))
    } else if (frame.type === 'error') {
      connecting.value = false
      connectError.value = true
      statusMsg.value = frame.msg || t('console.connectFail')
      writeText(`\r\n\x1b[31m[${t('console.errorLabel')}] ${frame.msg}\x1b[0m\r\n`)
    } else if (frame.type === 'exit') {
      onDisconnect()
    }
  }
  ws.onerror = () => {
    connecting.value = false
    connectError.value = true
    statusMsg.value = t('console.errorLabel')
  }
  ws.onclose = () => {
    if (connected.value) {
      connected.value = false
      connecting.value = false
      statusMsg.value = t('console.closed')
    }
    ws = null
  }
}

function onDisconnect() {
  try { send('close') } catch (e) {}
  try { ws && ws.close() } catch (e) {}
  ws = null
  connected.value = false
  connecting.value = false
  statusMsg.value = t('console.disconnected')
}

// 窗口尺寸变化时让终端自适应
function onWindowResize() {
  if (fitAddon) {
    try { fitAddon.fit() } catch (e) {}
  }
}

onMounted(() => {
  disposed = false
  initTerm()
  window.addEventListener('resize', onWindowResize)
})

// keep-alive 重新激活:DOM 重新插入,重测终端尺寸并刷新,避免切回时空白/错位
onActivated(async () => {
  if (!term) return
  await nextTick()
  try { fitAddon.fit() } catch (e) {}
  try { term.refresh(0, term.rows - 1) } catch (e) {}
})

onBeforeUnmount(() => {
  disposed = true
  window.removeEventListener('resize', onWindowResize)
  try { send('close') } catch (e) {}
  try { ws && ws.close() } catch (e) {}
  ws = null
  try { term && term.dispose() } catch (e) {}
  term = null
})
</script>

<style scoped>
.terminal-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  box-sizing: border-box;
  background: transparent;
  overflow: hidden;
}

.term-toolbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  padding: 10px 14px;
  background: linear-gradient(90deg, rgba(13, 20, 33, 0.9), rgba(10, 16, 31, 0.85));
  border: 1px solid rgba(0, 229, 255, 0.15);
  border-radius: 8px;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.field {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  color: #8b9bb4;
  white-space: nowrap;
}

.t-input {
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid rgba(22, 93, 255, 0.3);
  border-radius: 4px;
  color: #e6f7ff;
  font-size: 0.75rem;
  padding: 4px 8px;
  width: 130px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.t-input:focus {
  outline: none;
  border-color: rgba(0, 229, 255, 0.6);
  box-shadow: 0 0 6px rgba(0, 229, 255, 0.25);
}

.t-input:disabled {
  opacity: 0.55;
}

.t-input.host { width: 130px; }
.t-input.port { width: 60px; }
.t-input.pw { width: 120px; }

.t-btn {
  border-radius: 4px;
  padding: 5px 16px;
  font-size: 0.75rem;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
  white-space: nowrap;
}

.t-btn.primary {
  background: rgba(0, 229, 255, 0.15);
  border-color: rgba(0, 229, 255, 0.5);
  color: #00E5FF;
}

.t-btn.primary:hover:not(:disabled) {
  background: rgba(0, 229, 255, 0.3);
  box-shadow: 0 0 8px rgba(0, 229, 255, 0.3);
}

.t-btn.primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.t-btn.danger {
  background: rgba(255, 51, 102, 0.15);
  border-color: rgba(255, 51, 102, 0.5);
  color: #FF3366;
}

.t-btn.danger:hover {
  background: rgba(255, 51, 102, 0.3);
}

.status-msg {
  font-size: 0.75rem;
  color: #8b9bb4;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.status-msg.ok { color: #00FF96; }
.status-msg.err { color: #FF3366; }

.hint {
  font-size: 0.6875rem;
  color: #5a6a7f;
}

.term-wrap {
  flex: 1;
  min-width: 0;
  min-height: 0;
  background: #0d1421;
  border: 1px solid rgba(0, 229, 255, 0.12);
  border-radius: 8px;
  padding: 8px;
  overflow: hidden;
}

.term-wrap.connected {
  border-color: rgba(0, 229, 255, 0.4);
  box-shadow: 0 0 20px rgba(0, 229, 255, 0.06);
}

.term-box {
  width: 100%;
  height: 100%;
}

/* 终端 + 快捷命令栏左右并排 */
.term-area {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: 12px;
}

/* 右侧快捷命令栏(固定 150px) */
.quickbar {
  width: 150px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, rgba(13, 20, 33, 0.9), rgba(10, 16, 31, 0.85));
  border: 1px solid rgba(0, 229, 255, 0.15);
  border-radius: 8px;
  overflow: hidden;
}

.q-title {
  flex-shrink: 0;
  padding: 8px 12px;
  font-size: 0.75rem;
  font-weight: 600;
  color: #00E5FF;
  border-bottom: 1px solid rgba(0, 229, 255, 0.12);
}

.q-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 10px;
}

.q-group {
  margin-bottom: 12px;
}

.q-group-title {
  font-size: 0.625rem;
  color: #5a6a7f;
  margin-bottom: 6px;
  letter-spacing: 1px;
}

.q-btn {
  display: block;
  width: 100%;
  text-align: left;
  margin-bottom: 6px;
  padding: 7px 9px;
  font-size: 0.6875rem;
  line-height: 1.3;
  color: #c2d4ea;
  background: rgba(22, 93, 255, 0.08);
  border: 1px solid rgba(22, 93, 255, 0.25);
  border-radius: 5px;
  cursor: pointer;
  transition: all 0.15s;
  white-space: normal;
  word-break: break-all;
}

.q-btn:hover:not(:disabled) {
  background: rgba(0, 229, 255, 0.16);
  border-color: rgba(0, 229, 255, 0.5);
  color: #00E5FF;
  box-shadow: 0 0 6px rgba(0, 229, 255, 0.2);
}

.q-btn:active:not(:disabled) {
  transform: scale(0.97);
}

.q-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.q-foot {
  flex-shrink: 0;
  padding: 8px 10px;
  font-size: 0.625rem;
  color: #00FF96;
  border-top: 1px solid rgba(0, 229, 255, 0.1);
}

.q-foot.off {
  color: #5a6a7f;
}
</style>