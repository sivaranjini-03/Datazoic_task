from app.policy.engine import PolicyEngine

def test_financial_requires_confirmation():
    p=PolicyEngine(); assert p.check({'name':'Capture payment','risk':'financial','requires_confirmation':True})['requires_confirmation']
    assert p.check({'name':'Capture payment','risk':'financial','requires_confirmation':True},True)['allowed']
