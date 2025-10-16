# BossJy Bot管理系统使用指南

## 概述

本系统提供了一个统一的管理界面来启动、停止、监控和维护所有的Telegram Bot。系统包括以下组件：

1. `bot_manager.py` - Python核心管理程序
2. `manage_bots.sh` - Shell管理脚本
3. `monitor_system.sh` - 系统监控脚本
4. `install_bot_dependencies.sh` - 依赖安装脚本

## 安装要求

### 快速安装（推荐）

```bash
# 运行依赖安装脚本
./install_bot_dependencies.sh
```

### 手动安装

```bash
# 安装必要的Python包
pip3 install psutil python-telegram-bot psycopg2-binary requests

# 确保脚本具有执行权限
chmod +x manage_bots.sh monitor_system.sh install_bot_dependencies.sh
```

## 使用方法

### 1. 基本管理命令

```bash
# 启动所有Bot
./manage_bots.sh start

# 停止所有Bot
./manage_bots.sh stop

# 强制停止所有Bot
./manage_bots.sh stop -f

# 重启所有Bot
./manage_bots.sh restart

# 查看Bot状态
./manage_bots.sh status

# 启动特定Bot
./manage_bots.sh -b bot1 start

# 停止特定Bot
./manage_bots.sh -b bot2 stop
```

### 2. 监控功能

```bash
# 实时监控Bot状态
./manage_bots.sh monitor

# 执行系统健康检查
./monitor_system.sh

# 实时监控系统状态
./monitor_system.sh -m
```

### 3. 维护功能

```bash
# 执行维护任务
./manage_bots.sh maintain
```

## 系统架构

### Bot管理器 (bot_manager.py)

核心功能：
- 进程管理（启动、停止、重启）
- 状态监控
- PID文件管理
- 日志管理

支持的Bot：
- bot1: 服务监控Bot
- bot2: 数据处理Bot
- bot3: 用户帮助Bot
- customer_bot: 客户服务Bot
- enhanced_bot: 增强版Bot

### 管理脚本 (manage_bots.sh)

提供命令行界面：
- 参数解析
- 颜色化输出
- 错误处理
- 帮助信息

### 监控脚本 (monitor_system.sh)

系统监控功能：
- 系统资源监控（CPU、内存、磁盘）
- Bot状态检查
- 网络连接检查
- 日志文件分析
- Telegram告警通知

## 配置说明

### 环境变量

```bash
# Telegram告警配置
export TELEGRAM_ALERT_BOT_TOKEN="your_bot_token"
export TELEGRAM_ALERT_CHAT_ID="your_chat_id"

# 数据库配置
export DB_HOST="localhost"
export DB_PORT="5432"
export DB_NAME="bossjy"
export DB_USER="bossjy"
export DB_PASSWORD="ji394su3"
```

## 日志管理

所有日志文件存储在 `logs/` 目录下：
- bot_manager.log: 管理器操作日志
- system_alerts.log: 系统告警日志
- health_check.log: 健康检查日志
- 各Bot的专用日志文件

## 自动化维护

建议将以下命令添加到crontab中：

```bash
# 每小时执行一次健康检查
0 * * * * /path/to/monitor_system.sh

# 每天凌晨执行维护任务
0 2 * * * /path/to/manage_bots.sh maintain
```

## 故障排除

### Bot无法启动
1. 检查日志文件：`logs/bot*-*.log`
2. 确认依赖包已安装
3. 检查环境变量配置

### Bot异常停止
1. 查看系统资源使用情况
2. 检查是否有错误日志
3. 使用`./manage_bots.sh restart`重启

### 监控告警
1. 检查告警日志：`logs/system_alerts.log`
2. 根据告警内容采取相应措施
3. 调整监控阈值（如需要）

## 最佳实践

1. **定期维护**：每天执行维护任务清理日志
2. **监控告警**：配置Telegram告警及时发现问题
3. **备份策略**：定期备份重要日志和配置文件
4. **权限管理**：确保脚本具有适当的执行权限
5. **日志轮转**：避免日志文件过大影响系统性能