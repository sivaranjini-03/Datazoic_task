import pytest
from app.retrieval.retriever import ToolRetriever
from app.agent.planner import LLMPlanner

@pytest.mark.asyncio
async def test_invoice_plan_is_multistep():
    r=ToolRetriever('data/tool_registry.json'); p=LLMPlanner(r,r); plan=await p.plan('Send an invoice for $50 to john@example.com',r.search('send invoice',8,'Invoices'),{})
    assert len(plan.steps)==2
    assert 'create draft invoice' in r.get(plan.steps[0].tool_id)['name'].lower()
    assert 'send invoice' in r.get(plan.steps[1].tool_id)['name'].lower()

@pytest.mark.asyncio
async def test_missing_order_id_clarifies():
    r=ToolRetriever('data/tool_registry.json'); p=LLMPlanner(r,r); plan=await p.plan('Show me order details',r.search('order details',8,'Orders'),{})
    assert plan.clarification
