#!/bin/bash
# BossJy 数据库备份脚本
set -e

BACKUP_DIR="/backups"
DB_HOST="bossjy-postgres"
DB_PORT="5432"
DB_NAME="bossjy_huaqiao"
DB_USER="jytian"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/bossjy_backup_${DATE}.sql.gz"
RETENTION_DAYS=30

mkdir -p ${BACKUP_DIR}
echo "Starting backup at $(date)"

PGPASSWORD=${PGPASSWORD} pg_dump -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} | gzip > ${BACKUP_FILE}

if [ $? -eq 0 ]; then
    echo "Backup completed: ${BACKUP_FILE}"
    du -h ${BACKUP_FILE}
else
    echo "Backup failed!"
    exit 1
fi

find ${BACKUP_DIR} -name "bossjy_backup_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete
echo "Backup completed at $(date)"
