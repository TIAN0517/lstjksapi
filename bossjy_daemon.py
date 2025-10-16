#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BossJy-Pro 守护进程管理器
自动启动所有服务并提供自动重启功能
"""

import os
import sys
import time
import signal
import subprocess
import logging
import psutil
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List

# 项目路径
PROJECT_DIR = Path(__file__).parent.absolute()
LOG_DIR = PROJECT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "daemon.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("BossJyDaemon")

class ServiceStatus:
    """服务状态枚举"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    FAILED = "failed"
    RESTARTING = "restarting"

class Service:
    """服务管理基类"""

    def __init__(self, name: str, restart_delay: int = 5, max_retries: int = 3):
        self.name = name
        self.status = ServiceStatus.STOPPED
        self.process: Optional[subprocess.Popen] = None
        self.restart_delay = restart_delay
        self.max_retries = max_retries
        self.retry_count = 0
        self.last_restart = None
        self.start_time = None

    def is_healthy(self) -> bool:
        """检查服务健康状态"""
        raise NotImplementedError

    def start(self) -> bool:
        """启动服务"""
        raise NotImplementedError

    def stop(self) -> bool:
        """停止服务"""
        raise NotImplementedError

    def restart(self) -> bool:
        """重启服务"""
        logger.info(f"重启服务: {self.name}")
        self.status = ServiceStatus.RESTARTING
        self.stop()
        time.sleep(self.restart_delay)
        return self.start()

