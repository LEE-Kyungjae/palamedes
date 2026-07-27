#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

from palamedes_observatory import build_observatory, render_cli, render_web_shell


class PalamedesObservatoryTests(unittest.TestCase):
    def test_projection_combines_lineage_without_mutating_sources(self):
        with tempfile.TemporaryDirectory() as tempdir:
            state = Path(tempdir) / ".palamedes"
            (state / "visions" / "records").mkdir(parents=True)
            (state / "missions" / "cognition").mkdir(parents=True)
            (state / "inventions" / "records").mkdir(parents=True)
            (state / "pursuits" / "records").mkdir(parents=True)
            (state / "visions" / "records" / "vision-genesis-aaaaaaaaaaaa.json").write_text(
                json.dumps({
                    "vision_genesis_id": "vision-genesis-aaaaaaaaaaaa",
                    "created_at": "2026-07-27T01:00:00Z",
                    "status": "selected",
                    "judgment": {"decision": "select", "vision_brief": "A durable world"},
                }), encoding="utf-8"
            )
            (state / "missions" / "mission-bbbbbbbbbbbb.json").write_text(
                json.dumps({
                    "mission_id": "mission-bbbbbbbbbbbb",
                    "approved_at": "2026-07-27T02:00:00Z",
                    "status": "approved",
                    "mission": "Test one consequence",
                    "vision_genesis_id": "vision-genesis-aaaaaaaaaaaa",
                }), encoding="utf-8"
            )
            (state / "inventions" / "records" / "invention-dddddddddddd.json").write_text(
                json.dumps({
                    "product_invention_id": "invention-dddddddddddd",
                    "created_at": "2026-07-27T01:30:00Z",
                    "status": "probe",
                    "selected_candidate_id": "world-3",
                    "candidates": [{"candidate_id": "world-3"}],
                    "provenance": {"origin": "palamedes", "palamedes_contribution": "originated"},
                    "delivery_authority_granted": False,
                }), encoding="utf-8"
            )
            (state / "pursuits" / "records" / "pursuit-eeeeeeeeeeee.json").write_text(
                json.dumps({
                    "pursuit_id": "pursuit-eeeeeeeeeeee",
                    "created_at": "2026-07-27T01:45:00Z",
                    "status": "ready",
                    "objective": "Investigate an unknown and author a report",
                    "epistemic_routing": {"task_types": ["discover", "author"]},
                    "execution_started": False,
                    "external_action_authority_granted": False,
                    "publication_authority_granted": False,
                    "financial_action_authority_granted": False,
                }), encoding="utf-8"
            )
            gate_path = state / "missions" / "outcome-gates.jsonl"
            gate_path.write_text("\n".join([
                json.dumps({"gate_id": "gate-cccccccccccc", "opened_at": "2026-07-27T03:00:00Z", "status": "open", "required_response": "Human evidence"}),
                json.dumps({"gate_id": "gate-cccccccccccc", "updated_at": "2026-07-27T04:00:00Z", "status": "resolved", "required_response": "Human evidence"}),
            ]) + "\n", encoding="utf-8")
            snapshot = build_observatory(state)

        self.assertTrue(snapshot["read_only"])
        self.assertEqual(snapshot["summary"]["visions"], 1)
        self.assertEqual(snapshot["summary"]["missions"], 1)
        self.assertEqual(snapshot["summary"]["inventions"], 1)
        self.assertEqual(snapshot["summary"]["pursuits"], 1)
        invention = next(event for event in snapshot["events"] if event["kind"] == "invention")
        self.assertEqual(invention["details"]["provenance"]["origin"], "palamedes")
        self.assertFalse(invention["details"]["delivery_authority_granted"])
        pursuit = next(event for event in snapshot["events"] if event["kind"] == "pursuit")
        self.assertFalse(pursuit["details"]["authority"]["publication"])
        self.assertEqual(snapshot["summary"]["open_gates"], 0)
        self.assertEqual(snapshot["events"][0]["id"], "gate-cccccccccccc")
        self.assertIn("Palamedes Observatory", render_cli(snapshot))

    def test_web_shell_is_read_only_and_fetches_projection(self):
        document = render_web_shell()
        self.assertIn("Palamedes Observatory", document)
        self.assertIn("fetch('/observatory?limit=300'", document)
        self.assertNotIn("method:'POST'", document)


if __name__ == "__main__":
    unittest.main()
