import httpx

from bot.wb_client import WBItem

COMPLETION_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

SYSTEM_PROMPT = (
    "Ты — вежливый и профессиональный менеджер поддержки продавца на Wildberries. "
    "Пишешь черновик ответа на отзыв или вопрос покупателя. "
    "Отвечай по-русски, кратко (2-4 предложения), благодари за обращение, "
    "будь дружелюбным и конкретным. Если это негативный отзыв — извинись и предложи решение. "
    "Не выдумывай факты о товаре, которых нет в тексте обращения. "
    "Не используй markdown-разметку."
)


class YandexGPTClient:
    def __init__(self, api_key: str, folder_id: str, model: str):
        self._api_key = api_key
        self._model_uri = f"gpt://{folder_id}/{model}"

    async def generate_reply(self, item: WBItem) -> str:
        kind_label = "отзыв" if item.kind == "review" else "вопрос"
        rating_line = f"Оценка: {item.rating}/5\n" if item.rating else ""
        user_prompt = (
            f"Товар: {item.product_name}\n"
            f"{rating_line}"
            f"Тип обращения: {kind_label}\n"
            f"Текст покупателя: {item.text}\n\n"
            "Напиши черновик ответа продавца."
        )

        body = {
            "modelUri": self._model_uri,
            "completionOptions": {"stream": False, "temperature": 0.4, "maxTokens": 400},
            "messages": [
                {"role": "system", "text": SYSTEM_PROMPT},
                {"role": "user", "text": user_prompt},
            ],
        }
        headers = {"Authorization": f"Api-Key {self._api_key}"}

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(COMPLETION_URL, headers=headers, json=body)
            resp.raise_for_status()
            payload = resp.json()

        alternatives = payload["result"]["alternatives"]
        return alternatives[0]["message"]["text"].strip()
