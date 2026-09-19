# LangGraph adapter. The application remains runnable when LangGraph is not installed.
try:
    from langgraph.graph import StateGraph, START, END
    LANGGRAPH_AVAILABLE=True
except Exception:
    StateGraph=START=END=None; LANGGRAPH_AVAILABLE=False

def build_graph(node_fn):
    if not LANGGRAPH_AVAILABLE: return None
    g=StateGraph(dict); g.add_node('agent',node_fn); g.add_edge(START,'agent'); g.add_edge('agent',END); return g.compile()
