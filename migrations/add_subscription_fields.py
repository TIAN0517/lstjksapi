#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：添加订阅相关字段
Migration: Add subscription fields to users table
"""

import sqlite3
from datetime import datetime
import os

def migrate():
    """执行数据库迁移"""
    db_path = 'bossjy_users.db'

    if not os.path.exists(db_path):
        print(f"[ERROR] Database file not found: {db_path}")
        print(f"        Current directory: {os.getcwd()}")
        print("        Please run this script from project root")
        return False

    print(f"[INFO] Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 检查users表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("[ERROR] Table 'users' not found")
            return False

        print("[OK] Found users table")

        # 获取现有列
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        print(f"[INFO] Existing columns: {existing_columns}")

        # 要添加的新列
        new_columns = {
            'subscription_tier': "ALTER TABLE users ADD COLUMN subscription_tier VARCHAR(20) DEFAULT 'payg' NOT NULL",
            'subscription_expires_at': "ALTER TABLE users ADD COLUMN subscription_expires_at DATETIME",
            'monthly_usage_count': "ALTER TABLE users ADD COLUMN monthly_usage_count INTEGER DEFAULT 0 NOT NULL",
            'monthly_usage_limit': "ALTER TABLE users ADD COLUMN monthly_usage_limit INTEGER DEFAULT 0 NOT NULL",
            'monthly_usage_reset_date': "ALTER TABLE users ADD COLUMN monthly_usage_reset_date DATETIME"
        }

        # 添加缺失的列
        added_count = 0
        for column_name, sql in new_columns.items():
            if column_name not in existing_columns:
                print(f"[ADD] Adding column: {column_name}")
                cursor.execute(sql)
                added_count += 1
            else:
                print(f"[SKIP] Column already exists: {column_name}")

        if added_count > 0:
            conn.commit()
            print(f"\n[SUCCESS] Added {added_count} new columns to users table")
        else:
            print("\n[INFO] All columns already exist, no migration needed")

        # 验证
        cursor.execute("PRAGMA table_info(users)")
        final_columns = [row[1] for row in cursor.fetchall()]
        print(f"\n[INFO] Final columns: {final_columns}")

        return True

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == '__main__':
    print("=" * 60)
    print("[Migration] Add subscription fields to users table")
    print("=" * 60)
    print()

    success = migrate()

    print()
    print("=" * 60)
    if success:
        print("[SUCCESS] Migration completed")
    else:
        print("[FAILED] Migration failed")
    print("=" * 60)
