### Prachi Gupta SJSUID- 019106594 ###
# src/storage.py
import aiosqlite
from typing import List, Tuple, Optional

# SQLite database file name
DB_PATH = "events.db"

# SQL schema -> create events table if not already present
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


# init database -> create table on startup
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_SQL)
        await db.commit()


# insert webhook event in DB (idempotent -> ignore duplicates)
async def insert_event(
    delivery_id: str,
    event: str,
    action: Optional[str],
    issue_number: Optional[int],
    payload: str,
):
    action_key = action or ""  # make sure NOT NULL is satisfied
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
        # don’t crash webhook handler if DB write fails
        print("EVENT_STORE_WRITE_ERROR:", repr(e))


# get recent events (for debugging/inspection)
async def list_recent_events(limit: int = 20) -> List[Tuple[str, str, str, Optional[int], str]]:
    """
    Return recent events like:
    [(id, event, action, issue_number, timestamp), ...]
    """
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
