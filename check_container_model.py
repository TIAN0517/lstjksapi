#!/usr/bin/env python3
"""查看容器中的模型文件"""
with open('/app/models/__init__.py', 'r') as f:
    lines = f.readlines()
    
for i, line in enumerate(lines):
    if 'class User' in line:
        print(f"Line {i+1}: {line.strip()}")
        for j in range(1, 6):
            if i+j < len(lines):
                print(f"Line {i+j+1}: {lines[i+j].strip()}")