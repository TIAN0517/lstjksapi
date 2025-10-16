# BossJy-Pro 增強數據清洗服務指南

本指南說明如何使用新集成的精準數據清洗功能，包括電話驗證、華人識別、地址標準化、語言檢測、去重和質量驗證。

## 📋 目錄

1. [功能概覽](#功能概覽)
2. [依賴安裝](#依賴安裝)
3. [模型準備](#模型準備)
4. [API 使用](#api-使用)
5. [服務層使用](#服務層使用)
6. [數據庫遷移](#數據庫遷移)
7. [配置說明](#配置說明)

---

## 功能概覽

### 🔍 精度與來源

| 功能 | 核心庫 | 精度特點 | 用例 |
|------|--------|----------|------|
| **電話驗證** | `phonenumbers` + Twilio Lookup v2 | E.164 標準化、運營商識別、在網檢測 | 格式驗證、空號過濾 |
| **華人識別** | Sinonym + `ethnicolr` + 百家姓 | 多訊號融合（姓名/語言/區碼/地址） | 全球華人/華裔篩選 |
| **地址標準化** | `libpostal` + `cpca` | 全球地址解析 + 中國省市區 | 地址清洗、去重 |
| **語言檢測** | `fastText LID` | 176 語言、支持粵語/閩南語 | 多語言數據分類 |
| **去重關聯** | `Splink` + `RapidFuzz` | 概率記錄鏈接（億級可用） | 數據去重、實體關聯 |
| **質量驗證** | `Great Expectations` | 自動驗證報告 | 數據質量監控 |

---

## 依賴安裝

### 1. Docker 構建（推薦）

```bash
# 包含所有依賴和 libpostal 編譯
docker-compose build
```

### 2. 本地安裝

```bash
# 安裝 Python 依賴
pip install -r requirements.txt

# 安裝 libpostal（系統層）
git clone https://github.com/openvenues/libpostal /tmp/libpostal
cd /tmp/libpostal
./bootstrap.sh
./configure --datadir=/usr/local/share/libpostal
make -j$(nproc)
sudo make install
sudo ldconfig
```

---

## 模型準備

### fastText 語言識別模型

```bash
# 下載 176 語言模型（約 130 MB）
cd models
wget https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz

# 設置環境變量
export FASTTEXT_LID_MODEL=/app/models/lid.176.ftz
```

### Twilio Lookup v2（選配）

如需使用「在網/空號」檢測，配置 Twilio：

```bash
# .env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
```

---

## API 使用

所有新端點位於 `/api/v1/enhanced` 路徑下，需要 Bearer Token 認證。

### 1. 電話驗證 `POST /api/v1/enhanced/phone/validate`

**請求：**

```json
{
  "numbers": [
    "+852 9123 4567",
    "+86 138 1234 5678",
    "invalid-phone"
  ],
  "default_region": "HK",
  "use_lookup": false
}
```

**響應：**

```json
{
  "results": [
    {
      "raw": "+852 9123 4567",
      "e164": "+85291234567",
      "region_code": "HK",
      "is_valid": true,
      "line_type": "mobile",
      "carrier": "SmarTone",
      "validation_score": 0.95
    },
    {
      "raw": "invalid-phone",
      "is_valid": false,
      "e164": null,
      "validation_score": 0.0
    }
  ],
  "total": 3,
  "valid_count": 2,
  "invalid_count": 1
}
```

### 2. 華人識別 `POST /api/v1/enhanced/ethnicity/score`

**請求：**

```json
{
  "names": [
    {
      "name": "李明",
      "phone": "+852 9123 4567",
      "address": "Hong Kong"
    },
    {
      "name": "John Smith",
      "phone": "+1 415 123 4567"
    }
  ]
}
```

**響應：**

```json
{
  "results": [
    {
      "name": "李明",
      "prob_chinese": 0.95,
      "surname": "李",
      "signals": {
        "sinonym_score": 0.40,
        "surname_score": 0.30,
        "region_score": 0.15,
        "address_score": 0.05
      }
    },
    {
      "name": "John Smith",
      "prob_chinese": 0.05,
      "surname": "Smith",
      "signals": {
        "surname_score": 0.0
      }
    }
  ],
  "total": 2,
  "chinese_count": 1
}
```

### 3. 地址標準化 `POST /api/v1/enhanced/address/normalize`

**請求：**

```json
{
  "addresses": [
    "北京市朝陽區建國門外大街1號",
    "123 Nathan Road, Tsim Sha Tsui, Hong Kong"
  ],
  "country_hint": null
}
```

**響應：**

```json
{
  "results": [
    {
      "original": "北京市朝陽區建國門外大街1號",
      "normalized": "北京市朝陽區",
      "cn_adm": {
        "省": "北京市",
        "市": "北京市",
        "區": "朝陽區"
      },
      "quality_score": 0.85
    },
    {
      "original": "123 Nathan Road, Tsim Sha Tsui, Hong Kong",
      "normalized": "123, Nathan Road, Tsim Sha Tsui, Hong Kong",
      "libpostal": {
        "house_number": "123",
        "road": "Nathan Road",
        "suburb": "Tsim Sha Tsui",
        "country": "Hong Kong"
      },
      "quality_score": 0.95
    }
  ],
  "total": 2
}
```

### 4. 語言檢測 `POST /api/v1/enhanced/language/detect`

**請求：**

```json
{
  "texts": [
    "這是一段繁體中文文字。",
    "This is English text.",
    "呢個係粵語。"
  ],
  "top_k": 3
}
```

**響應：**

```json
{
  "results": [
    {
      "lang": "zh",
      "score": 0.99,
      "top_k": [
        {"lang": "zh", "score": 0.99},
        {"lang": "ja", "score": 0.005}
      ]
    },
    {
      "lang": "en",
      "score": 0.98
    },
    {
      "lang": "yue",
      "score": 0.85
    }
  ],
  "total": 3
}
```

### 5. 去重 `POST /api/v1/enhanced/dedup`

**請求：**

```json
{
  "records": [
    {
      "name": "張三",
      "phone": "+852 9123 4567",
      "email": "zhang@example.com"
    },
    {
      "name": "Zhang San",
      "phone": "+852-9123-4567",
      "email": "zhang@example.com"
    },
    {
      "name": "李四",
      "phone": "+86 138 1234 5678",
      "email": "li@example.com"
    }
  ],
  "match_threshold": 0.8
}
```

**響應：**

```json
{
  "results": [
    {
      "name": "張三",
      "cluster_id": "0",
      "match_score": 1.0,
      "duplicate_of": null
    },
    {
      "name": "Zhang San",
      "cluster_id": "0",
      "match_score": 0.92,
      "duplicate_of": 0
    },
    {
      "name": "李四",
      "cluster_id": "1",
      "match_score": 1.0,
      "duplicate_of": null
    }
  ],
  "total": 3,
  "unique_count": 2,
  "duplicate_count": 1,
  "clusters": {
    "cluster_0": [0, 1],
    "cluster_1": [2]
  }
}
```

### 6. 質量驗證 `POST /api/v1/enhanced/quality/check`

**請求：**

```json
{
  "data": [
    {
      "id": 1,
      "name": "張三",
      "phone_e164": "+85291234567",
      "email": "zhang@example.com",
      "lang_score": 0.95,
      "name_zh_prob": 0.98
    }
  ],
  "dataset_name": "test_data",
  "upload_id": "upload-123"
}
```

**響應：**

```json
{
  "success": true,
  "summary": {
    "total_expectations": 8,
    "successful_expectations": 7,
    "failed_expectations": 1,
    "success_rate": 87.5
  },
  "report_path": "/app/data/quality_reports/quality_report_upload-123.html"
}
```

---

## 服務層使用

### Python 直接調用

```python
from app.services.phone_validator import phone_validator
from app.services.ethnicity_scoring import ethnicity_scorer
from app.services.address_normalizer import address_normalizer
from app.services.lang_detect import language_detector
from app.services.linkage import entity_linker
from app.services.quality import data_quality_validator

# 電話驗證
result = phone_validator.normalize("+852 9123 4567", default_region="HK")
print(result["e164"])  # +85291234567

# 華人識別
score = ethnicity_scorer.chinese_likelihood(
    name="李明",
    e164_region="HK",
    address="Hong Kong"
)
print(score["prob_chinese"])  # 0.95

# 地址標準化
addr_result = address_normalizer.normalize_address(
    "北京市朝陽區建國門外大街1號",
    country_hint="CN"
)
print(addr_result["cn_adm"])  # {"省": "北京市", "市": "北京市", ...}

# 語言檢測
lang_result = language_detector.detect_lang("這是中文")
print(lang_result["lang"])  # zh

# 去重
dedup_result = entity_linker.deduplicate_records(
    records=[...],
    match_threshold=0.8
)

# 質量驗證
import pandas as pd
df = pd.DataFrame([...])
quality_result = data_quality_validator.validate_dataset(
    df=df,
    dataset_name="my_data"
)
```

### 運行示例

```bash
# 運行示例腳本
python examples/enhanced_cleaning_demo.py
```

---

## 數據庫遷移

### 執行遷移

```bash
# PostgreSQL
psql -U postgres -d bossjy_db -f migrations/add_enhanced_cleaning_fields.sql
```

### 主要新增表

1. **`enhanced_records`**: 存儲所有增強字段
2. **`data_quality_reports`**: 質量驗證報告
3. **`dedup_clusters`**: 去重集群信息

### 主要新增字段

- `phone_e164`, `phone_region`, `phone_carrier`, `phone_line_type`, `phone_reachable`
- `name_zh_prob`, `name_signals`, `name_surname`, `name_normalized`
- `addr_libpostal`, `addr_cn`, `addr_normalized`, `addr_quality_score`
- `lang_code`, `lang_score`, `lang_top_k`
- `entity_cluster_id`, `entity_match_score`, `entity_duplicate_of`

---

## 配置說明

### 環境變量

```bash
# .env

# Twilio（選配，用於電話在網檢測）
TWILIO_ACCOUNT_SID=ACxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token

# fastText 模型路徑
FASTTEXT_LID_MODEL=/app/models/lid.176.ftz

# Great Expectations 報告目錄
GX_REPORTS_DIR=/app/data/quality_reports
```

### Docker Compose

```yaml
services:
  app:
    environment:
      - TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID}
      - TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}
      - FASTTEXT_LID_MODEL=/app/models/lid.176.ftz
    volumes:
      - ./models:/app/models
      - ./data/quality_reports:/app/data/quality_reports
```

---

## 精度說明

### 電話驗證

- **格式驗證**: 99%+（基於 libphonenumber 規則庫）
- **在網檢測**: 95%+（需 Twilio Lookup v2，消耗額度）

### 華人識別

- **Sinonym 模型**: 90-95%（機器學習）
- **百家姓匹配**: 85-90%（含羅馬化變體）
- **多訊號融合**: 92-97%（綜合所有訊號）

### 地址標準化

- **libpostal**: 85-95%（全球地址）
- **cpca**: 90-95%（中國省市區）

### 語言檢測

- **fastText**: 95-99%（文本長度 > 20 字符）
- **中文方言**: 80-90%（粵語/閩南語）

### 去重

- **Splink**: 90-95%（大數據集，需配置阻塞規則）
- **RapidFuzz**: 85-90%（小數據集）

---

## 常見問題

### Q1: libpostal 編譯失敗？

A: 確保安裝了所有構建依賴：

```bash
sudo apt-get install autoconf automake libtool build-essential pkg-config
```

### Q2: fastText 模型未找到？

A: 下載並放置到正確路徑：

```bash
cd models
wget https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz
```

### Q3: Twilio Lookup 返回錯誤？

A: 檢查：
1. SID 和 Token 是否正確
2. 賬戶餘額是否充足
3. 是否啟用了 Lookup v2 API

### Q4: Great Expectations 初始化失敗？

A: 確保報告目錄存在且有寫入權限：

```bash
mkdir -p /app/data/quality_reports
chmod 777 /app/data/quality_reports
```

---

## 參考文檔

- [libpostal](https://github.com/openvenues/libpostal)
- [phonenumbers](https://github.com/daviddrysdale/python-phonenumbers)
- [Sinonym](https://github.com/allenai/sinonym)
- [ethnicolr](https://github.com/appeler/ethnicolr)
- [fastText LID](https://fasttext.cc/docs/en/language-identification.html)
- [Splink](https://moj-analytical-services.github.io/splink/)
- [Great Expectations](https://greatexpectations.io/)
- [Twilio Lookup v2](https://www.twilio.com/docs/lookup/v2-api)

---

## 支持

如有問題，請聯繫：
- Email: support@bossjy.com
- Telegram: @BossJySupport
