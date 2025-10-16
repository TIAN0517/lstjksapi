# BossJy-CN 服务管理完整指南

**最后更新**: 2025-10-07
**版本**: v1.5.1

---

## 🎯 快速开始 (30秒)

```bash
# 1. 启动所有服务
./start_all.sh

# 2. 查看服务状态
./check_services.sh

# 3. 访问应用
#    Web界面: http://localhost:9001
#    API文档: http://localhost:28001/docs
```

**就这么简单！** 🎉

---

## 📁 脚本文件说明

| 脚本文件 | 功能 | 执行时间 | 说明 |
|---------|------|----------|------|
| **start_all.sh** | 启动所有服务 | ~30秒 | ⭐ 推荐：一键启动全功能 |
| **stop_all.sh** | 停止所有服务 | ~10秒 | 优雅停止，保留数据库容器 |
| **restart_all.sh** | 重启所有服务 | ~40秒 | 先停止，再启动 |
| **check_services.sh** | 查看服务状态 | ~2秒 | 实时监控服务健康度 |

---

## 🚀 详细使用说明

### 1. `start_all.sh` - 全功能启动

**功能**：
- ✅ 自动检测操作系统 (Windows/Linux)
- ✅ 检查 Python 环境和虚拟环境
- ✅ 自动安装/更新依赖
- ✅ 启动数据库 (Docker 或本地)
- ✅ 启动 FastAPI (Uvicorn, 端口 28001)
- ✅ 启动 Flask Web (Gunicorn, 端口 9001)
- ✅ 启动 Celery Worker (异步任务)
- ✅ 启动 Telegram Bots (3个)
- ✅ 完整的健康检查
- ✅ 生成详细的启动日志

**使用方式**：
```bash
# 基本启动
./start_all.sh

# 查看详细日志
tail -f logs/startup-*.log
```

**启动流程**：
```
1. 检测操作系统 → Windows/Linux
2. 检查 Python 环境 → 3.9+
3. 激活虚拟环境 → venv/
4. 更新依赖包 → requirements.txt
5. 启动数据库 → PostgreSQL + Redis
6. 启动 FastAPI → localhost:28001
7. 启动 Flask Web → localhost:9001
8. 启动 Celery Worker → 后台任务
9. 启动 Telegram Bots → 3个 Bot
10. 健康检查 → 验证所有服务
11. 显示访问信息 → URL + 日志路径
```

**输出示例**：
```
════════════════════════════════════════════════════
🚀 BossJy-CN 全功能启动脚本
════════════════════════════════════════════════════

ℹ️  操作系统: windows

═══════════════════════════════════════════════════
步骤1: 检查Python环境
═══════════════════════════════════════════════════

✅ Python已安装: Python 3.11.0
✅ 虚拟环境已存在: venv/
✅ 虚拟环境已激活

...

🎉 所有服务启动完成

服务访问地址:
  🌐 Flask Web界面:    http://localhost:9001
  🔌 FastAPI后端:      http://localhost:28001
  📖 API文档 (Swagger): http://localhost:28001/docs
```

---

### 2. `stop_all.sh` - 停止所有服务

**功能**：
- ✅ 优雅停止所有应用进程
- ✅ 保留数据库容器 (可选完全停止)
- ✅ 清理临时文件和 PID 文件
- ✅ 验证进程是否完全停止

**使用方式**：
```bash
# 基本停止（保留数据库）
./stop_all.sh

# 停止并清理 Python 缓存
./stop_all.sh --clean

# 完全停止（包括 Docker 容器）
./stop_all.sh
docker-compose down
```

**停止的服务**：
- FastAPI (Uvicorn)
- Flask Web (Gunicorn/Dev Server)
- Celery Worker
- Telegram Bot 1 (服务监控)
- Telegram Bot 2 (数据处理)
- Telegram Bot 3 (用户助手)
- Enhanced Telegram Bot

**输出示例**：
```
════════════════════════════════════════════════════
⏹️  BossJy-CN 全功能停止脚本
════════════════════════════════════════════════════

📋 步骤1: 停止应用服务

停止 FastAPI (Uvicorn)... ✅
停止 Flask Web (Gunicorn)... ✅
停止 Celery Worker... (未运行)
停止 Telegram Bot 1... ✅
停止 Telegram Bot 2... ✅
停止 Telegram Bot 3... ✅

📋 步骤2: 检查Docker容器

停止Docker容器 (保留PostgreSQL/Redis)... ✅
💡 提示: PostgreSQL和Redis容器保持运行中
   如需完全停止: docker-compose down

✅ 所有应用进程已成功停止
```

---

### 3. `restart_all.sh` - 重启所有服务

