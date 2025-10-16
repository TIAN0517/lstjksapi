@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Phone Number Cleaning Tool - Batch Version
echo ========================================
echo.

if "%~1"=="" (
    echo Usage: batch_clean_en.bat [API_KEY] [INPUT_FILE] [OUTPUT_FILE] [COUNTRY_CODE] [VENDOR]
    echo.
    echo Examples:
    echo   batch_clean_en.bat YOUR_KEY data\input.csv data\output.csv CN telnyx
    echo   batch_clean_en.bat "" data\input.csv data\output.csv CN
    echo.
    pause
    exit /b 1
)

set "HLR_API_KEY=%~1"
set "INPUT_FILE=%~2"
set "OUTPUT_FILE=%~3"
set "DEFAULT_REGION=%~4"
set "HLR_VENDOR=%~5"

if "%HLR_VENDOR%"=="" set "HLR_VENDOR=none"

echo Input file: %INPUT_FILE%
echo Output file: %OUTPUT_FILE%
echo Default region: %DEFAULT_REGION%
echo HLR vendor: %HLR_VENDOR%
echo.

if not exist "%INPUT_FILE%" (
    echo ERROR: Input file not found - %INPUT_FILE%
    pause
    exit /b 1
)

echo Starting processing...
echo.

if "%HLR_VENDOR%"=="none" (
    echo Running basic cleaning (no HLR detection)...
    venv\Scripts\python.exe scripts\clean_numbers.py --in "%INPUT_FILE%" --out "%OUTPUT_FILE%" --default-region "%DEFAULT_REGION%"
) else (
    echo Running cleaning + HLR detection...
    if "%HLR_API_KEY%"=="" (
        echo ERROR: HLR detection requires API key
        pause
        exit /b 1
    )
    set "HLR_API_KEY=%HLR_API_KEY%"
    venv\Scripts\python.exe scripts\clean_numbers.py --in "%INPUT_FILE%" --out "%OUTPUT_FILE%" --default-region "%DEFAULT_REGION%" --hlr-vendor "%HLR_VENDOR%"
)

echo.
if %ERRORLEVEL% EQU 0 (
    echo ========================================
    echo Processing completed!
    echo ========================================
    echo Output file: %OUTPUT_FILE%
    
    if exist "%OUTPUT_FILE%" (
        echo.
        echo First 5 lines of results:
        powershell -Command "Get-Content '%OUTPUT_FILE%' | Select-Object -First 5"
    )
) else (
    echo ========================================
    echo Processing failed!
    echo ========================================
)

echo.
pause