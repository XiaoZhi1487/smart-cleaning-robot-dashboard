# SSH 控制台（Web 终端）开发文档

> 功能目标：在监控平台**左侧菜单栏**新增「控制台」页面，用户可在浏览器里以**交互式 SSH 终端**直接登录机器人设备（默认 `192.168.0.2`），用于查看/启动/停止 ROS 服务、执行运维命令，无需再单独打开终端软件。
>
> 需求确认结论（用户已选择）：
> - 交互形式：**交互式终端**（xterm.js 实时双向，支持 vim / top / ros2 run 等）
> - 凭据处理：**页面表单手动填写 + 保存在浏览器 localStorage** 自动回填
> - 连接目标：**固定机器人设备**（默认 192.168.0.2，IP 可改）
> - 文档范围：**完整开发文档**

---

## 1. 背景与目标

当前机器人编程/维护依赖本机 SSH 客户端手动连接 `192.168.0.2`。为简化运维，希望把 SSH 能力集成进现有 Vue3 监控大屏：

1. 浏览器内一键登录机器人，免装额外工具。
2. 在终端里可直接执行 `ros2 topic list`、`ros2 run ...`、`python3 start_all_services.py` 等运维/启动命令。
3. 与现有「底部状态栏手动填 ROS/相机地址」体验一致：表单 + 本地记忆。

**约束（来自项目记忆/约定）**：
- 后端依赖安装到**系统 Python3.9**（`E:\python\Python39\python.exe`），不使用 venv。
- 前端经 `npm run serve`（`serve-all.js`）并**并行启动后端进程**，Ctrl+C 统一关闭。
- 增量升级，不破坏现有 ROS 连接、路由、相机、控制逻辑。
- SSH 密码**不得硬编码**到代码（凭据由用户在表单输入 + localStorage 记忆）；仅默认填好主机 IP。
- 上线的服务端口避免与现有端口冲突（8081 前端 / 8082 设备相机 / 8083 YOLO / 9090 rosbridge）。

---

## 2. 总体架构

```
浏览器 (Vue3 + xterm.js, 端口 8081)
   │  1) fetch 保存/读取连接表单
   ▼
WebSocket  (ws://localhost:8084/  ← 文本帧: JSON)
   │
后端 ssh_server.py (websockets + paramiko, 端口 8084)
   │  2) paramiko 建立 SSH, 开一个 PTY 交互 shell
   ▼
SSH (22) 192.168.0.2 (nvidia / 用户输入密码)
   │  3) ros2 / bash / python 任何交互式命令
   ▼
机器人设备 (ROS2 Humble, rosbridge 9090, camera_http 8082)
```

链路要点：
- **前端→后端**：`ws://localhost:8084/`，后端用 `websockets` 协议库起独立 WebSocket 服务（与 YOLO 的 Flask 进程分离，互不影响）。
- **后端→设备**：每建立一个 WS 连接，就 `paramiko.invoke_shell()` 开一个**交互式 PTY shell**（不是 `exec_command`，后者只能跑单条命令无法交互）。
- **数据方向**：
  - 设备输出/回显 → channel stdout → WS 发 `output` 帧 → xterm `write()`。
  - 键盘输入 → xterm `onData` → WS 发 `input` 帧 → channel 写回。
  - 终端尺寸变化 → WS 发 `resize` 帧 → `channel.resize_pty()`。
- **WS 关闭/断开 → 关闭 paramiko channel 与 client**，避免连接/线程泄漏（复刻相机节点抗泄漏的教训）。

---

## 3. 前后端数据流与消息协议

WebSocket 文本帧均为 JSON，`type` 区分消息角色。

### 3.1 客户端 → 后端

| type | 字段 | 说明 |
|------|------|------|
| `connect` | `host, port, username, password` | 建立 SSH 会话；成功后才允许后续消息 |
| `input` | `data`（Base64 字符串） | 终端输入字节（含普通字符与转义序列） |
| `resize` | `cols, rows` | 终端尺寸，触发 `channel.resize_pty()` |
| `close` | — | 前端主动断开，后端清理 SSH 会话 |

### 3.2 后端 → 客户端

| type | 字段 | 说明 |
|------|------|------|
| `ready` | `msg` | SSH 连接成功、shell 已就绪 |
| `output` | `data`（Base64 字符串） | 设备端输出字节（xterm.write 渲染） |
| `error` | `msg` | 连接失败原因（认证失败/超时/主机不可达） |
| `exit` | `code` | shell 退出 / 连接被服务端关闭 |

