"""Redis-backed chat history: per-thread messages + a recency-ordered thread index.

Powers a Claude-like "Recents" sidebar: listing all threads and, on click,
loading that thread's full message history.
"""

import json
import time
from typing import Any, Dict, List, Optional

from app.config.log_config import logger
from app.config.redis_config import redis_config

_THREAD_MESSAGES_KEY = "chat_messages:{thread_id}"
_THREAD_META_KEY = "chat_thread_meta:{thread_id}"
_THREAD_INDEX_KEY = "chat_threads_index"  # sorted set: score=updated_at, member=thread_id

_TITLE_MAX_LEN = 60


class ChatHistoryRepository:
    """Persists chat messages and thread metadata for the "Recents" sidebar."""

    def __init__(self) -> None:
        """Initialize with the shared Redis client."""
        self.redis_client = redis_config.get_redis_client()

    def add_message(
        self,
        thread_id: str,
        role: str,
        content: str,
        sql: Optional[str] = None,
        source: Optional[str] = None,
    ) -> None:
        """Append a message to a thread's history and bump its recency.

        Args:
            thread_id: Conversation thread identifier.
            role: "user" or "assistant".
            content: Message text.
            sql: Optional SQL statement associated with an assistant message.
            source: Optional resolution source ("cache", "template", "llm_generated").
        """
        message = {
            "role": role,
            "content": content,
            "sql": sql,
            "source": source,
            "timestamp": time.time(),
        }
        try:
            self.redis_client.rpush(
                _THREAD_MESSAGES_KEY.format(thread_id=thread_id), json.dumps(message)
            )
            self._touch_thread(thread_id, first_user_message=content if role == "user" else None)
        except Exception as exc:
            logger.warning("Failed to persist chat message (non-fatal): %s", exc)

    def get_messages(self, thread_id: str) -> List[Dict[str, Any]]:
        """Fetch the full message history for a thread, oldest first.

        Args:
            thread_id: Conversation thread identifier.

        Returns:
            List of message dicts (role, content, sql, source, timestamp).
        """
        try:
            raw_messages = self.redis_client.lrange(
                _THREAD_MESSAGES_KEY.format(thread_id=thread_id), 0, -1
            )
            return [json.loads(m) for m in raw_messages]
        except Exception as exc:
            logger.warning("Failed to load chat history for thread %s: %s", thread_id, exc)
            return []

    def list_threads(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List threads ordered by most-recently-updated first.

        Args:
            limit: Max number of threads to return.

        Returns:
            List of {"thread_id", "title", "updated_at"} dicts.
        """
        try:
            thread_ids = self.redis_client.zrevrange(_THREAD_INDEX_KEY, 0, limit - 1)
        except Exception as exc:
            logger.warning("Failed to list chat threads: %s", exc)
            return []

        threads = []
        for thread_id in thread_ids:
            thread_id = thread_id if isinstance(thread_id, str) else thread_id.decode("utf-8")
            meta = self._get_thread_meta(thread_id)
            if meta:
                threads.append({"thread_id": thread_id, **meta})
        return threads

    def _touch_thread(self, thread_id: str, first_user_message: Optional[str]) -> None:
        """Update a thread's recency score and set its title on first message.

        Args:
            thread_id: Conversation thread identifier.
            first_user_message: The user's message text, if this call is for
                a user-role message (used to derive the thread title).
        """
        now = time.time()
        self.redis_client.zadd(_THREAD_INDEX_KEY, {thread_id: now})

        meta_key = _THREAD_META_KEY.format(thread_id=thread_id)
        existing = self.redis_client.get(meta_key)

        if existing is None and first_user_message:
            title = first_user_message.strip().replace("\n", " ")
            if len(title) > _TITLE_MAX_LEN:
                title = title[:_TITLE_MAX_LEN].rstrip() + "..."
            meta = {"title": title, "created_at": now, "updated_at": now}
        elif existing is not None:
            meta = json.loads(existing)
            meta["updated_at"] = now
        else:
            # Assistant message arriving before any user message is stored
            # (shouldn't normally happen) — use a placeholder title.
            meta = {"title": "New conversation", "created_at": now, "updated_at": now}

        self.redis_client.set(meta_key, json.dumps(meta))

    def _get_thread_meta(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a thread's stored metadata (title, created_at, updated_at).

        Args:
            thread_id: Conversation thread identifier.

        Returns:
            Metadata dict, or None if not found.
        """
        try:
            raw = self.redis_client.get(_THREAD_META_KEY.format(thread_id=thread_id))
            return json.loads(raw) if raw else None
        except Exception as exc:
            logger.warning("Failed to load thread meta for %s: %s", thread_id, exc)
            return None


chat_history_repository = ChatHistoryRepository()