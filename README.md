# URL 文章速览工具（CLI）

给一篇网页链接，输出可直接阅读的结果：

- 摘要
- 关键观点
- 关键词
- 每条观点对应的证据片段

支持 OpenAI 兼容接口（OpenAI / Gemini 兼容网关 / OpenRouter / OneAPI 等）。

## 快速开始（推荐）

### 1. 安装依赖（只做一次）

```bash
pip install -r requirements.txt
```

### 2. 配置服务（只做一次）

双击 [setup.bat](setup.bat)，按提示填写：

1. API Key
2. 模型名（例如 `gpt-4o-mini`、`gemini-2.5-flash`）
3. Base URL（官方 OpenAI 可留空；第三方兼容平台通常要填）

### 3. 开始使用

可选以下任一方式：

1. 双击 [start.bat](start.bat)  
会进入菜单，按步骤操作。
2. 双击 [summarize.bat](summarize.bat)  
粘贴单篇 URL，直接出结果。
3. 双击 [batch.bat](batch.bat)  
输入链接文件路径，批量处理。

## 批量文件格式

- 文本示例：[examples/urls.txt](examples/urls.txt)
- CSV 示例：[examples/urls_template.csv](examples/urls_template.csv)

CSV 默认优先读取 `url` 或 `link` 列。

## 输出模板

- `general`: 通用阅读
- `study`: 学习复盘
- `creator`: 内容创作
- `research`: 研究分析

## 命令行模式（进阶）

```bash
# 单篇
python src/cli.py summarize "https://example.com/article" --template study

# 批量
python src/cli.py batch examples/urls.txt --template research --format markdown --output outputs/batch.md
```

也兼容旧写法：

```bash
python src/cli.py "https://example.com/article"
```

## 常见问题

### 1) 提示未检测到 API Key

重新运行：

```bash
python src/cli.py setup
```

### 2) 我用 Gemini，Base URL 怎么填

```env
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
LLM_MODEL=gemini-2.5-flash
```

### 3) 有些链接批量失败

属于正常情况，常见原因：

1. 页面需要登录
2. 页面有访问限制
3. 链接本身无效

批量任务会继续处理其余链接，并在结果中记录失败原因。

## 项目结构

```text
src/
  cli.py
  content_extractor.py
  summarizer.py
examples/
  urls.txt
  urls_template.csv
setup.bat
start.bat
summarize.bat
batch.bat
```

更新记录见 [CHANGELOG.md](CHANGELOG.md)。

## License

MIT
