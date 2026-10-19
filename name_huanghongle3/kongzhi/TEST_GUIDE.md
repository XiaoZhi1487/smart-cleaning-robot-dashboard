# 机器人控制测试操作文档

## 一、服务信息

| 项目 | 值 |
|------|-----|
| Jetson IP | `192.168.0.2` |
| HTTP 端口 | `5000` |
| WebSocket | `ws://192.168.0.2:5000/` |
| 运行模式 | 模拟模式 (`--mock`) |

---

## 二、HTTP API 接口

### 2.1 基础控制接口

```
POST http://192.168.0.2:5000/api/control
Content-Type: application/json
```

**请求参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `command` | string | 是 | 命令名称 |
| `duration` | number | 否 | 持续时间（秒），0=持续，>0=自动停止 |

**可用命令：**

| command | 数字 | 功能 | duration 建议 |
|---------|------|------|--------------|
| `stop` | 1 | 停止 | 0 |
| `forward` | 2 | 前进 | 2 或 0 |
| `backward` | 3 | 后退 | 2 或 0 |
| `turn_left` | 4 | 左转 | 2 或 0 |
| `turn_right` | 5 | 右转 | 2 或 0 |
| `brushless_stop` | 6 | 无刷停止 | 0 |
| `brushless_mid` | 7 | 无刷中速 | 0 |

**请求示例：**

```bash
# 前进2秒自动停
curl -X POST http://192.168.0.2:5000/api/control \
  -H "Content-Type: application/json" \
  -d '{"command":"forward","duration":2}'

# 一直前进（需手动停）
curl -X POST http://192.168.0.2:5000/api/control \
  -H "Content-Type: application/json" \
  -d '{"command":"forward","duration":0}'

# 立即停止
curl -X POST http://192.168.0.2:5000/api/control \
  -H "Content-Type: application/json" \
  -d '{"command":"stop","duration":0}'
```

**响应格式：**

```json
{
  "status": "ok",
  "success": true,
  "command": "forward",
  "duration": 2,
  "message": "[模拟]OK",
  "device_status": {
    "connected": true,
    "mock_mode": true,
    "current_command": "forward",
    "port": "/dev/ttyACM3"
  }
}
```

---

### 2.2 其他 HTTP 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `GET /` | GET | 服务状态检查 |
| `GET /api/status` | GET | 获取系统状态 |
| `POST /api/connect` | POST | 手动连接串口 |
| `POST /api/disconnect` | POST | 断开串口 |
| `POST /api/stop` | POST | 紧急停止 |

**示例：**
```bash
# 检查状态
curl http://192.168.0.2:5000/api/status

# 紧急停止
curl -X POST http://192.168.0.2:5000/api/stop
```

---

## 三、WebSocket 实时控制

### 3.1 连接地址
```
ws://192.168.0.2:5000/
```

### 3.2 支持的事件

**前端发送：**

| 事件名 | 数据 | 说明 |
|--------|------|------|
| `control` | `{"command":"forward"}` | 发送控制命令 |
| `stop` | `{}` | 紧急停止 |
| `heartbeat` | `{}` | 心跳（每100ms） |

**后端推送：**

| 事件名 | 说明 |
|--------|------|
| `connected` | 连接成功通知 |
| `control_ack` | 命令执行确认 |
| `status_update` | 状态更新推送 |
| `heartbeat_ack` | 心跳响应 |

### 3.3 前端示例

```javascript
const ws = new WebSocket('ws://192.168.0.2:5000/');

// 连接成功
ws.onopen = () => {
    console.log('已连接');
    
    // 发送控制命令
    ws.send(JSON.stringify({
        event: 'control',
        data: {command: 'forward'}
    }));
    
    // 启动心跳
    setInterval(() => {
        ws.send(JSON.stringify({event: 'heartbeat'}));
    }, 100);
};

// 接收消息
ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    console.log('收到:', msg);
};
```

---

## 四、测试步骤

### 4.1 HTTP 基础测试

1. **检查服务状态**
   ```bash
   curl http://192.168.0.2:5000/
   ```
   预期返回：`{"service": "Robot Control Server", ...}`

