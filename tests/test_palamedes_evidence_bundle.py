#!/usr/bin/env python3
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from palamedes_evidence_bundle import (
    BUNDLE_VERSION,
    LEGACY_BUNDLE_VERSION,
    MAX_TOTAL_BYTES,
    build_cognition_evidence_bundle,
    citation_allowlist,
    mission_claim_ledger,
    project_cognition_evidence,
    project_mission_evidence,
    upgrade_cognition_evidence_bundle_v1,
)
from palamedes_architecture_transfer import validate_gitnexus_evidence_packet
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


def as_frozen_v1_bundle(bundle):
    """Re-seal a current fixture with the exact cognition-evidence v1 identity."""

    legacy = copy.deepcopy(bundle)
    legacy.pop("mission_claim_ledger", None)
    legacy["bundle_version"] = LEGACY_BUNDLE_VERSION
    all_items = []
    for field in ("product_signals", "outcome_memory", "knowledge", "unknowns"):
        all_items.extend(legacy[field])
    for rows in legacy["exploration_frontier"].values():
        all_items.extend(rows)
    all_items.extend(legacy["cross_domain_transfer"]["reference_patterns"])
    all_items.extend(legacy["cross_domain_transfer"]["transfer_mappings"])
    legacy["citation_allowlists"]["mission_source_ids"] = sorted(
        row["item_id"]
        for row in all_items
        if row.get("decision_authority") in {"mission_citable", "advisory"}
    )
    identity = {
        "bundle_version": legacy["bundle_version"],
        "request": legacy["request"],
        "workspace": legacy["workspace"],
        "authority_context": legacy["authority_context"],
        "product_signals": legacy["product_signals"],
        "outcome_memory": legacy["outcome_memory"],
        "knowledge": legacy["knowledge"],
        "unknowns": legacy["unknowns"],
        "exploration_frontier": legacy["exploration_frontier"],
        "cross_domain_transfer": legacy["cross_domain_transfer"],
        "citation_allowlists": legacy["citation_allowlists"],
        "selection_manifest": legacy["selection_manifest"],
        "delivery_authority_granted": False,
    }
    canonical = json.dumps(
        identity,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    legacy["bundle_id"] = "evidence-" + hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()[:16]
    return legacy


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

    def test_valid_v1_bundle_upgrades_without_mutation_and_rederives_claim_ledger(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_json(
                root / "opportunities/records/opportunity-a.json",
                eligible_opportunity(),
            )
            current = self.build(root)
            legacy = as_frozen_v1_bundle(current)
            frozen_copy = copy.deepcopy(legacy)

            upgraded = upgrade_cognition_evidence_bundle_v1(legacy)
            upgraded_again = upgrade_cognition_evidence_bundle_v1(legacy)

            self.assertEqual(legacy, frozen_copy)
            self.assertEqual(upgraded, upgraded_again)
            self.assertEqual(upgraded["bundle_version"], BUNDLE_VERSION)
            self.assertNotEqual(upgraded["bundle_id"], legacy["bundle_id"])
            ledger_ids = sorted(
                row["source_id"] for row in upgraded["mission_claim_ledger"]
            )
            self.assertEqual(
                upgraded["citation_allowlists"]["mission_source_ids"],
                ledger_ids,
            )
            # Advisory v1 citations are context only under the v2 custody model.
            self.assertLess(
                len(ledger_ids),
                len(legacy["citation_allowlists"]["mission_source_ids"]),
            )

    def test_v1_upgrade_rejects_tampering_before_migration(self):
        with tempfile.TemporaryDirectory() as temporary:
            legacy = as_frozen_v1_bundle(self.build(Path(temporary)))
            legacy["request"]["user_request"] = "tampered after the cycle froze"

            with self.assertRaisesRegex(ValueError, "fingerprint mismatch"):
                upgrade_cognition_evidence_bundle_v1(legacy)

    def test_v1_upgrade_excludes_unverified_legacy_transfer_mappings(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            baseline = self.build(root)
            target_id = baseline["product_signals"][0]["item_id"]
            packet, _ = collect_packet(root)
            mapping = valid_transfer(
                [source["source_id"] for source in packet["sources"]]
            )
            mapping["target_evidence_ids"] = [target_id]
            with patch(
                "palamedes_architecture_transfer.reverify_gitnexus_evidence_packet",
                side_effect=lambda value: validate_gitnexus_evidence_packet(value),
            ):
                current = self.build(
                    root,
                    architecture_packet=packet,
                    transfer_mappings=[mapping],
                )
            legacy = as_frozen_v1_bundle(current)
            legacy_payload = legacy["cross_domain_transfer"]["transfer_mappings"][0][
                "payload"
            ]
            legacy_payload.pop("transfer_contract_version", None)
            legacy_payload.pop("source_claim_support", None)
            legacy_payload.pop("source_support_verification", None)
            legacy_payload.pop("source_support_semantics_verified", None)
            legacy = as_frozen_v1_bundle(legacy)

            upgraded = upgrade_cognition_evidence_bundle_v1(legacy)

            self.assertEqual(
                upgraded["cross_domain_transfer"]["transfer_mappings"], []
            )
            self.assertEqual(
                upgraded["citation_allowlists"]["transfer_mapping_ids"], []
            )
            self.assertTrue(
                any(
                    row.get("reason")
                    == "legacy_unverified_transfer_mapping_excluded"
                    for row in upgraded["selection_manifest"]["diagnostics"]
                )
            )

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
            interpretation_id = bundle["knowledge"][0]["item_id"]
            self.assertEqual(
                bundle["knowledge"][0]["decision_authority"], "advisory"
            )
            self.assertNotIn(interpretation_id, citation_allowlist(bundle, "mission"))
            with self.assertRaisesRegex(ValueError, "non-citable"):
                project_mission_evidence(bundle, [interpretation_id])

    def test_candidate_wording_cannot_replace_generic_workspace_observation(self):
        with tempfile.TemporaryDirectory() as temporary:
            bundle = self.build(Path(temporary))
            workspace = next(
                row
                for row in bundle["product_signals"]
                if row["kind"] == "workspace_observation"
            )
            invented_candidate_claim = (
                "Customers demand a paid product and repeat revenue will increase."
            )

            projected = project_mission_evidence(
                bundle, [workspace["item_id"]]
            )

            self.assertEqual(len(projected), 1)
            self.assertNotIn(
                invented_candidate_claim,
                json.dumps(projected, ensure_ascii=False),
            )
            self.assertEqual(projected[0]["claim_payload"], workspace["payload"])
            self.assertEqual(
                projected[0]["epistemic_class"], "direct_observation"
            )
            self.assertFalse(
                projected[0]["custody"]["candidate_language_certified"]
            )

    def test_verified_source_claim_keeps_verbatim_claim_confidence_and_custody(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            exact_claim = "Returning players completed 37 percent more matches."
            write_json(
                root / "knowledge/claims/verified.json",
                {
                    "knowledge_id": "knowledge-verified",
                    "status": "active",
                    "claim_type": "fact",
                    "domain": "internal_product",
                    "claim": exact_claim,
                    "scope": "measured cohort",
                    "source_ids": ["cohort-report-17"],
                    "confidence": 82,
                    "last_verified_at": "2026-08-12T00:00:00+00:00",
                    "epistemic_profile": {"evidence_layer": "behavior"},
                },
            )
            bundle = self.build(root)
            source = bundle["knowledge"][0]

            ledger = mission_claim_ledger(bundle)
            entry = ledger[source["item_id"]]
            projected = project_mission_evidence(bundle, [source["item_id"]])

            self.assertEqual(entry["claim"], exact_claim)
            self.assertEqual(entry["claim_payload"]["claim"], exact_claim)
            self.assertEqual(entry["confidence"], 82)
            self.assertEqual(entry["epistemic_class"], "host_verified")
            self.assertEqual(entry["custody"]["owner"], "host")
            self.assertTrue(
                entry["custody"]["source_claim_preserved_verbatim"]
            )
            self.assertEqual(projected[0]["claim"], exact_claim)
            self.assertEqual(projected[0]["confidence"], 82)

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
            with patch(
                "palamedes_architecture_transfer.reverify_gitnexus_evidence_packet",
                side_effect=lambda value: validate_gitnexus_evidence_packet(value),
            ):
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
