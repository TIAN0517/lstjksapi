#!/bin/bash

# BossJy-Pro 服务器部署脚本
# 用于在新服务器上快速部署整个系统

set -e

# 配置参数
REGISTRY=${REGISTRY:-"your-registry.com"}
VERSION=${VERSION:-"latest"}
DOMAIN=${DOMAIN:-"your-domain.com"}
SSL_EMAIL=${SSL_EMAIL:-"admin@your-domain.com"}

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}====================================${NC}"
echo -e "${GREEN}BossJy-Pro 服务器部署脚本${NC}"
echo -e "${GREEN}====================================${NC}"
echo

# 检查系统要求
check_requirements() {
    echo -e "${YELLOW}检查系统要求...${NC}"
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}错误: Docker 未安装${NC}"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}错误: Docker Compose 未安装${NC}"
        exit 1
    fi
    
    # 检查端口占用
    ports=(80 443 3000 3001 8080 8081 9001 15432 16379 18001 9090)
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo -e "${RED}错误: 端口 $port 已被占用${NC}"
            exit 1
        fi
    done
    
    echo -e "${GREEN}系统要求检查通过${NC}"
}

# 安装Docker（如果需要）
install_docker() {
    if command -v docker &> /dev/null; then
        echo -e "${GREEN}Docker 已安装${NC}"
        return
    fi
    
    echo -e "${YELLOW}安装 Docker...${NC}"
    
    # Ubuntu/Debian
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    # CentOS/RHEL
    elif command -v yum &> /dev/null; then
        sudo yum install -y yum-utils
        sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    fi
    
    # 启动Docker服务
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # 添加用户到docker组
    sudo usermod -aG docker $USER
    
    echo -e "${GREEN}Docker 安装完成${NC}"
}

# 创建项目目录
setup_directories() {
    echo -e "${YELLOW}创建项目目录...${NC}"
    
    mkdir -p /opt/bossjy-pro/{data/{postgres,redis,prometheus,grafana},logs,backups,ssl}
    
    # 设置权限
    sudo chown -R $USER:$USER /opt/bossjy-pro
    
    echo -e "${GREEN}目录创建完成${NC}"
}

# 下载配置文件
download_configs() {
    echo -e "${YELLOW}下载配置文件...${NC}"
    
    cd /opt/bossjy-pro
    
    # 创建docker-compose.yml
    cat > docker-compose.yml << EOF
version: '3.8'

services:
  postgres:
    image: ${REGISTRY}/bossjy-cn-postgres:${VERSION}
    container_name: bossjy-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: bossjy_huaqiao
      POSTGRES_USER: jytian
      POSTGRES_PASSWORD: ji394su3
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
      - ./backups:/backups
    ports:
      - "15432:5432"
    networks:
      - bossjy-network

  redis:
    image: redis:7-alpine
    container_name: bossjy-redis
    restart: unless-stopped
    command: redis-server --requirepass ji394su3!! --appendonly yes
    volumes:
      - ./data/redis:/data
    ports:
      - "16379:6379"
    networks:
      - bossjy-network

  fastapi:
    image: ${REGISTRY}/bossjy-cn-fastapi:${VERSION}
    container_name: bossjy-fastapi
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql://jytian:ji394su3@postgres:5432/bossjy_huaqiao
      - REDIS_URL=redis://:ji394su3!!@redis:6379
    ports:
      - "18001:8000"
    depends_on:
      - postgres
      - redis
    networks:
      - bossjy-network

  go-api:
    image: ${REGISTRY}/bossjy-cn-go-api:${VERSION}
    container_name: bossjy-go-api
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql://jytian:ji394su3@postgres:5432/bossjy_huaqiao
    ports:
      - "8081:8080"
    depends_on:
      - postgres
    networks:
      - bossjy-network

  vue-frontend:
    image: ${REGISTRY}/bossjy-cn-vue-frontend:${VERSION}
    container_name: bossjy-vue-frontend
    restart: unless-stopped
    ports:
      - "8080:80"
    depends_on:
      - fastapi
    networks:
      - bossjy-network

  nginx:
    image: nginx:alpine
    container_name: bossjy-nginx
    restart: unless-stopped
    volumes:
      - ./ssl:/etc/nginx/ssl:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - vue-frontend
      - fastapi
    networks:
      - bossjy-network

  bots:
    image: ${REGISTRY}/bossjy-cn-bots:${VERSION}
    container_name: bossjy-bots
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql://jytian:ji394su3@postgres:5432/bossjy_huaqiao
      - REDIS_URL=redis://:ji394su3!!@redis:6379
    ports:
      - "9001:9001"
    depends_on:
      - postgres
    networks:
      - bossjy-network

networks:
  bossjy-network:
    driver: bridge
EOF

    # 创建环境变量文件
    cat > .env << EOF
REGISTRY=${REGISTRY}
VERSION=${VERSION}
DOMAIN=${DOMAIN}
SSL_EMAIL=${SSL_EMAIL}
POSTGRES_DB=bossjy_huaqiao
POSTGRES_USER=jytian
POSTGRES_PASSWORD=ji394su3
REDIS_PASSWORD=ji394su3!!
JWT_SECRET_KEY=$(openssl rand -hex 32)
EOF

    echo -e "${GREEN}配置文件创建完成${NC}"
}

