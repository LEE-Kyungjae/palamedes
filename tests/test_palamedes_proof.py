#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import palamedes_proof


def portfolio(root: Path):
    repositories = []
    for index in range(3):
        repository = root / f"repo-{index}"
        repository.mkdir()
        (repository / "README.md").write_text(
            f"# Project {index}\n\nDecision evidence.\n", encoding="utf-8"
        )
        repositories.append(repository)
    return {
        "proof_portfolio_version": "palamedes-proof-portfolio/1",
        "portfolio_id": "test",
        "generation_protocol": {
            "same_model_required": True,
            "same_information_packet_required": True,
            "compute_is_not_equal": True,
            "compute_tradeoff_must_be_reported": True,
            "maximum_artifact_bytes": 2000,
        },
        "rubric": {
            "problem_framing": {"weight": 20},
            "non_genericity": {"weight": 20},
            "evidence_use": {"weight": 20},
            "falsifiability": {"weight": 20},
            "decision_usefulness": {"weight": 20},
        },
        "success_gate": {
            "minimum_cases": 3,
            "minimum_blinded_reviews_per_case": 1,
            "palamedes_preferred_cases": 2,
            "minimum_attributable_outcomes": 1,
            "minimum_labor_retirement_cases": 1,
        },
        "cases": [
            {
                "case_id": f"case-{index}",
                "repository": str(repository),
                "question": "What next?",
                "required_decision": "Choose.",
                "artifacts": ["README.md"],
            }
            for index, repository in enumerate(repositories)
        ],
    }


def mission(name: str):
    return {
        "situation": "A decision is pending.",
        "interpretation": "Evidence is missing.",
        "mission": name,
        "rationale": "It reduces uncertainty.",
        "beneficiary": "The owner.",
        "success_signal": "A decision changes.",
        "falsifiers": ["No decision changes."],
        "non_goals": ["Do not expand scope."],
        "next_probe": "Run a bounded comparison.",
        "consequential_choice": "sequence: proof before expansion",
    }


