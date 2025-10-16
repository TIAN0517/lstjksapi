-- 🔒 增强积分系统数据库迁移脚本
-- 添加防重复、审计、并发控制字段

-- 1. CreditsAccount 表（如不存在则创建）
CREATE TABLE IF NOT EXISTS credits_accounts (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE,
    tenant_id VARCHAR(50),
    balance BIGINT NOT NULL DEFAULT 0,  -- 当前余额
    total_earned BIGINT NOT NULL DEFAULT 0,  -- 累计充值
    total_spent BIGINT NOT NULL DEFAULT 0,  -- 累计消费
    frozen_balance BIGINT NOT NULL DEFAULT 0,  -- 冻结余额
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 余额必须非负约束
ALTER TABLE credits_accounts ADD CONSTRAINT check_balance_non_negative
CHECK (balance >= 0);

-- 2. CreditsTransaction 表（如不存在则创建）
CREATE TABLE IF NOT EXISTS credits_transactions (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    account_id BIGINT REFERENCES credits_accounts(id),
    order_id VARCHAR(100),  -- 关联订单号
    request_id VARCHAR(64),  -- 🔒 幂等性键（防重复）
    transaction_type VARCHAR(50) NOT NULL,  -- recharge, filtering, translation等
    amount BIGINT NOT NULL,  -- 正数=充值，负数=扣费
    balance_before BIGINT,  -- 🔒 操作前余额（审计）
    balance_after BIGINT NOT NULL,  -- 🔒 操作后余额（审计）
    description TEXT,
    tx_hash VARCHAR(128),  -- 区块链交易哈希
    metadata JSONB,  -- 🔒 完整元数据
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. RechargeOrder 表（如不存在则创建）
CREATE TABLE IF NOT EXISTS recharge_orders (
    id BIGSERIAL PRIMARY KEY,
    order_id VARCHAR(100) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    usdt_amount NUMERIC(18, 6) NOT NULL,
    credits_amount INTEGER NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    tx_hash VARCHAR(128),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    paid_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. 添加增强字段到 usdt_deposits（如不存在）
ALTER TABLE usdt_deposits ADD COLUMN IF NOT EXISTS credits_added INTEGER DEFAULT 0;
ALTER TABLE usdt_deposits ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP;

-- 5. 创建索引（性能优化）

-- Credits Account 索引
CREATE INDEX IF NOT EXISTS idx_credits_account_user ON credits_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_credits_account_tenant ON credits_accounts(tenant_id);
CREATE INDEX IF NOT EXISTS idx_credits_account_balance ON credits_accounts(balance);

-- Credits Transaction 索引
CREATE INDEX IF NOT EXISTS idx_credits_tx_user ON credits_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_credits_tx_account ON credits_transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_credits_tx_type ON credits_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_credits_tx_created ON credits_transactions(created_at DESC);

-- 🔒 幂等性索引（防重复扣费）
CREATE UNIQUE INDEX IF NOT EXISTS idx_credits_tx_request_unique
ON credits_transactions(user_id, request_id)
WHERE request_id IS NOT NULL;

-- Recharge Order 索引
CREATE INDEX IF NOT EXISTS idx_recharge_order_user ON recharge_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_recharge_order_status ON recharge_orders(status);
CREATE INDEX IF NOT EXISTS idx_recharge_order_created ON recharge_orders(created_at DESC);

-- USDT Deposits 增强索引
CREATE UNIQUE INDEX IF NOT EXISTS idx_usdt_deposit_tx_unique ON usdt_deposits(tx_id);
CREATE INDEX IF NOT EXISTS idx_usdt_deposit_credits_added ON usdt_deposits(credits_added);
CREATE INDEX IF NOT EXISTS idx_usdt_deposit_processed ON usdt_deposits(processed_at);

-- 6. 添加触发器（自动更新 updated_at）

-- Credits Account 自动更新
CREATE OR REPLACE FUNCTION update_credits_account_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_credits_account_timestamp ON credits_accounts;
CREATE TRIGGER trigger_update_credits_account_timestamp
    BEFORE UPDATE ON credits_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_credits_account_updated_at();

-- Recharge Order 自动更新
CREATE OR REPLACE FUNCTION update_recharge_order_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_recharge_order_timestamp ON recharge_orders;
CREATE TRIGGER trigger_update_recharge_order_timestamp
    BEFORE UPDATE ON recharge_orders
    FOR EACH ROW
    EXECUTE FUNCTION update_recharge_order_updated_at();

-- 7. 数据完整性检查

-- 确保扣费记录的 balance_after 正确
CREATE OR REPLACE FUNCTION verify_balance_calculation()
RETURNS TRIGGER AS $$
BEGIN
    -- 如果有 balance_before，验证计算
    IF NEW.balance_before IS NOT NULL THEN
        IF NEW.balance_after != NEW.balance_before + NEW.amount THEN
            RAISE EXCEPTION '余额计算错误: % + % != %',
                NEW.balance_before, NEW.amount, NEW.balance_after;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_verify_balance ON credits_transactions;
CREATE TRIGGER trigger_verify_balance
    BEFORE INSERT ON credits_transactions
    FOR EACH ROW
    EXECUTE FUNCTION verify_balance_calculation();

-- 8. 查询优化：物化视图（积分统计）

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_credits_stats AS
SELECT
    user_id,
    COUNT(*) as total_transactions,
    SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_recharged,
    SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as total_consumed,
    COUNT(CASE WHEN transaction_type = 'recharge' THEN 1 END) as recharge_count,
    COUNT(CASE WHEN transaction_type != 'recharge' THEN 1 END) as consume_count,
    MAX(created_at) as last_transaction_at
FROM credits_transactions
GROUP BY user_id;

-- 创建物化视图索引
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_credits_stats_user
ON mv_credits_stats(user_id);

-- 刷新物化视图的函数
CREATE OR REPLACE FUNCTION refresh_credits_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_credits_stats;
END;
$$ LANGUAGE plpgsql;

-- 9. 审计日志表
CREATE TABLE IF NOT EXISTS credits_audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    operation VARCHAR(50) NOT NULL,
    amount BIGINT,
    balance_before BIGINT,
    balance_after BIGINT,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    request_id VARCHAR(64),
    ip_address INET,
    user_agent TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_user ON credits_audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_operation ON credits_audit_logs(operation);
CREATE INDEX IF NOT EXISTS idx_audit_created ON credits_audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_success ON credits_audit_logs(success);

-- 10. 权限设置（生产环境）
-- GRANT SELECT, INSERT, UPDATE ON credits_accounts TO app_user;
-- GRANT SELECT, INSERT ON credits_transactions TO app_user;
-- GRANT SELECT, INSERT, UPDATE ON recharge_orders TO app_user;

-- 迁移完成提示
DO $$
BEGIN
    RAISE NOTICE '✅ 积分系统增强迁移完成！';
    RAISE NOTICE '🔒 已添加: 幂等性、审计、并发控制';
    RAISE NOTICE '📊 已创建: 统计视图、审计日志';
END $$;
