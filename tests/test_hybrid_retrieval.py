from app.retrieval.fusion import reciprocal_rank_fusion


def test_rrf_combines_and_deduplicates(chunks):
    dense = [{"chunk": chunks[0], "dense_rank": 1, "dense_score": 0.9}]
    sparse = [
        {"chunk": chunks[0], "sparse_rank": 1, "sparse_score": 5.0},
        {"chunk": chunks[1], "sparse_rank": 2, "sparse_score": 4.0},
    ]
    fused = reciprocal_rank_fusion(dense, sparse)
    assert len(fused) == 2
    assert fused[0]["chunk"].chunk_id == chunks[0].chunk_id
    assert fused[0]["fusion_score"] > fused[1]["fusion_score"]
