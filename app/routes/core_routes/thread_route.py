from fastapi import APIRouter

from app.repository.sql_repository.chat_history_repository import (
    chat_history_repository,
)
from app.schemas.core_schemas.thread_schema import (
    ThreadListResponse,
    ThreadMessagesResponse,
)

router = APIRouter()


@router.get("/threads", response_model=ThreadListResponse)
async def list_threads():
    """List recent conversation threads, most-recently-updated first.

    Returns:
        ThreadListResponse with thread_id, title, created_at, updated_at.
    """
    threads = chat_history_repository.list_threads()
    return {"threads": threads}


@router.get("/threads/{thread_id}/messages", response_model=ThreadMessagesResponse)
async def get_thread_messages(thread_id: str):
    """Fetch the full message history for a thread.

    Args:
        thread_id: Conversation thread identifier.

    Returns:
        ThreadMessagesResponse with the ordered message list.
    """
    messages = chat_history_repository.get_messages(thread_id)
    return {"thread_id": thread_id, "messages": messages}