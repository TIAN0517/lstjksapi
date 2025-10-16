#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试导入印尼华人数据
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import logging
from pathlib import Path
from datetime import datetime
import hashlib

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据库配置
import re
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

# 从DATABASE_URL解析配置
DATABASE_URL = os.getenv('DATABASE_URL', 'os.environ.get('DATABASE_URL', 'postgresql://bossjy:CHANGE_ME@postgres:5432/bossjy')')
# 处理Docker host名称
DATABASE_URL = DATABASE_URL.replace('@postgres:', '@localhost:')
# 强制使用正确的端口
DATABASE_URL = DATABASE_URL.replace(':5432/', ':15432/')

# 解析DATABASE_URL
match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
if match:
    user, password, host, port, database = match.groups()
    DB_CONFIG = {
        'host': host,
        'port': int(port),
        'database': database,
        'user': user,
        'password': password
    }
else:
    # 默认配置
    DB_CONFIG = {
        'host': 'localhost',
        'port': 15432,
        'database': 'bossjy_huaqiao',
        'user': 'bossjy',
        'password': 'ji394su3'
    }

def test_import_indonesian_data():
    """测试导入印尼数据"""
    logger.info("测试导入印尼华人数据...")
    
    # 获取第一个文件
    data_dir = Path("data/processed/印尼华人筛选结果")
    if not data_dir.exists():
        logger.error(f"目录不存在: {data_dir}")
        return
    
    # 找到最小的文件
    excel_files = list(data_dir.glob("*.xlsx"))
    excel_files.extend(list(data_dir.glob("*.xls")))
    
    if not excel_files:
        logger.error("没有找到Excel文件")
        return
    
    # 按文件大小排序，选择最小的
    excel_files.sort(key=lambda x: x.stat().st_size)
    test_file = excel_files[0]
    
    logger.info(f"选择测试文件: {test_file} (大小: {test_file.stat().st_size / (1024*1024):.1f} MB)")
    
    # 读取文件前100行作为测试
    try:
        df = pd.read_excel(test_file, nrows=100)
        logger.info(f"文件包含 {len(df.columns)} 列")
        logger.info(f"列名: {list(df.columns)}")
        
        # 显示前5行数据
        logger.info("前5行数据预览:")
        for i, row in df.head(5).iterrows():
            logger.info(f"  行 {i+1}: {dict(row)}")
            
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        return
    
    # 连接数据库
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # 创建测试表
        cursor.execute("""
            DROP TABLE IF EXISTS indonesian_test;
            CREATE TABLE indonesian_test (
                id SERIAL PRIMARY KEY,
                data JSONB
            );
        """)
        
        # 插入测试数据
        test_data = {
            'file_name': test_file.name,
            'file_size': test_file.stat().st_size,
            'columns': list(df.columns),
            'sample_data': df.head(5).to_dict('records')
        }
        
        cursor.execute("""
            INSERT INTO indonesian_test (data)
            VALUES (%s)
        """, (json.dumps(test_data, ensure_ascii=False),))
        
        conn.commit()
        conn.close()
        
        logger.info("测试数据已保存到 indonesian_test 表")
        
    except Exception as e:
        logger.error(f"数据库操作失败: {e}")

if __name__ == "__main__":
    import json
    test_import_indonesian_data()