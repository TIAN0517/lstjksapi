# appai.tiankai.it.com 部署指南

## 📋 域名變更說明

```
舊域名: gasapi.jytian.it.com
新域名: appai.tiankai.it.com
後端: 127.0.0.1:18001
```

---

## 🚀 快速部署（自動化）

```bash
# 執行自動部署腳本
sudo ./deploy_appai.sh
```

腳本會自動完成：
- ✅ 檢查後端服務狀態
- ✅ 備份現有配置
- ✅ 部署 Nginx 配置
- ✅ 選擇並配置 SSL 憑證
- ✅ 測試並重載 Nginx
- ✅ 驗證部署狀態

---

## 🔧 手動部署步驟

### 步驟 1: 部署 Nginx 配置

```bash
# 複製配置文件
sudo cp nginx/appai.tiankai.it.com.conf \
     /etc/nginx/sites-available/appai.tiankai.it.com.conf

# 創建符號連結
sudo ln -s /etc/nginx/sites-available/appai.tiankai.it.com.conf \
           /etc/nginx/sites-enabled/

# 測試配置
sudo nginx -t
```

### 步驟 2: SSL 憑證配置

#### 方案 A: Let's Encrypt（推薦）

```bash
# 申請憑證
sudo certbot certonly --nginx -d appai.tiankai.it.com

# 憑證路徑（已在配置中設定）
# /etc/letsencrypt/live/appai.tiankai.it.com/fullchain.pem
# /etc/letsencrypt/live/appai.tiankai.it.com/privkey.pem

# 自動續期（certbot 會自動配置 cron）
sudo certbot renew --dry-run
```

#### 方案 B: Cloudflare Origin Certificate

**1. 在 Cloudflare Dashboard 生成憑證**

路徑: `SSL/TLS` → `Origin Server` → `Create Certificate`

設定:
- Private key type: `RSA (2048)`
- Hostnames: `appai.tiankai.it.com`, `*.tiankai.it.com`
- Certificate validity: `15 years`

**2. 保存憑證到伺服器**

```bash
# 創建目錄
sudo mkdir -p /etc/ssl/cloudflare

# 保存 Certificate
sudo nano /etc/ssl/cloudflare/appai.tiankai.it.com.pem
# (貼上 Origin Certificate)

# 保存 Private Key
sudo nano /etc/ssl/cloudflare/appai.tiankai.it.com.key
# (貼上 Private Key)

# 設置權限
sudo chmod 644 /etc/ssl/cloudflare/appai.tiankai.it.com.pem
sudo chmod 600 /etc/ssl/cloudflare/appai.tiankai.it.com.key
```

**3. 更新 Nginx 配置**

編輯 `/etc/nginx/sites-available/appai.tiankai.it.com.conf`:

```nginx
# 註解掉 Let's Encrypt 部分
# ssl_certificate /etc/letsencrypt/live/appai.tiankai.it.com/fullchain.pem;
# ssl_certificate_key /etc/letsencrypt/live/appai.tiankai.it.com/privkey.pem;

# 取消註解 Cloudflare 部分
ssl_certificate /etc/ssl/cloudflare/appai.tiankai.it.com.pem;
ssl_certificate_key /etc/ssl/cloudflare/appai.tiankai.it.com.key;
```

### 步驟 3: 重載 Nginx

```bash
# 測試配置
sudo nginx -t

# 重載 Nginx
sudo systemctl reload nginx

# 檢查狀態
sudo systemctl status nginx
```

---

## 🌐 Cloudflare 設定（重要！）

### 1. DNS 設定

**Cloudflare Dashboard** → **DNS** → **Records**

| 類型 | 名稱 | 內容 | 代理狀態 | TTL |
|------|------|------|----------|-----|
| A | appai | [伺服器IP] | 已代理（🟠） | Auto |

**關鍵**:
- ✅ 代理狀態必須為「已代理」（橙色雲）
- ✅ 指向伺服器真實 IP

### 2. SSL/TLS 模式設定

**SSL/TLS** → **Overview**

**推薦設定**: `Full (Strict)`

| SSL 模式 | 說明 | 伺服器需求 | 安全性 |
|----------|------|-----------|--------|
| **Full (Strict)** | 端到端加密，驗證憑證 | 有效 SSL 憑證 | ⭐⭐⭐⭐⭐ |
| Full | 端到端加密，不驗證憑證 | 自簽憑證即可 | ⭐⭐⭐⭐ |
| Flexible | CF到源站用 HTTP | 無需 SSL | ⭐⭐ (不推薦) |

**設定步驟**:
1. Cloudflare Dashboard → **SSL/TLS** → **Overview**
2. 選擇 `Full (Strict)`
3. 等待約 1-2 分鐘生效

### 3. Edge Certificates 設定

**SSL/TLS** → **Edge Certificates**

