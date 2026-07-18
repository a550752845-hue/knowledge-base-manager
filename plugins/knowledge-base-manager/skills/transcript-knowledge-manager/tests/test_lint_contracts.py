from __future__ import annotations

import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from kb_common import parse_frontmatter
from lint_knowledge_base import Inventory, check_v3_contract


def talk_track(**replacements: str | None) -> str:
    today = date.today().isoformat()
    values: dict[str, str] = {
        "id": "talk-001",
        "role": "talk-track",
        "truth": "generated",
        "preservation": "derived",
        "reuse": "direct-use",
        "status": "approved",
        "audience": "prospect",
        "last_verified": today,
        "promotion": "approved",
        "tested": "reviewed",
    }
    for key, value in replacements.items():
        if value is None:
            values.pop(key, None)
        else:
            values[key] = value
    optional = {
        "audience": "audience: {audience}\n",
        "last_verified": "last_verified: {last_verified}\n",
        "promotion": "promotion_status: {promotion}\n",
        "tested": "tested_status: {tested}\n",
    }
    extras = "".join(
        template.format(**values) for key, template in optional.items() if key in values
    )
    return f"""---
schema_version: 3
id: {values["id"]}
type: {values["role"]}
knowledge_role: {values["role"]}
truth_status: {values["truth"]}
preservation: {values["preservation"]}
reuse_mode: {values["reuse"]}
status: {values["status"]}
scope_type: responsibility
primary_domain: sales
domains: [sales]
industries: []
responsibilities: [sales]
topics: [conversion]
source_ids: []
source_anchors: []
provenance: conversation:test
confidence: medium
maturity: candidate
time_sensitivity: medium
sensitivity: internal
created: {date.today().isoformat()}
updated: {date.today().isoformat()}
scenario: discovery-call
goal: clarify-next-step
variables: [product]
boundary: no-guarantees
compliance_risk: reviewed
rights_or_permission: internal-approved
{extras}---
# Test
"""


