"""Run the public CLI through a disposable end-to-end knowledge-base workflow."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
KB_CLI = (
    PROJECT_ROOT
    / "plugins"
    / "knowledge-base-manager"
    / "skills"
    / "transcript-knowledge-manager"
    / "scripts"
    / "kb.py"
)


class SmokeFailure(RuntimeError):
    """Raised when an end-to-end release invariant is not satisfied."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeFailure(message)


def run_cli(stage: str, *arguments: str) -> str:
    environment = os.environ.copy()
    environment.update({"PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    result = subprocess.run(
        [sys.executable, str(KB_CLI), *arguments],
        cwd=PROJECT_ROOT,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    if result.returncode != 0:
        raise SmokeFailure(
            f"{stage} failed with exit code {result.returncode}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result.stdout


def parse_json_output(stage: str, output: str) -> Any:
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise SmokeFailure(f"{stage} did not emit valid JSON: {exc}\n{output}") from exc


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def synthetic_asset(today: str) -> str:
    return f"""---
schema_version: 3
id: procedure-release-smoke
title: Queue capacity release smoke procedure
type: procedure
knowledge_role: procedure
truth_status: user-preference
preservation: normalized
reuse_mode: adapt-required
status: active
scope_type: general
primary_domain: release-validation
domains: [release-validation]
industries: []
responsibilities: []
topics: [queue-capacity, release-smoke]
retrieval_queries: [protect queue capacity during release verification]
audiences: [maintainers]
languages: [en]
source_ids: []
source_anchors: []
provenance: conversation:release-smoke
confidence: high
maturity: stable
evidence_strength: moderate
time_sensitivity: low
sensitivity: public
created: {today}
updated: {today}
last_verified: {today}
summary: Protect queue capacity while validating a release workflow.
---

# Queue capacity release smoke procedure

Keep bounded release work visible, ordered, and reversible.
"""


def execute(workspace: Path) -> None:
    knowledge_root = workspace / "knowledge-root"
    source_root = workspace / "immutable-sources"
    source_root.mkdir()
    source_file = source_root / "source.txt"
    source_payload = b"immutable release smoke source\n"
    source_file.write_bytes(source_payload)
    source_hash_before = sha256(source_file)

    init_result = parse_json_output(
        "init",
        run_cli(
            "init",
            "init",
            str(knowledge_root),
            "--kb-id",
            "release-smoke",
            "--scope-type",
            "general",
            "--apply",
            "--json",
        ),
    )
    require(init_result.get("ok") is True, "init did not report ok=true")
    require(init_result.get("status") == "initialized", "init did not initialize a new root")
    require(
        (knowledge_root / "_meta" / "knowledge-base.json").is_file(),
        "init did not create the knowledge-base manifest",
    )

    configured_path = knowledge_root / "30-knowledge-objects"
    if not configured_path.is_dir():
        configured_path = knowledge_root / "30-knowledge-objects"
        for candidate in knowledge_root.iterdir():
            if candidate.is_dir() and candidate.name.startswith("30-"):
                configured_path = candidate
                break
    require(configured_path.is_dir(), "init did not create the knowledge asset directory")
    asset_path = configured_path / "release-smoke-procedure.md"
    asset_path.write_text(synthetic_asset(date.today().isoformat()), encoding="utf-8", newline="\n")

    doctor_result = parse_json_output(
        "doctor", run_cli("doctor", "doctor", str(knowledge_root), "--strict", "--json")
    )
    require(doctor_result.get("findings") == {}, "doctor reported findings for the fresh root")

    index_output = run_cli("index write", "index", str(knowledge_root), "--write", "--summary")
    require("Indexed assets: 1" in index_output, "index did not discover the smoke asset")
    run_cli("index check", "index", str(knowledge_root), "--check")

    query_result = parse_json_output(
        "query",
        run_cli(
            "query",
            "query",
            str(knowledge_root),
            "--intent",
            "diagnose",
            "--query",
            "queue capacity",
            "--top",
            "3",
            "--json",
        ),
    )
    require(isinstance(query_result, list) and bool(query_result), "query returned no assets")
    require(
        query_result[0].get("id") == "procedure-release-smoke",
        "query did not return the expected smoke asset first",
    )

    integrity_manifest = knowledge_root / "_meta" / "source-integrity-smoke.json"
    run_cli(
        "source snapshot",
        "source",
        "snapshot",
        "--source",
        str(source_root),
        "--output",
        str(integrity_manifest),
        "--apply",
    )
    require(integrity_manifest.is_file(), "source snapshot did not create its manifest")
    verify_result = parse_json_output(
        "source verify",
        run_cli(
            "source verify",
            "source",
            "verify",
            "--manifest",
            str(integrity_manifest),
            "--check-new",
            "--json",
        ),
    )
    require(verify_result.get("ok") is True, "source verify did not report ok=true")
    require(verify_result.get("checked_files") == 1, "source verify checked the wrong file count")
    for field in ("changed", "missing", "missing_roots", "unexpected"):
        require(verify_result.get(field) == [], f"source verify reported {field}")
    require(source_file.read_bytes() == source_payload, "source bytes changed during the workflow")
    require(sha256(source_file) == source_hash_before, "source SHA-256 changed during the workflow")


def main() -> int:
    require(KB_CLI.is_file(), f"CLI entrypoint is missing: {KB_CLI}")
    workspace: Path | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="knowledge-base-manager-e2e-") as temporary:
            workspace = Path(temporary)
            execute(workspace)
        require(
            workspace is not None and not workspace.exists(), "temporary workspace was not removed"
        )
    except (OSError, SmokeFailure, subprocess.SubprocessError) as exc:
        print(f"End-to-end smoke failed: {exc}", file=sys.stderr)
        return 1
    print("End-to-end smoke passed: init -> doctor -> index -> query -> source snapshot/verify")
    print("Source SHA-256 unchanged; temporary workspace removed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
