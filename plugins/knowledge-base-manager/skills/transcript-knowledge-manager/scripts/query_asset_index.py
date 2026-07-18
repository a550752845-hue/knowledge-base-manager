"""Deterministically shortlist knowledge assets before model-level judgment."""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from datetime import date
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from build_asset_index import (
    BUILD_PROFILE_INCLUDE_MANAGEMENT,
    build_rows,
    default_index_path,
    parse_index_document,
    render_jsonl,
)
from kb_common import (
    as_list,
    clean_scalar,
    ensure_safe_contained_path,
    load_manifest,
    parse_iso_date,
    read_text,
    stable_json,
)


ASCII_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9._+-]*", re.IGNORECASE)
CJK_RE = re.compile(r"[\u3400-\u9fff]+")

INTENT_ROLE_WEIGHTS: dict[str, dict[str, float]] = {
    "generate": {"talk-track": 7, "procedure": 6, "model": 4, "principle": 3, "evidence": 1},
    "diagnose": {"model": 7, "principle": 6, "procedure": 5, "fact": 3, "evidence": 2},
    "decide": {"model": 6, "procedure": 6, "fact": 5, "principle": 4, "evidence": 3},
    "explain": {"principle": 6, "model": 5, "fact": 5, "logic-map": 4, "claim": 3},
    "research": {"logic-map": 6, "source-profile": 5, "claim": 5, "evidence": 5, "fact": 4},
    "verify": {"evidence": 8, "fact": 7, "source": 6, "logic-map": 2, "claim": 1},
    "quote": {"evidence": 8, "source": 7, "fact": 3},
    "manage": {"management": 8, "source-profile": 3, "logic-map": 2},
}

FIELD_WEIGHTS = {
    "title": 8.0,
    "retrieval_queries": 7.0,
    "topics": 6.0,
    "industries": 5.0,
    "responsibilities": 5.0,
    "domains": 4.0,
    "summary": 3.0,
}

MATURITY_BOOST = {"seed": 0.0, "candidate": 0.5, "stable": 1.5, "core": 2.5}
CONFIDENCE_BOOST = {"low": 0.0, "medium": 0.5, "high": 1.0}
ELIGIBLE_STATUSES = frozenset({"active", "approved"})
SENSITIVITY_LEVELS = ("public", "internal", "private", "restricted")
SENSITIVITY_RANK = {name: rank for rank, name in enumerate(SENSITIVITY_LEVELS)}
HASH_RE = re.compile(r"[0-9a-f]{64}")

ROW_STRING_FIELDS = frozenset(
    {
        "id",
        "title",
        "path",
        "asset_hash",
        "type",
        "knowledge_role",
        "truth_status",
        "preservation",
        "reuse_mode",
        "status",
        "scope_type",
        "primary_domain",
        "confidence",
        "maturity",
        "evidence_strength",
        "time_sensitivity",
        "sensitivity",
        "source_id",
        "updated",
        "last_verified",
        "summary",
    }
)
ROW_LIST_FIELDS = frozenset(
    {
        "domains",
        "industries",
        "responsibilities",
        "topics",
        "retrieval_queries",
        "audiences",
        "languages",
        "source_ids",
    }
)


def tokenize(text: str) -> set[str]:
    lowered = text.casefold()
    tokens = set(ASCII_TOKEN_RE.findall(lowered))
    for sequence in CJK_RE.findall(lowered):
        tokens.update(sequence)
        tokens.update(sequence[index : index + 2] for index in range(len(sequence) - 1))
    return {token for token in tokens if token}


