"""Single entrypoint for deterministic knowledge-base operations."""

from __future__ import annotations

import sys
from collections.abc import Callable
from functools import partial
from importlib import import_module
from pathlib import Path

VERSION = "1.0.0"
REQUIREMENTS_FILE = Path(__file__).resolve().parents[1] / "requirements.txt"
COMMAND_MODULES = {
    "doctor": "lint_knowledge_base",
    "index": "build_asset_index",
    "query": "query_asset_index",
    "init": "init_knowledge_base",
    "source": "source_integrity",
}


def _dependency_name(exc: ImportError | SystemExit) -> str | None:
    if isinstance(exc, ImportError):
        return exc.name or str(exc)

    message = exc.code if isinstance(exc.code, str) else ""
    marker = " is required"
    if marker in message and "pip install" in message:
        return message.split(marker, 1)[0].strip()
    return None


def _print_dependency_error(command: str, dependency: str) -> None:
    print(
        f"Cannot run '{command}': missing runtime dependency '{dependency}'.",
        file=sys.stderr,
    )
    print("Install the skill requirements with:", file=sys.stderr)
    print(f'  python -m pip install -r "{REQUIREMENTS_FILE}"', file=sys.stderr)


def _run_command(command: str, args: list[str] | None) -> int:
    try:
        module = import_module(COMMAND_MODULES[command])
    except (ImportError, SystemExit) as exc:
        dependency = _dependency_name(exc)
        if dependency is None:
            raise
        _print_dependency_error(command, dependency)
        return 2
    return module.main(args)


def commands() -> dict[str, Callable[[list[str] | None], int]]:
    """Return dependency-free lazy entrypoints for all supported commands."""

    return {command: partial(_run_command, command) for command in COMMAND_MODULES}


def print_help() -> None:
    print("Knowledge Base Manager deterministic tools")
    print()
    print("Usage: python scripts/kb.py <command> [arguments]")
    print()
    print("Commands:")
    print("  doctor  Audit structure, semantics, provenance, links, and freshness")
    print("  index   Build, write, or verify the machine asset index")
    print("  query   Shortlist indexed assets by task intent and scope")
    print("  init    Plan or initialize a non-destructive schema-v3 root")
    print("  source  Snapshot or verify immutable source files")
    print()
    print("Options:")
    print("  --version  Show the CLI version")
    print()
    print("Run '<command> --help' for command-specific options.")


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in {"-h", "--help", "help"}:
        print_help()
        return 0
    if args[0] == "--version":
        print(f"Knowledge Base Manager {VERSION}")
        return 0
    command = args.pop(0)
    available = commands()
    if command not in available:
        print(f"Unknown command: {command}", file=sys.stderr)
        print_help()
        return 2
    return available[command](args)


if __name__ == "__main__":
    raise SystemExit(main())
