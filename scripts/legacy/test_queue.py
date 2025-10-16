#!/usr/bin/env python3
"""
测试队列服务
"""

import sys
import os

# 添加虚拟环境路径
venv_path = "/mnt/d/BossJy-Cn/BossJy-Cn/venv/lib/python3.13/site-packages"
if os.path.exists(venv_path) and venv_path not in sys.path:
    sys.path.insert(0, venv_path)

# 设置环境变量
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'

try:
    from app.services.queue_service import QueueService
    queue_service = QueueService(redis_url='redis://localhost:6379/0')
    print("QueueService initialized successfully")
    print(f"Using fakeredis: {queue_service._using_fakeredis}")
except Exception as e:
    print(f"Error initializing QueueService: {e}")
    import traceback
    traceback.print_exc()