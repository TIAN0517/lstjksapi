-- 创建群组相关表
-- 注意：请在PostgreSQL中执行此SQL文件

-- 创建telegram_groups表
CREATE TABLE IF NOT EXISTS telegram_groups (
    id SERIAL PRIMARY KEY,
    group_id VARCHAR(50) UNIQUE NOT NULL,
    group_title VARCHAR(255),
    group_type VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建group_members表
CREATE TABLE IF NOT EXISTS group_members (
    id SERIAL PRIMARY KEY,
    group_id VARCHAR(50) NOT NULL,
    telegram_id VARCHAR(50) NOT NULL,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id, telegram_id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_telegram_groups_group_id ON telegram_groups(group_id);
CREATE INDEX IF NOT EXISTS idx_group_members_group_id ON group_members(group_id);
CREATE INDEX IF NOT EXISTS idx_group_members_telegram_id ON group_members(telegram_id);

-- 创建更新时间触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_telegram_groups_updated_at 
    BEFORE UPDATE ON telegram_groups 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();