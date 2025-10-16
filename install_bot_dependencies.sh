#!/bin/bash
################################################################################
# BossJy Bot 依赖安装脚本
# 安装所有必需的依赖包
################################################################################

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 项目配置
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}BossJy Bot 依赖安装脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检测操作系统
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    OS="windows"
    PIP_CMD="pip"
else
    OS="linux"
    PIP_CMD="pip3"
fi

echo -e "${YELLOW}检测到操作系统: $OS${NC}"
echo ""

# 检查Python
echo -n "检查Python... "
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ $PYTHON_VERSION${NC}"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version)
    echo -e "${GREEN}✅ $PYTHON_VERSION${NC}"
    PIP_CMD="pip"
else
    echo -e "${RED}❌ 未找到Python${NC}"
    exit 1
fi

# 更新pip
echo -n "更新pip... "
if $PIP_CMD install --upgrade pip >> install.log 2>&1; then
    echo -e "${GREEN}✅ 完成${NC}"
else
    echo -e "${YELLOW}⚠️  更新失败（可能需要sudo权限）${NC}"
fi

# 安装必需的Python包
REQUIRED_PACKAGES=(
    "psutil"           # 进程管理
    "python-telegram-bot"  # Telegram Bot API
    "psycopg2-binary"  # PostgreSQL数据库连接
    "requests"         # HTTP请求
)

echo ""
echo -e "${YELLOW}安装必需的Python包...${NC}"

for package in "${REQUIRED_PACKAGES[@]}"; do
    echo -n "安装 $package... "
    if $PIP_CMD install "$package" >> install.log 2>&1; then
        echo -e "${GREEN}✅ 完成${NC}"
    else
        echo -e "${RED}❌ 失败${NC}"
    fi
done

# 安装可选的Python包（用于监控和维护）
OPTIONAL_PACKAGES=(
    "bc"               # 计算工具（Linux）
    "curl"             # HTTP客户端（通常已预装）
)

echo ""
echo -e "${YELLOW}检查可选依赖...${NC}"

# 检查bc（用于监控脚本中的计算）
if command -v bc &> /dev/null; then
    echo -e "bc: ${GREEN}✅ 已安装${NC}"
else
    echo -e "bc: ${YELLOW}⚠️  未安装（Linux系统可使用包管理器安装）${NC}"
    if [[ "$OS" == "linux" ]]; then
        echo -e "    ${YELLOW}Ubuntu/Debian: sudo apt-get install bc${NC}"
        echo -e "    ${YELLOW}CentOS/RHEL: sudo yum install bc${NC}"
    fi
fi

# 检查curl
if command -v curl &> /dev/null; then
    echo -e "curl: ${GREEN}✅ 已安装${NC}"
else
    echo -e "curl: ${RED}❌ 未安装${NC}"
    if [[ "$OS" == "linux" ]]; then
        echo -e "    ${YELLOW}Ubuntu/Debian: sudo apt-get install curl${NC}"
        echo -e "    ${YELLOW}CentOS/RHEL: sudo yum install curl${NC}"
    fi
fi

# 验证安装
echo ""
echo -e "${YELLOW}验证安装...${NC}"

INSTALL_SUCCESS=true

# 验证psutil
echo -n "验证psutil... "
if python3 -c "import psutil; print('版本:', psutil.__version__)" >> install.log 2>&1; then
    echo -e "${GREEN}✅ 成功${NC}"
else
    echo -e "${RED}❌ 失败${NC}"
    INSTALL_SUCCESS=false
fi

# 验证python-telegram-bot
echo -n "验证python-telegram-bot... "
if python3 -c "import telegram; print('版本:', telegram.__version__)" >> install.log 2>&1; then
    echo -e "${GREEN}✅ 成功${NC}"
else
    echo -e "${RED}❌ 失败${NC}"
    INSTALL_SUCCESS=false
fi

# 验证psycopg2
echo -n "验证psycopg2... "
if python3 -c "import psycopg2; print('版本:', psycopg2.__version__)" >> install.log 2>&1; then
    echo -e "${GREEN}✅ 成功${NC}"
else
    echo -e "${RED}❌ 失败${NC}"
    INSTALL_SUCCESS=false
fi

# 设置执行权限
echo ""
echo -n "设置脚本执行权限... "
chmod +x "$PROJECT_DIR/manage_bots.sh" "$PROJECT_DIR/monitor_system.sh" 2>/dev/null || true
echo -e "${GREEN}✅ 完成${NC}"

echo ""
echo -e "${BLUE}========================================${NC}"
if [ "$INSTALL_SUCCESS" = true ]; then
    echo -e "${GREEN}✅ 所有必需依赖安装成功！${NC}"
    echo ""
    echo -e "现在可以使用以下命令管理Bot："
    echo -e "  ${GREEN}./manage_bots.sh start${NC}    - 启动所有Bot"
    echo -e "  ${GREEN}./manage_bots.sh stop${NC}     - 停止所有Bot"
    echo -e "  ${GREEN}./manage_bots.sh status${NC}   - 查看Bot状态"
    echo -e "  ${GREEN}./monitor_system.sh${NC}       - 执行系统健康检查"
else
    echo -e "${RED}❌ 部分依赖安装失败${NC}"
    echo -e "${YELLOW}请查看 install.log 文件获取详细信息${NC}"
fi
echo -e "${BLUE}========================================${NC}"