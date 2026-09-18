from app.ingestion.chunker import chunk_policy
from app.ingestion.pdf_loader import load_pdf_pages
from app.config import settings


def test_chunks_are_deterministic_and_traceable():
    pages = load_pdf_pages(settings.policy_path)
    first = chunk_policy(pages)
    second = chunk_policy(pages)
    assert [c.chunk_id for c in first] == [c.chunk_id for c in second]
    assert all(c.page and c.section and c.heading and c.text for c in first)
    assert {"DEFINITIONS", "SCOPE OF COVER", "WHAT WE EXCLUDE"} <= {c.section for c in first}
