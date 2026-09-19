import json, re, httpx
from typing import Any
from app.config import settings
from app.models import AgentPlan, PlanStep

SYSTEM='''You are a PayPal API planning agent. Select ONLY from the supplied candidate tools. Never invent tool IDs or endpoints. Return JSON only with keys intent, domain, steps, clarification. Each step has tool_id, parameters, purpose, requires_confirmation. Parameters may contain path values directly and body/query/headers. For multi-step workflows, later steps may use state references like {{state.order_id}}. If required information is absent, set clarification and steps=[]. Prefer the minimal safe sequence. Financial/destructive tools require confirmation.'''

class LLMPlanner:
    def __init__(self, registry, retriever): self.registry=registry; self.retriever=retriever

    async def plan(self, query:str, candidates:list[dict], state:dict)->AgentPlan:
        if settings.openai_api_key:
            try: return await self._openai(query,candidates,state)
            except Exception:
                pass
        return self._fallback(query,candidates,state)

    async def _openai(self,query,candidates,state):
        tools=[]
        for c in candidates:
            t=self.registry.get(c['tool_id']); tools.append({k:t.get(k) for k in ['tool_id','name','method','path','domain','description','path_parameters','query_parameters','request_schema','request_example','risk','requires_confirmation']})
        prompt={'query':query,'candidates':tools,'state':state}
        body={'model':settings.openai_model,'temperature':settings.llm_temperature,'messages':[{'role':'system','content':SYSTEM},{'role':'user','content':json.dumps(prompt)}], 'response_format':{'type':'json_object'}}
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as c:
            r=await c.post(settings.openai_base_url.rstrip('/')+'/chat/completions',headers={'Authorization':f'Bearer {settings.openai_api_key}','Content-Type':'application/json'},json=body); r.raise_for_status(); data=r.json()
        content=data['choices'][0]['message']['content']; obj=json.loads(content); return AgentPlan.model_validate(obj)

    def _fallback(self,q,candidates,state):
        ql=q.lower(); ids={c['name'].lower():c['tool_id'] for c in candidates}
        def find(fragment):
            frag=fragment.lower()
            for c in candidates:
                if c['name'].lower()==frag: return c['tool_id']
            for t in self.registry.all():
                if t['name'].lower()==frag: return t['tool_id']
            for c in candidates:
                if frag in c['name'].lower(): return c['tool_id']
            for t in self.registry.all():
                if frag in t['name'].lower(): return t['tool_id']
            return None
        amount=self._amount(q); email=self._email(q); currency=self._currency(q)
        if 'invoice' in ql and ('send' in ql or 'email' in ql):
            create=find('create draft invoice'); send=find('send invoice')
            if not amount or not email: return AgentPlan(intent='create_and_send_invoice',domain='Invoices',clarification='Please provide the invoice amount and recipient email address.',steps=[])
            return AgentPlan(intent='create_and_send_invoice',domain='Invoices',steps=[PlanStep(tool_id=create,parameters={'amount':amount,'currency':currency,'recipient_email':email},purpose='Create draft invoice'),PlanStep(tool_id=send,parameters={'invoice_id':'{{state.invoice_id}}'},purpose='Send the created invoice')])
        if 'create' in ql and 'order' in ql and ('capture' in ql or 'pay' in ql):
            create=find('create order'); capture=find('capture payment for order')
            if not amount: return AgentPlan(intent='create_and_capture_order',domain='Orders',clarification='What amount should the order be for?',steps=[])
            return AgentPlan(intent='create_and_capture_order',domain='Orders',steps=[PlanStep(tool_id=create,parameters={'amount':amount,'currency':currency},purpose='Create order'),PlanStep(tool_id=capture,parameters={'order_id':'{{state.order_id}}'},purpose='Capture the order')])
        if 'order' in ql and any(x in ql for x in ['show','details','get']):
            oid=self._id(q,'order') or state.get('order_id')
            tool=find('show order details')
            if not oid: return AgentPlan(intent='get_order',domain='Orders',clarification='Please provide the order ID.',steps=[])
            return AgentPlan(intent='get_order',domain='Orders',steps=[PlanStep(tool_id=tool,parameters={'order_id':oid},purpose='Get order details')])
        if 'invoice' in ql and any(x in ql for x in ['show','details','get']):
            iid=self._id(q,'invoice') or state.get('invoice_id'); tool=find('show invoice details')
            if not iid: return AgentPlan(intent='get_invoice',domain='Invoices',clarification='Please provide the invoice ID.',steps=[])
            return AgentPlan(intent='get_invoice',domain='Invoices',steps=[PlanStep(tool_id=tool,parameters={'invoice_id':iid},purpose='Get invoice details')])
        if candidates:
            c=candidates[0]; return AgentPlan(intent='api_operation',domain=c['domain'],steps=[PlanStep(tool_id=c['tool_id'],parameters={},purpose='Best retrieved API candidate')])
        return AgentPlan(intent='unknown',clarification='I could not identify a suitable PayPal operation.',steps=[])

    def _amount(self,q):
        m=re.search(r'(?:\$|usd\s*)?(\d+(?:\.\d{1,2})?)',q,re.I); return m.group(1) if m else None
    def _email(self,q):
        m=re.search(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}',q); return m.group(0) if m else None
    def _currency(self,q): return 'USD' if '$' in q or 'usd' in q.lower() else 'USD'
    def _id(self,q,kind):
        m=re.search(rf'{kind}\s+(?:id\s*)?[:#]?\s*([A-Za-z0-9_-]+)',q,re.I)
        if not m: return None
        value=m.group(1)
        if value.lower() in {'details','detail','information','info'}: return None
        return value
