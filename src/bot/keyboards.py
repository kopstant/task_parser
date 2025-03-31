from telegram import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from typing import List


def get_topics_keyboard(topics: List[str]) -> InlineKeyboardMarkup:
    """Создает inline-клавиатуру с темами (без кнопки отмены)"""
    keyboard = []
    for i in range(0, len(topics), 2):  # 2 кнопки в ряду
        row = [
            InlineKeyboardButton(topic, callback_data=f"topic_{topic}")
            for topic in topics[i:i + 2]
        ]
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)


def get_difficulty_keyboard() -> ReplyKeyboardMarkup:
    """Создает клавиатуру с популярными сложностями (без кнопки отмены)"""
    difficulties = ['800', '1000', '1200', '1400', '1600', '1800', '2000']
    keyboard = [
        [KeyboardButton(diff) for diff in difficulties[i:i + 3]]
        for i in range(0, len(difficulties), 3)
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        one_time_keyboard=True,
        resize_keyboard=True,
        input_field_placeholder="Выберите сложность"
    )
