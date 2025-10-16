# BossJy Customer Bot 设置指南

## Bot 信息
- **Bot名称**: BossJy @ntp_nezhabot
- **Bot Token**: `8314772330:AAHNeQaWQOsKCh7DZfq0c7fOinZzaQoVEqA`

## 功能列表

### 1. 用户注册
- 命令：`/register` 或 点击 "📝 注册"
- 功能：创建新用户账户
- 流程：用户名 → 邮箱 → 密码

### 2. 充值功能
- 命令：`/recharge` 或 点击 "💰 充值"
- 支持：USDT (TRC20)
- 充值地址：`TEKcZDV8UKzXvHmHqV7nWFJRqQJfYsZkXb`
- 汇率：1 USDT = 10,000 积分

### 3. 数据查询
- 命令：`/query` 或 点击 "🔍 查询数据"
- 功能：查询各类数据（只读）
- 类型：香港、印尼、澳洲、全球华人、新加坡等

### 4. 样本试用
- 命令：`/trial` 或 点击 "🎁 试用样本"
- 规则：
  - 每个账户每种数据类型只能试用一次
  - 每次提供 100 条样本数据
  - 有效期 7 天
- 可试用数据类型：
  - 🇭🇰 香港数据
  - 🇮🇩 印尼数据
  - 🇦🇺 澳洲数据
  - 🌏 全球华人数据
  - 🇸🇬 新加坡数据

### 5. 群组管理
- 自动检测并记录群组信息
- 自动记录群组成员
- 命令：`/mygroups` 查看加入的群组

### 6. 账户管理
- 命令：`/account` 或 点击 "👤 我的账户"
- 显示：
  - 用户信息
  - 订阅状态
  - 使用情况
  - 试用记录

### 7. 官方网站
- 命令：`/website` 或 点击 "🌐 官方网站"
- 网址：https://jytian.xyz

## 安装步骤

### 1. 数据库准备
```bash
# 执行数据库迁移
psql -h localhost -U bossjy -d bossjy_huaqiao -f migrations/create_sample_trial_table.sql
```

### 2. 安装依赖
```bash
pip install python-telegram-bot psycopg2-binary werkzeug
```

### 3. 配置环境变量
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=bossjy_huaqiao
export DB_USER=bossjy
export DB_PASSWORD=ji394su3
```

### 4. 启动 Bot

**Linux/Mac:**
```bash
chmod +x start_customer_bot.sh
./start_customer_bot.sh
```

**Windows:**
```cmd
start_customer_bot.bat
```

**手动启动:**
```bash
python3 bossjy_customer_bot.py
```

## 数据库表结构

### sample_trials (样本试用记录表)
- `id`: 主键
- `user_id`: 用户ID
- `telegram_id`: Telegram ID
- `data_type`: 数据类型
- `sample_count`: 样本数量 (默认100)
- `status`: 状态
- `result_file_path`: 结果文件路径
- `created_at`: 创建时间
- `expires_at`: 过期时间
- `used_at`: 使用时间

**约束**: 每个用户每种数据类型只能试用一次 `UNIQUE(user_id, data_type)`

### telegram_groups (群组表)
- `id`: 主键
- `group_id`: 群组ID (唯一)
- `group_title`: 群组标题
- `group_type`: 群组类型 (group/supergroup/channel)
- `is_active`: 是否激活
- `allow_trials`: 是否允许试用
- `allow_queries`: 是否允许查询
- `member_count`: 成员数量
- `trial_count`: 试用次数
- `query_count`: 查询次数
- `created_at`: 创建时间
- `updated_at`: 更新时间

### telegram_group_members (群组成员表)
- `id`: 主键
- `group_id`: 群组ID
- `telegram_id`: Telegram ID
- `user_id`: 用户ID
- `username`: 用户名
- `first_name`: 名字
- `last_name`: 姓氏
- `is_admin`: 是否管理员
- `joined_at`: 加入时间
- `last_seen_at`: 最后活跃时间

**约束**: `UNIQUE(group_id, telegram_id)`

## Bot 命令列表

### 基础命令
- `/start` - 开始使用
- `/help` - 显示帮助
- `/register` - 注册账户
- `/account` - 查看账户信息
- `/cancel` - 取消当前操作

### 充值相关
- `/recharge` - 充值积分
- `/balance` - 查看余额
- `/usdt` - USDT充值地址
- `/confirm <TX_Hash> <金额>` - 确认充值

### 数据查询
- `/query` - 查询数据
- `/stats` - 查看统计

### 样本试用
- `/trial` - 申请试用样本
- `/mytrial` - 查看我的试用记录

### 群组功能
- `/mygroups` - 查看我加入的群组
- `/groupinfo` - 查看当前群组信息

### 其他
- `/website` - 官方网站
- `/support` - 联系客服

## 键盘菜单

主菜单包含以下按钮：
- 📝 注册
- 💰 充值
- 🔍 查询数据
- 🎁 试用样本
- 🌐 官方网站
- 👤 我的账户
- 📊 我的群组
- ❓ 帮助

## 功能特点

### 自动群组检测
- Bot 会自动检测所有群组消息
- 自动记录群组信息（ID、标题、类型）
- 自动记录群组成员信息
- 跟踪成员活跃度

### 试用限制
- 每个账户每种数据类型只能试用一次
- 通过数据库唯一约束强制执行
- 试用期限 7 天
- 每次提供 100 条样本数据

### 充值优惠
- 🎁 首次充值额外赠送 10%
- 🎁 充值 ≥100 USDT 赠送 15%
- 🎁 充值 ≥500 USDT 赠送 20%

## 安全特性
- 密码使用 werkzeug 加密存储
- 数据库连接使用参数化查询防止SQL注入
- 敏感信息通过环境变量配置
- 用户数据隔离

## 监控和日志
- 所有操作记录日志
- 群组活动自动追踪
- 试用记录完整保存
- 错误自动捕获和记录

## 故障排除

### Bot 无法启动
1. 检查 Bot Token 是否正确
2. 检查网络连接
3. 检查 Python 依赖是否安装完整

### 数据库连接失败
1. 检查数据库服务是否运行
2. 检查数据库配置是否正确
3. 检查数据库用户权限

### 群组检测不工作
1. 确保 Bot 已添加到群组
2. 确保 Bot 有读取消息权限
3. 检查数据库表是否创建成功

## 维护建议
1. 定期备份数据库
2. 监控 Bot 运行状态
3. 定期清理过期试用记录
4. 监控充值交易状态

## 联系支持
- 官方网站：https://jytian.xyz
- Telegram：@BossJy_Support
