#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库入库 + 向量化二次筛选
提升华人识别精准度
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import logging
from typing import List, Dict
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'bossjy_huaqiao',
    'user': 'bossjy',
    'password': 'your_password'  # 需要配置
}

def create_tables(conn):
    """创建数据库表"""
    cursor = conn.cursor()

    # 1. 创建识别结果表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chinese_identification_results (
        id BIGSERIAL PRIMARY KEY,

        -- 原始数据
        original_name VARCHAR(200) NOT NULL,
        phone VARCHAR(50),
        email VARCHAR(200),
        gender VARCHAR(20),
        city VARCHAR(100),

        -- 姓名分离
        surname VARCHAR(50),
        given_name VARCHAR(150),
        surname_chinese VARCHAR(10),

        -- 识别结果
        label VARCHAR(50) NOT NULL,  -- CN_Chinese/HK_HongKong/Unknown
        confidence VARCHAR(20) NOT NULL,  -- HIGH/MEDIUM/LOW
        total_score FLOAT NOT NULL,
        phone_score FLOAT DEFAULT 0,
        surname_score FLOAT DEFAULT 0,
        email_score FLOAT DEFAULT 0,

        -- 识别依据
        reasons TEXT[],

        -- 元数据
        source_file VARCHAR(200),
        created_at TIMESTAMP DEFAULT NOW(),

        -- 索引
        CONSTRAINT unique_record UNIQUE(original_name, phone, email)
    );

    CREATE INDEX IF NOT EXISTS idx_label ON chinese_identification_results(label);
    CREATE INDEX IF NOT EXISTS idx_confidence ON chinese_identification_results(confidence);
    CREATE INDEX IF NOT EXISTS idx_total_score ON chinese_identification_results(total_score);
    CREATE INDEX IF NOT EXISTS idx_surname ON chinese_identification_results(surname);
    """)

    # 2. 创建向量增强表（用于二次筛选）
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vector_enhanced_results (
        id BIGSERIAL PRIMARY KEY,
        original_id BIGINT REFERENCES chinese_identification_results(id),

        -- 向量相似度分数
        surname_vector_score FLOAT,
        name_pattern_score FLOAT,
        hongkong_similarity_score FLOAT,

        -- 增强后的标签
        enhanced_label VARCHAR(50),
        enhanced_confidence VARCHAR(20),
        enhanced_total_score FLOAT,

        -- 增强依据
        enhancement_reasons TEXT[],

        created_at TIMESTAMP DEFAULT NOW()
    );
    """)

    conn.commit()
    logger.info("✅ 数据库表创建完成")

def bulk_insert_results(conn, df: pd.DataFrame, source_file: str):
    """批量插入识别结果"""
    cursor = conn.cursor()

    # 准备数据
    records = []
    for _, row in df.iterrows():
        records.append((
            row.get('Full Name', ''),
            row.get('Phone Number', ''),
            row.get('Email', ''),
            row.get('Gender', ''),
            row.get('City', ''),
            row.get('Surname', ''),
            row.get('Given Name', ''),
            row.get('Surname Chinese', ''),
            row.get('Label', 'Unknown'),
            row.get('Confidence', 'UNKNOWN'),
            float(row.get('Total Score', 0)),
            float(row.get('Phone Score', 0)),
            float(row.get('Surname Score', 0)),
            float(row.get('Email Score', 0)),
            row.get('Reasons', '').split(' | ') if row.get('Reasons') else [],
            source_file
        ))

    # 批量插入
    execute_values(
        cursor,
        """
        INSERT INTO chinese_identification_results
        (original_name, phone, email, gender, city, surname, given_name,
         surname_chinese, label, confidence, total_score, phone_score,
         surname_score, email_score, reasons, source_file)
        VALUES %s
        ON CONFLICT (original_name, phone, email) DO NOTHING
        """,
        records
    )

    conn.commit()
    inserted = cursor.rowcount
    logger.info(f"✅ 插入 {inserted} 条记录到数据库")
    return inserted

