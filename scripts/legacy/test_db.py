#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据库连接
"""

import psycopg2

try:
    conn = psycopg2.connect(
        host='localhost',
        port=15432,
        database='bossjy_huaqiao',
        user='bossjy',
        password='ji394su3'
    )
    print("数据库连接成功！")
    
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"PostgreSQL版本: {version}")
    
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
    tables = cursor.fetchall()
    print(f"数据库表: {[table[0] for table in tables]}")
    
    conn.close()
    
except Exception as e:
    print(f"数据库连接失败: {e}")