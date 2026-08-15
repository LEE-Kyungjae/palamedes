#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

import palamedes_inventor_proof as inventor
import palamedes_proof


def portfolio(root: Path):
    cases = []
    for index in range(3):
        repo = root / f"external-{index}"
        repo.mkdir()
        (repo / "README.md").write_text(f"External project {index}\n", encoding="utf-8")
        cases.append({
            "case_id": f"external-case-{index}",
            "owner_id": f"external-owner-{index}",
            "owner_relationship": "independent_external",
            "palamedes_tuning_exposure": False,
            "repository": str(repo),
            "question": "What opportunity should change the next decision?",
            "required_decision": "Choose one bounded external probe.",
            "artifacts": ["README.md"],
            "probe_preregistration": {
                "decision_to_be_changed": "Choose a product direction.",
                "intervention_window": "1-7 days",
                "primary_metric": "qualified return",
                "success_threshold": "at least one qualified return",
                "failure_threshold": "zero qualified returns",
                "measurement_source": f"fixed-log-{index}",
            },
        })
    return {
        "proof_portfolio_version": "palamedes-proof-portfolio/1",
        "inventor_proof_version": "palamedes-inventor-proof/1",
        "portfolio_id": "test-external",
        "generation_protocol": {"same_model_required": True, "same_information_packet_required": True, "compute_is_not_equal": True, "compute_tradeoff_must_be_reported": True, "maximum_artifact_bytes": 2000},
        "inventor_protocol": {"external_projects_required": True, "independent_human_review_required": True, "equal_call_comparator_required": True, "comparison_condition": "tournament", "treatment_condition": "palamedes", "calls_per_condition": 4, "probe_preregistered_before_reveal": True, "measured_outcomes_required": True, "failed_cases_retained": True},
        "rubric": {axis: {"weight": 20} for axis in inventor.AXES},
        "success_gate": {"minimum_cases": 3, "minimum_blinded_reviews_per_case": 3, "palamedes_preferred_cases": 2, "minimum_attributable_outcomes": 0, "minimum_labor_retirement_cases": 0},
        "inventor_success_gate": {"minimum_external_cases": 3, "minimum_independent_human_reviews_per_case": 3, "minimum_palamedes_preferred_cases": 2, "minimum_measured_probe_outcomes": 3, "minimum_positive_attributable_outcomes": 2},
        "cases": cases,
    }


class InventorProofTests(unittest.TestCase):
    def test_validation_rejects_tuned_or_nonexternal_case(self):
        with tempfile.TemporaryDirectory() as tempdir:
            payload = portfolio(Path(tempdir))
            payload["cases"][0]["palamedes_tuning_exposure"] = True
            payload["cases"][0]["owner_relationship"] = "creator"
            errors = inventor.validate_inventor_portfolio(payload)
        self.assertTrue(any("tuning_exposure" in error for error in errors))
        self.assertTrue(any("owner_relationship" in error for error in errors))

    def test_prepare_preserves_external_custody(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            config = portfolio(root)
            result = inventor.prepare_inventor_run(config, run_root=root / "runs", run_id="inventor-test")
            custody = palamedes_proof.load_object(Path(result["run_path"]) / "private" / "inventor-custody.json")
        self.assertTrue(custody["external_evidence_fabrication_forbidden"])

    def test_probe_outcome_is_append_once_and_bound_to_source(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            config = portfolio(root)
            result = inventor.prepare_inventor_run(config, run_root=root / "runs", run_id="inventor-test")
            run = Path(result["run_path"])
            payload = {"case_id": "external-case-0", "started_at": "2026-01-01", "ended_at": "2026-01-02", "measurement_source": "fixed-log-0", "measurement_provenance": "measured", "raw_evidence": "immutable log sha256:abc", "owner_attestation": "I observed this result.", "selected_system": "palamedes", "metric_value": 1, "threshold_passed": True, "attributable_decision": True}
            record = inventor.record_probe_outcome(run, payload)
            with self.assertRaises(ValueError):
                inventor.record_probe_outcome(run, payload)
            expected = inventor.fingerprint(config["cases"][0]["probe_preregistration"])
        self.assertEqual(record["probe_preregistration_fingerprint"], expected)

    def test_human_review_rejects_owner_and_nonhuman(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            config = portfolio(root)
            result = inventor.prepare_inventor_run(config, run_root=root / "runs", run_id="inventor-test")
            run = Path(result["run_path"])
            packet = {"blind_packet_version": "palamedes-proof-blind/1", "run_id": "inventor-test", "rubric": config["rubric"], "cases": [{"case_id": f"external-case-{i}"} for i in range(3)]}
            palamedes_proof.write_object(run / "blind" / "packet.json", packet)
            response = {"reviewer_id": "external-owner-0", "reviewer_kind": "human", "reviewer_relationship": "independent", "origin_visible": False, "independence_attestation": "I did not see origins.", "reviews": []}
            with self.assertRaisesRegex(ValueError, "cover every"):
                inventor.import_human_review(run, response)
            response["reviewer_kind"] = "model"
            with self.assertRaisesRegex(ValueError, "must be human"):
                inventor.import_human_review(run, response)


if __name__ == "__main__":
    unittest.main()
