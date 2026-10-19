# 机器人控制系统技术文档

## 项目概述

**项目名称**: 高空幕墙清洁机器人控制系统  
**开发阶段**: HTTP控制测试通过 / WebSocket预留 / 模拟模式运行  
**文档版本**: v1.0  
**更新日期**: 2026-03-05  

---

## 一、通信架构

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              系统架构                                    │
└─────────────────────────────────────────────────────────────────────────┘

  [Web前端]                    [Jetson后端]                  [STM32机器人]
  ┌─────────┐                 ┌─────────────┐               ┌─────────────┐
  │ Vue3    │ ──HTTP POST───→ │ Flask服务   │ ──UART串口──→ │ 控制器      │
  │ fetch   │ {cmd,duration}  │ 192.168.0.2 │ '/dev/ttyACM3'│ 执行动作    │
  │         │ ←─JSON响应──── │ :5000       │ 115200bps     │             │
  └─────────┘                 └─────────────┘               └─────────────┘
     ↓                               ↓
  localhost:8080              模拟模式(MockSTM32)
                              或真实串口(硬件模式)
```

### 1.2 通信方式

| 层级 | 协议 | 地址/端口 | 说明 |
|------|------|-----------|------|
| **应用层** | HTTP REST API | `192.168.0.2:5000` | 前端按钮控制 |
| **传输层** | TCP | 端口 5000 | Flask内置服务器 |
| **物理层** | UART串口 | `/dev/ttyACM3` | USB转串口连接STM32 |
| **数据格式** | 字符串+换行 | `'2\n'` | 数字命令+`\n`结束符 |

### 1.3 协议规范

**HTTP请求格式:**
```http
POST /api/control HTTP/1.1
Host: 192.168.0.2:5000
Content-Type: application/json

{
    "command": "forward",
    "duration": 2
}
```

**串口数据格式:**
```
数字 + '\n' (UTF-8编码)

示例:
'1\n' → 停止
'2\n' → 前进
'3\n' → 后退
'4\n' → 左转
'5\n' → 右转
```

---

## 二、服务组件

### 2.1 Jetson后端服务

**服务名称**: `robot_server.py`  
**技术栈**: Flask + Flask-SocketIO + PySerial  
**运行位置**: `/home/nvidia/name_huanghongle3/kongzhi/`  

**文件结构:**
```
/home/nvidia/name_huanghongle3/kongzhi/
├── robot_server.py         # 主服务(HTTP+WebSocket)
├── stm32_controller.py     # STM32串口控制器
├── mock_stm32.py          # 模拟STM32(测试用)
├── config.py              # 配置文件
└── TECHNICAL_DOCUMENT.md  # 本文档
```

**启动方式:**
```bash
# 模拟模式(无硬件,测试用)
cd /home/nvidia/name_huanghongle3/kongzhi
python3 robot_server.py --mock

# 真实硬件模式(连接STM32)
python3 robot_server.py
```

**服务输出:**
```
============================================================
机器人Web控制服务器 - Jetson端
============================================================
[启动] 模拟模式已启用（假机器人）
[启动] 尝试连接STM32...
[MockSTM32] 模拟串口已打开: /dev/ttyACM3, 波特率 115200
[STM32] 模拟模式已启动
[启动] 模拟STM32连接成功
[启动] 服务器配置:
  - 运行模式: [模拟模式]
  - HTTP API: http://0.0.0.0:5000/api/control
  - WebSocket: ws://0.0.0.0:5000/
 * Running on http://192.168.0.2:5000
```

### 2.2 前端服务

**技术栈**: Vue 3 + 原生fetch  
**开发服务器**: `npm run serve`  
**访问地址**: `http://localhost:8080/#/ultrasonic`  

**启动命令:**
```bash
cd d:\Vue\shujudaping\data-dashboard
npm install    # 首次运行
npm run serve  # 启动开发服务器
```

---

## 三、命令映射表

### 3.1 控制指令

| 命令名称 | 串口数字 | duration=2 | duration=0 | 说明 |
|----------|----------|------------|------------|------|
| `stop` | 1 | 立即停止 | 立即停止 | 紧急停止 |
| `forward` | 2 | 前进2秒自停 | 一直前进 | 前进控制 |
| `backward` | 3 | 后退2秒自停 | 一直后退 | 后退控制 |
| `turn_left` | 4 | 左转2秒自停 | - | 左转控制 |
| `turn_right` | 5 | 右转2秒自停 | - | 右转控制 |
| `brushless_stop` | 6 | 无刷停止 | 无刷停止 | 无刷电机停 |
| `brushless_mid` | 7 | 无刷中速 | 无刷中速 | 无刷电机中速 |

### 3.2 按钮配置

```
┌─────────────────────────────┐
│        控制面板              │
├─────────────────────────────┤
│      [  前进  ]             │  duration=2 (2秒自动停)
│  [左转] [停止] [右转]       │
│      [  后退  ]             │
├─────────────────────────────┤
│ [一直前进] [一直后退]       │  duration=0 (持续)
├─────────────────────────────┤
│ [无刷停止] [无刷中速]       │
└─────────────────────────────┘
```

---

## 四、通信测试方式

### 4.1 测试准备

**1. 启动Jetson后端(终端1)**
```bash
ssh nvidia@192.168.0.2
cd /home/nvidia/name_huanghongle3/kongzhi
python3 robot_server.py --mock
```

**2. 监控日志(终端2)**
```bash
ssh nvidia@192.168.0.2
tail -f /tmp/mock_stm32.log
```

**3. 启动前端**
```bash
# 在前端开发机器上
cd d:\Vue\shujudaping\data-dashboard
npm run serve
# 浏览器访问 http://localhost:8080/#/ultrasonic
```

