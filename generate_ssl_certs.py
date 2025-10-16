#!/usr/bin/env python3
"""
BossJy-Pro SSL证书生成器
为子域名生成自签名SSL证书
"""

import os
import subprocess
import sys
from datetime import datetime, timedelta

def create_ssl_directory():
    """创建SSL证书目录"""
    ssl_dir = "deploy/nginx/ssl"
    os.makedirs(ssl_dir, exist_ok=True)
    return ssl_dir

def generate_self_signed_cert(domain, ssl_dir):
    """生成自签名SSL证书"""
    try:
        # 检查是否安装了cryptography库
        try:
            from cryptography import x509
            from cryptography.x509.oid import NameOID
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import rsa
            import ipaddress
        except ImportError:
            print("需要安装cryptography库")
            print("请运行: pip install cryptography")
            return False
        
        # 生成私钥
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # 创建证书主题
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Beijing"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Beijing"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "BossJy-Pro"),
            x509.NameAttribute(NameOID.COMMON_NAME, domain),
        ])
        
        # 创建证书
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=365)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(domain),
                x509.DNSName(f"*.{domain}"),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # 保存证书
        cert_path = os.path.join(ssl_dir, f"{domain}.crt")
        key_path = os.path.join(ssl_dir, f"{domain}.key")
        
        with open(cert_path, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        with open(key_path, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        print(f"已生成证书: {domain}")
        print(f"   证书文件: {cert_path}")
        print(f"   私钥文件: {key_path}")
        return True
        
    except Exception as e:
        print(f"生成证书失败 {domain}: {e}")
        return False

def main():
    """主函数"""
    print("BossJy-Pro SSL证书生成器")
    print("=" * 50)
    
    # 创建SSL目录
    ssl_dir = create_ssl_directory()
    print(f"SSL证书目录: {ssl_dir}")
    
    # 子域名列表
    domains = [
        "appai.tiankai.it.com",
        "bossjy.tiankai.it.com",
        "chat88.tiankai.it.com",
        "jyt2.tiankai.it.com",
        "admin2.tiankai.it.com"
    ]
    
    print("\n开始生成SSL证书...")
    print("-" * 50)
    
    success_count = 0
    for domain in domains:
        if generate_self_signed_cert(domain, ssl_dir):
            success_count += 1
    
    print("-" * 50)
    print(f"成功生成 {success_count}/{len(domains)} 个SSL证书")
    
    if success_count == len(domains):
        print("\n所有SSL证书生成完成!")
        print("\n证书列表:")
        for domain in domains:
            print(f"   {domain}.crt / {domain}.key")
        
        print("\n提示:")
        print("   • 这些是自签名证书，浏览器会显示安全警告")
        print("   • 在生产环境中，请使用正规CA签发的证书")
        print("   • 可以配置Cloudflare SSL证书来避免警告")
        print("\n现在可以启动Nginx代理服务了!")
    else:
        print("\n部分证书生成失败，请检查错误信息")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n已取消证书生成")
        sys.exit(1)
