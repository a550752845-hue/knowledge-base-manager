from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from build_asset_index import (
    BUILD_PROFILE_DEFAULT,
    build_rows,
    detect_profile,
    main,
    parse_index_document,
    render_jsonl,
)


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_asset_index.py"


def create_directory_link(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=True)
        return
    except (NotImplementedError, OSError):
        pass
    if os.name != "nt":
        raise unittest.SkipTest("Directory links are not available on this platform")
    completed = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if completed.returncode != 0:
        raise unittest.SkipTest("Directory links and junctions are unavailable")


def remove_directory_link(link: Path) -> None:
    if not os.path.lexists(link):
        return
    checker = getattr(link, "is_junction", None)
    if checker is not None and checker():
        link.rmdir()
    else:
        link.unlink()


NOTE = """---
schema_version: 3
id: model-audience-fit
type: model
knowledge_role: model
truth_status: model-synthesis
preservation: derived
reuse_mode: analyze-only
status: active
scope_type: cross-domain
domains: [marketing]
industries: [healthcare, tourism]
responsibilities: [growth]
topics: [audience fit]
retrieval_queries: [如何判断受众匹配]
source_ids: [src-1]
source_anchors: [section-1]
confidence: medium
maturity: candidate
evidence_strength: moderate
time_sensitivity: low
sensitivity: internal
created: 2026-07-15
updated: 2026-07-15
last_verified: 2026-07-15
summary: 判断内容与目标受众是否匹配。
---
# Audience Fit Model
"""


