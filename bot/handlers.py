from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.keyboards import generate_keyboard
from bot.wb_client import WBClient
from bot.yandex_gpt import YandexGPTClient


def build_router(wb_client: WBClient, gpt_client: YandexGPTClient) -> Router:
    router = Router()

    @router.callback_query(F.data.startswith("gen:"))
    async def on_generate(callback: CallbackQuery) -> None:
        _, kind, item_id = callback.data.split(":", 2)
        await callback.answer("Генерирую черновик…")

        try:
            item = await wb_client.get_item_by_id(kind, item_id)
        except Exception as exc:  # noqa: BLE001
            await callback.message.reply(f"Не удалось получить данные из WB: {exc}")
            return

        if item is None:
            await callback.message.reply(
                "Не удалось найти это обращение в WB (возможно, на него уже ответили)."
            )
            return

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
