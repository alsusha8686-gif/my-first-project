from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def generate_keyboard(kind: str, item_id: str, label: str = "🤖 Сгенерировать ответ") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=label, callback_data=f"gen:{kind}:{item_id}")]]
    )
