#!/usr/bin/env python3
"""
BossJy-Pro 系统健康检查脚本
检查所有服务的运行状态和健康度
"""
import requests
import subprocess
import json
import sys
from datetime import datetime
from typing import Dict, List, Tuple


class HealthChecker:
    """系统健康检查器"""

    def __init__(self):
        self.results = []
        self.total_checks = 0
        self.passed_checks = 0
        self.failed_checks = 0

    def check_docker_container(self, container_name: str) -> Tuple[bool, str]:
        """检查Docker容器状态"""
        try:
            result = subprocess.run(
                ["docker", "inspect", "--format={{.State.Status}}", container_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            status = result.stdout.strip()
            if status == "running":
                return True, "运行中"
            else:
                return False, f"状态: {status}"
        except subprocess.TimeoutExpired:
            return False, "检查超时"
        except Exception as e:
            return False, f"错误: {str(e)}"

    def check_http_endpoint(self, url: str, expected_status: int = 200) -> Tuple[bool, str]:
        """检查HTTP端点"""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == expected_status:
                return True, f"HTTP {response.status_code}"
            else:
                return False, f"HTTP {response.status_code} (期望 {expected_status})"
        except requests.exceptions.ConnectionError:
            return False, "连接失败"
        except requests.exceptions.Timeout:
            return False, "请求超时"
        except Exception as e:
            return False, f"错误: {str(e)}"

    def check_port(self, host: str, port: int) -> Tuple[bool, str]:
        """检查端口是否可访问"""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                return True, f"端口 {port} 开放"
            else:
                return False, f"端口 {port} 关闭"
        except Exception as e:
            return False, f"错误: {str(e)}"

    def add_check(self, name: str, passed: bool, message: str, category: str = "general"):
        """添加检查结果"""
        self.total_checks += 1
        if passed:
            self.passed_checks += 1
            status = "[OK]"
        else:
            self.failed_checks += 1
            status = "[FAIL]"

        self.results.append({
            "name": name,
            "status": status,
            "passed": passed,
            "message": message,
            "category": category
        })

    def run_all_checks(self):
        """运行所有健康检查"""
        print("=" * 70)
        print("BossJy-Pro System Health Check")
        print("=" * 70)
        print(f"Check Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Docker容器检查
        print("[1] Docker Container Check...")
        containers = [
            "bossjy-postgres",
            "bossjy-redis",
            "bossjy-fastapi",
            "bossjy-go-api",
            "bossjy-bots",
            "bossjy-vue-frontend",
            "bossjy-nginx"
        ]

        for container in containers:
            passed, message = self.check_docker_container(container)
            self.add_check(container, passed, message, "docker")

        # 端口检查
        print("\n[2] Port Connection Check...")
        ports = [
            ("PostgreSQL", "localhost", 15432),
            ("Redis", "localhost", 16379),
            ("FastAPI", "localhost", 18001),
            ("Go API", "localhost", 8080),
            ("Bots", "localhost", 9001),
            ("Vue Frontend", "localhost", 3000),
            ("Nginx HTTP", "localhost", 80),
        ]

        for name, host, port in ports:
            passed, message = self.check_port(host, port)
            self.add_check(f"{name} ({port})", passed, message, "port")

        # API端点检查
        print("\n[3] API Endpoint Check...")
        endpoints = [
            ("FastAPI Health", "http://localhost:18001/api/health"),
            ("FastAPI Status", "http://localhost:18001/api/status"),
            ("Go API Health", "http://localhost:8080/health"),
        ]

        for name, url in endpoints:
            passed, message = self.check_http_endpoint(url)
            self.add_check(name, passed, message, "api")

    def print_summary(self):
        """打印检查结果摘要"""
        print("\n" + "=" * 70)
        print("Summary of Health Check Results")
        print("=" * 70)

        # 按类别分组
        categories = {}
        for result in self.results:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result)

        # 打印每个类别
        for category, items in categories.items():
            category_names = {
                "docker": "Docker 容器",
                "port": "端口连接",
                "api": "API 端点"
            }
            print(f"\n{category_names.get(category, category)}:")
            for item in items:
                print(f"  {item['status']} {item['name']}: {item['message']}")

        # 统计信息
        print("\n" + "=" * 70)
        print(f"Total Checks: {self.total_checks}")
        print(f"[OK] Passed: {self.passed_checks}")
        print(f"[FAIL] Failed: {self.failed_checks}")

        if self.failed_checks == 0:
            print("\n[SUCCESS] All checks passed! System is running normally.")
            return 0
        else:
            print(f"\n[WARNING] Found {self.failed_checks} issues, please check!")
            return 1

    def export_json(self, filename: str = "health_check_report.json"):
        """导出JSON格式报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_checks": self.total_checks,
            "passed": self.passed_checks,
            "failed": self.failed_checks,
            "checks": self.results
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n[REPORT] Detailed report exported: {filename}")


def main():
    """主函数"""
    checker = HealthChecker()

    try:
        checker.run_all_checks()
        exit_code = checker.print_summary()

        # 导出JSON报告
        checker.export_json()

        return exit_code

    except KeyboardInterrupt:
        print("\n\nHealth check interrupted")
        return 1
    except Exception as e:
        print(f"\n[ERROR] Health check failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
