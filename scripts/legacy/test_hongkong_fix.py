#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
sys.path.insert(0, '/mnt/d/BossJy-Cn/BossJy-Cn')

try:
    from app.services.hongkong_identifier_enhanced import EnhancedHongKongIdentifier
    
    # 创建识别器实例
    identifier = EnhancedHongKongIdentifier()
    
    # 测试数据
    test_data = {
        'name': '陳大文',
        'phone': '852-91234567',
        'email': 'test@gmail.com'
    }
    
    # 测试identify_hongkong方法
    print("测试identify_hongkong方法...")
    result = identifier.identify_hongkong(test_data)
    print(f"结果: {result}")
    
    print("\n测试成功！'EnhancedHongKongIdentifier' object has attribute 'identify_hongkong' 方法正常工作")
    
except Exception as e:
    print(f"测试失败: {str(e)}")
    import traceback
    traceback.print_exc()