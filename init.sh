#!/bin/bash
set -e

echo "🚀 智能过滤系统初始化脚本"
echo "================================"

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
  echo "请使用 sudo 运行此脚本"
  exit 1
fi

# 更新系统
echo "📦 更新系统包..."
apt update && apt upgrade -y

# 安装基础工具
echo "🔧 安装基础工具..."
apt install -y curl git wget build-essential ufw software-properties-common

# 安装Docker
echo "🐳 安装Docker..."
if ! command -v docker &> /dev/null; then
  curl -fsSL https://get.docker.com | sh
  usermod -aG docker $USER
  systemctl enable docker
  systemctl start docker
  echo "✅ Docker 安装完成"
else
  echo "✅ Docker 已安装"
fi

# 安装Docker Compose
echo "🔧 安装Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
  curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  chmod +x /usr/local/bin/docker-compose
  echo "✅ Docker Compose 安装完成"
else
  echo "✅ Docker Compose 已安装"
fi

# 安装Node.js (用于本地开发)
echo "📦 安装Node.js..."
if ! command -v node &> /dev/null; then
  curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
  apt install -y nodejs
  echo "✅ Node.js 安装完成"
else
  echo "✅ Node.js 已安装"
fi

# 安装Go (用于本地开发)
echo "🔷 安装Go..."
if ! command -v go &> /dev/null; then
  GO_VERSION="1.21.0"
  wget https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz
  rm -rf /usr/local/go
  tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz
  echo 'export PATH=$PATH:/usr/local/go/bin' >> /etc/profile
  echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
  source ~/.bashrc
  echo "✅ Go 安装完成"
else
  echo "✅ Go 已安装"
fi

# 配置防火墙
echo "🔥 配置防火墙..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8080/tcp
ufw allow 18001/tcp
ufw --force enable
echo "✅ 防火墙配置完成"

# 创建必要的目录
echo "📁 创建项目目录..."
mkdir -p deployment/ssl
mkdir -p logs
mkdir -p data/mysql
mkdir -p data/redis
echo "✅ 目录创建完成"

# 生成自签名SSL证书 (可选)
echo "🔐 生成SSL证书..."
if [ ! -f deployment/ssl/cert.pem ]; then
  openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout deployment/ssl/key.pem \
    -out deployment/ssl/cert.pem \
    -subj "/C=CN/ST=State/L=City/O=Organization/CN=localhost"
  echo "✅ SSL证书生成完成"
else
  echo "✅ SSL证书已存在"
fi

# 设置文件权限
echo "🔒 设置文件权限..."
chmod +x init.sh
chmod -R 755 deployment/
chmod -R 755 filter-system/
chmod -R 755 src/
echo "✅ 权限设置完成"

# 创建环境变量文件
echo "📝 创建环境变量文件..."
if [ ! -f .env ]; then
  cat > .env << EOF
# 数据库配置
MYSQL_ROOT_PASSWORD=your_password
MYSQL_DATABASE=filter_system
MYSQL_USER=filter_user
MYSQL_PASSWORD=filter_pass

# JWT配置
JWT_SECRET=your_jwt_secret_key_change_in_production

# 应用配置
APP_ENV=production
APP_PORT=8080
EOF
  echo "✅ 环境变量文件创建完成"
else
  echo "✅ 环境变量文件已存在"
fi

echo ""
echo "🎉 初始化完成！"
echo "================================"
echo ""
echo "📋 下一步操作："
echo "1. 编辑 .env 文件设置你的配置"
echo "2. 运行 'docker-compose up -d --build' 启动服务"
echo "3. 访问 http://localhost 查看前端"
echo "4. 访问 http://localhost:8080/health 检查后端"
echo ""
echo "🔑 默认管理员账号："
echo "用户名: admin"
echo "密码: admin123"
echo ""
echo "📚 更多信息请查看 README.md"
