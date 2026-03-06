import json
import os
from typing import Any, Dict

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def summarize_text(text: str, title: str = "", max_points: int = 5) -> Dict[str, Any]:
    api_key = os.getenv("LLM_API_KEY", "").strip() or os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("缺少 API Key，请在 .env 中设置 LLM_API_KEY。")

    model = os.getenv("LLM_MODEL", "").strip() or os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    base_url = os.getenv("LLM_BASE_URL", "").strip() or os.getenv("OPENAI_BASE_URL", "").strip()
    client = OpenAI(api_key=api_key, base_url=base_url or None)

    system_prompt = (
        "You are a precise article analyst. Return valid JSON only. "
        "Do not add markdown or extra commentary."
    )
    user_prompt = (
        "Summarize this article in Chinese and return JSON with keys:\n"
        "{\n"
        '  "summary": "string",\n'
        '  "key_points": ["string", "..."],\n'
        '  "keywords": ["string", "..."]\n'
        "}\n"
        f"Rules:\n- key_points length <= {max_points}\n"
        "- keywords length between 5 and 10\n"
        "- Focus on factual and core ideas only\n\n"
        f"Title: {title or 'N/A'}\n"
        f"Content:\n{text}"
    )

    completion = client.chat.completions.create(
        model=model,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )

    content = completion.choices[0].message.content or "{}"
    parsed = json.loads(content)

    return {
        "summary": parsed.get("summary", "").strip(),
        "key_points": parsed.get("key_points", []),
        "keywords": parsed.get("keywords", []),
        "model": model,
    }
