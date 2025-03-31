from telegram import Update
from telegram.ext import ContextTypes
from src.database.base import SessionLocal
from src.database.crud import get_problems_by_filter
from src.utils.helpers import format_problem_message
from sqlalchemy import text
from telegram.ext import ConversationHandler
from src.bot.keyboards import get_topics_keyboard, get_difficulty_keyboard
import logging

logging.basicConfig(level=logging.INFO)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Привет! Я помогу тебе найти задачи на Codeforces.\n"
             "Введи сложность задачи (800-2000, с шагом в 200).\n"
             "/cancel для отмены:",
        reply_markup=get_difficulty_keyboard()
    )
    return 0


async def handle_difficulty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        rating_input = update.message.text.strip()
        rating = int(rating_input)
        context.user_data['rating'] = rating

        db = SessionLocal()
        try:
            # Добавляем логирование запроса
            logging.info("Fetching topics from database...")
            topics = db.execute(text("SELECT DISTINCT name FROM topics ORDER BY name")).fetchall()
            logging.info(f"Raw topics from DB: {topics}")

            if not topics:
                logging.warning("No topics found in database!")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="В базе данных нет доступных тем. Попробуйте позже после обновления данных."
                )
                return ConversationHandler.END

            topics = [topic[0] for topic in topics]  # Извлекаем только названия
            logging.info(f"Processed topics: {topics}")

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Отлично! Теперь выбери тему:",
                reply_markup=get_topics_keyboard(topics)
            )
            return 1
        finally:
            db.close()

    except ValueError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Пожалуйста, введите число (например, 800)"
        )
        return 0


async def handle_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    topic = query.data.replace('topic_', '')
    context.user_data['topic'] = topic

    # Добавляем лог для отладки
    logging.info(f"Selected topic: {topic}, user_data: {context.user_data}")

    try:
        await show_problems(update, context)
    except Exception as e:
        logging.error(f"Error in show_problems: {str(e)}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Произошла ошибка при поиске задач. Попробуйте позже."
        )

    return ConversationHandler.END  # Явно завершаем диалог


async def show_problems(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_data = context.user_data
    rating = user_data.get('rating')
    topic = user_data.get('topic')

    logging.info(f"Searching problems with rating={rating}, topic={topic}")

    try:
        db = SessionLocal()
        problems = get_problems_by_filter(db, rating=rating, topic=topic)

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

    except Exception as e:
        logging.error(f"Error in show_problems: {str(e)}")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Произошла ошибка при поиске задач. Попробуйте позже."
        )
    finally:
        db.close()  # Гарантированное закрытие соединения


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет текущий диалог и сбрасывает состояние"""
    await update.message.reply_text("Поиск отменён. Начните заново командой /start")
    # Очищаем user_data
    context.user_data.clear()
    return ConversationHandler.END  # Завершаем диалог
