-- BossJy-Pro 一庫化資料庫初始化 (修正版)

-- 啟用 pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- 建立必要 Schema
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_namespace WHERE nspname = 'huaqiao') THEN
        CREATE SCHEMA huaqiao;
    END IF;
END$$;

SET search_path TO huaqiao;

---------------------------------------------------------
-- 1. 清洗後數據表
---------------------------------------------------------
CREATE TABLE IF NOT EXISTS cleaned_data (
    id SERIAL PRIMARY KEY,
    tenant VARCHAR(100) NOT NULL,
    upload_id VARCHAR(64),
    job_id VARCHAR(64),
    source_file VARCHAR(255),
    name VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    birth_date DATE,
    gender VARCHAR(10),
    id_number VARCHAR(100),
    bank_account VARCHAR(100),
    occupation VARCHAR(100),
    company VARCHAR(255),
    country VARCHAR(100),
    city VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    is_chinese BOOLEAN DEFAULT false,
    chinese_score NUMERIC(5,2) DEFAULT 0.0,
    quality_score NUMERIC(5,2) DEFAULT 0.0,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

---------------------------------------------------------
-- 2. Embeddings 表 (向量化數據)
---------------------------------------------------------
CREATE TABLE IF NOT EXISTS embeddings (
    id SERIAL PRIMARY KEY,
    record_id INT REFERENCES cleaned_data(id) ON DELETE CASCADE,
    tenant VARCHAR(100) NOT NULL,
    source_field VARCHAR(50),
    vector vector(384), -- pgvector
    created_at TIMESTAMP DEFAULT now()
);

---------------------------------------------------------
-- 3. 資料來源設定表
---------------------------------------------------------
CREATE TABLE IF NOT EXISTS data_source_configs (
    id SERIAL PRIMARY KEY,
    tenant VARCHAR(100) NOT NULL,
    source_type VARCHAR(50),
    connection_info JSONB,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

---------------------------------------------------------
-- 4. 任務紀錄表
---------------------------------------------------------
CREATE TABLE IF NOT EXISTS dispatch_tasks (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(64) UNIQUE NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    user_id INT,
    username VARCHAR(100),
    tenant VARCHAR(100),
    filename VARCHAR(255),
    file_size BIGINT,
    strategy VARCHAR(50),
    country VARCHAR(50),
    source VARCHAR(50),
    steps_completed JSONB DEFAULT '[]',
    error_messages JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

---------------------------------------------------------
-- 5. AI 推理結果表
---------------------------------------------------------
CREATE TABLE IF NOT EXISTS ai_results (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(64) REFERENCES dispatch_tasks(task_id) ON DELETE CASCADE,
    model_used VARCHAR(50) NOT NULL,
    ai_summary TEXT,
    raw_response JSONB,
    quality_score NUMERIC(5,2),
    created_at TIMESTAMP DEFAULT now()
);

---------------------------------------------------------
-- 6. 處理效能表
---------------------------------------------------------
CREATE TABLE IF NOT EXISTS processing_metrics (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(64) NOT NULL,
    task_type VARCHAR(50) NOT NULL,
    processing_time DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT now()
);

---------------------------------------------------------
-- 7. 索引
---------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_cleaned_data_tenant ON cleaned_data(tenant);
CREATE INDEX IF NOT EXISTS idx_cleaned_data_source_file ON cleaned_data(source_file);
CREATE INDEX IF NOT EXISTS idx_cleaned_data_upload_id ON cleaned_data(upload_id);
CREATE INDEX IF NOT EXISTS idx_cleaned_data_job_id ON cleaned_data(job_id);
CREATE INDEX IF NOT EXISTS idx_cleaned_data_is_chinese ON cleaned_data(is_chinese);
CREATE INDEX IF NOT EXISTS idx_cleaned_data_status ON cleaned_data(status);
CREATE INDEX IF NOT EXISTS idx_cleaned_data_name ON cleaned_data(name);
CREATE INDEX IF NOT EXISTS idx_cleaned_data_phone ON cleaned_data(phone);
CREATE INDEX IF NOT EXISTS idx_cleaned_data_created_at ON cleaned_data(created_at);

CREATE INDEX IF NOT EXISTS idx_embeddings_record_id ON embeddings(record_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_tenant ON embeddings(tenant);
CREATE INDEX IF NOT EXISTS idx_embeddings_source_field ON embeddings(source_field);
CREATE INDEX IF NOT EXISTS idx_embeddings_created_at ON embeddings(created_at);
CREATE INDEX IF NOT EXISTS idx_embeddings_vector ON embeddings USING ivfflat (vector vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_processing_metrics_task_id ON processing_metrics(task_id);
CREATE INDEX IF NOT EXISTS idx_processing_metrics_operation_type ON processing_metrics(task_type);
CREATE INDEX IF NOT EXISTS idx_processing_metrics_created_at ON processing_metrics(created_at);

---------------------------------------------------------
-- 8. Trigger 更新 updated_at
---------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
   NEW.updated_at = now();
   RETURN NEW;
END;
$$ language 'plpgsql';

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'update_cleaned_data_updated_at'
    ) THEN
        CREATE TRIGGER update_cleaned_data_updated_at
        BEFORE UPDATE ON cleaned_data
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger WHERE tgname = 'update_data_source_configs_updated_at'
    ) THEN
        CREATE TRIGGER update_data_source_configs_updated_at
        BEFORE UPDATE ON data_source_configs
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    END IF;
END$$;

---------------------------------------------------------
-- 完成訊息
---------------------------------------------------------
INSERT INTO data_source_configs (tenant, source_type, connection_info)
VALUES ('system', 'init', '{}')
ON CONFLICT DO NOTHING;

SELECT '✅ BossJy-Pro 一庫化資料庫表初始化完成！' as status;

\dt huaqiao.*

