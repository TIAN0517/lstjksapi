@echo off
chcp 65001 >nul
echo ====================================
echo BossJy-Pro Docker Image Push Script
echo ====================================
echo.

set REGISTRY=your-registry.com
set VERSION=latest

echo Building and pushing Docker images...
echo.

echo [1/5] Building FastAPI image...
docker build -t bossjy-cn-fastapi:%VERSION% -f services/fastapi/Dockerfile .
docker tag bossjy-cn-fastapi:%VERSION% %REGISTRY%/bossjy-cn-fastapi:%VERSION%
docker push %REGISTRY%/bossjy-cn-fastapi:%VERSION%

echo.
echo [2/5] Building Go API image...
docker build -t bossjy-cn-go-api:%VERSION% -f services/go-api/Dockerfile .
docker tag bossjy-cn-go-api:%VERSION% %REGISTRY%/bossjy-cn-go-api:%VERSION%
docker push %REGISTRY%/bossjy-cn-go-api:%VERSION%

echo.
echo [3/5] Building Vue Frontend image...
docker build -t bossjy-cn-vue-frontend:%VERSION% -f web/Dockerfile .
docker tag bossjy-cn-vue-frontend:%VERSION% %REGISTRY%/bossjy-cn-vue-frontend:%VERSION%
docker push %REGISTRY%/bossjy-cn-vue-frontend:%VERSION%

echo.
echo [4/5] Building Bots image...
docker build -t bossjy-cn-bots:%VERSION% -f integrations/telegram/Dockerfile .
docker tag bossjy-cn-bots:%VERSION% %REGISTRY%/bossjy-cn-bots:%VERSION%
docker push %REGISTRY%/bossjy-cn-bots:%VERSION%

echo.
echo [5/5] All images pushed successfully!
echo.

pause