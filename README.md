# URL Article Summarizer CLI

输入文章 URL，输出：
- 摘要（Summary）
- 关键观点（Key Points）
- 关键词（Keywords）

适合快速阅读长文、做资料整理和选题调研。

## Features

- URL 抓取与正文提取
- 文本清洗
- 调用 OpenAI 兼容接口生成结构化总结
- 命令行使用，开箱即用

## Tech Stack

- Python
- requests
- BeautifulSoup4
- OpenAI Python SDK（兼容 OpenAI-style API）

## Project Structure

- `src/content_extractor.py`：抓取和正文提取
- `src/summarizer.py`：调用模型并结构化输出
- `src/cli.py`：命令行入口

## Quick Start

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 创建配置文件

```bash
copy .env.example .env
```

3. 编辑 `.env`

```env
LLM_API_KEY=your_key_here
LLM_BASE_URL=https://your-provider.example/v1
LLM_MODEL=gpt-4o-mini
```

说明：
- `LLM_API_KEY` 必填
- `LLM_MODEL` 必填（必须是你平台支持的模型名）
- `LLM_BASE_URL` 对多数第三方平台是必填

兼容旧变量（可选）：
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`

4. 运行

```bash
python src/cli.py "https://example.com/article"
```

可选参数：

```bash
python src/cli.py "https://example.com/article" --max-points 6
```

## Model Examples

```env
LLM_MODEL=gpt-4o-mini
# LLM_MODEL=gpt-4.1-mini
# LLM_MODEL=gemini-2.5-flash
```

如果提示 `model not found`，请从你的平台文档复制准确的模型名。

## License

MIT
