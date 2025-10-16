# 充值积分UI/授权跳转/USDT校验 - 验收测试清单

**分支**: `fix/recharge-auth-ui-usdt`
**日期**: 2025-10-07
**测试人**: _________

---

## ✅ 测试清单

### 1. UI一致性测试

#### 测试步骤：
1. 访问 `/dashboard`
2. 观察「积分余额」卡片与其他数据卡片的对齐情况

#### 验收标准：
- [ ] 四张卡片（总筛选次数、本月筛选、成功匹配、积分余额）等高对齐
- [ ] 积分卡片包含两个操作按钮：「充值积分」和「查看历史」
- [ ] 按钮样式为 `neon-button--purple` 和 `neon-button--cyan`
- [ ] Icon 大小一致（40px × 40px）
- [ ] 字体大小一致：
  - 卡片数值：`text-3xl` (3rem)
  - 卡片标签：`text-sm`
  - 按钮文字：`0.8rem`

#### 实际结果：
```
代码位置: web/templates/dashboard_cyberpunk.html:253-267
- Icon容器: 40px × 40px ✓
- 数值显示: data-card__value ✓
- 按钮容器: margin-top: 12px, flex gap: 8px ✓
```

---

### 2. 路由跳转测试（无整页重载）

#### 测试步骤：
1. 打开浏览器 DevTools → Network 标签页
2. 勾选「Preserve log」
3. 点击「查看历史」按钮
4. 观察 Network 是否出现 `document` 类型的请求

#### 验收标准：
- [ ] 点击「查看历史」按钮后，URL 变为 `/credits#history`
- [ ] **没有**整页重载（Network 中无 `document` 类型请求）
- [ ] 成功显示历史记录数据
- [ ] 用户保持登入状态（顶部导航栏积分余额仍显示）

#### 实际结果：
```
注意：当前实现使用 window.location.href='/credits#history'，
这会触发整页重载。如需避免重载，应使用 History API 或 SPA 路由。

代码位置: web/templates/dashboard_cyberpunk.html:504-506
```

#### ⚠️ 已知问题：
由于项目是 MPA 架构（非 SPA），页面间跳转会有整页重载。这是架构限制，但不影响核心功能。

---

### 3. USDT 地址校验测试

#### 测试步骤：
1. 访问 `/credits` 或 `/usdt_recharge`
2. 选择充值套餐
3. 测试以下地址输入：

| 输入地址 | 预期结果 |
|---------|---------|
| ` ` (空) | 允许提交（可选字段） |
| `TXYZopNCsuJfjw...` (有效TRC20) | ✓ 地址格式正确（绿色提示） |
| `0x742d35...` (ETH地址) | ✗ 无效的TRC20地址（红色提示 + 按钮禁用） |
| `abc123` | ✗ 无效的TRC20地址（红色提示 + 按钮禁用） |

#### 验收标准：
- [ ] 空地址时不显示错误，允许提交
- [ ] 有效TRC20地址（T开头34位）显示绿色✓提示
- [ ] 无效地址显示红色✗提示
- [ ] 无效地址时「生成支付二维码」按钮被禁用 (`disabled=true`)

#### 实际结果：
```
前端校验: web/templates/usdt_recharge.html:327-364
后端校验: app/api/credits_api.py:32-53, 359-364

校验逻辑:
- 正则: /^T[1-9A-HJ-NP-Za-km-z]{33}$/
- Base58Check: 后端使用 base58 库验证
```

---

### 4. 创建订单API测试

#### 测试步骤（使用 curl 或 Postman）：

```bash
# 1. 有效请求
curl -X POST https://api-v2.jytian.it.com:8443/api/v1/credits/usdt/create-order \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 10,
    "network_type": "TRC20",
    "usdt_address": "TYuZ9xQQu9zxCQvE8GJx..."
  }'

# 预期响应: 201 Created
{
  "success": true,
  "order_id": "ORD-20251007-XXXX",
  "wallet_address": "...",
  "qr_code_url": "...",
  "amount": 10.0,
  "credits": 10000
}

# 2. 无效地址请求
curl -X POST ... -d '{
  "amount": 10,
  "network_type": "TRC20",
  "usdt_address": "0x742d35..."
}'

# 预期响应: 422 Unprocessable Entity
{
  "detail": [
    {
      "loc": ["body", "usdt_address"],
      "msg": "Value error, 无效的USDT-TRC20地址格式",
      "type": "value_error"
    }
  ]
}
```

#### 验收标准：
- [ ] 有效地址 → 201 Created，返回 `order_id`
- [ ] 无效地址 → 422 Unprocessable Entity
- [ ] 空地址 → 201 Created（可选字段）
- [ ] 未登录 → 401 Unauthorized

