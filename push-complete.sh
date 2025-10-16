#!/bin/bash
# BossJy-Pro Git 推送腳本

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查 Git 狀態
check_git_status() {
    log_info "檢查 Git 狀態..."
    
    # 檢查是否有未提交的更改
    if [[ -n $(git status --porcelain) ]]; then
        log_warning "發現未提交的更改"
        git status --short
        
        read -p "是否要繼續推送？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "取消推送"
            exit 0
        fi
    else
        log_success "沒有未提交的更改"
    fi
}

# 添加文件到暫存區
add_files() {
    log_info "添加文件到暫存區..."
    
    # 添加新創建的整合文件
    git add docker-compose.complete.yml
    git add services/fastapi/api/phone_validation_api.py
    git add services/fastapi/main.py
    git add deploy/nginx/nginx.conf
    git add deploy/nginx/conf.d/bossjy-complete.conf
    git add deploy/nginx/snippets/proxy-params.conf
    git add deploy-complete.sh
    git add deploy-complete.bat
    git add DEPLOYMENT_COMPLETE_GUIDE.md
    
    # 添加所有更改
    git add .
    
    log_success "文件已添加到暫存區"
}

# 提交更改
commit_changes() {
    log_info "提交更改..."
    
    # 創建提交信息
    COMMIT_MESSAGE="feat: 完整架構整合與部署優化

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
    
    git commit -m "$COMMIT_MESSAGE"
    
    log_success "更改已提交"
}

# 推送到遠程倉庫
push_to_remote() {
    log_info "推送到遠程倉庫..."
    
    # 獲取當前分支
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    
    # 推送到遠程
    git push origin "$CURRENT_BRANCH"
    
    log_success "已推送到遠程倉庫"
}

# 顯示推送後信息
show_post_push_info() {
    log_success "🎉 代碼推送完成！"
    echo ""
    echo "=== 後續操作 ==="
    echo "🚀 在服務器上部署:"
    echo "   git pull origin main"
    echo "   ./deploy-complete.sh  # Linux"
    echo "   ./deploy-complete.bat # Windows"
    echo ""
    echo "🔍 查看部署狀態:"
    echo "   docker-compose -f docker-compose.complete.yml ps"
    echo ""
    echo "📊 查看服務日誌:"
    echo "   docker-compose -f docker-compose.complete.yml logs -f"
    echo ""
    echo "🌐 訪問服務:"
    echo "   主站: https://bossjy.tiankai.it.com"
    echo "   監控: https://monitor.bossjy.tiankai.it.com"
    echo ""
    log_info "請確保服務器環境已準備就緒"
}

# 主函數
main() {
    echo "🚀 BossJy-Pro Git 推送腳本"
    echo "========================="
    echo ""
    
    # 檢查 Git 狀態
    check_git_status
    
    # 添加文件
    add_files
    
    # 提交更改
    commit_changes
    
    # 推送到遠程
    push_to_remote
    
    # 顯示後續信息
    show_post_push_info
}

# 處理中斷信號
trap 'log_warning "推送被中斷"; exit 1' INT TERM

# 執行主函數
main "$@"