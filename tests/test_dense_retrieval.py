from app.retrieval.dense import HashingDenseRetriever


def test_semantic_normalization_finds_domiciliary(chunks):
    results = HashingDenseRetriever(chunks).search("home treatment because hospital room unavailable", top_k=10)
    assert any("domiciliary" in item["chunk"].text.lower() for item in results)
