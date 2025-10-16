@echo off
echo ========================================
echo BossJy-Cn Services Status
echo ========================================

echo.
echo Running Services:
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo All Containers:
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo Service URLs:
echo - Frontend:     http://localhost:3000
echo - FastAPI:      http://localhost:18001  
echo - Go API:       http://localhost:8081
echo - Bots Service: http://localhost:9001
echo - Admin:        http://localhost:9888
echo - JYT Service:  http://localhost:9003
echo - Chat Service: http://localhost:9002

echo.
echo ========================================
echo.
pause