**Always Use HTTPS**: `ON`
- 自動將 HTTP 跳轉到 HTTPS
- 避免在 Nginx 重複跳轉造成 Redirect Loop

**Minimum TLS Version**: `TLS 1.2`

**Automatic HTTPS Rewrites**: `ON`

### 4. 檢查 Page Rules

**Rules** → **Page Rules**

**重要**: 確保沒有多餘的 redirect 規則造成迴圈

如果有 `appai.tiankai.it.com/*` 相關規則，請檢查是否會造成衝突

---

## 🧪 測試與驗證

### 測試 1: 後端服務

```bash
# 檢查後端端口
netstat -tlnp | grep :18001

# 測試後端回應
curl http://127.0.0.1:18001/
curl http://127.0.0.1:18001/health
```

### 測試 2: Nginx 配置

```bash
# 測試配置語法
sudo nginx -t

# 預期輸出:
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration file /etc/nginx/nginx.conf test is successful

# 檢查是否有 http2 警告（應該沒有）
sudo nginx -t 2>&1 | grep deprecated
```

### 測試 3: HTTP 跳轉

```bash
# 測試 HTTP → HTTPS 跳轉
curl -I http://appai.tiankai.it.com

# 預期結果:
# HTTP/1.1 301 Moved Permanently
# Location: https://appai.tiankai.it.com/
```

### 測試 4: HTTPS 訪問

```bash
# 測試 HTTPS
curl -I https://appai.tiankai.it.com

# 預期結果:
# HTTP/2 200 OK (或 301/302，但不應該是 522/525)

# 詳細測試
curl -vkI https://appai.tiankai.it.com
```

### 測試 5: SSL 憑證

```bash
# 檢查 SSL 憑證
openssl s_client -connect appai.tiankai.it.com:443 -servername appai.tiankai.it.com

# 檢查項目:
# ✅ Verify return code: 0 (ok)
# ✅ subject=/CN=appai.tiankai.it.com
# ✅ issuer (Let's Encrypt 或 Cloudflare)
# ✅ Certificate chain
```

### 測試 6: 完整功能測試

```bash
# 測試 API 端點（根據你的實際 API）
curl -X GET https://appai.tiankai.it.com/api/v1/
curl -X GET https://appai.tiankai.it.com/health
curl -X GET https://appai.tiankai.it.com/docs
```

---

## 🐛 問題排查

### 問題 1: HTTP 522 錯誤

**錯誤**: Cloudflare 無法連接到源服務器

**檢查項目**:
```bash
# 1. Nginx 是否運行
sudo systemctl status nginx

# 2. 端口是否監聽
netstat -tlnp | grep :443

# 3. 防火牆設定
sudo ufw status
sudo ufw allow 443/tcp
sudo ufw allow 80/tcp

# 4. 測試本地 HTTPS
curl -k https://127.0.0.1/
```

**解決方法**:
- 啟動 Nginx: `sudo systemctl start nginx`
- 開放端口: `sudo ufw allow 443/tcp`
- 檢查憑證路徑是否正確

### 問題 2: HTTP 525 錯誤

**錯誤**: SSL 握手失敗

**原因**:
- Cloudflare 模式為 `Full (Strict)` 但伺服器憑證無效
- 憑證路徑錯誤
- 憑證過期

**檢查**:
```bash
# 檢查憑證是否存在
ls -l /etc/letsencrypt/live/appai.tiankai.it.com/
# 或
ls -l /etc/ssl/cloudflare/appai.tiankai.it.com.*

# 檢查憑證有效期
openssl x509 -in /etc/letsencrypt/live/appai.tiankai.it.com/fullchain.pem -noout -dates
# 或
openssl x509 -in /etc/ssl/cloudflare/appai.tiankai.it.com.pem -noout -dates

# 檢查憑證權限
ls -l /etc/ssl/cloudflare/
```

**解決方法**:
- 重新申請憑證
- 將 Cloudflare SSL 模式改為 `Full`（暫時）
- 檢查並修正憑證路徑

### 問題 3: Redirect Loop

**錯誤**: 瀏覽器提示「重定向次數過多」

**原因**: Cloudflare 和 Nginx 雙重跳轉

**檢查**:
```bash
# 檢查 Nginx HTTP server 配置
sudo grep -A 10 "listen 80" /etc/nginx/sites-available/appai.tiankai.it.com.conf

# 檢查是否有 return 301
```

**解決方法**:

**方案 A**: 移除 Nginx HTTP 跳轉（推薦）
```nginx
server {
    listen 80;
    server_name appai.tiankai.it.com;

    # 不要跳轉！直接提供服務
    location / {
        proxy_pass http://127.0.0.1:18001;
        ...
    }
}
```

**方案 B**: 使用條件跳轉
```nginx
server {
    listen 80;
    server_name appai.tiankai.it.com;

    # 只在非 HTTPS 時跳轉
    if ($http_x_forwarded_proto != "https") {
        return 301 https://$host$request_uri;
    }

    location / {
        proxy_pass http://127.0.0.1:18001;
        ...
    }
}
```

