import logging
import random
import string
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from supabase import create_client, Client
import os

# Получаем токен из переменных окружения Vercel
BOT_TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Подключаемся к Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Генерация случайного кода
def generate_code(length=6):
    return ''.join(random.choices(string.digits, k=length))

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    logger.info(f"Пользователь {user.id} (@{user.username}) запустил бота")
    
    # Сохраняем пользователя в базу
    try:
        existing = supabase.table('telegram_users')\
            .select('*')\
            .eq('telegram_id', user.id)\
            .execute()
        
        if not existing.data:
            supabase.table('telegram_users').insert({
                'telegram_id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name or '',
                'chat_id': chat_id
            }).execute()
            logger.info(f"Новый пользователь сохранен: {user.id}")
    except Exception as e:
        logger.error(f"Ошибка сохранения пользователя: {e}")
    
    # Генерируем код
    code = generate_code()
    expires = datetime.now() + timedelta(minutes=5)
    
    # Сохраняем код в базу
    try:
        supabase.table('auth_codes').insert({
            'chat_id': chat_id,
            'code': code,
            'telegram_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'expires_at': expires.isoformat()
        }).execute()
        logger.info(f"Код {code} сохранен для пользователя {user.id}")
    except Exception as e:
        logger.error(f"Ошибка сохранения кода: {e}")
        await update.message.reply_text("❌ Ошибка сервера. Попробуйте позже.")
        return
    
    # Отправляем сообщение с кодом
    await update.message.reply_text(
        f"✅ <b>Ваш код подтверждения:</b>\n\n"
        f"<code>{code}</code>\n\n"
        f"⏰ Код действителен 5 минут\n\n"
        f"Введите этот код на сайте, чтобы войти в чат.",
        parse_mode='HTML'
    )

# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

def main():
    """Запуск бота"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("🤖 Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    main()
