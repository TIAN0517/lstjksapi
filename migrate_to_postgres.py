#!/usr/bin/env python3
"""
BossJy-Pro 数据库迁移脚本
将SQLite数据迁移到PostgreSQL
"""

import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os
import logging
from datetime import datetime
import pandas as pd
from tqdm import tqdm

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据库配置
SQLITE_DB_PATH = 'data/marketplace.db'
POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 15432,
    'database': 'bossjy',
    'user': 'bossjy',
    'password': 'CHANGE_ME'  # 从环境变量获取
}

def get_postgres_connection():
    """获取PostgreSQL连接"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"PostgreSQL连接失败: {e}")
        raise

def get_sqlite_connection():
    """获取SQLite连接"""
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        return conn
    except Exception as e:
        logger.error(f"SQLite连接失败: {e}")
        raise

def get_table_names(sqlite_conn):
    """获取SQLite中的所有表名"""
    cursor = sqlite_conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    return tables

def get_table_schema(sqlite_conn, table_name):
    """获取表结构"""
    cursor = sqlite_conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    return columns

def create_postgres_table(postgres_conn, table_name, columns):
    """在PostgreSQL中创建表"""
    cursor = postgres_conn.cursor()
    
    # 构建CREATE TABLE语句
    column_defs = []
    for col in columns:
        col_name = col[1]
        col_type = col[2].upper()
        
        # 转换数据类型
        if 'INT' in col_type:
            pg_type = 'INTEGER'
        elif 'TEXT' in col_type or 'CHAR' in col_type:
            pg_type = 'TEXT'
        elif 'REAL' in col_type or 'FLOAT' in col_type:
            pg_type = 'REAL'
        elif 'BLOB' in col_type:
            pg_type = 'BYTEA'
        else:
            pg_type = 'TEXT'
        
        nullable = 'NOT NULL' if col[3] == 1 else ''
        column_defs.append(f"{col_name} {pg_type} {nullable}")
    
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id SERIAL PRIMARY KEY,
        {', '.join(column_defs)}
    );
    """
    
    try:
        cursor.execute(create_sql)
        postgres_conn.commit()
        logger.info(f"创建表 {table_name} 成功")
    except Exception as e:
        logger.error(f"创建表 {table_name} 失败: {e}")
        postgres_conn.rollback()
        raise

def migrate_table_data(sqlite_conn, postgres_conn, table_name):
    """迁移表数据"""
    # 获取SQLite数据
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", sqlite_conn)
    
    if df.empty:
        logger.info(f"表 {table_name} 无数据，跳过")
        return
    
    cursor = postgres_conn.cursor()
    
    try:
        # 批量插入数据
        tuples = [tuple(x) for x in df.to_numpy()]
        cols = ','.join(list(df.columns))
        
        # 使用execute_values进行批量插入
        insert_sql = f"INSERT INTO {table_name} ({cols}) VALUES %s"
        execute_values(cursor, insert_sql, tuples)
        
        postgres_conn.commit()
        logger.info(f"表 {table_name} 迁移完成，共 {len(df)} 条记录")
        
    except Exception as e:
        logger.error(f"迁移表 {table_name} 失败: {e}")
        postgres_conn.rollback()
        raise

def main():
    """主函数"""
    logger.info("开始数据迁移...")
    
    try:
        # 连接数据库
        sqlite_conn = get_sqlite_connection()
        postgres_conn = get_postgres_connection()
        
        # 获取所有表名
        tables = get_table_names(sqlite_conn)
        logger.info(f"发现 {len(tables)} 个表: {', '.join(tables)}")
        
        # 迁移每个表
        for table_name in tqdm(tables, desc="迁移表"):
            try:
                # 获取表结构
                columns = get_table_schema(sqlite_conn, table_name)
                
                # 在PostgreSQL中创建表
                create_postgres_table(postgres_conn, table_name, columns)
                
                # 迁移数据
                migrate_table_data(sqlite_conn, postgres_conn, table_name)
                
            except Exception as e:
                logger.error(f"处理表 {table_name} 时出错: {e}")
                continue
        
        # 关闭连接
        sqlite_conn.close()
        postgres_conn.close()
        
        logger.info("数据迁移完成！")
        
    except Exception as e:
        logger.error(f"迁移失败: {e}")
        raise

if __name__ == "__main__":
    main()