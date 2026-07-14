from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.keyboards import generate_keyboard
from bot.storage import SeenItemsStorage
from bot.wb_client import WBItem
from bot.yandex_gpt import YandexGPTClient


def build_router(gpt_client: YandexGPTClient, storage: SeenItemsStorage) -> Router:
    router = Router()

    @router.callback_query(F.data.startswith("gen:"))
    async def on_generate(callback: CallbackQuery) -> None:
        _, kind, item_id = callback.data.split(":", 2)
        await callback.answer("Генерирую черновик…")

        data = storage.get_item_data(kind, item_id)
        if data is None:
            await callback.message.reply(
                "Не нашёл сохранённые данные этого обращения "
                "(бот был перезапущен до того, как о нём пришло уведомление?)."
            )
            return
        item = WBItem(**data)

        try:
            draft = await gpt_client.generate_reply(item)
        except Exception as exc:  # noqa: BLE001
            await callback.message.reply(f"Не получилось сгенерировать ответ: {exc}")
            return

        await callback.message.reply(
            f"📝 Черновик ответа (скопируйте в личный кабинет WB):\n\n{draft}",
            reply_markup=generate_keyboard(kind, item_id, label="♻️ Сгенерировать заново"),
        )

    return router
