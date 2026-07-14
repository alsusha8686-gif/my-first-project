"""Разовая утилита: вывести в консоль последние 5 отзывов и 5 вопросов из WB.

Запуск (после того как заполнен .env и установлены зависимости):

    python fetch_last.py
"""

import asyncio

from bot.config import load_settings
from bot.wb_client import WBClient, WBItem


def print_item(item: WBItem) -> None:
    kind_label = "ОТЗЫВ" if item.kind == "review" else "ВОПРОС"
    rating = f", оценка {item.rating}/5" if item.rating else ""
    print(f"[{kind_label}] {item.created_date} — {item.product_name}{rating}")
    print(f"  ID: {item.id}")
    print(f"  Автор: {item.author_name or '—'}")
    print(f"  Текст: {item.text}")
    print("-" * 60)


async def main() -> None:
    settings = load_settings()
    client = WBClient(settings.wb_api_token)
    try:
        print("=== Последние 5 отзывов ===")
        feedbacks = await client.get_new_feedbacks(take=5)
        if not feedbacks:
            print("(неотвеченных отзывов нет)")
        for item in feedbacks[:5]:
            print_item(item)

        print("\n=== Последние 5 вопросов ===")
        questions = await client.get_new_questions(take=5)
        if not questions:
            print("(неотвеченных вопросов нет)")
        for item in questions[:5]:
            print_item(item)
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
