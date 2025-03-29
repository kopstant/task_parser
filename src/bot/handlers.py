from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from src.database.base import SessionLocal
from src.database.crud import get_problems_by_filter
from src.utils.helpers import format_problem_message
from sqlalchemy import text
from telegram.ext import ConversationHandler
import logging

logging.basicConfig(level=logging.INFO)


def get_topics_keyboard(topics):
    keyboard = []
    for i in range(0, len(topics), 2):
        row = []
        for topic in topics[i:i + 2]:
            row.append(InlineKeyboardButton(topic, callback_data=f"topic_{topic}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Привет! Я помогу тебе найти задачи на Codeforces.\n"
             "Введи сложность задачи (например, 800) или /cancel для отмены:"
    )
    return 0


async def handle_difficulty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        # Очищаем введенный текст от лишних пробелов
        rating_input = update.message.text.strip()
        logging.info(f"Пользователь ввел: '{rating_input}'")

        # Преобразуем строку в число
        rating = int(rating_input)  # Попробуем сразу преобразовать в число
        logging.info(f"Преобразуем значение {rating_input} в число {rating}")

        context.user_data['rating'] = rating

        db = SessionLocal()
        topics = db.execute(text("SELECT DISTINCT name FROM topics")).fetchall()
        logging.info(f"Topics from DB before processing: {topics}")
        db.close()

        topics = [topic[0].encode('utf-8', 'ignore').decode('utf-8', 'ignore') for topic in topics]
        logging.info(f"Processed topics: {topics}")

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Отлично! Теперь выбери тему:",
            reply_markup=get_topics_keyboard(topics)
        )
        return 1
    except ValueError as e:
        logging.error(f"Ошибка при преобразовании: {rating_input} | Exception: {e}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Пожалуйста, введите число (например, 800)"
        )
        return 0

async def handle_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    topic = update.callback_query.data.replace('topic_', '')
    context.user_data['topic'] = topic

    await show_problems(update, context)
    return -1


async def show_problems(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_data = context.user_data
    rating = user_data.get('rating')
    topic = user_data.get('topic')

    db = SessionLocal()
    problems = get_problems_by_filter(db, rating=rating, topic=topic)
    db.close()

    if not problems:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Задачи не найдены. Попробуйте другие параметры."
        )
        return

    response = [format_problem_message(problem) for problem in problems[:10]]

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="\n\n".join(response),
        parse_mode='HTML',
        disable_web_page_preview=True
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет текущий диалог и сбрасывает состояние"""
    await update.message.reply_text("Поиск отменён. Начните заново командой /start")
    # Очищаем user_data если нужно
    context.user_data.clear()
    return ConversationHandler.END  # Завершаем диалог
