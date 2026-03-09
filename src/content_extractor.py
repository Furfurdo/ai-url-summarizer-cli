import re
from typing import Tuple

import requests
from bs4 import BeautifulSoup, Tag


def fetch_html(url: str, timeout: int = 20) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise ValueError("网页请求超时，请稍后重试。") from exc
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        raise ValueError(f"网页访问失败（HTTP {status}），请确认链接可公开访问。") from exc
    except requests.exceptions.RequestException as exc:
        raise ValueError("无法访问该链接，请检查网络或链接是否正确。") from exc

    response.encoding = response.apparent_encoding
    return response.text


def _clean_dom(soup: BeautifulSoup) -> None:
    for tag_name in [
        "script",
        "style",
        "noscript",
        "header",
        "footer",
        "nav",
        "aside",
        "form",
        "iframe",
        "svg",
    ]:
        for node in soup.find_all(tag_name):
            node.decompose()


def _pick_content_container(soup: BeautifulSoup) -> Tag:
    candidates = []

    for selector in ["article", "main", "[role='main']", ".content", ".post", ".article"]:
        for node in soup.select(selector):
            text = node.get_text(" ", strip=True)
            score = len(text)
            if score > 200:
                candidates.append((score + 500, node))

    for node in soup.find_all(["div", "section"]):
        text = node.get_text(" ", strip=True)
        score = len(text)
        if score > 400:
            candidates.append((score, node))

    if not candidates:
        return soup.body if soup.body else soup

    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def _normalize_text(raw_text: str) -> str:
    text = re.sub(r"\s+", " ", raw_text)
    text = re.sub(r"([\u3002\uff01\uff1f\uff1b.!?;])\s*", r"\1\n", text)
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line and len(line) > 1]
    return "\n".join(lines)


def extract_article_text(url: str, max_chars: int = 12000) -> Tuple[str, str]:
    html = fetch_html(url)
    soup = BeautifulSoup(html, "html.parser")
    _clean_dom(soup)

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    container = _pick_content_container(soup)
    text = container.get_text(" ", strip=True)
    text = _normalize_text(text)

    if len(text) > max_chars:
        text = text[:max_chars]

    return title, text
