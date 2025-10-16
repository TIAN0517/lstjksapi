"""
BossJy-Pro 增強數據清洗服務示例
演示如何使用所有新的精準驗證功能
"""

import asyncio
import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.phone_validator import phone_validator
from app.services.ethnicity_scoring import ethnicity_scorer
from app.services.address_normalizer import address_normalizer
from app.services.lang_detect import language_detector
from app.services.linkage import entity_linker
from app.services.quality import data_quality_validator
import pandas as pd


def demo_phone_validation():
    """示例 1：電話驗證"""
    print("\n" + "=" * 60)
    print("示例 1：電話驗證")
    print("=" * 60)

    # 測試電話號碼
    test_numbers = [
        "+852 9123 4567",           # 香港手機
        "+86 138 1234 5678",        # 中國大陸手機
        "+1 415 123 4567",          # 美國號碼
        "09123456789",              # 菲律賓（無國碼）
        "invalid-phone",            # 無效號碼
    ]

    print("\n測試號碼:")
    for num in test_numbers:
        print(f"  - {num}")

    # 驗證
    results = phone_validator.batch_validate(
        numbers=test_numbers,
        default_region="HK",
        use_lookup=False  # 設為 True 需要 Twilio 配置
    )

    print("\n驗證結果:")
    for i, result in enumerate(results):
        print(f"\n  [{i+1}] {result['raw']}")
        print(f"      有效: {result['is_valid']}")
        print(f"      E.164: {result['e164']}")
        print(f"      地區: {result['region_code']}")
        print(f"      類型: {result['line_type']}")
        print(f"      分數: {result['validation_score']:.2f}")


def demo_ethnicity_scoring():
    """示例 2：華人識別"""
    print("\n" + "=" * 60)
    print("示例 2：華人/華裔識別")
    print("=" * 60)

    # 測試姓名
    test_records = [
        {
            "name": "李明",
            "phone": "+852 9123 4567",
            "address": "Hong Kong, Kowloon"
        },
        {
            "name": "John Smith",
            "phone": "+1 415 123 4567",
            "address": "San Francisco, CA"
        },
        {
            "name": "王偉 (Wang Wei)",
            "phone": "+86 138 1234 5678",
            "address": "北京市朝陽區"
        },
        {
            "name": "Lee Chen",
            "phone": "+65 9123 4567",
            "address": "Singapore"
        },
    ]

    print("\n測試記錄:")
    for record in test_records:
        print(f"  - {record['name']} | {record['phone']}")

    # 評分
    print("\n識別結果:")
    for record in test_records:
        result = ethnicity_scorer.chinese_likelihood(
            name=record["name"],
            e164_region=record["phone"][:4] if record["phone"].startswith("+") else None,
            address=record["address"]
        )

        print(f"\n  姓名: {record['name']}")
        print(f"      華人機率: {result['prob_chinese']:.1%}")
        print(f"      姓氏: {result['surname']}")
        print(f"      訊號分數:")
        for signal, score in result['signals'].items():
            if score > 0:
                print(f"        - {signal}: {score:.3f}")


def demo_address_normalization():
    """示例 3：地址標準化"""
    print("\n" + "=" * 60)
    print("示例 3：地址標準化")
    print("=" * 60)

    # 測試地址
    test_addresses = [
        "123 Nathan Road, Tsim Sha Tsui, Kowloon, Hong Kong",
        "北京市朝陽區建國門外大街1號",
        "1600 Amphitheatre Parkway, Mountain View, CA 94043",
        "台北市信義區信義路五段7號",
    ]

    print("\n測試地址:")
    for addr in test_addresses:
        print(f"  - {addr}")

    # 標準化
    results = address_normalizer.batch_normalize(
        addresses=test_addresses
    )

    print("\n標準化結果:")
    for i, result in enumerate(results):
        print(f"\n  [{i+1}] 原始: {result['original'][:50]}...")
        print(f"      標準化: {result['normalized']}")
        print(f"      質量分數: {result['quality_score']:.2f}")

        if result.get('cn_adm'):
            print(f"      省市區: {result['cn_adm']}")


