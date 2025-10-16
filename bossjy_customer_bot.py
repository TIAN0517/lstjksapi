#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BossJy 客户服务机器人
功能：注册、充值、查询、试用样本、群组管理
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import sqlite3
import secrets

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler
)
from telegram.constants import ParseMode

# 导入Bot数据服务
try:
    from services.bot_data_service import BotDataService
    BOT_DATA_SERVICE_AVAILABLE = True
except ImportError:
    BOT_DATA_SERVICE_AVAILABLE = False

# 导入电话检测服务
try:
    import requests
    PHONE_DETECTION_AVAILABLE = True
    PHONE_API_URL = "http://localhost:18003"
except ImportError:
    PHONE_DETECTION_AVAILABLE = False

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token
BOT_TOKEN = "8431805678:AAHuBD2EwmeipWzgyZKaMvHTEefsXmACF0o"

# 数据库配置 - 使用SQLite
DB_PATH = 'bossjy_users.db'

# 官方网站
OFFICIAL_WEBSITE = "https://bossjy.tiankai.it.com"

# 对话状态
(REGISTER_USERNAME, REGISTER_EMAIL, REGISTER_PASSWORD) = range(3)

# 数据库连接池
def get_db_connection():
    """获取数据库连接"""
    return sqlite3.connect(DB_PATH)


# ==================== 群组管理功能 ====================
async def auto_bind_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """自动绑定群组到Bot"""
    if update.effective_chat.type in ['group', 'supergroup']:
        group_id = str(update.effective_chat.id)
        group_title = update.effective_chat.title
        group_type = update.effective_chat.type

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # 检查群组是否已绑定
            cur.execute("SELECT * FROM telegram_groups WHERE group_id = ?", (group_id,))
            existing_group = cur.fetchone()

            if not existing_group:
                # 新群组，自动绑定
                cur.execute("""
                    INSERT INTO telegram_groups (group_id, group_title, group_type, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, (group_id, group_title, group_type, 1))
                
                conn.commit()
                logger.info(f"Auto-bound new group: {group_title} ({group_id})")
                
                # 发送欢迎消息
                welcome_msg = f"""
🎉 **群组自动绑定成功！**

📋 群组信息：
• 名称：{group_title}
• ID：{group_id}
• 类型：{group_type}

✅ 本群已成功绑定到BossJy客户服务Bot！

🤖 **Bot功能：**
• 📝 用户注册
• 💰 账户充值  
• 🔍 数据查询
• 🎁 试用样本
• 👤 账户管理

📌 **常用命令：**
/start - 开始使用
/help - 查看帮助
/register - 注册账户
/recharge - 充值积分
/trial - 试用样本

💬 **直接发送消息即可与我对话！**
                """
                
                await update.message.reply_text(welcome_msg, parse_mode=ParseMode.MARKDOWN)
            else:
                # 更新群组信息
                cur.execute("""
                    UPDATE telegram_groups 
                    SET group_title = ?, group_type = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE group_id = ?
                """, (group_title, group_type, group_id))
                
                conn.commit()
                logger.info(f"Updated group info: {group_title} ({group_id})")

            cur.close()
            conn.close()

        except Exception as e:
            logger.error(f"Error in auto_bind_group: {e}")


async def auto_respond_in_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """在群组中自动响应消息"""
    if update.effective_chat.type in ['group', 'supergroup']:
        
        # 检查是否是@提及Bot
        if update.message and update.message.text and f"@{context.bot.username}" in update.message.text:
            await update.message.reply_text(
                "👋 您好！我是BossJy客户服务Bot。\n\n"
                "📋 **可用功能：**\n"
                "• 📝 用户注册\n"
                "• 💰 账户充值\n"
                "• 🔍 数据查询\n"
                "• 🎁 试用样本\n\n"
                "💬 **请发送 /start 开始使用**",
                parse_mode=ParseMode.MARKDOWN
            )
            return

        # 检查是否是直接命令
        if update.message and update.message.text and update.message.text.startswith('/'):
            command = update.message.text.split()[0].lower()
            
            if command in ['/start', '/help', '/register', '/recharge', '/trial', '/account']:
                await update.message.reply_text(
                    "👋 **欢迎使用BossJy客户服务！**\n\n"
                    "🤖 **我是您的专属客服Bot**\n\n"
                    "📋 **主要功能：**\n"
                    "• 📝 用户注册 - 创建账户\n"
                    "• 💰 账户充值 - 购买积分\n"
                    "• 🔍 数据查询 - 查看数据\n"
                    "• 🎁 试用样本 - 免费试用\n\n"
                    "💬 **请私信我使用完整功能**\n"
                    "或直接点击下方按钮：\n\n"
                    "🔗 [官方客服](https://t.me/bossjy_support)",
                    parse_mode=ParseMode.MARKDOWN
                )


async def track_group_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """记录群组成员信息"""
    if update.effective_chat.type in ['group', 'supergroup'] and update.effective_user:
        group_id = str(update.effective_chat.id)
        telegram_id = str(update.effective_user.id)
        username = update.effective_user.username
        first_name = update.effective_user.first_name
        last_name = update.effective_user.last_name

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # 记录成员信息
            cur.execute("""
                INSERT OR REPLACE INTO telegram_group_members
                (group_id, telegram_id, username, first_name, last_name, joined_at, last_active)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (group_id, telegram_id, username, first_name, last_name))

            conn.commit()
            cur.close()
            conn.close()

        except Exception as e:
            logger.error(f"Error tracking group member: {e}")


