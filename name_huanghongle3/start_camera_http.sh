#!/bin/bash
# Start Camera (Color Only, 10fps, 640x360) + HTTP MJPEG Server
# Usage: ./start_camera_http.sh

set -e

echo "============================================"
echo "Starting Color Camera + HTTP MJPEG Server"
echo "============================================"

# Source ROS2
source /opt/ros/humble/setup.bash

# Check if camera is already running
if ! ros2 topic list | grep -q "/camera/color/image_raw"; then
    echo "[1/3] Starting Orbbec Camera (Color Only, 10fps, 640x360)..."
    
    ros2 launch orbbec_camera gemini_330_series.launch.py \
        enable_color:=true \
        enable_depth:=false \
        enable_point_cloud:=false \
        color_fps:=10 \
        color_width:=640 \
        color_height:=360 \
        color_format:=MJPG \
        enable_left_ir:=false \
        enable_right_ir:=false \
        enable_accel:=false \
        enable_gyro:=false \
        > /tmp/camera.log 2>&1 &
    
    CAMERA_PID=$!
    echo "Camera PID: $CAMERA_PID"
    
    # Wait for camera to start
    echo "Waiting for camera to initialize..."
    for i in {1..15}; do
        if ros2 topic list | grep -q "/camera/color/image_raw"; then
            echo "✓ Camera is ready!"
            break
        fi
        sleep 1
        echo -n "."
    done
    
    if ! ros2 topic list | grep -q "/camera/color/image_raw"; then
        echo "✗ Camera failed to start!"
        echo "Check log: tail -50 /tmp/camera.log"
        exit 1
    fi
else
    echo "[1/3] Camera already running"
fi

# Build and source HTTP server workspace
echo "[2/3] Building HTTP Server..."
cd /home/nvidia/name_huanghongle3/camera_http_ws

# Build if not built
if [ ! -d "install" ]; then
    colcon build --packages-select camera_http 2>&1 | tail -10
fi

source install/setup.bash

# Start HTTP Server
# 用 python3 直接运行源码，绕过 ament 可执行索引缺失导致的 ros2 run "No executable found"
echo "[3/3] Starting HTTP MJPEG Server..."
python3 src/camera_http/camera_http/camera_http_node.py \
    > /tmp/http_server.log 2>&1 &

HTTP_PID=$!
echo "HTTP Server PID: $HTTP_PID"

# Wait for server to start
sleep 2

echo ""
echo "============================================"
echo "✓ All services started!"
echo "============================================"
echo ""
echo "Camera Stream URL:"
echo "  http://192.168.0.2:8080/camera"
echo ""
echo "Frontend usage:"
echo '  <img src="http://192.168.0.2:8080/camera" alt="Camera" />'
echo ""
echo "Logs:"
echo "  Camera:  tail -f /tmp/camera.log"
echo "  HTTP:    tail -f /tmp/http_server.log"
echo ""
echo "Press Ctrl+C to stop"
echo "============================================"

# Handle cleanup
cleanup() {
    echo ""
    echo "Stopping services..."
    kill $HTTP_PID $CAMERA_PID 2>/dev/null || true
    echo "Stopped."
    exit
}
trap cleanup SIGINT SIGTERM

# Keep script running
wait
