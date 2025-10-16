# BossJy-Pro 完整部署與登入流程指南

## 📋 目錄
1. [環境需求](#環境需求)
2. [後端部署](#後端部署)
3. [前端部署](#前端部署)
4. [登入流程驗證](#登入流程驗證)
5. [API 端點說明](#api-端點說明)

---

## 🔧 環境需求

### Python 環境
- **Python 版本**: 3.11.9 (推薦)
- **虛擬環境**: venv
- **套件管理**: pip 25.2+

### 已安裝套件
```bash
pandas==2.2.2
numpy>=1.26.4,<2.0.0
fastapi==0.115.11
uvicorn==0.32.0
pydantic==2.10.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
sqlalchemy==2.0.23
```

---

## 🚀 後端部署

### 1. 安裝步驟

```bash
# 1. 確認 Python 版本
python3.11 --version
# 輸出: Python 3.11.9

# 2. 建立虛擬環境（已完成）
python3.11 -m venv venv

# 3. 激活虛擬環境
source venv/bin/activate

# 4. 升級 pip
pip install --upgrade pip wheel setuptools

# 5. 安裝依賴
pip install -r requirements.txt

# 6. 驗證安裝
python -c "import pandas, numpy; print(f'pandas: {pandas.__version__}, numpy: {numpy.__version__}')"
```

### 2. 啟動後端服務

```bash
# 方法一：使用啟動腳本（推薦）
./start_dev_server.sh

# 方法二：直接啟動
source venv/bin/activate
uvicorn app.web_app:app --host 0.0.0.0 --port 9001 --reload
```

### 3. 驗證後端運行

訪問 http://localhost:9001/docs 查看 API 文檔

---

## 🎨 前端部署

### 1. 安裝依賴

```bash
cd frontend
npm install
```

### 2. 啟動開發服務器

```bash
npm run dev
```

### 3. 訪問前端

瀏覽器打開 http://localhost:5173

---

## 🔐 登入流程驗證

### 完整登入流程

#### 1. 用戶註冊 (POST /api/v1/auth/register)

```bash
curl -X POST http://localhost:9001/api/v1/auth/register \
  -F "username=testuser" \
  -F "email=test@example.com" \
  -F "password=Test@123456" \
  -F "confirm_password=Test@123456"
```

**密碼規則**:
- 最少 8 位
- 至少 1 個大寫字母
- 至少 1 個小寫字母
- 至少 1 個數字

**成功響應**:
```json
{
  "success": true,
  "message": "注册成功！请登录并充值后开始使用。",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "role": "user",
    "tenant": "default"
  }
}
```

#### 2. 用戶登入 (POST /api/v1/auth/login)

```bash
curl -X POST http://localhost:9001/api/v1/auth/login \
  -F "username=testuser" \
  -F "password=Test@123456" \
  -c cookies.txt
```

**成功響應**:
```json
{
  "success": true,
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "tenant": "default",
    "role": "user",
    "is_active": true,
    "subscription_tier": "free",
    "monthly_usage_count": 0,
    "monthly_usage_limit": 1000
  }
}
```

**Cookie 設置**:
- `access_token`: HTTPOnly, SameSite=Strict
- 有效期: 24 小時
- 路徑: /

#### 3. 獲取用戶信息 (GET /api/v1/auth/me)

```bash
curl -X GET http://localhost:9001/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

**成功響應**:
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "tenant": "default",
    "role": "user",
    "is_active": true,
    "is_verified": false,
    "subscription_tier": "free",
    "monthly_usage_count": 0,
    "monthly_usage_limit": 1000,
    "created_at": "2025-10-08T10:30:00",
    "last_login_at": "2025-10-08T10:35:00"
  }
}
```

#### 4. 登出 (POST /api/v1/auth/logout)

```bash
curl -X POST http://localhost:9001/api/v1/auth/logout \
  -b cookies.txt
```

**成功響應**:
```json
{
  "success": true,
  "message": "登出成功"
}
```

---

## 📡 API 端點說明

### 認證相關

| 端點 | 方法 | 說明 | 權限 |
|------|------|------|------|
| `/api/v1/auth/register` | POST | 用戶註冊 | 公開 |
| `/api/v1/auth/login` | POST | 用戶登入 | 公開 |
| `/api/v1/auth/logout` | POST | 用戶登出 | 需登入 |
| `/api/v1/auth/me` | GET | 獲取當前用戶信息 | 需登入 |
| `/api/v1/auth/subscription/info` | GET | 獲取訂閱信息 | 需登入 |

### 權限系統

#### 角色類型
- **admin**: 管理員（完整系統訪問權限）
- **user**: 普通用戶（基本功能權限）
- **guest**: 訪客（僅限查看）

#### 權限驗證
```python
# 後端權限驗證
from app.auth import require_admin, get_current_user

@router.get("/admin/users")
async def list_users(current_user = Depends(require_admin)):
    # 僅管理員可訪問
    pass

@router.get("/profile")
async def get_profile(current_user = Depends(get_current_user)):
    # 所有登入用戶可訪問
    pass
```

---

## 🎯 前端集成

### 1. Auth Store 使用

```javascript
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// 登入
const result = await authStore.login({
  username: 'testuser',
  password: 'Test@123456'
})

if (result.success) {
  router.push('/dashboard')
}

// 獲取用戶信息
await authStore.fetchUserInfo()

// 檢查權限
if (authStore.isAdmin) {
  // 管理員功能
}

// 登出
await authStore.logout()
router.push('/login')
```

### 2. 路由守衛

```javascript
// router/index.js
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // 需要認證的頁面
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
    return
  }

  // 需要管理員權限
  if (to.meta.requiresAdmin && !authStore.isAdmin) {
    ElMessage.error('需要管理員權限')
    next('/')
    return
  }

  next()
})
```

### 3. Dashboard 功能

登入後 Dashboard 顯示：
- ✅ 歡迎卡片（用戶名、角色、登入時間）
- ✅ 統計卡片（總人數、華人數量、佔比、涵蓋國家）
- ✅ 圖表區域（國家分布、置信度分布）
- ✅ 最近活動日誌
- ✅ 用戶狀態與權限顯示

---

## 🧪 測試腳本

### 完整登入流程測試

```bash
#!/bin/bash

echo "🧪 開始測試登入流程..."

# 1. 註冊
echo "1️⃣ 測試註冊..."
curl -X POST http://localhost:9001/api/v1/auth/register \
  -F "username=testuser$(date +%s)" \
  -F "email=test$(date +%s)@example.com" \
  -F "password=Test@123456" \
  -F "confirm_password=Test@123456"

# 2. 登入
echo -e "\n2️⃣ 測試登入..."
RESPONSE=$(curl -s -X POST http://localhost:9001/api/v1/auth/login \
  -F "username=testuser" \
  -F "password=Test@123456")

TOKEN=$(echo $RESPONSE | jq -r '.access_token')
echo "Token: ${TOKEN:0:50}..."

# 3. 獲取用戶信息
echo -e "\n3️⃣ 測試獲取用戶信息..."
curl -X GET http://localhost:9001/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"

# 4. 登出
echo -e "\n4️⃣ 測試登出..."
curl -X POST http://localhost:9001/api/v1/auth/logout

echo -e "\n✅ 測試完成！"
```

---

## 📊 系統狀態檢查

### 檢查後端服務

```bash
# 健康檢查
curl http://localhost:9001/health

# API 文檔
curl http://localhost:9001/docs

# 檢查認證端點
curl http://localhost:9001/api/v1/auth/me
```

### 檢查前端服務

```bash
# 檢查前端服務
curl http://localhost:5173

# 檢查靜態資源
ls frontend/dist/
```

---

## 🔒 安全配置

### 生產環境配置

```bash
# .env 文件
JWT_SECRET=<your-secret-key-change-in-production>
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@localhost/bossjy
REDIS_URL=redis://localhost:6379

# 啟用 HTTPS
# Cookie 設置
# - secure=True
# - samesite=strict
# - httponly=True
```

---

## 📝 常見問題

### Q1: 登入失敗，提示 "無效的令牌"
**A**: 檢查 JWT_SECRET 是否正確設置

### Q2: Cookie 沒有設置
**A**: 確認後端設置了 `response.set_cookie()`

### Q3: 前端無法訪問 /api/v1/auth/me
**A**: 檢查 axios 請求頭是否包含 `Authorization: Bearer <token>`

### Q4: pandas/numpy 安裝失敗
**A**: 確認使用 Python 3.11.9，並安裝編譯工具

---

## ✅ 驗證清單

- [x] Python 3.11.9 已安裝
- [x] 虛擬環境已建立
- [x] 所有依賴已安裝（pandas, numpy, fastapi）
- [x] 後端 JWT 認證已實現
- [x] /auth/me 端點已建立
- [x] 權限管理系統已完成
- [x] 前端 Auth Store 已實現
- [x] Dashboard 已完成（含用戶信息顯示）
- [x] 登入流程完整運行

---

## 🎉 完成狀態

**系統已完全修復並可正常運行！**

### 後端完成項目
✅ Python 3.11.9 環境
✅ FastAPI + Pydantic
✅ JWT 認證中間件
✅ 完整的用戶註冊/登入/登出 API
✅ /auth/me 獲取用戶信息端點
✅ 權限管理（admin/user/guest）
✅ Cookie 安全設置（HTTPOnly, SameSite）

### 前端完成項目
✅ Auth Store (Pinia)
✅ Login/Register 組件
✅ Dashboard（含用戶歡迎卡片）
✅ 路由守衛
✅ 權限檢查
✅ 自動獲取用戶信息

---

**作者**: Claude Code
**更新日期**: 2025-10-08
**版本**: 1.0.0
