# Runtime Flows

## Single-step

```text
User
 ↓
FastAPI
 ↓
Agent
 ↓
Domain Router
 ↓
Tool Registry / Retrieval
 ↓
Top-K candidates
 ↓
Planner
 ↓
Validation
 ↓
Policy
 ↓
Executor
 ↓
PayPal
 ↓
State + Response
```

## Invoice

```text
User: Send an invoice for $50 to john@example.com
 ↓
Invoice domain
 ↓
Create Draft Invoice
 ↓
invoice_id
 ↓
Send Invoice
 ↓
Response
```

## Order + capture

```text
User: Create an order for $100 and capture payment
 ↓
Create Order
 ↓
order_id stored
 ↓
Confirmation gate
 ↓
Capture Order
 ↓
Response
```

## RAG

```text
User question
 ↓
RAG Tool
 ↓
Knowledge chunks
 ↓
Answer + sources
```

## System Search

```text
System question
 ↓
Tool Registry / execution records
 ↓
Structured result
```