class DockerService(Service):
    """Docker服务管理"""

    def __init__(self):
        super().__init__("Docker Compose", restart_delay=10)
        self.container_names = ["bossjy-pro-app", "bossjy-postgres", "bossjy-redis"]

    def is_healthy(self) -> bool:
        """检查Docker容器健康状态"""
        try:
            result = subprocess.run(
                ["docker", "compose", "ps", "-q"],
                cwd=PROJECT_DIR,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return False

            # 检查所有容器是否运行
            for container in self.container_names:
                check_result = subprocess.run(
                    ["docker", "inspect", "-f", "{{.State.Running}}", container],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if check_result.stdout.strip() != "true":
                    logger.warning(f"容器 {container} 未运行")
                    return False

            return True

        except Exception as e:
            logger.error(f"检查Docker容器失败: {e}")
            return False

    def start(self) -> bool:
        """启动Docker服务"""
        try:
            logger.info("启动Docker Compose服务...")
            self.status = ServiceStatus.STARTING

            # 启动容器
            result = subprocess.run(
                ["docker", "compose", "up", "-d", "postgres", "redis", "app"],
                cwd=PROJECT_DIR,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                logger.error(f"Docker启动失败: {result.stderr}")
                self.status = ServiceStatus.FAILED
                return False

            # 等待容器健康检查
            logger.info("等待容器健康检查...")
            for i in range(30):
                time.sleep(2)
                if self.is_healthy():
                    logger.info("✅ Docker容器启动成功")
                    self.status = ServiceStatus.RUNNING
                    self.start_time = datetime.now()
                    self.retry_count = 0
                    return True

            logger.error("Docker容器健康检查超时")
            self.status = ServiceStatus.FAILED
            return False

        except Exception as e:
            logger.error(f"启动Docker服务失败: {e}")
            self.status = ServiceStatus.FAILED
            return False

    def stop(self) -> bool:
        """停止Docker服务"""
        try:
            logger.info("停止Docker Compose服务...")
            subprocess.run(
                ["docker", "compose", "down"],
                cwd=PROJECT_DIR,
                timeout=30
            )
            self.status = ServiceStatus.STOPPED
            return True
        except Exception as e:
            logger.error(f"停止Docker服务失败: {e}")
            return False

class FlaskWebService(Service):
    """Flask Web服务管理"""

    def __init__(self):
        super().__init__("Flask Web", restart_delay=5)
        self.port = 5000
        self.pid_file = "/tmp/bossjy-web.pid"

    def is_healthy(self) -> bool:
        """检查Flask服务健康状态"""
        try:
            # 检查进程
            if os.path.exists(self.pid_file):
                with open(self.pid_file) as f:
                    pid = int(f.read().strip())
                    if psutil.pid_exists(pid):
                        proc = psutil.Process(pid)
                        if proc.is_running() and "gunicorn" in proc.name().lower():
                            return True

            # 检查端口
            for conn in psutil.net_connections():
                if conn.laddr.port == self.port and conn.status == 'LISTEN':
                    return True

            return False

        except Exception as e:
            logger.error(f"检查Flask服务失败: {e}")
            return False

    def start(self) -> bool:
        """启动Flask Web服务"""
        try:
            logger.info("启动Flask Web服务...")
            self.status = ServiceStatus.STARTING

            # 停止旧进程
            self.stop()

            # 启动Gunicorn
            venv_python = PROJECT_DIR / "venv" / "bin" / "python3"
            gunicorn_bin = PROJECT_DIR / "venv" / "bin" / "gunicorn"

            if not gunicorn_bin.exists():
                # 尝试系统gunicorn
                gunicorn_bin = "gunicorn"

            cmd = [
                str(gunicorn_bin),
                "-w", "4",
                "-b", f"127.0.0.1:{self.port}",
                "--daemon",
                "--pid", self.pid_file,
                "--access-logfile", str(LOG_DIR / "web-access.log"),
                "--error-logfile", str(LOG_DIR / "web-error.log"),
                "--timeout", "120",
                "--graceful-timeout", "30",
                "app.web_app:app"
            ]

            result = subprocess.run(
                cmd,
                cwd=PROJECT_DIR,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                logger.error(f"Flask启动失败: {result.stderr}")
                self.status = ServiceStatus.FAILED
                return False

            # 等待启动
            time.sleep(3)

            if self.is_healthy():
                logger.info("✅ Flask Web服务启动成功")
                self.status = ServiceStatus.RUNNING
                self.start_time = datetime.now()
                self.retry_count = 0
                return True
            else:
                logger.error("Flask Web服务启动后健康检查失败")
                self.status = ServiceStatus.FAILED
                return False

        except Exception as e:
            logger.error(f"启动Flask Web服务失败: {e}")
            self.status = ServiceStatus.FAILED
            return False

    def stop(self) -> bool:
        """停止Flask Web服务"""
        try:
            # 通过PID文件停止
            if os.path.exists(self.pid_file):
                with open(self.pid_file) as f:
                    pid = int(f.read().strip())
                    if psutil.pid_exists(pid):
                        proc = psutil.Process(pid)
                        proc.terminate()
                        proc.wait(timeout=10)
                os.remove(self.pid_file)

            # 杀掉所有gunicorn进程
            for proc in psutil.process_iter(['name', 'cmdline']):
                try:
                    if 'gunicorn' in proc.name().lower():
                        if 'web_app' in ' '.join(proc.cmdline()):
                            proc.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            self.status = ServiceStatus.STOPPED
            return True

        except Exception as e:
            logger.error(f"停止Flask Web服务失败: {e}")
            return False

class TelegramBotService(Service):
    """Telegram Bot服务管理"""

    def __init__(self):
        super().__init__("Telegram Bot", restart_delay=10)
        self.bot_script = PROJECT_DIR / "start_full_bot.py"
        self.pid_file = "/tmp/bossjy-telegram-bot.pid"

    def is_healthy(self) -> bool:
        """检查Bot健康状态"""
        try:
            if not os.path.exists(self.pid_file):
                return False

            with open(self.pid_file) as f:
                pid = int(f.read().strip())

            if not psutil.pid_exists(pid):
                return False

            proc = psutil.Process(pid)
            if not proc.is_running():
                return False

            # 检查是否是我们的Bot进程
            cmdline = ' '.join(proc.cmdline())
            if 'start_full_bot.py' in cmdline:
                return True

            return False

        except Exception as e:
            logger.error(f"检查Telegram Bot失败: {e}")
            return False

    def start(self) -> bool:
        """启动Telegram Bot"""
        try:
            logger.info("启动Telegram Bot服务...")
            self.status = ServiceStatus.STARTING

            # 停止旧进程
            self.stop()

            # 启动Bot
            python_bin = PROJECT_DIR / "venv" / "bin" / "python3"
            if not python_bin.exists():
                python_bin = "python3"

            # 使用nohup在后台运行
            log_file = LOG_DIR / "telegram-bot.log"
            cmd = f"nohup {python_bin} {self.bot_script} >> {log_file} 2>&1 & echo $! > {self.pid_file}"

            result = subprocess.run(
                cmd,
                shell=True,
                cwd=PROJECT_DIR,
                timeout=10
            )

            # 等待启动
            time.sleep(5)

            if self.is_healthy():
                logger.info("✅ Telegram Bot服务启动成功")
                self.status = ServiceStatus.RUNNING
                self.start_time = datetime.now()
                self.retry_count = 0
                return True
            else:
                logger.error("Telegram Bot启动后健康检查失败")
                self.status = ServiceStatus.FAILED
                return False

        except Exception as e:
            logger.error(f"启动Telegram Bot失败: {e}")
            self.status = ServiceStatus.FAILED
            return False

    def stop(self) -> bool:
        """停止Telegram Bot"""
        try:
            if os.path.exists(self.pid_file):
                with open(self.pid_file) as f:
                    pid = int(f.read().strip())

                if psutil.pid_exists(pid):
                    proc = psutil.Process(pid)
                    proc.terminate()
                    proc.wait(timeout=10)

                os.remove(self.pid_file)

            # 杀掉所有相关进程
            for proc in psutil.process_iter(['cmdline']):
                try:
                    cmdline = ' '.join(proc.cmdline())
                    if 'start_full_bot.py' in cmdline:
                        proc.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            self.status = ServiceStatus.STOPPED
            return True

        except Exception as e:
            logger.error(f"停止Telegram Bot失败: {e}")
            return False

class DaemonManager:
    """守护进程管理器"""

    def __init__(self):
        self.services: List[Service] = [
            DockerService(),
            FlaskWebService(),
            TelegramBotService()
        ]
        self.running = False
        self.check_interval = 30  # 30秒检查一次

    def start_all(self) -> bool:
        """启动所有服务"""
        logger.info("=" * 60)
        logger.info("🚀 BossJy-Pro 守护进程管理器启动")
        logger.info("=" * 60)

        success = True
        for service in self.services:
            logger.info(f"启动服务: {service.name}")
            if not service.start():
                logger.error(f"服务 {service.name} 启动失败")
                success = False
            else:
                logger.info(f"✅ {service.name} 已启动")

        return success

    def stop_all(self):
        """停止所有服务"""
        logger.info("停止所有服务...")
        for service in reversed(self.services):
            logger.info(f"停止服务: {service.name}")
            service.stop()

    def check_and_restart(self):
        """检查并重启失败的服务"""
        for service in self.services:
            try:
                if service.status == ServiceStatus.RUNNING:
                    if not service.is_healthy():
                        logger.warning(f"服务 {service.name} 健康检查失败")

                        # 检查重试次数
                        if service.retry_count >= service.max_retries:
                            logger.error(f"服务 {service.name} 达到最大重试次数，停止重启")
                            service.status = ServiceStatus.FAILED
                            continue

                        # 重启服务
                        service.retry_count += 1
                        service.last_restart = datetime.now()
                        logger.info(f"尝试重启 {service.name} (第 {service.retry_count}/{service.max_retries} 次)")

                        if service.restart():
                            logger.info(f"✅ {service.name} 重启成功")
                        else:
                            logger.error(f"❌ {service.name} 重启失败")

            except Exception as e:
                logger.error(f"检查服务 {service.name} 时出错: {e}")

    def print_status(self):
        """打印服务状态"""
        logger.info("-" * 60)
        logger.info("服务状态汇总:")
        for service in self.services:
            status_icon = "✅" if service.status == ServiceStatus.RUNNING else "❌"
            uptime = ""
            if service.start_time:
                uptime = f"(运行时长: {datetime.now() - service.start_time})"
            logger.info(f"  {status_icon} {service.name}: {service.status} {uptime}")
        logger.info("-" * 60)

    def run(self):
        """运行守护进程"""
        self.running = True

        # 启动所有服务
        if not self.start_all():
            logger.error("部分服务启动失败，但将继续监控")

        logger.info(f"守护进程已启动，每 {self.check_interval} 秒检查一次服务状态")
        logger.info("按 Ctrl+C 停止守护进程")

        try:
            while self.running:
                time.sleep(self.check_interval)
                self.check_and_restart()
                self.print_status()

        except KeyboardInterrupt:
            logger.info("收到停止信号...")
        finally:
            self.stop_all()
            logger.info("守护进程已停止")

def main():
    """主函数"""
    # 处理信号
    manager = DaemonManager()

    def signal_handler(signum, frame):
        logger.info(f"收到信号 {signum}")
        manager.running = False

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 运行守护进程
    manager.run()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"守护进程错误: {e}")
        sys.exit(1)
