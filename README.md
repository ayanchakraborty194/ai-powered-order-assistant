# AI-Powered Order Assistant

A conversational, AI-powered assistant that lets business users ask natural
language questions about order processing data — orders, customers,
products, and shipments — instead of writing SQL or searching multiple
tables by hand.

See [docs/architecture.md](docs/architecture.md) for the full flow, API
contract, and how each PoC requirement maps to the codebase.

## Stack
- FastAPI backend
- Gemini (LLM)
- PostgreSQL (order processing data)
- Qdrant (schema metadata RAG)
- Redis (SQL cache + multi-turn clarification memory)
- Streamlit (chat UI)

## Quick start
```bash
cp .env.example .env      # fill in GEMINI_API_KEY
docker compose up -d postgres qdrant redis
docker compose run --rm order-bootstrap   # creates schema, seeds sample data, ingests schema metadata
docker compose up -d app streamlit
```
Then open the UI at http://localhost:8501, or call the API directly:
```bash
curl -X POST http://localhost:8000/ai_powered_order_assistant/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"thread_id": "demo", "query": "List pending shipments."}'
```

## Project layout
```
app/
├── agents/            intent_agent, sql_agent (orchestrator), responder_agent
├── config/            env, logging, Postgres, Qdrant, Redis config
├── constants/         app-wide enums/constants
├── exceptions/        domain error types + FastAPI handlers
├── llms/               Gemini chat client + factory
├── models/            SQLAlchemy models for the order-processing schema
├── prompts/           intent/SQL-generation/response-formatting prompts
├── repository/
│   ├── sql_repository/     order_repository, sql_template_repository, query_cache_repository
│   └── vector_repository/  qdrant_repository
├── routes/core_routes/     /health, /query
├── schemas/core_schemas/   request/response models
├── services/core_services/ schema_metadata_service, nl_to_sql_service,
│                            sql_validation_service, query_execution_service
├── tests/             unit tests
├── utils/core_utils/  embeddings client, SQL cache key helpers, DB seed script
└── workers/           order_bootstrap_worker (schema + seed + RAG ingestion)

streamlit_app/         Streamlit chat UI (calls the FastAPI backend)
docs/                  architecture and API documentation
```

## Running tests
```bash
pip install -e ".[dev]"
pytest app/tests -v
```
