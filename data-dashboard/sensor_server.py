#!/usr/bin/env python3
"""
超声波传感器UDP接收 + WebSocket转发服务器
同时支持UDP接收传感器数据，并通过WebSocket转发给Web页面
"""

import socket
import json
import asyncio
import websockets
from datetime import datetime
from collections import deque

# 配置
UDP_IP = "0.0.0.0"  # 监听所有接口
UDP_PORT = 6667
WS_PORT = 6668       # WebSocket端口
WS_HOST = "0.0.0.0"  # WebSocket绑定到所有接口

# 存储最新的传感器数据
latest_sensor_data = None
connected_clients = set()


def process_ultrasonic_data(data):
    """处理超声波传感器数据：8字节数据（4个传感器，每个2字节）转换为厘米"""
    try:
        # 确保数据长度至少为8字节
        if len(data) < 8:
            return None, "数据长度不足8字节"

        sensors = []
        for i in range(4):
            # 提取每个传感器的2字节数据
            sensor_data = data[i*2:(i+1)*2]
            hex_data = sensor_data.hex().upper()
            mm_value = int(hex_data, 16)
            cm_value = mm_value / 10.0
            sensors.append({
                'sensor_id': i + 1,
                'hex': hex_data,
                'mm': mm_value,
                'cm': cm_value
            })

        return sensors, None

    except (ValueError, IndexError) as e:
        return None, f"数据解析错误: {e}"


def format_output(sensors, client_info):
    """格式化输出超声波传感器数据"""
    output = []
    output.append("=" * 50)
    output.append(f"📡 超声波传感器数据 (4个传感器) - {client_info}")
    output.append("-" * 50)
    for sensor in sensors:
        output.append(f"传感器 {sensor['sensor_id']}:")
        output.append(f"  原始十六进制: {sensor['hex']}")
        output.append(f"  距离 (毫米): {sensor['mm']}")
        output.append(f"  距离 (厘米): {sensor['cm']:.1f}")
    output.append("=" * 50)
    return "\n".join(output)


async def broadcast_to_clients(data):
    """广播数据到所有连接的WebSocket客户端"""
    if not connected_clients:
        return
    
    message = json.dumps(data)
    disconnected = set()
    
    for client in connected_clients:
        try:
            await client.send(message)
        except websockets.exceptions.ConnectionClosed:
            disconnected.add(client)
        except Exception as e:
            print(f"发送数据到客户端失败: {e}")
            disconnected.add(client)
    
    # 移除断开的客户端
    connected_clients -= disconnected


async def udp_server():
    """UDP服务器 - 接收传感器数据"""
    global latest_sensor_data
    
    # 创建UDP套接字
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    udp_socket.bind((UDP_IP, UDP_PORT))
    udp_socket.setblocking(False)
    
    print(f"\n🔊 超声波传感器UDP服务器已启动")
    print(f"监听地址: {UDP_IP}:{UDP_PORT}")
    print(f"WebSocket服务器端口: {WS_PORT}")
    print("按 Ctrl+C 停止服务器...\n")
    
    loop = asyncio.get_event_loop()
    
    while True:
        try:
            # 非阻塞接收数据
            data, client_address = await loop.run_in_executor(
                None, udp_socket.recvfrom, 1024
            )
            client_info = f"{client_address[0]}:{client_address[1]}"
            
            # 处理超声波传感器数据
            sensors, error = process_ultrasonic_data(data)
            
            if sensors is not None:
                # 格式化输出到控制台
                output = format_output(sensors, client_info)
                print(output)
                
                # 准备WebSocket数据
                sensor_data = {
                    'timestamp': datetime.now().isoformat(),
                    'client': client_info,
                    'sensors': sensors
                }
                latest_sensor_data = sensor_data
                
                # 广播到所有WebSocket客户端
                await broadcast_to_clients(sensor_data)
                
                # 发送UDP响应
                sensor1_cm = sensors[0]['cm']
                response = f"✅ 已接收4个传感器数据，传感器1距离: {sensor1_cm:.1f}厘米"
                udp_socket.sendto(response.encode(), client_address)
                print(f"📤 已向 {client_info} 发送响应\n")
            else:
                # 处理错误情况
                print(f"❌ 从 {client_info} 收到无效数据")
                print(f"   数据长度: {len(data)} 字节")
                print(f"   原始数据: {data.hex().upper()}")
                print(f"   错误信息: {error}")
                
                response = f"❌ 无效数据格式，需要8字节十六进制数据（4个传感器）"
                udp_socket.sendto(response.encode(), client_address)
                print(f"📤 已向 {client_info} 发送错误响应\n")
                
        except BlockingIOError:
            await asyncio.sleep(0.001)
        except Exception as e:
            print(f"UDP服务器错误: {e}")
            await asyncio.sleep(0.1)


async def websocket_handler(websocket, path):
    """WebSocket连接处理器"""
    print(f"🔌 WebSocket客户端已连接: {websocket.remote_address}")
    connected_clients.add(websocket)
    
    try:
        # 发送当前最新数据（如果有）
        if latest_sensor_data:
            await websocket.send(json.dumps(latest_sensor_data))
        
        # 保持连接，等待客户端断开
        async for message in websocket:
            # 可以处理客户端发送的命令
            try:
                cmd = json.loads(message)
                print(f"收到客户端命令: {cmd}")
            except:
                pass
                
    except websockets.exceptions.ConnectionClosed:
        print(f"🔌 WebSocket客户端已断开: {websocket.remote_address}")
    finally:
        connected_clients.discard(websocket)


async def main():
    """主函数 - 启动UDP和WebSocket服务器"""
    # 启动WebSocket服务器
    ws_server = await websockets.serve(
        websocket_handler, 
        WS_HOST,  # 绑定到指定IP
        WS_PORT,
        ping_interval=20,
        ping_timeout=10
    )
    
    print(f"🌐 WebSocket服务器已启动: ws://{WS_HOST}:{WS_PORT}")
    
    # 启动UDP服务器
    udp_task = asyncio.create_task(udp_server())
    
    try:
        # 同时运行两个服务器
        await asyncio.gather(udp_task, ws_server.wait_closed())
    except KeyboardInterrupt:
        print("\n🛑 服务器正在关闭...")
    finally:
        ws_server.close()
        await ws_server.wait_closed()
        print("🔌 服务器已关闭")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 程序已终止")
