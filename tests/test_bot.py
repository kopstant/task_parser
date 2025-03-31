import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from telegram import Update, Message, CallbackQuery, User
from telegram.ext import CallbackContext
from src.bot.handlers import start, handle_difficulty, handle_topic, show_problems
from tests.test_data import SAMPLE_DB_PROBLEMS


class TestBotHandlers(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.bot = AsyncMock()
        self.update = MagicMock(spec=Update)
        self.context = MagicMock(spec=CallbackContext)
        self.context.bot = self.bot

    async def test_start(self):
        self.update.message = MagicMock(spec=Message)
        self.update.message.chat_id = 1

        result = await start(self.update, self.context)
        self.assertEqual(result, 0)
        self.context.bot.send_message.assert_awaited_once()

    async def test_handle_difficulty_valid(self):
        self.update.message = MagicMock(spec=Message)
        self.update.message.text = '800'
        self.update.message.chat_id = 1

        with patch('src.bot.handlers.SessionLocal') as mock_session:
            mock_db = MagicMock()
            mock_db.execute.return_value.fetchall.return_value = [
                ('math',),
                ('dp',)
            ]
            mock_session.return_value = mock_db

            result = await handle_difficulty(self.update, self.context)
            self.assertEqual(result, 1)
            self.context.bot.send_message.assert_awaited_once()

    async def test_handle_difficulty_invalid(self):
        self.update.message = MagicMock(spec=Message)
        self.update.message.text = 'invalid'
        self.update.message.chat_id = 1

        result = await handle_difficulty(self.update, self.context)
        self.assertEqual(result, 0)
        self.context.bot.send_message.assert_awaited_once()

    async def test_handle_topic(self):
        self.update.callback_query = MagicMock(spec=CallbackQuery)
        self.update.callback_query.data = 'topic_math'
        self.update.callback_query.from_user = User(id=1, first_name='Test', is_bot=False)
        self.update.callback_query.bot = self.bot

        with patch('src.bot.handlers.show_problems', new_callable=AsyncMock):
            result = await handle_topic(self.update, self.context)
            self.assertEqual(result, -1)
            self.update.callback_query.answer.assert_awaited_once()

    async def test_show_problems(self):
        self.update.effective_chat = MagicMock()
        self.update.effective_chat.id = 1

        with (patch('src.bot.handlers.SessionLocal') as mock_session):
            mock_db = MagicMock()
            mock_db.query.return_value \
                .join.return_value \
                .filter.return_value \
                .order_by.return_value \
                .limit.return_value \
                .all.return_value = SAMPLE_DB_PROBLEMS
            mock_session.return_value = mock_db

            await show_problems(self.update, self.context)
            self.context.bot.send_message.assert_awaited_once()
