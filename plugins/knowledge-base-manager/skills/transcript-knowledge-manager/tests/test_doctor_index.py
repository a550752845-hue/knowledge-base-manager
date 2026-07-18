from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from build_asset_index import (
    BUILD_PROFILE_DEFAULT,
    BUILD_PROFILE_INCLUDE_MANAGEMENT,
    main as build_index_main,
    parse_index_document,
)
from init_knowledge_base import main as init_main
from lint_knowledge_base import main as lint_main


def run_quietly(entrypoint, argv: list[str]) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = entrypoint(argv)
    return code, stdout.getvalue(), stderr.getvalue()


def indexable_asset() -> str:
    today = date.today().isoformat()
    return f"""---
schema_version: 3
id: principle-retrieval-routing
type: principle
knowledge_role: principle
truth_status: model-synthesis
preservation: derived
reuse_mode: analyze-only
status: active
scope_type: general
domains: [knowledge-management]
industries: []
responsibilities: []
topics: [retrieval]
source_ids: []
source_anchors: []
provenance: conversation:test
confidence: medium
maturity: candidate
evidence_strength: moderate
time_sensitivity: low
sensitivity: internal
created: {today}
updated: {today}
summary: Route retrieval through the machine index before opening source files.
---
# Retrieval routing

Read the smallest relevant durable assets before returning to source evidence.
"""


class DoctorAssetIndexTests(unittest.TestCase):
    def create_initialized_root(self) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name) / "knowledge"
        code, _, stderr = run_quietly(
            init_main,
            [str(root), "--kb-id", "test-kb", "--json", "--apply"],
        )
        self.assertEqual(0, code, stderr)
        return root

    def run_doctor(self, root: Path) -> tuple[int, dict[str, object], str]:
        code, stdout, stderr = run_quietly(
            lint_main,
            [str(root), "--check-index", "--strict", "--json"],
        )
        return code, json.loads(stdout), stderr

    @staticmethod
    def finding_codes(summary: dict[str, object]) -> list[str]:
        details = summary.get("details", [])
        assert isinstance(details, list)
        return [str(item["code"]) for item in details if isinstance(item, dict)]

    def test_default_owned_index_passes_doctor(self) -> None:
        root = self.create_initialized_root()
        index_path = root / "00-AI入口" / "资产索引.jsonl"
        profile, rows = parse_index_document(
            index_path.read_text(encoding="utf-8"),
            str(index_path),
            require_owned=True,
        )

        code, summary, stderr = self.run_doctor(root)

        self.assertEqual(BUILD_PROFILE_DEFAULT, profile)
        self.assertEqual([], rows)
        self.assertEqual(0, code, stderr)
        self.assertEqual([], self.finding_codes(summary))

    def test_include_management_index_passes_doctor_with_same_profile(self) -> None:
        root = self.create_initialized_root()
        code, _, stderr = run_quietly(
            build_index_main,
            [str(root), "--write", "--include-management"],
        )
        self.assertEqual(0, code, stderr)
        index_path = root / "00-AI入口" / "资产索引.jsonl"
        profile, rows = parse_index_document(
            index_path.read_text(encoding="utf-8"),
            str(index_path),
            require_owned=True,
        )

        doctor_code, summary, doctor_stderr = self.run_doctor(root)

        self.assertEqual(BUILD_PROFILE_INCLUDE_MANAGEMENT, profile)
        self.assertTrue(any(row.get("knowledge_role") == "management" for row in rows))
        self.assertEqual(0, doctor_code, doctor_stderr)
        self.assertEqual([], self.finding_codes(summary))

    def test_unowned_legacy_jsonl_is_reported_as_invalid(self) -> None:
        root = self.create_initialized_root()
        index_path = root / "00-AI入口" / "资产索引.jsonl"
        index_path.write_text('{"id":"legacy-row"}\n', encoding="utf-8")

        code, summary, stderr = self.run_doctor(root)

        self.assertEqual(1, code, stderr)
        self.assertIn("invalid-asset-index", self.finding_codes(summary))

    def test_asset_content_drift_is_reported_as_stale(self) -> None:
        root = self.create_initialized_root()
        note = root / "30-知识对象" / "retrieval-routing.md"
        note.write_text(indexable_asset(), encoding="utf-8")
        code, _, stderr = run_quietly(build_index_main, [str(root), "--write"])
        self.assertEqual(0, code, stderr)
        self.assertEqual(0, self.run_doctor(root)[0])

        note.write_text(indexable_asset() + "\nChanged after indexing.\n", encoding="utf-8")
        doctor_code, summary, doctor_stderr = self.run_doctor(root)

        self.assertEqual(1, doctor_code, doctor_stderr)
        self.assertIn("stale-asset-index", self.finding_codes(summary))


if __name__ == "__main__":
    unittest.main()
