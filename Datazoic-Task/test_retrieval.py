from app.retrieval.retriever import ToolRetriever

def test_registry_has_116_tools():
    r=ToolRetriever('data/tool_registry.json'); assert len(r.all())==116

def test_nested_invoice_domain_search():
    r=ToolRetriever('data/tool_registry.json'); x=r.search('send an invoice',8,'Invoices'); assert any('invoice' in t['name'].lower() for t in x)
