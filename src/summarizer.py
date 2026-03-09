import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


@dataclass
class RuntimeSettings:
    api_key: str
    model: str
    base_url: str


def load_runtime_settings() -> RuntimeSettings:
    api_key = os.getenv("LLM_API_KEY", "").strip() or os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("LLM_MODEL", "").strip() or os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
    base_url = os.getenv("LLM_BASE_URL", "").strip() or os.getenv("OPENAI_BASE_URL", "").strip()

    if not api_key:
        raise ValueError(
            "未检测到 API Key。请先运行 `python src/cli.py setup`，或在 .env 中填写 LLM_API_KEY。"
        )
    if not model:
        raise ValueError(
            "未检测到模型名称。请先运行 `python src/cli.py setup`，或在 .env 中填写 LLM_MODEL。"
        )

    return RuntimeSettings(api_key=api_key, model=model, base_url=base_url)


def _extract_json_object(content: str) -> Dict[str, Any]:
    cleaned = (content or "").strip()
    if not cleaned:
        return {}

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {}

    snippet = cleaned[start : end + 1]
    try:
        return json.loads(snippet)
    except json.JSONDecodeError:
        return {}


def _normalize_list(value: Any, max_items: int) -> List[str]:
    if isinstance(value, list):
        items = value
    elif isinstance(value, str):
        items = [s.strip() for s in value.split(",") if s.strip()]
    else:
        items = []

    normalized: List[str] = []
    for item in items:
        text = str(item).strip()
        if text:
            normalized.append(text)
        if len(normalized) >= max_items:
            break
    return normalized


def summarize_text(
    text: str,
    title: str = "",
    max_points: int = 5,
    max_keywords: int = 8,
    language: str = "zh",
) -> Dict[str, Any]:
    settings = load_runtime_settings()
    client = OpenAI(api_key=settings.api_key, base_url=settings.base_url or None)

    output_lang = "Chinese" if language.lower().startswith("zh") else "English"
    system_prompt = (
        "You are a precise article analyst. Return JSON only without markdown code fences."
    )
    user_prompt = (
        f"Summarize this article in {output_lang} and return JSON with keys:\n"
        "{\n"
        '  "summary": "string",\n'
        '  "key_points": ["string", "..."],\n'
        '  "keywords": ["string", "..."]\n'
        "}\n"
        f"Rules:\n- key_points length <= {max_points}\n"
        f"- keywords length <= {max_keywords}\n"
        "- Focus on factual and core ideas only\n\n"
        f"Title: {title or 'N/A'}\n"
        f"Content:\n{text}"
    )

    try:
        completion = client.chat.completions.create(
            model=settings.model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
    except Exception:
        # Some OpenAI-compatible gateways do not support response_format.
        completion = client.chat.completions.create(
            model=settings.model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

    content = completion.choices[0].message.content or ""
    parsed = _extract_json_object(content)

    summary = str(parsed.get("summary", "")).strip()
    key_points = _normalize_list(parsed.get("key_points", []), max_items=max_points)
    keywords = _normalize_list(parsed.get("keywords", []), max_items=max_keywords)

    if not summary:
        summary = "未能生成有效摘要，请稍后重试或更换模型。"
    if not key_points:
        key_points = ["未提取到关键观点，请尝试调大内容长度或更换模型。"]
    if not keywords:
        keywords = ["待补充"]

    return {
        "summary": summary,
        "key_points": key_points,
        "keywords": keywords,
        "model": settings.model,
    }
