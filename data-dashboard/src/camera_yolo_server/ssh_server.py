#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web 交互式 SSH 控制台桥接服务
================================
为监控平台前端提供「交互式 SSH 终端」能力：
    - 前端(8081) --WebSocket(8084)--> 本服务 --paramiko SSH(22)--> 机器人设备
前置依赖：
    pip install websockets paramiko        (paramiko 可能已随 camera_yolo_server 安装)

启动：
    python ssh_server.py
    # 或由 data-dashboard/serve-all.js 的 npm run serve 一键并行拉起

协议(WebSocket 文本帧, JSON)：
    客户端 -> 服务端
        {"type":"connect", "host":..., "port":..., "username":..., "password":...}
        {"type":"input",   "data":"<base64 终端输入字节>"}
        {"type":"resize",  "cols":<int>, "rows":<int>}
        {"type":"close"}
    服务端 -> 客户端
        {"type":"ready",  "msg":"SSH 已连接"}
        {"type":"output", "data":"<base64 设备输出字节>"}
        {"type":"error",  "msg":"连接失败原因"}
        {"type":"exit",   "code":<int 或 null>}
"""
import argparse
import asyncio
import base64
import json
import select
import threading
import time

try:
    import paramiko
except Exception:  # noqa: BLE001
    paramiko = None

import websockets


HOST = "0.0.0.0"
PORT = 8084
# 最大并发 SSH 会话数,防止设备/本机资源被耗尽
MAX_SESSIONS = 10
_WS_ORIGINS = [
    "http://localhost:8081", "http://127.0.0.1:8081", "http://localhost:8080", "http://127.0.0.1:8080",
]

_session_count = 0
_session_lock = threading.Lock()


def _b64(bin_bytes: bytes) -> str:
    """字节 -> base64 字符串(ascii),保证任意字节无损传输"""
    return base64.b64encode(bin_bytes).decode("ascii")


def _unb64(s: str) -> bytes:
    """base64 字符串 -> 字节"""
    return base64.b64decode(s)


class SshSession:
    """一个 paramiko 交互式 PTY shell,通过 WebSocket 双向转发输入/输出"""

    def __init__(self, ws, loop, host, port, username, password):
        self.ws = ws
        self.loop = loop
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = None
        self.channel = None
        self.reader = None
        self.closed = False

    def open(self):
        """建立 SSH 并启动读取线程;失败抛出异常由上层转成 error 帧"""
        if paramiko is None:
            raise RuntimeError("paramiko 未安装,无法建立 SSH")
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        # 显著超时,前端可在连不上时快速得到反馈
        self.client.connect(
            hostname=self.host, port=self.port, username=self.username,
            password=self.password, timeout=8, banner_timeout=8, auth_timeout=8,
        )
        # 交互式终端必须有 PTY(invoke_shell),exec_command 无法承载 vim/top 等
        self.channel = self.client.invoke_shell(term="xterm", width=80, height=24)
        self.channel.settimeout(0.0)  # 非阻塞,配合 select 使用

        # 后台线程:读设备输出并通过 loop 转发给前端
        self.reader = threading.Thread(target=self._read_loop, daemon=True)
        self.reader.start()

    def write(self, data: bytes):
        try:
            if self.channel is not None and not self.channel.closed:
                self.channel.send(data)
        except Exception:  # noqa: BLE001
            pass

    def resize(self, cols: int, rows: int):
        try:
            if self.channel is not None and not self.channel.closed:
                self.channel.resize_pty(width=max(cols, 2), height=max(rows, 2))
        except Exception:  # noqa: BLE001
            pass

    def _read_loop(self):
        try:
            while not self.closed:
                if self.channel is None or self.channel.closed:
                    break
                if self.channel.exit_status_ready():
                    break
                # select 超时 0.2s,便于及时感知关闭
                r, _, _ = select.select([self.channel], [], [], 0.2)
                if self.channel in r:
                    data = self.channel.recv(4096)
                    if not data:
                        break
                    self._send_async({"type": "output", "data": _b64(data)})
        except Exception:  # noqa: BLE001
            pass
        finally:
            if not self.closed:
                self._send_async({"type": "exit", "code": self._exit_code()})
            self.close()

    def _exit_code(self):
        try:
            return self.channel.recv_exit_status() if self.channel else None
        except Exception:  # noqa: BLE001
            return None

    def _send_async(self, frame: dict):
        """从读取线程安全地把一帧 JSON 交由 ws 发送"""
        try:
            fut = asyncio.run_coroutine_threadsafe(self._send(frame), self.loop)
            fut.result(timeout=0.5)
        except Exception:  # noqa: BLE001
            pass

    async def _send(self, frame: dict):
        try:
            await self.ws.send(json.dumps(frame))
        except Exception:  # noqa: BLE001
            pass

    async def shed(self):
        """退出前向前端补发一条断开帧"""
        if not self.closed:
            try:
                await self.ws.send(json.dumps({"type": "exit", "code": None}))
            except Exception:  # noqa: BLE001
                pass

    def close(self):
        """严格清理 channel/client/线程计数,避免连接泄漏"""
        if self.closed:
            return
        self.closed = True
        try:
            if self.channel is not None:
                self.channel.close()
        except Exception:  # noqa: BLE001
            pass
        try:
            if self.client is not None:
                self.client.close()
        except Exception:  # noqa: BLE001
            pass
        global _session_count
        with _session_lock:
            _session_count = max(0, _session_count - 1)


def _acquire_slot() -> bool:
    global _session_count
    with _session_lock:
        if _session_count >= MAX_SESSIONS:
            return False
        _session_count += 1
        return True


async def _ws_handler(websocket):
    """每个 WebSocket 连接的处理协程"""
    session = None
    loop = asyncio.get_running_loop()
    try:
        # —— 1. 等一条 connect 帧,拿到 SSH 凭据 ——
        frame = None
        try:
            frame = json.loads(await websocket.recv())
        except (json.JSONDecodeError, UnicodeDecodeError):  # noqa: BLE001
            pass
        if not frame or frame.get("type") != "connect":
            await websocket.send(json.dumps({"type": "error", "msg": "缺少 connect 帧"}))
            return

        host = str(frame.get("host") or "192.168.0.2")
        port = int(frame.get("port") or 22)
        username = str(frame.get("username") or "nvidia")
        password = str(frame.get("password") or "")

        if not _acquire_slot():
            await websocket.send(json.dumps({"type": "error", "msg": "并发会话数已达上限,请稍后再试"}))
            return

        session = SshSession(websocket, loop, host, port, username, password)
        try:
            session.open()
        except Exception as e:  # noqa: BLE001  认证失败/超时/主机不可达
            await websocket.send(json.dumps({"type": "error", "msg": f"SSH 连接失败: {e}"}))
            if session:
                session.close()
            return

        await websocket.send(json.dumps({"type": "ready", "msg": f"已连接 {username}@{host}:{port}"}))

        # —— 2. 转发循环:input/resize/close ——
        async for raw in websocket:
            if raw is None:
                continue
            try:
                data = raw if isinstance(raw, bytes) else raw.encode("utf-8", "replace")
                f = json.loads(data.decode("utf-8", "replace"))
            except (json.JSONDecodeError, UnicodeDecodeError):  # noqa: BLE001
                continue
            t = f.get("type")
            if t == "input":
                try:
                    session.write(_unb64(str(f.get("data", ""))))
                except Exception:  # noqa: BLE001
                    pass
            elif t == "resize":
                session.resize(int(f.get("cols") or 80), int(f.get("rows") or 24))
            elif t == "close":
                break
    except websockets.exceptions.ConnectionClosed:  # 浏览器直接关闭连接是正常路径
        pass
    except Exception as e:  # noqa: BLE001
        try:
            await websocket.send(json.dumps({"type": "error", "msg": str(e)}))
        except Exception:  # noqa: BLE001
            pass
    finally:
        if session:
            await session.shed()
            session.close()


def _parse_args():
    p = argparse.ArgumentParser(description="Web 交互式 SSH 桥接服务")
    p.add_argument("--host", default=HOST)
    p.add_argument("--port", type=int, default=PORT)
    return p.parse_args()


def main():
    args = _parse_args()
    if paramiko is None:
        print("[ssh] [ERROR] 未检测到 paramiko,请先安装: pip install paramiko")
        return
    try:
        import websockets  # noqa: F401
    except Exception:  # noqa: BLE001
        print("[ssh] [ERROR] 未检测到 websockets,请先安装: pip install websockets")
        return

    print(f"[ssh] 交互式 SSH 服务启动: ws://localhost:{args.port}")
    print(f"[ssh] 前端在端口 8081 访问 '控制台' 页面连接")
    # websockets>=12 要求 serve 在运行中的事件循环内构建,故使用 asyncio.run 的标准模式
    asyncio.run(_serve_forever(_ws_handler, args.host, args.port))


async def _serve_forever(handler, host, port):
    async with websockets.serve(handler, host, port, origins=None):
        await asyncio.Future()  # 挂起直到进程终止(等价于 run_forever)


if __name__ == "__main__":
    main()