**功能**：
- ✅ 调用 `stop_all.sh` 停止所有服务
- ✅ 等待进程完全退出 (5秒)
- ✅ 调用 `start_all.sh` 启动所有服务

**使用方式**：
```bash
# 一键重启
./restart_all.sh
```

**适用场景**：
- 代码更新后需要重启
- 配置文件修改后重启
- 服务异常需要重启
- 部署新版本

---

### 4. `check_services.sh` - 服务状态检查

**功能**：
- ✅ 检查 Docker 容器状态
- ✅ 检查应用进程数量
- ✅ 检查端口监听状态
- ✅ HTTP 健康检查
- ✅ 系统资源使用统计
- ✅ 日志文件统计
- ✅ 计算系统健康度

**使用方式**：
```bash
# 单次检查
./check_services.sh

# 自动刷新模式（每10秒）
./check_services.sh --watch
```

**输出示例**：
```
════════════════════════════════════════════════════
📊 BossJy-CN 服务状态监控
════════════════════════════════════════════════════

━━━ Docker 容器状态 ━━━

  PostgreSQL 容器: ✅ 运行中
  Redis 容器: ✅ 运行中
  FastAPI 容器: ✅ 运行中

━━━ 应用进程状态 ━━━

  FastAPI (Uvicorn): ✅ 1 个进程
  Flask Web (Gunicorn): ✅ 4 个进程
  Celery Worker: ✅ 2 个进程
  Telegram Bot 1: ✅ 1 个进程
  Telegram Bot 2: ✅ 1 个进程
  Telegram Bot 3: ✅ 1 个进程

━━━ 端口监听状态 ━━━

  端口 9001 (Flask Web): ✅ 监听中
  端口 28001 (FastAPI): ✅ 监听中
  端口 15432 (PostgreSQL): ✅ 监听中
  端口 16379 (Redis): ✅ 监听中

━━━ HTTP 服务健康检查 ━━━

  Flask Web 首页 (http://localhost:9001/): ✅ 响应正常
  FastAPI 健康检查 (http://localhost:28001/health): ✅ 响应正常
  API 文档 (http://localhost:28001/docs): ✅ 响应正常

━━━ 系统资源使用 ━━━

  磁盘使用率 (项目目录): 45%

━━━ 日志文件统计 ━━━

  日志文件数量: 8
  日志总大小: 12M
  最新日志: logs/startup-20251007-095030.log

════════════════════════════════════════════════════
✅ 状态检查完成
════════════════════════════════════════════════════

🎉 系统健康度: 100% (良好)
```

---

## 🔧 常见使用场景

### 场景1: 每天开始工作

```bash
# 1. 启动所有服务
./start_all.sh

# 2. 等待30秒（自动完成）

# 3. 访问应用
#    打开浏览器: http://localhost:9001
```

### 场景2: 代码更新后重启

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 重启服务
./restart_all.sh

# 3. 验证状态
./check_services.sh
```

### 场景3: 下班关闭服务

```bash
# 1. 停止所有服务
./stop_all.sh

# 2. 验证已停止
ps aux | grep -E "gunicorn|uvicorn"
# 应无输出
```

### 场景4: 部署新版本

```bash
# 1. 停止服务
./stop_all.sh

# 2. 备份数据库（可选）
docker exec bossjy-postgres pg_dump -U postgres bossjy > backup.sql

# 3. 更新代码
git checkout v1.5.1

# 4. 更新依赖
source venv/Scripts/activate  # Windows
pip install -r requirements.txt

# 5. 运行迁移（如需要）
# alembic upgrade head

# 6. 启动服务
./start_all.sh

# 7. 验证部署
./check_services.sh
```

### 场景5: 故障诊断

```bash
# 1. 查看服务状态
./check_services.sh

