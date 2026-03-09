import argparse
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from flask import Flask, Response, redirect, render_template_string, request, url_for

from content_extractor import extract_article_text
from publish_adapter import CHANNEL_CHOICES, build_channel_draft
from summarizer import summarize_text

TEMPLATE_CHOICES = ["general", "study", "creator", "research"]
TEMPLATE_LABELS = {
    "general": "通用阅读",
    "study": "学习复盘",
    "creator": "内容创作",
    "research": "研究分析",
}
APP_ROOT = Path(__file__).resolve().parents[1]
HISTORY_FILE = APP_ROOT / "outputs" / "web_history.json"
MAX_HISTORY = 30

TEMPLATE_TIPS = {
    "general": "通用阅读：平衡信息密度与可读性。",
    "study": "学习复盘：更强调概念和可记忆点。",
    "creator": "内容创作：更强调角度、表达和可引用观点。",
    "research": "研究分析：更强调论据质量与方法边界。",
}

CHANNEL_TIPS = {
    "none": "不生成发布稿，仅保留总结结果。",
    "xiaohongshu": "生成小红书可直接改写的成稿框架。",
    "wechat": "生成公众号可直接扩写的文章框架。",
    "tweet": "生成推文线程（Thread）三段式文案。",
}

CHANNEL_LABELS = {
    "none": "不生成",
    "xiaohongshu": "小红书",
    "wechat": "公众号",
    "tweet": "推文",
}


