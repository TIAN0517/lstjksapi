import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class TestSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=None,  # 不加载 .env 文件
        case_sensitive=False,
        extra='ignore'
    )
    
    # 简化配置
    app_name: str = "Test App"
    secret_key: str = "test-secret"
    jwt_secret_key: str = "test-jwt-secret"
    database_url: str = "sqlite:///./test.db"
    gemini_api_keys: List[str] = ["test-key"]

# 测试加载
try:
    settings = TestSettings()
    print("Settings loaded successfully!")
    print(f"App name: {settings.app_name}")
    print(f"Gemini keys: {settings.gemini_api_keys}")
except Exception as e:
    print(f"Error loading settings: {e}")
    import traceback
    traceback.print_exc()