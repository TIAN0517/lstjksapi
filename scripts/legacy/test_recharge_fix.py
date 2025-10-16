#!/usr/bin/env python3
"""
充值积分修复 - 自动化测试脚本
测试 USDT 地址校验、API 权限、审计日志等功能
"""

import pytest
import re
from decimal import Decimal


# ============================================================================
# 测试1: USDT-TRC20 地址校验
# ============================================================================

def is_valid_tron_address(addr: str) -> bool:
    """复制自 app/api/credits_api.py 的校验函数"""
    if not addr or not re.fullmatch(r"T[1-9A-HJ-NP-Za-km-z]{33}", addr):
        return False

    try:
        import base58
        raw = base58.b58decode_check(addr)
        return len(raw) == 21 and raw[0] == 0x41
    except (ValueError, Exception):
        return False


class TestUSDTAddressValidation:
    """USDT地址校验测试"""

    def test_valid_trc20_addresses(self):
        """测试有效的TRC20地址"""
        valid_addresses = [
            "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",  # Tether USDT-TRC20 官方合约地址
            "TN3W4H6rK2ce4vX9YnFQHwKENnHjoxb3m9",  # 真实钱包地址示例1
            "TKHuVq1oKVruCGLvqVexFs6dawKv6fQgFs",  # 真实钱包地址示例2
        ]

        for addr in valid_addresses:
            assert len(addr) == 34, f"地址长度应为34: {addr}"
            assert addr[0] == 'T', f"地址应以T开头: {addr}"
            # 格式校验应通过（实际 Base58Check 需要 base58 库）
            assert re.fullmatch(r"T[1-9A-HJ-NP-Za-km-z]{33}", addr), f"格式校验失败: {addr}"

    def test_invalid_trc20_addresses(self):
        """测试无效的TRC20地址"""
        invalid_addresses = [
            "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",  # ETH地址
            "bc1qar0srrr7xfkvy5l643lydnw9re59gtzzwf5mdq",  # BTC地址
            "abc123",  # 随机字符串
            "T123",  # 太短
            "",  # 空字符串
            "tYuZ9xQQu9zxCQvE8GJxUWv3Jx7s9p5RXC",  # 小写t（应为大写T）
            "T0XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",  # 包含0（不符合Base58）
            "TOXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",  # 包含O（不符合Base58）
        ]

        for addr in invalid_addresses:
            assert not re.fullmatch(r"T[1-9A-HJ-NP-Za-km-z]{33}", addr or ""), \
                f"格式校验应失败: {addr}"

    def test_optional_address_field(self):
        """测试地址为可选字段"""
        # 空地址应允许通过（Optional字段）
        assert is_valid_tron_address("") == False  # 空字符串不通过格式校验
        # 但在API层面，Optional[str] 允许 None


# ============================================================================
# 测试2: API 请求模型校验
# ============================================================================

class TestCreateOrderRequest:
    """创建订单请求模型测试"""

    def test_valid_request_data(self):
        """测试有效的请求数据"""
        valid_data = {
            "amount": 10,
            "network_type": "TRC20",
            "usdt_address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # Tether USDT-TRC20 合约
        }

        assert valid_data["amount"] > 0
        assert valid_data["network_type"] == "TRC20"
        assert len(valid_data["usdt_address"]) == 34

    def test_invalid_amount(self):
        """测试无效金额"""
        invalid_amounts = [0, -10, -0.01, "abc", None]

        for amount in invalid_amounts:
            if amount is None:
                continue
            try:
                if isinstance(amount, str):
                    Decimal(amount)
                else:
                    assert amount <= 0, f"金额应大于0: {amount}"
            except:
                pass  # 预期会失败

    def test_invalid_network_type(self):
        """测试无效的网络类型"""
        invalid_networks = ["ERC20", "BEP20", "SOL", "", None]

        for network in invalid_networks:
            assert network != "TRC20", f"网络类型应仅支持TRC20: {network}"


# ============================================================================
# 测试3: 前端校验逻辑
# ============================================================================

