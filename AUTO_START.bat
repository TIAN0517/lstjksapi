@echo off
chcp 65001 >nul
echo ========================================
echo BossJy系统自动启动脚本
echo ========================================
echo.

echo 📊 Docker镜像状态检查...
docker images | findstr "bossjy"
echo.

echo ⚠️ 重要提示：
echo 如果您刚刚重启了Docker Desktop，请确认：
echo   1. Docker Desktop已完全启动（鲸鱼图标稳定）
echo   2. 已经等待至少30秒
echo.

echo 按任意键开始启动服务...
pause >nul
echo.

echo ========================================
echo 第1步：清理旧容器和网络
echo ========================================
docker-compose down -v 2>nul
echo 完成！
echo.

echo ========================================
echo 第2步：启动数据库服务
echo ========================================
echo 正在启动 PostgreSQL 和 Redis...
docker-compose up -d postgres redis
if errorlevel 1 (
    echo.
    echo ❌ 错误：数据库服务启动失败！
    echo.
    echo 这通常是Docker overlay问题。请：
    echo 1. 完全退出Docker Desktop（右键图标 → Quit）
    echo 2. 等待10秒
    echo 3. 重新打开Docker Desktop
    echo 4. 等待Docker完全初始化（30-60秒）
    echo 5. 重新运行此脚本
    echo.
    pause
    exit /b 1
)
echo ✅ 数据库服务启动命令已执行
echo.

echo ========================================
echo 第3步：等待数据库初始化
echo ========================================
echo 等待20秒让PostgreSQL完全启动...
for /l %%i in (1,1,20) do (
    echo %%i秒...
    ping 127.0.0.1 -n 2 >nul
)
echo.

echo ========================================
echo 第4步：检查数据库状态
echo ========================================
docker-compose ps postgres
docker-compose ps redis
echo.

echo 检查PostgreSQL日志...
docker-compose logs postgres | findstr "ready to accept connections"
if errorlevel 1 (
    echo ⚠️ PostgreSQL可能还未完全启动
    echo 建议：再等待10秒，然后手动检查
    echo 命令：docker-compose logs postgres
) else (
    echo ✅ PostgreSQL已就绪！
)
echo.

echo ========================================
echo 第5步：初始化数据库
echo ========================================
echo 正在创建数据库表和初始数据...
docker exec -i bossjy-postgres psql -U jytian -d bossjy_huaqiao < deploy\init.sql
if errorlevel 1 (
    echo ⚠️ 数据库初始化可能失败
    echo 这可能是因为：
    echo   1. PostgreSQL还未完全启动
    echo   2. 数据库已经存在
    echo.
    echo 继续启动其他服务...
) else (
    echo ✅ 数据库初始化成功！
)
echo.

echo ========================================
echo 第6步：启动应用服务
echo ========================================
echo 正在启动 FastAPI, Go API, Bots, Vue...
docker-compose up -d fastapi go-api bots vue-frontend
if errorlevel 1 (
    echo ❌ 应用服务启动失败！
    echo 查看日志：docker-compose logs
    pause
    exit /b 1
)
echo ✅ 应用服务启动命令已执行
echo.

echo ========================================
echo 第7步：启动Nginx
echo ========================================
echo 正在启动 Nginx...
docker-compose up -d nginx
echo ✅ Nginx启动命令已执行
echo.

echo 等待5秒让所有服务完全启动...
ping 127.0.0.1 -n 6 >nul
echo.

echo ========================================
echo 第8步：检查所有服务状态
echo ========================================
docker-compose ps
echo.

echo ========================================
echo 第9步：验证服务
echo ========================================
echo.
echo 检查FastAPI健康状态...
curl -s http://localhost:18001/health 2>nul
if errorlevel 1 (
    echo ⚠️ FastAPI可能还未就绪，请稍后访问
) else (
    echo ✅ FastAPI正常！
)
echo.

echo ========================================
echo 🎉 启动流程完成！
echo ========================================
echo.
echo 请访问以下地址验证系统：
echo.
echo 📱 前端应用：     http://localhost:3000
echo 📚 API文档：      http://localhost:18001/docs
echo 📊 Grafana监控：  http://localhost:3001 (admin / ji394su3!!)
echo 🔍 Prometheus：   http://localhost:9090
echo 🔧 Go API健康：   http://localhost:8080/api/health
echo.

echo ========================================
echo 📋 有用的命令
echo ========================================
echo 查看日志：       docker-compose logs -f
echo 查看特定服务：   docker-compose logs -f fastapi
echo 重启服务：       docker-compose restart
echo 停止服务：       docker-compose down
echo.

echo ========================================
echo 🧪 测试命令示例
echo ========================================
echo.
echo 测试电话验证：
echo curl -X POST http://localhost:18001/phone/validate ^
echo   -H "Content-Type: application/json" ^
echo   -d "{\"phone_number\": \"+86 138 0000 0000\"}"
echo.
echo 测试用户注册：
echo curl -X POST http://localhost:18001/auth/register ^
echo   -H "Content-Type: application/json" ^
echo   -d "{\"username\": \"test\", \"email\": \"test@test.com\", \"password\": \"test123\"}"
echo.

pause
