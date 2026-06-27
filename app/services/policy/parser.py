from typing import Any, cast

import pymupdf4llm


def parse_policy_pdf(file_path: str) -> list[dict]:
    """
    Converts a policy PDF into a list of per-page markdown blocks.
    Returns: [{"page": int, "text": str}, ...]
    """
    raw_pages = pymupdf4llm.to_markdown(file_path, page_chunks=True)
    print("<-Raw Pages->")
    pages = cast(list[dict[str, Any]], raw_pages)
    print("<-Extracted Pages->")
    return [
        {"page": page["metadata"].get("page", idx + 1), "text": page["text"]}
        for idx, page in enumerate(pages)
    ]