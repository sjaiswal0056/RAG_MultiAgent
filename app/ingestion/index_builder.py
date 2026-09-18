from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.config import settings
from app.ingestion.chunker import chunk_policy
from app.ingestion.pdf_loader import load_pdf_pages
from app.models.evidence import PolicyChunk


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_index(policy_path: Path | None = None, index_dir: Path | None = None) -> dict:
    policy_path = policy_path or settings.policy_path
    index_dir = index_dir or settings.index_dir
    chunks = chunk_policy(load_pdf_pages(policy_path))
    index_dir.mkdir(parents=True, exist_ok=True)
    payload = [chunk.model_dump() for chunk in chunks]
    (index_dir / "chunks.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    sections = sorted({chunk.section for chunk in chunks})
    manifest = {
        "policy_sha256": _sha256(policy_path),
        "source": policy_path.name,
        "chunk_count": len(chunks),
        "pages_represented": sorted({chunk.page for chunk in chunks}),
        "sections": sections,
    }
    (index_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def load_chunks(index_dir: Path | None = None, auto_build: bool = True) -> list[PolicyChunk]:
    index_dir = index_dir or settings.index_dir
    target = index_dir / "chunks.json"
    if not target.exists():
        if not auto_build:
            raise FileNotFoundError("Policy index is not built")
        build_index(index_dir=index_dir)
    return [PolicyChunk.model_validate(item) for item in json.loads(target.read_text(encoding="utf-8"))]
