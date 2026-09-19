import pytest
from app.retrieval.retriever import ToolRetriever
from app.paypal.executor import PayPalExecutor
from app.config import settings

@pytest.mark.asyncio
async def test_mock_create_order(monkeypatch):
    monkeypatch.setattr(settings,'paypal_mock_mode',True)
    r=ToolRetriever('data/tool_registry.json'); ex=PayPalExecutor(r)
    tool=next(t for t in r.all() if t['name']=='Create order')
    result=await ex.execute(tool['tool_id'],{'amount':'100','currency':'USD'}, {}, 'x')
    assert result['success'] and result['data']['id']=='MOCK-ORDER-1001'
