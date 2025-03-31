import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
)
from src.bot.main import main, init_parser


@pytest.fixture(autouse=True)
def mock_config():
    with patch('src.bot.main.config') as mock_config:
        mock_config.TELEGRAM_TOKEN = 'test_token'
        yield mock_config


@pytest.fixture
def mock_app():
    return MagicMock(spec=Application)


@pytest.fixture
def mock_handlers():
    with patch('src.bot.main.start') as mock_start, \
            patch('src.bot.main.handle_difficulty') as mock_diff, \
            patch('src.bot.main.handle_topic') as mock_topic, \
            patch('src.bot.main.show_problems') as mock_show:
        yield {
            'start': mock_start,
            'handle_difficulty': mock_diff,
            'handle_topic': mock_topic,
            'show_problems': mock_show
        }


@pytest.fixture(autouse=True)
def mock_db_init():
    async_init_parser = AsyncMock()
    with patch('src.bot.main.init_db') as mock_init_db, \
            patch('src.bot.main.init_parser', new=async_init_parser) as mock_init_parser, \
            patch('src.bot.main.asyncio.get_event_loop') as mock_loop:
        mock_loop.return_value.run_until_complete = MagicMock()
        yield {
            'init_db': mock_init_db,
            'init_parser': mock_init_parser,
            'loop': mock_loop
        }


def test_main_initialization(mock_app, mock_db_init):
    with patch('telegram.ext.Application.builder') as mock_builder:
        mock_builder.return_value.token.return_value.build.return_value = mock_app

        main()

        # Проверяем инициализацию базы данных
        mock_db_init['init_db'].assert_called_once()

        # Проверяем запуск парсера
        mock_db_init['loop'].return_value.run_until_complete.assert_called_once()

        # Проверяем инициализацию бота
        mock_builder.assert_called_once()
        mock_builder.return_value.token.assert_called_once_with('test_token')
        mock_builder.return_value.token.return_value.build.assert_called_once()

        # Проверяем запуск бота
        mock_app.run_polling.assert_called_once()


def test_handlers_registration(mock_app):
    with patch('telegram.ext.Application.builder') as mock_builder:
        mock_builder.return_value.token.return_value.build.return_value = mock_app

        main()

        # Проверяем что были попытки добавить обработчики
        assert mock_app.add_handler.call_count >= 2

        # Получаем все аргументы вызовов add_handler
        handler_calls = [args[0][0] for args in mock_app.add_handler.call_args_list]

        # Проверяем что есть ConversationHandler
        conv_handlers = [h for h in handler_calls if isinstance(h, ConversationHandler)]
        assert len(conv_handlers) == 1

        # Проверяем что есть CommandHandler для /show
        cmd_handlers = [h for h in handler_calls if isinstance(h, CommandHandler) and 'show' in h.commands]
        assert len(cmd_handlers) == 1

        # Проверяем что первым добавляется ConversationHandler
        first_handler = mock_app.add_handler.call_args_list[0][0][0]
        assert isinstance(first_handler, ConversationHandler)

        # Проверяем что вторым добавляется CommandHandler для /show
        second_handler = mock_app.add_handler.call_args_list[1][0][0]
        assert isinstance(second_handler, CommandHandler)
        assert 'show' in second_handler.commands


def test_conversation_handler_details(mock_app):
    with patch('telegram.ext.Application.builder') as mock_builder:
        mock_builder.return_value.token.return_value.build.return_value = mock_app
        mock_conv_handler = MagicMock(spec=ConversationHandler)

        with patch('telegram.ext.ConversationHandler', return_value=mock_conv_handler):
            main()

            # Проверяем что ConversationHandler был создан
            assert mock_app.add_handler.call_count >= 1
            assert any(isinstance(args[0][0], ConversationHandler)
                       for args in mock_app.add_handler.call_args_list)


@pytest.mark.asyncio
async def test_polling_start(mock_app):
    with patch('telegram.ext.Application.builder') as mock_builder:
        mock_app.run_polling = AsyncMock()
        mock_builder.return_value.token.return_value.build.return_value = mock_app

        main()  # Не используем await, так как main() не асинхронная

        await mock_app.run_polling.assert_awaited_once()


@pytest.mark.asyncio
async def test_init_parser_success():
    """Тест успешной инициализации парсера"""
    with patch('src.bot.main.parse_and_save_problems') as mock_parse:
        mock_parse.return_value = {"status": "success", "count": 10}

        await init_parser()

        mock_parse.assert_called_once()


@pytest.mark.asyncio
async def test_init_parser_error():
    """Тест обработки ошибки при инициализации парсера"""
    with patch('src.bot.main.parse_and_save_problems') as mock_parse:
        mock_parse.side_effect = Exception("Test error")

        # Проверяем, что функция не вызывает исключение
        await init_parser()

        mock_parse.assert_called_once()


@pytest.mark.asyncio
async def test_main_success():
    """Тест успешного запуска бота"""
    with patch('src.bot.main.init_db') as mock_init_db, \
            patch('src.bot.main.init_parser') as mock_init_parser, \
            patch('src.bot.main.Application') as mock_app, \
            patch('src.bot.main.config.TELEGRAM_TOKEN', 'test_token'):
        # Настраиваем мок для Application
        mock_application = MagicMock()
        mock_app.builder.return_value.token.return_value.build.return_value = mock_application

        # Запускаем main
        main()

        # Проверяем вызовы
        mock_init_db.assert_called_once()
        mock_init_parser.assert_called_once()
        mock_app.builder.assert_called_once()

        # Проверяем, что add_handler был вызван дважды
        assert mock_application.add_handler.call_count == 2

        # Проверяем, что первым добавлен ConversationHandler
        first_handler = mock_application.add_handler.call_args_list[0][0][0]
        assert isinstance(first_handler, ConversationHandler)
        assert len(first_handler.entry_points) == 1
        assert len(first_handler.states) == 2
        assert len(first_handler.fallbacks) == 2

        # Проверяем, что вторым добавлен CommandHandler для /show
        second_handler = mock_application.add_handler.call_args_list[1][0][0]
        assert isinstance(second_handler, CommandHandler)
        assert 'show' in second_handler.commands


def test_main_db_error():
    """Тест обработки ошибки при инициализации базы данных"""
    with patch('src.bot.main.init_db', side_effect=Exception("DB error")), \
            pytest.raises(Exception) as exc_info:
        main()

        assert str(exc_info.value) == "DB error"


def test_main_parser_error():
    """Тест обработки ошибки при инициализации парсера"""
    with patch('src.bot.main.init_db'), \
            patch('src.bot.main.init_parser', side_effect=Exception("Parser error")), \
            pytest.raises(Exception) as exc_info:
        main()
        assert str(exc_info.value) == "Parser error"
