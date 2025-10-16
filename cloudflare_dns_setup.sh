#!/bin/bash
# Cloudflare DNS 自動化配置腳本
# 為 appai.tiankai.it.com 創建 DNS 記錄並配置

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ==================== 配置 ====================
CF_ACCOUNT_ID="294ea8539d4d17934ce09438d7c01967"
CF_API_TOKEN="jea-yHF7J58QRsKT9sQdKAaALIjgqZIf4iLBqmhl"
ZONE_NAME="tiankai.it.com"
SUBDOMAIN="bossjy"
FULL_DOMAIN="${SUBDOMAIN}.${ZONE_NAME}"
SERVER_IP="146.88.134.254"
SERVER_PORT="8080"
DNS_TYPE="A"
PROXY_STATUS="true"
DNS_TTL="300"
DNS_COMMENT="BossJy API Service - Port 18001"
SSL_MODE="flexible"
CACHE_LEVEL="aggressive"
MINIFY_HTML="true"
MINIFY_CSS="true"
MINIFY_JS="true"
BROTLI_COMPRESSION="true"
HTTP2="true"

# ==================== 函數 ====================

# 驗證 API Token
verify_token() {
    echo -e "${YELLOW}🔐 驗證 Cloudflare API Token...${NC}"

    RESPONSE=$(curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/${CF_ACCOUNT_ID}/tokens/verify" \
        -H "Authorization: Bearer ${CF_API_TOKEN}" \
        -H "Content-Type: application/json")

    if echo "$RESPONSE" | grep -q '"success":true'; then
        echo -e "${GREEN}✅ API Token 驗證成功${NC}"
        echo "$RESPONSE" | grep -o '"status":"[^"]*"'
        return 0
    else
        echo -e "${RED}❌ API Token 驗證失敗${NC}"
        echo "$RESPONSE"
        exit 1
    fi
}

# 獲取 Zone ID
get_zone_id() {
    echo -e "${YELLOW}🔍 獲取 Zone ID for ${ZONE_NAME}...${NC}"

    RESPONSE=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=${ZONE_NAME}" \
        -H "Authorization: Bearer ${CF_API_TOKEN}" \
        -H "Content-Type: application/json")

    ZONE_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

    if [ -z "$ZONE_ID" ]; then
        echo -e "${RED}❌ 找不到 Zone: ${ZONE_NAME}${NC}"
        echo "$RESPONSE"
        exit 1
    fi

    echo -e "${GREEN}✅ Zone ID: ${ZONE_ID}${NC}"
}

# 檢查 DNS 記錄是否存在
check_dns_record() {
    echo -e "${YELLOW}🔍 檢查 ${FULL_DOMAIN} DNS 記錄...${NC}"

    RESPONSE=$(curl -s -X GET \
        "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records?name=${FULL_DOMAIN}" \
        -H "Authorization: Bearer ${CF_API_TOKEN}" \
        -H "Content-Type: application/json")

    RECORD_ID=$(echo "$RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

    if [ -n "$RECORD_ID" ]; then
        echo -e "${YELLOW}⚠️  DNS 記錄已存在 (ID: ${RECORD_ID})${NC}"
        return 0
    else
        echo -e "${BLUE}ℹ️  DNS 記錄不存在，將創建新記錄${NC}"
        return 1
    fi
}

# 創建/更新 A 記錄
create_or_update_dns() {
    if check_dns_record; then
        echo -e "${YELLOW}📝 更新現有 DNS 記錄...${NC}"

        RESPONSE=$(curl -s -X PUT \
            "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records/${RECORD_ID}" \
            -H "Authorization: Bearer ${CF_API_TOKEN}" \
            -H "Content-Type: application/json" \
            --data "{
                \"type\": \"A\",
                \"name\": \"${FULL_DOMAIN}\",
                \"content\": \"${SERVER_IP}\",
                \"ttl\": 1,
                \"proxied\": true
            }")
    else
        echo -e "${YELLOW}📝 創建新 DNS 記錄...${NC}"

        RESPONSE=$(curl -s -X POST \
            "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records" \
            -H "Authorization: Bearer ${CF_API_TOKEN}" \
            -H "Content-Type: application/json" \
            --data "{
                \"type\": \"A\",
                \"name\": \"${FULL_DOMAIN}\",
                \"content\": \"${SERVER_IP}\",
                \"ttl\": 1,
                \"proxied\": true
            }")
    fi

    if echo "$RESPONSE" | grep -q '"success":true'; then
        echo -e "${GREEN}✅ DNS 記錄操作成功${NC}"
        echo "$RESPONSE" | grep -o '"name":"[^"]*"'
        echo "$RESPONSE" | grep -o '"content":"[^"]*"'
        return 0
    else
        echo -e "${RED}❌ DNS 記錄操作失敗${NC}"
        echo "$RESPONSE"
        return 1
    fi
}

# 設置 SSL/TLS 為 Full (Strict)
set_ssl_mode() {
    echo -e "${YELLOW}🔒 設置 SSL/TLS 模式為 Full (Strict)...${NC}"

    RESPONSE=$(curl -s -X PATCH \
        "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/settings/ssl" \
        -H "Authorization: Bearer ${CF_API_TOKEN}" \
        -H "Content-Type: application/json" \
        --data '{"value":"strict"}')

    if echo "$RESPONSE" | grep -q '"success":true'; then
        echo -e "${GREEN}✅ SSL 模式已設置為 Full (Strict)${NC}"
    else
        echo -e "${YELLOW}⚠️  SSL 模式設置可能失敗（或已是正確值）${NC}"
        echo "$RESPONSE" | head -5
    fi
}

# 啟用 Always Use HTTPS
enable_always_https() {
    echo -e "${YELLOW}🔒 啟用 Always Use HTTPS...${NC}"

    RESPONSE=$(curl -s -X PATCH \
        "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/settings/always_use_https" \
        -H "Authorization: Bearer ${CF_API_TOKEN}" \
        -H "Content-Type: application/json" \
        --data '{"value":"on"}')

    if echo "$RESPONSE" | grep -q '"success":true'; then
        echo -e "${GREEN}✅ Always Use HTTPS 已啟用${NC}"
    else
        echo -e "${YELLOW}⚠️  Always Use HTTPS 設置可能失敗${NC}"
    fi
}

# 設置最小 TLS 版本
set_min_tls_version() {
    echo -e "${YELLOW}🔒 設置最小 TLS 版本為 1.2...${NC}"

    RESPONSE=$(curl -s -X PATCH \
        "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/settings/min_tls_version" \
        -H "Authorization: Bearer ${CF_API_TOKEN}" \
        -H "Content-Type: application/json" \
        --data '{"value":"1.2"}')

    if echo "$RESPONSE" | grep -q '"success":true'; then
        echo -e "${GREEN}✅ 最小 TLS 版本已設置為 1.2${NC}"
    else
        echo -e "${YELLOW}⚠️  TLS 版本設置可能失敗${NC}"
    fi
}

# 驗證 DNS 解析
verify_dns() {
    echo -e "${YELLOW}🧪 驗證 DNS 解析...${NC}"
    sleep 5  # 等待 DNS 傳播

    echo -e "${BLUE}使用 dig 查詢...${NC}"
    dig +short ${FULL_DOMAIN} @1.1.1.1

    echo -e "${BLUE}使用 nslookup 查詢...${NC}"
    nslookup ${FULL_DOMAIN} 1.1.1.1 || true
}

# 測試 HTTPS 訪問
test_https() {
    echo -e "${YELLOW}🧪 測試 HTTPS 訪問...${NC}"
    sleep 10  # 等待 SSL 傳播

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        https://${FULL_DOMAIN} \
        --connect-timeout 10 2>/dev/null || echo "000")

    echo -e "${BLUE}HTTP 狀態碼: ${HTTP_CODE}${NC}"

    case $HTTP_CODE in
        200|301|302|405)
            echo -e "${GREEN}✅ HTTPS 訪問成功${NC}"
            ;;
        522)
            echo -e "${YELLOW}⚠️  HTTP 522 - 連接超時（檢查後端服務）${NC}"
            ;;
        525)
            echo -e "${YELLOW}⚠️  HTTP 525 - SSL 握手失敗（檢查憑證）${NC}"
            ;;
        *)
            echo -e "${YELLOW}⚠️  HTTP ${HTTP_CODE}${NC}"
            ;;
    esac

    echo ""
    echo -e "${BLUE}完整 HTTP 標頭:${NC}"
    curl -I https://${FULL_DOMAIN} --connect-timeout 10 2>/dev/null || true
}

