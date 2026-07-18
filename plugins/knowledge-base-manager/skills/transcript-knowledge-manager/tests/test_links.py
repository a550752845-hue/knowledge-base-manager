from __future__ import annotations

import tempfile
import unittest
import os
import subprocess
from pathlib import Path

from lint_knowledge_base import build_inventory, check_links


class LinkTests(unittest.TestCase):
    def test_code_fence_links_are_ignored_and_aliases_resolve(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            target = root / "notes" / "target.md"
            target.parent.mkdir()
            target.write_text("---\naliases: [Target Alias]\n---\n# Target\n", encoding="utf-8")
            source = root / "source.md"
            source.write_text(
                "# Source\n\n[[Target Alias]]\n\n```markdown\n[[not-a-real-link]]\n```\n",
                encoding="utf-8",
            )
            inv = build_inventory(root)
            check_links(inv)
            self.assertEqual([], inv.findings)
            self.assertEqual(1, inv.links_inbound[target])

    def test_link_cannot_escape_root_or_crash_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "root"
            root.mkdir()
            outside = Path(temp) / "outside.md"
            outside.write_text("# Outside\n", encoding="utf-8")
            (root / "source.md").write_text("[[../outside]]\n", encoding="utf-8")
            inv = build_inventory(root)
            check_links(inv)
            self.assertTrue(any(item.code == "broken-wikilink" for item in inv.findings))

    def test_exact_path_wins_over_same_stem_elsewhere(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "a" / "target.md"
            second = root / "b" / "target.md"
            first.parent.mkdir()
            second.parent.mkdir()
            first.write_text("# First\n", encoding="utf-8")
            second.write_text("# Second\n", encoding="utf-8")
            (root / "source.md").write_text("[[a/target]]\n", encoding="utf-8")
            inv = build_inventory(root)
            check_links(inv)
            self.assertEqual([], inv.findings)
            self.assertEqual(1, inv.links_inbound[first])
            self.assertEqual(0, inv.links_inbound[second])

    def test_variable_inline_code_comments_and_attachment_are_handled(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "image.png").write_bytes(b"synthetic")
            (root / "source.md").write_text(
                "``[[not-a-link]]``\n%% [[also-not-a-link]] %%\n"
                "<!-- [[still-not-a-link]] -->\n![[image.png]]\n",
                encoding="utf-8",
            )
            inv = build_inventory(root)
            check_links(inv)
            self.assertEqual([], inv.findings)

    def test_fence_like_code_line_does_not_close_the_fence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "source.md").write_text(
                "```markdown\n```not-a-closing-fence\n[[not-a-link]]\n```\n",
                encoding="utf-8",
            )
            inv = build_inventory(root)
            check_links(inv)
            self.assertEqual([], inv.findings)

    def test_external_linked_directory_is_not_inventory_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "root"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            restricted = outside / "restricted.md"
            restricted.write_text("# Restricted\n", encoding="utf-8")
            linked = root / "linked"
            try:
                os.symlink(outside, linked, target_is_directory=True)
            except OSError:
                if os.name != "nt":
                    self.skipTest("Directory symlink is unavailable")
                result = subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(linked), str(outside)],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    self.skipTest("Directory junction is unavailable")

            inv = build_inventory(root)
            self.assertNotIn(restricted, inv.notes)
            self.assertTrue(any(item.code == "unsafe-filesystem-entry" for item in inv.findings))
