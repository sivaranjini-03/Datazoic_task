# PayPal Agentic AI System — Structured Implementation

A scalable agentic system for operating a large PayPal Postman API collection through natural language.

## What this version fixes

This version upgrades the earlier proof of concept with the missing implementation pieces:

- 116-endpoint sanitized Tool Registry generated from the supplied Postman collection
- Hierarchical/domain-aware hybrid retrieval with bounded Top-K context
- Real structured LLM planner when `OPENAI_API_KEY` is configured
- Deterministic fallback planner for offline demos
- Correct multi-step invoice workflow: Create Draft Invoice → Send Invoice
- Correct multi-step order workflow: Create Order → Capture Order
- Persistent SQLite session/execution state
- Parameter and path validation with clarification questions
- Financial/destructive confirmation gate
- Generic PayPal executor with OAuth 2.0, 401 refresh, bounded retries and rate-limit handling
- Idempotency/request IDs for mutating calls
- Separate RAG and System Search tools
- System Search can inspect execution history
- Structured JSON observability logs
- Optional LangGraph integration with a runnable fallback if the package is unavailable
- Mock mode for demos without PayPal credentials
- Automated tests
- Docker support

## Architecture

```text
USER
  ↓
FastAPI Gateway
  ↓
LangGraph Agent / Orchestrator
  ↓
Intent + Domain Router
  ├── PayPal Tool Pipeline
  ├── RAG Tool
  └── System Search Tool
          │
          ▼
     Tool Registry
          ↓
   Hybrid Retrieval
 (domain + TF-IDF + ranking)
          ↓
       Top 5–10
          ↓
      LLM Planner
          ↓
 Schema / Parameter Validation
          ↓
  Policy + Confirmation
          ↓
   Generic PayPal Executor
          ↓
      OAuth 2.0
          ↓
     PayPal APIs
          ↓
 Persistent State + Logs
```

The important scalability decision is that the LLM never receives the full API catalogue. The registry may contain hundreds or thousands of tools, while the planner receives only a small retrieved candidate set.

## Quick start — under 5 minutes

### Windows / VS Code

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

If PowerShell blocks activation, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first.

Keep `PAYPAL_MOCK_MODE=true` for the first run. **No PayPal credentials are required.**

Open:

- UI: `http://127.0.0.1:8000/ui/`
- API docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

### Three-minute demo

1. Open the UI.
2. Send: `Send an invoice for $50 to john@example.com`
3. Send: `Create an order for $100 and capture the payment` and click **Confirm** when prompted.
4. Send: `What APIs are available for invoices?`
5. Send: `How does PayPal invoicing work?`

The **Agent Trace** panel shows routing, bounded retrieval, planning, validation, policy and execution. The trace is intentionally safe: it shows tool IDs/status/latency, not OAuth secrets or access tokens.

### CLI smoke demo

```powershell
python scripts/demo.py
```

### Automated validation

```powershell
python scripts/validate_project.py
```

The validator checks the 116-tool registry and the automated test suite.

## Rebuild the registry

The original Postman collection is intentionally not packaged because it may contain credential-like values. Regenerate a sanitized registry from your local collection:

```powershell
python scripts/import_postman.py "PayPal APIs.postman_collection.json" data/tool_registry.json
```

The importer produced 116 tools from the supplied collection during this build.

## Testing

```powershell
python -m pytest -q
```

The current implementation includes tests for registry size, nested-domain retrieval, structured/fallback planning, missing parameters, mock execution, confirmation policy, persistent state, and end-to-end agent trace stages.

## Production path

For production, replace SQLite with PostgreSQL/Redis, use a dedicated vector index such as pgvector/Qdrant, add OpenTelemetry/LangSmith exporters, add a formal evaluation dataset for tool-selection accuracy, and use a durable workflow engine for long-running operations.
