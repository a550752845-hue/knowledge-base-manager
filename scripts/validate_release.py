#!/usr/bin/env python3
"""Validate the repository as a public skill-only Codex plugin release."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote

import yaml
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_NAME = "knowledge-base-manager"
SKILL_NAME = "transcript-knowledge-manager"
RELEASE_VERSION = "1.0.0"
REPOSITORY_URL = "https://github.com/a550752845-hue/knowledge-base-manager"
PRIVACY_URL = f"{REPOSITORY_URL}/blob/main/PRIVACY.md"
TERMS_URL = f"{REPOSITORY_URL}/blob/main/LICENSE"

PLUGIN_RELATIVE = Path("plugins") / PLUGIN_NAME
SKILL_RELATIVE = PLUGIN_RELATIVE / "skills" / SKILL_NAME
MANIFEST_RELATIVE = PLUGIN_RELATIVE / ".codex-plugin" / "plugin.json"
MARKETPLACE_RELATIVE = Path(".agents") / "plugins" / "marketplace.json"
CI_RELATIVE = Path(".github") / "workflows" / "ci.yml"

TEXT_SUFFIXES = {".json", ".md", ".py", ".toml", ".txt", ".yaml", ".yml"}
TEXT_FILENAMES = {".gitattributes", ".gitignore", "CODEOWNERS", "LICENSE"}
EXCLUDED_DIRECTORY_NAMES = {
    ".git",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".release-smoke",
    ".ruff_cache",
    ".tox",
    ".venv",
    "build",
    "dist",
    "env",
    "htmlcov",
    "node_modules",
    "venv",
}


class Report:
    """Collect all release failures so one run gives a complete repair list."""

    def __init__(self) -> None:
        self.checks = 0
        self.errors: list[str] = []

    def require(self, condition: bool, message: str) -> None:
        self.checks += 1
        if not condition:
            self.errors.append(message)

    def fail(self, message: str) -> None:
        self.checks += 1
        self.errors.append(message)


def display(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def is_excluded(path: Path, root: Path) -> bool:
    return any(part in EXCLUDED_DIRECTORY_NAMES for part in path.relative_to(root).parts)


def repository_glob(root: Path, pattern: str) -> list[Path]:
    return sorted(path for path in root.rglob(pattern) if not is_excluded(path, root))


def read_text(path: Path, root: Path, report: Report) -> str | None:
    report.checks += 1
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        report.errors.append(f"Cannot read UTF-8 text {display(path, root)}: {exc}")
        return None


def reject_duplicate_json_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path, root: Path, report: Report) -> Any | None:
    text = read_text(path, root, report)
    if text is None:
        return None
    report.checks += 1
    try:
        return json.loads(text, object_pairs_hook=reject_duplicate_json_keys)
    except (json.JSONDecodeError, ValueError) as exc:
        report.errors.append(f"Invalid JSON {display(path, root)}: {exc}")
        return None


def load_yaml(path: Path, root: Path, report: Report) -> Any | None:
    text = read_text(path, root, report)
    if text is None:
        return None
    report.checks += 1
    try:
        return yaml.safe_load(text)
    except yaml.YAMLError as exc:
        report.errors.append(f"Invalid YAML {display(path, root)}: {exc}")
        return None


def validate_structure(root: Path, report: Report) -> None:
    required_files = (
        Path("README.md"),
        Path("LICENSE"),
        Path("CHANGELOG.md"),
        Path("CONTRIBUTING.md"),
        Path("SECURITY.md"),
        Path("PRIVACY.md"),
        Path(".gitignore"),
        Path(".gitattributes"),
        Path("pyproject.toml"),
        Path("requirements-dev.txt"),
        Path("scripts") / "validate_release.py",
        Path("scripts") / "smoke_e2e.py",
        MARKETPLACE_RELATIVE,
        MANIFEST_RELATIVE,
        CI_RELATIVE,
        SKILL_RELATIVE / "SKILL.md",
        SKILL_RELATIVE / "agents" / "openai.yaml",
        SKILL_RELATIVE / "requirements.txt",
        SKILL_RELATIVE / "scripts" / "kb.py",
    )
    for relative in required_files:
        report.require((root / relative).is_file(), f"Missing required file: {relative.as_posix()}")

    required_directories = (
        SKILL_RELATIVE / "references",
        SKILL_RELATIVE / "scripts",
        SKILL_RELATIVE / "tests",
    )
    for relative in required_directories:
        report.require(
            (root / relative).is_dir(), f"Missing required directory: {relative.as_posix()}"
        )

    tests = sorted((root / SKILL_RELATIVE / "tests").glob("test_*.py"))
    report.require(bool(tests), "Skill tests directory must contain at least one test_*.py file")


def validate_structured_files(root: Path, report: Report) -> dict[Path, Any]:
    documents: dict[Path, Any] = {}

    for path in repository_glob(root, "*.json"):
        document = load_json(path, root, report)
        if document is not None:
            documents[path] = document
        if path.name.endswith(".schema.json") and isinstance(document, dict):
            report.checks += 1
            try:
                Draft202012Validator.check_schema(document)
            except SchemaError as exc:
                report.errors.append(f"Invalid JSON Schema {display(path, root)}: {exc.message}")

    yaml_paths = repository_glob(root, "*.yaml") + repository_glob(root, "*.yml")
    for path in yaml_paths:
        document = load_yaml(path, root, report)
        if document is not None:
            documents[path] = document

    pyproject = root / "pyproject.toml"
    text = read_text(pyproject, root, report)
    if text is not None:
        report.checks += 1
        try:
            documents[pyproject] = tomllib.loads(text)
        except tomllib.TOMLDecodeError as exc:
            report.errors.append(f"Invalid TOML pyproject.toml: {exc}")

    return documents


def validate_skill_frontmatter(root: Path, report: Report) -> None:
    skill_path = root / SKILL_RELATIVE / "SKILL.md"
    text = read_text(skill_path, root, report)
    if text is None:
        return

    match = re.match(r"\A---\s*\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", text, flags=re.DOTALL)
    report.require(match is not None, "Skill SKILL.md must start with YAML frontmatter")
    if match is None:
        return

    report.checks += 1
    try:
        metadata = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        report.errors.append(f"Invalid Skill frontmatter YAML: {exc}")
        return

    report.require(isinstance(metadata, dict), "Skill frontmatter must be a YAML mapping")
    if not isinstance(metadata, dict):
        return
    report.require(metadata.get("name") == SKILL_NAME, "Skill frontmatter name is inconsistent")
    report.require(
        isinstance(metadata.get("description"), str) and bool(metadata["description"].strip()),
        "Skill frontmatter description must be non-empty",
    )


def resolve_relative_path(
    base: Path,
    raw_path: Any,
    boundary: Path,
    label: str,
    report: Report,
) -> Path | None:
    report.require(isinstance(raw_path, str), f"{label} must be a string")
    if not isinstance(raw_path, str):
        return None
    report.require(raw_path.startswith("./"), f"{label} must start with ./")
    candidate = (base / raw_path).resolve()
    report.require(candidate.is_relative_to(boundary.resolve()), f"{label} escapes its boundary")
    report.require(candidate.exists(), f"{label} does not exist: {raw_path}")
    return candidate


def validate_plugin_manifest(manifest: Any, root: Path, report: Report) -> None:
    report.require(isinstance(manifest, dict), "Plugin manifest must be a JSON object")
    if not isinstance(manifest, dict):
        return

    report.require(manifest.get("name") == PLUGIN_NAME, "Plugin manifest name is inconsistent")
    version = manifest.get("version")
    report.require(isinstance(version, str), "Plugin version must be a string")
    if isinstance(version, str):
        report.require(
            re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", version) is not None,
            "Plugin version must be strict semantic versioning",
        )
        report.require(version == RELEASE_VERSION, "Plugin version must match the release version")

    report.require(
        isinstance(manifest.get("description"), str) and bool(manifest["description"].strip()),
        "Plugin description must be non-empty",
    )
    report.require(manifest.get("repository") == REPOSITORY_URL, "Plugin repository URL is wrong")
    report.require(manifest.get("homepage") == REPOSITORY_URL, "Plugin homepage URL is wrong")
    report.require(manifest.get("license") == "MIT", "Plugin license must be MIT")

    author = manifest.get("author")
    report.require(isinstance(author, dict), "Plugin author must be an object")
    if isinstance(author, dict):
        report.require(author.get("name") == "chen", "Plugin author name must be chen")
        report.require(
            author.get("url") == "https://github.com/a550752845-hue",
            "Plugin author URL is wrong",
        )
        report.require("email" not in author, "Plugin manifest must not publish an author email")

    plugin_root = root / PLUGIN_RELATIVE
    skills_root = resolve_relative_path(
        plugin_root, manifest.get("skills"), plugin_root, "Plugin skills path", report
    )
    if skills_root is not None:
        skill_manifests = sorted(skills_root.glob("*/SKILL.md"))
        report.require(bool(skill_manifests), "Plugin skills path contains no Skill")
        report.require(
            skills_root / SKILL_NAME / "SKILL.md" in skill_manifests,
            "Expected Skill is not discoverable from the plugin skills path",
        )

    for unsupported in ("apps", "hooks", "mcpServers"):
        report.require(
            unsupported not in manifest,
            f"Skill-only plugin manifest must not declare {unsupported}",
        )

    interface = manifest.get("interface")
    report.require(isinstance(interface, dict), "Plugin interface must be an object")
    if not isinstance(interface, dict):
        return
    for key in (
        "displayName",
        "shortDescription",
        "longDescription",
        "developerName",
        "category",
        "capabilities",
        "websiteURL",
        "privacyPolicyURL",
        "termsOfServiceURL",
        "defaultPrompt",
    ):
        report.require(key in interface, f"Plugin interface is missing {key}")
    report.require(interface.get("developerName") == "chen", "Plugin developerName is inconsistent")
    expected_urls = {
        "websiteURL": REPOSITORY_URL,
        "privacyPolicyURL": PRIVACY_URL,
        "termsOfServiceURL": TERMS_URL,
    }
    for key, expected in expected_urls.items():
        value = interface.get(key)
        report.require(
            isinstance(value, str) and value.startswith("https://"), f"{key} must use HTTPS"
        )
        report.require(value == expected, f"{key} is inconsistent with the public release URL")

    prompts = interface.get("defaultPrompt")
    report.require(isinstance(prompts, list), "Plugin defaultPrompt must be an array")
    if isinstance(prompts, list):
        report.require(1 <= len(prompts) <= 3, "Plugin defaultPrompt must contain 1 to 3 prompts")
        for index, prompt in enumerate(prompts):
            report.require(
                isinstance(prompt, str) and 0 < len(prompt) <= 128,
                f"Plugin defaultPrompt[{index}] must be 1 to 128 characters",
            )


def validate_marketplace(marketplace: Any, root: Path, report: Report) -> None:
    report.require(isinstance(marketplace, dict), "Marketplace manifest must be a JSON object")
    if not isinstance(marketplace, dict):
        return

    report.require(marketplace.get("name") == PLUGIN_NAME, "Marketplace name is inconsistent")
    interface = marketplace.get("interface")
    report.require(isinstance(interface, dict), "Marketplace interface must be an object")
    if isinstance(interface, dict):
        report.require(
            interface.get("displayName") == "Knowledge Base Manager",
            "Marketplace displayName is inconsistent",
        )

    plugins = marketplace.get("plugins")
    report.require(isinstance(plugins, list), "Marketplace plugins must be an array")
    if not isinstance(plugins, list):
        return
    report.require(len(plugins) == 1, "Marketplace must contain exactly one plugin entry")
    if len(plugins) != 1 or not isinstance(plugins[0], dict):
        return

    entry = plugins[0]
    report.require(entry.get("name") == PLUGIN_NAME, "Marketplace plugin name is inconsistent")
    report.require(entry.get("category") == "Productivity", "Marketplace category is inconsistent")

    source = entry.get("source")
    report.require(isinstance(source, dict), "Marketplace source must be an object")
    if isinstance(source, dict):
        report.require(source.get("source") == "local", "Marketplace source must be local")
        expected_path = f"./plugins/{PLUGIN_NAME}"
        report.require(
            source.get("path") == expected_path, "Marketplace source path is inconsistent"
        )
        resolved = resolve_relative_path(
            root, source.get("path"), root, "Marketplace source path", report
        )
        if resolved is not None:
            report.require(
                resolved == (root / PLUGIN_RELATIVE).resolve(),
                "Marketplace source does not resolve to the plugin root",
            )

    policy = entry.get("policy")
    report.require(isinstance(policy, dict), "Marketplace policy must be an object")
    if isinstance(policy, dict):
        report.require(
            policy.get("installation") == "AVAILABLE",
            "Marketplace installation policy must be AVAILABLE",
        )
        report.require(
            policy.get("authentication") == "ON_INSTALL",
            "Marketplace authentication policy must be ON_INSTALL",
        )


def iter_text_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for path in repository_glob(root, "*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name in TEXT_FILENAMES:
            paths.append(path)
    return sorted(paths)


def validate_markdown_links(root: Path, report: Report) -> None:
    link_pattern = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
    for path in repository_glob(root, "*.md"):
        relative_parts = path.relative_to(root).parts
        if "evals" in relative_parts and "fixtures" in relative_parts:
            continue
        text = read_text(path, root, report)
        if text is None:
            continue
        for raw_target in link_pattern.findall(text):
            target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
            if target.startswith(("#", "https://", "http://", "mailto:")):
                continue
            relative = unquote(target.split("#", 1)[0].split("?", 1)[0])
            if not relative:
                continue
            resolved = (path.parent / relative).resolve()
            report.require(
                resolved.is_relative_to(root.resolve()),
                f"Markdown link escapes repository: {display(path, root)} -> {target}",
            )
            report.require(
                resolved.exists(),
                f"Broken Markdown link: {display(path, root)} -> {target}",
            )


def validate_skill_references(root: Path, report: Report) -> None:
    skill_root = root / SKILL_RELATIVE
    skill_path = skill_root / "SKILL.md"
    text = read_text(skill_path, root, report)
    if text is None:
        return

    token_pattern = re.compile(
        r"(?<![A-Za-z0-9_-])((?:references|scripts)/[A-Za-z0-9._-]+\.(?:json|md|py|txt|yaml|yml)|requirements\.txt)"
    )
    references = sorted(set(token_pattern.findall(text)))
    report.require(bool(references), "Skill SKILL.md must reference its supporting files")
    for reference in references:
        target = (skill_root / reference).resolve()
        report.require(
            target.is_relative_to(skill_root.resolve()), f"Skill reference escapes: {reference}"
        )
        report.require(target.is_file(), f"Missing Skill reference: {reference}")


def validate_version_and_docs(root: Path, report: Report) -> None:
    kb_cli = read_text(root / SKILL_RELATIVE / "scripts" / "kb.py", root, report)
    if kb_cli is not None:
        version_match = re.search(
            r'(?m)^VERSION\s*=\s*["\']([^"\']+)["\']\s*$',
            kb_cli,
        )
        report.require(version_match is not None, "kb.py must declare a literal VERSION")
        if version_match is not None:
            report.require(
                version_match.group(1) == RELEASE_VERSION,
                "kb.py VERSION must match the release version",
            )

    changelog = read_text(root / "CHANGELOG.md", root, report)
    if changelog is not None:
        report.require(
            f"## [{RELEASE_VERSION}]" in changelog,
            "CHANGELOG does not contain the release version",
        )
        report.require(
            REPOSITORY_URL in changelog, "CHANGELOG release link uses the wrong repository"
        )

    readme = read_text(root / "README.md", root, report)
    if readme is None:
        return
    required_fragments = (
        f"codex plugin marketplace add a550752845-hue/{PLUGIN_NAME} --ref v{RELEASE_VERSION}",
        f"codex plugin marketplace upgrade {PLUGIN_NAME}",
        f"git clone {REPOSITORY_URL}.git",
        "codex plugin marketplace add .",
        f"codex plugin add {PLUGIN_NAME}@{PLUGIN_NAME}",
        f"codex plugin remove {PLUGIN_NAME}@{PLUGIN_NAME}",
        f"codex plugin marketplace remove {PLUGIN_NAME}",
        "$transcript-knowledge-manager",
        "插件是唯一规范来源",
        "scripts/kb.py --help",
        "scripts/smoke_e2e.py",
        "PyYAML",
        "jsonschema",
        "PowerShell",
        "--fail-under=75",
        "## 架构",
        "## 安全",
        "## CLI",
        "## 开发与验证",
        "PRIVACY.md",
        RELEASE_VERSION,
    )
    for fragment in required_fragments:
        report.require(fragment in readme, f"README is missing required content: {fragment}")
    for forbidden in ("可单独安装", "只安装或升级 Skill", "skill-backups", "Copy-Item -Recurse"):
        report.require(forbidden not in readme, f"README must remain plugin-only: {forbidden}")


def validate_ci_and_dependencies(root: Path, report: Report) -> None:
    requirement_sets = (
        (root / "requirements-dev.txt", ("coverage", "jsonschema", "PyYAML", "ruff")),
        (
            root / SKILL_RELATIVE / "requirements.txt",
            ("jsonschema", "PyYAML"),
        ),
    )
    for path, packages in requirement_sets:
        requirements = read_text(path, root, report)
        if requirements is None:
            continue
        for package in packages:
            pattern = re.compile(rf"(?mi)^{package}(?:\[[^\]]+\])?\s*[<>=!~]")
            report.require(
                pattern.search(requirements) is not None,
                f"{display(path, root)} lacks {package}",
            )

    ci = read_text(root / CI_RELATIVE, root, report)
    if ci is None:
        return
    required_ci_fragments = (
        "ubuntu-latest",
        "windows-latest",
        'python-version: "3.11"',
        'python-version: "3.14"',
        "requirements-dev.txt",
        "ruff check .",
        "ruff format --check .",
        "python scripts/validate_release.py",
        "python scripts/smoke_e2e.py",
        "python -m coverage run",
        "--fail-under=75",
        "python -m coverage xml",
        "py_compile",
    )
    for fragment in required_ci_fragments:
        report.require(fragment in ci, f"CI is missing required command or platform: {fragment}")

    report.checks += 1
    try:
        workflow = yaml.safe_load(ci)
    except yaml.YAMLError as exc:
        report.errors.append(f"Cannot inspect CI workflow semantics: {exc}")
        return
    jobs = workflow.get("jobs") if isinstance(workflow, dict) else None
    report.require(isinstance(jobs, dict), "CI workflow must declare jobs")
    if not isinstance(jobs, dict):
        return
    test_job = jobs.get("test")
    report.require(isinstance(test_job, dict), "CI workflow must declare a test job")
    if not isinstance(test_job, dict):
        return

    strategy = test_job.get("strategy")
    matrix = strategy.get("matrix") if isinstance(strategy, dict) else None
    include = matrix.get("include") if isinstance(matrix, dict) else None
    report.require(isinstance(include, list), "CI test job must use an include matrix")
    if isinstance(include, list):
        combinations = {
            (entry.get("os"), entry.get("python-version"))
            for entry in include
            if isinstance(entry, dict)
        }
        expected = {
            ("ubuntu-latest", "3.11"),
            ("windows-latest", "3.11"),
            ("ubuntu-latest", "3.14"),
        }
        report.require(
            combinations == expected and len(include) == len(expected),
            "CI test matrix must cover both platforms plus current Python without a full product",
        )

    steps = test_job.get("steps")
    report.require(isinstance(steps, list), "CI test job must declare steps")
    if isinstance(steps, list):
        run_commands = "\n".join(
            str(step.get("run", "")) for step in steps if isinstance(step, dict)
        )
        for command in (
            "python scripts/smoke_e2e.py",
            "python -m coverage run",
            "--fail-under=75",
        ):
            report.require(command in run_commands, f"CI test matrix does not run: {command}")


def git_tracked_paths(root: Path, report: Report) -> list[str] | None:
    """Return Git-index paths, or None when validating an unpacked release tree."""

    if not (root / ".git").exists():
        return None
    report.checks += 1
    try:
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--full-name", "-z", "--"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="surrogateescape",
        )
    except OSError as exc:
        report.errors.append(f"Cannot inspect Git tracked files: {exc}")
        return []
    if result.returncode != 0:
        detail = result.stderr.strip() or f"git ls-files exited {result.returncode}"
        report.errors.append(f"Cannot inspect Git tracked files: {detail}")
        return []
    return [item for item in result.stdout.split("\0") if item]


def is_python_cache_path(path: str) -> bool:
    relative = PurePosixPath(path.replace("\\", "/"))
    return "__pycache__" in relative.parts or relative.suffix.casefold() in {".pyc", ".pyo"}


def validate_ignored_outputs(root: Path, report: Report) -> None:
    gitignore = read_text(root / ".gitignore", root, report)
    if gitignore is not None:
        for fragment in ("__pycache__/", "*.py[cod]", ".coverage", "coverage.xml", ".ruff_cache/"):
            report.require(
                fragment in gitignore, f".gitignore is missing generated output: {fragment}"
            )

    attributes = read_text(root / ".gitattributes", root, report)
    if attributes is not None:
        report.require(
            "* text=auto eol=lf" in attributes,
            ".gitattributes must normalize repository text files to LF",
        )

    tracked = git_tracked_paths(root, report)
    if tracked is None:
        artifacts = sorted(
            display(path, root)
            for path in repository_glob(root, "*")
            if path.name == "__pycache__"
            or (path.is_file() and path.suffix.casefold() in {".pyc", ".pyo"})
        )
    else:
        artifacts = sorted(path for path in tracked if is_python_cache_path(path))
    preview = ", ".join(artifacts[:12])
    if len(artifacts) > 12:
        preview += f", and {len(artifacts) - 12} more"
    report.require(not artifacts, f"Tracked Python cache artifacts must not be released: {preview}")


def validate_public_content(root: Path, report: Report) -> None:
    placeholder_terms = (
        "TO" + "DO",
        "T" + "BD",
        "FIX" + "ME",
        "your-" + "name",
        "your-" + "org",
        "your-" + "repo",
        "example" + ".com",
    )
    placeholder_pattern = re.compile(
        "|".join(re.escape(term) for term in placeholder_terms), flags=re.IGNORECASE
    )
    windows_private_path = re.compile(
        r"(?i)(?<![A-Za-z0-9])(?:[A-Z]:[\\/](?:Users|Obsidian|Documents and Settings)[\\/][^\s`\"'<>]+)"
    )
    posix_private_path = re.compile(r"/(?:Users|home)/[A-Za-z0-9._-]+/")

    for path in iter_text_files(root):
        text = read_text(path, root, report)
        if text is None:
            continue
        placeholder = placeholder_pattern.search(text)
        report.require(
            placeholder is None,
            f"Placeholder leaked in {display(path, root)}: {placeholder.group(0) if placeholder else ''}",
        )
        private_path = windows_private_path.search(text) or posix_private_path.search(text)
        report.require(
            private_path is None,
            f"Private absolute path leaked in {display(path, root)}: "
            f"{private_path.group(0) if private_path else ''}",
        )


def validate_license(root: Path, report: Report) -> None:
    license_text = read_text(root / "LICENSE", root, report)
    if license_text is None:
        return
    report.require(license_text.startswith("MIT License"), "LICENSE must contain the MIT license")
    report.require("Copyright (c) 2026 chen" in license_text, "LICENSE owner is inconsistent")


def run(root: Path) -> Report:
    report = Report()
    validate_structure(root, report)
    documents = validate_structured_files(root, report)
    validate_skill_frontmatter(root, report)
    validate_plugin_manifest(documents.get(root / MANIFEST_RELATIVE), root, report)
    validate_marketplace(documents.get(root / MARKETPLACE_RELATIVE), root, report)
    validate_markdown_links(root, report)
    validate_skill_references(root, report)
    validate_version_and_docs(root, report)
    validate_ci_and_dependencies(root, report)
    validate_ignored_outputs(root, report)
    validate_public_content(root, report)
    validate_license(root, report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=PROJECT_ROOT,
        help="Repository root; defaults to the parent of this script directory",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if not root.is_dir():
        print(f"Release validation failed: repository root does not exist: {root}", file=sys.stderr)
        return 2

    report = run(root)
    if report.errors:
        print(f"Release validation failed with {len(report.errors)} error(s):")
        for error in report.errors:
            print(f"- {error}")
        print(f"Checks executed: {report.checks}")
        return 1

    print(f"Release validation passed: {report.checks} checks")
    print(f"Plugin: {PLUGIN_NAME} {RELEASE_VERSION}")
    print(f"Skill: {SKILL_NAME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
