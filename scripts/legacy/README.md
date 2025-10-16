# 智能黑名单/白名单过滤系统管理平台

## 📖 项目简介

这是一个基于 Go + Vue 3 的智能过滤系统管理平台，支持黑名单和白名单管理，提供实时过滤、统计分析和数据导出功能。

## ✨ 功能特性

- 🔐 **用户认证**: JWT令牌认证，支持登录注册
- 🛡️ **过滤器管理**: 支持手机号、IP、邮箱、设备等多种类型过滤
- ⚫ **黑名单管理**: 添加、删除、查询黑名单项
- ⚪ **白名单管理**: 添加、删除、查询白名单项
- 📊 **统计分析**: 实时统计、趋势图表、数据可视化
- 📤 **数据导出**: 支持CSV格式数据导出
- 🐳 **容器化部署**: Docker + Docker Compose 一键部署
- 🔒 **HTTPS支持**: Nginx反向代理，SSL证书配置

## 🏗️ 技术架构

### 后端技术栈
- **语言**: Go 1.21+
- **框架**: Gin Web Framework
- **数据库**: MySQL 8.0
- **缓存**: Redis 6.0
- **ORM**: GORM
- **认证**: JWT-Go

### 前端技术栈
- **框架**: Vue 3 + TypeScript
- **UI库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router
- **HTTP客户端**: Axios
- **图表**: ECharts
- **构建工具**: Vite

### 部署技术
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx
- **SSL**: Let's Encrypt / 自签名证书

## 🚀 快速开始

### 环境要求
- Docker 20.0+
- Docker Compose 2.0+
- Git

### 一键部署

1. 克隆项目
```bash
git clone <repository-url>
cd BossJy-Cn
```

2. 运行初始化脚本
```bash
chmod +x init.sh
sudo ./init.sh
```

3. 启动服务
```bash
docker-compose up -d --build
```

4. 访问系统
- 前端地址: http://localhost
- 后端API: http://localhost:8080
- 健康检查: http://localhost:8080/health

### 默认账号
- 用户名: `admin`
- 密码: `admin123`

## 📁 项目结构

```
BossJy-Cn/
├── filter-system/          # Go后端项目
│   ├── cmd/server/         # 主程序入口
│   ├── internal/           # 内部包
│   │   ├── config/         # 配置管理
│   │   ├── handler/        # HTTP处理器
│   │   ├── middleware/     # 中间件
│   │   ├── model/          # 数据模型
│   │   ├── repository/     # 数据访问层
│   │   └── service/        # 业务逻辑层
│   ├── configs/            # 配置文件
│   ├── docker/             # Docker文件
│   └── go.mod              # Go模块文件
├── src/                    # Vue前端项目
│   ├── src/                # 源代码
│   │   ├── api/            # API接口
│   │   ├── components/     # 组件
│   │   ├── layout/         # 布局组件
│   │   ├── router/         # 路由配置
│   │   ├── stores/         # 状态管理
│   │   ├── types/          # 类型定义
│   │   └── views/          # 页面组件
│   ├── docker/             # Docker文件
│   └── package.json        # 依赖配置
├── deployment/             # 部署配置
│   ├── nginx.conf          # Nginx配置
│   └── init.sql            # 数据库初始化
├── docker-compose.yml      # Docker编排
├── init.sh                 # 初始化脚本
├── test_api.sh             # API测试脚本
└── README.md               # 项目文档
```

## 🔧 开发环境

### 后端开发
```bash
cd filter-system
go mod tidy
go run cmd/server/main.go
```

### 前端开发
```bash
cd src
npm install
npm run dev
```

## 📝 API文档

### 认证接口
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/refresh` - 刷新令牌

### 过滤器接口
- `POST /api/v1/filter/check` - 过滤检查
- `GET /api/v1/filter/blacklist` - 获取黑名单
- `POST /api/v1/filter/blacklist` - 添加黑名单
- `DELETE /api/v1/filter/blacklist/:id` - 删除黑名单
- `GET /api/v1/filter/whitelist` - 获取白名单
- `POST /api/v1/filter/whitelist` - 添加白名单
- `DELETE /api/v1/filter/whitelist/:id` - 删除白名单

### 统计接口
- `GET /api/v1/admin/stats` - 获取统计数据
- `GET /api/v1/admin/stats/filter` - 获取过滤统计
- `POST /api/v1/admin/stats/export` - 导出数据

## 🧪 测试

### API测试
```bash
# 使用脚本测试
chmod +x test_api.sh
./test_api.sh

# 或使用REST Client插件
# 在VS Code中打开 api_test.http 文件
```

## 🔒 安全配置

### 生产环境配置
1. 修改默认密码
2. 更换JWT密钥
3. 配置HTTPS证书
4. 设置防火墙规则
5. 定期备份数据

### SSL证书配置
```bash
# 自签名证书
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout deployment/ssl/key.pem \
  -out deployment/ssl/cert.pem

# Let's Encrypt证书
certbot --nginx -d your-domain.com
```

## 📊 监控和日志

### 日志查看
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f nginx
```

### 性能监控
- 系统资源使用情况
- API响应时间
- 数据库查询性能
- Redis缓存命中率

## 🔄 更新和维护

### 更新服务
```bash
# 拉取最新代码
git pull

# 重新构建和启动
docker-compose down
docker-compose up -d --build
```

### 数据备份
```bash
# 备份数据库
docker exec filter-mysql mysqldump -u root -p filter_system > backup.sql

# 备份Redis数据
docker exec filter-redis redis-cli BGSAVE
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🆘 支持

如果您遇到问题或有疑问，请：
1. 查看 [FAQ](docs/FAQ.md)
2. 搜索 [Issues](../../issues)
3. 创建新的 [Issue](../../issues/new)

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者！