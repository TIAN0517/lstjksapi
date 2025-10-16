#!/bin/bash
# BossJy-Pro 完整部署腳本
# 支援 Docker Desktop + SSL 證書映射

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

# 檢查 Docker Desktop 是否運行
check_docker() {
    log_info "檢查 Docker Desktop 狀態..."
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker Desktop 未運行，請先啟動 Docker Desktop"
        exit 1
    fi
    log_success "Docker Desktop 運行中"
}

# 檢查 SSL 證書
check_ssl_certificates() {
    log_info "檢查 SSL 證書..."
    
    # 定義本地 SSL 證書路徑 (Windows)
    SSL_DIR="C:/nginx/ssl"
    
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows 環境
        if [[ ! -d "$SSL_DIR" ]]; then
            log_warning "SSL 證書目錄不存在: $SSL_DIR"
            log_info "將創建自簽名證書用於測試..."
            mkdir -p "$SSL_DIR"
            
            # 生成自簽名證書
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout "$SSL_DIR/bossjy.tiankai.it.com.key" \
                -out "$SSL_DIR/bossjy.tiankai.it.com.crt" \
                -subj "/C=TW/ST=Taipei/L=Taipei/O=BossJy/CN=bossjy.tiankai.it.com"
            
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout "$SSL_DIR/appai.tiankai.it.com.key" \
                -out "$SSL_DIR/appai.tiankai.it.com.crt" \
                -subj "/C=TW/ST=Taipei/L=Taipei/O=BossJy/CN=appai.tiankai.it.com"
            
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout "$SSL_DIR/monitor.bossjy.tiankai.it.com.key" \
                -out "$SSL_DIR/monitor.bossjy.tiankai.it.com.crt" \
                -subj "/C=TW/ST=Taipei/L=Taipei/O=BossJy/CN=monitor.bossjy.tiankai.it.com"
            
            log_success "自簽名證書已創建"
        else
            log_success "SSL 證書目錄存在"
        fi
    else
        log_warning "非 Windows 環境，請手動配置 SSL 證書路徑"
    fi
}

# 創建必要的目錄
create_directories() {
    log_info "創建必要的目錄..."
    
    # 創建日誌目錄
    mkdir -p logs/{fastapi,go-api,bots,nginx}
    
    # 創建數據目錄
    mkdir -p data/{uploads,processed,exports}
    mkdir -p backups
    mkdir -p monitoring
    
    # 創建電話驗證數據庫目錄
    mkdir -p services/fastapi/phone_db
    
    log_success "目錄創建完成"
}

# 檢查環境變數文件
check_env_file() {
    log_info "檢查環境變數文件..."
    
    if [[ ! -f ".env" ]]; then
        log_warning ".env 文件不存在，複製範本文件..."
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            log_warning "請編輯 .env 文件並設置正確的配置值"
            log_info "重點修改以下配置："
            log_info "- POSTGRES_PASSWORD"
            log_info "- REDIS_PASSWORD"
            log_info "- SECRET_KEY"
            log_info "- JWT_SECRET_KEY"
            log_info "- BOT_TOKENS"
            log_info "- TWILIO_ACCOUNT_SID (可選)"
            log_info "- TWILIO_AUTH_TOKEN (可選)"
        else
            log_error ".env.example 文件不存在"
            exit 1
        fi
    else
        log_success ".env 文件存在"
    fi
}

# 構建 Docker 鏡像
build_images() {
    log_info "構建 Docker 鏡像..."
    
    # 使用完整的 docker-compose 文件
    docker-compose -f docker-compose.complete.yml build --no-cache
    
    log_success "Docker 鏡像構建完成"
}

# 啟動服務
start_services() {
    log_info "啟動 BossJy-Pro 服務..."
    
    # 使用完整的 docker-compose 文件
    docker-compose -f docker-compose.complete.yml up -d
    
    log_success "服務啟動中..."
}

# 等待服務就緒
wait_for_services() {
    log_info "等待服務就緒..."
    
    # 等待數據庫
    log_info "等待 PostgreSQL..."
    until docker-compose -f docker-compose.complete.yml exec -T postgres pg_isready -U bossjy -d bossjy; do
        sleep 2
    done
    
    # 等待 Redis
    log_info "等待 Redis..."
    until docker-compose -f docker-compose.complete.yml exec -T redis redis-cli ping; do
        sleep 2
    done
    
    # 等待 FastAPI
    log_info "等待 FastAPI..."
    until curl -f http://localhost:18001/api/health >/dev/null 2>&1; do
        sleep 5
    done
    
    log_success "所有服務已就緒"
}

