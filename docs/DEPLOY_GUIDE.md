# BossJy-Pro 部署指南

本指南詳細說明如何在各種環境中部署 BossJy-Pro 企業級平台。

## 📋 部署前準備

### 系統要求

#### 最低配置
- **CPU**: 2 vCPU
- **記憶體**: 4GB RAM
- **存儲**: 80GB NVMe SSD
- **網路**: 100Mbps
- **操作系統**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+

#### 推薦配置
- **CPU**: 4 vCPU
- **記憶體**: 8-16GB RAM
- **存儲**: 160GB NVMe SSD
- **網路**: 1Gbps
- **操作系統**: Ubuntu 22.04 LTS

#### 高性能配置
- **CPU**: 8+ vCPU
- **記憶體**: 32GB+ RAM
- **存儲**: 320GB+ NVMe SSD
- **網路**: 1Gbps+
- **操作系統**: Ubuntu 22.04 LTS

### 依賴軟件

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y docker.io docker-compose curl wget git

# CentOS/RHEL
sudo yum update
sudo yum install -y docker docker-compose curl wget git

# 啟動 Docker 服務
sudo systemctl start docker
sudo systemctl enable docker

# 添加用戶到 docker 組
sudo usermod -aG docker $USER
```

## 🚀 快速部署

### 1. 獲取源碼

```bash
# 克隆項目
git clone https://github.com/lstjks/BossJy-Pro.git
cd BossJy-Pro

# 切換到最新版本
git checkout v1.6.0-integrated
```

### 2. 配置環境變數

```bash
# 複製環境變數範本
cp deploy/env/.env.example .env

# 編輯配置文件
nano .env
```

**重要配置項**：

```bash
# 資料庫配置
POSTGRES_DB=bossjy
POSTGRES_USER=bossjy
POSTGRES_PASSWORD=your_secure_password

# Redis 配置
REDIS_PASSWORD=your_redis_password

# JWT 密鑰 (請生成強密鑰)
JWT_SECRET_KEY=your_jwt_secret_key
SECRET_KEY=your_secret_key

# Telegram Bot Tokens
BOT1_TOKEN=your_bot1_token
BOT2_TOKEN=your_bot2_token
BOT3_TOKEN=your_bot3_token

# 域名配置
BOSSJY_DOMAIN=bossjy.yourdomain.com
APPAI_DOMAIN=appai.yourdomain.com
```

### 3. 啟動服務

```bash
# 創建必要的目錄
mkdir -p logs deploy/backups

# 啟動所有服務
docker-compose up -d --build

# 查看服務狀態
docker-compose ps
```

### 4. 驗證部署

```bash
# 運行驗收腳本
./scripts/verify_deployment.sh

# 手動檢查服務
curl -kI https://yourdomain.com/api/health
```

## 🌐 生產環境部署

### 域名和 SSL 配置

#### 1. 域名解析

將以下域名解析到您的服務器 IP：

```
bossjy.yourdomain.com → YOUR_SERVER_IP
appai.yourdomain.com → YOUR_SERVER_IP
```

#### 2. SSL 憑證配置

**選項 A: Let's Encrypt (推薦)**

```bash
# 安裝 certbot
sudo apt install certbot

# 生成憑證
sudo certbot certonly --standalone -d bossjy.yourdomain.com -d appai.yourdomain.com

# 複製憑證到項目目錄
sudo cp /etc/letsencrypt/live/bossjy.yourdomain.com/fullchain.pem deploy/nginx/ssl/bossjy.yourdomain.com.crt
sudo cp /etc/letsencrypt/live/bossjy.yourdomain.com/privkey.pem deploy/nginx/ssl/bossjy.yourdomain.com.key
sudo cp /etc/letsencrypt/live/appai.yourdomain.com/fullchain.pem deploy/nginx/ssl/appai.yourdomain.com.crt
sudo cp /etc/letsencrypt/live/appai.yourdomain.com/privkey.pem deploy/nginx/ssl/appai.yourdomain.com.key
```

**選項 B: Cloudflare Origin Certificate**

1. 在 Cloudflare 控制台生成 Origin Certificate
2. 下載憑證和私鑰
3. 放置到 `deploy/nginx/ssl/` 目錄

### 防火牆配置

```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 生產環境配置優化

#### 1. 系統內核參數

```bash
# 編輯 sysctl 配置
sudo nano /etc/sysctl.d/99-bossjy.conf
```

```
# 網絡優化
net.core.somaxconn = 4096
net.ipv4.ip_local_port_range = 10000 65000
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_tw_reuse = 1

# 文件描述符限制
fs.file-max = 1000000

# 虛擬內存優化
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
```

```bash
# 應用配置
sudo sysctl -p /etc/sysctl.d/99-bossjy.conf
```

#### 2. Docker 配置優化

```bash
# 編輯 Docker 配置
sudo nano /etc/docker/daemon.json
```

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "storage-opts": [
    "overlay2.override_kernel_check=true"
  ]
}
```

```bash
# 重啟 Docker
sudo systemctl restart docker
```

#### 3. 資料庫優化

```bash
# 進入 PostgreSQL 容器
docker exec -it bossjy-postgres psql -U bossjy -d bossjy

