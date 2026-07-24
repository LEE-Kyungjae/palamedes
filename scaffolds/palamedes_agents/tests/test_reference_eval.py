#!/usr/bin/env python3
import json
import sys
import unittest
from pathlib import Path


SCAFFOLD_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = SCAFFOLD_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from palamedes_agents.reference_eval import evaluate_reference_retrieval


class ReferenceEvalTests(unittest.TestCase):
    def test_checked_in_reference_retrieval_baseline_passes(self):
        dataset = json.loads((SCAFFOLD_ROOT / "evals" / "reference-retrieval.json").read_text(encoding="utf-8"))
        result = evaluate_reference_retrieval(dataset, dataset["corpus"])
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["metrics"]["case_count"], 2)
        self.assertEqual(result["metrics"]["mean_recall_at_k"], 1.0)
        self.assertEqual(result["metrics"]["gate_accuracy"], 1.0)

    def test_evaluation_reports_failed_threshold(self):
        dataset = {
            "thresholds": {"mean_recall_at_k": 1.0},
            "cases": [
                {
                    "query": "unrelated query",
                    "relevant_reference_ids": ["missing"],
                    "expect_sufficient": False,
                }
            ],
        }
        result = evaluate_reference_retrieval(dataset, [])
        self.assertFalse(result["ok"])
        self.assertEqual(result["metrics"]["mean_recall_at_k"], 0.0)


if __name__ == "__main__":
    unittest.main()
