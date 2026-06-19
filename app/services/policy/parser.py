"""PDF -> per-page markdown, using pymupdf4llm."""

import pymupdf4llm


def parse_policy_pdf(file_path: str) -> list[dict]:
    """
    Converts a policy PDF into a list of per-page markdown blocks.

    Why markdown + per-page: pymupdf4llm's markdown output preserves heading
    structure (e.g. larger/bold text becomes `#`/`##`/`**...**`), which the
    chunker relies on to find clause boundaries -- much more reliable than
    splitting raw extracted text. Keeping page numbers lets every stored
    clause be traced back to an exact page in the source PDF, which matters
    for audit defensibility ("this exclusion is on page 14").

    Returns: [{"page": int, "text": str}, ...]
    """
    pages = pymupdf4llm.to_markdown(file_path, page_chunks=True)
    return [
        {"page": page["metadata"].get("page", idx + 1), "text": page["text"]}
        for idx, page in enumerate(pages)
    ]