# 運行數據庫遷移
run_migrations() {
    log_info "運行數據庫遷移..."
    
    # 運行 Alembic 遷移
    docker-compose -f docker-compose.complete.yml exec -T fastapi alembic upgrade head
    
    log_success "數據庫遷移完成"
}

# 設置管理員用戶
setup_admin() {
    log_info "設置管理員用戶..."
    
    # 運行管理員設置腳本
    docker-compose -f docker-compose.complete.yml exec -T fastapi python setup_admin_user.py
    
    log_success "管理員用戶設置完成"
}

# 驗證部署
verify_deployment() {
    log_info "驗證部署..."
    
    # 檢查服務狀態
    docker-compose -f docker-compose.complete.yml ps
    
    # 檢查健康狀態
    log_info "檢查服務健康狀態..."
    
    # FastAPI
    if curl -f http://localhost:18001/api/health >/dev/null 2>&1; then
        log_success "✅ FastAPI (18001) - 正常"
    else
        log_error "❌ FastAPI (18001) - 異常"
    fi
    
    # Go API
    if curl -f http://localhost:8080/api/health >/dev/null 2>&1; then
        log_success "✅ Go API (8080) - 正常"
    else
        log_error "❌ Go API (8080) - 異常"
    fi
    
    # Vue Frontend
    if curl -f http://localhost:3000/health >/dev/null 2>&1; then
        log_success "✅ Vue Frontend (3000) - 正常"
    else
        log_error "❌ Vue Frontend (3000) - 異常"
    fi
    
    # Telegram Bots
    if curl -f http://localhost:9001/status >/dev/null 2>&1; then
        log_success "✅ Telegram Bots (9001) - 正常"
    else
        log_error "❌ Telegram Bots (9001) - 異常"
    fi
    
    # Grafana
    if curl -f http://localhost:3001/api/health >/dev/null 2>&1; then
        log_success "✅ Grafana (3001) - 正常"
    else
        log_error "❌ Grafana (3001) - 異常"
    fi
}

# 顯示部署信息
show_deployment_info() {
    log_success "🎉 BossJy-Pro 部署完成！"
    echo ""
    echo "=== 服務訪問地址 ==="
    echo "🌐 主站: https://bossjy.tiankai.it.com"
    echo "🤖 AppAI: https://appai.tiankai.it.com"
    echo "📊 監控面板: https://monitor.bossjy.tiankai.it.com"
    echo ""
    echo "=== 本地開發端口 ==="
    echo "🔧 FastAPI: http://localhost:18001"
    echo "🔧 Go API: http://localhost:8080"
    echo "🔧 Vue Frontend: http://localhost:3000"
    echo "🔧 Telegram Bots: http://localhost:9001"
    echo "🔧 Grafana: http://localhost:3001"
    echo "🔧 Prometheus: http://localhost:9090"
    echo "🔧 Kibana: http://localhost:5601"
    echo ""
    echo "=== 數據庫端口 ==="
    echo "🗄️ PostgreSQL: localhost:15432"
    echo "🗄️ Redis: localhost:16379"
    echo ""
    echo "=== API 文檔 ==="
    echo "📚 FastAPI 文檔: http://localhost:18001/docs"
    echo "📚 Go API 文檔: http://localhost:8080/docs"
    echo ""
    echo "=== 管理命令 ==="
    echo "🔄 重啟服務: docker-compose -f docker-compose.complete.yml restart"
    echo "📊 查看日誌: docker-compose -f docker-compose.complete.yml logs -f [service_name]"
    echo "🛑 停止服務: docker-compose -f docker-compose.complete.yml down"
    echo ""
    log_info "請確保域名指向正確的 IP 地址"
    log_info "如果是本地測試，請修改 hosts 文件添加域名映射"
}

# 主函數
main() {
    echo "🚀 BossJy-Pro 完整部署腳本"
    echo "==============================="
    echo ""
    
    # 檢查先決條件
    check_docker
    check_ssl_certificates
    check_env_file
    
    # 準備環境
    create_directories
    
    # 構建和部署
    build_images
    start_services
    
    # 等待服務就緒
    wait_for_services
    
    # 初始化
    run_migrations
    setup_admin
    
    # 驗證
    verify_deployment
    
    # 顯示信息
    show_deployment_info
}

# 處理中斷信號
trap 'log_warning "部署被中斷"; exit 1' INT TERM

# 執行主函數
main "$@"