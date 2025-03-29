import pytest
from unittest.mock import MagicMock, patch, call
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
)
from src.bot.main import main


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


def test_main_initialization(mock_app, mock_handlers):
    with patch('telegram.ext.Application.builder') as mock_builder:
        mock_builder.return_value.token.return_value.build.return_value = mock_app

        main()

        mock_builder.assert_called_once()
        mock_app.add_handler.assert_called()
        mock_app.run_polling.assert_called_once()


def test_handlers_registration(mock_app, mock_handlers):
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
        assert 'show' in second_handler.commands  # Изменённая проверка


def test_conversation_handler_details(mock_app, mock_handlers):
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
async def test_polling_start(mock_app, mock_handlers):
    with patch('telegram.ext.Application.builder') as mock_builder:
        mock_app.run_polling = MagicMock()
        mock_builder.return_value.token.return_value.build.return_value = mock_app

        main()  # Не используем await, так как main() не асинхронная

        mock_app.run_polling.assert_called_once()
