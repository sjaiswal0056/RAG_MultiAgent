from __future__ import annotations

from functools import lru_cache

from app.ingestion.index_builder import load_chunks
from app.retrieval.hybrid_retriever import HybridRetriever


@lru_cache(maxsize=1)
def get_retriever() -> HybridRetriever:
    return HybridRetriever(load_chunks())
