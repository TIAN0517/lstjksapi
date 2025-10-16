# Windows 服务配置指南 - BossJy-CN

本指南帮助您在 Windows 上将 BossJy-CN 配置为**后台服务**，实现开机自启动和崩溃自动重启。

---

## 🎯 方案选择

### 方案1：NSSM (推荐 - 最简单)

**优点**：
- ✅ 图形化配置，无需编程
- ✅ 自动重启、日志记录
- ✅ 适合生产环境

**步骤**：

1. **下载 NSSM**
   ```bash
   # 访问: https://nssm.cc/download
   # 下载 nssm-2.24.zip 并解压到 C:\nssm
   ```

2. **安装 Flask Web 服务**
   ```cmd
   # 以管理员身份运行 CMD
   cd D:\BossJy-Cn\BossJy-Cn
   C:\nssm\win64\nssm.exe install BossJy-Web
   ```

   **GUI 配置**：
   - **Path**: `D:\BossJy-Cn\BossJy-Cn\venv\Scripts\python.exe`
   - **Startup directory**: `D:\BossJy-Cn\BossJy-Cn`
   - **Arguments**: `-m gunicorn -w 4 -b 0.0.0.0:9001 app.web_app:app`
   - **Service name**: `BossJy-Web`

   **Details 选项卡**：
   - Display name: `BossJy Web Service`
   - Description: `BossJy-CN Flask Web Application`
   - Startup type: `Automatic`

   **I/O 选项卡**：
   - Output (stdout): `D:\BossJy-Cn\BossJy-Cn\logs\web-service.log`
   - Error (stderr): `D:\BossJy-Cn\BossJy-Cn\logs\web-error.log`

   **Exit actions 选项卡**：
   - Throttle: `10000` (10秒后重启)
   - Restart: Yes

3. **安装 FastAPI 服务**
   ```cmd
   C:\nssm\win64\nssm.exe install BossJy-API
   ```

   **GUI 配置**：
   - **Path**: `D:\BossJy-Cn\BossJy-Cn\venv\Scripts\python.exe`
   - **Arguments**: `-m uvicorn app.api.main:app --host 0.0.0.0 --port 28001`
   - **Output**: `D:\BossJy-Cn\BossJy-Cn\logs\api-service.log`

4. **启动服务**
   ```cmd
   # 启动 Web 服务
   C:\nssm\win64\nssm.exe start BossJy-Web

   # 启动 API 服务
   C:\nssm\win64\nssm.exe start BossJy-API

   # 查看状态
   C:\nssm\win64\nssm.exe status BossJy-Web
   C:\nssm\win64\nssm.exe status BossJy-API
   ```

5. **管理服务**
   ```cmd
   # 停止服务
   C:\nssm\win64\nssm.exe stop BossJy-Web

   # 重启服务
   C:\nssm\win64\nssm.exe restart BossJy-Web

   # 删除服务
   C:\nssm\win64\nssm.exe remove BossJy-Web confirm
   ```

---

### 方案2：Windows Task Scheduler (免费，内置)

**优点**：
- ✅ Windows 内置，无需下载
- ✅ 支持开机自启动

**缺点**：
- ❌ 不会自动重启崩溃的服务
- ❌ 日志管理不便

**步骤**：

1. **创建启动任务**
   - 打开 `任务计划程序` (Task Scheduler)
   - 创建基本任务 → 名称: `BossJy-CN Startup`
   - 触发器: `计算机启动时`
   - 操作: `启动程序`
     - 程序: `C:\Program Files\Git\bin\bash.exe`
     - 参数: `-c "cd /d/BossJy-Cn/BossJy-Cn && ./start_all.sh"`
   - 条件: 取消勾选 "只有在使用交流电源时才启动此任务"
   - 设置: 勾选 "如果任务失败，重新启动间隔: 10分钟"

---

### 方案3：Windows Subsystem for Linux (WSL2)

**优点**：
- ✅ 完整的 Linux 环境
- ✅ 可使用 systemd 服务

**步骤**：