2. **测试前进（2秒自动停）**
   ```bash
   curl -X POST http://192.168.0.2:5000/api/control \
     -H "Content-Type: application/json" \
     -d '{"command":"forward","duration":2}'
   ```
   预期返回：`{"status":"ok","command":"forward",...}`
   Jetson 日志应显示：`[MockSTM32] 收到命令: 2 | 前进`

3. **测试立即停止**
   ```bash
   curl -X POST http://192.168.0.2:5000/api/control \
     -H "Content-Type: application/json" \
     -d '{"command":"stop","duration":0}'
   ```
   预期返回：`{"status":"ok","command":"stop",...}`
   Jetson 日志应显示：`[MockSTM32] 收到命令: 1 | 停止`

### 4.2 前端按钮测试

| 步骤 | 操作 | 预期结果 |
|------|------|---------|
| 1 | 点击"前进"按钮 | Jetson 日志显示 `收到命令: 2`，2秒后自动停止 |
| 2 | 点击"后退"按钮 | Jetson 日志显示 `收到命令: 3`，2秒后自动停止 |
| 3 | 点击"左转"按钮 | Jetson 日志显示 `收到命令: 4`，2秒后自动停止 |
| 4 | 点击"右转"按钮 | Jetson 日志显示 `收到命令: 5`，2秒后自动停止 |
| 5 | 点击"一直前进"按钮 | Jetson 日志显示 `收到命令: 2`，持续不停止 |
| 6 | 点击"停止"按钮 | Jetson 日志显示 `收到命令: 1`，立即停止 |

### 4.3 WebSocket 测试（可选）

1. **连接 WebSocket**
   - 地址：`ws://192.168.0.2:5000/`
   - 预期：连接成功，收到 `connected` 事件

2. **发送控制命令**
   - 发送：`{"event":"control","data":{"command":"forward"}}`
   - 预期：Jetson 日志显示收到命令，前端收到 `control_ack`

3. **心跳测试**
   - 每 100ms 发送 `{"event":"heartbeat"}`
   - 预期：收到 `heartbeat_ack`，500ms 无心跳自动停止

---

## 五、日志查看

### 5.1 在 Jetson 上查看

```bash
# 查看 MockSTM32 命令日志
tail -f /tmp/mock_stm32.log

# 查看 HTTP 访问日志
tail -f /tmp/robot_server.log

# 查看所有日志
tail -f /tmp/mock_stm32.log /tmp/robot_server.log
```

### 5.2 日志格式说明

**MockSTM32 日志：**
```
2026-03-04 19:12:25,465 - [MockSTM32] 模拟串口已打开
2026-03-04 19:12:49,840 - [MockSTM32] 收到命令: 2 | 前进 (FORWARD) | 原始数据: '2\n'
```

**HTTP 访问日志：**
```
192.168.0.126 - - [04/Mar/2026 18:47:52] "POST /api/control HTTP/1.1" 200 -
```

---

## 六、故障排查

| 问题 | 可能原因 | 解决方法 |
|------|---------|---------|
| 连接被拒绝 | 服务未启动 | `ps aux \| grep robot_server` 检查 |
| 跨域错误 | CORS 配置问题 | 确认后端已设置 `CORS(app)` |
| 405 Method Not Allowed | 用了 GET 而非 POST | 改为 `method: 'POST'` |
| 日志无输出 | 服务异常 | 重启服务 `pkill robot_server.py && python3 robot_server.py --mock` |
| 命令无响应 | 队列满或断开 | 检查 `device_status.connected` 字段 |

---

## 七、切换到真实硬件

当机器人充电完成后：

```bash
# 1. 停止模拟服务
pkill -f robot_server.py

# 2. 确认 STM32 接入
ls /dev/ttyACM*  # 应该能看到 /dev/ttyACM3

# 3. 启动真实模式（去掉 --mock）
cd /home/nvidia/name_huanghongle3/kongzhi
python3 robot_server.py

# 4. 检查连接状态
curl http://192.168.0.2:5000/api/status
```

---

**测试日期：** 2026-03-04  
**文档版本：** v1.0  
**Jetson 工程师：** 后端服务负责人  
**前端工程师：** 请按此文档进行测试
