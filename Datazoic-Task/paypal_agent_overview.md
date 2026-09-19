# PayPal Agentic System Knowledge Base

The system exposes a large PayPal API collection through a searchable tool registry. The agent should not expose the entire API catalogue to the language model. It first identifies the likely domain, retrieves relevant candidate APIs, reranks them, and gives a bounded top-K set to the planner.

RAG is separate from API execution. Knowledge questions should retrieve documentation and answer from the retrieved context. System Search is separate again and is used to discover available APIs, tool metadata, or execution history.

For multi-step workflows, the agent stores intermediate resource identifiers such as order_id and invoice_id in persistent session state. A later tool can consume those identifiers.
