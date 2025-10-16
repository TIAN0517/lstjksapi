#!/usr/bin/env python3
"""
BossJy-Pro 金鑰健康檢測器
BossJy-Pro Key Health Checker

提供完整的 API 金鑰健康檢測和管理功能
"""

import os
import json
import time
import random
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from rich.console import Console
from rich.table import Table

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# 設定 Rich Console
console = Console()

# 內建金鑰池
DEFAULT_API_KEYS = [
    "AIzaSyCbFPAWJActC5-H7Tu-Er8pqwPPUgdvhkc",
    "AIzaSyCE44ezL17NUbvJrdSTsLQ_eMs80XYeUzU",
    "AIzaSyAW76tREHx0d0_U5I_M569EoAbvWQ8X1CY",
    "AIzaSyBAnXZ-2F6vcGtr4qgtFw6TzI02xbhGyPA",
    "AIzaSyC1GUIM_iCQ4Fj8JnGXKh_6BQadajM_NY0",
    "AIzaSyACDjmu1lED5kY1pl-EiqER49FhwILFZAA",
    "AIzaSyAB_KJ3QGhYgfB3xyz5nRHDbSX7YR1p6pk",
    "AIzaSyBBI7ddnmIejMuBmc1_pGhIQNwLSLPcTAk",
    "AIzaSyAiWqJ6mH_m0qMVz0E1s8mFsZbi9gCE3L8",
    "AIzaSyDUFDnO-EGRXEH-2ljfAaWbwRDw8Q31hhk",
    "AIzaSyDGrE60mgS-KYZDlsXGOWihP0JM8yy0gyA"
]

MODEL = "gemini-2.5-pro"