class ContractTests(unittest.TestCase):
    def run_contract(self, text: str, source_registry: dict | None = None) -> Inventory:
        root = Path(tempfile.mkdtemp())
        note = root / "40-可执行资产" / "test.md"
        note.parent.mkdir(parents=True)
        note.write_text(text, encoding="utf-8")
        fields = parse_frontmatter(text)
        inv = Inventory(root=root, notes=[note], fields_by_note={note: fields})
        inv.source_registry = source_registry or {}
        check_v3_contract(inv, note, fields, {})
        return inv

    def test_direct_use_complete(self) -> None:
        self.assertEqual([], self.run_contract(talk_track()).findings)

    def test_direct_use_missing_context(self) -> None:
        inv = self.run_contract(talk_track(audience=None))
        self.assertTrue(any(item.code == "incomplete-direct-use" for item in inv.findings))

    def test_direct_use_may_explicitly_have_no_variables(self) -> None:
        text = talk_track().replace("variables: [product]", "variables: []")
        inv = self.run_contract(text)
        self.assertFalse(any(item.code == "incomplete-direct-use" for item in inv.findings))

    def test_generated_asset_requires_promotion(self) -> None:
        inv = self.run_contract(talk_track(promotion=None))
        self.assertTrue(any(item.code == "unreviewed-generated-knowledge" for item in inv.findings))

    def test_stale_direct_use_is_an_error(self) -> None:
        old = (date.today() - timedelta(days=365)).isoformat()
        inv = self.run_contract(talk_track(last_verified=old))
        self.assertTrue(
            any(item.code == "stale-asset" and item.severity == "error" for item in inv.findings)
        )

    def test_logic_map_cannot_be_direct_use(self) -> None:
        inv = self.run_contract(
            talk_track(
                role="logic-map",
                truth="source-claim",
                preservation="derived",
                reuse="direct-use",
                promotion=None,
            )
        )
        self.assertTrue(any(item.code == "role-contract-violation" for item in inv.findings))

    def test_verified_fact_requires_verification_record(self) -> None:
        text = talk_track(
            role="fact",
            truth="verified-fact",
            preservation="normalized",
            reuse="reference-only",
            promotion=None,
        )
        inv = self.run_contract(text)
        self.assertTrue(any(item.code == "unverified-fact" for item in inv.findings))

    def test_exact_evidence_requires_anchor(self) -> None:
        text = talk_track(
            role="evidence",
            truth="source-record",
            preservation="exact",
            reuse="quote-only",
            promotion=None,
        )
        inv = self.run_contract(text)
        self.assertTrue(any(item.code == "unanchored-exact-content" for item in inv.findings))

    def test_sensitivity_downgrade_is_visible(self) -> None:
        text = talk_track(reuse="adapt-required", status="active")
        text = text.replace("source_ids: []", "source_ids: [src-private]")
        inv = self.run_contract(text, {"src-private": {"sensitivity": "private"}})
        self.assertTrue(any(item.code == "sensitivity-downgrade" for item in inv.findings))

    def test_single_source_id_inherits_sensitivity(self) -> None:
        text = talk_track(reuse="adapt-required", status="active")
        text = text.replace("source_ids: []", "source_id: src-private\nsource_ids: []")
        inv = self.run_contract(text, {"src-private": {"sensitivity": "private"}})
        self.assertTrue(
            any(
                item.code == "sensitivity-downgrade" and item.severity == "error"
                for item in inv.findings
            )
        )

    def test_incomplete_privacy_approval_does_not_bypass_inheritance(self) -> None:
        text = talk_track(reuse="adapt-required", status="active")
        text = text.replace("source_ids: []", "source_id: src-private\nsource_ids: []")
        text = text.replace(
            "sensitivity: internal",
            "sensitivity: public\nanonymization_status: approved",
        )
        inv = self.run_contract(text, {"src-private": {"sensitivity": "private"}})
        self.assertTrue(any(item.code == "invalid-privacy-approval" for item in inv.findings))
        self.assertTrue(any(item.code == "sensitivity-downgrade" for item in inv.findings))

    def test_complete_privacy_approval_allows_recorded_downgrade(self) -> None:
        text = talk_track(reuse="adapt-required", status="active")
        text = text.replace("source_ids: []", "source_id: src-private\nsource_ids: []")
        text = text.replace(
            "sensitivity: internal",
            "\n".join(
                (
                    "sensitivity: public",
                    "anonymization_status: approved",
                    "privacy_reviewed_by: privacy-owner",
                    "privacy_review_reason: identifiers-removed",
                    f"privacy_reviewed_at: {date.today().isoformat()}",
                )
            ),
        )
        inv = self.run_contract(text, {"src-private": {"sensitivity": "private"}})
        self.assertFalse(any(item.code == "sensitivity-downgrade" for item in inv.findings))
        self.assertFalse(any(item.code == "invalid-privacy-approval" for item in inv.findings))

    def test_authoritative_schema_rejects_missing_version_and_non_scalar_id(self) -> None:
        text = (
            talk_track()
            .replace("schema_version: 3\n", "")
            .replace("id: talk-001", "id: [talk-001]")
        )
        inv = self.run_contract(text)
        schema_errors = [item for item in inv.findings if item.code == "invalid-asset-schema"]
        self.assertGreaterEqual(len(schema_errors), 2)

    def test_duplicate_asset_id(self) -> None:
        text = talk_track()
        root = Path(tempfile.mkdtemp())
        note = root / "test.md"
        fields = parse_frontmatter(text)
        inv = Inventory(root=root, notes=[note], fields_by_note={note: fields})
        check_v3_contract(inv, note, fields, {"talk-001": "other.md"})
        self.assertTrue(any(item.code == "duplicate-asset-id" for item in inv.findings))

    def test_empty_machine_registry_still_flags_unknown_source(self) -> None:
        text = talk_track(reuse="adapt-required", status="active").replace(
            "source_ids: []", "source_ids: [src-missing]"
        )
        root = Path(tempfile.mkdtemp())
        note = root / "test.md"
        fields = parse_frontmatter(text)
        inv = Inventory(
            root=root, notes=[note], fields_by_note={note: fields}, source_registry_loaded=True
        )
        check_v3_contract(inv, note, fields, {})
        self.assertTrue(any(item.code == "unknown-source-id" for item in inv.findings))
