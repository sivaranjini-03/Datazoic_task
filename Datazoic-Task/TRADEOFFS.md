# Framework and Architecture Trade-offs

| Approach | Strength | Trade-off |
|---|---|---|
| LangGraph | Explicit stateful workflows and branching | Adds dependency/graph concepts |
| LangChain | Large integration ecosystem | Can add abstraction overhead |
| LlamaIndex | Strong document/RAG workflows | Less central to API execution orchestration |
| CrewAI | Easy role-based multi-agent patterns | More agent complexity than required for the MVP |
| DSPy | Programmatic prompt optimization | Better suited to optimization/evaluation than runtime workflow control |
| Custom orchestrator | Maximum control | More code and less built-in workflow tooling |

Recommended: LangGraph for orchestration, a custom Tool Registry/Retrieval interface for PayPal APIs, FastAPI for the service boundary, and a generic PayPal executor.

## MVP vs production

MVP uses SQLite, TF-IDF retrieval, local RAG and mock PayPal execution.

Production can use PostgreSQL/Redis, pgvector/OpenSearch/Qdrant, stronger reranking, durable workflows, OpenTelemetry/LangSmith, and a dedicated evaluation suite.
