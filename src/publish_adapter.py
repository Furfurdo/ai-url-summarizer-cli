from typing import Dict, List

CHANNEL_CHOICES = ["none", "xiaohongshu", "wechat", "tweet"]


def _safe_title(title: str, fallback: str = "这篇文章") -> str:
    value = (title or "").strip()
    return value if value else fallback


def _safe_summary(summary: str) -> str:
    value = (summary or "").strip()
    return value if value else "这篇内容信息密度很高，值得花 3 分钟做一次重点梳理。"


def _first_points(key_points: List[str], limit: int = 3) -> List[str]:
    points = [p.strip() for p in key_points if p and p.strip()]
    return points[:limit] if points else ["先抓结论，再看证据，最后落实到行动。"]


def _format_tags(keywords: List[str], fallback: str) -> str:
    if not keywords:
        return fallback
    clean = [str(k).strip() for k in keywords if str(k).strip()]
    if not clean:
        return fallback
    normalized = [k.replace(" ", "") for k in clean[:6]]
    return " ".join([f"#{k}" for k in normalized if k])


def _format_points(points: List[str]) -> List[str]:
    return [f"{idx}. {point}" for idx, point in enumerate(points, start=1)]


def _shorten(text: str, limit: int) -> str:
    value = " ".join((text or "").split())
    if len(value) <= limit:
        return value
    return f"{value[:limit].rstrip()}..."


def _build_xiaohongshu(title: str, summary: str, points: List[str], tags: str, url: str) -> str:
    short_summary = _shorten(summary, 100)
    lines = [
        "【小红书发布稿｜可直接改写】",
        "",
        "标题备选",
        f"1) {title}：我会反复看的 3 个关键点",
        f"2) 读完《{title}》，这 3 条最值得立刻用起来",
        f"3) {title}：30 秒先看结论，再决定要不要精读",
        "",
        "开场",
        f"如果你只看 30 秒，先记住这句：{short_summary}",
        "",
        "正文",
        "我从这篇内容里筛出了 3 个最值得马上落地的点：",
    ]
    lines.extend(_format_points(points))
    lines.extend(
        [
            "",
            "你可以先挑 1 条，今天就试一次，效果会比收藏更明显。",
            "",
            "互动引导",
            "你最想先执行哪一条？评论区回我，我补充对应案例。",
            "",
            "推荐标签",
            tags,
            "",
            f"原文链接：{url}",
        ]
    )
    return "\n".join(lines)


def _build_wechat(title: str, summary: str, points: List[str], url: str) -> str:
    short_summary = _shorten(summary, 120)
    lines = [
        "【公众号草稿｜可直接扩写】",
        "",
        f"标题建议：{title}，最值得先抓住的 3 个重点",
        "",
        "导语",
        f"先说结论：{short_summary}",
        "如果你时间有限，先看下面 3 个重点，再决定是否精读全文。",
        "",
        "正文框架",
    ]
    for idx, point in enumerate(points, start=1):
        lines.append(f"小节 {idx}｜{point}")
        lines.append(f"扩写建议：补 1 个真实案例，把“{point}”讲透。")
    lines.extend(
        [
            "",
            "结尾",
            "真正有用的阅读，不在于读了多少，而在于能不能转成行动。",
            "建议今天先选 1 条执行，明天复盘结果。",
            "",
            f"参考链接：{url}",
        ]
    )
    return "\n".join(lines)


def _build_tweet(title: str, summary: str, points: List[str], tags: str, url: str) -> str:
    short_title = _shorten(title, 70)
    short_summary = _shorten(summary, 130)
    lines = [
        "【推文 Thread 草稿】",
        "",
        "Tweet 1/3",
        f"刚读完《{short_title}》。一句话总结：{short_summary}",
        "",
        "Tweet 2/3",
        "最值得记住的 3 点：",
    ]
    lines.extend(_format_points(points))
    lines.extend(
        [
            "",
            "Tweet 3/3",
            f"原文：{url}",
            tags,
        ]
    )
    return "\n".join(lines)


def build_channel_draft(channel: str, result: Dict[str, object], url: str) -> str:
    if channel == "none":
        return ""

    title = _safe_title(str(result.get("title", "")))
    summary = _safe_summary(str(result.get("summary", "")))
    points = _first_points(result.get("key_points", []))  # type: ignore[arg-type]
    keywords = result.get("keywords", [])
    keyword_list = keywords if isinstance(keywords, list) else []

    if channel == "xiaohongshu":
        tags = _format_tags(keyword_list, "#信息整理 #效率工具 #学习方法")
        return _build_xiaohongshu(title=title, summary=summary, points=points, tags=tags, url=url)

    if channel == "wechat":
        return _build_wechat(title=title, summary=summary, points=points, url=url)

    if channel == "tweet":
        tags = _format_tags(keyword_list, "#AI #Learning #Productivity")
        return _build_tweet(title=title, summary=summary, points=points, tags=tags, url=url)

    return ""
