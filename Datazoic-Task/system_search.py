import json
class SystemSearch:
    def __init__(self,retriever,state_store): self.retriever=retriever; self.state_store=state_store
    def search(self,query,session_id=None):
        q=query.lower()
        if session_id and any(x in q for x in ['last request','last operation','previous request','history']):
            return {'type':'execution_history','results':self.state_store.recent(session_id,20)}
        return {'type':'tools','results':self.retriever.search(query,10)}