> 说明：终端输出可能是任意字节（转义序列、非 UTF-8），**统一用 Base64 编码 `data` 字段**保证无损传输；前端 `atob` 解码后转为二进制字符串写入 xterm。输入侧同理，避免特殊字节在 JSON 传输中被破坏。

---

## 4. 文件改动清单

### 4.1 新增（后端 SSH 桥）
- **`src/camera_yolo_server/ssh_server.py`**（新建）
  - 依赖：`websockets`（新装）、`paramiko`（已装）。
  - 职责：
    - 监听 `0.0.0.0:8084`，WebSocket 服务。
    - `_handle_ws(websocket)`：读 `connect` 帧 → `paramiko.SSHClient().connect(...)` → `invoke_shell(term='xterm', width, height)` → 启动**两个后台线程/异步循环**：
      - channel → WS 读循环：`channel.recv(4096)` 收到字节就 base64 后发 `output`。
      - WS → channel 写循环：收到 `input` 解码写 channel，收到 `resize` 调 `resize_pty`。
    - `try/finally` 保证任何异常都会关闭 channel + client（放在 `finally` 防止泄漏）。
    - 连接/认证失败发 `error` 帧并关闭。
  - 与 YOLO 进程隔离，不 import Flask，作为**独立进程**由 `serve-all.js` 拉起。

### 4.2 修改（后端拉起脚本）
- **`serve-all.js`**：仿照 `startYolo` 新增 `startSsh()`，spawn 系统 Python3.9 跑 `ssh_server.py`，输出加 `[ssh]` 前缀；在 `shutdown()` 里同步 kill。使其 `npm run serve` 一键拉起三个进程（前端 / YOLO / SSH 桥），Ctrl+C 统一关闭。

### 4.3 新增（前端页面）
- **`src/views/Terminal.vue`**（新建，路由 `/console`，name `Console`）
  - 顶部工具栏：主机 / 端口 / 用户名 / 密码 form（默认主机 `192.168.0.2`、账号 `nvidia`），「连接」「断开」按钮；表单值读写 **localStorage**（`sshHost/sshPort/sshUser/sshPass`）实现自动回填。
  - 终端区：`xterm.js` + `@xterm/addon-fit`，深色科技风配色与整体 `#0a101f`/`#00E5FF` 一致。
  - 逻辑：
    - `connect()`：`new WebSocket('ws://localhost:8084/')`，open 后发 `connect` 帧；收到 `ready` 才允许输入；收到 `output` 解码写入 `term.write`；收到 `error` 在终端内红色提示。
    - `term.onData` → WS 发 `input`（btoa）。
    - `term.onResize` → `fit.addon.fit()` 后发 `resize`。
    - `disconnect()`/组件卸载 (`onUnmounted`)：主动 `WebSocket.close()` 并 `term.dispose()`，**避免连接与定时器泄漏**。
    - `resize` 监听：`window.resize`/`ResizeObserver` 触发 `fit.fit()`。
  - 离线/断开状态在终端内给明确提示。

### 4.4 修改（菜单与路由）
- **`src/router/index.js`**：在 `Layout` 的 `children` 中追加 `{ path: 'console', name: 'Console', component: () => import('@/views/Terminal.vue'), meta: { title: '控制台', icon: '<svg ...>(终端图标)</svg>' } }`。
- **`src/views/Layout.vue`**：`titleKeyMap` 增加 `Console: 'nav.console'`（侧边栏菜单由 router children 自动生成，见 `accessibleRoutes`）。

### 4.5 修改（国际化）
- **`src/locales/zh.js`**（及其余 en/th/ms/id/vi）：增加 `nav.console: '控制台' / 'Console' / ...` 及终端按钮文案键（连接/断开/主机/端口/用户名/密码/连接中/已断开 等），保持多语言一致。

### 4.6 待安装依赖
- 后端（系统 Python3.9）：
  ```
  E:\python\Python39\python.exe -m pip install websockets
  ```
  （`paramiko` 已随 `/uptime` 功能安装，无需重复装）
- 前端：
  ```
  cd data-dashboard && npm install xterm @xterm/addon-fit
  ```

---

## 5. 消息/协议关键实现要点（编码时注意）