# ==================== 主流程 ====================

main() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  Cloudflare DNS 自動化配置${NC}"
    echo -e "${BLUE}  Domain: ${FULL_DOMAIN}${NC}"
    echo -e "${BLUE}  IP: ${SERVER_IP}${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""

    # 1. 驗證 Token
    verify_token
    echo ""

    # 2. 獲取 Zone ID
    get_zone_id
    echo ""

    # 3. 創建/更新 DNS 記錄
    create_or_update_dns
    echo ""

    # 4. 設置 SSL/TLS
    set_ssl_mode
    echo ""

    # 5. 啟用 Always HTTPS
    enable_always_https
    echo ""

    # 6. 設置最小 TLS 版本
    set_min_tls_version
    echo ""

    # 7. 驗證 DNS
    verify_dns
    echo ""

    # 8. 測試 HTTPS
    test_https
    echo ""

    echo -e "${BLUE}================================================${NC}"
    echo -e "${GREEN}✅ 配置完成！${NC}"
    echo -e "${BLUE}================================================${NC}"
    echo ""

    echo -e "${YELLOW}📋 配置摘要${NC}"
    echo "  Domain: ${FULL_DOMAIN}"
    echo "  IP: ${SERVER_IP}"
    echo "  Proxy: ✅ 已啟用（橙色雲）"
    echo "  SSL/TLS: Full (Strict)"
    echo "  Always HTTPS: ON"
    echo "  Min TLS: 1.2"
    echo ""

    echo -e "${YELLOW}🔗 訪問連結${NC}"
    echo "  https://${FULL_DOMAIN}"
    echo "  https://${FULL_DOMAIN}/health"
    echo "  https://${FULL_DOMAIN}/status"
    echo ""

    echo -e "${YELLOW}📝 下一步${NC}"
    echo "  1. 確保後端服務運行在 port 18001"
    echo "  2. 執行: ./fix_appai_nginx.sh (修復 Nginx 配置)"
    echo "  3. 測試: curl https://${FULL_DOMAIN}/health"
    echo ""
}

# 執行主流程
main
