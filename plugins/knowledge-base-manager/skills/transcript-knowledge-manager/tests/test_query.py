from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from build_asset_index import (
    BUILD_PROFILE_DEFAULT,
    BUILD_PROFILE_INCLUDE_MANAGEMENT,
    build_rows,
    render_jsonl,
)
from query_asset_index import main, shortlist, tokenize, validate_index_rows


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "query_asset_index.py"


def create_directory_link(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=True)
        return
    except (NotImplementedError, OSError):
        pass
    if os.name != "nt":
        raise OSError("Directory symlinks are unavailable")
    completed = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if completed.returncode != 0:
        raise OSError(f"Unable to create directory junction: {completed.stderr.strip()}")


def remove_directory_link(link: Path) -> None:
    if not os.path.lexists(link):
        return
    if link.is_symlink():
        link.unlink()
    else:
        link.rmdir()


ASSET_NOTE = """---
schema_version: 3
id: current-asset
type: model
knowledge_role: model
truth_status: model-synthesis
preservation: derived
reuse_mode: analyze-only
status: active
scope_type: general
primary_domain: testing
domains: [testing]
industries: []
responsibilities: []
topics: [trusted]
retrieval_queries: [current asset]
audiences: [maintainers]
languages: [en]
source_ids: [src-current]
source_anchors: [section-1]
confidence: high
maturity: stable
evidence_strength: strong
time_sensitivity: low
sensitivity: internal
updated: 2026-07-15
last_verified: 2026-07-15
summary: Trusted current asset.
---
# Current asset

Trusted content.
"""


MANAGEMENT_NOTE = """---
schema_version: 3
id: management-route
type: management
knowledge_role: management
truth_status: model-synthesis
preservation: derived
reuse_mode: reference-only
status: active
scope_type: general
topics: [routing]
sensitivity: internal
---
# Management route

Current routing guidance.
"""


ROWS = [
    {
        "id": "talk-health",
        "title": "康养咨询开场话术",
        "path": "40/talk.md",
        "knowledge_role": "talk-track",
        "reuse_mode": "adapt-required",
        "status": "active",
        "sensitivity": "internal",
        "truth_status": "generated",
        "industries": ["healthcare"],
        "responsibilities": ["sales"],
        "topics": ["consultation", "opening"],
        "retrieval_queries": ["康养客户咨询如何开场"],
        "summary": "用于康养客户首次咨询。",
        "confidence": "medium",
        "maturity": "candidate",
        "time_sensitivity": "low",
        "last_verified": "2026-07-15",
    },
    {
        "id": "model-health",
        "title": "康养客户信任模型",
        "path": "30/model.md",
        "knowledge_role": "model",
        "reuse_mode": "analyze-only",
        "status": "approved",
        "sensitivity": "internal",
        "truth_status": "model-synthesis",
        "industries": ["healthcare"],
        "responsibilities": ["sales"],
        "topics": ["trust"],
        "summary": "解释客户信任形成机制。",
        "confidence": "high",
        "maturity": "stable",
        "time_sensitivity": "low",
        "last_verified": "2026-07-15",
    },
    {
        "id": "blocked",
        "title": "禁止复用的旧话术",
        "path": "40/blocked.md",
        "knowledge_role": "talk-track",
        "reuse_mode": "do-not-use",
        "status": "active",
        "sensitivity": "internal",
        "industries": ["healthcare"],
        "topics": ["opening"],
    },
]


