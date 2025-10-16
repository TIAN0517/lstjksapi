# Cloudflare + Nginx 修復指南

## 🎯 問題診斷與解決方案

### 問題 1: Cloudflare Redirect Loop (重定向迴圈)
### 問題 2: Nginx HTTP/2 警告訊息

---

## 📋 修復清單

### ✅ 已完成
1. **HTTP/2 語法更新** - 將 `listen 443 ssl http2;` 改為 `listen 443 ssl; http2 on;`
2. **創建 gasapi.jytian.it.com 配置** - 避免重定向衝突
3. **安全標頭優化** - 加入 HSTS, X-Frame-Options 等

---

## 🔧 修復步驟

### 步驟 1: 更新 Nginx 配置

#### 1.1 修復 app.tiankai.it.com

```bash
# 備份現有配置
sudo cp /etc/nginx/sites-available/app.tiankai.it.com.conf \
     /etc/nginx/sites-available/app.tiankai.it.com.conf.backup.$(date +%Y%m%d)

# 複製修正後的配置
sudo cp nginx/app.tiankai.it.com-fixed.conf \
     /etc/nginx/sites-available/app.tiankai.it.com.conf

# 測試配置
sudo nginx -t

# 如果測試通過，重載 Nginx
sudo systemctl reload nginx
```

#### 1.2 部署 gasapi.jytian.it.com

```bash
# 複製配置文件
sudo cp nginx/gasapi.jytian.it.com.conf \
     /etc/nginx/sites-available/gasapi.jytian.it.com.conf

# 創建符號連結
sudo ln -s /etc/nginx/sites-available/gasapi.jytian.it.com.conf \
           /etc/nginx/sites-enabled/

# 測試配置
sudo nginx -t

# 重載 Nginx
sudo systemctl reload nginx
```

---

## 🌐 Cloudflare 配置（重要！）

### 問題根因：Redirect Loop 的三種情況

#### 情況 A: SSL/TLS 模式錯誤
**問題**: Cloudflare 設為 `Flexible`，但 Nginx 強制跳轉 HTTPS
**解決**: 改為 `Full` 或 `Full (Strict)`

#### 情況 B: 雙重跳轉
**問題**: Cloudflare 和 Nginx 都在做 HTTP → HTTPS 跳轉
**解決**: 只在一邊做跳轉

#### 情況 C: 憑證不匹配
**問題**: SSL 模式為 `Full (Strict)` 但伺服器憑證無效
**解決**: 使用有效憑證（Let's Encrypt 或 Cloudflare Origin Certificate）

---

## 🔒 Cloudflare SSL/TLS 設定（正確方法）

### 步驟 1: 選擇 SSL/TLS 加密模式

登入 Cloudflare → 選擇域名 → **SSL/TLS** → **Overview**

#### 方案 A: Full (Strict) - **強烈推薦**

```
使用時機：伺服器有有效的 SSL 憑證
優點：端到端加密，最安全
配置：
  - Cloudflare 模式：Full (Strict)
  - Nginx：需要有效憑證（Let's Encrypt 或 Cloudflare Origin Cert）
  - HTTP 跳轉：在 Nginx 做
```

**Nginx 配置**（gasapi.jytian.it.com）:
```nginx
# HTTP server
server {
    listen 80;
    server_name gasapi.jytian.it.com;

    # 檢查 X-Forwarded-Proto 避免迴圈
    if ($http_x_forwarded_proto != "https") {
        return 301 https://$host$request_uri;
    }

    # 或者直接提供服務，讓 Cloudflare 處理跳轉
    location / {
        proxy_pass http://127.0.0.1:8080;
        ...
    }
}

# HTTPS server
server {
    listen 443 ssl;
    http2 on;
    server_name gasapi.jytian.it.com;

    ssl_certificate /etc/letsencrypt/live/gasapi.jytian.it.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/gasapi.jytian.it.com/privkey.pem;
    ...
}
```

#### 方案 B: Full（不驗證憑證）

```
使用時機：伺服器使用自簽憑證
優點：簡單，不需管理憑證
配置：
  - Cloudflare 模式：Full
  - Nginx：自簽憑證即可
  - HTTP 跳轉：在 Cloudflare 做
```

**Cloudflare 設置**:
- **SSL/TLS** → **Overview** → 選擇 `Full`
- **SSL/TLS** → **Edge Certificates** → `Always Use HTTPS` → **ON**

**Nginx 配置**:
```nginx
# HTTP server - 不要做跳轉！
server {
    listen 80;
    server_name gasapi.jytian.it.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        ...
    }
}
```

#### 方案 C: Flexible（不推薦）

```
使用時機：伺服器無法配置 HTTPS
缺點：Cloudflare 到源站是 HTTP（不安全）
配置：
  - Cloudflare 模式：Flexible
  - Nginx：只監聽 80 端口
  - HTTP 跳轉：在 Cloudflare 做
```

---

### 步驟 2: 配置 Cloudflare Origin Certificate（推薦）

#### 2.1 生成 Origin Certificate

