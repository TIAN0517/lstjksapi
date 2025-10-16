#!/usr/bin/env python3
"""
BossJy 電話號碼驗證引擎測試腳本
"""

import requests
import json
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

BASE_URL = "http://localhost:18001"

def test_health():
    """測試健康檢查端點"""
    console.print("[cyan]🔍 測試健康檢查端點...[/cyan]")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            console.print("✅ 健康檢查通過")
            console.print(json.dumps(response.json(), indent=2, ensure_ascii=False))
            return True
        else:
            console.print(f"❌ 健康檢查失敗: {response.status_code}")
            return False
    except Exception as e:
        console.print(f"❌ 健康檢查錯誤: {e}")
        return False

def test_phone_validation():
    """測試電話號碼驗證 API"""
    console.print("[cyan]🔍 測試電話號碼驗證 API...[/cyan]")
    
    test_cases = [
        {"phone": "+886912345678", "country_code": "TW", "description": "台灣手機號碼"},
        {"phone": "0912345678", "country_code": "TW", "description": "台灣手機號碼(無國碼)"},
        {"phone": "+14155552671", "country_code": "US", "description": "美國號碼"},
        {"phone": "+8613812345678", "country_code": "CN", "description": "中國大陸號碼"},
        {"phone": "invalid_number", "country_code": None, "description": "無效號碼"},
        {"phone": "+442071838750", "country_code": "GB", "description": "英國號碼"},
        {"phone": "+81201234567", "country_code": "JP", "description": "日本號碼"}
    ]
    
    results = []
    
    for case in test_cases:
        console.print(f"\n[yellow]測試: {case['description']} - {case['phone']}[/yellow]")
        
        try:
            # 測試 POST 方式
            response = requests.post(
                f"{BASE_URL}/api/validate/phone",
                json={"phone": case["phone"], "country_code": case["country_code"]},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                console.print(f"✅ POST: {result}")
                results.append({"case": case["description"], "status": "success", "result": result})
            else:
                console.print(f"❌ POST 失敗: {response.status_code} - {response.text}")
                results.append({"case": case["description"], "status": "failed", "error": response.text})
            
            # 測試 GET 方式
            params = {"phone": case["phone"]}
            if case["country_code"]:
                params["country_code"] = case["country_code"]
                
            response = requests.get(f"{BASE_URL}/api/validate/phone", params=params)
            
            if response.status_code == 200:
                result = response.json()
                console.print(f"✅ GET: {result}")
            else:
                console.print(f"❌ GET 失敗: {response.status_code} - {response.text}")
                
        except Exception as e:
            console.print(f"❌ 測試錯誤: {e}")
            results.append({"case": case["description"], "status": "error", "error": str(e)})
        
        time.sleep(0.5)  # 避免請求過快
    
    return results

def test_stats():
    """測試統計 API"""
    console.print("[cyan]🔍 測試統計 API...[/cyan]")
    try:
        response = requests.get(f"{BASE_URL}/api/stats")
        if response.status_code == 200:
            stats = response.json()
            console.print("✅ 統計信息獲取成功")
            
            # 顯示統計表格
            table = Table(title="📊 驗證統計")
            table.add_column("項目", style="cyan")
            table.add_column("數值", style="green")
            
            table.add_row("總驗證數", str(stats.get("total_validations", 0)))
            table.add_row("有效號碼", str(stats.get("valid_count", 0)))
            table.add_row("無效號碼", str(stats.get("invalid_count", 0)))
            table.add_row("成功率", f"{stats.get('success_rate', 0)}%")
            
            console.print(table)
            
            # 顯示國家分布
            if stats.get("country_distribution"):
                console.print("\n[bold]🌍 國家分布:[/bold]")
                for country, count in stats["country_distribution"].items():
                    console.print(f"  {country}: {count}")
            
            # 顯示類型分布
            if stats.get("type_distribution"):
                console.print("\n[bold]📱 類型分布:[/bold]")
                for phone_type, count in stats["type_distribution"].items():
                    console.print(f"  {phone_type}: {count}")
            
            # 顯示樣本號碼
            if stats.get("sample_numbers"):
                console.print("\n[bold]🔍 樣本號碼:[/bold]")
                for sample in stats["sample_numbers"]:
                    console.print(f"  {sample.get('masked_number', 'N/A')} ({sample.get('country', 'N/A')})")
            
            return True
        else:
            console.print(f"❌ 統計 API 失敗: {response.status_code}")
            return False
    except Exception as e:
        console.print(f"❌ 統計 API 錯誤: {e}")
        return False

def main():
    """主測試函數"""
    console.print(Panel.fit(
        "[bold green]🧪 BossJy 電話號碼驗證引擎測試[/bold green]",
        title="API 測試",
        border_style="green"
    ))
    
    # 等待服務啟動
    console.print("[yellow]⏳ 等待服務啟動...[/yellow]")
    time.sleep(3)
    
    # 執行測試
    tests = [
        ("健康檢查", test_health),
        ("電話號碼驗證", test_phone_validation),
        ("統計信息", test_stats)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        console.print(f"\n[bold magenta]🔬 執行測試: {test_name}[/bold magenta]")
        results[test_name] = test_func()
    
    # 顯示測試總結
    console.print("\n" + "="*50)
    console.print("[bold green]📋 測試總結[/bold green]")
    
    for test_name, result in results.items():
        if isinstance(result, bool):
            status = "✅ 通過" if result else "❌ 失敗"
            console.print(f"{test_name}: {status}")
        else:
            success_count = sum(1 for r in result if r.get("status") == "success")
            total_count = len(result)
            console.print(f"{test_name}: {success_count}/{total_count} 通過")
    
    console.print("\n[bold cyan]🎉 測試完成！[/bold cyan]")

if __name__ == "__main__":
    main()