1. **必须用 `invoke_shell`（PTY），不能用 `exec_command`**——交互式终端需要伪终端承载 vim/top/命令回显/光标控制。
2. `connect(width, height)` 里 `term='xterm'` 并传入当前终端尺寸；之后每次 `resize` 调用 `channel.resize_pty(width=cols, height=rows)`。
3. paramiko 读循环用 `channel.recv(4096)`（阻塞或 `.recv_ready()`）即可，无需 socket select。
4. **清理铁律**：`login_shell` 退出、WS 断开、任何异常都必须关闭 `channel`、`client`，并结束对应线程——否则像相机节点那样积累泄漏导致无法连接。
5. Base64 编解码：Python 用 `base64.b64encode(b64decode(...))`；前端用 `btoa/atob`。xterm 写入需二进制字符串（`String.fromCharCode(...byte...)`）。
6. WebSocket 服务端校验 Origin 为 `http://localhost:8081`（或同源），避免被任意网页盗连。

---

## 6. 安装与启动

```bash
# 1) 后端依赖（系统 Python3.9）
E:\python\Python39\python.exe -m pip install websockets

# 2) 前端依赖
cd e:\Allcode\shujudaping_1017\data-dashboard
npm install xterm @xterm/addon-fit

# 3) 一键启动（前端 8081 + YOLO 8083 + SSH 桥 8084）
npm run serve
```

启动后浏览器自动打开 `http://localhost:8081`，左侧菜单出现「控制台」，点击进入填写凭据连接即可。

> 若只想单独调试后端：`E:\python\Python39\python.exe src/camera_yolo_server/ssh_server.py`（监听 8084）。

---

## 7. 验证方式

1. **编译通过**：`npm run build` 无报错。
2. **菜单可见**：`npm run serve` 后左侧出现「控制台」菜单项，点击进入页面。
3. **连接成功**：填入默认主机 `192.168.0.2`、账号 `nvidia`、密码，点「连接」，终端出现 `nvidia@...:~$` 提示符。
4. **交互正常**：依次验证
   - `ros2 topic list`（能看到 `/camera/color/image_raw` 等）；
   - `ls /home/nvidia` 、`python3 -c "print('ok')"`（普通命令、回显与光标正常）；
   - `vim --version` 或 `top`（交互式程序正常，方向键/top 刷新可用）。
5. **尺寸自适应**：拖拽窗口/全屏，终端内容自动换行重排（fit 生效）。
6. **断开与重连**：点「断开」提示已断开；再次连接成功；未知价格认证失败时终端内显示红色错误而非卡死。
7. **多语言**：切换 en/中文，「控制台」菜单文案随之变化。
8. **回归**：原「数据大屏 / 超声波 / 工业相机」页面、ROS 连接、视频流不受影响。

---

## 8. 风险与回滚

| 风险 | 应对 |
|------|------|
| 凭据保存在 localStorage 可能被其它脚本读取 | 仅做便利性记忆，属用户明示选择的折衷；文档注明「敏感环境建议勾选断开后清空」；后端**不落盘**密码 |
| 8084 端口被占 | 可在 `ssh_server.py` 顶部改端口常量，前端 WS 地址同步改 |
| WS 连接/线程泄漏导致无法再连接 | 严格 try/finally 清理 + 单会话上限（可使用）。上线前用「连续连接/断开 20 次」验证 |
| websockets 版本兼容 | 锁版 `pip install "websockets>=12"` |
| 影响现有功能 | 新增独立进程与独立路由，不 touch 现有逻辑；如出问题删除 `ssh_server.py` 的 spawn + 移除路由即可回退 |

**回退方式**：停止使用——`serve-all.js` 去掉 `startSsh()` 调用、`git checkout` 还原 `router/index.js`、`Layout.vue`、`locales/*.js`、删除 `Terminal.vue` 与 `ssh_server.py`；前端 `npm uninstall xterm @xterm/addon-fit` 即可完全恢复原状。

---

## 9. 待办实现顺序

1. 后端装 `websockets`，新建 `ssh_server.py` 并单独启动验证「人连 WS 可实现交互」。
2. `serve-all.js` 接入 `startSsh()`，一键拉起。
3. 前端 `npm install xterm @xterm/addon-fit`，新建 `Terminal.vue`。
4. `router/index.js` + `Layout.vue`（titleKeyMap）+ `locales/*` 加菜单与文案。
5. `npm run build` 编译 → `npm run serve` 全链路验证（第 7 节）。