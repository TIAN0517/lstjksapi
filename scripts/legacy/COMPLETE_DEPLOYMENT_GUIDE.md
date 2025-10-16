# BossJy-Pro 完整部署指南

## 📋 概述

本指南將幫助您完成 `appai.tiankai.it.com` 的完整部署，包括：
- ✅ Cloudflare DNS 自動配置
- ✅ Nginx 配置修復
- ✅ SSL 憑證設置
- ✅ 健康檢查端點
- ✅ 完整驗證流程

**當前狀態**：
- 域名：`tiankai.it.com`（綁在其他機器）
- 目標子域名：`appai.tiankai.it.com`
- 當前機器 IP：`146.88.134.254`
- 後端服務埠：`18001`
- Cloudflare API Token：已驗證 ✅

---

## 🚀 快速部署（3 步完成）

### 步驟 1：配置 Cloudflare DNS

```bash
# 自動創建 DNS 記錄並配置 SSL/TLS
./cloudflare_dns_setup.sh
```

**此腳本會自動**：
1. ✅ 驗證 Cloudflare API Token
2. ✅ 獲取 `tiankai.it.com` 的 Zone ID
3. ✅ 創建 A 記錄：`appai.tiankai.it.com` → `146.88.134.254`
4. ✅ 啟用 Cloudflare Proxy（橙色雲）
5. ✅ 設置 SSL/TLS 為 `Full (Strict)`
6. ✅ 啟用 `Always Use HTTPS`
7. ✅ 設置最小 TLS 版本為 1.2
8. ✅ 驗證 DNS 解析
9. ✅ 測試 HTTPS 訪問

**預期輸出**：
```
✅ API Token 驗證成功
✅ Zone ID: xxxxxxxxxx
✅ DNS 記錄操作成功
✅ SSL 模式已設置為 Full (Strict)
✅ Always Use HTTPS 已啟用
✅ 最小 TLS 版本已設置為 1.2
✅ 配置完成！
```

### 步驟 2：修復 Nginx 配置

```bash
# 以 root 權限執行
sudo ./fix_appai_nginx.sh
```

**此腳本會自動**：
1. ✅ 檢查 Cloudflare 憑證是否存在
2. ✅ 備份現有 Nginx 配置
3. ✅ 更新配置使用 Cloudflare 憑證
4. ✅ 設置憑證權限（644/600）
5. ✅ 測試 Nginx 配置
6. ✅ 重載 Nginx

**預期輸出**：
```
✅ 找到 Cloudflare 憑證
✅ 已備份現有配置
✅ Nginx 配置已更新
✅ 憑證權限已設置
✅ Nginx 配置測試通過
✅ Nginx 已重載
✅ 修復完成！
```

### 步驟 3：驗證部署

```bash
# 完整驗證
./verify_deployment.sh
```

**此腳本會檢查**：
1. ✅ Python 3.11 環境
2. ✅ SSL 憑證存在與權限
3. ✅ Nginx 配置語法
4. ✅ 服務運行狀態
5. ✅ 本地端點響應
6. ✅ DNS 解析
7. ✅ HTTPS 訪問
8. ✅ SSL/TLS 憑證鏈
9. ✅ HTTP/2 支持
10. ✅ 健康檢查端點

**預期輸出**：
```
✅ 通過: 20
❌ 失敗: 0
⚠️  警告: 0

🎉 所有關鍵測試通過！部署成功！
```

---

## 📝 詳細部署流程

### 前置檢查

```bash
# 1. 檢查當前目錄
pwd
# 應該在: /mnt/d/BossJy-Cn/BossJy-Cn

# 2. 檢查 Cloudflare 憑證
ls -l /etc/ssl/cloudflare/app_ssl.*
# 應該看到:
# -rw-r--r-- ... app_ssl.pem
# -rw------- ... app_ssl.key

# 3. 檢查後端服務
netstat -tlnp | grep :18001
# 如果沒有運行，執行:
./start_appai_api.sh
```

### A. Cloudflare DNS 配置

#### 手動配置（可選）

如果自動腳本失敗，可以手動在 Cloudflare Dashboard 配置：

1. **登入 Cloudflare**：https://dash.cloudflare.com
2. **選擇 Zone**：`tiankai.it.com`
3. **DNS Records** → **Add record**：
   - Type: `A`
   - Name: `appai`
   - IPv4 address: `146.88.134.254`
   - Proxy status: ✅ **Proxied**（橙色雲）
   - TTL: `Auto`

4. **SSL/TLS** → **Overview**：
   - Encryption mode: `Full (Strict)`

5. **SSL/TLS** → **Edge Certificates**：
   - Always Use HTTPS: `ON`
   - Minimum TLS Version: `TLS 1.2`

#### 驗證 DNS

