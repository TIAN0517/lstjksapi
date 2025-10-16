#!/bin/bash
# Nginx部署脚本
# 使用方法: chmod +x 2-deploy-nginx.sh && sudo ./2-deploy-nginx.sh

set -e

echo "================================"
echo "🚀 Nginx配置部署脚本"
echo "================================"
echo ""

# 项目根目录（修改为你的实际路径）
PROJECT_ROOT="/root/BossJy-Cn"

# 1. 创建必要目录
echo "📁 创建目录..."
mkdir -p /etc/nginx/snippets
mkdir -p /var/www/jytian-decoy
mkdir -p /var/www/jytian-honeypot
mkdir -p /var/www/tiankai-decoy
mkdir -p /var/www/tiankai-honeypot

# 2. 复制公共配置片段
echo "📝 复制公共配置..."
cp $PROJECT_ROOT/nginx/snippets/security-headers.conf /etc/nginx/snippets/
cp $PROJECT_ROOT/nginx/snippets/proxy-params.conf /etc/nginx/snippets/

# 3. 复制所有站点配置
echo "📝 复制站点配置..."
cp $PROJECT_ROOT/nginx/jytian-*.conf /etc/nginx/sites-available/
cp $PROJECT_ROOT/nginx/tiankai-*.conf /etc/nginx/sites-available/

# 4. 复制诱饵和蜜罐页面
echo "📝 复制静态页面..."
cp $PROJECT_ROOT/web/static/decoy.html /var/www/jytian-decoy/index.html
cp $PROJECT_ROOT/web/static/honeypot.html /var/www/jytian-honeypot/index.html
cp $PROJECT_ROOT/web/static/decoy.html /var/www/tiankai-decoy/index.html
cp $PROJECT_ROOT/web/static/honeypot.html /var/www/tiankai-honeypot/index.html

# 5. 启用所有站点
echo "🔗 启用站点..."
ln -sf /etc/nginx/sites-available/jytian-main.conf /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/jytian-api.conf /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/jytian-web.conf /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/jytian-admin.conf /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/jytian-honeypot.conf /etc/nginx/sites-enabled/
ln -sf /etc/nginx/sites-available/tiankai-api.conf /etc/nginx/sites-enabled/

# 6. 删除默认配置
echo "🗑️  删除默认配置..."
rm -f /etc/nginx/sites-enabled/default

# 7. 测试配置
echo ""
echo "🔍 测试Nginx配置..."
nginx -t

# 8. 重启Nginx
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 配置测试通过，重启Nginx..."
    systemctl restart nginx
    systemctl enable nginx
    systemctl status nginx --no-pager
else
    echo "❌ 配置错误，请检查"
    exit 1
fi

echo ""
echo "================================"
echo "✅ Nginx部署完成！"
echo "================================"
echo ""
echo "访问地址："
echo ""
echo "jytian.it.com："
echo "  主站（诱饵）:   https://jytian.it.com"
echo "  真实API:       https://api-v2.jytian.it.com:8443"
echo "  Web应用:       https://cdn.jytian.it.com"
echo "  管理后台:      https://admin-portal.jytian.it.com:9443"
echo "  蜜罐:          https://backup.jytian.it.com"
echo ""
echo "tiankai.it.com："
echo "  主站（诱饵）:   https://tiankai.it.com"
echo "  真实API:       https://gateway.tiankai.it.com:7443"
echo "  Web应用:       https://bossjy.tiankai.it.com"
echo "  管理后台:      https://console.tiankai.it.com:6443"
echo "  蜜罐:          https://monitor.tiankai.it.com"
echo ""
echo "⚠️  重要提醒："
echo "  1. 修改管理后台IP白名单 (jytian-admin.conf, tiankai-admin.conf)"
echo "  2. 配置防火墙: sudo ./3-setup-firewall.sh"
echo "  3. 开启Cloudflare代理"
echo ""
