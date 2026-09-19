import json, re
from pathlib import Path
from typing import Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DOMAIN_ALIASES={
 'invoice':'Invoices','invoices':'Invoices','bill':'Invoices','billing':'Invoices',
 'order':'Orders','orders':'Orders','checkout':'Orders',
 'payment':'Payments','payments':'Payments','charge':'Payments','refund':'Payments',
 'subscription':'Subscriptions','subscriptions':'Subscriptions','recurring':'Subscriptions',
 'dispute':'Disputes','disputes':'Disputes','claim':'Disputes',
 'payout':'Payouts','payouts':'Payouts', 'webhook':'Webhooks','webhooks':'Webhooks',
 'tracking':'Shipment Tracking','shipment':'Shipment Tracking', 'transaction':'Transaction Search','transactions':'Transaction Search',
 'currency':'Currency Exchange','exchange':'Currency Exchange', 'token':'Payment Method Tokens',
 'product':'Subscriptions','products':'Subscriptions', 'plan':'Subscriptions'
}

class ToolRetriever:
    def __init__(self, registry_path: str):
        d=json.loads(Path(registry_path).read_text(encoding='utf-8')); self.tools=d['tools']
        self.texts=[t['search_text'] for t in self.tools]
        self.vectorizer=TfidfVectorizer(ngram_range=(1,2), sublinear_tf=True, stop_words='english')
        self.matrix=self.vectorizer.fit_transform(self.texts)

    def infer_domain(self, query:str)->str:
        q=query.lower()
        scores={}
        for word,domain in DOMAIN_ALIASES.items():
            if re.search(r'\b'+re.escape(word)+r'\b',q): scores[domain]=scores.get(domain,0)+1
        return max(scores,key=scores.get) if scores else 'unknown'

    def _domain_match(self, tool, domain):
        if domain=='unknown': return 0.0
        td=tool.get('domain','')
        group=tool.get('group','')
        if td==domain or group.startswith(domain+'/'): return 1.0
        return 0.0

    def search(self, query:str, k:int=8, domain: str|None=None)->list[dict[str,Any]]:
        domain=domain or self.infer_domain(query)
        qv=self.vectorizer.transform([query]); lexical=cosine_similarity(qv,self.matrix)[0]
        scored=[]
        qwords=set(re.findall(r'[a-z0-9]+',query.lower()))
        for i,t in enumerate(self.tools):
            dscore=self._domain_match(t,domain)
            name_words=set(re.findall(r'[a-z0-9]+',t['name'].lower()))
            overlap=len(qwords & name_words)/max(1,len(qwords))
            # hybrid score: semantic + exact name + domain boost + write intent alignment
            write_intent=any(w in query.lower() for w in ['create','send','capture','refund','cancel','delete','update','pay','payout','record','appeal','settle'])
            method_boost=0.08 if write_intent and t['method'] in ('POST','PUT','PATCH','DELETE') else 0.0
            score=0.55*float(lexical[i])+0.22*overlap+0.18*dscore+method_boost
            scored.append((score,t))
        scored.sort(key=lambda x:x[0], reverse=True)
        out=[]
        for score,t in scored[:max(k,1)]:
            out.append({'tool_id':t['tool_id'],'name':t['name'],'score':round(score,4),'domain':t['domain'],'method':t['method'],'path':t['path'],'reason':f'domain={domain}; hybrid={score:.3f}'})
        return out

    def get(self, tool_id):
        return next((t for t in self.tools if t['tool_id']==tool_id),None)

    def all(self): return self.tools
