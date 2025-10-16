@echo off
echo ========================================
echo BossJy完整部署脚本
echo ========================================
echo.

echo [1/5] 检查Docker状态...
docker version >nul 2>&1
if errorlevel 1 (
    echo 错误: Docker未运行，请先启动Docker Desktop
    pause
    exit /b 1
)

echo.
echo [2/5] 停止旧容器...
docker-compose down

echo.
echo [3/5] 启动数据库服务...
docker-compose up -d postgres redis
timeout /t 10

echo.
echo [4/5] 启动应用服务...
docker-compose up -d fastapi go-api bots vue-frontend

echo.
echo [5/5] 启动Nginx...
docker-compose up -d nginx

echo.
echo ========================================
echo 部署完成！
echo ========================================
echo.
echo 服务访问地址：
echo - 前端: http://localhost:3000
echo - API文档: http://localhost:18001/docs
echo - Go API: http://localhost:8080/api/health
echo.
echo 查看服务状态: docker-compose ps
echo 查看日志: docker-compose logs -f
echo.
pause
