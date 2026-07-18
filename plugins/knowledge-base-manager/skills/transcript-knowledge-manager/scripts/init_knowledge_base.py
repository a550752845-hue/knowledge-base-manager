"""Plan or initialize a lifecycle-based knowledge-base root without overwriting files."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat as stat_module
import sys
from datetime import date
from pathlib import Path
from typing import Any

from build_asset_index import render_jsonl
from kb_common import exclusive_write_text, parse_json, read_text, stable_json


ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
DIRECTORIES = (
    "00-AI入口",
    "10-原始证据",
    "20-来源解析",
    "30-知识对象",
    "40-可执行资产",
    "50-证据验证",
    "60-输出成品",
    "_meta",
)
CONFLICT_ACTIONS = frozenset(("conflict-directory", "conflict-manifest", "conflict-path"))


class InitializationConflict(RuntimeError):
    """Raised when another filesystem entry wins an exclusive initialization path."""


def lexical_absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path.expanduser())))


def is_junction(path: Path) -> bool:
    checker = getattr(path, "is_junction", None)
    if checker is not None:
        try:
            return bool(checker())
        except OSError:
            return False

    path_checker = getattr(os.path, "isjunction", None)
    if path_checker is not None:
        try:
            return bool(path_checker(path))
        except OSError:
            return False

    if os.name != "nt":
        return False
    try:
        result = path.lstat()
    except OSError:
        return False
    attributes = getattr(result, "st_file_attributes", 0)
    reparse_tag = getattr(result, "st_reparse_tag", 0)
    return bool(
        attributes & getattr(stat_module, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        and reparse_tag == getattr(stat_module, "IO_REPARSE_TAG_MOUNT_POINT", -1)
    )


def path_kind(path: Path) -> str:
    if path.is_symlink():
        return "symlink"
    if is_junction(path):
        return "junction"
    if path.is_dir():
        return "directory"
    if path.is_file():
        return "file"
    if os.path.lexists(os.fspath(path)):
        return "other"
    return "missing"


def manifest_payload(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "schema_version": 3,
        "knowledge_base_id": args.kb_id,
        "name": args.name or args.kb_id,
        "scope": {
            "type": args.scope_type,
            "industries": args.industry,
            "responsibilities": args.responsibility,
        },
        "paths": {
            "ai_entry": "00-AI入口/AI首读.md",
            "asset_index": "00-AI入口/资产索引.jsonl",
            "management_rules": "_meta/知识库管理规则.md",
            "recent_context": "_meta/最近上下文.md",
            "source_registry_human": "_meta/来源注册表.md",
            "source_registry_machine": "_meta/来源注册表.jsonl",
            "maintenance_log": "_meta/维护日志.md",
        },
        "role_paths": {
            "ai_entry": "00-AI入口",
            "source": "10-原始证据",
            "source_analysis": "20-来源解析",
            "knowledge": "30-知识对象",
            "execution": "40-可执行资产",
            "evidence": "50-证据验证",
            "output": "60-输出成品",
            "management": "_meta",
        },
        "source_roots": [],
        "freshness_policy": {"high_days": 30, "medium_days": 180, "low_days": 3650},
    }


def markdown_files(args: argparse.Namespace) -> dict[str, str]:
    industries = "、".join(args.industry) or "无（通用或尚未归类）"
    responsibilities = "、".join(args.responsibility) or "无（通用或尚未归类）"
    today = date.today().isoformat()
    return {
        "00-AI入口/AI首读.md": f"""# AI 首读入口

## 本库身份

- ID：`{args.kb_id}`
- 名称：{args.name or args.kb_id}
- 范围：`{args.scope_type}`
- 行业：{industries}
- 职责：{responsibilities}

## 调用路线

| 任务 | 先查 | 再读 | 何时回原始来源 |
| --- | --- | --- | --- |
| 诊断/决策 | `资产索引.jsonl` 中的 model、principle、procedure | 证据验证 | 结论冲突、高风险或证据薄弱 |
| 生成/执行 | talk-track、procedure | model、evidence | 需要精确事实或直接引用 |
| 解释/研究 | logic-map、claim、fact | evidence、source-profile | 需要原文语境或核验 |
| 引用/核验 | evidence、来源注册表 | 原始来源 | 始终回到精确锚点 |

