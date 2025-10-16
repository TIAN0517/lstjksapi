#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BossJy API集成服务
提供统一的API接口，支持多种数据源和服务集成
"""

import os
import logging
import asyncio
import aiohttp
import aiofiles
import json
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from urllib.parse import urljoin, urlencode
import sqlite3
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Security, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field, validator
import redis.asyncio as redis
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 配置
API_CONFIG = {
    'host': os.environ.get('API_HOST', '0.0.0.0'),
    'port': int(os.environ.get('API_PORT', 18001)),
    'debug': os.environ.get('DEBUG', 'false').lower() == 'true',
    'redis_url': os.environ.get('REDIS_URL', 'redis://localhost:6379'),
    'database_url': os.environ.get('DATABASE_URL', 'sqlite:///bossjy_api.db'),
    'jwt_secret': os.environ.get('JWT_SECRET', 'your-secret-key'),
    'cors_origins': os.environ.get('ALLOWED_ORIGINS', '*').split(','),
    'rate_limit': {
        'requests_per_minute': int(os.environ.get('RATE_LIMIT_RPM', 60)),
        'requests_per_hour': int(os.environ.get('RATE_LIMIT_RPH', 1000))
    }
}

# 数据库配置
DB_PATH = 'bossjy_api.db'

# Redis连接
redis_client = None

# 安全配置
security = HTTPBearer()

# Prometheus指标
REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('api_request_duration_seconds', 'API request duration')
ACTIVE_CONNECTIONS = Counter('active_connections', 'Active connections')

# 数据模型
@dataclass
class APIResponse:
    """API响应格式"""
    success: bool
    message: str
    data: Any = None
    code: int = 200
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

class UserCredentials(BaseModel):
    """用户凭据"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    
    @validator('username')
    def validate_username(cls, v):
        if not v.replace('_', '').isalnum():
            raise ValueError('用户名只能包含字母、数字和下划线')
        return v

class APIKey(BaseModel):
    """API密钥"""
    key_id: str
    key_secret: str
    permissions: List[str]
    rate_limit: int = 1000
    expires_at: Optional[datetime] = None

class DataQuery(BaseModel):
    """数据查询请求"""
    data_type: str = Field(..., regex='^(hongkong|indonesia|australia|global_chinese|singapore)$')
    conditions: Optional[Dict[str, Any]] = {}
    limit: int = Field(100, ge=1, le=10000)
    offset: int = Field(0, ge=0)
    format: str = Field('json', regex='^(json|csv|excel)$')

class DataExport(BaseModel):
    """数据导出请求"""
    query: DataQuery
    export_format: str = Field('excel', regex='^(excel|csv|json)$')
    email: Optional[str] = None

class RechargeRequest(BaseModel):
    """充值请求"""
    amount: float = Field(..., gt=0)
    tx_hash: str = Field(..., min_length=10)
    currency: str = Field('USDT', regex='^(USDT|BTC|ETH)$')

class WebhookPayload(BaseModel):
    """Webhook载荷"""
    event: str
    data: Dict[str, Any]
    timestamp: datetime = None
    signature: Optional[str] = None

