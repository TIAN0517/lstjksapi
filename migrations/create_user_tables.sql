-- 创建用户认证系统数据库表
-- User Authentication System Database Tables

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,

    -- Telegram绑定信息
    telegram_id VARCHAR(50) UNIQUE,
    telegram_username VARCHAR(100),
    telegram_first_name VARCHAR(100),
    telegram_last_name VARCHAR(100),
    telegram_bind_code VARCHAR(6),
    telegram_bind_code_expires DATETIME,

    -- 用户状态
    is_active BOOLEAN DEFAULT 1 NOT NULL,
    is_verified BOOLEAN DEFAULT 0 NOT NULL,
    is_admin BOOLEAN DEFAULT 0 NOT NULL,

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    last_login_at DATETIME
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_user_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_user_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_user_telegram_id ON users(telegram_id);

-- 用户会话表
CREATE TABLE IF NOT EXISTS user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,

    -- JWT Token信息
    token_jti VARCHAR(255) UNIQUE NOT NULL,

    -- 登录信息
    ip_address VARCHAR(50),
    user_agent TEXT,
    login_source VARCHAR(20),  -- 'web' 或 'telegram'

    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    expires_at DATETIME NOT NULL,
    last_activity_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    -- 是否已登出
    is_revoked BOOLEAN DEFAULT 0 NOT NULL,
    revoked_at DATETIME,

    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_session_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_session_token_jti ON user_sessions(token_jti);
