#!/usr/bin/env python3
"""
BossJy-Pro 数据导入脚本
从现有SQLite数据库导入数据到PostgreSQL
"""

import os
import sys
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import logging
from datetime import datetime
import pandas as pd
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataImporter:
    """数据导入器"""
    
    def __init__(self):
        self.postgres_config = {
            'host': 'localhost',
            'port': 15432,
            'database': 'bossjy',
            'user': 'bossjy',
            'password': os.getenv('POSTGRES_PASSWORD', 'CHANGE_ME')
        }
        self.data_dir = Path('data')
        self.available_dbs = []
        
    def scan_databases(self):
        """扫描可用的数据库文件"""
        logger.info("扫描数据库文件...")
        
        db_files = list(self.data_dir.glob('*.db'))
        for db_file in db_files:
            size_mb = db_file.stat().st_size / (1024 * 1024)
            self.available_dbs.append({
                'name': db_file.name,
                'path': str(db_file),
                'size_mb': size_mb
            })
        
        logger.info(f"找到 {len(self.available_dbs)} 个数据库文件:")
        for db in self.available_dbs:
            logger.info(f"  - {db['name']} ({db['size_mb']:.2f} MB)")
        
        return self.available_dbs
    
    def connect_postgres(self):
        """连接PostgreSQL"""
        try:
            conn = psycopg2.connect(**self.postgres_config)
            logger.info("PostgreSQL连接成功")
            return conn
        except Exception as e:
            logger.error(f"PostgreSQL连接失败: {e}")
            raise
    
    def connect_sqlite(self, db_path):
        """连接SQLite"""
        try:
            conn = sqlite3.connect(db_path)
            logger.info(f"SQLite连接成功: {db_path}")
            return conn
        except Exception as e:
            logger.error(f"SQLite连接失败: {e}")
            raise
    
    def get_table_info(self, sqlite_conn):
        """获取表信息"""
        cursor = sqlite_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        table_info = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            table_info[table] = count
        
        return table_info
    
    def import_marketplace_data(self):
        """导入marketplace数据"""
        marketplace_db = self.data_dir / 'marketplace.db'
        
        if not marketplace_db.exists():
            logger.error("marketplace.db 文件不存在")
            return
        
        logger.info("开始导入 marketplace 数据...")
        
        sqlite_conn = self.connect_sqlite(str(marketplace_db))
        postgres_conn = self.connect_postgres()
        
        try:
            # 获取表信息
            table_info = self.get_table_info(sqlite_conn)
            logger.info(f"Marketplace 数据库包含 {len(table_info)} 个表:")
            for table, count in table_info.items():
                logger.info(f"  - {table}: {count} 条记录")
            
            # 创建基本表结构（如果不存在）
            self.create_basic_tables(postgres_conn)
            
            # 导入主要数据表
            main_tables = ['users', 'data_records', 'credits', 'transactions']
            
            for table in main_tables:
                if table in table_info and table_info[table] > 0:
                    self.import_table_data(sqlite_conn, postgres_conn, table)
            
            logger.info("Marketplace 数据导入完成")
            
        except Exception as e:
            logger.error(f"导入失败: {e}")
            raise
        finally:
            sqlite_conn.close()
            postgres_conn.close()
    
    def create_basic_tables(self, postgres_conn):
        """创建基本表结构"""
        cursor = postgres_conn.cursor()
        
        # 用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255),
                password_hash VARCHAR(255),
                role VARCHAR(50) DEFAULT 'user',
                status VARCHAR(20) DEFAULT 'active',
                credits INTEGER DEFAULT 0,
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
                currency VARCHAR(10),
                status VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        postgres_conn.commit()
        logger.info("基本表结构创建完成")
    
    def import_table_data(self, sqlite_conn, postgres_conn, table_name):
        """导入表数据"""
        logger.info(f"导入表 {table_name}...")
        
        # 读取SQLite数据
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", sqlite_conn)
        
        if df.empty:
            logger.info(f"表 {table_name} 无数据")
            return
        
        cursor = postgres_conn.cursor()
        
        try:
            # 准备数据
            df = df.where(pd.notnull(df), None)  # 替换NaN为None
            
            # 转换为元组列表
            tuples = [tuple(x) for x in df.to_numpy()]
            cols = ','.join(list(df.columns))
            
            # 批量插入
            insert_sql = f"INSERT INTO {table_name} ({cols}) VALUES %s"
            execute_values(cursor, insert_sql, tuples)
            
            postgres_conn.commit()
            logger.info(f"表 {table_name} 导入完成，共 {len(df)} 条记录")
            
        except Exception as e:
            logger.error(f"导入表 {table_name} 失败: {e}")
            postgres_conn.rollback()
            raise
    
    def import_telegram_bot_data(self):
        """导入Telegram Bot数据"""
        telegram_db = self.data_dir / 'telegram_bot.db'
        
        if not telegram_db.exists():
            logger.warning("telegram_bot.db 文件不存在")
            return
        
        logger.info("开始导入 Telegram Bot 数据...")
        
        sqlite_conn = self.connect_sqlite(str(telegram_db))
        postgres_conn = self.connect_postgres()
        
        try:
            # 获取表信息
            table_info = self.get_table_info(sqlite_conn)
            logger.info(f"Telegram Bot 数据库包含 {len(table_info)} 个表")
            
            # 创建Telegram相关表
            self.create_telegram_tables(postgres_conn)
            
            # 导入数据
            for table, count in table_info.items():
                if count > 0:
                    self.import_table_data(sqlite_conn, postgres_conn, f"telegram_{table}")
            
            logger.info("Telegram Bot 数据导入完成")
            
        except Exception as e:
            logger.error(f"导入失败: {e}")
            raise
        finally:
            sqlite_conn.close()
            postgres_conn.close()
    
    def create_telegram_tables(self, postgres_conn):
        """创建Telegram相关表"""
        cursor = postgres_conn.cursor()
        
        # Telegram用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telegram_users (
                id SERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username VARCHAR(100),
                first_name VARCHAR(100),
                last_name VARCHAR(100),
                is_bot BOOLEAN DEFAULT FALSE,
                language_code VARCHAR(10),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Telegram群组表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS telegram_groups (
                id SERIAL PRIMARY KEY,
                group_id BIGINT UNIQUE NOT NULL,
                title VARCHAR(255),
                username VARCHAR(100),
                description TEXT,
                member_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        postgres_conn.commit()
        logger.info("Telegram表结构创建完成")
    
    def run_import(self):
        """运行导入"""
        logger.info("开始数据导入流程...")
        
        # 确保日志目录存在
        os.makedirs('logs', exist_ok=True)
        
        # 扫描数据库
        self.scan_databases()
        
        # 导入marketplace数据
        self.import_marketplace_data()
        
        # 导入Telegram Bot数据
        self.import_telegram_bot_data()
        
        logger.info("所有数据导入完成！")

def main():
    """主函数"""
    importer = DataImporter()
    try:
        importer.run_import()
    except Exception as e:
        logger.error(f"导入失败: {e}")
        raise

if __name__ == "__main__":
    main()