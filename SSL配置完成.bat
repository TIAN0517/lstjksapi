@echo off
chcp 65001 >nul
title BossJy-Pro SSL配置完成

echo ========================================
echo    BossJy-Pro SSL配置已完成
echo ========================================
echo.

echo 🔐 SSL证书状态: ✅ 已完成
echo 📁 证书位置: deploy\nginx\ssl\
echo.

echo 📋 已生成的SSL证书:
echo    • appai.tiankai.it.com.crt / .key
echo    • bossjy.tiankai.it.com.crt / .key
echo    • chat.tiankai.it.com.crt / .key
echo    • jyt.tiankai.it.com.crt / .key
echo    • admin.tiankai.it.com.crt / .key
echo.

echo 🌐 子域名配置:
echo    • appai.tiankai.it.com  -> 端口 18001
echo    • bossjy.tiankai.it.com -> 端口 9001
echo    • chat.tiankai.it.com   -> 端口 9002
echo    • jyt.tiankai.it.com    -> 端口 9003
echo    • admin.tiankai.it.com  -> 端口 9888
echo.

echo 🚀 启动选项:
echo.
echo 选项1 - Docker方式 (推荐):
echo    docker-compose up -d nginx
echo.
echo 选项2 - 本地Nginx方式:
echo    start_local_nginx.bat
echo.
echo 选项3 - 端口服务测试:
echo    python test_ports.py
echo.

echo 💡 重要提示:
echo    • SSL证书已配置完成，可以开启HTTPS代理
echo    • 这些是自签名证书，浏览器会显示安全警告
echo    • 在生产环境中建议使用Cloudflare SSL证书
echo    • 确保DNS记录已正确配置所有子域名
echo    • 确保防火墙允许80/443端口访问
echo.

echo 🎉 配置完成! 现在可以开启代理服务了!
echo.

pause