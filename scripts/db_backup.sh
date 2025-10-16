#!/bin/bash
# ================================================
# BossJy数据库备份脚本
# 创建时间: 2025-10-10
# 用途: 自动备份PostgreSQL数据库
# ================================================

set -e

# 配置变量
BACKUP_DIR="./backups/database"
RETENTION_DAYS=30
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DATE_DIR=$(date +"%Y/%m")

# 数据库配置（从环境变量读取）
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-15432}"
DB_NAME="${POSTGRES_DB:-bossjy}"
DB_USER="${POSTGRES_USER:-bossjy}"
DB_PASSWORD="${POSTGRES_PASSWORD:-CHANGE_ME}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# 创建备份目录
create_backup_dir() {
    FULL_BACKUP_DIR="${BACKUP_DIR}/${DATE_DIR}"
    mkdir -p "${FULL_BACKUP_DIR}"
    log_info "Created backup directory: ${FULL_BACKUP_DIR}"
}

# 全量备份
full_backup() {
    local backup_file="${FULL_BACKUP_DIR}/bossjy_full_${TIMESTAMP}.sql.gz"
    log_info "Starting full database backup..."

    export PGPASSWORD="${DB_PASSWORD}"

    if pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
        --format=plain --no-owner --no-acl | gzip > "${backup_file}"; then

        local size=$(du -h "${backup_file}" | cut -f1)
        log_info "Full backup completed: ${backup_file} (${size})"
        echo "${backup_file}"
    else
        log_error "Full backup failed!"
        return 1
    fi

    unset PGPASSWORD
}

# 仅备份数据（不包括schema）
data_only_backup() {
    local backup_file="${FULL_BACKUP_DIR}/bossjy_data_${TIMESTAMP}.sql.gz"
    log_info "Starting data-only backup..."

    export PGPASSWORD="${DB_PASSWORD}"

    if pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
        --data-only --format=plain --no-owner --no-acl | gzip > "${backup_file}"; then

        local size=$(du -h "${backup_file}" | cut -f1)
        log_info "Data-only backup completed: ${backup_file} (${size})"
    else
        log_error "Data-only backup failed!"
    fi

    unset PGPASSWORD
}

# 仅备份schema
schema_backup() {
    local backup_file="${FULL_BACKUP_DIR}/bossjy_schema_${TIMESTAMP}.sql"
    log_info "Starting schema-only backup..."

    export PGPASSWORD="${DB_PASSWORD}"

    if pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
        --schema-only --format=plain --no-owner --no-acl > "${backup_file}"; then

        local size=$(du -h "${backup_file}" | cut -f1)
        log_info "Schema-only backup completed: ${backup_file} (${size})"
    else
        log_error "Schema-only backup failed!"
    fi

    unset PGPASSWORD
}

# 自定义格式备份（支持并行恢复）
custom_format_backup() {
    local backup_file="${FULL_BACKUP_DIR}/bossjy_custom_${TIMESTAMP}.dump"
    log_info "Starting custom format backup..."

    export PGPASSWORD="${DB_PASSWORD}"

    if pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
        --format=custom --compress=9 --file="${backup_file}"; then

        local size=$(du -h "${backup_file}" | cut -f1)
        log_info "Custom format backup completed: ${backup_file} (${size})"
    else
        log_error "Custom format backup failed!"
    fi

    unset PGPASSWORD
}

# 备份指定表
backup_tables() {
    local tables=("users" "transactions" "jobs" "api_keys" "audit_logs")
    local backup_file="${FULL_BACKUP_DIR}/bossjy_tables_${TIMESTAMP}.sql.gz"

    log_info "Starting table-specific backup..."

    export PGPASSWORD="${DB_PASSWORD}"

    local table_args=""
    for table in "${tables[@]}"; do
        table_args="${table_args} -t ${table}"
    done

    if pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" \
        ${table_args} --format=plain --no-owner --no-acl | gzip > "${backup_file}"; then

        local size=$(du -h "${backup_file}" | cut -f1)
        log_info "Table backup completed: ${backup_file} (${size})"
    else
        log_error "Table backup failed!"
    fi

    unset PGPASSWORD
}

