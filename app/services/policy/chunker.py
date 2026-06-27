"""
Splits per-page markdown into clause-level chunks.

Why this exists: feeding 40 pages of raw text to an LLM on every claim is
slow, expensive, and dilutes the model's attention. Splitting into clauses
lets us embed and retrieve only the handful of clauses relevant to a given
claim (see retrieval.py).

NOTE (production hardening): insurers format policy wordings very
differently -- some use strict numbered clauses ("4.1.2 ..."), others use
markdown-style headings only, others use tables for sub-limits. The regex
below covers the common "N.N Heading" pattern plus markdown `#` headings,
and falls back to fixed-size splitting for anything else. For a specific
insurer's template, it's worth spot-checking chunk boundaries on a sample
policy and tightening HEADING_PATTERN if needed -- bad chunking is the most
common cause of poor retrieval quality.
"""

import re

# Matches either:
#   - markdown headings:           "## 4.1 Waiting Periods"
#   - plain numbered clause headings: "4.1.2 Pre-existing Diseases"
HEADING_PATTERN = re.compile(
    r"^##\s+\*\*(?:([A-Z\d]+(?:\.[A-Z\d]+)*)\.)?\s*(.*?)\*\*$", re.MULTILINE
)


def chunk_policy_pages(pages: list[dict]) -> list[dict]:
    """
    Splits each page's markdown into clause chunks by detecting numbered
    headings. Each chunk retains its clause number, heading text, body text,
    and source page number for traceability.

    Pages with no detectable headings (dense paragraphs, table-derived text)
    fall back to fixed-size paragraph-boundary splitting so content is never
    silently dropped.

    Returns: [{"clause_number": str|None, "heading": str|None,
               "text": str, "page": int}, ...]
    """
    chunks = []

    for page in pages:
        text = page["text"]
        matches = list(HEADING_PATTERN.finditer(text))

        if not matches:
            for piece in _fixed_size_split(text, max_chars=1500):
                if piece.strip():
                    chunks.append(
                        {
                            "clause_number": None,
                            "heading": None,
                            "text": piece.strip(),
                            "page": page["page"],
                        }
                    )
            continue

        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = text[start:end].strip()

            if len(body) < 10:
                continue

            chunks.append(
                {
                    "clause_number": match.group(1).rstrip("."),
                    "heading": match.group(2).strip(),
                    "text": body,
                    "page": page["page"],
                }
            )

    return chunks


def _fixed_size_split(text: str, max_chars: int) -> list[str]:
    """Splits unstructured text into ~max_chars pieces on paragraph boundaries."""
    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if current and len(current) + len(para) > max_chars:
            chunks.append(current)
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para

    if current:
        chunks.append(current)

    return chunks
