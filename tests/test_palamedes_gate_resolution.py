#!/usr/bin/env python3
import hashlib, json, tempfile, unittest
from pathlib import Path
from palamedes_gate_resolution import apply_gate_resolution, propose_gate_resolution


class PalamedesGateResolutionTests(unittest.TestCase):
    def fixture(self, root):
        missions = root / ".palamedes" / "missions"
        missions.mkdir(parents=True)
        gate = {
            "gate_id": "gate-aaaaaaaaaaaa",
            "outcome_id": "outcome-aaaaaaaaaaaa",
            "mission_contract_id": "mission-aaaaaaaaaaaa",
            "status": "open",
            "required_response": "Verify correction",
        }
        (missions / "outcome-gates.jsonl").write_text(json.dumps(gate) + "\n")
        evidence = []
        for name, kind in (("runtime.json", "runtime_audit"), ("test.py", "test")):
            path = root / name
            path.write_text(name)
            evidence.append(
                {
                    "kind": kind,
                    "claim": f"{kind} verifies correction",
                    "path": str(path),
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
        return missions, evidence

    def test_two_phase_resolution_is_evidence_bound_and_append_only(self):
        with tempfile.TemporaryDirectory() as d:
            missions, evidence = self.fixture(Path(d))
            proposal = propose_gate_resolution(
                missions,
                gate_id="gate-aaaaaaaaaaaa",
                evidence=evidence,
                coverage_assertions=["verified"],
                reviewer="host",
            )
            with self.assertRaisesRegex(ValueError, "exact fresh"):
                apply_gate_resolution(
                    missions,
                    gate_id="gate-aaaaaaaaaaaa",
                    evidence=evidence,
                    coverage_assertions=["verified"],
                    reviewer="host",
                    expected_proposal_fingerprint="wrong",
                )
            resolution = apply_gate_resolution(
                missions,
                gate_id="gate-aaaaaaaaaaaa",
                evidence=evidence,
                coverage_assertions=["verified"],
                reviewer="host",
                expected_proposal_fingerprint=proposal["proposal_fingerprint"],
            )
            rows = [
                json.loads(x)
                for x in (missions / "outcome-gates.jsonl").read_text().splitlines()
            ]
        self.assertEqual(rows[0]["status"], "open")
        self.assertEqual(rows[-1]["status"], "responded")
        self.assertEqual(rows[-1]["resolution_id"], resolution["resolution_id"])

    def test_stale_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            missions, evidence = self.fixture(Path(d))
            Path(evidence[0]["path"]).write_text("changed")
            with self.assertRaisesRegex(ValueError, "stale or mismatched"):
                propose_gate_resolution(
                    missions,
                    gate_id="gate-aaaaaaaaaaaa",
                    evidence=evidence,
                    coverage_assertions=["verified"],
                    reviewer="host",
                )


if __name__ == "__main__":
    unittest.main()