# 配置SSL证书
setup_ssl() {
    echo -e "${YELLOW}配置SSL证书...${NC}"
    
    # 使用Let's Encrypt获取免费SSL证书
    if command -v certbot &> /dev/null; then
        sudo certbot certonly --standalone -d ${DOMAIN} --email ${SSL_EMAIL} --agree-tos --non-interactive
        sudo cp /etc/letsencrypt/live/${DOMAIN}/fullchain.pem ./ssl/
        sudo cp /etc/letsencrypt/live/${DOMAIN}/privkey.pem ./ssl/
        sudo chown $USER:$USER ./ssl/*.pem
    else
        echo -e "${YELLOW}警告: Certbot未安装，请手动配置SSL证书${NC}"
        echo -e "${YELLOW}将证书文件放置在 ./ssl/ 目录${NC}"
    fi
}

# 启动服务
start_services() {
    echo -e "${YELLOW}启动服务...${NC}"
    
    cd /opt/bossjy-pro
    
    # 拉取镜像
    docker-compose pull
    
    # 启动服务
    docker-compose up -d
    
    # 等待服务启动
    echo -e "${YELLOW}等待服务启动...${NC}"
    sleep 30
    
    # 检查服务状态
    docker-compose ps
    
    echo -e "${GREEN}服务启动完成${NC}"
}

# 导入数据
import_data() {
    echo -e "${YELLOW}导入数据...${NC}"
    
    # 如果有数据备份，恢复数据
    if [ -f "./backups/latest_backup.sql.gz" ]; then
        docker exec -i bossjy-postgres gunzip -c | psql -U jytian -d bossjy_huaqiao
        echo -e "${GREEN}数据恢复完成${NC}"
    else
        echo -e "${YELLOW}未找到数据备份${NC}"
    fi
}

# 验证部署
verify_deployment() {
    echo -e "${YELLOW}验证部署...${NC}"
    
    # 检查服务健康状态
    services=("fastapi:18001/api/health" "go-api:8081/api/health" "vue-frontend:8080")
    
    for service in "${services[@]}"; do
        IFS=':' read -r name port_path <<< "$service"
        if curl -f http://localhost:${port_path} &> /dev/null; then
            echo -e "${GREEN}✓ $name 服务正常${NC}"
        else
            echo -e "${RED}✗ $name 服务异常${NC}"
        fi
    done
    
    echo
    echo -e "${GREEN}====================================${NC}"
    echo -e "${GREEN}部署完成！${NC}"
    echo -e "${GREEN}====================================${NC}"
    echo
    echo "访问地址："
    echo "  前端: http://${DOMAIN}"
    echo "  API: http://${DOMAIN}/api"
    echo "  监控: http://${DOMAIN}:3001"
    echo
    echo "默认账户："
    echo "  管理员: admin@bossjy.com / admin123"
    echo "  Grafana: admin / ji394su3!!"
    echo
}

# 主函数
main() {
    check_requirements
    install_docker
    setup_directories
    download_configs
    setup_ssl
    start_services
    import_data
    verify_deployment
}

# 执行主函数
main "$@"