### 問題 4: HTTP/2 警告仍存在

**錯誤**: `the 'listen ... http2' directive is deprecated`

**檢查**:
```bash
# 搜尋所有包含舊語法的配置
sudo grep -r "listen.*http2" /etc/nginx/

# 檢查當前配置
sudo cat /etc/nginx/sites-available/appai.tiankai.it.com.conf | grep -A 2 "listen 443"
```

**正確語法**:
```nginx
server {
    # ❌ 舊語法
    # listen 443 ssl http2;

    # ✅ 新語法
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;

    server_name appai.tiankai.it.com;
    ...
}
```

### 問題 5: 後端服務未運行

**檢查**:
```bash
# 檢查端口
netstat -tlnp | grep :18001

# 如果無結果，啟動後端服務
# (根據你的實際啟動方式)
```

---

## 📊 日誌檢查

### Nginx 日誌

```bash
# 訪問日誌
sudo tail -f /var/log/nginx/appai.tiankai.it.com-access.log

# 錯誤日誌
sudo tail -f /var/log/nginx/appai.tiankai.it.com-error.log

# Nginx 主錯誤日誌
sudo tail -f /var/log/nginx/error.log

# 搜尋特定錯誤
sudo grep "appai.tiankai.it.com" /var/log/nginx/error.log | tail -20
```

### 系統日誌

```bash
# Nginx 服務日誌
sudo journalctl -u nginx -f

# 系統日誌
sudo journalctl -xe
```

---

## 🔄 回滾步驟

如果部署出現問題，可以回滾到之前的配置：

```bash
# 列出備份
ls -lt /etc/nginx/sites-available/appai.tiankai.it.com.conf.backup.*

# 恢復備份（使用最新的備份）
LATEST_BACKUP=$(ls -t /etc/nginx/sites-available/appai.tiankai.it.com.conf.backup.* | head -1)
sudo cp $LATEST_BACKUP /etc/nginx/sites-available/appai.tiankai.it.com.conf

# 測試並重載
sudo nginx -t && sudo systemctl reload nginx
```

---

## 📋 部署檢查清單

### 部署前
- [ ] 後端服務在 port 18001 正常運行
- [ ] 伺服器防火牆已開放 80/443 端口
- [ ] DNS 已更新（A 記錄指向伺服器 IP）

### Nginx 配置
- [ ] 配置文件已複製到 `/etc/nginx/sites-available/`
- [ ] 符號連結已創建到 `/etc/nginx/sites-enabled/`
- [ ] 使用新的 http2 語法（`http2 on;`）
- [ ] `sudo nginx -t` 無錯誤
- [ ] 憑證路徑正確

### SSL 憑證
- [ ] Let's Encrypt 憑證已申請 或
- [ ] Cloudflare Origin Certificate 已安裝
- [ ] 憑證權限正確（pem: 644, key: 600）

### Cloudflare 設定
- [ ] DNS A 記錄已添加（appai → 伺服器IP）
- [ ] 代理狀態為「已代理」（橙色雲）
- [ ] SSL/TLS 模式為 `Full (Strict)`
- [ ] Always Use HTTPS = ON
- [ ] 無多餘的 Page Rules

### 測試驗證
- [ ] HTTP 自動跳轉到 HTTPS
- [ ] HTTPS 訪問返回 200
- [ ] 無 Redirect Loop
- [ ] 無 522/525 錯誤
- [ ] SSL 憑證有效
- [ ] 後端 API 正常回應

---

## 📚 相關文檔

- **Nginx 配置**: `nginx/appai.tiankai.it.com.conf`
- **部署腳本**: `deploy_appai.sh`
- **Cloudflare 指南**: `CLOUDFLARE_NGINX_FIX_GUIDE.md`

---

## 🆘 快速命令參考

```bash
# 部署
sudo ./deploy_appai.sh

# 手動部署
sudo cp nginx/appai.tiankai.it.com.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/appai.tiankai.it.com.conf /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# SSL 憑證 (Let's Encrypt)
sudo certbot certonly --nginx -d appai.tiankai.it.com

# 測試
curl -I https://appai.tiankai.it.com
curl -vkI https://appai.tiankai.it.com

# 日誌
sudo tail -f /var/log/nginx/appai.tiankai.it.com-error.log

# 重載 Nginx
sudo nginx -t && sudo systemctl reload nginx

# 回滾
sudo cp /etc/nginx/sites-available/appai.tiankai.it.com.conf.backup.* \
     /etc/nginx/sites-available/appai.tiankai.it.com.conf
sudo nginx -t && sudo systemctl reload nginx
```

---

**部署日期**: 2025-10-08
**維護**: Claude Code
**狀態**: Production Ready ✅
