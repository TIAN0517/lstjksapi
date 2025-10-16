# appai.tiankai.it.com Nginx 配置修復指南

## 🔴 當前問題

執行 `nginx -t` 時出現錯誤：
```
[emerg] cannot load certificate "/etc/letsencrypt/live/appai.tiankai.it.com/fullchain.pem":
BIO_new_file() failed (SSL: error:8000000D:system library::Permission denied)
```

### 問題原因
1. ❌ Nginx 配置使用了不存在的 Let's Encrypt 憑證
2. ❌ Cloudflare 憑證路徑錯誤（`appai.tiankai.it.com.pem` 應為 `app_ssl.pem`）
3. ⚠️  有舊的 http2 語法警告

## ✅ 解決方案

### 方法 1：使用自動修復腳本（推薦）

```bash
# 以 root 權限執行修復腳本
sudo ./fix_appai_nginx.sh
```

**腳本會自動**：
1. ✅ 檢查 Cloudflare 憑證是否存在
2. ✅ 備份現有配置
3. ✅ 更新為修復後的配置（使用 `app_ssl.pem`）
4. ✅ 設置憑證權限
5. ✅ 測試 Nginx 配置
6. ✅ 重載 Nginx

### 方法 2：手動修復

#### 步驟 1：備份現有配置
```bash
sudo cp /etc/nginx/sites-available/appai.tiankai.it.com.conf \
        /etc/nginx/sites-available/appai.tiankai.it.com.conf.backup
```

#### 步驟 2：更新配置
```bash
sudo cp nginx/appai.tiankai.it.com.conf.fixed \
        /etc/nginx/sites-available/appai.tiankai.it.com.conf
```

#### 步驟 3：檢查憑證權限
```bash
sudo chmod 644 /etc/ssl/cloudflare/app_ssl.pem
sudo chmod 600 /etc/ssl/cloudflare/app_ssl.key
```

#### 步驟 4：測試配置
```bash
sudo nginx -t
```

**預期輸出**：
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

#### 步驟 5：重載 Nginx
```bash
sudo systemctl reload nginx
```

## 📝 配置變更摘要

### 修改前（錯誤）
```nginx
# Let's Encrypt 憑證（未註解，檔案不存在）
ssl_certificate /etc/letsencrypt/live/appai.tiankai.it.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/appai.tiankai.it.com/privkey.pem;

# Cloudflare 憑證（已註解，且路徑錯誤）
# ssl_certificate /etc/ssl/cloudflare/appai.tiankai.it.com.pem;
# ssl_certificate_key /etc/ssl/cloudflare/appai.tiankai.it.com.key;
```

### 修改後（正確）
```nginx
# Let's Encrypt 憑證（已註解）
#ssl_certificate /etc/letsencrypt/live/appai.tiankai.it.com/fullchain.pem;
#ssl_certificate_key /etc/letsencrypt/live/appai.tiankai.it.com/privkey.pem;

# Cloudflare 憑證（啟用，使用 app_ssl.pem）
ssl_certificate /etc/ssl/cloudflare/app_ssl.pem;
ssl_certificate_key /etc/ssl/cloudflare/app_ssl.key;
```

## 🌐 外網訪問狀態

**當前狀態**: ✅ 外網可訪問

```bash
curl -I https://appai.tiankai.it.com
```

**測試結果**：
- HTTP/2 405 Method Not Allowed
- server: cloudflare
- cf-ray: 98b61edb4a4e8332-KIX

**說明**：
- ✅ Cloudflare CDN 工作正常
- ✅ SSL/TLS 連接正常
- ✅ HTTP/2 啟用成功
- ⚠️  後端可能需要檢查 (405 錯誤)

**IP**: 146.88.134.254 (Cloudflare CDN)

## 🔍 問題排查

### 檢查 Cloudflare 憑證
```bash
ls -l /etc/ssl/cloudflare/app_ssl.*
```

**預期輸出**：
```
-rw-r--r-- 1 root root XXXX Oct  X XX:XX /etc/ssl/cloudflare/app_ssl.pem
-rw------- 1 root root XXXX Oct  X XX:XX /etc/ssl/cloudflare/app_ssl.key
```

### 檢查後端服務
```bash
# 檢查 port 18001 是否監聽
netstat -tlnp | grep :18001

# 測試本地訪問
curl -I http://127.0.0.1:18001/
curl -I http://127.0.0.1:18001/health
```

### 檢查 Nginx 配置
```bash
# 查看當前 SSL 憑證配置
sudo cat /etc/nginx/sites-available/appai.tiankai.it.com.conf | grep -A 2 "ssl_certificate"

# 測試配置
sudo nginx -t
```

### 檢查 Nginx 狀態
```bash
sudo systemctl status nginx
```

## 📊 完整測試流程

### 1. 修復 Nginx 配置
```bash
sudo ./fix_appai_nginx.sh
```

### 2. 檢查後端服務
```bash
# 如果 port 18001 沒有運行，啟動它
cd /mnt/d/BossJy-Cn/BossJy-Cn
./start_appai_api.sh
```

### 3. 測試本地訪問
```bash
# 測試後端
curl http://127.0.0.1:18001/health

# 測試 Nginx (需要 hosts 或實際 DNS)
curl -H "Host: appai.tiankai.it.com" https://127.0.0.1/health
```

### 4. 測試外網訪問
```bash
# 基本訪問
curl -I https://appai.tiankai.it.com

# 健康檢查
curl https://appai.tiankai.it.com/health

# 狀態檢查
curl https://appai.tiankai.it.com/status
```

## 🎯 預期結果

修復後的預期結果：

### nginx -t
```
✅ nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
✅ nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 外網訪問
```bash
curl https://appai.tiankai.it.com/health
# {"status":"ok"}

curl https://appai.tiankai.it.com/status
# {"status":"ok","timestamp":"2025-10-08T13:52:45Z","python_version":"3.11.9"}
```

## 📁 相關文件

- **修復後的配置**: `nginx/appai.tiankai.it.com.conf.fixed`
- **修復腳本**: `fix_appai_nginx.sh`
- **部署腳本**: `deploy_appai.sh`
- **啟動腳本**: `start_appai_api.sh`

## 🆘 常見問題

### Q1: 修復腳本執行失敗
**A**: 確保使用 root 權限：`sudo ./fix_appai_nginx.sh`

### Q2: Cloudflare 憑證不存在
**A**: 確認憑證已上傳到：
- `/etc/ssl/cloudflare/app_ssl.pem`
- `/etc/ssl/cloudflare/app_ssl.key`

### Q3: nginx -t 仍然失敗
**A**: 檢查配置文件路徑和憑證權限：
```bash
sudo ls -l /etc/ssl/cloudflare/app_ssl.*
sudo cat /etc/nginx/sites-available/appai.tiankai.it.com.conf | grep ssl_certificate
```

### Q4: 外網訪問 502/522/525 錯誤
**A**:
- **502/522**: 後端服務未運行，啟動 `./start_appai_api.sh`
- **525**: SSL 握手失敗，檢查 Cloudflare SSL 模式應為 `Full (Strict)`

### Q5: 405 Method Not Allowed
**A**: 正常！這表示 Nginx 和後端都在工作，只是不支持該 HTTP 方法（如 HEAD 請求）。嘗試 GET 請求：
```bash
curl https://appai.tiankai.it.com/health
```

---

**更新日期**: 2025-10-08
**狀態**: Ready to Fix ✅
