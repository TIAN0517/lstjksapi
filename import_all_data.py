#!/usr/bin/env python3
"""
BossJy-Pro 统一数据导入脚本
自动扫描并导入所有数据文件到PostgreSQL
支持CSV、Excel、JSON、SQLite格式
"""

import os
import sys
import json
import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
from pathlib import Path
import logging
from datetime import datetime
import hashlib

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/import_all_data.log'),
        logging.StreamHandler()
    ]
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

class UniversalDataImporter:
    """通用数据导入器"""
    
    def __init__(self):
        self.data_dir = Path('data')
        self.postgres_conn = None
        self.imported_files = set()
        self.failed_files = []
        
        # 确保日志目录存在
        os.makedirs('logs', exist_ok=True)
        
    def connect_postgres(self):
        """连接PostgreSQL"""
        try:
            self.postgres_conn = psycopg2.connect(**POSTGRES_CONFIG)
            logger.info("PostgreSQL连接成功")
            return True
        except Exception as e:
            logger.error(f"PostgreSQL连接失败: {e}")
            return False
    
    def create_tables(self):
        """创建所有必要的表"""
        cursor = self.postgres_conn.cursor()
        
        # 创建导入记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS import_history (
                id SERIAL PRIMARY KEY,
                file_path VARCHAR(500),
                file_hash VARCHAR(64),
                file_size BIGINT,
                import_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20),
                records_count INTEGER,
                error_message TEXT
            );
        """)
        
        # 创建数据市场表（增强版）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS data_marketplace (
                id SERIAL PRIMARY KEY,
                source_file VARCHAR(500),
                data_type VARCHAR(100),
                name VARCHAR(255),
                company VARCHAR(255),
                phone VARCHAR(50),
                email VARCHAR(255),
                address TEXT,
                city VARCHAR(100),
                state VARCHAR(100),
                country VARCHAR(100),
                postal_code VARCHAR(20),
                website VARCHAR(255),
                industry VARCHAR(100),
                raw_data JSONB,
                is_sample BOOLEAN DEFAULT FALSE,
                price DECIMAL(10,2) DEFAULT 99.0,
                quality_score INTEGER DEFAULT 50,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_data_marketplace_type ON data_marketplace(data_type);
            CREATE INDEX IF NOT EXISTS idx_data_marketplace_phone ON data_marketplace(phone);
            CREATE INDEX IF NOT EXISTS idx_data_marketplace_email ON data_marketplace(email);
            CREATE INDEX IF NOT EXISTS idx_data_marketplace_country ON data_marketplace(country);
        """)
        
        self.postgres_conn.commit()
        logger.info("数据表创建完成")
    
    def get_file_hash(self, file_path):
        """计算文件哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def is_file_imported(self, file_path):
        """检查文件是否已导入"""
        file_hash = self.get_file_hash(file_path)
        cursor = self.postgres_conn.cursor()
        cursor.execute(
            "SELECT id FROM import_history WHERE file_hash = %s AND status = 'success'",
            (file_hash,)
        )
        return cursor.fetchone() is not None
    
    def record_import(self, file_path, status, records_count=0, error_message=None):
        """记录导入历史"""
        file_hash = self.get_file_hash(file_path)
        file_size = os.path.getsize(file_path)
        
        cursor = self.postgres_conn.cursor()
        cursor.execute("""
            INSERT INTO import_history 
            (file_path, file_hash, file_size, status, records_count, error_message)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (file_path, file_hash, file_size, status, records_count, error_message))
        
        self.postgres_conn.commit()
    
    def classify_data_type(self, file_path, df):
        """智能分类数据类型"""
        file_name = os.path.basename(file_path).lower()
        file_path_lower = file_path.lower()
        
        # 根据文件名判断
        if any(keyword in file_name for keyword in ['hongkong', 'hong_kong', '香港']):
            return 'hongkong'
        elif any(keyword in file_name for keyword in ['australia', '澳洲', 'au']):
            return 'australia'
        elif any(keyword in file_name for keyword in ['indonesia', '印尼']):
            return 'indonesia'
        elif any(keyword in file_name for keyword in ['canada', '加拿大']):
            return 'canada'
        elif any(keyword in file_name for keyword in ['usa', 'america', '美国']):
            return 'usa'
        elif any(keyword in file_name for keyword in ['uk', 'britain', '英国']):
            return 'uk'
        elif any(keyword in file_name for keyword in ['germany', '德国']):
            return 'germany'
        elif any(keyword in file_name for keyword in ['italy', '意大利']):
            return 'italy'
        elif any(keyword in file_name for keyword in ['singapore', '新加坡']):
            return 'singapore'
        elif any(keyword in file_name for keyword in ['malaysia', '马来西亚']):
            return 'malaysia'
        elif any(keyword in file_name for keyword in ['chinese', '华人']):
            return 'chinese_global'
        
        # 根据内容判断
        if 'country' in df.columns:
            countries = df['country'].dropna().astype(str).str.lower().unique()
            if any('hong kong' in c for c in countries):
                return 'hongkong'
            elif any('australia' in c for c in countries):
                return 'australia'
            elif any('indonesia' in c for c in countries):
                return 'indonesia'
            elif any('china' in c or 'chinese' in c for c in countries):
                return 'chinese_global'
        
        # 默认分类
        return 'other'
    
    def clean_phone_number(self, phone):
        """清理电话号码"""
        if pd.isna(phone):
            return None
        phone_str = str(phone)
        # 移除所有非数字字符
        phone_str = ''.join(filter(str.isdigit, phone_str))
        # 保留国家代码
        if len(phone_str) > 10:
            return '+' + phone_str
        return phone_str if phone_str else None
    
    def clean_email(self, email):
        """清理邮箱地址"""
        if pd.isna(email):
            return None
        email_str = str(email).strip().lower()
        # 简单的邮箱格式验证
        if '@' in email_str and '.' in email_str.split('@')[-1]:
            return email_str
        return None
    
    def import_csv_excel(self, file_path):
        """导入CSV或Excel文件"""
        try:
            # 读取文件
            if file_path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path)
            
            logger.info(f"  文件包含 {len(df)} 条记录，{len(df.columns)} 个字段")
            
            if df.empty:
                logger.warning(f"  文件为空，跳过")
                return 0
            
            # 分类数据类型
            data_type = self.classify_data_type(file_path, df)
            logger.info(f"  数据类型: {data_type}")
            
            # 标准化列名
            column_mapping = {
                '姓名': 'name', '名字': 'name', '名': 'name',
                '公司': 'company', '企业': 'company', '单位': 'company',
                '电话': 'phone', '手机': 'phone', '联系方式': 'phone',
                '邮箱': 'email', '电子邮件': 'email', 'mail': 'email',
                '地址': 'address', '住址': 'address',
                '城市': 'city', '市': 'city',
                '省份': 'state', '州': 'state',
                '国家': 'country', '國家': 'country',
                '邮编': 'postal_code', '邮政编码': 'postal_code',
                '网站': 'website', '网址': 'website',
                '行业': 'industry', '产业': 'industry'
            }
            
            # 重命名列
            df = df.rename(columns=column_mapping)
            
            # 准备数据
            records = []
            sample_count = min(10, len(df))
            
            for idx, row in df.iterrows():
                # 清理数据
                record = {
                    'source_file': str(file_path),
                    'data_type': data_type,
                    'name': row.get('name') if pd.notna(row.get('name')) else None,
                    'company': row.get('company') if pd.notna(row.get('company')) else None,
                    'phone': self.clean_phone_number(row.get('phone')),
                    'email': self.clean_email(row.get('email')),
                    'address': row.get('address') if pd.notna(row.get('address')) else None,
                    'city': row.get('city') if pd.notna(row.get('city')) else None,
                    'state': row.get('state') if pd.notna(row.get('state')) else None,
                    'country': row.get('country') if pd.notna(row.get('country')) else None,
                    'postal_code': row.get('postal_code') if pd.notna(row.get('postal_code')) else None,
                    'website': row.get('website') if pd.notna(row.get('website')) else None,
                    'industry': row.get('industry') if pd.notna(row.get('industry')) else None,
                    'raw_data': json.dumps(row.to_dict(), ensure_ascii=False),
                    'is_sample': idx < sample_count,
                    'price': 99.0,
                    'quality_score': 50
                }
                records.append(record)
            
            # 批量插入
            cursor = self.postgres_conn.cursor()
            execute_values(
                cursor,
                """
                INSERT INTO data_marketplace 
                (source_file, data_type, name, company, phone, email, address, city, 
                 state, country, postal_code, website, industry, raw_data, is_sample, 
                 price, quality_score)
                VALUES %s
                """,
                records
            )
            
            self.postgres_conn.commit()
            logger.info(f"  成功导入 {len(records)} 条记录")
            return len(records)
            
        except Exception as e:
            logger.error(f"  导入失败: {e}")
            raise
    
    def import_sqlite(self, file_path):
        """导入SQLite数据库"""
        try:
            sqlite_conn = sqlite3.connect(str(file_path))
            cursor = sqlite_conn.cursor()
            
            # 获取所有表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            total_records = 0
            for table_name, in tables:
                # 读取表数据
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", sqlite_conn)
                
                if not df.empty:
                    # 转换并导入
                    records = []
                    for _, row in df.iterrows():
                        record = {
                            'source_file': str(file_path) + f':{table_name}',
                            'data_type': f'sqlite_{table_name}',
                            'name': row.get('name') if pd.notna(row.get('name')) else None,
                            'company': row.get('company') if pd.notna(row.get('company')) else None,
                            'phone': self.clean_phone_number(row.get('phone')),
                            'email': self.clean_email(row.get('email')),
                            'address': row.get('address') if pd.notna(row.get('address')) else None,
                            'city': row.get('city') if pd.notna(row.get('city')) else None,
                            'state': row.get('state') if pd.notna(row.get('state')) else None,
                            'country': row.get('country') if pd.notna(row.get('country')) else None,
                            'raw_data': json.dumps(row.to_dict(), ensure_ascii=False),
                            'is_sample': False,
                            'price': 99.0,
                            'quality_score': 50
                        }
                        records.append(record)
                    
                    # 批量插入
                    pg_cursor = self.postgres_conn.cursor()
                    execute_values(
                        pg_cursor,
                        """
                        INSERT INTO data_marketplace 
                        (source_file, data_type, name, company, phone, email, address, 
                         city, state, country, raw_data, is_sample, price, quality_score)
                        VALUES %s
                        """,
                        records
                    )
                    
                    total_records += len(records)
                    logger.info(f"  表 {table_name}: {len(records)} 条记录")
            
            sqlite_conn.close()
            self.postgres_conn.commit()
            logger.info(f"  SQLite数据库导入完成，共 {total_records} 条记录")
            return total_records
            
        except Exception as e:
            logger.error(f"  SQLite导入失败: {e}")
            raise
    
    def import_json(self, file_path):
        """导入JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            records = []
            if isinstance(data, list):
                items = data
            else:
                items = [data]
            
            for item in items:
                record = {
                    'source_file': str(file_path),
                    'data_type': 'json_data',
                    'name': item.get('name'),
                    'company': item.get('company'),
                    'phone': self.clean_phone_number(item.get('phone')),
                    'email': self.clean_email(item.get('email')),
                    'address': item.get('address'),
                    'city': item.get('city'),
                    'state': item.get('state'),
                    'country': item.get('country'),
                    'raw_data': json.dumps(item, ensure_ascii=False),
                    'is_sample': False,
                    'price': 99.0,
                    'quality_score': 50
                }
                records.append(record)
            
            # 批量插入
            cursor = self.postgres_conn.cursor()
            execute_values(
                cursor,
                """
                INSERT INTO data_marketplace 
                (source_file, data_type, name, company, phone, email, address, 
                 city, state, country, raw_data, is_sample, price, quality_score)
                VALUES %s
                """,
                records
            )
            
            self.postgres_conn.commit()
            logger.info(f"  JSON文件导入完成，共 {len(records)} 条记录")
            return len(records)
            
        except Exception as e:
            logger.error(f"  JSON导入失败: {e}")
            raise
    
    def scan_and_import(self):
        """扫描并导入所有数据文件"""
        if not self.connect_postgres():
            return False
        
        self.create_tables()
        
        # 支持的文件类型
        file_types = ['.csv', '.xlsx', '.xls', '.db', '.json']
        
        # 扫描所有文件
        all_files = []
        for file_path in self.data_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in file_types:
                all_files.append(file_path)
        
        logger.info(f"找到 {len(all_files)} 个数据文件")
        
        # 导入文件
        for file_path in all_files:
            try:
                logger.info(f"\n处理文件: {file_path}")
                
                # 检查是否已导入
                if self.is_file_imported(file_path):
                    logger.info("  文件已导入，跳过")
                    continue
                
                # 根据文件类型导入
                records_count = 0
                if file_path.suffix.lower() in ['.csv', '.xlsx', '.xls']:
                    records_count = self.import_csv_excel(file_path)
                elif file_path.suffix.lower() == '.db':
                    records_count = self.import_sqlite(file_path)
                elif file_path.suffix.lower() == '.json':
                    records_count = self.import_json(file_path)
                
                # 记录导入历史
                self.record_import(file_path, 'success', records_count)
                self.imported_files.add(str(file_path))
                
            except Exception as e:
                logger.error(f"文件导入失败: {e}")
                self.record_import(file_path, 'failed', 0, str(e))
                self.failed_files.append(str(file_path))
        
        # 显示统计
        self.show_statistics()
        
        return True
    
    def show_statistics(self):
        """显示导入统计"""
        logger.info("\n" + "=" * 60)
        logger.info("导入统计")
        logger.info("=" * 60)
        
        cursor = self.postgres_conn.cursor()
        
        # 总体统计
        cursor.execute("SELECT COUNT(*) FROM data_marketplace")
        total_count = cursor.fetchone()[0]
        logger.info(f"数据市场总记录数: {total_count}")
        
        # 按类型统计
        cursor.execute("""
            SELECT data_type, COUNT(*) 
            FROM data_marketplace 
            GROUP BY data_type 
            ORDER BY COUNT(*) DESC
        """)
        type_stats = cursor.fetchall()
        logger.info("\n按数据类型统计:")
        for data_type, count in type_stats:
            logger.info(f"  {data_type}: {count} 条")
        
        # 按来源文件统计
        cursor.execute("""
            SELECT source_file, COUNT(*) 
            FROM data_marketplace 
            GROUP BY source_file 
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)
        file_stats = cursor.fetchall()
        logger.info("\n按文件统计（前10）:")
        for file_path, count in file_stats:
            logger.info(f"  {os.path.basename(file_path)}: {count} 条")
        
        # 导入历史
        cursor.execute("""
            SELECT status, COUNT(*) 
            FROM import_history 
            GROUP BY status
        """)
        history_stats = cursor.fetchall()
        logger.info("\n导入历史:")
        for status, count in history_stats:
            logger.info(f"  {status}: {count} 个文件")
        
        logger.info(f"\n成功导入: {len(self.imported_files)} 个文件")
        logger.info(f"导入失败: {len(self.failed_files)} 个文件")
        
        if self.failed_files:
            logger.info("\n失败的文件:")
            for file in self.failed_files:
                logger.info(f"  - {file}")

def main():
    """主函数"""
    logger.info("BossJy-Pro 统一数据导入开始")
    logger.info("=" * 60)
    
    importer = UniversalDataImporter()
    
    try:
        success = importer.scan_and_import()
        if success:
            logger.info("\n数据导入完成！")
        else:
            logger.error("\n数据导入失败！")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"导入过程出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
