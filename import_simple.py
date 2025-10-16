#!/usr/bin/env python3
"""
简单的PostgreSQL数据导入脚本
创建基础表结构并插入示例数据
"""

import psycopg2
import os
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# PostgreSQL配置
POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 15432,
    'database': 'bossjy_huaqiao',
    'user': 'jytian',
    'password': 'ji394su3'
}

def connect_postgres():
    """连接PostgreSQL"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        logger.info("PostgreSQL连接成功")
        return conn
    except Exception as e:
        logger.error(f"PostgreSQL连接失败: {e}")
        raise

def create_tables(conn):
    """创建基础表结构"""
    cursor = conn.cursor()
    
    try:
        # 用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255),
                password_hash VARCHAR(255),
                role VARCHAR(50) DEFAULT 'user',
                status VARCHAR(20) DEFAULT 'active',
                credits INTEGER DEFAULT 100,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 数据记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_records (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                data_type VARCHAR(100),
                content TEXT,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 数据市场表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_marketplace (
                id SERIAL PRIMARY KEY,
                data_type VARCHAR(100) NOT NULL,
                name VARCHAR(255),
                company VARCHAR(255),
                phone VARCHAR(50),
                email VARCHAR(255),
                address TEXT,
                city VARCHAR(100),
                country VARCHAR(100),
                raw_data JSONB,
                is_sample BOOLEAN DEFAULT FALSE,
                price DECIMAL(10,2) DEFAULT 99.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 积分表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credits (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                amount INTEGER,
                type VARCHAR(50),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 交易表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                amount DECIMAL(10,2),
                currency VARCHAR(10) DEFAULT 'USDT',
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        conn.commit()
        logger.info("基础表结构创建完成")
        
    except Exception as e:
        logger.error(f"创建表失败: {e}")
        conn.rollback()
        raise

def insert_sample_data(conn):
    """插入示例数据"""
    cursor = conn.cursor()
    
    try:
        # 插入示例用户
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role, credits) VALUES
            ('admin', 'admin@bossjy.com', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iKVjzieMwkOmANgNOgKQNNBDvAGK', 'admin', 10000),
            ('demo_user', 'demo@example.com', '$2a$10$N.zmdr9k7uOCQb376NoUnuTJ8iKVjzieMwkOmANgNOgKQNNBDvAGK', 'user', 100)
            ON CONFLICT (username) DO NOTHING;
        """)
        
        # 插入示例数据市场数据
        sample_data = [
            ('hongkong', '张三', '香港贸易公司', '+85212345678', 'zhangsan@example.com', '香港中环', '香港', '中国香港', '{"age": 35, "industry": "贸易"}', True, 99.0),
            ('australia', 'John Smith', 'Aussie Trading', '+61412345678', 'john@aussie.com', 'Sydney CBD', 'Sydney', 'Australia', '{"age": 42, "industry": "进出口"}', True, 99.0),
            ('indonesia', 'Budi Santoso', 'PT Jakarta Import', '+628123456789', 'budi@jakarta.co.id', 'Jakarta Pusat', 'Jakarta', 'Indonesia', '{"age": 38, "industry": "进口贸易"}', True, 99.0),
            ('chinese_global', '李四', '全球华人集团', '+14155552671', 'lisi@global.com', 'San Francisco', 'San Francisco', 'USA', '{"age": 45, "industry": "科技"}', True, 99.0)
        ]
        
        cursor.executemany("""
            INSERT INTO data_marketplace 
            (data_type, name, company, phone, email, address, city, country, raw_data, is_sample, price)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING;
        """, sample_data)
        
        conn.commit()
        logger.info("示例数据插入完成")
        
    except Exception as e:
        logger.error(f"插入示例数据失败: {e}")
        conn.rollback()
        raise

def main():
    """主函数"""
    logger.info("开始创建PostgreSQL数据库结构...")
    
    conn = connect_postgres()
    
    try:
        # 创建表结构
        create_tables(conn)
        
        # 插入示例数据
        insert_sample_data(conn)
        
        logger.info("PostgreSQL数据库初始化完成！")
        
        # 显示统计信息
        cursor = conn.cursor()
        
        # 用户统计
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        logger.info(f"用户数: {user_count}")
        
        # 数据统计
        cursor.execute("SELECT data_type, COUNT(*) FROM data_marketplace GROUP BY data_type")
        data_stats = cursor.fetchall()
        logger.info("数据市场统计:")
        for data_type, count in data_stats:
            logger.info(f"  - {data_type}: {count} 条")
        
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()