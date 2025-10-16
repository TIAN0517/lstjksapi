-- 检查所有表的记录数
SELECT 
    schemaname,
    tablename,
    n_tup_ins AS total_inserts,
    n_tup_upd AS total_updates,
    n_tup_del AS total_deletes,
    n_live_tup AS live_rows,
    n_dead_tup AS dead_rows
FROM pg_stat_user_tables 
ORDER BY schemaname, tablename;