"""Build, write, or verify a deterministic JSONL retrieval index."""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from kb_common import (
    FrontmatterError,
    as_list,
    atomic_write_text,
    clean_scalar,
    ensure_safe_contained_path,
    exclusive_write_text,
    field_value,
    load_manifest,
    normalized_value,
    parse_json,
    read_text,
    split_frontmatter,
    stable_json,
)

INDEX_OWNERSHIP_KEY = "_knowledge_base_manager"
INDEX_OWNER = "knowledge-base-manager"
INDEX_DOCUMENT_TYPE = "asset-index"
INDEX_FORMAT_VERSION = 1
BUILD_PROFILE_DEFAULT = "default"
BUILD_PROFILE_INCLUDE_MANAGEMENT = "include-management"
SUPPORTED_BUILD_PROFILES = frozenset({BUILD_PROFILE_DEFAULT, BUILD_PROFILE_INCLUDE_MANAGEMENT})

RESTRICTED_ROUTING_FIELDS = (
    "schema_version",
    "type",
    "knowledge_role",
    "reuse_mode",
    "status",
    "scope_type",
    "primary_domain",
    "domains",
    "industries",
    "responsibilities",
    "languages",
    "sensitivity",
)

KNOWN_PROTECTED_PATHS = (
    "_meta/knowledge-base.json",
    "_meta/知识库清单.json",
    "_meta/knowledge-base-registry.json",
    "_meta/source-registry.jsonl",
    "_meta/来源注册表.jsonl",
)


INDEX_FIELDS = (
    "schema_version",
    "type",
    "knowledge_role",
    "truth_status",
    "preservation",
    "reuse_mode",
    "status",
    "scope_type",
    "primary_domain",
    "domains",
    "industries",
    "responsibilities",
    "topics",
    "retrieval_queries",
    "audiences",
    "languages",
    "confidence",
    "maturity",
    "evidence_strength",
    "time_sensitivity",
    "sensitivity",
    "source_id",
    "source_ids",
    "source_anchors",
    "provenance",
    "relations",
    "updated",
    "last_verified",
    "summary",
)

LEGACY_MARKERS = (
    "来源解析",
    "知识对象",
    "可执行资产",
    "证据验证",
    "素材拆解",
    "知识卡片",
    "模型方法",
    "来源档案",
    "案例证据",
    "输出成品",
)


def index_metadata(build_profile: str = BUILD_PROFILE_DEFAULT) -> dict[str, Any]:
    if build_profile not in SUPPORTED_BUILD_PROFILES:
        raise ValueError(f"Unsupported asset-index build profile: {build_profile}")
    return {
        INDEX_OWNERSHIP_KEY: {
            "document_type": INDEX_DOCUMENT_TYPE,
            "format_version": INDEX_FORMAT_VERSION,
            "owner": INDEX_OWNER,
        },
        "build_profile": build_profile,
    }


def _profile_from_record(record: dict[str, Any], source: str) -> str | None:
    marker = record.get(INDEX_OWNERSHIP_KEY)
    if marker is None:
        return None
    if not isinstance(marker, dict):
        raise ValueError(f"Invalid generated-index ownership marker in {source}")
    expected = {
        "document_type": INDEX_DOCUMENT_TYPE,
        "format_version": INDEX_FORMAT_VERSION,
        "owner": INDEX_OWNER,
    }
    if marker != expected:
        raise ValueError(f"Invalid generated-index ownership marker in {source}")
    profile = record.get("build_profile")
    if not isinstance(profile, str) or profile not in SUPPORTED_BUILD_PROFILES:
        raise ValueError(f"Unsupported or missing build_profile in {source}")
    return profile


def detect_profile(text: str, source: str = "<memory>") -> str | None:
    """Return a supported build profile when the first JSONL record owns the file."""
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        record = parse_json(line, f"{source}:{number}")
        if not isinstance(record, dict):
            return None
        return _profile_from_record(record, f"{source}:{number}")
    return None


