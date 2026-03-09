import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from publish_adapter import build_channel_draft


class PublishAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sample = {
            "title": "测试标题",
            "summary": "先定场景，再定指标，最后迭代。",
            "key_points": ["明确用户问题", "搭最小可用版本", "用数据迭代"],
            "keywords": ["效率", "总结", "内容"],
        }
        self.url = "https://example.com/article"

    def test_none_channel_returns_empty(self) -> None:
        self.assertEqual(build_channel_draft("none", self.sample, self.url), "")

    def test_xiaohongshu_contains_key_sections(self) -> None:
        text = build_channel_draft("xiaohongshu", self.sample, self.url)
        self.assertIn("小红书发布稿", text)
        self.assertIn("标题备选", text)
        self.assertIn("原文链接", text)

    def test_wechat_contains_key_sections(self) -> None:
        text = build_channel_draft("wechat", self.sample, self.url)
        self.assertIn("公众号草稿", text)
        self.assertIn("导语", text)
        self.assertIn("参考链接", text)

    def test_tweet_contains_key_sections(self) -> None:
        text = build_channel_draft("tweet", self.sample, self.url)
        self.assertIn("Thread 草稿", text)
        self.assertIn("Tweet 1/3", text)
        self.assertIn(self.url, text)


if __name__ == "__main__":
    unittest.main()
