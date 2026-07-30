#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

from palamedes_product_alignment import ProductAlignmentStore


class ProductAlignmentEventTests(unittest.TestCase):
    def test_candidate_requires_approval_and_approval_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = ProductAlignmentStore(Path(tempdir) / "alignment")
            candidate = store.propose_candidate(
                candidate_type="purpose",
                payload={
                    "purpose_id": "purpose-online",
                    "statement": "Games use authoritative online rooms.",
                    "strength": "product_invariant",
                },
                source_ids=["brief-1"],
                surface_key="game:yut",
            )
            self.assertEqual(store.active_context()["purposes"], [])
            first = store.approve_candidate(candidate["candidate_id"], approver="owner")
            second = store.approve_candidate(
                candidate["candidate_id"], approver="owner"
            )
            context = store.active_context()
        self.assertFalse(first["idempotent"])
        self.assertTrue(second["idempotent"])
        self.assertEqual(len(context["purposes"]), 1)
        self.assertIn("game:yut", context["surfaces"])

    def test_same_identity_merges_sources_and_preserves_statement_variants(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = ProductAlignmentStore(Path(tempdir) / "alignment")
            store.record_purpose(
                purpose_id="purpose-social",
                statement="People return to play together.",
                source_ids=["brief-1"],
                surface_key="service-core",
            )
            store.record_purpose(
                purpose_id="purpose-social",
                statement="People discover, play, remember, and return together.",
                source_ids=["playtest-1"],
                surface_key="service-core",
            )
            purpose = store.active_context()["purposes"][0]
            events = store.events()
        self.assertEqual(purpose["statement"], "People return to play together.")
        self.assertEqual(set(purpose["source_ids"]), {"brief-1", "playtest-1"})
        self.assertIn(
            "People discover, play, remember, and return together.",
            purpose["statement_variants"],
        )
        self.assertEqual(len(events), 2)

    def test_surface_stages_remain_independent(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = ProductAlignmentStore(Path(tempdir) / "alignment")
            store.set_product_stage(
                stage="alpha",
                required_journey_ids=["journey-yut"],
                evidence_ids=["evidence-yut"],
                surface_key="game:yut",
            )
            store.set_product_stage(
                stage="prototype",
                required_journey_ids=["journey-night"],
                evidence_ids=["evidence-night"],
                surface_key="game:night-office",
            )
            context = store.active_context()
        self.assertEqual(context["surface_stages"]["game:yut"]["stage"], "alpha")
        self.assertEqual(
            context["surface_stages"]["game:night-office"]["stage"], "prototype"
        )

    def test_projection_is_rebuilt_from_events_when_state_is_missing_or_stale(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = ProductAlignmentStore(Path(tempdir) / "alignment")
            candidate = store.propose_candidate(
                candidate_type="capability",
                payload={
                    "capability_id": "cap-resume",
                    "statement": "Resume one failed role.",
                },
                source_ids=["test-resume"],
                surface_key="service-core",
            )
            store.approve_candidate(candidate["candidate_id"], approver="owner")
            store.state_path.write_text('{"capabilities": []}')
            rebuilt = store.active_context()
        self.assertEqual(rebuilt["capabilities"][0]["capability_id"], "cap-resume")


if __name__ == "__main__":
    unittest.main()
