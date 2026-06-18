"""
Thin wrapper around the Anthropic API that enforces structured (JSON) output
and adds retries. Every LLM step in this pipeline -- clause classification,
structured field extraction at ingestion, and clause-based reasoning at audit
time -- needs machine-readable output that downstream code can act on without
further parsing/guessing.
"""

import json
import time

import openai

from app.core.settings import settings

_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)


def call_claude_json(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 2000,
    max_retries: int = 3,
) -> dict:
    """
    Calls Claude with a system prompt that instructs strict JSON-only output
    and a user prompt containing the task content. Strips markdown code
    fences if the model wraps its JSON in ```json ... ``` despite
    instructions, and retries on transient API errors or JSON parse failures.

    Returns the parsed dict. Raises RuntimeError if all retries fail --
    callers should treat that as a hard failure (do not silently continue
    an ingestion or audit with missing data).
    """
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            response = _client.chat.completions.create(
                model="gpt-4o-mini",
                max_tokens=max_tokens,
                messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            )
            text_out = "".join(
                block.text for block in response. if block.type == "text"
            ).strip()

            text_out = _strip_code_fences(text_out)
            return json.loads(text_out)

        except (json.JSONDecodeError, anthropic.APIError) as exc:
            last_error = exc
            time.sleep(1.5 * (attempt + 1))

    raise RuntimeError(f"LLM call failed after {max_retries} attempts: {last_error}")


def _strip_code_fences(text_out: str) -> str:
    """Removes ```json / ``` wrappers some models add despite instructions."""
    if not text_out.startswith("```"):
        return text_out

    lines = text_out.splitlines()
    if lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]
    return "\n".join(lines).strip()
