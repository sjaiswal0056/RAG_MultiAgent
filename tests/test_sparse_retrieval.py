from app.retrieval.sparse import BM25Retriever


def test_exact_policy_phrase_found(chunks):
    results = BM25Retriever(chunks).search("30 days Waiting Period", top_k=5)
    assert any("30 days Waiting Period".lower() in item["chunk"].text.lower() for item in results)
