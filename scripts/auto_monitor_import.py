#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动监控和入库脚本
监控数据处理进度，完成后自动入库
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime
import logging
import subprocess

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 配置日志
log_file = f"auto_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutoMonitor:
    """自动监控器"""
    
    def __init__(self):
        self.processed_data_path = Path("D:/BossJy-Cn/BossJy-Cn/data/processed_data")
        self.progress_files = list(Path("D:/BossJy-Cn/BossJy-Cn").glob("comprehensive_progress_*.json"))
        self.check_interval = 300  # 5分钟检查一次
        
    def get_latest_progress(self):
        """获取最新进度"""
        if not self.progress_files:
            return None
        
        latest_file = max(self.progress_files, key=lambda x: x.stat().st_mtime)
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                progress = json.load(f)
            return progress
        except:
            return None
    
    def is_processing_complete(self):
        """检查处理是否完成"""
        progress = self.get_latest_progress()
        if not progress:
            return False
        
        # 检查是否有进度文件
        log_files = list(Path("D:/BossJy-Cn/BossJy-Cn").glob("comprehensive_processing_*.log"))
        if not log_files:
            return False
        
        # 检查最新的日志文件
        latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
        
        # 检查日志文件最后修改时间
        last_modified = latest_log.stat().st_mtime
        current_time = time.time()
        
        # 如果超过10分钟没有更新，认为处理完成
        if current_time - last_modified > 600:
            logger.info("检测到处理已完成（10分钟无更新）")
            return True
        
        return False
    
    def run_import_script(self):
        """运行入库脚本"""
        logger.info("开始运行数据入库脚本...")
        
        try:
            # 运行入库脚本
            result = subprocess.run(
                ['python', 'scripts/import_chinese_data.py'],
                cwd='D:/BossJy-Cn/BossJy-Cn',
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                logger.info("数据入库完成！")
                logger.info(f"输出: {result.stdout}")
            else:
                logger.error(f"入库失败: {result.stderr}")
                
        except Exception as e:
            logger.error(f"运行入库脚本失败: {str(e)}")
    
    def monitor_and_import(self):
        """监控并自动入库"""
        logger.info("开始监控数据处理进度...")
        
        while True:
            try:
                # 检查处理是否完成
                if self.is_processing_complete():
                    logger.info("数据处理已完成，准备入库...")
                    
                    # 等待2分钟确保文件写入完成
                    time.sleep(120)
                    
                    # 运行入库脚本
                    self.run_import_script()
                    
                    # 通知用户
                    self.send_completion_notification()
                    
                    break
                else:
                    # 打印当前进度
                    progress = self.get_latest_progress()
                    if progress:
                        logger.info(f"当前进度: 已处理 {progress.get('processed_files', 0)} 个文件")
                    
                    # 等待下次检查
                    time.sleep(self.check_interval)
                    
            except KeyboardInterrupt:
                logger.info("用户中断监控")
                break
            except Exception as e:
                logger.error(f"监控过程出错: {str(e)}")
                time.sleep(60)  # 出错后等待1分钟再继续
    
    def send_completion_notification(self):
        """发送完成通知"""
        logger.info("="*80)
        logger.info("数据处理和入库全部完成！")
        logger.info("="*80)
        logger.info("数据库已准备就绪，Bot可以开始查询华人数据")
        logger.info("数据库位置: D:/BossJy-Cn/BossJy-Cn/data/chinese_database.db")
        logger.info("="*80)

def main():
    """主函数"""
    logger.info("="*80)
    logger.info("自动监控和入库工具")
    logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)
    
    monitor = AutoMonitor()
    
    try:
        monitor.monitor_and_import()
    except Exception as e:
        logger.error(f"监控失败: {str(e)}")

if __name__ == "__main__":
    main()