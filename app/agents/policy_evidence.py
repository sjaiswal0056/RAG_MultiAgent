from __future__ import annotations

import time

from app.models.agent_state import ClaimWorkflowState
from app.models.decision import TraceEvent
from app.retrieval.hybrid_retriever import HybridRetriever


class PolicyEvidenceAgent:
    name = "PolicyEvidenceAgent"

    def __init__(self, retriever: HybridRetriever):
        self.retriever = retriever

    def run(self, state: ClaimWorkflowState) -> ClaimWorkflowState:
        assert state.analysis is not None
        by_key = {}
        for planned in state.analysis.retrieval_queries:
            started = time.perf_counter()
            results = self.retriever.search(planned.query, planned.dimension)
            for evidence in results:
                key = (planned.dimension, evidence.chunk_id)
                previous = by_key.get(key)
                if previous is None or evidence.rerank_score > previous.rerank_score:
                    by_key[key] = evidence
            state.trace.append(TraceEvent(agent=self.name, action="hybrid_retrieve_fuse_rerank", retrieval_query=planned.query,
                result_count=len(results), evidence_ids=[item.chunk_id for item in results],
                elapsed_ms=(time.perf_counter()-started)*1000, brief_outcome=f"Retrieved evidence for {planned.dimension}"))
        state.retrieved_evidence = list(by_key.values())
        return state
