#!/bin/bash
# SSL证书申请脚本（Cloudflare DNS验证）
# 适用于：Cloudflare代理已开启的情况
# 使用方法: chmod +x 1-install-ssl-cloudflare.sh && sudo ./1-install-ssl-cloudflare.sh

set -e

echo "================================"
echo "🔐 SSL证书申请脚本（Cloudflare DNS验证）"
echo "================================"
echo ""

# 检查是否已安装certbot
if ! command -v certbot &> /dev/null; then
    echo "📦 安装Certbot..."
    apt update
    apt install certbot python3-certbot-dns-cloudflare -y
fi

echo ""
echo "⚠️  重要提示："
echo "  1. 需要Cloudflare API Token"
echo "  2. 获取方式："
echo "     - 登录 Cloudflare → My Profile → API Tokens"
echo "     - Create Token → Edit zone DNS 模板"
echo "     - Zone Resources: Include → Specific zone → 选择你的域名"
echo "     - Create Token → 复制Token"
echo ""

read -p "是否已准备好Cloudflare API Token? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 请先获取Cloudflare API Token"
    echo ""
    echo "获取地址: https://dash.cloudflare.com/profile/api-tokens"
    exit 1
fi

# 创建Cloudflare配置文件
mkdir -p /root/.secrets
chmod 700 /root/.secrets

echo ""
read -p "请输入Cloudflare API Token: " CF_TOKEN

# 写入配置文件
cat > /root/.secrets/cloudflare.ini << EOF
# Cloudflare API token
dns_cloudflare_api_token = $CF_TOKEN
EOF

chmod 600 /root/.secrets/cloudflare.ini

echo ""
echo "🔐 申请 jytian.it.com SSL证书（包含所有子域名）..."
certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials /root/.secrets/cloudflare.ini \
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

echo ""
echo "🔐 申请 tiankai.it.com SSL证书（包含所有子域名）..."
certbot certonly \
  --dns-cloudflare \
  --dns-cloudflare-credentials /root/.secrets/cloudflare.ini \
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

# 验证证书
echo ""
echo "🔍 验证证书..."
ls -la /etc/letsencrypt/live/jytian.it.com/
ls -la /etc/letsencrypt/live/tiankai.it.com/

# 设置自动续期
echo ""
echo "⏰ 配置自动续期..."
cat > /etc/cron.d/certbot-renew << 'EOF'
0 0,12 * * * root certbot renew --quiet --post-hook "systemctl reload nginx"
EOF

echo "✅ 自动续期已配置"

# 测试续期
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
echo "  sudo ./2-deploy-nginx.sh"
echo ""
