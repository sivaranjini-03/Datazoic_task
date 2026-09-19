import re, uuid
from app.agent.planner import LLMPlanner
from app.agent.graph import build_graph
from app.models import AgentState
from app.policy.engine import PolicyEngine
from app.observability.logging import logger
from app.agent.graph import build_graph

class AgentOrchestrator:
    def __init__(self,retriever,planner,executor,state_store,policy):
        self.retriever=retriever; self.planner=planner; self.executor=executor; self.store=state_store; self.policy=policy
        self.graph=build_graph(self._graph_node)

    async def _graph_node(self,state):
        return await self._run_impl(state['session_id'],state['query'],state.get('confirmed',False))

    async def run(self,sid,query,confirmed=False):
        if self.graph is not None:
            return await self.graph.ainvoke({'session_id':sid,'query':query,'confirmed':confirmed})
        return await self._run_impl(sid,query,confirmed)

    async def _run_impl(self,sid,query,confirmed=False):
        persisted=self.store.load(sid)
        trace=[{'stage':'request','status':'received','query':query}]
        # Resume a plan waiting for confirmation.
        if confirmed and persisted.get('pending_plan'):
            plan=persisted['pending_plan']; query=persisted.get('original_query',query)
            candidates=[]
        else:
            domain=self.retriever.infer_domain(query); candidates=self.retriever.search(query,8,domain)
            trace.append({'stage':'routing','status':'completed','domain':domain})
            trace.append({'stage':'retrieval','status':'completed','registry_size':len(self.retriever.all()),'candidate_count':len(candidates),'candidates':[{'tool_id':c['tool_id'],'name':c['name'],'score':c['score']} for c in candidates]})
            plan=(await self.planner.plan(query,candidates,persisted)).model_dump()
            trace.append({'stage':'planning','status':'completed','intent':plan.get('intent'),'step_count':len(plan.get('steps',[])),'tools':[x.get('tool_id') for x in plan.get('steps',[])]})
            if plan.get('clarification'):
                persisted['original_query']=query; self.store.save(sid,persisted)
                trace.append({'stage':'clarification','status':'required'})
                return {'session_id':sid,'answer':plan['clarification'],'status':'clarification','plan':plan.get('steps',[]),'trace':trace}
        # If confirmation is required later, execute safe prefix and persist the remainder.
        steps=plan.get('steps',[])
        history=persisted.get('execution_history',[]); state=persisted.get('intermediate_results',{})
        for idx,step in enumerate(steps):
            tool=self.retriever.get(step['tool_id'])
            if not tool: return {'session_id':sid,'answer':'The planned tool is not available in the registry.','status':'error','plan':steps,'trace':trace}
            if idx==0 or not confirmed:
                policy=self.policy.check(tool,confirmed=confirmed)
                if not policy['allowed'] and policy['requires_confirmation']:
                    persisted.update({'pending_plan':{'steps':steps[idx:],'intent':plan.get('intent'),'domain':plan.get('domain')},'original_query':query,'intermediate_results':state})
                    self.store.save(sid,persisted)
                    trace.append({'stage':'policy','status':'confirmation_required','tool_id':tool['tool_id'],'tool':tool['name']})
                    return {'session_id':sid,'answer':f"I’m ready to perform '{tool['name']}'. This action requires confirmation. Reply with confirmation to proceed.",'status':'confirmation_required','plan':steps[idx:],'trace':trace}
            params=self._resolve_refs(step.get('parameters',{}),state)
            err=self._validate(tool,params)
            if err:
                persisted['original_query']=query; self.store.save(sid,persisted)
                trace.append({'stage':'validation','status':'clarification_required','message':err})
                return {'session_id':sid,'answer':err,'status':'clarification','plan':steps[idx:],'trace':trace}
            trace.append({'stage':'validation','status':'passed','tool_id':tool['tool_id']})
            eid=str(uuid.uuid4()); result=await self.executor.execute(tool['tool_id'],params,state,eid)
            self.store.record_execution(sid,tool['tool_id'],result); history.append(result)
            trace.append({'stage':'execution','status':'success' if result.get('success') else 'failed','tool_id':tool['tool_id'],'tool':tool['name'],'execution_id':eid,'latency_ms':result.get('latency_ms',0)})
            if not result.get('success'):
                persisted.update({'execution_history':history,'intermediate_results':state}); self.store.save(sid,persisted)
                return {'session_id':sid,'answer':'The PayPal operation failed.','status':'error','tool_used':tool['tool_id'],'execution_id':eid,'plan':steps,'trace':trace}
            self._promote_ids(tool,result,state)
            # After a safe prefix, force confirmation on a later sensitive step.
            if idx+1 < len(steps):
                nxt=self.retriever.get(steps[idx+1]['tool_id'])
                if nxt and nxt.get('requires_confirmation') and not confirmed:
                    persisted.update({'pending_plan':{'steps':steps[idx+1:],'intent':plan.get('intent'),'domain':plan.get('domain')},'original_query':query,'intermediate_results':state,'execution_history':history})
                    self.store.save(sid,persisted)
                    trace.append({'stage':'policy','status':'confirmation_required','tool_id':nxt['tool_id'],'tool':nxt['name']})
                    return {'session_id':sid,'answer':f"The first step succeeded. Next I need to perform '{nxt['name']}', which requires confirmation. Reply with confirmation to continue.",'status':'confirmation_required','tool_used':tool['tool_id'],'execution_id':eid,'plan':steps,'trace':trace}
        persisted.update({'intermediate_results':state,'execution_history':history,'pending_plan':None,'original_query':query}); self.store.save(sid,persisted)
        answer=self._format(plan,history,state)
        logger.event('agent_completed',session_id=sid,intent=plan.get('intent'),domain=plan.get('domain'),tools=[x['tool_id'] for x in steps])
        trace.append({'stage':'completed','status':'success','tool_count':len(steps)})
        return {'session_id':sid,'answer':answer,'status':'completed','tool_used':steps[-1]['tool_id'] if steps else None,'execution_id':history[-1].get('execution_id') if history else None,'plan':steps,'trace':trace}

    def _validate(self,tool,params):
        for p in tool.get('path_parameters',[]):
            if not params.get(p): return f"Please provide the {p.replace('_',' ')}."
        # Do not force every example field; Postman examples often contain optional fields.
        if params.get('amount') is not None:
            try:
                if float(params['amount'])<=0: return 'The amount must be greater than zero.'
            except: return 'Please provide a valid numeric amount.'
        return None

    def _resolve_refs(self,obj,state):
        if isinstance(obj,dict): return {k:self._resolve_refs(v,state) for k,v in obj.items()}
        if isinstance(obj,list): return [self._resolve_refs(v,state) for v in obj]
        if isinstance(obj,str):
            m=re.fullmatch(r'\{\{state\.([A-Za-z0-9_]+)\}\}',obj)
            if m: return state.get(m.group(1),obj)
        return obj

    def _promote_ids(self,tool,result,state):
        data=result.get('data') or {}; name=tool['name'].lower()
        if isinstance(data,dict):
            if 'order' in name and data.get('id'): state['order_id']=data['id']
            if 'invoice' in name and data.get('id'): state['invoice_id']=data['id']
            for key in ['payment_id','capture_id','refund_id','dispute_id','subscription_id']:
                if data.get(key): state[key]=data[key]
            if data.get('id') and 'payment' in name: state['payment_id']=data['id']

    def _format(self,plan,history,state):
        if not history: return plan.get('final_answer') or 'No operation was executed.'
        last=history[-1].get('data') or {}
        if plan.get('intent')=='create_and_send_invoice': return f"Invoice {state.get('invoice_id','created')} was created and sent successfully."
        if plan.get('intent')=='create_and_capture_order': return f"Order {state.get('order_id','created')} was created and the payment was captured successfully."
        return f"The PayPal operation completed successfully. Result: {last}"
