from typing import Any, Literal, Optional
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=10000)
    confirmed: bool = False

class ChatResponse(BaseModel):
    session_id: str
    answer: str
    status: str = 'completed'
    tool_used: Optional[str] = None
    execution_id: Optional[str] = None
    plan: list[dict[str, Any]] = []
    clarification: Optional[str] = None
    trace: list[dict[str, Any]] = []

class ToolCandidate(BaseModel):
    tool_id: str
    name: str
    score: float
    domain: str
    method: str
    path: str
    reason: str = ''

class PlanStep(BaseModel):
    tool_id: str
    parameters: dict[str, Any] = {}
    purpose: str = ''
    requires_confirmation: bool = False

class AgentPlan(BaseModel):
    intent: str
    domain: str = 'unknown'
    steps: list[PlanStep] = []
    clarification: Optional[str] = None
    trace: list[dict[str, Any]] = []
    final_answer: Optional[str] = None

class ExecutionResult(BaseModel):
    execution_id: str
    tool_id: str
    status_code: int
    success: bool
    data: Any = None
    error: Optional[dict[str, Any]] = None
    latency_ms: float = 0

class AgentState(BaseModel):
    session_id: str
    user_query: str
    intent: str = ''
    domain: str = 'unknown'
    candidates: list[ToolCandidate] = []
    plan: Optional[AgentPlan] = None
    execution_history: list[dict[str, Any]] = []
    intermediate_results: dict[str, Any] = {}
    pending_confirmation: bool = False
    final_answer: str = ''
