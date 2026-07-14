import json
import sqlite3
from contextlib import closing
from typing import Optional


class SeenItemsStorage:
    """Хранит уже показанные отзывы/вопросы вместе с их данными.

    Данные сохраняются здесь же (не перезапрашиваются у WB повторно), чтобы
    кнопка «Сгенерировать ответ» могла работать по локальной копии — WB не
    предоставляет надёжного способа получить один конкретный отзыв/вопрос
    по ID отдельным запросом.
    """

    def __init__(self, db_path: str):
        self._db_path = db_path
        with closing(sqlite3.connect(self._db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS seen_items (
                    kind TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    data TEXT,
                    PRIMARY KEY (kind, item_id)
                )
                """
            )
            try:
                conn.execute("ALTER TABLE seen_items ADD COLUMN data TEXT")
            except sqlite3.OperationalError:
                pass  # колонка уже существует (база из более старой версии бота)
            conn.commit()

    def is_new(self, kind: str, item_id: str) -> bool:
        with closing(sqlite3.connect(self._db_path)) as conn:
            row = conn.execute(
                "SELECT 1 FROM seen_items WHERE kind = ? AND item_id = ?",
                (kind, item_id),
            ).fetchone()
        return row is None

    def mark_seen(self, kind: str, item_id: str, data: dict) -> None:
        with closing(sqlite3.connect(self._db_path)) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO seen_items (kind, item_id, data) VALUES (?, ?, ?)",
                (kind, item_id, json.dumps(data, ensure_ascii=False)),
            )
            conn.commit()

    def get_item_data(self, kind: str, item_id: str) -> Optional[dict]:
        with closing(sqlite3.connect(self._db_path)) as conn:
            row = conn.execute(
                "SELECT data FROM seen_items WHERE kind = ? AND item_id = ?",
                (kind, item_id),
            ).fetchone()
        if row is None or row[0] is None:
            return None
        return json.loads(row[0])
