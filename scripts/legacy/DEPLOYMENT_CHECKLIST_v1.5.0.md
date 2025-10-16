# 📋 快速部署清单 - v1.5.0

**版本**: v1.5.0-recharge-fix | **预计时间**: 10 分钟

---

## ⚡ 部署步骤（按顺序执行）

### ✅ 1. 代码部署 (2分钟)
```bash
cd /path/to/BossJy-Cn
git checkout main && git pull origin main
git checkout v1.5.0-recharge-fix
```

### ✅ 2. 安装依赖 (1分钟)
```bash
source venv/bin/activate
pip install base58==2.1.1
python3 -c "import base58; print('✓ OK')"
```

### ✅ 3. Nginx 配置 (1分钟)
```bash
sudo nginx -t  # 验证配置
sudo nginx -s reload  # 零停机重载
```

### ✅ 4. 应用重启 (1分钟)
```bash
sudo systemctl restart bossjy-web.service
sudo systemctl status bossjy-web.service  # 确认运行中
```

### ✅ 5. 验证部署 (5分钟)

#### 5.1 后端验证
```bash
curl -I http://localhost:9001/health  # 200 OK
ls web/static/js/apiClient.js  # 文件存在
```

#### 5.2 前端验证（浏览器）
- [ ] 访问 `/dashboard`
- [ ] 积分卡片显示"充值积分"和"查看历史"按钮
- [ ] 访问 `/usdt_recharge`
- [ ] 输入 `TYuZ9xQQu9zxCQvE8GJxUWv3Jx7s9p5RXC`（有效地址）
- [ ] 看到绿色 ✓ "地址格式正确"
- [ ] 输入 `0x742d35Cc...`（无效地址）
- [ ] 看到红色 ✗ "无效的TRC20地址格式"，按钮禁用

#### 5.3 审计日志验证
```bash
tail -f logs/app.log | grep AUDIT
# 创建订单后应看到: [AUDIT] 用户 xxx ... 地址: TYuZ9xQQu9...9p5RXC
```

---

## 🚨 回滚方案（如需要）

```bash
git checkout v1.4.x  # 回滚到上一版本
sudo systemctl restart bossjy-web.service
sudo nginx -s reload
```

---

## 📞 问题排查

| 问题 | 解决方案 |
|------|----------|
| `apiClient is not defined` | 清除浏览器缓存，检查 `web/static/js/apiClient.js` 是否存在 |
| USDT校验失败 | `pip install base58==2.1.1` 并重启应用 |
| 401循环 | 检查 `nginx/snippets/proxy-params.conf` 包含 `Authorization` 头设置 |

---

## ✅ 签署确认

- [ ] 部署完成
- [ ] 验证通过
- [ ] 审计日志正常

**执行人**: __________ **日期**: __________ **签名**: __________

---

**详细文档**: [DEPLOYMENT_GUIDE_v1.5.0.md](./DEPLOYMENT_GUIDE_v1.5.0.md)
