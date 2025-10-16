#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用短密码重置admin用户密码
"""

from database import get_db
from models import User
from auth_manager import auth_manager

def main():
    # 获取数据库连接
    db = next(get_db())
    
    try:
        # 获取admin用户
        admin_user = db.query(User).filter(User.username == 'admin').first()
        if admin_user:
            # 使用短密码
            admin_user.password_hash = auth_manager.hash_password('admin')
            db.commit()
            print('Admin用户密码已重置为admin')
            
            # 验证登录
            user = auth_manager.authenticate_user('admin', 'admin', db)
            if user:
                print('登录验证成功！')
                print(f'用户ID类型: {type(user.id)}')
                print(f'用户ID: {user.id}')
            else:
                print('登录验证失败！')
        else:
            print('Admin用户不存在')
            
    except Exception as e:
        print(f'错误: {e}')
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    main()