# BossJy Pro - 三Bot系统使用指南

**更新时间**: 2025-10-07 01:26

## 🎯 系统架构

BossJy Pro采用**三Bot分工**架构，每个Bot专注于不同的功能领域，提供专业化服务：

```
┌─────────────────────────────────────────────────┐
│         BossJy Pro 系统架构                      │
├─────────────────────────────────────────────────┤
│                                                 │
│  🔧 Bot 1           📊 Bot 2          👋 Bot 3  │
│  服务监控           数据处理          用户帮助   │
│                                                 │
│  • 系统状态        • 文件上传        • FAQ      │
│  • 健康检查        • 数据筛选        • 指南     │
│  • 日志查看        • 任务管理        • 支持     │
│  • 容器监控        • 批量处理        • 反馈     │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 🤖 Bot详细介绍

### 🔧 Bot 1: 服务监控Bot

**Token**: `8431805678:AAGTukXa3NCKz9odA48Oc3awMKdt1LGdNVE`

**专注领域**: 系统监控、服务管理、运维监控

**核心功能**:
- `/status` - 查看所有服务状态（Docker + Flask + Bot）
- `/health` - FastAPI健康检查，查看各服务运行状态
- `/docker` - Docker容器详细信息和端口映射
- `/logs` - 查看最新系统日志
- `/uptime` - 系统运行时间
- `/ping` - 测试Bot响应速度

**适用人群**:
- 系统管理员
- 运维人员
- 技术团队

**使用场景**:
- 定期检查系统健康状态
- 排查服务故障
- 监控系统性能
- 查看错误日志

---

### 📊 Bot 2: 数据处理Bot

**Token**: `8314772330:AAHNeQaWQOsKCh7DZfq0c7fOinZzaQoVEqA`

**专注领域**: 数据上传、智能筛选、批量处理

**核心功能**:
- `/upload` - 文件上传指南（支持CSV/Excel）
- `/filter_hongkong` - 香港数据专项筛选
- `/filter_chinese` - 全球华人数据识别
- `/filter_australia` - 澳大利亚数据处理
- `/tasks` - 查看所有处理任务状态
- `/stats` - 数据处理统计报告
- 文件上传 - 直接发送文件开始处理

**适用人群**:
- 数据分析师
- 业务人员
- 市场团队
- 销售团队

**使用场景**:
- 上传客户数据文件
- 筛选目标市场数据
- 批量处理联系人信息
- 生成数据分析报告

---

### 👋 Bot 3: 用户帮助Bot

**Token**: `8344575992:AAHq0Wn7WN24B2mkCZCYjkRReLbK7SEhpWU`

**专注领域**: 用户咨询、功能介绍、问题解答

**核心功能**:
- `/guide` - 完整使用指南
- `/quickstart` - 3分钟快速上手
- `/features` - 核心功能介绍
- `/faq` - 常见问题解答
- `/support` - 获取技术支持
- `/feedback` - 提交反馈建议
- `/contact` - 联系我们
- 智能对话 - 直接发送问题获取解答

**适用人群**:
- 新用户
- 所有用户
- 需要帮助的人

**使用场景**:
- 首次使用学习
- 遇到问题求助
- 提交功能建议
- 了解系统功能

---

## 🚀 快速开始

### 1. 查找Bot

在Telegram中搜索Bot（需要先从BotFather获取Bot用户名）：

```
搜索Bot用户名（暂未设置，需要在BotFather中配置）
```

### 2. 开始对话

每个Bot都支持 `/start` 命令开始使用：

```
/start
```

### 3. 根据需求选择Bot

| 我想...                | 应该使用        |
|------------------------|----------------|
| 检查系统是否正常        | 🔧 Bot 1       |
| 上传数据文件            | 📊 Bot 2       |
| 学习如何使用            | 👋 Bot 3       |
| 查看服务状态            | 🔧 Bot 1       |
| 筛选华人数据            | 📊 Bot 2       |
| 遇到问题需要帮助        | 👋 Bot 3       |

---

## 📋 常用命令速查

### Bot 1 - 服务监控
```bash
/status      # 服务状态总览
/health      # API健康检查
/docker      # 容器详细信息
/logs        # 查看日志
/uptime      # 运行时间
```

### Bot 2 - 数据处理
```bash
/upload             # 上传指南
/filter_hongkong    # 香港数据
/filter_chinese     # 华人识别
/tasks              # 任务列表
/stats              # 处理统计
```

### Bot 3 - 用户帮助
```bash
/quickstart    # 快速开始
/features      # 功能介绍
/faq           # 常见问题
/support       # 技术支持
/feedback      # 提交反馈
```

---

## 💻 本地管理

### 启动所有Bot
```bash
cd /mnt/d/BossJy-Cn/BossJy-Cn
./start_all_bots.sh
```

### 停止所有Bot
```bash
./stop_all_bots.sh
```

### 查看Bot日志
```bash
# Bot 1 日志
tail -f logs/bot1-monitor.log

