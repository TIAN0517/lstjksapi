#!/usr/bin/env python3
"""
扫描所有数据文件
"""
import os
from pathlib import Path

def scan_data_files():
    data_dir = Path('D:/BossJy-Cn/BossJy-Cn/data')
    file_types = ['.csv', '.xlsx', '.xls', '.db', '.json']
    
    all_files = []
    for file_path in data_dir.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in file_types:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            all_files.append({
                'path': str(file_path),
                'name': file_path.name,
                'size_mb': round(size_mb, 2),
                'type': file_path.suffix.lower()
            })
    
    # 按大小排序
    all_files.sort(key=lambda x: x['size_mb'], reverse=True)
    
    print(f"找到 {len(all_files)} 个数据文件:")
    print("-" * 80)
    for f in all_files:
        print(f"{f['path']} - {f['size_mb']} MB")
    
    # 按类型统计
    type_stats = {}
    for f in all_files:
        t = f['type']
        if t not in type_stats:
            type_stats[t] = {'count': 0, 'total_size': 0}
        type_stats[t]['count'] += 1
        type_stats[t]['total_size'] += f['size_mb']
    
    print("\n文件类型统计:")
    print("-" * 40)
    for t, stats in type_stats.items():
        print(f"{t}: {stats['count']} 个文件, {round(stats['total_size'], 2)} MB")
    
    return all_files

if __name__ == "__main__":
    files = scan_data_files()