from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader


class PolicyLoadError(RuntimeError):
    pass


def load_pdf_pages(path: Path) -> list[dict]:
    if not path.exists():
        raise PolicyLoadError(f"Policy PDF not found: {path}")
    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise PolicyLoadError(f"Policy PDF could not be opened: {exc}") from exc
    pages = []
    for index, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            pages.append({"page": index, "text": text})
    if not pages:
        raise PolicyLoadError("Policy PDF extraction produced no text")
    return pages
