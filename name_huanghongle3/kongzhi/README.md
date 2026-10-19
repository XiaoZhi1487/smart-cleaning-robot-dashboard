# 机器人Web控制服务器 - Jetson端

## 文件结构
```
/home/nvidia/name_huanghongle3/kongzhi/
├── config.py           # 配置文件
├── stm32_controller.py # STM32串口控制器
├── robot_server.py     # 主服务 (HTTP + WebSocket)
├── requirements.txt    # 依赖列表
└── README.md          # 说明文档
```

## 安装依赖
```bash
cd /home/nvidia/name_huanghongle3/kongzhi
pip3 install -r requirements.txt
```

## 启动服务
```bash
python3 robot_server.py
```

## 前端接口

### HTTP API
- `POST /api/control` - 控制命令
  ```json
  {"command": "forward", "duration": 0}
  ```

### WebSocket
- 地址: `ws://<jetson_ip>:5000/`
- 事件: `control`, `stop`, `heartbeat`

## 命令列表
- `stop` - 停止
- `forward` - 前进
- `backward` - 后退
- `turn_left` - 左转
- `turn_right` - 右转
- `brushless_stop` - 无刷停止
- `brushless_mid` - 无刷中速
