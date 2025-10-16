#!/usr/bin/env python3
"""
批量数据导入脚本（优化版）
功能：
1. 扫描所有数据文件
2. 删除日期相关字段（保护数据时效性）
3. 分类整理数据
4. 批量导入数据市场数据库（使用批量插入，带进度显示）
"""

import pandas as pd
import os
import sys
import sqlite3
from pathlib import Path
import logging
import json
from tqdm import tqdm

sys.path.append('/mnt/d/BossJy-Cn/BossJy-Cn')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/mnt/d/BossJy-Cn/BossJy-Cn/logs/bulk_import_optimized.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 数据库路径
DB_PATH = '/mnt/d/BossJy-Cn/BossJy-Cn/data/marketplace.db'

# 日期相关字段的关键词（中英文）
DATE_KEYWORDS = [
    'date', 'time', 'year', 'month', 'day',
    '日期', '时间', '年份', '月份', '年',
    'created', 'updated', 'modified',
    '创建', '更新', '修改',
    'register', 'registration',
    '注册',
    'birth', 'birthday',
    '生日', '出生'
]

def is_date_column(column_name):
    """判断是否为日期相关字段"""
    column_lower = str(column_name).lower()
    for keyword in DATE_KEYWORDS:
        if keyword in column_lower:
            return True
    return False

def remove_date_columns(df):
    """删除数据框中的日期相关字段"""
    date_columns = [col for col in df.columns if is_date_column(col)]

    if date_columns:
        logger.info(f"  🗑️  删除日期字段: {', '.join(date_columns)}")
        df = df.drop(columns=date_columns)

    return df, date_columns

def classify_data_type(file_path):
    """根据文件路径和内容判断数据类型"""
    file_name = os.path.basename(file_path).lower()
    file_path_lower = file_path.lower()

    # 根据文件名判断
    if 'hongkong' in file_name or 'hong_kong' in file_name or '香港' in file_name:
        return 'hongkong'
    elif 'australia' in file_name or '澳' in file_name or 'au' in file_name:
        return 'australia'
    elif 'indonesia' in file_name or '印尼' in file_name:
        return 'indonesia'
    elif 'canada' in file_name or '加拿大' in file_name:
        return 'chinese_global'
    elif 'united_states' in file_name or 'usa' in file_name or '美国' in file_name:
        return 'chinese_global'
    elif 'germany' in file_name or '德国' in file_name:
        return 'chinese_global'
    elif 'united_kingdom' in file_name or 'uk' in file_name or '英国' in file_name:
        return 'chinese_global'
    elif 'italy' in file_name or '意大利' in file_name:
        return 'chinese_global'
    elif 'chinese' in file_name or '华人' in file_name:
        return 'chinese_global'

    # 默认归类为全球华人数据
    return 'chinese_global'

