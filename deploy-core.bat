@echo off
REM BossJy-Pro Core Deployment Script (Windows)
REM Starts only essential services

setlocal enabledelayedexpansion

echo BossJy-Pro Core Deployment Script (Windows)
echo ============================================
echo.

REM Check if Docker Desktop is running
echo [INFO] Checking Docker Desktop status...
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktop is not running, please start Docker Desktop first
    pause
    exit /b 1
)
echo [SUCCESS] Docker Desktop is running

REM Check SSL certificates
echo [INFO] Checking SSL certificates...
set SSL_DIR=C:\nginx\ssl

if not exist "%SSL_DIR%" (
    echo [WARNING] SSL certificate directory does not exist: %SSL_DIR%
    echo [INFO] Creating self-signed certificates for testing...
    if not exist "%SSL_DIR%" mkdir "%SSL_DIR%"
    
    REM Generate self-signed certificates
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout "%SSL_DIR%\bossjy.tiankai.it.com.key" -out "%SSL_DIR%\bossjy.tiankai.it.com.crt" -subj "/C=TW/ST=Taipei/L=Taipei/O=BossJy/CN=bossjy.tiankai.it.com"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout "%SSL_DIR%\appai.tiankai.it.com.key" -out "%SSL_DIR%\appai.tiankai.it.com.crt" -subj "/C=TW/ST=Taipei/L=Taipei/O=BossJy/CN=appai.tiankai.it.com"
    
    echo [SUCCESS] Self-signed certificates created
) else (
    echo [SUCCESS] SSL certificate directory exists
)

REM Create necessary directories
echo [INFO] Creating necessary directories...
if not exist "logs" mkdir logs
if not exist "logs\fastapi" mkdir logs\fastapi
if not exist "logs\go-api" mkdir logs\go-api
if not exist "logs\bots" mkdir logs\bots
if not exist "logs\nginx" mkdir logs\nginx

if not exist "data" mkdir data
if not exist "data\uploads" mkdir data\uploads
if not exist "data\processed" mkdir data\processed
if not exist "data\exports" mkdir data\exports

if not exist "backups" mkdir backups
if not exist "services\fastapi\phone_db" mkdir services\fastapi\phone_db

echo [SUCCESS] Directories created

REM Check environment file
echo [INFO] Checking environment file...

REM Check if .env exists
if exist ".env" (
    echo [SUCCESS] .env file exists
    goto env_check_done
)

REM .env doesn't exist, check for .env.example
echo [WARNING] .env file does not exist, checking for template file...
if exist ".env.example" (
    echo [INFO] Found .env.example, creating .env file...
    copy .env.example .env >nul
    echo [WARNING] Please edit .env file and set correct configuration values
    echo [INFO] Key configurations to modify:
    echo [INFO] - POSTGRES_PASSWORD
    echo [INFO] - REDIS_PASSWORD
    echo [INFO] - SECRET_KEY
    echo [INFO] - JWT_SECRET_KEY
    echo [INFO] - BOT_TOKENS
    echo [INFO] - TWILIO_ACCOUNT_SID (optional)
    echo [INFO] - TWILIO_AUTH_TOKEN (optional)
) else (
    echo [ERROR] .env.example file does not exist
    echo [ERROR] Cannot create .env file without template
    pause
    exit /b 1
)

:env_check_done

REM Build Docker images
echo [INFO] Building Docker images...
docker-compose -f docker-compose.yml build --no-cache
if errorlevel 1 (
    echo [ERROR] Docker image build failed
    pause
    exit /b 1
)
echo [SUCCESS] Docker images built

REM Start services
echo [INFO] Starting BossJy-Pro core services...
docker-compose -f docker-compose.yml up -d
if errorlevel 1 (
    echo [ERROR] Service startup failed
    pause
    exit /b 1
)
echo [SUCCESS] Services starting...

REM Wait for services to be ready
echo [INFO] Waiting for services to be ready...

:wait_postgres
echo [INFO] Waiting for PostgreSQL...
docker-compose -f docker-compose.yml exec -T postgres pg_isready -U bossjy -d bossjy >nul 2>&1
if errorlevel 1 (
    timeout /t 2 >nul
    goto wait_postgres
)

:wait_redis
echo [INFO] Waiting for Redis...
docker-compose -f docker-compose.yml exec -T redis redis-cli ping >nul 2>&1
if errorlevel 1 (
    timeout /t 2 >nul
    goto wait_redis
)

:wait_fastapi
echo [INFO] Waiting for FastAPI...
curl -f http://localhost:18001/api/health >nul 2>&1
if errorlevel 1 (
    timeout /t 5 >nul
    goto wait_fastapi
)

echo [SUCCESS] All services are ready

REM Verify deployment
echo [INFO] Verifying deployment...
docker-compose -f docker-compose.yml ps

echo [INFO] Checking service health status...

REM FastAPI
curl -f http://localhost:18001/api/health >nul 2>&1
if errorlevel 1 (
    echo [ERROR] FastAPI (18001) - abnormal
) else (
    echo [SUCCESS] FastAPI (18001) - normal
)

REM Go API
curl -f http://localhost:8080/api/health >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Go API (8080) - abnormal
) else (
    echo [SUCCESS] Go API (8080) - normal
)

REM Vue Frontend
curl -f http://localhost:3000/health >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Vue Frontend (3000) - abnormal
) else (
    echo [SUCCESS] Vue Frontend (3000) - normal
)

REM Telegram Bots
curl -f http://localhost:9001/status >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Telegram Bots (9001) - abnormal
) else (
    echo [SUCCESS] Telegram Bots (9001) - normal
)

REM Display deployment information
echo.
echo [SUCCESS] BossJy-Pro core deployment completed!
echo.
echo === Service Access Addresses ===
echo Main Site: https://bossjy.tiankai.it.com
echo AppAI: https://appai.tiankai.it.com
echo.
echo === Local Development Ports ===
echo FastAPI: http://localhost:18001
echo Go API: http://localhost:8080
echo Vue Frontend: http://localhost:3000
echo Telegram Bots: http://localhost:9001
echo.
echo === Database Ports ===
echo PostgreSQL: localhost:15432
echo Redis: localhost:16379
echo.
echo === API Documentation ===
echo FastAPI Docs: http://localhost:18001/docs
echo Go API Docs: http://localhost:8080/docs
echo.
echo === Management Commands ===
echo Restart Services: docker-compose -f docker-compose.yml restart
echo View Logs: docker-compose -f docker-compose.yml logs -f [service_name]
echo Stop Services: docker-compose -f docker-compose.yml down
echo.
echo [INFO] Please ensure domains point to the correct IP address
echo [INFO] For local testing, modify hosts file to add domain mapping
echo.

pause