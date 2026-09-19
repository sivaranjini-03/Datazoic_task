from app.state.store import StateStore

def test_state_persists(tmp_path):
    s=StateStore(str(tmp_path/'x.db')); s.save('a',{'session_id':'a','intermediate_results':{'order_id':'123'},'execution_history':[]}); assert s.load('a')['intermediate_results']['order_id']=='123'
