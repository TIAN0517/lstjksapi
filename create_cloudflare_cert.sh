#!/bin/bash
# 創建 Cloudflare Origin Certificate

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CF_ACCOUNT_ID="294ea8539d4d17934ce09438d7c01967"
CF_API_TOKEN="jea-yHF7J58QRsKT9sQdKAaALIjgqZIf4iLBqmhl"
ZONE_ID="ca7fcf0fe0366d56c18fd45ab36d6cb0"
DOMAIN="appai.tiankai.it.com"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  創建 Cloudflare Origin Certificate${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

echo -e "${YELLOW}📝 請求創建 Origin Certificate...${NC}"

# 創建憑證請求
RESPONSE=$(curl -s -X POST \
    "https://api.cloudflare.com/client/v4/certificates" \
    -H "Authorization: Bearer ${CF_API_TOKEN}" \
    -H "Content-Type: application/json" \
    --data "{
        \"hostnames\": [
            \"${DOMAIN}\",
            \"*.tiankai.it.com\"
        ],
        \"requested_validity\": 5475,
        \"request_type\": \"origin-rsa\",
        \"csr\": \"\"
    }")

# 檢查是否成功
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo -e "${GREEN}✅ Origin Certificate 創建成功${NC}"
    echo ""

    # 提取憑證和私鑰
    CERTIFICATE=$(echo "$RESPONSE" | grep -o '"certificate":"[^"]*"' | cut -d'"' -f4 | sed 's/\\n/\n/g')
    PRIVATE_KEY=$(echo "$RESPONSE" | grep -o '"private_key":"[^"]*"' | cut -d'"' -f4 | sed 's/\\n/\n/g')

    # 顯示提取的內容長度
    CERT_LEN=$(echo "$CERTIFICATE" | wc -c)
    KEY_LEN=$(echo "$PRIVATE_KEY" | wc -c)

    echo -e "${BLUE}憑證長度: ${CERT_LEN} bytes${NC}"
    echo -e "${BLUE}私鑰長度: ${KEY_LEN} bytes${NC}"
    echo ""

    # 保存到臨時文件
    echo "$CERTIFICATE" > /tmp/app_ssl.pem
    echo "$PRIVATE_KEY" > /tmp/app_ssl.key

    echo -e "${GREEN}✅ 憑證已保存到臨時文件${NC}"
    echo "  Certificate: /tmp/app_ssl.pem"
    echo "  Private Key: /tmp/app_ssl.key"
    echo ""

    echo -e "${YELLOW}📋 下一步（需要 root 權限）:${NC}"
    echo ""
    echo "  sudo mkdir -p /etc/ssl/cloudflare"
    echo "  sudo cp /tmp/app_ssl.pem /etc/ssl/cloudflare/"
    echo "  sudo cp /tmp/app_ssl.key /etc/ssl/cloudflare/"
    echo "  sudo chmod 644 /etc/ssl/cloudflare/app_ssl.pem"
    echo "  sudo chmod 600 /etc/ssl/cloudflare/app_ssl.key"
    echo ""

    # 顯示憑證信息
    echo -e "${BLUE}憑證預覽:${NC}"
    head -3 /tmp/app_ssl.pem
    echo "..."
    echo ""

else
    echo -e "${RED}❌ Origin Certificate 創建失敗${NC}"
    echo "$RESPONSE" | head -20
    exit 1
fi
