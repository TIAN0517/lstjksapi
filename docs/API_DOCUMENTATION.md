# BossJy-Pro API 文档

## 📋 目录

- [概述](#概述)
- [认证](#认证)
- [用户管理](#用户管理)
- [电话验证](#电话验证)
- [数据管理](#数据管理)
- [系统监控](#系统监控)
- [错误处理](#错误处理)
- [速率限制](#速率限制)
- [示例代码](#示例代码)

## 概述

BossJy-Pro 是一个企业级的电话验证和数据管理系统，提供完整的RESTful API接口。

### 基础信息

- **Base URL**: `https://api.bossjy.com`
- **API Version**: `v1`
- **Content Type**: `application/json`
- **认证方式**: JWT Bearer Token

### 响应格式

所有API响应都遵循统一格式：

```json
{
  "success": true,
  "data": {},
  "message": "操作成功",
  "timestamp": "2023-01-01T00:00:00Z",
  "request_id": "req_123456789"
}
```

## 认证

### 获取访问令牌

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**响应示例：**

```json
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {
      "id": "user_123",
      "username": "your_username",
      "email": "user@example.com",
      "role": "user",
      "subscription_tier": "premium"
    }
  }
}
```

### 刷新令牌

```http
POST /api/auth/refresh
Authorization: Bearer your_access_token
```

### 登出

```http
POST /api/auth/logout
Authorization: Bearer your_access_token
```

## 用户管理

### 用户注册

```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "new_user",
  "email": "newuser@example.com",
  "password": "SecurePassword123",
  "confirm_password": "SecurePassword123",
  "tenant": "default"
}
```

### 获取用户信息

```http
GET /api/auth/me
Authorization: Bearer your_access_token
```

### 更新用户信息

```http
PUT /api/auth/profile
Authorization: Bearer your_access_token
Content-Type: application/json

{
  "email": "newemail@example.com",
  "phone": "+86 138 0000 0000"
}
```

### 修改密码

```http
POST /api/auth/change-password
Authorization: Bearer your_access_token
Content-Type: application/json

{
  "current_password": "old_password",
  "new_password": "NewSecurePassword123",
  "confirm_password": "NewSecurePassword123"
}
```

## 电话验证

### 验证单个电话号码

```http
POST /api/phone/validate
Authorization: Bearer your_access_token
Content-Type: application/json

{
  "phone_number": "+86 138 0000 0000",
  "default_region": "CN"
}
```

**响应示例：**

```json
{
  "success": true,
  "data": {
    "is_valid": true,
    "country_code": "CN",
    "national_number": "13800000000",
    "carrier": "China Mobile",
    "timezone": "Asia/Shanghai",
    "formatted_number": "+86 138 0000 0000"
  }
}
```

### 批量验证电话号码

```http
POST /api/phone/batch-validate
Authorization: Bearer your_access_token
Content-Type: application/json

{
  "phone_numbers": [
    "+86 138 0000 0000",
    "+1 555 123 4567",
    "+44 20 7946 0958"
  ],
  "default_region": "CN"
}
```

### 获取国家信息

```http
GET /api/phone/country-info/{country_code}
Authorization: Bearer your_access_token
```

### 获取支持的地区列表

```http
GET /api/phone/supported-regions
Authorization: Bearer your_access_token
```

## 数据管理

### 导入数据

```http
POST /api/data/import
Authorization: Bearer your_access_token
Content-Type: multipart/form-data

{
  "file": "data.csv",
  "table_name": "users",
  "skip_duplicates": true,
  "batch_size": 1000
}
```

### 导出数据

```http
GET /api/data/export
Authorization: Bearer your_access_token
Query Parameters:
  - table_name: 表名
  - format: csv|json|xlsx
  - filters: JSON格式的过滤条件
```

### 查询数据

```http
GET /api/data/query
Authorization: Bearer your_access_token
Query Parameters:
  - table: 表名
  - page: 页码 (默认: 1)
  - size: 每页大小 (默认: 20)
  - sort: 排序字段
  - order: asc|desc
  - filters: JSON格式的过滤条件
```

**响应示例：**

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "1",
        "name": "张三",
        "phone": "+86 138 0000 0000",
        "created_at": "2023-01-01T00:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "size": 20,
      "total": 100,
      "pages": 5
    }
  }
}
```

## 系统监控

### 获取系统状态

```http
GET /api/system/status
Authorization: Bearer your_access_token
```

### 获取性能指标

```http
GET /api/performance/metrics
Authorization: Bearer your_access_token
```

### 获取健康检查

```http
GET /api/health
```

### 获取安全状态

```http
GET /api/security/status
Authorization: Bearer your_access_token
```

## 错误处理

### 错误代码

| 代码 | 说明 |
|------|------|
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 422 | 数据验证失败 |
| 429 | 请求过于频繁 |
| 500 | 服务器内部错误 |
| 502 | 网关错误 |
| 503 | 服务不可用 |
| 504 | 网关超时 |

### 错误响应格式

```json
{
  "success": false,
  "error": "validation_error",
  "message": "请求参数验证失败",
  "details": [
    {
      "field": "email",
      "message": "邮箱格式不正确"
    }
  ],
  "path": "/api/auth/register",
  "timestamp": "2023-01-01T00:00:00Z",
  "request_id": "req_123456789"
}
```

## 速率限制

### 限制规则

- **普通用户**: 100 请求/分钟
- **高级用户**: 500 请求/分钟
- **企业用户**: 2000 请求/分钟

### 速率限制头

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## 示例代码

### Python 示例

```python
import requests
import json

class BossJyClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.token = None
    
    def login(self):
        """登录获取令牌"""
        response = requests.post(
            f"{self.base_url}/api/auth/login",
            json={
                "username": self.username,
                "password": self.password
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data['data']['access_token']
            return True
        return False
    
    def validate_phone(self, phone_number, region="CN"):
        """验证电话号码"""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(
            f"{self.base_url}/api/phone/validate",
            headers=headers,
            json={
                "phone_number": phone_number,
                "default_region": region
            }
        )
        return response.json()
    
    def batch_validate_phones(self, phone_numbers, region="CN"):
        """批量验证电话号码"""
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(
            f"{self.base_url}/api/phone/batch-validate",
            headers=headers,
            json={
                "phone_numbers": phone_numbers,
                "default_region": region
            }
        )
        return response.json()

# 使用示例
client = BossJyClient("https://api.bossjy.com", "your_username", "your_password")
if client.login():
    result = client.validate_phone("+86 138 0000 0000")
    print(result)
```

### JavaScript 示例

```javascript
class BossJyClient {
    constructor(baseUrl, username, password) {
        this.baseUrl = baseUrl;
        this.username = username;
        this.password = password;
        this.token = null;
    }
    
    async login() {
        const response = await fetch(`${this.baseUrl}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: this.username,
                password: this.password
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            this.token = data.data.access_token;
            return true;
        }
        return false;
    }
    
    async validatePhone(phoneNumber, region = 'CN') {
        const response = await fetch(`${this.baseUrl}/api/phone/validate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.token}`
            },
            body: JSON.stringify({
                phone_number: phoneNumber,
                default_region: region
            })
        });
        
        return await response.json();
    }
}

// 使用示例
const client = new BossJyClient('https://api.bossjy.com', 'your_username', 'your_password');
client.login().then(success => {
    if (success) {
        client.validatePhone('+86 138 0000 0000').then(result => {
            console.log(result);
        });
    }
});
```

### cURL 示例

```bash
# 登录
curl -X POST "https://api.bossjy.com/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'

# 验证电话号码
curl -X POST "https://api.bossjy.com/api/phone/validate" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_access_token" \
  -d '{
    "phone_number": "+86 138 0000 0000",
    "default_region": "CN"
  }'

# 获取系统状态
curl -X GET "https://api.bossjy.com/api/system/status" \
  -H "Authorization: Bearer your_access_token"
```

## 更新日志

### v1.2.0 (2023-01-09)
- 新增企业级安全中间件
- 新增性能优化系统
- 新增完整的CI/CD流水线
- 新增API文档
- 优化错误处理机制
- 提升系统稳定性

### v1.1.0 (2023-01-01)
- 新增电话验证API
- 新增数据导入导出功能
- 新增用户管理功能
- 新增系统监控功能

### v1.0.0 (2022-12-01)
- 初始版本发布
- 基础认证系统
- 基础API框架

---

**技术支持**: support@bossjy.com  
**文档更新**: 2023-01-09  
**API版本**: v1.2.0
