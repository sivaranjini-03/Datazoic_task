import pytest
from app.config import settings
from app.retrieval.retriever import ToolRetriever
from app.agent.planner import LLMPlanner
from app.paypal.executor import PayPalExecutor
from app.state.store import StateStore
from app.policy.engine import PolicyEngine
from app.agent.orchestrator import AgentOrchestrator

@pytest.mark.asyncio
async def test_invoice_workflow(tmp_path, monkeypatch):
    monkeypatch.setattr(settings,'paypal_mock_mode',True)
    r=ToolRetriever('data/tool_registry.json'); a=AgentOrchestrator(r,LLMPlanner(r,r),PayPalExecutor(r),StateStore(str(tmp_path/'x.db')),PolicyEngine())
    out=await a.run('s1','Send an invoice for $50 to john@example.com')
    assert out['status']=='completed' and 'sent successfully' in out['answer']

@pytest.mark.asyncio
async def test_order_requires_confirmation(tmp_path, monkeypatch):
    monkeypatch.setattr(settings,'paypal_mock_mode',True)
    r=ToolRetriever('data/tool_registry.json'); a=AgentOrchestrator(r,LLMPlanner(r,r),PayPalExecutor(r),StateStore(str(tmp_path/'x.db')),PolicyEngine())
    out=await a.run('s2','Create an order for $100 and capture the payment')
    assert out['status']=='confirmation_required'
    out2=await a.run('s2','Create an order for $100 and capture the payment',True)
    assert out2['status']=='completed'

@pytest.mark.asyncio
async def test_trace_exposes_architecture_stages(tmp_path, monkeypatch):
    monkeypatch.setattr(settings,'paypal_mock_mode',True)
    r=ToolRetriever('data/tool_registry.json')
    a=AgentOrchestrator(r,LLMPlanner(r,r),PayPalExecutor(r),StateStore(str(tmp_path/'x.db')),PolicyEngine())
    out=await a.run('trace-1','Send an invoice for $25 to trace@example.com')
    stages=[x['stage'] for x in out['trace']]
    assert out['status']=='completed'
    assert 'routing' in stages and 'retrieval' in stages and 'planning' in stages
    assert 'validation' in stages and 'execution' in stages and 'completed' in stages