---

### 5. Token 刷新与持久化测试

#### 测试步骤：
1. 登入系统，观察 `localStorage.access_token` 和 `localStorage.refresh_token`
2. 手动清空 `access_token`（保留 `refresh_token`）
3. 刷新页面或发起 API 请求
4. 观察是否自动刷新 token

#### 验收标准：
- [ ] 刷新页面后仍保持登入（读取 `localStorage.access_token`）
- [ ] `access_token` 过期时，自动调用 `/api/v1/auth/refresh`
- [ ] 刷新成功后，重试原始请求
- [ ] 仅在 `refresh_token` 也过期时才跳转 `/login?next=...`

#### 实际结果：
```
API 客户端: web/static/js/apiClient.js:25-120
- 刷新机制: isRefreshing + refreshQueue (防并发)
- 重试逻辑: config._isRetry = true
- 登出跳转: redirectToLogin() 保留 next 参数
```

---

### 6. 401 错误处理测试

#### 测试步骤：
1. 打开浏览器 Console
2. 手动修改 `localStorage.access_token` 为无效值
3. 点击任意需要认证的操作（如查看积分余额）
4. 观察：
   - Console 是否有 Toast 提示
   - 是否立即跳转登入页

#### 验收标准：
- [ ] 首次 401 时，**不立即跳转**，而是尝试刷新 token
- [ ] Toast 显示：「登入已過期，請重新登入」
- [ ] 仅在刷新失败后才跳转 `/login?next=/current/path`
- [ ] 跳转URL包含当前页面作为 `next` 参数

#### 实际结果：
```
错误处理: web/static/js/apiClient.js:82-117
- 刷新失败时显示 Toast
- 跳转保留 next: window.location.pathname + window.location.search
```

---

### 7. 审计日志测试

#### 测试步骤：
1. 创建一个充值订单（有效 USDT 地址）
2. 检查后端日志文件或控制台输出

#### 验收标准：
- [ ] 日志包含：`[AUDIT] 用户 {user_id} ({username}) 创建USDT充值订单`
- [ ] 日志包含：金额、网络类型、地址（脱敏显示）
- [ ] 日志包含：`地址校验: 通过`
- [ ] 订单创建成功后，日志包含：`order_id` 和积分数量

#### 实际结果：
```
日志位置: app/api/credits_api.py:385-412

示例输出:
[AUDIT] 用户 123 (test_user) 创建USDT充值订单 | 金额: 10 USDT | 网络: TRC20 | 地址: TYuZ9xQQu9...Jx7s9p | 地址校验: 通过
[AUDIT] 订单创建成功 | order_id: ORD-20251007-XXXX | 积分: 10000
```

---

## 🔧 部署检查清单

### Nginx 配置更新
```bash
# 1. 检查 proxy-params.conf 是否已更新
cat /etc/nginx/snippets/proxy-params.conf | grep Authorization

# 预期输出:
# proxy_set_header Authorization $http_authorization;
# proxy_pass_header Authorization;

# 2. 重载 Nginx
sudo nginx -t && sudo nginx -s reload
```

### 环境变量配置
```bash
# .env 文件确认
export ALLOWED_ORIGINS="https://jytian.it.com,https://api-v2.jytian.it.com:8443"
```

### Python 依赖安装
```bash
# 安装 base58 库
pip install base58==2.1.1
```

---

## 📊 测试结果汇总

| 测试项 | 状态 | 备注 |
|-------|-----|------|
| UI 一致性 | ⬜ |  |
| 路由跳转（无重载） | ⬜ | MPA 架构会有整页重载 |
| USDT 地址前端校验 | ⬜ |  |
| USDT 地址后端校验 | ⬜ |  |
| 创建订单 API | ⬜ |  |
| Token 持久化 | ⬜ |  |
| 401 错误处理 | ⬜ |  |
| 审计日志 | ⬜ |  |
| Nginx 配置 | ⬜ |  |

---

## 🐛 已知问题与限制

1. **MPA 架构导致整页重载**
   - 原因：项目使用 Flask MPA，非 React SPA
   - 影响：页面跳转会有整页重载
   - 解决方案：未来迁移到 SPA 或使用 HTMX

2. **前端 Base58Check 校验简化**
   - 原因：避免引入大型 JS 库
   - 当前：仅正则格式校验
   - 后端：完整 Base58Check + 0x41 前缀校验

---

## ✅ 签字确认

- [ ] 所有测试通过
- [ ] 代码已 Review
- [ ] 部署清单已执行

**测试人签字**: _____________
**日期**: _____________
