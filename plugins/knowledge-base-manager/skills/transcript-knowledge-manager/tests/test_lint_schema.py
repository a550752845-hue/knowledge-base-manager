from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lint_knowledge_base import (
    Inventory,
    build_inventory,
    check_manifest,
    load_source_registry,
)


class LintSchemaTests(unittest.TestCase):
    def test_manifest_schema_is_enforced_by_doctor(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            metadata = root / "_meta"
            metadata.mkdir()
            (metadata / "knowledge-base.json").write_text(
                json.dumps(
                    {
                        "schema_version": 3,
                        "knowledge_base_id": "incomplete",
                        "scope": {"type": "general"},
                        "paths": {},
                        "source_roots": [],
                    }
                ),
                encoding="utf-8",
            )
            inv = build_inventory(root)
            check_manifest(inv)
            errors = [item for item in inv.findings if item.code == "invalid-manifest-schema"]
            self.assertTrue(errors)
            self.assertTrue(any("name" in item.detail for item in errors))
            self.assertTrue(any("role_paths" in item.detail for item in errors))
            self.assertTrue(any("freshness_policy" in item.detail for item in errors))

    def test_source_registry_rejects_wrong_types_and_duplicate_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            metadata = root / "_meta"
            metadata.mkdir()
            registry = metadata / "来源注册表.jsonl"
            registry.write_text(
                '{"source_id":["bad"],"title":"x","source_type":"text",'
                '"sensitivity":"public","status":"active"}\n'
                '{"source_id":"dup","source_id":"dup2","title":"x",'
                '"source_type":"text","sensitivity":"public","status":"active"}\n',
                encoding="utf-8",
            )
            inv = Inventory(root=root, notes=[])
            load_source_registry(inv)
            errors = [item for item in inv.findings if item.code == "invalid-source-registry"]
            self.assertEqual(2, len(errors))
            self.assertEqual({}, inv.source_registry)


if __name__ == "__main__":
    unittest.main()