PAGE_TEMPLATE = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>文章速览 Web</title>
  <style>
    :root {
      --bg: #f5f7fb;
      --card: #ffffff;
      --line: #e5e7eb;
      --text: #0f172a;
      --muted: #64748b;
      --primary: #0f766e;
      --primary-2: #155e75;
      --danger: #b91c1c;
      --ok: #166534;
      --warn: #92400e;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--text);
      background:
        radial-gradient(circle at 85% 0%, #dbeafe 0, transparent 35%),
        radial-gradient(circle at 0% 30%, #ecfeff 0, transparent 36%),
        var(--bg);
      font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    }
    .container {
      max-width: 1200px;
      margin: 0 auto;
      padding: 18px 14px 36px;
    }
    .hero {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 14px 16px;
      margin-bottom: 12px;
    }
    .hero h1 {
      margin: 0 0 6px;
      font-size: 30px;
      letter-spacing: 0.3px;
    }
    .hero .sub {
      margin: 0;
      color: var(--muted);
    }
    .layout {
      display: grid;
      grid-template-columns: 1.4fr 0.85fr;
      gap: 12px;
    }
    .card {
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 14px;
      margin-bottom: 12px;
    }
    .card h2 {
      margin: 0 0 10px;
      font-size: 20px;
    }
    label {
      display: block;
      margin: 10px 0 6px;
      font-weight: 600;
    }
    input, select, button, textarea {
      width: 100%;
      border: 1px solid #d1d5db;
      border-radius: 10px;
      padding: 10px 12px;
      font-size: 15px;
      background: #fff;
    }
    .row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }
    .inline-actions {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
      margin-top: 8px;
    }
    .tip {
      font-size: 13px;
      color: var(--muted);
      margin-top: 6px;
    }
    .msg {
      margin-top: 10px;
      padding: 9px 11px;
      border-radius: 9px;
      font-size: 14px;
    }
    .msg.ok {
      background: #f0fdf4;
      color: var(--ok);
      border: 1px solid #bbf7d0;
    }
    .msg.err {
      background: #fef2f2;
      color: var(--danger);
      border: 1px solid #fecaca;
    }
    .btn {
      cursor: pointer;
      border: 0;
      color: #fff;
      background: var(--primary);
      font-weight: 600;
      margin-top: 10px;
    }
    .btn:hover { background: #0d5f59; }
    .btn:disabled {
      opacity: 0.7;
      cursor: not-allowed;
    }
    .btn-secondary {
      background: var(--primary-2);
    }
    .btn-secondary:hover {
      background: #164e63;
    }
    .btn-light {
      background: #f1f5f9;
      color: #334155;
      border: 1px solid #cbd5e1;
    }
    .btn-light:hover {
      background: #e2e8f0;
    }
    .btn-danger {
      background: var(--danger);
    }
    .btn-danger:hover {
      background: #991b1b;
    }
    .result-meta {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 10px;
    }
    .pill {
      border: 1px solid #d1d5db;
      border-radius: 999px;
      padding: 3px 10px;
      font-size: 12px;
      color: #475569;
      background: #fff;
    }
    pre {
      white-space: pre-wrap;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      padding: 10px;
      margin: 0;
    }
    textarea {
      min-height: 160px;
      resize: vertical;
    }
    .actions {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
      margin-top: 8px;
      margin-bottom: 10px;
    }
    .history-head {
      display: grid;
      grid-template-columns: 1fr auto;
      align-items: center;
      gap: 8px;
    }
    .history-head-actions {
      display: grid;
      grid-template-columns: auto auto;
      align-items: center;
      gap: 8px;
    }
    .btn-mini {
      width: auto;
      padding: 8px 10px;
      margin: 0;
      text-decoration: none;
      display: inline-block;
      text-align: center;
      font-size: 13px;
    }
    .history-list {
      max-height: 68vh;
      overflow: auto;
      padding-right: 2px;
    }
    .history-tools {
      display: grid;
      grid-template-columns: 1fr 120px;
      gap: 8px;
      margin-bottom: 8px;
    }
    .history-item {
      border: 1px solid #e5e7eb;
      border-radius: 10px;
      padding: 10px;
      margin-top: 8px;
      background: #fcfcfd;
    }
    .history-title {
      font-weight: 600;
      margin-bottom: 4px;
    }
    .history-meta {
      font-size: 12px;
      color: var(--muted);
      margin-bottom: 8px;
    }
    .history-preview {
      font-size: 13px;
      color: #334155;
      margin-bottom: 8px;
      line-height: 1.45;
    }
    .history-actions {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
    .history-actions button {
      margin-top: 0;
    }
    details summary {
      cursor: pointer;
      color: #334155;
      font-size: 13px;
    }
    .loading {
      display: none;
      font-size: 13px;
      color: var(--muted);
      margin-top: 8px;
    }
    .loading.show {
      display: block;
    }
    @media (max-width: 980px) {
      .layout { grid-template-columns: 1fr; }
      .history-list { max-height: none; }
      .actions { grid-template-columns: 1fr; }
      .row { grid-template-columns: 1fr; }
      .inline-actions { grid-template-columns: 1fr; }
      .history-actions { grid-template-columns: 1fr; }
      .history-tools { grid-template-columns: 1fr; }
      .history-head-actions { grid-template-columns: 1fr; }
    }
  </style>
  <script>
    function isValidHttpUrl(value) {
      const url = (value || "").trim();
      if (!url) return false;
      try {
        const parsed = new URL(url);
        return parsed.protocol === "http:" || parsed.protocol === "https:";
      } catch (e) {
        return false;
      }
    }
    function copyText(text) {
      const value = text || "";
      navigator.clipboard.writeText(value).then(function() {
        alert("已复制到剪贴板");
      }).catch(function() {
        alert("复制失败，请手动复制");
      });
    }
    function copyFromId(id) {
      const el = document.getElementById(id);
      if (!el) return;
      copyText(el.value || el.textContent || "");
    }
    function applyHistory(item) {
      const urlEl = document.getElementById("url");
      const tplEl = document.getElementById("template");
      const channelEl = document.getElementById("channel");
      if (urlEl) urlEl.value = item.url || "";
      if (tplEl) tplEl.value = item.template || "general";
      if (channelEl) channelEl.value = item.channel || "none";
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
    function bindSubmitLoading() {
      const form = document.getElementById("mainForm");
      const btn = document.getElementById("submitBtn");
      const loading = document.getElementById("loading");
      const urlEl = document.getElementById("url");
      if (!form || !btn || !loading) return;
      form.addEventListener("submit", function(event) {
        const url = urlEl ? urlEl.value : "";
        if (!isValidHttpUrl(url)) {
          event.preventDefault();
          alert("请输入完整链接，例如 https://example.com/article");
          return;
        }
        btn.disabled = true;
        btn.innerText = "生成中...";
        loading.classList.add("show");
      });
    }
    function fillDemoUrl() {
      const urlEl = document.getElementById("url");
      if (!urlEl) return;
      urlEl.value = "https://example.com/article";
      urlEl.focus();
    }
    function clearUrlInput() {
      const urlEl = document.getElementById("url");
      if (!urlEl) return;
      urlEl.value = "";
      urlEl.focus();
    }
    function confirmClearHistory() {
      return window.confirm("确认清空历史记录吗？此操作不可恢复。");
    }
    function filterHistory() {
      const keywordEl = document.getElementById("historySearch");
      const channelEl = document.getElementById("historyChannel");
      const kw = (keywordEl ? keywordEl.value : "").toLowerCase().trim();
      const channel = channelEl ? channelEl.value : "all";
      const items = document.querySelectorAll(".history-item");
      items.forEach(function(item) {
        const text = (item.dataset.search || "").toLowerCase();
        const itemChannel = item.dataset.channel || "none";
        const matchKw = !kw || text.includes(kw);
        const matchChannel = channel === "all" || channel === itemChannel;
        item.style.display = (matchKw && matchChannel) ? "" : "none";
      });
    }
    function bindHistoryFilter() {
      const keywordEl = document.getElementById("historySearch");
      const channelEl = document.getElementById("historyChannel");
      if (keywordEl) keywordEl.addEventListener("input", filterHistory);
      if (channelEl) channelEl.addEventListener("change", filterHistory);
    }
    window.addEventListener("DOMContentLoaded", bindSubmitLoading);
    window.addEventListener("DOMContentLoaded", bindHistoryFilter);
  </script>
</head>
<body>
  <div class="container">
    <section class="hero">
      <h1>文章速览 Web</h1>
      <p class="sub">输入链接后，系统会输出摘要、关键观点、Markdown 与发布渠道文案。</p>
    </section>

    <div class="layout">
      <main>
        <section class="card">
          <h2>生成内容</h2>
          <form id="mainForm" method="post" action="/summarize">
            <label for="url">文章链接</label>
            <input id="url" name="url" placeholder="https://example.com/article" value="{{ form.url }}" />
            <div class="inline-actions">
              <button class="btn btn-light" type="button" onclick="fillDemoUrl()">填入示例链接</button>
              <button class="btn btn-light" type="button" onclick="clearUrlInput()">清空链接</button>
            </div>

            <div class="row">
              <div>
                <label for="template">总结模板</label>
                <select id="template" name="template">
                  {% for item in templates %}
                  <option value="{{ item }}" {% if form.template == item %}selected{% endif %}>{{ template_labels.get(item, item) }}</option>
                  {% endfor %}
                </select>
                <div class="tip">{{ template_tips.get(form.template, "") }}</div>
              </div>
              <div>
                <label for="channel">发布渠道</label>
                <select id="channel" name="channel">
                  {% for item in channels %}
                  <option value="{{ item }}" {% if form.channel == item %}selected{% endif %}>{{ channel_labels.get(item, item) }}</option>
                  {% endfor %}
                </select>
                <div class="tip">{{ channel_tips.get(form.channel, "") }}</div>
              </div>
            </div>

            <button id="submitBtn" class="btn" type="submit">生成结果</button>
            <div id="loading" class="loading">正在抓取正文并调用模型，请稍候...</div>
          </form>

          {% if message %}
          <div class="msg {{ 'ok' if ok else 'err' }}">{{ message }}</div>
          {% if diagnostics %}
          <div class="card" style="margin-top:10px; margin-bottom:0; border-style:dashed;">
            <h3 style="margin-top:0;">排查建议</h3>
            <ul style="margin:6px 0 0; padding-left:18px;">
              {% for item in diagnostics %}
              <li>{{ item }}</li>
              {% endfor %}
            </ul>
          </div>
          {% endif %}
          {% endif %}
        </section>

        {% if result %}
        <section class="card" id="resultCard">
          <h2>本次结果</h2>
          <div class="result-meta">
            <span class="pill">标题：{{ result.title or '未获取到标题' }}</span>
            <span class="pill">模板：{{ template_labels.get(result.template, result.template) }}</span>
            <span class="pill">渠道：{{ channel_labels.get(result.channel, result.channel) }}</span>
          </div>
          <div class="tip">来源：{{ result.url }}</div>

          <div class="actions">
            <button class="btn btn-secondary" type="button" onclick="copyText({{ result.summary|tojson }})">复制摘要</button>
            <button class="btn btn-secondary" type="button" onclick="copyFromId('current_md')">复制 Markdown</button>
            <button class="btn btn-secondary" type="button" onclick="copyText({{ (result.channel_draft or '')|tojson }})">复制渠道文案</button>
          </div>

          <h3>摘要</h3>
          <pre>{{ result.summary }}</pre>

          <h3>关键观点</h3>
          <pre>{% for p in result.key_points %}{{ loop.index }}. {{ p }}
{% endfor %}</pre>

          {% if result.channel_draft %}
          <h3>发布渠道文案</h3>
          <pre>{{ result.channel_draft }}</pre>
          {% endif %}

          <h3>Markdown</h3>
          <textarea id="current_md" rows="14">{{ result.markdown }}</textarea>
        </section>
        <script>
          window.addEventListener("DOMContentLoaded", function() {
            const el = document.getElementById("resultCard");
            if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
          });
        </script>
        {% endif %}
      </main>

      <aside>
        <section class="card">
          <div class="history-head">
            <h2 style="margin:0;">历史记录</h2>
            <div class="history-head-actions">
              <a class="btn btn-secondary btn-mini" href="/export_history">导出 Markdown</a>
              <form method="post" action="/clear_history" onsubmit="return confirmClearHistory()">
                <button class="btn btn-danger btn-mini" type="submit">清空历史</button>
              </form>
            </div>
          </div>
          <p class="tip">保留最近 {{ max_history }} 条，可回填、筛选、导出。</p>
          <div class="history-tools">
            <input id="historySearch" placeholder="搜索标题/链接..." />
            <select id="historyChannel">
              <option value="all">全部渠道</option>
              {% for item in channels %}
              <option value="{{ item }}">{{ channel_labels.get(item, item) }}</option>
              {% endfor %}
            </select>
          </div>
          <div class="history-list">
            {% if history %}
              {% for item in history %}
              <div class="history-item"
                   data-channel="{{ item.channel }}"
                   data-search="{{ (item.title or '') ~ ' ' ~ (item.url or '') ~ ' ' ~ (item.summary_preview or '') }}">
                <div class="history-title">{{ item.title or '未获取到标题' }}</div>
                <div class="history-meta">{{ item.created_at }} · {{ channel_labels.get(item.channel, item.channel) }}</div>
                <div class="history-meta">{{ item.url }}</div>
                <div class="history-preview">{{ item.summary_preview or '暂无摘要预览' }}</div>
                <div class="history-actions">
                  <button class="btn btn-secondary" type="button" onclick='applyHistory({{ item|tojson }})'>回填到输入框</button>
                  <button class="btn btn-secondary" type="button" onclick='copyText({{ item.markdown|tojson }})'>复制 Markdown</button>
                </div>
                {% if item.channel_draft %}
                <details style="margin-top:8px;">
                  <summary>查看渠道文案</summary>
                  <pre style="margin-top:8px;">{{ item.channel_draft }}</pre>
                </details>
                {% endif %}
              </div>
              {% endfor %}
            {% else %}
              <p class="tip">暂无历史记录。</p>
            {% endif %}
          </div>
        </section>
      </aside>
    </div>
  </div>
</body>
</html>
"""


def _is_valid_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _build_markdown(result: dict) -> str:
    lines = [
        f"# {result.get('title') or '文章总结'}",
        "",
        f"- 来源: {result['url']}",
        f"- 模板: {result['template']}",
        f"- 渠道: {result['channel']}",
        "",
        "## 摘要",
        result["summary"],
        "",
        "## 关键观点",
    ]
    for idx, point in enumerate(result["key_points"], start=1):
        lines.append(f"{idx}. {point}")
    lines.extend(["", "## 关键词", ", ".join(result["keywords"])])
    if result.get("channel_draft"):
        lines.extend(
            [
                "",
                f"## 发布渠道文案（{result['channel']}）",
                "",
                "```text",
                result["channel_draft"],
                "```",
            ]
        )
    return "\n".join(lines)


def _preview_text(text: str, limit: int = 90) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[:limit].rstrip()}..."


def _build_history_export_markdown(history: list[dict]) -> str:
    lines = [
        "# 文章速览历史导出",
        "",
        f"- 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 记录数量: {len(history)}",
        "",
    ]
    if not history:
        lines.append("暂无可导出的历史记录。")
        return "\n".join(lines) + "\n"

    for idx, item in enumerate(history, start=1):
        title = item.get("title") or "未获取到标题"
        channel = item.get("channel") or "none"
        lines.extend(
            [
                f"## {idx}. {title}",
                f"- 时间: {item.get('created_at', '-')}",
                f"- 链接: {item.get('url', '-')}",
                f"- 模板: {item.get('template', '-')}",
                f"- 渠道: {channel}",
                "",
            ]
        )
        summary = str(item.get("summary", "")).strip()
        if summary:
            lines.extend(["### 摘要", summary, ""])

        markdown = str(item.get("markdown", "")).strip()
        if markdown:
            lines.extend(["### Markdown", "```markdown", markdown, "```", ""])

        channel_draft = str(item.get("channel_draft", "")).strip()
        if channel_draft:
            lines.extend(["### 渠道文案", "```text", channel_draft, "```", ""])

    return "\n".join(lines).rstrip() + "\n"


def _load_history() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    try:
        raw = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            return raw
    except json.JSONDecodeError:
        pass
    return []


def _save_history(items: list[dict]) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(
        json.dumps(items[:MAX_HISTORY], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _default_form(url: str = "", template: str = "general", channel: str = "none") -> dict:
    return {
        "url": url,
        "template": template if template in TEMPLATE_CHOICES else "general",
        "channel": channel if channel in CHANNEL_CHOICES else "none",
    }


def _create_result(url: str, template: str, channel: str) -> dict:
    title, text = extract_article_text(url, max_chars=12000)
    if not text.strip():
        raise ValueError("未获取到可读正文，请尝试其他链接。")

    raw = summarize_text(
        text=text,
        title=title,
        max_points=5,
        max_keywords=8,
        language="zh",
        summary_template=template,
        include_evidence=True,
    )
    result = {
        "url": url,
        "title": title,
        "summary": raw["summary"],
        "key_points": raw["key_points"],
        "keywords": raw["keywords"],
        "template": template,
        "channel": channel,
        "channel_draft": build_channel_draft(channel, result={"title": title, **raw}, url=url),
    }
    result["markdown"] = _build_markdown(result)
    return result


def _diagnose_error(message: str) -> list[str]:
    text = (message or "").lower()
    tips: list[str] = []
    if "连接" in message or "connection" in text or "timeout" in text:
        tips.extend(
            [
                "检查网络是否可访问模型服务地址（例如 googleapis.com）。",
                "确认 .env 里的 LLM_BASE_URL 与服务商文档一致。",
                "稍后重试，避免网络抖动导致临时失败。",
            ]
        )
    elif "鉴权" in message or "unauthorized" in text or "authentication" in text:
        tips.extend(
            [
                "确认 API Key 没有过期，并且没有多余空格。",
                "确认当前账号有访问该模型的权限。",
            ]
        )
    elif "模型" in message or "model" in text or "not found" in text:
        tips.extend(
            [
                "检查 LLM_MODEL 是否为平台支持的模型名。",
                "优先从服务商控制台复制模型名，避免手打错误。",
            ]
        )
    elif "链接格式" in message:
        tips.append("请粘贴以 http:// 或 https:// 开头的完整链接。")
    else:
        tips.extend(["请先确认链接可访问，再检查模型配置是否正确。", "如持续失败，可切换模型重试。"])
    return tips


def create_app() -> Flask:
    app = Flask(__name__)

    def render_page(
        *,
        result: dict | None,
        message: str,
        ok: bool,
        form: dict,
    ):
        diagnostics = _diagnose_error(message) if (message and not ok) else []
        return render_template_string(
            PAGE_TEMPLATE,
            result=result,
            message=message,
            ok=ok,
            diagnostics=diagnostics,
            templates=TEMPLATE_CHOICES,
            template_labels=TEMPLATE_LABELS,
            channels=CHANNEL_CHOICES,
            channel_labels=CHANNEL_LABELS,
            template_tips=TEMPLATE_TIPS,
            channel_tips=CHANNEL_TIPS,
            form=form,
            history=_load_history(),
            max_history=MAX_HISTORY,
        )

    @app.get("/")
    def home():
        return render_page(result=None, message="", ok=True, form=_default_form())

    @app.post("/clear_history")
    def clear_history():
        _save_history([])
        return redirect(url_for("home"))

    @app.get("/export_history")
    def export_history():
        history = _load_history()
        content = _build_history_export_markdown(history)
        filename = f"web_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        response = Response(content, mimetype="text/markdown; charset=utf-8")
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response

    @app.post("/summarize")
    def summarize_page():
        url = (request.form.get("url") or "").strip()
        template = (request.form.get("template") or "general").strip()
        channel = (request.form.get("channel") or "none").strip()
        form = _default_form(url=url, template=template, channel=channel)

        if not _is_valid_url(url):
            return render_page(
                result=None,
                message="链接格式不正确，请输入 http(s) 开头的完整链接。",
                ok=False,
                form=form,
            )

        try:
            result = _create_result(url=url, template=form["template"], channel=form["channel"])
            history = _load_history()
            history.insert(
                0,
                {
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "url": result["url"],
                    "title": result["title"],
                    "template": result["template"],
                    "channel": result["channel"],
                    "summary": result["summary"],
                    "summary_preview": _preview_text(result["summary"]),
                    "markdown": result["markdown"],
                    "channel_draft": result["channel_draft"],
                },
            )
            _save_history(history)
            return render_page(
                result=result,
                message="已生成完成。你可以直接复制摘要、Markdown 或渠道文案。",
                ok=True,
                form=form,
            )
        except Exception as exc:
            return render_page(
                result=None,
                message=f"生成失败：{exc}",
                ok=False,
                form=form,
            )

    return app


def main() -> int:
    parser = argparse.ArgumentParser(description="文章速览 Web 页面")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()

    app = create_app()
    app.run(host=args.host, port=args.port, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
