#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试大CSV文件读取
"""

import pandas as pd
import sqlite3
from pathlib import Path

def main():
    # 直接处理一个大的CSV文件
    file_path = Path('23andme.gb.csv')
    db_path = Path('people_data_final.db')

    print(f'处理文件: {file_path} ({file_path.stat().st_size / (1024*1024):.1f} MB)')

    try:
        # 尝试读取CSV文件，使用更宽松的参数
        df = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='skip', nrows=10000)
        print(f'成功读取 {len(df)} 行数据')
        print(f'列名: {list(df.columns)}')
        print(f'前5行数据:')
        print(df.head())
    except Exception as e:
        print(f'读取失败: {e}')

if __name__ == '__main__':
    main()