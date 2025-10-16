#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电话号码验证系统 - 检测空号并添加备注标题
"""

import os
import sys
import json
import sqlite3
import logging
import re
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('phone_validation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PhoneValidationSystem:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.validation_results = {}
        self.processed_count = 0
        self.invalid_count = 0
        
    def connect_to_db(self) -> bool:
        """连接到数据库"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.execute("PRAGMA journal_mode=WAL")
            self.conn.execute("PRAGMA synchronous=NORMAL")
            self.conn.execute("PRAGMA cache_size=10000")
            self.conn.execute("PRAGMA temp_store=MEMORY")
            logger.info(f"成功连接到数据库: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False
    
    def get_phone_records(self, limit: int = 1000, offset: int = 0) -> List[Dict[str, Any]]:
        """获取待验证的电话号码记录"""
        cursor = self.conn.execute("""
            SELECT rowid, full_name, phone_e164, country_code, source_file, validation_status, validation_note
            FROM people 
            WHERE phone_e164 IS NOT NULL AND phone_e164 != ''
            AND (validation_status IS NULL OR validation_status = '')
            ORDER BY rowid
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        records = []
        for row in cursor.fetchall():
            records.append({
                'rowid': row[0],
                'full_name': row[1],
                'phone_e164': row[2],
                'country_code': row[3],
                'source_file': row[4],
                'validation_status': row[5],
                'validation_note': row[6]
            })
        
        return records
    
    def validate_phone_batch(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量验证电话号码"""
        logger.info(f"开始验证 {len(records)} 条电话号码记录")
        
        batch_results = {
            'total': len(records),
            'valid': 0,
            'invalid': 0,
            'categories': {},
            'details': []
        }
        
        for record in records:
            phone = record['phone_e164']
            
            # 格式验证
            format_result = self.validate_phone_format(phone)
            
            # 更新统计
            if format_result['valid']:
                batch_results['valid'] += 1
                status = 'valid'
                note = '号码格式正常'
            else:
                batch_results['invalid'] += 1
                status = 'invalid'
                note = format_result['reason']
                
                # 统计无效原因
                category = format_result['category']
                if category not in batch_results['categories']:
                    batch_results['categories'][category] = 0
                batch_results['categories'][category] += 1
            
            # 保存详细结果
            batch_results['details'].append({
                'rowid': record['rowid'],
                'phone': phone,
                'status': status,
                'note': note,
                'category': format_result['category']
            })
            
            # 更新数据库
            self.update_record_validation(record['rowid'], status, note)
            
            self.processed_count += 1
            if not format_result['valid']:
                self.invalid_count += 1
        
        return batch_results
    
    def update_record_validation(self, rowid: int, status: str, note: str) -> bool:
        """更新记录的验证状态和备注"""
        try:
            cursor = self.conn.execute("""
                UPDATE people 
                SET validation_status = ?, validation_note = ?, validation_date = ?
                WHERE rowid = ?
            """, (status, note, datetime.now().isoformat(), rowid))
            
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"更新记录 {rowid} 验证状态失败: {e}")
            return False
    
    def add_custom_note(self, rowid: int, note_title: str, note_content: str) -> bool:
        """添加自定义备注标题和内容"""
        try:
            # 合并备注标题和内容
            full_note = f"[{note_title}] {note_content}"
            
            cursor = self.conn.execute("""
                UPDATE people 
                SET validation_note = ?, custom_note_title = ?, custom_note_content = ?, last_modified = ?
                WHERE rowid = ?
            """, (full_note, note_title, note_content, datetime.now().isoformat(), rowid))
            
            self.conn.commit()
            logger.info(f"已为记录 {rowid} 添加备注: [{note_title}] {note_content}")
            return True
        except Exception as e:
            logger.error(f"添加备注失败: {e}")
            return False
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """获取验证汇总信息"""
        # 总体统计
        cursor = self.conn.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN validation_status = 'valid' THEN 1 END) as valid,
                COUNT(CASE WHEN validation_status = 'invalid' THEN 1 END) as invalid,
                COUNT(CASE WHEN validation_status IS NULL OR validation_status = '' THEN 1 END) as pending
            FROM people 
            WHERE phone_e164 IS NOT NULL AND phone_e164 != ''
        """)
        
        stats = cursor.fetchone()
        
        # 按国家统计
        cursor = self.conn.execute("""
            SELECT country_code, validation_status, COUNT(*) as count
            FROM people 
            WHERE phone_e164 IS NOT NULL AND phone_e164 != ''
            GROUP BY country_code, validation_status
            ORDER BY country_code, count DESC
        """)
        
        country_stats = {}
        for row in cursor.fetchall():
            country, status, count = row
            if country not in country_stats:
                country_stats[country] = {}
            country_stats[country][status] = count
        
        # 无效号码原因统计
        cursor = self.conn.execute("""
            SELECT validation_note, COUNT(*) as count
            FROM people 
            WHERE validation_status = 'invalid' AND validation_note IS NOT NULL
            GROUP BY validation_note
            ORDER BY count DESC
        """)
        
        invalid_reasons = [{'reason': row[0], 'count': row[1]} for row in cursor.fetchall()]
        
        return {
            'total_records': stats[0],
            'valid_numbers': stats[1],
            'invalid_numbers': stats[2],
            'pending_validation': stats[3],
            'country_stats': country_stats,
            'invalid_reasons': invalid_reasons,
            'processed_in_session': self.processed_count,
            'invalid_found_in_session': self.invalid_count
        }
    
    def run_validation(self, batch_size: int = 1000, max_batches: int = None) -> bool:
        """运行验证流程"""
        logger.info("开始电话号码验证流程")
        
        # 连接数据库
        if not self.connect_to_db():
            return False
        
        try:
            # 获取待验证记录总数
            cursor = self.conn.execute("""
                SELECT COUNT(*) FROM people 
                WHERE phone_e164 IS NOT NULL AND phone_e164 != ''
                AND (validation_status IS NULL OR validation_status = '')
            """)
            pending_count = cursor.fetchone()[0]
            
            logger.info(f"待验证记录总数: {pending_count:,}")
            
            if pending_count == 0:
                logger.info("没有待验证的记录")
                return True
            
            # 分批处理
            batch_num = 0
            offset = 0
            
            while True:
                # 获取一批记录
                records = self.get_phone_records(batch_size, offset)
                
                if not records:
                    break
                
                batch_num += 1
                logger.info(f"处理第 {batch_num} 批，记录数: {len(records)}")
                
                # 验证这批记录
                batch_results = self.validate_phone_batch(records)
                
                # 打印批次结果
                logger.info(f"第 {batch_num} 批结果: 有效 {batch_results['valid']}, 无效 {batch_results['invalid']}")
                
                # 检查是否达到最大批次数
                if max_batches and batch_num >= max_batches:
                    logger.info(f"已达到最大批次数 {max_batches}，停止处理")
                    break
                
                offset += batch_size
                
                # 如果这批记录数小于批次大小，说明已经处理完所有记录
                if len(records) < batch_size:
                    break
            
            # 生成最终报告
            summary = self.get_validation_summary()
            
            # 保存报告
            report_path = Path(self.db_path).parent / "phone_validation_report.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            logger.info(f"验证完成！报告已保存到: {report_path}")
            
            # 打印摘要
            print("\n" + "="*50)
            print("电话号码验证摘要:")
            print(f"总记录数: {summary['total_records']:,}")
            print(f"有效号码: {summary['valid_numbers']:,}")
            print(f"无效号码: {summary['invalid_numbers']:,}")
            print(f"待验证: {summary['pending_validation']:,}")
            print(f"本次处理: {summary['processed_in_session']:,}")
            print(f"本次发现无效: {summary['invalid_found_in_session']:,}")
            print("="*50)
            
            return True
            
        except Exception as e:
            logger.error(f"验证过程中出错: {e}")
            return False
        
        finally:
            if self.conn:
                self.conn.close()

def main():
    # 使用当前目录的数据库
    data_dir = Path.cwd()
    db_path = data_dir / "people_data_final.db"
    
    print(f"数据库路径: {db_path}")
    print("=" * 50)
    print("开始电话号码验证...")
    
    # 创建验证系统并运行
    validator = PhoneValidationSystem(str(db_path))
    success = validator.run_validation(batch_size=500, max_batches=10)
    
    if success:
        print("\n电话号码验证完成！")
    else:
        print("\n电话号码验证失败！")
        sys.exit(1)

if __name__ == '__main__':
    main()