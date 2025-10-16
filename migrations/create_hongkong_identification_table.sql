-- 创建香港人识别记录表
-- Migration: create_hongkong_identification_table
-- Date: 2025-10-03

CREATE TABLE IF NOT EXISTS hongkong_identification_logs (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) NOT NULL,
    job_id VARCHAR(40),

    -- 原始数据
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    email VARCHAR(255),

    -- 识别结果
    confidence VARCHAR(20),  -- HIGH, MEDIUM, LOW, UNKNOWN
    total_score NUMERIC(5, 3),
    phone_score NUMERIC(5, 3),
    name_score NUMERIC(5, 3),
    email_score NUMERIC(5, 3),
    reasons TEXT,

    -- 时间戳
    created_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_hk_tenant_conf ON hongkong_identification_logs(tenant_id, confidence);
CREATE INDEX IF NOT EXISTS idx_hk_job ON hongkong_identification_logs(job_id);
CREATE INDEX IF NOT EXISTS idx_hk_score ON hongkong_identification_logs(total_score);
CREATE INDEX IF NOT EXISTS idx_hk_created ON hongkong_identification_logs(created_at);

-- 添加注释
COMMENT ON TABLE hongkong_identification_logs IS '香港人智能识别记录表';
COMMENT ON COLUMN hongkong_identification_logs.confidence IS '识别置信度: HIGH(高)/MEDIUM(中)/LOW(低)/UNKNOWN(未知)';
COMMENT ON COLUMN hongkong_identification_logs.total_score IS '综合评分 (0-1.0)';
COMMENT ON COLUMN hongkong_identification_logs.reasons IS '识别依据说明';
