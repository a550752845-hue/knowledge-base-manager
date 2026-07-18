from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import init_knowledge_base
from init_knowledge_base import main as init_main
from lint_knowledge_base import main as lint_main


def run_init(argv: list[str]) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = init_main(argv)
    return code, stdout.getvalue(), stderr.getvalue()


def base_args(root: Path) -> list[str]:
    return [str(root), "--kb-id", "test-kb"]


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


class InitializationTests(unittest.TestCase):
    def test_dry_run_then_apply_is_non_destructive_and_healthy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "知识库"
            args = [
                str(root),
                "--kb-id",
                "test-kb",
                "--scope-type",
                "industry",
                "--industry",
                "healthcare",
            ]
            self.assertEqual(0, init_main(args))
            self.assertFalse(root.exists())
            self.assertEqual(0, init_main([*args, "--apply"]))
            rules = root / "_meta" / "知识库管理规则.md"
            original = rules.read_text(encoding="utf-8")
            self.assertEqual(0, init_main([*args, "--apply"]))
            self.assertEqual(original, rules.read_text(encoding="utf-8"))
            self.assertEqual(0, lint_main([str(root), "--check-index", "--strict"]))

            manifest_before = (root / "_meta" / "knowledge-base.json").read_text(encoding="utf-8")
            conflicting = [str(root), "--kb-id", "other-kb", "--scope-type", "general", "--apply"]
            self.assertEqual(1, init_main(conflicting))
            self.assertEqual(
                manifest_before,
                (root / "_meta" / "knowledge-base.json").read_text(encoding="utf-8"),
            )

    def test_json_stdout_is_exactly_one_document_for_dry_run_and_apply(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "knowledge"
            args = [*base_args(root), "--json"]

            dry_code, dry_stdout, dry_stderr = run_init(args)
            self.assertEqual(0, dry_code)
            self.assertEqual("", dry_stderr)
            dry_result = json.loads(dry_stdout)
            self.assertEqual("dry-run", dry_result["status"])
            self.assertFalse(root.exists())

            apply_code, apply_stdout, apply_stderr = run_init([*args, "--apply"])
            self.assertEqual(0, apply_code)
            self.assertEqual("", apply_stderr)
            apply_result = json.loads(apply_stdout)
            self.assertEqual("initialized", apply_result["status"])
            self.assertGreater(apply_result["created_files"], 0)

    def test_expected_file_directory_conflict_fails_before_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "knowledge"
            blocked = root / "_meta" / "来源注册表.md"
            blocked.mkdir(parents=True)

            code, _, _ = run_init([*base_args(root), "--apply"])

            self.assertEqual(1, code)
            self.assertTrue(blocked.is_dir())
            self.assertFalse((root / "00-AI入口").exists())
            self.assertFalse((root / "_meta" / "knowledge-base.json").exists())

    def test_expected_file_link_or_junction_conflict_fails_before_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "knowledge"
            target = Path(temp) / "target"
            target.mkdir()
            link = root / "_meta" / "knowledge-base.json"
            link.parent.mkdir(parents=True)
            create_directory_link(link, target)
            try:
                code, _, _ = run_init([*base_args(root), "--apply"])
                self.assertEqual(1, code)
                self.assertTrue(os.path.lexists(link))
                self.assertFalse((root / "00-AI入口").exists())
            finally:
                remove_directory_link(link)

    def test_every_new_file_uses_exclusive_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "knowledge"
            real_writer = init_knowledge_base.exclusive_write_text
            with patch.object(
                init_knowledge_base, "exclusive_write_text", wraps=real_writer
            ) as writer:
                code, stdout, _ = run_init([*base_args(root), "--json", "--apply"])

            result = json.loads(stdout)
            self.assertEqual(0, code)
            self.assertEqual(result["created_files"], writer.call_count)
            self.assertGreater(writer.call_count, 0)

    def test_concurrent_file_creation_is_preserved_and_returns_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "knowledge"
            real_writer = init_knowledge_base.exclusive_write_text
            raced_paths: list[Path] = []

            def race_once(path: Path, payload: str) -> None:
                if not raced_paths:
                    path.write_text("concurrent owner", encoding="utf-8")
                    raced_paths.append(path)
                real_writer(path, payload)

            with patch.object(init_knowledge_base, "exclusive_write_text", side_effect=race_once):
                code, stdout, stderr = run_init([*base_args(root), "--json", "--apply"])

            result = json.loads(stdout)
            self.assertEqual(1, code)
            self.assertEqual("conflict", result["status"])
            self.assertEqual("", stderr)
            self.assertEqual("concurrent owner", raced_paths[0].read_text(encoding="utf-8"))

    def test_json_runtime_error_returns_two_without_extra_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "knowledge"
            with patch.object(
                init_knowledge_base,
                "exclusive_write_text",
                side_effect=PermissionError("denied"),
            ):
                code, stdout, stderr = run_init([*base_args(root), "--json", "--apply"])

            result = json.loads(stdout)
            self.assertEqual(2, code)
            self.assertEqual("error", result["status"])
            self.assertEqual("", stderr)
