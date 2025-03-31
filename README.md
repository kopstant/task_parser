# Codeforces Task Parser

Сервис для автоматического парсинга задач с платформы Codeforces с Telegram ботом для удобного поиска задач. Проект использует Celery для периодического сбора данных и SQLAlchemy для работы с базой данных.

## Основные возможности

- Автоматический сбор задач с Codeforces
- Периодическое обновление базы данных (каждый час)
- Telegram бот для поиска задач:
  - Поиск по сложности
  - Поиск по темам
  - Получение случайной задачи
  - Просмотр статистики решений
- Хранение информации о задачах, включая:
  - ID контеста
  - Индекс задачи
  - Название
  - Сложность (рейтинг)
  - Количество решивших
  - Темы (теги)
- Поиск и фильтрация задач по различным параметрам

## Технологический стек

- Python 3.8+
- python-telegram-bot для создания Telegram бота
- Celery для асинхронных задач
- Redis как брокер сообщений
- PostgreSQL для хранения данных
- SQLAlchemy как ORM
- Poetry для управления зависимостями

## Требования

- Python 3.8 или выше
- Redis
- PostgreSQL
- Poetry
- Telegram Bot Token (получить у @BotFather)

## Установка

1. Клонируйте репозиторий:
```bash
git clone <repository-url>
cd task_parser
```

2. Установите зависимости с помощью Poetry:
```bash
poetry install
```

3. Создайте файл `.env` в корневой директории проекта:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/codeforces_parser

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

## Запуск

1. Запустите Redis:
```bash
docker run -d -p 6379:6379 redis
```

2. Запустите PostgreSQL (если не установлен локально):
```bash
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=password -e POSTGRES_USER=user -e POSTGRES_DB=codeforces_parser postgres
```

3. Инициализируйте базу данных:
```bash
poetry run python -m src.database.init_db
```

4. Запустите Celery worker:
```bash
poetry run celery -A src.celery.celery_app worker --loglevel=info -Q parsing
```

5. Запустите Celery beat для периодических задач:
```bash
poetry run celery -A src.celery.celery_app beat --loglevel=info
```

6. Запустите Telegram бота:
```bash
poetry run python -m src.bot.main
```

## Использование бота

1. Найдите бота в Telegram по его имени
2. Отправьте команду `/start` для начала работы
3. Доступные команды:
   - `/help` - показать справку
   - `/search` - поиск задач по параметрам
   - `/random` - получить случайную задачу
   - `/topic` - поиск задач по теме
   - `/rating` - поиск задач по сложности
   - `/stats` - показать статистику решений

## Тестирование

Для запуска тестов используйте команду:
```bash
poetry run pytest
```

Для запуска тестов с отчетом о покрытии:
```bash
poetry run pytest --cov=src
```

## Структура проекта

```
task_parser/
├── src/
│   ├── bot/
│   │   ├── main.py        # Точка входа для Telegram бота
│   │   ├── handlers.py    # Обработчики команд бота
│   │   └── keyboards.py   # Клавиатуры и кнопки
│   ├── celery/
│   │   ├── celery_app.py  # Конфигурация Celery
│   │   └── tasks.py       # Определение задач Celery
│   ├── database/
│   │   ├── base.py        # Базовые классы SQLAlchemy
│   │   ├── models.py      # Модели данных
│   │   ├── crud.py        # CRUD операции
│   │   └── init_db.py     # Инициализация БД
│   ├── parser/
│   │   └── codeforces_api.py  # Работа с API Codeforces
│   └── config.py          # Конфигурация приложения
├── tests/                 # Тесты
├── poetry.lock           # Зафиксированные версии зависимостей
├── pyproject.toml        # Конфигурация Poetry и зависимости
└── README.md            # Документация проекта
```

## Конфигурация

Основные настройки проекта находятся в файле `src/config.py`. Для изменения параметров используйте переменные окружения или файл `.env`.

## Логирование

Логи Celery worker и beat доступны в консоли при запуске с флагом `--loglevel=info`. 
Для изменения уровня логирования используйте один из следующих уровней:
- debug
- info
- warning
- error
- critical

## Мониторинг

Для мониторинга задач Celery можно использовать Flower:
```bash
poetry run celery -A src.celery.celery_app flower
```

После запуска интерфейс мониторинга будет доступен по адресу: http://localhost:5555