def parse_index_document(
    text: str,
    source: str = "<memory>",
    *,
    require_owned: bool = False,
) -> tuple[str | None, list[dict[str, Any]]]:
    """Parse owned or legacy JSONL and separate metadata from asset rows."""
    records: list[tuple[int, dict[str, Any]]] = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        record = parse_json(line, f"{source}:{number}")
        if not isinstance(record, dict):
            raise ValueError(f"Index row must be an object at {source}:{number}")
        records.append((number, record))

    profile: str | None = None
    if records:
        number, first = records[0]
        profile = _profile_from_record(first, f"{source}:{number}")
    if require_owned and profile is None:
        raise ValueError(f"Asset index lacks the generated-index ownership marker: {source}")

    row_records = records[1:] if profile is not None else records
    rows: list[dict[str, Any]] = []
    for number, record in row_records:
        if INDEX_OWNERSHIP_KEY in record:
            raise ValueError(
                f"Generated-index metadata must be the first record: {source}:{number}"
            )
        rows.append(record)
    return profile, rows


def title_from_text(path: Path, body: str) -> str:
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def first_paragraph(body: str) -> str:
    paragraphs: list[str] = []
    current: list[str] = []
    in_fence = False
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not stripped:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        if stripped.startswith(("#", "|", "- ", "* ", ">", "![")):
            continue
        current.append(stripped)
    if current:
        paragraphs.append(" ".join(current))
    return paragraphs[0][:320] if paragraphs else ""


def infer_legacy(path: Path, fields: dict[str, Any]) -> dict[str, str]:
    rel = path.as_posix()
    note_type = field_value(fields, "type")

    if note_type == "model" or "模型方法" in rel or "核心模型" in rel:
        role, truth, preservation, reuse = "model", "model-synthesis", "derived", "analyze-only"
    elif note_type == "source-profile" or "来源档案" in rel or "作者档案" in rel:
        role, truth, preservation, reuse = (
            "source-profile",
            "source-claim",
            "normalized",
            "analyze-only",
        )
    elif note_type in {"material-index", "source-map"} or "素材拆解" in rel or "素材索引" in rel:
        role, truth, preservation, reuse = "logic-map", "source-claim", "derived", "analyze-only"
    elif "案例证据" in rel or note_type.startswith("evidence"):
        role, truth, preservation, reuse = "evidence", "source-record", "anchored", "reference-only"
    elif note_type == "output" or "输出成品" in rel:
        role, truth, preservation, reuse = "output", "generated", "derived", "reference-only"
    elif note_type == "knowledge-card" or "知识卡片" in rel:
        role, truth, preservation, reuse = "claim", "source-claim", "normalized", "analyze-only"
    else:
        role, truth, preservation, reuse = (
            "management",
            "model-synthesis",
            "derived",
            "reference-only",
        )

    return {
        "knowledge_role": role,
        "truth_status": truth,
        "preservation": preservation,
        "reuse_mode": reuse,
    }


def is_v3(fields: dict[str, Any]) -> bool:
    return clean_scalar(fields.get("schema_version")) == "3" or any(
        key in fields for key in ("knowledge_role", "truth_status", "preservation", "reuse_mode")
    )


def is_indexable(path: Path, fields: dict[str, Any], include_management: bool) -> bool:
    rel = path.as_posix()
    role = field_value(fields, "knowledge_role")
    if role:
        return include_management or role != "management"
    if rel.startswith("_meta/") or rel.startswith("00-"):
        return include_management
    return any(marker in rel for marker in LEGACY_MARKERS)


def normalize_index_field(name: str, value: Any) -> Any:
    if name in {
        "domains",
        "industries",
        "responsibilities",
        "topics",
        "retrieval_queries",
        "audiences",
        "languages",
        "source_ids",
    }:
        return as_list(value)
    return normalized_value(value)


