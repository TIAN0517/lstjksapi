#!/bin/bash
# 测试Cloudflare API Token

TOKEN="D1GwtcDBMGCRvoIoLb0IIe_8vdxJfoqiMoM0ZCbp"

echo "================================"
echo "🔍 测试Cloudflare API Token"
echo "================================"
echo ""

# 1. 验证Token
echo "1️⃣ 验证Token..."
curl -s -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | python3 -m json.tool

echo ""
echo "2️⃣ 获取Zone列表..."
curl -s -X GET "https://api.cloudflare.com/client/v4/zones" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | python3 -m json.tool

echo ""
echo "================================"
echo "✅ 测试完成"
echo "================================"
