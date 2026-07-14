import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

FEEDBACKS_URL = "https://feedbacks-api.wildberries.ru/api/v1/feedbacks"
QUESTIONS_URL = "https://feedbacks-api.wildberries.ru/api/v1/questions"

REVIEW = "review"
QUESTION = "question"

MAX_RETRIES_ON_429 = 3
INITIAL_BACKOFF_SECONDS = 2.0


@dataclass
class WBItem:
    id: str
    kind: str  # REVIEW или QUESTION
    text: str
    product_name: str
    rating: Optional[int]
    author_name: Optional[str]
    created_date: str


class WBClient:
    """Тонкая обёртка над Seller API Wildberries (раздел «Вопросы и отзывы»)."""

    def __init__(self, api_token: str):
        self._client = httpx.AsyncClient(headers={"Authorization": api_token}, timeout=30)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _get(self, url: str, params: dict) -> Optional[dict]:
        """GET-запрос к WB API с повторными попытками при HTTP 429 (лимит запросов)."""
        backoff = INITIAL_BACKOFF_SECONDS
        for attempt in range(1, MAX_RETRIES_ON_429 + 1):
            resp = await self._client.get(url, params=params)

            if resp.status_code == 429:
                retry_after = float(resp.headers.get("Retry-After", backoff))
                logger.warning(
                    "WB API: превышен лимит запросов (429) на %s, попытка %s/%s, жду %.1f сек",
                    url,
                    attempt,
                    MAX_RETRIES_ON_429,
                    retry_after,
                )
                await asyncio.sleep(retry_after)
                backoff *= 2
                continue

            if resp.status_code == 404:
                return None

            resp.raise_for_status()
            return resp.json()

        logger.error(
            "WB API: не удалось выполнить запрос к %s — лимит запросов (429) не снялся после %s попыток",
            url,
            MAX_RETRIES_ON_429,
        )
        return None

    async def get_new_feedbacks(self, take: int = 100) -> list[WBItem]:
        payload = await self._get(
            FEEDBACKS_URL,
            {"isAnswered": "false", "take": take, "skip": 0, "order": "dateDesc"},
        )
        if not payload:
            return []
        feedbacks = (payload.get("data") or {}).get("feedbacks") or []
        return [self._feedback_to_item(fb) for fb in feedbacks]

    async def get_new_questions(self, take: int = 100) -> list[WBItem]:
        payload = await self._get(
            QUESTIONS_URL,
            {"isAnswered": "false", "take": take, "skip": 0, "order": "dateDesc"},
        )
        if not payload:
            return []
        questions = (payload.get("data") or {}).get("questions") or []
        return [self._question_to_item(q) for q in questions]

    @staticmethod
    def _feedback_to_item(fb: dict) -> WBItem:
        return WBItem(
            id=fb["id"],
            kind=REVIEW,
            text=fb.get("text") or "(без текста, только оценка)",
            product_name=(fb.get("productDetails") or {}).get("productName", "—"),
            rating=fb.get("productValuation"),
            author_name=fb.get("userName"),
            created_date=fb.get("createdDate", ""),
        )

    @staticmethod
    def _question_to_item(q: dict) -> WBItem:
        return WBItem(
            id=q["id"],
            kind=QUESTION,
            text=q.get("text") or "",
            product_name=(q.get("productDetails") or {}).get("productName", "—"),
            rating=None,
            author_name=q.get("userName"),
            created_date=q.get("createdDate", ""),
        )
