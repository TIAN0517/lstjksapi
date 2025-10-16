#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
华人数据入库脚本
将处理后的华人数据导入数据库，方便Bot查询
"""

import pandas as pd
import sqlite3
import os
import sys
from pathlib import Path
from datetime import datetime
import logging
import json

# 配置日志
log_file = f"database_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ChineseDataImporter:
    """华人数据入库器"""
    
    def __init__(self):
        self.db_path = "D:/BossJy-Cn/BossJy-Cn/data/chinese_database.db"
        self.processed_data_path = Path("D:/BossJy-Cn/BossJy-Cn/data/processed_data")
        self.stats = {
            'total_files': 0,
            'imported_files': 0,
            'failed_files': 0,
            'total_records': 0,
            'imported_records': 0,
            'indonesian_records': 0,
            'hongkong_records': 0,
            'other_records': 0
        }
        
        # 初始化数据库
        self.init_database()
    
    def init_database(self):
        """初始化数据库和表结构"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建主表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chinese_people (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_name TEXT,
                    chinese_name TEXT,
                    category TEXT,
                    source_file TEXT,
                    region TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX(category),
                    INDEX(region),
                    INDEX(source_file)
                )
            ''')
            
            # 创建详细信息表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chinese_people_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    people_id INTEGER,
                    field_name TEXT,
                    field_value TEXT,
                    FOREIGN KEY (people_id) REFERENCES chinese_people (id)
                )
            ''')
            
            # 创建统计视图
            cursor.execute('''
                CREATE VIEW IF NOT EXISTS chinese_stats AS
                SELECT 
                    category,
                    region,
                    COUNT(*) as count,
                    DATE(created_at) as date
                FROM chinese_people
                GROUP BY category, region, DATE(created_at)
            ''')
            
            conn.commit()
            conn.close()
            logger.info(f"数据库初始化完成: {self.db_path}")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
    
    def import_file(self, file_path, category):
        """导入单个文件"""
        try:
            logger.info(f"正在导入文件: {file_path}")
            
            # 读取文件
            if file_path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            elif file_path.suffix.lower() == '.csv':
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(file_path, encoding='latin1')
                    except UnicodeDecodeError:
                        df = pd.read_csv(file_path, encoding='cp1252')
            else:
                logger.warning(f"跳过不支持的文件格式: {file_path}")
                return 0
            
            # 确定地区
            region = "其他"
            if "印尼" in str(file_path):
                region = "印尼"
            elif "香港" in str(file_path) or "澳洲" in str(file_path):
                region = "澳洲/香港"
            elif "加拿大" in str(file_path):
                region = "加拿大"
            
            # 连接数据库
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            imported_count = 0
            
            # 遍历每一行数据
            for index, row in df.iterrows():
                try:
                    # 查找姓名列
                    name_value = None
                    chinese_name_value = None
                    
                    # 查找可能的姓名列
                    for col in df.columns:
                        col_lower = str(col).lower()
                        if any(keyword in col_lower for keyword in ['name', '姓名', 'nama']):
                            if pd.notna(row[col]):
                                name_value = str(row[col]).strip()
                                break
                    
                    # 查找翻译后的中文名
                    if 'chinese_name_translated' in df.columns and pd.notna(row['chinese_name_translated']):
                        chinese_name_value = str(row['chinese_name_translated']).strip()
                    
                    # 如果没有找到姓名，跳过
                    if not name_value:
                        continue
                    
                    # 插入主表
                    cursor.execute('''
                        INSERT INTO chinese_people (original_name, chinese_name, category, source_file, region)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        name_value,
                        chinese_name_value or '',
                        category,
                        file_path.name,
                        region
                    ))
                    
                    people_id = cursor.lastrowid
                    
                    # 插入详细信息
                    for col in df.columns:
                        if pd.notna(row[col]) and str(row[col]).strip():
                            cursor.execute('''
                                INSERT INTO chinese_people_details (people_id, field_name, field_value)
                                VALUES (?, ?, ?)
                            ''', (people_id, str(col), str(row[col])))
                    
                    imported_count += 1
                    
                except Exception as e:
                    logger.warning(f"导入行数据失败: {str(e)}")
                    continue
            
            conn.commit()
            conn.close()
            
            self.stats['imported_records'] += imported_count
            if category == "印尼华人":
                self.stats['indonesian_records'] += imported_count
            elif category == "香港人":
                self.stats['hongkong_records'] += imported_count
            else:
                self.stats['other_records'] += imported_count
            
            logger.info(f"文件导入完成: {file_path}, 导入记录数: {imported_count}")
            return imported_count
            
        except Exception as e:
            logger.error(f"导入文件失败 {file_path}: {str(e)}")
            self.stats['failed_files'] += 1
            return 0
    
    def import_all_data(self):
        """导入所有处理后的数据"""
        logger.info("开始导入所有华人数据到数据库")
        
        # 导入印尼华人数据
        indonesian_dir = self.processed_data_path / "印尼华人"
        if indonesian_dir.exists():
            logger.info("导入印尼华人数据...")
            for file_path in indonesian_dir.glob("*.xlsx"):
                self.stats['total_files'] += 1
                self.import_file(file_path, "印尼华人")
                self.stats['imported_files'] += 1
            
            for file_path in indonesian_dir.glob("*.csv"):
                self.stats['total_files'] += 1
                self.import_file(file_path, "印尼华人")
                self.stats['imported_files'] += 1
        
        # 导入香港人数据
        hongkong_dir = self.processed_data_path / "香港人"
        if hongkong_dir.exists():
            logger.info("导入香港人数据...")
            for file_path in hongkong_dir.glob("*.xlsx"):
                self.stats['total_files'] += 1
                self.import_file(file_path, "香港人")
                self.stats['imported_files'] += 1
            
            for file_path in hongkong_dir.glob("*.csv"):
                self.stats['total_files'] += 1
                self.import_file(file_path, "香港人")
                self.stats['imported_files'] += 1
        
        # 导入其他华人数据
        other_dir = self.processed_data_path / "其他华人"
        if other_dir.exists():
            logger.info("导入其他华人数据...")
            for file_path in other_dir.glob("*.xlsx"):
                self.stats['total_files'] += 1
                self.import_file(file_path, "其他华人")
                self.stats['imported_files'] += 1
            
            for file_path in other_dir.glob("*.csv"):
                self.stats['total_files'] += 1
                self.import_file(file_path, "其他华人")
                self.stats['imported_files'] += 1
        
        # 生成统计报告
        self.generate_import_report()
    
    def generate_import_report(self):
        """生成导入报告"""
        report_file = self.processed_data_path / "处理报告" / f"database_import_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("华人数据入库报告\n")
            f.write("="*80 + "\n")
            f.write(f"导入时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"数据库路径: {self.db_path}\n")
            f.write("\n统计信息:\n")
            f.write(f"  总文件数: {self.stats['total_files']}\n")
            f.write(f"  成功导入: {self.stats['imported_files']}\n")
            f.write(f"  导入失败: {self.stats['failed_files']}\n")
            f.write(f"  总记录数: {self.stats['imported_records']:,}\n")
            f.write(f"  印尼华人: {self.stats['indonesian_records']:,}\n")
            f.write(f"  香港人: {self.stats['hongkong_records']:,}\n")
            f.write(f"  其他华人: {self.stats['other_records']:,}\n")
        
        logger.info(f"导入报告已保存到: {report_file}")
    
    def create_bot_query_functions(self):
        """创建Bot查询函数"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建查询华人姓名的函数
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS query_functions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    function_name TEXT,
                    sql_query TEXT,
                    description TEXT
                )
            ''')
            
            # 插入常用查询函数
            queries = [
                {
                    'name': 'search_by_name',
                    'sql': 'SELECT * FROM chinese_people WHERE original_name LIKE ? OR chinese_name LIKE ?',
                    'desc': '按姓名搜索华人'
                },
                {
                    'name': 'search_by_category',
                    'sql': 'SELECT * FROM chinese_people WHERE category = ?',
                    'desc': '按类别搜索华人'
                },
                {
                    'name': 'search_by_region',
                    'sql': 'SELECT * FROM chinese_people WHERE region = ?',
                    'desc': '按地区搜索华人'
                },
                {
                    'name': 'get_statistics',
                    'sql': 'SELECT * FROM chinese_stats',
                    'desc': '获取统计信息'
                }
            ]
            
            for query in queries:
                cursor.execute('''
                    INSERT OR REPLACE INTO query_functions (function_name, sql_query, description)
                    VALUES (?, ?, ?)
                ''', (query['name'], query['sql'], query['desc']))
            
            conn.commit()
            conn.close()
            logger.info("Bot查询函数创建完成")
            
        except Exception as e:
            logger.error(f"创建Bot查询函数失败: {str(e)}")

def main():
    """主函数"""
    logger.info("="*80)
    logger.info("华人数据入库工具")
    logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)
    
    # 创建导入器
    importer = ChineseDataImporter()
    
    try:
        # 导入所有数据
        importer.import_all_data()
        
        # 创建Bot查询函数
        importer.create_bot_query_functions()
        
        logger.info("\n数据入库完成！")
        logger.info(f"数据库位置: {importer.db_path}")
        logger.info("Bot现在可以通过数据库查询华人数据")
        
    except Exception as e:
        logger.error(f"入库过程中发生错误: {str(e)}")
    finally:
        logger.info(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()