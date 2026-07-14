import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    telegram_chat_id: int
    wb_api_token: str
    yandex_api_key: str
    yandex_folder_id: str
    yandex_gpt_model: str
    poll_interval_seconds: int
    db_path: str


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Переменная окружения {name} не задана. Проверьте файл .env")
    return value


def load_settings() -> Settings:
    return Settings(
        telegram_bot_token=_required("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=int(_required("TELEGRAM_CHAT_ID")),
        wb_api_token=_required("WB_API_TOKEN"),
        yandex_api_key=_required("YANDEX_API_KEY"),
        yandex_folder_id=_required("YANDEX_FOLDER_ID"),
        yandex_gpt_model=os.getenv("YANDEX_GPT_MODEL", "yandexgpt-lite/latest"),
        poll_interval_seconds=int(os.getenv("POLL_INTERVAL_SECONDS", "300")),
        db_path=os.getenv("DB_PATH", "wb_bot.db"),
    )