## 核心入口

- 机器资产索引：[[资产索引.jsonl]]
- AI 调用规则：[[_meta/AI调用索引]]
- 来源注册表：[[_meta/来源注册表]]
- 最近上下文：[[_meta/最近上下文]]
- 管理规则：[[_meta/知识库管理规则]]

## 不可越过的边界

- 原始材料只读；分析写入衍生文件。
- 逻辑图只解释来源完整逻辑，不认证事实，也不直接充当话术。
- 来源主张、已核事实、模型综合和生成输出必须分开。
- 话术默认需要改编；只有满足审核合同的资产才可直接使用。
""",
        "_meta/知识库管理规则.md": f"""# 知识库管理规则

## 身份与范围

- 知识库 ID：`{args.kb_id}`
- schema：3
- scope：`{args.scope_type}`
- 行业：{industries}
- 职责：{responsibilities}

机器可读配置以 `knowledge-base.json` 为准。本文件记录给人和大模型阅读的管理约定。

## 目录角色

| 角色 | 当前路径 | 约束 |
| --- | --- | --- |
| AI 入口 | `00-AI入口/` | 只放路由、索引和队列 |
| 原始证据 | `10-原始证据/` | 原件或外部只读指针 |
| 来源解析 | `20-来源解析/` | 完整逻辑图、结构图、来源画像 |
| 知识对象 | `30-知识对象/` | 事实、主张、原则、模型、方法 |
| 可执行资产 | `40-可执行资产/` | SOP、脚本、话术、提示词、模板 |
| 证据验证 | `50-证据验证/` | 引文、案例、数据、反例、验证记录 |
| 输出成品 | `60-输出成品/` | 一次性草稿、审核稿、交付物 |
| 元管理 | `_meta/` | 配置、注册表、上下文、日志、健康状态 |

## 知识合同

1. 原始材料不可覆盖、改名、移动或注释，除非用户明确授权。
2. 每个深度处理来源先形成一份完整逻辑图，再决定是否提炼资产。
3. 逻辑、原话、事实、模型、SOP、话术和输出是不同资产，不因目录相近而混用。
4. 生成输出默认不自动晋升为知识。
5. `direct-use` 必须满足受众、场景、目标、变量、边界、权限、合规、测试和时效合同。
6. 最近上下文保持为短期交接快照；维护日志保留长期记录。

## 变更控制

- 可自动执行：新增来源登记、衍生逻辑图、候选资产、局部链接修复、索引重建、上下文与日志更新。
- 必须确认：修改原件、批量移动/重命名、改变顶层范围、合并知识库、降低隐私等级、覆盖冲突资产。
""",
        "_meta/AI调用索引.md": """# AI 调用索引

## 默认路线

1. 读取 `knowledge-base.json` 与 `最近上下文.md`。
2. 根据任务意图查询 `00-AI入口/资产索引.jsonl`。
3. 读取少量最匹配资产。
4. 只有在精确引用、事实核验、冲突、高风险或时效问题时回到证据和原始来源。

## 意图优先级

| 意图 | 优先资产 |
| --- | --- |
| 生成 | talk-track、procedure、model |
| 诊断 | model、principle、procedure |
| 决策 | model、procedure、fact、evidence |
| 解释 | principle、model、fact、logic-map |
| 研究 | logic-map、source-profile、claim、evidence |
| 核验/引用 | evidence、fact、source |

## 使用边界

- `source-claim` 必须归因；`verified-fact` 必须检查验证日期。
- `analyze-only` 不得直接复制成话术。
- `adapt-required` 必须按当前受众、场景和事实改写。
- `do-not-use` 只保留审计，不进入输出。
""",
        "_meta/来源注册表.md": """# 来源注册表

机器可读主表：`来源注册表.jsonl`。

| source_id | 标题 | 类型 | 作者/所有者 | 日期/版本 | 首选读取路径 | sensitivity | 状态 | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## 重复与版本关系

| source_id | 关系 | 相关 ID/路径 | 判断依据 | 处理 |
| --- | --- | --- | --- | --- |
""",
        "_meta/最近上下文.md": """# 最近上下文

本文件是有界交接快照，不是永久日志。只保留最近最影响下一次工作的内容。

