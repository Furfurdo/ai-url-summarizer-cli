import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    OpenAI,
    RateLimitError,
)

load_dotenv()


TEMPLATE_INSTRUCTIONS = {
    "general": "Use a balanced style for broad readers.",
    "study": "Focus on definitions, concepts, and learnable takeaways.",
    "creator": "Focus on content angles, hooks, and practical storytelling points.",
    "research": "Focus on methods, claims, evidence quality, and limitations.",
}


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


def _split_sentences(text: str) -> List[str]:
    raw = re.split(r"(?<=[。！？!?；;])\s+|\n+", text)
    sentences = [s.strip() for s in raw if s and s.strip()]
    return [s for s in sentences if len(s) >= 15]


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]", text.lower())


def _best_evidence_for_point(point: str, sentences: List[str]) -> str:
    point_tokens = set(_tokenize(point))
    if not point_tokens:
        return sentences[0] if sentences else ""

    best_sentence = ""
    best_score = 0.0
    for sentence in sentences:
        sentence_tokens = set(_tokenize(sentence))
        if not sentence_tokens:
            continue
        overlap = point_tokens.intersection(sentence_tokens)
        score = len(overlap) / max(1, len(point_tokens))
        if score > best_score:
            best_score = score
            best_sentence = sentence

    if best_sentence:
        return best_sentence
    return sentences[0] if sentences else ""


def _build_key_point_items(key_points: List[str], text: str) -> List[Dict[str, str]]:
    sentences = _split_sentences(text)
    items: List[Dict[str, str]] = []
    for idx, point in enumerate(key_points, start=1):
        evidence = _best_evidence_for_point(point, sentences)
        evidence = evidence[:220].strip() if evidence else "未匹配到可引用片段。"
        items.append(
            {
                "index": str(idx),
                "point": point,
                "evidence": evidence,
            }
        )
    return items


def summarize_text(
    text: str,
    title: str = "",
    max_points: int = 5,
    max_keywords: int = 8,
    language: str = "zh",
    summary_template: str = "general",
    include_evidence: bool = True,
) -> Dict[str, Any]:
    settings = load_runtime_settings()
    client = OpenAI(api_key=settings.api_key, base_url=settings.base_url or None, timeout=60.0)

    output_lang = "Chinese" if language.lower().startswith("zh") else "English"
    template_key = summary_template if summary_template in TEMPLATE_INSTRUCTIONS else "general"
    template_instruction = TEMPLATE_INSTRUCTIONS[template_key]

    system_prompt = "Return valid JSON only. Do not include markdown code fences."
    user_prompt = (
        f"Summarize this article in {output_lang} and return JSON with keys:\n"
        "{\n"
        '  "summary": "string",\n'
        '  "key_points": ["string", "..."],\n'
        '  "keywords": ["string", "..."]\n'
        "}\n"
        f"Rules:\n- key_points length <= {max_points}\n"
        f"- keywords length <= {max_keywords}\n"
        "- Focus on factual and core ideas only\n"
        f"- Style instruction: {template_instruction}\n\n"
        f"Title: {title or 'N/A'}\n"
        f"Content:\n{text}"
    )

    try:
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
        except BadRequestError:
            # Some OpenAI-compatible gateways do not support response_format.
            completion = client.chat.completions.create(
                model=settings.model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
    except (APIConnectionError, APITimeoutError) as exc:
        raise ValueError(
            "无法连接到模型服务。请检查：1) Base URL 是否正确；2) 本机网络是否可访问该地址；"
            f"3) 当前模型服务是否可用。当前 Base URL: {settings.base_url or '默认官方地址'}。"
        ) from exc
    except AuthenticationError as exc:
        raise ValueError("鉴权失败，请检查 API Key 是否有效、是否有权限访问该模型。") from exc
    except NotFoundError as exc:
        raise ValueError(f"模型不存在或不可用：{settings.model}。请更换为平台支持的模型名。") from exc
    except RateLimitError as exc:
        raise ValueError("调用频率超限或余额不足，请稍后重试或检查账号额度。") from exc
    except APIStatusError as exc:
        raise ValueError(f"模型服务返回异常状态（HTTP {exc.status_code}）。请稍后重试。") from exc

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

    key_point_items = _build_key_point_items(key_points, text) if include_evidence else []

    return {
        "summary": summary,
        "key_points": key_points,
        "key_point_items": key_point_items,
        "keywords": keywords,
        "model": settings.model,
        "template": template_key,
    }
