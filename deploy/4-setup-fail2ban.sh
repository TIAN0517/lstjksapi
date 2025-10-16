#!/bin/bash
# Fail2Ban配置脚本
# 使用方法: chmod +x 4-setup-fail2ban.sh && sudo ./4-setup-fail2ban.sh

set -e

echo "================================"
echo "🛡️ Fail2Ban配置脚本"
echo "================================"
echo ""

PROJECT_ROOT="/root/BossJy-Cn"

# 1. 安装Fail2Ban
echo "📦 安装Fail2Ban..."
apt update
apt install fail2ban -y

# 2. 复制配置文件
echo "📝 复制配置文件..."
cp $PROJECT_ROOT/security/fail2ban-nginx.conf /etc/fail2ban/filter.d/nginx-login.conf
cp $PROJECT_ROOT/security/fail2ban-jail.conf /etc/fail2ban/jail.d/nginx-bossjy.conf

# 3. 重启Fail2Ban
echo "🔄 重启Fail2Ban..."
systemctl restart fail2ban
systemctl enable fail2ban

# 4. 显示状态
echo ""
echo "📊 Fail2Ban状态："
fail2ban-client status

echo ""
echo "================================"
echo "✅ Fail2Ban配置完成！"
echo "================================"
echo ""
echo "监控的日志："
echo "  /var/log/nginx/jytian-login.log"
echo "  /var/log/nginx/tiankai-login.log"
echo ""
echo "查看监狱状态："
echo "  sudo fail2ban-client status nginx-login-jytian"
echo "  sudo fail2ban-client status nginx-login-tiankai"
echo ""
echo "解封IP："
echo "  sudo fail2ban-client set nginx-login-jytian unbanip IP地址"
echo ""
