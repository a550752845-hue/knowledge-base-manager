## 变更说明

说明本次变更解决的问题和用户可观察到的结果。

## 验证

- [ ] `ruff check .`
- [ ] `python scripts/validate_release.py`
- [ ] Skill 单元测试与 Coverage 通过
- [ ] `py_compile` 通过
- [ ] CLI smoke 通过

## 风险检查

- [ ] 未提交真实知识库内容、私有路径、密钥或令牌
- [ ] 未提交 `coverage.xml`、`.coverage`、`__pycache__` 或 `.pyc`
- [ ] 已说明原始来源、批量写入、隐私边界和兼容性影响
- [ ] 用户可见变化已记录到 `CHANGELOG.md`
