from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from src.config import config
from src.database.base import init_db
from .handlers import start, handle_difficulty, handle_topic, show_problems, cancel
from celery_config.tasks import parse_codeforces_problems


def main():
    # Инициализируем базу данных, создаем таблицы
    init_db()
    parse_codeforces_problems()  # Инициализация периодических задач

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
    main()
