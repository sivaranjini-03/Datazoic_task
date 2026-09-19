# Scaling from 50 to 5,000+ APIs

## 50 APIs
SQLite + TF-IDF + metadata filtering is enough.

## 500 APIs
Introduce domain indexes, hybrid lexical/semantic retrieval and caching.

## 5,000+ APIs
Use a service/domain/operation hierarchy, metadata filters, vector search, BM25/OpenSearch, reranking, top-K context, distributed state and observability.

The LLM context remains approximately constant because it receives only the final candidate set.
