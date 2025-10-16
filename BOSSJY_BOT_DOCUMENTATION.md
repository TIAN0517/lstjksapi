# BossJy TG Bot 完整功能实现文档

## 📋 项目概述

BossJy TG Bot 是一个功能完整的Telegram机器人系统，提供数据服务、客户管理、群组管理等全方位功能。

## 🚀 主要功能

### 1. 客户服务Bot (bossjy_customer_bot.py)
- **用户注册系统**：完整的用户注册流程，支持用户名、邮箱验证
- **充值功能**：USDT充值，支持交易验证和自动积分发放
- **积分系统**：完整的积分管理，包括消费记录和充值历史
- **试用功能**：每种数据类型100条免费试用
- **群组管理**：自动绑定群组，支持群成员管理
- **数据查询**：集成数据查询功能

### 2. 数据查询Bot (enhanced_data_query_bot.py)
- **实时数据统计**：显示各类数据的统计信息
- **智能查询**：支持多条件查询，包括模糊匹配、字段筛选
- **数据导出**：支持Excel、CSV、JSON格式导出
- **积分消费**：查询和导出消费积分，实时扣除
- **高级搜索**：支持复杂条件查询和正则表达式

### 3. 群组管理Bot (enhanced_group_manager_bot.py)
- **自动化管理**：自动欢迎新成员，垃圾信息过滤
- **权限系统**：多级权限管理，支持自动权限分配
- **规则引擎**：可配置的群组规则，支持多种过滤条件
- **数据分析**：群组活跃度统计，成员行为分析
- **实时监控**：实时监控群组活动，自动处理违规行为

### 4. API集成服务 (api_integration_service.py)
- **RESTful API**：完整的REST API接口
- **认证系统**：API密钥认证，支持权限控制
- **速率限制**：可配置的请求速率限制
- **数据接口**：提供数据查询、导出的API接口
- **监控指标**：Prometheus指标支持

### 5. 数据导出服务 (data_export_service.py)
- **多格式支持**：Excel、CSV、JSON、XML、SQL格式
- **异步处理**：大文件异步导出，支持进度跟踪
- **邮件通知**：导出完成后邮件通知
- **文件压缩**：支持文件压缩，节省空间
- **历史记录**：完整的导出历史记录

## 🛠️ 安装和部署

### 1. 环境要求
- Python 3.8+
- Redis (可选，用于缓存和速率限制)
- SQLite (默认数据库)
- 2GB+ RAM
- 10GB+ 存储空间

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 环境配置
复制 `.env.example` 到 `.env` 并配置：
```bash
cp .env.example .env
```

主要配置项：
```env
# Telegram Bot Token
TELEGRAM_BOT_TOKEN=your_bot_token_here
DATA_QUERY_BOT_TOKEN=your_data_query_bot_token
GROUP_MANAGER_BOT_TOKEN=your_group_manager_bot_token

# API配置
API_HOST=0.0.0.0
API_PORT=18001
JWT_SECRET=your_jwt_secret

# Redis配置
REDIS_URL=redis://localhost:6379

# 邮件配置（可选）
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### 4. 数据库初始化
```bash
# 创建数据库表
python3 -c "
from bossjy_customer_bot import get_db_connection
conn = get_db_connection()
# 数据库表会在首次运行时自动创建
"
```

## 🚀 启动服务

### 1. 使用统一启动器
```bash
# 启动所有服务
python3 bossjy_starter.py start

# 停止所有服务
python3 bossjy_starter.py stop

# 重启所有服务
python3 bossjy_starter.py restart

# 查看服务状态
python3 bossjy_starter.py status

# 健康检查
python3 bossjy_starter.py health
```

### 2. 单独启动服务
```bash
# 启动客户服务Bot
python3 bossjy_customer_bot.py

# 启动数据查询Bot
python3 enhanced_data_query_bot.py

# 启动群组管理Bot
python3 enhanced_group_manager_bot.py

# 启动API服务
python3 api_integration_service.py

# 启动数据导出服务
python3 data_export_service.py
```

### 3. 使用Docker部署
```bash
# 构建镜像
docker build -t bossjy-bot .

