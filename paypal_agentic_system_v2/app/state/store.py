import json, sqlite3, uuid
from datetime import datetime, timezone
from pathlib import Path

class StateStore:
    def __init__(self, db_path='data/app.db'):
        Path(db_path).parent.mkdir(parents=True,exist_ok=True); self.db_path=db_path; self._init()
    def _conn(self): return sqlite3.connect(self.db_path)
    def _init(self):
        with self._conn() as c:
            c.execute('CREATE TABLE IF NOT EXISTS sessions(session_id TEXT PRIMARY KEY,state_json TEXT NOT NULL,updated_at TEXT NOT NULL)')
            c.execute('CREATE TABLE IF NOT EXISTS executions(execution_id TEXT PRIMARY KEY,session_id TEXT,tool_id TEXT,status TEXT,result_json TEXT,created_at TEXT)')
    def load(self,sid):
        with self._conn() as c:
            r=c.execute('SELECT state_json FROM sessions WHERE session_id=?',(sid,)).fetchone()
        return json.loads(r[0]) if r else {'session_id':sid,'intermediate_results':{},'execution_history':[]}
    def save(self,sid,state):
        now=datetime.now(timezone.utc).isoformat()
        with self._conn() as c: c.execute('INSERT INTO sessions VALUES(?,?,?) ON CONFLICT(session_id) DO UPDATE SET state_json=excluded.state_json,updated_at=excluded.updated_at',(sid,json.dumps(state),now))
    def record_execution(self,sid,tool_id,result):
        eid=result.get('execution_id') or str(uuid.uuid4()); now=datetime.now(timezone.utc).isoformat()
        with self._conn() as c: c.execute('INSERT OR REPLACE INTO executions VALUES(?,?,?,?,?,?)',(eid,sid,tool_id,'success' if result.get('success') else 'error',json.dumps(result),now))
        return eid
    def recent(self,sid,limit=20):
        with self._conn() as c: rows=c.execute('SELECT execution_id,tool_id,status,result_json,created_at FROM executions WHERE session_id=? ORDER BY created_at DESC LIMIT ?',(sid,limit)).fetchall()
        return [{'execution_id':r[0],'tool_id':r[1],'status':r[2],'result':json.loads(r[3]),'created_at':r[4]} for r in rows]
    def search_executions(self,sid,query):
        rows=self.recent(sid,100); q=query.lower(); return [r for r in rows if q in json.dumps(r).lower()]
