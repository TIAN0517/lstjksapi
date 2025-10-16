-- ================================================
-- BossJy数据库性能优化脚本
-- 创建时间: 2025-10-10
-- 用途: 添加额外的性能索引和优化配置
-- ================================================

-- 1. 添加复合索引以提升查询性能
-- ================================================

-- 用户相关复合索引
CREATE INDEX IF NOT EXISTS idx_users_active_role ON users(is_active, role) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_users_email_active ON users(email, is_active);

-- 交易记录复合索引
CREATE INDEX IF NOT EXISTS idx_transactions_user_status ON transactions(user_id, status);
CREATE INDEX IF NOT EXISTS idx_transactions_user_created ON transactions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_status_created ON transactions(status, created_at DESC);

-- 任务相关复合索引
CREATE INDEX IF NOT EXISTS idx_jobs_user_status ON jobs(user_id, status);
CREATE INDEX IF NOT EXISTS idx_jobs_user_type_status ON jobs(user_id, job_type, status);
CREATE INDEX IF NOT EXISTS idx_jobs_status_created ON jobs(status, created_at DESC);

-- API密钥复合索引
CREATE INDEX IF NOT EXISTS idx_api_keys_user_active ON api_keys(user_id, is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_api_keys_hash_active ON api_keys(key_hash, is_active) WHERE is_active = true;

-- 审计日志复合索引
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_action ON audit_logs(user_id, action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- 2. 添加GIN索引以支持JSONB查询
-- ================================================
CREATE INDEX IF NOT EXISTS idx_jobs_input_data_gin ON jobs USING GIN (input_data);
CREATE INDEX IF NOT EXISTS idx_jobs_output_data_gin ON jobs USING GIN (output_data);
CREATE INDEX IF NOT EXISTS idx_audit_logs_details_gin ON audit_logs USING GIN (details);

-- 3. 添加部分索引（Partial Index）以节省空间
-- ================================================
CREATE INDEX IF NOT EXISTS idx_transactions_pending ON transactions(created_at DESC)
WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_jobs_running ON jobs(started_at)
WHERE status = 'running';

CREATE INDEX IF NOT EXISTS idx_jobs_failed ON jobs(created_at DESC)
WHERE status = 'failed';

-- 4. 创建物化视图以加速复杂查询
-- ================================================

-- 用户统计物化视图
DROP MATERIALIZED VIEW IF EXISTS mv_user_stats CASCADE;
CREATE MATERIALIZED VIEW mv_user_stats AS
SELECT
    u.id as user_id,
    u.username,
    u.email,
    u.role,
    u.credits,
    u.created_at as registered_at,
    u.last_login,

    -- 任务统计
    COUNT(DISTINCT j.id) as total_jobs,
    COUNT(DISTINCT CASE WHEN j.status = 'completed' THEN j.id END) as completed_jobs,
    COUNT(DISTINCT CASE WHEN j.status = 'failed' THEN j.id END) as failed_jobs,
    COUNT(DISTINCT CASE WHEN j.status = 'pending' THEN j.id END) as pending_jobs,
    SUM(COALESCE(j.credits_used, 0)) as total_credits_used,

    -- 交易统计
    COUNT(DISTINCT t.id) as total_transactions,
    SUM(CASE WHEN t.status = 'completed' THEN t.amount ELSE 0 END) as total_amount_spent,
    MAX(t.created_at) as last_transaction_at,

    -- API密钥统计
    COUNT(DISTINCT ak.id) as total_api_keys,
    COUNT(DISTINCT CASE WHEN ak.is_active THEN ak.id END) as active_api_keys,

    -- 活跃度指标
    CASE
        WHEN u.last_login > CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 'active'
        WHEN u.last_login > CURRENT_TIMESTAMP - INTERVAL '30 days' THEN 'inactive'
        ELSE 'dormant'
    END as activity_status

FROM users u
LEFT JOIN jobs j ON u.id = j.user_id
LEFT JOIN transactions t ON u.id = t.user_id
LEFT JOIN api_keys ak ON u.id = ak.user_id
GROUP BY u.id, u.username, u.email, u.role, u.credits, u.created_at, u.last_login;

-- 为物化视图创建索引
CREATE UNIQUE INDEX idx_mv_user_stats_user_id ON mv_user_stats(user_id);
CREATE INDEX idx_mv_user_stats_activity ON mv_user_stats(activity_status);

-- 5. 创建自动统计信息更新函数
-- ================================================
CREATE OR REPLACE FUNCTION refresh_user_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_user_stats;
END;
$$ LANGUAGE plpgsql;

-- 6. 添加表分区（为大表准备）
-- ================================================

-- 为审计日志表创建分区表结构（按月分区）
-- 注意：这需要在生产环境中谨慎执行，可能需要迁移现有数据

-- 示例：创建未来3个月的分区
CREATE TABLE IF NOT EXISTS audit_logs_2025_10 PARTITION OF audit_logs
FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');

CREATE TABLE IF NOT EXISTS audit_logs_2025_11 PARTITION OF audit_logs
FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');

CREATE TABLE IF NOT EXISTS audit_logs_2025_12 PARTITION OF audit_logs
FOR VALUES FROM ('2025-12-01') TO ('2026-01-01');

-- 7. 数据库维护函数
-- ================================================

-- 清理旧的审计日志（保留90天）
CREATE OR REPLACE FUNCTION cleanup_old_audit_logs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM audit_logs
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '90 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 清理过期的API密钥
CREATE OR REPLACE FUNCTION cleanup_expired_api_keys()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    UPDATE api_keys
    SET is_active = false
    WHERE expires_at < CURRENT_TIMESTAMP
    AND is_active = true;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 8. 性能监控视图
-- ================================================

-- 慢查询监控视图
CREATE OR REPLACE VIEW v_slow_queries AS
SELECT
    query,
    calls,
    total_time,
    mean_time,
    max_time,
    stddev_time
FROM pg_stat_statements
WHERE mean_time > 1000  -- 平均执行时间超过1秒
ORDER BY mean_time DESC
LIMIT 50;

-- 表大小监控视图
CREATE OR REPLACE VIEW v_table_sizes AS
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_indexes_size(schemaname||'.'||tablename)) AS indexes_size,
    pg_total_relation_size(schemaname||'.'||tablename) AS bytes
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY bytes DESC;

-- 索引使用情况监控
CREATE OR REPLACE VIEW v_index_usage AS
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched,
    pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;

-- 9. 数据库配置优化建议
-- ================================================

-- 设置合适的工作内存
ALTER SYSTEM SET work_mem = '16MB';

-- 设置共享缓冲区（建议为系统内存的25%）
-- ALTER SYSTEM SET shared_buffers = '1GB';  -- 根据实际内存调整

-- 设置有效缓存大小
-- ALTER SYSTEM SET effective_cache_size = '3GB';  -- 根据实际内存调整

-- 设置维护工作内存
ALTER SYSTEM SET maintenance_work_mem = '256MB';

-- 启用自动vacuum
ALTER SYSTEM SET autovacuum = on;

-- 设置检查点间隔
ALTER SYSTEM SET checkpoint_timeout = '15min';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;

-- 10. 创建数据库健康检查函数
-- ================================================

CREATE OR REPLACE FUNCTION database_health_check()
RETURNS TABLE(
    check_name TEXT,
    status TEXT,
    value TEXT,
    recommendation TEXT
) AS $$
BEGIN
    -- 检查表膨胀
    RETURN QUERY
    SELECT
        'Table Bloat'::TEXT,
        CASE WHEN COUNT(*) > 0 THEN 'WARNING' ELSE 'OK' END::TEXT,
        COUNT(*)::TEXT,
        'Run VACUUM FULL on bloated tables'::TEXT
    FROM pg_stat_user_tables
    WHERE n_dead_tup > n_live_tup;

    -- 检查未使用的索引
    RETURN QUERY
    SELECT
        'Unused Indexes'::TEXT,
        CASE WHEN COUNT(*) > 0 THEN 'INFO' ELSE 'OK' END::TEXT,
        COUNT(*)::TEXT,
        'Consider dropping unused indexes'::TEXT
    FROM pg_stat_user_indexes
    WHERE idx_scan = 0;

    -- 检查连接数
    RETURN QUERY
    SELECT
        'Active Connections'::TEXT,
        CASE WHEN COUNT(*) > 80 THEN 'WARNING' ELSE 'OK' END::TEXT,
        COUNT(*)::TEXT,
        'Monitor connection pooling'::TEXT
    FROM pg_stat_activity
    WHERE state = 'active';

    -- 检查缓存命中率
    RETURN QUERY
    SELECT
        'Cache Hit Ratio'::TEXT,
        CASE
            WHEN SUM(blks_hit)::FLOAT / NULLIF(SUM(blks_hit + blks_read), 0) > 0.99 THEN 'OK'
            WHEN SUM(blks_hit)::FLOAT / NULLIF(SUM(blks_hit + blks_read), 0) > 0.95 THEN 'WARNING'
            ELSE 'CRITICAL'
        END::TEXT,
        ROUND(SUM(blks_hit)::NUMERIC / NULLIF(SUM(blks_hit + blks_read), 0) * 100, 2)::TEXT || '%',
        'Consider increasing shared_buffers if < 99%'::TEXT
    FROM pg_stat_database;

END;
$$ LANGUAGE plpgsql;

-- 11. 执行统计信息收集
-- ================================================
ANALYZE users;
ANALYZE transactions;
ANALYZE jobs;
ANALYZE api_keys;
ANALYZE audit_logs;

-- 12. 输出优化完成信息
-- ================================================
DO $$
BEGIN
    RAISE NOTICE '================================================';
    RAISE NOTICE 'Database optimization completed!';
    RAISE NOTICE '================================================';
    RAISE NOTICE 'Added indexes: 15+ performance indexes';
    RAISE NOTICE 'Created materialized view: mv_user_stats';
    RAISE NOTICE 'Created monitoring views: v_slow_queries, v_table_sizes, v_index_usage';
    RAISE NOTICE 'Created maintenance functions: cleanup_old_audit_logs, cleanup_expired_api_keys';
    RAISE NOTICE 'Created health check: SELECT * FROM database_health_check()';
    RAISE NOTICE '================================================';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Run: SELECT * FROM database_health_check();';
    RAISE NOTICE '2. Schedule: SELECT refresh_user_stats(); (hourly)';
    RAISE NOTICE '3. Schedule: SELECT cleanup_old_audit_logs(); (daily)';
    RAISE NOTICE '4. Monitor: SELECT * FROM v_table_sizes;';
    RAISE NOTICE '================================================';
END $$;