# 数据库操作
class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # API用户表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS api_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                api_key TEXT UNIQUE,
                api_secret TEXT UNIQUE,
                permissions TEXT,
                rate_limit INTEGER DEFAULT 1000,
                credits INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # API使用记录表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                status_code INTEGER,
                response_time REAL,
                credits_consumed INTEGER DEFAULT 0,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES api_users (id)
            )
        """)
        
        # 充值记录表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS recharge_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                amount REAL NOT NULL,
                tx_hash TEXT UNIQUE,
                currency TEXT DEFAULT 'USDT',
                credits INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES api_users (id)
            )
        """)
        
        # 数据查询记录表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS query_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                data_type TEXT NOT NULL,
                conditions TEXT,
                result_count INTEGER,
                credits_consumed INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES api_users (id)
            )
        """)
        
        conn.commit()
        cur.close()
        conn.close()
    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)

# 业务逻辑
class BossJyAPIService:
    """BossJy API服务"""
    
    def __init__(self, db_manager: DatabaseManager, redis_client):
        self.db = db_manager
        self.redis = redis_client
    
    async def authenticate_user(self, credentials: UserCredentials) -> Optional[Dict]:
        """验证用户"""
        try:
            conn = self.db.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, username, password_hash, api_key, permissions, credits, is_active
                FROM api_users 
                WHERE username = ? AND is_active = 1
            """, (credentials.username,))
            user = cur.fetchone()
            cur.close()
            conn.close()
            
            if user and self.verify_password(credentials.password, user[2]):
                return {
                    'id': user[0],
                    'username': user[1],
                    'api_key': user[3],
                    'permissions': json.loads(user[4]) if user[4] else [],
                    'credits': user[5],
                    'is_active': bool(user[6])
                }
            return None
        except Exception as e:
            logger.error(f"用户认证失败: {e}")
            return None
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        # 简单的密码验证（实际应该使用bcrypt）
        return hashlib.sha256(password.encode()).hexdigest() == password_hash
    
    async def generate_api_key(self, user_id: int) -> APIKey:
        """生成API密钥"""
        import secrets
        
        key_id = f"bk_{secrets.token_hex(16)}"
        key_secret = f"bs_{secrets.token_hex(32)}"
        
        try:
            conn = self.db.get_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE api_users 
                SET api_key = ?, api_secret = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (key_id, key_secret, user_id))
            conn.commit()
            cur.close()
            conn.close()
            
            return APIKey(
                key_id=key_id,
                key_secret=key_secret,
                permissions=['data_query', 'data_export'],
                rate_limit=1000
            )
        except Exception as e:
            logger.error(f"生成API密钥失败: {e}")
            raise HTTPException(status_code=500, detail="生成API密钥失败")
    
    async def verify_api_key(self, api_key: str, api_secret: str) -> Optional[Dict]:
        """验证API密钥"""
        try:
            conn = self.db.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, username, permissions, credits, rate_limit, is_active
                FROM api_users 
                WHERE api_key = ? AND api_secret = ? AND is_active = 1
            """, (api_key, api_secret))
            user = cur.fetchone()
            cur.close()
            conn.close()
            
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'permissions': json.loads(user[2]) if user[2] else [],
                    'credits': user[3],
                    'rate_limit': user[4]
                }
            return None
        except Exception as e:
            logger.error(f"API密钥验证失败: {e}")
            return None
    
    async def check_rate_limit(self, user_id: int, endpoint: str) -> bool:
        """检查速率限制"""
        try:
            key = f"rate_limit:{user_id}:{endpoint}"
            current = await self.redis.incr(key)
            
            if current == 1:
                await self.redis.expire(key, 60)  # 1分钟过期
            
            # 获取用户限制
            conn = self.db.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT rate_limit FROM api_users WHERE id = ?", (user_id,))
            result = cur.fetchone()
            cur.close()
            conn.close()
            
            if result:
                limit = result[0]
                return current <= limit
            
            return current <= API_CONFIG['rate_limit']['requests_per_minute']
        except Exception as e:
            logger.error(f"检查速率限制失败: {e}")
            return True  # 出错时允许请求
    
    async def deduct_credits(self, user_id: int, credits: int, reason: str) -> bool:
        """扣除积分"""
        try:
            conn = self.db.get_connection()
            cur = conn.cursor()
            
            # 检查积分是否足够
            cur.execute("SELECT credits FROM api_users WHERE id = ?", (user_id,))
            result = cur.fetchone()
            if not result or result[0] < credits:
                cur.close()
                conn.close()
                return False
            
            # 扣除积分
            cur.execute("""
                UPDATE api_users 
                SET credits = credits - ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (credits, user_id))
            
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"扣除积分失败: {e}")
            return False
    
    async def query_data(self, user_id: int, query: DataQuery) -> Dict:
        """查询数据"""
        # 检查权限
        if 'data_query' not await self.get_user_permissions(user_id):
            raise HTTPException(status_code=403, detail="无数据查询权限")
        
        # 检查积分
        credits_needed = max(1, query.limit // 100)  # 每100条1积分
        if not await self.deduct_credits(user_id, credits_needed, f"数据查询-{query.data_type}"):
            raise HTTPException(status_code=402, detail="积分不足")
        
        # 执行查询
        try:
            # 这里应该连接到实际的数据源
            # 模拟查询结果
            results = await self.execute_data_query(query)
            
            # 记录查询
            await self.record_query(user_id, query, len(results), credits_needed)
            
            return {
                'data': results,
                'total': len(results),
                'query': query.dict(),
                'credits_consumed': credits_needed
            }
        except Exception as e:
            logger.error(f"数据查询失败: {e}")
            raise HTTPException(status_code=500, detail="数据查询失败")
    
    async def execute_data_query(self, query: DataQuery) -> List[Dict]:
        """执行数据查询"""
        # 模拟数据查询
        # 实际应该连接到相应的数据库或API
        
        sample_data = []
        for i in range(min(query.limit, 100)):  # 限制返回数量
            sample_data.append({
                'id': i + 1,
                'name': f'样本数据_{i}',
                'phone': f'138****{i:04d}',
                'email': f'sample{i}@example.com',
                'address': f'测试地址_{i}',
                'company': f'测试公司_{i}'
            })
        
        return sample_data
    
    async def record_query(self, user_id: int, query: DataQuery, result_count: int, credits: int):
        """记录查询"""
        try:
            conn = self.db.get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO query_records 
                (user_id, data_type, conditions, result_count, credits_consumed)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_id,
                query.data_type,
                json.dumps(query.conditions),
                result_count,
                credits
            ))
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            logger.error(f"记录查询失败: {e}")
    
    async def export_data(self, user_id: int, export_request: DataExport) -> str:
        """导出数据"""
        # 检查权限
        if 'data_export' not await self.get_user_permissions(user_id):
            raise HTTPException(status_code=403, detail="无数据导出权限")
        
        # 检查积分
        credits_needed = 50  # 导出固定50积分
        if not await self.deduct_credits(user_id, credits_needed, f"数据导出-{export_request.export_format}"):
            raise HTTPException(status_code=402, detail="积分不足")
        
        # 执行导出
        try:
            # 查询数据
            results = await self.execute_data_query(export_request.query)
            
            # 生成文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{export_request.query.data_type}_{timestamp}.{export_request.export_format}"
            filepath = f"/tmp/{filename}"
            
            if export_request.export_format == 'json':
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
            elif export_request.export_format == 'csv':
                import pandas as pd
                df = pd.DataFrame(results)
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
            elif export_request.export_format == 'excel':
                import pandas as pd
                df = pd.DataFrame(results)
                df.to_excel(filepath, index=False, engine='openpyxl')
            
            # 记录导出
            await self.record_query(user_id, export_request.query, len(results), credits_needed)
            
            return filepath
        except Exception as e:
            logger.error(f"数据导出失败: {e}")
            raise HTTPException(status_code=500, detail="数据导出失败")
    
    async def process_recharge(self, user_id: int, recharge: RechargeRequest) -> Dict:
        """处理充值"""
        try:
            # 验证交易
            if not await self.verify_transaction(recharge.tx_hash, recharge.amount):
                raise HTTPException(status_code=400, detail="交易验证失败")
            
            # 计算积分
            credits = int(recharge.amount * 10000)  # 1 USDT = 10000 积分
            
            # 更新用户积分
            conn = self.db.get_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE api_users 
                SET credits = credits + ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (credits, user_id))
            
            # 记录充值
            cur.execute("""
                INSERT INTO recharge_records 
                (user_id, amount, tx_hash, currency, credits, status)
                VALUES (?, ?, ?, ?, ?, 'completed')
            """, (user_id, recharge.amount, recharge.tx_hash, recharge.currency, credits))
            
            conn.commit()
            cur.close()
            conn.close()
            
            return {
                'credits_added': credits,
                'transaction_hash': recharge.tx_hash,
                'amount': recharge.amount,
                'currency': recharge.currency
            }
        except Exception as e:
            logger.error(f"处理充值失败: {e}")
            raise HTTPException(status_code=500, detail="处理充值失败")
    
    async def verify_transaction(self, tx_hash: str, amount: float) -> bool:
        """验证交易"""
        # 这里应该调用区块链API验证交易
        # 模拟验证
        await asyncio.sleep(1)  # 模拟网络延迟
        return len(tx_hash) == 64 and amount > 0
    
    async def get_user_permissions(self, user_id: int) -> List[str]:
        """获取用户权限"""
        try:
            conn = self.db.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT permissions FROM api_users WHERE id = ?", (user_id,))
            result = cur.fetchone()
            cur.close()
            conn.close()
            
            if result and result[0]:
                return json.loads(result[0])
            return []
        except Exception as e:
            logger.error(f"获取用户权限失败: {e}")
            return []
    
    async def get_user_stats(self, user_id: int) -> Dict:
        """获取用户统计"""
        try:
            conn = self.db.get_connection()
            cur = conn.cursor()
            
            # 获取用户信息
            cur.execute("""
                SELECT username, credits, rate_limit, created_at
                FROM api_users 
                WHERE id = ?
            """, (user_id,))
            user_info = cur.fetchone()
            
            # 获取使用统计
            cur.execute("""
                SELECT COUNT(*) as total_requests,
                       AVG(response_time) as avg_response_time,
                       SUM(credits_consumed) as total_credits_used
                FROM api_usage 
                WHERE user_id = ? AND created_at >= DATE('now', '-30 days')
            """, (user_id,))
            usage_stats = cur.fetchone()
            
            # 获取查询统计
            cur.execute("""
                SELECT data_type, COUNT(*) as count, SUM(result_count) as total_results
                FROM query_records 
                WHERE user_id = ? AND created_at >= DATE('now', '-30 days')
                GROUP BY data_type
            """, (user_id,))
            query_stats = cur.fetchall()
            
            cur.close()
            conn.close()
            
            return {
                'user_info': {
                    'username': user_info[0],
                    'credits': user_info[1],
                    'rate_limit': user_info[2],
                    'created_at': user_info[3]
                },
                'usage_stats': {
                    'total_requests': usage_stats[0] or 0,
                    'avg_response_time': usage_stats[1] or 0,
                    'total_credits_used': usage_stats[2] or 0
                },
                'query_stats': [
                    {
                        'data_type': row[0],
                        'count': row[1],
                        'total_results': row[2]
                    }
                    for row in query_stats
                ]
            }
        except Exception as e:
            logger.error(f"获取用户统计失败: {e}")
            raise HTTPException(status_code=500, detail="获取用户统计失败")

