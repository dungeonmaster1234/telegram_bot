# bot.py (вставьте сюда код из предыдущего сообщения)
import logging
import pysqlite3 as sqlite3
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler,
                          CallbackQueryHandler, ContextTypes, filters)
import database  # ваш файл database.py

# Установите свой токен и ID админа
TOKEN = '7368248796:AAEaCqJv63V9a0Rz_yRuqLADRpjkjLpGfDM'
ADMIN_ID = 818644261  # замените на реальный Telegram user_id администратора

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Отправь свой вопрос, и администратор скоро ответит.")


# Обработка входящих сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text

    # Если это админ — проверяем, ожидается ли ответ
    if user.id == ADMIN_ID:
        pending_question_id = database.get_admin_pending_response(user.id)
        if pending_question_id:
            question_data = database.get_question_by_id(pending_question_id)
            if question_data:
                question_id, target_user_id, _, _, _ = question_data
                database.save_answer(question_id, text)
                database.clear_admin_pending_response(user.id)
                try:
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text=f'💬 Ответ администратора:\n{text}')
                    await update.message.reply_text("✅ Ответ отправлен.")
                except Exception as e:
                    await update.message.reply_text("❌ Ошибка отправки.")
            return

    # Если это пользователь — сохраняем вопрос + данные отправителя
    question_id = database.add_question(user_id=user.id,
                                        username=user.username,
                                        first_name=user.first_name,
                                        question=text)
    await update.message.reply_text("✅ Вопрос отправлен администратору.")

    # Формируем сообщение для админа с данными отправителя
    admin_message = (
        f"📩 Новый вопрос #{question_id}\n"
        f"├ От: {user.first_name} {f'(@{user.username})' if user.username else ''}\n"
        f"└ ID: `{user.id}`\n\n"
        f"Текст: {text}")
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✏️ Ответить",
                             callback_data=f"reply_{question_id}")
    ]])
    await context.bot.send_message(chat_id=ADMIN_ID,
                                   text=admin_message,
                                   reply_markup=keyboard,
                                   parse_mode='Markdown')


# Обработка кнопки "Ответить"
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("reply_"):
        question_id = int(data.split("_")[1])
        database.save_admin_pending_response(query.from_user.id, question_id)
        await query.message.reply_text(
            f"✏️ Введи ответ на вопрос #{question_id}:")


# Команда для просмотра всех необработанных вопросов (по желанию)
async def list_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔️ У вас нет прав.")
        return

    questions = database.get_pending_questions()
    if not questions:
        await update.message.reply_text("✅ Нет новых вопросов.")
        return

    for q in questions:
        question_id, user_id, question_text = q
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✏️ Ответить",
                                 callback_data=f"reply_{question_id}")
        ]])
        await update.message.reply_text(
            f"📨 Вопрос #{question_id} от пользователя {user_id}:\n{question_text}",
            reply_markup=keyboard)


# Главная функция запуска бота
async def main():
    database.init_db()

    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("list", list_questions))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logging.info("Бот запущен")
    await application.run_polling()


# Запуск
if __name__ == '__main__':
    import nest_asyncio

    nest_asyncio.apply()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
