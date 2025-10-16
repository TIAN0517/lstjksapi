-- 样本试用记录表
CREATE TABLE IF NOT EXISTS sample_trials (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    telegram_id VARCHAR(50) NOT NULL,

    -- 试用信息
    data_type VARCHAR(100) NOT NULL,  -- 数据类型（hongkong, indonesia, australia等）
    sample_count INTEGER DEFAULT 100,  -- 样本数量

    -- 试用状态
    status VARCHAR(50) DEFAULT 'active',  -- active, completed, expired

    -- 试用结果文件
    result_file_path VARCHAR(500),

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    used_at TIMESTAMP,

    -- 约束：每个用户每种数据类型只能试用一次
    UNIQUE(user_id, data_type)
);

-- 创建索引
CREATE INDEX idx_sample_trials_user_id ON sample_trials(user_id);
CREATE INDEX idx_sample_trials_telegram_id ON sample_trials(telegram_id);
CREATE INDEX idx_sample_trials_data_type ON sample_trials(data_type);
CREATE INDEX idx_sample_trials_status ON sample_trials(status);

-- 群组绑定表
CREATE TABLE IF NOT EXISTS telegram_groups (
    id BIGSERIAL PRIMARY KEY,
    group_id VARCHAR(100) UNIQUE NOT NULL,
    group_title VARCHAR(255),
    group_type VARCHAR(50),  -- 'group', 'supergroup', 'channel'

    -- 绑定信息
    is_active BOOLEAN DEFAULT TRUE,

    -- 群组设置
    allow_trials BOOLEAN DEFAULT TRUE,  -- 是否允许试用
    allow_queries BOOLEAN DEFAULT TRUE,  -- 是否允许查询

    -- 统计
    member_count INTEGER DEFAULT 0,
    trial_count INTEGER DEFAULT 0,
    query_count INTEGER DEFAULT 0,

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_telegram_groups_group_id ON telegram_groups(group_id);
CREATE INDEX idx_telegram_groups_is_active ON telegram_groups(is_active);

-- 群组成员表
CREATE TABLE IF NOT EXISTS telegram_group_members (
    id BIGSERIAL PRIMARY KEY,
    group_id VARCHAR(100) NOT NULL,
    telegram_id VARCHAR(50) NOT NULL,
    user_id INTEGER,

    -- 成员信息
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),

    -- 权限
    is_admin BOOLEAN DEFAULT FALSE,

    -- 时间戳
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 约束
    UNIQUE(group_id, telegram_id)
);

-- 创建索引
CREATE INDEX idx_telegram_group_members_group_id ON telegram_group_members(group_id);
CREATE INDEX idx_telegram_group_members_telegram_id ON telegram_group_members(telegram_id);
CREATE INDEX idx_telegram_group_members_user_id ON telegram_group_members(user_id);

COMMENT ON TABLE sample_trials IS '样本试用记录表';
COMMENT ON TABLE telegram_groups IS 'Telegram群组绑定表';
COMMENT ON TABLE telegram_group_members IS 'Telegram群组成员表';