def text_value(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(clean_scalar(item) for item in value)
    if isinstance(value, dict):
        return " ".join(f"{key} {text_value(item)}" for key, item in value.items())
    return clean_scalar(value)


def load_current_rows(root: Path, index_path: Path) -> list[dict[str, Any]]:
    """Return canonical rows only when the stored generated index is current."""
    stored_text = read_text(index_path)
    build_profile, _ = parse_index_document(
        stored_text,
        str(index_path),
        require_owned=True,
    )
    if build_profile is None:  # Defensive narrowing; require_owned already rejects this case.
        raise ValueError(f"Asset index lacks the generated-index ownership marker: {index_path}")

    current_rows = build_rows(
        root,
        include_management=build_profile == BUILD_PROFILE_INCLUDE_MANAGEMENT,
    )
    canonical_text = render_jsonl(current_rows, build_profile=build_profile)
    if stored_text != canonical_text:
        raise ValueError(
            f"Asset index is stale or has been tampered with: {index_path}. "
            "Rebuild the asset index before querying."
        )
    return current_rows


def _validate_relative_path(raw_path: str, row_number: int) -> PurePosixPath:
    if "\\" in raw_path:
        raise ValueError(f"Index row {row_number} path must use forward slashes: {raw_path!r}")
    relative = PurePosixPath(raw_path)
    windows_path = PureWindowsPath(raw_path)
    if (
        not raw_path
        or relative.is_absolute()
        or windows_path.is_absolute()
        or windows_path.drive
        or not relative.parts
        or ".." in relative.parts
        or relative.as_posix() != raw_path
    ):
        raise ValueError(f"Index row {row_number} has an unsafe relative path: {raw_path!r}")
    return relative


def validate_index_rows(rows: list[dict[str, Any]], root: Path | None = None) -> None:
    seen_ids: set[str] = set()
    resolved_root = root.resolve(strict=True) if root is not None else None
    for number, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f"Index row {number} must be an object")

        for field in ROW_STRING_FIELDS:
            if field in row and not isinstance(row[field], str):
                raise ValueError(f"Index row {number} field {field!r} must be a string")
        schema_version = row.get("schema_version")
        if schema_version is not None and (
            isinstance(schema_version, bool) or not isinstance(schema_version, (int, str))
        ):
            raise ValueError(
                f"Index row {number} field 'schema_version' must be a string or integer"
            )
        for field in ROW_LIST_FIELDS:
            if field not in row:
                continue
            value = row[field]
            if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                raise ValueError(f"Index row {number} field {field!r} must be a list of strings")
        for field in ("legacy_inferred", "restricted"):
            if field in row and not isinstance(row[field], bool):
                raise ValueError(f"Index row {number} field {field!r} must be a boolean")

        asset_id = row.get("id", "")
        if not isinstance(asset_id, str) or not asset_id.strip():
            raise ValueError(f"Index row {number} must have a nonempty string id")
        if asset_id in seen_ids:
            raise ValueError(f"Duplicate asset ID in index: {asset_id}")
        seen_ids.add(asset_id)

        raw_path = row.get("path", "")
        if not isinstance(raw_path, str):
            raise ValueError(f"Index row {number} must have a string path")
        relative = _validate_relative_path(raw_path, number)
        if resolved_root is None:
            continue

        candidate = resolved_root.joinpath(*relative.parts)
        safe_path = ensure_safe_contained_path(resolved_root, candidate)
        if not safe_path.is_file():
            raise ValueError(f"Indexed asset is not a regular file: {raw_path}")
        asset_hash = row.get("asset_hash")
        if not isinstance(asset_hash, str) or HASH_RE.fullmatch(asset_hash) is None:
            raise ValueError(f"Index row {number} has an invalid asset_hash")
        current_hash = hashlib.sha256(read_text(safe_path).encode("utf-8")).hexdigest()
        if current_hash != asset_hash:
            raise ValueError(f"Asset hash mismatch for indexed path: {raw_path}")


def matches_filter(row: dict[str, Any], name: str, wanted: list[str]) -> bool:
    if not wanted:
        return True
    actual = {item.casefold() for item in as_list(row.get(name))}
    return bool(actual.intersection(item.casefold() for item in wanted))


def effective_sensitivity(row: dict[str, Any]) -> str:
    sensitivity = clean_scalar(row.get("sensitivity")).casefold()
    return sensitivity if sensitivity in SENSITIVITY_RANK else "restricted"


def stale_penalty(
    row: dict[str, Any], thresholds: dict[str, int] | None = None
) -> tuple[float, str | None]:
    verified = parse_iso_date(row.get("last_verified"))
    time_sensitivity = clean_scalar(row.get("time_sensitivity"))
    thresholds = thresholds or {"high": 30, "medium": 180, "low": 3650}
    threshold = thresholds.get(time_sensitivity)
    if not threshold:
        return 0.0, None
    if verified is None:
        return (-4.0 if time_sensitivity == "high" else -1.0), "missing verification date"
    age = (date.today() - verified).days
    if age > threshold:
        return (
            -6.0 if clean_scalar(row.get("reuse_mode")) == "direct-use" else -2.0
        ), f"stale by {age - threshold} days"
    return 0.0, None


def score_row(
    row: dict[str, Any], query: str, intent: str, freshness: dict[str, int] | None = None
) -> tuple[float, list[str]]:
    query_tokens = tokenize(query)
    score = INTENT_ROLE_WEIGHTS.get(intent, {}).get(clean_scalar(row.get("knowledge_role")), 0.0)
    reasons: list[str] = []
    if score:
        reasons.append(f"{intent} role match")

    query_folded = query.casefold().strip()
    for field, weight in FIELD_WEIGHTS.items():
        raw = text_value(row.get(field, ""))
        if not raw:
            continue
        field_tokens = tokenize(raw)
        overlap = query_tokens.intersection(field_tokens)
        if overlap:
            contribution = weight * min(1.0, len(overlap) / max(1, len(query_tokens)))
            score += contribution
            reasons.append(f"{field}: {', '.join(sorted(overlap)[:4])}")
        if query_folded and query_folded in raw.casefold():
            score += weight * 0.75
            reasons.append(f"exact phrase in {field}")

    maturity = clean_scalar(row.get("maturity"))
    confidence = clean_scalar(row.get("confidence"))
    score += MATURITY_BOOST.get(maturity, 0.0)
    score += CONFIDENCE_BOOST.get(confidence, 0.0)

    penalty, stale_reason = stale_penalty(row, freshness)
    score += penalty
    if stale_reason:
        reasons.append(stale_reason)
    if clean_scalar(row.get("truth_status")) == "generated":
        score -= 0.5
    return score, reasons


