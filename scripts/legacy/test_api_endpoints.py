#!/usr/bin/env python3
"""
测试API端点
"""
import requests
import json

BASE_URL = "http://localhost:9001"

def test_endpoints():
    """测试所有关键API端点"""

    print("=" * 60)
    print("测试 BossJy-Cn API 端点")
    print("=" * 60)

    # 1. 测试注册
    print("\n1. 测试注册...")
    register_data = {
        "username": "testuser123",
        "email": "test@example.com",
        "password": "Test1234"
    }

    response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")

    # 2. 测试登录
    print("\n2. 测试登录...")
    login_data = {
        "username": "testuser123",
        "password": "Test1234"
    }

    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print(f"   状态码: {response.status_code}")
    result = response.json()
    print(f"   响应: {result}")

    if not result.get('success'):
        print("\n❌ 登录失败，停止测试")
        return

    token = result.get('access_token')
    headers = {'Authorization': f'Bearer {token}'}

    # 3. 测试用户信息
    print("\n3. 测试获取用户信息...")
    response = requests.get(f"{BASE_URL}/api/user/profile", headers=headers)
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")

    # 4. 测试积分余额
    print("\n4. 测试获取积分余额...")
    response = requests.get(f"{BASE_URL}/api/credits/balance", headers=headers)
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}")

    # 5. 测试交易记录
    print("\n5. 测试获取交易记录...")
    response = requests.get(f"{BASE_URL}/api/credits/transactions", headers=headers)
    print(f"   状态码: {response.status_code}")
    result = response.json()
    print(f"   成功: {result.get('success')}")
    print(f"   交易数量: {len(result.get('transactions', []))}")

    # 6. 测试充值历史
    print("\n6. 测试获取充值历史...")
    response = requests.get(f"{BASE_URL}/api/credits/recharge/history?limit=5", headers=headers)
    print(f"   状态码: {response.status_code}")
    result = response.json()
    print(f"   成功: {result.get('success')}")
    print(f"   订单数量: {len(result.get('orders', []))}")

    # 7. 测试任务列表
    print("\n7. 测试获取任务列表...")
    response = requests.get(f"{BASE_URL}/api/tasks/list", headers=headers)
    print(f"   状态码: {response.status_code}")
    result = response.json()
    print(f"   成功: {result.get('success')}")
    print(f"   任务数量: {len(result.get('tasks', []))}")

    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_endpoints()