class AssetIndexTests(unittest.TestCase):
    def create_root(self) -> Path:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        note = root / "30-知识对象" / "model.md"
        note.parent.mkdir(parents=True)
        note.write_text(NOTE, encoding="utf-8")
        return root

    def test_structured_arrays_are_preserved(self) -> None:
        rows = build_rows(self.create_root())
        self.assertEqual(["healthcare", "tourism"], rows[0]["industries"])
        self.assertEqual(["如何判断受众匹配"], rows[0]["retrieval_queries"])

    def test_rendered_index_exposes_owned_build_profile(self) -> None:
        rows = build_rows(self.create_root())
        payload = render_jsonl(rows)
        profile, parsed_rows = parse_index_document(payload, "generated.jsonl", require_owned=True)
        self.assertEqual(BUILD_PROFILE_DEFAULT, profile)
        self.assertEqual(BUILD_PROFILE_DEFAULT, detect_profile(payload, "generated.jsonl"))
        self.assertEqual(rows, parsed_rows)

    def test_write_and_check_detect_drift(self) -> None:
        root = self.create_root()
        self.assertEqual(0, main([str(root), "--write"]))
        self.assertEqual(0, main([str(root), "--check"]))
        note = root / "30-知识对象" / "model.md"
        note.write_text(
            NOTE.replace("Audience Fit Model", "Audience Fit Model Updated"), encoding="utf-8"
        )
        self.assertEqual(1, main([str(root), "--check"]))

    def test_write_atomically_replaces_an_owned_generated_index(self) -> None:
        root = self.create_root()
        self.assertEqual(0, main([str(root), "--write"]))
        note = root / "30-知识对象" / "model.md"
        note.write_text(
            NOTE.replace("Audience Fit Model", "Audience Fit Model Updated"), encoding="utf-8"
        )
        self.assertEqual(0, main([str(root), "--write"]))
        index_path = root / "00-AI入口" / "资产索引.jsonl"
        _, rows = parse_index_document(index_path.read_text(encoding="utf-8"), str(index_path))
        self.assertEqual("Audience Fit Model Updated", rows[0]["title"])

    def test_write_refuses_arbitrary_existing_jsonl(self) -> None:
        root = self.create_root()
        destination = root / "custom.jsonl"
        destination.write_text("source registry content\n", encoding="utf-8")
        self.assertEqual(2, main([str(root), "--write", "--output", destination.name]))
        self.assertEqual("source registry content\n", destination.read_text(encoding="utf-8"))

    def test_write_refuses_configured_source_registry_even_when_missing(self) -> None:
        root = self.create_root()
        manifest = root / "_meta" / "knowledge-base.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(
            '{"paths":{"asset_index":"index.jsonl",'
            '"source_registry_machine":"_meta/source-registry.jsonl"}}',
            encoding="utf-8",
        )
        registry = root / "_meta" / "source-registry.jsonl"
        self.assertEqual(
            2,
            main(
                [
                    str(root),
                    "--write",
                    "--output",
                    "_meta/source-registry.jsonl",
                ]
            ),
        )
        self.assertFalse(registry.exists())

    def test_write_refuses_markdown_destination(self) -> None:
        root = self.create_root()
        note = root / "30-知识对象" / "model.md"
        original = note.read_text(encoding="utf-8")
        self.assertEqual(
            2,
            main([str(root), "--write", "--output", "30-知识对象/model.md"]),
        )
        self.assertEqual(original, note.read_text(encoding="utf-8"))

    def test_restricted_assets_emit_only_opaque_routing_metadata(self) -> None:
        root = self.create_root()
        note = root / "30-知识对象" / "model.md"
        restricted = NOTE.replace("sensitivity: internal", "sensitivity: restricted").replace(
            "---\n# Audience Fit Model",
            "provenance: secret-source-details\n---\n# Secret Audience Fit Model\nDo not leak this body.",
        )
        note.write_text(restricted, encoding="utf-8")
        row = build_rows(root)[0]
        self.assertEqual("[restricted]", row["title"])
        self.assertTrue(row["restricted"])
        for field in (
            "summary",
            "provenance",
            "source_id",
            "source_ids",
            "source_anchors",
            "topics",
            "retrieval_queries",
        ):
            self.assertNotIn(field, row)
        rendered = render_jsonl([row])
        self.assertNotIn("Do not leak this body", rendered)
        self.assertNotIn("secret-source-details", rendered)

    def test_output_cannot_escape_root(self) -> None:
        root = self.create_root()
        outside = root.parent / "outside.jsonl"
        self.assertEqual(2, main([str(root), "--write", "--output", str(outside)]))
        self.assertFalse(outside.exists())

    def test_build_rows_skips_file_symlink_outside_root(self) -> None:
        root = self.create_root()
        outside_temp = tempfile.TemporaryDirectory()
        self.addCleanup(outside_temp.cleanup)
        outside = Path(outside_temp.name) / "secret.md"
        outside.write_text(NOTE.replace("model-audience-fit", "outside-secret"), encoding="utf-8")
        link = root / "30-知识对象" / "linked-secret.md"
        try:
            link.symlink_to(outside)
        except (NotImplementedError, OSError):
            link = root / "30-知识对象" / "linked-secret-directory"
            create_directory_link(link, outside.parent)
            self.addCleanup(remove_directory_link, link)
        self.assertEqual(["model-audience-fit"], [row["id"] for row in build_rows(root)])

    def test_build_rows_skips_directory_symlink_outside_root(self) -> None:
        root = self.create_root()
        outside_temp = tempfile.TemporaryDirectory()
        self.addCleanup(outside_temp.cleanup)
        outside = Path(outside_temp.name)
        (outside / "secret.md").write_text(
            NOTE.replace("model-audience-fit", "outside-secret"), encoding="utf-8"
        )
        link = root / "30-知识对象" / "linked-directory"
        create_directory_link(link, outside)
        self.addCleanup(remove_directory_link, link)
        self.assertEqual(["model-audience-fit"], [row["id"] for row in build_rows(root)])

    def test_write_refuses_symlink_destination_without_modifying_target(self) -> None:
        root = self.create_root()
        outside_temp = tempfile.TemporaryDirectory()
        self.addCleanup(outside_temp.cleanup)
        target_directory = Path(outside_temp.name)
        target = target_directory / "target.jsonl"
        target.write_text("protected\n", encoding="utf-8")
        link = root / "linked-index.jsonl"
        try:
            link.symlink_to(target)
            output = link.name
        except (NotImplementedError, OSError):
            link = root / "linked-output"
            create_directory_link(link, target_directory)
            self.addCleanup(remove_directory_link, link)
            output = "linked-output/target.jsonl"
        self.assertEqual(2, main([str(root), "--write", "--output", output]))
        self.assertEqual("protected\n", target.read_text(encoding="utf-8"))

    def test_directory_link_is_neither_traversed_nor_used_as_destination(self) -> None:
        root = self.create_root()
        outside_temp = tempfile.TemporaryDirectory()
        self.addCleanup(outside_temp.cleanup)
        outside = Path(outside_temp.name)
        (outside / "secret.md").write_text(
            NOTE.replace("model-audience-fit", "junction-secret"), encoding="utf-8"
        )
        junction = root / "30-知识对象" / "junction"
        create_directory_link(junction, outside)
        try:
            self.assertEqual(["model-audience-fit"], [row["id"] for row in build_rows(root)])
            self.assertEqual(
                2,
                main(
                    [
                        str(root),
                        "--write",
                        "--output",
                        "30-知识对象/junction/index.jsonl",
                    ]
                ),
            )
            self.assertFalse((outside / "index.jsonl").exists())
        finally:
            remove_directory_link(junction)

    def test_malformed_manifest_returns_code_2_without_traceback(self) -> None:
        root = self.create_root()
        manifest = root / "_meta" / "knowledge-base.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text('{"paths": ', encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), str(root), "--write"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(2, completed.returncode)
        self.assertNotIn("Traceback", completed.stderr)
        self.assertIn("Invalid JSON", completed.stderr)

    def test_malformed_index_check_returns_code_2_without_traceback(self) -> None:
        root = self.create_root()
        index_path = root / "broken.jsonl"
        index_path.write_text('{"id":\n', encoding="utf-8")
        completed = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                str(root),
                "--check",
                "--output",
                index_path.name,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        self.assertEqual(2, completed.returncode)
        self.assertNotIn("Traceback", completed.stderr)
        self.assertIn("Invalid JSON", completed.stderr)
