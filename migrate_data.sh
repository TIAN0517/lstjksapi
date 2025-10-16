#!/bin/bash

# BossJy-Pro 数据迁移脚本
# 用于将数据从旧服务器迁移到新服务器

set -e

# 配置
OLD_SERVER=${OLD_SERVER:-"old-server.com"}
NEW_SERVER=${NEW_SERVER:-"new-server.com"}
SSH_USER=${SSH_USER:-"root"}
SSH_KEY=${SSH_KEY:-"~/.ssh/id_rsa"}

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}BossJy-Pro 数据迁移脚本${NC}"
echo -e "${GREEN}====================================${NC}"
echo

# 导出数据库
export_database() {
    echo -e "${YELLOW}导出数据库...${NC}"
    
    # 在旧服务器上执行
    ssh -i $SSH_KEY $SSH_USER@$OLD_SERVER << 'EOF'
        # 创建备份目录
        mkdir -p /tmp/bossjy_backup
        
        # 导出PostgreSQL数据库
        docker exec bossjy-postgres pg_dump -U jytian -d bossjy_huaqiao | gzip > /tmp/bossjy_backup/postgres_backup.sql.gz
        
        # 导出Redis数据
        docker exec bossjy-redis redis-cli --rdb /tmp/dump.rdb
        cp /var/lib/docker/volumes/bossjy_redis_data/_data/dump.rdb /tmp/bossjy_backup/
        
        # 打包数据文件
        tar -czf /tmp/bossjy_backup/data.tar.gz /opt/bossjy-pro/data/
        
        echo "数据库导出完成"
EOF
    
    echo -e "${GREEN}数据库导出完成${NC}"
}

# 传输数据
transfer_data() {
    echo -e "${YELLOW}传输数据到新服务器...${NC}"
    
    # 创建传输目录
    ssh -i $SSH_KEY $SSH_USER@$NEW_SERVER "mkdir -p /tmp/bossjy_migration"
    
    # 传输备份文件
    scp -i $SSH_KEY $SSH_USER@$OLD_SERVER:/tmp/bossjy_backup/* $SSH_USER@$NEW_SERVER:/tmp/bossjy_migration/
    
    echo -e "${GREEN}数据传输完成${NC}"
}

# 导入数据库
import_database() {
    echo -e "${YELLOW}导入数据库...${NC}"
    
    ssh -i $SSH_KEY $SSH_USER@$NEW_SERVER << EOF
        # 停止相关服务
        cd /opt/bossjy-pro
        docker-compose stop fastapi bots
        
        # 导入PostgreSQL数据
        gunzip -c /tmp/bossjy_migration/postgres_backup.sql.gz | docker exec -i bossjy-postgres psql -U jytian -d bossjy_huaqiao
        
        # 导入Redis数据
        docker cp /tmp/bossjy_migration/dump.rdb bossjy-redis:/data/
        docker restart bossjy-redis
        
        # 解压数据文件
        cd /opt/bossjy-pro
        tar -xzf /tmp/bossjy_migration/data.tar.gz -C . --strip-components=2
        
        # 重启服务
        docker-compose start fastapi bots
        
        echo "数据库导入完成"
EOF
    
    echo -e "${GREEN}数据库导入完成${NC}"
}

# 验证迁移
verify_migration() {
    echo -e "${YELLOW}验证迁移...${NC}"
    
    # 检查数据量
    ssh -i $SSH_KEY $SSH_USER@$NEW_SERVER << 'EOF'
        echo "检查PostgreSQL数据:"
        docker exec bossjy-postgres psql -U jytian -d bossjy_huaqiao -c "SELECT 'users' as table_name, COUNT(*) as count FROM users UNION ALL SELECT 'data_marketplace', COUNT(*) FROM data_marketplace;"
        
        echo "检查Redis数据:"
        docker exec bossjy-redis redis-cli -a ji394su3!! info keyspace
        
        echo "检查数据文件:"
        ls -la /opt/bossjy-pro/data/
EOF
    
    echo -e "${GREEN}迁移验证完成${NC}"
}

# 清理临时文件
cleanup() {
    echo -e "${YELLOW}清理临时文件...${NC}"
    
    ssh -i $SSH_KEY $SSH_USER@$OLD_SERVER "rm -rf /tmp/bossjy_backup"
    ssh -i $SSH_KEY $SSH_USER@$NEW_SERVER "rm -rf /tmp/bossjy_migration"
    
    echo -e "${GREEN}清理完成${NC}"
}

# 主函数
main() {
    echo "开始数据迁移..."
    echo "源服务器: $OLD_SERVER"
    echo "目标服务器: $NEW_SERVER"
    echo
    
    export_database
    transfer_data
    import_database
    verify_migration
    cleanup
    
    echo
    echo -e "${GREEN}====================================${NC}"
    echo -e "${GREEN}数据迁移完成！${NC}"
    echo -e "${GREEN}====================================${NC}"
}

# 执行主函数
main "$@"