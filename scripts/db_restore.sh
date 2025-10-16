#!/bin/bash
# ================================================
# BossJy数据库恢复脚本
# 创建时间: 2025-10-10
# 用途: 从备份恢复PostgreSQL数据库
# ================================================

set -e

# 数据库配置
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-15432}"
DB_NAME="${POSTGRES_DB:-bossjy}"
DB_USER="${POSTGRES_USER:-bossjy}"
DB_PASSWORD="${POSTGRES_PASSWORD:-CHANGE_ME}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 确认操作
confirm_restore() {
    log_warn "================================================"
    log_warn "WARNING: This will REPLACE the current database!"
    log_warn "Database: ${DB_NAME}"
    log_warn "Host: ${DB_HOST}:${DB_PORT}"
    log_warn "Backup file: $1"
    log_warn "================================================"

    read -p "Are you sure you want to continue? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        log_info "Restore cancelled by user"
        exit 0
    fi
}

# 备份当前数据库（安全措施）
backup_current_db() {
    local safety_backup="./backups/pre_restore_${DB_NAME}_$(date +%Y%m%d_%H%M%S).sql.gz"

    log_info "Creating safety backup of current database..."

    export PGPASSWORD="${DB_PASSWORD}"

    if pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
        --format=plain --no-owner --no-acl | gzip > "${safety_backup}"; then
        log_info "Safety backup created: ${safety_backup}"
    else
        log_error "Failed to create safety backup!"
        exit 1
    fi

    unset PGPASSWORD
}

# 恢复数据库
restore_database() {
    local backup_file=$1

    if [ ! -f "${backup_file}" ]; then
        log_error "Backup file not found: ${backup_file}"
        exit 1
    fi

    log_info "Starting database restore from: ${backup_file}"

    export PGPASSWORD="${DB_PASSWORD}"

    # 检查文件类型
    if [[ "${backup_file}" == *.gz ]]; then
        # gzip压缩的SQL文件
        if gunzip -c "${backup_file}" | psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}"; then
            log_info "Database restored successfully from gzip file"
        else
            log_error "Failed to restore from gzip file!"
            exit 1
        fi
    elif [[ "${backup_file}" == *.dump ]]; then
        # 自定义格式的备份文件
        if pg_restore -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
            --clean --if-exists --no-owner --no-acl "${backup_file}"; then
            log_info "Database restored successfully from custom format"
        else
            log_error "Failed to restore from custom format!"
            exit 1
        fi
    elif [[ "${backup_file}" == *.sql ]]; then
        # 普通SQL文件
        if psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" < "${backup_file}"; then
            log_info "Database restored successfully from SQL file"
        else
            log_error "Failed to restore from SQL file!"
            exit 1
        fi
    else
        log_error "Unknown backup file format: ${backup_file}"
        exit 1
    fi

    unset PGPASSWORD
}

# 验证恢复结果
verify_restore() {
    log_info "Verifying database restore..."

    export PGPASSWORD="${DB_PASSWORD}"

    # 检查表是否存在
    local tables=$(psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -t -c "
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_schema = 'public'
    ")

    if [ "$tables" -gt 0 ]; then
        log_info "Database verification successful. Found ${tables} tables."

        # 显示表记录数
        psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -c "
            SELECT
                'users' as table_name, COUNT(*) as records FROM users
            UNION ALL
            SELECT 'transactions', COUNT(*) FROM transactions
            UNION ALL
            SELECT 'jobs', COUNT(*) FROM jobs
            UNION ALL
            SELECT 'api_keys', COUNT(*) FROM api_keys
            UNION ALL
            SELECT 'audit_logs', COUNT(*) FROM audit_logs
        "
    else
        log_error "Database verification failed. No tables found!"
        exit 1
    fi

    unset PGPASSWORD
}

# 主函数
main() {
    if [ -z "$1" ]; then
        log_error "Usage: $0 <backup_file>"
        log_info "Example: $0 ./backups/database/2025/10/bossjy_full_20251010_120000.sql.gz"
        exit 1
    fi

    local backup_file=$1

    log_info "================================================"
    log_info "Starting BossJy Database Restore"
    log_info "================================================"

    # 确认操作
    confirm_restore "${backup_file}"

    # 创建安全备份
    backup_current_db

    # 执行恢复
    restore_database "${backup_file}"

    # 验证恢复
    verify_restore

    log_info "================================================"
    log_info "Database restore completed successfully!"
    log_info "================================================"
}

# 执行主函数
main "$@"
