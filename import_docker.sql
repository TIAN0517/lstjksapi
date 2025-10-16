-- PostgreSQL数据库初始化脚本
-- 创建基础表结构并插入示例数据

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255),
    password_hash VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',
    status VARCHAR(20) DEFAULT 'active',
    credits INTEGER DEFAULT 100,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 数据记录表
CREATE TABLE IF NOT EXISTS data_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    data_type VARCHAR(100),
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 数据市场表
CREATE TABLE IF NOT EXISTS data_marketplace (
    id SERIAL PRIMARY KEY,
    data_type VARCHAR(100) NOT NULL,
    name VARCHAR(255),
    company VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    raw_data JSONB,
    is_sample BOOLEAN DEFAULT FALSE,
    price DECIMAL(10,2) DEFAULT 99.0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 积分表
CREATE TABLE IF NOT EXISTS credits (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    amount INTEGER,
    type VARCHAR(50),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 交易表
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    amount DECIMAL(10,2),
    currency VARCHAR(10) DEFAULT 'USDT',
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入示例用户
INSERT INTO users (username, email, password_hash, role, credits) VALUES
('admin', 'admin@bossjy.com', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iKVjzieMwkOmANgNOgKQNNBDvAGK', 'admin', 10000),
('demo_user', 'demo@example.com', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iKVjzieMwkOmANgNOgKQNNBDvAGK', 'user', 100)
ON CONFLICT (username) DO NOTHING;

-- 插入示例数据市场数据
INSERT INTO data_marketplace 
(data_type, name, company, phone, email, address, city, country, raw_data, is_sample, price) VALUES
('hongkong', 'Zhang San', 'Hong Kong Trading Co', '+85212345678', 'zhangsan@example.com', 'Central Hong Kong', 'Hong Kong', 'China Hong Kong', '{"age": 35, "industry": "Trading"}', True, 99.0),
('australia', 'John Smith', 'Aussie Trading', '+61412345678', 'john@aussie.com', 'Sydney CBD', 'Sydney', 'Australia', '{"age": 42, "industry": "Import Export"}', True, 99.0),
('indonesia', 'Budi Santoso', 'PT Jakarta Import', '+628123456789', 'budi@jakarta.co.id', 'Jakarta Pusat', 'Jakarta', 'Indonesia', '{"age": 38, "industry": "Import Trading"}', True, 99.0),
('chinese_global', 'Li Si', 'Global Chinese Group', '+14155552671', 'lisi@global.com', 'San Francisco', 'San Francisco', 'USA', '{"age": 45, "industry": "Technology"}', True, 99.0)
ON CONFLICT DO NOTHING;

-- 显示统计信息
SELECT 'users' as table_name, COUNT(*) as record_count FROM users
UNION ALL
SELECT 'data_records', COUNT(*) FROM data_records
UNION ALL
SELECT 'data_marketplace', COUNT(*) FROM data_marketplace
UNION ALL
SELECT 'credits', COUNT(*) FROM credits
UNION ALL
SELECT 'transactions', COUNT(*) FROM transactions;

-- 按数据类型统计
SELECT 'Data marketplace by type' as info, data_type, COUNT(*) as count 
FROM data_marketplace 
GROUP BY data_type;