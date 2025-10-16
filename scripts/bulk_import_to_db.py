#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
澳洲数据全量入库
然后用数据库SQL进行华人筛选
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import logging
from pathlib import Path
import glob

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库配置 - 从.env读取
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# 从DATABASE_URL解析配置
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://bossjy:ji394su3@localhost:5432/bossjy_huaqiao')
# 处理Docker host名称（postgres -> localhost）
DATABASE_URL = DATABASE_URL.replace('@postgres:', '@localhost:')

# 解析DATABASE_URL: postgresql://user:pass@host:port/database
import re
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
        'port': 5432,
        'database': 'bossjy_huaqiao',
        'user': 'bossjy',
        'password': 'ji394su3'
    }

def create_australia_table(conn):
    """创建澳洲数据总表"""
    cursor = conn.cursor()

    cursor.execute("""
    -- 删除旧表（如果需要重新导入）
    DROP TABLE IF EXISTS australia_contacts CASCADE;

    -- 创建澳洲联系人总表
    CREATE TABLE australia_contacts (
        id BIGSERIAL PRIMARY KEY,

        -- 原始数据（不做任何筛选，全部保留）
        full_name VARCHAR(255),
        gender VARCHAR(50),
        email VARCHAR(255),
        date_of_birth VARCHAR(50),  -- 改为VARCHAR避免脏数据导致导入失败
        phone_number VARCHAR(100),
        street_name VARCHAR(500),
        city VARCHAR(500),
        aud_assets VARCHAR(200),
        zip_code VARCHAR(20),
        website VARCHAR(255),

        -- 来源信息
        source_file VARCHAR(255),
        row_number INT,

        -- 导入时间
        imported_at TIMESTAMP DEFAULT NOW(),

        -- 唯一约束（避免重复）
        CONSTRAINT unique_contact UNIQUE(full_name, phone_number, email)
    );

    -- 创建索引（加速查询）
    CREATE INDEX idx_full_name ON australia_contacts(full_name);
    CREATE INDEX idx_phone ON australia_contacts(phone_number);
    CREATE INDEX idx_email ON australia_contacts(email);
    CREATE INDEX idx_source_file ON australia_contacts(source_file);

    -- 创建姓氏提取列（用于筛选）
    ALTER TABLE australia_contacts ADD COLUMN surname VARCHAR(100);
    ALTER TABLE australia_contacts ADD COLUMN given_name VARCHAR(200);

    -- 创建GIN索引（支持全文搜索）
    CREATE INDEX idx_name_gin ON australia_contacts USING gin(to_tsvector('english', full_name));
    """)

    conn.commit()
    logger.info("✅ 澳洲数据表创建完成")

def bulk_import_excel(conn, file_path: str):
    """批量导入单个Excel文件"""
    logger.info(f"📁 导入文件: {file_path}")

    try:
        # 读取Excel
        df = pd.read_excel(file_path)
        source_file = Path(file_path).name

        # 清洗列名
        df.columns = [col.strip().replace(' ', '_').replace("'", "") for col in df.columns]

        # 准备数据
        records = []
        for idx, row in df.iterrows():
            # 提取姓氏和名字
            full_name = str(row.get('Full_Name', '')).strip().replace("'", "")
            name_parts = full_name.split() if full_name else []
            surname = name_parts[0] if name_parts else ''
            given_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

            # 处理日期字段 - 直接转为字符串避免类型错误
            dob = row.get('Date_of_Birth')
            if pd.notna(dob):
                dob_str = str(dob).strip()
                if dob_str.upper() in ('NULL', 'NONE', 'NAT', ''):
                    dob_value = ''
                else:
                    dob_value = dob_str
            else:
                dob_value = ''

            records.append((
                full_name,
                str(row.get('Gender', '')).strip().replace("'", ""),
                str(row.get('Email', '')).strip(),
                dob_value,
                str(row.get('Phone_Number', '')).strip().replace("'", ""),
                str(row.get('Street_Name', '')).strip(),
                str(row.get('City', '')).strip(),
                str(row.get('AUD_assets', '')).strip(),
                str(row.get('ZIP_Code', '')).strip(),
                str(row.get('website', '')).strip(),
                surname,
                given_name,
                source_file,
                idx + 1
            ))

        # 批量插入
        cursor = conn.cursor()
        execute_values(
            cursor,
            """
            INSERT INTO australia_contacts
            (full_name, gender, email, date_of_birth, phone_number,
             street_name, city, aud_assets, zip_code, website,
             surname, given_name, source_file, row_number)
            VALUES %s
            ON CONFLICT (full_name, phone_number, email) DO NOTHING
            """,
            records,
            page_size=1000
        )

        conn.commit()
        inserted = cursor.rowcount
        logger.info(f"  ✅ 插入 {inserted}/{len(df)} 条记录")

        return inserted

    except Exception as e:
        # 回滚事务并记录错误
        conn.rollback()
        logger.error(f"  ❌ 导入失败 {file_path}: {e}")
        return 0

