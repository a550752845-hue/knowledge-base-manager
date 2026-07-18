"""Read-only semantic and structural health checks for Markdown knowledge bases."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from kb_common import (
    FrontmatterError,
    as_list,
    clean_scalar,
    ensure_within,
    field_value,
    has_value,
    load_manifest,
    normalized_value,
    parse_frontmatter,
    parse_iso_date,
    read_text,
    stable_json,
)


WIKILINK_RE = re.compile(r"!?\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._:-]*$")
FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})")
SKILL_ROOT = Path(__file__).resolve().parents[1]
ASSET_SCHEMA_PATH = SKILL_ROOT / "references" / "asset-frontmatter.schema.json"
MANIFEST_SCHEMA_PATH = SKILL_ROOT / "references" / "knowledge-base-manifest.schema.json"
SOURCE_REGISTRY_SCHEMA_PATH = SKILL_ROOT / "references" / "source-registry-row.schema.json"
PRIVACY_REVIEW_FIELDS = ("privacy_reviewed_by", "privacy_review_reason", "privacy_reviewed_at")
_SCHEMA_VALIDATORS: dict[Path, Draft202012Validator] = {}

LEGACY_REUSABLE_MARKERS = (
    "知识卡片",
    "模型",
    "模型方法",
    "案例证据",
    "主题问题",
    "行业板块",
    "来源档案",
    "素材拆解",
)
V3_REUSABLE_MARKERS = ("20-来源解析", "30-知识对象", "40-可执行资产", "50-证据验证")

SOURCE_FIELDS = (
    "source_id",
    "source_ids",
    "source_materials",
    "source_path",
    "source_urls",
    "provenance",
    "conversation_id",
    "decision_id",
)
ANCHOR_FIELDS = ("source_anchors", "source_anchor", "anchor_value", "page", "timestamp", "row")

V3_REQUIRED_FIELDS = (
    "id",
    "type",
    "knowledge_role",
    "truth_status",
    "preservation",
    "reuse_mode",
    "status",
    "scope_type",
    "topics",
    "confidence",
    "maturity",
    "time_sensitivity",
    "sensitivity",
    "created",
    "updated",
)
ARRAY_FIELDS = (
    "domains",
    "industries",
    "responsibilities",
    "topics",
    "retrieval_queries",
    "audiences",
    "languages",
    "source_ids",
    "source_anchors",
    "relations",
)
DIRECT_USE_FIELDS = (
    "audience",
    "scenario",
    "goal",
    "variables",
    "boundary",
    "compliance_risk",
    "rights_or_permission",
    "tested_status",
    "last_verified",
)

ENUMS = {
    "knowledge_role": {
        "source",
        "logic-map",
        "fact",
        "claim",
        "principle",
        "model",
        "procedure",
        "talk-track",
        "evidence",
        "source-profile",
        "output",
        "management",
    },
    "truth_status": {
        "source-record",
        "source-claim",
        "verified-fact",
        "model-synthesis",
        "user-preference",
        "generated",
    },
    "preservation": {"exact", "anchored", "normalized", "derived"},
    "reuse_mode": {
        "quote-only",
        "analyze-only",
        "adapt-required",
        "direct-use",
        "reference-only",
        "do-not-use",
    },
    "status": {"draft", "active", "pending-review", "approved", "deprecated", "archived"},
    "scope_type": {"general", "industry", "responsibility", "cross-domain", "project"},
    "confidence": {"low", "medium", "high"},
    "maturity": {"seed", "candidate", "stable", "core"},
    "evidence_strength": {"weak", "moderate", "strong"},
    "time_sensitivity": {"low", "medium", "high"},
    "sensitivity": {"public", "internal", "private", "restricted"},
    "tested_status": {"untested", "reviewed", "tested"},
    "promotion_status": {"not-reviewed", "pending-review", "approved", "promoted", "rejected"},
}

ROLE_CONTRACTS: dict[str, dict[str, set[str]]] = {
    "source": {
        "truth_status": {"source-record"},
        "preservation": {"exact"},
        "reuse_mode": {"reference-only", "quote-only", "do-not-use"},
    },
    "logic-map": {
        "truth_status": {"source-claim"},
        "preservation": {"derived"},
        "reuse_mode": {"analyze-only"},
    },
    "fact": {
        "truth_status": {"verified-fact"},
        "preservation": {"normalized", "anchored"},
        "reuse_mode": {"reference-only", "analyze-only"},
    },
    "claim": {
        "truth_status": {"source-claim", "model-synthesis", "user-preference"},
        "preservation": {"normalized", "derived", "anchored"},
        "reuse_mode": {"analyze-only", "reference-only", "do-not-use"},
    },
    "principle": {
        "truth_status": {"model-synthesis", "user-preference", "source-claim"},
        "preservation": {"normalized", "derived"},
        "reuse_mode": {"analyze-only", "adapt-required", "reference-only"},
    },
    "model": {
        "truth_status": {"model-synthesis"},
        "preservation": {"derived", "normalized"},
        "reuse_mode": {"analyze-only", "adapt-required", "reference-only"},
    },
    "procedure": {
        "truth_status": {"model-synthesis", "user-preference", "generated", "verified-fact"},
        "preservation": {"normalized", "derived", "exact"},
        "reuse_mode": {"adapt-required", "direct-use", "analyze-only", "reference-only"},
    },
    "talk-track": {
        "truth_status": {"generated", "user-preference", "model-synthesis", "source-record"},
        "preservation": {"exact", "anchored", "normalized", "derived"},
        "reuse_mode": {"quote-only", "adapt-required", "direct-use", "do-not-use"},
    },
    "evidence": {
        "truth_status": {"source-record", "source-claim", "verified-fact"},
        "preservation": {"exact", "anchored", "normalized"},
        "reuse_mode": {"quote-only", "reference-only", "do-not-use"},
    },
    "source-profile": {
        "truth_status": {"source-record", "source-claim", "model-synthesis"},
        "preservation": {"normalized", "derived"},
        "reuse_mode": {"analyze-only", "reference-only"},
    },
    "output": {
        "truth_status": {"generated", "user-preference"},
        "preservation": {"derived", "exact"},
        "reuse_mode": {"reference-only", "do-not-use"},
    },
    "management": {
        "truth_status": {"user-preference", "model-synthesis", "generated"},
        "preservation": {"normalized", "derived", "exact"},
        "reuse_mode": {"reference-only"},
    },
}

SENSITIVITY_RANK = {"public": 0, "internal": 1, "private": 2, "restricted": 3}


def schema_validator(path: Path) -> Draft202012Validator:
    validator = _SCHEMA_VALIDATORS.get(path)
    if validator is not None:
        return validator
    schema = json.loads(read_text(path))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    _SCHEMA_VALIDATORS[path] = validator
    return validator


def schema_error_detail(error: Any) -> str:
    location = ".".join(str(item) for item in error.absolute_path) or "$"
    return f"{location}: {error.message}"


def is_link_or_junction(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        is_junction = getattr(path, "is_junction", None)
        if is_junction is not None and is_junction():
            return True
        metadata = os.lstat(path)
    except OSError:
        return True
    reparse_tag = getattr(metadata, "st_reparse_tag", 0)
    return reparse_tag in {
        getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003),
        getattr(stat, "IO_REPARSE_TAG_SYMLINK", 0xA000000C),
    }


def resolves_within(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve(strict=False).relative_to(root.resolve())
    except (OSError, ValueError):
        return False
    return True


def discover_markdown_files(root: Path) -> tuple[list[Path], list[tuple[Path, str]]]:
    notes: list[Path] = []
    skipped: list[tuple[Path, str]] = []
    for current_raw, directory_names, file_names in os.walk(root, topdown=True, followlinks=False):
        current = Path(current_raw)
        kept_directories: list[str] = []
        for name in sorted(directory_names):
            candidate = current / name
            if is_link_or_junction(candidate):
                skipped.append((candidate, "Skipped linked or junction directory"))
            elif not resolves_within(root, candidate):
                skipped.append((candidate, "Skipped directory resolving outside the managed root"))
            else:
                kept_directories.append(name)
        directory_names[:] = kept_directories

        for name in sorted(file_names):
            if not name.casefold().endswith(".md"):
                continue
            candidate = current / name
            if is_link_or_junction(candidate):
                skipped.append((candidate, "Skipped linked Markdown file"))
            elif not resolves_within(root, candidate):
                skipped.append(
                    (candidate, "Skipped Markdown file resolving outside the managed root")
                )
            elif candidate.is_file():
                notes.append(candidate)
    return sorted(notes), skipped


def strip_ignored_regions(text: str) -> str:
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    text = re.sub(r"%%.*?%%", "", text, flags=re.DOTALL)
    output: list[str] = []
    fence_character = ""
    fence_length = 0
    for line in text.splitlines(keepends=True):
        match = FENCE_RE.match(line)
        if fence_character:
            stripped = line.lstrip()
            run = len(stripped) - len(stripped.lstrip(fence_character))
            if run >= fence_length and not stripped[run:].strip():
                fence_character = ""
                fence_length = 0
            output.append("\n" if line.endswith("\n") else "")
            continue
        if match:
            delimiter = match.group(1)
            fence_character = delimiter[0]
            fence_length = len(delimiter)
            output.append("\n" if line.endswith("\n") else "")
            continue

        cleaned: list[str] = []
        index = 0
        while index < len(line):
            if line[index] != "`":
                cleaned.append(line[index])
                index += 1
                continue
            run_end = index
            while run_end < len(line) and line[run_end] == "`":
                run_end += 1
            delimiter = line[index:run_end]
            closing = line.find(delimiter, run_end)
            if closing < 0:
                cleaned.append(delimiter)
                index = run_end
                continue
            cleaned.append(" " * (closing + len(delimiter) - index))
            index = closing + len(delimiter)
        output.append("".join(cleaned))
    return "".join(output)


@dataclass
class Finding:
    severity: str
    code: str
    file: str
    detail: str


@dataclass
class Inventory:
    root: Path
    notes: list[Path]
    manifest_path: Path | None = None
    manifest: dict[str, Any] = field(default_factory=dict)
    fields_by_note: dict[Path, dict[str, Any]] = field(default_factory=dict)
    note_by_stem: dict[str, list[Path]] = field(default_factory=dict)
    note_by_alias: dict[str, list[Path]] = field(default_factory=dict)
    note_by_rel: dict[str, Path] = field(default_factory=dict)
    links_inbound: dict[Path, int] = field(default_factory=dict)
    source_registry: dict[str, dict[str, Any]] = field(default_factory=dict)
    source_registry_loaded: bool = False
    findings: list[Finding] = field(default_factory=list)

    def rel(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

    def add(self, severity: str, code: str, path: Path | str, detail: str) -> None:
        rel = self.rel(path) if isinstance(path, Path) else path
        self.findings.append(Finding(severity, code, rel, detail))


def is_v3(fields: dict[str, Any]) -> bool:
    return field_value(fields, "schema_version") == "3" or any(
        key in fields for key in ("knowledge_role", "truth_status", "preservation", "reuse_mode")
    )


def is_reusable_note(root: Path, path: Path, fields: dict[str, Any]) -> bool:
    rel = path.relative_to(root).as_posix()
    if rel.startswith("_meta/") or rel.startswith("00-"):
        return is_v3(fields) and field_value(fields, "knowledge_role") not in {"", "management"}
    return is_v3(fields) or any(
        marker in rel for marker in LEGACY_REUSABLE_MARKERS + V3_REUSABLE_MARKERS
    )


def requires_provenance(fields: dict[str, Any]) -> bool:
    return field_value(fields, "knowledge_role") in {
        "logic-map",
        "fact",
        "claim",
        "principle",
        "model",
        "procedure",
        "talk-track",
        "evidence",
        "source-profile",
    }


def build_inventory(root: Path) -> Inventory:
    notes, skipped = discover_markdown_files(root)
    manifest_path: Path | None = None
    manifest: dict[str, Any] = {}
    manifest_unsafe = False
    for candidate in (
        root / "_meta" / "knowledge-base.json",
        root / "_meta" / "知识库清单.json",
    ):
        if not candidate.exists() and not candidate.is_symlink():
            continue
        manifest_path = candidate
        if (
            not candidate.is_file()
            or is_link_or_junction(candidate)
            or not resolves_within(root, candidate)
        ):
            manifest_unsafe = True
            break
        manifest_path, manifest = load_manifest(root)
        break
    inv = Inventory(root=root, notes=notes, manifest_path=manifest_path, manifest=manifest)
    for path, detail in skipped:
        inv.add("error", "unsafe-filesystem-entry", path, detail)
    if manifest_path is not None and manifest_unsafe:
        inv.add(
            "error",
            "unsafe-machine-manifest",
            manifest_path,
            "Machine manifest must be a regular file contained in the managed root",
        )
    for note in notes:
        rel = inv.rel(note)
        inv.note_by_rel[rel.casefold()] = note
        inv.note_by_rel[rel.removesuffix(".md").casefold()] = note
        inv.note_by_stem.setdefault(note.stem.casefold(), []).append(note)
        inv.links_inbound[note] = 0
        try:
            fields = parse_frontmatter(read_text(note), rel)
        except (FrontmatterError, OSError, UnicodeError) as exc:
            inv.add("error", "invalid-frontmatter", note, str(exc))
            fields = {}
        inv.fields_by_note[note] = fields
        for alias in as_list(fields.get("aliases")):
            inv.note_by_alias.setdefault(alias.casefold(), []).append(note)
    return inv


def link_candidates(
    inv: Inventory, source: Path, target: str, *, markdown: bool
) -> tuple[list[Path], bool]:
    normalized = target.strip().replace("\\", "/")
    raw = Path(normalized)
    if raw.is_absolute():
        return [], True
    if markdown and raw.suffix.casefold() != ".md":
        raw = Path(f"{normalized}.md")

    if normalized.startswith(("./", "../")):
        bases = [source.parent]
    elif "/" in normalized:
        bases = [inv.root, source.parent]
    else:
        bases = [source.parent, inv.root]

    candidates: list[Path] = []
    unsafe = False
    seen: set[str] = set()
    for base in bases:
        candidate = base / raw
        try:
            resolved = ensure_within(inv.root, candidate)
        except (OSError, ValueError):
            unsafe = True
            continue
        if candidate.exists() and is_link_or_junction(candidate):
            unsafe = True
            continue
        key = os.path.normcase(str(resolved))
        if key not in seen:
            seen.add(key)
            candidates.append(resolved)
    return candidates, unsafe


def resolve_wikilink(inv: Inventory, source: Path, target: str) -> list[Path]:
    normalized = target.strip().replace("\\", "/")
    if normalized.endswith(".md"):
        normalized = normalized[:-3]
    exact_paths, _ = link_candidates(inv, source, normalized, markdown=True)
    for exact in exact_paths:
        if not exact.is_file():
            continue
        relative = exact.relative_to(inv.root).as_posix()
        match = inv.note_by_rel.get(relative.casefold())
        if match is not None:
            return [match]

    if "/" in normalized or normalized.startswith((".", "..")):
        return []
    lookup = Path(normalized).name.casefold()
    candidates = [*inv.note_by_stem.get(lookup, []), *inv.note_by_alias.get(lookup, [])]
    return sorted(set(candidates))


def attachment_exists(inv: Inventory, source: Path, target: str) -> tuple[bool, bool]:
    candidates, unsafe = link_candidates(inv, source, target, markdown=False)
    return any(path.is_file() and path.suffix.casefold() != ".md" for path in candidates), unsafe


def check_links(inv: Inventory) -> None:
    for alias, matches in inv.note_by_alias.items():
        if len(matches) > 1:
            paths = ", ".join(inv.rel(path) for path in matches)
            inv.add(
                "warning",
                "duplicate-alias",
                paths.split(", ", 1)[0],
                f"Alias {alias!r} is shared by: {paths}",
            )
    for note in inv.notes:
        text = strip_ignored_regions(read_text(note))
        for raw_target in WIKILINK_RE.findall(text):
            attachment_found, unsafe_attachment = attachment_exists(inv, note, raw_target)
            if attachment_found:
                continue
            matches = resolve_wikilink(inv, note, raw_target)
            if not matches:
                _, unsafe_markdown = link_candidates(inv, note, raw_target, markdown=True)
                detail = (
                    f"Target escapes the managed root: [[{raw_target}]]"
                    if unsafe_attachment or unsafe_markdown
                    else f"Missing target: [[{raw_target}]]"
                )
                inv.add("error", "broken-wikilink", note, detail)
            elif len(matches) > 1:
                paths = ", ".join(inv.rel(path) for path in matches)
                inv.add("error", "ambiguous-wikilink", note, f"[[{raw_target}]] matches: {paths}")
            else:
                target = matches[0]
                inv.links_inbound[target] = inv.links_inbound.get(target, 0) + 1


def manifest_paths(inv: Inventory) -> dict[str, str]:
    paths = inv.manifest.get("paths", {})
    if not isinstance(paths, dict):
        inv.add(
            "error",
            "invalid-manifest",
            inv.manifest_path or "_meta/knowledge-base.json",
            "paths must be an object",
        )
        return {}
    return {
        str(key): value.strip()
        for key, value in paths.items()
        if isinstance(value, str) and value.strip()
    }


def check_manifest(inv: Inventory) -> None:
    v3_count = sum(is_v3(fields) for fields in inv.fields_by_note.values())
    if inv.manifest_path is None:
        if v3_count:
            inv.add(
                "warning",
                "missing-machine-manifest",
                "_meta/knowledge-base.json",
                "Schema-v3 root has no machine-readable manifest",
            )
        return

    try:
        validator = schema_validator(MANIFEST_SCHEMA_PATH)
    except (OSError, UnicodeError, json.JSONDecodeError, SchemaError) as exc:
        inv.add(
            "error",
            "invalid-bundled-schema",
            "references/knowledge-base-manifest.schema.json",
            str(exc),
        )
    else:
        for error in sorted(validator.iter_errors(normalized_value(inv.manifest)), key=str):
            inv.add(
                "error",
                "invalid-manifest-schema",
                inv.manifest_path,
                schema_error_detail(error),
            )

    if clean_scalar(inv.manifest.get("schema_version")) != "3":
        inv.add("error", "invalid-manifest", inv.manifest_path, "schema_version must be 3")
    if not clean_scalar(inv.manifest.get("knowledge_base_id")):
        inv.add("error", "invalid-manifest", inv.manifest_path, "knowledge_base_id is required")

    scope = inv.manifest.get("scope", {})
    if not isinstance(scope, dict) or clean_scalar(scope.get("type")) not in ENUMS["scope_type"]:
        inv.add("error", "invalid-manifest", inv.manifest_path, "scope.type is missing or invalid")

    required_path_keys = (
        "ai_entry",
        "management_rules",
        "recent_context",
        "source_registry_human",
        "source_registry_machine",
        "maintenance_log",
        "asset_index",
    )
    paths = manifest_paths(inv)
    for key in required_path_keys:
        relative = paths.get(key)
        if not relative:
            inv.add("error", "missing-manifest-path", inv.manifest_path, f"paths.{key} is required")
            continue
        try:
            target = ensure_within(inv.root, inv.root / relative)
        except ValueError as exc:
            inv.add("error", "unsafe-manifest-path", inv.manifest_path, str(exc))
            continue
        if key != "asset_index" and not target.is_file():
            inv.add(
                "error",
                "missing-management-file",
                relative,
                f"Configured paths.{key} file is missing",
            )
        elif key == "asset_index":
            if target.suffix.casefold() != ".jsonl":
                inv.add(
                    "error",
                    "unsafe-manifest-path",
                    inv.manifest_path,
                    "paths.asset_index must point to a .jsonl generated-index file",
                )
            if target.exists() and not target.is_file():
                inv.add(
                    "error",
                    "unsafe-manifest-path",
                    inv.manifest_path,
                    "paths.asset_index exists but is not a regular file",
                )

    role_paths = inv.manifest.get("role_paths", {})
    if isinstance(role_paths, dict):
        for role, relative in role_paths.items():
            if not isinstance(relative, str) or not relative.strip():
                continue
            try:
                target = ensure_within(inv.root, inv.root / relative)
            except ValueError as exc:
                inv.add(
                    "error",
                    "unsafe-role-path",
                    inv.manifest_path,
                    f"role_paths.{role}: {exc}",
                )
                continue
            if not target.is_dir():
                inv.add(
                    "error",
                    "missing-role-path",
                    inv.manifest_path,
                    f"role_paths.{role} directory is missing: {relative}",
                )

    source_roots = inv.manifest.get("source_roots", [])
    if source_roots and not isinstance(source_roots, list):
        inv.add("error", "invalid-manifest", inv.manifest_path, "source_roots must be an array")
    elif isinstance(source_roots, list):
        for position, item in enumerate(source_roots, 1):
            if not isinstance(item, dict) or clean_scalar(item.get("mode")) != "read-only":
                inv.add(
                    "warning",
                    "mutable-source-root",
                    inv.manifest_path,
                    f"source_roots[{position}] should declare mode: read-only",
                )


def fallback_required_files(inv: Inventory) -> None:
    if inv.manifest_path is not None:
        return
    required = (
        "_meta/知识库管理规则.md",
        "_meta/AI调用索引.md",
        "_meta/来源注册表.md",
        "_meta/最近上下文.md",
        "_meta/维护日志.md",
    )
    any_legacy_management = any((inv.root / rel).exists() for rel in required)
    if not any_legacy_management:
        return
    for rel in required:
        if not (inv.root / rel).is_file():
            inv.add(
                "error",
                "missing-management-file",
                rel,
                "Required legacy management file is missing",
            )


def source_registry_path(inv: Inventory) -> Path | None:
    relative = manifest_paths(inv).get("source_registry_machine") if inv.manifest_path else None
    if not relative:
        candidate = inv.root / "_meta" / "来源注册表.jsonl"
        return candidate if candidate.is_file() else None
    try:
        return ensure_within(inv.root, inv.root / relative)
    except ValueError:
        return None


def reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_source_registry(inv: Inventory) -> None:
    path = source_registry_path(inv)
    if path is None or not path.is_file():
        return
    inv.source_registry_loaded = True
    try:
        validator = schema_validator(SOURCE_REGISTRY_SCHEMA_PATH)
    except (OSError, UnicodeError, json.JSONDecodeError, SchemaError) as exc:
        inv.add(
            "error",
            "invalid-bundled-schema",
            "references/source-registry-row.schema.json",
            str(exc),
        )
        return
    for number, line in enumerate(read_text(path).splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line, object_pairs_hook=reject_duplicate_json_keys)
        except (json.JSONDecodeError, ValueError) as exc:
            inv.add("error", "invalid-source-registry", path, f"Line {number}: {exc}")
            continue
        if not isinstance(row, dict):
            inv.add("error", "invalid-source-registry", path, f"Line {number} must be an object")
            continue
        for error in sorted(validator.iter_errors(row), key=str):
            inv.add(
                "error",
                "invalid-source-registry-schema",
                path,
                f"Line {number} {schema_error_detail(error)}",
            )
        raw_source_id = row.get("source_id")
        if not isinstance(raw_source_id, str) or not raw_source_id.strip():
            inv.add(
                "error",
                "invalid-source-registry",
                path,
                f"Line {number} source_id must be a non-empty string",
            )
            continue
        source_id = raw_source_id.strip()
        if source_id in inv.source_registry:
            inv.add("error", "duplicate-source-id", path, f"Duplicate source_id: {source_id}")
            continue
        inv.source_registry[source_id] = row

        if not ID_RE.fullmatch(source_id):
            inv.add(
                "error",
                "invalid-source-id",
                path,
                f"source_id should use stable lowercase ASCII: {source_id}",
            )
        for required in ("title", "source_type", "sensitivity", "status"):
            if not isinstance(row.get(required), str) or not row[required].strip():
                inv.add(
                    "error",
                    "incomplete-source-record",
                    path,
                    f"{source_id}: {required} must be a non-empty string",
                )
        sensitivity = clean_scalar(row.get("sensitivity"))
        if sensitivity and sensitivity not in ENUMS["sensitivity"]:
            inv.add(
                "error",
                "invalid-source-record",
                path,
                f"{source_id}: invalid sensitivity {sensitivity!r}",
            )

        preferred_raw = row.get("preferred_read_path", "")
        if not isinstance(preferred_raw, str):
            inv.add(
                "error",
                "invalid-source-record",
                path,
                f"{source_id}: preferred_read_path must be a string",
            )
            preferred = ""
        else:
            preferred = preferred_raw.strip()
        known_paths_raw = row.get("all_known_paths", [])
        if not isinstance(known_paths_raw, list) or any(
            not isinstance(item, str) or not item.strip() for item in known_paths_raw
        ):
            inv.add(
                "error",
                "invalid-source-record",
                path,
                f"{source_id}: all_known_paths must be an array of non-empty strings",
            )
            known_paths: list[str] = []
        else:
            known_paths = [item.strip() for item in known_paths_raw]
        if preferred and known_paths and preferred not in known_paths:
            inv.add(
                "warning",
                "unregistered-preferred-path",
                path,
                f"{source_id}: preferred path is not in all_known_paths",
            )


def add_contract_finding(
    inv: Inventory, note: Path, field: str, value: str, allowed: set[str]
) -> None:
    role = field_value(inv.fields_by_note[note], "knowledge_role")
    allowed_values = ", ".join(sorted(allowed))
    inv.add(
        "error",
        "role-contract-violation",
        note,
        f"{field}={value!r} is invalid for {role}; allowed: {allowed_values}",
    )


def check_role_contract(inv: Inventory, note: Path, fields: dict[str, Any]) -> None:
    role = field_value(fields, "knowledge_role")
    contract = ROLE_CONTRACTS.get(role)
    if not contract:
        return
    for name, allowed in contract.items():
        value = field_value(fields, name)
        if value and value not in allowed:
            add_contract_finding(inv, note, name, value, allowed)


def check_dates(
    inv: Inventory, note: Path, fields: dict[str, Any], freshness: dict[str, int]
) -> None:
    created = parse_iso_date(fields.get("created"))
    updated = parse_iso_date(fields.get("updated"))
    verified = parse_iso_date(fields.get("last_verified"))
    for name, parsed in (("created", created), ("updated", updated)):
        if has_value(fields, name) and parsed is None:
            inv.add("warning", "invalid-date", note, f"{name} must be YYYY-MM-DD")
    if created and updated and updated < created:
        inv.add("error", "invalid-date-order", note, "updated is earlier than created")
    if verified and verified > date.today():
        inv.add("error", "future-verification-date", note, "last_verified is in the future")

    sensitivity = field_value(fields, "time_sensitivity")
    threshold = freshness.get(sensitivity)
    if threshold is None:
        return
    if sensitivity == "high" and verified is None:
        inv.add(
            "error",
            "missing-verification-date",
            note,
            "High-time-sensitivity asset requires last_verified",
        )
        return
    if verified and (date.today() - verified).days > threshold:
        severity = "error" if field_value(fields, "reuse_mode") == "direct-use" else "warning"
        inv.add(
            severity,
            "stale-asset",
            note,
            f"last_verified exceeds {threshold}-day {sensitivity} threshold",
        )


def referenced_source_ids(fields: dict[str, Any]) -> list[str]:
    source_ids = as_list(fields.get("source_ids"))
    source_id = fields.get("source_id")
    if isinstance(source_id, str) and source_id.strip():
        source_ids.append(source_id.strip())
    return list(dict.fromkeys(source_ids))


def privacy_approval_is_complete(inv: Inventory, note: Path, fields: dict[str, Any]) -> bool:
    declared = any(
        field_value(fields, name) == "approved"
        for name in ("declassification_status", "anonymization_status")
    )
    if not declared:
        return False

    missing = [name for name in PRIVACY_REVIEW_FIELDS if not has_value(fields, name)]
    reviewed_at = parse_iso_date(fields.get("privacy_reviewed_at"))
    if missing:
        inv.add(
            "error",
            "invalid-privacy-approval",
            note,
            "Approved anonymization/declassification is missing: " + ", ".join(missing),
        )
        return False
    if reviewed_at is None or reviewed_at > date.today():
        inv.add(
            "error",
            "invalid-privacy-approval",
            note,
            "privacy_reviewed_at must be a valid, non-future date",
        )
        return False
    return True


def check_sensitivity(inv: Inventory, note: Path, fields: dict[str, Any]) -> None:
    asset_sensitivity = field_value(fields, "sensitivity")
    if asset_sensitivity not in SENSITIVITY_RANK or not inv.source_registry:
        return
    downgrades: list[tuple[str, str]] = []
    for source_id in referenced_source_ids(fields):
        source = inv.source_registry.get(source_id)
        if not source:
            continue
        source_sensitivity = clean_scalar(source.get("sensitivity"))
        if (
            source_sensitivity in SENSITIVITY_RANK
            and SENSITIVITY_RANK[asset_sensitivity] < SENSITIVITY_RANK[source_sensitivity]
        ):
            downgrades.append((source_id, source_sensitivity))
    if not downgrades:
        return
    if privacy_approval_is_complete(inv, note, fields):
        return
    for source_id, source_sensitivity in downgrades:
        inv.add(
            "error",
            "sensitivity-downgrade",
            note,
            f"Asset is {asset_sensitivity} but source {source_id} is {source_sensitivity}",
        )


def check_v3_contract(
    inv: Inventory,
    note: Path,
    fields: dict[str, Any],
    ids: dict[str, str],
    freshness: dict[str, int] | None = None,
) -> None:
    freshness = freshness or {"high": 30, "medium": 180, "low": 3650}
    rel = inv.rel(note)
    try:
        validator = schema_validator(ASSET_SCHEMA_PATH)
    except (OSError, UnicodeError, json.JSONDecodeError, SchemaError) as exc:
        inv.add(
            "error",
            "invalid-bundled-schema",
            "references/asset-frontmatter.schema.json",
            str(exc),
        )
    else:
        for error in sorted(validator.iter_errors(normalized_value(fields)), key=str):
            inv.add(
                "error",
                "invalid-asset-schema",
                note,
                schema_error_detail(error),
            )

    if "source_id" in fields and not isinstance(fields["source_id"], str):
        inv.add("error", "invalid-v3-field", note, "source_id must be a string")
    for name in V3_REQUIRED_FIELDS:
        if not has_value(fields, name):
            inv.add("warning", "missing-v3-field", note, f"Missing schema-v3 field: {name}")

    asset_id = field_value(fields, "id")
    if asset_id:
        if not ID_RE.fullmatch(asset_id):
            inv.add(
                "warning",
                "invalid-asset-id",
                note,
                "ID should use stable lowercase ASCII characters",
            )
        if asset_id in ids:
            inv.add(
                "error",
                "duplicate-asset-id",
                note,
                f"Asset ID {asset_id!r} already used by {ids[asset_id]}",
            )
        else:
            ids[asset_id] = rel

    for name, allowed in ENUMS.items():
        value = field_value(fields, name)
        if value and value not in allowed:
            inv.add("warning", "invalid-v3-value", note, f"Invalid {name}: {value!r}")

    for name in ARRAY_FIELDS:
        if name in fields and fields[name] not in (None, "") and not isinstance(fields[name], list):
            inv.add("warning", "non-array-field", note, f"{name} must be a YAML array")

    check_role_contract(inv, note, fields)
    check_dates(inv, note, fields, freshness)
    check_sensitivity(inv, note, fields)

    role = field_value(fields, "knowledge_role")
    truth = field_value(fields, "truth_status")
    reuse = field_value(fields, "reuse_mode")
    preservation = field_value(fields, "preservation")

    if requires_provenance(fields) and not any(has_value(fields, name) for name in SOURCE_FIELDS):
        inv.add(
            "warning",
            "missing-provenance",
            note,
            "Durable asset has no source or conversation provenance",
        )

    if (
        role == "logic-map"
        and not as_list(fields.get("source_ids"))
        and not has_value(fields, "source_id")
    ):
        inv.add(
            "error",
            "unlinked-logic-map",
            note,
            "Logic map must identify the source whose complete logic it analyzes",
        )

    if preservation in {"exact", "anchored"} and role != "source":
        if not any(has_value(fields, name) for name in SOURCE_FIELDS):
            inv.add(
                "error",
                "unanchored-exact-content",
                note,
                "Exact/anchored asset has no source tracking",
            )
        if not any(has_value(fields, name) for name in ANCHOR_FIELDS):
            inv.add(
                "error",
                "unanchored-exact-content",
                note,
                "Exact/anchored asset has no precise source anchor",
            )

    if role == "source" and not any(
        has_value(fields, name)
        for name in ("source_path", "source_url", "source_urls", "content_hash")
    ):
        inv.add(
            "warning", "unlocated-source", note, "Source record has no path, URL, or content hash"
        )

    if truth == "verified-fact":
        if not any(
            has_value(fields, name) for name in ("verification_method", "verification_sources")
        ):
            inv.add(
                "error",
                "unverified-fact",
                note,
                "Verified fact must record verification_method or verification_sources",
            )
        if not has_value(fields, "last_verified"):
            inv.add("error", "unverified-fact", note, "Verified fact must record last_verified")

    if reuse == "direct-use":
        for name in DIRECT_USE_FIELDS:
            if name == "variables":
                if name not in fields or not isinstance(fields[name], list):
                    inv.add(
                        "error",
                        "incomplete-direct-use",
                        note,
                        "Direct-use asset requires variables as a YAML array",
                    )
            elif not has_value(fields, name):
                inv.add("error", "incomplete-direct-use", note, f"Direct-use asset missing: {name}")
        if field_value(fields, "status") != "approved":
            inv.add(
                "error",
                "unapproved-direct-use",
                note,
                "Direct-use asset must have status: approved",
            )
        if field_value(fields, "tested_status") not in {"reviewed", "tested"}:
            inv.add(
                "error",
                "unreviewed-direct-use",
                note,
                "Direct-use asset must be reviewed or tested",
            )

    if truth == "generated" and role != "output":
        if field_value(fields, "promotion_status") not in {"approved", "promoted"}:
            inv.add(
                "error",
                "unreviewed-generated-knowledge",
                note,
                "Generated durable asset requires explicit promotion approval",
            )

    maturity = field_value(fields, "maturity")
    if maturity in {"stable", "core"} and field_value(fields, "evidence_strength") not in {
        "moderate",
        "strong",
    }:
        inv.add(
            "warning",
            "weak-mature-asset",
            note,
            f"{maturity} asset needs moderate or strong evidence_strength",
        )
    if maturity == "core" and not has_value(fields, "validation_records"):
        inv.add("warning", "unvalidated-core-asset", note, "Core asset needs validation_records")

    for source_id in referenced_source_ids(fields):
        if inv.source_registry_loaded and source_id not in inv.source_registry:
            inv.add(
                "warning",
                "unknown-source-id",
                note,
                f"source_id is absent from machine registry: {source_id}",
            )


def freshness_policy(inv: Inventory) -> dict[str, int]:
    defaults = {"high": 30, "medium": 180, "low": 3650}
    raw = inv.manifest.get("freshness_policy", {})
    if not isinstance(raw, dict):
        return defaults
    for key in defaults:
        value = raw.get(f"{key}_days", raw.get(key))
        if isinstance(value, int) and value > 0:
            defaults[key] = value
    return defaults


def check_frontmatter(inv: Inventory) -> None:
    ids: dict[str, str] = {}
    freshness = freshness_policy(inv)
    for note in inv.notes:
        fields = inv.fields_by_note[note]
        if not is_reusable_note(inv.root, note, fields):
            continue
        if not fields:
            inv.add("warning", "missing-frontmatter", note, "Reusable note has no frontmatter")
            continue
        if is_v3(fields):
            check_v3_contract(inv, note, fields, ids, freshness)
        else:
            for name in ("industry_sector", "confidence", "maturity"):
                if not has_value(fields, name):
                    inv.add(
                        "warning", "missing-legacy-field", note, f"Missing legacy field: {name}"
                    )


def check_old_path_residue(inv: Inventory) -> None:
    for note in inv.notes:
        text = strip_ignored_regions(read_text(note))
        for marker in ("素材索引", "知识卡片", "核心模型", "主题索引", "作者档案"):
            if f"[[{marker}/" in text:
                inv.add(
                    "info", "old-path-residue", note, f"Contains old-style wikilink: [[{marker}/"
                )


def check_asset_index(inv: Inventory) -> None:
    from build_asset_index import (
        BUILD_PROFILE_INCLUDE_MANAGEMENT,
        build_rows,
        default_index_path,
        parse_index_document,
        render_jsonl,
    )

    try:
        index_path = default_index_path(inv.root)
    except (FrontmatterError, OSError, UnicodeError, ValueError) as exc:
        inv.add("error", "asset-index-build-failed", "00-AI入口/资产索引.jsonl", str(exc))
        return
    if not index_path.is_file():
        inv.add(
            "error",
            "missing-asset-index",
            index_path.relative_to(inv.root).as_posix(),
            "Machine asset index is missing",
        )
        return

    actual = read_text(index_path)
    try:
        profile, _ = parse_index_document(actual, str(index_path), require_owned=True)
        include_management = profile == BUILD_PROFILE_INCLUDE_MANAGEMENT
        expected = render_jsonl(build_rows(inv.root, include_management), profile)
    except (FrontmatterError, OSError, UnicodeError, ValueError) as exc:
        inv.add("error", "invalid-asset-index", index_path, str(exc))
        return
    if actual != expected:
        inv.add(
            "error",
            "stale-asset-index",
            index_path,
            "Machine asset index does not match current assets",
        )


def summarize(inv: Inventory) -> dict[str, Any]:
    counts = Counter(finding.severity for finding in inv.findings)
    return {
        "root": str(inv.root),
        "markdown_files": len(inv.notes),
        "schema_v3_assets": sum(is_v3(fields) for fields in inv.fields_by_note.values()),
        "registered_sources": len(inv.source_registry),
        "findings": dict(sorted(counts.items())),
        "details": [finding.__dict__ for finding in inv.findings],
    }


def print_markdown(summary: dict[str, Any]) -> None:
    print("# Knowledge Base Health Check")
    print()
    print(f"- Root: `{summary['root']}`")
    print(f"- Markdown files: {summary['markdown_files']}")
    print(f"- Schema-v3 assets: {summary['schema_v3_assets']}")
    print(f"- Registered sources: {summary['registered_sources']}")
    counts = summary["findings"]
    print(
        "- Findings: "
        + (", ".join(f"{key}={value}" for key, value in counts.items()) if counts else "none")
    )
    print()
    if not summary["details"]:
        print("No health issues found by this check.")
        return
    print("| Severity | Code | File | Detail |")
    print("| --- | --- | --- | --- |")
    for item in summary["details"]:
        detail = str(item["detail"]).replace("|", "\\|")
        print(f"| {item['severity']} | {item['code']} | {item['file']} | {detail} |")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Lint a legacy or schema-v3 Markdown knowledge base."
    )
    parser.add_argument("root", help="Knowledge-base root directory")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of Markdown")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument(
        "--check-index", action="store_true", help="Verify the machine asset index is current"
    )
    parser.add_argument("--no-links", action="store_true", help="Skip Obsidian wikilink checks")
    args = parser.parse_args(argv)

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"Knowledge-base root is not a directory: {root}", file=sys.stderr)
        return 2

    try:
        inv = build_inventory(root)
        check_manifest(inv)
        fallback_required_files(inv)
        load_source_registry(inv)
        if not args.no_links:
            check_links(inv)
        check_frontmatter(inv)
        check_old_path_residue(inv)
        if args.check_index:
            check_asset_index(inv)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    summary = summarize(inv)
    if args.json:
        print(stable_json(summary, pretty=True))
    else:
        print_markdown(summary)

    if any(finding.severity == "error" for finding in inv.findings):
        return 1
    if args.strict and any(finding.severity == "warning" for finding in inv.findings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
