#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BossJy-Pro 数据导入和统计工具
将data目录下的所有数据导入PostgreSQL数据库，并提供Bot查询功能
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values, execute_batch
import logging
from pathlib import Path
import glob
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any
import hashlib

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_import.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 数据库配置
import re
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# 从DATABASE_URL解析配置
DATABASE_URL = os.getenv('DATABASE_URL', 'os.environ.get('DATABASE_URL', 'postgresql://bossjy:CHANGE_ME@postgres:5432/bossjy')')
# 处理Docker host名称
DATABASE_URL = DATABASE_URL.replace('@postgres:', '@localhost:')
# 强制使用正确的端口
DATABASE_URL = DATABASE_URL.replace(':5432/', ':15432/')

# 解析DATABASE_URL
print(f"DATABASE_URL: {DATABASE_URL}")
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
    print(f"解析的数据库配置: {DB_CONFIG}")
else:
    # 默认配置
    DB_CONFIG = {
        'host': 'localhost',
        'port': 15432,
        'database': 'bossjy_huaqiao',
        'user': 'bossjy',
        'password': 'ji394su3'
    }
    print(f"使用默认数据库配置: {DB_CONFIG}")

class DataImporter:
    """数据导入器"""
    
    def __init__(self):
        self.data_dir = Path("data")
        self.stats = {
            'total_files': 0,
            'imported_files': 0,
            'failed_files': 0,
            'total_records': 0,
            'imported_records': 0,
            'categories': {},
            'regions': {},
            'sources': {}
        }
        
        # 创建日志目录
        Path("logs").mkdir(exist_ok=True)
        
    def get_connection(self):
        """获取数据库连接"""
        return psycopg2.connect(**DB_CONFIG)
    
    def create_tables(self):
        """创建数据表"""
        logger.info("创建数据表...")
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # 创建主数据表
            cursor.execute("""
                DROP TABLE IF EXISTS chinese_data CASCADE;
                CREATE TABLE chinese_data (
                    id BIGSERIAL PRIMARY KEY,
                    original_name VARCHAR(500),
                    chinese_name VARCHAR(500),
                    english_name VARCHAR(500),
                    phone_number VARCHAR(100),
                    email VARCHAR(255),
                    address TEXT,
                    city VARCHAR(200),
                    region VARCHAR(100),
                    country VARCHAR(100),
                    category VARCHAR(100),
                    source_file VARCHAR(500),
                    file_hash VARCHAR(64),
                    row_number INTEGER,
                    confidence_score DECIMAL(3,2),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    
                    -- 索引
                    INDEX idx_original_name (original_name),
                    INDEX idx_chinese_name (chinese_name),
                    INDEX idx_phone_number (phone_number),
                    INDEX idx_email (email),
                    INDEX idx_region (region),
                    INDEX idx_category (category),
                    INDEX idx_source_file (source_file),
                    INDEX idx_confidence_score (confidence_score),
                    
                    -- 全文搜索索引
                    INDEX idx_full_text_search USING gin(to_tsvector('chinese', original_name || ' ' || COALESCE(chinese_name, '') || ' ' || COALESCE(address, '')))
                );
                
                -- 创建统计表
                CREATE TABLE IF NOT EXISTS data_statistics (
                    id SERIAL PRIMARY KEY,
                    category VARCHAR(100),
                    region VARCHAR(100),
                    country VARCHAR(100),
                    source_file VARCHAR(500),
                    record_count INTEGER,
                    import_time TIMESTAMP DEFAULT NOW()
                );
                
                -- 创建查询缓存表
                CREATE TABLE IF NOT EXISTS query_cache (
                    id SERIAL PRIMARY KEY,
                    query_key VARCHAR(255) UNIQUE,
                    query_result JSONB,
                    created_at TIMESTAMP DEFAULT NOW(),
                    expires_at TIMESTAMP
                );
                
                -- 创建数据来源表
                CREATE TABLE IF NOT EXISTS data_sources (
                    id SERIAL PRIMARY KEY,
                    source_file VARCHAR(500) UNIQUE,
                    file_path TEXT,
                    file_size BIGINT,
                    file_hash VARCHAR(64),
                    import_status VARCHAR(50),
                    record_count INTEGER,
                    import_time TIMESTAMP DEFAULT NOW(),
                    last_updated TIMESTAMP DEFAULT NOW()
                );
            """)
            
            conn.commit()
            logger.info("数据表创建完成")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"创建数据表失败: {e}")
            raise
        finally:
            conn.close()
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def detect_category_and_region(self, file_path: Path) -> Tuple[str, str]:
        """检测文件类别和地区"""
        file_name = file_path.name.lower()
        file_path_str = str(file_path).lower()
        
        # 检测类别
        category = "其他"
        if "华人" in file_name or "chinese" in file_name:
            category = "华人"
        elif "香港" in file_name or "hongkong" in file_name or "hk" in file_name:
            category = "香港人"
        elif "印尼" in file_name or "indonesia" in file_name or "indonesian" in file_name:
            category = "印尼华人"
        elif "澳洲" in file_name or "australia" in file_name or "au" in file_name:
            category = "澳洲华人"
        elif "加拿大" in file_name or "canada" in file_name or "ca" in file_name:
            category = "加拿大华人"
        
        # 检测地区
        region = "其他"
        if "香港" in file_path_str or "hongkong" in file_path_str:
            region = "香港"
        elif "澳洲" in file_path_str or "australia" in file_path_str:
            region = "澳洲"
        elif "印尼" in file_path_str or "indonesia" in file_path_str:
            region = "印尼"
        elif "加拿大" in file_path_str or "canada" in file_path_str:
            region = "加拿大"
        elif "台湾" in file_path_str or "taiwan" in file_path_str:
            region = "台湾"
        elif "新加坡" in file_path_str or "singapore" in file_path_str:
            region = "新加坡"
        
        return category, region
    
    def extract_name_fields(self, df: pd.DataFrame, file_path: Path) -> Dict[str, str]:
        """提取姓名字段"""
        name_fields = {}
        columns = df.columns.tolist()
        
        # 查找可能的姓名列
        for col in columns:
            col_lower = str(col).lower()
            
            # 原始姓名
            if any(keyword in col_lower for keyword in ['name', '姓名', 'nama', 'full_name', 'full name']):
                if df[col].notna().any():
                    name_fields['original_name'] = col
            
            # 中文名
            if any(keyword in col_lower for keyword in ['chinese', '中文', '中文名', 'chinese_name', 'chinese name']):
                if df[col].notna().any():
                    name_fields['chinese_name'] = col
            
            # 英文名
            if any(keyword in col_lower for keyword in ['english', '英文', '英文名', 'english_name', 'english name']):
                if df[col].notna().any():
                    name_fields['english_name'] = col
        
        return name_fields
    
    def extract_contact_fields(self, df: pd.DataFrame, file_path: Path) -> Dict[str, str]:
        """提取联系方式字段"""
        contact_fields = {}
        columns = df.columns.tolist()
        
        for col in columns:
            col_lower = str(col).lower()
            
            # 电话
            if any(keyword in col_lower for keyword in ['phone', '电话', 'mobile', '手机', 'contact', '联系方式']):
                if df[col].notna().any():
                    contact_fields['phone_number'] = col
            
            # 邮箱
            if any(keyword in col_lower for keyword in ['email', '邮箱', 'mail', '电子邮件']):
                if df[col].notna().any():
                    contact_fields['email'] = col
            
            # 地址
            if any(keyword in col_lower for keyword in ['address', '地址', 'street', '街道']):
                if df[col].notna().any():
                    contact_fields['address'] = col
            
            # 城市
            if any(keyword in col_lower for keyword in ['city', '城市', 'town', '城镇']):
                if df[col].notna().any():
                    contact_fields['city'] = col
        
        return contact_fields
    
    def calculate_confidence_score(self, row: pd.Series, category: str, name_fields: Dict[str, str]) -> float:
        """计算置信度分数"""
        score = 0.0
        
        # 基础分数
        if category == "华人":
            score += 0.3
        elif category == "香港人":
            score += 0.4
        elif category == "印尼华人":
            score += 0.35
        elif category == "澳洲华人":
            score += 0.3
        
        # 姓名字段完整性
        if 'original_name' in name_fields and pd.notna(row.get(name_fields['original_name'])):
            score += 0.2
        if 'chinese_name' in name_fields and pd.notna(row.get(name_fields['chinese_name'])):
            score += 0.3
        
        # 联系方式完整性
        if pd.notna(row.get('phone_number')):
            score += 0.1
        if pd.notna(row.get('email')):
            score += 0.1
        
        return min(score, 1.0)
    
    def import_file(self, file_path: Path) -> int:
        """导入单个文件"""
        logger.info(f"导入文件: {file_path}")
        
        try:
            # 计算文件哈希
            file_hash = self.calculate_file_hash(file_path)
            file_size = file_path.stat().st_size
            
            # 检查文件是否已导入
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM data_sources WHERE file_hash = %s", (file_hash,))
            if cursor.fetchone():
                logger.info(f"文件已导入，跳过: {file_path}")
                conn.close()
                return 0
            
            # 检测类别和地区
            category, region = self.detect_category_and_region(file_path)
            
            # 读取文件
            if file_path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            elif file_path.suffix.lower() == '.csv':
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(file_path, encoding='gbk')
                    except UnicodeDecodeError:
                        df = pd.read_csv(file_path, encoding='latin1')
            else:
                logger.warning(f"不支持的文件格式: {file_path}")
                conn.close()
                return 0
            
            # 提取字段映射
            name_fields = self.extract_name_fields(df, file_path)
            contact_fields = self.extract_contact_fields(df, file_path)
            
            # 准备数据
            records = []
            for idx, row in df.iterrows():
                try:
                    # 提取姓名
                    original_name = ""
                    if 'original_name' in name_fields:
                        original_name = str(row.get(name_fields['original_name'], "")).strip()
                    
                    chinese_name = ""
                    if 'chinese_name' in name_fields:
                        chinese_name = str(row.get(name_fields['chinese_name'], "")).strip()
                    
                    english_name = ""
                    if 'english_name' in name_fields:
                        english_name = str(row.get(name_fields['english_name'], "")).strip()
                    
                    # 提取联系方式
                    phone_number = ""
                    if 'phone_number' in contact_fields:
                        phone_number = str(row.get(contact_fields['phone_number'], "")).strip()
                    
                    email = ""
                    if 'email' in contact_fields:
                        email = str(row.get(contact_fields['email'], "")).strip()
                    
                    address = ""
                    if 'address' in contact_fields:
                        address = str(row.get(contact_fields['address'], "")).strip()
                    
                    city = ""
                    if 'city' in contact_fields:
                        city = str(row.get(contact_fields['city'], "")).strip()
                    
                    # 计算置信度
                    confidence_score = self.calculate_confidence_score(row, category, name_fields)
                    
                    # 创建记录
                    record = (
                        original_name or None,
                        chinese_name or None,
                        english_name or None,
                        phone_number or None,
                        email or None,
                        address or None,
                        city or None,
                        region,
                        None,  # country
                        category,
                        file_path.name,
                        file_hash,
                        idx + 1,
                        confidence_score
                    )
                    
                    records.append(record)
                    
                except Exception as e:
                    logger.warning(f"处理行数据失败: {e}")
                    continue
            
            # 批量插入
            if records:
                execute_values(
                    cursor,
                    """
                    INSERT INTO chinese_data
                    (original_name, chinese_name, english_name, phone_number, email,
                     address, city, region, country, category, source_file,
                     file_hash, row_number, confidence_score)
                    VALUES %s
                    """,
                    records,
                    page_size=1000
                )
                
                # 记录文件信息
                cursor.execute("""
                    INSERT INTO data_sources
                    (source_file, file_path, file_size, file_hash, import_status, record_count)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source_file) DO UPDATE SET
                    record_count = EXCLUDED.record_count,
                    last_updated = NOW()
                """, (file_path.name, str(file_path), file_size, file_hash, 'completed', len(records)))
                
                # 更新统计
                cursor.execute("""
                    INSERT INTO data_statistics
                    (category, region, record_count)
                    VALUES (%s, %s, %s)
                """, (category, region, len(records)))
            
            conn.commit()
            conn.close()
            
            # 更新统计信息
            self.stats['imported_records'] += len(records)
            self.stats['categories'][category] = self.stats['categories'].get(category, 0) + len(records)
            self.stats['regions'][region] = self.stats['regions'].get(region, 0) + len(records)
            self.stats['sources'][file_path.name] = len(records)
            
            logger.info(f"文件导入完成: {file_path}, 记录数: {len(records)}")
            return len(records)
            
        except Exception as e:
            logger.error(f"导入文件失败 {file_path}: {e}")
            if 'conn' in locals():
                conn.rollback()
                conn.close()
            return 0
    
    def import_all_data(self):
        """导入所有数据"""
        logger.info("开始导入所有数据...")
        
        # 创建表
        self.create_tables()
        
        # 查找所有文件
        all_files = []
        
        # 查找CSV文件
        csv_files = list(self.data_dir.rglob("*.csv"))
        all_files.extend(csv_files)
        
        # 查找Excel文件
        excel_files = list(self.data_dir.rglob("*.xlsx"))
        all_files.extend(excel_files)
        
        excel_files.extend(list(self.data_dir.rglob("*.xls")))
        all_files.extend(excel_files)
        
        logger.info(f"找到 {len(all_files)} 个文件")
        
        # 导入文件
        for file_path in all_files:
            self.stats['total_files'] += 1
            imported = self.import_file(file_path)
            if imported > 0:
                self.stats['imported_files'] += 1
            else:
                self.stats['failed_files'] += 1
        
        # 生成报告
        self.generate_report()
    
    def generate_report(self):
        """生成导入报告"""
        report = {
            'import_time': datetime.now().isoformat(),
            'statistics': self.stats,
            'database_info': DB_CONFIG
        }
        
        # 保存报告
        report_file = Path("logs/import_report.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 打印摘要
        logger.info("="*80)
        logger.info("数据导入完成！")
        logger.info(f"总文件数: {self.stats['total_files']}")
        logger.info(f"成功导入: {self.stats['imported_files']}")
        logger.info(f"导入失败: {self.stats['failed_files']}")
        logger.info(f"总记录数: {self.stats['imported_records']:,}")
        logger.info("按类别统计:")
        for category, count in self.stats['categories'].items():
            logger.info(f"  {category}: {count:,}")
        logger.info("按地区统计:")
        for region, count in self.stats['regions'].items():
            logger.info(f"  {region}: {count:,}")
        logger.info(f"详细报告: {report_file}")
        logger.info("="*80)

class DataQueryService:
    """数据查询服务"""
    
    def __init__(self):
        self.conn = None
        
    def get_connection(self):
        """获取数据库连接"""
        if not self.conn:
            self.conn = psycopg2.connect(**DB_CONFIG)
        return self.conn
    
    def get_total_count(self) -> Dict[str, Any]:
        """获取总记录数"""
        cursor = self.get_connection().cursor()
        cursor.execute("SELECT COUNT(*) FROM persons")
        total = cursor.fetchone()[0]
        
        # 按国家统计
        cursor.execute("""
            SELECT country, COUNT(*) 
            FROM persons 
            WHERE country IS NOT NULL
            GROUP BY country
        """)
        by_country = dict(cursor.fetchall())
        
        # 按城市统计
        cursor.execute("""
            SELECT city, COUNT(*) 
            FROM persons 
            WHERE city IS NOT NULL
            GROUP BY city
        """)
        by_city = dict(cursor.fetchall())
        
        return {
            'total': total,
            'by_country': by_country,
            'by_city': by_city
        }
    
    def search_by_name(self, name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """按姓名搜索"""
        cursor = self.get_connection().cursor()
        cursor.execute("""
            cursor.execute("""
            SELECT name, phone, email, city, country, is_chinese, chinese_score
            FROM persons 
            WHERE name ILIKE %s 
        """, (f"%{name}%",))
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def search_by_category(self, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """按国家搜索"""
        cursor = self.get_connection().cursor()
        cursor.execute("""
            SELECT name, phone, email, city, country, is_chinese
            FROM persons 
            WHERE country = %s
            ORDER BY chinese_score DESC
            LIMIT %s
        """, (category, limit))
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def search_by_region(self, region: str, limit: int = 10) -> List[Dict[str, Any]]:
        """按城市搜索"""
        cursor = self.get_connection().cursor()
        cursor.execute("""
            SELECT name, phone, email, city, country, is_chinese
            FROM persons 
            WHERE city = %s
            ORDER BY chinese_score DESC
            LIMIT %s
        """, (region, limit))
        
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='BossJy-Pro 数据导入工具')
    parser.add_argument('--import-data', action='store_true', help='导入所有数据')
    parser.add_argument('--stats', action='store_true', help='显示统计信息')
    parser.add_argument('--search', type=str, help='搜索姓名')
    parser.add_argument('--category', type=str, help='按类别搜索')
    parser.add_argument('--region', type=str, help='按地区搜索')
    
    args = parser.parse_args()
    
    if args.import_data:
        # 导入数据
        importer = DataImporter()
        importer.import_all_data()
    
    elif args.stats or args.search or args.category or args.region:
        # 查询数据
        query_service = DataQueryService()
        
        if args.stats:
            stats = query_service.get_total_count()
            print("数据统计:")
            print(f"总记录数: {stats['total']:,}")
            print("\n按国家:")
            for country, count in stats['by_country'].items():
                print(f"  {country}: {count:,}")
            print("\n按城市:")
            for city, count in stats['by_city'].items():
                print(f"  {city}: {count:,}")
            
        
        elif args.search:
            results = query_service.search_by_name(args.search)
            print(f"🔍 搜索 '{args.search}' 的结果:")
            for result in results:
                print(f"  姓名: {result['original_name']}")
                print(f"  中文: {result['chinese_name']}")
                print(f"  电话: {result['phone_number']}")
                print(f"  邮箱: {result['email']}")
                print(f"  地区: {result['region']}")
                print(f"  类别: {result['category']}")
                print("-" * 40)
        
        elif args.category:
            results = query_service.search_by_category(args.category)
            print(f"📂 类别 '{args.category}' 的记录:")
            for result in results:
                print(f"  姓名: {result['original_name']}")
                print(f"  中文: {result['chinese_name']}")
                print(f"  电话: {result['phone_number']}")
                print(f"  城市: {result['city']}")
                print("-" * 40)
        
        elif args.region:
            results = query_service.search_by_region(args.region)
            print(f"🌍 地区 '{args.region}' 的记录:")
            for result in results:
                print(f"  姓名: {result['original_name']}")
                print(f"  中文: {result['chinese_name']}")
                print(f"  电话: {result['phone_number']}")
                print(f"  类别: {result['category']}")
                print("-" * 40)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
