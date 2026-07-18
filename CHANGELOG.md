# Changelog

本项目的显著变更记录在此文件中。版本号遵循 Semantic Versioning。

## [1.0.0] - 2026-07-15

### Added

- 首个公开稳定版 skill-only Codex plugin。
- 仓库级 Codex marketplace 与 `knowledge-base-manager` plugin manifest。
- `$transcript-knowledge-manager` Skill、知识契约参考资料和确定性本地 CLI。
- 初始化、知识库审计、资产索引、意图检索和来源完整性命令。
- 查询前对 skill-owned 索引执行完整规范对账，拒绝陈旧、无归属或被篡改的隐私与复用元数据。
- 统一 CLI 按需加载子命令，提供版本输出和缺失依赖的可执行修复提示。
- 跨平台一键端到端 smoke，覆盖初始化、审计、索引、检索和来源完整性闭环。
- 发布结构校验器，检查 manifests、JSON/YAML、引用、版本、泄漏和发布生成物。
- Windows 与 Ubuntu CI，覆盖 Ruff、Coverage、单元测试、`py_compile` 和 CLI smoke。
- 中文 README、贡献指南、安全策略、Issue 表单和 Pull Request 模板。
- 本地处理、无遥测的隐私说明和公开 manifest 隐私/条款 URL。

[1.0.0]: https://github.com/a550752845-hue/knowledge-base-manager/releases/tag/v1.0.0
