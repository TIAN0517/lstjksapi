"""
BossJy-Pro Telegram Integration Service
Telegram Bot 集成服务
"""

import os
import sys
import asyncio
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
import httpx

# 设置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 从环境变量获取配置
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
MAIN_API_URL = os.getenv('MAIN_API_URL', 'http://localhost:8000')
MAIN_API_KEY = os.getenv('MAIN_API_KEY', '')

async def start_command(update: Update, context):
    """处理 /start 命令"""
    welcome_message = """
🚀 BossJy-Pro Telegram Bot 已启动！

📋 可用命令：
/start - 启动 Bot
/help - 查看帮助
/status - 查看系统状态
/query <内容> - 与 BossJy-Pro 主控系统交互
/translate <文本> - 翻译文本（支持多语言）
/clean_phone <号码> - 清洗电话号码
/dedupe - 开始数据去重任务

💡 提示：发送文件进行批量处理
    """
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context):
    """处理 /help 命令"""
    help_message = """
📚 BossJy-Pro Bot 帮助

🔑 系统命令：
/start - 启动 Bot
/help - 查看帮助
/status - 查看系统状态

🔄 交互命令：
/query <内容> - 与 BossJy-Pro 主控系统交互

💡 使用提示：
• 发送文件进行数据处理
• 使用 /query 命令与 AI 助手对话
• 查看 /status 了解系统状态
    """
    await update.message.reply_text(help_message)

async def status_command(update: Update, context):
    """处理 /status 命令"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MAIN_API_URL}/api/status")
            if response.status_code == 200:
                status_data = response.json()
                status_message = f"""
📊 BossJy-Pro 系统状态

🔑 API 密钥：{status_data.get('api_keys', {}).get('healthy', 0)}/{status_data.get('api_keys', {}).get('total', 0)} 健康

🤖 模型：{status_data.get('models', {}).get('current_model', 'N/A')}

🧹 助手服务：
• 助手A：{status_data.get('assistants', {}).get('assistant_a', 'N/A')}
• 助手B：{status_data.get('assistants', {}).get('assistant_b', 'N/A')}

🔧 服务状态：
• Dashboard：{status_data.get('services', {}).get('dashboard', 'N/A')}
• Telegram：{status_data.get('services', {}).get('telegram', 'N/A')}
• 数据管道：{status_data.get('services', {}).get('data_pipeline', 'N/A')}
                """
            else:
                status_message = "❌ 无法连接到主控系统"
    except Exception as e:
        status_message = f"❌ 状态查询失败：{str(e)}"
    
    await update.message.reply_text(status_message)

async def query_command(update: Update, context):
    """处理 /query 命令"""
    if not context.args:
        await update.message.reply_text("请提供查询内容，例如：/query 分析系统架构")
        return
    
    query_text = " ".join(context.args)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MAIN_API_URL}/api/query",
                json={"query": query_text},
                headers={"Authorization": f"Bearer {MAIN_API_KEY}"} if MAIN_API_KEY else {}
            )
            
            if response.status_code == 200:
                result = response.json()
                await update.message.reply_text(f"🤖 BossJy-Pro 回复：\n\n{result.get('response', '处理完成')}")
            else:
                await update.message.reply_text(f"❌ 查询失败：HTTP {response.status_code}")
    except Exception as e:
        await update.message.reply_text(f"❌ 查询失败：{str(e)}")

async def translate_command(update: Update, context):
    """处理 /translate 命令"""
    if not context.args:
        await update.message.reply_text(
            "📝 翻译命令格式：\n"
            "/translate <文本>\n"
            "/translate -s en -t zh-TW <文本>\n\n"
            "支持的语言：\n"
            "• en (英文)\n"
            "• zh-TW (繁体中文)\n"
            "• zh-CN (简体中文)\n"
            "• ja (日文)\n"
            "• ko (韩文)"
        )
        return

    # 解析参数
    source_lang = 'en'
    target_lang = 'zh-TW'
    text_to_translate = " ".join(context.args)

    # 检查是否指定了语言
    if '-s' in context.args:
        s_index = context.args.index('-s')
        if s_index + 1 < len(context.args):
            source_lang = context.args[s_index + 1]

    if '-t' in context.args:
        t_index = context.args.index('-t')
        if t_index + 1 < len(context.args):
            target_lang = context.args[t_index + 1]

    # 移除语言参数，获取纯文本
    args_filtered = [arg for arg in context.args if arg not in ['-s', '-t', source_lang, target_lang]]
    text_to_translate = " ".join(args_filtered)

    if not text_to_translate:
        await update.message.reply_text("请提供要翻译的文本")
        return

    await update.message.reply_text(f"🔄 正在翻译...")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{MAIN_API_URL}/api/translate",
                json={
                    "texts": [text_to_translate],
                    "source_lang": source_lang,
                    "target_lang": target_lang
                },
                headers={"Authorization": f"Bearer {MAIN_API_KEY}"} if MAIN_API_KEY else {}
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('results') and len(result['results']) > 0:
                    translation = result['results'][0]
                    quality_score = translation.get('quality_score', 0)

                    message = f"""