# ==================== 用户认证功能 ====================
def get_user_by_telegram_id(telegram_id: str) -> Optional[Dict]:
    """通过Telegram ID获取用户信息"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        user = cur.fetchone()
        if user:
            # 获取列名
            columns = [desc[0] for desc in cur.description]
            user_dict = dict(zip(columns, user))
        else:
            user_dict = None
        cur.close()
        conn.close()
        return user_dict
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return None


def create_user(telegram_id: str, username: str, email: str, password: str) -> Optional[int]:
    """创建新用户"""
    try:
        # 简单的密码哈希（生产环境应使用更安全的方法）
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO users (username, email, password_hash, telegram_id, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (username, email, password_hash, telegram_id, 1))

        user_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()

        return user_id
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return None


# ==================== 命令处理器 ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令"""
    # 追踪群组和成员
    await track_group(update, context)
    await track_group_member(update, context)

    user = update.effective_user
    telegram_id = str(user.id)

    # 检查用户是否已注册
    db_user = get_user_by_telegram_id(telegram_id)

    keyboard = [
        [KeyboardButton("📝 注册"), KeyboardButton("💰 充值")],
        [KeyboardButton("🔍 查询数据"), KeyboardButton("🎁 试用样本")],
        [KeyboardButton("📞 电话检测"), KeyboardButton("🌐 官方网站")],
        [KeyboardButton("👤 我的账户"), KeyboardButton("📊 我的群组")],
        [KeyboardButton("❓ 帮助")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    welcome_msg = f"""
👋 欢迎使用 BossJy 数据服务！

{'✅ 您已注册' if db_user else '⚠️ 您还未注册，请先注册'}

🤖 我可以帮你：
• 📝 注册账户
• 💰 充值积分（USDT）
• 🔍 查询各类数据
• 🎁 免费试用样本（每种数据100条）
• 📊 管理群组数据权限

请选择您需要的功能：
"""

    await update.message.reply_text(welcome_msg, reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /help 命令"""
    await track_group(update, context)
    await track_group_member(update, context)

    help_text = """
🤖 **BossJy 客户服务Bot 帮助**

📋 **主要功能：**
• 📝 用户注册 - 创建新账户
• 💰 账户充值 - 购买积分
• 🔍 查询数据 - 查看清洗结果
• 🎁 试用样本 - 免费试用数据
• 👤 我的账户 - 查看个人信息
• 📊 我的群组 - 管理群组
• 📞 电话检测 - 验证电话号码
• 🌐 官方网站 - 访问官网

💬 **使用方法：**
1. 私信Bot使用完整功能
2. 群组中@Bot或发送命令获得帮助
3. 直接点击下方按钮快速操作

📞 **电话检测功能：**
• 支持全球电话号码验证
• 提供号码格式化和类型检测
• 支持批量验证和搜索

🔗 **官方网站：** https://jytian.xyz
📞 **客服支持：** @bossjy_support
    """
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)


async def admin_list_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """管理员查看所有绑定群组"""
    # 简单的管理员验证（可以替换为更安全的验证方式）
    admin_users = [str(update.effective_user.id)]  # 这里添加管理员ID
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # 获取所有群组
        cur.execute("""
            SELECT g.*, COUNT(gm.telegram_id) as member_count
            FROM telegram_groups g
            LEFT JOIN telegram_group_members gm ON g.group_id = gm.group_id
            WHERE g.is_active = 1
            GROUP BY g.id, g.group_id, g.group_title, g.group_type, g.is_active, g.created_at, g.updated_at
            ORDER BY g.updated_at DESC
        """)
        groups = cur.fetchall()

        cur.close()
        conn.close()

        if not groups:
            await update.message.reply_text("📊 **暂无绑定的群组**")
            return

        # 构建群组列表
        group_list = "📊 **已绑定的群组列表：**\n\n"
        
        for group in groups:
            status = "✅ 活跃" if group['is_active'] else "❌ 停用"
            group_list += f"🏷️ **{group['group_title']}**\n"
            group_list += f"🆔 ID: `{group['group_id']}`\n"
            group_list += f"👥 成员: {group['member_count']} 人\n"
            group_list += f"📅 绑定: {group['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
            group_list += f"🔄 更新: {group['updated_at'].strftime('%Y-%m-%d %H:%M')}\n"
            group_list += f"📊 状态: {status}\n\n"

        group_list += f"📈 **总计：{len(groups)} 个群组**"

        # 如果消息太长，分段发送
        if len(group_list) > 4000:
            parts = [group_list[i:i+4000] for i in range(0, len(group_list), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text(group_list, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Error in admin_list_groups: {e}")
        await update.message.reply_text("❌ 获取群组列表失败，请稍后重试")


# ==================== 注册功能 ====================
async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """开始注册流程"""
    await track_group(update, context)
    await track_group_member(update, context)

    telegram_id = str(update.effective_user.id)
    user = get_user_by_telegram_id(telegram_id)

    if user:
        await update.message.reply_text("✅ 您已经注册过了！\n输入 /account 查看账户信息。")
        return ConversationHandler.END

    await update.message.reply_text(
        "📝 **开始注册**\n\n"
        "请输入您的用户名（3-20个字符，只能包含字母、数字、下划线）：",
        parse_mode=ParseMode.MARKDOWN
    )
    return REGISTER_USERNAME


async def register_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理用户名输入"""
    username = update.message.text.strip()

    # 验证用户名
    if len(username) < 3 or len(username) > 20:
        await update.message.reply_text("❌ 用户名长度必须在3-20个字符之间，请重新输入：")
        return REGISTER_USERNAME

    if not username.replace('_', '').isalnum():
        await update.message.reply_text("❌ 用户名只能包含字母、数字和下划线，请重新输入：")
        return REGISTER_USERNAME

    # 检查用户名是否已存在
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        exists = cur.fetchone()
        cur.close()
        conn.close()

        if exists:
            await update.message.reply_text("❌ 该用户名已被使用，请重新输入：")
            return REGISTER_USERNAME
    except Exception as e:
        logger.error(f"Error checking username: {e}")
        await update.message.reply_text("❌ 系统错误，请稍后重试。")
        return ConversationHandler.END

    context.user_data['username'] = username
    await update.message.reply_text("✅ 用户名可用！\n\n请输入您的邮箱地址：")
    return REGISTER_EMAIL


async def register_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理邮箱输入"""
    email = update.message.text.strip()

    # 简单的邮箱验证
    if '@' not in email or '.' not in email.split('@')[1]:
        await update.message.reply_text("❌ 邮箱格式不正确，请重新输入：")
        return REGISTER_EMAIL

    # 检查邮箱是否已存在
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email = ?", (email,))
        exists = cur.fetchone()
        cur.close()
        conn.close()

        if exists:
            await update.message.reply_text("❌ 该邮箱已被注册，请重新输入：")
            return REGISTER_EMAIL
    except Exception as e:
        logger.error(f"Error checking email: {e}")
        await update.message.reply_text("❌ 系统错误，请稍后重试。")
        return ConversationHandler.END

    context.user_data['email'] = email
    await update.message.reply_text("✅ 邮箱可用！\n\n请设置您的密码（至少6个字符）：")
    return REGISTER_PASSWORD


async def register_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理密码输入并完成注册"""
    password = update.message.text.strip()

    # 验证密码
    if len(password) < 6:
        await update.message.reply_text("❌ 密码至少需要6个字符，请重新输入：")
        return REGISTER_PASSWORD

    # 创建用户
    telegram_id = str(update.effective_user.id)
    username = context.user_data['username']
    email = context.user_data['email']

    user_id = create_user(telegram_id, username, email, password)

    if user_id:
        # 清除敏感数据
        context.user_data.clear()

        await update.message.reply_text(
            f"🎉 **注册成功！**\n\n"
            f"用户名：`{username}`\n"
            f"邮箱：`{email}`\n"
            f"Telegram ID：`{telegram_id}`\n\n"
            f"🎁 新用户福利：\n"
            f"• 免费试用所有数据类型（每种100条）\n"
            f"• 首次充值赠送10%积分\n\n"
            f"输入 /trial 开始试用数据！",
            parse_mode=ParseMode.MARKDOWN
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ 注册失败，请稍后重试。")
        return ConversationHandler.END


async def register_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """取消注册"""
    context.user_data.clear()
    await update.message.reply_text("❌ 注册已取消。\n输入 /start 重新开始。")
    return ConversationHandler.END


# ==================== 账户管理 ====================
async def account_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """显示账户信息"""
    await track_group(update, context)
    await track_group_member(update, context)

    telegram_id = str(update.effective_user.id)
    user = get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("⚠️ 您还未注册！\n输入 /register 开始注册。")
        return

    # 获取试用记录
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) as trial_count,
                   GROUP_CONCAT(data_type, ', ') as trial_types
            FROM sample_trials
            WHERE user_id = ?
        """, (user['id'],))
        trial_info = cur.fetchone()
        cur.close()
        conn.close()
    except:
        trial_info = (0, '无')

    account_text = f"""
👤 **账户信息**

**基本信息：**
用户名：`{user['username']}`
邮箱：`{user['email']}`
Telegram ID：`{telegram_id}`

**订阅信息：**
订阅级别：{user['subscription_tier'].upper()}
订阅状态：{'✅ 有效' if user.get('subscription_expires_at') else '⚠️ 未订阅'}

**使用情况：**
本月使用：{user.get('monthly_usage_count', 0)} 条
月度限额：{user.get('monthly_usage_limit', 0) if user.get('monthly_usage_limit') > 0 else '无限制'}

**试用记录：**
已试用：{trial_info['trial_count']} 种数据
类型：{trial_info['trial_types'] or '无'}

注册时间：{user['created_at'].strftime('%Y-%m-%d %H:%M')}
"""

    keyboard = [
        [InlineKeyboardButton("💰 充值", callback_data="recharge")],
        [InlineKeyboardButton("🎁 试用数据", callback_data="trial")],
        [InlineKeyboardButton("📊 查看群组", callback_data="mygroups")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(account_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


# ==================== 充值功能 ====================
async def recharge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """显示充值信息"""
    await track_group(update, context)
    await track_group_member(update, context)

    telegram_id = str(update.effective_user.id)
    user = get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("⚠️ 您还未注册！\n输入 /register 开始注册。")
        return

    # 生成用户专属充值地址
    user_address = generate_user_deposit_address(user['id'])
    
    recharge_text = f"""
💰 **USDT 充值**

**您的专属充值地址（TRC20）：**
`{user_address}`

**充值说明：**
1. 使用 TRON 网络（TRC20）转账
2. 最低充值金额：10 USDT
3. 1 USDT = 10,000 积分
4. 到账时间：3-10分钟（自动检测）

**充值后系统会自动检测到账：**
• 无需手动确认
• 自动发放积分
• 实时通知到账

**如需手动确认，请提供：**
• 交易哈希（TX Hash）
• 充值金额
• 您的用户ID：`{user['id']}`

发送格式：
`/confirm <TX_Hash> <金额>`

例如：
`/confirm abc123def456 100`

**优惠活动：**
🎁 首次充值额外赠送 10%
🎁 充值 ≥100 USDT 赠送 15%
🎁 充值 ≥500 USDT 赠送 20%

**当前汇率：**
1 USDT = 10,000 积分 + 优惠赠送
"""

    keyboard = [
        [InlineKeyboardButton("📊 查看充值记录", callback_data="recharge_history")],
        [InlineKeyboardButton("💳 积分明细", callback_data="credit_history")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(recharge_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


async def confirm_recharge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理充值确认"""
    await track_group(update, context)
    await track_group_member(update, context)

    telegram_id = str(update.effective_user.id)
    user = get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("⚠️ 您还未注册！\n输入 /register 开始注册。")
        return

    # 解析命令参数
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ 格式错误！\n\n"
            "正确格式：\n"
            "/confirm <TX_Hash> <金额>\n\n"
            "例如：\n"
            "/confirm abc123def456 100",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    tx_hash = context.args[0]
    try:
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ 金额格式错误！请输入数字。")
        return

    if amount < 10:
        await update.message.reply_text("❌ 最低充值金额为 10 USDT")
        return

    # 检查是否已经处理过
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM recharge_records 
            WHERE tx_hash = ? AND status != 'failed'
        """, (tx_hash,))
        existing = cur.fetchone()
        cur.close()
        conn.close()

        if existing:
            await update.message.reply_text("⚠️ 此交易已处理过，请勿重复提交。")
            return
    except Exception as e:
        logger.error(f"检查交易记录失败: {e}")

    # 验证交易
    await update.message.reply_text("⏳ 正在验证交易，请稍候...")

    verification_result = await verify_tron_transaction(tx_hash, amount, user['id'])
    
    if verification_result['success']:
        # 计算积分和优惠
        credits, bonus_rate = calculate_credits(amount, user['id'])
        
        # 更新用户积分
        success = update_user_credits(user['id'], credits)
        
        if success:
            # 记录充值历史
            record_recharge(user['id'], tx_hash, amount, credits, bonus_rate, 'completed')
            
            success_msg = f"""
✅ **充值成功！**

💰 **充值详情：**
• 交易哈希：`{tx_hash[:10]}...{tx_hash[-10:]}`
• 充值金额：{amount} USDT
• 获得积分：{credits:,} 积分
• 优惠赠送：{bonus_rate*100:.0f}%

💳 **账户信息：**
• 用户ID：{user['id']}
• 当前积分：{get_user_credits(user['id']):,} 积分

🎉 **积分已到账，您现在可以：**
• 查询数据
• 下载样本
• 使用API服务

感谢您的支持！
"""
            
            keyboard = [
                [InlineKeyboardButton("📊 查看数据", callback_data="query_data")],
                [InlineKeyboardButton("🎁 试用样本", callback_data="trial")],
                [InlineKeyboardButton("💳 积分明细", callback_data="credit_history")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(success_msg, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
        else:
            await update.message.reply_text("❌ 积分更新失败，请联系客服。")
    else:
        # 记录失败的充值尝试
        record_recharge(user['id'], tx_hash, amount, 0, 0, 'failed', verification_result['message'])
        
        error_msg = f"""
❌ **充值验证失败**

**失败原因：**
{verification_result['message']}

**请检查：**
• 交易哈希是否正确
• 充值金额是否匹配
• 是否使用TRC20网络
• 交易是否已确认

如有疑问，请联系客服。
"""
        await update.message.reply_text(error_msg, parse_mode=ParseMode.MARKDOWN)


def generate_user_deposit_address(user_id: int) -> str:
    """生成用户专属充值地址"""
    # 这里可以实现地址生成逻辑，比如基于用户ID生成特定地址
    # 或者使用支付网关的API生成地址
    base_address = "TEKcZDV8UKzXvHmHqV7nWFJRqQJfYsZkXb"
    
    # 简单的地址映射（实际应用中应该使用更安全的方法）
    address_suffix = format(user_id % 1000000, '06d')
    return f"{base_address}{address_suffix}"


async def verify_tron_transaction(tx_hash: str, amount: float, user_id: int) -> Dict:
    """验证TRON交易"""
    try:
        # 这里应该调用TRON API验证交易
        # 示例代码，实际需要集成TRON API
        
        # 模拟API调用
        import time
        await asyncio.sleep(2)  # 模拟网络延迟
        
        # 模拟验证结果（实际应该查询区块链）
        if tx_hash.startswith("test") or len(tx_hash) == 64:
            return {
                'success': True,
                'message': '交易验证成功',
                'actual_amount': amount,
                'confirmations': 12
            }
        else:
            return {
                'success': False,
                'message': '交易哈希格式错误或交易未找到'
            }
            
    except Exception as e:
        logger.error(f"验证交易失败: {e}")
        return {
            'success': False,
            'message': f'验证失败: {str(e)}'
        }


def calculate_credits(amount: float, user_id: int) -> tuple[int, float]:
    """计算积分和优惠"""
    base_credits = int(amount * 10000)  # 1 USDT = 10,000 积分
    
    # 检查是否是首次充值
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) as recharge_count 
            FROM recharge_records 
            WHERE user_id = ? AND status = 'completed'
        """, (user_id,))
        result = cur.fetchone()
        is_first_time = result['recharge_count'] == 0 if result else True
        cur.close()
        conn.close()
    except:
        is_first_time = True
    
    # 计算优惠
    bonus_rate = 0.0
    if is_first_time:
        bonus_rate = 0.10  # 首次充值10%
    elif amount >= 500:
        bonus_rate = 0.20  # 500 USDT以上20%
    elif amount >= 100:
        bonus_rate = 0.15  # 100 USDT以上15%
    
    bonus_credits = int(base_credits * bonus_rate)
    total_credits = base_credits + bonus_credits
    
    return total_credits, bonus_rate


def update_user_credits(user_id: int, credits: int) -> bool:
    """更新用户积分"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 检查用户积分记录是否存在
        cur.execute("SELECT credits FROM user_credits WHERE user_id = ?", (user_id,))
        result = cur.fetchone()
        
        if result:
            # 更新现有积分
            cur.execute("""
                UPDATE user_credits 
                SET credits = credits + ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """, (credits, user_id))
        else:
            # 创建积分记录
            cur.execute("""
                INSERT INTO user_credits (user_id, credits, created_at, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (user_id, credits))
        
        conn.commit()
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"更新用户积分失败: {e}")
        return False


def get_user_credits(user_id: int) -> int:
    """获取用户积分"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT credits FROM user_credits WHERE user_id = ?", (user_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        return result['credits'] if result else 0
    except:
        return 0


def record_recharge(user_id: int, tx_hash: str, amount: float, credits: int, 
                   bonus_rate: float, status: str, message: str = None):
    """记录充值历史"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO recharge_records 
            (user_id, tx_hash, amount, credits, bonus_rate, status, message, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, tx_hash, amount, credits, bonus_rate, status, message))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"记录充值历史失败: {e}")


