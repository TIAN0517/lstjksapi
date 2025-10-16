# BossJy-Pro 部署问题解决方案

## 问题描述
部署脚本遇到Docker容器文件系统错误：
```
Error response from daemon: failed to create task for container: failed to create shim task: OCI runtime create failed: runc create failed: invalid rootfs
```

## 解决方案

### 方案1：重启Docker Desktop（推荐）
1. 完全退出Docker Desktop（右键系统托盘图标 -> Quit Docker Desktop）
2. 等待所有Docker进程完全停止
3. 重新启动Docker Desktop
4. 等待Docker Desktop完全启动（状态显示为绿色）
5. 重新运行部署脚本：`.\deploy-core.bat`

### 方案2：重置Docker Desktop
如果重启无效，可以尝试重置：
1. 打开Docker Desktop设置
2. 转到"Troubleshoot"（故障排除）选项卡
3. 点击"Reset to factory defaults"（重置为工厂默认设置）
4. 等待重置完成
5. 重新运行部署脚本

### 方案3：检查WSL2状态
1. 打开PowerShell（管理员）
2. 运行：`wsl --shutdown`
3. 等待WSL完全关闭
4. 重启Docker Desktop
5. 重新运行部署脚本

### 方案4：使用Docker CLI直接部署
如果Compose有问题，可以手动启动各个服务：

```bash
# 1. 启动PostgreSQL
docker run -d --name bossjy-postgres `
    -e POSTGRES_DB=bossjy `
    -e POSTGRES_USER=bossjy `
    -e POSTGRES_PASSWORD=your_password `
    -p 15432:5432 `
    postgres:15-alpine

# 2. 启动Redis
docker run -d --name bossjy-redis `
    -p 16379:6379 `
    redis:7-alpine

# 3. 启动FastAPI
docker run -d --name bossjy-fastapi `
    -p 18001:8000 `
    -e DATABASE_URL=postgresql://bossjy:your_password@host.docker.internal:15432/bossjy `
    -e REDIS_URL=redis://host.docker.internal:16379 `
    bossjy-cn-fastapi

# 4. 启动Nginx
docker run -d --name bossjy-nginx `
    -p 80:80 -p 443:443 `
    -v C:/nginx/ssl:/etc/nginx/ssl:ro `
    nginx:alpine
```

## 验证Docker是否正常工作
运行以下命令验证Docker是否正常：
```bash
docker run hello-world
```

如果此命令失败，说明Docker Desktop需要重新安装或修复。

## 环境文件配置
确保 `.env` 文件已正确配置，特别是：
- POSTGRES_PASSWORD
- REDIS_PASSWORD
- SECRET_KEY
- JWT_SECRET_KEY
- BOT_TOKENS

## 联系支持
如果问题仍然存在，请提供以下信息：
1. Docker Desktop版本
2. Windows版本
3. WSL2版本（运行 `wsl --version`）
4. 完整的错误日志

---
更新时间：2025-10-09