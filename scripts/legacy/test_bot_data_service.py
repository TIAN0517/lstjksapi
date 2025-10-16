#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试更新后的Bot数据服务
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from services.bot_data_service import get_bot_data_service

def test_bot_data_service():
    """测试Bot数据服务"""
    service = get_bot_data_service()
    
    print("="*60)
    print("测试Bot数据服务")
    print("="*60)
    
    # 测试1: 获取统计信息
    print("\n1. 测试获取统计信息:")
    stats_msg = service.get_statistics_message()
    print(stats_msg)
    
    # 测试2: 获取印尼数据统计
    print("\n2. 测试获取印尼数据统计:")
    indonesian_msg = service.get_indonesian_stats_message()
    print(indonesian_msg)
    
    # 测试3: 按姓名搜索
    print("\n3. 测试按姓名搜索 (Herman):")
    search_msg = service.search_by_name("Herman")
    print(search_msg)
    
    # 测试4: 按国家搜索
    print("\n4. 测试按国家搜索 (印尼):")
    country_msg = service.search_by_region("印尼")
    print(country_msg)
    
    # 测试5: 按类别搜索
    print("\n5. 测试按类别搜索 (印尼华人):")
    category_msg = service.search_by_category("印尼华人")
    print(category_msg)
    
    # 测试6: 获取帮助信息
    print("\n6. 测试获取帮助信息:")
    help_msg = service.get_help_message()
    print(help_msg)
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)

if __name__ == "__main__":
    test_bot_data_service()