# 验证备份文件
verify_backup() {
    local backup_file=$1

    if [ ! -f "${backup_file}" ]; then
        log_error "Backup file not found: ${backup_file}"
        return 1
    fi

    local size=$(stat -f%z "${backup_file}" 2>/dev/null || stat -c%s "${backup_file}" 2>/dev/null)

    if [ "${size}" -lt 1000 ]; then
        log_error "Backup file is too small (${size} bytes), possibly corrupted"
        return 1
    fi

    # 验证gzip文件完整性
    if [[ "${backup_file}" == *.gz ]]; then
        if gzip -t "${backup_file}" 2>/dev/null; then
            log_info "Backup file integrity verified: ${backup_file}"
            return 0
        else
            log_error "Backup file is corrupted: ${backup_file}"
            return 1
        fi
    fi

    log_info "Backup file verified: ${backup_file}"
    return 0
}

# 清理旧备份
cleanup_old_backups() {
    log_info "Cleaning up backups older than ${RETENTION_DAYS} days..."

    find "${BACKUP_DIR}" -type f -name "*.sql.gz" -mtime +${RETENTION_DAYS} -delete
    find "${BACKUP_DIR}" -type f -name "*.sql" -mtime +${RETENTION_DAYS} -delete
    find "${BACKUP_DIR}" -type f -name "*.dump" -mtime +${RETENTION_DAYS} -delete

    # 删除空目录
    find "${BACKUP_DIR}" -type d -empty -delete

    log_info "Cleanup completed"
}

# 生成备份报告
generate_report() {
    local backup_file=$1
    local report_file="${FULL_BACKUP_DIR}/backup_report_${TIMESTAMP}.txt"

    cat > "${report_file}" << EOF
========================================
BossJy Database Backup Report
========================================
Timestamp: $(date '+%Y-%m-%d %H:%M:%S')
Database: ${DB_NAME}
Host: ${DB_HOST}:${DB_PORT}

Backup File: ${backup_file}
File Size: $(du -h "${backup_file}" | cut -f1)

Database Statistics:
----------------------------------------
EOF

    export PGPASSWORD="${DB_PASSWORD}"

    psql -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" -d "${DB_NAME}" -t -c "
        SELECT
            'Total Users: ' || COUNT(*) FROM users
        UNION ALL
        SELECT
            'Total Transactions: ' || COUNT(*) FROM transactions
        UNION ALL
        SELECT
            'Total Jobs: ' || COUNT(*) FROM jobs
        UNION ALL
        SELECT
            'Database Size: ' || pg_size_pretty(pg_database_size('${DB_NAME}'))
    " >> "${report_file}"

    unset PGPASSWORD

    log_info "Backup report generated: ${report_file}"
}

# 上传到云存储（可选）
upload_to_cloud() {
    local backup_file=$1

    # 示例：上传到S3（需要配置AWS CLI）
    # aws s3 cp "${backup_file}" "s3://your-bucket/backups/$(basename ${backup_file})"

    # 示例：上传到Google Cloud Storage
    # gsutil cp "${backup_file}" "gs://your-bucket/backups/$(basename ${backup_file})"

    log_warn "Cloud upload not configured. Skipping..."
}

# 主函数
main() {
    log_info "================================================"
    log_info "Starting BossJy Database Backup"
    log_info "================================================"

    # 检查pg_dump是否可用
    if ! command -v pg_dump &> /dev/null; then
        log_error "pg_dump not found. Please install PostgreSQL client tools."
        exit 1
    fi

    # 创建备份目录
    create_backup_dir

    # 执行备份（根据参数选择备份类型）
    case "${1:-full}" in
        full)
            backup_file=$(full_backup)
            ;;
        data)
            backup_file=$(data_only_backup)
            ;;
        schema)
            backup_file=$(schema_backup)
            ;;
        custom)
            backup_file=$(custom_format_backup)
            ;;
        tables)
            backup_file=$(backup_tables)
            ;;
        all)
            full_backup
            data_only_backup
            schema_backup
            custom_format_backup
            ;;
        *)
            log_error "Unknown backup type: $1"
            log_info "Usage: $0 {full|data|schema|custom|tables|all}"
            exit 1
            ;;
    esac

    # 验证备份
    if [ -n "${backup_file}" ]; then
        if verify_backup "${backup_file}"; then
            generate_report "${backup_file}"
            # upload_to_cloud "${backup_file}"
        else
            log_error "Backup verification failed!"
            exit 1
        fi
    fi

    # 清理旧备份
    cleanup_old_backups

    log_info "================================================"
    log_info "Backup completed successfully!"
    log_info "================================================"
}

# 执行主函数
main "$@"
