from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from source_integrity import (
    MANIFEST_OWNER,
    SourceChangedDuringHashError,
    build_snapshot,
    main,
    verify_snapshot,
)


def run_quietly(argv: list[str]) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = main(argv)
    return code, stdout.getvalue(), stderr.getvalue()


def create_directory_link(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=True)
        return
    except (NotImplementedError, OSError):
        pass
    if os.name != "nt":
        raise unittest.SkipTest("Directory symlinks are not available on this platform")
    completed = subprocess.run(
        ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if completed.returncode != 0:
        raise unittest.SkipTest("Directory symlinks and junctions are unavailable")


def remove_directory_link(link: Path) -> None:
    if not os.path.lexists(link):
        return
    checker = getattr(link, "is_junction", None)
    if checker is not None and checker():
        link.rmdir()
    else:
        link.unlink()


class SourceIntegrityTests(unittest.TestCase):
    def test_snapshot_detects_content_change_and_new_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "sources"
            root.mkdir()
            source = root / "transcript.txt"
            source.write_text("original", encoding="utf-8")
            snapshot = build_snapshot([root], [])
            self.assertTrue(verify_snapshot(snapshot, check_new=True)["ok"])

            source.write_text("modified", encoding="utf-8")
            (root / "new.txt").write_text("new", encoding="utf-8")
            result = verify_snapshot(snapshot, check_new=True)
            self.assertFalse(result["ok"])
            self.assertEqual(1, len(result["changed"]))
            self.assertEqual(1, len(result["unexpected"]))

    def test_manifest_cannot_be_written_inside_source_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "sources"
            root.mkdir()
            (root / "source.txt").write_text("source", encoding="utf-8")
            self.assertEqual(
                2,
                main(
                    [
                        "snapshot",
                        "--source",
                        str(root),
                        "--output",
                        str(root / "integrity.json"),
                        "--apply",
                    ]
                ),
            )

    def test_missing_empty_source_root_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "empty"
            root.mkdir()
            snapshot = build_snapshot([root], [])
            root.rmdir()
            result = verify_snapshot(snapshot, check_new=True)
            self.assertFalse(result["ok"])
            self.assertEqual([str(root.resolve(strict=False))], result["missing_roots"])

    def test_manifest_v2_preserves_lexical_roots_and_handles_overlap_deterministically(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "sources"
            child = root / "child"
            child.mkdir(parents=True)
            (root / "parent.txt").write_text("parent", encoding="utf-8")
            (child / "child.txt").write_text("child", encoding="utf-8")

            first = build_snapshot([root, child], [])
            second = build_snapshot([child, root], [])

            self.assertEqual(2, first["manifest_version"])
            self.assertEqual(MANIFEST_OWNER, first["manifest_owner"])
            self.assertEqual(first["source_roots"], second["source_roots"])
            self.assertEqual(first["files"], second["files"])
            self.assertTrue(all("root_id" in row for row in first["files"]))
            self.assertTrue(all("relative_path" in row for row in first["files"]))
            self.assertEqual(2, len(first["files"]))
            self.assertTrue(verify_snapshot(first, check_new=True)["ok"])

    def test_existing_arbitrary_output_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "sources"
            root.mkdir()
            (root / "source.txt").write_text("source", encoding="utf-8")
            output = Path(temp) / "integrity.json"
            for existing in ("hands off", '{"ordinary": true}\n'):
                with self.subTest(existing=existing):
                    output.write_text(existing, encoding="utf-8")
                    code, _, stderr = run_quietly(
                        [
                            "snapshot",
                            "--source",
                            str(root),
                            "--output",
                            str(output),
                            "--apply",
                        ]
                    )
                    self.assertEqual(2, code)
                    self.assertEqual(existing, output.read_text(encoding="utf-8"))
                    self.assertNotIn("Traceback", stderr)

    def test_owned_output_can_be_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "sources"
            root.mkdir()
            source = root / "source.txt"
            source.write_text("first", encoding="utf-8")
            output = Path(temp) / "integrity.json"
            args = [
                "snapshot",
                "--source",
                str(root),
                "--output",
                str(output),
                "--apply",
            ]
            self.assertEqual(0, run_quietly(args)[0])
            first = json.loads(output.read_text(encoding="utf-8"))
            source.write_text("second", encoding="utf-8")
            self.assertEqual(0, run_quietly(args)[0])
            second = json.loads(output.read_text(encoding="utf-8"))
            self.assertNotEqual(first["files"][0]["sha256"], second["files"][0]["sha256"])

    def test_v1_manifest_is_verified_but_not_treated_as_owned_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "sources"
            root.mkdir()
            source = root / "source.txt"
            payload = b"legacy"
            source.write_bytes(payload)
            result = source.stat()
            legacy = {
                "manifest_version": 1,
                "source_roots": [str(root.resolve())],
                "excludes": [],
                "files": [
                    {
                        "path": str(source.resolve()),
                        "kind": "file",
                        "size": result.st_size,
                        "mtime_ns": result.st_mtime_ns,
                        "sha256": hashlib.sha256(payload).hexdigest(),
                    }
                ],
            }
            self.assertTrue(verify_snapshot(legacy, check_new=True)["ok"])

            output = Path(temp) / "legacy.json"
            original = json.dumps(legacy)
            output.write_text(original, encoding="utf-8")
            code, _, _ = run_quietly(
                [
                    "snapshot",
                    "--source",
                    str(root),
                    "--output",
                    str(output),
                    "--apply",
                ]
            )
            self.assertEqual(2, code)
            self.assertEqual(original, output.read_text(encoding="utf-8"))

    def test_malformed_manifest_collection_types_return_two_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "sources"
            root.mkdir()
            (root / "source.txt").write_text("source", encoding="utf-8")
            baseline = build_snapshot([root], [])
            manifest_path = Path(temp) / "manifest.json"
            malformed_documents: list[dict[str, object]] = []
            for field, value in (
                ("excludes", "*.tmp"),
                ("source_roots", {}),
                ("files", {}),
            ):
                malformed = copy.deepcopy(baseline)
                malformed[field] = value
                malformed_documents.append(malformed)
            malformed = copy.deepcopy(baseline)
            malformed["source_roots"] = ["not-an-object"]
            malformed_documents.append(malformed)
            malformed = copy.deepcopy(baseline)
            malformed["files"] = ["not-an-object"]
            malformed_documents.append(malformed)

            for malformed in malformed_documents:
                with self.subTest(document=malformed):
                    manifest_path.write_text(json.dumps(malformed), encoding="utf-8")
                    code, _, stderr = run_quietly(
                        ["verify", "--manifest", str(manifest_path), "--check-new"]
                    )
                    self.assertEqual(2, code)
                    self.assertNotIn("Traceback", stderr)

            manifest_path.write_text(
                '{"manifest_version":2,"manifest_version":1}', encoding="utf-8"
            )
            code, _, stderr = run_quietly(["verify", "--manifest", str(manifest_path)])
            self.assertEqual(2, code)
            self.assertNotIn("Traceback", stderr)

    def test_verification_reports_a_file_that_changes_during_hashing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "sources"
            root.mkdir()
            (root / "source.txt").write_text("source", encoding="utf-8")
            baseline = build_snapshot([root], [])
            with patch(
                "source_integrity.hash_file_stable",
                side_effect=SourceChangedDuringHashError("changed"),
            ):
                result = verify_snapshot(baseline, check_new=False)
            self.assertFalse(result["ok"])
            self.assertEqual("changed-during-hash", result["changed"][0]["reason"])

    def test_link_root_retargeting_and_target_content_changes_are_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            first_target = base / "first"
            second_target = base / "second"
            first_target.mkdir()
            second_target.mkdir()
            (first_target / "source.txt").write_text("first", encoding="utf-8")
            (second_target / "source.txt").write_text("second", encoding="utf-8")
            (second_target / "new.txt").write_text("new", encoding="utf-8")
            link = base / "linked-root"
            create_directory_link(link, first_target)
            try:
                baseline = build_snapshot([link], [])
                root_row = baseline["source_roots"][0]
                self.assertEqual(str(link.absolute()), root_row["path"])
                self.assertIn(root_row["kind"], {"symlink", "junction"})
                self.assertTrue(verify_snapshot(baseline, check_new=True)["ok"])

                remove_directory_link(link)
                create_directory_link(link, second_target)
                result = verify_snapshot(baseline, check_new=True)
                reasons = {row["reason"] for row in result["changed"]}
                self.assertFalse(result["ok"])
                self.assertIn("root-target", reasons)
                self.assertIn("root-resolved-identity", reasons)
                self.assertIn("content", reasons)
                self.assertEqual(1, len(result["unexpected"]))
            finally:
                remove_directory_link(link)

    def test_nested_links_are_recorded_without_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "sources"
            external = base / "external"
            root.mkdir()
            external.mkdir()
            (external / "outside.txt").write_text("outside", encoding="utf-8")
            nested = root / "nested"
            create_directory_link(nested, external)
            try:
                baseline = build_snapshot([root], [])
                self.assertEqual(1, len(baseline["files"]))
                self.assertEqual("nested", baseline["files"][0]["relative_path"])
                self.assertIn(baseline["files"][0]["kind"], {"symlink", "junction"})
                self.assertTrue(verify_snapshot(baseline, check_new=True)["ok"])
            finally:
                remove_directory_link(nested)