# Bot 2 日志
tail -f logs/bot2-processor.log

# Bot 3 日志
tail -f logs/bot3-helper.log
```

### 检查Bot进程
```bash
ps aux | grep bot[123]_
```

### 查看PID文件
```bash
cat /tmp/bot1.pid    # Bot 1 PID
cat /tmp/bot2.pid    # Bot 2 PID
cat /tmp/bot3.pid    # Bot 3 PID
```

---

## 🔐 安全说明

### Token管理
- 所有Token都硬编码在Bot文件中
- 生产环境建议使用环境变量
- 定期轮换Token

### 权限控制
- 当前所有用户都可以使用
- 可配置管理员白名单（ADMIN_IDS列表）
- 敏感命令建议添加权限验证

---

## 📊 系统状态

### 当前运行状态
```
✅ Bot 1 (服务监控): 运行中 (PID: 141411)
✅ Bot 2 (数据处理): 运行中 (PID: 141436)
✅ Bot 3 (用户帮助): 运行中 (PID: 141679)
```

### 服务端口
```
Docker:
  - PostgreSQL: 15432
  - Redis: 16379
  - FastAPI: 28001

Web:
  - Flask: 5000
```

---

## 🛠️ 故障排查

### Bot无响应
1. 检查Bot进程是否运行
   ```bash
   ps aux | grep bot[123]_
   ```

2. 查看日志寻找错误
   ```bash
   tail -100 logs/bot1-monitor.log
   tail -100 logs/bot2-processor.log
   tail -100 logs/bot3-helper.log
   ```

3. 重启Bot
   ```bash
   ./stop_all_bots.sh
   ./start_all_bots.sh
   ```

### API连接失败
1. 检查FastAPI服务
   ```bash
   curl http://localhost:28001/health
   ```

2. 检查Docker容器
   ```bash
   docker ps | grep bossjy
   ```

3. 使用Bot 1查看状态
   ```
   /status
   /health
   ```

### 文件上传失败
1. 检查文件格式（CSV/Excel）
2. 确认文件大小（<50MB）
3. 查看Bot 2日志
4. 联系Bot 3获取支持

---

## 📖 使用示例

### 示例1: 每日系统检查
```
1. 打开Bot 1（服务监控）
2. 发送 /status
3. 发送 /health
4. 查看是否有异常
```

### 示例2: 处理华人数据
```
1. 打开Bot 2（数据处理）
2. 准备CSV文件（包含姓名、电话等）
3. 直接发送文件给Bot
4. 选择 /filter_chinese
5. 等待处理完成
6. 下载结果文件
```

### 示例3: 新用户学习
```
1. 打开Bot 3（用户帮助）
2. 发送 /quickstart
3. 阅读快速指南
4. 发送 /features 了解功能
5. 有问题发送 /support
```

---

## 🔄 更新日志

### 2025-10-07
- ✅ 创建三Bot系统架构
- ✅ Bot 1: 服务监控功能完成
- ✅ Bot 2: 数据处理基础功能
- ✅ Bot 3: 用户帮助完整功能
- ✅ 统一启动/停止脚本
- ✅ 完整使用文档

---

## 📞 技术支持

如有任何问题，请：

1. 查看Bot 3的FAQ: `/faq`
2. 联系技术支持: `/support` (在Bot 3中)
3. 提交反馈: `/feedback` (在Bot 3中)

---

**BossJy Pro Team**
Version: 1.0.0 (Three-Bot System)
