#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版香港人/华人筛选配置 (Enhanced Version)
集成粤语名字识别、姓氏置信度加权、姓名组合模式分析
预期准确率提升: 60-70% → 85-95%
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

# ==================== 【新增】姓氏香港专属度（置信度权重）====================
HONGKONG_SURNAME_CONFIDENCE = {
    # 极高置信度 (90%+) - 几乎只有香港人使用
    'ng': 0.95,           # 吴（粤语特有简写）
    'szeto': 0.95,        # 司徒（复姓，香港常见）
    'tsang': 0.92,        # 曾（粤语拼音）
    'yip': 0.90,          # 叶
    'mak': 0.90,          # 麦
    'tse': 0.88,          # 谢
    'kwok': 0.87,         # 郭
    'yuen': 0.85,         # 袁

    # 高置信度 (70-85%) - 香港为主，但广东、澳门也有
    'wong': 0.78,         # 王/黄（广东、新加坡也用）
    'chan': 0.75,         # 陈
    'cheung': 0.77,       # 张
    'lam': 0.76,          # 林
    'leung': 0.80,        # 梁
    'lau': 0.74,          # 刘
    'tam': 0.73,          # 谭
    'poon': 0.72,         # 潘
    'yeung': 0.75,        # 杨

    # 中等置信度 (55-70%) - 香港常见，全球华人都用
    'chow': 0.65,         # 周
    'tang': 0.62,         # 邓/唐
    'ho': 0.60,           # 何
    'chung': 0.68,        # 钟
    'fung': 0.67,         # 冯
    'ko': 0.63,           # 高
    'choi': 0.66,         # 蔡
    'lai': 0.64,          # 黎
    'wan': 0.61,          # 温
    'so': 0.65,           # 苏

    # 低置信度 (30-55%) - 全球华人通用，难以区分
    'lee': 0.35,          # 李（韩国、新加坡、全球华人）
    'li': 0.33,           # 李
    'tan': 0.30,          # 谭（新加坡、马来西亚）
    'lim': 0.28,          # 林（新加坡、马来西亚）
    'teo': 0.25,          # 张（新加坡）
    'ong': 0.32,          # 王（新加坡、马来西亚）
    'goh': 0.30,          # 吴（新加坡）

    # 普通话拼音（中等偏低）
    'wang': 0.45,         # 王（大陆为主）
    'chen': 0.48,         # 陈
    'zhang': 0.46,        # 张
    'liu': 0.44,          # 刘
    'yang': 0.47,         # 杨
    'huang': 0.50,        # 黄
    'zhao': 0.42,         # 赵
    'wu': 0.43,           # 吴
    'zhou': 0.41,         # 周
}

# ==================== 【新增】粤语名字特征音节 ====================
CANTONESE_GIVEN_NAME_SYLLABLES = {
    # 高频粤语音节（香港名字常用）
    'ka', 'yan', 'ming', 'fai', 'wai', 'man', 'kin', 'wing',
    'chi', 'chun', 'shing', 'yiu', 'ching', 'kit', 'yuk',
    'tsz', 'lok', 'hei', 'sze', 'yu', 'chak', 'pui', 'mei',
    'shun', 'ting', 'yee', 'choi', 'lai', 'po', 'keung',
    'tat', 'chit', 'tak', 'sum', 'wah', 'ho', 'shan', 'ying',
    'hung', 'cheuk', 'hoi', 'kei', 'sin', 'yat', 'sai', 'king',

    # 女性常用音节
    'yi', 'ling', 'lin', 'nga', 'fun', 'sau', 'yung', 'wah',

    # 双字音节组合常见
    'ka yan', 'ming fai', 'wai man', 'chi wing', 'tsz ching',
    'hoi ying', 'shing yiu', 'lok yin', 'chak yin', 'yuk ching'
}

# ==================== 【新增】大陆普通话特征（排除项）====================
MAINLAND_MANDARIN_PATTERNS = {
    # 普通话特有音节（香港人很少用）
    'xiao', 'qing', 'xiong', 'xue', 'zhen', 'qiang', 'jun',
    'jing', 'rong', 'tao', 'hui', 'feng', 'lei', 'hua',
    'xin', 'bin', 'dong', 'long', 'peng', 'chao', 'gang'
}