```bash
# 使用 Cloudflare DNS 查詢
dig +short appai.tiankai.it.com @1.1.1.1

# 使用 nslookup
nslookup appai.tiankai.it.com 1.1.1.1

# 檢查是否返回 Cloudflare IP（代理模式）
# 如果返回 146.88.134.254，表示未啟用 Proxy
```

### B. Nginx 配置修復

#### 配置文件位置

- **源文件**：`nginx/appai.tiankai.it.com.conf.fixed`
- **目標位置**：`/etc/nginx/sites-available/appai.tiankai.it.com.conf`
- **符號連結**：`/etc/nginx/sites-enabled/appai.tiankai.it.com.conf`

#### 關鍵配置檢查

```bash
# 檢查 SSL 憑證配置
sudo grep ssl_certificate /etc/nginx/sites-available/appai.tiankai.it.com.conf

# 應該看到:
# ssl_certificate /etc/ssl/cloudflare/app_ssl.pem;
# ssl_certificate_key /etc/ssl/cloudflare/app_ssl.key;

# 檢查 http2 語法
sudo grep http2 /etc/nginx/sites-available/appai.tiankai.it.com.conf

# 應該看到:
# http2 on;
# 而不是: listen 443 ssl http2;
```

#### 測試配置

```bash
# 測試語法
sudo nginx -t

# 預期輸出:
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration file /etc/nginx/nginx.conf test is successful

# 重載 Nginx
sudo systemctl reload nginx

# 檢查狀態
sudo systemctl status nginx
```

### C. 後端服務啟動

#### 檢查服務狀態

```bash
# 檢查 port 18001
netstat -tlnp | grep :18001

# 檢查進程
ps aux | grep "uvicorn.*18001"
```

#### 啟動服務

```bash
# 使用啟動腳本
./start_appai_api.sh

# 或手動啟動
source venv/bin/activate
nohup uvicorn app.api.main:app --host 0.0.0.0 --port 18001 --workers 2 > logs/appai_api.log 2>&1 &
```

#### 測試本地端點

```bash
# 健康檢查
curl http://127.0.0.1:18001/health
# 預期: {"status":"ok"}

# 狀態檢查
curl http://127.0.0.1:18001/status
# 預期: {"status":"ok","timestamp":"...","python_version":"3.11.9"}
```

---

## 🧪 測試與驗證

### 1. 本地測試

```bash
# 測試後端
curl http://127.0.0.1:18001/health

# 測試 Nginx 本地 HTTPS（需要修改 hosts）
curl -k https://127.0.0.1/health -H "Host: appai.tiankai.it.com"
```

### 2. DNS 測試

```bash
# DNS 解析
dig appai.tiankai.it.com

# Cloudflare DNS
dig @1.1.1.1 appai.tiankai.it.com

# Google DNS
dig @8.8.8.8 appai.tiankai.it.com
```

### 3. HTTPS 測試

```bash
# 基本訪問
curl -I https://appai.tiankai.it.com

# 詳細信息
curl -vI https://appai.tiankai.it.com

# HTTP/2 測試
curl -I https://appai.tiankai.it.com --http2

# 健康檢查
curl https://appai.tiankai.it.com/health

# 狀態檢查
curl https://appai.tiankai.it.com/status
```

### 4. SSL/TLS 測試

```bash
# 檢查憑證鏈
echo | openssl s_client -connect appai.tiankai.it.com:443 -servername appai.tiankai.it.com

# 檢查 ALPN (HTTP/2)
echo | openssl s_client -connect appai.tiankai.it.com:443 -alpn h2,http/1.1

# 在線 SSL 測試
# https://www.ssllabs.com/ssltest/analyze.html?d=appai.tiankai.it.com
```

### 5. 完整驗證腳本

```bash
# 執行完整驗證
./verify_deployment.sh

# 查看詳細報告
./verify_deployment.sh | tee deployment_report.txt
```

---

## 🔧 問題排查

### 問題 1: DNS 未解析

**症狀**：`dig appai.tiankai.it.com` 無結果

**解決**：
```bash
# 重新執行 DNS 配置
./cloudflare_dns_setup.sh

# 等待 DNS 傳播（通常 1-5 分鐘）
watch -n 5 'dig +short appai.tiankai.it.com @1.1.1.1'

# 手動在 Cloudflare Dashboard 檢查
```

### 問題 2: HTTP 522 錯誤

**症狀**：訪問 `https://appai.tiankai.it.com` 返回 522

**原因**：後端服務未運行或 Nginx 未啟動

**解決**：
```bash
# 1. 檢查後端
netstat -tlnp | grep :18001
./start_appai_api.sh

# 2. 檢查 Nginx
sudo systemctl status nginx
sudo nginx -t
sudo systemctl restart nginx

# 3. 檢查日誌
sudo tail -f /var/log/nginx/appai.tiankai.it.com-error.log
tail -f logs/appai_api.log
```

### 問題 3: HTTP 525 錯誤

**症狀**：訪問返回 525 SSL handshake failed

**原因**：
- SSL 憑證配置錯誤
- Cloudflare SSL 模式不正確

