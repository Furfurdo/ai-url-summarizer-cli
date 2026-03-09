import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

from content_extractor import extract_article_text
from summarizer import load_runtime_settings, summarize_text


def _is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _build_text_output(result: dict, title: str, url: str) -> str:
    lines = [
        f"标题: {title or '未获取到标题'}",
        f"链接: {url}",
        "",
        "=== 摘要 ===",
        result["summary"],
        "",
        "=== 关键观点 ===",
    ]
    for idx, point in enumerate(result["key_points"], start=1):
        lines.append(f"{idx}. {point}")

    lines.extend(
        [
            "",
            "=== 关键词 ===",
            ", ".join(result["keywords"]),
            "",
            f"模型: {result['model']}",
        ]
    )
    return "\n".join(lines)


def _build_markdown_output(result: dict, title: str, url: str) -> str:
    lines = [
        f"# {title or '文章总结'}",
        "",
        f"- Source: {url}",
        f"- Model: {result['model']}",
        "",
        "## Summary",
        result["summary"],
        "",
        "## Key Points",
    ]
    for point in result["key_points"]:
        lines.append(f"- {point}")

    lines.extend(["", "## Keywords", ", ".join(result["keywords"])])
    return "\n".join(lines)


def run_setup(force: bool = False) -> int:
    env_path = Path(".env")
    if env_path.exists() and not force:
        answer = input("检测到已有 .env，是否覆盖？(y/N): ").strip().lower()
        if answer not in {"y", "yes"}:
            print("已取消。")
            return 0

    print("=== 首次配置向导 ===")
    print("说明：支持任意 OpenAI 兼容接口。")
    print("如果你使用官方 OpenAI，Base URL 可留空。")
    print("如果你使用 Gemini/OpenRouter/OneAPI 等，请填写对应兼容地址。")

    api_key = ""
    while not api_key:
        api_key = input("1) 请输入 API Key: ").strip()
        if not api_key:
            print("API Key 不能为空，请重新输入。")

    model = input("2) 请输入模型名（默认 gpt-4o-mini）: ").strip() or "gpt-4o-mini"
    base_url = input("3) 请输入兼容 Base URL（可留空）: ").strip()

    lines = [
        "# Universal LLM settings (OpenAI-compatible API)",
        f"LLM_API_KEY={api_key}",
        f"LLM_MODEL={model}",
        f"LLM_BASE_URL={base_url}",
        "",
        "# Examples:",
        "# LLM_MODEL=gpt-4o-mini",
        "# LLM_MODEL=gpt-4.1-mini",
        "# LLM_MODEL=gemini-2.5-flash",
        "# LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai",
        "# LLM_BASE_URL=https://api.openai.com/v1",
    ]
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\n配置已写入: {env_path.resolve()}")
    print("你现在可以运行：python src/cli.py \"https://example.com/article\"")
    return 0


def run_summarize(args: argparse.Namespace) -> int:
    if not _is_valid_url(args.url):
        print("链接格式不正确，请使用 http(s) 开头的完整 URL。")
        return 1

    if args.max_points < 3:
        print("参数错误：--max-points 不能小于 3。")
        return 1

    if args.max_keywords < 3:
        print("参数错误：--max-keywords 不能小于 3。")
        return 1

    try:
        load_runtime_settings()
    except Exception as exc:
        print(str(exc))
        print("下一步：运行 `python src/cli.py setup` 完成配置。")
        return 1

    try:
        print("正在抓取网页内容...")
        title, text = extract_article_text(args.url, max_chars=args.max_chars)
        if not text.strip():
            print("提取失败：该页面未获取到可读正文。")
            return 1

        print("正在生成总结...")
        result = summarize_text(
            text=text,
            title=title,
            max_points=args.max_points,
            max_keywords=args.max_keywords,
            language=args.lang,
        )
    except Exception as exc:
        print(f"运行失败：{exc}")
        return 1

    payload = {
        "url": args.url,
        "title": title,
        "summary": result["summary"],
        "key_points": result["key_points"],
        "keywords": result["keywords"],
        "model": result["model"],
    }

    if args.format == "json":
        output = json.dumps(payload, ensure_ascii=False, indent=2)
    elif args.format == "markdown":
        output = _build_markdown_output(result, title=title, url=args.url)
    else:
        output = _build_text_output(result, title=title, url=args.url)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output + "\n", encoding="utf-8")
        print(f"已输出到文件: {output_path.resolve()}")
    else:
        print("")
        print(output)

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="URL 文章总结工具（支持 OpenAI 兼容接口）",
    )
    subparsers = parser.add_subparsers(dest="command")

    setup_parser = subparsers.add_parser("setup", help="首次配置向导")
    setup_parser.add_argument(
        "--force",
        action="store_true",
        help="强制覆盖已有 .env",
    )

    summarize_parser = subparsers.add_parser("summarize", help="总结指定 URL")
    summarize_parser.add_argument("url", help="文章链接（http/https）")
    summarize_parser.add_argument("--max-points", type=int, default=5, help="关键观点上限，默认 5")
    summarize_parser.add_argument("--max-keywords", type=int, default=8, help="关键词上限，默认 8")
    summarize_parser.add_argument(
        "--lang",
        choices=["zh", "en"],
        default="zh",
        help="输出语言：zh 或 en",
    )
    summarize_parser.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="输出格式，默认 text",
    )
    summarize_parser.add_argument(
        "--max-chars",
        type=int,
        default=12000,
        help="传给模型的正文最大字符数，默认 12000",
    )
    summarize_parser.add_argument("--output", help="输出到文件路径（可选）")

    return parser


def _normalize_argv(argv: list[str]) -> list[str]:
    if len(argv) <= 1:
        return argv

    first = argv[1]
    known = {"setup", "summarize", "-h", "--help"}
    if first in known:
        return argv

    # Backward compatibility:
    # python src/cli.py "https://example.com/article"
    return [argv[0], "summarize", *argv[1:]]


def main() -> int:
    argv = _normalize_argv(sys.argv)
    parser = build_parser()
    args = parser.parse_args(argv[1:])

    if args.command == "setup":
        return run_setup(force=args.force)

    if args.command == "summarize":
        return run_summarize(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
