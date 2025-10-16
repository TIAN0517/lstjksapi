@echo off
setlocal enabledelayedexpansion

:menu
cls
echo ========================================
echo     BossJy 系统管理工具
echo ========================================
echo.
echo 1. 启动所有服务
echo 2. 停止所有服务
echo 3. 重启所有服务
echo 4. 查看服务状态
echo 5. 查看服务日志
echo 6. 数据库管理
echo 7. 备份数据库
echo 8. 系统诊断
echo 9. Docker修复
echo 0. 退出
echo.
set /p choice=请选择操作 (0-9): 

if "%choice%"=="1" goto start_services
if "%choice%"=="2" goto stop_services
if "%choice%"=="3" goto restart_services
if "%choice%"=="4" goto service_status
if "%choice%"=="5" goto view_logs
if "%choice%"=="6" goto db_management
if "%choice%"=="7" goto backup_db
if "%choice%"=="8" goto diagnose
if "%choice%"=="9" goto fix_docker
if "%choice%"=="0" goto end

echo 无效选择，请重试
timeout /t 2 >nul
goto menu

:start_services
cls
echo ========================================
echo 启动服务
echo ========================================
echo.
echo [1/4] 启动数据库服务...
docker-compose up -d postgres redis
timeout /t 10

echo.
echo [2/4] 启动应用服务...
docker-compose up -d fastapi go-api bots vue-frontend

echo.
echo [3/4] 启动Nginx...
docker-compose up -d nginx

echo.
echo [4/4] 启动监控服务...
docker-compose -f docker-compose.complete.yml up -d prometheus grafana

echo.
echo 服务启动完成！
pause
goto menu

:stop_services
cls
echo ========================================
echo 停止服务
echo ========================================
echo.
docker-compose down
echo.
echo 服务已停止！
pause
goto menu

:restart_services
cls
echo ========================================
echo 重启服务
echo ========================================
echo.
docker-compose restart
echo.
echo 服务已重启！
pause
goto menu

:service_status
cls
echo ========================================
echo 服务状态
echo ========================================
echo.
docker-compose ps
echo.
pause
goto menu

:view_logs
cls
echo ========================================
echo 查看日志
echo ========================================
echo.
echo 1. FastAPI日志
echo 2. Go API日志
echo 3. Telegram Bots日志
echo 4. Nginx日志
echo 5. 所有服务日志
echo 0. 返回主菜单
echo.
set /p log_choice=请选择 (0-5): 

if "%log_choice%"=="1" docker-compose logs -f fastapi
if "%log_choice%"=="2" docker-compose logs -f go-api
if "%log_choice%"=="3" docker-compose logs -f bots
if "%log_choice%"=="4" docker-compose logs -f nginx
if "%log_choice%"=="5" docker-compose logs -f
if "%log_choice%"=="0" goto menu

pause
goto menu

:db_management
cls
echo ========================================
echo 数据库管理
echo ========================================
echo.
echo 1. 连接PostgreSQL
echo 2. 运行初始化脚本
echo 3. 查看数据库表
echo 4. 查看用户统计
echo 0. 返回主菜单
echo.
set /p db_choice=请选择 (0-4): 

if "%db_choice%"=="1" (
    docker exec -it bossjy-postgres psql -U jytian -d bossjy_huaqiao
)
if "%db_choice%"=="2" (
    docker exec -i bossjy-postgres psql -U jytian -d bossjy_huaqiao < deploy/init.sql
    echo 初始化脚本执行完成！
    pause
)
if "%db_choice%"=="3" (
    docker exec -it bossjy-postgres psql -U jytian -d bossjy_huaqiao -c "\dt"
    pause
)
if "%db_choice%"=="4" (
    docker exec -it bossjy-postgres psql -U jytian -d bossjy_huaqiao -c "SELECT * FROM user_statistics;"
    pause
)
if "%db_choice%"=="0" goto menu

goto menu

:backup_db
cls
echo ========================================
echo 备份数据库
echo ========================================
echo.
set backup_name=backup_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.sql.gz
set backup_name=%backup_name: =0%
echo 备份文件名: %backup_name%
echo.
docker exec bossjy-postgres pg_dump -U jytian bossjy_huaqiao | gzip > backups/%backup_name%
echo.
if %errorlevel% equ 0 (
    echo 备份成功！
) else (
    echo 备份失败！
)
pause
goto menu

:diagnose
cls
echo ========================================
echo 系统诊断
echo ========================================
echo.
echo [Docker版本]
docker version
echo.
echo [WSL状态]
wsl -l -v
echo.
echo [容器状态]
docker ps -a
echo.
echo [镜像列表]
docker images | findstr bossjy
echo.
echo [卷列表]
docker volume ls | findstr bossjy
echo.
pause
goto menu

:fix_docker
cls
echo ========================================
echo Docker修复
echo ========================================
echo.
echo 警告：此操作将停止所有容器并清理Docker系统
echo.
set /p confirm=确认继续? (Y/N): 
if /i not "%confirm%"=="Y" goto menu

echo.
echo [1/4] 停止所有容器...
docker-compose down -v

echo.
echo [2/4] 关闭WSL...
wsl --shutdown
timeout /t 5

echo.
echo [3/4] 清理Docker系统...
docker system prune -a -f --volumes

echo.
echo [4/4] 请手动重启Docker Desktop
echo.
pause
goto menu

:end
echo 感谢使用！
endlocal
exit /b 0