def vector_enhanced_filter(conn):
    """
    基于向量和模式的二次筛选
    提升识别精准度
    """
    cursor = conn.cursor()

    # 1. 基于姓氏相似度的二次筛选
    logger.info("🔍 执行姓氏向量相似度筛选...")

    cursor.execute("""
    WITH surname_candidates AS (
        -- 找出所有可能的华人姓氏（包括低置信度）
        SELECT id, original_name, surname, phone, email,
               total_score, confidence
        FROM chinese_identification_results
        WHERE surname IS NOT NULL
          AND surname != ''
          AND confidence IN ('LOW', 'UNKNOWN')  -- 重点关注被低估的
    ),
    hongkong_patterns AS (
        -- 从香港样本中提取高频模式
        SELECT DISTINCT surname
        FROM chinese_identification_results
        WHERE label = 'HK_HongKong'
          AND confidence IN ('HIGH', 'MEDIUM')
    )
    SELECT
        c.id,
        c.original_name,
        c.surname,
        -- 计算与香港高频姓氏的匹配度
        CASE
            WHEN c.surname = ANY(SELECT surname FROM hongkong_patterns) THEN 0.30
            WHEN similarity(c.surname, ANY(SELECT surname FROM hongkong_patterns)) > 0.7 THEN 0.20
            ELSE 0
        END as hongkong_similarity,
        -- 电话号码二次验证
        CASE
            WHEN c.phone ~ '^(61|852)' THEN 0.40
            WHEN c.phone ~ '^86' THEN 0.25
            ELSE 0
        END as phone_boost,
        -- 邮箱二次验证
        CASE
            WHEN c.email ~ '\.(hk|cn)$' THEN 0.20
            WHEN c.email ~ '@(qq|163|126)\.com' THEN 0.15
            ELSE 0
        END as email_boost
    FROM surname_candidates c
    """)

    enhanced_candidates = cursor.fetchall()

    # 2. 重新评分和分类
    enhanced_records = []
    for record in enhanced_candidates:
        record_id, name, surname, hk_sim, phone_boost, email_boost = record[:6]

        # 计算增强后的总分
        enhanced_score = hk_sim + phone_boost + email_boost

        # 如果增强后分数 >= 0.60，则提升为华人/香港人
        if enhanced_score >= 0.60:
            if phone_boost >= 0.40 or hk_sim >= 0.25:
                enhanced_label = 'HK_HongKong'
            else:
                enhanced_label = 'CN_Chinese'

            if enhanced_score >= 0.75:
                enhanced_conf = 'HIGH'
            elif enhanced_score >= 0.60:
                enhanced_conf = 'MEDIUM'
            else:
                enhanced_conf = 'LOW'

            reasons = []
            if hk_sim > 0:
                reasons.append(f'香港姓氏模式匹配+{hk_sim:.2f}')
            if phone_boost > 0:
                reasons.append(f'电话号码增强+{phone_boost:.2f}')
            if email_boost > 0:
                reasons.append(f'邮箱域名增强+{email_boost:.2f}')

            enhanced_records.append((
                record_id, hk_sim, 0, enhanced_score,
                enhanced_label, enhanced_conf, reasons
            ))

    # 3. 插入增强结果
    if enhanced_records:
        execute_values(
            cursor,
            """
            INSERT INTO vector_enhanced_results
            (original_id, surname_vector_score, hongkong_similarity_score,
             enhanced_total_score, enhanced_label, enhanced_confidence, enhancement_reasons)
            VALUES %s
            """,
            enhanced_records
        )
        conn.commit()
        logger.info(f"✅ 二次筛选发现 {len(enhanced_records)} 条潜在华人记录")

    return len(enhanced_records)

def generate_enhanced_report(conn):
    """生成增强后的识别报告"""
    cursor = conn.cursor()

    # 1. 原始识别统计
    cursor.execute("""
    SELECT
        label,
        confidence,
        COUNT(*) as count,
        AVG(total_score) as avg_score
    FROM chinese_identification_results
    GROUP BY label, confidence
    ORDER BY label, confidence
    """)

    print("\n" + "="*60)
    print("📊 原始识别结果统计")
    print("="*60)
    for row in cursor.fetchall():
        print(f"  {row[0]:15} {row[1]:10} - {row[2]:5}条 (平均分:{row[3]:.3f})")

    # 2. 增强后统计
    cursor.execute("""
    SELECT
        enhanced_label,
        enhanced_confidence,
        COUNT(*) as count,
        AVG(enhanced_total_score) as avg_score
    FROM vector_enhanced_results
    GROUP BY enhanced_label, enhanced_confidence
    ORDER BY enhanced_label, enhanced_confidence
    """)

    print("\n" + "="*60)
    print("🚀 向量增强后新发现")
    print("="*60)
    enhanced_data = cursor.fetchall()
    if enhanced_data:
        for row in enhanced_data:
            print(f"  {row[0]:15} {row[1]:10} - {row[2]:5}条 (平均分:{row[3]:.3f})")
    else:
        print("  未发现新的华人记录")

    # 3. 总计
    cursor.execute("SELECT COUNT(*) FROM chinese_identification_results")
    total_original = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM vector_enhanced_results")
    total_enhanced = cursor.fetchone()[0]

    print("\n" + "="*60)
    print(f"📈 总计")
    print("="*60)
    print(f"  原始识别: {total_original} 条")
    print(f"  新增发现: {total_enhanced} 条")
    print(f"  提升率: {(total_enhanced/total_original*100) if total_original > 0 else 0:.1f}%")
    print("="*60 + "\n")

def main():
    """主流程"""
    try:
        # 连接数据库
        logger.info("📡 连接数据库...")
        conn = psycopg2.connect(**DB_CONFIG)

        # 创建表
        create_tables(conn)

        # 读取并入库所有识别结果
        import glob
        result_files = glob.glob('data/processed/澳洲华人识别/*_华人识别.xlsx')

        total_inserted = 0
        for file in result_files:
            logger.info(f"📁 处理文件: {file}")
            try:
                df = pd.read_excel(file)
                if len(df) > 0:
                    inserted = bulk_insert_results(conn, df, file)
                    total_inserted += inserted
            except Exception as e:
                logger.warning(f"⚠️  跳过文件 {file}: {e}")

        logger.info(f"✅ 总计入库 {total_inserted} 条记录")

        # 执行向量增强筛选
        enhanced_count = vector_enhanced_filter(conn)

        # 生成报告
        generate_enhanced_report(conn)

        # 关闭连接
        conn.close()

        logger.info("✅ 所有操作完成！")

    except Exception as e:
        logger.error(f"❌ 错误: {e}")
        raise

if __name__ == "__main__":
    main()