def iter_markdown_files(root: Path) -> list[Path]:
    resolved_root = root.resolve(strict=True)
    notes: list[Path] = []
    for directory, directory_names, file_names in os.walk(
        resolved_root, topdown=True, followlinks=False
    ):
        current = Path(directory)
        safe_directories: list[str] = []
        for name in sorted(directory_names):
            candidate = current / name
            try:
                ensure_safe_contained_path(resolved_root, candidate)
            except (OSError, ValueError):
                continue
            safe_directories.append(name)
        directory_names[:] = safe_directories

        for name in sorted(file_names):
            if Path(name).suffix.casefold() != ".md":
                continue
            candidate = current / name
            try:
                safe_note = ensure_safe_contained_path(resolved_root, candidate)
            except (OSError, ValueError):
                continue
            if safe_note.is_file():
                notes.append(safe_note)
    return sorted(notes, key=lambda path: path.relative_to(resolved_root).as_posix())


def build_rows(root: Path, include_management: bool = False) -> list[dict[str, Any]]:
    root = root.resolve(strict=True)
    rows: list[dict[str, Any]] = []
    for note in iter_markdown_files(root):
        note = ensure_safe_contained_path(root, note)
        rel = note.relative_to(root)
        text = read_text(note)
        fields, body = split_frontmatter(text, rel.as_posix())
        if not is_indexable(rel, fields, include_management):
            continue

        legacy = not is_v3(fields)
        inferred = infer_legacy(rel, fields) if legacy else {}
        asset_id = field_value(fields, "id") or f"legacy:{rel.as_posix()}"
        row: dict[str, Any] = {
            "id": asset_id,
            "title": "[restricted]"
            if field_value(fields, "sensitivity") == "restricted"
            else title_from_text(note, body),
            "path": rel.as_posix(),
            "asset_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "legacy_inferred": legacy,
        }

        restricted = field_value(fields, "sensitivity") == "restricted"
        selected_fields = RESTRICTED_ROUTING_FIELDS if restricted else INDEX_FIELDS
        for name in selected_fields:
            if name in fields:
                row[name] = normalize_index_field(name, fields[name])
        for name, value in inferred.items():
            if not restricted or name in RESTRICTED_ROUTING_FIELDS:
                row.setdefault(name, value)

        if restricted:
            row["restricted"] = True
        elif not row.get("summary"):
            row["summary"] = first_paragraph(body)
        rows.append(row)
    return rows


def render_jsonl(rows: list[dict[str, Any]], build_profile: str = BUILD_PROFILE_DEFAULT) -> str:
    lines = [stable_json(index_metadata(build_profile)), *(stable_json(row) for row in rows)]
    return "\n".join(lines) + "\n"


def default_index_path(root: Path) -> Path:
    _, manifest = load_manifest(root)
    paths = manifest.get("paths", {})
    configured = paths.get("asset_index") if isinstance(paths, dict) else None
    relative = clean_scalar(configured) or "00-AI入口/资产索引.jsonl"
    return ensure_safe_contained_path(root, root / relative, allow_missing=True)


def resolve_destination(root: Path, output: str | None) -> Path:
    if not output:
        return default_index_path(root)
    candidate = Path(output).expanduser()
    candidate = candidate if candidate.is_absolute() else root / candidate
    return ensure_safe_contained_path(root, candidate, allow_missing=True)


def protected_destination_paths(
    root: Path, manifest_path: Path | None, manifest: dict[str, Any]
) -> set[Path]:
    protected = {
        ensure_safe_contained_path(root, root / relative, allow_missing=True)
        for relative in KNOWN_PROTECTED_PATHS
    }
    if manifest_path is not None:
        protected.add(ensure_safe_contained_path(root, manifest_path))

    configured_paths = manifest.get("paths", {})
    if not isinstance(configured_paths, dict):
        raise ValueError("Manifest field 'paths' must be an object")
    for name, value in configured_paths.items():
        if name == "asset_index":
            continue
        relative = clean_scalar(value)
        if relative:
            protected.add(ensure_safe_contained_path(root, root / relative, allow_missing=True))
    return protected


