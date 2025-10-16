# BossJy-Pro 守护进程管理器使用指南

## 🚀 快速开始

### 方法1: 一键启动脚本 (推荐)
```bash
# 运行启动脚本，选择启动模式
./start_daemon.sh
```

启动模式选项：
1. **守护进程模式** - 后台运行，自动监控和重启
2. **前台模式** - 控制台输出，适合调试
3. **systemd服务** - 系统级服务，开机自启
4. **仅Docker** - 只启动容器服务

### 方法2: 直接运行守护进程
```bash
# 前台运行（推荐用于测试）
python3 bossjy_daemon.py

# 后台运行
nohup python3 bossjy_daemon.py > logs/daemon-console.log 2>&1 &
```

### 方法3: systemd服务 (生产环境推荐)
```bash
# 安装服务
sudo cp bossjy-all.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable bossjy-all.service

# 启动服务
sudo systemctl start bossjy-all.service

# 查看状态
sudo systemctl status bossjy-all.service

# 查看实时日志
sudo journalctl -u bossjy-all.service -f
```

## 📊 功能特性

### 自动管理的服务

1. **Docker Compose 服务**
   - FastAPI 主应用 (端口 28001)
   - PostgreSQL 数据库 (端口 15432)
   - Redis 缓存 (端口 16379)

2. **Flask Web 应用**
   - Gunicorn 多进程运行
   - 端口 9001
   - 自动日志轮转

3. **Telegram Bot**
   - 企业级功能
   - 自动重连
   - 错误恢复

### 自动重启机制

- ✅ **健康检查**: 每 30 秒检查一次所有服务
- ✅ **自动重启**: 服务异常时自动重启
- ✅ **重试限制**: 最多重试 3 次，防止无限循环
- ✅ **智能延迟**: 重启前等待 5-10 秒
- ✅ **状态监控**: 实时记录服务运行时长

### 日志系统

所有日志保存在 `logs/` 目录：

- `daemon.log` - 守护进程主日志
- `daemon-console.log` - 控制台输出
- `web-access.log` - Flask Web访问日志
- `web-error.log` - Flask Web错误日志
- `telegram-bot.log` - Telegram Bot日志

## 🔧 管理命令

### 查看服务状态

```bash
# 守护进程模式
tail -f logs/daemon.log

# systemd模式
sudo systemctl status bossjy-all

# Docker容器
docker compose ps

# 进程状态
ps aux | grep -E "bossjy|gunicorn|start_full_bot"
```

### 停止服务

```bash
# 守护进程模式
kill $(cat /tmp/bossjy-daemon.pid)

# systemd模式
sudo systemctl stop bossjy-all

# 手动停止所有
pkill -f bossjy_daemon.py
docker compose down
pkill -f gunicorn
pkill -f start_full_bot.py
```

### 重启服务

```bash
# systemd模式
sudo systemctl restart bossjy-all

# 手动重启
./start_daemon.sh  # 选择模式2 (前台) 或 模式1 (后台)
```

## 🐛 故障排除

### 1. 服务启动失败

**问题**: Docker容器无法启动
```bash
# 检查Docker日志
docker compose logs app

# 手动启动测试
docker compose up app
```

**问题**: Flask Web启动失败
```bash
# 查看错误日志
cat logs/web-error.log

# 检查端口占用
sudo netstat -tlnp | grep 5000

# 手动测试
python3 -c "from app.web_app import app; app.run(port=9001)"
```

**问题**: Telegram Bot启动失败
```bash
# 查看Bot日志
cat logs/telegram-bot.log

# 检查环境变量
grep TELEGRAM_BOT_TOKEN .env

# 手动测试
python3 start_full_bot.py
```

### 2. 自动重启不工作

检查守护进程状态：
```bash
# 查看守护进程日志
tail -50 logs/daemon.log

# 检查PID文件
cat /tmp/bossjy-daemon.pid
ps aux | grep $(cat /tmp/bossjy-daemon.pid)
```

### 3. systemd服务问题

```bash
# 查看详细状态
sudo systemctl status bossjy-all -l

# 查看完整日志
sudo journalctl -u bossjy-all --no-pager

# 重新加载配置
sudo systemctl daemon-reload
sudo systemctl restart bossjy-all
```

### 4. 端口冲突

```bash
# 检查端口占用
sudo netstat -tlnp | grep -E "5000|28001|15432|16379"

# 杀掉占用进程
sudo fuser -k 5000/tcp
sudo fuser -k 28001/tcp
```

### 5. 权限问题

```bash
# 确保日志目录可写
chmod 755 logs
chmod 666 logs/*.log

# 确保脚本可执行
chmod +x start_daemon.sh bossjy_daemon.py start_full_bot.py
```

## 📈 性能监控

### 查看资源使用

```bash
# CPU和内存
docker stats bossjy-pro-app bossjy-postgres bossjy-redis

# 磁盘使用
du -sh data/* logs/*

# 网络连接
netstat -an | grep -E "5000|28001"
```

### 日志大小管理

```bash
# 查看日志大小
du -sh logs/*.log

# 清理旧日志 (保留最近1000行)
for log in logs/*.log; do
    tail -1000 "$log" > "$log.tmp" && mv "$log.tmp" "$log"
done
```

## 🔒 安全建议

1. **环境变量**: 确保 `.env` 文件权限为 600
   ```bash
   chmod 600 .env
   ```

2. **数据库密码**: 修改默认密码
   ```bash
   # 编辑 docker-compose.yml 和 .env
   POSTGRES_PASSWORD=你的强密码
   ```

3. **防火墙**: 限制端口访问
   ```bash
   # 只允许本地访问
   sudo ufw allow from 127.0.0.1 to any port 28001
   sudo ufw allow from 127.0.0.1 to any port 9001
   ```

4. **日志脱敏**: 定期检查日志中的敏感信息

## 🌟 最佳实践

### 生产环境部署

1. **使用 systemd 服务**
   ```bash
   ./start_daemon.sh
   # 选择选项 3: 安装为systemd服务
   ```

2. **配置日志轮转**
   ```bash
   # 创建 /etc/logrotate.d/bossjy
   /mnt/d/BossJy-Cn/BossJy-Cn/logs/*.log {
       daily
       rotate 7
       compress
       delaycompress
       missingok
       notifempty
   }
   ```

3. **监控告警**
   - 设置 Telegram Bot 发送系统状态
   - 配置邮件告警

4. **定期备份**
   ```bash
   # 备份数据库
   docker exec bossjy-postgres pg_dump -U bossjy bossjy_huaqiao > backup.sql

   # 备份数据文件
   tar -czf data-backup.tar.gz data/
   ```

### 开发环境

1. **使用前台模式**
   ```bash
   ./start_daemon.sh
   # 选择选项 2: 前台模式
   ```

2. **快速重启**
   ```bash
   # Ctrl+C 停止
   # ./start_daemon.sh 重新启动
   ```

## 📞 获取帮助

- **查看日志**: `tail -f logs/daemon.log`
- **健康检查**: `curl http://localhost:28001/health`
- **API文档**: http://localhost:28001/docs
- **项目仓库**: https://github.com/lstjks/Jybot

## 🎯 下一步

1. 确认所有服务运行正常
2. 访问 API 文档测试功能
3. 配置 Telegram Bot Token
4. 设置数据库连接
5. 开始处理数据

---

**版本**: 2.0
**最后更新**: 2025-10-07
**维护者**: BossJy Team
