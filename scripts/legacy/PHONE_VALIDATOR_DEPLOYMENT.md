# BossJy 免費全球電話號碼驗證引擎部署文檔

## 🎯 概述

BossJy 電話號碼驗證引擎是一個基於 FastAPI 的高性能電話號碼驗證服務，支援全球 200+ 國家和地區的電話號碼驗證。

## ✨ 功能特性

- **全球號碼驗證**: 支援 200+ 國家和地區的電話號碼格式驗證
- **號碼類型識別**: 自動識別手機、固網、VoIP、付費號碼等類型
- **SQLite 數據庫**: 本地存儲驗證記錄，支援統計查詢
- **RESTful API**: 提供 REST 接口，支援 GET/POST 方式
- **實時統計**: 提供驗證統計、國家分布、類型分布等數據
- **美觀控制台**: 使用 Rich 庫提供彩色日誌和進度條顯示
- **健康檢查**: 內置健康檢查端點，監控服務狀態

## 🚀 快速啟動

### 方法一：使用啟動腳本

```bash
cd /mnt/d/BossJy-Cn/BossJy-Cn
./start_phone_validator.sh
```

### 方法二：直接啟動

```bash
cd /mnt/d/BossJy-Cn/BossJy-Cn
python phone_validator.py
```

### 方法三：使用 uvicorn

```bash
cd /mnt/d/BossJy-Cn/BossJy-Cn
uvicorn phone_validator:app --host 0.0.0.0 --port 18001
```

## 📡 API 接口

### 1. 健康檢查

**端點**: `GET /health`

**響應**:
```json
{
  "status": "healthy",
  "service": "BossJy Phone Validator",
  "version": "1.0.0",
  "timestamp": "2025-10-08T17:33:49.385157"
}
```

### 2. 電話號碼驗證

**端點**: 
- `POST /api/validate/phone`
- `GET /api/validate/phone`

**參數**:
- `phone` (必需): 要驗證的電話號碼
- `country_code` (可選): 國家代碼 (例如: TW, US, CN)

**POST 請求示例**:
```json
{
  "phone": "+886912345678",
  "country_code": "TW"
}
```

**GET 請求示例**:
```
GET /api/validate/phone?phone=+886912345678&country_code=TW
```

**響應**:
```json
{
  "is_valid": true,
  "phone": "+886912345678",
  "normalized_number": "+886912345678",
  "country": "TW",
  "country_code": "TW",
  "type": "mobile",
  "error": null
}
```

### 3. 統計信息

**端點**: `GET /api/stats`

**響應**:
```json
{
  "total_validations": 12,
  "valid_count": 10,
  "invalid_count": 2,
  "success_rate": 83.33,
  "country_distribution": {
    "TW": 4,
    "CN": 2,
    "GB": 2,
    "US": 2
  },
  "type_distribution": {
    "mobile": 6,
    "fixed_line": 2,
    "fixed_line_or_mobile": 2
  },
  "sample_numbers": [
    {
      "masked_number": "+44xxx750",
      "country": "GB",
      "type": "fixed_line",
      "created_at": "2025-10-08T17:33:49.385157"
    }
  ]
}
```

## 🧪 測試

運行測試腳本：

```bash
cd /mnt/d/BossJy-Cn/BossJy-Cn
python test_phone_validator.py
```

測試腳本會自動測試：
- 健康檢查端點
- 多國電話號碼驗證 (台灣、美國、中國大陸、英國、日本等)
- 統計信息 API
- GET/POST 兩種請求方式

## 📁 項目結構

```
/mnt/d/BossJy-Cn/BossJy-Cn/
├── phone_validator.py          # 主服務文件
├── start_phone_validator.sh    # 啟動腳本
├── test_phone_validator.py     # 測試腳本
├── requirements.txt            # 依賴套件
├── db/
│   └── phone_stats.db         # SQLite 數據庫
└── logs/
    └── phone_validator.log    # 日誌文件
```

## 📦 依賴套件

主要依賴套件 (已更新至最新版本):

```
fastapi==0.115.11
uvicorn[standard]==0.32.0
phonenumbers==8.13.45
redis==5.3.1
httptools==0.6.4
watchfiles==0.24.0
pydantic==2.10.6
rich==13.7.0
```

## 🔧 配置說明

### 數據庫配置
- 數據庫類型: SQLite
- 數據庫路徑: `/mnt/d/BossJy-Cn/BossJy-Cn/db/phone_stats.db`
- 自動創建表結構和索引

### 日誌配置
- 日誌級別: INFO
- 日誌文件: `/mnt/d/BossJy-Cn/BossJy-Cn/logs/phone_validator.log`
- 同時輸出到控制台和文件

### 服務配置
- 服務端口: 18001
- 綁定地址: 0.0.0.0 (允許外部訪問)
- 支援熱重載: 開發模式下可用

## 🚨 故障排除

### 1. 依賴衝突問題

如果遇到 redis 或 phonenumbers 版本衝突：

```bash
# 卸載舊版本
pip uninstall redis phonenumbers

# 重新安裝正確版本
pip install redis==5.3.1 phonenumbers==8.13.45
```

### 2. 端口佔用問題

如果端口 18001 被佔用：

```bash
# 查找佔用進程
lsof -i :18001

# 終止進程
kill -9 <PID>

# 或者更改端口
uvicorn phone_validator:app --port 18002
```

### 3. 數據庫權限問題

確保數據庫目錄有寫入權限：

```bash
chmod 755 /mnt/d/BossJy-Cn/BossJy-Cn/db
chmod 644 /mnt/d/BossJy-Cn/BossJy-Cn/db/phone_stats.db
```

## 📊 性能優化

- **數據庫索引**: 已為 country、type、created_at 字段創建索引
- **連接池**: SQLite 自動管理連接
- **異步處理**: FastAPI 提供高並發處理能力
- **日誌級別**: 生產環境可調整為 WARNING 以提高性能

## 🔒 安全建議

- 生產環境建議使用 HTTPS
- 可添加 API 認證中間件
- 定期備份 SQLite 數據庫文件
- 監控日誌文件大小

## 📈 監控指標

系統提供以下監控指標：
- 總驗證數量
- 有效/無效號碼比例
- 各國號碼分布
- 號碼類型分布
- 實時成功率

## 🎉 成功案例

測試結果顯示：
- ✅ 健康檢查: 通過
- ✅ 電話號碼驗證: 7/7 通過
- ✅ 統計信息: 通過
- 📊 成功率: 83.33%
- 🌍 支援國家: TW, CN, GB, US 等

---

**BossJy 團隊專業 AI 助理開發**  
*部署完成時間: 2025-10-08*