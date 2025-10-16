@echo off
echo ========================================
echo Docker Complete Fix Script
echo ========================================
echo.

echo Step 1: Stopping all Docker containers...
docker-compose down -v 2>nul
docker stop $(docker ps -aq) 2>nul
docker rm $(docker ps -aq) 2>nul

echo.
echo Step 2: Shutting down WSL...
wsl --shutdown
timeout /t 3 >nul

echo.
echo Step 3: Stopping Docker Desktop...
taskkill /F /IM "Docker Desktop.exe" 2>nul
timeout /t 3 >nul

echo.
echo Step 4: Cleaning Docker data...
wsl --shutdown
timeout /t 2 >nul

echo.
echo ========================================
echo MANUAL STEP REQUIRED:
echo ========================================
echo Please manually:
echo 1. Start Docker Desktop
echo 2. Wait for it to fully initialize (whale icon should be steady)
echo 3. Press any key here to continue...
echo ========================================
pause >nul

echo.
echo Step 5: Verifying Docker is running...
docker version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop manually and run this script again.
    pause
    exit /b 1
)

echo.
echo Step 6: Testing Docker with hello-world...
docker run --rm hello-world

echo.
echo Step 7: Starting BossJy services...
echo Starting databases first...
docker-compose up -d postgres redis

echo.
echo Waiting 15 seconds for databases to initialize...
timeout /t 15 /nobreak

echo.
echo Starting application services...
docker-compose up -d fastapi go-api bots vue-frontend

echo.
echo Starting nginx...
docker-compose up -d nginx

echo.
echo Step 8: Checking service status...
docker-compose ps

echo.
echo ========================================
echo Docker Fix Complete!
echo ========================================
echo.
echo Services should now be running.
echo Check status with: docker-compose ps
echo View logs with: docker-compose logs -f
echo.
pause
