# 🚀 立即執行部署（複製貼上即可）

## 當前狀態

✅ **已完成**：
- Cloudflare DNS 配置成功（appai.tiankai.it.com → 146.88.134.254）
- SSL 憑證已生成（/tmp/app_ssl.pem）
- Nginx 配置已準備好（nginx/appai.tiankai.it.com.conf.fixed）

⚠️ **待執行**（需要 root 權限）：
- 安裝 SSL 憑證到 /etc/ssl/cloudflare/
- 更新 Nginx 配置
- 重載 Nginx
- 啟動後端服務

---

## 方案 A：一鍵安裝（推薦）

**只需一個命令**（會要求輸入 sudo 密碼）：

```bash
sudo ./install_all.sh
```

**完成後測試**：

```bash
curl https://appai.tiankai.it.com/health
```

---

## 方案 B：手動執行（逐步）

### 步驟 1：安裝 SSL 憑證

```bash
sudo mkdir -p /etc/ssl/cloudflare
sudo cp /tmp/app_ssl.pem /etc/ssl/cloudflare/
sudo cp /tmp/app_ssl.key /etc/ssl/cloudflare/
sudo chmod 644 /etc/ssl/cloudflare/app_ssl.pem
sudo chmod 600 /etc/ssl/cloudflare/app_ssl.key
```

**驗證**：
```bash
ls -l /etc/ssl/cloudflare/
```

預期輸出：
```
-rw-r--r-- 1 root root ... app_ssl.pem
-rw------- 1 root root ... app_ssl.key
```

### 步驟 2：更新 Nginx 配置

```bash
# 備份現有配置
sudo cp /etc/nginx/sites-available/appai.tiankai.it.com.conf \
        /etc/nginx/sites-available/appai.tiankai.it.com.conf.backup.$(date +%Y%m%d_%H%M%S)

# 應用新配置
sudo cp nginx/appai.tiankai.it.com.conf.fixed \
        /etc/nginx/sites-available/appai.tiankai.it.com.conf
```

**驗證**：
```bash
sudo nginx -t
```

預期輸出：
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 步驟 3：重載 Nginx

```bash
sudo systemctl reload nginx
sudo systemctl status nginx
```

### 步驟 4：啟動後端服務

**檢查是否已運行**：
```bash
netstat -tlnp | grep :18001
```

**如果未運行，啟動它**：
```bash
./start_appai_api.sh
```

**或手動啟動**：
```bash
source venv/bin/activate
nohup uvicorn app.api.main:app --host 0.0.0.0 --port 18001 --workers 2 > logs/appai_api.log 2>&1 &
```

**驗證後端**：
```bash
curl http://127.0.0.1:18001/health
```

預期輸出：
```json
{"status":"ok"}
```

### 步驟 5：測試外網訪問

```bash
# 測試 HTTPS
curl https://appai.tiankai.it.com/health

# 查看詳細信息
curl -I https://appai.tiankai.it.com

# 測試 HTTP/2
curl -I https://appai.tiankai.it.com --http2
```

---

## 完整驗證

```bash
./verify_deployment.sh
```

---

## 快速排錯

### 問題 1：nginx -t 失敗

```bash
# 查看詳細錯誤
sudo nginx -t

# 檢查憑證
ls -l /etc/ssl/cloudflare/app_ssl.*

# 檢查配置文件
sudo cat /etc/nginx/sites-available/appai.tiankai.it.com.conf | grep ssl_certificate
```

### 問題 2：HTTP 522 錯誤

```bash
# 檢查後端是否運行
netstat -tlnp | grep :18001

# 啟動後端
./start_appai_api.sh

# 查看後端日誌
tail -f logs/appai_api.log
```

### 問題 3：HTTP 521 錯誤（Web server is down）

```bash
# 檢查 Nginx 狀態
sudo systemctl status nginx

# 重啟 Nginx
sudo systemctl restart nginx

# 查看 Nginx 錯誤日誌
sudo tail -f /var/log/nginx/appai.tiankai.it.com-error.log
```

---

## 所有命令合集（一次複製）

如果您想一次性複製所有命令：

```bash
# === 完整安裝腳本（需要 sudo） ===

# 1. 安裝憑證
sudo mkdir -p /etc/ssl/cloudflare && \
sudo cp /tmp/app_ssl.pem /etc/ssl/cloudflare/ && \
sudo cp /tmp/app_ssl.key /etc/ssl/cloudflare/ && \
sudo chmod 644 /etc/ssl/cloudflare/app_ssl.pem && \
sudo chmod 600 /etc/ssl/cloudflare/app_ssl.key && \
echo "✅ 憑證已安裝"

# 2. 更新 Nginx 配置
sudo cp /etc/nginx/sites-available/appai.tiankai.it.com.conf \
        /etc/nginx/sites-available/appai.tiankai.it.com.conf.backup.$(date +%Y%m%d_%H%M%S) && \
sudo cp nginx/appai.tiankai.it.com.conf.fixed \
        /etc/nginx/sites-available/appai.tiankai.it.com.conf && \
echo "✅ Nginx 配置已更新"

# 3. 測試並重載 Nginx
sudo nginx -t && \
sudo systemctl reload nginx && \
echo "✅ Nginx 已重載"

# 4. 測試訪問
sleep 3 && \
curl https://appai.tiankai.it.com/health
```

---

## 預期最終結果

✅ **DNS 解析**：
```bash
$ dig +short appai.tiankai.it.com @1.1.1.1
104.21.37.62
172.67.205.6
```

✅ **HTTPS 訪問**：
```bash
$ curl https://appai.tiankai.it.com/health
{"status":"ok"}
```

✅ **Nginx 測試**：
```bash
$ sudo nginx -t
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

✅ **後端運行**：
```bash
$ netstat -tlnp | grep :18001
tcp   0   0 0.0.0.0:18001   0.0.0.0:*   LISTEN   12345/python3.11
```

---

## 時間預估

- **方案 A（一鍵）**：1-2 分鐘
- **方案 B（手動）**：3-5 分鐘

---

## 需要幫助？

1. 查看完整文檔：`COMPLETE_DEPLOYMENT_GUIDE.md`
2. 查看 Nginx 修復：`NGINX_APPAI_FIX_GUIDE.md`
3. 執行驗證腳本：`./verify_deployment.sh`

---

**準備好了嗎？複製上面的命令開始部署！** 🚀
