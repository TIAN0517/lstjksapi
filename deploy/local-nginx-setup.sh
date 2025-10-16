#!/bin/bash
# 本地Nginx配置（WSL）
# 不需要SSL，由Cloudflare处理

set -e

echo "================================"
echo "🚀 本地Nginx配置（WSL）"
echo "================================"
echo ""

PROJECT_ROOT="/mnt/d/BossJy-Cn/BossJy-Cn"

# 1. 安装Nginx
echo "📦 安装Nginx..."
apt update
apt install -y nginx

# 2. 创建简单的Nginx配置（HTTP only）
echo ""
echo "📝 创建Nginx配置..."

cat > /etc/nginx/sites-available/bossjy-local << 'EOF'
# 本地Nginx配置（所有流量来自Cloudflare Tunnel）

server {
    listen 5000;
    server_name _;

    # 日志
    access_log /var/log/nginx/bossjy-access.log;
    error_log /var/log/nginx/bossjy-error.log;

    # Flask应用
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }
}

# 管理后台
server {
    listen 5001;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

# 蜜罐
server {
    listen 5002;
    server_name _;

    root /var/www/honeypot;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }
}
EOF

# 3. 启用配置
ln -sf /etc/nginx/sites-available/bossjy-local /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 4. 测试配置
nginx -t

# 5. 重启Nginx
systemctl restart nginx
systemctl enable nginx

echo ""
echo "================================"
echo "✅ Nginx配置完成！"
echo "================================"
echo ""
echo "监听端口:"
echo "  5000 - 主应用"
echo "  5001 - 管理后台"
echo "  5002 - 蜜罐"
echo ""
echo "下一步:"
echo "  1. 启动Flask应用: gunicorn -w 4 -b 127.0.0.1:8000 app.web_app:app"
echo "  2. 启动Cloudflare Tunnel: sudo systemctl start cloudflared"
echo ""
