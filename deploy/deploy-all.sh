#!/bin/bash
# 一键部署脚本
# 使用方法: chmod +x deploy-all.sh && sudo ./deploy-all.sh

set -e

echo "========================================"
echo "🚀 BossJy-Cn 一键部署脚本"
echo "========================================"
echo ""
echo "⚠️  重要提醒："
echo "  1. DNS已配置所有子域名"
echo "  2. Cloudflare代理暂时关闭（部署完成后再开）"
echo "  3. 服务器防火墙已允许80/443端口"
echo ""
read -p "确认以上条件已满足？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 部署取消"
    exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo ""
echo "================================"
echo "步骤 1/4: 申请SSL证书"
echo "================================"
bash $SCRIPT_DIR/1-install-ssl.sh

echo ""
echo "================================"
echo "步骤 2/4: 部署Nginx配置"
echo "================================"
bash $SCRIPT_DIR/2-deploy-nginx.sh

echo ""
echo "================================"
echo "步骤 3/4: 配置防火墙"
echo "================================"
bash $SCRIPT_DIR/3-setup-firewall.sh

echo ""
echo "================================"
echo "步骤 4/4: 配置Fail2Ban"
echo "================================"
bash $SCRIPT_DIR/4-setup-fail2ban.sh

echo ""
echo "========================================"
echo "✅ 部署完成！"
echo "========================================"
echo ""
echo "📋 接下来的步骤："
echo ""
echo "1. 修改管理后台IP白名单："
echo "   查询你的IP: curl ifconfig.me"
echo "   编辑配置: sudo nano /etc/nginx/sites-available/jytian-admin.conf"
echo "   重新加载: sudo systemctl reload nginx"
echo ""
echo "2. 启动Flask应用："
echo "   cd /root/BossJy-Cn"
echo "   pip install gunicorn flask flask-jwt-extended"
echo "   gunicorn -w 4 -b 127.0.0.1:5000 app.web_app:app --daemon"
echo ""
echo "3. 开启Cloudflare代理（DNS所有记录改为橙色🟠）"
echo ""
echo "4. 测试访问："
echo "   https://jytian.it.com"
echo "   https://api-v2.jytian.it.com:8443/health"
echo "   https://cdn.jytian.it.com"
echo ""
echo "5. 检查SSL评分："
echo "   https://www.ssllabs.com/ssltest/analyze.html?d=jytian.it.com"
echo ""
echo "🎉 享受企业级安全防护！"
echo ""
