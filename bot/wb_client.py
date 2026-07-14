from dataclasses import dataclass
from typing import Optional

import httpx

FEEDBACKS_URL = "https://feedbacks-api.wildberries.ru/api/v1/feedbacks"
FEEDBACK_URL = "https://feedbacks-api.wildberries.ru/api/v1/feedback"
QUESTIONS_URL = "https://feedbacks-api.wildberries.ru/api/v1/questions"
QUESTION_URL = "https://feedbacks-api.wildberries.ru/api/v1/question"

REVIEW = "review"
QUESTION = "question"


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
        self._headers = {"Authorization": api_token}

    async def get_new_feedbacks(self, take: int = 100) -> list[WBItem]:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                FEEDBACKS_URL,
                headers=self._headers,
                params={"isAnswered": "false", "take": take, "skip": 0, "order": "dateDesc"},
            )
            resp.raise_for_status()
            payload = resp.json()

        feedbacks = (payload.get("data") or {}).get("feedbacks") or []
        return [self._feedback_to_item(fb) for fb in feedbacks]

    async def get_new_questions(self, take: int = 100) -> list[WBItem]:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                QUESTIONS_URL,
                headers=self._headers,
                params={"isAnswered": "false", "take": take, "skip": 0, "order": "dateDesc"},
            )
            resp.raise_for_status()
            payload = resp.json()

        questions = (payload.get("data") or {}).get("questions") or []
        return [self._question_to_item(q) for q in questions]

    async def get_item_by_id(self, kind: str, item_id: str) -> Optional[WBItem]:
        url = FEEDBACK_URL if kind == REVIEW else QUESTION_URL
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, headers=self._headers, params={"id": item_id})
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            payload = resp.json()

        raw = payload.get("data")
        if not raw:
            return None

        return self._feedback_to_item(raw) if kind == REVIEW else self._question_to_item(raw)

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