1. Cloudflare Dashboard → **SSL/TLS** → **Origin Server**
2. 點擊 **Create Certificate**
3. 選擇：
   - **Private key type**: RSA (2048)
   - **Hostnames**: `gasapi.jytian.it.com`, `*.jytian.it.com`
   - **Certificate validity**: 15 years
4. 點擊 **Create**
5. 複製 **Origin Certificate** 和 **Private Key**

#### 2.2 安裝憑證到伺服器

```bash
# 創建目錄
sudo mkdir -p /etc/ssl/cloudflare

# 保存 Origin Certificate
sudo nano /etc/ssl/cloudflare/gasapi.jytian.it.com.pem
# 貼上 Origin Certificate

# 保存 Private Key
sudo nano /etc/ssl/cloudflare/gasapi.jytian.it.com.key
# 貼上 Private Key

# 設置權限
sudo chmod 644 /etc/ssl/cloudflare/gasapi.jytian.it.com.pem
sudo chmod 600 /etc/ssl/cloudflare/gasapi.jytian.it.com.key
```

#### 2.3 更新 Nginx 配置

```nginx
server {
    listen 443 ssl;
    http2 on;
    server_name gasapi.jytian.it.com;

    # 使用 Cloudflare Origin Certificate
    ssl_certificate /etc/ssl/cloudflare/gasapi.jytian.it.com.pem;
    ssl_certificate_key /etc/ssl/cloudflare/gasapi.jytian.it.com.key;
    ...
}
```

---

### 步驟 3: 其他 Cloudflare 設定

#### 3.1 Always Use HTTPS

**SSL/TLS** → **Edge Certificates** → **Always Use HTTPS** → **ON**

這會在 Cloudflare 層級處理 HTTP → HTTPS 跳轉

#### 3.2 HSTS（可選）

**SSL/TLS** → **Edge Certificates** → **HTTP Strict Transport Security (HSTS)**

```
Status: Enabled
Max Age: 6 months
Include Subdomains: On
Preload: Off (除非確定要加入瀏覽器預載清單)
```

#### 3.3 Minimum TLS Version

**SSL/TLS** → **Edge Certificates** → **Minimum TLS Version** → `TLS 1.2`

---

## 🧪 測試與驗證

### 測試 1: 檢查 DNS 解析

```bash
dig +short gasapi.jytian.it.com
nslookup gasapi.jytian.it.com
```

應該返回 Cloudflare 的 IP

### 測試 2: 測試 HTTP 跳轉

```bash
curl -I http://gasapi.jytian.it.com

# 預期結果（Full/Full Strict 模式）:
HTTP/1.1 301 Moved Permanently
Location: https://gasapi.jytian.it.com/
```

### 測試 3: 測試 HTTPS 連接

```bash
curl -I https://gasapi.jytian.it.com

# 預期結果:
HTTP/2 200 OK
或
HTTP/2 301/302（如果有額外跳轉）

# 不應該出現:
HTTP/2 525 (SSL Handshake Failed)
HTTP/2 522 (Connection Timed Out)
Redirect Loop
```

### 測試 4: 檢查 SSL 憑證

```bash
openssl s_client -connect gasapi.jytian.it.com:443 -servername gasapi.jytian.it.com

# 檢查輸出中的:
# - Verify return code: 0 (ok)
# - subject=/CN=gasapi.jytian.it.com
# - issuer（Cloudflare 或 Let's Encrypt）
```

### 測試 5: 完整 Curl 測試

```bash
curl -vkI https://gasapi.jytian.it.com 2>&1 | grep -E "HTTP|Location|SSL|TLS"

# 查看:
# - TLS 版本（應為 TLSv1.2 或 TLSv1.3）
# - HTTP/2（如果啟用）
# - 無 Redirect Loop
```

### 測試 6: 檢查 Nginx 日誌

```bash
# 錯誤日誌（不應該有 http2 警告）
sudo tail -f /var/log/nginx/gasapi.jytian.it.com-error.log

# 訪問日誌
sudo tail -f /var/log/nginx/gasapi.jytian.it.com-access.log
```

---

## 🐛 常見問題排查

### 問題 A: 仍然出現 Redirect Loop

**檢查項目**:
```bash
# 1. Cloudflare SSL 模式
curl -I https://gasapi.jytian.it.com | grep "cf-cache-status"

# 2. Nginx 配置
sudo nginx -T | grep -A 20 "gasapi.jytian.it.com"

# 3. 檢查 HTTP server 是否有跳轉
sudo nginx -T | grep -B 5 -A 10 "return 301"
```

**解決方法**:
1. 確認 Cloudflare SSL 模式為 `Full` 或 `Full (Strict)`
2. 移除 Nginx HTTP server 的 `return 301` 跳轉
3. 或使用條件跳轉（檢查 `$http_x_forwarded_proto`）

### 問題 B: HTTP 525 錯誤（SSL Handshake Failed）

**原因**: Cloudflare 無法驗證源站憑證

**解決**:
1. 檢查憑證是否過期: `openssl x509 -in /etc/ssl/cloudflare/gasapi.jytian.it.com.pem -noout -dates`
2. 檢查憑證權限: `ls -l /etc/ssl/cloudflare/`
3. 使用 Cloudflare Origin Certificate
4. 或將 SSL 模式改為 `Full`（不驗證憑證）

