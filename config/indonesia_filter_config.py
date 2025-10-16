#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印尼华人筛选配置
基于完整百家姓CSV文件的印尼拼音映射
"""

import pandas as pd
from pathlib import Path

# ==================== 印尼华人姓氏映射 ====================
# 从CSV文件加载的中文-印尼拼音映射
INDONESIAN_SURNAME_MAPPING = {
    # 基于完整百家姓.csv的映射
    'zhao': ['Tio', 'Tjio', 'Tjauw'],
    'qian': ['Tjien', 'Tjin'],
    'sun': ['Swie', 'Soon', 'Swan'],
    'li': ['Lie', 'Liem', 'Lee'],
    'zhou': ['Tjioe', 'Tjoe'],
    'wu': ['Go', 'Gouw', 'Ngo'],
    'zheng': ['Tjeng', 'Tjiang'],
    'wang': ['Ong', 'Oei Ong', 'Oey Ong'],
    'feng': ['Hong', 'Pheng'],
    'chen': ['Tan', 'Tjan', 'Chan'],
    'chu': ['Tjo', 'Tju', 'Tjoei'],
    'wei': ['Oei', 'Oey', 'Wie'],
    'jiang': ['Tjiang', 'Nio Tjiang'],
    'shen': ['Sim', 'Sie', 'Tjin Shen'],
    'han': ['Han', 'Handojo'],
    'yang': ['Njoo', 'Nio', 'Jaya'],
    'zhu': ['Tjoa', 'Tju', 'Chua'],
    'qin': ['Tjin', 'Tjing'],
    'you': ['Yauw', 'Yoe', 'Yo'],
    'xu': ['Hsu', 'Sie', 'Tjio'],
    'he': ['Ho', 'Oho', 'Hoe'],
    'lu': ['Loo', 'Lo', 'Lau'],
    'shi': ['Sie', 'Si'],
    'zhang': ['Tjoa', 'Tjiang', 'Tjung'],
    'kong': ['Khong', 'Khoe'],
    'cao': ['Tjauw', 'Tjau'],
    'yan': ['Njoan', 'Njan', 'Yan'],
    'hua': ['Hwa', 'Hoa'],
    'jin': ['Kim', 'Djim'],
    'tao': ['Tho', 'Tjo'],
    'qi': ['Tjie', 'Tjhi'],
    'xie': ['Sie', 'Tjia', 'Tjhia'],
    'zou': ['Tjauw', 'Tjio'],
    'yu': ['Oei', 'Oey', 'Juwono'],
    'bai': ['Pek', 'Phoa'],
    'su': ['Soe', 'Soewondo'],
    'pan': ['Phan', 'Phang'],
    'ge': ['Gie', 'Goey'],
    'dou': ['Siek', 'Sie'],
    'fan': ['Phan', 'Phaan'],
    'yun': ['Pang', 'Phang'],
    'ma': ['Oen Ma', 'Ma'],
    'huang': ['Oei', 'Oey', 'Oeywie'],
    'xi': ['Lo', 'Loo', 'Lau'],
    'peng': ['Pang', 'Phang'],
    'lang': ['Siauw', 'Sioe'],
    'lu': ['Tjhan', 'Tjan'],
    'ji': ['Kie', 'Djie'],
    'cheng': ['Tjeng', 'Tjing'],
    'dai': ['Tai', 'Tjai'],
    'miao': ['Tham', 'Thamto'],
    'song': ['Soong', 'Soeng'],
    'long': ['Pang', 'Phang'],
    # 更多姓氏映射...
}

# ==================== 印尼特有姓氏 ====================
INDONESIAN_SPECIFIC_SURNAMES = {
    # 常见印尼华人姓氏
    'tan', 'lie', 'lim', 'gozali', 'halim', 'kusuma', 'wijaya',
    'santoso', 'wibowo', 'setiawan', 'pratama', 'kurniawan',
    'sutanto', 'haryanto', 'rahmanto', 'susanto', 'indrawan',
    # 印尼化的中文姓氏
    'salim', 'widjaja', 'tanoko', 'santoso', 'wibowo'
}

# ==================== 印尼电话号码规则 ====================
INDONESIA_PHONE_RULES = {
    'prefixes': {
        # 印尼本地号码
        '62': 0.9,        # 印尼国家码
        '08': 0.8,        # 印尼手机
        '021': 0.7,       # 雅加达
        '022': 0.6,       # 万隆
        '031': 0.6,       # 泗水
        '024': 0.5,       # 三宝垄
        '0271': 0.5,      # 梭罗
        
        # 国际号码（印尼华人常用）
        '65': 0.4,        # 新加坡
        '60': 0.3,        # 马来西亚
        '852': 0.2,       # 香港
        '853': 0.2,       # 澳门
    },
    'length': {
        'indonesia': [10, 11, 12, 13],  # 印尼号码长度
        'mobile': [11, 12, 13],        # 手机长度
        'landline': [9, 10, 11]        # 固话长度
    }
}

# ==================== 印尼邮箱域名规则 ====================
INDONESIA_EMAIL_RULES = {
    'high_confidence': {
        # 印尼本地邮箱
        'gmail.com': 0.8,  # 印尼最常用
        'yahoo.com': 0.7,
        'yahoo.co.id': 0.9,
        'outlook.com': 0.6,
        'hotmail.com': 0.5,
        
        # 印尼企业邮箱
        'telkom.net': 0.8,
        'indosat.net.id': 0.8,
        'xl.co.id': 0.8,
        
        # 印尼教育邮箱
        'ac.id': 0.8,     # 印尼大学
        'sch.id': 0.7,    # 印尼学校
    },
    'medium_confidence': {
        'rocketmail.com': 0.5,
        'mail.com': 0.4,
        'inbox.com': 0.4,
        
        # 中文邮箱（印尼华人也可能使用）
        'qq.com': 0.4,
        '163.com': 0.3,
        '126.com': 0.3,
        'sina.com': 0.3,
    },
    'low_confidence': {
        'facebook.com': 0.2,
        'twitter.com': 0.2,
        'instagram.com': 0.2,
    }
}

# ==================== 置信度阈值 ====================
CONFIDENCE_THRESHOLDS = {
    'HIGH': 0.8,       # 高置信度
    'MEDIUM': 0.6,     # 中等置信度
    'LOW': 0.4         # 低置信度
}

# ==================== 评分权重 ====================
SCORING_WEIGHTS = {
    'surname': 0.7,    # 姓氏权重70%（最重要）
    'phone': 0.2,      # 电话权重20%
    'email': 0.1       # 邮箱权重10%
}

# ==================== 输出配置 ====================
OUTPUT_CONFIG = {
    'include_all_sheets': True,
    'sheet_names': {
        'all_data': '全部数据_带标记',
        'chinese': '华人',
        'indonesian_chinese': '印尼华人'
    },
    'file_suffix': '_印尼华人_',
    'timestamp_format': '%Y%m%d_%H%M%S'
}

def load_indonesian_mapping():
    """从CSV文件加载印尼姓氏映射"""
    csv_path = Path("完整百家姓.csv")
    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            mapping = {}
            
            for _, row in df.iterrows():
                pinyin = str(row.get('拼音', '')).lower().strip()
                chinese = str(row.get('漢字', '')).strip()
                indonesian = str(row.get('印尼拼寫', '')).strip()
                
                if pinyin and indonesian:
                    # 处理多个印尼拼写（用逗号分隔）
                    indonesian_list = [s.strip() for s in indonesian.split(',')]
                    mapping[pinyin] = indonesian_list
            
            return mapping
        except Exception as e:
            print(f"加载印尼姓氏映射失败: {e}")
            return INDONESIAN_SURNAME_MAPPING
    else:
        print("未找到完整百家姓.csv文件，使用默认映射")
        return INDONESIAN_SURNAME_MAPPING

def is_indonesian_surname(surname: str, mapping: dict = None) -> bool:
    """判断是否为印尼华人姓氏"""
    if not surname:
        return False
    
    surname = surname.lower().strip()
    
    # 使用提供的映射或加载默认映射
    if mapping is None:
        mapping = load_indonesian_mapping()
    
    # 检查是否在印尼特有姓氏中
    if surname in INDONESIAN_SPECIFIC_SURNAMES:
        return True
    
    # 检查是否在印尼拼音映射中
    for chinese_pinyin, indonesian_spellings in mapping.items():
        if surname in [s.lower() for s in indonesian_spellings]:
            return True
    
    return False

def translate_indonesian_surname(surname: str, mapping: dict = None) -> str:
    """翻译印尼姓氏为中文"""
    if not surname:
        return surname
    
    surname = surname.lower().strip()
    
    # 使用提供的映射或加载默认映射
    if mapping is None:
        mapping = load_indonesian_mapping()
    
    # 查找对应的中文姓氏
    for chinese_pinyin, indonesian_spellings in mapping.items():
        if surname in [s.lower() for s in indonesian_spellings]:
            return chinese_pinyin
    
    return surname

def calculate_indonesian_phone_score(phone: str) -> float:
    """计算印尼电话评分"""
    if not phone or pd.isna(phone):
        return 0.0
    
    phone = str(phone).strip().replace(' ', '').replace('-', '')
    
    for prefix, score in INDONESIA_PHONE_RULES['prefixes'].items():
        if phone.startswith(prefix):
            return score
    
    return 0.0

def calculate_indonesian_email_score(email: str) -> float:
    """计算印尼邮箱评分"""
    if not email or pd.isna(email) or '@' not in str(email):
        return 0.0
    
    domain = str(email).strip().lower().split('@')[1]
    
    # 检查高置信度域名
    for domain_pattern, score in INDONESIA_EMAIL_RULES['high_confidence'].items():
        if domain == domain_pattern or domain.endswith(domain_pattern):
            return score
    
    # 检查中等置信度域名
    for domain_pattern, score in INDONESIA_EMAIL_RULES['medium_confidence'].items():
        if domain == domain_pattern or domain.endswith(domain_pattern):
            return score
    
    # 检查低置信度域名
    for domain_pattern, score in INDONESIA_EMAIL_RULES['low_confidence'].items():
        if domain == domain_pattern or domain.endswith(domain_pattern):
            return score
    
    return 0.0

def calculate_indonesian_total_score(surname_score: float, phone_score: float, email_score: float) -> float:
    """计算印尼华人总评分"""
    return (
        surname_score * SCORING_WEIGHTS['surname'] +
        phone_score * SCORING_WEIGHTS['phone'] +
        email_score * SCORING_WEIGHTS['email']
    )

def determine_indonesian_confidence(total_score: float) -> str:
    """确定印尼华人置信度"""
    if total_score >= CONFIDENCE_THRESHOLDS['HIGH']:
        return 'HIGH'
    elif total_score >= CONFIDENCE_THRESHOLDS['MEDIUM']:
        return 'MEDIUM'
    elif total_score >= CONFIDENCE_THRESHOLDS['LOW']:
        return 'LOW'
    else:
        return 'VERY_LOW'