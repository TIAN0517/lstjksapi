-- 显示所有表及其记录数
SELECT 
    schemaname,
    tablename,
    n_live_tup as live_rows
FROM pg_stat_user_tables 
ORDER BY schemaname, tablename;

-- 显示每个表的精确行数
DO $$
DECLARE
    r RECORD;
    sql TEXT;
    row_count INTEGER;
BEGIN
    RAISE NOTICE '=== 表行数统计 ===';
    FOR r IN 
        SELECT table_schema, table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    LOOP
        sql := 'SELECT COUNT(*) FROM ' || quote_ident(r.table_schema) || '.' || quote_ident(r.table_name);
        EXECUTE sql INTO row_count;
        RAISE NOTICE '%.%: % 行', r.table_schema, r.table_name, row_count;
    END LOOP;
END $$;