# Release Guide

这个项目使用 Git tag 触发自动发布。

## 发布前检查

```bash
python -m ruff check src tests
python -m unittest discover -s tests -v
```

## 版本号规则

采用语义化版本：

- `v1.0.0`：重大更新或不兼容变更
- `v1.1.0`：新增功能，兼容旧版本
- `v1.1.1`：修复问题

## 发布步骤

1. 提交当前代码

```bash
git add .
git commit -m "chore: prepare release v1.0.0"
git push origin main
```

2. 打标签并推送

```bash
git tag v1.0.0
git push origin v1.0.0
```

3. 等待 GitHub Actions

- Workflow: `Release`
- 成功后会在 GitHub `Releases` 自动生成版本说明

## 回滚错误标签

如果标签打错：

```bash
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0
```
