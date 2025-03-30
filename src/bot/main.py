from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from src.config import config
from src.database.base import init_db, check_db_connection
from .handlers import start, handle_difficulty, handle_topic, show_problems, cancel
from src.parser.codeforces_api import parse_and_save_problems
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_parser():
    """Инициализация парсера при запуске"""
    try:
        logger.info("Starting initial parsing...")
        result = parse_and_save_problems()
        logger.info(f"Initial parsing completed: {result}")
    except Exception as e:
        logger.error(f"Error during initial parsing: {str(e)}")

def main():
    # Инициализируем базу данных, создаем таблицы
    init_db()
    
    # Запускаем первоначальный парсинг
    asyncio.get_event_loop().run_until_complete(init_parser())

    app = Application.builder().token(config.TELEGRAM_TOKEN).build()

    # Явно задаём фильтры для каждого состояния
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            # Состояние 0 - ожидаем текст (любой) для обработки как сложность
            0: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_difficulty)],

            # Состояние 1 - ожидаем callback с темой
            1: [CallbackQueryHandler(handle_topic, pattern='^topic_')]
        },
        fallbacks=[
            CommandHandler('cancel', cancel),  # Обработчик отмены
            CommandHandler('start', start)  # Альтернативный вариант начала заново
        ],
        allow_reentry=True
    )

    # Важно добавлять ConversationHandler ПЕРВЫМ
    app.add_handler(conv_handler)

    # Другие обработчики добавляем ПОСЛЕ ConversationHandler
    app.add_handler(CommandHandler("show", show_problems))

    app.run_polling()


if __name__ == '__main__':
    check_db_connection()
    main()
