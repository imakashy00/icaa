import json
import time

import openai

from app.core.settings import settings

_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)


def call_openai_json(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 2000,
    max_retries: int = 3,
) -> dict:
    """Calls OpenAI for strict JSON output, strips code fences, and retries on failure."""
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
            response_format={"type": "json_object"} 
            )
            content = response.choices[0].message.content
            text_out = content.strip() if content else ""
            text_out = _strip_code_fences(text_out)
            return json.loads(text_out)

        except (json.JSONDecodeError, openai.OpenAIError) as exc:
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
