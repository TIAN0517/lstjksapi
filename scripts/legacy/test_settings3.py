"""
BossJy-Pro 统一配置管理
集成所有配置，避免重复和冲突
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from functools import lru_cache

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    from pydantic import BaseSettings
    SettingsConfigDict = dict

from pydantic import field_validator, Field


class UnifiedSettings(BaseSettings):
    """统一配置类 - 整合所有配置项"""

    model_config = SettingsConfigDict(
        env_file=None,  # 不加载 .env 文件来测试
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
        env_parse_none_str='null',
        env_ignore_empty=True
    )

    # ==================== 基本信息 ====================
    app_name: str = "BossJy-Pro Enterprise API"
    app_version: str = "2.0.0"
    environment: str = "production"
    debug: bool = False

    # ==================== 安全配置 ====================
    secret_key: str = "default-secret-key-change-in-production"
    jwt_secret_key: str = "default-jwt-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # ==================== 数据库配置 ====================
    database_url: str = "sqlite:///./data/bossjy.db"
    redis_url: str = "redis://localhost:6379/0"

    # 连接池配置
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_timeout: int = 30
    db_pool_recycle: int = 300

    # ==================== API 密钥配置 ====================
    gemini_api_keys: List[str] = Field(default_factory=list)
    gemini_model: str = "gemini-2.0-flash-exp"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, **data):
        # 调用父类初始化
        super().__init__(**data)
        
        # 特殊处理 GEMINI_API_KEYS 环境变量
        gemini_keys = os.getenv('GEMINI_API_KEYS')
        if gemini_keys:
            if isinstance(gemini_keys, str):
                # 按逗号分割并清理
                keys = [key.strip() for key in gemini_keys.split(',') if key.strip()]
                self.gemini_api_keys = keys


@lru_cache()
def get_settings() -> UnifiedSettings:
    """获取配置单例"""
    return UnifiedSettings()


# 向后兼容
Settings = UnifiedSettings

# 全局设置实例
settings = get_settings()