-- 添加Telegram绑定字段到租户表
-- Migration: add_telegram_binding_to_tenants
-- Date: 2025-10-03

-- 添加Telegram相关字段
ALTER TABLE tenants
ADD COLUMN IF NOT EXISTS telegram_id VARCHAR(50) UNIQUE,
ADD COLUMN IF NOT EXISTS telegram_username VARCHAR(255),
ADD COLUMN IF NOT EXISTS telegram_bound_at TIMESTAMP;

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_tenants_telegram_id ON tenants(telegram_id);

-- 添加注释
COMMENT ON COLUMN tenants.telegram_id IS 'Telegram用户ID，唯一绑定';
COMMENT ON COLUMN tenants.telegram_username IS 'Telegram用户名或昵称';
COMMENT ON COLUMN tenants.telegram_bound_at IS 'Telegram绑定时间';
