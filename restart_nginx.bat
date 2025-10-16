@echo off
chcp 65001 >nul
title BossJy-Pro Nginx 重启器

echo ========================================
echo    BossJy-Pro Nginx 重启器
echo ========================================
echo.

echo 🔄 重启Nginx服务...
cd /d C:\nginx

REM 停止现有服务
echo 🛑 停止现有Nginx服务...
nginx -s stop >nul 2>&1
timeout /t 2 >nul

REM 启动服务
echo 🚀 启动Nginx服务...
start nginx

echo ✅ Nginx已重启
echo.

echo 📋 测试路径:
echo    • https://appai.tiankai.it.com/register?plan=enterprise
echo    • https://appai.tiankai.it.com/login
echo    • https://appai.tiankai.it.com/dashboard
echo    • https://bossjy.tiankai.it.com/api/test
echo.

echo 💡 提示:
echo    • 确保端口服务已启动 (python test_ports.py)
echo    • 如果仍有问题，请检查Nginx错误日志
echo.

pause