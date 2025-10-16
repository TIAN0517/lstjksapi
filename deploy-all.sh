#!/bin/bash

# BossJy-Cn 完整系统一键部署脚本

echo "==================================="
echo "BossJy-Cn 完整系统一键部署脚本"
echo "==================================="

# 1. 检查Docker是否安装
echo "[1/8] 检查Docker环境..."
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装或未启动"
    echo "请先安装Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo "✓ Docker已安装"

# 2. 检查Docker Compose是否可用
echo "[2/8] 检查Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose不可用"
    exit 1
fi
echo "✓ Docker Compose已就绪"

# 3. 停止现有服务
echo "[3/8] 停止现有服务..."
docker-compose -f docker-compose.frontend.yml down > /dev/null 2>&1
echo "✓ 已停止现有服务"

# 4. 清理旧镜像（可选）
echo "[4/8] 清理旧镜像..."
read -p "是否清理旧的Docker镜像？(y/n): " clean_images
if [ "$clean_images" = "y" ] || [ "$clean_images" = "Y" ]; then
    docker system prune -f
    echo "✓ 已清理旧镜像"
else
    echo "跳过清理旧镜像"
fi

# 5. 构建并启动所有服务
echo "[5/8] 构建并启动所有服务..."
docker-compose -f docker-compose.frontend.yml up --build -d
if [ $? -ne 0 ]; then
    echo "错误: 服务启动失败"
    exit 1
fi
echo "✓ 服务启动成功"

# 6. 等待服务就绪
echo "[6/8] 等待服务就绪..."
sleep 10

# 7. 检查服务状态
echo "[7/8] 检查服务状态..."
docker-compose -f docker-compose.frontend.yml ps

# 8. 显示访问信息
echo "[8/8] 系统部署完成！"
echo ""
echo "==================================="
echo "BossJy-Cn 系统已成功部署！"
echo ""
echo "访问地址:"
echo "- 前端应用: http://localhost:3000"
echo "- 后端API: http://localhost:18001"
echo "- API文档: http://localhost:18001/docs"
echo "- 数据库: localhost:15432"
echo "- Redis: localhost:16379"
echo ""
echo "默认账户:"
echo "- 用户名: admin@bossjy.com"
echo "- 密码: admin123"
echo ""
echo "管理命令:"
echo "- 查看日志: docker-compose -f docker-compose.frontend.yml logs -f"
echo "- 停止系统: docker-compose -f docker-compose.frontend.yml down"
echo "- 重启系统: docker-compose -f docker-compose.frontend.yml restart"
echo "==================================="
echo ""

# 询问是否查看日志
read -p "是否查看实时日志？(y/n): " view_logs
if [ "$view_logs" = "y" ] || [ "$view_logs" = "Y" ]; then
    echo "显示实时日志（按Ctrl+C退出）..."
    docker-compose -f docker-compose.frontend.yml logs -f
fi