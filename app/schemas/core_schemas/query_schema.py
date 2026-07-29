from typing import Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request body for the order-processing NL query endpoint."""

    thread_id: str = Field(..., description="Conversation thread id")
    query: str = Field(..., description="User's natural language question")


class QueryResponse(BaseModel):
    """Response body for the order-processing NL query endpoint."""

    thread_id: str = Field(..., description="Conversation thread id")
    answer: str = Field(..., description="Business-friendly assistant response")
    needs_clarification: bool = Field(
        default=False,
        description="True if the assistant is asking for missing information",
    )
    sql: Optional[str] = Field(
        default=None, description="The SQL statement executed (if any), for the optional SQL view"
    )
    source: Optional[str] = Field(
        default=None,
        description="Which layer answered the query: cache, template, or llm_generated",
    )
