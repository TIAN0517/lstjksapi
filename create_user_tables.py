#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查并创建用户表
"""

import sqlite3

def check_and_create_user_tables():
    conn = sqlite3.connect('bossjy_users.db')
    cursor = conn.cursor()
    
    # 检查现有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print('数据库中的表:')
    for table in tables:
        print(f'  {table}')
    
    # 创建用户表（如果不存在）
    if 'users' not in tables:
        print('\n创建用户表...')
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                telegram_id TEXT UNIQUE,
                is_active BOOLEAN DEFAULT TRUE,
                subscription_tier TEXT DEFAULT 'free',
                monthly_usage_limit INTEGER DEFAULT 1000,
                monthly_usage_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX idx_users_telegram_id ON users(telegram_id)")
        cursor.execute("CREATE INDEX idx_users_username ON users(username)")
        cursor.execute("CREATE INDEX idx_users_email ON users(email)")
        
        print('用户表创建成功')
    else:
        print('\n用户表已存在')
    
    # 创建群组表（如果不存在）
    if 'telegram_groups' not in tables:
        print('\n创建群组表...')
        cursor.execute("""
            CREATE TABLE telegram_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id TEXT UNIQUE NOT NULL,
                group_title TEXT,
                group_type TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print('群组表创建成功')
    else:
        print('\n群组表已存在')
    
    # 创建群组成员表（如果不存在）
    if 'telegram_group_members' not in tables:
        print('\n创建群组成员表...')
        cursor.execute("""
            CREATE TABLE telegram_group_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id TEXT NOT NULL,
                telegram_id TEXT NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_admin BOOLEAN DEFAULT FALSE,
                joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_seen_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(group_id, telegram_id)
            )
        """)
        print('群组成员表创建成功')
    else:
        print('\n群组成员表已存在')
    
    # 创建试用记录表（如果不存在）
    if 'sample_trials' not in tables:
        print('\n创建试用记录表...')
        cursor.execute("""
            CREATE TABLE sample_trials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                telegram_id TEXT NOT NULL,
                data_type TEXT NOT NULL,
                sample_count INTEGER DEFAULT 100,
                status TEXT DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        print('试用记录表创建成功')
    else:
        print('\n试用记录表已存在')
    
    conn.commit()
    conn.close()
    print('\n数据库表检查完成')

if __name__ == "__main__":
    check_and_create_user_tables()