# 2. 查看日志
tail -f logs/*.log

# 3. 如果服务异常，重启
./restart_all.sh

# 4. 如果仍有问题，完全重置
./stop_all.sh --clean
pkill -9 -f "gunicorn|uvicorn|celery|flask"
./start_all.sh
```

---

## 🛠️ 高级配置

### Windows 服务配置 (开机自启动)

参考: [WINDOWS_SERVICE_SETUP.md](./WINDOWS_SERVICE_SETUP.md)

**推荐方案**: NSSM (Non-Sucking Service Manager)

```cmd
# 下载 NSSM: https://nssm.cc/download

# 安装服务
nssm install BossJy-Web D:\BossJy-Cn\BossJy-Cn\start_all.sh

# 启动服务
nssm start BossJy-Web

# 查看状态
nssm status BossJy-Web
```

### Linux Systemd 服务

```bash
# 创建服务文件
sudo nano /etc/systemd/system/bossjy.service
```

```ini
[Unit]
Description=BossJy-CN Application
After=network.target

[Service]
Type=forking
User=yourusername
WorkingDirectory=/path/to/BossJy-Cn
ExecStart=/path/to/BossJy-Cn/start_all.sh
ExecStop=/path/to/BossJy-Cn/stop_all.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启用服务
sudo systemctl daemon-reload
sudo systemctl enable bossjy
sudo systemctl start bossjy

# 查看状态
sudo systemctl status bossjy
```

---

## 📋 故障排查

### 问题1: 脚本无法执行

**症状**: `Permission denied: ./start_all.sh`

**解决方案**:
```bash
# 添加执行权限
chmod +x *.sh

# 重新运行
./start_all.sh
```

### 问题2: 端口被占用

**症状**: `Address already in use: 5000`

**解决方案**:
```bash
# Windows: 查找并终止进程
netstat -ano | findstr :5000
taskkill /PID <进程ID> /F

# Linux: 查找并终止进程
lsof -ti:9001 | xargs kill -9

# 或修改端口
# 编辑 start_all.sh 中的端口号
```

### 问题3: 虚拟环境未激活

**症状**: `ModuleNotFoundError: No module named 'flask'`

**解决方案**:
```bash
# 手动激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 重新启动
./start_all.sh
```

### 问题4: Docker 容器未启动

**症状**: `could not connect to server: Connection refused`

**解决方案**:
```bash
# 检查 Docker 是否运行
docker ps

# 启动 Docker Desktop (Windows)
# 或启动 Docker 服务 (Linux):
sudo systemctl start docker

# 启动容器
docker-compose up -d postgres redis

# 验证
docker ps | grep bossjy
```

---

## 📊 日志管理

### 日志文件位置

```
logs/
├── startup-YYYYMMDD-HHMMSS.log  # 启动日志
├── fastapi.log                   # FastAPI 日志
├── web-access.log               # Web 访问日志
├── web-error.log                # Web 错误日志
├── celery.log                   # Celery 日志
├── bot1_service_monitor.log     # Bot1 日志
├── bot2_data_processor.log      # Bot2 日志
└── bot3_user_helper.log         # Bot3 日志
```

### 查看实时日志

```bash
# 查看所有日志
tail -f logs/*.log

# 查看特定服务日志
tail -f logs/fastapi.log
tail -f logs/web-error.log

# 查看最近100行
tail -100 logs/web-access.log

# 搜索错误
grep -i error logs/*.log
```

### 日志清理

```bash
# 清理7天前的日志
find logs/ -name "*.log" -mtime +7 -delete

# 清理大于100MB的日志
find logs/ -name "*.log" -size +100M -delete

# 压缩旧日志
gzip logs/*.log
```

---

## ✅ 验收清单

部署完成后，请验证以下功能：

### 基础功能
- [ ] 所有服务成功启动
- [ ] Flask Web 可访问 (http://localhost:9001)
- [ ] FastAPI 可访问 (http://localhost:28001)
- [ ] API 文档可访问 (http://localhost:28001/docs)
- [ ] 数据库连接正常
- [ ] Redis 连接正常

### 脚本功能
- [ ] `./start_all.sh` 可正常启动所有服务
- [ ] `./stop_all.sh` 可正常停止所有服务
- [ ] `./restart_all.sh` 可正常重启所有服务
- [ ] `./check_services.sh` 可正常显示服务状态

### 日志记录
- [ ] 启动日志生成正常
- [ ] FastAPI 日志记录正常
- [ ] Web 访问日志记录正常
- [ ] 错误日志记录正常

### 健康检查
- [ ] HTTP 健康检查通过
- [ ] 进程数量正常
- [ ] 端口监听正常
- [ ] 系统资源使用正常

---

## 🆘 获取帮助

**文档**:
- [快速启动指南](./QUICK_START.md)
- [Windows 服务配置](./WINDOWS_SERVICE_SETUP.md)
- [部署指南](./DEPLOYMENT_GUIDE_v1.5.0.md)
- [修复报告](./FIX_RECHARGE_LOGIN_REDIRECT.md)

**紧急故障恢复**:
```bash
# 1. 完全停止
./stop_all.sh --clean

# 2. 强制终止所有进程
pkill -9 -f "gunicorn|uvicorn|celery|flask|bot"

# 3. 清理临时文件
rm -f /tmp/bossjy-*.pid
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null

# 4. 重新启动
./start_all.sh
```

---

**🎉 祝您使用愉快！**

**🤖 Generated with Claude Code**
**Co-Authored-By: Claude <noreply@anthropic.com>**
