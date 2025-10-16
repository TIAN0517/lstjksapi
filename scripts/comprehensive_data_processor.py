#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合数据处理脚本
自动处理uploads目录下的所有数据文件，包括：
1. 筛选华人（印尼华人、澳洲香港人、其他地区华人）
2. 姓名翻译（拼音转中文）
3. 数据分类和整理
"""

import pandas as pd
import os
import sys
import time
from pathlib import Path
from datetime import datetime
import logging
import json
import shutil

# 配置日志
log_file = f"comprehensive_processing_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
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
        
        return pinyin_surnames, indonesian_surnames, hongkong_surnames, df
        
    except Exception as e:
        logger.error(f"加载百家姓失败: {str(e)}")
        return set(), set(), set(), pd.DataFrame()

# 加载数据
PINYIN_SURNAMES, INDONESIAN_SURNAMES, HONGKONG_SURNAMES, SURNAMES_DF = load_complete_surnames()

class ComprehensiveDataProcessor:
    """综合数据处理器"""
    
    def __init__(self):
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'failed_files': 0,
            'total_rows': 0,
            'chinese_rows': 0,
            'indonesian_chinese': 0,
            'hongkong_chinese': 0,
            'other_chinese': 0,
            'files_processed': [],
            'start_time': datetime.now()
        }
        
        # 创建输出目录结构
        self.create_output_structure()
        
        # 进度文件
        self.progress_file = f"comprehensive_progress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 加载之前的进度（如果存在）
        self.load_progress()
    
    def create_output_structure(self):
        """创建输出目录结构"""
        base_output = Path("D:/BossJy-Cn/BossJy-Cn/data/processed_data")
        
        # 主要分类目录
        self.output_dirs = {
            'indonesian_chinese': base_output / '印尼华人',
            'hongkong_chinese': base_output / '香港人',
            'other_chinese': base_output / '其他华人',
            'translated': base_output / '翻译数据',
            'original': base_output / '原始数据备份',
            'reports': base_output / '处理报告'
        }
        
        # 创建所有目录
        for dir_path in self.output_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"创建输出目录结构: {base_output}")
    
    def load_progress(self):
        """加载之前的进度"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                    self.stats['processed_files'] = progress.get('processed_files', 0)
                    self.stats['files_processed'] = progress.get('files_processed', [])
                logger.info(f"加载进度: 已处理 {self.stats['processed_files']} 个文件")
            except Exception as e:
                logger.warning(f"加载进度失败: {str(e)}")
    
    def save_progress(self):
        """保存进度"""
        progress = {
            'processed_files': self.stats['processed_files'],
            'files_processed': self.stats['files_processed'][-20:],  # 只保存最近20个文件
            'timestamp': datetime.now().isoformat()
        }
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存进度失败: {str(e)}")
    
    def translate_pinyin_name(self, pinyin_name):
        """翻译拼音姓名为中文"""
        if not pinyin_name or pd.isna(pinyin_name):
            return pinyin_name
        
        # 确保转换为字符串
        pinyin_name = str(pinyin_name).strip()
        if not pinyin_name:
            return pinyin_name
        
        name_parts = pinyin_name.split()
        if not name_parts:
            return pinyin_name
        
        # 翻译姓氏
        surname = name_parts[0].lower()
        chinese_surname = ''
        
        # 从百家姓中查找对应汉字
        if surname in PINYIN_SURNAMES:
            matching_rows = SURNAMES_DF[SURNAMES_DF['拼音'].str.lower() == surname]
            if not matching_rows.empty:
                chinese_surname = str(matching_rows.iloc[0]['漢字'])
        
        # 翻译名字（简单音译）
        given_name = ' '.join(name_parts[1:])
        chinese_given_name = self.phonetic_translate(given_name)
        
        return chinese_surname + chinese_given_name
    
    def phonetic_translate(self, pinyin):
        """简单音译"""
        if not pinyin:
            return ''
        
        # 简单音译映射
        phonetic_map = {
            'a': '阿', 'ai': '爱', 'an': '安', 'ang': '昂', 'ao': '奥',
            'ba': '巴', 'bai': '白', 'ban': '班', 'bang': '邦', 'bao': '宝',
            'bei': '贝', 'ben': '本', 'beng': '崩', 'bi': '比', 'bian': '边',
            'biao': '标', 'bie': '别', 'bin': '彬', 'bing': '兵', 'bo': '波',
            'bu': '布', 'ca': '擦', 'cai': '才', 'can': '参', 'cang': '仓',
            'cao': '草', 'ce': '策', 'cen': '岑', 'ceng': '层', 'cha': '查',
            'chan': '禅', 'chang': '昌', 'chao': '超', 'che': '车', 'chen': '晨',
            'cheng': '成', 'chi': '池', 'chong': '冲', 'chou': '愁', 'chu': '初',
            'chua': '蔡', 'chung': '钟', 'chow': '周', 'chan': '陈', 'chang': '张',
            'cheung': '蒋', 'ng': '吴', 'lam': '林', 'leung': '梁', 'tsang': '曾',
            'yip': '叶', 'mak': '麦', 'tse': '谢', 'yuen': '袁', 'szeto': '司徒',
            'lau': '刘', 'ho': '何', 'kwok': '郭', 'tam': '谭', 'poon': '潘',
            'fung': '冯', 'ko': '高', 'lee': '李', 'lai': '黎', 'wan': '尹',
            'tang': '邓', 'yeung': '杨', 'so': '苏', 'to': '杜', 'wong': '黄',
            'tan': '陈', 'lim': '林', 'ong': '王', 'teo': '张', 'goh': '吴',
            'koh': '许', 'sim': '沈', 'tay': '郑', 'chia': '谢', 'kang': '康',
            'yeo': '杨', 'chua': '蔡', 'gan': '颜', 'chong': '庄', 'yong': '雍',
            'heng': '恒', 'wee': '黄', 'ang': '洪', 'toh': '卓', 'soh': '苏',
            'seah': '余', 'sia': '谢', 'tjong': '庄', 'wijaya': '维查雅',
            'kusuma': '古斯玛', 'lie': '李', 'oei': '黄', 'ting': '丁'
        }
        
        # 尝试匹配
        for pinyin_part in pinyin.lower().split():
            if pinyin_part in phonetic_map:
                return phonetic_map[pinyin_part]
        
        # 如果没有匹配，返回第一个字符的音译
        if pinyin:
            first_char = pinyin[0].lower()
            return phonetic_map.get(first_char, pinyin)
        
        return pinyin
    
    def is_indonesian_chinese(self, name):
        """检查是否是印尼华人姓名"""
        if not name or pd.isna(name):
            return False
        
        name = str(name).strip()
        if not name:
            return False
        
        name_parts = name.split()
        if not name_parts:
            return False
        
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
        
        name_parts = name.split()
        if not name_parts:
            return False
        
        first_part = name_parts[0].lower()
        
        # 检查拼音姓氏
        if first_part in PINYIN_SURNAMES:
            return True
        
        # 检查香港英文
        if first_part in HONGKONG_SURNAMES:
            return True
        
        return False
    
    def is_chinese(self, name):
        """检查是否是华人姓名（通用）"""
        if not name or pd.isna(name):
            return False
        
        name = str(name).strip()
        if not name:
            return False
        
        name_parts = name.split()
        if not name_parts:
            return False
        
        first_part = name_parts[0].lower()
        
        # 检查拼音姓氏
        if first_part in PINYIN_SURNAMES:
            return True
        
        # 检查印尼拼写
        if first_part in INDONESIAN_SURNAMES:
            return True
        
        # 检查香港英文
        if first_part in HONGKONG_SURNAMES:
            return True
        
        return False
    
    def find_name_columns(self, df):
        """查找姓名列"""
        possible_name_columns = []
        
        # 常见的姓名列名
        name_keywords = [
            'name', 'fullname', 'full_name', 'first_name', 'last_name', 
            'customer_name', 'user_name', 'nama', 'nama jelas', 
            '姓名', '名字', '全名', '用户名', '客户名'
        ]
        
        for column in df.columns:
            column_lower = str(column).lower()
            for keyword in name_keywords:
                if keyword in column_lower:
                    possible_name_columns.append(column)
                    break
        
        # 如果没找到，尝试查找包含字母的列
        if not possible_name_columns:
            for column in df.columns:
                try:
                    sample_values = df[column].dropna().head(10).astype(str)
                    if sample_values.str.contains(r'[a-zA-Z]', na=False).any():
                        avg_length = sample_values.str.len().mean()
                        if 2 <= avg_length <= 30:
                            possible_name_columns.append(column)
                            if len(possible_name_columns) >= 3:
                                break
                except:
                    continue
        
        return possible_name_columns
    
    def process_file(self, file_path):
        """处理单个文件"""
        try:
            # 检查是否已经处理过
            if str(file_path) in [f['file'] for f in self.stats['files_processed']]:
                logger.info(f"跳过已处理的文件: {file_path}")
                return None
            
            logger.info(f"正在处理文件: {file_path}")
            
            # 读取文件
            if file_path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            elif file_path.suffix.lower() == '.csv':
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(file_path, encoding='latin1')
                    except UnicodeDecodeError:
                        df = pd.read_csv(file_path, encoding='cp1252')
            elif file_path.suffix.lower() == '.sql':
                logger.info(f"跳过SQL文件: {file_path}")
                return None
            else:
                logger.warning(f"跳过不支持的文件格式: {file_path}")
                return None
            
            original_count = len(df)
            self.stats['total_rows'] += original_count
            
            # 查找姓名列
            name_columns = self.find_name_columns(df)
            if not name_columns:
                logger.warning(f"未找到姓名列: {file_path}")
                return None
            
            logger.info(f"找到可能的姓名列: {name_columns}")
            
            # 备份原始文件
            backup_file = self.output_dirs['original'] / file_path.name
            if file_path.suffix.lower() in ['.xlsx', '.xls']:
                df.to_excel(backup_file, index=False)
            else:
                df.to_csv(backup_file, index=False, encoding='utf-8')
            
            # 创建分类标记
            df['is_chinese'] = False
            df['is_indonesian_chinese'] = False
            df['is_hongkong_chinese'] = False
            df['chinese_category'] = '非华人'
            df['chinese_name_translated'] = ''
            
            # 筛选和分类
            for col in name_columns:
                if col in df.columns:
                    # 标记华人
                    chinese_mask = df[col].apply(self.is_chinese)
                    df.loc[chinese_mask, 'is_chinese'] = True
                    
                    # 标记印尼华人
                    indonesian_mask = df[col].apply(self.is_indonesian_chinese)
                    df.loc[indonesian_mask, 'is_indonesian_chinese'] = True
                    
                    # 标记香港人
                    hongkong_mask = df[col].apply(self.is_hongkong_chinese)
                    df.loc[hongkong_mask, 'is_hongkong_chinese'] = True
                    
                    # 翻译姓名
                    for idx in df[chinese_mask].index:
                        original_name = df.loc[idx, col]
                        translated_name = self.translate_pinyin_name(original_name)
                        df.loc[idx, 'chinese_name_translated'] = translated_name
            
            # 设置分类
            df.loc[df['is_indonesian_chinese'], 'chinese_category'] = '印尼华人'
            df.loc[df['is_hongkong_chinese'], 'chinese_category'] = '香港人'
            df.loc[(df['is_chinese']) & (~df['is_indonesian_chinese']) & (~df['is_hongkong_chinese']), 'chinese_category'] = '其他华人'
            
            # 统计各类别人数
            chinese_count = df['is_chinese'].sum()
            indonesian_count = df['is_indonesian_chinese'].sum()
            hongkong_count = df['is_hongkong_chinese'].sum()
            other_count = chinese_count - indonesian_count - hongkong_count
            
            self.stats['chinese_rows'] += chinese_count
            self.stats['indonesian_chinese'] += indonesian_count
            self.stats['hongkong_chinese'] += hongkong_count
            self.stats['other_chinese'] += other_count
            
            # 保存分类后的文件
            base_name = f"processed_{file_path.stem}"
            
            # 保存完整处理后的文件
            processed_file = self.output_dirs['translated'] / f"{base_name}{file_path.suffix}"
            if file_path.suffix.lower() in ['.xlsx', '.xls']:
                df.to_excel(processed_file, index=False)
            else:
                df.to_csv(processed_file, index=False, encoding='utf-8')
            
            # 保存印尼华人数据
            if indonesian_count > 0:
                indonesian_df = df[df['is_indonesian_chinese']]
                indonesian_file = self.output_dirs['indonesian_chinese'] / f"indonesian_{file_path.stem}{file_path.suffix}"
                if file_path.suffix.lower() in ['.xlsx', '.xls']:
                    indonesian_df.to_excel(indonesian_file, index=False)
                else:
                    indonesian_df.to_csv(indonesian_file, index=False, encoding='utf-8')
            
            # 保存香港人数据
            if hongkong_count > 0:
                hongkong_df = df[df['is_hongkong_chinese']]
                hongkong_file = self.output_dirs['hongkong_chinese'] / f"hongkong_{file_path.stem}{file_path.suffix}"
                if file_path.suffix.lower() in ['.xlsx', '.xls']:
                    hongkong_df.to_excel(hongkong_file, index=False)
                else:
                    hongkong_df.to_csv(hongkong_file, index=False, encoding='utf-8')
            
            # 保存其他华人数据
            if other_count > 0:
                other_df = df[(df['is_chinese']) & (~df['is_indonesian_chinese']) & (~df['is_hongkong_chinese'])]
                other_file = self.output_dirs['other_chinese'] / f"other_{file_path.stem}{file_path.suffix}"
                if file_path.suffix.lower() in ['.xlsx', '.xls']:
                    other_df.to_excel(other_file, index=False)
                else:
                    other_df.to_csv(other_file, index=False, encoding='utf-8')
            
            # 记录处理结果
            result = {
                'file': str(file_path),
                'total_rows': original_count,
                'chinese_rows': int(chinese_count),
                'indonesian_chinese': int(indonesian_count),
                'hongkong_chinese': int(hongkong_count),
                'other_chinese': int(other_count),
                'chinese_percentage': (chinese_count/original_count*100) if original_count > 0 else 0
            }
            self.stats['files_processed'].append(result)
            self.stats['processed_files'] += 1
            
            logger.info(f"处理完成: {file_path}")
            logger.info(f"总行数: {original_count}, 华人: {chinese_count} ({result['chinese_percentage']:.2f}%)")
            logger.info(f"  印尼华人: {indonesian_count}, 香港人: {hongkong_count}, 其他华人: {other_count}")
            
            # 保存进度
            self.save_progress()
            
            return result
            
        except Exception as e:
            logger.error(f"处理文件失败 {file_path}: {str(e)}")
            self.stats['failed_files'] += 1
            return None
    
    def process_all_directories(self):
        """处理所有目录"""
        base_path = Path("D:/BossJy-Cn/BossJy-Cn/data/uploads")
        
        if not base_path.exists():
            logger.error(f"目录不存在: {base_path}")
            return
        
        logger.info(f"开始处理所有目录: {base_path}")
        
        # 查找所有文件
        all_files = []
        for ext in ['*.xlsx', '*.xls', '*.csv']:
            all_files.extend(base_path.rglob(ext))
        
        # 排除已处理的文件
        processed_files = set()
        for output_dir in self.output_dirs.values():
            if output_dir.exists():
                for file_path in output_dir.rglob('*'):
                    if file_path.is_file():
                        processed_files.add(file_path.name)
        
        # 过滤未处理的文件
        files_to_process = [f for f in all_files if f.name not in processed_files]
        
        self.stats['total_files'] = len(files_to_process)
        logger.info(f"找到 {len(files_to_process)} 个待处理文件")
        
        # 处理每个文件
        for i, file_path in enumerate(files_to_process):
            logger.info(f"进度: {i+1}/{len(files_to_process)} - {file_path.name}")
            self.process_file(file_path)
            
            # 每10个文件打印一次统计
            if (i + 1) % 10 == 0:
                self.print_stats(intermediate=True)
        
        # 生成最终报告
        self.generate_final_report()
        
        # 打印最终统计
        self.print_stats()
    
    def generate_final_report(self):
        """生成最终处理报告"""
        report_file = self.output_dirs['reports'] / f"processing_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("综合数据处理报告\n")
            f.write("="*80 + "\n")
            f.write(f"处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总耗时: {datetime.now() - self.stats['start_time']}\n")
            f.write("\n统计信息:\n")
            f.write(f"  总文件数: {self.stats['total_files']}\n")
            f.write(f"  成功处理: {self.stats['processed_files']}\n")
            f.write(f"  处理失败: {self.stats['failed_files']}\n")
            f.write(f"  总数据行数: {self.stats['total_rows']:,}\n")
            f.write(f"  华人数据行数: {self.stats['chinese_rows']:,}\n")
            f.write(f"  印尼华人: {self.stats['indonesian_chinese']:,}\n")
            f.write(f"  香港人: {self.stats['hongkong_chinese']:,}\n")
            f.write(f"  其他华人: {self.stats['other_chinese']:,}\n")
            
            if self.stats['total_rows'] > 0:
                percentage = (self.stats['chinese_rows'] / self.stats['total_rows']) * 100
                f.write(f"  华人占比: {percentage:.2f}%\n")
            
            f.write("\n输出目录:\n")
            for name, path in self.output_dirs.items():
                f.write(f"  {name}: {path}\n")
            
            f.write("\n处理详情:\n")
            for result in self.stats['files_processed']:
                f.write(f"  文件: {result['file']}\n")
                f.write(f"    总行数: {result['total_rows']}, 华人: {result['chinese_rows']} ({result['chinese_percentage']:.2f}%)\n")
                f.write(f"    印尼华人: {result['indonesian_chinese']}, 香港人: {result['hongkong_chinese']}, 其他华人: {result['other_chinese']}\n")
        
        logger.info(f"处理报告已保存到: {report_file}")
    
    def print_stats(self, intermediate=False):
        """打印统计信息"""
        status = "中间统计" if intermediate else "最终统计"
        logger.info("="*80)
        logger.info(f"综合数据处理{status}")
        logger.info("="*80)
        logger.info(f"总文件数: {self.stats['total_files']}")
        logger.info(f"已处理文件: {self.stats['processed_files']}")
        logger.info(f"处理失败: {self.stats['failed_files']}")
        logger.info(f"总数据行数: {self.stats['total_rows']:,}")
        logger.info(f"华人数据行数: {self.stats['chinese_rows']:,}")
        logger.info(f"  印尼华人: {self.stats['indonesian_chinese']:,}")
        logger.info(f"  香港人: {self.stats['hongkong_chinese']:,}")
        logger.info(f"  其他华人: {self.stats['other_chinese']:,}")
        
        if self.stats['total_rows'] > 0:
            percentage = (self.stats['chinese_rows'] / self.stats['total_rows']) * 100
            logger.info(f"华人占比: {percentage:.2f}%")
        
        if not intermediate:
            elapsed = datetime.now() - self.stats['start_time']
            logger.info(f"总耗时: {elapsed}")
        
        logger.info("="*80)

def main():
    """主函数"""
    logger.info("="*80)
    logger.info("综合数据处理工具")
    logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"日志文件: {log_file}")
    logger.info("="*80)
    
    # 创建处理器
    processor = ComprehensiveDataProcessor()
    
    try:
        # 处理所有目录
        processor.process_all_directories()
        
        logger.info("\n所有处理完成！")
        
    except KeyboardInterrupt:
        logger.info("\n用户中断，但进度已保存")
    except Exception as e:
        logger.error(f"处理过程中发生错误: {str(e)}")
    finally:
        logger.info(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
