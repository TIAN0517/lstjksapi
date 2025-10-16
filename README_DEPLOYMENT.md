# BossJy系统部署快速指南

## 🚀 立即开始

### 当前状态
✅ **8/19 任务已完成** - 系统配置基本完成，等待Docker修复后即可启动

### 快速部署（3步）

**步骤1：修复Docker（必须）**
```batch
wsl --shutdown
```
然后通过任务管理器重启Docker Desktop，或运行：
```batch
fix-docker.bat
```

**步骤2：启动服务**
```batch
manage-system.bat  # 使用图形化管理工具
```
或
```batch
deploy-complete.bat  # 使用自动化部署脚本
```

**步骤3：验证服务**
- 前端: http://localhost:3000
- API: http://localhost:18001/docs
- 监控: http://localhost:3001 (admin / ji394su3!!)

## 📁 重要文件

| 文件 | 说明 |
|------|------|
| `SYSTEM_STATUS_REPORT.md` | 完整的系统状态和配置报告 |
| `DEPLOYMENT_GUIDE.md` | 详细的部署指南 |
| `manage-system.bat` | 系统管理工具（推荐使用） |
| `deploy-complete.bat` | 自动化部署脚本 |
| `fix-docker.bat` | Docker修复脚本 |
| `check-system.bat` | 系统诊断脚本 |
| `.env.production` | 生产环境配置模板 |
| `deploy/init.sql` | 数据库初始化脚本 |
| `scripts/backup.sh` | 数据库备份脚本 |

## 🔑 默认凭证

### 数据库
- PostgreSQL: `jytian` / `ji394su3`
- Redis: 密码 `ji394su3!!`

### 管理界面
- 系统管理员: `admin@bossjy.com` / `admin123`
- Grafana: `admin` / `ji394su3!!`

⚠️ **重要**：请在生产环境中修改这些默认密码！

## 📊 服务端口

| 服务 | 端口 | 访问地址 |
|------|------|----------|
| 前端 | 3000 | http://localhost:3000 |
| FastAPI | 18001 | http://localhost:18001/docs |
| Go API | 8080 | http://localhost:8080/api/health |
| Grafana | 3001 | http://localhost:3001 |
| Prometheus | 9090 | http://localhost:9090 |
| PostgreSQL | 15432 | localhost:15432 |
| Redis | 16379 | localhost:16379 |

## ⚡ 快速命令

```batch
# 查看所有服务状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 重启所有服务
docker-compose restart

# 停止所有服务
docker-compose down

# 备份数据库
docker exec bossjy-postgres pg_dump -U jytian bossjy_huaqiao | gzip > backups/backup.sql.gz
```

## 🐛 遇到问题？

### Docker无法启动容器
```batch
# 运行修复脚本
fix-docker.bat
```

### 查看详细日志
```batch
# 特定服务
docker-compose logs fastapi
docker-compose logs go-api

# 所有服务
docker-compose logs -f
```

### 系统诊断
```batch
check-system.bat
```

## 📚 详细文档

- [系统状态报告](SYSTEM_STATUS_REPORT.md) - 当前状态和待办事项
- [部署指南](DEPLOYMENT_GUIDE.md) - 完整部署流程
- [Bot文档](BOSSJY_BOT_DOCUMENTATION.md) - Telegram Bot说明

## ✅ 已完成的配置

1. ✅ 数据库配置修复（PostgreSQL + Redis）
2. ✅ 生产环境.env配置
3. ✅ Prometheus和Grafana监控系统
4. ✅ 日志系统和Logstash配置
5. ✅ 数据库备份策略（30天保留）
6. ✅ Docker镜像构建
7. ✅ 数据库初始化脚本
8. ✅ 管理和部署脚本

## 🔜 待完成任务

### 高优先级
- [ ] 修复Docker Overlay文件系统错误
- [ ] 启动和验证所有服务
- [ ] 数据库初始化
- [ ] Go API服务测试

### 中优先级
- [ ] 整合电话检测服务
- [ ] 配置外部API（Twilio、Google Cloud）
- [ ] 优化Telegram Bot系统
- [ ] 加强安全配置

### 低优先级
- [ ] Redis缓存优化
- [ ] 数据库索引优化
- [ ] 全面系统测试

## 💡 提示

1. **首次部署**：建议使用`manage-system.bat`，它提供了交互式菜单
2. **生产环境**：记得修改`.env`中的所有`CHANGE_THIS_IN_PRODUCTION`项
3. **监控访问**：Grafana初次登录后建议修改密码
4. **定期备份**：自动备份已配置，但建议定期手动备份重要数据

## 🆘 需要帮助？

1. 查看`SYSTEM_STATUS_REPORT.md`了解详细状态
2. 运行`check-system.bat`进行系统诊断
3. 查看`DEPLOYMENT_GUIDE.md`获取详细说明
4. 检查Docker Desktop日志（设置 -> Troubleshoot -> View Logs）

---
**最后更新**: 2025-10-09
**状态**: Docker构建完成，等待修复overlay文件系统错误后启动
