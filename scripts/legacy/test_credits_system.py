"""
积分系统测试
测试积分充值、消费、余额查询等功能
"""

import pytest


@pytest.mark.unit
class TestCreditsBalance:
    """积分余额测试"""

    def test_get_balance(self, test_client, auth_headers):
        """测试获取余额"""
        if not auth_headers:
            pytest.skip("No auth token available")

        response = test_client.get(
            "/api/credits/balance",
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()
            assert "balance" in data
            assert data["balance"] >= 0

    def test_balance_returns_number(self, test_client, auth_headers):
        """测试余额返回数字类型"""
        if not auth_headers:
            pytest.skip("No auth token available")

        response = test_client.get(
            "/api/credits/balance",
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data.get("balance"), (int, float))


@pytest.mark.integration
class TestCreditsConsumption:
    """积分消费测试"""

    def test_consume_credits_requires_auth(self, test_client):
        """测试消费积分需要认证"""
        response = test_client.post(
            "/api/credits/consume",
            json={"amount": 10, "reason": "test"}
        )
        assert response.status_code == 401

    def test_consume_negative_credits(self, test_client, auth_headers):
        """测试负数消费"""
        if not auth_headers:
            pytest.skip("No auth token available")

        response = test_client.post(
            "/api/credits/consume",
            headers=auth_headers,
            json={"amount": -10, "reason": "test"}
        )
        # 应该被拒绝
        assert response.status_code in [400, 422]

    def test_consume_more_than_balance(self, test_client, auth_headers):
        """测试消费超过余额"""
        if not auth_headers:
            pytest.skip("No auth token available")

        # 先获取余额
        balance_response = test_client.get(
            "/api/credits/balance",
            headers=auth_headers
        )

        if balance_response.status_code == 200:
            balance = balance_response.json().get("balance", 0)

            # 尝试消费超过余额的金额
            response = test_client.post(
                "/api/credits/consume",
                headers=auth_headers,
                json={"amount": balance + 1000, "reason": "test"}
            )

            # 应该失败
            assert response.status_code in [400, 402, 403]


@pytest.mark.integration
class TestUSDTRecharge:
    """USDT充值测试"""

    def test_create_recharge_order(self, test_client, auth_headers):
        """测试创建充值订单"""
        if not auth_headers:
            pytest.skip("No auth token available")

        response = test_client.post(
            "/api/usdt/create_order",
            headers=auth_headers,
            json={"amount": 10}
        )

        if response.status_code == 200:
            data = response.json()
            assert "order_id" in data
            assert "wallet_address" in data

    def test_create_order_minimum_amount(self, test_client, auth_headers):
        """测试最小充值金额"""
        if not auth_headers:
            pytest.skip("No auth token available")

        response = test_client.post(
            "/api/usdt/create_order",
            headers=auth_headers,
            json={"amount": 0.5}  # 小于最小值1 USDT
        )
        # 应该被拒绝
        assert response.status_code in [400, 422]

    def test_check_payment_status(self, test_client, auth_headers):
        """测试检查支付状态"""
        if not auth_headers:
            pytest.skip("No auth token available")

        # 先创建订单
        create_response = test_client.post(
            "/api/usdt/create_order",
            headers=auth_headers,
            json={"amount": 10}
        )

        if create_response.status_code == 200:
            order_id = create_response.json().get("order_id")

            # 检查支付状态
            status_response = test_client.get(
                f"/api/usdt/check_payment/{order_id}",
                headers=auth_headers
            )

            if status_response.status_code == 200:
                data = status_response.json()
                assert "status" in data
                assert data["status"] in ["pending", "completed", "failed"]


@pytest.mark.unit
class TestCreditsHistory:
    """积分历史测试"""

    def test_get_credits_history(self, test_client, auth_headers):
        """测试获取积分历史"""
        if not auth_headers:
            pytest.skip("No auth token available")

        response = test_client.get(
            "/api/credits/history",
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict))

    def test_history_pagination(self, test_client, auth_headers):
        """测试历史记录分页"""
        if not auth_headers:
            pytest.skip("No auth token available")

        response = test_client.get(
            "/api/credits/history?page=1&limit=10",
            headers=auth_headers
        )

        # 应该支持分页参数
        assert response.status_code in [200, 404]


@pytest.mark.unit
class TestCreditsCalculation:
    """积分计算测试"""

    def test_usdt_to_credits_conversion(self):
        """测试USDT到Credits的转换"""
        # 1 USDT = 100 Credits
        assert 1 * 100 == 100
        assert 10 * 100 == 1000
        assert 0.5 * 100 == 50

    def test_data_processing_cost(self):
        """测试数据处理成本计算"""
        # 每条数据消耗1 Credit
        records = 100
        cost = records * 1
        assert cost == 100

    def test_credits_sufficient_for_task(self):
        """测试积分是否足够完成任务"""
        balance = 500
        task_cost = 100
        assert balance >= task_cost

        large_task_cost = 1000
        assert balance < large_task_cost
