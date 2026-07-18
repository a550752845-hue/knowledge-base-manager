from __future__ import annotations

import argparse
import json
import unittest
from pathlib import Path

import jsonschema

from init_knowledge_base import manifest_payload
from kb_common import normalized_value, parse_frontmatter
from lint_knowledge_base import ENUMS
from tests.test_lint_contracts import talk_track


REFERENCES = Path(__file__).resolve().parents[1] / "references"
EVAL_FIXTURES = Path(__file__).resolve().parents[1] / "evals" / "fixtures"


class SchemaFileTests(unittest.TestCase):
    def load(self, name: str) -> dict:
        return json.loads((REFERENCES / name).read_text(encoding="utf-8"))

    def test_linter_enums_match_asset_schema(self) -> None:
        schema = self.load("asset-frontmatter.schema.json")
        properties = schema["properties"]
        for name in (
            "knowledge_role",
            "truth_status",
            "preservation",
            "reuse_mode",
            "status",
            "scope_type",
            "confidence",
            "maturity",
            "evidence_strength",
            "time_sensitivity",
            "sensitivity",
            "tested_status",
            "promotion_status",
        ):
            self.assertEqual(ENUMS[name], set(properties[name]["enum"]), name)

    def test_complete_direct_use_asset_validates(self) -> None:
        schema = self.load("asset-frontmatter.schema.json")
        fields = normalized_value(parse_frontmatter(talk_track()))
        jsonschema.Draft202012Validator(schema).validate(fields)

    def test_generated_manifest_validates(self) -> None:
        schema = self.load("knowledge-base-manifest.schema.json")
        args = argparse.Namespace(
            kb_id="healthcare-growth",
            name="Healthcare Growth",
            scope_type="industry",
            industry=["healthcare"],
            responsibility=["growth"],
        )
        jsonschema.Draft202012Validator(schema).validate(manifest_payload(args))

    def test_all_eval_manifests_and_v3_assets_validate(self) -> None:
        manifest_validator = jsonschema.Draft202012Validator(
            self.load("knowledge-base-manifest.schema.json")
        )
        asset_validator = jsonschema.Draft202012Validator(
            self.load("asset-frontmatter.schema.json")
        )

        manifests = sorted(EVAL_FIXTURES.rglob("knowledge-base.json"))
        self.assertGreaterEqual(len(manifests), 8)
        for path in manifests:
            with self.subTest(manifest=path.relative_to(EVAL_FIXTURES).as_posix()):
                manifest_validator.validate(json.loads(path.read_text(encoding="utf-8")))

        assets = 0
        for path in sorted(EVAL_FIXTURES.rglob("*.md")):
            fields = parse_frontmatter(path.read_text(encoding="utf-8-sig"), str(path))
            if str(fields.get("schema_version", "")) != "3":
                continue
            assets += 1
            with self.subTest(asset=path.relative_to(EVAL_FIXTURES).as_posix()):
                asset_validator.validate(normalized_value(fields))
        self.assertGreaterEqual(assets, 9)

    def test_source_registry_template_row_validates(self) -> None:
        schema = self.load("source-registry-row.schema.json")
        row = {
            "source_id": "src-interview-001",
            "title": "Synthetic interview",
            "source_type": "transcript",
            "preferred_read_path": "10-sources/interview.md",
            "all_known_paths": ["10-sources/interview.md"],
            "representations": [],
            "versions": [],
            "sensitivity": "internal",
            "status": "superseded",
        }
        jsonschema.Draft202012Validator(schema).validate(row)