# ==================== 【新增】韩国名字特征（排除项）====================
KOREAN_NAME_PATTERNS = {
    # 韩国名字常用音节
    'jae', 'sung', 'hyun', 'min', 'jun', 'soo', 'hee', 'ji',
    'young', 'seung', 'ho', 'kyung', 'dong', 'eun', 'hye', 'in',
    'yeon', 'seo', 'woo', 'jin', 'ah', 'mi', 'sun'
}

# ==================== 【新增】西方名字库（降低置信度）====================
WESTERN_GIVEN_NAMES = {
    # 常见英文名
    'john', 'mary', 'david', 'michael', 'sarah', 'james', 'robert',
    'william', 'richard', 'jennifer', 'linda', 'daniel', 'matthew',
    'lisa', 'paul', 'mark', 'steven', 'peter', 'nancy', 'karen',
    'thomas', 'charles', 'chris', 'andrew', 'kevin', 'jason', 'brian',
    'emily', 'jessica', 'ashley', 'amy', 'melissa', 'amanda', 'nicole'
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
        # 香港本地号码（在香港的香港人）
        '852': 0.9,       # +852 香港国家码
        '8529': 0.95,     # +852 9xxx xxxx 香港手机
        '8526': 0.90,     # +852 6xxx xxxx 香港手机
        '8525': 0.85,     # +852 5xxx xxxx 香港手机

        # 海外号码（在澳洲的香港人会用这些号码）
        '61': 0.4,        # +61 澳洲国家码（中性分，符合移民预期）
        '04': 0.4,        # 04 澳洲手机（中性分）
        '02': 0.3,        # 02 悉尼
        '03': 0.3,        # 03 墨尔本
        '07': 0.3,        # 07 布里斯班
        '08': 0.3,        # 08 珀斯/阿德莱德
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

# ==================== 【优化】置信度阈值（更严格）====================
CONFIDENCE_THRESHOLDS = {
    'HIGH': 0.80,      # 提高至0.80（原0.75）- 更严格
    'MEDIUM': 0.60,    # 提高至0.60（原0.50）
    'LOW': 0.40        # 提高至0.40（原0.25）
}

# ==================== 【优化】评分权重（增加名字分析）====================
SCORING_WEIGHTS = {
    'surname_confidence': 0.30,  # 姓氏置信度（考虑稀有度）
    'given_name_cantonese': 0.25,  # 名字粤语特征
    'name_pattern': 0.20,        # 姓名组合模式
    'phone': 0.12,               # 降低电话权重（大多澳洲号）
    'email': 0.13                # 降低邮箱权重
}

# ==================== Elasticsearch 配置 ====================
ELASTICSEARCH_CONFIG = {
    'hosts': ['http://localhost:9200'],
    'index': 'hongkong_people_enhanced',  # 新索引名
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
            'surname': {'type': 'keyword'},
            'given_name': {'type': 'text'},
            'chinese_surname': {
                'type': 'text',
                'fields': {'keyword': {'type': 'keyword'}}
            },
            'phone': {'type': 'keyword'},
            'phone_prefix': {'type': 'keyword'},
            'email': {
                'type': 'text',
                'fields': {'keyword': {'type': 'keyword'}}
            },
            'email_domain': {'type': 'keyword'},
            'confidence': {'type': 'keyword'},
            'is_chinese': {'type': 'boolean'},
            'is_hongkong': {'type': 'boolean'},

            # 新增字段
            'surname_confidence_score': {'type': 'float'},
            'given_name_cantonese_score': {'type': 'float'},
            'name_pattern_score': {'type': 'float'},
            'has_western_name': {'type': 'boolean'},
            'has_mainland_pattern': {'type': 'boolean'},
            'has_korean_pattern': {'type': 'boolean'},

            'total_score': {'type': 'float'},
            'name_score': {'type': 'float'},
            'phone_score': {'type': 'float'},
            'email_score': {'type': 'float'},
            'source_file': {'type': 'keyword'},
            'source_country': {'type': 'keyword'},
            'created_at': {'type': 'date'}
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
    'excel_sheets': ['全部数据_带标记', '华人', '香港人', '高置信度香港人'],  # 新增工作表
    'batch_size': 1000  # 批量插入大小
}

# ==================== 【新增】版本信息 ====================
VERSION_INFO = {
    'version': '2.0-enhanced',
    'release_date': '2025-10-03',
    'improvements': [
        '新增粤语名字音节识别',
        '新增姓氏置信度加权',
        '新增姓名组合模式分析',
        '新增西方/大陆/韩国名字排除',
        '优化评分权重分配',
        '预期准确率: 85-95% (HIGH置信度)'
    ]
}
