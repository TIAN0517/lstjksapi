#!/bin/bash
# BossJy-Pro 生产环境部署脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
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

# 检查Docker和Docker Compose
check_dependencies() {
    log_info "检查依赖..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装"
        exit 1
    fi
    
    log_success "依赖检查通过"
}

# 创建环境变量文件
create_env_file() {
    log_info "创建环境变量文件..."
    
    if [ ! -f .env.production ]; then
        cat > .env.production << 'ENVEOF'
# BossJy-Pro 生产环境配置

# 数据库配置
POSTGRES_PASSWORD=ji394su3!!
REDIS_PASSWORD=ji394su3!!

# JWT配置
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production

# Grafana配置
GRAFANA_PASSWORD=ji394su3!!

# 其他配置
ENVIRONMENT=production
LOG_LEVEL=INFO
ENVEOF
        log_success "环境变量文件已创建"
    else
        log_warning "环境变量文件已存在，跳过创建"
    fi
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    
    mkdir -p logs
    mkdir -p data/uploads
    mkdir -p data/processed
    mkdir -p data/exports
    mkdir -p monitoring/logs
    mkdir -p deploy/nginx/ssl
    
    log_success "目录创建完成"
}

# 生成SSL证书
generate_ssl_certs() {
    log_info "生成SSL证书..."
    
    if [ ! -f deploy/nginx/ssl/cert.pem ]; then
        openssl req -x509 -newkey rsa:4096 -keyout deploy/nginx/ssl/key.pem -out deploy/nginx/ssl/cert.pem -days 365 -nodes -subj "/C=CN/ST=Beijing/L=Beijing/O=BossJy/OU=IT/CN=bossjy.com"
        log_success "SSL证书已生成"
    else
        log_warning "SSL证书已存在，跳过生成"
    fi
}

# 构建Docker镜像
build_images() {
    log_info "构建Docker镜像..."
    
    # 构建FastAPI镜像
    log_info "构建FastAPI镜像..."
    docker build -f services/fastapi/Dockerfile.production -t bossjy-fastapi:latest .
    
    # 构建Go API镜像
    log_info "构建Go API镜像..."
    docker build -f services/go-api/Dockerfile -t bossjy-go-api:latest .
    
    # 构建Vue前端镜像
    log_info "构建Vue前端镜像..."
    docker build -f services/vue-frontend/Dockerfile -t bossjy-frontend:latest .
    
    log_success "Docker镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 使用生产环境配置启动服务
    docker-compose -f docker-compose.production.yml --env-file .env.production up -d
    
    log_success "服务启动完成"
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务就绪..."
    
    # 等待数据库
    log_info "等待数据库启动..."
    timeout 60 bash -c 'until docker exec bossjy-postgres-prod pg_isready -U jytian -d bossjy_huaqiao; do sleep 2; done'
    
    # 等待Redis
    log_info "等待Redis启动..."
    timeout 30 bash -c 'until docker exec bossjy-redis-prod redis-cli ping; do sleep 2; done'
    
    # 等待FastAPI
    log_info "等待FastAPI启动..."
    timeout 60 bash -c 'until curl -f http://localhost:18001/api/health; do sleep 2; done'
    
    # 等待Go API
    log_info "等待Go API启动..."
    timeout 30 bash -c 'until curl -f http://localhost:18080/health; do sleep 2; done'
    
    # 等待前端
    log_info "等待前端启动..."
    timeout 30 bash -c 'until curl -f http://localhost:9001; do sleep 2; done'
    
    log_success "所有服务已就绪"
}

# 运行健康检查
health_check() {
    log_info "运行健康检查..."
    
    # 检查FastAPI
    if curl -f http://localhost:18001/api/health > /dev/null 2>&1; then
        log_success "FastAPI 健康检查通过"
    else
        log_error "FastAPI 健康检查失败"
        return 1
    fi
    
    # 检查Go API
    if curl -f http://localhost:18080/health > /dev/null 2>&1; then
        log_success "Go API 健康检查通过"
    else
        log_error "Go API 健康检查失败"
        return 1
    fi
    
    # 检查前端
    if curl -f http://localhost:9001 > /dev/null 2>&1; then
        log_success "前端 健康检查通过"
    else
        log_error "前端 健康检查失败"
        return 1
    fi
    
    # 检查Grafana
    if curl -f http://localhost:3001 > /dev/null 2>&1; then
        log_success "Grafana 健康检查通过"
    else
        log_error "Grafana 健康检查失败"
        return 1
    fi
    
    log_success "所有健康检查通过"
}

# 显示服务信息
show_service_info() {
    log_info "服务信息："
    echo ""
    echo "🌐 前端访问地址: http://localhost:9001"
    echo "🔧 API访问地址: http://localhost:18001"
    echo "📊 监控面板: http://localhost:3001 (admin / ji394su3!!)"
    echo "📈 Prometheus: http://localhost:9090"
    echo ""
    echo "📋 服务状态："
    docker-compose -f docker-compose.production.yml ps
    echo ""
    echo "📊 资源使用："
    docker stats --no-stream
}

# 主函数
main() {
    log_info "开始部署 BossJy-Pro 生产环境..."
    echo ""
    
    check_dependencies
    create_env_file
    create_directories
    generate_ssl_certs
    build_images
    start_services
    wait_for_services
    health_check
    show_service_info
    
    echo ""
    log_success "🎉 BossJy-Pro 生产环境部署完成！"
    echo ""
    log_info "下一步："
    echo "1. 访问 http://localhost:9001 查看前端"
    echo "2. 访问 http://localhost:3001 查看监控面板"
    echo "3. 运行 'docker-compose -f docker-compose.production.yml logs -f' 查看日志"
    echo "4. 运行 'docker-compose -f docker-compose.production.yml down' 停止服务"
}

# 错误处理
trap 'log_error "部署过程中发生错误，请检查日志"; exit 1' ERR

# 运行主函数
main "$@"