## 最近完成

| 日期 | 动作 | 影响范围 | 关键变化 |
| --- | --- | --- | --- |

## 下次先读

| 场景 | 首读 | 再读 | 注意 |
| --- | --- | --- | --- |

## 当前待决

| 事项 | 风险 | 建议动作 |
| --- | --- | --- |
""",
        "_meta/维护日志.md": f"""# 维护日志

| 日期 | 动作 | 文件/范围 | 原因 | 验证 | 残余风险 |
| --- | --- | --- | --- | --- | --- |
| {today} | 初始化 schema-v3 知识库 | 全库 | 建立来源、知识、执行与检索合同 | 待运行 doctor | 尚无知识资产 |
""",
        "50-证据验证/模型成熟度.md": f"""---
schema_version: 3
id: management-model-maturity
type: management
knowledge_role: management
truth_status: user-preference
preservation: normalized
reuse_mode: reference-only
status: active
scope_type: {args.scope_type}
domains: []
industries: {json.dumps(args.industry, ensure_ascii=False)}
responsibilities: {json.dumps(args.responsibility, ensure_ascii=False)}
topics: [knowledge-governance]
source_ids: []
source_anchors: []
confidence: high
maturity: candidate
time_sensitivity: low
sensitivity: internal
created: {today}
updated: {today}
summary: 管理模型成熟度、证据缺口、反例和升级降级条件。
---
# 模型成熟度与证据缺口

