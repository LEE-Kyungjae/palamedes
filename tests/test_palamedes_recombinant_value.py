import copy
import unittest

from palamedes_mission import (
    evaluate_grounded_recombinant_candidate,
    recombinant_evaluation_guideline,
    validate_recombinant_value_profile,
)


class RecombinantValueProfileTests(unittest.TestCase):
    def _payload(self):
        measures = (
            ("relation_rarity", 0.82),
            ("structural_delta", 0.76),
            ("baseline_non_reducibility", 0.71),
            ("semantic_distance", 0.48),
            ("human_judgment", 0.79),
        )
        payload = {
            "evaluation_id": "recombinant-eval-001",
            "candidate_id": "candidate-rare-tail",
            "comparison_population_id": "palamedes-candidates-2026q3",
            "comparison_as_of": "2026-08-26T00:00:00Z",
            "evaluation_as_of": "2026-08-26T01:00:00Z",
            "evaluation_rationale": "Preserve a familiar operational core while testing one unusual authority relation.",
            "recombinant_profile": {
                "known_components": ["evidence ledger", "bounded probe", "mission candidate"],
                "conventional_core_strength": 0.88,
                "conventional_core_evidence_ids": ["baseline-001"],
                "atypical_tail_strength": 0.82,
                "atypical_relations": [
                    {
                        "relation_id": "relation-001",
                        "left_component": "evidence ledger",
                        "right_component": "bounded probe",
                        "relation": "probe allocation responds to disagreement among novelty measures",
                        "structural_delta": "uncertainty changes treatment instead of only changing rank",
                        "rarity_evidence_id": "rarity-001",
                        "rarity_strength": 0.82,
                    }
                ],
            },
            "novelty_measures": [
                {
                    "measure": name,
                    "score": score,
                    "evidence_id": f"evidence-{name}",
                    "rationale": f"Independent assessment of {name}.",
                }
                for name, score in measures
            ],
            "novelty_measure_disagreement": True,
            "disagreement_rationale": "Semantic distance is moderate while the structural relation is rare.",
            "absorption_profile": {
                "host_capability_snapshot_id": "capability-snapshot-001",
                "local_knowledge_score": 0.73,
                "missing_concepts": ["calibrated novelty comparison population"],
                "comprehension_cost": 0.68,
                "independent_validator_available": True,
            },
            "knowledge_temporality": {
                "evidence_as_of": "2026-08-26T00:00:00Z",
                "last_validated_at": "2026-08-26T00:00:00Z",
                "maturity_score": 0.61,
                "adoption_saturation": 0.24,
                "obsolescence_risk": 0.17,
                "maturity_rationale": "The component contracts exist but outcome calibration is new.",
            },
            "complement_profile": {
                "complements_required": True,
                "integration_cost": 0.41,
                "complements": [
                    {
                        "complement_id": "complement-001",
                        "capability": "historical candidate evaluation set",
                        "available": False,
                        "compatible": True,
                        "availability_evidence_id": "inventory-001",
                        "owner": "human evaluator",
                    }
                ],
            },
            "uncertainty_profile": {
                "expected_value": 0.67,
                "outcome_variance": 0.79,
                "treatment": "bounded_probe",
                "treatment_rationale": "High variance warrants a reversible offline evaluation.",
                "success_signal": "Added dimensions improve blinded preservation decisions.",
                "failure_signal": "Added dimensions do not outperform current scores.",
                "falsifier": "Reviewer agreement and outcome prediction remain unchanged.",
                "probe": "Score a frozen historical candidate sample.",
                "probe_budget_id": "probe-budget-001",
                "probe_reversible": True,
            },
            "inverted_u_hardcoded": False,
            "citation_impact_used_as_value": False,
            "novelty_overrides_constitutional_gates": False,
            "profile_authorizes_mission": False,
        }
        rubric_values = {
            "conventional_core_strength": 0.88,
            "atypical_tail_strength": 0.82,
            "local_knowledge_score": 0.73,
            "comprehension_cost": 0.68,
            "knowledge_maturity": 0.61,
            "integration_cost": 0.41,
            "outcome_variance": 0.79,
        }
        payload["rubric_assessments"] = [
            {
                "dimension": dimension,
                "score": score,
                "anchor": "zero" if score <= 0.24 else "mid" if score <= 0.74 else "one",
                "evidence_ids": [f"rubric-evidence-{dimension}"],
                "rationale": f"The evidence places {dimension} in its declared anchor.",
            }
            for dimension, score in rubric_values.items()
        ]
        return payload

    def _registries(self, payload):
        evidence_ids = set(payload["recombinant_profile"]["conventional_core_evidence_ids"])
        evidence_ids.update(
            relation["rarity_evidence_id"]
            for relation in payload["recombinant_profile"]["atypical_relations"]
        )
        evidence_ids.update(measure["evidence_id"] for measure in payload["novelty_measures"])
        evidence_ids.update(
            complement["availability_evidence_id"]
            for complement in payload["complement_profile"]["complements"]
        )
        evidence_ids.update(
            evidence_id
            for assessment in payload["rubric_assessments"]
            for evidence_id in assessment["evidence_ids"]
        )
        return {
            "evidence_records": {
                evidence_id: {
                    "status": "verified",
                    "observed_at": "2026-08-26T00:30:00Z",
                    "source_id": f"source-{evidence_id}",
                }
                for evidence_id in evidence_ids
            },
            "comparison_populations": {
                payload["comparison_population_id"]: {
                    "as_of": payload["comparison_as_of"],
                    "candidate_count": 40,
                    "selection_rule": "same host, candidate kind, and evaluation quarter",
                }
            },
            "capability_snapshots": {
                payload["absorption_profile"]["host_capability_snapshot_id"]: {
                    "as_of": "2026-08-26T00:15:00Z",
                    "demonstrated_capabilities": ["evidence validation", "bounded offline evaluation"],
                }
            },
        }

    def _eligibility(self):
        return {
            "consequence_eligible": True,
            "causally_coherent": True,
            "constitutional_gates_passed": True,
            "structural_delta_verified": True,
            "baseline_reducible": False,
            "human_authority_preserved": True,
            "probe_complement_ids": ["complement-001"],
            "frontier_preservation_requested": False,
        }

    def test_accepts_conventional_core_with_atypical_tail_and_bounded_probe(self):
        report = validate_recombinant_value_profile(self._payload())

        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual(report["unavailable_complement_count"], 1)
        self.assertEqual(report["uncertainty_treatment"], "bounded_probe")
        self.assertTrue(report["novelty_measure_disagreement"])
        self.assertFalse(report["mission_authorized"])

    def test_rejects_scalar_or_incomplete_novelty_evidence(self):
        payload = self._payload()
        payload["novelty_measures"] = payload["novelty_measures"][:1]
        payload["novelty_measure_disagreement"] = False

        report = validate_recombinant_value_profile(payload)

        self.assertFalse(report["valid"])
        self.assertTrue(any("exactly five" in error for error in report["errors"]))

    def test_rejects_relations_outside_known_components(self):
        payload = self._payload()
        payload["recombinant_profile"]["atypical_relations"][0][
            "right_component"
        ] = "unretrieved magical component"

        report = validate_recombinant_value_profile(payload)

        self.assertFalse(report["valid"])
        self.assertTrue(any("known component" in error for error in report["errors"]))

    def test_requires_missing_concept_when_comprehension_cost_is_high(self):
        payload = self._payload()
        payload["absorption_profile"]["missing_concepts"] = []

        report = validate_recombinant_value_profile(payload)

        self.assertFalse(report["valid"])
        self.assertTrue(any("high comprehension cost" in error for error in report["errors"]))

    def test_preserves_metric_disagreement_instead_of_averaging_it_away(self):
        payload = self._payload()
        payload["novelty_measure_disagreement"] = False

        report = validate_recombinant_value_profile(payload)

        self.assertFalse(report["valid"])
        self.assertGreater(report["novelty_measure_spread"], 0.25)

    def test_requires_a_reversible_discriminating_bounded_probe(self):
        payload = self._payload()
        del payload["uncertainty_profile"]["probe"]
        payload["uncertainty_profile"]["probe_reversible"] = False

        report = validate_recombinant_value_profile(payload)

        self.assertFalse(report["valid"])
        self.assertTrue(any("bounded probe" in error for error in report["errors"]))

    def test_rejects_research_proxy_as_authority(self):
        for field in (
            "inverted_u_hardcoded",
            "citation_impact_used_as_value",
            "novelty_overrides_constitutional_gates",
            "profile_authorizes_mission",
        ):
            with self.subTest(field=field):
                payload = copy.deepcopy(self._payload())
                payload[field] = True
                report = validate_recombinant_value_profile(payload)
                self.assertFalse(report["valid"])
                self.assertTrue(any(field in error for error in report["errors"]))

    def test_guideline_exposes_anchored_dimensions_and_dispositions(self):
        guideline = recombinant_evaluation_guideline()

        self.assertEqual(guideline["version"], "recombinant-evaluation-guideline/1")
        self.assertEqual(
            set(guideline["dispositions"]),
            {"reject", "defer", "preserve", "bounded_probe", "progress"},
        )
        for dimension in guideline["dimensions"].values():
            self.assertEqual(
                set(dimension), {"zero", "mid", "one", "required_evidence"}
            )
        self.assertEqual(guideline["calibration_status"], "provisional_ordinal_anchors")

    def test_rejects_score_without_matching_guideline_anchor(self):
        payload = self._payload()
        payload["rubric_assessments"][0]["anchor"] = "zero"

        report = validate_recombinant_value_profile(payload)

        self.assertFalse(report["valid"])
        self.assertTrue(any("provisional score band" in error for error in report["errors"]))

    def test_rejects_rubric_score_that_disagrees_with_profile(self):
        payload = self._payload()
        payload["rubric_assessments"][0]["score"] = 0.5
        payload["rubric_assessments"][0]["anchor"] = "mid"

        report = validate_recombinant_value_profile(payload)

        self.assertFalse(report["valid"])
        self.assertTrue(any("profile score" in error for error in report["errors"]))

    def test_grounded_evaluator_rejects_fabricated_evidence(self):
        payload = self._payload()
        registries = self._registries(payload)
        del registries["evidence_records"]["rarity-001"]

        report = evaluate_grounded_recombinant_candidate(
            payload=payload, registries=registries, eligibility=self._eligibility()
        )

        self.assertFalse(report["valid"])
        self.assertEqual(report["disposition"], "reject")
        self.assertTrue(any("rarity-001" in error for error in report["grounding_errors"]))

    def test_grounded_evaluator_rejects_failed_hard_gate(self):
        payload = self._payload()
        eligibility = self._eligibility()
        eligibility["causally_coherent"] = False

        report = evaluate_grounded_recombinant_candidate(
            payload=payload,
            registries=self._registries(payload),
            eligibility=eligibility,
        )

        self.assertEqual(report["disposition"], "reject")
        self.assertFalse(report["mission_authorized"])

    def test_grounded_evaluator_routes_ready_uncertainty_to_bounded_probe(self):
        payload = self._payload()
        complement = payload["complement_profile"]["complements"][0]
        complement["available"] = True

        report = evaluate_grounded_recombinant_candidate(
            payload=payload,
            registries=self._registries(payload),
            eligibility=self._eligibility(),
        )

        self.assertTrue(report["valid"], report)
        self.assertEqual(report["disposition"], "bounded_probe")
        self.assertTrue(report["probe_complements_ready"])
        self.assertTrue(report["human_decision_required"])

    def test_grounded_evaluator_defers_when_probe_complement_is_unavailable(self):
        payload = self._payload()

        report = evaluate_grounded_recombinant_candidate(
            payload=payload,
            registries=self._registries(payload),
            eligibility=self._eligibility(),
        )

        self.assertTrue(report["valid"], report)
        self.assertEqual(report["disposition"], "defer")

    def test_grounded_evaluator_preserves_grounded_frontier_when_requested(self):
        payload = self._payload()
        eligibility = self._eligibility()
        eligibility["frontier_preservation_requested"] = True

        report = evaluate_grounded_recombinant_candidate(
            payload=payload,
            registries=self._registries(payload),
            eligibility=eligibility,
        )

        self.assertTrue(report["valid"], report)
        self.assertEqual(report["disposition"], "preserve")

    def test_grounded_evaluator_progresses_ready_normal_evidence_path(self):
        payload = self._payload()
        payload["uncertainty_profile"]["treatment"] = "normal_progression"
        complement = payload["complement_profile"]["complements"][0]
        complement["available"] = True

        report = evaluate_grounded_recombinant_candidate(
            payload=payload,
            registries=self._registries(payload),
            eligibility=self._eligibility(),
        )

        self.assertTrue(report["valid"], report)
        self.assertEqual(report["disposition"], "progress")

    def test_rejects_temporally_impossible_grounding(self):
        payload = self._payload()
        payload["knowledge_temporality"]["last_validated_at"] = "2026-08-27T00:00:00Z"

        report = validate_recombinant_value_profile(payload)

        self.assertFalse(report["valid"])
        self.assertTrue(any("evaluation_as_of" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
