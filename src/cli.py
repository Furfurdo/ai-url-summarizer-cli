import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from content_extractor import extract_article_text
from summarizer import load_runtime_settings, summarize_text


TEMPLATE_CHOICES = ["general", "study", "creator", "research"]
FORMAT_CHOICES = ["text", "json", "markdown"]
APP_NAME = "文章速览工具"


def _is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _validate_runtime_args(args: argparse.Namespace) -> str | None:
    if args.max_points < 3:
        return "参数错误：--max-points 不能小于 3。"
    if args.max_keywords < 3:
        return "参数错误：--max-keywords 不能小于 3。"
    if args.max_chars < 1000:
        return "参数错误：--max-chars 不能小于 1000。"
    return None


def _load_urls_from_file(path: Path) -> list[str]:
    if not path.exists():
        raise ValueError(f"输入文件不存在：{path}")

    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                lowered = {name.lower(): name for name in reader.fieldnames}
                col = (
                    lowered.get("url")
                    or lowered.get("link")
                    or lowered.get("网址")
                    or lowered.get("链接")
                )
                if col:
                    raw_urls = [str(row.get(col, "")).strip() for row in reader]
                else:
                    first_col = reader.fieldnames[0]
                    raw_urls = [str(row.get(first_col, "")).strip() for row in reader]
            else:
                raw_urls = []
    else:
        lines = path.read_text(encoding="utf-8").splitlines()
        raw_urls = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]

    urls: list[str] = []
    seen = set()
    for url in raw_urls:
        if url in seen:
            continue
        seen.add(url)
        urls.append(url)
    return urls


def _summarize_single_url(url: str, args: argparse.Namespace) -> dict:
    if not _is_valid_url(url):
        raise ValueError("链接格式不正确，请使用 http(s) 开头的完整 URL。")

    title, text = extract_article_text(url, max_chars=args.max_chars)
    if not text.strip():
        raise ValueError("该页面未获取到可读正文。")

    result = summarize_text(
        text=text,
        title=title,
        max_points=args.max_points,
        max_keywords=args.max_keywords,
        language=args.lang,
        summary_template=args.template,
        include_evidence=not args.no_evidence,
    )
    return {
        "status": "ok",
        "url": url,
        "title": title,
        "summary": result["summary"],
        "key_points": result["key_points"],
        "key_point_items": result.get("key_point_items", []),
        "keywords": result["keywords"],
        "model": result["model"],
        "template": result["template"],
    }


def _build_text_output(result: dict) -> str:
    lines = [
        f"标题: {result.get('title') or '未获取到标题'}",
        f"链接: {result['url']}",
        f"模板: {result.get('template', 'general')}",
        "",
        "=== 摘要 ===",
        result["summary"],
        "",
        "=== 关键观点 ===",
    ]

    items = result.get("key_point_items") or []
    if items:
        for item in items:
            lines.append(f"{item['index']}. {item['point']}")
            lines.append(f"   证据: {item['evidence']}")
    else:
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


def _build_markdown_sections(result: dict, level: str = "##") -> list[str]:
    lines = [
        f"{level} 摘要",
        result["summary"],
        "",
        f"{level} 关键观点",
    ]

    items = result.get("key_point_items") or []
    if items:
        for item in items:
            lines.append(f"{item['index']}. **{item['point']}**")
            lines.append(f"   - 证据: {item['evidence']}")
    else:
        for point in result["key_points"]:
            lines.append(f"- {point}")

    lines.extend(["", f"{level} 关键词", ", ".join(result["keywords"])])
    return lines


def _build_markdown_output(result: dict) -> str:
    lines = [
        f"# {result.get('title') or '文章总结'}",
        "",
        f"- 来源: {result['url']}",
        f"- 模型: {result['model']}",
        f"- 模板: {result.get('template', 'general')}",
        "",
    ]
    lines.extend(_build_markdown_sections(result, level="##"))
    return "\n".join(lines)


