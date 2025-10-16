#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用完整百家姓筛选印尼华人和澳洲香港人脚本
使用完整百家姓.csv文件进行精确筛选
"""

import pandas as pd
import os
import sys
from pathlib import Path
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载完整百家姓数据
def load_complete_surnames():
    """加载完整百家姓数据"""
    try:
        # 使用gbk编码读取
        df = pd.read_csv('D:/BossJy-Cn/BossJy-Cn/完整百家姓.csv', encoding='gbk')
        
        # 提取各种姓氏格式
        pinyin_surnames = set(df['拼音'].str.lower().dropna())
        indonesian_surnames = set()
        hongkong_surnames = set()
        
        # 处理印尼拼写（多个拼写用逗号分隔）
        for spellings in df['印尼拼寫'].dropna():
            for spelling in spellings.split(','):
                indonesian_surnames.add(spelling.strip().lower())
        
        # 处理香港英文（多个英文用逗号分隔）
        for english_names in df['香港英文'].dropna():
            for name in english_names.split(','):
                hongkong_surnames.add(name.strip().lower())
        
        logger.info(f"加载百家姓成功: 拼音姓氏 {len(pinyin_surnames)} 个, 印尼拼写 {len(indonesian_surnames)} 个, 香港英文 {len(hongkong_surnames)} 个")
        
        return pinyin_surnames, indonesian_surnames, hongkong_surnames
        
    except Exception as e:
        logger.error(f"加载百家姓失败: {str(e)}")
        return set(), set(), set()

# 加载数据
PINYIN_SURNAMES, INDONESIAN_SURNAMES, HONGKONG_SURNAMES = load_complete_surnames()

class ChineseNameFilter:
    """华人姓名筛选器"""
    
    def __init__(self):
        self.stats = {
            'total_files': 0,
            'total_rows': 0,
            'chinese_rows': 0,
            'files_processed': []
        }
    
    def is_indonesian_chinese(self, name):
        """检查是否是印尼华人姓名"""
        if not name or pd.isna(name):
            return False
        
        name = str(name).strip()
        if not name:
            return False
        
        # 分割姓名
        name_parts = name.split()
        if not name_parts:
            return False
        
        # 检查第一个部分是否是华人姓氏
        first_part = name_parts[0].lower()
        
        # 检查拼音姓氏
        if first_part in PINYIN_SURNAMES:
            return True
        
        # 检查印尼拼写
        if first_part in INDONESIAN_SURNAMES:
            return True
        
        return False
    
    def is_hongkong_chinese(self, name):
        """检查是否是香港华人姓名"""
        if not name or pd.isna(name):
            return False
        
        name = str(name).strip()
        if not name:
            return False
        
        # 分割姓名
        name_parts = name.split()
        if not name_parts:
            return False
        
        # 检查第一个部分是否是华人姓氏
        first_part = name_parts[0].lower()
        
        # 检查拼音姓氏
        if first_part in PINYIN_SURNAMES:
            return True
        
        # 检查香港英文
        if first_part in HONGKONG_SURNAMES:
            return True
        
        return False
    
    def find_name_columns(self, df):
        """查找姓名列"""
        possible_name_columns = []
        
        # 常见的姓名列名
        name_keywords = ['name', 'fullname', 'full_name', 'nama', 'nama jelas', '姓名', '名字', '全名']
        
        for column in df.columns:
            column_lower = str(column).lower()
            for keyword in name_keywords:
                if keyword in column_lower:
                    possible_name_columns.append(column)
                    break
        
        # 如果没找到，尝试查找包含字母的列
        if not possible_name_columns:
            for column in df.columns:
                # 检查列中是否包含类似姓名的数据
                sample_values = df[column].dropna().head(10).astype(str)
                if sample_values.str.contains(r'[a-zA-Z]', na=False).any():
                    # 检查是否看起来像姓名（通常2-30个字符）
                    avg_length = sample_values.str.len().mean()
                    if 2 <= avg_length <= 30:
                        possible_name_columns.append(column)
                        if len(possible_name_columns) >= 3:  # 最多取3个可能的列
                            break
        
        return possible_name_columns
    
    def filter_file(self, file_path, filter_type='indonesian'):
        """筛选单个文件"""
        try:
            logger.info(f"正在处理文件: {file_path}")
            
            # 读取文件
            if file_path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            elif file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path, encoding='utf-8')
            else:
                logger.warning(f"跳过不支持的文件格式: {file_path}")
                return None
            
            self.stats['total_rows'] += len(df)
            
            # 查找姓名列
            name_columns = self.find_name_columns(df)
            if not name_columns:
                logger.warning(f"未找到姓名列: {file_path}")
                return None
            
            logger.info(f"找到可能的姓名列: {name_columns}")
            
            # 筛选华人
            mask = pd.Series([False] * len(df))
            
            for col in name_columns:
                if col in df.columns:
                    if filter_type == 'indonesian':
                        col_mask = df[col].apply(self.is_indonesian_chinese)
                    else:  # hongkong
                        col_mask = df[col].apply(self.is_hongkong_chinese)
                    mask = mask | col_mask
            
            filtered_df = df[mask]
            chinese_count = len(filtered_df)
            self.stats['chinese_rows'] += chinese_count
            
            # 创建输出文件路径
            output_dir = file_path.parent / f"{filter_type}_filtered_complete"
            output_dir.mkdir(exist_ok=True)
            
            output_file = output_dir / f"filtered_{file_path.stem}{file_path.suffix}"
            
            # 保存筛选结果
            if file_path.suffix.lower() in ['.xlsx', '.xls']:
                filtered_df.to_excel(output_file, index=False)
            else:
                filtered_df.to_csv(output_file, index=False, encoding='utf-8')
            
            logger.info(f"筛选完成: {file_path} -> {output_file}")
            logger.info(f"总行数: {len(df)}, 华人行数: {chinese_count}, 占比: {chinese_count/len(df)*100:.2f}%")
            
            self.stats['files_processed'].append({
                'file': str(file_path),
                'total_rows': len(df),
                'chinese_rows': chinese_count,
                'output_file': str(output_file)
            })
            
            return output_file
            
        except Exception as e:
            logger.error(f"处理文件失败 {file_path}: {str(e)}")
            return None
    
    def process_directory(self, input_dir, filter_type='indonesian'):
        """处理整个目录"""
        input_path = Path(input_dir)
        if not input_path.exists():
            logger.error(f"目录不存在: {input_dir}")
            return
        
        logger.info(f"开始处理目录: {input_dir}")
        self.stats['total_files'] = 0
        
        # 查找所有Excel和CSV文件
        files = []
        for ext in ['*.xlsx', '*.xls', '*.csv']:
            files.extend(input_path.glob(ext))
        
        self.stats['total_files'] = len(files)
        logger.info(f"找到 {len(files)} 个文件")
        
        # 处理每个文件
        for file_path in files:
            self.filter_file(file_path, filter_type)
        
        # 打印统计信息
        self.print_stats(filter_type)
    
    def print_stats(self, filter_type):
        """打印统计信息"""
        logger.info("="*80)
        logger.info(f"{filter_type.title()}华人筛选统计 (使用完整百家姓)")
        logger.info("="*80)
        logger.info(f"总文件数: {self.stats['total_files']}")
        logger.info(f"总数据行数: {self.stats['total_rows']:,}")
        logger.info(f"华人数据行数: {self.stats['chinese_rows']:,}")
        
        if self.stats['total_rows'] > 0:
            percentage = (self.stats['chinese_rows'] / self.stats['total_rows']) * 100
            logger.info(f"华人占比: {percentage:.2f}%")
        
        logger.info("="*80)

def main():
    """主函数"""
    logger.info("="*80)
    logger.info("完整百家姓华人筛选工具")
    logger.info("="*80)
    
    # 创建筛选器
    filter = ChineseNameFilter()
    
    # 处理印尼数据
    logger.info("\n开始处理印尼数据...")
    indonesia_dir = "D:/BossJy-Cn/BossJy-Cn/data/uploads/印尼"
    filter.process_directory(indonesia_dir, 'indonesian')
    
    # 重置统计
    filter.stats = {
        'total_files': 0,
        'total_rows': 0,
        'chinese_rows': 0,
        'files_processed': []
    }
    
    # 处理澳洲数据
    logger.info("\n开始处理澳洲数据...")
    australia_dir = "D:/BossJy-Cn/BossJy-Cn/data/uploads/澳洲"
    filter.process_directory(australia_dir, 'hongkong')
    
    logger.info("\n处理完成！")

if __name__ == "__main__":
    main()