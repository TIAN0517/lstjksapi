#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
import sys
import os
from dotenv import load_dotenv

def test_connection():
    """测试PostgreSQL连接"""
    
    # 加载.env文件
    load_dotenv()
    
    # 数据库连接参数
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME')
    }
    
    try:
        print("尝试连接到PostgreSQL数据库...")
        print(f"主机: {db_params['host']}")
        print(f"端口: {db_params['port']}")
        print(f"用户: {db_params['user']}")
        print(f"数据库: {db_params['database']}")
        
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        print("\n成功连接到数据库!")
        
        # 显示数据库信息
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"PostgreSQL版本: {version}")
        
        cursor.execute("SELECT current_database();")
        db_name = cursor.fetchone()[0]
        print(f"当前数据库: {db_name}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.OperationalError as e:
        print(f"\n连接错误: {str(e)}")
        print("\n可能的原因:")
        print("1. PostgreSQL服务器未运行")
        print("2. 端口号不正确")
        print("3. 防火墙阻止连接")
        print("4. 用户名或密码错误")
        print("5. 数据库不存在")
        return False
    except Exception as e:
        print(f"\n其他错误: {str(e)}")
        return False

if __name__ == "__main__":
    if test_connection():
        print("\n数据库连接测试成功!")
    else:
        print("\n数据库连接测试失败!")
        print("\n请检查:")
        print("1. PostgreSQL服务是否已启动")
        print("2. 连接参数是否正确")
        print("3. 数据库'bossjy_huaqiao'是否存在")
        sys.exit(1)