def _build_batch_text_output(results: list[dict]) -> str:
    lines = [f"批量总结完成，共 {len(results)} 条。", ""]
    ok_count = sum(1 for item in results if item.get("status") == "ok")
    fail_count = len(results) - ok_count
    lines.append(f"成功: {ok_count} | 失败: {fail_count}")
    lines.append("")

    for idx, item in enumerate(results, start=1):
        lines.append(f"===== [{idx}/{len(results)}] {item['url']} =====")
        if item.get("status") != "ok":
            lines.append("状态: 失败")
            lines.append(f"原因: {item.get('error', '未知错误')}")
            lines.append("")
            continue
        lines.append(_build_text_output(item))
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _build_batch_markdown_output(results: list[dict]) -> str:
    lines = ["# 批量总结报告", ""]
    ok_count = sum(1 for item in results if item.get("status") == "ok")
    fail_count = len(results) - ok_count
    lines.append(f"- 总数: {len(results)}")
    lines.append(f"- 成功: {ok_count}")
    lines.append(f"- 失败: {fail_count}")
    lines.append("")

    for idx, item in enumerate(results, start=1):
        lines.append(f"## {idx}. {item.get('title') or item['url']}")
        if item.get("status") != "ok":
            lines.append("- 状态: 失败")
            lines.append(f"- 原因: {item.get('error', '未知错误')}")
            lines.append("")
            continue
        lines.append(f"- 来源: {item['url']}")
        lines.append(f"- 模型: {item['model']}")
        lines.append(f"- 模板: {item.get('template', 'general')}")
        lines.append("")
        lines.extend(_build_markdown_sections(item, level="###"))
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _output_results(output: str, output_path: str | None) -> None:
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(output, encoding="utf-8")
        print(f"已输出到文件: {path.resolve()}")
    else:
        print(output)


def _to_output_path(raw: str) -> str | None:
    value = raw.strip()
    return value or None


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
    print("如果你使用 Gemini/OpenRouter/OneAPI 等，请填写兼容地址。")

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
    print("你现在可以运行：python src/cli.py")
    return 0


def run_summarize(args: argparse.Namespace) -> int:
    validation_error = _validate_runtime_args(args)
    if validation_error:
        print(validation_error)
        return 1

    try:
        load_runtime_settings()
    except Exception as exc:
        print(str(exc))
        print("下一步：运行 `python src/cli.py setup` 完成配置。")
        return 1

    try:
        print("正在抓取网页内容并生成总结...")
        payload = _summarize_single_url(args.url, args)
    except Exception as exc:
        print(f"运行失败：{exc}")
        return 1

    if args.format == "json":
        output = json.dumps(payload, ensure_ascii=False, indent=2)
    elif args.format == "markdown":
        output = _build_markdown_output(payload)
    else:
        output = _build_text_output(payload)

    _output_results(output + ("\n" if not output.endswith("\n") else ""), args.output)
    return 0


def run_batch(args: argparse.Namespace) -> int:
    validation_error = _validate_runtime_args(args)
    if validation_error:
        print(validation_error)
        return 1

    try:
        load_runtime_settings()
    except Exception as exc:
        print(str(exc))
        print("下一步：运行 `python src/cli.py setup` 完成配置。")
        return 1

    input_path = Path(args.input)
    try:
        urls = _load_urls_from_file(input_path)
    except Exception as exc:
        print(f"读取输入文件失败：{exc}")
        return 1

    if not urls:
        print("输入文件中没有可用链接。")
        return 1

    print(f"开始批量总结，共 {len(urls)} 条链接...")
    results: list[dict] = []
    for idx, url in enumerate(urls, start=1):
        print(f"[{idx}/{len(urls)}] {url}")
        try:
            item = _summarize_single_url(url, args)
        except Exception as exc:
            item = {"status": "error", "url": url, "error": str(exc)}
        results.append(item)

    if args.format == "json":
        output = json.dumps(results, ensure_ascii=False, indent=2) + "\n"
    elif args.format == "markdown":
        output = _build_batch_markdown_output(results)
    else:
        output = _build_batch_text_output(results)

    _output_results(output, args.output)
    return 0


def _ask_choice(title: str, options: list[str], default_idx: int = 0) -> str:
    print(title)
    for idx, option in enumerate(options, start=1):
        mark = " (默认)" if idx - 1 == default_idx else ""
        print(f"{idx}. {option}{mark}")
    raw = input("请输入选项编号: ").strip()
    if not raw:
        return options[default_idx]
    try:
        picked = int(raw)
    except ValueError:
        return options[default_idx]
    if picked < 1 or picked > len(options):
        return options[default_idx]
    return options[picked - 1]


def _default_output_name(prefix: str, extension: str) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return str(Path("outputs") / f"{prefix}_{stamp}.{extension}")


