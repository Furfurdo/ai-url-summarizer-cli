import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import web_app


class WebAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.history_file = Path(self.temp_dir.name) / "web_history.json"
        self.old_history_file = web_app.HISTORY_FILE
        web_app.HISTORY_FILE = self.history_file

        app = web_app.create_app()
        self.client = app.test_client()

    def tearDown(self) -> None:
        web_app.HISTORY_FILE = self.old_history_file
        self.temp_dir.cleanup()

    def test_home_page_available(self) -> None:
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("文章速览 Web".encode("utf-8"), resp.data)

    def test_invalid_url_returns_friendly_error(self) -> None:
        resp = self.client.post(
            "/summarize",
            data={"url": "bad-url", "template": "general", "channel": "none"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("链接格式不正确".encode("utf-8"), resp.data)

    def test_clear_history_works(self) -> None:
        web_app._save_history(  # noqa: SLF001 - deliberate test setup
            [
                {
                    "created_at": "2026-03-09 18:00:00",
                    "url": "https://example.com",
                    "title": "Demo",
                    "template": "general",
                    "channel": "none",
                    "summary": "这是一个摘要。",
                    "summary_preview": "这是一个摘要。",
                    "markdown": "# demo",
                    "channel_draft": "",
                }
            ]
        )
        self.assertTrue(self.history_file.exists())
        resp = self.client.post("/clear_history", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        data = json.loads(self.history_file.read_text(encoding="utf-8"))
        self.assertEqual(data, [])

    def test_export_history_returns_markdown_attachment(self) -> None:
        web_app._save_history(  # noqa: SLF001 - deliberate test setup
            [
                {
                    "created_at": "2026-03-09 18:00:00",
                    "url": "https://example.com",
                    "title": "Demo",
                    "template": "general",
                    "channel": "none",
                    "summary": "这是一个摘要。",
                    "summary_preview": "这是一个摘要。",
                    "markdown": "# demo",
                    "channel_draft": "",
                }
            ]
        )
        resp = self.client.get("/export_history")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/markdown", resp.content_type)
        content_disposition = resp.headers.get("Content-Disposition", "")
        self.assertIn("attachment; filename=", content_disposition)
        self.assertIn("# 文章速览历史导出".encode("utf-8"), resp.data)


if __name__ == "__main__":
    unittest.main()
