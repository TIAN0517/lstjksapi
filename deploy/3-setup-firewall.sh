#!/bin/bash
# 防火墙配置脚本
# 使用方法: chmod +x 3-setup-firewall.sh && sudo ./3-setup-firewall.sh

set -e

echo "================================"
echo "🛡️ 防火墙配置脚本"
echo "================================"
echo ""

# 获取当前SSH端口
SSH_PORT=$(ss -tlnp | grep sshd | awk '{print $4}' | cut -d: -f2 | head -1)
if [ -z "$SSH_PORT" ]; then
    SSH_PORT=22
fi

echo "当前SSH端口: $SSH_PORT"
echo ""

# 1. 安装UFW
echo "📦 安装UFW..."
apt update
apt install ufw -y

# 2. 重置规则
echo "🔄 重置防火墙规则..."
ufw --force reset

# 3. 默认策略
echo "📋 设置默认策略..."
ufw default deny incoming
ufw default allow outgoing

# 4. 允许SSH（非常重要！）
echo "🔓 允许SSH端口 $SSH_PORT..."
ufw allow $SSH_PORT/tcp comment 'SSH'

# 5. 允许HTTP和HTTPS
echo "🔓 允许HTTP/HTTPS..."
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'

# 6. 允许自定义API端口
echo "🔓 允许自定义API端口..."
ufw allow 8443/tcp comment 'jytian API'
ufw allow 7443/tcp comment 'tiankai API'

# 7. 管理后台端口（限制IP - 可选）
echo "🔓 允许管理后台端口..."
# 如果你知道自己的公网IP，取消下面注释并修改
# ufw allow from YOUR_IP to any port 9443 proto tcp comment 'jytian admin'
# ufw allow from YOUR_IP to any port 6443 proto tcp comment 'tiankai admin'

# 临时允许所有（部署后务必修改为IP限制）
ufw allow 9443/tcp comment 'jytian admin - TEMP'
ufw allow 6443/tcp comment 'tiankai admin - TEMP'

# 8. 限制SSH连接速率（防暴力破解）
echo "🔒 配置SSH限流..."
ufw limit $SSH_PORT/tcp

# 9. 启用防火墙
echo ""
echo "✅ 启用防火墙..."
ufw --force enable

# 10. 显示状态
echo ""
echo "📊 防火墙状态："
ufw status numbered

echo ""
echo "================================"
echo "✅ 防火墙配置完成！"
echo "================================"
echo ""
echo "开放端口："
echo "  SSH:           $SSH_PORT"
echo "  HTTP:          80"
echo "  HTTPS:         443"
echo "  jytian API:    8443"
echo "  tiankai API:   7443"
echo "  jytian Admin:  9443 (⚠️ 建议限制IP)"
echo "  tiankai Admin: 6443 (⚠️ 建议限制IP)"
echo ""
echo "⚠️  重要提醒："
echo "  管理后台端口当前允许所有IP访问"
echo "  强烈建议修改为IP白名单："
echo "    sudo ufw delete allow 9443/tcp"
echo "    sudo ufw allow from YOUR_IP to any port 9443 proto tcp"
echo ""
echo "查询你的公网IP："
echo "  curl ifconfig.me"
echo ""
