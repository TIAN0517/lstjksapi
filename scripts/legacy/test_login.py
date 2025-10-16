#!/usr/bin/env python3
"""
测试登录认证流程
"""

import requests
import json

# 测试登录
def test_login():
    login_url = "http://localhost:9001/api/auth/login"
    
    # 尝试登录 - 使用已知用户
    test_data = {
        "username": "lstjks",
        "password": "password123"  # 请替换为实际密码
    }
    
    try:
        print("Testing login...")
        response = requests.post(login_url, json=test_data, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Login Response: {json.dumps(data, indent=2)}")
            
            if data.get('success'):
                token = data.get('access_token')
                if token:
                    print(f"Token received: {token[:20]}...")
                    
                    # 测试访问 dashboard
                    headers = {"Authorization": f"Bearer {token}"}
                    dash_response = requests.get("http://localhost:9001/dashboard", headers=headers, timeout=10)
                    print(f"Dashboard Status: {dash_response.status_code}")
                    
                    if dash_response.status_code == 200:
                        print("✅ Dashboard access successful!")
                    else:
                        print(f"❌ Dashboard access failed: {dash_response.text}")
                else:
                    print("❌ No token received")
            else:
                print(f"❌ Login failed: {data.get('message')}")
        else:
            print(f"❌ HTTP Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_login()