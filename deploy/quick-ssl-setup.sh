#!/bin/bash
# 快速SSL设置（Cloudflare DNS验证）
# Token: D1GwtcDBMGCRvoIoLb0IIe_8vdxJfoqiMoM0ZCbp

set -e

echo "================================"
echo "🔐 快速SSL证书申请"
echo "================================"
echo ""

# 1. 安装Certbot Cloudflare插件
echo "📦 安装Certbot Cloudflare插件..."
apt update
apt install certbot python3-certbot-dns-cloudflare -y

# 2. 创建Cloudflare配置
echo "📝 创建Cloudflare配置..."
mkdir -p /root/.secrets
chmod 700 /root/.secrets

cat > /root/.secrets/cloudflare.ini << 'EOF'
# Cloudflare API token
dns_cloudflare_api_token = D1GwtcDBMGCRvoIoLb0IIe_8vdxJfoqiMoM0ZCbp
EOF

chmod 600 /root/.secrets/cloudflare.ini

# 3. 申请jytian.it.com证书
echo ""
echo "🔐 申请 jytian.it.com SSL证书..."
certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials /root/.secrets/cloudflare.ini \
  --dns-cloudflare-propagation-seconds 60 \
  -d jytian.it.com \
  -d www.jytian.it.com \
  -d api-v2.jytian.it.com \
  -d cdn.jytian.it.com \
  -d admin-portal.jytian.it.com \
  -d static.jytian.it.com \
  -d backup.jytian.it.com \
  --email admin@jytian.it.com \
  --agree-tos \
  --non-interactive

if [ $? -eq 0 ]; then
    echo "✅ jytian.it.com 证书申请成功！"
else
    echo "❌ jytian.it.com 证书申请失败"
    exit 1
fi

# 4. 申请tiankai.it.com证书
echo ""
echo "🔐 申请 tiankai.it.com SSL证书..."
certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials /root/.secrets/cloudflare.ini \
  --dns-cloudflare-propagation-seconds 60 \
  -d tiankai.it.com \
  -d www.tiankai.it.com \
  -d gateway.tiankai.it.com \
  -d bossjy.tiankai.it.com \
  -d console.tiankai.it.com \
  -d assets.tiankai.it.com \
  -d monitor.tiankai.it.com \
  --email admin@tiankai.it.com \
  --agree-tos \
  --non-interactive

if [ $? -eq 0 ]; then
    echo "✅ tiankai.it.com 证书申请成功！"
else
    echo "❌ tiankai.it.com 证书申请失败"
    exit 1
fi

# 5. 验证证书
echo ""
echo "🔍 验证证书..."
ls -la /etc/letsencrypt/live/jytian.it.com/
echo ""
ls -la /etc/letsencrypt/live/tiankai.it.com/

# 6. 配置自动续期
echo ""
echo "⏰ 配置自动续期..."
cat > /etc/cron.d/certbot-renew << 'EOF'
0 0,12 * * * root certbot renew --quiet --post-hook "systemctl reload nginx"
EOF

echo "✅ 自动续期已配置"

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
echo "  cd /root/BossJy-Cn"
echo "  sudo ./deploy/2-deploy-nginx.sh"
echo ""
