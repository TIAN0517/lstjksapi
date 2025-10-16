#!/bin/bash
# 通配符SSL证书申请（Cloudflare DNS验证）
# 一个证书覆盖所有子域名

set -e

echo "================================"
echo "🔐 通配符SSL证书申请"
echo "================================"
echo ""

# 1. 确保插件已安装
echo "📦 检查Certbot插件..."
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

# 3. 申请jytian.it.com通配符证书
echo ""
echo "🔐 申请 jytian.it.com 通配符证书（*.jytian.it.com）..."
certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials /root/.secrets/cloudflare.ini \
  --dns-cloudflare-propagation-seconds 30 \
  -d jytian.it.com \
  -d '*.jytian.it.com' \
  --email admin@jytian.it.com \
  --agree-tos \
  --non-interactive

if [ $? -eq 0 ]; then
    echo "✅ jytian.it.com 通配符证书申请成功！"
else
    echo "❌ jytian.it.com 证书申请失败"
    exit 1
fi

# 4. 申请tiankai.it.com通配符证书
echo ""
echo "🔐 申请 tiankai.it.com 通配符证书（*.tiankai.it.com）..."
certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials /root/.secrets/cloudflare.ini \
  --dns-cloudflare-propagation-seconds 30 \
  -d tiankai.it.com \
  -d '*.tiankai.it.com' \
  --email admin@tiankai.it.com \
  --agree-tos \
  --non-interactive

if [ $? -eq 0 ]; then
    echo "✅ tiankai.it.com 通配符证书申请成功！"
else
    echo "❌ tiankai.it.com 证书申请失败"
    exit 1
fi

# 5. 验证证书
echo ""
echo "🔍 验证证书..."
echo "jytian.it.com 证书："
ls -la /etc/letsencrypt/live/jytian.it.com/
echo ""
echo "tiankai.it.com 证书："
ls -la /etc/letsencrypt/live/tiankai.it.com/

# 6. 显示证书详情
echo ""
echo "📋 证书覆盖的域名："
openssl x509 -in /etc/letsencrypt/live/jytian.it.com/cert.pem -noout -text | grep DNS:

# 7. 配置自动续期
echo ""
echo "⏰ 配置自动续期..."
cat > /etc/cron.d/certbot-renew << 'EOF'
0 0,12 * * * root certbot renew --quiet --post-hook "systemctl reload nginx"
EOF

echo "✅ 自动续期已配置"

# 8. 测试续期
echo ""
echo "🧪 测试自动续期..."
certbot renew --dry-run

echo ""
echo "================================"
echo "✅ 通配符SSL证书申请完成！"
echo "================================"
echo ""
echo "证书位置："
echo "  jytian.it.com:  /etc/letsencrypt/live/jytian.it.com/"
echo "  tiankai.it.com: /etc/letsencrypt/live/tiankai.it.com/"
echo ""
echo "覆盖域名："
echo "  jytian.it.com + *.jytian.it.com"
echo "  tiankai.it.com + *.tiankai.it.com"
echo ""
echo "下一步："
echo "  cd /root/BossJy-Cn"
echo "  sudo ./deploy/2-deploy-nginx.sh"
echo ""
