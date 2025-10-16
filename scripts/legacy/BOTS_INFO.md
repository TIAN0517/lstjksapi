# ✅ 三Bot系统已启动 - 快速参考

**启动时间**: 2025-10-07 01:26
**状态**: 所有Bot运行正常 ✅

---

## 🤖 Bot信息总览

### 🔧 Bot 1 - 服务监控 (Lstjksbot)
```
Telegram用户名: @Lstjksbot
Bot ID: 8431805678
Token: 8431805678:AAGTukXa3NCKz9odA48Oc3awMKdt1LGdNVE
进程PID: 141411
日志文件: /mnt/d/BossJy-Cn/BossJy-Cn/logs/bot1-monitor.log
```

**核心功能**:
- ✅ 系统服务状态监控
- ✅ Docker容器管理
- ✅ API健康检查
- ✅ 日志查看

**常用命令**:
```
/start    - 开始使用
/status   - 查看所有服务状态
/health   - API健康检查
/docker   - Docker容器详情
/logs     - 查看最新日志
/ping     - 测试响应
```

**使用场景**: 系统管理员、运维人员检查系统状态

---

### 📊 Bot 2 - 数据处理 (ntp_nezhabot)
```
Telegram用户名: @ntp_nezhabot
Bot ID: 8314772330
Token: 8314772330:AAHNeQaWQOsKCh7DZfq0c7fOinZzaQoVEqA
进程PID: 141436
日志文件: /mnt/d/BossJy-Cn/BossJy-Cn/logs/bot2-processor.log
```

**核心功能**:
- ✅ 文件上传处理
- ✅ 数据筛选（香港、华人、澳洲）
- ✅ 任务管理
- ✅ 数据统计

**常用命令**:
```
/start             - 开始使用
/upload            - 文件上传指南
/filter_hongkong   - 香港数据筛选
/filter_chinese    - 华人数据识别
/tasks             - 查看任务列表
/stats             - 数据统计
/ping              - 测试响应
```

**特殊功能**: 直接发送CSV/Excel文件进行处理

**使用场景**: 数据分析师、业务人员处理客户数据

---

### 👋 Bot 3 - 用户帮助 (lstjks_jy_bot)
```
Telegram用户名: @lstjks_jy_bot
Bot ID: 8344575992
Token: 8344575992:AAHq0Wn7WN24B2mkCZCYjkRReLbK7SEhpWU
进程PID: 141679
日志文件: /mnt/d/BossJy-Cn/BossJy-Cn/logs/bot3-helper.log
```

**核心功能**:
- ✅ 新手指南
- ✅ 常见问题解答
- ✅ 技术支持
- ✅ 反馈收集

**常用命令**:
```
/start       - 欢迎消息
/help        - 查看所有命令
/quickstart  - 快速开始（3分钟）
/guide       - 完整使用指南
/features    - 功能介绍
/faq         - 常见问题
/support     - 技术支持
/feedback    - 提交反馈
/contact     - 联系我们
/ping        - 测试响应
```

**特殊功能**: 发送【反馈】开头的消息提交反馈

**使用场景**: 所有用户，特别是新用户

---

## 🚀 快速开始

### 1. 在Telegram中搜索Bot

```
方式1: 搜索用户名
  @Lstjksbot       (服务监控)
  @ntp_nezhabot    (数据处理)
  @lstjks_jy_bot   (用户帮助)

方式2: 直接访问链接
  https://t.me/Lstjksbot
  https://t.me/ntp_nezhabot
  https://t.me/lstjks_jy_bot
```

### 2. 发送 /start 开始使用

每个Bot都会显示欢迎消息和可用命令列表。

### 3. 根据需求选择合适的Bot

