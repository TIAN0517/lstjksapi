#!/bin/bash
# BossJy-Pro 資料庫備份與還原腳本
# 使用方法: ./backup_restore.sh [backup|restore] [options]

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_ROOT/deploy/backups"
CONTAINER_NAME="bossjy-postgres"
POSTGRES_USER="${POSTGRES_USER:-bossjy}"
POSTGRES_DB="${POSTGRES_DB:-bossjy}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/bossjy_backup_$TIMESTAMP.sql.gz"

# S3 配置 (可選)
S3_ENABLED="${S3_ENABLED:-false}"
S3_BUCKET="${S3_BUCKET:-bossjy-backups}"
S3_ENDPOINT="${S3_ENDPOINT:-}"
S3_ACCESS_KEY="${S3_ACCESS_KEY:-}"
S3_SECRET_KEY="${S3_SECRET_KEY:-}"

# 創建備份目錄
mkdir -p "$BACKUP_DIR"

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

# 檢查 Docker 容器是否運行
check_container() {
    if ! docker ps | grep -q "$CONTAINER_NAME"; then
        log_error "容器 $CONTAINER_NAME 未運行"
        exit 1
    fi
}

# 備份函數
backup_database() {
    log_info "開始備份資料庫..."
    
    check_container
    
    # 創建備份
    log_info "創建資料庫備份: $BACKUP_FILE"
    docker exec "$CONTAINER_NAME" pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc -Z 9 -f "/tmp/backup_$TIMESTAMP.dump"
    
    # 複製備份檔案到主機
    docker cp "$CONTAINER_NAME:/tmp/backup_$TIMESTAMP.dump" "$BACKUP_FILE"
    
    # 清理容器中的臨時檔案
    docker exec "$CONTAINER_NAME" rm -f "/tmp/backup_$TIMESTAMP.dump"
    
    log_success "資料庫備份完成: $BACKUP_FILE"
    
    # 檢查檔案大小
    local file_size=$(du -h "$BACKUP_FILE" | cut -f1)
    log_info "備份檔案大小: $file_size"
    
    # S3 上傳 (如果啟用)
    if [ "$S3_ENABLED" = "true" ]; then
        upload_to_s3
    fi
    
    # 清理舊備份 (保留最近 7 份)
    cleanup_old_backups
}

# 上傳到 S3
upload_to_s3() {
    log_info "上傳備份到 S3..."
    
    if command -v aws &> /dev/null; then
        # 使用 AWS CLI
        AWS_ARGS=""
        if [ -n "$S3_ENDPOINT" ]; then
            AWS_ARGS="--endpoint-url $S3_ENDPOINT"
        fi
        
        export AWS_ACCESS_KEY_ID="$S3_ACCESS_KEY"
        export AWS_SECRET_ACCESS_KEY="$S3_SECRET_KEY"
        
        aws s3 $AWS_ARGS cp "$BACKUP_FILE" "s3://$S3_BUCKET/database/"
        log_success "備份已上傳到 S3"
    else
        log_warning "AWS CLI 未安裝，跳過 S3 上傳"
    fi
}

# 清理舊備份
cleanup_old_backups() {
    log_info "清理舊備份檔案..."
    
    local backup_count=$(ls -1 "$BACKUP_DIR"/bossjy_backup_*.sql.gz 2>/dev/null | wc -l)
    
    if [ "$backup_count" -gt 7 ]; then
        ls -1t "$BACKUP_DIR"/bossjy_backup_*.sql.gz | tail -n +8 | xargs rm -f
        log_success "已清理舊備份檔案"
    fi
}

# 還原函數
restore_database() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ]; then
        log_error "請指定備份檔案"
        log_info "可用備份檔案:"
        ls -la "$BACKUP_DIR"/bossjy_backup_*.sql.gz 2>/dev/null || log_warning "沒有找到備份檔案"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        log_error "備份檔案不存在: $backup_file"
        exit 1
    fi
    
    log_warning "⚠️  還原操作將覆蓋現有資料庫！"
    read -p "確認繼續？(y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "操作已取消"
        exit 0
    fi
    
    check_container
    
    log_info "開始還原資料庫..."
    
    # 複製備份檔案到容器
    local container_backup="/tmp/restore_$(date +%s).dump"
    docker cp "$backup_file" "$CONTAINER_NAME:$container_backup"
    
    # 停止應用服務以避免衝突
    log_info "停止應用服務..."
    docker-compose stop fastapi go-api bots
    
    # 還原資料庫
    log_info "執行資料庫還原..."
    docker exec "$CONTAINER_NAME" dropdb -U "$POSTGRES_USER" "$POSTGRES_DB" || true
    docker exec "$CONTAINER_NAME" createdb -U "$POSTGRES_USER" "$POSTGRES_DB"
    docker exec "$CONTAINER_NAME" pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists -v "$container_backup"
    
    # 清理容器中的臨時檔案
    docker exec "$CONTAINER_NAME" rm -f "$container_backup"
    
    # 重啟應用服務
    log_info "重啟應用服務..."
    docker-compose start fastapi go-api bots
    
    log_success "資料庫還原完成"
}

# 列出備份
list_backups() {
    log_info "可用備份檔案:"
    ls -lah "$BACKUP_DIR"/bossjy_backup_*.sql.gz 2>/dev/null || log_warning "沒有找到備份檔案"
}

# 顯示幫助
show_help() {
    echo "BossJy-Pro 資料庫備份與還原工具"
    echo ""
    echo "使用方法:"
    echo "  $0 backup                    備份資料庫"
    echo "  $0 restore <backup_file>     從備份檔案還原"
    echo "  $0 list                      列出可用備份"
    echo "  $0 help                      顯示此幫助"
    echo ""
    echo "環境變數:"
    echo "  POSTGRES_USER    PostgreSQL 用戶名 (默認: bossjy)"
    echo "  POSTGRES_DB      PostgreSQL 資料庫名 (默認: bossjy)"
    echo "  S3_ENABLED       啟用 S3 上傳 (默認: false)"
    echo "  S3_BUCKET        S3 存儲桶名稱"
    echo "  S3_ENDPOINT      S3 端點 URL"
    echo "  S3_ACCESS_KEY    S3 訪問密鑰"
    echo "  S3_SECRET_KEY    S3 密鑰"
}

# 主函數
main() {
    case "${1:-}" in
        "backup")
            backup_database
            ;;
        "restore")
            restore_database "$2"
            ;;
        "list")
            list_backups
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "未知命令: ${1:-}"
            show_help
            exit 1
            ;;
    esac
}

# 執行主函數
main "$@"