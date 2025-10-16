# Bot启动指南

## 🚀 快速启动

### 1. 设置环境变量
```bash
# Linux/Mac
export TELEGRAM_BOT_TOKEN=your_bot_token_here

# Windows
set TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 2. 启动方式

#### 方式一：使用启动管理器（推荐）
```bash
# Linux/Mac
./start_bots.sh

# Windows
start_bots.bat
```

#### 方式二：使用命令行
```bash
# 启动简单Bot (1bot)
python start_bots.py 1bot

# 启动认证Bot (2bot)
python start_bots.py 2bot

# 启动全功能Bot
python start_bots.py full

# 启动所有Bot
python start_bots.py all
```

#### 方式三：直接启动
```bash
# 简单Bot
python start_1bot.py

# 认证Bot
python start_2bot.py

# 全功能Bot
python start_full_bot.py
```

## 📋 Bot功能对比

| 功能 | 1bot | 2bot | 全功能Bot |
|------|------|------|-----------|
| 基础文件处理 | ✅ | ❌ | ✅ |
| 用户认证绑定 | ❌ | ✅ | ✅ |
| 企业级错误处理 | ❌ | ❌ | ✅ |
| 性能监控 | ❌ | ❌ | ✅ |
| 管理员面板 | ❌ | ❌ | ✅ |
| 会话管理 | ❌ | ❌ | ✅ |
| 大文件处理 | ❌ | ❌ | ✅ |
| 系统健康检查 | ❌ | ❌ | ✅ |

## 🔧 常用命令

### 全功能Bot命令
- `/start` - 开始使用
- `/help` - 显示帮助
- `/bind <tenant_id>` - 绑定租户ID
- `/upload` - 上传文件
- `/filter` - 设置筛选条件
- `/status` - 查看任务状态
- `/balance` - 查询余额
- `/stats` - 使用统计
- `/settings` - 个人设置
- `/system_status` - 系统状态
- `/admin` - 管理员面板
- `/ping` - 系统检查
- `/usage` - 使用指南

### 管理员功能
设置环境变量：
```bash
export TELEGRAM_ADMIN_USERS=user_id1,user_id2
```

## 🛠️ 故障排除

### 1. Bot Token未设置
```bash
# 检查是否设置
echo $TELEGRAM_BOT_TOKEN

# 设置Token
export TELEGRAM_BOT_TOKEN=your_actual_token
```

### 2. 依赖包问题
```bash
# 安装依赖
pip install -r requirements.txt

# 或安装Telegram Bot依赖
pip install python-telegram-bot
```

### 3. 数据库连接问题
检查 `.env` 文件中的数据库配置：
```env
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
```

### 4. 端口占用
```bash
# 检查端口
netstat -tulpn | grep :5432

# 杀死进程
sudo kill -9 <PID>
```

## 📝 日志查看

### 查看实时日志
```bash
# 查看应用日志
tail -f logs/app.log

# 查看系统日志
journalctl -u bossjy-bot -f
```

## 🔒 安全建议

1. **保护Bot Token**
   - 不要在代码中硬编码Token
   - 使用环境变量存储
   - 定期轮换Token

2. **数据库安全**
   - 使用强密码
   - 限制数据库访问权限
   - 定期备份数据

3. **网络安全**
   - 使用HTTPS
   - 配置防火墙
   - 限制API访问

## 📞 支持

如有问题，请联系：
- 技术支持：support@bossjy-pro.com
- Telegram客服：@BossJySupport