# 运行容器
docker run -d --name bossjy-bot -p 18001:18001 bossjy-bot
```

## 📖 使用指南

### 1. 客户服务Bot使用流程

#### 用户注册
1. 发送 `/start` 开始
2. 点击 "📝 注册" 按钮
3. 按提示输入用户名、邮箱、密码
4. 注册成功后获得100条免费试用

#### 充值流程
1. 点击 "💰 充值" 按钮
2. 获取专属充值地址
3. 使用USDT-TRC20转账
4. 系统自动检测到账并发送积分

#### 数据查询
1. 点击 "🔍 查询数据" 按钮
2. 选择数据类型
3. 输入查询条件
4. 查看结果并可选择导出

### 2. 数据查询Bot使用流程

#### 快速查询
1. 发送 `/start` 开始
2. 点击 "🔍 快速查询" 按钮
3. 选择数据类型
4. 输入查询条件
5. 查看结果

#### 高级搜索
1. 点击 "📋 高级搜索" 按钮
2. 使用高级查询语法
3. 支持多条件组合
4. 支持正则表达式

#### 数据导出
1. 查询数据后选择导出
2. 选择导出格式（Excel/CSV）
3. 支持邮件发送
4. 查看导出历史

### 3. 群组管理Bot使用流程

#### 群组设置
1. 将Bot添加到群组
2. 管理员发送 `/setup` 开始配置
3. 设置欢迎消息、过滤规则等
4. 配置权限管理规则

#### 日常管理
1. 使用 `/admin` 查看管理面板
2. 使用 `/rules` 管理群组规则
3. 使用 `/stats` 查看群组统计
4. Bot自动处理违规行为

### 4. API服务使用

#### 认证
```bash
# 登录获取API密钥
curl -X POST "http://localhost:18001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

#### 数据查询
```bash
# 查询数据
curl -X POST "http://localhost:18001/data/query" \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "data_type": "hongkong",
    "conditions": {"name": "test"},
    "limit": 100
  }'
```

#### 数据导出
```bash
# 导出数据
curl -X POST "http://localhost:18001/data/export" \
  -H "Authorization: Bearer your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": {
      "data_type": "hongkong",
      "conditions": {"name": "test"},
      "limit": 1000
    },
    "export_format": "excel"
  }'
```

## 🔧 配置说明

### 1. Bot Token配置
每个Bot需要独立的Token：
- 客户服务Bot：用于用户注册、充值等
- 数据查询Bot：用于数据查询和导出
- 群组管理Bot：用于群组管理功能

### 2. 数据库配置
默认使用SQLite，可配置PostgreSQL：
```env
DATABASE_URL=postgresql://username:password@localhost:5432/bossjy
```

### 3. Redis配置
用于缓存和速率限制：
```env
REDIS_URL=redis://localhost:6379
```

### 4. 邮件配置
用于导出文件邮件通知：
```env
EMAIL_ENABLED=true
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## 📊 监控和维护

### 1. 日志管理
- 所有日志存储在 `logs/` 目录
- 按服务分类存储
- 支持日志轮转

### 2. 性能监控
- API服务支持Prometheus指标
- 访问 `http://localhost:18001/metrics` 查看指标
- 支持自定义监控

### 3. 健康检查
```bash
# 检查所有服务状态
python3 bossjy_starter.py health

# 检查API服务
curl http://localhost:18001/health
```

### 4. 数据备份
```bash
# 备份数据库
cp bossjy_users.db backup/users_$(date +%Y%m%d).db
cp bossjy_data.db backup/data_$(date +%Y%m%d).db
```

## 🚨 故障排除

### 1. 常见问题

#### Bot无法启动
- 检查Token是否正确
- 检查网络连接
- 查看日志文件

#### 数据库连接失败
- 检查数据库文件权限
- 检查数据库路径
- 检查SQLite版本

#### API服务无法访问
- 检查端口是否被占用
- 检查防火墙设置
- 查看API服务日志

### 2. 日志查看
```bash
# 查看所有服务日志
tail -f logs/*.log

# 查看特定服务日志
tail -f logs/customer_bot.log
```

### 3. 性能优化
- 调整数据库查询缓存
- 优化导出文件大小限制
- 配置Redis缓存策略

## 📝 更新日志

### v2.0.0 (2025-10-09)
- ✅ 完善客户服务Bot充值确认功能
- ✅ 优化数据查询Bot实时数据展示
- ✅ 增强群组管理功能
- ✅ 实现API集成功能
- ✅ 添加数据导出功能
- ✅ 创建统一启动脚本
- ✅ 完善文档和部署指南

## 📞 技术支持

- 官方网站：https://bossjy.tiankai.it.com
- 客服支持：@bossjy_support
- 技术文档：https://docs.bossjy.tiankai.it.com

## 📄 许可证

本项目采用 MIT 许可证，详情请参阅 LICENSE 文件。