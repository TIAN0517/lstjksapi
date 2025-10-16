# 🚀 完整部署流程

## 准备工作

1. DNS已配置（所有子域名）✅
2. 服务器可访问
3. 开启代理前先完成SSL申请

---

## 部署步骤

### 第1步：上传文件到服务器

```bash
# 在本地（Windows）打包项目
cd D:\BossJy-Cn\BossJy-Cn
tar -czf bossjy-deploy.tar.gz deploy/ nginx/ web/static/ security/

# 上传到服务器
scp bossjy-deploy.tar.gz root@你的服务器IP:/root/

# 在服务器上解压
ssh root@你的服务器IP
cd /root
tar -xzf bossjy-deploy.tar.gz
mv deploy nginx web security BossJy-Cn/
cd BossJy-Cn
```

### 第2步：申请SSL证书（⚠️ 先不要开代理）

```bash
# 给脚本执行权限
chmod +x deploy/*.sh

# 申请SSL证书
sudo ./deploy/1-install-ssl.sh
```

**等待SSL证书申请完成（约2-3分钟）**

证书位置：
- `/etc/letsencrypt/live/jytian.it.com/`
- `/etc/letsencrypt/live/tiankai.it.com/`

### 第3步：部署Nginx配置

```bash
# 部署Nginx
sudo ./deploy/2-deploy-nginx.sh
```

### 第4步：配置防火墙

```bash
# 配置UFW防火墙
sudo ./deploy/3-setup-firewall.sh
```

### 第5步：配置Fail2Ban

```bash
# 配置Fail2Ban防暴力破解
sudo ./deploy/4-setup-fail2ban.sh
```

### 第6步：修改管理后台IP白名单

```bash
# 查询你的公网IP
curl ifconfig.me

# 编辑jytian管理后台配置
sudo nano /etc/nginx/sites-available/jytian-admin.conf

# 找到第29-32行，取消注释并修改为你的IP：
# allow 你的公网IP;
# deny all;

# 编辑tiankai管理后台配置（同样操作）
sudo nano /etc/nginx/sites-available/tiankai-admin.conf

# 重启Nginx
sudo systemctl reload nginx

# 更新防火墙规则
sudo ufw delete allow 9443/tcp
sudo ufw delete allow 6443/tcp
sudo ufw allow from 你的公网IP to any port 9443 proto tcp
sudo ufw allow from 你的公网IP to any port 6443 proto tcp
sudo ufw reload
```

### 第7步：测试访问

```bash
# 测试主域名（诱饵页）
curl -I https://jytian.it.com
curl -I https://tiankai.it.com

# 测试真实API
curl -I https://api-v2.jytian.it.com:8443/health
curl -I https://gateway.tiankai.it.com:7443/health

# 测试Web应用
curl -I https://cdn.jytian.it.com
curl -I https://app.tiankai.it.com
```

### 第8步：启动Flask应用

```bash
# 安装依赖
cd /root/BossJy-Cn
pip install -r requirements.txt
pip install gunicorn

# 创建systemd服务
sudo nano /etc/systemd/system/bossjy-web.service
```

添加内容：
```ini
[Unit]
Description=BossJy-Cn Web Application
After=network.target

[Service]
Type=notify
User=root
WorkingDirectory=/root/BossJy-Cn
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/local/bin/gunicorn -w 4 -b 127.0.0.1:5000 app.web_app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
sudo systemctl daemon-reload
sudo systemctl start bossjy-web
sudo systemctl enable bossjy-web
sudo systemctl status bossjy-web
```

### 第9步：开启Cloudflare代理

**现在可以安全地开启Cloudflare代理了！**

在Cloudflare DNS页面：
1. 所有子域名的云朵图标都点成🟠橙色（Proxied）
2. SSL/TLS → 设置为 "Full (strict)"
3. Security → 设置为 "Medium"

---

## ✅ 验证清单

- [ ] SSL证书申请成功
- [ ] Nginx配置正确
- [ ] 防火墙已配置
- [ ] Fail2Ban运行中
- [ ] 管理后台IP白名单已设置
- [ ] Flask应用运行中
- [ ] 所有子域名可访问
- [ ] Cloudflare代理已开启
- [ ] SSL Labs评分 A+

---

## 📊 服务状态检查

```bash
# Nginx状态
sudo systemctl status nginx

# Flask应用状态
sudo systemctl status bossjy-web

# Fail2Ban状态
sudo fail2ban-client status

# 防火墙状态
sudo ufw status numbered

# 查看日志
sudo tail -f /var/log/nginx/jytian-real-api.log
sudo tail -f /var/log/nginx/jytian-honeypot-attack.log
sudo journalctl -u bossjy-web -f
```

---

## 🔍 故障排查

### SSL证书申请失败

```bash
# 检查DNS解析
nslookup jytian.it.com
dig jytian.it.com +short

# 检查80端口是否占用
sudo netstat -tlnp | grep :80

# 手动申请
sudo certbot certonly --standalone -d jytian.it.com --dry-run
```

### Nginx启动失败

```bash
# 测试配置
sudo nginx -t

# 查看详细错误
sudo journalctl -u nginx -n 50

# 检查证书文件
ls -la /etc/letsencrypt/live/jytian.it.com/
```

### Flask应用无法启动

```bash
# 检查端口5000
sudo netstat -tlnp | grep :5000

# 查看应用日志
sudo journalctl -u bossjy-web -n 100

# 手动测试
cd /root/BossJy-Cn
python -c "from app.web_app import app; print('OK')"
```

---

## 🎯 完成后的访问地址

### jytian.it.com
- 主站（诱饵）: https://jytian.it.com
- 真实API: https://api-v2.jytian.it.com:8443
- Web应用: https://cdn.jytian.it.com
- 管理后台: https://admin-portal.jytian.it.com:9443 （需IP白名单）
- 蜜罐: https://backup.jytian.it.com

### tiankai.it.com
- 主站（诱饵）: https://tiankai.it.com
- 真实API: https://gateway.tiankai.it.com:7443
- Web应用: https://app.tiankai.it.com
- 管理后台: https://console.tiankai.it.com:6443 （需IP白名单）
- 蜜罐: https://monitor.tiankai.it.com

---

**部署完成！享受企业级安全防护！** 🎉
