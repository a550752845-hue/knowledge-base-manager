# Knowledge Base Manager

[![CI](https://github.com/a550752845-hue/knowledge-base-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/a550752845-hue/knowledge-base-manager/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Knowledge Base Manager 是一个 **skill-only Codex plugin**。它把逐字稿、文稿、文档、网页、
笔记和混合来源整理为可追溯、可检索、可复用、可持续维护的 Markdown 或 Obsidian 知识库。

仓库同时提供：

- Codex marketplace/plugin 安装结构；
- 通过插件暴露的 `$transcript-knowledge-manager` Skill；
- 本地确定性 CLI，用于初始化、审计、索引、检索和来源完整性验证；
- Windows 与 Ubuntu 双平台 CI、Ruff、Coverage 和发布结构校验。

当前首个稳定版本为 `1.0.0`。

## 核心能力

- 先保护原始来源，再生成校正文、来源解析和可复用知识资产。
- 区分来源记录、来源主张、已验证事实、模型综合和生成内容。
- 用 `knowledge_role`、`truth_status`、`preservation`、`reuse_mode` 四轴约束知识用途。
- 生成并检查机器资产索引，按意图、行业、职责、主题和受众检索。
- 检查来源锚点、Obsidian 链接、冲突、时效、敏感度和 direct-use 条件。
- 对不可变来源建立哈希快照，并验证缺失、变更和新增文件。

## 环境要求

- Codex Desktop 或 Codex CLI，且 `codex plugin --help` 可用。
- Python 3.11 或更高版本，且可运行 `python -m pip`。
- 运行时 Python 包：PyYAML 和 jsonschema。
- Git 仅用于本地开发或贡献，不是普通安装的前置条件。

项目仅支持通过 marketplace 安装和使用完整插件；插件是唯一规范来源。

## 安装

### 远程 Marketplace 安装（推荐）

先为 Codex 将调用的 Python 安装两个运行时依赖，再从不可变发布标签注册远程 marketplace：

```bash
python -m pip install "PyYAML>=6.0,<7" "jsonschema>=4.20,<5"
codex plugin marketplace add a550752845-hue/knowledge-base-manager --ref v1.0.0
codex plugin add knowledge-base-manager@knowledge-base-manager
codex plugin list --json
```

Windows PowerShell 可使用 Python Launcher；其余 Codex 命令相同：

```powershell
py -3 -m pip install "PyYAML>=6.0,<7" "jsonschema>=4.20,<5"
codex plugin marketplace add a550752845-hue/knowledge-base-manager --ref v1.0.0
codex plugin add knowledge-base-manager@knowledge-base-manager
codex plugin list --json
```

如果 PowerShell 的执行策略阻止 `codex.ps1`，将上述 `codex` 替换为 `codex.cmd`。不要关闭系统
执行策略来绕过该限制。

安装后请新建一个 Codex 任务，并用 `$transcript-knowledge-manager` 完成一次只读审计或 `--help`
smoke，确认插件中的 Skill 已加载。

### 安全更新与重装

刷新当前远程发布快照后，重装插件以确保新任务加载刷新后的内容：

```bash
python -m pip install --upgrade "PyYAML>=6.0,<7" "jsonschema>=4.20,<5"
codex plugin marketplace upgrade knowledge-base-manager
codex plugin remove knowledge-base-manager@knowledge-base-manager
codex plugin add knowledge-base-manager@knowledge-base-manager
codex plugin list --json
```

升级到后续版本时，将目标标签代入 `--ref`，先移除已安装插件和旧 marketplace，再注册目标标签。
以下以当前 `v1.0.0` 为例：

```bash
codex plugin remove knowledge-base-manager@knowledge-base-manager
codex plugin marketplace remove knowledge-base-manager
codex plugin marketplace add a550752845-hue/knowledge-base-manager --ref v1.0.0
codex plugin add knowledge-base-manager@knowledge-base-manager
```

发布标签应保持不可变。重装完成后新建 Codex 任务，避免旧任务继续使用缓存的 Skill 定义。

### 本地 clone 开发

本地 clone 只用于开发和贡献。若已安装远程版本，先移除同名插件和 marketplace，再切换到本地
工作树：

```bash
git clone https://github.com/a550752845-hue/knowledge-base-manager.git
cd knowledge-base-manager
python -m pip install -r requirements-dev.txt
codex plugin remove knowledge-base-manager@knowledge-base-manager
codex plugin marketplace remove knowledge-base-manager
codex plugin marketplace add .
codex plugin add knowledge-base-manager@knowledge-base-manager
```

本地 marketplace 直接读取当前工作树，适合验证未发布改动；普通用户应使用远程发布标签。

### 从旧独立 Skill 迁移

如果此前手动安装过同名 standalone Skill，先完成插件安装，并在新任务中验证
`$transcript-knowledge-manager` 可正常调用。验证成功后，将旧独立 Skill 从 Codex 的 active
personal skills 目录移出、停用或删除，避免出现两个同名触发来源。此后插件是唯一规范来源。

这一步只清理旧的 Skill 安装，不迁移、不改写任何知识库。知识库来源保护和迁移边界仍按“安全”
与“CLI”章节执行。

## 调用方法

显式调用最稳定：

```text
用 $transcript-knowledge-manager 审计当前知识库，先保护原始来源，再修复索引和检索入口。
```

```text
用 $transcript-knowledge-manager 把这批逐字稿整理成可追溯知识库，并运行严格验证。
```

Skill 也允许隐式调用。可以直接说“整理知识库”“把逐字稿整理成知识库”“继续管理当前知识库”
等自然语言；需要确保调用确定性时，仍建议写出 `$transcript-knowledge-manager`。

完整工作契约见 [Skill 说明](plugins/knowledge-base-manager/skills/transcript-knowledge-manager/SKILL.md)。

## 架构

```text
knowledge-base-manager/
  .agents/plugins/marketplace.json
  plugins/knowledge-base-manager/
    .codex-plugin/plugin.json
    skills/transcript-knowledge-manager/
      SKILL.md
      agents/openai.yaml
      references/
      scripts/
      tests/
  scripts/validate_release.py
  .github/workflows/ci.yml
```

调用链分为两层：

1. Skill 层负责判断任务意图、来源保护边界、知识契约、写入范围和完成标准。
2. CLI 层执行可重复验证的初始化、审计、索引、检索和来源哈希操作。

插件不包含 MCP server、App 或 Hook。Marketplace 只把仓库中的 Skill bundle 暴露给 Codex，
避免引入额外服务和认证面。

## CLI

从仓库根目录查看统一入口：

```bash
python plugins/knowledge-base-manager/skills/transcript-knowledge-manager/scripts/kb.py --help
```

常用命令：

```bash
# 只生成初始化计划；加 --apply 后才创建缺失文件
python plugins/knowledge-base-manager/skills/transcript-knowledge-manager/scripts/kb.py init ./demo-vault --kb-id demo-vault --scope-type general

# 严格审计并检查资产索引
python plugins/knowledge-base-manager/skills/transcript-knowledge-manager/scripts/kb.py doctor ./demo-vault --check-index --strict

# 原子重建或验证资产索引
python plugins/knowledge-base-manager/skills/transcript-knowledge-manager/scripts/kb.py index ./demo-vault --write --summary
python plugins/knowledge-base-manager/skills/transcript-knowledge-manager/scripts/kb.py index ./demo-vault --check

# 按任务意图检索候选资产
python plugins/knowledge-base-manager/skills/transcript-knowledge-manager/scripts/kb.py query ./demo-vault --intent diagnose --query "当前知识库最需要修复什么" --top 12 --json

# 为不可变来源建立快照，并在后续验证
python plugins/knowledge-base-manager/skills/transcript-knowledge-manager/scripts/kb.py source snapshot --source ./sources --output ./source-integrity.json --apply
python plugins/knowledge-base-manager/skills/transcript-knowledge-manager/scripts/kb.py source verify --manifest ./source-integrity.json --check-new --json
```

`init` 默认 dry-run，不覆盖已有文件；索引写入是原子的；来源完整性清单必须写在来源目录之外。
`query` 只接受由本插件生成且与当前资产完全一致的索引；无归属、陈旧或元数据被篡改的索引会
整体拒绝查询，需要先运行 `index --write` 和 `index --check`，不会返回降级后的部分结果。

## 安全

- 确定性 CLI 在本地运行，不包含网络客户端、遥测或远程执行服务。
- Skill 会读写用户明确选择的知识库，实际权限仍由 Codex 宿主和当前工作区策略控制。
- 修改、移动、重命名或删除原始来源前必须确认。
- 批量移动、根范围变化、敏感度降低和 direct-use 提升都设有确认门槛。
- 不要把私密、受限或无授权内容提交到公开仓库、Issue、日志或测试夹具。
- 对高风险输入，先运行来源快照和 dry-run，再审查计划并执行写入。

漏洞报告方式见 [安全策略](SECURITY.md)。
本项目的数据处理边界见 [隐私说明](PRIVACY.md)。

## 开发与验证

安装开发依赖：

```bash
python -m pip install -r requirements-dev.txt
```

运行发布结构校验、Ruff 和完整端到端 smoke：

```bash
python scripts/validate_release.py
ruff check .
ruff format --check .
python scripts/smoke_e2e.py
```

运行单元测试与覆盖率时，需要把 Skill 的 `scripts` 目录加入 `PYTHONPATH`。CI 在 Windows 和
Ubuntu 上使用同一测试发现入口，并执行：

```bash
python -m coverage run --source=plugins/knowledge-base-manager/skills/transcript-knowledge-manager/scripts -m unittest discover -s plugins/knowledge-base-manager/skills/transcript-knowledge-manager/tests -t plugins/knowledge-base-manager/skills/transcript-knowledge-manager -p "test_*.py" -v
python -m coverage report --show-missing --fail-under=75
python -m coverage xml
```

`scripts/smoke_e2e.py` 在临时目录中串行验证
`init -> doctor -> index -> query -> source snapshot/verify`，并确认原始来源哈希未变化、临时目录
已清理。CI 在 Windows 与 Ubuntu 上都运行这项 E2E 和 Coverage；同时用一组额外的 Ubuntu
任务验证当前 Python 3.14，避免完整平台与版本笛卡尔积造成重复。CI 还会通过 `py_compile`
编译所有 Python 文件。

```bash
python plugins/knowledge-base-manager/skills/transcript-knowledge-manager/scripts/kb.py --help
python scripts/smoke_e2e.py
```

`coverage.xml`、`.coverage`、Python 字节码和缓存均为生成物，不应提交。发布校验器会验证
plugin、marketplace、Skill、JSON/YAML、引用、版本、README 安装信息和泄漏风险。

贡献流程见 [CONTRIBUTING.md](CONTRIBUTING.md)，版本记录见 [CHANGELOG.md](CHANGELOG.md)。

## 许可证

本项目采用 [MIT License](LICENSE)，该许可证同时作为本地开源插件的使用条款。版权所有者为 chen。
