#!/bin/bash
# 一鍵安裝所有內容（需要 root 權限）

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  BossJy-Pro 一鍵部署${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# 檢查 root 權限
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ 請使用 root 權限運行${NC}"
    echo "使用: sudo ./install_all.sh"
    exit 1
fi

# 步驟 1: 安裝憑證
echo -e "${YELLOW}[1/4] 安裝 SSL 憑證...${NC}"
mkdir -p /etc/ssl/cloudflare
cp /tmp/app_ssl.pem /etc/ssl/cloudflare/
cp /tmp/app_ssl.key /etc/ssl/cloudflare/
chmod 644 /etc/ssl/cloudflare/app_ssl.pem
chmod 600 /etc/ssl/cloudflare/app_ssl.key
echo -e "${GREEN}✅ 憑證已安裝${NC}"
echo ""

# 步驟 2: 備份並更新 Nginx 配置
echo -e "${YELLOW}[2/4] 更新 Nginx 配置...${NC}"
NGINX_CONF="/etc/nginx/sites-available/appai.tiankai.it.com.conf"
BACKUP_FILE="${NGINX_CONF}.backup.$(date +%Y%m%d_%H%M%S)"

if [ -f "$NGINX_CONF" ]; then
    cp "$NGINX_CONF" "$BACKUP_FILE"
    echo -e "${GREEN}✅ 已備份: $BACKUP_FILE${NC}"
fi

cp nginx/appai.tiankai.it.com.conf.fixed "$NGINX_CONF"
echo -e "${GREEN}✅ Nginx 配置已更新${NC}"
echo ""

# 步驟 3: 測試並重載 Nginx
echo -e "${YELLOW}[3/4] 測試 Nginx 配置...${NC}"
if nginx -t; then
    echo -e "${GREEN}✅ Nginx 配置測試通過${NC}"
    systemctl reload nginx
    echo -e "${GREEN}✅ Nginx 已重載${NC}"
else
    echo -e "${RED}❌ Nginx 配置測試失敗${NC}"
    if [ -f "$BACKUP_FILE" ]; then
        cp "$BACKUP_FILE" "$NGINX_CONF"
        echo -e "${YELLOW}已恢復備份${NC}"
    fi
    exit 1
fi
echo ""

# 步驟 4: 檢查後端服務
echo -e "${YELLOW}[4/4] 檢查後端服務...${NC}"
if netstat -tlnp 2>/dev/null | grep -q :18001; then
    echo -e "${GREEN}✅ 後端服務運行中 (port 18001)${NC}"
else
    echo -e "${YELLOW}⚠️  後端服務未運行${NC}"
    echo "請執行: ./start_appai_api.sh"
fi
echo ""

echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}✅ 安裝完成！${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

echo -e "${YELLOW}🧪 測試訪問:${NC}"
echo "  curl https://appai.tiankai.it.com/health"
echo ""

# 測試 HTTPS 訪問
sleep 2
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://appai.tiankai.it.com --connect-timeout 10 2>/dev/null || echo "000")

echo -e "${BLUE}HTTPS 狀態碼: ${HTTP_CODE}${NC}"

case $HTTP_CODE in
    200|301|302|405)
        echo -e "${GREEN}✅ HTTPS 訪問成功！${NC}"
        ;;
    522)
        echo -e "${YELLOW}⚠️  HTTP 522 - 後端服務未運行${NC}"
        echo "請執行: ./start_appai_api.sh"
        ;;
    *)
        echo -e "${YELLOW}⚠️  HTTP ${HTTP_CODE}${NC}"
        ;;
esac
echo ""
