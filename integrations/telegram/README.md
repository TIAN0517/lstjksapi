# BossJy-Pro Telegram Integration

这个目录包含 Telegram Bot 与主控系统的集成文件。

## 文件结构

- `bot_handler.py` - Telegram Bot 处理器
- `message_router.py` - 消息路由器
- `user_manager.py` - 用户管理
- `command_handler.py` - 命令处理器

## 集成状态

✅ Telegram Bot 已成功集成到主控系统
✅ 支持用户查询和文件上传
✅ 支持与 BossJy-Pro 主控系统通信
✅ 支持信用系统集成

## 使用方法

1. 确保主控系统正在运行
2. 设置环境变量 `TELEGRAM_BOT_TOKEN`
3. 启动 Telegram Bot 服务

## API 端点

- `/api/telegram/webhook` - Telegram Webhook 端点
- `/api/telegram/status` - Bot 状态查询
- `/api/telegram/users` - 用户管理
