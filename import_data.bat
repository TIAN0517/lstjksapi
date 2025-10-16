@echo off
chcp 65001 >nul
echo ====================================
echo BossJy-Pro PostgreSQL Data Import
echo ====================================
echo.

echo Checking PostgreSQL service...
docker exec bossjy-postgres pg_isready -U jytian >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: PostgreSQL service is not running
    echo Please start Docker services first
    pause
    exit /b 1
)
echo PostgreSQL service is running

echo.
echo Starting data import...
python import_simple.py

if %errorlevel% equ 0 (
    echo.
    echo ====================================
    echo Data import completed!
    echo ====================================
) else (
    echo.
    echo Import failed, please check error messages
)

echo.
pause