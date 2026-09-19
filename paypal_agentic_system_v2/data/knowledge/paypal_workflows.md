# Common PayPal Workflow Patterns

Creating and sending an invoice is a multi-step workflow: create a draft invoice first, obtain its invoice_id, then send the invoice using the invoice_id.

Creating and capturing an order is also multi-step: create the order, obtain the order_id, then capture payment for that order. Capture and refund operations are sensitive financial actions and should require explicit user confirmation before execution.

Missing required identifiers should result in a clarification question rather than guessing. API errors should be classified so that validation errors are corrected, authentication failures refresh credentials once, rate limits use bounded backoff, and business errors are not blindly retried.
