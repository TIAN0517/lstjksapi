#!/bin/bash
# Cloudflare Tunnel 本地部署方案
# 无需公网IP，无需端口转发

set -e

echo "================================"
echo "🚇 Cloudflare Tunnel 设置"
echo "================================"
echo ""

# 1. 安装cloudflared
echo "📦 安装cloudflared..."
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
dpkg -i cloudflared-linux-amd64.deb
rm cloudflared-linux-amd64.deb

# 2. 登录Cloudflare
echo ""
echo "🔐 登录Cloudflare..."
echo "浏览器会打开，请登录你的Cloudflare账号"
cloudflared tunnel login

# 3. 创建Tunnel
echo ""
echo "🚇 创建Tunnel..."
cloudflared tunnel create bossjy-tunnel

# 4. 配置Tunnel
echo ""
echo "📝 创建配置文件..."
cat > ~/.cloudflared/config.yml << 'EOF'
tunnel: bossjy-tunnel
credentials-file: /root/.cloudflared/TUNNEL_ID.json

ingress:
  # jytian.it.com 主域名
  - hostname: jytian.it.com
    service: http://localhost:9001

  # jytian.it.com 子域名
  - hostname: www.jytian.it.com
    service: http://localhost:9001

  - hostname: api-v2.jytian.it.com
    service: http://localhost:9001

  - hostname: cdn.jytian.it.com
    service: http://localhost:9001

  - hostname: admin-portal.jytian.it.com
    service: http://localhost:5001

  - hostname: backup.jytian.it.com
    service: http://localhost:5002

  # tiankai.it.com 主域名
  - hostname: tiankai.it.com
    service: http://localhost:9001

  # tiankai.it.com 子域名
  - hostname: www.tiankai.it.com
    service: http://localhost:9001

  - hostname: gateway.tiankai.it.com
    service: http://localhost:9001

  - hostname: bossjy.tiankai.it.com
    service: http://localhost:9001

  - hostname: console.tiankai.it.com
    service: http://localhost:5001

  - hostname: monitor.tiankai.it.com
    service: http://localhost:5002

  # 默认规则
  - service: http_status:404
EOF

# 5. 配置DNS
echo ""
echo "🌐 配置DNS路由..."
echo "请手动执行以下命令配置每个子域名："
echo ""
echo "cloudflared tunnel route dns bossjy-tunnel jytian.it.com"
echo "cloudflared tunnel route dns bossjy-tunnel www.jytian.it.com"
echo "cloudflared tunnel route dns bossjy-tunnel api-v2.jytian.it.com"
echo "cloudflared tunnel route dns bossjy-tunnel cdn.jytian.it.com"
echo "cloudflared tunnel route dns bossjy-tunnel admin-portal.jytian.it.com"
echo "cloudflared tunnel route dns bossjy-tunnel backup.jytian.it.com"
echo ""
echo "cloudflared tunnel route dns bossjy-tunnel tiankai.it.com"
echo "cloudflared tunnel route dns bossjy-tunnel www.tiankai.it.com"
echo "cloudflared tunnel route dns bossjy-tunnel gateway.tiankai.it.com"
echo "cloudflared tunnel route dns bossjy-tunnel bossjy.tiankai.it.com"
echo "cloudflared tunnel route dns bossjy-tunnel console.tiankai.it.com"
echo "cloudflared tunnel route dns bossjy-tunnel monitor.tiankai.it.com"

# 6. 安装系统服务
echo ""
echo "⚙️ 安装系统服务..."
cloudflared service install

echo ""
echo "================================"
echo "✅ Cloudflare Tunnel 设置完成！"
echo "================================"
echo ""
echo "启动Tunnel:"
echo "  sudo systemctl start cloudflared"
echo "  sudo systemctl enable cloudflared"
echo ""
echo "查看状态:"
echo "  sudo systemctl status cloudflared"
echo ""
echo "查看日志:"
echo "  sudo journalctl -u cloudflared -f"
echo ""
