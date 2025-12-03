import os
import sqlite3
import json
from typing import Dict, Any, List

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'messages.db')

CREATE_TABLE_SQL = '''
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    role TEXT,
    content TEXT,
    timestamp TEXT
);
'''


def _get_conn():
    # Open a new connection per operation to keep it simple and safe across threads
    conn = sqlite3.connect(DB_FILE, timeout=30)
    return conn


def init_db() -> None:
    """Create the messages database and table if they don't exist."""
    os.makedirs(BASE_DIR, exist_ok=True)
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(CREATE_TABLE_SQL)
        conn.commit()
    finally:
        conn.close()


def insert_message(message: Dict[str, Any]) -> None:
    """
    Insert a message dict into the messages table. Raises no error on duplicate id (ignored).

    Expected message shape (partial):
      {
        'message_id': 'uuid',
        'user_id': '1',
        'role': 'assistant' | 'result',
        'content': { ... } or None,
        'timestamp': 'ISO timestamp'
      }
    """
    if message is None:
        raise ValueError("message is required")

    msg_id = message.get('message_id')
    if not msg_id:
        raise ValueError("message must contain 'message_id'")

    user_id = message.get('user_id')
    role = message.get('role')
    content = message.get('content')
    timestamp = message.get('timestamp')

    content_json = None
    if content is not None:
        try:
            content_json = json.dumps(content)
        except (TypeError, ValueError):
            # Fallback to string representation
            content_json = str(content)

    conn = _get_conn()
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO messages (id, user_id, role, content, timestamp) VALUES (?, ?, ?, ?, ?)",
                (msg_id, user_id, role, content_json, timestamp),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            # Duplicate primary key -> ignore (id uniqueness enforced)
            pass
    finally:
        conn.close()


def get_messages(limit: int = 100) -> List[Dict[str, Any]]:
    """Return messages ordered by rowid descending (most recent first)."""
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, user_id, role, content, timestamp FROM messages ORDER BY rowid DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        results: List[Dict[str, Any]] = []
        for row in rows:
            id_, user_id, role, content_json, timestamp = row
            content = None
            if content_json is not None:
                try:
                    content = json.loads(content_json)
                except json.JSONDecodeError:
                    content = content_json
            results.append({
                'message_id': id_,
                'user_id': user_id,
                'role': role,
                'content': content,
                'timestamp': timestamp,
            })
        return results
    finally:
        conn.close()
