# AI URL Summarizer CLI

一个面向普通用户的文章总结工具。  
输入文章 URL，自动输出：

- 摘要（Summary）
- 关键观点（Key Points）
- 关键词（Keywords）

支持任意 **OpenAI 兼容接口**（OpenAI、Gemini 兼容网关、OpenRouter、OneAPI 等）。

## 1. 功能亮点

- 自动抓取网页正文并清洗文本
- 支持多种输出格式：`text` / `json` / `markdown`
- 可直接输出到文件，方便沉淀到知识库
- 保留旧命令习惯：`python src/cli.py "<URL>"`

## 2. 安装

```bash
pip install -r requirements.txt
```

## 3. 3 分钟上手

### 第一步：首次配置

```bash
python src/cli.py setup
```

按提示填写：

1. `API Key`
2. `模型名`（如 `gpt-4o-mini`、`gemini-2.5-flash`）
3. `Base URL`（官方 OpenAI 可留空，其他兼容平台一般要填）

### 第二步：总结文章

```bash
python src/cli.py "https://example.com/article"
```

## 4. 常用命令

```bash
# 显式调用 summarize
python src/cli.py summarize "https://example.com/article"

# 限制关键观点条数
python src/cli.py "https://example.com/article" --max-points 6

# 输出英文
python src/cli.py "https://example.com/article" --lang en

# 输出 JSON
python src/cli.py "https://example.com/article" --format json

# 输出 Markdown 并写入文件
python src/cli.py "https://example.com/article" --format markdown --output outputs/result.md
```

## 5. 配置说明

项目使用以下环境变量（写在 `.env`）：

- `LLM_API_KEY`: 必填，服务密钥
- `LLM_MODEL`: 必填，模型名称
- `LLM_BASE_URL`: 选填，兼容接口地址

示例：

```env
LLM_API_KEY=your_api_key_here
LLM_MODEL=gemini-2.5-flash
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
```

也兼容旧变量（可选）：

- `OPENAI_API_KEY`
- `OPENAI_MODEL`
- `OPENAI_BASE_URL`

## 6. 目录结构

```text
src/
  cli.py                # 命令行入口（setup/summarize）
  content_extractor.py  # 抓取与正文提取
  summarizer.py         # 调用 LLM 并输出结构化结果
```

## 7. 常见问题

### Q1: 运行时提示未检测到 API Key

运行：

```bash
python src/cli.py setup
```

### Q2: 我用 Gemini，Base URL 怎么填？

可使用 Gemini 的 OpenAI 兼容地址：

```env
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
```

模型名按你的平台实际支持填写，例如：

```env
LLM_MODEL=gemini-2.5-flash
```

### Q3: 文章无法提取

可能原因：

1. 页面有反爬限制
2. 需要登录后才能查看全文
3. URL 本身不可访问

可以先在浏览器无登录状态打开该 URL 自检。

## License

MIT
