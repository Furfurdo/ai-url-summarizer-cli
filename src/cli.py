import argparse
import sys

from content_extractor import extract_article_text
from summarizer import summarize_text


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="文章链接总结工具（CLI）")
    parser.add_argument("url", help="文章链接")
    parser.add_argument(
        "--max-points",
        type=int,
        default=5,
        help="关键观点条数上限（默认 5）",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.max_points < 3:
        print("参数错误：--max-points 不能小于 3")
        return 1

    try:
        print("正在抓取并提取正文...")
        title, text = extract_article_text(args.url)
        if not text.strip():
            print("提取失败：未获得可读的正文内容。")
            return 1

        print("正在生成总结...")
        result = summarize_text(text=text, title=title, max_points=args.max_points)
    except Exception as exc:
        print(f"运行失败：{exc}")
        return 1

    print("\n=== 摘要 ===")
    print(result["summary"])

    print("\n=== 关键观点 ===")
    for idx, point in enumerate(result["key_points"], start=1):
        print(f"{idx}. {point}")

    print("\n=== 关键词 ===")
    print(", ".join(result["keywords"]))

    print(f"\n（模型：{result['model']}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
