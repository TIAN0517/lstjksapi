-- BossJy-Pro 增強數據清洗字段
-- 添加電話、姓名、地址、語言檢測相關字段
-- 執行: psql -U postgres -d bossjy_db -f migrations/add_enhanced_cleaning_fields.sql

-- ==================== 擴展現有表（假設有 records 表） ====================
-- 根據實際表結構調整表名

-- 示例：如果有 processed_records 或 data_records 表
-- ALTER TABLE processed_records ADD COLUMN IF NOT EXISTS ...

-- 創建通用數據記錄增強表（如果不存在）
CREATE TABLE IF NOT EXISTS enhanced_records (
    id BIGSERIAL PRIMARY KEY,

    -- 原始數據
    original_name TEXT,
    original_phone TEXT,
    original_email TEXT,
    original_address TEXT,

    -- 電話驗證結果
    phone_e164 TEXT,                    -- E.164 標準格式
    phone_region TEXT,                  -- 國家/地區代碼
    phone_carrier TEXT,                 -- 運營商
    phone_line_type TEXT,               -- 線路類型 (mobile/fixed_line/voip)
    phone_reachable BOOLEAN,            -- 在網狀態（Twilio HLR）
    phone_validation_score NUMERIC(3,2), -- 驗證分數 0-1

    -- 華人識別結果
    name_zh_prob NUMERIC(3,2),          -- 華人機率 0-1
    name_signals JSONB,                 -- 各訊號詳情
    name_surname TEXT,                  -- 提取的姓氏
    name_normalized TEXT,               -- 標準化姓名

    -- 地址標準化
    addr_libpostal JSONB,               -- libpostal 解析結果
    addr_cn JSONB,                      -- 中國省市區 {省, 市, 區, adcode}
    addr_normalized TEXT,               -- 標準化地址
    addr_quality_score NUMERIC(3,2),    -- 地址質量分數

    -- 語言檢測
    lang_code TEXT,                     -- 語言代碼 (zh/en/yue...)
    lang_score NUMERIC(3,2),            -- 置信度
    lang_top_k JSONB,                   -- Top-K 語言預測

    -- 去重關聯
    entity_cluster_id TEXT,             -- 集群 ID
    entity_match_score NUMERIC(3,2),    -- 匹配分數
    entity_duplicate_of INT,            -- 重複記錄索引

    -- 元數據
    upload_id TEXT,                     -- 關聯上傳 ID
    processed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_enhanced_records_upload_id ON enhanced_records(upload_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_records_phone_e164 ON enhanced_records(phone_e164);
CREATE INDEX IF NOT EXISTS idx_enhanced_records_cluster_id ON enhanced_records(entity_cluster_id);
CREATE INDEX IF NOT EXISTS idx_enhanced_records_zh_prob ON enhanced_records(name_zh_prob);

-- ==================== 或者：擴展現有表（推薦方式） ====================
-- 如果已有主記錄表（如 uploads 或 records），添加這些字段

-- 假設表名為 records：
-- ALTER TABLE records ADD COLUMN IF NOT EXISTS phone_e164 TEXT;
-- ALTER TABLE records ADD COLUMN IF NOT EXISTS phone_region TEXT;
-- ALTER TABLE records ADD COLUMN IF NOT EXISTS phone_carrier TEXT;
-- ALTER TABLE records ADD COLUMN IF NOT EXISTS phone_line_type TEXT;
-- ALTER TABLE records ADD COLUMN IF NOT EXISTS phone_reachable BOOLEAN;
-- ALTER TABLE records ADD COLUMN IF NOT EXISTS phone_validation_score NUMERIC(3,2);

-- ALTER TABLE records ADD COLUMN IF NOT EXISTS name_zh_prob NUMERIC(3,2);
-- ALTER TABLE records ADD COLUMN IF NOT EXISTS name_signals JSONB;
-- ALTER TABLE records ADD COLUMN IF NOT EXISTS name_surname TEXT;
-- ALTER TABLE records ADD COLUMN IF NOT EXISTS name_normalized TEXT;

-- ALTER TABLE records ADD COLUMN IF NOT EXISTS addr_libpostal JSONB;
-- ALTER TABLE records ADD COLUMN IF NOT EXISTS addr_cn JSONB;
-- ALTER TABLE records ADD COLUMN IF NOT EXISTS addr_normalized TEXT;
-- ALTER TABLE records ADD COLUMN IF NOT EXISTS addr_quality_score NUMERIC(3,2);

-- ALTER TABLE records ADD COLUMN IF NOT EXISTS lang_code TEXT;
-- ALTER TABLE records ADD COLUMN IF NOT EXISTS lang_score NUMERIC(3,2);
-- ALTER TABLE records ADD COLUMN IF NOT EXISTS lang_top_k JSONB;

-- ALTER TABLE records ADD COLUMN IF NOT EXISTS entity_cluster_id TEXT;
-- ALTER TABLE records ADD COLUMN IF NOT EXISTS entity_match_score NUMERIC(3,2);
-- ALTER TABLE records ADD COLUMN IF NOT EXISTS entity_duplicate_of INT;

-- ==================== 質量報告表 ====================
CREATE TABLE IF NOT EXISTS data_quality_reports (
    id BIGSERIAL PRIMARY KEY,

    upload_id TEXT NOT NULL,
    dataset_name TEXT,

    -- 驗證結果
    success BOOLEAN,
    total_expectations INT,
    successful_expectations INT,
    failed_expectations INT,
    success_rate NUMERIC(5,2),

    -- 報告
    report_path TEXT,
    report_data JSONB,

    -- 元數據
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_quality_reports_upload_id ON data_quality_reports(upload_id);

-- ==================== 去重集群表 ====================
CREATE TABLE IF NOT EXISTS dedup_clusters (
    cluster_id TEXT PRIMARY KEY,

    -- 集群信息
    record_count INT DEFAULT 1,
    primary_record_id BIGINT,

    -- 匹配信息
    match_threshold NUMERIC(3,2),
    avg_match_score NUMERIC(3,2),

    -- 元數據
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ==================== 更新時間戳觸發器 ====================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_enhanced_records_updated_at ON enhanced_records;
CREATE TRIGGER update_enhanced_records_updated_at
    BEFORE UPDATE ON enhanced_records
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ==================== 權限（調整為實際用戶） ====================
-- GRANT ALL PRIVILEGES ON enhanced_records TO bossjy_user;
-- GRANT ALL PRIVILEGES ON data_quality_reports TO bossjy_user;
-- GRANT ALL PRIVILEGES ON dedup_clusters TO bossjy_user;

-- ==================== 完成 ====================
\echo '✅ Enhanced cleaning fields migration completed'
