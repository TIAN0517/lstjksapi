#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BossJy 数据导出服务
支持多种格式的数据导出，包括Excel、CSV、JSON等
"""

import os
import logging
import asyncio
import aiofiles
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pathlib import Path
import zipfile
import tempfile
import sqlite3
from concurrent.futures import ThreadPoolExecutor
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置
EXPORT_CONFIG = {
    'export_dir': 'data/exports',
    'temp_dir': '/tmp/bossjy_exports',
    'max_file_size_mb': 100,
    'max_records_per_file': 50000,
    'email_enabled': os.environ.get('EMAIL_ENABLED', 'false').lower() == 'true',
    'smtp_server': os.environ.get('SMTP_SERVER', 'smtp.gmail.com'),
    'smtp_port': int(os.environ.get('SMTP_PORT', 587)),
    'smtp_username': os.environ.get('SMTP_USERNAME', ''),
    'smtp_password': os.environ.get('SMTP_PASSWORD', ''),
    'retention_days': int(os.environ.get('EXPORT_RETENTION_DAYS', 7))
}

# 支持的导出格式
EXPORT_FORMATS = {
    'excel': {
        'extension': '.xlsx',
        'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'description': 'Excel文件'
    },
    'csv': {
        'extension': '.csv',
        'mime_type': 'text/csv',
        'description': 'CSV文件'
    },
    'json': {
        'extension': '.json',
        'mime_type': 'application/json',
        'description': 'JSON文件'
    },
    'xml': {
        'extension': '.xml',
        'mime_type': 'application/xml',
        'description': 'XML文件'
    },
    'sql': {
        'extension': '.sql',
        'mime_type': 'text/plain',
        'description': 'SQL脚本'
    }
}

# 数据库配置
DB_PATH = 'bossjy_data.db'

@dataclass
class ExportRequest:
    """导出请求"""
    user_id: int
    data_type: str
    conditions: Dict[str, Any]
    format: str
    fields: Optional[List[str]] = None
    limit: Optional[int] = None
    email: Optional[str] = None
    compress: bool = False
    include_headers: bool = True
    date_format: str = '%Y-%m-%d %H:%M:%S'

@dataclass
class ExportResult:
    """导出结果"""
    success: bool
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    record_count: int = 0
    format: str = ''
    download_url: Optional[str] = None
    error_message: Optional[str] = None
    export_time: datetime = None
    
    def __post_init__(self):
        if self.export_time is None:
            self.export_time = datetime.utcnow()

class DataExporter:
    """数据导出器"""
    
    def __init__(self):
        self.export_dir = Path(EXPORT_CONFIG['export_dir'])
        self.temp_dir = Path(EXPORT_CONFIG['temp_dir'])
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # 确保目录存在
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    async def export_data(self, request: ExportRequest) -> ExportResult:
        """导出数据"""
        try:
            logger.info(f"开始导出数据: {request.data_type} - {request.format}")
            
            # 验证请求
            if not self.validate_request(request):
                return ExportResult(
                    success=False,
                    error_message="无效的导出请求"
                )
            
            # 查询数据
            data = await self.query_data(request)
            if not data:
                return ExportResult(
                    success=False,
                    error_message="没有找到匹配的数据"
                )
            
            # 生成文件
            file_path = await self.generate_export_file(data, request)
            
            # 压缩文件（如果需要）
            if request.compress:
                file_path = await self.compress_file(file_path)
            
            # 发送邮件（如果需要）
            if request.email and EXPORT_CONFIG['email_enabled']:
                await self.send_email_notification(file_path, request)
            
            # 清理旧文件
            await self.cleanup_old_files()
            
            result = ExportResult(
                success=True,
                file_path=str(file_path),
                file_size=os.path.getsize(file_path),
                record_count=len(data),
                format=request.format,
                download_url=f"/exports/{file_path.name}"
            )
            
            logger.info(f"导出完成: {file_path} ({len(data)} 条记录)")
            return result
            
        except Exception as e:
            logger.error(f"导出失败: {e}", exc_info=True)
            return ExportResult(
                success=False,
                error_message=str(e)
            )
    
    def validate_request(self, request: ExportRequest) -> bool:
        """验证导出请求"""
        # 检查格式
        if request.format not in EXPORT_FORMATS:
            return False
        
        # 检查数据类型
        valid_types = ['hongkong', 'indonesia', 'australia', 'global_chinese', 'singapore']
        if request.data_type not in valid_types:
            return False
        
        # 检查限制
        if request.limit and request.limit > EXPORT_CONFIG['max_records_per_file']:
            return False
        
        # 检查邮箱
        if request.email and '@' not in request.email:
            return False
        
        return True
    
    async def query_data(self, request: ExportRequest) -> List[Dict]:
        """查询数据"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            
            # 构建查询
            table_name = f"{request.data_type}_data"
            
            # 获取字段
            if request.fields:
                fields = ', '.join(request.fields)
            else:
                cur.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cur.fetchall()]
                fields = ', '.join(columns)
            
            # 构建WHERE条件
            where_clause = ""
            params = []
            
            if request.conditions:
                conditions = []
                for field, value in request.conditions.items():
                    if isinstance(value, str):
                        conditions.append(f"{field} LIKE ?")
                        params.append(f"%{value}%")
                    elif isinstance(value, list):
                        placeholders = ', '.join(['?' for _ in value])
                        conditions.append(f"{field} IN ({placeholders})")
                        params.extend(value)
                    else:
                        conditions.append(f"{field} = ?")
                        params.append(value)
                
                if conditions:
                    where_clause = "WHERE " + " AND ".join(conditions)
            
            # 构建LIMIT
            limit_clause = ""
            if request.limit:
                limit_clause = f"LIMIT {request.limit}"
            
            # 执行查询
            query = f"""
                SELECT {fields}
                FROM {table_name}
                {where_clause}
                {limit_clause}
            """
            
            cur.execute(query, params)
            rows = cur.fetchall()
            
            # 获取列名
            cur.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cur.fetchall()]
            
            cur.close()
            conn.close()
            
            # 转换为字典列表
            data = []
            for row in rows:
                record = dict(zip(columns, row))
                # 处理日期格式
                for key, value in record.items():
                    if isinstance(value, str) and 'T' in value:
                        try:
                            record[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except:
                            pass
                data.append(record)
            
            return data
            
        except Exception as e:
            logger.error(f"查询数据失败: {e}")
            raise
    
    async def generate_export_file(self, data: List[Dict], request: ExportRequest) -> Path:
        """生成导出文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_{request.data_type}_{timestamp}{EXPORT_FORMATS[request.format]['extension']}"
        file_path = self.export_dir / filename
        
        # 在线程池中执行导出
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self._generate_export_file_sync,
            data, request, file_path
        )
        
        return file_path
    
    def _generate_export_file_sync(self, data: List[Dict], request: ExportRequest, file_path: Path):
        """同步生成导出文件"""
        try:
            if request.format == 'excel':
                self._export_to_excel(data, request, file_path)
            elif request.format == 'csv':
                self._export_to_csv(data, request, file_path)
            elif request.format == 'json':
                self._export_to_json(data, request, file_path)
            elif request.format == 'xml':
                self._export_to_xml(data, request, file_path)
            elif request.format == 'sql':
                self._export_to_sql(data, request, file_path)
            else:
                raise ValueError(f"不支持的格式: {request.format}")
                
        except Exception as e:
            logger.error(f"生成导出文件失败: {e}")
            raise
    
    def _export_to_excel(self, data: List[Dict], request: ExportRequest, file_path: Path):
        """导出到Excel"""
        df = pd.DataFrame(data)
        
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='数据')
            
            # 获取工作表
            worksheet = writer.sheets['数据']
            
            # 设置列宽
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
    
    def _export_to_csv(self, data: List[Dict], request: ExportRequest, file_path: Path):
        """导出到CSV"""
        df = pd.DataFrame(data)
        df.to_csv(file_path, index=False, encoding='utf-8-sig')
    
    def _export_to_json(self, data: List[Dict], request: ExportRequest, file_path: Path):
        """导出到JSON"""
        export_data = {
            'metadata': {
                'export_time': datetime.utcnow().isoformat(),
                'data_type': request.data_type,
                'record_count': len(data),
                'conditions': request.conditions,
                'format': request.format
            },
            'data': data
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
    
    def _export_to_xml(self, data: List[Dict], request: ExportRequest, file_path: Path):
        """导出到XML"""
        import xml.etree.ElementTree as ET
        
        root = ET.Element('data_export')
        
        # 添加元数据
        metadata = ET.SubElement(root, 'metadata')
        ET.SubElement(metadata, 'export_time').text = datetime.utcnow().isoformat()
        ET.SubElement(metadata, 'data_type').text = request.data_type
        ET.SubElement(metadata, 'record_count').text = str(len(data))
        
        # 添加数据
        records = ET.SubElement(root, 'records')
        for record in data:
            record_elem = ET.SubElement(records, 'record')
            for key, value in record.items():
                elem = ET.SubElement(record_elem, key)
                elem.text = str(value) if value is not None else ''
        
        # 生成XML文件
        tree = ET.ElementTree(root)
        tree.write(file_path, encoding='utf-8', xml_declaration=True)
    
    def _export_to_sql(self, data: List[Dict], request: ExportRequest, file_path: Path):
        """导出到SQL"""
        if not data:
            return
        
        with open(file_path, 'w', encoding='utf-8') as f:
            # 写入头部
            f.write(f"-- BossJy 数据导出\n")
            f.write(f"-- 导出时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"-- 数据类型: {request.data_type}\n")
            f.write(f"-- 记录数: {len(data)}\n\n")
            
            # 写入建表语句
            table_name = f"export_{request.data_type}_{datetime.now().strftime('%Y%m%d')}"
            f.write(f"-- 创建表\n")
            f.write(f"CREATE TABLE {table_name} (\n")
            
            columns = list(data[0].keys())
            for i, col in enumerate(columns):
                col_type = "TEXT"
                if col.endswith('_id') or col.endswith('_count'):
                    col_type = "INTEGER"
                elif col.endswith('_amount') or col.endswith('_price'):
                    col_type = "DECIMAL(10,2)"
                
                comma = "," if i < len(columns) - 1 else ""
                f.write(f"    {col} {col_type}{comma}\n")
            
            f.write(");\n\n")
            
            # 写入插入语句
            f.write(f"-- 插入数据\n")
            for record in data:
                values = []
                for col in columns:
                    value = record.get(col)
                    if value is None:
                        values.append("NULL")
                    elif isinstance(value, str):
                        values.append(f"'{value.replace(\"'\", \"''\")}'")
                    else:
                        values.append(str(value))
                
                f.write(f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)});\n")
    
    async def compress_file(self, file_path: Path) -> Path:
        """压缩文件"""
        zip_path = file_path.with_suffix(file_path.suffix + '.zip')
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.executor,
            self._compress_file_sync,
            file_path, zip_path
        )
        
        # 删除原文件
        file_path.unlink()
        
        return zip_path
    
    def _compress_file_sync(self, file_path: Path, zip_path: Path):
        """同步压缩文件"""
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(file_path, file_path.name)
    
    async def send_email_notification(self, file_path: Path, request: ExportRequest):
        """发送邮件通知"""
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = EXPORT_CONFIG['smtp_username']
            msg['To'] = request.email
            msg['Subject'] = f"BossJy 数据导出完成 - {request.data_type}"
            
            # 邮件正文
            body = f"""
            您的数据导出已完成：
            
            数据类型：{request.data_type}
            导出格式：{request.format}
            记录数：{os.path.getsize(file_path)}
            文件大小：{self._format_file_size(os.path.getsize(file_path))}
            导出时间：{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}
            
            请查收附件中的导出文件。
            
            BossJy 数据服务
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # 添加附件
            with open(file_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {file_path.name}'
            )
            msg.attach(part)
            
            # 发送邮件
            with smtplib.SMTP(EXPORT_CONFIG['smtp_server'], EXPORT_CONFIG['smtp_port']) as server:
                server.starttls()
                server.login(EXPORT_CONFIG['smtp_username'], EXPORT_CONFIG['smtp_password'])
                server.send_message(msg)
            
            logger.info(f"邮件通知已发送: {request.email}")
            
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
    
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
    
    async def cleanup_old_files(self):
        """清理旧文件"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=EXPORT_CONFIG['retention_days'])
            
            for file_path in self.export_dir.glob('*'):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        file_path.unlink()
                        logger.info(f"删除旧文件: {file_path}")
            
        except Exception as e:
            logger.error(f"清理旧文件失败: {e}")
    
    async def get_export_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """获取导出历史"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            
            # 创建导出历史表（如果不存在）
            cur.execute("""
                CREATE TABLE IF NOT EXISTS export_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    data_type TEXT NOT NULL,
                    format TEXT NOT NULL,
                    file_path TEXT,
                    file_size INTEGER,
                    record_count INTEGER,
                    status TEXT DEFAULT 'completed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 查询历史记录
            cur.execute("""
                SELECT data_type, format, file_size, record_count, status, created_at
                FROM export_history
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (user_id, limit))
            
            records = cur.fetchall()
            cur.close()
            conn.close()
            
            return [
                {
                    'data_type': row[0],
                    'format': row[1],
                    'file_size': row[2],
                    'record_count': row[3],
                    'status': row[4],
                    'created_at': row[5]
                }
                for row in records
            ]
            
        except Exception as e:
            logger.error(f"获取导出历史失败: {e}")
            return []
    
    async def save_export_record(self, user_id: int, result: ExportResult, request: ExportRequest):
        """保存导出记录"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO export_history
                (user_id, data_type, format, file_path, file_size, record_count, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                request.data_type,
                request.format,
                result.file_path,
                result.file_size,
                result.record_count,
                'completed' if result.success else 'failed'
            ))
            
            conn.commit()
            cur.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"保存导出记录失败: {e}")

class ExportManager:
    """导出管理器"""
    
    def __init__(self):
        self.exporter = DataExporter()
        self.active_exports = {}
    
    async def create_export(self, request: ExportRequest) -> str:
        """创建导出任务"""
        export_id = f"export_{request.user_id}_{int(datetime.utcnow().timestamp())}"
        
        # 启动导出任务
        task = asyncio.create_task(self._run_export(export_id, request))
        self.active_exports[export_id] = task
        
        return export_id
    
    async def _run_export(self, export_id: str, request: ExportRequest):
        """运行导出任务"""
        try:
            result = await self.exporter.export_data(request)
            await self.exporter.save_export_record(request.user_id, result, request)
            
            # 清理活动任务
            if export_id in self.active_exports:
                del self.active_exports[export_id]
            
            return result
            
        except Exception as e:
            logger.error(f"导出任务失败: {e}")
            
            # 清理活动任务
            if export_id in self.active_exports:
                del self.active_exports[export_id]
            
            raise
    
    async def get_export_status(self, export_id: str) -> Dict:
        """获取导出状态"""
        if export_id in self.active_exports:
            task = self.active_exports[export_id]
            if task.done():
                return {'status': 'completed', 'result': task.result()}
            else:
                return {'status': 'running', 'progress': '处理中...'}
        else:
            return {'status': 'not_found'}
    
    async def cancel_export(self, export_id: str) -> bool:
        """取消导出任务"""
        if export_id in self.active_exports:
            task = self.active_exports[export_id]
            task.cancel()
            del self.active_exports[export_id]
            return True
        return False

# 全局导出管理器
export_manager = ExportManager()

async def main():
    """测试导出功能"""
    # 创建测试请求
    request = ExportRequest(
        user_id=1,
        data_type='hongkong',
        conditions={'name': 'test'},
        format='excel',
        limit=1000,
        email='test@example.com',
        compress=True
    )
    
    # 执行导出
    result = await export_manager.exporter.export_data(request)
    
    if result.success:
        print(f"导出成功: {result.file_path}")
        print(f"文件大小: {result.file_size} 字节")
        print(f"记录数: {result.record_count}")
    else:
        print(f"导出失败: {result.error_message}")

if __name__ == '__main__':
    asyncio.run(main())