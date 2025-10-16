-- 创建phone_validations表
-- 用于存储电话号码验证记录

-- 创建表
CREATE TABLE IF NOT EXISTS phone_validations (
    id SERIAL PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    country_code VARCHAR(5) NOT NULL,
    is_valid BOOLEAN NOT NULL DEFAULT FALSE,
    validation_type VARCHAR(50) NOT NULL DEFAULT 'format',
    validation_result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER REFERENCES users(id),
    tenant VARCHAR(50) DEFAULT 'default',
    metadata JSONB
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_phone_validations_phone_number ON phone_validations(phone_number);
CREATE INDEX IF NOT EXISTS idx_phone_validations_country_code ON phone_validations(country_code);
CREATE INDEX IF NOT EXISTS idx_phone_validations_is_valid ON phone_validations(is_valid);
CREATE INDEX IF NOT EXISTS idx_phone_validations_user_id ON phone_validations(user_id);
CREATE INDEX IF NOT EXISTS idx_phone_validations_tenant ON phone_validations(tenant);
CREATE INDEX IF NOT EXISTS idx_phone_validations_created_at ON phone_validations(created_at);

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_phone_validations_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 创建触发器
DROP TRIGGER IF EXISTS phone_validations_updated_at_trigger ON phone_validations;
CREATE TRIGGER phone_validations_updated_at_trigger
    BEFORE UPDATE ON phone_validations
    FOR EACH ROW
    EXECUTE FUNCTION update_phone_validations_updated_at();

-- 添加注释
COMMENT ON TABLE phone_validations IS '电话号码验证记录表';
COMMENT ON COLUMN phone_validations.phone_number IS '电话号码';
COMMENT ON COLUMN phone_validations.country_code IS '国家代码';
COMMENT ON COLUMN phone_validations.is_valid IS '是否有效';
COMMENT ON COLUMN phone_validations.validation_type IS '验证类型: format, carrier, existence';
COMMENT ON COLUMN phone_validations.validation_result IS '验证结果详情';
COMMENT ON COLUMN phone_validations.user_id IS '关联用户ID';
COMMENT ON COLUMN phone_validations.tenant IS '租户标识';
COMMENT ON COLUMN phone_validations.metadata IS '额外元数据';

-- 验证表创建成功
SELECT 
    'phone_validations表创建成功' AS status,
    NOW() AS created_at;