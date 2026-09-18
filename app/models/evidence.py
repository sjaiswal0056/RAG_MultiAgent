from __future__ import annotations

from pydantic import BaseModel, Field


class PolicyChunk(BaseModel):
    chunk_id: str
    source: str
    page: int = Field(ge=1)
    section: str
    heading: str
    subsection: str = ""
    text: str
    start_offset: int = 0
    end_offset: int = 0


class Evidence(BaseModel):
    dimension: str
    chunk_id: str
    source: str
    page: int
    section: str
    heading: str
    text: str
    dense_score: float | None = None
    dense_rank: int | None = None
    sparse_score: float | None = None
    sparse_rank: int | None = None
    fusion_score: float
    pre_rerank_position: int
    rerank_score: float
    final_rank: int
