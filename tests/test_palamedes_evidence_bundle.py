#!/usr/bin/env python3
import json
import copy
import tempfile
import unittest
from pathlib import Path

from palamedes_evidence_bundle import (
    MAX_TOTAL_BYTES,
    build_cognition_evidence_bundle,
    citation_allowlist,
    project_cognition_evidence,
)
from tests.test_palamedes_architecture_transfer import (
    collect_packet,
    valid_transfer,
)


def snapshot():
    return {
        "observation_id": "observation-aaaaaaaaaaaa",
        "snapshot_fingerprint": "a" * 64,
        "observed_at": "2026-08-12T00:00:00+00:00",
        "signals": {
            "observed_at": "2026-08-12T00:00:00+00:00",
            "documents": [],
            "git": {"head": "b" * 40, "branch": "main"},
            "change": {"reasons": []},
            "test": {"executed": False},
        },
    }


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def append_jsonl(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def eligible_opportunity(scout_id="opportunity-aaaaaaaaaaaa", title="Seasonal journey"):
    return {
        "opportunity_scout_id": scout_id,
        "created_at": "2026-08-12T00:00:00+00:00",
        "opportunities": [{
            "opportunity_id": "opportunity-1",
            "title": title,
            "observation": "Players repeat short matches.",
            "latent_need": "Progress should persist across sessions.",
            "current_gap": "There is no long-term progression.",
            "mechanism": "Optional seasonal progression across modes.",
            "behavior_change": "Players return across weeks.",
            "business_effect": "An optional paid track could create repeat revenue.",
            "failure_condition": "Return stays flat or play becomes compulsory.",
            "validation_probe": {"intervention": "Expose a free track."},
            "delivery_authority_granted": True,
        }],
        "critic": {
            "top_opportunity_ids": ["opportunity-1"],
            "assessments": [{
                "opportunity_id": "opportunity-1",
                "disposition": "validate",
                "insight_survives_name_removal": True,
                "second_order_accounted": True,
                "failure_basis_honest": True,
                "operational_burden_accounted": True,
            }],
        },
        "delivery_authority_granted": True,
    }


class CognitionEvidenceBundleTests(unittest.TestCase):
    def build(self, root, **kwargs):
        return build_cognition_evidence_bundle(
            state_root=Path(root),
            snapshot=snapshot(),
            user_request="Find the hidden product and business opportunity.",
            mode="product",
            **kwargs,
        )

    def test_empty_read_is_stable_and_does_not_create_state(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "not-yet-created"
            first = self.build(root)
            second = self.build(root)
            self.assertEqual(first["bundle_id"], second["bundle_id"])
            self.assertFalse(root.exists())
            self.assertFalse(first["delivery_authority_granted"])

    def test_latest_opportunity_is_semantic_and_mtime_independent(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            older = eligible_opportunity(
                "opportunity-ffffffffffff", "Old file-hash winner"
            )
            older["created_at"] = "2026-08-10T00:00:00+00:00"
            newer = eligible_opportunity(
                "opportunity-000000000000", "Current semantic opportunity"
            )
            write_json(
                root / "opportunities/records/opportunity-ffffffffffff.json", older
            )
            write_json(
                root / "opportunities/records/opportunity-000000000000.json", newer
            )
            first = self.build(root)
            (root / "opportunities/records/opportunity-ffffffffffff.json").touch()
            second = self.build(root)
            self.assertEqual(first["bundle_id"], second["bundle_id"])
            rows = first["exploration_frontier"]["opportunity_hypotheses"]
            self.assertEqual(rows[0]["payload"]["title"], "Current semantic opportunity")

    def test_status_filters_and_host_authority_override_stored_claims(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_json(
                root / "knowledge/claims/active.json",
                {
                    "knowledge_id": "knowledge-active",
                    "status": "active",
                    "claim_type": "interpretation",
                    "domain": "internal_product",
                    "claim": "Repeat play exists.",
                    "scope": "game",
                    "perspective": "player",
                    "source_ids": ["source-1"],
                    "confidence": 70,
                    "last_verified_at": "2026-08-12T00:00:00+00:00",
                    "delivery_authority_granted": True,
                },
            )
            write_json(
                root / "knowledge/claims/stale.json",
                {
                    "knowledge_id": "knowledge-stale",
                    "status": "superseded",
                    "claim": "Old claim",
                },
            )
            write_json(
                root / "opportunities/records/opportunity-a.json",
                eligible_opportunity(),
            )
            write_json(
                root / "inventions/records/invention-a.json",
                {
                    "product_invention_id": "invention-a",
                    "created_at": "2026-08-12T00:00:00+00:00",
                    "candidates": [
                        {"candidate_id": "keep", "thesis": "keep", "delivery_authority_granted": True},
                        {"candidate_id": "drop", "thesis": "drop"},
                    ],
                    "frontier": [
                        {"candidate_id": "keep", "disposition": "preserve"},
                        {"candidate_id": "drop", "disposition": "reject"},
                    ],
                },
            )
            bundle = self.build(root)
            self.assertEqual(len(bundle["knowledge"]), 1)
            self.assertEqual(
                bundle["knowledge"][0]["payload"]["knowledge_id"],
                "knowledge-active",
            )
            self.assertEqual(
                [
                    row["payload"]["candidate_id"]
                    for row in bundle["exploration_frontier"]["invention_candidates"]
                ],
                ["keep"],
            )
            encoded = json.dumps(bundle, ensure_ascii=False)
            self.assertNotIn('"delivery_authority_granted": true', encoded)

    def test_corrupt_lane_degrades_without_erasing_other_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "knowledge/claims/broken.json"
            path.parent.mkdir(parents=True)
            path.write_text("{broken", encoding="utf-8")
            write_json(
                root / "thoughts/thoughts/good.json",
                {
                    "thought_id": "thought-good",
                    "status": "incubating",
                    "kind": "possibility",
                    "content": "A repeat loop may support a seasonal journey.",
                    "strength": 0.8,
                    "last_revisited_at": "2026-08-12T00:00:00+00:00",
                },
            )
            bundle = self.build(root)
            self.assertEqual(bundle["status"], "degraded")
            self.assertEqual(
                len(bundle["exploration_frontier"]["thoughts"]), 1
            )
            self.assertEqual(
                bundle["selection_manifest"]["diagnostics"][0]["lane"],
                "knowledge",
            )

    def test_outcome_observation_and_interpretation_never_share_custody(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            append_jsonl(
                root / "missions/outcomes.jsonl",
                {
                    "outcome_id": "outcome-1",
                    "mission_contract_id": "mission-1",
                    "recorded_at": "2026-08-12T00:00:00+00:00",
                    "reported_outcome_status": "failure",
                    "outcome_type": "adverse_result",
                    "observation": "Operating burden exceeded the budget.",
                },
            )
            append_jsonl(
                root / "missions/outcome-interpretations.jsonl",
                {
                    "outcome_interpretation_id": "interpretation-1",
                    "outcome_id": "outcome-1",
                    "created_at": "2026-08-12T00:01:00+00:00",
                    "causal_signature": "content-cadence-overload",
                    "mechanism_summary": "Cadence grew faster than capacity.",
                    "confidence": 60,
                },
            )
            bundle = self.build(root)
            classes = {
                row["kind"]: row["epistemic_class"]
                for row in bundle["outcome_memory"]
            }
            self.assertEqual(
                classes["mission_outcome_observation"], "direct_observation"
            )
            self.assertEqual(
                classes["mission_outcome_interpretation"], "model_interpretation"
            )
            self.assertIn("outcome-1", citation_allowlist(bundle, "direct_failure"))

    def test_independent_inventor_cannot_see_prior_idea_names(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_json(
                root / "opportunities/records/opportunity-a.json",
                eligible_opportunity(title="SECRET_BATTLE_PASS_TEMPLATE"),
            )
            bundle = self.build(root)
            independent = json.dumps(
                project_cognition_evidence(bundle, "independent_inventor"),
                ensure_ascii=False,
            )
            transfer = json.dumps(
                project_cognition_evidence(bundle, "transfer_inventor"),
                ensure_ascii=False,
            )
            self.assertNotIn("SECRET_BATTLE_PASS_TEMPLATE", independent)
            self.assertIn("SECRET_BATTLE_PASS_TEMPLATE", transfer)

    def test_architecture_transfer_requires_source_target_differences_and_limit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            baseline = self.build(root)
            target_id = baseline["product_signals"][0]["item_id"]
            packet, _ = collect_packet(root)
            mapping = valid_transfer(
                [source["source_id"] for source in packet["sources"]]
            )
            mapping["target_evidence_ids"] = [target_id]
            bundle = self.build(
                root,
                architecture_packet=packet,
                transfer_mappings=[mapping],
            )
            self.assertEqual(
                len(bundle["cross_domain_transfer"]["transfer_mappings"]), 1
            )
            malformed = copy.deepcopy(mapping)
            malformed["transfer_limit"] = ""
            with self.assertRaisesRegex(ValueError, "transfer_limit"):
                self.build(
                    root,
                    architecture_packet=packet,
                    transfer_mappings=[malformed],
                )

            escalation = copy.deepcopy(mapping)
            escalation["source_outcome_is_target_forecast"] = "false"
            with self.assertRaisesRegex(ValueError, "exactly false"):
                self.build(
                    root,
                    architecture_packet=packet,
                    transfer_mappings=[escalation],
                )

            fabricated_target = copy.deepcopy(mapping)
            fabricated_target["target_evidence_ids"] = ["target-fabricated"]
            with self.assertRaisesRegex(ValueError, "unavailable target"):
                self.build(
                    root,
                    architecture_packet=packet,
                    transfer_mappings=[fabricated_target],
                )

    def test_new_eligible_evidence_changes_bundle_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = self.build(root)
            write_json(
                root / "opportunities/records/opportunity-a.json",
                eligible_opportunity(),
            )
            second = self.build(root)
            self.assertNotEqual(first["bundle_id"], second["bundle_id"])

    def test_lane_and_total_payload_are_bounded(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index in range(20):
                write_json(
                    root / f"thoughts/thoughts/thought-{index}.json",
                    {
                        "thought_id": f"thought-{index}",
                        "status": "incubating",
                        "kind": "possibility",
                        "content": "x" * 50_000,
                        "strength": index / 20,
                        "last_revisited_at": f"2026-08-12T00:{index:02d}:00+00:00",
                    },
                )
            opportunity_row = eligible_opportunity()
            opportunity_row["opportunities"][0]["validation_probe"] = {
                "intervention": "y" * 50_000,
                "nested": {"payload": "z" * 50_000},
            }
            write_json(
                root / "opportunities/records/opportunity-a.json",
                opportunity_row,
            )
            bundle = self.build(root)
            self.assertEqual(
                len(bundle["exploration_frontier"]["thoughts"]), 12
            )
            self.assertLessEqual(
                len(json.dumps(bundle, ensure_ascii=False).encode("utf-8")),
                MAX_TOTAL_BYTES,
            )


if __name__ == "__main__":
    unittest.main()