def _interactive_mode() -> int:
    while True:
        print("")
        print(f"{APP_NAME}")
        print("请选择操作：")
        print("1. 首次配置或更新配置")
        print("2. 总结一篇文章（粘贴链接）")
        print("3. 批量总结（读取 txt/csv 文件）")
        print("4. 查看示例文件路径")
        print("5. 退出")

        action = input("输入编号并回车: ").strip()

        if action == "1":
            run_setup(force=False)
            continue

        if action == "2":
            url = input("请输入文章链接: ").strip()
            if not url:
                print("未输入链接。")
                continue

            template = _ask_choice("选择总结模板：", TEMPLATE_CHOICES, default_idx=0)
            out_format = _ask_choice("选择输出格式：", FORMAT_CHOICES, default_idx=0)
            want_output_file = input("是否保存到文件？(Y/n): ").strip().lower()
            output = None
            if want_output_file not in {"n", "no"}:
                ext_map = {"text": "txt", "json": "json", "markdown": "md"}
                suggested = _default_output_name("summary", ext_map[out_format])
                custom = input(f"输出文件路径（留空使用 {suggested}）: ").strip()
                output = _to_output_path(custom) or suggested

            args = argparse.Namespace(
                url=url,
                max_points=5,
                max_keywords=8,
                lang="zh",
                template=template,
                format=out_format,
                max_chars=12000,
                no_evidence=False,
                output=output,
            )
            run_summarize(args)
            continue

        if action == "3":
            default_input = "examples/urls.txt"
            raw_input_path = input(f"请输入文件路径（留空使用 {default_input}）: ").strip()
            input_path = raw_input_path or default_input

            template = _ask_choice("选择总结模板：", TEMPLATE_CHOICES, default_idx=0)
            out_format = _ask_choice("选择输出格式：", FORMAT_CHOICES, default_idx=2)
            ext_map = {"text": "txt", "json": "json", "markdown": "md"}
            suggested = _default_output_name("batch", ext_map[out_format])
            custom = input(f"输出文件路径（留空使用 {suggested}）: ").strip()
            output = _to_output_path(custom) or suggested

            args = argparse.Namespace(
                input=input_path,
                max_points=5,
                max_keywords=8,
                lang="zh",
                template=template,
                format=out_format,
                max_chars=12000,
                no_evidence=False,
                output=output,
            )
            run_batch(args)
            continue

        if action == "4":
            print("示例文本: examples/urls.txt")
            print("示例表格: examples/urls_template.csv")
            continue

        if action == "5":
            print("已退出。")
            return 0

        print("无效选项，请输入 1-5。")


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--max-points", type=int, default=5, help="关键观点上限，默认 5")
    parser.add_argument("--max-keywords", type=int, default=8, help="关键词上限，默认 8")
    parser.add_argument(
        "--lang",
        choices=["zh", "en"],
        default="zh",
        help="输出语言：zh 或 en",
    )
    parser.add_argument(
        "--template",
        choices=TEMPLATE_CHOICES,
        default="general",
        help="总结模板：general/study/creator/research",
    )
    parser.add_argument(
        "--format",
        choices=FORMAT_CHOICES,
        default="text",
        help="输出格式，默认 text",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=12000,
        help="传给模型的正文最大字符数，默认 12000",
    )
    parser.add_argument(
        "--no-evidence",
        action="store_true",
        help="不展示观点证据片段",
    )
    parser.add_argument("--output", help="输出到文件路径（可选）")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="URL 文章总结工具（支持 OpenAI 兼容接口；无参数运行会进入交互菜单）",
    )
    subparsers = parser.add_subparsers(dest="command")

    setup_parser = subparsers.add_parser("setup", help="首次配置向导")
    setup_parser.add_argument(
        "--force",
        action="store_true",
        help="强制覆盖已有 .env",
    )

    summarize_parser = subparsers.add_parser("summarize", help="总结单条 URL")
    summarize_parser.add_argument("url", help="文章链接（http/https）")
    _add_common_options(summarize_parser)

    batch_parser = subparsers.add_parser("batch", help="批量总结（从 txt/csv 读 URL）")
    batch_parser.add_argument("input", help="输入文件路径（.txt 或 .csv）")
    _add_common_options(batch_parser)

    return parser


def _normalize_argv(argv: list[str]) -> list[str]:
    if len(argv) <= 1:
        return argv

    first = argv[1]
    known = {"setup", "summarize", "batch", "-h", "--help"}
    if first in known:
        return argv

    # Backward compatibility:
    # python src/cli.py "https://example.com/article"
    return [argv[0], "summarize", *argv[1:]]


def main() -> int:
    if len(sys.argv) <= 1:
        if sys.stdin.isatty():
            return _interactive_mode()
        parser = build_parser()
        parser.print_help()
        return 0

    argv = _normalize_argv(sys.argv)
    parser = build_parser()
    args = parser.parse_args(argv[1:])

    if args.command == "setup":
        return run_setup(force=args.force)

    if args.command == "summarize":
        return run_summarize(args)

    if args.command == "batch":
        return run_batch(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
