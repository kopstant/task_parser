from telegram import InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from src.bot.keyboards import get_topics_keyboard, get_difficulty_keyboard


class TestKeyboards:
    def test_topics_keyboard_creation(self):
        """Тест создания inline-клавиатуры с темами"""
        topics = ["math", "graphs", "dp", "greedy"]
        keyboard = get_topics_keyboard(topics)

        assert isinstance(keyboard, InlineKeyboardMarkup)
        assert len(keyboard.inline_keyboard) == 2  # 2 ряда
        assert len(keyboard.inline_keyboard[0]) == 2  # 2 кнопки в первом ряду

    def test_topics_keyboard_odd_number(self):
        """Тест с нечетным количеством тем"""
        keyboard = get_topics_keyboard(["math", "graphs", "dp"])
        assert len(keyboard.inline_keyboard) == 2  # 2 ряда (последний с 1 кнопкой)

    def test_difficulty_keyboard_creation(self):
        """Тест создания клавиатуры сложностей"""
        keyboard = get_difficulty_keyboard()

        assert isinstance(keyboard, ReplyKeyboardMarkup)
        assert keyboard.one_time_keyboard is True
        assert len(keyboard.keyboard) == 3  # 3 ряда

        # Проверяем тип кнопок
        assert isinstance(keyboard.keyboard[0][0], KeyboardButton)
        assert keyboard.keyboard[0][0].text == '800'
