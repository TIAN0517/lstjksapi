# BossJy-Pro 增強數據清洗部署清單

本文檔列出部署新增強數據清洗功能所需的所有步驟。

## ✅ 預部署檢查

### 1. 系統要求

- [ ] Docker 20.10+ 或 Python 3.11+
- [ ] PostgreSQL 14+
- [ ] Redis 6+
- [ ] 至少 4GB RAM（推薦 8GB）
- [ ] 10GB 可用磁碟空間（用於 libpostal 模型和 fastText）

### 2. 代碼審查

- [ ] 檢查所有新增文件已提交：
  - `app/services/phone_validator.py`
  - `app/services/ethnicity_scoring.py`
  - `app/services/address_normalizer.py`
  - `app/services/lang_detect.py`
  - `app/services/linkage.py`
  - `app/services/quality.py`
  - `app/api/enhanced_cleaning_api.py`
  - `migrations/add_enhanced_cleaning_fields.sql`

- [ ] 檢查依賴更新：
  - `requirements.txt` 包含所有新依賴
  - `Dockerfile` 包含 libpostal 編譯步驟

---

## 📦 部署步驟

### 步驟 1：準備模型文件

```bash
# 創建模型目錄
mkdir -p models

# 下載 fastText LID 模型（~130 MB）
cd models
wget https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz

# 驗證下載
ls -lh lid.176.ftz
# 預期輸出: -rw-r--r-- 1 user user 128M lid.176.ftz
```

### 步驟 2：配置環境變量

```bash
# 複製環境變量模板
cp .env.example.enhanced .env

# 編輯 .env，至少配置以下項目：
# - FASTTEXT_LID_MODEL=/app/models/lid.176.ftz
# - GX_REPORTS_DIR=/app/data/quality_reports

# （可選）如需電話在網檢測，配置 Twilio：
# - TWILIO_ACCOUNT_SID=ACxxxxxxxxxx
# - TWILIO_AUTH_TOKEN=your_token
```

### 步驟 3：構建 Docker 映像

```bash
# 構建（包含 libpostal 編譯，預計 10-15 分鐘）
docker-compose build

# 檢查映像大小
docker images | grep bossjy
# 預期大小: ~2-3 GB（包含 libpostal 模型）
```

**注意事項：**
- libpostal 首次構建會下載約 1.5GB 的語言模型
- 編譯過程需要 4-8 分鐘（取決於 CPU）
- 如構建失敗，檢查系統依賴（autoconf, libtool 等）

### 步驟 4：數據庫遷移

```bash
# 方式 A：Docker Compose 環境
docker-compose exec db psql -U postgres -d bossjy_db -f /migrations/add_enhanced_cleaning_fields.sql

# 方式 B：本地 PostgreSQL
psql -U postgres -d bossjy_db -f migrations/add_enhanced_cleaning_fields.sql

# 驗證表已創建
psql -U postgres -d bossjy_db -c "\dt enhanced_records data_quality_reports dedup_clusters"
```

**預期輸出：**
```
✅ Enhanced cleaning fields migration completed
```

### 步驟 5：啟動服務

```bash
# 啟動所有服務
docker-compose up -d

# 檢查日誌
docker-compose logs -f app

# 預期日誌：
# ✓ Great Expectations 已加載
# ✓ Splink 已加載
# ✓ libpostal 已加載
# ✓ fastText LID 模型已加載
```

### 步驟 6：健康檢查

```bash
# 檢查服務健康
curl http://localhost:8000/api/v1/enhanced/health

# 預期響應：
# {
#   "status": "ok",
#   "services": {
#     "phone_validator": "available",
#     "ethnicity_scorer": "available",
#     "address_normalizer": "available",
#     "language_detector": "available",
#     "entity_linker": "available",
#     "quality_validator": "available"
#   }
# }
```

### 步驟 7：運行示例測試

```bash
# 方式 A：Docker 內運行
docker-compose exec app python examples/enhanced_cleaning_demo.py

# 方式 B：本地運行
python examples/enhanced_cleaning_demo.py

# 預期輸出：
# ==================== 示例 1：電話驗證 ====================
# ✓ 所有示例運行完成！
```

---

## 🧪 功能驗證

### 驗證 1：電話驗證 API

```bash
curl -X POST http://localhost:8000/api/v1/enhanced/phone/validate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "numbers": ["+852 9123 4567", "+86 138 1234 5678"],
    "default_region": "HK"
  }'
```

**預期：** 返回包含 `e164`、`region_code`、`is_valid` 的 JSON

### 驗證 2：華人識別 API

```bash
curl -X POST http://localhost:8000/api/v1/enhanced/ethnicity/score \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "names": [
      {"name": "李明", "phone": "+852 9123 4567", "address": "Hong Kong"}
    ]
  }'
```

**預期：** 返回 `prob_chinese` ≥ 0.8

### 驗證 3：地址標準化 API

```bash
curl -X POST http://localhost:8000/api/v1/enhanced/address/normalize \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "addresses": ["北京市朝陽區建國門外大街1號"]
  }'
```

**預期：** 返回 `cn_adm` 包含省市區

### 驗證 4：語言檢測 API

