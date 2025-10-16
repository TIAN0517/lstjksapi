@echo off
echo ========================================
echo BossJy Docker修复脚本
echo ========================================
echo.

echo [1/4] 停止所有Docker容器...
docker-compose down -v 2>nul
docker stop $(docker ps -aq) 2>nul
docker rm $(docker ps -aq) 2>nul

echo.
echo [2/4] 关闭WSL和Docker...
wsl --shutdown
timeout /t 5

echo.
echo [3/4] 清理Docker系统...
docker system prune -a -f --volumes

echo.
echo [4/4] 请手动重启Docker Desktop，然后运行：
echo    docker-compose -f docker-compose.complete.yml up -d
echo.
echo 按任意键退出...
pause
