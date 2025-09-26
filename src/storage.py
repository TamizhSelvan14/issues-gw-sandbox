# src/storage.py
import aiosqlite
from typing import List, Tuple, Optional

DB_PATH = "events.db"

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS events (
  delivery_id TEXT NOT NULL,
  event TEXT NOT NULL,
  action TEXT NOT NULL,
  issue_number INTEGER,
  payload TEXT,
  received_at TEXT DEFAULT (datetime('now')),
  PRIMARY KEY (delivery_id, action)
);
"""

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_SQL)
        await db.commit()

async def insert_event(
    delivery_id: str,
    event: str,
    action: Optional[str],
    issue_number: Optional[int],
    payload: str,
):
    """Insert a webhook event; ignore duplicates (idempotent)."""
    action_key = action or ""  # NOT NULL column
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(
                """
                INSERT OR IGNORE INTO events
                (delivery_id, event, action, issue_number, payload)
                VALUES (?, ?, ?, ?, ?)
                """,
                (str(delivery_id), str(event), str(action_key), issue_number, payload),
            )
            await db.commit()
    except Exception as e:
        # Never crash the webhook handler because of storage errors.
        print("EVENT_STORE_WRITE_ERROR:", repr(e))

async def list_recent_events(limit: int = 20) -> List[Tuple[str, str, str, Optional[int], str]]:
    """Return recent events for debugging: [(id, event, action, issue_number, timestamp), ...]"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """
            SELECT delivery_id, event, action, issue_number, received_at
            FROM events
            ORDER BY received_at DESC
            LIMIT ?
            """,
            (limit,),
        ) as cur:
            return await cur.fetchall()