class PalamedesProofTests(unittest.TestCase):
    def test_prepare_freezes_three_real_information_packets(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            result = palamedes_proof.prepare_run(
                portfolio(root), run_root=root / "runs", run_id="proof-test"
            )
            run = Path(result["run_path"])

            packets = sorted(run.glob("cases/*/information.json"))

        self.assertEqual(len(packets), 3)
        self.assertEqual(result["manifest"]["claim_status"], "unproven")
        self.assertTrue(
            all(item["information_fingerprint"] for item in result["manifest"]["frozen_cases"])
        )

    def test_freeze_distributes_budget_across_all_declared_artifacts(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            repository = root / "repo"
            repository.mkdir()
            for name in ("README.md", "DESIGN.md", "ARCHITECTURE.md"):
                (repository / name).write_text(
                    name + "\n" + ("evidence\n" * 2000), encoding="utf-8"
                )
            case = {
                "case_id": "balanced",
                "repository": str(repository),
                "question": "What next?",
                "required_decision": "Choose.",
                "artifacts": ["README.md", "DESIGN.md", "ARCHITECTURE.md"],
            }

            packet = palamedes_proof.freeze_case(
                case, maximum_artifact_bytes=3000
            )

        self.assertEqual(packet["declared_artifact_count"], 3)
        self.assertEqual(packet["represented_declared_artifact_count"], 3)
        self.assertEqual(
            {item["declared_path"] for item in packet["artifacts"]},
            {"README.md", "DESIGN.md", "ARCHITECTURE.md"},
        )

    def test_blinding_hides_condition_and_score_requires_outcome(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            prepared = palamedes_proof.prepare_run(
                portfolio(root), run_root=root / "runs", run_id="proof-test"
            )
            run = Path(prepared["run_path"])
            for item in prepared["manifest"]["frozen_cases"]:
                case_root = run / "cases" / item["case_id"]
                for condition in ("baseline", "palamedes"):
                    record = {
                        "condition": condition,
                        "mission": mission(condition),
                        "usage": {
                            "call_count": 1 if condition == "baseline" else 4,
                            "token_usage": {
                                "input_tokens": (
                                    100 if condition == "baseline" else 425
                                ),
                                "output_tokens": 10,
                                "reasoning_output_tokens": 2,
                            },
                        },
                    }
                    palamedes_proof.write_object(
                        case_root / f"{condition}.json", record
                    )
            result = palamedes_proof.prepare_blind_packet(run, seed="secret")
            packet = result["packet"]
            key = palamedes_proof.load_object(
                run / "private" / "answer-key.json"
            )
            reviews = []
            for case in packet["cases"]:
                labels = next(
                    item["labels"]
                    for item in key["cases"]
                    if item["case_id"] == case["case_id"]
                )
                preferred = next(
                    label for label, system in labels.items() if system == "palamedes"
                )
                reviews.append(
                    {
                        "case_id": case["case_id"],
                        "reviewer_id": "blind-reviewer",
                        "review": {
                            "scores": {
                                "A": {
                                    dimension: 5 if preferred == "A" else 2
                                    for dimension in packet["rubric"]
                                },
                                "B": {
                                    dimension: 5 if preferred == "B" else 2
                                    for dimension in packet["rubric"]
                                },
                            },
                            "preferred": preferred,
                            "rationale": "More decision useful.",
                            "decision_difference": "Changes sequencing.",
                            "confidence": 80,
                        },
                        "usage": {},
                    }
                )
            palamedes_proof.write_object(
                run / "reviews" / "blind-reviewer.json",
                {
                    "reviewer_id": "blind-reviewer",
                    "reviews": reviews,
                },
            )

            score = palamedes_proof.score_run(run)

        for case in packet["cases"]:
            self.assertEqual(set(case["missions"]), {"A", "B"})
            self.assertNotIn("condition", case)
            self.assertNotIn("labels", case)
        self.assertTrue(score["mission_quality_gate_passed"])
        self.assertFalse(score["outcome_gate_passed"])
        self.assertFalse(score["claim_demonstrated"])
        self.assertEqual(score["preference_summary"]["palamedes_votes"], 3)
        self.assertEqual(score["preference_summary"]["unanimous_cases"], 3)
        self.assertEqual(
            score["condition_usage"]["input_token_ratio_palamedes_to_baseline"],
            4.25,
        )

    def test_recorded_attributable_labor_outcome_completes_outcome_gate(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            prepared = palamedes_proof.prepare_run(
                portfolio(root), run_root=root / "runs", run_id="proof-test"
            )
            run = Path(prepared["run_path"])

            outcome = palamedes_proof.record_outcome(
                run,
                case_id="case-0",
                selected_system="palamedes",
                observed_choice="Proof before expansion.",
                attributable_decision=True,
                owner_seconds_without=600,
                owner_seconds_with=120,
                evidence="Owner timestamped decision record.",
            )

            with self.assertRaises(ValueError):
                palamedes_proof.record_outcome(
                    run,
                    case_id="case-0",
                    selected_system="palamedes",
                    observed_choice="Rewrite history.",
                    attributable_decision=True,
                    owner_seconds_without=600,
                    owner_seconds_with=120,
                    evidence="Duplicate.",
                )

        self.assertTrue(outcome["labor_retired"])
        self.assertEqual(outcome["retired_seconds"], 480)

    def test_generation_failure_is_preserved_and_not_retried_in_place(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            prepared = palamedes_proof.prepare_run(
                portfolio(root), run_root=root / "runs", run_id="proof-test"
            )
            run = Path(prepared["run_path"])
            with patch(
                "palamedes_proof.generate_baseline",
                side_effect=ValueError("invalid mission"),
            ):
                with self.assertRaises(ValueError):
                    palamedes_proof.generate_condition(
                        run, condition="baseline", case_id="case-0"
                    )

            failures = list(
                (run / "cases" / "case-0").glob("baseline.failure-*.json")
            )
            record = palamedes_proof.load_object(failures[0])

        self.assertEqual(len(failures), 1)
        self.assertEqual(record["failure"], "invalid mission")
        self.assertFalse(record["retry_appended_to_same_run"])
        self.assertFalse((run / "cases" / "case-0" / "baseline.json").exists())


if __name__ == "__main__":
    unittest.main()