async def recharge_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看充值记录"""
    query = update.callback_query
    await query.answer()

    telegram_id = str(query.from_user.id)
    user = get_user_by_telegram_id(telegram_id)

    if not user:
        await query.message.reply_text("⚠️ 您还未注册！")
        return

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT tx_hash, amount, credits, bonus_rate, status, created_at, message
            FROM recharge_records
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 10
        """, (user['id'],))
        records = cur.fetchall()
        cur.close()
        conn.close()

        if not records:
            await query.message.reply_text("📊 您暂无充值记录。")
            return

        history_text = "💳 **充值记录**\n\n"
        
        for record in records:
            status_icon = "✅" if record['status'] == 'completed' else "❌"
            bonus_text = f" (+{record['bonus_rate']*100:.0f}%)" if record['bonus_rate'] > 0 else ""
            
            history_text += f"{status_icon} **{record['amount']} USDT**\n"
            history_text += f"   积分: {record['credits']:,}{bonus_text}\n"
            history_text += f"   时间: {record['created_at'].strftime('%Y-%m-%d %H:%M')}\n"
            history_text += f"   哈希: `{record['tx_hash'][:10]}...{record['tx_hash'][-10:]}`\n\n"

        await query.message.reply_text(history_text, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"获取充值记录失败: {e}")
        await query.message.reply_text("❌ 获取充值记录失败。")


