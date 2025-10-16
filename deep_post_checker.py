#!/usr/bin/env python3
"""
BossJy-Pro POST端点深层检查器
分析所有POST请求的对应关系和缺失情况
"""

import os
import re
import json
from pathlib import Path

def find_post_endpoints():
    """查找所有POST端点"""
    post_endpoints = {}
    api_dir = Path("services/fastapi/api")
    
    if not api_dir.exists():
        return {"error": "API目录不存在"}
    
    # 遍历所有API文件
    for api_file in api_dir.glob("*.py"):
        try:
            with open(api_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 查找POST端点
            post_matches = re.findall(r'@.*\.post\(["\']([^"\']+)["\']', content)
            
            if post_matches:
                post_endpoints[api_file.name] = {
                    "file": str(api_file),
                    "endpoints": []
                }
                
                # 获取每个端点的详细信息
                for endpoint in post_matches:
                    # 查找端点函数
                    func_pattern = rf'@.*\.post\(["\']{re.escape(endpoint)}["\'][\s\S]*?def\s+(\w+)\s*\([^)]*\):'
                    func_match = re.search(func_pattern, content)
                    
                    if func_match:
                        func_name = func_match.group(1)
                        
                        # 获取函数文档
                        doc_pattern = rf'def\s+{func_name}\s*\([^)]*\):[\s\S]*?"""([\s\S]*?)"""'
                        doc_match = re.search(doc_pattern, content)
                        doc = doc_match.group(1).strip() if doc_match else "无文档"
                        
                        # 获取参数
                        param_pattern = rf'def\s+{func_name}\s*\(([^)]*)\):'
                        param_match = re.search(param_pattern, content)
                        params = param_match.group(1).strip() if param_match else ""
                        
                        post_endpoints[api_file.name]["endpoints"].append({
                            "path": endpoint,
                            "function": func_name,
                            "description": doc,
                            "parameters": params
                        })
        except Exception as e:
            post_endpoints[api_file.name] = {"error": str(e)}
    
    return post_endpoints

def find_form_endpoints():
    """查找表单提交端点"""
    form_endpoints = {}
    vue_dir = Path("services/vue-frontend/src")
    
    if not vue_dir.exists():
        return {"error": "Vue前端目录不存在"}
    
    # 查找Vue组件中的表单提交
    for vue_file in vue_dir.rglob("*.vue"):
        try:
            with open(vue_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 查找表单提交
            form_matches = re.findall(r'method=["\']post["\'][^>]*action=["\']([^"\']+)["\']', content, re.IGNORECASE)
            
            if form_matches:
                form_endpoints[vue_file.name] = {
                    "file": str(vue_file),
                    "forms": []
                }
                
                for action in form_matches:
                    form_endpoints[vue_file.name]["forms"].append({
                        "action": action,
                        "type": "form"
                    })
            
            # 查找axios POST请求
            axios_matches = re.findall(r'axios\.post\(["\']([^"\']+)["\']', content)
            
            if axios_matches:
                if vue_file.name not in form_endpoints:
                    form_endpoints[vue_file.name] = {
                        "file": str(vue_file),
                        "forms": []
                    }
                
                for url in axios_matches:
                    form_endpoints[vue_file.name]["forms"].append({
                        "action": url,
                        "type": "axios"
                    })
                    
        except Exception as e:
            form_endpoints[vue_file.name] = {"error": str(e)}
    
    return form_endpoints

def analyze_missing_endpoints():
    """分析缺失的端点"""
    post_endpoints = find_post_endpoints()
    form_endpoints = find_form_endpoints()
    
    # 获取所有后端端点
    backend_endpoints = set()
    for file_data in post_endpoints.values():
        if "endpoints" in file_data:
            for endpoint in file_data["endpoints"]:
                backend_endpoints.add(endpoint["path"])
    
    # 获取所有前端请求
    frontend_requests = set()
    for file_data in form_endpoints.values():
        if "forms" in file_data:
            for form in file_data["forms"]:
                frontend_requests.add(form["action"])
    
    # 找出缺失的端点
    missing_endpoints = frontend_requests - backend_endpoints
    
    return {
        "backend_endpoints": list(backend_endpoints),
        "frontend_requests": list(frontend_requests),
        "missing_endpoints": list(missing_endpoints)
    }

def generate_report():
    """生成详细报告"""
    report = {
        "timestamp": str(datetime.now()),
        "post_endpoints": find_post_endpoints(),
        "form_endpoints": find_form_endpoints(),
        "analysis": analyze_missing_endpoints()
    }
    
    return report

def main():
    """主函数"""
    print("BossJy-Pro POST端点深层检查器")
    print("=" * 50)
    
    # 查找POST端点
    print("\n[INFO] 查找POST端点...")
    post_endpoints = find_post_endpoints()
    
    if "error" in post_endpoints:
        print(f"[ERROR] 错误: {post_endpoints['error']}")
        return
    
    total_endpoints = 0
    for file_name, file_data in post_endpoints.items():
        if "endpoints" in file_data:
            print(f"\n[FILE] {file_name}:")
            for endpoint in file_data["endpoints"]:
                total_endpoints += 1
                print(f"  - POST {endpoint['path']}")
                print(f"    函数: {endpoint['function']}")
                print(f"    描述: {endpoint['description']}")
                if endpoint['parameters']:
                    print(f"    参数: {endpoint['parameters']}")
                print()
    
    print(f"[SUCCESS] 总共找到 {total_endpoints} 个POST端点")
    
    # 查找表单提交
    print("\n[INFO] 查找前端表单提交...")
    form_endpoints = find_form_endpoints()
    
    if "error" in form_endpoints:
        print(f"[ERROR] 错误: {form_endpoints['error']}")
    else:
        total_forms = 0
        for file_name, file_data in form_endpoints.items():
            if "forms" in file_data:
                print(f"\n[FILE] {file_name}:")
                for form in file_data["forms"]:
                    total_forms += 1
                    print(f"  - {form['type'].upper()}: {form['action']}")
        
        print(f"[SUCCESS] 总共找到 {total_forms} 个表单提交")
    
    # 分析缺失端点
    print("\n[INFO] 分析缺失端点...")
    analysis = analyze_missing_endpoints()
    
    if analysis["missing_endpoints"]:
        print(f"[WARNING] 发现 {len(analysis['missing_endpoints'])} 个缺失端点:")
        for endpoint in analysis["missing_endpoints"]:
            print(f"  - {endpoint}")
    else:
        print("[SUCCESS] 没有发现缺失端点")
    
    # 生成详细报告
    print("\n[INFO] 生成详细报告...")
    report = generate_report()
    
    # 保存报告
    with open("post_endpoints_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print("[SUCCESS] 报告已保存到 post_endpoints_report.json")
    
    # 生成可读报告
    with open("post_endpoints_report.txt", "w", encoding="utf-8") as f:
        f.write("BossJy-Pro POST端点深层检查报告\n")
        f.write("=" * 50 + "\n")
        f.write(f"生成时间: {report['timestamp']}\n\n")
        
        f.write("[POST] POST端点列表\n")
        f.write("-" * 30 + "\n")
        for file_name, file_data in report["post_endpoints"].items():
            if "endpoints" in file_data:
                f.write(f"\n[FILE] {file_name}:\n")
                for endpoint in file_data["endpoints"]:
                    f.write(f"  - POST {endpoint['path']}\n")
                    f.write(f"    函数: {endpoint['function']}\n")
                    f.write(f"    描述: {endpoint['description']}\n")
                    if endpoint['parameters']:
                        f.write(f"    参数: {endpoint['parameters']}\n")
                    f.write("\n")
        
        f.write("\n[FRONTEND] 前端表单提交\n")
        f.write("-" * 30 + "\n")
        for file_name, file_data in report["form_endpoints"].items():
            if "forms" in file_data:
                f.write(f"\n[FILE] {file_name}:\n")
                for form in file_data["forms"]:
                    f.write(f"  - {form['type'].upper()}: {form['action']}\n")
        
        f.write("\n[ANALYSIS] 缺失端点分析\n")
        f.write("-" * 30 + "\n")
        if analysis["missing_endpoints"]:
            f.write(f"[WARNING] 发现 {len(analysis['missing_endpoints'])} 个缺失端点:\n")
            for endpoint in analysis["missing_endpoints"]:
                f.write(f"  - {endpoint}\n")
        else:
            f.write("[SUCCESS] 没有发现缺失端点\n")
    
    print("[SUCCESS] 可读报告已保存到 post_endpoints_report.txt")

if __name__ == "__main__":
    from datetime import datetime
    main()
