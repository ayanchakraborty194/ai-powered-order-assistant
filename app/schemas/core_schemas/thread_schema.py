from typing import List, Optional

from pydantic import BaseModel, Field


class ThreadSummary(BaseModel):
    """Summary of a conversation thread, shown in the "Recents" sidebar."""

    thread_id: str
    title: str
    created_at: float
    updated_at: float


class ThreadListResponse(BaseModel):
    """Response for listing recent threads."""

    threads: List[ThreadSummary]


class ChatMessage(BaseModel):
    """A single message within a thread's history."""

    role: str = Field(..., description="'user' or 'assistant'")
    content: str
    sql: Optional[str] = None
    source: Optional[str] = None
    timestamp: float


class ThreadMessagesResponse(BaseModel):
    """Response for fetching a thread's full message history."""

    thread_id: str
    messages: List[ChatMessage]