def demo_language_detection():
    """示例 4：語言檢測"""
    print("\n" + "=" * 60)
    print("示例 4：語言檢測")
    print("=" * 60)

    # 測試文本
    test_texts = [
        "這是一段繁體中文文字。",
        "This is English text.",
        "呢個係粵語。",  # 粵語（可能被識別為 zh 或 yue）
        "Ceci est du français.",
        "こんにちは、日本語です。",
    ]

    print("\n測試文本:")
    for text in test_texts:
        print(f"  - {text}")

    # 檢測
    results = language_detector.batch_detect(
        texts=test_texts,
        k=3
    )

    print("\n檢測結果:")
    for i, result in enumerate(results):
        print(f"\n  文本: {test_texts[i]}")
        print(f"      語言: {result['lang']}")
        print(f"      置信度: {result['score']:.1%}")
        if result.get('top_k'):
            print(f"      Top-3: {', '.join([f\"{r['lang']}({r['score']:.1%})\" for r in result['top_k'][:3]])}")


def demo_deduplication():
    """示例 5：去重"""
    print("\n" + "=" * 60)
    print("示例 5：數據去重")
    print("=" * 60)

    # 測試記錄（含重複）
    test_records = [
        {"name": "張三", "phone": "+852 9123 4567", "email": "zhang@example.com"},
        {"name": "Zhang San", "phone": "+852-9123-4567", "email": "zhang@example.com"},  # 重複 1
        {"name": "李四", "phone": "+86 138 1234 5678", "email": "li@example.com"},
        {"name": "王五", "phone": "+1 415 123 4567", "email": "wang@example.com"},
        {"name": "张三", "phone": "85291234567", "email": "zhangsan@example.com"},  # 重複 1（拼寫不同）
    ]

    print("\n測試記錄:")
    for i, record in enumerate(test_records):
        print(f"  [{i}] {record['name']} | {record['phone']} | {record['email']}")

    # 去重
    results = entity_linker.deduplicate_records(
        records=test_records,
        match_threshold=0.8
    )

    # 查找重複集群
    clusters = entity_linker.find_duplicates(
        records=test_records,
        match_threshold=0.8
    )

    print("\n去重結果:")
    for i, result in enumerate(results):
        status = "✓ 唯一" if result.get("duplicate_of") is None else f"⚠ 重複 -> 記錄 {result['duplicate_of']}"
        print(f"  [{i}] Cluster {result['cluster_id']} | 分數 {result['match_score']:.2f} | {status}")

    print(f"\n重複集群: {len(clusters)} 個")
    for cluster_id, indices in clusters.items():
        print(f"  {cluster_id}: 記錄 {indices}")


def demo_quality_check():
    """示例 6：數據質量驗證"""
    print("\n" + "=" * 60)
    print("示例 6：數據質量驗證")
    print("=" * 60)

    # 創建測試數據
    test_data = [
        {
            "id": 1,
            "name": "張三",
            "phone_e164": "+852 9123 4567",
            "email": "zhang@example.com",
            "lang_score": 0.95,
            "name_zh_prob": 0.98,
        },
        {
            "id": 2,
            "name": "李四",
            "phone_e164": "+86138",  # 無效格式
            "email": "invalid-email",  # 無效郵箱
            "lang_score": 0.45,
            "name_zh_prob": 0.85,
        },
        {
            "id": 3,
            "name": "王五",
            "phone_e164": "+14151234567",
            "email": "wang@example.com",
            "lang_score": 1.2,  # 超出範圍
            "name_zh_prob": 0.70,
        },
    ]

    df = pd.DataFrame(test_data)

    print("\n測試數據:")
    print(df.to_string(index=False))

    # 快速檢查（不使用 GX）
    quick_result = data_quality_validator.quick_check(df)

    print("\n快速質量檢查:")
    print(f"  總行數: {quick_result['total_rows']}")
    print(f"  重複行: {quick_result['duplicate_rows']}")
    print(f"  缺失值: {quick_result['missing_values']}")


def main():
    """運行所有示例"""
    print("\n" + "=" * 60)
    print("BossJy-Pro 增強數據清洗服務示例")
    print("=" * 60)

    try:
        demo_phone_validation()
        demo_ethnicity_scoring()
        demo_address_normalization()
        demo_language_detection()
        demo_deduplication()
        demo_quality_check()

        print("\n" + "=" * 60)
        print("✅ 所有示例運行完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
