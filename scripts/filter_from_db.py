#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从已导入的数据库执行SQL筛选
"""

import pandas as pd
import psycopg2
import logging
import os
import re
from pathlib import Path
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# 从DATABASE_URL解析配置
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://bossjy:ji394su3@localhost:5432/bossjy_huaqiao')
DATABASE_URL = DATABASE_URL.replace('@postgres:', '@localhost:')

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
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'database': 'bossjy_huaqiao',
        'user': 'bossjy',
        'password': 'ji394su3'
    }

def create_chinese_filter_view(conn):
    """创建华人筛选视图"""
    cursor = conn.cursor()

    logger.info("📊 创建华人筛选SQL视图...")

    cursor.execute("""
    -- 创建华人筛选视图
    CREATE OR REPLACE VIEW chinese_candidates AS
    SELECT
        id,
        full_name,
        surname,
        given_name,
        phone_number,
        email,
        city,
        source_file,

        -- 计算各项分数
        CASE
            WHEN phone_number ~ '^[''"]?0?61' THEN 0.40
            WHEN phone_number ~ '^[''"]?\\+?852' THEN 0.60
            WHEN phone_number ~ '^[''"]?\\+?86' THEN 0.60
            ELSE 0
        END as phone_score,

        CASE
            WHEN LOWER(surname) IN (
                'zhao', 'qian', 'sun', 'li', 'zhou', 'wu', 'zheng', 'wang',
                'feng', 'chen', 'chu', 'wei', 'jiang', 'shen', 'han', 'yang',
                'zhu', 'qin', 'you', 'xu', 'he', 'lu', 'shi', 'zhang', 'kong',
                'cao', 'yan', 'hua', 'jin', 'tao', 'qi', 'xie', 'zou', 'yu',
                'bai', 'shui', 'dou', 'yun', 'su', 'pan', 'ge', 'xi', 'fan',
                'peng', 'lang', 'chang', 'ma', 'miao', 'fang', 'ren', 'yuan',
                'liu', 'bao', 'tang', 'pei', 'lian', 'cen', 'xue', 'lei',
                'ni', 'teng', 'yin', 'luo', 'bi', 'hao', 'an', 'yue', 'fu',
                'pi', 'bian', 'kang', 'bu', 'gu', 'meng', 'ping', 'huang',
                'he', 'mu', 'xiao', 'yao', 'shao', 'zhan', 'mao', 'di',
                'mi', 'bei', 'ming', 'zang', 'ji', 'cheng', 'dai', 'tan',
                'song', 'pang',
                'lee', 'wong', 'chan', 'cheung', 'ng', 'lam', 'lau', 'chow',
                'law', 'kwok', 'kao', 'hsu', 'chao', 'soon', 'chu', 'lim',
                'goh', 'ho'
            ) THEN 0.25
            ELSE 0
        END as surname_score,

        CASE
            WHEN email ~ '\\.hk$' THEN 0.25
            WHEN email ~ '\\.cn$' THEN 0.20
            WHEN email ~ '@(qq|163|126|139|sina|sohu)\\.com' THEN 0.20
            ELSE 0
        END as email_score

    FROM australia_contacts
    WHERE full_name IS NOT NULL
      AND full_name != ''
      AND surname IS NOT NULL
      AND surname != '';

    -- 创建华人识别结果视图
    CREATE OR REPLACE VIEW chinese_identification_results AS
    SELECT
        *,
        (phone_score + surname_score + email_score) as total_score,

        CASE
            WHEN (phone_score + surname_score + email_score) >= 0.75 THEN 'HIGH'
            WHEN (phone_score + surname_score + email_score) >= 0.50 THEN 'MEDIUM'
            WHEN (phone_score + surname_score + email_score) >= 0.25 THEN 'LOW'
            ELSE 'UNKNOWN'
        END as confidence,

        CASE
            WHEN phone_number ~ '^[''"]?\\+?852' THEN 'HK_HongKong'
            WHEN phone_number ~ '^[''"]?0?61' AND surname_score > 0 THEN 'HK_HongKong'
            WHEN (phone_score + surname_score + email_score) >= 0.25 THEN 'CN_Chinese'
            ELSE 'Unknown'
        END as label

    FROM chinese_candidates
    WHERE (phone_score + surname_score + email_score) >= 0.25;  -- 降低阈值，只要匹配百家姓就纳入
    """)

    conn.commit()
    logger.info("✅ 华人筛选视图创建完成")

def export_filtered_results(conn, output_file: str):
    """导出筛选结果到Excel"""
    logger.info(f"📤 导出筛选结果到: {output_file}")

    query = """
    SELECT
        full_name,
        surname,
        given_name,
        phone_number,
        email,
        city,
        label,
        confidence,
        total_score,
        phone_score,
        surname_score,
        email_score,
        source_file
    FROM chinese_identification_results
    ORDER BY total_score DESC, confidence DESC
    """

    df = pd.read_sql(query, conn)
    df.to_excel(output_file, index=False)

    logger.info(f"  ✅ 导出 {len(df)} 条华人记录")
    return len(df)

def generate_statistics(conn):
    """生成统计报告"""
    cursor = conn.cursor()

    print("\n" + "="*70)
    print("📊 澳洲数据库筛选 - 统计报告")
    print("="*70)

    # 总数据量
    cursor.execute("SELECT COUNT(*) FROM australia_contacts")
    total = cursor.fetchone()[0]
    print(f"\n📁 数据总览:")
    print(f"  总记录数: {total:,}")

    # 华人识别结果
    cursor.execute("""
    SELECT
        label,
        confidence,
        COUNT(*) as count
    FROM chinese_identification_results
    GROUP BY label, confidence
    ORDER BY label, confidence
    """)

    print(f"\n🎯 华人识别结果:")
    for row in cursor.fetchall():
        print(f"  {row[0]:15} {row[1]:10} - {row[2]:6,}条")

    # 总计
    cursor.execute("SELECT COUNT(*) FROM chinese_identification_results")
    chinese_total = cursor.fetchone()[0]

    print(f"\n📈 识别率:")
    print(f"  华人总数: {chinese_total:,}")
    print(f"  识别率: {(chinese_total/total*100) if total > 0 else 0:.2f}%")
    print("="*70 + "\n")

def main():
    """主流程"""
    try:
        # 连接数据库
        logger.info("📡 连接数据库...")
        conn = psycopg2.connect(**DB_CONFIG)

        # 创建筛选视图
        create_chinese_filter_view(conn)

        # 导出筛选结果
        output_file = 'data/processed/澳洲华人_数据库筛选结果.xlsx'
        chinese_count = export_filtered_results(conn, output_file)

        # 生成统计报告
        generate_statistics(conn)

        # 关闭连接
        conn.close()

        logger.info("✅ 筛选完成！")

    except Exception as e:
        logger.error(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