**解決**：
```bash
# 1. 檢查憑證
ls -l /etc/ssl/cloudflare/app_ssl.*
sudo chmod 644 /etc/ssl/cloudflare/app_ssl.pem
sudo chmod 600 /etc/ssl/cloudflare/app_ssl.key

# 2. 檢查 Nginx 配置
sudo grep ssl_certificate /etc/nginx/sites-available/appai.tiankai.it.com.conf
sudo nginx -t

# 3. 檢查 Cloudflare SSL 模式
# 應為: Full (Strict)
./cloudflare_dns_setup.sh  # 重新設置
```

### 問題 4: Nginx 配置測試失敗

**症狀**：`nginx -t` 失敗

**解決**：
```bash
# 查看詳細錯誤
sudo nginx -t

# 常見問題：
# 1. 憑證路徑錯誤
sudo ls -l /etc/ssl/cloudflare/app_ssl.*

# 2. 語法錯誤
sudo ./fix_appai_nginx.sh  # 重新應用配置

# 3. 回滾到備份
sudo cp /etc/nginx/sites-available/appai.tiankai.it.com.conf.backup.* \
        /etc/nginx/sites-available/appai.tiankai.it.com.conf
sudo nginx -t
```

### 問題 5: 後端服務無法啟動

**症狀**：`./start_appai_api.sh` 失敗

**解決**：
```bash
# 查看日誌
cat logs/appai_api.log

# 常見問題：
# 1. 缺少依賴
source venv/bin/activate
pip install -r requirements.txt

# 2. 端口被佔用
sudo lsof -i :18001
sudo kill -9 <PID>

# 3. 權限問題
chmod +x start_appai_api.sh
```

---

## 📊 監控與維護

### 日誌位置

```bash
# Nginx 訪問日誌
sudo tail -f /var/log/nginx/appai.tiankai.it.com-access.log

# Nginx 錯誤日誌
sudo tail -f /var/log/nginx/appai.tiankai.it.com-error.log

# 後端應用日誌
tail -f logs/appai_api.log

# 系統日誌
sudo journalctl -u nginx -f
```

### 健康檢查

```bash
# 定期檢查（每 5 分鐘）
*/5 * * * * /mnt/d/BossJy-Cn/BossJy-Cn/verify_deployment.sh >> /var/log/deployment_check.log 2>&1

# 手動檢查
./verify_deployment.sh
```

### 性能監控

```bash
# Nginx 連接數
sudo netstat -an | grep :443 | wc -l

# 後端響應時間
curl -o /dev/null -s -w "Total: %{time_total}s\n" https://appai.tiankai.it.com/health

# 完整性能測試（如果安裝了 ab）
ab -n 100 -c 10 https://appai.tiankai.it.com/health
```

---

## 🔐 安全建議

1. **定期更新憑證**：Cloudflare Origin Certificate 有效期 15 年
2. **監控訪問日誌**：檢查異常請求
3. **啟用防火牆**：
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```
4. **限制後端訪問**：確保 18001 只能本地訪問
5. **定期備份配置**：
   ```bash
   sudo cp /etc/nginx/sites-available/appai.tiankai.it.com.conf \
           ~/nginx_backup_$(date +%Y%m%d).conf
   ```

---

## 📁 文件清單

| 文件 | 用途 |
|------|------|
| `cloudflare_dns_setup.sh` | Cloudflare DNS 自動配置 |
| `fix_appai_nginx.sh` | Nginx 配置修復 |
| `verify_deployment.sh` | 部署驗證 |
| `start_appai_api.sh` | 後端服務啟動 |
| `nginx/appai.tiankai.it.com.conf.fixed` | 修復後的 Nginx 配置 |
| `COMPLETE_DEPLOYMENT_GUIDE.md` | 本指南 |
| `NGINX_APPAI_FIX_GUIDE.md` | Nginx 修復指南 |
| `DEPLOY_APPAI_CLOUDFLARE_FIX.md` | Cloudflare 修復說明 |

---

## ✅ 部署檢查清單

部署前：
- [ ] Cloudflare API Token 已驗證
- [ ] Cloudflare 憑證已上傳到 `/etc/ssl/cloudflare/`
- [ ] Python 3.11 環境已安裝
- [ ] Nginx 已安裝
- [ ] 虛擬環境已創建（venv）

部署中：
- [ ] 執行 `./cloudflare_dns_setup.sh`
- [ ] 執行 `sudo ./fix_appai_nginx.sh`
- [ ] 啟動後端服務 `./start_appai_api.sh`

部署後：
- [ ] 執行 `./verify_deployment.sh` 全部通過
- [ ] DNS 解析正確
- [ ] HTTPS 訪問正常
- [ ] `/health` 端點返回 200
- [ ] `/status` 端點返回正確數據

---

**更新日期**：2025-10-08
**版本**：1.0
**狀態**：Production Ready ✅