class QueryTests(unittest.TestCase):
    def create_root_and_row(self) -> tuple[Path, dict[str, object]]:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        note = root / "30" / "asset.md"
        note.parent.mkdir(parents=True)
        note.write_text(ASSET_NOTE, encoding="utf-8")
        row: dict[str, object] = build_rows(root)[0]
        return root, row

    def write_current_index(
        self,
        root: Path,
        *,
        build_profile: str = BUILD_PROFILE_DEFAULT,
        name: str = "index.jsonl",
    ) -> Path:
        include_management = build_profile == BUILD_PROFILE_INCLUDE_MANAGEMENT
        index_path = root / name
        index_path.write_text(
            render_jsonl(
                build_rows(root, include_management=include_management),
                build_profile=build_profile,
            ),
            encoding="utf-8",
        )
        return index_path

    def run_main(self, argv: list[str]) -> tuple[int, str, str]:
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_chinese_tokenization_builds_bigrams(self) -> None:
        self.assertIn("康养", tokenize("康养客户"))

    def test_generate_intent_prefers_talk_track(self) -> None:
        results = shortlist(
            ROWS,
            query="康养客户咨询开场",
            intent="generate",
            domains=[],
            industries=["healthcare"],
            responsibilities=["sales"],
            roles=[],
            include_outputs=False,
            include_blocked=False,
            limit=10,
        )
        self.assertEqual("talk-health", results[0]["id"])
        self.assertNotIn("blocked", [row["id"] for row in results])

    def test_industry_filter_is_independent(self) -> None:
        results = shortlist(
            ROWS,
            query="trust",
            intent="diagnose",
            domains=[],
            industries=["tourism"],
            responsibilities=[],
            roles=[],
            include_outputs=False,
            include_blocked=False,
            limit=10,
        )
        self.assertEqual([], results)

    def test_inactive_assets_are_excluded_unless_explicitly_included(self) -> None:
        inactive = [
            {
                **ROWS[0],
                "id": f"{status}-talk",
                "path": f"40/{status}.md",
                "status": status,
            }
            for status in ("draft", "pending", "pending-review", "deprecated", "archived")
        ]
        default_results = shortlist(
            [*ROWS, *inactive],
            query="",
            intent="generate",
            domains=[],
            industries=[],
            responsibilities=[],
            roles=[],
            include_outputs=False,
            include_blocked=False,
            limit=10,
        )
        default_ids = {row["id"] for row in default_results}
        self.assertTrue(default_ids.isdisjoint(row["id"] for row in inactive))
        included_results = shortlist(
            [*ROWS, *inactive],
            query="",
            intent="generate",
            domains=[],
            industries=[],
            responsibilities=[],
            roles=[],
            include_outputs=False,
            include_blocked=False,
            limit=10,
            include_inactive=True,
        )
        included_ids = {row["id"] for row in included_results}
        self.assertTrue({row["id"] for row in inactive}.issubset(included_ids))

    def test_max_sensitivity_is_an_inclusive_conservative_ceiling(self) -> None:
        rows = [
            {
                **ROWS[1],
                "id": f"asset-{sensitivity}",
                "path": f"30/{sensitivity}.md",
                "sensitivity": sensitivity,
            }
            for sensitivity in ("public", "internal", "private", "restricted", "unknown")
        ]
        internal_results = shortlist(
            rows,
            query="",
            intent="explain",
            domains=[],
            industries=[],
            responsibilities=[],
            roles=[],
            include_outputs=False,
            include_blocked=False,
            limit=10,
            max_sensitivity="internal",
        )
        self.assertEqual(
            {"asset-public", "asset-internal"},
            {row["id"] for row in internal_results},
        )
        restricted_results = shortlist(
            rows,
            query="",
            intent="explain",
            domains=[],
            industries=[],
            responsibilities=[],
            roles=[],
            include_outputs=False,
            include_blocked=False,
            limit=10,
            max_sensitivity="restricted",
        )
        self.assertEqual(5, len(restricted_results))

    def test_output_and_blocked_switches_remain_independent(self) -> None:
        output = {
            **ROWS[0],
            "id": "output",
            "path": "60/output.md",
            "knowledge_role": "output",
            "reuse_mode": "reference-only",
        }
        defaults = shortlist(
            [*ROWS, output],
            query="",
            intent="generate",
            domains=[],
            industries=[],
            responsibilities=[],
            roles=[],
            include_outputs=False,
            include_blocked=False,
            limit=10,
        )
        self.assertNotIn("output", [row["id"] for row in defaults])
        self.assertNotIn("blocked", [row["id"] for row in defaults])
        included = shortlist(
            [*ROWS, output],
            query="",
            intent="generate",
            domains=[],
            industries=[],
            responsibilities=[],
            roles=[],
            include_outputs=True,
            include_blocked=True,
            limit=10,
        )
        self.assertIn("output", [row["id"] for row in included])
        self.assertIn("blocked", [row["id"] for row in included])

    def test_duplicate_ids_and_basic_row_types_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Duplicate asset ID"):
            validate_index_rows([ROWS[0], dict(ROWS[0])])
        malformed = {**ROWS[0], "industries": "healthcare"}
        with self.assertRaisesRegex(ValueError, "list of strings"):
            validate_index_rows([malformed])

    def test_unsafe_relative_path_and_tampered_hash_are_rejected(self) -> None:
        root, row = self.create_root_and_row()
        validate_index_rows([row], root)
        unsafe = {**row, "path": "../outside.md"}
        with self.assertRaisesRegex(ValueError, "unsafe relative path"):
            validate_index_rows([unsafe], root)
        tampered = {**row, "asset_hash": "0" * 64}
        with self.assertRaisesRegex(ValueError, "Asset hash mismatch"):
            shortlist(
                [tampered],
                query="",
                intent="explain",
                domains=[],
                industries=[],
                responsibilities=[],
                roles=[],
                include_outputs=False,
                include_blocked=False,
                limit=10,
                root=root,
            )

    def test_query_validation_rejects_symlinked_asset(self) -> None:
        root, row = self.create_root_and_row()
        outside_temp = tempfile.TemporaryDirectory()
        self.addCleanup(outside_temp.cleanup)
        outside_dir = Path(outside_temp.name)
        outside = outside_dir / "outside.md"
        outside_text = "# Outside\n\nSecret.\n"
        outside.write_text(outside_text, encoding="utf-8")
        link = root / "linked"
        create_directory_link(link, outside_dir)
        self.addCleanup(remove_directory_link, link)
        linked_row = {
            **row,
            "path": "linked/outside.md",
            "asset_hash": hashlib.sha256(outside_text.encode("utf-8")).hexdigest(),
        }
        with self.assertRaisesRegex(ValueError, "symlink, junction, or reparse point"):
            validate_index_rows([linked_row], root)

    def test_current_owned_index_returns_results(self) -> None:
        root, row = self.create_root_and_row()
        index_path = self.write_current_index(root)

        code, stdout, stderr = self.run_main([str(root), "--index", str(index_path), "--json"])

        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        self.assertEqual([row["id"]], [result["id"] for result in json.loads(stdout)])

    def test_owned_include_management_profile_rebuilds_with_management(self) -> None:
        root, _ = self.create_root_and_row()
        management = root / "_meta" / "management.md"
        management.parent.mkdir(parents=True)
        management.write_text(MANAGEMENT_NOTE, encoding="utf-8")
        index_path = self.write_current_index(
            root,
            build_profile=BUILD_PROFILE_INCLUDE_MANAGEMENT,
        )

        code, stdout, stderr = self.run_main([str(root), "--index", str(index_path), "--json"])

        self.assertEqual(0, code)
        self.assertEqual("", stderr)
        self.assertEqual(
            {"current-asset", "management-route"},
            {result["id"] for result in json.loads(stdout)},
        )

    def test_unowned_index_fails_closed_without_results(self) -> None:
        root, _ = self.create_root_and_row()
        owned_lines = render_jsonl(build_rows(root)).splitlines()
        index_path = root / "unowned.jsonl"
        index_path.write_text("\n".join(owned_lines[1:]) + "\n", encoding="utf-8")

        code, stdout, stderr = self.run_main([str(root), "--index", str(index_path), "--json"])

        self.assertEqual(2, code)
        self.assertEqual("", stdout)
        self.assertIn("lacks the generated-index ownership marker", stderr)

    def test_metadata_tampering_fails_closed_even_when_asset_hash_matches(self) -> None:
        root, row = self.create_root_and_row()
        tampered_values = {
            "sensitivity": "public",
            "reuse_mode": "direct-use",
            "status": "approved",
            "knowledge_role": "fact",
        }

        for field, value in tampered_values.items():
            with self.subTest(field=field):
                index_path = root / f"tampered-{field}.jsonl"
                index_path.write_text(
                    render_jsonl([{**row, field: value}]),
                    encoding="utf-8",
                )
                code, stdout, stderr = self.run_main(
                    [str(root), "--index", str(index_path), "--json"]
                )
                self.assertEqual(2, code)
                self.assertEqual("", stdout)
                self.assertIn("stale or has been tampered with", stderr)

    def test_stale_owned_index_fails_closed_without_results(self) -> None:
        root, _ = self.create_root_and_row()
        index_path = self.write_current_index(root)
        note = root / "30" / "asset.md"
        note.write_text(ASSET_NOTE + "\nChanged after indexing.\n", encoding="utf-8")

        code, stdout, stderr = self.run_main([str(root), "--index", str(index_path), "--json"])

        self.assertEqual(2, code)
        self.assertEqual("", stdout)
        self.assertIn("stale or has been tampered with", stderr)

    def test_tampered_index_returns_code_2_without_traceback(self) -> None:
        root, row = self.create_root_and_row()
        index_path = root / "index.jsonl"
        index_path.write_text(render_jsonl([{**row, "asset_hash": "0" * 64}]), encoding="utf-8")
        self.assertEqual(
            2,
            main([str(root), "--index", str(index_path), "--json"]),
        )
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(root),
                "--index",
                str(index_path),
                "--json",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(2, completed.returncode)
        self.assertNotIn("Traceback", completed.stderr)
        self.assertIn("stale or has been tampered with", completed.stderr)

    def test_malformed_index_returns_code_2_without_traceback(self) -> None:
        root, _ = self.create_root_and_row()
        index_path = root / "broken.jsonl"
        index_path.write_text('{"id":"first","id":"second"}\n', encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), str(root), "--index", str(index_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(2, completed.returncode)
        self.assertNotIn("Traceback", completed.stderr)
        self.assertIn("Duplicate JSON object key", completed.stderr)

    def test_malformed_manifest_returns_code_2_without_traceback(self) -> None:
        root, _ = self.create_root_and_row()
        manifest = root / "_meta" / "knowledge-base.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text('{"paths":', encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), str(root)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(2, completed.returncode)
        self.assertNotIn("Traceback", completed.stderr)
        self.assertIn("Invalid JSON", completed.stderr)
