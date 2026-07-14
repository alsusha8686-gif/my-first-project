import sqlite3
from contextlib import closing


class SeenItemsStorage:
    """Хранит ID уже показанных отзывов/вопросов, чтобы не слать дубликаты."""

    def __init__(self, db_path: str):
        self._db_path = db_path
        with closing(sqlite3.connect(self._db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS seen_items (
                    kind TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    PRIMARY KEY (kind, item_id)
                )
                """
            )
            conn.commit()

    def is_new(self, kind: str, item_id: str) -> bool:
        with closing(sqlite3.connect(self._db_path)) as conn:
            row = conn.execute(
                "SELECT 1 FROM seen_items WHERE kind = ? AND item_id = ?",
                (kind, item_id),
            ).fetchone()
        return row is None

    def mark_seen(self, kind: str, item_id: str) -> None:
        with closing(sqlite3.connect(self._db_path)) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO seen_items (kind, item_id) VALUES (?, ?)",
                (kind, item_id),
            )
            conn.commit()
