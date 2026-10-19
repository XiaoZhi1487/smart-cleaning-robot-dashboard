#!/bin/bash
# 快速启动脚本（纯 Bash，无 Python 依赖）
# 一键启动相机 + HTTP + ROS Bridge + 超声波

set -e

echo "=============================================="
echo "Jetson 服务快速启动脚本"
echo "=============================================="

# 颜色定义
GREEN='\033[92m'
RED='\033[91m'
YELLOW='\033[93m'
BLUE='\033[94m'
END='\033[0m'

log() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] $1${END}"
}

ok() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓ $1${END}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚠ $1${END}"
}

err() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ✗ $1${END}"
}

# 停止旧进程
echo ""
log "步骤 1/5: 清理旧进程..."

pkill -9 -f "gemini_330_series" 2>/dev/null || true
pkill -9 -f "component_container" 2>/dev/null || true
pkill -9 -f "camera_http_node" 2>/dev/null || true
pkill -9 -f "rosbridge_websocket" 2>/dev/null || true
pkill -9 -f "wave_length_node" 2>/dev/null || true

sleep 2
ok "旧进程已清理"

# 检查端口占用
echo ""
log "步骤 2/5: 检查端口占用..."

if ss -tlnp 2>/dev/null | grep -q ":8082"; then
    warn "端口 8082 仍被占用，尝试释放..."
    fuser -k 8082/tcp 2>/dev/null || true
fi

if ss -tlnp 2>/dev/null | grep -q ":9090"; then
    warn "端口 9090 仍被占用，尝试释放..."
    fuser -k 9090/tcp 2>/dev/null || true
fi

ok "端口检查完成"

# Source ROS2
echo ""
log "步骤 3/5: 加载 ROS2 环境..."
source /opt/ros/humble/setup.bash
ok "ROS2 环境已加载"

# 启动相机
echo ""
log "步骤 4/5: 启动相机..."
ros2 launch orbbec_camera gemini_330_series.launch.py \
    color_width:=640 \
    color_height:=360 \
    color_fps:=10 \
    enable_depth:=false \
    enable_point_cloud:=false \
    > /tmp/camera.log 2>&1 &

CAMERA_PID=$!
log "相机 PID: $CAMERA_PID"
log "等待相机初始化 (15秒)..."

for i in {1..15}; do
    echo -n "."
    sleep 1
done
echo ""

# 检查相机话题
if ros2 topic list 2>/dev/null | grep -q "/camera/color/image_raw"; then
    ok "相机话题已出现"
else
    err "相机话题未出现，请检查日志: tail -f /tmp/camera.log"
    exit 1
fi

# 等待相机稳定输出图像
log "等待相机稳定输出 (5秒)..."
sleep 5

# 验证相机数据流
if timeout 3 ros2 topic hz /camera/color/image_raw --window 3 2>/dev/null | grep -q "average rate"; then
    ok "相机数据流正常"
else
    warn "相机数据流可能不稳定，继续启动..."
fi

# 启动 HTTP 服务器
echo ""
log "步骤 5/5: 启动其他服务..."

# HTTP 服务器（直接使用 Python 运行，绕过 entry_points 问题）
cd /home/nvidia/name_huanghongle3/camera_http_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
python3 src/camera_http/camera_http/camera_http_node.py > /tmp/http_server.log 2>&1 &
HTTP_PID=$!
log "HTTP 服务器 PID: $HTTP_PID"

# 启动 ROS Bridge
ros2 launch rosbridge_server rosbridge_websocket_launch.xml > /tmp/rosbridge.log 2>&1 &
ROS_PID=$!
log "ROS Bridge PID: $ROS_PID"

# 启动超声波（可选，如需禁用请注释掉）
cd /home/nvidia/name_ranhongmei/ws
source /opt/ros/humble/setup.bash
source install/setup.bash
# 使用 python 直接运行，避免 entry_points 问题
python3 /home/nvidia/name_ranhongmei/ws/install/fist_demo_uart/lib/fist_demo_uart/wave_length_node > /tmp/ultrasonic.log 2>&1 &
ULTRA_PID=$!
log "超声波 PID: $ULTRA_PID"

# 等待服务稳定
sleep 5

# 检查 HTTP 是否真的启动了
if ! ss -tlnp 2>/dev/null | grep -q ":8082"; then
    warn "HTTP 服务器端口未监听，尝试重新启动..."
    cd /home/nvidia/name_huanghongle3/camera_http_ws
    source /opt/ros/humble/setup.bash
    source install/setup.bash
    python3 src/camera_http/camera_http/camera_http_node.py > /tmp/http_server.log 2>&1 &
    HTTP_PID=$!
    sleep 3
fi

# 最终检查
echo ""
echo "=============================================="
echo "启动完成！"
echo "=============================================="

# 状态检查
echo ""
echo "服务状态:"

# 检查相机
if ps -p $CAMERA_PID > /dev/null 2>&1; then
    ok "相机 (PID: $CAMERA_PID)"
else
    err "相机已退出"
fi

# 检查 HTTP
if ps -p $HTTP_PID > /dev/null 2>&1; then
    ok "HTTP 服务器 (PID: $HTTP_PID)"
else
    err "HTTP 服务器已退出"
fi

# 检查 ROS
if ps -p $ROS_PID > /dev/null 2>&1; then
    ok "ROS Bridge (PID: $ROS_PID)"
else
    err "ROS Bridge 已退出"
fi

# 检查超声波
if ps -p $ULTRA_PID > /dev/null 2>&1; then
    ok "超声波 (PID: $ULTRA_PID)"
else
    warn "超声波已退出（可选服务）"
fi

echo ""
echo "访问地址:"
echo "  📹 视频流: http://192.168.0.2:8082/camera"
echo "  🔌 ROS:    ws://192.168.0.2:9090"
echo "  📡 超声波: /wave_length (ROS Topic)"

echo ""
echo "日志文件:"
echo "  /tmp/camera.log"
echo "  /tmp/http_server.log"
echo "  /tmp/rosbridge.log"
echo "  /tmp/ultrasonic.log"

echo ""
echo "按 Ctrl+C 停止所有服务"
echo "或运行: python3 /home/nvidia/name_huanghongle3/stop_all_services.py"
echo "=============================================="

# 等待中断
trap "echo ''; echo '正在停止服务...'; kill $CAMERA_PID $HTTP_PID $ROS_PID $ULTRA_PID 2>/dev/null || true; exit" SIGINT SIGTERM
wait
