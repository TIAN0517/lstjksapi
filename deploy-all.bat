@echo off
echo ===================================
echo BossJy-Cn Full System Deployment
echo ===================================

:: Set color
color 0E

:: Check Docker installation
echo [1/8] Checking Docker environment...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker not installed or not running
    echo Please install Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)
echo Docker is installed

:: Check Docker Compose
echo [2/8] Checking Docker Compose...
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker Compose not available
    pause
    exit /b 1
)
echo Docker Compose is ready

:: Stop existing services
echo [3/8] Stopping existing services...
docker-compose -f docker-compose.frontend.yml down >nul 2>&1
echo Existing services stopped

:: Clean old images (optional)
echo [4/8] Cleaning old images...
set /p clean_images="Clean old Docker images? (y/n): "
if /i "%clean_images%"=="y" (
    docker system prune -f
    echo Old images cleaned
) else (
    echo Skipping image cleanup
)

:: Build and start all services
echo [5/8] Building and starting all services...
docker-compose -f docker-compose.frontend.yml up --build -d
if %errorlevel% neq 0 (
    echo ERROR: Service startup failed
    pause
    exit /b 1
)
echo Services started successfully

:: Wait for services to be ready
echo [6/8] Waiting for services to be ready...
timeout /t 10 /nobreak >nul

:: Check service status
echo [7/8] Checking service status...
docker-compose -f docker-compose.frontend.yml ps

:: Display access information
echo [8/8] System deployment complete!
echo.
echo ===================================
echo BossJy-Cn System Successfully Deployed!
echo.
echo Access URLs:
echo - Frontend: http://localhost:3000
echo - Backend API: http://localhost:18001
echo - API Docs: http://localhost:18001/docs
echo - Database: localhost:15432
echo - Redis: localhost:16379
echo.
echo Default Account:
echo - Username: admin@bossjy.com
echo - Password: admin123
echo.
echo Management Commands:
echo - View logs: docker-compose -f docker-compose.frontend.yml logs -f
echo - Stop system: docker-compose -f docker-compose.frontend.yml down
echo - Restart system: docker-compose -f docker-compose.frontend.yml restart
echo ===================================
echo.

:: Ask to view logs
set /p view_logs="View real-time logs? (y/n): "
if /i "%view_logs%"=="y" (
    echo Displaying real-time logs (press Ctrl+C to exit)...
    docker-compose -f docker-compose.frontend.yml logs -f
)

pause