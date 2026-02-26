import logging
import random
import string
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from supabase import create_client, Client
import os
import asyncio

# Настройки из переменных окружения
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Подключение к Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_code():
    return ''.join(random.choices(string.digits, k=6))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Генерируем код
    code = generate_code()
    expires = datetime.now() + timedelta(minutes=5)
    
    # Сохраняем в Supabase
    try:
        supabase.table('auth_codes').insert({
            'chat_id': chat_id,
            'code': code,
            'telegram_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'expires_at': expires.isoformat()
        }).execute()
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    
    # Отправляем код пользователю
    await update.message.reply_text(
        f"🔐 Ваш код для входа на сайт:\n\n"
        f"<code>{code}</code>\n\n"
        f"⏰ Действителен 5 минут",
        parse_mode='HTML'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

def main():
    """Запуск бота"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Бот запущен...")
    app.run_polling()

if __name__ == '__main__':
    main()
