# BossJy Bot 依赖安装说明

## 快速安装

```bash
# 运行依赖安装脚本
./install_bot_dependencies.sh
```

## 手动安装

### 1. 必需依赖

```bash
# 安装Python包
pip3 install psutil
pip3 install python-telegram-bot
pip3 install psycopg2-binary
pip3 install requests
```

### 2. 可选依赖

```bash
# Linux系统安装bc和curl
sudo apt-get install bc curl  # Ubuntu/Debian
sudo yum install bc curl      # CentOS/RHEL
```

## 依赖说明

| 包名 | 用途 | 必需性 |
|------|------|--------|
| psutil | 进程管理和系统监控 | 必需 |
| python-telegram-bot | Telegram Bot API | 必需 |
| psycopg2-binary | PostgreSQL数据库连接 | 必需 |
| requests | HTTP请求处理 | 必需 |
| bc | 命令行计算器 | 可选（监控脚本使用） |
| curl | HTTP客户端 | 可选（监控脚本使用） |

## 验证安装

```bash
# 验证Python包
python3 -c "import psutil; print('psutil版本:', psutil.__version__)"
python3 -c "import telegram; print('telegram版本:', telegram.__version__)"
python3 -c "import psycopg2; print('psycopg2版本:', psycopg2.__version__)"
```

## 故障排除

### 常见问题

1. **权限错误**：
   ```bash
   sudo ./install_bot_dependencies.sh
   ```

2. **pip命令未找到**：
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3-pip
   
   # CentOS/RHEL
   sudo yum install python3-pip
   ```

3. **编译错误（psycopg2）**：
   ```bash
   # Ubuntu/Debian
   sudo apt-get install libpq-dev python3-dev
   
   # CentOS/RHEL
   sudo yum install postgresql-devel python3-devel
   ```

### 网络问题

如果遇到网络问题，可以使用国内镜像源：

```bash
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple psutil
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple python-telegram-bot
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple psycopg2-binary
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple requests
```