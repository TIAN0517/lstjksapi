-- 获取所有表名
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

-- 获取每个表的记录数
DO $$
DECLARE
    t RECORD;
    count_val BIGINT;
BEGIN
    RAISE NOTICE '=== 表记录统计 ===';
    FOR t IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
    LOOP
        EXECUTE 'SELECT COUNT(*) FROM ' || t.table_name INTO count_val;
        RAISE NOTICE '%: % 条记录', t.table_name, count_val;
    END LOOP;
END $$;