async def credit_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """查看积分使用明细"""
    query = update.callback_query
    await query.answer()

    telegram_id = str(query.from_user.id)
    user = get_user_by_telegram_id(telegram_id)

    if not user:
        await query.message.reply_text("⚠️ 您还未注册！")
        return

    current_credits = get_user_credits(user['id'])
    
    credit_text = f"""
💳 **积分明细**

💰 **当前积分：** {current_credits:,}

📊 **积分来源：**
• 充值获得
• 优惠赠送
• 系统赠送

📋 **使用记录：**
• 数据查询消费
• 样本下载消费
• API调用消费

💡 **获取更多积分：**
点击 /充值 进行充值
"""

    keyboard = [
        [InlineKeyboardButton("💰 充值", callback_data="recharge")],
        [InlineKeyboardButton("📊 使用记录", callback_data="usage_history")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(credit_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


# ==================== 样本试用功能 ====================
async def trial_samples(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """显示可试用的数据类型"""
    await track_group(update, context)
    await track_group_member(update, context)

    telegram_id = str(update.effective_user.id)
    user = get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("⚠️ 您还未注册！\n输入 /register 开始注册。")
        return

    # 获取已试用的数据类型
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT data_type FROM sample_trials
            WHERE user_id = ?
        """, (user['id'],))
        used_trials = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
    except:
        used_trials = []

    # 可用的数据类型
    data_types = {
        'hongkong': '🇭🇰 香港数据',
        'indonesia': '🇮🇩 印尼数据',
        'australia': '🇦🇺 澳洲数据',
        'global_chinese': '🌏 全球华人数据',
        'singapore': '🇸🇬 新加坡数据',
    }

    keyboard = []
    for key, label in data_types.items():
        if key in used_trials:
            button_text = f"{label} ✅"
            callback = f"trial_used_{key}"
        else:
            button_text = f"{label} (100条免费)"
            callback = f"trial_{key}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback)])

    trial_text = f"""
🎁 **免费样本试用**

每种数据类型可免费试用 **100条**
每个账户每种类型只能试用一次

您已试用：{len(used_trials)} / {len(data_types)} 种

请选择要试用的数据类型：
"""

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(trial_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


async def handle_trial_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理试用回调"""
    query = update.callback_query
    await query.answer()

    telegram_id = str(query.from_user.id)
    user = get_user_by_telegram_id(telegram_id)

    if not user:
        await query.message.reply_text("⚠️ 您还未注册！")
        return

    # 解析回调数据
    if query.data.startswith('trial_used_'):
        await query.message.reply_text("✅ 您已经试用过这种数据类型了！")
        return

    if not query.data.startswith('trial_'):
        return

    data_type = query.data.replace('trial_', '')

    # 检查是否已试用
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM sample_trials
            WHERE user_id = %s AND data_type = %s
        """, (user['id'], data_type))
        existing = cur.fetchone()

        if existing:
            await query.message.reply_text("✅ 您已经试用过这种数据类型了！")
            cur.close()
            conn.close()
            return

        # 创建试用记录
        cur.execute("""
            INSERT INTO sample_trials (user_id, telegram_id, data_type, sample_count, status, created_at, expires_at)
            VALUES (%s, %s, %s, 100, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP + INTERVAL '7 days')
            RETURNING id
        """, (user['id'], telegram_id, data_type))

        trial_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()

        success_text = f"""
✅ **试用申请成功！**

数据类型：{data_type}
样本数量：100 条
有效期：7 天

📥 样本数据将在 5-10 分钟内生成
生成完成后会发送给您

试用ID：`{trial_id}`

查看试用记录：/mytrial
"""

        await query.message.reply_text(success_text, parse_mode=ParseMode.MARKDOWN)

        # TODO: 触发样本生成任务

    except Exception as e:
        logger.error(f"Error creating trial: {e}")
        await query.message.reply_text("❌ 申请失败，请稍后重试。")


# ==================== 群组管理功能 ====================
async def my_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """显示用户加入的群组"""
    await track_group(update, context)
    await track_group_member(update, context)

    telegram_id = str(update.effective_user.id)
    user = get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("⚠️ 您还未注册！")
        return

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # 获取用户加入的群组
        cur.execute("""
            SELECT g.group_id, g.group_title, g.group_type,
                   gm.joined_at, gm.is_admin
            FROM telegram_groups g
            JOIN telegram_group_members gm ON g.group_id = gm.group_id
            WHERE gm.telegram_id = ?
            ORDER BY gm.joined_at DESC
        """, (telegram_id,))
        groups = cur.fetchall()
        cur.close()
        conn.close()

        if not groups:
            await update.message.reply_text("📊 您还没有加入任何群组。")
            return

        groups_text = f"📊 **我的群组** ({len(groups)}个)\n\n"

        for g in groups:
            admin_badge = " 👑" if g['is_admin'] else ""
            groups_text += f"• {g['group_title']}{admin_badge}\n"
            groups_text += f"  ID: `{g['group_id']}`\n"
            groups_text += f"  类型: {g['group_type']}\n"
            groups_text += f"  加入时间: {g['joined_at'].strftime('%Y-%m-%d')}\n\n"

        await update.message.reply_text(groups_text, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Error getting groups: {e}")
        await update.message.reply_text("❌ 获取群组信息失败。")


# ==================== 数据查询 ====================
async def data_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """显示数据库统计信息"""
    await track_group(update, context)
    await track_group_member(update, context)

    if not BOT_DATA_SERVICE_AVAILABLE:
        await update.message.reply_text("❌ 数据查询服务暂时不可用")
        return

    try:
        bot_service = BotDataService()
        stats_message = bot_service.get_database_stats()
        await update.message.reply_text(stats_message, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(f"Error getting data stats: {e}")
        await update.message.reply_text("❌ 获取数据统计失败")


# ==================== 电话检测功能 ====================
async def phone_detection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """电话检测功能"""
    await track_group(update, context)
    await track_group_member(update, context)

    telegram_id = str(update.effective_user.id)
    user = get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("⚠️ 您还未注册！\n输入 /register 开始注册。")
        return

    if not PHONE_DETECTION_AVAILABLE:
        await update.message.reply_text("❌ 电话检测服务暂时不可用")
        return

    phone_text = """
📞 **电话号码检测**

🔍 **支持功能：**
• 全球电话号码验证
• 号码格式化和类型检测
• 运营商信息查询
• 时区信息获取
• 批量号码验证

📋 **使用方法：**
1. 直接发送电话号码
2. 使用 /validate <号码> 验证单个号码
3. 使用 /batch <号码1,号码2> 批量验证

💡 **支持的格式：**
• 国际格式：+85291234567
• 国家代码：85291234567
• 本地格式：91234567 (需指定国家)

📊 **检测信息：**
• 有效性验证
• 号码类型（手机/固话等）
• 所属国家和地区
• 标准格式化
• 运营商信息

请发送要检测的电话号码：
"""

    keyboard = [
        [InlineKeyboardButton("📊 检测统计", callback_data="phone_stats")],
        [InlineKeyboardButton("📋 使用帮助", callback_data="phone_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(phone_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

async def validate_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """验证电话号码"""
    await track_group(update, context)
    await track_group_member(update, context)

    telegram_id = str(update.effective_user.id)
    user = get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("⚠️ 您还未注册！\n输入 /register 开始注册。")
        return

    if not PHONE_DETECTION_AVAILABLE:
        await update.message.reply_text("❌ 电话检测服务暂时不可用")
        return

    if not context.args:
        await update.message.reply_text(
            "❌ 请提供电话号码\n\n"
            "使用方法：\n"
            "/validate <电话号码>\n\n"
            "示例：\n"
            "/validate +85291234567\n"
            "/validate 91234567 HK"
        )
        return

    phone = context.args[0]
    country_code = context.args[1] if len(context.args) > 1 else None

    await update.message.reply_text("🔍 正在验证电话号码，请稍候...")

    try:
        # 调用电话检测API
        response = requests.post(
            f"{PHONE_API_URL}/validate",
            json={
                "phone": phone,
                "country_code": country_code,
                "format_type": "E164"
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            
            status_icon = "✅" if result['is_valid'] else "❌"
            
            validation_text = f"""
{status_icon} **电话号码验证结果**

📞 **原始号码：** `{result['phone']}`
🌍 **国家代码：** {result['country_code']}
🏳️ **地区代码：** {result['region_code']}
📱 **号码类型：** {result['phone_type']}

📋 **格式化结果：**
• 国际格式：`{result['formatted_international']}`
• 国家格式：`{result['formatted_national']}`
• E164格式：`{result['formatted_e164']}`

📊 **验证信息：**
• 有效性：{'✅ 有效' if result['is_valid'] else '❌ 无效'}
• 验证分数：{result['validation_score']:.2f}/1.0
"""
            
            if result.get('carrier'):
                validation_text += f"• 运营商：{result['carrier']}\n"
            
            if result.get('timezone'):
                validation_text += f"• 时区：{result['timezone']}\n"
            
            validation_text += f"\n🕐 验证时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            await update.message.reply_text(validation_text, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("❌ 验证失败，请稍后重试。")

    except requests.Timeout:
        await update.message.reply_text("❌ 验证超时，请稍后重试。")
    except Exception as e:
        logger.error(f"电话验证失败: {e}")
        await update.message.reply_text("❌ 验证失败，请稍后重试。")

async def batch_validate_phones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """批量验证电话号码"""
    await track_group(update, context)
    await track_group_member(update, context)

    telegram_id = str(update.effective_user.id)
    user = get_user_by_telegram_id(telegram_id)

    if not user:
        await update.message.reply_text("⚠️ 您还未注册！\n输入 /register 开始注册。")
        return

    if not PHONE_DETECTION_AVAILABLE:
        await update.message.reply_text("❌ 电话检测服务暂时不可用")
        return

    if not context.args:
        await update.message.reply_text(
            "❌ 请提供电话号码列表\n\n"
            "使用方法：\n"
            "/batch <号码1,号码2,号码3>\n\n"
            "示例：\n"
            "/batch +85291234567,+8613812345678"
        )
        return

    phones_text = context.args[0]
    phones = [phone.strip() for phone in phones_text.split(',') if phone.strip()]

    if len(phones) > 50:
        await update.message.reply_text("❌ 批量验证最多支持50个号码")
        return

    await update.message.reply_text(f"🔍 正在验证 {len(phones)} 个电话号码，请稍候...")

    try:
        # 调用批量验证API
        response = requests.post(
            f"{PHONE_API_URL}/validate/batch",
            json={
                "phones": phones,
                "format_type": "E164"
            },
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            results = result['results']
            
            valid_count = sum(1 for r in results if r['is_valid'])
            invalid_count = len(results) - valid_count
            
            batch_text = f"""
📊 **批量验证结果**

📞 **总数量：** {len(results)}
✅ **有效号码：** {valid_count}
❌ **无效号码：** {invalid_count}

📋 **详细结果：**
"""
            
            for i, phone_result in enumerate(results[:10], 1):  # 只显示前10个
                status_icon = "✅" if phone_result['is_valid'] else "❌"
                batch_text += f"{i}. {status_icon} `{phone_result['formatted_e164']}`\n"
            
            if len(results) > 10:
                batch_text += f"... 还有 {len(results) - 10} 个结果\n"
            
            batch_text += f"\n🕐 验证时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            await update.message.reply_text(batch_text, parse_mode=ParseMode.MARKDOWN)
        else:
            await update.message.reply_text("❌ 批量验证失败，请稍后重试。")

    except requests.Timeout:
        await update.message.reply_text("❌ 验证超时，请稍后重试。")
    except Exception as e:
        logger.error(f"批量电话验证失败: {e}")
        await update.message.reply_text("❌ 验证失败，请稍后重试。")

async def phone_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """电话检测统计"""
    query = update.callback_query
    await query.answer()

    if not PHONE_DETECTION_AVAILABLE:
        await query.message.reply_text("❌ 电话检测服务暂时不可用")
        return

    try:
        # 调用统计API
        response = requests.get(f"{PHONE_API_URL}/stats?days=30", timeout=10)

        if response.status_code == 200:
            stats = response.json()
            
            stats_text = f"""
📊 **电话检测统计（30天）**

📈 **验证统计：**
• 总验证数：{stats['total_validations']:,}
• 有效号码：{stats['valid_phones']:,}
• 无效号码：{stats['invalid_phones']:,}
• 有效率：{stats['valid_rate']:.2%}

🌍 **热门国家/地区："""
            
            for country_stat in stats['country_stats'][:5]:
                stats_text += f"\n• {country_stat['country']}: {country_stat['count']:,}"
            
            stats_text += f"\n\n📱 **号码类型分布："""
            
            for type_stat in stats['type_stats'][:5]:
                stats_text += f"\n• {type_stat['type']}: {type_stat['count']:,}"
            
            await query.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)
        else:
            await query.message.reply_text("❌ 获取统计失败，请稍后重试。")

    except Exception as e:
        logger.error(f"获取电话统计失败: {e}")
        await query.message.reply_text("❌ 获取统计失败，请稍后重试。")

async def phone_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """电话检测帮助"""
    query = update.callback_query
    await query.answer()

    help_text = """
📞 **电话检测使用帮助**

📋 **支持的命令：**
• /validate <号码> - 验证单个号码
• /batch <号码1,号码2> - 批量验证
• /phone - 电话检测主界面

🔍 **验证功能：**
• 有效性验证
• 号码格式化
• 类型识别（手机/固话等）
• 国家地区识别
• 运营商信息
• 时区信息

💡 **使用技巧：**
1. 使用国际格式获得最佳结果
2. 批量验证用逗号分隔号码
3. 可以指定国家代码提高准确性
4. 支持全球200+国家号码

📞 **支持的号码格式：**
• +85291234567 (国际格式)
• 85291234567 (国家代码)
• 91234567 (本地，需指定国家)

🌐 **支持的国家：**
香港、澳门、台湾、中国大陆、
新加坡、马来西亚、印尼、
澳洲、美国、加拿大等200+国家

如有问题请联系客服：@bossjy_support
"""

    await query.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

# ==================== 网站和帮助 ====================
async def website(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """显示官方网站"""
    await track_group(update, context)
    await track_group_member(update, context)

    website_text = f"""
🌐 **官方网站**

{OFFICIAL_WEBSITE}

**功能特点：**
✅ 在线数据查询
✅ 批量数据处理
✅ API接口服务
✅ 实时数据分析
✅ 多维度筛选

访问网站获取更多功能！
"""

    keyboard = [[InlineKeyboardButton("🌐 打开网站", url=OFFICIAL_WEBSITE)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(website_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)


# ==================== 消息处理器 ====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理文本消息"""
    await track_group(update, context)
    await track_group_member(update, context)

    text = update.message.text

    if text == "📝 注册":
        await register_start(update, context)
    elif text == "💰 充值":
        await recharge(update, context)
    elif text == "🔍 查询数据":
        await data_stats(update, context)
    elif text == "🎁 试用样本":
        await trial_samples(update, context)
    elif text == "🌐 官方网站":
        await website(update, context)
    elif text == "👤 我的账户":
        await account_info(update, context)
    elif text == "📊 我的群组":
        await my_groups(update, context)
    elif text == "❓ 帮助":
        await help_command(update, context)


# ==================== 主函数 ====================
def main():
    """启动Bot"""
    # 创建Application
    application = Application.builder().token(BOT_TOKEN).build()

    # 注册处理器
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("account", account_info))
    application.add_handler(CommandHandler("recharge", recharge))
    application.add_handler(CommandHandler("confirm", confirm_recharge))
    application.add_handler(CommandHandler("trial", trial_samples))
    application.add_handler(CommandHandler("mygroups", my_groups))
    application.add_handler(CommandHandler("website", website))
    application.add_handler(CommandHandler("admin_groups", admin_list_groups))
    application.add_handler(CommandHandler("stats", data_stats))
    
    # 电话检测相关命令
    application.add_handler(CommandHandler("phone", phone_detection))
    application.add_handler(CommandHandler("validate", validate_phone))
    application.add_handler(CommandHandler("batch", batch_validate_phones))

    # 注册对话处理器
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("register", register_start)],
        states={
            REGISTER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_username)],
            REGISTER_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_email)],
            REGISTER_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, register_password)],
        },
        fallbacks=[CommandHandler("cancel", register_cancel)],
    )
    application.add_handler(conv_handler)

    # 回调查询处理器
    application.add_handler(CallbackQueryHandler(handle_trial_callback))
    application.add_handler(CallbackQueryHandler(recharge_history, pattern='^recharge_history

    # 文本消息处理器
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 群组消息处理器 - 优先级高
    application.add_handler(MessageHandler(filters.UpdateType.MESSAGE, auto_bind_group), group=1)
    application.add_handler(MessageHandler(filters.UpdateType.MESSAGE, track_group_member), group=2)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_respond_in_group), group=3)

    # 启动Bot
    logger.info("BossJy Customer Bot 启动中...")
    application.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    main()
))
    application.add_handler(CallbackQueryHandler(credit_history, pattern='^credit_history

    # 文本消息处理器
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 群组消息处理器 - 优先级高
    application.add_handler(MessageHandler(filters.UpdateType.MESSAGE, auto_bind_group), group=1)
    application.add_handler(MessageHandler(filters.UpdateType.MESSAGE, track_group_member), group=2)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_respond_in_group), group=3)

    # 启动Bot
    logger.info("BossJy Customer Bot 启动中...")
    application.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    main()
))

    # 文本消息处理器
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 群组消息处理器 - 优先级高
    application.add_handler(MessageHandler(filters.UpdateType.MESSAGE, auto_bind_group), group=1)
    application.add_handler(MessageHandler(filters.UpdateType.MESSAGE, track_group_member), group=2)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_respond_in_group), group=3)

    # 启动Bot
    logger.info("BossJy Customer Bot 启动中...")
    application.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    main()
