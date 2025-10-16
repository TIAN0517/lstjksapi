-- 数据市场表：存储可售卖的数据
CREATE TABLE IF NOT EXISTS data_marketplace (
    id SERIAL PRIMARY KEY,
    data_type VARCHAR(50) NOT NULL,  -- hongkong, australia, chinese_global
    source VARCHAR(100),              -- 数据来源
    name VARCHAR(255),               -- 姓名
    company VARCHAR(255),            -- 公司
    phone VARCHAR(50),               -- 电话
    email VARCHAR(255),              -- 邮箱
    address TEXT,                    -- 地址
    city VARCHAR(100),               -- 城市
    country VARCHAR(100),            -- 国家
    raw_data JSONB,                  -- 原始数据JSON
    is_sample BOOLEAN DEFAULT FALSE, -- 是否样本数据
    price DECIMAL(10,2),             -- 单条价格
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 数据分类索引
CREATE INDEX IF NOT EXISTS idx_marketplace_type ON data_marketplace(data_type);
CREATE INDEX IF NOT EXISTS idx_marketplace_sample ON data_marketplace(is_sample);
CREATE INDEX IF NOT EXISTS idx_marketplace_country ON data_marketplace(country);

-- 数据统计视图
CREATE OR REPLACE VIEW data_marketplace_stats AS
SELECT
    data_type,
    COUNT(*) as total_records,
    COUNT(CASE WHEN is_sample = TRUE THEN 1 END) as sample_records,
    MIN(price) as min_price,
    MAX(price) as max_price,
    AVG(price) as avg_price
FROM data_marketplace
GROUP BY data_type;

-- 用户购买记录表
CREATE TABLE IF NOT EXISTS data_purchases (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    telegram_user_id BIGINT,
    data_type VARCHAR(50) NOT NULL,
    quantity INTEGER DEFAULT 0,
    total_price DECIMAL(10,2),
    status VARCHAR(20) DEFAULT 'pending', -- pending, approved, completed, cancelled
    contact_info TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_purchases_user ON data_purchases(telegram_user_id);
CREATE INDEX IF NOT EXISTS idx_purchases_status ON data_purchases(status);

COMMENT ON TABLE data_marketplace IS '数据市场 - 存储可售卖的数据';
COMMENT ON TABLE data_purchases IS '购买记录 - 用户购买数据的记录';
