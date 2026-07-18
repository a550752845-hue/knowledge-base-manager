from __future__ import annotations

import contextlib
import io
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import kb


class CliRouterTests(unittest.TestCase):
    def capture(self, argv: list[str] | None) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = kb.main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_command_registry_exposes_every_supported_operation(self) -> None:
        with patch.object(kb, "import_module") as importer:
            available = kb.commands()

        self.assertEqual({"doctor", "index", "query", "init", "source"}, set(available))
        self.assertTrue(all(callable(entrypoint) for entrypoint in available.values()))
        importer.assert_not_called()

    def test_selected_command_imports_only_its_module(self) -> None:
        for command, module_name in kb.COMMAND_MODULES.items():
            with self.subTest(command=command):
                entrypoint = Mock(return_value=7)
                module = SimpleNamespace(main=entrypoint)
                with patch.object(kb, "import_module", return_value=module) as importer:
                    code, stdout, stderr = self.capture([command, "root", "--json"])

                self.assertEqual(7, code)
                importer.assert_called_once_with(module_name)
                entrypoint.assert_called_once_with(["root", "--json"])
                self.assertEqual("", stdout)
                self.assertEqual("", stderr)

    def test_each_command_receives_unmodified_remaining_arguments(self) -> None:
        for command in ("doctor", "index", "query", "init", "source"):
            with self.subTest(command=command):
                entrypoint = Mock(return_value=7)
                with patch.object(kb, "commands", return_value={command: entrypoint}):
                    code, stdout, stderr = self.capture([command, "root", "--json"])

                self.assertEqual(7, code)
                entrypoint.assert_called_once_with(["root", "--json"])
                self.assertEqual("", stdout)
                self.assertEqual("", stderr)

    def test_help_aliases_do_not_load_command_registry(self) -> None:
        for argv in ([], ["-h"], ["--help"], ["help"]):
            with (
                self.subTest(argv=argv),
                patch.object(kb, "commands") as registry,
                patch.object(kb, "import_module") as importer,
            ):
                code, stdout, stderr = self.capture(argv)

            self.assertEqual(0, code)
            self.assertIn("Knowledge Base Manager deterministic tools", stdout)
            self.assertEqual("", stderr)
            registry.assert_not_called()
            importer.assert_not_called()

    def test_unknown_command_returns_usage_error_without_importing(self) -> None:
        with patch.object(kb, "import_module") as importer:
            code, stdout, stderr = self.capture(["unknown"])

        self.assertEqual(2, code)
        self.assertIn("Usage:", stdout)
        self.assertIn("Unknown command: unknown", stderr)
        importer.assert_not_called()

    def test_version_is_dependency_free(self) -> None:
        with patch.object(kb, "import_module") as importer:
            code, stdout, stderr = self.capture(["--version"])

        self.assertEqual("1.0.0", kb.VERSION)
        self.assertEqual("Knowledge Base Manager 1.0.0\n", stdout)
        self.assertEqual("", stderr)
        self.assertEqual(0, code)
        importer.assert_not_called()

    def test_missing_dependency_returns_actionable_usage_error(self) -> None:
        missing = ModuleNotFoundError("No module named 'yaml'", name="yaml")
        with patch.object(kb, "import_module", side_effect=missing):
            code, stdout, stderr = self.capture(["index", "root"])

        self.assertEqual(2, code)
        self.assertEqual("", stdout)
        self.assertIn("missing runtime dependency 'yaml'", stderr)
        self.assertIn(f'python -m pip install -r "{kb.REQUIREMENTS_FILE}"', stderr)
        self.assertNotIn("Traceback", stderr)

    def test_wrapped_dependency_error_is_normalized(self) -> None:
        wrapped = SystemExit(
            "PyYAML is required. Install the skill requirements with: "
            "python -m pip install -r requirements.txt"
        )
        with patch.object(kb, "import_module", side_effect=wrapped):
            code, stdout, stderr = self.capture(["source", "verify"])

        self.assertEqual(2, code)
        self.assertEqual("", stdout)
        self.assertIn("missing runtime dependency 'PyYAML'", stderr)
        self.assertIn(f'python -m pip install -r "{kb.REQUIREMENTS_FILE}"', stderr)
        self.assertNotIn("Traceback", stderr)

    def test_none_argv_uses_process_arguments(self) -> None:
        with patch.object(sys, "argv", ["kb.py", "help"]):
            code, stdout, stderr = self.capture(None)

        self.assertEqual(0, code)
        self.assertIn("Commands:", stdout)
        self.assertEqual("", stderr)


if __name__ == "__main__":
    unittest.main()
