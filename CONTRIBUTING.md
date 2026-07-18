# 贡献指南

感谢你改进 Knowledge Base Manager。提交变更前，请先阅读本指南和 [安全策略](SECURITY.md)。

## 开发环境

需要 Python 3.11 或更高版本。建议使用独立虚拟环境：

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

激活虚拟环境的命令因操作系统和 Shell 而异。

## 变更原则

- 保持插件为 skill-only，除非提案明确说明新增服务面的必要性和安全影响。
- 不要破坏原始来源保护、truth status、reuse mode、索引原子写入或路径边界。
- 新增 CLI 行为时同步增加测试和用户文档。
- 测试夹具必须使用合成数据，不得包含真实客户信息、访问令牌或私有路径。
- Manifest、marketplace 与 Changelog 的发布版本必须一致。

## 本地检查

至少运行：

```bash
ruff check .
ruff format --check .
python scripts/validate_release.py
python scripts/smoke_e2e.py
```

单元测试和 Coverage 的完整命令见 [README](README.md#开发与验证)。测试入口要求
`plugins/knowledge-base-manager/skills/transcript-knowledge-manager/scripts` 位于 `PYTHONPATH`。

完整测试与覆盖率门槛：

```bash
python -m coverage run --source=plugins/knowledge-base-manager/skills/transcript-knowledge-manager/scripts -m unittest discover -s plugins/knowledge-base-manager/skills/transcript-knowledge-manager/tests -t plugins/knowledge-base-manager/skills/transcript-knowledge-manager -p "test_*.py" -v
python -m coverage report --show-missing --fail-under=75
python -m coverage xml
```

`scripts/smoke_e2e.py` 使用临时知识库走通初始化、严格审计、索引、检索和来源快照/验证，不会在
仓库中留下 `.release-smoke`。Windows PowerShell 可将 `python` 换成 `py -3`。

## Pull Request

- 每个 Pull Request 聚焦一个可审查目标。
- 说明行为变化、兼容性、安全影响和验证结果。
- 确认没有提交 `coverage.xml`、`.coverage`、`__pycache__`、`.pyc` 或本地知识库内容。
- CI 必须在 Windows 和 Ubuntu 上通过。
- 用户可见变化应写入 `CHANGELOG.md` 的对应版本。

提交 Pull Request 即表示你同意按本仓库的 MIT License 授权该贡献。
