# 更新记录

## 2026-03-09

- 新增无参数交互菜单：`python src/cli.py` 直接进入菜单。
- 新增 Windows 一键脚本：
  - `setup.bat`
  - `start.bat`
  - `summarize.bat`
  - `batch.bat`
- 新增批量 CSV 模板：`examples/urls_template.csv`。
- 新增总结模板能力：`general / study / creator / research`。
- 新增“关键观点证据片段”输出，便于核对来源。
- 新增发布渠道文案适配：`xiaohongshu / wechat / tweet`。
- 新增网页端：输入链接、查看历史、一键复制 Markdown。
- 新增网页端启动脚本：`web.bat`。
- 优化发布渠道文案为可直接发布的成稿风格，减少“模板说明腔”。
- 重构网页端体验：主操作区 + 历史侧栏、回填历史、清空历史、复制摘要/文案/Markdown。
- 网页端新增输入快捷操作（示例链接/清空链接）与前端链接校验，降低误操作。
- 网页端新增历史导出 Markdown 与摘要预览，便于内容复用和归档。
- 发布渠道文案二次优化：改为更自然的“可直接改写/扩写”文案结构。
- 仓库工程化升级：新增 GitHub CI（Python 3.10/3.11 + ruff + unittest）。
- 新增开源协作文档：`CONTRIBUTING.md`、`SECURITY.md`、Issue/PR 模板。
- README 重写为产品化首页结构，突出价值、上手路径与质量标准。
- 新增 README 演示图（Web 首页与渠道草稿），增强仓库展示效果。
- 新增自动发布工作流：推送 `v*.*.*` 标签自动创建 GitHub Release。
- 新增发布指南与路线图文档：`docs/RELEASE.md`、`docs/ROADMAP.md`。
- 新增 `Roadmap Item` Issue 模板，便于产品需求持续管理。
- 重写 README，改为用户优先的上手说明。
