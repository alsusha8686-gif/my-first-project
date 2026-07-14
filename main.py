import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.config import load_settings
from bot.handlers import build_router
from bot.notifier import poll_loop
from bot.storage import SeenItemsStorage
from bot.wb_client import WBClient
from bot.yandex_gpt import YandexGPTClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


async def main() -> None:
    settings = load_settings()

    bot = Bot(settings.telegram_bot_token)
    dp = Dispatcher()

    wb_client = WBClient(settings.wb_api_token)
    gpt_client = YandexGPTClient(settings.yandex_api_key, settings.yandex_folder_id, settings.yandex_gpt_model)
    storage = SeenItemsStorage(settings.db_path)

    dp.include_router(build_router(wb_client, gpt_client))

    poll_task = asyncio.create_task(
        poll_loop(bot, settings.telegram_chat_id, wb_client, storage, settings.poll_interval_seconds)
    )

    try:
        await dp.start_polling(bot)
    finally:
        poll_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
