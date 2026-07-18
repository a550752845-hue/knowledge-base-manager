"""Shared, dependency-light helpers for knowledge-base tooling."""

from __future__ import annotations

import json
import os
import re
import stat
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - exercised by installation checks
    raise SystemExit(
        "PyYAML is required. Install the skill requirements with: "
        "python -m pip install -r requirements.txt"
    ) from exc


FRONTMATTER_RE = re.compile(
    r"\A\ufeff?---[ \t]*\r?\n(?P<yaml>.*?)\r?\n---[ \t]*(?:\r?\n|\Z)",
    re.DOTALL,
)
FENCED_CODE_RE = re.compile(r"```.*?```|~~~.*?~~~", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
REPARSE_POINT_ATTRIBUTE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


class _UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys at every depth."""


def _construct_unique_mapping(
    loader: _UniqueKeyLoader, node: yaml.nodes.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable mapping key",
                key_node.start_mark,
            ) from exc
        if duplicate:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


class _DuplicateJsonKeyError(ValueError):
    def __init__(self, key: str) -> None:
        self.key = key
        super().__init__(key)


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKeyError(key)
        result[key] = value
    return result


class FrontmatterError(ValueError):
    """Raised when Markdown frontmatter is malformed or not a mapping."""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="strict")


def split_frontmatter(text: str, source: str = "<memory>") -> tuple[dict[str, Any], str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}, text

    try:
        loaded = yaml.load(match.group("yaml"), Loader=_UniqueKeyLoader)
    except yaml.YAMLError as exc:
        raise FrontmatterError(f"Invalid YAML frontmatter in {source}: {exc}") from exc

    if loaded is None:
        fields: dict[str, Any] = {}
    elif not isinstance(loaded, dict):
        raise FrontmatterError(f"Frontmatter in {source} must be a YAML mapping")
    else:
        fields = {str(key): value for key, value in loaded.items()}
    return fields, text[match.end() :]


def parse_frontmatter(text: str, source: str = "<memory>") -> dict[str, Any]:
    return split_frontmatter(text, source)[0]


def clean_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip()


def as_list(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, (set, frozenset)):
        return sorted(clean_scalar(item) for item in value if clean_scalar(item))
    if isinstance(value, (list, tuple)):
        return [clean_scalar(item) for item in value if clean_scalar(item)]
    return [clean_scalar(value)] if clean_scalar(value) else []


def has_value(fields: dict[str, Any], name: str) -> bool:
    return bool(as_list(fields.get(name)))


def field_value(fields: dict[str, Any], name: str) -> str:
    value = fields.get(name)
    if isinstance(value, (list, tuple, set, dict)):
        return ""
    return clean_scalar(value)


def normalized_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): normalized_value(item) for key, item in value.items()}
    if isinstance(value, (set, frozenset)):
        normalized = [normalized_value(item) for item in value]
        return sorted(
            normalized,
            key=lambda item: json.dumps(item, ensure_ascii=False, sort_keys=True, default=str),
        )
    if isinstance(value, (list, tuple)):
        return [normalized_value(item) for item in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def parse_iso_date(value: Any) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raw = clean_scalar(value)
    if not raw:
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
        except ValueError:
            return None


def atomic_write_text(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def exclusive_write_text(path: Path, payload: str) -> None:
    """Publish a complete new file without replacing an existing destination."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def is_link_or_reparse(path: Path) -> bool:
    """Return whether a path itself is a symlink, junction, or reparse point."""
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return False
    if stat.S_ISLNK(metadata.st_mode):
        return True
    if getattr(metadata, "st_file_attributes", 0) & REPARSE_POINT_ATTRIBUTE:
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction and is_junction())


def ensure_within(root: Path, candidate: Path) -> Path:
    resolved_root = root.resolve()
    resolved_candidate = candidate.resolve()
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"Path escapes knowledge-base root: {resolved_candidate}") from exc
    return resolved_candidate


def ensure_safe_contained_path(root: Path, candidate: Path, *, allow_missing: bool = False) -> Path:
    """Validate containment without allowing symlink or reparse-point components."""
    resolved_root = root.resolve(strict=True)
    absolute_candidate = Path(os.path.abspath(candidate))
    try:
        relative = absolute_candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"Path escapes knowledge-base root: {absolute_candidate}") from exc

    current = resolved_root
    for part in relative.parts:
        current /= part
        try:
            current.lstat()
        except FileNotFoundError:
            if allow_missing:
                break
            raise ValueError(f"Path does not exist: {current}") from None
        if is_link_or_reparse(current):
            raise ValueError(f"Path uses a symlink, junction, or reparse point: {current}")

    resolved_candidate = absolute_candidate.resolve(strict=not allow_missing)
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"Path escapes knowledge-base root: {resolved_candidate}") from exc
    return absolute_candidate


def stable_json(value: Any, *, pretty: bool = False) -> str:
    if pretty:
        return json.dumps(normalized_value(value), ensure_ascii=False, indent=2, sort_keys=True)
    return json.dumps(
        normalized_value(value), ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )


def parse_json(text: str, source: str = "<memory>") -> Any:
    try:
        return json.loads(text, object_pairs_hook=_unique_json_object)
    except _DuplicateJsonKeyError as exc:
        raise ValueError(f"Duplicate JSON object key {exc.key!r} in {source}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {source}: {exc}") from exc


def strip_code_for_link_scan(text: str) -> str:
    return INLINE_CODE_RE.sub("", FENCED_CODE_RE.sub("", text))


def load_json(path: Path) -> dict[str, Any]:
    loaded = parse_json(read_text(path), str(path))
    if not isinstance(loaded, dict):
        raise ValueError(f"JSON document must be an object: {path}")
    return loaded


def find_manifest(root: Path) -> Path | None:
    candidates = (
        root / "_meta" / "knowledge-base.json",
        root / "_meta" / "知识库清单.json",
    )
    for path in candidates:
        if not path.exists() and not is_link_or_reparse(path):
            continue
        safe_path = ensure_safe_contained_path(root, path)
        if not safe_path.is_file():
            raise ValueError(f"Knowledge-base manifest is not a regular file: {safe_path}")
        return safe_path
    return None


def load_manifest(root: Path) -> tuple[Path | None, dict[str, Any]]:
    path = find_manifest(root)
    return (path, load_json(path)) if path else (None, {})
