#!/usr/bin/env python3
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCAFFOLD_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = SCAFFOLD_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from palamedes_agents.strategy_benchmark import prepare_blind_packet, score_reviews, validate_dataset


class StrategyBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.dataset = json.loads((SCAFFOLD_ROOT / "evals" / "agent-cycle-cases.json").read_text(encoding="utf-8"))

    def test_dataset_is_valid(self):
        self.assertEqual(validate_dataset(self.dataset), [])

    def test_prepare_packet_hides_system_identity_and_key_reveals_it(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            baseline_dir = root / "baseline"
            candidate_dir = root / "candidate"
            baseline_dir.mkdir()
            candidate_dir.mkdir()
            for case in self.dataset["cases"]:
                (baseline_dir / f"{case['id']}.json").write_text('{"answer":"baseline"}', encoding="utf-8")
                (candidate_dir / f"{case['id']}.json").write_text('{"answer":"candidate"}', encoding="utf-8")

            packet, key = prepare_blind_packet(
                self.dataset,
                baseline_dir=baseline_dir,
                candidate_dir=candidate_dir,
                seed="secret-seed",
            )

            self.assertNotIn("labels", packet["cases"][0])
            self.assertEqual(set(packet["cases"][0]["reports"]), {"A", "B"})
            self.assertIn("palamedes", json.dumps(key).lower())
            self.assertEqual(len(packet["cases"]), 3)

    def test_score_reviews_applies_success_gate(self):
        packet = {
            "rubric": self.dataset["rubric"],
            "cases": [{"case_id": case["id"]} for case in self.dataset["cases"]],
        }
        key = {
            "success_gate": self.dataset["success_gate"],
            "cases": [
                {"case_id": case["id"], "labels": {"A": "baseline", "B": "palamedes"}}
                for case in self.dataset["cases"]
            ],
        }
        high = {name: 5 for name in self.dataset["rubric"]}
        low = {name: 2 for name in self.dataset["rubric"]}
        reviews = [
            {
                "case_id": case["id"],
                "reviewer": f"reviewer-{index}",
                "scores": {"A": low, "B": high},
                "attributable_decision": index == 0,
                "decision_note": "Changed positioning." if index == 0 else "",
            }
            for index, case in enumerate(self.dataset["cases"])
        ]

        result = score_reviews(packet, key, reviews)

        self.assertTrue(result["ok"])
        self.assertEqual(result["palamedes_wins"], 3)
        self.assertEqual(result["attributable_decisions"], 1)


if __name__ == "__main__":
    unittest.main()