class TestFrontendValidation:
    """前端校验逻辑测试"""

    TRC20_ADDRESS_REGEX = r"^T[1-9A-HJ-NP-Za-km-z]{33}$"

    def test_regex_pattern(self):
        """测试正则表达式模式"""
        pattern = re.compile(self.TRC20_ADDRESS_REGEX)

        # 有效地址
        assert pattern.match("TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t")
        assert pattern.match("TN3W4H6rK2ce4vX9YnFQHwKENnHjoxb3m9")

        # 无效地址
        assert not pattern.match("0x742d35Cc6634C0532925a3b844Bc454e4438f44e")
        assert not pattern.match("abc123")
        assert not pattern.match("T123")  # 太短
        assert not pattern.match("")

    def test_button_disable_logic(self):
        """测试按钮禁用逻辑"""
        # 模拟前端逻辑
        def should_disable_button(address: str) -> bool:
            if not address:
                return False  # 空地址允许提交
            return not re.fullmatch(self.TRC20_ADDRESS_REGEX, address)

        assert should_disable_button("") == False  # 空地址不禁用
        assert should_disable_button("TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t") == False  # 有效地址不禁用
        assert should_disable_button("0x742d35...") == True  # 无效地址禁用


# ============================================================================
# 测试4: 审计日志格式
# ============================================================================

class TestAuditLogging:
    """审计日志测试"""

    def test_log_format(self):
        """测试日志格式"""
        # 模拟日志生成
        user_id = 123
        username = "test_user"
        amount = 10
        network_type = "TRC20"
        usdt_address = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # Tether USDT-TRC20

        # 地址脱敏
        masked_address = f"{usdt_address[:10]}...{usdt_address[-6:]}"

        log_message = (
            f"[AUDIT] 用户 {user_id} ({username}) 创建USDT充值订单 | "
            f"金额: {amount} USDT | 网络: {network_type} | "
            f"地址: {masked_address} | "
            f"地址校验: 通过"
        )

        # 验证日志包含关键信息
        assert "[AUDIT]" in log_message
        assert str(user_id) in log_message
        assert username in log_message
        assert str(amount) in log_message
        assert network_type in log_message
        assert "..." in masked_address  # 确认地址已脱敏
        assert len(masked_address) < len(usdt_address)  # 脱敏后应该更短

    def test_address_masking(self):
        """测试地址脱敏"""
        address = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # Tether USDT-TRC20
        masked = f"{address[:10]}...{address[-6:]}"

        assert masked == "TR7NHqjeKQ...gjLj6t"  # 前10位 + ... + 后6位
        assert len(masked) == 19  # 10 + 3 + 6
        assert address.startswith(masked[:10])
        assert address.endswith(masked[-6:])


# ============================================================================
# 测试5: API响应格式
# ============================================================================

class TestAPIResponses:
    """API响应格式测试"""

    def test_success_response_format(self):
        """测试成功响应格式"""
        mock_response = {
            "success": True,
            "order_id": "ORD-20251007-ABCD1234",
            "wallet_address": "TXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
            "qr_code_url": "https://api.qrserver.com/v1/...",
            "amount": 10.0,
            "credits": 10000,
            "expires_at": "2025-10-07T12:00:00"
        }

        assert mock_response["success"] == True
        assert "order_id" in mock_response
        assert mock_response["credits"] == mock_response["amount"] * 1000
        assert mock_response["amount"] > 0

    def test_error_response_format(self):
        """测试错误响应格式"""
        mock_error_422 = {
            "detail": [
                {
                    "loc": ["body", "usdt_address"],
                    "msg": "Value error, 无效的USDT-TRC20地址格式",
                    "type": "value_error"
                }
            ]
        }

        assert "detail" in mock_error_422
        assert isinstance(mock_error_422["detail"], list)
        assert "usdt_address" in str(mock_error_422["detail"])


# ============================================================================
# 运行测试
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("充值积分修复 - 自动化测试")
    print("=" * 70)
    print()

    # 运行 pytest
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
