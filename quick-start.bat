@echo off
chcp 65001 >nul
echo ===================================
echo BossJy-Cn 快速启动脚本
echo ===================================

:: 检查Docker是否运行
echo [1/3] 检查Docker状态...
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: Docker未运行，请启动Docker Desktop
    pause
    exit /b 1
)
echo ✓ Docker正在运行

:: 启动服务
echo [2/3] 启动所有服务...
docker-compose -f docker-compose.frontend.yml start
if %errorlevel% neq 0 (
    echo 错误: 服务启动失败，尝试完整部署...
    call deploy-all.bat
    exit /b 1
)
echo ✓ 服务启动成功

:: 显示访问信息
echo [3/3] 显示访问信息...
echo.
echo ===================================
echo BossJy-Cn 系统已启动！
echo.
echo 访问地址:
echo - 前端应用: http://localhost:3000
echo - 后端API: http://localhost:18001/docs
echo.
echo 管理命令:
echo - 查看日志: docker-compose -f docker-compose.frontend.yml logs -f
echo - 停止系统: docker-compose -f docker-compose.frontend.yml stop
echo ===================================
echo.

:: 询问是否打开浏览器
set /p open_browser="是否打开浏览器访问应用？(y/n): "
if /i "%open_browser%"=="y" (
    start http://localhost:3000
)

pause