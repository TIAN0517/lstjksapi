# Filter System 容器管理架构

## 1. 端口架构设计

### 对外服务端口（External Services）
```
┌─────────────────┬────────────┬─────────────────┬──────────────┐
│   服务名称      │  外部端口  │   内部端口      │   用途说明   │
├─────────────────┼────────────┼─────────────────┼──────────────┤
│ Nginx Proxy     │ 80, 443    │ 80              │ Web入口代理   │
│ Go API          │ 8080       │ 8080            │ 过滤系统API   │
│ FastAPI         │ 18001      │ 8000            │ 业务逻辑API   │
│ PostgreSQL      │ 15432      │ 5432            │ 数据库访问    │
│ Redis           │ 16379      │ 6379            │ 缓存访问      │
└─────────────────┴────────────┴─────────────────┴──────────────┘
```

### 内部服务端口（Internal Services）
```
┌─────────────────┬────────────┬─────────────────┬──────────────┐
│   服务名称      │  内部端口  │   通信对象      │   用途说明   │
├─────────────────┼────────────┼─────────────────┼──────────────┤
│ Vue Frontend    │ 80         │ Nginx           │ 前端页面     │
│ Telegram Bots   │ 9001       │ 内部监控        │ Bot服务      │
│ FastAPI         │ 8000       │ Nginx/Go API    │ API服务      │
│ PostgreSQL      │ 5432       │ Go/FastAPI      │ 数据存储     │
│ Redis           │ 6379       │ Go/FastAPI      │ 缓存服务     │
└─────────────────┴────────────┴─────────────────┴──────────────┘
```

## 2. 容器网络架构

### 网络分层设计
```
Internet
    ↓
[Nginx: 80/443] ← 外部访问入口
    ↓
┌─────────────────────────────────────┐
│           Application Layer         │
│  ┌─────────────┐ ┌─────────────┐   │
│  │ Vue: 80     │ │ Go API:8080 │   │
│  └─────────────┘ └─────────────┘   │
│  ┌─────────────┐ ┌─────────────┐   │
│  │ FastAPI:8000│ │ Bots:9001   │   │
│  └─────────────┘ └─────────────┘   │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│           Data Layer                │
│  ┌─────────────┐ ┌─────────────┐   │
│  │ PostgreSQL  │ │   Redis     │   │
│  │   :5432     │ │   :6379     │   │
│  └─────────────┘ └─────────────┘   │
└─────────────────────────────────────┘
```

## 3. 容器管理策略

### 服务分组管理
```yaml
# Web服务组
web_services:
  - nginx          # 反向代理
  - vue-frontend   # 前端界面
  
# API服务组  
api_services:
  - go-api         # 过滤系统API
  - fastapi        # 业务逻辑API
  
# 数据服务组
data_services:
  - postgres       # 主数据库
  - redis          # 缓存服务
  
# 应用服务组
app_services:
  - bots           # Telegram机器人
```

### 启动顺序管理
```bash
# 1. 基础设施服务
docker-compose up -d postgres redis

# 2. API服务
docker-compose up -d go-api fastapi

# 3. 应用服务
docker-compose up -d bots vue-frontend

# 4. 代理服务
docker-compose up -d nginx
```

## 4. 端口冲突处理

### 当前端口冲突解决
```bash
# 停止冲突服务
docker stop bossjy-pro-app  # 释放28001端口

# 启动新架构服务
docker-compose up -d
```

### 端口预留规划
```
8000-8099: API服务端口
9000-9099: 内部服务端口  
15000-15999: 数据库服务端口
16000-16099: 缓存服务端口
```

## 5. 安全访问控制

### 外部端口访问控制
```nginx
# Nginx配置示例
server {
    listen 80;
    server_name _;
    
    # API访问限制
    location /api/ {
        allow 192.168.1.0/24;  # 内网访问
        deny all;
        proxy_pass http://fastapi:8000;
    }
    
    # 数据库访问禁止
    location /database/ {
        deny all;
    }
}
```

### 内部服务隔离
```yaml
# 网络隔离配置
networks:
  frontend-network:    # 前端网络
    driver: bridge
  backend-network:     # 后端网络  
    driver: bridge
  database-network:    # 数据库网络
    driver: bridge
    internal: true     # 纯内部网络
```

## 6. 监控和管理

### 健康检查配置
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 30s
```

### 日志管理
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 7. 部署建议

### 生产环境配置
- 使用HTTPS（443端口）
- 禁用不必要的内部端口对外访问
- 配置防火墙规则
- 设置访问频率限制

### 开发环境配置
- 保留直接API访问端口（8080, 18001）
- 启用调试模式
- 开发数据库访问端口（15432）

## 8. 容器管理命令

### 批量管理
```bash
# 启动所有服务
docker-compose up -d

# 按组启动
docker-compose up -d postgres redis
docker-compose up -d go-api fastapi

# 停止所有服务
docker-compose down

# 重启特定服务
docker-compose restart go-api

# 查看服务状态
docker-compose ps
```

### 监控命令
```bash
# 查看端口使用
netstat -tlnp | grep LISTEN

# 查看容器日志
docker-compose logs -f go-api

# 查看资源使用
docker stats
```