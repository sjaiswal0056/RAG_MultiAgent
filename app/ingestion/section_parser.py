from __future__ import annotations

import re


MAJOR_HEADINGS = {
    "DEFINITIONS",
    "SCOPE OF COVER",
    "WHAT WE COVER",
    "WHAT WE EXCLUDE",
    "EXTENSIONS",
    "CLAIMS PROCEDURE",
    "STANDARD TERMS AND CONDITIONS",
}


def clean_page_text(text: str) -> str:
    lines = []
    for raw in text.replace("\u2019", "'").splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if not line:
            continue
        if "CSC- Individual Health Insurance-Policy Wording" in line:
            continue
        if line == "UNIVERSAL SOMPO GENERAL INSURANCE CO LTD":
            continue
        lines.append(line)
    return "\n".join(lines)


def detect_heading(line: str) -> str | None:
    normalized = re.sub(r"\s+", " ", line).strip(" :")
    upper = normalized.upper()
    if upper in MAJOR_HEADINGS:
        return upper
    if re.match(r"^(Critical Illness|Day Care Treatment|Domiciliary Treat|Pre-? ?Existing Diseases|Hospitalization|Hospital means)", normalized, re.I):
        return normalized[:100]
    return None
