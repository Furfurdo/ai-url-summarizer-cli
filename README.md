# 文章链接总结工具（CLI）

这个工具做一件事：输入文章链接，输出摘要、关键观点、关键词。

## 1. 安装

```bash
pip install -r requirements.txt
```

## 2. 配置

先复制配置模板：

```bash
copy .env.example .env
```

然后编辑 `.env`：

```env
LLM_API_KEY=你的平台key
LLM_BASE_URL=你的兼容地址/v1
LLM_MODEL=你的模型名
```

说明：
- `LLM_API_KEY` 必填
- `LLM_BASE_URL` 建议填写（Gemini、OpenRouter 等通常都要）
- `LLM_MODEL` 必须是平台实际支持的模型名

兼容旧变量（可不改）：
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`

## 3. 运行

```bash
python src/cli.py "https://文章链接"
```

限制关键观点数量：

```bash
python src/cli.py "https://文章链接" --max-points 6
```

## 4. 模型示例（可直接抄）

通用起步：

```env
LLM_MODEL=gpt-4o-mini
```

质量优先：

```env
LLM_MODEL=gpt-4.1-mini
```

Gemini 常用：

```env
LLM_MODEL=gemini-2.5-flash
```

提示：如果报 `model not found`，去你平台文档里复制准确模型名覆盖即可。
