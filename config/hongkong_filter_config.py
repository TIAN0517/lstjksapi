#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一的香港人/华人筛选配置
所有筛选脚本都使用这个配置
"""

# ==================== 华侨百家姓 ====================
CHINESE_SURNAMES = {
    'zhao', 'qian', 'sun', 'li', 'zhou', 'wu', 'zheng', 'wang', 'feng', 'chen',
    'chu', 'wei', 'jiang', 'shen', 'han', 'yang', 'zhu', 'qin', 'you', 'xu',
    'he', 'lu', 'shi', 'zhang', 'kong', 'cao', 'yan', 'hua', 'jin', 'wei',
    'tao', 'jiang', 'qi', 'xie', 'zou', 'yu', 'bai', 'shui', 'dou', 'zhang',
    'yun', 'su', 'pan', 'ge', 'xi', 'fan', 'peng', 'lang', 'lu', 'wei',
    'chang', 'ma', 'miao', 'feng', 'hua', 'fang', 'yu', 'ren', 'yuan', 'liu',
    'feng', 'bao', 'shi', 'tang', 'pei', 'lian', 'cen', 'xue', 'lei', 'he',
    'ni', 'tang', 'teng', 'yin', 'luo', 'bi', 'hao', 'wu', 'an', 'chang',
    'yue', 'yu', 'shi', 'fu', 'pi', 'bian', 'qi', 'kang', 'wu', 'yu',
    'yuan', 'bu', 'gu', 'meng', 'ping', 'huang', 'he', 'mu', 'xiao', 'yin',
    'yao', 'shao', 'zhan', 'wang', 'qi', 'mao', 'yu', 'di', 'mi', 'bei',
    'ming', 'zang', 'ji', 'fu', 'cheng', 'dai', 'tan', 'song', 'mao', 'pang'
}

# ==================== 香港特有姓氏（粤语拼音） ====================
HONGKONG_SPECIFIC_SURNAMES = {
    'wong', 'chan', 'cheung', 'ng', 'lam', 'leung', 'tsang', 'yip', 'mak', 'tse',
    'yuen', 'szeto', 'lau', 'ho', 'kwok', 'tam', 'poon', 'chung', 'fung', 'ko',
    'chow', 'lai', 'wan', 'tang', 'yeung', 'so', 'tsui', 'choi', 'tong', 'kwan',
    'siu', 'lok', 'ching', 'shum', 'lui', 'chu', 'hung', 'yim', 'tong', 'chiu'
}

# ==================== 香港特有复姓 ====================
HONGKONG_COMPOUND_SURNAMES = {
    'szeto', '司徒', 'ouyang', '欧阳', 'simon', '西门', 'sima', '司马',
    'situ', 'seeto'
}

# ==================== 香港姓氏中文翻译对照表 ====================
HONGKONG_SURNAME_TRANSLATION = {
    # 香港粤语拼音
    'wong': '王/黃', 'chan': '陳', 'cheung': '張', 'ng': '吳', 'lam': '林',
    'leung': '梁', 'tsang': '曾', 'yip': '葉', 'mak': '麥', 'tse': '謝',
    'yuen': '袁', 'szeto': '司徒', 'lau': '劉', 'ho': '何', 'kwok': '郭',
    'tam': '譚', 'poon': '潘', 'chung': '鍾', 'fung': '馮', 'ko': '高',
    'chow': '周', 'lai': '黎', 'wan': '溫', 'tang': '鄧', 'yeung': '楊',
    'so': '蘇', 'tsui': '徐', 'choi': '蔡', 'tong': '唐', 'kwan': '關',
    'siu': '蕭', 'lok': '駱', 'ching': '程', 'shum': '沈', 'lui': '呂',

    # 普通话拼音
    'lee': '李', 'li': '李', 'chang': '張', 'cheng': '鄭', 'chen': '陳',
    'zhang': '張', 'liu': '劉', 'wang': '王', 'yang': '楊', 'huang': '黃',
    'zhao': '趙', 'wu': '吳', 'zhou': '周', 'xu': '徐', 'sun': '孫',
    'ma': '馬', 'zhu': '朱', 'hu': '胡', 'guo': '郭', 'he': '何',
    'gao': '高', 'lin': '林', 'luo': '羅', 'zheng': '鄭', 'liang': '梁',
    'xie': '謝', 'song': '宋', 'deng': '鄧', 'han': '韓', 'feng': '馮',
    'cao': '曹', 'peng': '彭', 'zeng': '曾', 'xiao': '蕭',

    # 复姓
    'ouyang': '歐陽', 'simon': '西門', 'sima': '司馬', 'situ': '司徒'
}

# ==================== 电话号码规则 ====================
HONGKONG_PHONE_RULES = {
    'prefixes': {
        # 澳洲本地号码（可能是香港移民）
        '61': 0.3,        # 澳洲国家码
        '04': 0.2,        # 澳洲手机
        '02': 0.1,        # 悉尼
        '03': 0.1,        # 墨尔本

        # 香港号码
        '852': 0.9,       # 香港国家码
        '9': 0.8,         # 香港手机
        '6': 0.7,         # 香港手机
        '5': 0.6,         # 香港手机
    },
    'length': {
        'hongkong': [8, 11, 12],  # 香港号码长度
        'australia': [10, 12, 13]  # 澳洲号码长度
    }
}

# ==================== 邮箱域名规则 ====================
HONGKONG_EMAIL_RULES = {
    'high_confidence': {
        # 香港本地邮箱
        'netvigator.com': 0.9,
        'hknet.com': 0.9,
        'hkstar.com': 0.9,
        'biznetvigator.com': 0.8,
        'hongkong.com': 0.8,

        # 大陆邮箱（香港人也常用）
        'qq.com': 0.7,
        '163.com': 0.7,
        '126.com': 0.6,
        'sina.com': 0.6,
        'sohu.com': 0.5,
    },
    'medium_confidence': {
        'gmail.com': 0.3,
        'yahoo.com': 0.3,
        'hotmail.com': 0.2,
        'outlook.com': 0.2,
    }
}

# ==================== 置信度阈值 ====================
CONFIDENCE_THRESHOLDS = {
    'HIGH': 0.75,      # 高置信度：非常可能是香港人
    'MEDIUM': 0.50,    # 中等置信度：可能是香港人
    'LOW': 0.25        # 低置信度：不太确定
}

# ==================== 评分权重 ====================
SCORING_WEIGHTS = {
    'surname': 0.50,     # 姓氏权重 50%
    'phone': 0.25,       # 电话权重 25%
    'email': 0.25        # 邮箱权重 25%
}

# ==================== Elasticsearch 配置 ====================
ELASTICSEARCH_CONFIG = {
    'hosts': ['http://localhost:9200'],
    'index': 'hongkong_people',
    'settings': {
        'number_of_shards': 3,
        'number_of_replicas': 1,
        'analysis': {
            'analyzer': {
                'name_analyzer': {
                    'tokenizer': 'standard',
                    'filter': ['lowercase', 'asciifolding']
                },
                'pinyin_analyzer': {
                    'tokenizer': 'standard',
                    'filter': ['lowercase', 'pinyin_filter']
                }
            },
            'filter': {
                'pinyin_filter': {
                    'type': 'pinyin',
                    'keep_first_letter': True,
                    'keep_full_pinyin': True,
                    'keep_original': True
                }
            }
        }
    },
    'mappings': {
        'properties': {
            'name': {
                'type': 'text',
                'analyzer': 'name_analyzer',
                'fields': {
                    'keyword': {'type': 'keyword'},
                    'pinyin': {
                        'type': 'text',
                        'analyzer': 'pinyin_analyzer'
                    },
                    'suggest': {'type': 'completion'}
                }
            },
            'surname': {
                'type': 'keyword'
            },
            'given_name': {
                'type': 'text'
            },
            'chinese_surname': {
                'type': 'text',
                'fields': {
                    'keyword': {'type': 'keyword'}
                }
            },
            'phone': {
                'type': 'keyword'
            },
            'phone_prefix': {
                'type': 'keyword'
            },
            'email': {
                'type': 'text',
                'fields': {
                    'keyword': {'type': 'keyword'}
                }
            },
            'email_domain': {
                'type': 'keyword'
            },
            'confidence': {
                'type': 'keyword'
            },
            'is_chinese': {
                'type': 'boolean'
            },
            'is_hongkong': {
                'type': 'boolean'
            },
            'total_score': {
                'type': 'float'
            },
            'name_score': {
                'type': 'float'
            },
            'phone_score': {
                'type': 'float'
            },
            'email_score': {
                'type': 'float'
            },
            'source_file': {
                'type': 'keyword'
            },
            'source_country': {
                'type': 'keyword'
            },
            'created_at': {
                'type': 'date'
            }
        }
    }
}

# ==================== 数据库配置 ====================
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'bossjy_huaqiao',
    'user': 'bossjy',
    'password': 'ji394su3'
}

# ==================== 输出配置 ====================
OUTPUT_CONFIG = {
    'save_to_excel': True,
    'save_to_database': True,
    'save_to_elasticsearch': True,
    'excel_sheets': ['全部数据_带标记', '华人', '香港人'],
    'batch_size': 1000  # 批量插入大小
}
