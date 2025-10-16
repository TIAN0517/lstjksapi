# ⚠️ Cloudflare Flexible SSL 额外设置

您已将 SSL 模式改为 Flexible，但还需要关闭 "Always Use HTTPS" 才能正常工作。

---

## 🔧 必须完成的设置

### 关闭 "Always Use HTTPS"

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)
2. 选择域名 **tiankai.it.com**
3. 进入 **SSL/TLS** → **Edge Certificates**
4. 找到 **Always Use HTTPS**
5. 将其设置为 **OFF**（关闭）

**为什么需要关闭？**
- Flexible SSL 模式下，Cloudflare 通过 HTTP 连接到源服务器
- 如果 "Always Use HTTPS" 开启，Cloudflare 会将 HTTP 重定向到 HTTPS
- 这会造成循环，导致 520 错误

---

## ✅ 完整设置检查清单

在 Cloudflare Dashboard 确认以下设置：

### SSL/TLS 设置
- **SSL/TLS 加密模式**: ✅ Flexible
- **Always Use HTTPS**: ❌ OFF（关闭）
- **Minimum TLS Version**: 1.2（默认）

### DNS 设置
- **A 记录**: appai.tiankai.it.com → 146.88.134.254
- **Proxy status**: ✅ Proxied（橙色云）

---

## 🧪 完成后测试

关闭 "Always Use HTTPS" 后，等待 1-2 分钟，然后测试：

```bash
# 测试 HTTPS /docs
curl https://appai.tiankai.it.com/docs
# 应返回 Swagger UI HTML

# 在浏览器打开
https://appai.tiankai.it.com/docs
# 应显示完整 API 文档界面
```

---

## 📊 工作原理

### Flexible SSL 模式流程：

```
用户浏览器
    ↓ HTTPS (加密)
Cloudflare
    ↓ HTTP (未加密) ← 这一步需要 HTTP 可用
源服务器 (Nginx port 80)
    ↓
后端 (port 8000)
```

如果开启 "Always Use HTTPS"：
```
Cloudflare → HTTP 请求 → Nginx
Nginx → 返回 301 重定向到 HTTPS
Cloudflare → 再次 HTTP 请求 → Nginx
...（无限循环，导致 520 错误）
```

---

## ⚡ 当前状态

- ✅ Nginx 配置已更新（支持 HTTP 直接访问）
- ✅ 后端服务运行正常（port 8000）
- ✅ Cloudflare SSL 模式已改为 Flexible
- ⚠️ 需要关闭 "Always Use HTTPS"

完成此步骤后，https://appai.tiankai.it.com/docs 即可正常访问！
