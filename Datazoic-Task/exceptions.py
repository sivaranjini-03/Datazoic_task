class AgentError(Exception): pass
class ValidationError(AgentError): pass
class MissingParameterError(AgentError): pass
class PolicyError(AgentError): pass
class PayPalAPIError(AgentError):
    def __init__(self, message, status_code=None, debug_id=None, retryable=False, payload=None):
        super().__init__(message); self.status_code=status_code; self.debug_id=debug_id; self.retryable=retryable; self.payload=payload
