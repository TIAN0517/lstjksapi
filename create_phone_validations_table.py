#!/usr/bin/env python3
"""
创建phone_validations表的脚本
用于存储电话号码验证记录
"""

import psycopg2
from psycopg2 import sql
import os
from datetime import datetime

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'port': '15432',
    'database': 'bossjy_huaqiao',
    'user': 'jytian',
    'password': 'ji394su3'
}

def create_phone_validations_table():
    """创建phone_validations表"""
    try:
        # 连接数据库
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("成功连接到数据库")
        
        # 创建phone_validations表的SQL
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS phone_validations (
            id SERIAL PRIMARY KEY,
            phone_number VARCHAR(20) NOT NULL,
            country_code VARCHAR(5) NOT NULL,
            is_valid BOOLEAN NOT NULL DEFAULT FALSE,
            validation_type VARCHAR(50) NOT NULL DEFAULT 'format',
            validation_result JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER REFERENCES users(id),
            tenant VARCHAR(50) DEFAULT 'default',
            metadata JSONB
        );
        
        -- 创建索引
        CREATE INDEX IF NOT EXISTS idx_phone_validations_phone_number ON phone_validations(phone_number);
        CREATE INDEX IF NOT EXISTS idx_phone_validations_country_code ON phone_validations(country_code);
        CREATE INDEX IF NOT EXISTS idx_phone_validations_is_valid ON phone_validations(is_valid);
        CREATE INDEX IF NOT EXISTS idx_phone_validations_user_id ON phone_validations(user_id);
        CREATE INDEX IF NOT EXISTS idx_phone_validations_tenant ON phone_validations(tenant);
        CREATE INDEX IF NOT EXISTS idx_phone_validations_created_at ON phone_validations(created_at);
        
        -- 创建更新时间触发器
        CREATE OR REPLACE FUNCTION update_phone_validations_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        DROP TRIGGER IF EXISTS phone_validations_updated_at_trigger ON phone_validations;
        CREATE TRIGGER phone_validations_updated_at_trigger
            BEFORE UPDATE ON phone_validations
            FOR EACH ROW
            EXECUTE FUNCTION update_phone_validations_updated_at();
        
        -- 添加注释
        COMMENT ON TABLE phone_validations IS '电话号码验证记录表';
        COMMENT ON COLUMN phone_validations.phone_number IS '电话号码';
        COMMENT ON COLUMN phone_validations.country_code IS '国家代码';
        COMMENT ON COLUMN phone_validations.is_valid IS '是否有效';
        COMMENT ON COLUMN phone_validations.validation_type IS '验证类型: format, carrier, existence';
        COMMENT ON COLUMN phone_validations.validation_result IS '验证结果详情';
        COMMENT ON COLUMN phone_validations.user_id IS '关联用户ID';
        COMMENT ON COLUMN phone_validations.tenant IS '租户标识';
        COMMENT ON COLUMN phone_validations.metadata IS '额外元数据';
        """
        
        # 执行SQL
        cursor.execute(create_table_sql)
        
        # 提交事务
        conn.commit()
        
        print("✅ phone_validations表创建成功！")
        
        # 验证表是否创建成功
        cursor.execute("""
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'phone_validations'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("\n📋 表结构:")
        for col in columns:
            print(f"  - {col[0]}.{col[1]} ({col[2]}) {'NULL' if col[3] == 'YES' else 'NOT NULL'}")
        
        # 检查索引
        cursor.execute("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'phone_validations';
        """)
        
        indexes = cursor.fetchall()
        print("\n📑 创建的索引:")
        for idx in indexes:
            print(f"  - {idx[0]}")
        
    except psycopg2.Error as e:
        print(f"❌ 数据库错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
    
    return True

def check_existing_data():
    """检查是否已存在数据"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 检查表中是否有数据
        cursor.execute("SELECT COUNT(*) FROM phone_validations")
        count = cursor.fetchone()[0]
        
        print(f"\n📊 当前表中有 {count} 条记录")
        
        if count > 0:
            cursor.execute("""
                SELECT phone_number, country_code, is_valid, created_at
                FROM phone_validations
                ORDER BY created_at DESC
                LIMIT 5
            """)
            
            records = cursor.fetchall()
            print("\n📝 最近5条记录:")
            for record in records:
                print(f"  - {record[0]} (+{record[1]}) - {'有效' if record[2] else '无效'} - {record[3]}")
        
    except psycopg2.Error as e:
        print(f"❌ 检查数据时出错: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 开始创建phone_validations表")
    print("=" * 60)
    
    # 创建表
    if create_phone_validations_table():
        print("\n" + "=" * 60)
        print("✅ 表创建完成！")
        print("=" * 60)
        
        # 检查现有数据
        check_existing_data()
        
        print("\n🎉 phone_validations表已准备就绪！")
    else:
        print("\n" + "=" * 60)
        print("❌ 表创建失败！")
        print("=" * 60)