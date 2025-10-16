@echo off
echo ========================================
echo BossJy系统诊断脚本
echo ========================================
echo.

echo [Docker版本]
docker version

echo.
echo [Docker系统信息]
docker info | findstr "Storage Driver"
docker info | findstr "Overlay"

echo.
echo [WSL状态]
wsl -l -v

echo.
echo [Docker容器状态]
docker ps -a

echo.
echo [Docker镜像]
docker images | findstr bossjy

echo.
echo [Docker卷]
docker volume ls | findstr bossjy

echo.
echo [Docker网络]
docker network ls | findstr bossjy

echo.
echo ========================================
echo 诊断完成
echo ========================================
pause
