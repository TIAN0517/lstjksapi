@echo off
chcp 65001 >nul
REM BossJy-Pro Git 推送腳本 (Windows 版本)

setlocal enabledelayedexpansion

echo 🚀 BossJy-Pro Git 推送腳本 (Windows)
echo =====================================
echo.

REM 檢查 Git 狀態
echo [INFO] 檢查 Git 狀態...
git status --porcelain >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git 狀態檢查失敗
    pause
    exit /b 1
)

REM 檢查是否有未提交的更改
for /f %%i in ('git status --porcelain ^| find /c /v ""') do set CHANGES_COUNT=%%i
if %CHANGES_COUNT% GTR 0 (
    echo [WARNING] 發現未提交的更改
    git status --short
    
    set /p "CONTINUE=是否要繼續推送？(y/N): "
    if /i not "!CONTINUE!"=="y" (
        echo [INFO] 取消推送
        pause
        exit /b 0
    )
) else (
    echo [SUCCESS] 沒有未提交的更改
)

REM 添加文件到暫存區
echo [INFO] 添加文件到暫存區...

REM 添加新創建的整合文件
git add docker-compose.complete.yml
git add services\fastapi\api\phone_validation_api.py
git add services\fastapi\main.py
git add deploy\nginx\nginx.conf
git add deploy\nginx\conf.d\bossjy-complete.conf
git add deploy\nginx\snippets\proxy-params.conf
git add deploy-complete.sh
git add deploy-complete.bat
git add DEPLOYMENT_COMPLETE_GUIDE.md

REM 添加所有更改
git add .

if errorlevel 1 (
    echo [ERROR] 添加文件到暫存區失敗
    pause
    exit /b 1
)

echo [SUCCESS] 文件已添加到暫存區

REM 提交更改
echo [INFO] 提交更改...

REM 創建提交信息
git commit -m "feat: 完整架構整合與部署優化

🚀 主要更新:
- 整合電話驗證服務到主 FastAPI (移除重複實現)
- 新增完整的 Docker Compose 配置 (包含監控和日誌)
- 優化 Nginx SSL 配置和本地證書映射
- 創建統一部署腳本 (Windows/Linux 支援)
- 新增 Prometheus + Grafana 監控系統
- 整合 ELK Stack 日誌聚合
- 添加自動備份服務

🔧 技術改進:
- 統一服務端口管理
- 優化容器健康檢查
- 完善環境變數配置
- 增強安全設置

📚 文檔更新:
- 完整部署指南
- API 使用示例
- 故障排除指南

🐳 Docker Desktop 優化:
- 本地 SSL 證書映射 (C:/nginx/ssl)
- Windows 批處理腳本支援
- 一鍵部署流程

This commit integrates all scattered components into a unified, production-ready architecture."

if errorlevel 1 (
    echo [ERROR] 提交失敗
    pause
    exit /b 1
)

echo [SUCCESS] 更改已提交

REM 推送到遠程倉庫
echo [INFO] 推送到遠程倉庫...

REM 獲取當前分支
for /f %%i in ('git rev-parse --abbrev-ref HEAD') do set CURRENT_BRANCH=%%i

git push origin %CURRENT_BRANCH%

if errorlevel 1 (
    echo [ERROR] 推送到遠程倉庫失敗
    pause
    exit /b 1
)

echo [SUCCESS] 已推送到遠程倉庫

REM 顯示推送後信息
echo.
echo [SUCCESS] 代碼推送完成！
echo.
echo === 後續操作 ===
echo 🚀 在服務器上部署:
echo    git pull origin main
echo    ./deploy-complete.sh  # Linux
echo    ./deploy-complete.bat # Windows
echo.
echo 🔍 查看部署狀態:
echo    docker-compose -f docker-compose.complete.yml ps
echo.
echo 📊 查看服務日誌:
echo    docker-compose -f docker-compose.complete.yml logs -f
echo.
echo 🌐 訪問服務:
echo    主站: https://bossjy.tiankai.it.com
echo    監控: https://monitor.bossjy.tiankai.it.com
echo.
echo [INFO] 請確保服務器環境已準備就緒
echo.

pause