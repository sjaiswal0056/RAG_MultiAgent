from __future__ import annotations

from app.config import settings
from app.models.evidence import Evidence, PolicyChunk
from app.retrieval.dense import LSADenseRetriever, SentenceTransformerDenseRetriever
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.reranker import CrossFeatureReranker
from app.retrieval.sparse import BM25Retriever


class HybridRetriever:
    def __init__(self, chunks: list[PolicyChunk]):
        self.chunks = chunks
        if settings.embedding_backend == "sentence_transformers":
            try:
                self.dense = SentenceTransformerDenseRetriever(chunks, settings.embedding_model)
            except Exception:
                self.dense = LSADenseRetriever(chunks)
        else:
            self.dense = LSADenseRetriever(chunks)
        self.sparse = BM25Retriever(chunks)
        self.reranker = CrossFeatureReranker()

    def search(self, query: str, dimension: str, top_k: int | None = None) -> list[Evidence]:
        dense = self.dense.search(query, settings.dense_top_k)
        sparse = self.sparse.search(query, settings.sparse_top_k)
        fused = reciprocal_rank_fusion(dense, sparse, settings.rrf_k, settings.fused_top_k)
        reranked = self.reranker.rerank(query, fused, top_k or settings.rerank_top_k)
        results = []
        for item in reranked:
            chunk = item["chunk"]
            results.append(Evidence(
                dimension=dimension, chunk_id=chunk.chunk_id, source=chunk.source, page=chunk.page,
                section=chunk.section, heading=chunk.heading, text=chunk.text,
                dense_score=item.get("dense_score"), dense_rank=item.get("dense_rank"),
                sparse_score=item.get("sparse_score"), sparse_rank=item.get("sparse_rank"),
                fusion_score=item["fusion_score"], pre_rerank_position=item["pre_rerank_position"],
                rerank_score=item["rerank_score"], final_rank=item["final_rank"],
            ))
        return results
