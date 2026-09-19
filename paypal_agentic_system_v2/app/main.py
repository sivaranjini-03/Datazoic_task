from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.models import ChatRequest, ChatResponse
from app.retrieval.retriever import ToolRetriever
from app.tools.rag import RAGTool
from app.tools.system_search import SystemSearch
from app.paypal.executor import PayPalExecutor
from app.state.store import StateStore
from app.policy.engine import PolicyEngine
from app.agent.planner import LLMPlanner
from app.agent.orchestrator import AgentOrchestrator
from app.observability.logging import logger

retriever=ToolRetriever(settings.tool_registry_path)
state_store=StateStore(settings.database_url.replace('sqlite:///','') if settings.database_url.startswith('sqlite:///') else 'data/app.db')
executor=PayPalExecutor(retriever); planner=LLMPlanner(retriever.all() and retriever, retriever)
agent=AgentOrchestrator(retriever,planner,executor,state_store,PolicyEngine())
rag=RAGTool(settings.rag_knowledge_dir); system_search=SystemSearch(retriever,state_store)

app=FastAPI(title=settings.app_name,version='2.0.0')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_credentials=False,allow_methods=['*'],allow_headers=['*'])

@app.get('/health')
async def health(): return {'status':'ok','mock_mode':settings.paypal_mock_mode,'tools':len(retriever.all())}

@app.get('/tools')
async def tools(q:str|None=None,k:int=10): return {'tools':retriever.search(q,k) if q else retriever.all()[:k]}

@app.get('/tools/{tool_id:path}')
async def tool(tool_id:str):
    t=retriever.get(tool_id)
    return t or {'error':'tool not found'}

@app.post('/chat',response_model=ChatResponse)
async def chat(req:ChatRequest):
    q=req.message.lower()
    if any(x in q for x in ['what apis','what tools','available apis','available tools','system search','last request','previous request','history']):
        r=system_search.search(req.message,req.session_id); return ChatResponse(session_id=req.session_id,answer=str(r),status='completed',trace=[{'stage':'routing','status':'completed','capability':'system_search'},{'stage':'search','status':'completed','result_type':r.get('type') if isinstance(r,dict) else 'unknown'}])
    if any(x in q for x in ['how does','explain','documentation','what is paypal','how to']):
        r=rag.answer(req.message); return ChatResponse(session_id=req.session_id,answer=r['answer']+'\n\nSources: '+', '.join(x['source'] for x in r['sources']),status='completed',trace=[{'stage':'routing','status':'completed','capability':'rag'},{'stage':'retrieval','status':'completed','source_count':len(r['sources'])},{'stage':'completed','status':'success'}])
    r=await agent.run(req.session_id,req.message,req.confirmed)
    return ChatResponse(**r)

@app.post('/rag/search')
async def rag_search(query:str,k:int=4): return {'results':rag.search(query,k)}

@app.get('/system/search')
async def system_search_endpoint(q:str,session_id:str|None=None): return system_search.search(q,session_id)

@app.get('/executions/{session_id}')
async def executions(session_id:str): return {'executions':state_store.recent(session_id,100)}

app.mount('/ui', StaticFiles(directory='frontend', html=True), name='ui')
