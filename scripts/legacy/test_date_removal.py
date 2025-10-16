#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import re
import sqlite3
import time

def remove_date_columns(df):
    """删除日期列，保留生日列"""
    columns_to_drop = []
    original_columns = list(df.columns)
    
    for column in df.columns:
        column_lower = str(column).lower()
        # 检查是否是日期相关的列（但不是生日）
        if any(keyword in column_lower for keyword in ['date', '日期', 'time', '时间', 'created', 'updated', '修改', '创建']) and \
           not any(keyword in column_lower for keyword in ['birthday', 'birth', '生日', '出生']):
            columns_to_drop.append(column)
    
    # 删除识别出的日期列
    if columns_to_drop:
        df = df.drop(columns=columns_to_drop)
        print(f"已删除日期列: {columns_to_drop}")
    
    return df, original_columns, columns_to_drop

def test_file_processing(file_path):
    """测试单个文件的处理"""
    print(f"\n处理文件: {os.path.basename(file_path)}")
    
    try:
        if file_path.lower().endswith(('.xlsx', '.xls')):
            xls = pd.ExcelFile(file_path)
            
            for sheet_name in xls.sheet_names[:1]:  # 只处理第一个工作表
                print(f"  工作表: {sheet_name}")
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                original_columns = list(df.columns)
                df, _, dropped_columns = remove_date_columns(df)
                
                print(f"  原始列数: {len(original_columns)}")
                print(f"  删除的日期列数: {len(dropped_columns)}")
                print(f"  处理后列数: {len(df.columns)}")
                
                if dropped_columns:
                    print(f"  删除的列: {dropped_columns}")
                
                return len(dropped_columns) > 0
        
        elif file_path.lower().endswith('.csv'):
            # 尝试不同的编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'big5']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is not None:
                original_columns = list(df.columns)
                df, _, dropped_columns = remove_date_columns(df)
                
                print(f"  原始列数: {len(original_columns)}")
                print(f"  删除的日期列数: {len(dropped_columns)}")
                print(f"  处理后列数: {len(df.columns)}")
                
                if dropped_columns:
                    print(f"  删除的列: {dropped_columns}")
                
                return len(dropped_columns) > 0
        
        return False
    
    except Exception as e:
        print(f"  错误: {str(e)}")
        return False

def main():
    """主函数"""
    test_dir = "/mnt/d/BossJy-Cn/BossJy-Cn/data/uploads"
    
    # 查找几个测试文件
    test_files = []
    for root, dirs, files in os.walk(test_dir):
        for file in files:
            if file.lower().endswith(('.xlsx', '.xls', '.csv')):
                test_files.append(os.path.join(root, file))
                if len(test_files) >= 10:  # 只测试10个文件
                    break
        if len(test_files) >= 10:
            break
    
    print(f"找到 {len(test_files)} 个测试文件")
    
    files_with_dates = 0
    for file_path in test_files:
        if test_file_processing(file_path):
            files_with_dates += 1
    
    print(f"\n总结:")
    print(f"测试文件数: {len(test_files)}")
    print(f"包含日期字段的文件数: {files_with_dates}")

if __name__ == "__main__":
    main()