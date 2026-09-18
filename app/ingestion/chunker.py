from __future__ import annotations

import hashlib
import re

from app.ingestion.section_parser import clean_page_text, detect_heading
from app.models.evidence import PolicyChunk


SOURCE_NAME = "USGIC-CSCIndividualHealthInsurance_2017-2018.pdf"
BOUNDARY = re.compile(
    r"^(?:\d+\.|[a-z]\)|[ivxlcdm]+\)|NB\d+:|Note\b|[A-Z][A-Za-z /-]{2,45} means\b|Pre- ?Hospitalization|Post Hospitalization)",
    re.I,
)


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:36]
    return slug or "policy"


def _stable_id(page: int, heading: str, ordinal: int, text: str) -> str:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]
    return f"policy-p{page:03d}-{_slug(heading)}-{ordinal:03d}-{digest}"


def chunk_policy(pages: list[dict]) -> list[PolicyChunk]:
    chunks: list[PolicyChunk] = []
    section = "PROSPECTUS"
    heading = "Policy wording"
    for page_record in pages:
        page = page_record["page"]
        text = clean_page_text(page_record["text"])
        lines = text.splitlines()
        units: list[tuple[str, str, str]] = []
        current: list[str] = []
        current_section, current_heading = section, heading

        def flush() -> None:
            nonlocal current
            body = " ".join(current).strip()
            if len(body) >= 25:
                units.append((current_section, current_heading, body))
            current = []

        for line in lines:
            found = detect_heading(line)
            if found:
                flush()
                if found in {"DEFINITIONS", "SCOPE OF COVER", "WHAT WE EXCLUDE", "EXTENSIONS", "CLAIMS PROCEDURE", "STANDARD TERMS AND CONDITIONS"}:
                    section = found
                heading = found
                current_section, current_heading = section, heading
                current = [line]
                continue
            if BOUNDARY.match(line) and current:
                flush()
                current_section, current_heading = section, heading
            current.append(line)
            if len(" ".join(current)) > 1200:
                flush()
                current_section, current_heading = section, heading
        flush()
        for ordinal, (unit_section, unit_heading, body) in enumerate(units, start=1):
            offset = text.find(body[: min(60, len(body))])
            chunks.append(
                PolicyChunk(
                    chunk_id=_stable_id(page, unit_heading, ordinal, body),
                    source=SOURCE_NAME,
                    page=page,
                    section=unit_section,
                    heading=unit_heading,
                    subsection=body.split(".", 1)[0][:100],
                    text=body,
                    start_offset=max(offset, 0),
                    end_offset=max(offset, 0) + len(body),
                )
            )
    return chunks
