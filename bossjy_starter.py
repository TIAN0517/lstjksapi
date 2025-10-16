#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BossJy 统一启动脚本
用于启动和管理所有Bot和服务
"""

import os
import sys
import time
import signal
import subprocess
import psutil
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Optional
import asyncio

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bossjy_starter.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class BossJyStarter:
    """BossJy启动器"""
    
    def __init__(self, project_dir: str = None):
        self.project_dir = Path(project_dir) if project_dir else Path(__file__).parent
        self.log_dir = self.project_dir / "logs"
        self.pid_dir = Path("/tmp") / "bossjy_services"
        
        # 确保目录存在
        self.log_dir.mkdir(exist_ok=True)
        self.pid_dir.mkdir(exist_ok=True)
        
        # 服务配置
        self.services = {
            "customer_bot": {
                "name": "客户服务Bot",
                "script": "bossjy_customer_bot.py",
                "description": "用户注册、充值、查询服务",
                "port": None,
                "dependencies": ["python-telegram-bot"]
            },
            "data_query_bot": {
                "name": "数据查询Bot",
                "script": "enhanced_data_query_bot.py",
                "description": "数据查询、统计、导出服务",
                "port": None,
                "dependencies": ["python-telegram-bot", "pandas", "openpyxl"]
            },
            "group_manager_bot": {
                "name": "群组管理Bot",
                "script": "enhanced_group_manager_bot.py",
                "description": "群组自动化管理服务",
                "port": None,
                "dependencies": ["python-telegram-bot"]
            },
            "api_service": {
                "name": "API集成服务",
                "script": "api_integration_service.py",
                "description": "RESTful API服务",
                "port": 18001,
                "dependencies": ["fastapi", "uvicorn", "redis", "pandas"]
            },
            "export_service": {
                "name": "数据导出服务",
                "script": "data_export_service.py",
                "description": "数据导出和处理服务",
                "port": None,
                "dependencies": ["pandas", "openpyxl", "aiofiles"]
            }
        }
        
        # 环境变量
        self.env_vars = {
            'PYTHONPATH': str(self.project_dir),
            'BOSSJY_PROJECT_DIR': str(self.project_dir),
            'BOSSJY_LOG_DIR': str(self.log_dir)
        }
        
        # 进程字典
        self.processes = {}
        
    def _get_pid_file(self, service_name: str) -> Path:
        """获取PID文件路径"""
        return self.pid_dir / f"{service_name}.pid"
    
    def _read_pid(self, service_name: str) -> Optional[int]:
        """读取PID"""
        pid_file = self._get_pid_file(service_name)
        try:
            if pid_file.exists():
                with open(pid_file, 'r') as f:
                    return int(f.read().strip())
        except (ValueError, IOError):
            pass
        return None
    
    def _write_pid(self, service_name: str, pid: int):
        """写入PID"""
        pid_file = self._get_pid_file(service_name)
        try:
            with open(pid_file, 'w') as f:
                f.write(str(pid))
        except IOError as e:
            logger.error(f"写入PID文件失败 {pid_file}: {e}")
    
    def _remove_pid(self, service_name: str):
        """删除PID文件"""
        pid_file = self._get_pid_file(service_name)
        try:
            if pid_file.exists():
                pid_file.unlink()
        except IOError as e:
            logger.warning(f"删除PID文件失败 {pid_file}: {e}")
    
    def _is_process_running(self, pid: int) -> bool:
        """检查进程是否运行"""
        try:
            process = psutil.Process(pid)
            return process.is_running() and process.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def _check_dependencies(self, service_name: str) -> bool:
        """检查服务依赖"""
        service = self.services[service_name]
        script_path = self.project_dir / service["script"]
        
        if not script_path.exists():
            logger.error(f"服务脚本不存在: {script_path}")
            return False
        
        # 检查Python包
        for package in service.get("dependencies", []):
            try:
                __import__(package.replace("-", "_"))
            except ImportError:
                logger.error(f"缺少依赖包: {package}")
                return False
        
        return True
    
    def _prepare_environment(self, service_name: str) -> Dict[str, str]:
        """准备环境变量"""
        env = os.environ.copy()
        env.update(self.env_vars)
        
        # 添加服务特定的环境变量
        service = self.services[service_name]
        if service["port"]:
            env[f"{service_name.upper()}_PORT"] = str(service["port"])
        
        return env
    
    async def start_service(self, service_name: str) -> bool:
        """启动单个服务"""
        if service_name not in self.services:
            logger.error(f"未知服务: {service_name}")
            return False
        
        # 检查依赖
        if not self._check_dependencies(service_name):
            return False
        
        # 检查是否已运行
        pid = self._read_pid(service_name)
        if pid and self._is_process_running(pid):
            logger.info(f"{self.services[service_name]['name']} 已在运行 (PID: {pid})")
            return True
        
        service = self.services[service_name]
        script_path = self.project_dir / service["script"]
        
        try:
            logger.info(f"启动 {service['name']}...")
            
            # 准备环境
            env = self._prepare_environment(service_name)
            
            # 创建日志文件
            log_file = self.log_dir / f"{service_name}.log"
            with open(log_file, 'a') as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"启动时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"服务名称: {service['name']}\n")
                f.write(f"脚本路径: {script_path}\n")
                f.write(f"{'='*50}\n")
            
            # 启动进程
            if service["port"]:
                # Web服务
                cmd = [sys.executable, "-m", "uvicorn", f"{service['script'].replace('.py', '')}:app", 
                       "--host", "0.0.0.0", "--port", str(service["port"])]
            else:
                # Bot服务
                cmd = [sys.executable, str(script_path)]
            
            process = subprocess.Popen(
                cmd,
                stdout=open(log_file, 'a'),
                stderr=subprocess.STDOUT,
                cwd=str(self.project_dir),
                env=env
            )
            
            # 保存PID
            self._write_pid(service_name, process.pid)
            self.processes[service_name] = process
            
            # 等待启动
            await asyncio.sleep(3)
            
            if process.poll() is None:
                logger.info(f"{service['name']} 启动成功 (PID: {process.pid})")
                
                # 添加启动信息到日志
                with open(log_file, 'a') as f:
                    f.write(f"进程PID: {process.pid}\n")
                    f.write(f"启动命令: {' '.join(cmd)}\n")
                
                return True
            else:
                logger.error(f"{service['name']} 启动失败")
                self._remove_pid(service_name)
                return False
                
        except Exception as e:
            logger.error(f"启动 {service['name']} 失败: {e}")
            self._remove_pid(service_name)
            return False
    
    async def stop_service(self, service_name: str, force: bool = False) -> bool:
        """停止单个服务"""
        if service_name not in self.services:
            logger.error(f"未知服务: {service_name}")
            return False
        
        pid = self._read_pid(service_name)
        if not pid:
            logger.info(f"{self.services[service_name]['name']} 未运行")
            return True
        
        try:
            logger.info(f"停止 {self.services[service_name]['name']} (PID: {pid})...")
            
            process = None
            if service_name in self.processes:
                process = self.processes[service_name]
            else:
                try:
                    process = psutil.Process(pid)
                except psutil.NoSuchProcess:
                    pass
            
            if process:
                if force:
                    process.kill()
                else:
                    process.terminate()
                
                try:
                    if hasattr(process, 'wait'):
                        process.wait(timeout=10)
                    else:
                        process.wait(timeout=10)
                    logger.info(f"{self.services[service_name]['name']} 已停止")
                except subprocess.TimeoutExpired:
                    if not force:
                        logger.warning(f"{self.services[service_name]['name']} 未及时响应，强制终止")
                        process.kill()
            
            self._remove_pid(service_name)
            if service_name in self.processes:
                del self.processes[service_name]
            
            return True
            
        except Exception as e:
            logger.error(f"停止 {self.services[service_name]['name']} 失败: {e}")
            return False
    
    async def restart_service(self, service_name: str, force: bool = False) -> bool:
        """重启单个服务"""
        logger.info(f"重启 {self.services[service_name]['name']}...")
        return await self.stop_service(service_name, force) and await self.start_service(service_name)
    
    async def start_all(self) -> bool:
        """启动所有服务"""
        logger.info("启动所有服务...")
        success = True
        failed_services = []
        
        # 按依赖顺序启动
        startup_order = ["api_service", "export_service", "customer_bot", "data_query_bot", "group_manager_bot"]
        
        for service_name in startup_order:
            if service_name in self.services:
                if not await self.start_service(service_name):
                    success = False
                    failed_services.append(service_name)
                await asyncio.sleep(2)  # 服务间延迟
        
        if not success:
            logger.error(f"以下服务启动失败: {', '.join(failed_services)}")
        else:
            logger.info("所有服务启动成功")
        
        return success
    
    async def stop_all(self, force: bool = False) -> bool:
        """停止所有服务"""
        logger.info("停止所有服务...")
        success = True
        failed_services = []
        
        # 按逆序停止
        shutdown_order = ["group_manager_bot", "data_query_bot", "customer_bot", "export_service", "api_service"]
        
        for service_name in shutdown_order:
            if service_name in self.services:
                if not await self.stop_service(service_name, force):
                    success = False
                    failed_services.append(service_name)
                await asyncio.sleep(1)  # 服务间延迟
        
        if not success:
            logger.error(f"以下服务停止失败: {', '.join(failed_services)}")
        else:
            logger.info("所有服务已停止")
        
        return success
    
    async def restart_all(self, force: bool = False) -> bool:
        """重启所有服务"""
        logger.info("重启所有服务...")
        return await self.stop_all(force) and await self.start_all()
    
    def get_service_status(self, service_name: str) -> Dict:
        """获取单个服务状态"""
        if service_name not in self.services:
            return {"error": "未知服务"}
        
        service = self.services[service_name]
        pid = self._read_pid(service_name)
        
        status = {
            "name": service["name"],
            "script": service["script"],
            "description": service["description"],
            "running": False,
            "pid": None,
            "port": service["port"],
            "dependencies": service["dependencies"]
        }
        
        if pid and self._is_process_running(pid):
            status["running"] = True
            status["pid"] = pid
            
            # 获取进程信息
            try:
                process = psutil.Process(pid)
                status["cpu_percent"] = process.cpu_percent()
                status["memory_mb"] = process.memory_info().rss / 1024 / 1024
                status["start_time"] = process.create_time()
            except:
                pass
        
        return status
    
    def get_all_status(self) -> Dict[str, Dict]:
        """获取所有服务状态"""
        status = {}
        for service_name in self.services:
            status[service_name] = self.get_service_status(service_name)
        return status
    
    def show_status(self):
        """显示服务状态"""
        print("\n" + "="*80)
        print("BossJy 服务状态")
        print("="*80)
        
        status = self.get_all_status()
        all_running = True
        
        for service_name, service_status in status.items():
            status_icon = "✅" if service_status["running"] else "❌"
            pid_info = f" (PID: {service_status['pid']})" if service_status["running"] else ""
            port_info = f" (端口: {service_status['port']})" if service_status["port"] else ""
            
            print(f"{status_icon} {service_status['name']:<20} {service_status['script']}{pid_info}{port_info}")
            print(f"    {service_status['description']}")
            
            if service_status["running"] and "memory_mb" in service_status:
                print(f"    内存: {service_status['memory_mb']:.1f}MB, CPU: {service_status.get('cpu_percent', 0):.1f}%")
            
            print()
            
            if not service_status["running"]:
                all_running = False
        
        print("="*80)
        overall_status = "✅ 所有服务运行正常" if all_running else "❌ 部分服务未运行"
        print(overall_status)
        
        # 显示访问信息
        running_services = [s for s in status.values() if s["running"]]
        if running_services:
            print("\n📋 服务访问信息:")
            for service in running_services:
                if service["port"]:
                    print(f"• {service['name']}: http://localhost:{service['port']}")
                elif "Bot" in service["name"]:
                    print(f"• {service['name']}: 已启动，请在Telegram中使用")
        
        print(f"\n📁 日志目录: {self.log_dir}")
        print("🔧 管理命令:")
        print("  启动所有: python3 bossjy_starter.py start")
        print("  停止所有: python3 bossjy_starter.py stop")
        print("  重启所有: python3 bossjy_starter.py restart")
        print("  查看状态: python3 bossjy_starter.py status")
        print("  启动单个: python3 bossjy_starter.py start --service <service_name>")
        print("  停止单个: python3 bossjy_starter.py stop --service <service_name>")
    
    async def run_health_check(self) -> Dict:
        """运行健康检查"""
        health_status = {
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
            "overall": "healthy",
            "services": {}
        }
        
        for service_name in self.services:
            service_health = {
                "status": "healthy",
                "checks": {}
            }
            
            service_status = self.get_service_status(service_name)
            
            # 检查进程状态
            if service_status["running"]:
                service_health["checks"]["process"] = "running"
            else:
                service_health["checks"]["process"] = "stopped"
                service_health["status"] = "unhealthy"
                health_status["overall"] = "unhealthy"
            
            # 检查端口（如果有）
            if service_status["port"]:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex(('127.0.0.1', service_status["port"]))
                sock.close()
                
                if result == 0:
                    service_health["checks"]["port"] = "open"
                else:
                    service_health["checks"]["port"] = "closed"
                    service_health["status"] = "unhealthy"
                    health_status["overall"] = "unhealthy"
            
            # 检查日志文件
            log_file = self.log_dir / f"{service_name}.log"
            if log_file.exists():
                service_health["checks"]["log"] = "exists"
                
                # 检查最近的错误
                try:
                    with open(log_file, 'r') as f:
                        lines = f.readlines()
                        error_count = sum(1 for line in lines[-50:] if 'ERROR' in line)
                        if error_count > 5:
                            service_health["checks"]["recent_errors"] = f"{error_count} errors"
                            service_health["status"] = "degraded"
                except:
                    pass
            else:
                service_health["checks"]["log"] = "missing"
                service_health["status"] = "unhealthy"
                health_status["overall"] = "unhealthy"
            
            health_status["services"][service_name] = service_health
        
        return health_status
    
    async def show_health_check(self):
        """显示健康检查结果"""
        health = await self.run_health_check()
        
        print("\n" + "="*80)
        print("BossJy 健康检查")
        print("="*80)
        print(f"检查时间: {health['timestamp']}")
        print(f"整体状态: {health['overall']}")
        print()
        
        for service_name, service_health in health["services"].items():
            status_icon = "✅" if service_health["status"] == "healthy" else "⚠️" if service_health["status"] == "degraded" else "❌"
            print(f"{status_icon} {self.services[service_name]['name']}")
            
            for check_name, check_result in service_health["checks"].items():
                print(f"  {check_name}: {check_result}")
            
            print()
        
        print("="*80)

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="BossJy 服务启动器")
    parser.add_argument("action", choices=["start", "stop", "restart", "status", "health", "start-service", "stop-service"],
                       help="操作类型")
    parser.add_argument("--service", help="指定服务名称")
    parser.add_argument("--force", action="store_true", help="强制停止")
    parser.add_argument("--project-dir", help="项目目录")
    
    args = parser.parse_args()
    
    # 创建启动器
    starter = BossJyStarter(args.project_dir)
    
    # 执行操作
    if args.action == "start":
        if await starter.start_all():
            print("✅ 所有服务启动成功")
        else:
            print("❌ 部分服务启动失败")
            sys.exit(1)
            
    elif args.action == "stop":
        if await starter.stop_all(args.force):
            print("✅ 所有服务已停止")
        else:
            print("❌ 停止服务时出现错误")
            sys.exit(1)
            
    elif args.action == "restart":
        if await starter.restart_all(args.force):
            print("✅ 所有服务重启成功")
        else:
            print("❌ 重启服务时出现错误")
            sys.exit(1)
            
    elif args.action == "status":
        starter.show_status()
        
    elif args.action == "health":
        await starter.show_health_check()
        
    elif args.action == "start-service":
        if not args.service:
            print("❌ 请指定服务名称")
            sys.exit(1)
            
        if await starter.start_service(args.service):
            print(f"✅ {starter.services[args.service]['name']} 启动成功")
        else:
            print(f"❌ {starter.services[args.service]['name']} 启动失败")
            sys.exit(1)
            
    elif args.action == "stop-service":
        if not args.service:
            print("❌ 请指定服务名称")
            sys.exit(1)
            
        if await starter.stop_service(args.service, args.force):
            print(f"✅ {starter.services[args.service]['name']} 已停止")
        else:
            print(f"❌ 停止 {starter.services[args.service]['name']} 时出现错误")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())