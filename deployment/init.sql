-- 初始化数据库
CREATE DATABASE IF NOT EXISTS filter_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE filter_system;

-- 创建默认管理员用户
-- 密码: admin123 (bcrypt加密后的值)
INSERT INTO users (username, password, email, role, status, created_at, updated_at) VALUES 
('admin', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iKVjzieMwkOmANgNOgKQNNBDvAGK', 'admin@example.com', 'admin', 'active', NOW(), NOW())
ON DUPLICATE KEY UPDATE username = username;

-- 插入示例黑名单数据
INSERT INTO blacklists (type, value, reason, created_by, created_at, updated_at) VALUES
('phone', '13800138000', '测试手机号', 1, NOW(), NOW()),
('ip', '192.168.1.100', '测试IP地址', 1, NOW(), NOW()),
('email', 'spam@example.com', '垃圾邮件邮箱', 1, NOW(), NOW())
ON DUPLICATE KEY UPDATE value = value;

-- 插入示例白名单数据
INSERT INTO whitelists (type, value, reason, created_by, created_at, updated_at) VALUES
('phone', '13900139000', '可信手机号', 1, NOW(), NOW()),
('ip', '192.168.1.1', '内网IP', 1, NOW(), NOW()),
('email', 'trusted@example.com', '可信邮箱', 1, NOW(), NOW())
ON DUPLICATE KEY UPDATE value = value;