# FastAPI应用
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    global redis_client, api_service
    
    # 初始化Redis
    try:
        redis_client = redis.from_url(API_CONFIG['redis_url'])
        await redis_client.ping()
        logger.info("Redis连接成功")
    except Exception as e:
        logger.error(f"Redis连接失败: {e}")
        redis_client = None
    
    # 初始化数据库和服务
    db_manager = DatabaseManager(DB_PATH)
    api_service = BossJyAPIService(db_manager, redis_client)
    
    app.state.api_service = api_service
    app.state.redis_client = redis_client
    
    logger.info("API服务启动完成")
    
    yield
    
    # 关闭时清理
    if redis_client:
        await redis_client.close()
    logger.info("API服务已关闭")

# 创建FastAPI应用
app = FastAPI(
    title="BossJy API",
    description="BossJy 数据服务API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=API_CONFIG['cors_origins'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 中间件
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """日志中间件"""
    start_time = time.time()
    
    # 记录请求
    logger.info(f"请求开始: {request.method} {request.url}")
    
    # 处理请求
    response = await call_next(request)
    
    # 计算响应时间
    process_time = time.time() - start_time
    
    # 记录响应
    logger.info(f"请求完成: {response.status_code} - {process_time:.3f}s")
    
    # 添加响应头
    response.headers["X-Process-Time"] = str(process_time)
    
    # 更新Prometheus指标
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    REQUEST_DURATION.observe(process_time)
    
    return response

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """获取当前用户"""
    api_service = app.state.api_service
    
    # 解析API密钥
    try:
        api_key, api_secret = credentials.credentials.split(':', 1)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的API密钥格式",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证API密钥
    user = await api_service.verify_api_key(api_key, api_secret)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的API密钥",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 检查速率限制
    if not await api_service.check_rate_limit(user['id'], request.url.path):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="请求过于频繁，请稍后重试",
        )
    
    return user

