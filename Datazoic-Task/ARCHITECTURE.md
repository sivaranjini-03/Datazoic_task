# Architecture and Design Rationale

## 1. Architectural goal

The system turns a large PayPal Postman collection into a controlled tool catalogue that an agent can operate through natural language.

## 2. Main layers

### Gateway
FastAPI validates requests, identifies sessions and provides a stable API boundary.

### Orchestrator
LangGraph is the orchestration option. The agent maintains workflow state and can branch into PayPal, RAG or System Search capabilities.

### Tool Registry
The registry is generated from Postman rather than hand-coded. Each tool contains endpoint metadata, parameters, request examples, schemas and risk classification.

### Retrieval
Domain aliases narrow the search space. TF-IDF/keyword similarity and metadata signals are combined to produce a small candidate set. The interface is intentionally isolated so a production vector/BM25 backend can replace it without changing the agent.

### Planner
When an LLM key is configured, the planner receives only candidate tool metadata and state and returns structured JSON. In offline/mock mode, a deterministic planner covers the interview demo workflows.

### Validation and policy
Path parameters are checked before execution. Mutating/financial/destructive operations can require explicit confirmation.

### Executor
The generic executor translates tool metadata into HTTP requests. It owns OAuth, retries, 401 refresh, timeout handling, request IDs and response normalization. The LLM never directly handles credentials.

### State
SQLite persists session state and execution records. Resource IDs are promoted into state so later workflow steps can reference them.

### RAG and System Search
RAG answers knowledge questions from the knowledge base. System Search discovers tool capabilities and execution history. Neither is allowed to silently execute PayPal operations.

## 3. Scalability

```text
5,000+ registered APIs
        ↓
Domain / metadata filtering
        ↓
Hybrid retrieval
        ↓
Reranking
        ↓
5–10 candidate tools
        ↓
LLM
```

The key property is bounded LLM context rather than a growing prompt containing every API.

## 4. Why not many domain agents immediately?

A separate agent for every domain adds prompt, state and routing complexity. A single orchestrator plus retrieval is easier to test and sufficient for the first scaling stage. Domain-specific agents can be introduced later when a domain becomes complex enough to justify specialization.
