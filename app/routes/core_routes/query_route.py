from fastapi import APIRouter

from app.agents.sql_agent import sql_agent
from app.schemas.core_schemas.query_schema import QueryRequest, QueryResponse

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Answer a natural language order-processing question.

    Runs the full pipeline: intent detection, missing-parameter prompting,
    SQL retrieval (cache -> template -> LLM), validation, safe execution, and
    business-friendly response formatting.

    Args:
        request: QueryRequest with thread_id and query.

    Returns:
        QueryResponse with the answer and (if applicable) the executed SQL.

    Exceptions handled by global handlers.
    """
    result = sql_agent.invoke(thread_id=request.thread_id, query=request.query)
    return {
        "thread_id": request.thread_id,
        "answer": result["answer"],
        "needs_clarification": result["needs_clarification"],
        "sql": result["sql"],
        "source": result["source"],
    }