1. **安装 WSL2**
   ```powershell
   wsl --install
   wsl --set-default-version 2
   ```

2. **安装 systemd** (Ubuntu 22.04+)
   ```bash
   # 在 WSL 中执行
   sudo systemctl status  # 检查 systemd 是否可用
   ```

3. **创建 systemd 服务**
   ```bash
   # /etc/systemd/system/bossjy-web.service
   [Unit]
   Description=BossJy-CN Flask Web Application
   After=network.target postgresql.service redis.service

   [Service]
   Type=notify
   User=yourusername
   WorkingDirectory=/mnt/d/BossJy-Cn/BossJy-Cn
   Environment="PATH=/mnt/d/BossJy-Cn/BossJy-Cn/venv/bin"
   ExecStart=/mnt/d/BossJy-Cn/BossJy-Cn/venv/bin/gunicorn -w 4 -b 0.0.0.0:9001 app.web_app:app
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

4. **启用服务**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable bossjy-web
   sudo systemctl start bossjy-web
   ```

---

## 🔧 快速启动脚本（无需安装服务）

如果您**不需要开机自启动**，只需要方便的启动/停止脚本：

### 使用提供的脚本

1. **启动所有服务**
   ```bash
   ./start_all.sh
   ```

2. **停止所有服务**
   ```bash
   ./stop_all.sh
   ```

3. **重启所有服务**
   ```bash
   ./restart_all.sh
   ```

4. **查看服务状态**
   ```bash
   ./check_services.sh
   ```

   自动刷新模式:
   ```bash
   ./check_services.sh --watch
   ```

---

## 📋 服务管理快速参考

| 操作 | NSSM 命令 | 脚本方式 |
|------|----------|---------|
| **启动** | `nssm start BossJy-Web` | `./start_all.sh` |
| **停止** | `nssm stop BossJy-Web` | `./stop_all.sh` |
| **重启** | `nssm restart BossJy-Web` | `./restart_all.sh` |
| **状态** | `nssm status BossJy-Web` | `./check_services.sh` |
| **日志** | `logs\web-service.log` | `logs\*.log` |

---

## 🛠️ 故障排查

### 问题1: 服务无法启动

**检查步骤**：
```bash
# 1. 检查 Python 环境
venv/Scripts/python.exe --version

# 2. 手动测试启动
venv/Scripts/python.exe -m gunicorn -w 1 -b 0.0.0.0:9001 app.web_app:app

# 3. 查看日志
tail -f logs/web-service.log
```

### 问题2: 端口被占用

**解决方案**：
```bash
# 查看端口占用
netstat -ano | findstr :5000

# 终止进程（替换 PID）
taskkill /PID <进程ID> /F

# 或更改端口
nssm edit BossJy-Web
# 修改 Arguments: -b 0.0.0.0:5001
```

### 问题3: 服务自动重启失败

**检查 NSSM 配置**：
```cmd
# 编辑服务
nssm edit BossJy-Web

# Exit actions 选项卡:
# - Throttle: 10000 (10秒后重启)
# - Restart: Yes
```

---

## 📊 推荐配置

**开发环境**：
- ✅ 使用 `start_all.sh` 脚本启动
- ✅ 需要时手动重启

**生产环境（Windows Server）**：
- ✅ 使用 NSSM 安装服务
- ✅ 配置自动重启
- ✅ 设置日志轮转

**生产环境（Linux VPS）**：
- ✅ 使用 systemd 服务
- ✅ 配置 Nginx 反向代理
- ✅ 使用 Docker Compose

---

## ✅ 验收清单

部署完成后，验证以下功能：

- [ ] 服务自动启动（重启计算机后）
- [ ] 服务崩溃后自动重启
- [ ] Flask Web 可访问: http://localhost:9001
- [ ] FastAPI 可访问: http://localhost:28001
- [ ] 日志文件正常生成
- [ ] 数据库连接正常
- [ ] Telegram Bot 响应正常

---

**🤖 Generated with Claude Code**
**Co-Authored-By: Claude <noreply@anthropic.com>**
