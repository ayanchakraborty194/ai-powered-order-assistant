# AI-Powered Order Assistant — Architecture

## Overview
A conversational assistant that answers natural-language questions about
orders, customers, products, and shipments, without the user writing SQL.

## Stack (in scope only)
- **Database**: PostgreSQL (`customers`, `orders`, `order_items`, `products`, `shipments`)
- **LLM**: Gemini (`langchain-google-genai`, via `app/llms/llm_factory.py`)
- **Vector DB**: Qdrant (schema metadata RAG)
- **Cache**: Redis (SQL cache + multi-turn clarification state)
- **UI**: Streamlit (`streamlit_app/app.py`)
- **Backend**: FastAPI (`app/`)

There is no IAM/auth, no RabbitMQ/message queue, and no OpenAI integration in
this project — the assistant exposes a single public `/query` endpoint.

## Flow
```
User message → POST /ai_powered_order_assistant/api/v1/query
  → intent_agent            (extract tables/entities, detect missing info)
  → [if missing info] return clarifying question, remember pending query
  → nl_to_sql_service.resolve
        Layer 1: query_cache_repository   (Redis, exact/normalized match)
        Layer 2: sql_template_repository  (predefined validated templates)
        Layer 3: LLM generation           (Gemini + Qdrant schema RAG context)
  → sql_validation_service   (statement type, forbidden keywords, table
                               existence, EXPLAIN plan check)
  → query_execution_service  (30s timeout, row cap, thread-pool enforced)
  → nl_to_sql_service.remember (cache the successful SQL for reuse)
  → responder_agent          (format rows into a business-friendly answer)
  → QueryResponse { answer, sql, source, needs_clarification }
```

## Running locally
```bash
cp .env.example .env      # fill in GEMINI_API_KEY
docker compose up -d postgres qdrant redis
docker compose run --rm order-bootstrap   # creates schema, seeds data, ingests schema metadata
docker compose up -d app streamlit        # http://localhost:8501
```

## API
`POST /ai_powered_order_assistant/api/v1/query`
```json
{ "thread_id": "abc-123", "query": "Show pending shipments for customer ABC Ltd." }
```
Response:
```json
{
  "thread_id": "abc-123",
  "answer": "Customer ABC Ltd. has one shipped order (Order #10453)...",
  "needs_clarification": false,
  "sql": "SELECT ... FROM shipments ...",
  "source": "template"
}
```

## Success criteria mapping
| PoC requirement | Where it's implemented |
|---|---|
| Understand NL business questions | `app/agents/intent_agent.py` |
| Determine relevant tables | `intent_agent` → `tables` field |
| Ask for missing parameters | `intent_agent` → `missing_info`, `app/agents/sql_agent.py` clarification loop |
| Retrieve/generate accurate SQL | `app/services/core_services/nl_to_sql_service.py` |
| Execute safely within 30s | `app/services/core_services/query_execution_service.py` |
| Business-friendly responses | `app/agents/responder_agent.py` |
| Cache/repository reuse before LLM fallback | `nl_to_sql_service.resolve` layered strategy |

## Known limitations (PoC scope)
- Template parameter filling is name-based (`:customer_name`, `:order_id`, etc.); complex multi-entity questions may still fall through to LLM generation.
- Cache matching is exact-normalized text, not semantic/embedding similarity (a natural next step).
- No authentication is enforced on `/query` in this PoC.
