-- BossJy-Pro 摄取流水线表结构
-- 支持实用型的文件上传和处理

-- 确保 pgvector 扩展已安装
CREATE EXTENSION IF NOT EXISTS vector;

-- ===================== 摄取流水线表 =====================

-- 上传文件记录表
CREATE TABLE IF NOT EXISTS huaqiao.uploads (
    id SERIAL PRIMARY KEY,
    upload_id VARCHAR(50) UNIQUE NOT NULL,
    tenant VARCHAR(50) DEFAULT 'default',
    filename VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100),
    size_bytes INTEGER DEFAULT 0,
    rows_detected INTEGER DEFAULT 0,
    notes JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 清洗数据表（简化版本，适配摄取流水线）
CREATE TABLE IF NOT EXISTS huaqiao.cleaned_data (
    id BIGSERIAL PRIMARY KEY,
    upload_id VARCHAR(50) NOT NULL,
    tenant VARCHAR(50) DEFAULT 'default',

    -- 核心字段
    full_name VARCHAR(255),
    phone_raw VARCHAR(50),
    phone_e164 VARCHAR(50),
    email VARCHAR(255),
    country VARCHAR(100),
    city VARCHAR(100),

    -- 华人识别
    is_chinese BOOLEAN DEFAULT FALSE,

    -- 元数据
    meta JSONB DEFAULT '{}',

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 向量数据表
CREATE TABLE IF NOT EXISTS huaqiao.embeddings (
    id BIGSERIAL PRIMARY KEY,
    record_id BIGINT NOT NULL REFERENCES huaqiao.cleaned_data(id) ON DELETE CASCADE,
    upload_id VARCHAR(50) NOT NULL,
    tenant VARCHAR(50) DEFAULT 'default',

    -- 向量数据（384维）
    embedding vector(384) NOT NULL,

    -- 元数据
    meta JSONB DEFAULT '{}',

    -- 时间戳
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AI结果表（简化版）
CREATE TABLE IF NOT EXISTS huaqiao.ai_results (
    id BIGSERIAL PRIMARY KEY,
    task_id VARCHAR(50) NOT NULL,
    tenant VARCHAR(50) DEFAULT 'default',
    model_used VARCHAR(50),
    summary TEXT,
    diagnostics JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===================== 索引创建 =====================

-- uploads 表索引
CREATE INDEX IF NOT EXISTS idx_uploads_upload_id ON huaqiao.uploads(upload_id);
CREATE INDEX IF NOT EXISTS idx_uploads_tenant ON huaqiao.uploads(tenant);
CREATE INDEX IF NOT EXISTS idx_uploads_created_at ON huaqiao.uploads(created_at);

-- cleaned_data 表索引
CREATE INDEX IF NOT EXISTS idx_cleaned_data_upload_id ON huaqiao.cleaned_data(upload_id);
CREATE INDEX IF NOT EXISTS idx_cleaned_data_tenant ON huaqiao.cleaned_data(tenant);
CREATE INDEX IF NOT EXISTS idx_cleaned_data_full_name ON huaqiao.cleaned_data(full_name);
CREATE INDEX IF NOT EXISTS idx_cleaned_data_phone_e164 ON huaqiao.cleaned_data(phone_e164);
CREATE INDEX IF NOT EXISTS idx_cleaned_data_email ON huaqiao.cleaned_data(email);
CREATE INDEX IF NOT EXISTS idx_cleaned_data_country ON huaqiao.cleaned_data(country);
CREATE INDEX IF NOT EXISTS idx_cleaned_data_is_chinese ON huaqiao.cleaned_data(is_chinese);
CREATE INDEX IF NOT EXISTS idx_cleaned_data_created_at ON huaqiao.cleaned_data(created_at);

-- embeddings 表索引
CREATE INDEX IF NOT EXISTS idx_embeddings_record_id ON huaqiao.embeddings(record_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_upload_id ON huaqiao.embeddings(upload_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_tenant ON huaqiao.embeddings(tenant);
CREATE INDEX IF NOT EXISTS idx_embeddings_created_at ON huaqiao.embeddings(created_at);

-- pgvector 索引（用于相似性搜索）
CREATE INDEX IF NOT EXISTS idx_embeddings_vector_cosine ON huaqiao.embeddings
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- ai_results 表索引
CREATE INDEX IF NOT EXISTS idx_ai_results_task_id ON huaqiao.ai_results(task_id);
CREATE INDEX IF NOT EXISTS idx_ai_results_tenant ON huaqiao.ai_results(tenant);
CREATE INDEX IF NOT EXISTS idx_ai_results_created_at ON huaqiao.ai_results(created_at);

-- ===================== 触发器 =====================

-- 自动更新 updated_at 字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为 cleaned_data 添加更新触发器
CREATE TRIGGER update_cleaned_data_updated_at
    BEFORE UPDATE ON huaqiao.cleaned_data
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ===================== 示例查询视图 =====================

-- 华人数据统计视图
CREATE OR REPLACE VIEW huaqiao.chinese_stats_by_upload AS
SELECT
    upload_id,
    tenant,
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE is_chinese = true) as chinese_count,
    ROUND(
        COUNT(*) FILTER (WHERE is_chinese = true) * 100.0 / COUNT(*),
        2
    ) as chinese_percentage,
    COUNT(DISTINCT country) as countries_count,
    array_agg(DISTINCT country) FILTER (WHERE country IS NOT NULL) as countries
FROM huaqiao.cleaned_data
GROUP BY upload_id, tenant;

-- 向量化完成度视图
CREATE OR REPLACE VIEW huaqiao.embedding_progress AS
SELECT
    cd.upload_id,
    cd.tenant,
    COUNT(cd.id) as total_records,
    COUNT(e.id) as embedded_records,
    ROUND(
        COUNT(e.id) * 100.0 / COUNT(cd.id),
        2
    ) as embedding_percentage
FROM huaqiao.cleaned_data cd
LEFT JOIN huaqiao.embeddings e ON cd.id = e.record_id
GROUP BY cd.upload_id, cd.tenant;

-- 完成消息
SELECT 'BossJy-Pro 摄取流水线表创建完成！' as status;

-- 验证表创建
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name AND table_schema = 'huaqiao') as column_count
FROM information_schema.tables t
WHERE table_schema = 'huaqiao'
    AND table_name IN ('uploads', 'cleaned_data', 'embeddings', 'ai_results')
ORDER BY table_name;