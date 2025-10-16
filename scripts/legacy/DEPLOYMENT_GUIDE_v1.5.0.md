# 部署指南：v1.5.0 充值积分UI/授权/USDT校验全面修复

**版本**: v1.5.0-recharge-fix
**发布日期**: 2025-10-07
**Git Tag**: `v1.5.0-recharge-fix`
**部署环境**: Production (Ubuntu/Debian + Nginx + Gunicorn + PostgreSQL)

---

## 📋 部署前检查清单

### 1. 环境准备
- [ ] 确认当前分支为 `main`
- [ ] 确认已拉取最新代码 (`git pull origin main`)
- [ ] 确认标签已创建 (`git tag -l | grep v1.5.0`)
- [ ] 备份数据库（可选但推荐）
- [ ] 备份当前配置文件

### 2. 依赖版本确认
```bash
# Python 版本
python3 --version  # 需要 >= 3.9

# Nginx 版本
nginx -v  # 需要 >= 1.18

# PostgreSQL 版本
psql --version  # 需要 >= 12
```

### 3. 磁盘空间检查
```bash
df -h  # 确保至少有 2GB 可用空间
```

---

## 🚀 部署步骤

### Step 1: 拉取代码并切换到标签
```bash
cd /path/to/BossJy-Cn
git fetch --all --tags
git checkout main
git pull origin main
git checkout v1.5.0-recharge-fix

# 验证当前版本
git describe --tags
# 输出: v1.5.0-recharge-fix
```

### Step 2: 安装新增 Python 依赖
```bash
# 激活虚拟环境
source venv/bin/activate  # 或 source .venv/bin/activate

# 安装 base58 加密货币地址校验库
pip install base58==2.1.1

# 验证安装
python3 -c "import base58; print('✓ base58 installed')"

# 【可选】安装所有依赖（如果 requirements.txt 有其他更新）
pip install -r requirements.txt
```

**安装时间**: 约 10-30 秒

### Step 3: 更新 Nginx 配置
```bash
# 检查 nginx 配置文件路径
cat nginx/snippets/proxy-params.conf

# 验证配置包含以下内容:
# proxy_set_header Authorization $http_authorization;
# proxy_pass_header Authorization;

# 测试 Nginx 配置
sudo nginx -t

# 输出应为:
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### Step 4: 重新加载 Nginx（零停机）
```bash
sudo nginx -s reload

# 验证 Nginx 进程
sudo systemctl status nginx
# 输出: active (running)
```

**停机时间**: 0秒（reload 不中断服务）

### Step 5: 重启 Flask/Gunicorn 应用
```bash
# 方法 1: systemd 服务重启
sudo systemctl restart bossjy-web.service

# 方法 2: 手动重启（如果使用 gunicorn 直接启动）
pkill -f gunicorn && gunicorn app.web_app:app -c gunicorn_config.py &

# 方法 3: Docker 容器重启（如果使用 Docker）
docker-compose restart web

# 验证应用状态
sudo systemctl status bossjy-web.service
# 或
curl -I http://localhost:9001/health
```

**预计重启时间**: 5-10 秒

### Step 6: 验证静态文件部署
```bash
# 检查新增的 apiClient.js 是否存在
ls -lh web/static/js/apiClient.js

# 输出应为:
# -rw-r--r-- 1 user group 6.2K Oct  7 12:00 web/static/js/apiClient.js

# 验证文件可访问（通过浏览器或 curl）
curl -I http://your-domain.com/static/js/apiClient.js
# 应返回: 200 OK
```

---

## ✅ 部署后验证

### 1. 后端 API 验证

#### 测试 USDT 地址校验 API
```bash
# 有效地址测试
curl -X POST http://localhost:9001/api/v1/credits/usdt/create-order \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "amount": 10,
    "network_type": "TRC20",
    "usdt_address": "TYuZ9xQQu9zxCQvE8GJxUWv3Jx7s9p5RXC"
  }'

# 预期输出: 200 OK, {"success": true, "order_id": "ORD-..."}

