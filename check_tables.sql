-- 显示所有表及其记录数
SELECT 
    schemaname,
    tablename,
    n_tup_ins as total_inserts,
    n_tup_upd as total_updates,
    n_tup_del as total_deletes,
    n_live_tup as live_rows,
    n_dead_tup as dead_rows
FROM pg_stat_user_tables 
ORDER BY schemaname, tablename;

-- 显示每个表的精确行数
DO $$
DECLARE
    r RECORD;
    sql TEXT;
BEGIN
    RAISE NOTICE '=== 表行数统计 ===';
    FOR r IN 
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    LOOP
        sql := 'SELECT COUNT(*) FROM ' || quote_ident(r.table_schema) || '.' || quote_ident(r.table_name);
        EXECUTE sql INTO r;
        RAISE NOTICE '%.%: % 行', r.table_schema, r.table_name, r;
    END LOOP;
END $$;