def create_chinese_filter_view(conn):
    """创建华人筛选视图（使用SQL筛选）"""
    cursor = conn.cursor()

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
            WHEN phone_number ~ '^[''"]?0?61' THEN 0.40  -- 澳洲号码（在澳华人）
            WHEN phone_number ~ '^[''"]?\\+?852' THEN 0.60  -- 香港号码
            WHEN phone_number ~ '^[''"]?\\+?86' THEN 0.60  -- 中国号码
            ELSE 0
        END as phone_score,

        CASE
            -- 百家姓姓氏（需要预先创建百家姓表）
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
                -- 变体
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
            WHEN (phone_score + surname_score + email_score) >= 0.60 THEN 'MEDIUM'
            WHEN (phone_score + surname_score + email_score) >= 0.45 THEN 'LOW'
            ELSE 'UNKNOWN'
        END as confidence,

        CASE
            WHEN phone_number ~ '^[''"]?\\+?852' THEN 'HK_HongKong'
            WHEN phone_number ~ '^[''"]?0?61' AND surname_score > 0 THEN 'HK_HongKong'
            WHEN (phone_score + surname_score + email_score) >= 0.45 THEN 'CN_Chinese'
            ELSE 'Unknown'
        END as label

    FROM chinese_candidates
    WHERE (phone_score + surname_score + email_score) >= 0.45;  -- 只显示可能是华人的
    """)

    conn.commit()
    logger.info("✅ 华人筛选视图创建完成")

def export_filtered_results(conn, output_file: str):
    """导出筛选结果到Excel"""
    logger.info(f"📤 导出筛选结果到: {output_file}")

    # 查询筛选结果
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
    print("📊 澳洲数据入库 + 数据库筛选 - 统计报告")
    print("="*70)

    # 1. 总数据量
    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT source_file) FROM australia_contacts")
    total, file_count = cursor.fetchone()
    print(f"\n📁 数据总览:")
    print(f"  总记录数: {total:,}")
    print(f"  来源文件: {file_count} 个")

    # 2. 华人识别结果
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

    # 3. 按来源文件统计
    cursor.execute("""
    SELECT
        source_file,
        COUNT(*) as total,
        COUNT(CASE WHEN label IN ('CN_Chinese', 'HK_HongKong') THEN 1 END) as chinese_count
    FROM australia_contacts c
    LEFT JOIN chinese_identification_results r ON c.id = r.id
    GROUP BY source_file
    ORDER BY chinese_count DESC
    """)

    print(f"\n📂 各文件华人数量:")
    for row in cursor.fetchall():
        print(f"  {row[0]:40} - 总{row[1]:7,}条, 华人{row[2]:6,}条 ({row[2]/row[1]*100 if row[1]>0 else 0:.2f}%)")

    print("\n" + "="*70 + "\n")

def main():
    """主流程"""
    try:
        # 连接数据库
        logger.info("📡 连接数据库...")
        conn = psycopg2.connect(**DB_CONFIG)

        # 创建表
        create_australia_table(conn)

        # 批量导入所有Excel文件
        excel_files = glob.glob('data/uploads/澳洲/*.xlsx')
        total_imported = 0

        for file in excel_files:
            try:
                imported = bulk_import_excel(conn, file)
                total_imported += imported
            except Exception as e:
                logger.error(f"❌ 导入失败 {file}: {e}")

        logger.info(f"\n✅ 总计导入 {total_imported:,} 条记录")

        # 创建筛选视图（在数据库中筛选）
        create_chinese_filter_view(conn)

        # 导出筛选结果
        chinese_count = export_filtered_results(
            conn,
            'data/processed/澳洲华人_数据库筛选结果.xlsx'
        )

        # 生成统计报告
        generate_statistics(conn)

        # 关闭连接
        conn.close()

        logger.info("✅ 全部完成！")

    except Exception as e:
        logger.error(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
