from app.models.evidence import PolicyChunk
from app.retrieval.reranker import CrossFeatureReranker


def test_reranker_changes_order_for_relevant_pair():
    irrelevant = PolicyChunk(chunk_id="a", source="p", page=1, section="X", heading="Other", text="unrelated wording")
    relevant = PolicyChunk(chunk_id="b", source="p", page=1, section="X", heading="Waiting period", text="A 30 days waiting period applies")
    candidates = [
        {"chunk": irrelevant, "fusion_score": 0.04},
        {"chunk": relevant, "fusion_score": 0.03},
    ]
    ranked = CrossFeatureReranker().rerank("30 days waiting period", candidates)
    assert ranked[0]["chunk"].chunk_id == "b"
    assert ranked[0]["pre_rerank_position"] == 2
