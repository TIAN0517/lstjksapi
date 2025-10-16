-- 检查数据库表和数据
\dt
SELECT 'users' as table_name, COUNT(*) as record_count FROM users
UNION ALL
SELECT 'data_marketplace', COUNT(*) FROM data_marketplace;
SELECT * FROM users;
SELECT * FROM data_marketplace;