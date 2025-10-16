@echo off
chcp 65001 >nul
echo ===================================
echo BossJy-Cn 系统健康检查
echo ===================================

:: 检查前端服务
echo [1/5] 检查前端服务...
curl -s http://localhost:3000 >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 前端服务未运行 (端口3000)
) else (
    echo ✅ 前端服务正常
)

:: 检查后端API
echo [2/5] 检查后端API...
curl -s http://localhost:18001/health >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 后端API服务未运行 (端口18001)
) else (
    echo ✅ 后端API服务正常
)

:: 检查数据库
echo [3/5] 检查数据库...
docker exec bossjy-postgres pg_isready -U jytian >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ PostgreSQL数据库未就绪
) else (
    echo ✅ PostgreSQL数据库正常
)

:: 检查Redis
echo [4/5] 检查Redis...
docker exec bossjy-redis redis-cli -a ji394su3!! ping >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Redis服务未就绪
) else (
    echo ✅ Redis服务正常
)

:: 显示容器状态
echo [5/5] 容器状态
docker-compose -f docker-compose.frontend.yml ps

echo.
echo ===================================
echo 健康检查完成
echo ===================================

pause