# 无效地址测试
curl -X POST http://localhost:9001/api/v1/credits/usdt/create-order \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "amount": 10,
    "network_type": "TRC20",
    "usdt_address": "0x742d35Cc6634C0532925a3b844Bc454e4438f44e"
  }'

# 预期输出: 422 Unprocessable Entity
# {"detail": [{"loc": ["body", "usdt_address"], "msg": "Value error, 无效的USDT-TRC20地址格式"}]}
```

#### 测试 Token 刷新功能
```bash
# 使用过期 token 访问 API（应自动刷新）
curl -X GET http://localhost:9001/api/v1/user/credits \
  -H "Authorization: Bearer EXPIRED_TOKEN"

# 预期行为:
# - 第一次返回 401
# - apiClient.js 自动调用 /api/v1/auth/refresh
# - 重试原请求并返回正确数据
```

### 2. 前端 UI 验证

访问以下页面并检查：

#### Dashboard 页面 (`/dashboard`)
- [ ] 积分卡片显示正常
- [ ] "充值积分" 按钮存在且可点击
- [ ] "查看历史" 按钮存在且可点击
- [ ] 点击按钮正确跳转到对应页面

#### USDT 充值页面 (`/usdt_recharge`)
- [ ] USDT 地址输入框显示
- [ ] 输入有效 TRC20 地址时显示 "✓ 地址格式正确"（绿色）
- [ ] 输入无效地址时显示 "✗ 无效的TRC20地址格式"（红色）
- [ ] 无效地址时"生成支付订单"按钮禁用
- [ ] 空地址时按钮仍可点击（地址为可选字段）

### 3. 浏览器控制台验证
打开浏览器开发者工具（F12），检查：

#### Console 日志
```
应无报错，特别是：
✓ 无 "401 Unauthorized" 循环
✓ 无 "Failed to fetch" 错误
✓ 无 "apiClient is not defined" 错误
```

#### Network 面板
```
测试场景: 访问需要认证的页面，等待 token 过期

预期行为:
1. 第一个请求返回 401
2. 自动发起 /api/v1/auth/refresh 请求
3. 刷新成功后重试原请求
4. 原请求返回 200 OK

验证 Headers:
✓ Authorization: Bearer xxx (每个请求都应携带)
```

### 4. 审计日志验证
```bash
# 查看应用日志
tail -f logs/app.log | grep AUDIT

# 创建一个 USDT 订单后，应看到类似日志:
# [AUDIT] 用户 123 (test_user) 创建USDT充值订单 | 金额: 10 USDT | 网络: TRC20 | 地址: TYuZ9xQQu9...9p5RXC | 地址校验: 通过

# 验证地址已脱敏（仅显示前10位和后6位）
```

### 5. 运行自动化测试（可选）
```bash
# 在开发环境中运行
pytest tests/test_recharge_fix.py -v

# 预期输出:
# tests/test_recharge_fix.py::TestUSDTAddressValidation::test_valid_trc20_addresses PASSED
# tests/test_recharge_fix.py::TestUSDTAddressValidation::test_invalid_trc20_addresses PASSED
# ...
# ======================== 12 passed in 0.15s ========================
```

---

## 📊 功能验收清单

详细验收步骤请参考 [`TESTING_RECHARGE_FIX.md`](./TESTING_RECHARGE_FIX.md)

**快速验收**（5分钟）：
1. ✅ 登录系统，访问 Dashboard
2. ✅ 点击积分卡片的"充值积分"按钮
3. ✅ 在充值页面输入 USDT 地址（测试地址: `TYuZ9xQQu9zxCQvE8GJxUWv3Jx7s9p5RXC`）
4. ✅ 观察实时校验反馈（绿色✓）
5. ✅ 尝试输入无效地址（如 `0x742d35...`），观察红色✗和按钮禁用
6. ✅ 提交订单，检查审计日志

---

## 🔄 回滚方案

如果部署后发现问题，可快速回滚：

### 方法 1: 回滚到上一个稳定版本
```bash
# 切换到上一个标签
git checkout v1.4.x  # 替换为上一个稳定版本

