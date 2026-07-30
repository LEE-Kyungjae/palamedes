#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

from palamedes_lifecycle import (
    LifecycleStore,
    audit_lifecycle_events,
    reconcile_lifecycle,
)


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


class PalamedesLifecycleTests(unittest.TestCase):
    def fixture(self, root):
        missions = root / ".palamedes" / "missions"
        write_json(
            missions / "mission-aaaaaaaaaaaa.json",
            {"mission_id": "mission-aaaaaaaaaaaa", "surface_key": "game:yut"},
        )
        write_json(
            missions / "handoffs" / "handoff-aaaaaaaaaaaa.json",
            {
                "handoff_id": "handoff-aaaaaaaaaaaa",
                "mission_contract_id": "mission-aaaaaaaaaaaa",
                "status": "awaiting_planner",
            },
        )
        with (missions / "outcomes.jsonl").open("w", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "outcome_id": "outcome-bbbbbbbbbbbb",
                        "mission_contract_id": "mission-aaaaaaaaaaaa",
                        "status": "mixed",
                    }
                )
                + "\n"
            )
        return missions

    def test_dry_run_never_mutates_and_proposes_projection_event(self):
        with tempfile.TemporaryDirectory() as tempdir:
            missions = self.fixture(Path(tempdir))
            report = reconcile_lifecycle(missions)
            repeated = reconcile_lifecycle(missions)
            self.assertFalse((missions / "lifecycle-events.jsonl").exists())
        self.assertEqual(report["mode"], "dry_run")
        self.assertEqual(report["summary"]["proposals"], 1)
        self.assertEqual(report["items"][0]["projected_state"], "outcome_recorded")
        self.assertEqual(
            report["summary"]["by_projected_state"], {"outcome_recorded": 1}
        )
        self.assertEqual(report["report_fingerprint"], repeated["report_fingerprint"])
        self.assertEqual(report["proposals"][0]["scope_keys"], ["surface:game:yut"])

    def test_apply_is_idempotent_and_keeps_handoff_immutable(self):
        with tempfile.TemporaryDirectory() as tempdir:
            missions = self.fixture(Path(tempdir))
            handoff_path = missions / "handoffs" / "handoff-aaaaaaaaaaaa.json"
            before = handoff_path.read_bytes()
            dry_run = reconcile_lifecycle(missions)
            first = reconcile_lifecycle(
                missions,
                apply=True,
                expected_proposal_fingerprint=dry_run["proposal_fingerprint"],
            )
            second_dry_run = reconcile_lifecycle(missions)
            second = reconcile_lifecycle(
                missions,
                apply=True,
                expected_proposal_fingerprint=second_dry_run["proposal_fingerprint"],
            )
            events = LifecycleStore(missions).events()
            after = handoff_path.read_bytes()
        self.assertEqual(first["summary"]["applied"], 1)
        self.assertEqual(second["summary"]["applied"], 0)
        self.assertEqual(len(events), 1)
        self.assertEqual(before, after)

    def test_open_gate_projects_follow_up_and_missing_contract_fails_closed(self):
        with tempfile.TemporaryDirectory() as tempdir:
            missions = self.fixture(Path(tempdir))
            with (missions / "outcome-gates.jsonl").open(
                "w", encoding="utf-8"
            ) as handle:
                handle.write(
                    json.dumps(
                        {
                            "gate_id": "gate-bbbbbbbbbbbb",
                            "outcome_id": "outcome-bbbbbbbbbbbb",
                            "mission_contract_id": "mission-aaaaaaaaaaaa",
                            "status": "open",
                        }
                    )
                    + "\n"
                )
            report = reconcile_lifecycle(missions)
            (missions / "mission-aaaaaaaaaaaa.json").unlink()
            conflict_dry_run = reconcile_lifecycle(missions)
            conflicted = reconcile_lifecycle(
                missions,
                apply=True,
                expected_proposal_fingerprint=conflict_dry_run["proposal_fingerprint"],
            )
        self.assertEqual(report["proposals"][0]["state"], "follow_up_required")
        self.assertEqual(conflicted["summary"]["conflicts"], 1)
        self.assertEqual(conflicted["summary"]["applied"], 0)

    def test_apply_requires_exact_fresh_dry_run_fingerprint(self):
        with tempfile.TemporaryDirectory() as tempdir:
            missions = self.fixture(Path(tempdir))
            with self.assertRaisesRegex(ValueError, "exact proposal fingerprint"):
                reconcile_lifecycle(missions, apply=True)
            with self.assertRaisesRegex(ValueError, "exact proposal fingerprint"):
                reconcile_lifecycle(
                    missions,
                    apply=True,
                    expected_proposal_fingerprint="stale-or-invented",
                )
            self.assertFalse((missions / "lifecycle-events.jsonl").exists())

    def test_semantic_audit_replays_supported_event_without_mutation(self):
        with tempfile.TemporaryDirectory() as tempdir:
            missions = self.fixture(Path(tempdir))
            dry_run = reconcile_lifecycle(missions)
            reconcile_lifecycle(
                missions,
                apply=True,
                expected_proposal_fingerprint=dry_run["proposal_fingerprint"],
            )
            before = (missions / "lifecycle-events.jsonl").read_bytes()
            audit = audit_lifecycle_events(missions)
            after = (missions / "lifecycle-events.jsonl").read_bytes()
        self.assertEqual(audit["summary"]["supported"], 1)
        self.assertEqual(audit["summary"]["unsupported"], 0)
        self.assertEqual(audit["correction_proposals"], [])
        self.assertEqual(before, after)

    def test_semantic_audit_proposes_append_only_correction_for_bad_state(self):
        with tempfile.TemporaryDirectory() as tempdir:
            missions = self.fixture(Path(tempdir))
            dry_run = reconcile_lifecycle(missions)
            reconcile_lifecycle(
                missions,
                apply=True,
                expected_proposal_fingerprint=dry_run["proposal_fingerprint"],
            )
            path = missions / "lifecycle-events.jsonl"
            event = json.loads(path.read_text(encoding="utf-8"))
            event["state"] = "follow_up_required"
            path.write_text(json.dumps(event) + "\n", encoding="utf-8")
            audit = audit_lifecycle_events(missions)
        self.assertEqual(audit["summary"]["unsupported"], 1)
        self.assertEqual(audit["summary"]["correction_proposals"], 1)
        self.assertEqual(
            audit["correction_proposals"][0]["correction_of_event_ids"],
            [event["event_id"]],
        )


if __name__ == "__main__":
    unittest.main()