| 我想...            | 使用哪个Bot      | 命令          |
|-------------------|-----------------|--------------|
| 检查系统是否正常    | Bot 1 (监控)     | /status      |
| 查看API健康状态    | Bot 1 (监控)     | /health      |
| 上传数据文件       | Bot 2 (数据)     | 直接发送文件  |
| 筛选华人数据       | Bot 2 (数据)     | /filter_chinese |
| 学习如何使用       | Bot 3 (帮助)     | /quickstart  |
| 遇到问题需要帮助   | Bot 3 (帮助)     | /support     |
| 提交功能建议       | Bot 3 (帮助)     | /feedback    |

---

## 📊 系统状态

### 当前运行状态
```bash
✅ Bot 1 (服务监控): 运行中 (PID: 141411)
✅ Bot 2 (数据处理): 运行中 (PID: 141436)
✅ Bot 3 (用户帮助): 运行中 (PID: 141679)

✅ Docker Services: 运行正常
✅ Flask Web (端口9001): 运行正常
✅ FastAPI (端口28001): 运行正常
```

### 检查状态
```bash
# 检查Bot进程
ps aux | grep "bot[123]_"

# 查看Bot日志
tail -f logs/bot1-monitor.log
tail -f logs/bot2-processor.log
tail -f logs/bot3-helper.log

# 检查所有服务
./check_services.sh
```

---

## 🔧 管理命令

### 启动所有Bot
```bash
./start_all_bots.sh
```

### 停止所有Bot
```bash
./stop_all_bots.sh
```

### 重启所有Bot
```bash
./stop_all_bots.sh && ./start_all_bots.sh
```

### 单独重启某个Bot
```bash
# 停止Bot 1
kill $(cat /tmp/bot1.pid)

# 启动Bot 1
nohup python3 bot1_service_monitor.py > logs/bot1-monitor.log 2>&1 &
echo $! > /tmp/bot1.pid
```

---

## 📝 测试建议

### 测试Bot 1 (服务监控)
1. 搜索 @Lstjksbot
2. 发送 `/start`
3. 发送 `/status` 查看服务状态
4. 发送 `/health` 查看API健康

### 测试Bot 2 (数据处理)
1. 搜索 @ntp_nezhabot
2. 发送 `/start`
3. 发送 `/upload` 查看上传指南
4. 发送 `/tasks` 查看任务列表

### 测试Bot 3 (用户帮助)
1. 搜索 @lstjks_jy_bot
2. 发送 `/start`
3. 发送 `/quickstart` 查看快速指南
4. 发送 `/faq` 查看常见问题

---

## ⚠️ 故障排查

### Bot无响应
```bash
# 1. 检查进程是否运行
ps aux | grep bot[123]_

# 2. 查看日志
tail -100 logs/bot1-monitor.log
tail -100 logs/bot2-processor.log
tail -100 logs/bot3-helper.log

# 3. 重启Bot
./stop_all_bots.sh
./start_all_bots.sh

# 4. 测试API连接
curl https://api.telegram.org/bot8431805678:AAGTukXa3NCKz9odA48Oc3awMKdt1LGdNVE/getMe
```

### 某个Bot不工作
```bash
# 查看该Bot的日志
tail -50 logs/bot[X]-*.log

# 重启该Bot
kill $(cat /tmp/bot[X].pid)
nohup python3 bot[X]_*.py > logs/bot[X]-*.log 2>&1 &
echo $! > /tmp/bot[X].pid
```

---

## 📖 完整文档

详细使用指南请参考: `TELEGRAM_BOTS_GUIDE.md`

---

## 🎯 最佳实践

1. **日常监控**: 使用Bot 1定期检查系统状态
2. **数据处理**: 使用Bot 2上传和处理数据文件
3. **遇到问题**: 先查看Bot 3的FAQ，再联系支持
4. **反馈建议**: 通过Bot 3的 /feedback 提交
5. **定期检查**: 每天查看一次服务状态

---

**BossJy Pro Team**
Version: 1.0.0 (Three-Bot Architecture)
Last Updated: 2025-10-07 01:26