✅ 翻译完成

📝 原文：{translation['original']}

🌏 译文：{translation['translated']}

📊 质量评分：{quality_score:.2f}/1.00
🔤 语言：{source_lang} → {target_lang}
                    """
                    await update.message.reply_text(message)
                else:
                    await update.message.reply_text("❌ 翻译失败：无返回结果")
            else:
                await update.message.reply_text(f"❌ 翻译失败：HTTP {response.status_code}")
    except Exception as e:
        await update.message.reply_text(f"❌ 翻译失败：{str(e)}")

async def clean_phone_command(update: Update, context):
    """处理 /clean_phone 命令"""
    if not context.args:
        await update.message.reply_text(
            "📞 电话号码清洗格式：\n"
            "/clean_phone +1-416-555-1234\n"
            "/clean_phone -r CA 4165551234\n\n"
            "-r：指定默认国家代码（如 US, CA, CN, TW等）"
        )
        return

    # 解析参数
    default_region = None
    phone_number = " ".join(context.args)

    if '-r' in context.args:
        r_index = context.args.index('-r')
        if r_index + 1 < len(context.args):
            default_region = context.args[r_index + 1]
            args_filtered = [arg for arg in context.args if arg not in ['-r', default_region]]
            phone_number = " ".join(args_filtered)

    if not phone_number:
        await update.message.reply_text("请提供电话号码")
        return

    await update.message.reply_text(f"🔄 正在清洗电话号码...")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{MAIN_API_URL}/api/clean_phone",
                json={
                    "phone": phone_number,
                    "default_region": default_region
                },
                headers={"Authorization": f"Bearer {MAIN_API_KEY}"} if MAIN_API_KEY else {}
            )

            if response.status_code == 200:
                result = response.json()

                if result.get('is_valid'):
                    message = f"""
✅ 电话号码验证通过

📞 原始号码：{result['original']}
🌐 国际格式：{result['international']}
📱 E.164格式：{result['e164']}
🏴 国家/地区：{result['country_name']} ({result['country_code']})
🗺️ 地区：{result.get('region', 'N/A')}
📡 运营商：{result.get('carrier', 'N/A')}
📊 类型：{result['number_type']}
⏰ 时区：{', '.join(result.get('timezone', []))}
🎯 验证分数：{result.get('validation_score', 0):.2f}/1.00
                    """
                else:
                    message = f"""
⚠️ 电话号码可能无效

📞 原始号码：{result['original']}
❌ 错误：{result.get('error', '未知错误')}
                    """

                await update.message.reply_text(message)
            else:
                await update.message.reply_text(f"❌ 清洗失败：HTTP {response.status_code}")
    except Exception as e:
        await update.message.reply_text(f"❌ 清洗失败：{str(e)}")

async def handle_message(update: Update, context):
    """处理普通消息"""
    message_text = update.message.text
    await update.message.reply_text(f"收到消息：{message_text}\n\n使用 /help 查看可用命令")

async def error_handler(update: Update, context):
    """错误处理器"""
    logger.error(f"更新 {update} 导致错误：{context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("抱歉，处理您的请求时发生错误。请稍后重试。")

def main():
    """主函数"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("未设置 TELEGRAM_BOT_TOKEN 环境变量")
        return
    
    logger.info("🚀 启动 BossJy-Pro Telegram 集成服务...")
    
    # 创建应用
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # 添加处理器
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("query", query_command))
    application.add_handler(CommandHandler("translate", translate_command))
    application.add_handler(CommandHandler("clean_phone", clean_phone_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # 添加错误处理器
    application.add_error_handler(error_handler)
    
    logger.info("✅ Telegram Bot 服务已启动")
    
    # 启动 Bot
    application.run_polling()

if __name__ == "__main__":
    main()
