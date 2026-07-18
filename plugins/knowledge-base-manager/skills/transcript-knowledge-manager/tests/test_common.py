from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from kb_common import (
    FrontmatterError,
    as_list,
    atomic_write_text,
    exclusive_write_text,
    load_json,
    parse_frontmatter,
    parse_iso_date,
    stable_json,
)


class FrontmatterTests(unittest.TestCase):
    def test_yaml_parser_preserves_structured_values(self) -> None:
        fields = parse_frontmatter(
            """---
title: "Value: with colon"
topics: [strategy, "customer success"]
source_anchors:
  - type: timestamp
    value: "00:10-00:30"
created: 2026-07-15
---
# Body
"""
        )
        self.assertEqual("Value: with colon", fields["title"])
        self.assertEqual(["strategy", "customer success"], fields["topics"])
        self.assertEqual("timestamp", fields["source_anchors"][0]["type"])
        self.assertEqual("2026-07-15", fields["created"].isoformat())

    def test_invalid_yaml_is_rejected(self) -> None:
        with self.assertRaises(FrontmatterError):
            parse_frontmatter("---\ntopics: [broken\n---\n")

    def test_duplicate_yaml_keys_are_rejected(self) -> None:
        with self.assertRaisesRegex(FrontmatterError, "duplicate key"):
            parse_frontmatter("---\nid: first\nid: second\n---\n", "duplicate.md")

    def test_load_json_rejects_duplicate_object_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "manifest.json"
            path.write_text('{"paths": {}, "paths": {}}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Duplicate JSON object key 'paths'"):
                load_json(path)

    def test_set_normalization_is_deterministic(self) -> None:
        self.assertEqual(["alpha", "beta"], as_list({"beta", "alpha"}))
        self.assertEqual('{"values":["alpha","beta"]}', stable_json({"values": {"beta", "alpha"}}))

    def test_atomic_write_replaces_complete_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "nested" / "file.txt"
            atomic_write_text(path, "first\n")
            atomic_write_text(path, "second\n")
            self.assertEqual("second\n", path.read_text(encoding="utf-8"))

    def test_exclusive_write_does_not_modify_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "file.txt"
            path.write_text("original\n", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                exclusive_write_text(path, "replacement\n")
            self.assertEqual("original\n", path.read_text(encoding="utf-8"))
            self.assertEqual([], list(path.parent.glob(f".{path.name}.*.tmp")))

    def test_exclusive_write_publishes_complete_new_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "nested" / "file.txt"
            exclusive_write_text(path, "complete payload\n")
            self.assertEqual("complete payload\n", path.read_text(encoding="utf-8"))
            self.assertEqual([], list(path.parent.glob(f".{path.name}.*.tmp")))

    def test_invalid_date_suffix_is_not_silently_accepted(self) -> None:
        self.assertIsNone(parse_iso_date("2026-07-15-not-a-date"))