class KeyHealthChecker:
    """API 金鑰健康檢測器"""

    def __init__(self, api_keys: Optional[List[str]] = None):
        """
        初始化健康檢測器

        Args:
            api_keys: 要檢測的金鑰列表，如果為 None 則從環境變數或內建金鑰池載入
        """
        self.api_keys = api_keys or self._load_api_keys()
        self.healthy_keys: List[str] = []
        self.key_stats: Dict[str, Dict[str, Any]] = {}
        self.last_check_time: Optional[float] = None
        self.status_file = "key_health_status.json"

    def _load_api_keys(self) -> List[str]:
        """從環境變數或內建金鑰池載入 API 金鑰"""
        # 優先從環境變數載入
        keys_str = os.getenv("GEMINI_API_KEYS", "")
        if keys_str:
            keys = [key.strip() for key in keys_str.split(",") if key.strip()]
            logger.info(f"從環境變數載入 {len(keys)} 組 API 金鑰")
            return keys
        else:
            logger.info(f"使用內建金鑰池，共 {len(DEFAULT_API_KEYS)} 組金鑰")
            return DEFAULT_API_KEYS.copy()

    def _check_single_key(self, api_key: str, retries: int = 3) -> tuple[bool, str]:
        """
        檢查單一金鑰健康狀態

        Args:
            api_key: 要檢查的金鑰
            retries: 重試次數

        Returns:
            (是否健康, 錯誤訊息)
        """
        for attempt in range(1, retries + 1):
            try:
                genai.configure(api_key=api_key, transport='rest')
                model = genai.GenerativeModel(MODEL)

                # 使用 count_tokens 測試，更穩定
                tokens = model.count_tokens("健康檢測測試")
                if tokens.total_tokens > 0:
                    return True, "OK"

            except Exception as e:
                err_msg = str(e).split("\n")[0]
                if attempt < retries:
                    time.sleep(random.uniform(0.5, 1.5))  # 隨機延遲避免壓爆
                    continue
                return False, err_msg

        return False, "Unknown Error"

    def check_all_keys(self, force_check: bool = False) -> Dict[str, Any]:
        """
        檢查所有金鑰的健康狀態

        Args:
            force_check: 是否強制重新檢查（忽略快取）

        Returns:
            包含檢測結果的字典
        """
        console.print("🔍 [bold blue]金鑰健康檢測中...[/bold blue]")

        results = []
        healthy_count = 0

        for key in self.api_keys:
            prefix = key[:12] + "****"

            # 如果有快取且不需要強制檢查，跳過已檢查的金鑰
            if not force_check and key in self.key_stats and self.key_stats[key].get("last_checked"):
                last_checked = self.key_stats[key]["last_checked"]
                # 如果上次檢查在 5 分鐘內，視為有效
                if time.time() - last_checked < 300:
                    is_healthy = self.key_stats[key]["is_healthy"]
                    status = "✅ 有效" if is_healthy else "❌ 失效"
                    console.print(f"{status}: {prefix} (快取)")
                    results.append({
                        "key": prefix,
                        "status": status,
                        "message": self.key_stats[key].get("message", "Cached")
                    })
                    if is_healthy:
                        healthy_count += 1
                    continue

            # 實際檢查金鑰
            is_healthy, message = self._check_single_key(key)
            status = "✅ 有效" if is_healthy else "❌ 失效"

            console.print(f"{status}: {prefix} ({message})")

            # 更新統計
            self.key_stats[key] = {
                "is_healthy": is_healthy,
                "last_checked": time.time(),
                "message": message
            }

            results.append({
                "key": prefix,
                "status": status,
                "message": message
            })

            if is_healthy:
                healthy_count += 1

        # 儲存檢測結果
        self._save_health_status(results, healthy_count)

        return {
            "total": len(self.api_keys),
            "healthy": healthy_count,
            "unhealthy": len(self.api_keys) - healthy_count,
            "results": results
        }

    def _save_health_status(self, results: List[Dict], healthy_count: int):
        """儲存健康狀態到 JSON 檔案"""
        data = {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "total": len(self.api_keys),
            "valid": healthy_count,
            "invalid": len(self.api_keys) - healthy_count,
            "results": results
        }

        try:
            with open(self.status_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"✅ 檢測結果已儲存到 {self.status_file}")
        except Exception as e:
            logger.error(f"❌ 儲存檢測結果失敗: {e}")

    def get_healthy_keys(self) -> List[str]:
        """
        獲取所有健康的金鑰

        Returns:
            健康金鑰列表
        """
        # 確保有最新的檢測結果
        if not self.key_stats or not self.last_check_time or time.time() - self.last_check_time > 300:
            self.check_all_keys()

        self.healthy_keys = [
            key for key in self.api_keys
            if self.key_stats.get(key, {}).get("is_healthy", False)
        ]

        logger.info(f"找到 {len(self.healthy_keys)} 組健康金鑰")
        return self.healthy_keys.copy()

    def get_statistics(self) -> Dict[str, Any]:
        """獲取檢測統計資訊"""
        if not self.key_stats:
            return {"total": 0, "healthy": 0, "unhealthy": 0, "details": []}

        healthy_count = sum(1 for stat in self.key_stats.values() if stat.get("is_healthy", False))
        total_count = len(self.api_keys)

        return {
            "total": total_count,
            "healthy": healthy_count,
            "unhealthy": total_count - healthy_count,
            "last_check": self.last_check_time,
            "details": [
                {
                    "key_prefix": key[:12] + "****",
                    "is_healthy": self.key_stats[key].get("is_healthy", False),
                    "last_checked": self.key_stats[key].get("last_checked", 0),
                    "message": self.key_stats[key].get("message", "")
                }
                for key in self.api_keys
            ]
        }

    def is_key_healthy(self, api_key: str) -> bool:
        """檢查特定金鑰是否健康"""
        if api_key not in self.key_stats:
            return False
        return self.key_stats[api_key].get("is_healthy", False)

    def load_previous_results(self) -> bool:
        """載入之前的檢測結果"""
        try:
            if os.path.exists(self.status_file):
                with open(self.status_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 檢查結果是否在 5 分鐘內
                if data.get("checked_at"):
                    checked_time = datetime.fromisoformat(data["checked_at"].replace('Z', '+00:00'))
                    if (datetime.now(timezone.utc) - checked_time.replace(tzinfo=timezone.utc)).total_seconds() < 300:
                        # 載入之前的結果
                        for result in data.get("results", []):
                            key_full = next(
                                (k for k in self.api_keys if k.startswith(result["key"][:12])),
                                None
                            )
                            if key_full:
                                self.key_stats[key_full] = {
                                    "is_healthy": "有效" in result["status"],
                                    "last_checked": time.time(),
                                    "message": result["message"]
                                }

                        self.last_check_time = time.time()
                        logger.info(f"✅ 已載入之前的檢測結果，共 {data.get('valid', 0)} 組健康金鑰")
                        return True

            return False
        except Exception as e:
            logger.warning(f"⚠️ 載入檢測結果失敗: {e}")
            return False

# 便捷函數
def create_health_checker(api_keys: Optional[List[str]] = None) -> KeyHealthChecker:
    """創建健康檢測器實例"""
    return KeyHealthChecker(api_keys)

def quick_health_check() -> Dict[str, Any]:
    """快速健康檢查（便捷函數）"""
    checker = KeyHealthChecker()
    return checker.check_all_keys()

if __name__ == "__main__":
    # 測試模式
    checker = KeyHealthChecker()
    results = checker.check_all_keys()

    print("\n📊 檢測完成！")
    print(f"總金鑰數: {results['total']}")
    print(f"健康金鑰: {results['healthy']}")
    print(f"失效金鑰: {results['unhealthy']}")

    healthy_keys = checker.get_healthy_keys()
    print(f"可用的金鑰: {len(healthy_keys)} 組")

    if healthy_keys:
        print("🎯 建議使用這些金鑰:")
        for key in healthy_keys:
            print(f"  - {key[:12]}****")
