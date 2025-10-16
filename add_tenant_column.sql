-- 添加tenant列到users表
ALTER TABLE users ADD COLUMN tenant VARCHAR(50) DEFAULT 'default' NOT NULL;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_users_tenant ON users(tenant);

-- 更新现有用户的tenant值
UPDATE users SET tenant = 'default' WHERE tenant IS NULL;