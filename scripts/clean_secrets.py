#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理敏感資訊腳本 - 替換硬編碼的Token和密碼為環境變數
"""

import os
import re
import glob
from pathlib import Path

def clean_telegram_tokens(file_path):
    """清理Telegram Bot Token"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替換硬編碼的Token
        content = re.sub(
            r"'8431805678:[A-Za-z0-9_-]+'",
            "os.environ.get('BOT1_TOKEN', 'YOUR_BOT1_TOKEN')",
            content
        )
        
        content = re.sub(
            r"'8314772330:[A-Za-z0-9_-]+'",
            "os.environ.get('BOT2_TOKEN', 'YOUR_BOT2_TOKEN')",
            content
        )
        
        content = re.sub(
            r"'8344575992:[A-Za-z0-9_-]+'",
            "os.environ.get('BOT3_TOKEN', 'YOUR_BOT3_TOKEN')",
            content
        )
        
        content = re.sub(
            r"TELEGRAM_BOT_TOKEN.*?=.*?'[0-9]+:[A-Za-z0-9_-]+'",
            "TELEGRAM_BOT_TOKEN=os.environ.get('BOT1_TOKEN', 'YOUR_BOT1_TOKEN')",
            content
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"清理 {file_path} 失敗: {e}")
        return False

def clean_database_urls(file_path):
    """清理資料庫URL"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替換硬編碼的資料庫URL
        content = re.sub(
            r"postgresql://bossjy:[^@]+@localhost:15432/bossjy_huaqiao",
            "os.environ.get('DATABASE_URL', 'postgresql://bossjy:CHANGE_ME@postgres:5432/bossjy')",
            content
        )
        
        content = re.sub(
            r"postgresql://postgres:[^@]+@localhost:5432/bossjy_pro",
            "os.environ.get('DATABASE_URL', 'postgresql://bossjy:CHANGE_ME@postgres:5432/bossjy')",
            content
        )
        
        content = re.sub(
            r"postgresql://postgres:[^@]+@localhost:15432/bossjydb",
            "os.environ.get('DATABASE_URL', 'postgresql://bossjy:CHANGE_ME@postgres:5432/bossjy')",
            content
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
    except Exception as e:
        print(f"清理 {file_path} 失敗: {e}")
        return False

def main():
    """主函數"""
    project_root = Path(__file__).parent.parent
    
    # 需要清理的檔案類型
    patterns = [
        "**/*.py",
        "**/*.md",
        "**/*.sh",
        "**/*.yml",
        "**/*.yaml"
    ]
    
    cleaned_files = []
    
    for pattern in patterns:
        for file_path in project_root.glob(pattern):
            # 跳過某些目錄
            if any(skip in str(file_path) for skip in ['.git', '__pycache__', 'node_modules', 'venv']):
                continue
            
            # 跳過已經是範例的檔案
            if 'example' in str(file_path) or 'template' in str(file_path):
                continue
            
            # 清理檔案
            if file_path.suffix in ['.py', '.md', '.sh', '.yml', '.yaml']:
                if clean_telegram_tokens(file_path):
                    cleaned_files.append(str(file_path))
                
                if clean_database_urls(file_path):
                    cleaned_files.append(str(file_path))
    
    print(f"✅ 已清理 {len(cleaned_files)} 個檔案的敏感資訊")
    
    # 生成需要設置的環境變數清單
    env_vars = [
        "BOT1_TOKEN",
        "BOT2_TOKEN", 
        "BOT3_TOKEN",
        "DATABASE_URL",
        "POSTGRES_PASSWORD",
        "REDIS_PASSWORD",
        "SECRET_KEY",
        "JWT_SECRET_KEY",
        "S3_ACCESS_KEY",
        "S3_SECRET_KEY",
        "GEMINI_API_KEYS",
        "GOOGLE_PLACES_API_KEY"
    ]
    
    print("\n📋 需要設置的環境變數:")
    for var in env_vars:
        print(f"   {var}")

if __name__ == "__main__":
    main()
