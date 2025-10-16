# deploy_appai.sh Cloudflare 憑證修正

## 修正內容

### 1. Cloudflare 憑證檢查邏輯 ✅

**修正前**：
```bash
if [ ! -f "$CF_CERT" ] || [ ! -f "$CF_KEY" ]; then
```

**修正後**：
```bash
if [ -f "$CF_CERT" ] && [ -f "$CF_KEY" ]; then
    # 檔案存在，執行配置
else
    # 檔案不存在，顯示錯誤
fi
```

### 2. 固定憑證路徑 ✅

直接使用固定路徑，不再需要手動配置：
- Certificate: `/etc/ssl/cloudflare/app_ssl.pem`
- Private Key: `/etc/ssl/cloudflare/app_ssl.key`

### 3. Nginx 配置更新 ✅

**自動更新 Nginx vhost 配置為**：
```nginx
ssl_certificate     /etc/ssl/cloudflare/app_ssl.pem;
ssl_certificate_key /etc/ssl/cloudflare/app_ssl.key;
```

**處理邏輯**：
1. 註解掉 Let's Encrypt 憑證路徑
2. 如果已存在 Cloudflare 配置，取消註解並更新路徑
3. 如果不存在，在 `ssl_protocols` 之前插入新配置

### 4. 步驟 5 前顯示憑證信息 ✅

**Cloudflare 模式**：
```
✅ 使用 Cloudflare 憑證：/etc/ssl/cloudflare/app_ssl.pem
```

**Let's Encrypt 模式**：
```
✅ 使用 Let's Encrypt 憑證：/etc/letsencrypt/live/appai.tiankai.it.com/fullchain.pem
```

### 5. 權限設置 ✅

自動設置正確的檔案權限：
```bash
sudo chmod 644 /etc/ssl/cloudflare/app_ssl.pem
sudo chmod 600 /etc/ssl/cloudflare/app_ssl.key
```

## 使用方式

### 選項 2：Cloudflare Origin Certificate

```bash
sudo ./deploy_appai.sh
```

選擇 `2) Cloudflare Origin Certificate`

**前提條件**：
- `/etc/ssl/cloudflare/app_ssl.pem` 已存在
- `/etc/ssl/cloudflare/app_ssl.key` 已存在

**執行流程**：
1. ✅ 檢查憑證檔案存在
2. ✅ 設置憑證權限
3. ✅ 自動更新 Nginx 配置
4. ✅ 顯示使用的憑證路徑
5. ✅ 測試 Nginx 配置 (`nginx -t`)
6. ✅ 重載 Nginx (`systemctl reload nginx`)

**預期結果**：
- 不會報「憑證不存在」錯誤
- Nginx 配置測試通過
- Nginx 成功重載
- HTTPS 正常訪問

## 測試驗證

### 1. 檢查憑證檔案
```bash
ls -l /etc/ssl/cloudflare/app_ssl.*
```

### 2. 執行部署
```bash
sudo ./deploy_appai.sh
# 選擇選項 2
```

### 3. 驗證 Nginx 配置
```bash
sudo nginx -t
sudo cat /etc/nginx/sites-available/appai.tiankai.it.com.conf | grep ssl_certificate
```

### 4. 測試 HTTPS 訪問
```bash
curl -I https://appai.tiankai.it.com
```

## 錯誤處理

### 如果憑證不存在
```
❌ Cloudflare 憑證文件不存在

預期路徑:
  Certificate: /etc/ssl/cloudflare/app_ssl.pem
  Private Key: /etc/ssl/cloudflare/app_ssl.key

請先配置 Cloudflare Origin Certificate，或選擇其他 SSL 選項
```

### 解決方法
1. 確認憑證檔案已上傳到正確路徑
2. 檢查檔案權限
3. 或選擇選項 1 (Let's Encrypt) 或選項 3 (手動配置)

## 修改總結

✅ Cloudflare 憑證檢查邏輯已修正
✅ 使用 `[ -f ... ] && [ -f ... ]` 語法
✅ 直接更新為固定路徑 `/etc/ssl/cloudflare/app_ssl.pem`
✅ 步驟 5 前顯示使用的憑證
✅ 確保 `nginx -t` 通過
✅ 確保 `nginx reload` 成功

**腳本語法檢查**: ✅ 通過

---

**修改日期**: 2025-10-08
**版本**: v1.1
**狀態**: Ready for Production ✅