```bash
curl -X POST http://localhost:8000/api/v1/enhanced/language/detect \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["這是中文", "This is English"]
  }'
```

**預期：** 返回 `lang` = "zh" 和 "en"

---

## 🔧 故障排除

### 問題 1：libpostal 加載失敗

**錯誤：** `ImportError: libpostal.so.1: cannot open shared object file`

**解決：**
```bash
# Docker 內執行
docker-compose exec app ldconfig
docker-compose restart app

# 或重建映像
docker-compose build --no-cache
```

### 問題 2：fastText 模型未找到

**錯誤：** `FileNotFoundError: /app/models/lid.176.ftz`

**解決：**
```bash
# 檢查模型文件
docker-compose exec app ls -lh /app/models/

# 如不存在，重新下載
docker-compose exec app bash -c "
  cd /app/models
  wget https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz
"

# 重啟服務
docker-compose restart app
```

### 問題 3：Twilio Lookup 錯誤

**錯誤：** `TwilioRestException: Unable to create record`

**檢查：**
1. TWILIO_ACCOUNT_SID 和 TWILIO_AUTH_TOKEN 是否正確
2. 賬戶餘額是否充足
3. 是否啟用了 Lookup v2 API

**解決：**
```bash
# 測試 Twilio 憑證
curl -X GET "https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID.json" \
  -u "$TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN"
```

### 問題 4：Great Expectations 初始化失敗

**錯誤：** `PermissionError: /app/data/quality_reports`

**解決：**
```bash
# 創建目錄並設置權限
docker-compose exec app bash -c "
  mkdir -p /app/data/quality_reports
  chmod 777 /app/data/quality_reports
"
```

---

## 📊 性能優化

### 1. libpostal 模型預加載

在 `docker-compose.yml` 中設置：

```yaml
services:
  app:
    environment:
      - LIBPOSTAL_PRELOAD=true
```

### 2. Splink 阻塞規則優化

對於大數據集（>10 萬記錄），優化阻塞規則：

```python
# app/services/linkage.py
blocking_rules = [
    "l.name[0:3] = r.name[0:3]",  # 姓名前 3 字符
    "l.phone[-4:] = r.phone[-4:]",  # 電話末 4 位
]
```

### 3. fastText 批量預測

使用批量檢測提升性能：

```python
# 避免單條循環
for text in texts:
    result = detector.detect_lang(text)  # ❌ 慢

# 使用批量
results = detector.batch_detect(texts)  # ✅ 快
```

---

## 🔐 安全檢查

- [ ] `.env` 文件未提交到 Git（已加入 `.gitignore`）
- [ ] Twilio 憑證使用環境變量，不硬編碼
- [ ] API 端點需要 Bearer Token 認證
- [ ] 數據庫遷移腳本已審查（無 DROP 操作）
- [ ] 文件上傳限制已配置（防止超大模型文件）

---

## 📈 監控指標

部署後監控以下指標：

1. **性能指標：**
   - 電話驗證平均耗時：< 50ms
   - 華人識別平均耗時：< 100ms
   - 地址標準化平均耗時：< 150ms（libpostal）
   - 語言檢測平均耗時：< 30ms
   - 去重（100 記錄）：< 5s
   - 去重（10,000 記錄）：< 2min（Splink）

2. **準確率指標：**
   - 電話格式驗證：> 99%
   - 華人識別（高置信）：> 92%
   - 地址解析（英文）：> 90%
   - 語言檢測（>20 字符）：> 95%
   - 去重 F1-score：> 0.90

3. **資源使用：**
   - 內存：< 2GB（空閒）、< 4GB（高負載）
   - CPU：< 30%（空閒）、< 80%（批量處理）
   - 磁碟：libpostal 模型 ~1.5GB、fastText ~130MB

---

## ✅ 部署完成檢查

- [ ] 所有依賴已安裝
- [ ] Docker 映像構建成功
- [ ] 數據庫遷移執行成功
- [ ] 服務啟動無錯誤日誌
- [ ] 健康檢查 API 返回 200
- [ ] 示例腳本運行成功
- [ ] 所有 6 個 API 端點測試通過
- [ ] 性能指標符合預期
- [ ] 監控告警已配置
- [ ] 文檔已更新（API 文檔、README）

---

## 📝 回滾計劃

如遇嚴重問題需回滾：

```bash
# 1. 停止服務
docker-compose down

# 2. 回滾數據庫（如已執行遷移）
psql -U postgres -d bossjy_db -c "
  DROP TABLE IF EXISTS enhanced_records CASCADE;
  DROP TABLE IF EXISTS data_quality_reports CASCADE;
  DROP TABLE IF EXISTS dedup_clusters CASCADE;
"

# 3. 切換到舊版代碼
git checkout <previous-commit>

# 4. 重新構建並啟動
docker-compose build
docker-compose up -d
```

---

## 📞 支持聯繫

如遇部署問題：

- 技術支持: support@bossjy.com
- Telegram: @BossJySupport
- GitHub Issues: https://github.com/bossjy/bossjy-pro/issues

---

**部署日期：** _________

**部署人員：** _________

**版本號：** v2.0.0-enhanced-cleaning

**簽名確認：** _________
