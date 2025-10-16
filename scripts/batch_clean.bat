@echo off
setlocal enabledelayedexpansion

echo ========================================
echo 电话号码清洗工具 - 批处理版本
echo ========================================
echo.

if "%~1"=="" (
    echo 用法: batch_clean.bat [API_KEY] [输入文件] [输出文件] [国家代码] [供应商]
    echo.
    echo 示例:
    echo   batch_clean.bat YOUR_KEY data\input.csv data\output.csv CN telnyx
    echo   batch_clean.bat "" data\input.csv data\output.csv CN
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

echo 输入文件: %INPUT_FILE%
echo 输出文件: %OUTPUT_FILE%
echo 默认地区: %DEFAULT_REGION%
echo HLR供应商: %HLR_VENDOR%
echo.

if not exist "%INPUT_FILE%" (
    echo 错误: 输入文件不存在 - %INPUT_FILE%
    pause
    exit /b 1
)

echo 开始处理...
echo.

if "%HLR_VENDOR%"=="none" (
    echo 执行基础清洗（无HLR检测）...
    venv\Scripts\python.exe scripts\clean_numbers.py --in "%INPUT_FILE%" --out "%OUTPUT_FILE%" --default-region "%DEFAULT_REGION%"
) else (
    echo 执行清洗 + HLR检测...
    if "%HLR_API_KEY%"=="" (
        echo 错误: 使用HLR检测需要提供API密钥
        pause
        exit /b 1
    )
    set "HLR_API_KEY=%HLR_API_KEY%"
    venv\Scripts\python.exe scripts\clean_numbers.py --in "%INPUT_FILE%" --out "%OUTPUT_FILE%" --default-region "%DEFAULT_REGION%" --hlr-vendor "%HLR_VENDOR%"
)

echo.
if %ERRORLEVEL% EQU 0 (
    echo ========================================
    echo 处理完成！
    echo ========================================
    echo 输出文件: %OUTPUT_FILE%
    
    if exist "%OUTPUT_FILE%" (
        echo.
        echo 前5行结果:
        powershell -Command "Get-Content '%OUTPUT_FILE%' | Select-Object -First 5"
    )
) else (
    echo ========================================
    echo 处理失败！
    echo ========================================
)

echo.
pause