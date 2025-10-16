#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import psycopg2
import sys

def reset_postgres_password():
    # 尝试不同的postgres用户密码和主机地址
    passwords = ["", "postgres", "password", "admin", "123456"]
    hosts = ["localhost", "127.0.0.1"]
    
    for host in hosts:
        for password in passwords:
            try:
                print(f"尝试连接，主机: {host}，用户: postgres，密码: {'(空)' if password == '' else password}...")
                conn = psycopg2.connect(
                    host=host,
                    port="15432",
                    user="postgres",
                    password=password,
                    database="postgres"
                )
                print("成功连接到PostgreSQL!")
                
                cursor = conn.cursor()
                
                # 尝试创建jytian用户
                try:
                    cursor.execute("CREATE USER jytian WITH PASSWORD 'ji394su3';")
                    print("成功创建用户jytian")
                except psycopg2.errors.DuplicateObject:
                    print("用户jytian已存在，尝试更新密码...")
                    cursor.execute("ALTER USER jytian WITH PASSWORD 'ji394su3';")
                    print("成功更新jytian用户密码")
                
                # 创建bossjy_huaqiao数据库
                try:
                    cursor.execute("CREATE DATABASE bossjy_huaqiao OWNER jytian;")
                    print("成功创建数据库bossjy_huaqiao")
                except psycopg2.errors.DuplicateDatabase:
                    print("数据库bossjy_huaqiao已存在")
                
                # 授予权限
                cursor.execute("GRANT ALL PRIVILEGES ON DATABASE bossjy_huaqiao TO jytian;")
                print("成功授予jytian用户对bossjy_huaqiao数据库的所有权限")
                
                conn.commit()
                cursor.close()
                conn.close()
                
                print("密码重置完成!")
                return True
                
            except psycopg2.OperationalError as e:
                print(f"连接失败: {e}")
                continue
            except Exception as e:
                print(f"发生错误: {e}")
                continue
    
    print("所有连接尝试均失败")
    return False

if __name__ == "__main__":
    success = reset_postgres_password()
    sys.exit(0 if success else 1)