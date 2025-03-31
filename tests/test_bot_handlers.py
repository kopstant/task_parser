import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from telegram import Update, Message, CallbackQuery, User, Chat
from telegram.ext import CallbackContext, ConversationHandler
from src.bot.handlers import (
    start,
    handle_difficulty,
    handle_topic,
    show_problems,
    cancel
)
from src.database.models import Problem


@pytest.fixture
def mock_update():
    update = MagicMock(spec=Update)
    update.message = AsyncMock(spec=Message)
    update.message.from_user = MagicMock(spec=User)
    update.message.chat = MagicMock(spec=Chat)
    update.callback_query = AsyncMock(spec=CallbackQuery)
    update.effective_chat = MagicMock(spec=Chat)
    return update


@pytest.fixture
def mock_context():
    context = MagicMock(spec=CallbackContext)
    context.bot = AsyncMock()
    context.user_data = {}
    return context


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.execute = MagicMock()
    session.execute.return_value.fetchall.return_value = [("math",)]
    session.query = MagicMock()
    session.query.return_value.filter.return_value.all.return_value = []
    return session


@pytest.fixture
def mock_session_local(mock_session):
    with patch('src.bot.handlers.SessionLocal', return_value=mock_session) as mock:
        yield mock


@pytest.mark.asyncio
async def test_start(mock_update, mock_context):
    """Тест команды /start"""
    await start(mock_update, mock_context)
    mock_context.bot.send_message.assert_called_once_with(
        chat_id=mock_update.effective_chat.id,
        text="Привет! Я помогу тебе найти задачи на Codeforces.\n"
             "Введи сложность задачи (800-2000, с шагом в 200).\n"
             "/cancel для отмены:",
        reply_markup=mock_context.bot.send_message.call_args[1]['reply_markup']
    )


@pytest.mark.asyncio
async def test_handle_difficulty_success(mock_update, mock_context, mock_session_local):
    """Тест успешного ввода сложности"""
    mock_update.message.text = "800"

    result = await handle_difficulty(mock_update, mock_context)

    assert result == 1
    mock_context.bot.send_message.assert_called_once_with(
        chat_id=mock_update.effective_chat.id,
        text="Отлично! Теперь выбери тему:",
        reply_markup=mock_context.bot.send_message.call_args[1]['reply_markup']
    )


@pytest.mark.asyncio
async def test_handle_difficulty_invalid(mock_update, mock_context):
    """Тест некорректного ввода сложности"""
    mock_update.message.text = "invalid"

    result = await handle_difficulty(mock_update, mock_context)

    assert result == 0
    mock_context.bot.send_message.assert_called_once_with(
        chat_id=mock_update.effective_chat.id,
        text="Пожалуйста, введите число (например, 800)"
    )


@pytest.mark.asyncio
async def test_handle_topic_success(mock_update, mock_context):
    """Тест успешного выбора темы"""
    mock_update.callback_query.data = "topic_math"

    result = await handle_topic(mock_update, mock_context)

    assert result == ConversationHandler.END
    assert mock_context.user_data['topic'] == 'math'


@pytest.mark.asyncio
async def test_show_problems_success(mock_update, mock_context, mock_session_local):
    """Тест успешного отображения задач"""
    mock_context.user_data = {'rating': 800, 'topic': 'math'}
    problem = Problem(
        contest_id=1,
        index='A',
        name='Test Problem',
        rating=800
    )
    mock_session_local.return_value.query.return_value.filter.return_value.all.return_value = [problem]

    await show_problems(mock_update, mock_context)

    mock_context.bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_cancel(mock_update, mock_context):
    """Тест отмены поиска"""
    result = await cancel(mock_update, mock_context)

    assert result == ConversationHandler.END
    mock_update.message.reply_text.assert_called_once_with(
        "Поиск отменён. Начните заново командой /start"
    )
    assert len(mock_context.user_data) == 0
