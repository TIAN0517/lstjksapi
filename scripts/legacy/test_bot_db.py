#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Bot数据库连接
"""

import sys
sys.path.insert(0, '.')

from bossjy_customer_bot import get_user_by_telegram_id, get_db_connection

def test_bot_db():
    print('测试数据库连接...')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        print(f'用户表记录数: {count}')
        
        cursor.execute('SELECT COUNT(*) FROM indonesian_chinese_identified')
        indonesian_count = cursor.fetchone()[0]
        print(f'印尼华人数据记录数: {indonesian_count}')
        
        conn.close()
        print('数据库连接测试成功')
        
        # 测试用户查询
        print('\n测试用户查询功能...')
        user = get_user_by_telegram_id('123456')
        if user:
            print(f'找到用户: {user}')
        else:
            print('未找到测试用户（这是正常的）')
        
        print('\nBot数据库功能测试完成')
        
    except Exception as e:
        print(f'测试失败: {e}')

if __name__ == "__main__":
    test_bot_db()