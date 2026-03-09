# Contributing

感谢你愿意改进这个项目。

## 开发环境

```bash
pip install -r requirements.txt
pip install ruff
```

## 本地验证

```bash
python -m ruff check src tests
python -m unittest discover -s tests -v
```

## 提交规范

- 每次提交聚焦一个主题（功能、修复或文档）
- 提交前先通过 lint 和 tests
- 提交信息建议使用：
  - `feat: ...`
  - `fix: ...`
  - `docs: ...`
  - `refactor: ...`
  - `test: ...`

## Pull Request 建议

- 描述改动目标和影响范围
- 如果改了页面，请附关键截图
- 说明是否影响现有命令参数或输出格式