# 優化配置
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

# 重新加載配置
SELECT pg_reload_conf();
```

## 🔄 自動化部署

### GitHub Actions 部署

#### 1. 配置 Secrets

在 GitHub 倉庫中設置以下 Secrets：

```
VPS_HOST=your_server_ip
VPS_USER=your_username
VPS_SSH_KEY=your_private_ssh_key
POSTGRES_USER=your_postgres_user
POSTGRES_DB=your_postgres_db
```

#### 2. 觸發部署

```bash
# 手動觸發部署
gh workflow run deploy.yml

# 或推送標籤觸發自動部署
git tag v1.6.1
git push origin v1.6.1
```

### 腳本化部署

```bash
#!/bin/bash
# deploy.sh - 一鍵部署腳本

set -e

echo "🚀 開始部署 BossJy-Pro..."

# 檢查環境
if [ ! -f ".env" ]; then
    echo "❌ 找不到 .env 文件，請先配置環境變數"
    exit 1
fi

# 備份當前版本
if docker-compose ps | grep -q "Up"; then
    echo "💾 備份當前版本..."
    ./scripts/backup_restore.sh backup
fi

# 拉取最新代碼
echo "📥 拉取最新代碼..."
git pull origin main

# 建置並啟動服務
echo "🔨 建置並啟動服務..."
docker-compose down
docker-compose up -d --build

# 等待服務啟動
echo "⏳ 等待服務啟動..."
sleep 60

# 驗證部署
echo "🔍 驗證部署..."
./scripts/verify_deployment.sh

echo "✅ 部署完成！"
```

## 📊 監控和維護

### 日誌管理

```bash
# 查看所有服務日誌
docker-compose logs -f

# 查看特定服務日誌
docker-compose logs -f fastapi

# 清理舊日誌
docker system prune -f
```

### 性能監控

```bash
# 查看容器資源使用
docker stats

# 查看磁碟使用
df -h

# 查看記憶體使用
free -h
```

### 備份策略

```bash
# 自動備份腳本
cat > /etc/cron.daily/bossjy-backup << 'EOF'
#!/bin/bash
cd /opt/bossjy
./scripts/backup_restore.sh backup
EOF

chmod +x /etc/cron.daily/bossjy-backup
```

## 🔧 故障排除

### 常見問題

#### 1. 服務無法啟動

```bash
# 檢查配置
docker-compose config

# 查看詳細錯誤
docker-compose logs service_name

# 檢查端口占用
netstat -tulpn | grep :port
```

#### 2. 資料庫連線失敗

```bash
# 檢查資料庫狀態
docker exec bossjy-postgres pg_isready -U bossjy

# 檢查網路連線
docker network ls
docker network inspect bossjy_bossjy-network
```

#### 3. SSL 憑證問題

```bash
# 檢查憑證有效期
openssl x509 -in deploy/nginx/ssl/cert.pem -noout -dates

# 測試 SSL 配置
openssl s_client -connect yourdomain.com:443
```

#### 4. 性能問題

```bash
# 檢查系統負載
top
htop
iotop

# 檢查 Docker 資源使用
docker stats --no-stream

# 資料庫性能分析
docker exec bossjy-postgres psql -U bossjy -d bossjy -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;"
```

### 緊急恢復

```bash
# 快速回滾到上一版本
docker-compose down
git checkout previous_tag
docker-compose up -d

# 資料庫還原
./scripts/backup_restore.sh restore /path/to/backup.sql.gz
```

## 🔐 安全加固

### 系統安全

```bash
# 禁用 root SSH 登錄
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# 配置 fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# 定期更新系統
sudo apt update && sudo apt upgrade -y
```

### 應用安全

```bash
# 定期更新依賴
docker-compose pull
docker-compose up -d

# 掃描安全漏洞
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image bossjy-pro_fastapi:latest
```

## 📈 擴展部署

### 多節點部署

```yaml
# docker-compose.cluster.yml
version: '3.8'
services:
  fastapi:
    image: ghcr.io/lstjks/bossjy-pro/fastapi:latest
    deploy:
      replicas: 3
    
  nginx:
    image: nginx:alpine
    deploy:
      replicas: 2
```

### 負載均衡

```nginx
# nginx.conf
upstream fastapi_cluster {
    server fastapi_1:8000;
    server fastapi_2:8000;
    server fastapi_3:8000;
}
```

## 📞 技術支持

### 獲取幫助

- **文檔**: https://docs.bossjy.com
- **問題回報**: https://github.com/lstjks/BossJy-Pro/issues
- **討論**: https://github.com/lstjks/BossJy-Pro/discussions
- **郵件**: support@bossjy.com

### 社區資源

- **GitHub Wiki**: 項目詳細文檔
- **Discord社群**: 實時技術交流
- **YouTube頻道**: 視頻教程

---

**最後更新**: 2025-01-09  
**文檔版本**: v1.6.0  
**維護者**: BossJy Team