def validate_write_destination(root: Path, destination: Path) -> bool:
    destination = ensure_safe_contained_path(root, destination, allow_missing=True)
    if destination.suffix.casefold() != ".jsonl":
        raise ValueError(f"Asset-index destination must use the .jsonl extension: {destination}")

    manifest_path, manifest = load_manifest(root)
    if destination in protected_destination_paths(root, manifest_path, manifest):
        raise ValueError(
            f"Refusing to write an index over a protected semantic file: {destination}"
        )

    if not destination.exists():
        return False
    if not destination.is_file():
        raise ValueError(f"Asset-index destination is not a regular file: {destination}")

    before = destination.stat()
    try:
        parse_index_document(read_text(destination), str(destination), require_owned=True)
    except (OSError, UnicodeError, ValueError) as exc:
        raise ValueError(
            f"Refusing to overwrite a file not owned as a generated asset index: {destination}: "
            f"{exc}"
        ) from exc
    after = destination.stat()
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if identity_before != identity_after:
        raise ValueError(
            f"Asset-index destination changed during ownership validation: {destination}"
        )
    return True


def validate_unique_ids(rows: list[dict[str, Any]]) -> list[str]:
    ids = [clean_scalar(row.get("id")) for row in rows]
    return sorted(asset_id for asset_id, count in Counter(ids).items() if asset_id and count > 1)


def print_summary(rows: list[dict[str, Any]], destination: Path | None) -> None:
    roles = Counter(clean_scalar(row.get("knowledge_role")) or "unknown" for row in rows)
    legacy_count = sum(bool(row.get("legacy_inferred")) for row in rows)
    print(f"Indexed assets: {len(rows)}")
    print(f"Legacy-inferred assets: {legacy_count}")
    print("Roles: " + ", ".join(f"{key}={value}" for key, value in sorted(roles.items())))
    if destination is not None:
        print(f"Index: {destination}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build or verify a deterministic knowledge asset index."
    )
    parser.add_argument("root", help="Knowledge-base root directory")
    parser.add_argument("--output", help="Index path relative to the knowledge-base root")
    parser.add_argument("--write", action="store_true", help="Atomically write the index")
    parser.add_argument(
        "--check", action="store_true", help="Fail when the on-disk index is missing or stale"
    )
    parser.add_argument("--summary", action="store_true", help="Print a compact summary")
    parser.add_argument(
        "--include-management", action="store_true", help="Include management/navigation notes"
    )
    args = parser.parse_args(argv)

    try:
        root = Path(args.root).expanduser().resolve(strict=True)
    except OSError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"Knowledge-base root is not a directory: {root}", file=sys.stderr)
        return 2

    try:
        rows = build_rows(root, args.include_management)
    except (OSError, UnicodeError, FrontmatterError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    duplicates = validate_unique_ids(rows)
    if duplicates:
        print("Duplicate asset IDs: " + ", ".join(duplicates), file=sys.stderr)
        return 1

    build_profile = (
        BUILD_PROFILE_INCLUDE_MANAGEMENT if args.include_management else BUILD_PROFILE_DEFAULT
    )
    payload = render_jsonl(rows, build_profile)
    try:
        destination = (
            resolve_destination(root, args.output)
            if (args.write or args.check or args.output)
            else None
        )
    except (OSError, UnicodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.check:
        if destination is None or not destination.is_file():
            print(f"Asset index is missing: {destination}", file=sys.stderr)
            return 1
        try:
            on_disk = read_text(destination)
            parse_index_document(on_disk, str(destination))
            if on_disk != payload:
                print(f"Asset index is stale: {destination}", file=sys.stderr)
                return 1
        except (OSError, UnicodeError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 2

    if args.write:
        if destination is None:
            raise AssertionError("destination must be resolved for --write")
        try:
            replace_existing = validate_write_destination(root, destination)
            if replace_existing:
                atomic_write_text(destination, payload)
            else:
                exclusive_write_text(destination, payload)
        except (OSError, UnicodeError, ValueError) as exc:
            print(str(exc), file=sys.stderr)
            return 2

    if args.summary:
        print_summary(rows, destination)
    elif not args.write and not args.check:
        sys.stdout.write(payload)
    elif args.check:
        print(f"Asset index is current: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
