# Evaluation Plan

The production evaluation set should contain natural-language requests mapped to expected tool IDs and workflows.

Metrics:

- Top-1 tool selection accuracy
- Top-5 recall
- Domain classification accuracy
- Required-parameter clarification accuracy
- Multi-step plan exact match
- Unsafe-action block rate
- API execution success rate
- Median and p95 latency
- Retry rate

Recommended test groups:

1. Orders
2. Invoices
3. Payments
4. Disputes
5. Subscriptions
6. Payouts
7. Ambiguous queries
8. Missing-parameter queries
9. Sensitive financial actions
10. Out-of-scope questions
