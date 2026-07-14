import asyncio
import logging
from dataclasses import asdict

from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter

from bot.keyboards import generate_keyboard
from bot.storage import SeenItemsStorage
from bot.wb_client import WBClient, WBItem

logger = logging.getLogger(__name__)

# Небольшая пауза между отправками, чтобы не словить flood control Telegram,
# если за один опрос нашлось сразу много новых отзывов/вопросов.
SEND_DELAY_SECONDS = 0.5


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
    items: list[WBItem] = []

    # Отзывы и вопросы запрашиваются независимо: если один источник упал
    # (например, WB вернул 429), это не должно срывать обработку другого.
    try:
        items.extend(await wb_client.get_new_feedbacks())
    except Exception:  # noqa: BLE001
        logger.exception("Не удалось получить отзывы из WB API")

    try:
        items.extend(await wb_client.get_new_questions())
    except Exception:  # noqa: BLE001
        logger.exception("Не удалось получить вопросы из WB API")

    for item in items:
        if not storage.is_new(item.kind, item.id):
            continue

        # Отмечаем как показанное ТОЛЬКО после успешной отправки — иначе при
        # сбое отправки (сеть, flood control Telegram) отзыв будет считаться
        # показанным, хотя пользователь его так и не увидел, и бот его больше
        # никогда не пришлёт.
        if await _notify(bot, chat_id, item):
            storage.mark_seen(item.kind, item.id, asdict(item))

        await asyncio.sleep(SEND_DELAY_SECONDS)


async def _notify(bot: Bot, chat_id: int, item: WBItem) -> bool:
    """Отправляет уведомление в Telegram. Возвращает True, если оно реально доставлено."""
    try:
        await bot.send_message(
            chat_id,
            format_notification(item),
            reply_markup=generate_keyboard(item.kind, item.id),
        )
        return True
    except TelegramRetryAfter as exc:
        logger.warning(
            "Telegram flood control при отправке %s %s, жду %s сек и повторяю",
            item.kind,
            item.id,
            exc.retry_after,
        )
        await asyncio.sleep(exc.retry_after)
        try:
            await bot.send_message(
                chat_id,
                format_notification(item),
                reply_markup=generate_keyboard(item.kind, item.id),
            )
            return True
        except Exception:  # noqa: BLE001
            logger.exception("Не удалось отправить уведомление после повтора: %s %s", item.kind, item.id)
            return False
    except Exception:  # noqa: BLE001
        logger.exception("Не удалось отправить уведомление: %s %s", item.kind, item.id)
        return False
