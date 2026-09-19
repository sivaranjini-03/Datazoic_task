#!/usr/bin/env python3
"""Import a Postman collection into a sanitized, searchable PayPal tool registry."""
import argparse, json, re, hashlib
from pathlib import Path

SECRET_WORDS = re.compile(r"(secret|password|token|authorization|client[_-]?id|client[_-]?secret|api[_-]?key)", re.I)
PLACEHOLDER = re.compile(r"{{\s*([^}]+)\s*}}|:([A-Za-z_][A-Za-z0-9_-]*)")


def infer_schema(value):
    if isinstance(value, dict):
        return {k: infer_schema(v) for k, v in value.items()}
    if isinstance(value, list):
        return [infer_schema(value[0])] if value else []
    if isinstance(value, bool): return {"type":"boolean"}
    if isinstance(value, (int,float)): return {"type":"number"}
    if isinstance(value, str):
        if re.fullmatch(r"-?\d+(\.\d+)?", value): return {"type":"number"}
        if "email" in value.lower(): return {"type":"string", "format":"email"}
        return {"type":"string"}
    return {"type":"string"}


def sanitize_value(v):
    if isinstance(v, dict): return {k: sanitize_value(x) for k,x in v.items()}
    if isinstance(v, list): return [sanitize_value(x) for x in v]
    if isinstance(v, str):
        if SECRET_WORDS.search(v) and not v.startswith("{{"):
            return "[REDACTED]"
        return v
    return v


def parse_body(req):
    body=req.get('body') or {}
    mode=body.get('mode')
    if mode=='raw':
        raw=body.get('raw','')
        try:
            data=json.loads(raw)
            return sanitize_value(data), infer_schema(data)
        except Exception:
            return None, None
    if mode=='urlencoded':
        vals={}
        required=[]
        for x in body.get('urlencoded',[]):
            if x.get('disabled'): continue
            k=x.get('key')
            vals[k]=sanitize_value(x.get('value',''))
            required.append(k)
        return vals, {"type":"object","properties":{k:{"type":"string"} for k in vals},"required":required}
    if mode=='formdata':
        vals={}; required=[]
        for x in body.get('formdata',[]):
            if x.get('disabled'): continue
            k=x.get('key'); vals[k]=sanitize_value(x.get('value',''))
            required.append(k)
        return vals, {"type":"object","properties":{k:{"type":"string"} for k in vals},"required":required}
    return None,None


def walk(items, parents=()):
    for item in items or []:
        if 'item' in item:
            yield from walk(item['item'], parents+(item.get('name',''),))
        elif 'request' in item:
            yield parents,item


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('collection')
    ap.add_argument('output')
    args=ap.parse_args()
    data=json.loads(Path(args.collection).read_text(encoding='utf-8'))
    tools=[]
    for groups,item in walk(data.get('item',[])):
        req=item['request']; method=req.get('method','GET').upper(); url=req.get('url') or {}
        raw=url.get('raw','') if isinstance(url,dict) else str(url)
        path='/'+'/'.join(url.get('path',[])) if isinstance(url,dict) and url.get('path') else raw.split('{{base_url}}')[-1].split('?')[0]
        path=path.replace('//','/')
        path_params=[]
        for m in PLACEHOLDER.finditer(path):
            p=m.group(1) or m.group(2)
            if p not in ('base_url',): path_params.append(p)
        query=[]
        if isinstance(url,dict):
            for q in url.get('query',[]) or []:
                if not q.get('disabled'):
                    query.append({"name":q.get('key'),"description":q.get('description','')})
        body_example, body_schema=parse_body(req)
        group='/'.join(groups) or 'General'
        domain=groups[0] if groups else 'General'
        safe_name=re.sub(r'[^a-z0-9]+','_',item.get('name','tool').lower()).strip('_')
        raw_id=f"paypal.{domain.lower().replace(' ','_')}.{safe_name}"
        tool_id=raw_id[:90]
        # stable unique suffix when necessary
        if any(t['tool_id']==tool_id for t in tools):
            tool_id += '_' + hashlib.sha1(raw.encode()).hexdigest()[:8]
        text=' '.join([item.get('name',''), group, method, path, req.get('description','') or '', json.dumps(body_example or '')])
        risk='read'
        if method in ('POST','PUT','PATCH','DELETE'): risk='write'
        lower=item.get('name','').lower()+' '+path.lower()
        if any(w in lower for w in ['capture','refund','payout','payment','settle','adjudicate','cancel','delete','appeal','offer']): risk='financial' if any(w in lower for w in ['capture','refund','payout','payment']) else 'destructive'
        required=list(dict.fromkeys(path_params + ([x['name'] for x in query if x.get('name')] if method in ('GET','DELETE') else [])))
        tools.append({
            'tool_id':tool_id,'name':item.get('name',''),'service':'paypal','domain':domain,'group':group,
            'method':method,'path':path,'raw_url':raw,'description':req.get('description','') or item.get('description','') or '',
            'path_parameters':path_params,'query_parameters':query,'required_parameters':required,
            'request_example':body_example,'request_schema':body_schema,'risk':risk,
            'requires_confirmation': risk in ('financial','destructive'), 'search_text':text[:8000]
        })
    out={'version':'2.0','source':'sanitized Postman import','tool_count':len(tools),'tools':tools}
    Path(args.output).write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(f'Imported {len(tools)} tools -> {args.output}')

if __name__=='__main__': main()