### 問題 C: HTTP 522 錯誤（Connection Timed Out）

**原因**: Cloudflare 無法連接到源站

**檢查**:
```bash
# 1. 檢查 Nginx 是否運行
sudo systemctl status nginx

# 2. 檢查端口監聽
netstat -tlnp | grep :443

# 3. 檢查防火牆
sudo ufw status
sudo ufw allow 443/tcp
sudo ufw allow 80/tcp

# 4. 測試本地連接
curl -k https://127.0.0.1:443
```

### 問題 D: HTTP/2 警告仍然存在

**檢查**:
```bash
sudo nginx -t

# 應該看到:
nginx: configuration file /etc/nginx/nginx.conf test is successful

# 不應該看到:
the 'listen ... http2' directive is deprecated
```

**如果仍有警告**:
```bash
# 檢查所有配置文件
sudo grep -r "listen.*http2" /etc/nginx/

# 更新所有包含舊語法的文件
sudo sed -i 's/listen \(.*\) ssl http2;/listen \1 ssl;\n    http2 on;/' /etc/nginx/sites-available/*.conf
```

---

## 📊 最佳實踐建議

### 1. SSL/TLS 配置

**推薦方案**:
```
Cloudflare: Full (Strict)
憑證: Cloudflare Origin Certificate (15年有效期)
優點: 零維護成本，自動續期
```

### 2. HTTP 跳轉策略

**推薦方案**:
```
Cloudflare: Always Use HTTPS = ON
Nginx HTTP server: 不做跳轉，直接提供服務
優點: 避免雙重跳轉，降低 Redirect Loop 風險
```

### 3. 安全標頭

```nginx
# HSTS（確定域名不需要 HTTP 再啟用）
add_header Strict-Transport-Security 'max-age=31536000; includeSubDomains; preload' always;

# XSS 防護
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;

# CSP（根據需求調整）
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline';" always;
```

### 4. 效能優化

```nginx
# HTTP/2
http2 on;

# SSL Session Cache
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;

# Gzip 壓縮
gzip on;
gzip_vary on;
gzip_types text/plain text/css application/json application/javascript;
```

---

## 📝 部署檢查清單

### 部署前
- [ ] 備份現有 Nginx 配置
- [ ] 準備 SSL 憑證（Let's Encrypt 或 Cloudflare Origin Cert）
- [ ] 確認後端服務運行正常（port 8080）

### Cloudflare 設定
- [ ] SSL/TLS 模式設為 `Full (Strict)` 或 `Full`
- [ ] Always Use HTTPS = **ON**
- [ ] Minimum TLS Version = `TLS 1.2`
- [ ] 生成並安裝 Origin Certificate（如使用 Full Strict）

### Nginx 配置
- [ ] 更新為新的 http2 語法（`http2 on;`）
- [ ] 移除或條件化 HTTP → HTTPS 跳轉
- [ ] 配置正確的 SSL 憑證路徑
- [ ] 設定安全標頭

### 測試
- [ ] `sudo nginx -t` 無警告
- [ ] HTTP 訪問自動跳轉到 HTTPS
- [ ] HTTPS 訪問正常回應（200）
- [ ] 無 Redirect Loop
- [ ] SSL Labs 測試 A+ 評級

### 監控
- [ ] 設定日誌輪替
- [ ] 配置錯誤告警
- [ ] 監控 5xx 錯誤率

---

## 🚀 快速部署命令

```bash
# 1. 備份
sudo cp /etc/nginx/sites-available/app.tiankai.it.com.conf \
     /etc/nginx/sites-available/app.tiankai.it.com.conf.backup.$(date +%Y%m%d)

# 2. 部署 app.tiankai.it.com
sudo cp nginx/app.tiankai.it.com-fixed.conf \
     /etc/nginx/sites-available/app.tiankai.it.com.conf

# 3. 部署 gasapi.jytian.it.com
sudo cp nginx/gasapi.jytian.it.com.conf \
     /etc/nginx/sites-available/gasapi.jytian.it.com.conf
sudo ln -s /etc/nginx/sites-available/gasapi.jytian.it.com.conf \
           /etc/nginx/sites-enabled/

# 4. 測試配置
sudo nginx -t

# 5. 重載 Nginx
sudo systemctl reload nginx

# 6. 檢查狀態
sudo systemctl status nginx
curl -I https://gasapi.jytian.it.com
```

---

## 📞 支持資源

### Nginx 文檔
- HTTP/2 配置: https://nginx.org/en/docs/http/ngx_http_v2_module.html
- SSL 配置: https://nginx.org/en/docs/http/configuring_https_servers.html

### Cloudflare 文檔
- SSL/TLS: https://developers.cloudflare.com/ssl/
- Origin Certificates: https://developers.cloudflare.com/ssl/origin-configuration/origin-ca/

### 測試工具
- SSL Labs: https://www.ssllabs.com/ssltest/
- Cloudflare Debug: https://www.cloudflare.com/lp/debug/

---

**最後更新**: 2025-10-08
**維護者**: Claude Code
**狀態**: Production Ready ✅