def shortlist(
    rows: list[dict[str, Any]],
    *,
    query: str,
    intent: str,
    domains: list[str],
    industries: list[str],
    responsibilities: list[str],
    roles: list[str],
    include_outputs: bool,
    include_blocked: bool,
    limit: int,
    freshness: dict[str, int] | None = None,
    include_inactive: bool = False,
    max_sensitivity: str = "internal",
    root: Path | None = None,
) -> list[dict[str, Any]]:
    if max_sensitivity not in SENSITIVITY_RANK:
        raise ValueError("max_sensitivity must be one of: " + ", ".join(SENSITIVITY_LEVELS))
    validate_index_rows(rows, root)

    results: list[dict[str, Any]] = []
    for row in rows:
        role = clean_scalar(row.get("knowledge_role"))
        reuse = clean_scalar(row.get("reuse_mode"))
        status = clean_scalar(row.get("status")).casefold()
        if not include_inactive and status not in ELIGIBLE_STATUSES:
            continue
        if SENSITIVITY_RANK[effective_sensitivity(row)] > SENSITIVITY_RANK[max_sensitivity]:
            continue
        if role == "output" and not include_outputs:
            continue
        if reuse == "do-not-use" and not include_blocked:
            continue
        if roles and role.casefold() not in {item.casefold() for item in roles}:
            continue
        if not matches_filter(row, "domains", domains):
            continue
        if not matches_filter(row, "industries", industries):
            continue
        if not matches_filter(row, "responsibilities", responsibilities):
            continue

        score, reasons = score_row(row, query, intent, freshness)
        if query and score <= 0:
            continue
        result = dict(row)
        result["retrieval_score"] = round(score, 3)
        result["retrieval_reasons"] = reasons
        results.append(result)

    results.sort(key=lambda item: (-float(item["retrieval_score"]), clean_scalar(item.get("path"))))
    return results[:limit]


def print_markdown(results: list[dict[str, Any]]) -> None:
    if not results:
        print("No matching assets.")
        return
    print("| Score | Role | Reuse | Asset | Why |")
    print("| ---: | --- | --- | --- | --- |")
    for row in results:
        title = clean_scalar(row.get("title")) or clean_scalar(row.get("id"))
        path = clean_scalar(row.get("path"))
        reasons = "; ".join(as_list(row.get("retrieval_reasons"))[:3]).replace("|", "\\|")
        print(
            f"| {row['retrieval_score']:.3f} | {clean_scalar(row.get('knowledge_role'))} | "
            f"{clean_scalar(row.get('reuse_mode'))} | [{title}]({path}) | {reasons} |"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Shortlist assets from a machine-readable knowledge index."
    )
    parser.add_argument("root", help="Knowledge-base root directory")
    parser.add_argument("--query", default="", help="Natural-language retrieval query")
    parser.add_argument("--intent", choices=sorted(INTENT_ROLE_WEIGHTS), default="explain")
    parser.add_argument("--domain", action="append", default=[])
    parser.add_argument("--industry", action="append", default=[])
    parser.add_argument("--responsibility", action="append", default=[])
    parser.add_argument("--role", action="append", default=[])
    parser.add_argument("--top", type=int, default=12)
    parser.add_argument("--index", help="Override index path")
    parser.add_argument("--include-outputs", action="store_true")
    parser.add_argument(
        "--include-blocked", action="store_true", help="Include reuse_mode: do-not-use"
    )
    parser.add_argument(
        "--include-inactive",
        action="store_true",
        help="Include assets whose status is not active or approved",
    )
    parser.add_argument(
        "--max-sensitivity",
        choices=SENSITIVITY_LEVELS,
        default="internal",
        help=(
            "Highest sensitivity to include (public < internal < private < restricted); "
            "missing or unknown values are treated as restricted"
        ),
    )
    parser.add_argument("--json", action="store_true")
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
        index_path = (
            Path(args.index).expanduser().resolve() if args.index else default_index_path(root)
        )
    except (OSError, UnicodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if not index_path.is_file():
        print(f"Asset index is missing: {index_path}", file=sys.stderr)
        return 2
    if args.top < 1 or args.top > 100:
        print("--top must be between 1 and 100", file=sys.stderr)
        return 2

    try:
        _, manifest = load_manifest(root)
        configured = manifest.get("freshness_policy", {}) if isinstance(manifest, dict) else {}
        freshness = {"high": 30, "medium": 180, "low": 3650}
        if isinstance(configured, dict):
            for key in freshness:
                value = configured.get(f"{key}_days", configured.get(key))
                if isinstance(value, int) and value > 0:
                    freshness[key] = value
        results = shortlist(
            load_current_rows(root, index_path),
            query=args.query,
            intent=args.intent,
            domains=args.domain,
            industries=args.industry,
            responsibilities=args.responsibility,
            roles=args.role,
            include_outputs=args.include_outputs,
            include_blocked=args.include_blocked,
            limit=args.top,
            freshness=freshness,
            include_inactive=args.include_inactive,
            max_sensitivity=args.max_sensitivity,
            root=root,
        )
    except (OSError, UnicodeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.json:
        print(stable_json(results, pretty=True))
    else:
        print_markdown(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