# API路由
@app.get("/", response_model=APIResponse)
async def root():
    """根路径"""
    return APIResponse(
        success=True,
        message="BossJy API服务运行正常",
        data={
            "version": "2.0.0",
            "timestamp": datetime.utcnow(),
            "endpoints": [
                "/auth/login",
                "/data/query",
                "/data/export",
                "/user/stats",
                "/recharge"
            ]
        }
    )

@app.post("/auth/login", response_model=APIResponse)
async def login(credentials: UserCredentials):
    """用户登录"""
    api_service = app.state.api_service
    
    user = await api_service.authenticate_user(credentials)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 生成API密钥
    api_key = await api_service.generate_api_key(user['id'])
    
    return APIResponse(
        success=True,
        message="登录成功",
        data={
            "user_id": user['id'],
            "username": user['username'],
            "credits": user['credits'],
            "api_key": api_key.dict()
        }
    )

@app.post("/data/query", response_model=APIResponse)
async def query_data(query: DataQuery, current_user: Dict = Depends(get_current_user)):
    """查询数据"""
    api_service = app.state.api_service
    
    result = await api_service.query_data(current_user['id'], query)
    
    return APIResponse(
        success=True,
        message="查询成功",
        data=result
    )

@app.post("/data/export")
async def export_data(export_request: DataExport, current_user: Dict = Depends(get_current_user)):
    """导出数据"""
    api_service = app.state.api_service
    
    filepath = await api_service.export_data(current_user['id'], export_request)
    
    return FileResponse(
        filepath,
        media_type='application/octet-stream',
        filename=os.path.basename(filepath)
    )

