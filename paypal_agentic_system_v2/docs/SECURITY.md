# Security

- Credentials are environment variables only.
- The Postman importer sanitizes credential-like values and the generated registry was checked for bearer/JWT/client-secret patterns.
- Mock mode is the default.
- LLM output is constrained to registered tool IDs.
- Path parameters are validated before execution.
- Financial/destructive operations can require explicit confirmation.
- Mutating calls receive a PayPal request ID/idempotency key.
- 401 refresh is limited to one token refresh per request.
- 429/5xx/network retries are bounded.
- Logs should not contain secrets; production deployments should add log redaction and a managed secret store.
