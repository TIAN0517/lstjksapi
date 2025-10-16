#!/bin/bash
# SSL证书申请脚本
# 使用方法: chmod +x 1-install-ssl.sh && sudo ./1-install-ssl.sh

set -e  # 遇到错误立即停止

echo "================================"
echo "🔐 SSL证书申请脚本"
echo "================================"
echo ""

# 1. 安装Certbot
echo "📦 安装Certbot..."
apt update
apt install certbot python3-certbot-nginx -y

# 2. 停止Nginx（避免80端口冲突）
echo "⏸️  暂停Nginx..."
systemctl stop nginx || true

# 3. 申请jytian.it.com证书（包含所有子域名）
echo ""
echo "🔐 申请 jytian.it.com SSL证书..."
certbot certonly --standalone \
  -d jytian.it.com \
  -d www.jytian.it.com \
  -d api-v2.jytian.it.com \
  -d cdn.jytian.it.com \
  -d admin-portal.jytian.it.com \
  -d static.jytian.it.com \
  -d backup.jytian.it.com \
  --email admin@jytian.it.com \
  --agree-tos \
  --non-interactive \
  --staple-ocsp

echo "✅ jytian.it.com 证书申请成功！"

# 4. 申请tiankai.it.com证书（包含所有子域名）
echo ""
echo "🔐 申请 tiankai.it.com SSL证书..."
certbot certonly --standalone \
  -d tiankai.it.com \
  -d www.tiankai.it.com \
  -d gateway.tiankai.it.com \
  -d bossjy.tiankai.it.com \
  -d console.tiankai.it.com \
  -d assets.tiankai.it.com \
  -d monitor.tiankai.it.com \
  --email admin@tiankai.it.com \
  --agree-tos \
  --non-interactive \
  --staple-ocsp

echo "✅ tiankai.it.com 证书申请成功！"

# 5. 验证证书
echo ""
echo "🔍 验证证书..."
ls -la /etc/letsencrypt/live/jytian.it.com/
ls -la /etc/letsencrypt/live/tiankai.it.com/

# 6. 设置自动续期
echo ""
echo "⏰ 配置自动续期..."
cat > /etc/cron.d/certbot-renew << 'EOF'
0 0,12 * * * root certbot renew --quiet --post-hook "systemctl reload nginx"
EOF

echo "✅ 自动续期已配置（每天0点和12点检查）"

# 7. 测试续期
echo ""
echo "🧪 测试自动续期..."
certbot renew --dry-run

echo ""
echo "================================"
echo "✅ SSL证书申请完成！"
echo "================================"
echo ""
echo "证书位置："
echo "  jytian.it.com:  /etc/letsencrypt/live/jytian.it.com/"
echo "  tiankai.it.com: /etc/letsencrypt/live/tiankai.it.com/"
echo ""
echo "下一步："
echo "  1. 运行: sudo ./2-deploy-nginx.sh"
echo "  2. 配置Cloudflare代理"
echo ""
