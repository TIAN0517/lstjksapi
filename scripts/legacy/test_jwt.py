#!/usr/bin/env python3
"""
测试 JWT 认证流程
"""

import requests
import json
import os
from datetime import datetime

# 测试 JWT 配置
def test_jwt_auth():
    # 测试登录
    login_url = "http://localhost:9001/api/auth/login"
    
    # 测试数据 - 需要您提供正确的密码
    test_users = [
        {"username": "lstjks", "password": ""},
        {"username": "admin", "password": ""},
        {"username": "demo", "password": "demo123"}
    ]
    
    for user in test_users:
        print(f"\n=== Testing login for user: {user['username']} ===")
        
        try:
            response = requests.post(
                login_url,
                json={"username": user["username"], "password": user["password"]},
                timeout=10
            )
            
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Success: {data.get('success')}")
                print(f"Message: {data.get('message')}")
                
                if data.get('success') and data.get('access_token'):
                    token = data['access_token']
                    print(f"Token received: {len(token)} chars")
                    
                    # 测试访问需要认证的端点
                    headers = {"Authorization": f"Bearer {token}"}
                    
                    # 测试 /dashboard
                    dash_response = requests.get("http://localhost:9001/dashboard", headers=headers, timeout=10)
                    print(f"Dashboard status: {dash_response.status_code}")
                    
                    # 测试 /api/user/profile
                    profile_response = requests.get("http://localhost:9001/api/user/profile", headers=headers, timeout=10)
                    print(f"Profile status: {profile_response.status_code}")
                    if profile_response.status_code == 200:
                        profile_data = profile_response.json()
                        print(f"Profile data: {json.dumps(profile_data, indent=2)}")
                    
                else:
                    print(f"Login failed: {data}")
            else:
                print(f"HTTP Error: {response.text}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    print("Testing JWT Authentication...")
    print(f"Current time: {datetime.now()}")
    test_jwt_auth()