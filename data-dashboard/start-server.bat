@echo off
chcp 65001 >nul
echo ============================================
echo   智能清洁机器人数据可视化系统 - 启动脚本
echo ============================================
echo.
cd /d "%~dp0"

:: 1. 启动超声波 UDP + WebSocket 转发服务
echo [1/2] 启动超声波转发服务 (sensor_server.py)...
start "sensor_server" cmd /k "python sensor_server.py"

:: 2. 启动前端开发服务器（端口 8081）
echo [2/2] 启动前端 (npm run serve)...
start "frontend" cmd /k "npm run serve"

echo.
echo 服务已启动，请稍候打开浏览器访问: http://localhost:8081
pause
