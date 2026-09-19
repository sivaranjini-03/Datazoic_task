from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
class RAGTool:
    def __init__(self,knowledge_dir):
        self.docs=[]
        for p in Path(knowledge_dir).glob('*.md'):
            text=p.read_text(encoding='utf-8'); chunks=[x.strip() for x in text.split('\n\n') if x.strip()]
            self.docs += [{'source':p.name,'text':c} for c in chunks]
        self.vectorizer=TfidfVectorizer(stop_words='english'); self.matrix=self.vectorizer.fit_transform([d['text'] for d in self.docs]) if self.docs else None
    def search(self,q,k=4):
        if not self.docs: return []
        scores=cosine_similarity(self.vectorizer.transform([q]),self.matrix)[0]; idx=scores.argsort()[::-1][:k]
        return [{'source':self.docs[i]['source'],'text':self.docs[i]['text'],'score':round(float(scores[i]),4)} for i in idx]
    def answer(self,q):
        hits=self.search(q); return {'answer':'\n\n'.join(h['text'] for h in hits) if hits else 'No relevant knowledge was found.','sources':hits}