# 重启服务
sudo systemctl restart bossjy-web.service
sudo nginx -s reload
```

### 方法 2: 仅回滚 Nginx 配置
```bash
# 删除 proxy-params.conf 中新增的 Authorization 头设置
sudo vim /etc/nginx/snippets/proxy-params.conf

# 删除或注释以下两行:
# proxy_set_header Authorization $http_authorization;
# proxy_pass_header Authorization;

# 重新加载
sudo nginx -s reload
```

### 方法 3: 卸载 base58 依赖
```bash
pip uninstall base58 -y

# 降级到旧版 credits_api.py（需手动恢复）
git checkout v1.4.x -- app/api/credits_api.py

# 重启应用
sudo systemctl restart bossjy-web.service
```

**回滚时间**: 1-2 分钟

---

## 📝 已知限制与注意事项

### 1. Flask MPA 架构限制
- 页面跳转会触发全页刷新（非 SPA 单页应用）
- 建议未来迁移到 React/Vue SPA 以获得更好的用户体验

### 2. USDT 地址校验
- **前端校验**: 仅使用正则表达式（快速但不完整）
- **后端校验**: 使用 Base58Check + 0x41 前缀验证（严格）
- 最终以**后端校验为准**

### 3. Token 刷新机制
- 如果 refresh_token 也过期，用户会被重定向到登录页
- 建议在 `/api/v1/auth/refresh` 端点设置更长的 refresh_token 有效期

### 4. 审计日志
- 地址脱敏格式: `前10位...后6位`（如 `TYuZ9xQQu9...9p5RXC`）
- 日志文件路径: `logs/app.log`（需定期轮转）

### 5. Nginx 配置
- `proxy_set_header Authorization` 仅影响新的请求
- 如果使用多个 Nginx 实例（负载均衡），需同步配置

---

## 🛠️ 故障排查

### 问题 1: "apiClient is not defined"
**原因**: `apiClient.js` 未正确加载
**解决**:
```bash
# 检查文件是否存在
ls web/static/js/apiClient.js

# 检查模板是否引入
grep -n "apiClient.js" web/templates/dashboard_cyberpunk.html

# 清除浏览器缓存后重试
```

### 问题 2: USDT 地址校验总是失败
**原因**: `base58` 库未安装
**解决**:
```bash
pip install base58==2.1.1
sudo systemctl restart bossjy-web.service
```

### 问题 3: 401 错误循环
**原因**: Nginx 未透传 Authorization 头
**解决**:
```bash
# 检查 Nginx 配置
grep -A2 "Authorization" /etc/nginx/snippets/proxy-params.conf

# 应包含:
# proxy_set_header Authorization $http_authorization;
# proxy_pass_header Authorization;

# 重新加载 Nginx
sudo nginx -s reload
```

### 问题 4: Token 刷新失败
**检查步骤**:
```bash
# 1. 确认刷新端点存在
curl -X POST http://localhost:9001/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'

# 2. 检查应用日志
tail -f logs/app.log | grep refresh

# 3. 验证 localStorage 中是否有 refresh_token
# （需在浏览器 Console 中执行）
# localStorage.getItem('refresh_token')
```

---

## 📞 支持与联系

**部署支持**: Claude Code Agent
**文档版本**: v1.0
**最后更新**: 2025-10-07

**相关文档**:
- [验收测试清单](./TESTING_RECHARGE_FIX.md)
- [Pull Request 详情](./PR_RECHARGE_FIX.md)
- [自动化测试脚本](./tests/test_recharge_fix.py)

---

## ✅ 部署签署

**部署执行人**: ___________________
**部署日期**: ___________________
**验证结果**: [ ] 通过  [ ] 失败（备注: ___________________）

**回滚决策** (如适用):
[ ] 无需回滚
[ ] 已回滚至版本: ___________________

---

**🤖 Generated with Claude Code**
**Co-Authored-By: Claude <noreply@anthropic.com>**
