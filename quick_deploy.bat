@echo off
chcp 65001 >nul
echo ========================================
echo BossJy-Pro 快速部署脚本
echo ========================================
echo.

echo [1/5] 停止现有服务...
docker-compose down
if errorlevel 1 (
    echo 警告: 停止服务时出现问题，继续...
)
echo.

echo [2/5] 构建 Docker 镜像...
docker-compose build
if errorlevel 1 (
    echo 错误: Docker 镜像构建失败
    pause
    exit /b 1
)
echo.

echo [3/5] 启动所有服务...
docker-compose up -d
if errorlevel 1 (
    echo 错误: 服务启动失败
    pause
    exit /b 1
)
echo.

echo [4/5] 等待服务启动...
timeout /t 10 /nobreak >nul
echo.

echo [5/5] 检查服务健康状态...
python health_check.py
echo.

echo ========================================
echo 部署完成！
echo ========================================
echo.
echo 可用服务:
echo   - FastAPI:       http://localhost:18001
echo   - API 文档:      http://localhost:18001/docs
echo   - API 健康检查:   http://localhost:18001/api/health
echo   - Vue 前端:      http://localhost:3000
echo   - Go API:        http://localhost:8080
echo   - Bots 服务:     http://localhost:9001
echo.
echo 数据库:
echo   - PostgreSQL:    localhost:15432
echo   - Redis:         localhost:16379
echo.
echo 查看日志: docker-compose logs -f [service-name]
echo 停止服务: docker-compose down
echo.

pause
