import asyncio
import logging

from aiogram import Bot

from bot.keyboards import generate_keyboard
from bot.storage import SeenItemsStorage
from bot.wb_client import WBClient, WBItem

logger = logging.getLogger(__name__)


def format_notification(item: WBItem) -> str:
    kind_label = "⭐ Новый отзыв" if item.kind == "review" else "❓ Новый вопрос"
    rating_line = f"Оценка: {'⭐' * item.rating}\n" if item.rating else ""
    author = item.author_name or "Покупатель"
    text = item.text or "(без текста)"
    return (
        f"{kind_label}\n"
        f"Товар: {item.product_name}\n"
        f"{rating_line}"
        f"От: {author}\n\n"
        f"{text}"
    )


async def poll_loop(
    bot: Bot,
    chat_id: int,
    wb_client: WBClient,
    storage: SeenItemsStorage,
    interval_seconds: int,
) -> None:
    while True:
        try:
            await _check_once(bot, chat_id, wb_client, storage)
        except Exception:  # noqa: BLE001
            logger.exception("Ошибка при опросе WB API")
        await asyncio.sleep(interval_seconds)


async def _check_once(
    bot: Bot,
    chat_id: int,
    wb_client: WBClient,
    storage: SeenItemsStorage,
) -> None:
    items = [*(await wb_client.get_new_feedbacks()), *(await wb_client.get_new_questions())]
    for item in items:
        if not storage.is_new(item.kind, item.id):
            continue
        storage.mark_seen(item.kind, item.id)
        await bot.send_message(
            chat_id,
            format_notification(item),
            reply_markup=generate_keyboard(item.kind, item.id),
        )
