#!/bin/bash
################################################################################
# BossJy 系统监控脚本
# 监控所有服务的健康状态并发送告警
################################################################################

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 项目配置
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# 日志目录
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

# 告警配置
ALERT_LOG="$LOG_DIR/system_alerts.log"
HEALTH_LOG="$LOG_DIR/health_check.log"

# Bot管理器
BOT_MANAGER="$PROJECT_DIR/bot_manager.py"

# Telegram告警配置 (从环境变量读取)
TELEGRAM_BOT_TOKEN="${TELEGRAM_ALERT_BOT_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_ALERT_CHAT_ID:-}"

# 日志函数
log() {
    echo -e "$1" | tee -a "$HEALTH_LOG"
}

log_alert() {
    local message="$1"
    local level="${2:-INFO}"
    
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$level] $message" >> "$ALERT_LOG"
    
    # 发送Telegram告警
    if [[ -n "$TELEGRAM_BOT_TOKEN" && -n "$TELEGRAM_CHAT_ID" ]]; then
        send_telegram_alert "$message" "$level"
    fi
}

send_telegram_alert() {
    local message="$1"
    local level="$2"
    
    local emoji="ℹ️"
    case "$level" in
        WARN) emoji="⚠️" ;;
        ERROR) emoji="❌" ;;
        CRITICAL) emoji="🚨" ;;
    esac
    
    local full_message="$emoji [BossJy系统告警] $message"
    
    curl -s -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
        -d chat_id="$TELEGRAM_CHAT_ID" \
        -d text="$full_message" \
        -d parse_mode="Markdown" >/dev/null 2>&1 || true
}

# 检查系统资源
check_system_resources() {
    log "检查系统资源..."
    
    # CPU使用率
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    if (( $(echo "$cpu_usage > 85" | bc -l) )); then
        log_alert "CPU使用率过高: ${cpu_usage}%" "WARN"
    fi
    
    # 内存使用率
    local memory_usage=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
    if [ "$memory_usage" -gt 85 ]; then
        log_alert "内存使用率较高: ${memory_usage}%" "WARN"
    fi
    
    # 磁盘使用率
    local disk_usage=$(df "$PROJECT_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ "$disk_usage" -gt 90 ]; then
        log_alert "磁盘使用率过高: ${disk_usage}%" "ERROR"
    fi
    
    log "系统资源检查完成"
}

# 检查Bot状态
check_bot_status() {
    log "检查Bot状态..."
    
    # 获取Bot状态
    local status_output=$(python3 "$BOT_MANAGER" status 2>&1)
    
    # 检查是否有Bot失败
    if echo "$status_output" | grep -q "❌"; then
        local failed_bots=$(echo "$status_output" | grep "❌" | awk '{print $2}')
        log_alert "检测到Bot异常: $failed_bots" "ERROR"
        
        # 尝试自动重启
        log "尝试自动重启失败的Bot..."
        python3 "$BOT_MANAGER" restart --force >/dev/null 2>&1
    fi
    
    log "Bot状态检查完成"
}

# 检查网络连接
check_network() {
    log "检查网络连接..."
    
    # 检查外部连接
    if ! ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        log_alert "网络连接异常" "ERROR"
    fi
    
    # 检查数据库连接
    if ! python3 -c "import psycopg2; psycopg2.connect(
        host='${DB_HOST:-localhost}',
        port='${DB_PORT:-5432}',
        database='${DB_NAME:-bossjy}',
        user='${DB_USER:-bossjy}',
        password='${DB_PASSWORD:-ji394su3}'
    )" >/dev/null 2>&1; then
        log_alert "数据库连接失败" "ERROR"
    fi
    
    log "网络连接检查完成"
}

# 检查日志文件
check_logs() {
    log "检查日志文件..."
    
    # 检查错误日志
    local error_count=$(find "$LOG_DIR" -name "*.log" -exec grep -l "ERROR\|CRITICAL" {} \; | wc -l)
    if [ "$error_count" -gt 0 ]; then
        local recent_errors=$(find "$LOG_DIR" -name "*.log" -exec grep -h "ERROR\|CRITICAL" {} \; | tail -5)
        log_alert "检测到错误日志: $recent_errors" "WARN"
    fi
    
    log "日志文件检查完成"
}

# 执行完整健康检查
perform_health_check() {
    log ""
    log "========================================"
    log "BossJy 系统健康检查"
    log "时间: $(date)"
    log "========================================"
    
    check_system_resources
    check_bot_status
    check_network
    check_logs
    
    log "========================================"
    log "健康检查完成"
    log "========================================"
}

# 实时监控模式
monitor_mode() {
    log "启动实时监控模式..."
    
    trap 'echo -e "\n${YELLOW}监控已停止${NC}"; exit 0' INT
    
    while true; do
        perform_health_check
        sleep 300  # 每5分钟检查一次
    done
}

# 主函数
main() {
    local mode="check"
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -m|--monitor)
                mode="monitor"
                shift
                ;;
            -h|--help)
                echo "BossJy 系统监控脚本"
                echo ""
                echo "用法: $0 [选项]"
                echo ""
                echo "选项:"
                echo "  -m, --monitor    实时监控模式"
                echo "  -h, --help       显示此帮助信息"
                exit 0
                ;;
            *)
                echo "未知参数: $1"
                exit 1
                ;;
        esac
    done
    
    case "$mode" in
        check)
            perform_health_check
            ;;
        monitor)
            monitor_mode
            ;;
    esac
}

# 执行主函数
main "$@"