| 资产 ID | 当前成熟度 | 证据强度 | 支持证据 | 反例/冲突 | 升级条件 | 降级/拆分触发 |
| --- | --- | --- | --- | --- | --- | --- |
""",
    }


def build_plan(
    root: Path, args: argparse.Namespace
) -> tuple[list[dict[str, str]], dict[Path, str]]:
    manifest = manifest_payload(args)
    files = markdown_files(args)
    files["_meta/knowledge-base.json"] = stable_json(manifest, pretty=True) + "\n"
    files["_meta/来源注册表.jsonl"] = ""
    files["00-AI入口/资产索引.jsonl"] = render_jsonl([])

    plan: list[dict[str, str]] = []
    payloads: dict[Path, str] = {}
    for directory in DIRECTORIES:
        path = root / directory
        kind = path_kind(path)
        if kind == "directory":
            action = "keep"
        elif kind == "missing":
            action = "create-directory"
        else:
            action = "conflict-directory"
        plan.append({"action": action, "path": directory})
    for relative, payload in files.items():
        path = root / relative
        kind = path_kind(path)
        if kind == "file":
            if relative == "_meta/knowledge-base.json":
                try:
                    existing = parse_json(read_text(path), str(path))
                except (OSError, UnicodeError, ValueError):
                    action = "conflict-manifest"
                else:
                    expected_scope = manifest["scope"]
                    current_scope = existing.get("scope", {}) if isinstance(existing, dict) else {}
                    compatible = (
                        isinstance(existing, dict)
                        and existing.get("schema_version") == 3
                        and existing.get("knowledge_base_id") == args.kb_id
                        and isinstance(current_scope, dict)
                        and current_scope.get("type") == expected_scope["type"]
                        and current_scope.get("industries", []) == expected_scope["industries"]
                        and current_scope.get("responsibilities", [])
                        == expected_scope["responsibilities"]
                    )
                    action = "keep-existing" if compatible else "conflict-manifest"
            else:
                action = "keep-identical" if read_text(path) == payload else "keep-existing"
        elif kind == "missing":
            action = "create-file"
            payloads[path] = payload
        else:
            action = "conflict-path"
        plan.append({"action": action, "path": relative})
    return plan, payloads


def result_payload(
    root: Path,
    args: argparse.Namespace,
    plan: list[dict[str, str]],
    status: str,
    *,
    message: str,
    created_files: int = 0,
) -> dict[str, Any]:
    return {
        "apply": args.apply,
        "created_files": created_files,
        "message": message,
        "ok": status in {"dry-run", "initialized"},
        "plan": plan,
        "root": str(root),
        "status": status,
    }


def emit_result(
    args: argparse.Namespace,
    payload: dict[str, Any],
    *,
    error: bool = False,
) -> None:
    if args.json:
        print(stable_json(payload, pretty=True))
        return
    for item in payload["plan"]:
        print(f"{item['action']:20} {item['path']}")
    print(payload["message"], file=sys.stderr if error else sys.stdout)


def validation_failure(
    args: argparse.Namespace, root: Path, message: str, plan: list[dict[str, str]] | None = None
) -> int:
    emit_result(
        args,
        result_payload(root, args, plan or [], "error", message=message),
        error=True,
    )
    return 2


def conflict_failure(
    args: argparse.Namespace, root: Path, plan: list[dict[str, str]], message: str
) -> int:
    emit_result(
        args,
        result_payload(root, args, plan, "conflict", message=message),
        error=True,
    )
    return 1


def ensure_directory(path: Path) -> None:
    try:
        path.mkdir()
    except FileExistsError:
        if path_kind(path) != "directory":
            raise InitializationConflict(f"Expected directory path is occupied: {path}") from None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Initialize a non-destructive schema-v3 knowledge-base root."
    )
    parser.add_argument("root", help="Target knowledge-base root")
    parser.add_argument("--kb-id", required=True, help="Stable lowercase knowledge-base ID")
    parser.add_argument("--name", help="Human-readable knowledge-base name")
    parser.add_argument(
        "--scope-type",
        choices=("general", "industry", "responsibility", "cross-domain", "project"),
        default="general",
    )
    parser.add_argument("--industry", action="append", default=[])
    parser.add_argument("--responsibility", action="append", default=[])
    parser.add_argument(
        "--apply", action="store_true", help="Create missing files; never overwrite existing files"
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    args.industry = list(dict.fromkeys(item.strip() for item in args.industry if item.strip()))
    args.responsibility = list(
        dict.fromkeys(item.strip() for item in args.responsibility if item.strip())
    )

    root = lexical_absolute(Path(args.root))

    if not ID_RE.fullmatch(args.kb_id):
        return validation_failure(
            args,
            root,
            "--kb-id must use lowercase ASCII letters, digits, dots, underscores, or hyphens",
        )
    if args.scope_type == "industry" and not args.industry:
        return validation_failure(
            args, root, "Industry-scoped knowledge bases require at least one --industry"
        )
    if args.scope_type == "responsibility" and not args.responsibility:
        return validation_failure(
            args,
            root,
            "Responsibility-scoped knowledge bases require at least one --responsibility",
        )

    root_kind = path_kind(root)
    if root_kind not in {"missing", "directory"}:
        return conflict_failure(
            args,
            root,
            [],
            f"Target root must be a regular directory, not {root_kind}: {root}",
        )
    try:
        plan, payloads = build_plan(root, args)
    except (OSError, UnicodeError) as exc:
        return validation_failure(args, root, str(exc))

    conflicts = [item for item in plan if item["action"] in CONFLICT_ACTIONS]
    if conflicts:
        return conflict_failure(
            args,
            root,
            plan,
            "Filesystem conflicts with the requested knowledge-base structure; nothing was written.",
        )
    if not args.apply:
        emit_result(
            args,
            result_payload(
                root,
                args,
                plan,
                "dry-run",
                message="Dry run only; add --apply to create missing files.",
            ),
        )
        return 0

    created_files = 0
    try:
        root.mkdir(parents=True, exist_ok=True)
        if path_kind(root) != "directory":
            raise InitializationConflict(f"Target root is no longer a regular directory: {root}")
        for directory in DIRECTORIES:
            ensure_directory(root / directory)
        for path, payload in payloads.items():
            if path_kind(path.parent) != "directory":
                raise InitializationConflict(
                    f"Expected parent is no longer a regular directory: {path.parent}"
                )
            exclusive_write_text(path, payload)
            created_files += 1
    except FileExistsError as exc:
        return conflict_failure(
            args,
            root,
            plan,
            f"A file appeared during initialization and was preserved: {exc.filename or exc}",
        )
    except InitializationConflict as exc:
        return conflict_failure(args, root, plan, str(exc))
    except OSError as exc:
        return validation_failure(args, root, str(exc), plan)
    emit_result(
        args,
        result_payload(
            root,
            args,
            plan,
            "initialized",
            message=f"Initialized missing knowledge-base structure at: {root}",
            created_files=created_files,
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
