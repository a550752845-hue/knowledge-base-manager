"""Snapshot and verify immutable source files without modifying source locations."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import os
import stat as stat_module
import sys
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from kb_common import atomic_write_text, exclusive_write_text, parse_json, read_text, stable_json


DEFAULT_EXCLUDES = (".git", ".git/**", "__pycache__", "**/__pycache__/**")
MANIFEST_VERSION = 2
MANIFEST_OWNER = "knowledge-base-manager/source-integrity"
ROOT_KINDS = frozenset(("file", "directory", "symlink", "junction"))
ENTRY_KINDS = frozenset(("file", "symlink", "junction"))
LINK_KINDS = frozenset(("symlink", "junction"))


class SourceChangedDuringHashError(RuntimeError):
    """Raised when a file is not stable for the complete hashing operation."""


def clean_path(value: Any) -> str:
    return str(value).replace("\\", "/")


def lexical_absolute(path: Path) -> Path:
    """Make a path absolute without resolving a final link or junction."""

    return Path(os.path.abspath(os.fspath(path.expanduser())))


def normalized_path_key(path: Path | str) -> str:
    return os.path.normcase(os.path.normpath(os.fspath(path)))


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


def link_kind(path: Path) -> str | None:
    if path.is_symlink():
        return "symlink"
    if is_junction(path):
        return "junction"
    return None


def path_exists_lexically(path: Path) -> bool:
    return os.path.lexists(os.fspath(path))


def stat_signature(result: os.stat_result) -> tuple[int, ...]:
    return (
        result.st_dev,
        result.st_ino,
        result.st_size,
        result.st_mtime_ns,
    )


def hash_file_stable(path: Path, chunk_size: int = 1024 * 1024) -> tuple[str, os.stat_result]:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        before = os.fstat(handle.fileno())
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
        after = os.fstat(handle.fileno())

    path_after = path.stat()
    if (
        stat_signature(before) != stat_signature(after)
        or stat_signature(after) != stat_signature(path_after)
        or link_kind(path) is not None
    ):
        raise SourceChangedDuringHashError(
            f"Source changed while hashing; retry from a stable state: {path}"
        )
    return digest.hexdigest(), path_after


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    return hash_file_stable(path, chunk_size)[0]


def should_exclude(relative: str, patterns: list[str]) -> bool:
    normalized = relative.replace("\\", "/")
    return any(
        fnmatch.fnmatch(normalized, pattern)
        or fnmatch.fnmatch(PurePosixPath(normalized).name, pattern)
        for pattern in patterns
    )


def iter_directory_entries(
    directory: Path, excludes: list[str], prefix: PurePosixPath | None = None
) -> Iterable[tuple[Path, str, str]]:
    with os.scandir(directory) as scanner:
        entries = sorted(scanner, key=lambda item: os.path.normcase(item.name))

    for item in entries:
        relative_path = PurePosixPath(item.name) if prefix is None else prefix / item.name
        relative = relative_path.as_posix()
        if should_exclude(relative, excludes):
            continue

        path = Path(item.path)
        nested_link_kind = link_kind(path)
        if nested_link_kind is not None:
            yield path, relative, nested_link_kind
            continue
        if item.is_file(follow_symlinks=False):
            yield path, relative, "file"
            continue
        if item.is_dir(follow_symlinks=False):
            yield from iter_directory_entries(path, excludes, relative_path)
            continue
        raise ValueError(f"Unsupported source entry type: {path}")


def iter_source_entries(source: Path, excludes: list[str]) -> Iterable[tuple[Path, str, str]]:
    """Traverse an explicit root target, but never links found below that root."""

    resolved = source.resolve(strict=True)
    if resolved.is_file():
        yield resolved, ".", "file"
        return
    if resolved.is_dir():
        yield from iter_directory_entries(resolved, excludes)
        return
    raise ValueError(f"Source root must resolve to a file or directory: {source}")


def iter_source_files(source: Path, excludes: list[str]) -> Iterable[Path]:
    """Compatibility wrapper for callers that only need discovered paths."""

    for path, _, _ in iter_source_entries(source, excludes):
        yield path


def resolved_identity(path: Path) -> dict[str, Any]:
    resolved = path.resolve(strict=True)
    result = resolved.stat()
    if resolved.is_file():
        kind = "file"
    elif resolved.is_dir():
        kind = "directory"
    else:
        raise ValueError(f"Source target must be a file or directory: {path}")
    return {
        "path": str(resolved),
        "kind": kind,
        "device": result.st_dev,
        "inode": result.st_ino,
    }


def root_id_for(path: Path) -> str:
    identity = normalized_path_key(path).encode("utf-8", errors="surrogatepass")
    return f"root-{hashlib.sha256(identity).hexdigest()[:16]}"


def root_descriptor(source: Path) -> dict[str, Any]:
    source = lexical_absolute(source)
    root_link_kind = link_kind(source)
    if not path_exists_lexically(source):
        raise FileNotFoundError(f"Source path does not exist: {source}")

    if root_link_kind is not None:
        kind = root_link_kind
        target: str | None = os.readlink(source)
    elif source.is_file():
        kind = "file"
        target = None
    elif source.is_dir():
        kind = "directory"
        target = None
    else:
        raise ValueError(f"Source root must be a file, directory, symlink, or junction: {source}")

    return {
        "id": root_id_for(source),
        "path": str(source),
        "kind": kind,
        "target": target,
        "resolved_identity": resolved_identity(source),
    }


def entry_identity(path: Path, kind: str) -> tuple[str, str]:
    if kind == "file":
        return kind, normalized_path_key(path.resolve(strict=False))
    return "link", normalized_path_key(lexical_absolute(path))


def root_scan_order(roots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def sort_key(root: dict[str, Any]) -> tuple[int, str]:
        resolved = Path(root["resolved_identity"]["path"])
        return (-len(resolved.parts), normalized_path_key(root["path"]))

    return sorted(roots, key=sort_key)


def entry_for(
    path: Path, root_id: str | None = None, relative_path: str | None = None, kind: str = "file"
) -> dict[str, Any]:
    """Build a v2 row, while retaining the old one-argument helper behavior."""

    if root_id is None or relative_path is None:
        absolute = lexical_absolute(path)
        nested_link_kind = link_kind(absolute)
        if nested_link_kind is not None:
            return {
                "path": str(absolute),
                "kind": nested_link_kind,
                "target": os.readlink(absolute),
            }
        digest, result = hash_file_stable(absolute)
        return {
            "path": str(absolute.resolve(strict=False)),
            "kind": "file",
            "size": result.st_size,
            "mtime_ns": result.st_mtime_ns,
            "sha256": digest,
        }

    row: dict[str, Any] = {
        "root_id": root_id,
        "relative_path": relative_path,
        "kind": kind,
    }
    if kind in LINK_KINDS:
        row["target"] = os.readlink(path)
        try:
            row["resolved_identity"] = resolved_identity(path)
        except (FileNotFoundError, RuntimeError):
            row["resolved_identity"] = None
        return row

    digest, result = hash_file_stable(path)
    row.update(
        {
            "size": result.st_size,
            "mtime_ns": result.st_mtime_ns,
            "sha256": digest,
        }
    )
    return row


def validate_excludes(value: Any) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError("Integrity manifest excludes must be an array of strings")
    return list(value)


def validate_resolved_identity(value: Any, context: str) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{context} resolved_identity must be an object")
    if not isinstance(value.get("path"), str) or not value["path"]:
        raise ValueError(f"{context} resolved_identity path must be a non-empty string")
    if value.get("kind") not in {"file", "directory"}:
        raise ValueError(f"{context} resolved_identity kind must be file or directory")
    for field in ("device", "inode"):
        if not isinstance(value.get(field), int) or isinstance(value.get(field), bool):
            raise ValueError(f"{context} resolved_identity {field} must be an integer")


def validate_relative_path(value: Any) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("Integrity manifest relative_path must be a non-empty POSIX path")
    relative = PurePosixPath(value)
    if relative.is_absolute() or ".." in relative.parts or value not in {".", relative.as_posix()}:
        raise ValueError(f"Integrity manifest relative_path is unsafe or non-canonical: {value!r}")
    return value


def validate_file_hash_fields(row: dict[str, Any], context: str) -> None:
    size = row.get("size")
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        raise ValueError(f"{context} size must be a non-negative integer")
    digest = row.get("sha256")
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
    ):
        raise ValueError(f"{context} sha256 must be a lowercase hexadecimal SHA-256 digest")
    mtime_ns = row.get("mtime_ns")
    if not isinstance(mtime_ns, int) or isinstance(mtime_ns, bool):
        raise ValueError(f"{context} mtime_ns must be an integer")


def validate_v2_manifest(
    manifest: dict[str, Any], *, require_owner: bool = True
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    if require_owner and manifest.get("manifest_owner") != MANIFEST_OWNER:
        raise ValueError("Integrity manifest is not owned by this source-integrity tool")

    excludes = validate_excludes(manifest.get("excludes"))
    raw_roots = manifest.get("source_roots")
    if not isinstance(raw_roots, list):
        raise ValueError("Integrity manifest source_roots must be an array")
    raw_files = manifest.get("files")
    if not isinstance(raw_files, list):
        raise ValueError("Integrity manifest files must be an array")

    roots: list[dict[str, Any]] = []
    root_ids: set[str] = set()
    for position, root in enumerate(raw_roots):
        context = f"Integrity manifest source_roots[{position}]"
        if not isinstance(root, dict):
            raise ValueError(f"{context} must be an object")
        root_id = root.get("id")
        if not isinstance(root_id, str) or not root_id:
            raise ValueError(f"{context} id must be a non-empty string")
        if root_id in root_ids:
            raise ValueError(f"Integrity manifest has duplicate root id: {root_id}")
        root_ids.add(root_id)
        if not isinstance(root.get("path"), str) or not root["path"]:
            raise ValueError(f"{context} path must be a non-empty string")
        if root.get("kind") not in ROOT_KINDS:
            raise ValueError(f"{context} kind is unsupported")
        target = root.get("target")
        if root["kind"] in LINK_KINDS:
            if not isinstance(target, str):
                raise ValueError(f"{context} target must be a string for a link root")
        elif target is not None:
            raise ValueError(f"{context} target must be null for a non-link root")
        validate_resolved_identity(root.get("resolved_identity"), context)
        roots.append(root)

    files: list[dict[str, Any]] = []
    file_keys: set[tuple[str, str]] = set()
    for position, row in enumerate(raw_files):
        context = f"Integrity manifest files[{position}]"
        if not isinstance(row, dict):
            raise ValueError(f"{context} must be an object")
        root_id = row.get("root_id")
        if not isinstance(root_id, str) or root_id not in root_ids:
            raise ValueError(f"{context} root_id must reference a declared root")
        relative = validate_relative_path(row.get("relative_path"))
        key = (root_id, relative)
        if key in file_keys:
            raise ValueError(f"Integrity manifest has duplicate file row: {root_id}:{relative}")
        file_keys.add(key)
        kind = row.get("kind")
        if kind not in ENTRY_KINDS:
            raise ValueError(f"{context} kind is unsupported")
        if kind == "file":
            validate_file_hash_fields(row, context)
        else:
            if not isinstance(row.get("target"), str):
                raise ValueError(f"{context} target must be a string for a link entry")
            identity = row.get("resolved_identity")
            if identity is not None:
                validate_resolved_identity(identity, context)
        files.append(row)
    return roots, files, excludes


def validate_v1_manifest(
    manifest: dict[str, Any],
) -> tuple[list[str], list[dict[str, Any]], list[str]]:
    raw_roots = manifest.get("source_roots")
    if not isinstance(raw_roots, list) or any(
        not isinstance(item, str) or not item for item in raw_roots
    ):
        raise ValueError("Integrity manifest source_roots must be an array of path strings")
    excludes = validate_excludes(manifest.get("excludes", list(DEFAULT_EXCLUDES)))
    raw_files = manifest.get("files")
    if not isinstance(raw_files, list):
        raise ValueError("Integrity manifest files must be an array")

    files: list[dict[str, Any]] = []
    seen: set[str] = set()
    for position, row in enumerate(raw_files):
        context = f"Integrity manifest files[{position}]"
        if not isinstance(row, dict):
            raise ValueError(f"{context} must be an object")
        raw_path = row.get("path")
        if not isinstance(raw_path, str) or not raw_path:
            raise ValueError(f"{context} path must be a non-empty string")
        key = normalized_path_key(raw_path)
        if key in seen:
            raise ValueError(f"Integrity manifest has duplicate file path: {raw_path}")
        seen.add(key)
        kind = row.get("kind", "file")
        if kind not in {"file", "symlink"}:
            raise ValueError(f"{context} kind is unsupported")
        if kind == "file":
            validate_file_hash_fields(row, context)
        elif not isinstance(row.get("target"), str):
            raise ValueError(f"{context} target must be a string for a symlink")
        files.append(row)
    return list(raw_roots), files, excludes


def build_snapshot(
    sources: list[Path], excludes: list[str], output: Path | None = None
) -> dict[str, Any]:
    if not isinstance(sources, list) or not sources:
        raise ValueError("At least one source root is required")
    if any(not isinstance(source, Path) for source in sources):
        raise ValueError("Source roots must be paths")
    excludes = validate_excludes(excludes)

    roots_by_path: dict[str, dict[str, Any]] = {}
    for source in sources:
        descriptor = root_descriptor(source)
        roots_by_path.setdefault(normalized_path_key(descriptor["path"]), descriptor)
    roots = sorted(roots_by_path.values(), key=lambda item: normalized_path_key(item["path"]))

    seen_entries: set[tuple[str, str]] = set()
    files: list[dict[str, Any]] = []
    output_key = normalized_path_key(output.resolve(strict=False)) if output else None
    for root in root_scan_order(roots):
        source = Path(root["path"])
        for path, relative, kind in iter_source_entries(source, excludes):
            if (
                output_key is not None
                and normalized_path_key(path.resolve(strict=False)) == output_key
            ):
                continue
            identity = entry_identity(path, kind)
            if identity in seen_entries:
                continue
            seen_entries.add(identity)
            files.append(entry_for(path, root["id"], relative, kind))

    files.sort(
        key=lambda item: (
            item["root_id"],
            os.path.normcase(clean_path(item["relative_path"])),
        )
    )
    return {
        "manifest_version": MANIFEST_VERSION,
        "manifest_owner": MANIFEST_OWNER,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "source_roots": roots,
        "excludes": excludes,
        "files": files,
    }


def display_entry_path(root_path: Path, relative: str) -> str:
    return str(root_path if relative == "." else root_path / Path(*PurePosixPath(relative).parts))


def nested_link_component(content_root: Path, relative: str) -> Path | None:
    if relative == ".":
        return None
    candidate = content_root
    parts = PurePosixPath(relative).parts
    for part in parts[:-1]:
        candidate /= part
        if link_kind(candidate) is not None:
            return candidate
    return None


def compare_root(root: dict[str, Any], changed: list[dict[str, Any]], missing: list[str]) -> None:
    path = Path(root["path"])
    expected_kind = root["kind"]
    actual_link_kind = link_kind(path)
    if not path_exists_lexically(path):
        missing.append(str(path))
        return

    if actual_link_kind is not None:
        actual_kind = actual_link_kind
    elif path.is_file():
        actual_kind = "file"
    elif path.is_dir():
        actual_kind = "directory"
    else:
        actual_kind = "other"
    if actual_kind != expected_kind:
        changed.append(
            {
                "path": str(path),
                "reason": "root-kind",
                "expected": expected_kind,
                "actual": actual_kind,
            }
        )

    if expected_kind in LINK_KINDS:
        actual_target = os.readlink(path) if actual_link_kind is not None else None
        if actual_target != root["target"]:
            changed.append(
                {
                    "path": str(path),
                    "reason": "root-target",
                    "expected": root["target"],
                    "actual": actual_target,
                }
            )

    try:
        actual_identity = resolved_identity(path)
    except (FileNotFoundError, RuntimeError, ValueError):
        actual_identity = None
    if actual_identity != root["resolved_identity"]:
        changed.append(
            {
                "path": str(path),
                "reason": "root-resolved-identity",
                "expected": root["resolved_identity"],
                "actual": actual_identity,
            }
        )


def verify_v2(manifest: dict[str, Any], check_new: bool) -> dict[str, Any]:
    roots, expected_rows, excludes = validate_v2_manifest(manifest)
    roots_by_id = {root["id"]: root for root in roots}
    changed: list[dict[str, Any]] = []
    missing: list[str] = []
    missing_roots: list[str] = []

    for root in roots:
        compare_root(root, changed, missing_roots)

    content_roots: dict[str, Path | None] = {}
    for root in roots:
        try:
            content_roots[root["id"]] = Path(root["path"]).resolve(strict=True)
        except (FileNotFoundError, RuntimeError):
            content_roots[root["id"]] = None

    for row in expected_rows:
        root = roots_by_id[row["root_id"]]
        root_path = Path(root["path"])
        relative = row["relative_path"]
        display_path = display_entry_path(root_path, relative)
        content_root = content_roots[row["root_id"]]
        if content_root is None:
            missing.append(display_path)
            continue
        unsafe_component = nested_link_component(content_root, relative)
        if unsafe_component is not None:
            changed.append(
                {
                    "path": display_path,
                    "reason": "path-through-link",
                    "actual": str(unsafe_component),
                }
            )
            continue
        path = (
            content_root if relative == "." else content_root / Path(*PurePosixPath(relative).parts)
        )
        if not path_exists_lexically(path):
            missing.append(display_path)
            continue

        expected_kind = row["kind"]
        actual_link_kind = link_kind(path)
        if expected_kind in LINK_KINDS:
            if actual_link_kind != expected_kind:
                changed.append(
                    {
                        "path": display_path,
                        "reason": "link-kind",
                        "expected": expected_kind,
                        "actual": actual_link_kind or "non-link",
                    }
                )
                continue
            actual_target = os.readlink(path)
            if actual_target != row["target"]:
                changed.append(
                    {
                        "path": display_path,
                        "reason": "link-target",
                        "expected": row["target"],
                        "actual": actual_target,
                    }
                )
            try:
                actual_identity = resolved_identity(path)
            except (FileNotFoundError, RuntimeError, ValueError):
                actual_identity = None
            if actual_identity != row.get("resolved_identity"):
                changed.append(
                    {
                        "path": display_path,
                        "reason": "link-resolved-identity",
                        "expected": row.get("resolved_identity"),
                        "actual": actual_identity,
                    }
                )
            continue

        if actual_link_kind is not None or not path.is_file():
            changed.append({"path": display_path, "reason": "file-kind"})
            continue
        try:
            actual_hash, result = hash_file_stable(path)
        except SourceChangedDuringHashError:
            changed.append({"path": display_path, "reason": "changed-during-hash"})
            continue
        if result.st_size != row["size"] or actual_hash != row["sha256"]:
            changed.append(
                {
                    "path": display_path,
                    "reason": "content",
                    "expected_size": row["size"],
                    "actual_size": result.st_size,
                    "expected_sha256": row["sha256"],
                    "actual_sha256": actual_hash,
                }
            )

    unexpected: list[str] = []
    if check_new:
        expected_keys = {(row["root_id"], row["relative_path"]) for row in expected_rows}
        seen_entries: set[tuple[str, str]] = set()
        for root in root_scan_order(roots):
            source = Path(root["path"])
            try:
                entries = iter_source_entries(source, excludes)
                for path, relative, kind in entries:
                    identity = entry_identity(path, kind)
                    if identity in seen_entries:
                        continue
                    seen_entries.add(identity)
                    if (root["id"], relative) not in expected_keys:
                        unexpected.append(display_entry_path(source, relative))
            except (FileNotFoundError, RuntimeError):
                continue

    return {
        "checked_files": len(expected_rows),
        "ok": not changed and not missing and not missing_roots and not unexpected,
        "changed": changed,
        "missing": sorted(set(missing), key=os.path.normcase),
        "missing_roots": sorted(set(missing_roots), key=os.path.normcase),
        "unexpected": sorted(set(unexpected), key=os.path.normcase),
    }


def verify_v1(manifest: dict[str, Any], check_new: bool) -> dict[str, Any]:
    raw_roots, expected_rows, excludes = validate_v1_manifest(manifest)
    changed: list[dict[str, Any]] = []
    missing: list[str] = []
    expected_paths: set[str] = set()
    for row in expected_rows:
        path = Path(row["path"])
        expected_paths.add(normalized_path_key(path.resolve(strict=False)))
        if not path_exists_lexically(path):
            missing.append(str(path))
            continue
        kind = row.get("kind", "file")
        if kind == "symlink":
            actual_target = os.readlink(path) if path.is_symlink() else None
            if actual_target != row["target"]:
                changed.append(
                    {
                        "path": str(path),
                        "reason": "symlink-target",
                        "expected": row["target"],
                        "actual": actual_target,
                    }
                )
            continue
        if link_kind(path) is not None or not path.is_file():
            changed.append({"path": str(path), "reason": "file-kind"})
            continue
        try:
            actual_hash, result = hash_file_stable(path)
        except SourceChangedDuringHashError:
            changed.append({"path": str(path), "reason": "changed-during-hash"})
            continue
        if result.st_size != row["size"] or actual_hash != row["sha256"]:
            changed.append(
                {
                    "path": str(path),
                    "reason": "content",
                    "expected_size": row["size"],
                    "actual_size": result.st_size,
                    "expected_sha256": row["sha256"],
                    "actual_sha256": actual_hash,
                }
            )

    unexpected: list[str] = []
    missing_roots: list[str] = []
    if check_new:
        seen: set[str] = set()
        for raw_root in raw_roots:
            root = Path(raw_root)
            if not path_exists_lexically(root):
                missing_roots.append(str(root))
                continue
            try:
                entries = iter_source_entries(root, excludes)
                for path, _, _ in entries:
                    key = normalized_path_key(path.resolve(strict=False))
                    if key in seen:
                        continue
                    seen.add(key)
                    if key not in expected_paths:
                        unexpected.append(str(path.resolve(strict=False)))
            except (FileNotFoundError, RuntimeError):
                missing_roots.append(str(root))

    return {
        "checked_files": len(expected_rows),
        "ok": not changed and not missing and not missing_roots and not unexpected,
        "changed": changed,
        "missing": sorted(set(missing), key=os.path.normcase),
        "missing_roots": sorted(set(missing_roots), key=os.path.normcase),
        "unexpected": sorted(set(unexpected), key=os.path.normcase),
    }


def verify_snapshot(manifest: dict[str, Any], check_new: bool) -> dict[str, Any]:
    version = manifest.get("manifest_version")
    if version == 2 and not isinstance(version, bool):
        return verify_v2(manifest, check_new)
    if version == 1 and not isinstance(version, bool):
        return verify_v1(manifest, check_new)
    raise ValueError("Unsupported or missing source-integrity manifest_version")


def is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def validate_output_location(output: Path, roots: list[dict[str, Any]]) -> None:
    output = lexical_absolute(output)
    output_resolved = output.resolve(strict=False)
    for root in roots:
        lexical_root = Path(root["path"])
        resolved_root = Path(root["resolved_identity"]["path"])
        target_kind = root["resolved_identity"]["kind"]
        if target_kind == "directory":
            if is_relative_to(output, lexical_root) or is_relative_to(
                output_resolved, resolved_root
            ):
                raise ValueError(
                    "Integrity manifest must be stored outside immutable source directories"
                )
        elif output == lexical_root or output_resolved == resolved_root:
            raise ValueError("Integrity manifest cannot overwrite a source path")


def read_owned_manifest(output: Path) -> str | None:
    if not path_exists_lexically(output):
        return None
    output_link_kind = link_kind(output)
    if output_link_kind is not None:
        raise ValueError(f"Integrity manifest output cannot be a {output_link_kind}: {output}")
    if output.is_dir():
        raise ValueError(f"Integrity manifest output cannot be a directory: {output}")
    if not output.is_file():
        raise ValueError(f"Integrity manifest output must be a regular file: {output}")
    text = read_text(output)
    try:
        loaded = parse_json(text, str(output))
    except ValueError as exc:
        raise ValueError(
            "Existing output is not a source-integrity manifest owned by this tool"
        ) from exc
    if not isinstance(loaded, dict) or loaded.get("manifest_version") != MANIFEST_VERSION:
        raise ValueError("Existing output is not a source-integrity manifest owned by this tool")
    validate_v2_manifest(loaded)
    return text


def snapshot_command(args: argparse.Namespace) -> int:
    sources = [lexical_absolute(Path(value)) for value in args.source]
    output = lexical_absolute(Path(args.output))
    excludes = list(dict.fromkeys([*DEFAULT_EXCLUDES, *args.exclude]))
    try:
        excludes = validate_excludes(excludes)
        roots = [root_descriptor(source) for source in sources]
        validate_output_location(output, roots)
        existing_payload = read_owned_manifest(output)
        snapshot = build_snapshot(sources, excludes, output)
    except (OSError, RuntimeError, UnicodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Source files discovered: {len(snapshot['files'])}")
    print(f"Manifest: {output}")
    if not args.apply:
        print("Dry run only; add --apply to write the integrity manifest.")
        return 0

    payload = stable_json(snapshot, pretty=True) + "\n"
    try:
        if existing_payload is None:
            exclusive_write_text(output, payload)
        else:
            if read_owned_manifest(output) != existing_payload:
                raise FileExistsError(
                    "Integrity manifest changed concurrently; existing output was preserved"
                )
            atomic_write_text(output, payload)
    except (OSError, RuntimeError, UnicodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print("Integrity manifest written atomically.")
    return 0


def verify_command(args: argparse.Namespace) -> int:
    manifest_path = lexical_absolute(Path(args.manifest))
    try:
        manifest = parse_json(read_text(manifest_path), str(manifest_path))
        if not isinstance(manifest, dict):
            raise ValueError("Integrity manifest must be a JSON object")
        result = verify_snapshot(manifest, args.check_new)
    except (OSError, RuntimeError, UnicodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.json:
        print(stable_json(result, pretty=True))
    else:
        print(f"Checked files: {result['checked_files']}")
        print(f"Changed: {len(result['changed'])}")
        print(f"Missing: {len(result['missing'])}")
        print(f"Missing roots: {len(result['missing_roots'])}")
        print(f"Unexpected: {len(result['unexpected'])}")
        print("Source integrity: " + ("OK" if result["ok"] else "FAILED"))
    return 0 if result["ok"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Snapshot or verify immutable knowledge sources.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    snapshot = subparsers.add_parser("snapshot", help="Create a source integrity baseline")
    snapshot.add_argument(
        "--source", action="append", required=True, help="Source file or directory; repeatable"
    )
    snapshot.add_argument(
        "--output", required=True, help="Manifest JSON path outside immutable originals"
    )
    snapshot.add_argument(
        "--exclude", action="append", default=[], help="Glob to exclude; repeatable"
    )
    snapshot.add_argument(
        "--apply", action="store_true", help="Write the manifest; otherwise only report the plan"
    )
    snapshot.set_defaults(func=snapshot_command)

    verify = subparsers.add_parser("verify", help="Verify sources against a baseline")
    verify.add_argument("--manifest", required=True)
    verify.add_argument(
        "--check-new", action="store_true", help="Also report files added under snapshotted roots"
    )
    verify.add_argument("--json", action="store_true")
    verify.set_defaults(func=verify_command)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