@app.post("/recharge", response_model=APIResponse)
async def recharge(recharge: RechargeRequest, current_user: Dict = Depends(get_current_user)):
    """充值"""
    api_service = app.state.api_service
    
    result = await api_service.process_recharge(current_user['id'], recharge)
    
    return APIResponse(
        success=True,
        message="充值成功",
        data=result
    )

@app.get("/user/stats", response_model=APIResponse)
async def get_user_stats(current_user: Dict = Depends(get_current_user)):
    """获取用户统计"""
    api_service = app.state.api_service
    
    stats = await api_service.get_user_stats(current_user['id'])
    
    return APIResponse(
        success=True,
        message="获取统计成功",
        data=stats
    )

@app.get("/health", response_model=APIResponse)
async def health_check():
    """健康检查"""
    redis_status = "connected" if app.state.redis_client else "disconnected"
    
    return APIResponse(
        success=True,
        message="服务正常",
        data={
            "status": "operational",
            "timestamp": datetime.utcnow(),
            "services": {
                "api": "operational",
                "database": "operational",
                "redis": redis_status
            },
            "version": "2.0.0"
        }
    )

@app.get("/metrics")
async def metrics():
    """Prometheus指标"""
    if not API_CONFIG['debug']:
        raise HTTPException(status_code=404, detail="Not found")
    
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# 错误处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content=APIResponse(
            success=False,
            message=exc.detail,
            code=exc.status_code
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=APIResponse(
            success=False,
            message="服务器内部错误",
            code=500
        ).dict()
    )

# 启动服务
def main():
    """主函数"""
    logger.info("启动BossJy API服务...")
    
    uvicorn.run(
        "api_integration_service:app",
        host=API_CONFIG['host'],
        port=API_CONFIG['port'],
        reload=API_CONFIG['debug'],
        log_level="info"
    )

if __name__ == "__main__":
    main()