### 4.2 curl命令行测试

**测试步骤:**

```bash
# 1. 检查服务状态
curl http://192.168.0.2:5000/
# 预期返回: {"service": "Robot Control Server", ...}

# 2. 测试前进(2秒自动停)
curl -X POST http://192.168.0.2:5000/api/control \
  -H "Content-Type: application/json" \
  -d '{"command":"forward","duration":2}'
# 预期: Jetson日志显示 "收到命令: 2 | 前进"

# 3. 测试后退
curl -X POST http://192.168.0.2:5000/api/control \
  -H "Content-Type: application/json" \
  -d '{"command":"backward","duration":2}'
# 预期: Jetson日志显示 "收到命令: 3 | 后退"

# 4. 测试停止
curl -X POST http://192.168.0.2:5000/api/control \
  -H "Content-Type: application/json" \
  -d '{"command":"stop","duration":0}'
# 预期: Jetson日志显示 "收到命令: 1 | 停止"

# 5. 测试一直前进(需手动停)
curl -X POST http://192.168.0.2:5000/api/control \
  -H "Content-Type: application/json" \
  -d '{"command":"forward","duration":0}'
# 预期: 持续前进,不自动停止
```

### 4.3 前端页面测试

**测试步骤:**

1. **打开控制面板**
   - 访问 `http://localhost:8080`
   - 登录 (admin/admin123)
   - 点击"超声波雷达"菜单

2. **测试基础控制**
   - 点击"前进"按钮
   - 观察前端日志显示 "✅ 成功"
   - 观察Jetson终端显示 `[MockSTM32] 收到命令: 2 | 前进`
   - 等待2秒,观察自动停止

3. **测试持续控制**
   - 点击"一直前进"按钮
   - 观察Jetson日志显示命令
   - 点击"停止"按钮
   - 观察立即停止

4. **验证状态显示**
   - 连接成功时显示 "● 已连接"(绿色)
   - 连接失败时显示 "○ 未连接"(灰色)

### 4.4 预期输出示例

**Jetson日志输出:**
```
2026-03-04 19:14:02,193 - [MockSTM32] 收到命令: 2 | 前进 (FORWARD) | 原始数据: '2\n'
2026-03-04 19:14:02,194 - 192.168.0.126 - "POST /api/control HTTP/1.1" 200 -
2026-03-04 19:14:04,342 - [MockSTM32] 收到命令: 3 | 后退 (BACKWARD) | 原始数据: '3\n'
2026-03-04 19:14:04,344 - 192.168.0.126 - "POST /api/control HTTP/1.1" 200 -
```

**前端控制台输出:**
```
✅ 成功: [模拟]OK
命令: forward
原始数据: '2\n'
```

---

## 五、技术要点

### 5.1 关键设计决策

| 决策 | 方案 | 原因 |
|------|------|------|
| 串口协议 | 数字+`\n` | 与参考代码`com_with_stm.py`保持一致 |
| 通信方式 | HTTP POST | 简单可靠,前端fetch原生支持 |
| duration参数 | 0=持续,>0=自动停 | 兼顾点动和持续控制需求 |
| 模拟模式 | MockSTM32类 | 无硬件时可测试通信流程 |
| CORS配置 | 允许localhost:8080/8081 | 前端开发跨域需求 |

### 5.2 状态流转

```
前端点击按钮
    ↓
fetch POST {command, duration}
    ↓
Flask接收 → 验证命令 → 转换数字
    ↓
写入串口 (数字+'\n')
    ↓
STM32解析 → 执行动作
    ↓
返回JSON {status:"ok"}
    ↓
前端更新"已连接"状态
```

### 5.3 错误处理

| 错误场景 | 前端表现 | Jetson日志 |
|----------|----------|------------|
| 服务未启动 | "○ 未连接" | 无日志 |
| 命令错误 | "❌ 错误: 未知指令" | 打印错误 |
| 网络断开 | "❌ 连接失败" | 无新日志 |
| 队列满 | 丢弃指令 | "队列已满" |

---

## 六、切换真实硬件

### 6.1 前提条件
- STM32F103C8T6已上电
- USB转串口线已连接
- 确认设备节点: `ls /dev/ttyACM*` 显示 `/dev/ttyACM3`

### 6.2 切换步骤

```bash
# 1. 停止模拟服务
pkill -f robot_server.py

# 2. 检查硬件连接
ls -la /dev/ttyACM3

# 3. 启动真实模式(去掉--mock)
cd /home/nvidia/name_huanghongle3/kongzhi
python3 robot_server.py

# 4. 验证连接
curl http://192.168.0.2:5000/api/status
# 应显示: {"connected": true, "mock_mode": false, ...}
```

---

## 七、附录

### 7.1 文件清单

**Jetson后端:**
- `robot_server.py` - Flask主服务
- `stm32_controller.py` - 串口控制
- `mock_stm32.py` - 模拟器
- `config.py` - 配置

**前端:**
- `src/views/UltrasonicRadar.vue` - 控制面板
- `src/router/index.js` - 路由

### 7.2 相关文档

- `/home/nvidia/name_huanghongle3/kongzhi/TEST_GUIDE.md` - 详细测试指南
- `/home/nvidia/name_zhoushifei/STM32/com_with_stm.py` - 参考代码
- `/home/nvidia/name_zhoushifei/STM32/readme.txt` - STM32协议说明

### 7.3 联系方式

- **Jetson工程师**: 后端服务维护
- **前端工程师**: Vue控制面板开发
- **指导老师**: 架构设计建议

---

**文档结束**
