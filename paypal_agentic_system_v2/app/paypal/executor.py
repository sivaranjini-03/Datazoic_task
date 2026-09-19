import copy, json, time, uuid, re, urllib.parse, asyncio
from typing import Any
import httpx
from app.config import settings
from app.exceptions import PayPalAPIError, MissingParameterError
from app.paypal.oauth import OAuthManager

class PayPalExecutor:
    def __init__(self, registry): self.registry=registry; self.oauth=OAuthManager()

    def _resolve(self, value, params, state):
        if isinstance(value, dict): return {k:self._resolve(v,params,state) for k,v in value.items()}
        if isinstance(value, list): return [self._resolve(v,params,state) for v in value]
        if not isinstance(value,str): return value
        def sub(m):
            key=m.group(1)
            if key.startswith('state.'):
                cur=state
                for p in key[6:].split('.'):
                    cur=cur.get(p) if isinstance(cur,dict) else None
                return '' if cur is None else str(cur)
            return str(params.get(key,''))
        return re.sub(r'\{\{\s*([^}]+)\s*\}\}',sub,value)

    def _build(self, tool, params, state):
        path=tool['path']
        for p in tool.get('path_parameters',[]):
            v=params.get(p) or state.get(p)
            if v is None: raise MissingParameterError(f'Missing required parameter: {p}')
            path=path.replace(':'+p,urllib.parse.quote(str(v),safe=''))
        if ':' in path: raise MissingParameterError('Unresolved path parameter')
        query={}
        for q in tool.get('query_parameters',[]):
            name=q.get('name');
            if name and name in params: query[name]=params[name]
        body=copy.deepcopy(tool.get('request_example'))
        if body is not None:
            body=self._resolve(body,params,state)
            # LLM may provide a complete body; prefer explicit body.
            if isinstance(params.get('body'),dict): body=self._resolve(params['body'],params,state)
        elif isinstance(params.get('body'),dict): body=params['body']
        headers={'Accept':'application/json'}
        if body is not None: headers['Content-Type']='application/json'
        for k,v in params.get('headers',{}).items(): headers[k]=str(v)
        return path,query,body,headers

    async def execute(self, tool_id, params, state, execution_id=None):
        tool=self.registry.get(tool_id)
        if not tool: raise ValueError(f'Unknown tool: {tool_id}')
        execution_id=execution_id or str(uuid.uuid4())
        if settings.paypal_mock_mode: return self._mock(tool,params,state,execution_id)
        path,query,body,headers=self._build(tool,params,state)
        token=await self.oauth.get_token()
        headers['Authorization']=f'Bearer {token}'
        if tool['method'] in ('POST','PUT','PATCH','DELETE'):
            headers.setdefault('PayPal-Request-Id',execution_id)
        started=time.perf_counter(); last=None
        for attempt in range(settings.max_retries+1):
            try:
                async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as c:
                    r=await c.request(tool['method'],settings.paypal_base_url+path,params=query,headers=headers,json=body)
                if r.status_code==401 and attempt==0:
                    token=await self.oauth.get_token(force_refresh=True); headers['Authorization']=f'Bearer {token}'; continue
                if r.status_code==429 or 500<=r.status_code<600:
                    if attempt<settings.max_retries:
                        await asyncio.sleep(0.5*(2**attempt)); continue
                try: payload=r.json()
                except Exception: payload={'raw':r.text}
                if r.status_code>=400:
                    raise PayPalAPIError(payload.get('message','PayPal request failed') if isinstance(payload,dict) else 'PayPal request failed',r.status_code,payload.get('debug_id') if isinstance(payload,dict) else None,r.status_code in (429,500,502,503,504),payload)
                return {'execution_id':execution_id,'tool_id':tool_id,'status_code':r.status_code,'success':True,'data':payload,'latency_ms':(time.perf_counter()-started)*1000}
            except (httpx.TimeoutException,httpx.NetworkError) as e:
                last=e
                if attempt<settings.max_retries: await asyncio.sleep(0.5*(2**attempt)); continue
                raise PayPalAPIError(str(e),None,retryable=True)
        raise PayPalAPIError(str(last or 'request failed'),None,retryable=True)

    def _mock(self,tool,params,state,eid):
        n=tool['name'].lower(); data={}
        if 'create order' in n: data={'id':'MOCK-ORDER-1001','status':'CREATED','purchase_units':[{'amount':{'currency_code':params.get('currency','USD'),'value':str(params.get('amount','100.00'))}}]}
        elif 'capture payment for order' in n: data={'id':state.get('order_id','MOCK-ORDER-1001'),'status':'COMPLETED','mock':True}
        elif 'create draft invoice' in n: data={'id':'MOCK-INVOICE-1001','status':'DRAFT','detail':{'currency':'USD','amount':str(params.get('amount','50.00')),'recipient_email':params.get('recipient_email','')}}
        elif 'send invoice' in n: data={'id':state.get('invoice_id','MOCK-INVOICE-1001'),'status':'SENT','mock':True}
        elif 'show order details' in n: data={'id':params.get('order_id','MOCK-ORDER-1001'),'status':'COMPLETED','mock':True}
        elif 'show invoice details' in n: data={'id':params.get('invoice_id','MOCK-INVOICE-1001'),'status':'SENT','mock':True}
        elif 'list' in n or 'search' in n: data={'items':[],'total_items':0,'mock':True}
        else: data={'id':params.get('id','MOCK-RESOURCE-1'),'status':'SUCCESS','tool':tool['name'],'mock':True}
        return {'execution_id':eid,'tool_id':tool['tool_id'],'status_code':200,'success':True,'data':data,'latency_ms':1.0}