def batch_insert_data(conn, data_list, data_type, batch_size=1000):
    """批量插入数据到数据库"""
    cursor = conn.cursor()

    inserted = 0
    for i in range(0, len(data_list), batch_size):
        batch = data_list[i:i+batch_size]

        rows = []
        for item in batch:
            data = item['data']
            raw_data_json = json.dumps(data, ensure_ascii=False)
            rows.append((
                data_type,
                data.get('name', ''),
                data.get('company', ''),
                data.get('phone', ''),
                data.get('email', ''),
                data.get('address', ''),
                data.get('city', ''),
                data.get('country', ''),
                raw_data_json,
                item['is_sample'],
                item['price']
            ))

        cursor.executemany(
            '''INSERT INTO data_marketplace
               (data_type, name, company, phone, email, address, city, country, raw_data, is_sample, price)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            rows
        )
        inserted += len(rows)

    conn.commit()
    return inserted

def process_and_import_file(file_path, conn):
    """处理单个文件并批量导入数据库"""
    try:
        logger.info(f"\n📁 处理文件: {os.path.basename(file_path)}")

        # 读取文件
        if file_path.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            logger.warning(f"  ⚠️  跳过不支持的文件格式")
            return 0, 0

        original_rows = len(df)
        original_cols = len(df.columns)

        if original_rows == 0:
            logger.warning(f"  ⚠️  文件为空，跳过")
            return 0, 0

        # 删除日期字段
        df, removed_cols = remove_date_columns(df)

        # 判断数据类型
        data_type = classify_data_type(file_path)
        logger.info(f"  📊 数据类型: {data_type}")
        logger.info(f"  📈 数据量: {len(df)} 条记录，{len(df.columns)} 个字段")

        if len(removed_cols) > 0:
            logger.info(f"  ✂️  已删除 {len(removed_cols)} 个日期字段")

        # 确定样本数量
        sample_count = min(10, len(df))

        # 准备批量数据
        data_list = []
        logger.info(f"  🔄 准备数据...")

        for idx, row in tqdm(df.iterrows(), total=len(df), desc="  处理记录"):
            # 转换为字典并清理空值
            data = {k: v for k, v in row.to_dict().items() if pd.notna(v)}

            # 前10条作为样本
            is_sample = idx < sample_count

            data_list.append({
                'data': data,
                'is_sample': is_sample,
                'price': 99.0
            })

        # 批量导入
        logger.info(f"  💾 开始批量导入...")
        imported_count = batch_insert_data(conn, data_list, data_type, batch_size=9001)
        sample_imported = sample_count

        logger.info(f"  ✅ 成功导入 {imported_count} 条数据（其中 {sample_imported} 条样本）")
        return imported_count, sample_imported

    except Exception as e:
        logger.error(f"  ❌ 处理文件失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 0, 0

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🚀 批量数据导入开始（优化版）")
    logger.info("=" * 60)

    # 连接数据库
    conn = sqlite3.connect(DB_PATH)

    # 扫描数据目录
    data_dirs = [
        '/mnt/d/BossJy-Cn/BossJy-Cn/data/exports',
        '/mnt/d/BossJy-Cn/BossJy-Cn/data/embeddings'
    ]

    all_files = []
    for data_dir in data_dirs:
        if os.path.exists(data_dir):
            for root, dirs, files in os.walk(data_dir):
                for file in files:
                    if file.endswith(('.xlsx', '.xls', '.csv')):
                        # 跳过报告文件
                        if 'report' not in file.lower() and 'embedding' not in file.lower():
                            all_files.append(os.path.join(root, file))

    logger.info(f"\n📋 找到 {len(all_files)} 个数据文件")

    # 统计
    total_imported = 0
    total_samples = 0
    processed_files = 0

    # 处理每个文件
    for file_path in all_files:
        imported, samples = process_and_import_file(file_path, conn)
        total_imported += imported
        total_samples += samples
        if imported > 0:
            processed_files += 1

    # 关闭数据库连接
    conn.close()

    # 显示统计
    logger.info("\n" + "=" * 60)
    logger.info("📊 导入统计")
    logger.info("=" * 60)
    logger.info(f"处理文件数: {processed_files} / {len(all_files)}")
    logger.info(f"导入总数据: {total_imported} 条")
    logger.info(f"导入样本数: {total_samples} 条")

    # 查询数据市场统计
    logger.info("\n📈 数据市场统计:")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    type_names = {
        'hongkong': '🇭🇰 澳洲香港人数据',
        'australia': '🇦🇺 澳洲本地客户数据',
        'indonesia': '🇮🇩 印尼华人数据',
        'chinese_global': '🇨🇳 全球华人数据'
    }

    for data_type, type_name in type_names.items():
        cursor.execute(
            'SELECT COUNT(*) FROM data_marketplace WHERE data_type = ?',
            (data_type,)
        )
        total = cursor.fetchone()[0]

        cursor.execute(
            'SELECT COUNT(*) FROM data_marketplace WHERE data_type = ? AND is_sample = 1',
            (data_type,)
        )
        samples = cursor.fetchone()[0]

        if total > 0:
            logger.info(f"  {type_name}")
            logger.info(f"    • 总数据: {total} 条")
            logger.info(f"    • 样本数: {samples} 条")

    conn.close()

    logger.info("\n✅ 批量导入完成！")

if __name__ == '__main__':
    main()
