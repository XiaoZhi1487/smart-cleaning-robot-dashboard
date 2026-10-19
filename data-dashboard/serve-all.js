/**
 * 并行启动脚本：同时启动前端 dev server 与 YOLO 标注后端
 *
 * 运行：npm run serve
 *  - 前端：vue-cli-service serve （默认 http://localhost:8080）
 *  - YOLO ：camera_yolo_server.py （默认 http://localhost:8083/camera）
 *
 * 结束：在终端按 Ctrl+C 会同时关闭两个子进程。
 */
const { spawn } = require('child_process')
const path = require('path')

const yoloScript = path.resolve(__dirname, 'src/camera_yolo_server/camera_yolo_server.py')
const sshScript = path.resolve(__dirname, 'src/camera_yolo_server/ssh_server.py')

// YOLO 后端：优先使用系统 python（Windows 常见路径），否则用 PATH 中的 python
const pythonCandidates = [
  'E:\\python\\Python39\\python.exe', // 系统 Python3.9（已装 GPU torch）
  'python',
  'python3'
]

function startYolo() {
  // 逐个尝试可用的 python 解释器
  for (const py of pythonCandidates) {
    try {
      const child = spawn(py, [yoloScript], {
        stdio: ['ignore', 'pipe', 'pipe'],
        windowsHide: true
      })
      // spawn 若抛 ENOENT 说明该解释器不存在，尝试下一个
      child.on('error', () => {})
      // YOLO 输出加 [yolo] 前缀，便于与前端日志区分
      const prefix = (buf) => String(buf)
        .split('\n')
        .filter((l) => l.trim() !== '')
        .map((l) => '[yolo] ' + l)
        .join('\n') + '\n'
      child.stdout.on('data', (d) => process.stdout.write(prefix(d)))
      child.stderr.on('data', (d) => process.stderr.write(prefix(d)))
      console.log(`[yolo] 已启动: ${py} ${yoloScript}  (流: http://localhost:8083/camera)`)
      return child
    } catch (e) {
      // 解释器不存在，继续尝试下一个
    }
  }
  console.warn('[yolo] 未找到可用 python 解释器，跳过 YOLO 后端启动')
  return null
}

function startFrontend() {
  const child = spawn('npm', ['run', 'serve:frontend'], {
    stdio: 'inherit',
    windowsHide: true,
    shell: true
  })
  child.on('error', () => {
    console.error('[frontend] 前端启动失败')
  })
  return child
}

// SSH 桥后端：与 YOLO 复用同一套 python 解释器候选，输出加 [ssh] 前缀
function startSsh() {
  for (const py of pythonCandidates) {
    try {
      const child = spawn(py, [sshScript], {
        stdio: ['ignore', 'pipe', 'pipe'],
        windowsHide: true
      })
      child.on('error', () => {})
      const prefix = (buf) => String(buf)
        .split('\n')
        .filter((l) => l.trim() !== '')
        .map((l) => '[ssh] ' + l)
        .join('\n') + '\n'
      child.stdout.on('data', (d) => process.stdout.write(prefix(d)))
      child.stderr.on('data', (d) => process.stderr.write(prefix(d)))
      console.log(`[ssh] 已启动: ${py} ${sshScript}  (ws: ws://localhost:8084)`)
      return child
    } catch (e) {
      // 解释器不存在，继续尝试下一个
    }
  }
  console.warn('[ssh] 未找到可用 python 解释器，跳过 SSH 桥后端启动')
  return null
}

const frontend = startFrontend()
const yolo = startYolo()
const ssh = startSsh()

function shutdown() {
  console.log('\n[serve-all] 正在关闭...')
  try { frontend && frontend.kill('SIGTERM') } catch (e) {}
  try { yolo && yolo.kill('SIGTERM') } catch (e) {}
  try { ssh && ssh.kill('SIGTERM') } catch (e) {}
  process.exit(0)
}

process.on('SIGINT', shutdown)
process.on('SIGTERM', shutdown)

// 前端退出则整体退出
frontend && frontend.on('exit', (code) => {
  console.log(`[frontend] 已退出 (code=${code})`)
  shutdown()
})
