# BossJy-CN 快速启动指南

**5分钟快速启动所有服务**

---

## 🚀 一键启动

### Windows 用户

```bash
# 1. 启动所有服务
./start_all.sh

# 2. 验证服务状态
./check_services.sh

# 3. 访问应用
# - Web界面: http://localhost:9001
# - API文档: http://localhost:28001/docs
```

### Linux 用户

```bash
# 1. 给脚本添加执行权限
chmod +x *.sh

# 2. 启动所有服务
./start_all.sh

# 3. 查看服务状态
./check_services.sh
```

---

## 📋 完整流程

### 第一次启动

```bash
# 步骤1: 检查 Python 环境
python --version  # 需要 >= 3.9

# 步骤2: 创建虚拟环境（如果没有）
python -m venv venv

# 步骤3: 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 步骤4: 安装依赖
pip install -r requirements.txt

# 步骤5: 启动数据库（Docker方式）
docker-compose up -d postgres redis

# 步骤6: 启动所有服务
./start_all.sh
```

---

## 🔄 常用命令

| 操作 | 命令 | 说明 |
|------|------|------|
| **启动** | `./start_all.sh` | 启动所有服务 |
| **停止** | `./stop_all.sh` | 停止所有服务 |
| **重启** | `./restart_all.sh` | 重启所有服务 |
| **状态** | `./check_services.sh` | 查看服务状态 |
| **日志** | `tail -f logs/*.log` | 查看实时日志 |

---

**🤖 Generated with Claude Code**
