#!/usr/bin/env python3
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from palamedes_chat import (
    MissionStore,
    build_opportunity_experience_archive,
    render_opportunity_scout,
    run_autonomous_opportunity_scout,
)
from palamedes_opportunity import (
    OpportunityStore,
    PERSPECTIVES,
    SENIOR_LENSES,
    run_opportunity_scout,
)


def perspective_findings():
    return [
        {
            "perspective": perspective,
            "applicability": "plausible",
            "finding": f"finding for {perspective}",
            "blind_spot": f"blind spot for {perspective}",
            "question_owner_did_not_ask": f"what changes for {perspective}?",
            "why_no_signal": "",
        }
        for perspective in PERSPECTIVES
    ]


def deep_reframes():
    return [
        {
            "lens": lens,
            "applicability": "plausible",
            "observed_signal": f"bounded signal for {lens}",
            "hidden_assumption": f"hidden assumption for {lens}",
            "reframe": f"reframe for {lens}",
            "implication": f"implication for {lens}",
            "second_order_effect": f"second-order effect for {lens}",
            "design_invariant": f"design invariant for {lens}",
            "disconfirming_observation": f"disconfirming signal for {lens}",
            "evidence_status": "inferred",
            "source_experience_ids": [],
            "why_no_signal": "",
            "evidence_needed": "",
        }
        for lens in SENIOR_LENSES
    ]


def opportunity():
    selected_perspectives = ["repeat_behavior", "monetization", "content_economy"]
    selected_lenses = [
        "second_order_and_feedback_effects",
        "operations_and_total_cost",
    ]
    return {
        "opportunity_id": "opportunity-1",
        "title": "Cross-mode seasonal journey",
        "opportunity_type": "established_pattern",
        "perspectives": selected_perspectives,
        "source_finding_ids": [
            f"finding-{perspective}" for perspective in selected_perspectives
        ],
        "senior_lenses": selected_lenses,
        "reframe_lineage": [
            {
                "reframe_id": f"reframe-{lens}",
                "changed_conclusion": f"{lens} changed the mechanism boundary.",
                "counterfactual_without_reframe": f"Without {lens}, only rewards change.",
            }
            for lens in selected_lenses
        ],
        "observation": "Players repeat matches across modes.",
        "latent_need": "Progress should accumulate across sessions.",
        "current_gap": "There is no shared long-term progression.",
        "mechanism": "A seasonal track credits healthy play across modes.",
        "behavior_change": "Players return and explore more modes.",
        "business_effect": "An optional paid track can create recurring revenue.",
        "product_fit": "Existing activity events can feed one progression track.",
        "evidence_needed": ["cohort retention", "reward production cost"],
        "fastest_test": "Run a free four-week progression test.",
        "failure_condition": "Return rate does not rise or play feels compulsory.",
        "insight_chain": {
            "hidden_assumption": "Each mode needs isolated progression.",
            "reframe": "Progress can represent a cross-mode journey.",
            "first_order_effect": "Players gain a reason to return.",
            "second_order_effect": "Shared progression redistributes attention among modes.",
            "feedback_or_externality": "Reward tuning can crowd out intrinsic play.",
            "local_optimum_trap": "Optimizing pass sales can damage mode health.",
            "design_invariant": "Core competition stays fair without payment.",
            "why_now": "Existing events provide a reversible integration point.",
        },
        "delivery_reality": {
            "migration_path": "Start as an optional free track.",
            "rollback_boundary": "Disable rewards without changing match state.",
            "ongoing_operating_burden": "Rewards and balance need seasonal ownership.",
            "ownership_and_authority": "Product owns cadence; economy owns balance.",
        },
        "failure_basis": {
            "basis_type": "inference_only",
            "source_experience_ids": [],
            "lesson": "No local failure record exists; protect against forced play.",
            "missing_viability_condition": "Sustainable reward production is unverified.",
            "guardrail": "Validate a free version before monetization.",
            "transfer_limit": "The inference does not establish willingness to pay.",
        },
        "consequence_graph": {
            "effects": [
                {
                    "effect_id": "effect-return",
                    "caused_by": "mechanism",
                    "stakeholder": "repeat player",
                    "horizon": "first season",
                    "valence": "benefit",
                    "effect": "Cross-mode progress creates a return reason.",
                    "early_signal": "More players return in the next week.",
                },
                {
                    "effect_id": "effect-crowding",
                    "caused_by": "effect-return",
                    "stakeholder": "intrinsically motivated player",
                    "horizon": "second season",
                    "valence": "risk",
                    "effect": "Reward optimization can crowd out preferred modes.",
                    "early_signal": "Mode diversity falls while task completion rises.",
                },
            ],
            "design_responses": [{
                "effect_id": "effect-crowding",
                "invariant": "Players retain meaningful choice of mode.",
                "mitigation": "Credit broad goals and cap narrow task pressure.",
                "stop_condition": "Stop if mode diversity falls materially.",
            }],
        },
        "validation_probe": {
            "kind": "behavioral_exposure",
            "reaches_observable_response": True,
            "preparation_only": False,
            "reversible": True,
            "terminal_output_kind": "observed_actor_response",
            "intervention": "Expose an optional free track to a bounded cohort.",
            "target_actor": "repeat players",
            "observation_window": "four weeks",
            "metric": "return rate and mode diversity",
            "observable_response": "Players return and choose among modes.",
            "baseline_or_counterfactual": "Matched players without the track.",
            "falsifier": "Return rate stays flat or mode diversity declines.",
            "rollback": "Remove the optional track and preserve match state.",
            "stop_condition": "Stop on fairness complaints or diversity decline.",
            "authority_preconditions": ["product approval", "economy review"],
            "branches": {
                "if_supported": "Test willingness to pay separately.",
                "if_refuted": "Retire shared progression.",
                "if_inconclusive": "Repeat with a longer observation window.",
            },
        },
    }


class OpportunityFixture:
    def __init__(self):
        self.calls = []

    def __call__(self, role, prompt):
        self.calls.append(role)
        if role == "opportunity_structure_observer":
            return {
                "observed_facts": ["players repeat short matches"],
                "inferences": ["long-term progression may be weak"],
                "unknowns": ["retention by cohort"],
                "users": ["repeat players"],
                "core_actions": ["play matches"],
                "repeat_loops": ["play and retry"],
                "progression": [],
                "content_supply": ["several game modes"],
                "social_surfaces": [],
                "value_capture": ["one-time purchase"],
                "operational_cadence": [],
                "distribution_loops": [],
                "constraints": ["avoid pay to win"],
                "underused_capabilities": ["cross-mode activity events"],
            }
        if role == "senior_opportunity_reframer":
            return {
                "perspective_findings": perspective_findings(),
                "deep_reframes": deep_reframes(),
            }
        if role == "multi_perspective_opportunity_synthesizer":
            return {"opportunities": [opportunity()], "no_opportunity_reason": ""}
        if role == "opportunity_reality_critic":
            return {
                "assessments": [{
                    "opportunity_id": "opportunity-1",
                    "disposition": "validate",
                    "strongest_reason": "The repeat loop and event stream already exist.",
                    "strongest_risk": "Reward production may erase the margin.",
                    "decision_rationale": "Test retention before monetizing.",
                    "senior_judgment_gap": "Willingness to pay is still unknown.",
                    "insight_survives_name_removal": True,
                    "second_order_accounted": True,
                    "failure_basis_honest": True,
                    "operational_burden_accounted": True,
                }],
                "portfolio_summary": "Validate a free season before adding payment.",
                "top_opportunity_ids": ["opportunity-1"],
            }
        raise AssertionError(role)


class OpportunityScoutTests(unittest.TestCase):
    def run_fixture(self, fixture=None, *, experiences=None):
        fixture = fixture or OpportunityFixture()
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        store = OpportunityStore(Path(temporary.name) / "opportunities")
        record = run_opportunity_scout(
            ask=fixture,
            store=store,
            context="Assess the business opportunities.",
            experiences=experiences,
        )
        return fixture, store, record

    def test_preserves_a_grounded_established_pattern_with_lineage(self):
        fixture, store, record = self.run_fixture()
        self.assertEqual(fixture.calls, [
            "opportunity_structure_observer",
            "senior_opportunity_reframer",
            "multi_perspective_opportunity_synthesizer",
            "opportunity_reality_critic",
        ])
        row = record["opportunities"][0]
        self.assertEqual(record["status"], "opportunities_found")
        self.assertEqual(row["opportunity_type"], "established_pattern")
        self.assertEqual(len(row["reframe_lineage"]), 2)
        self.assertFalse(record["delivery_authority_granted"])
        self.assertEqual(
            store.latest()["opportunity_scout_id"], record["opportunity_scout_id"]
        )

    def test_repairs_nested_structure_entries_once(self):
        fixture = OpportunityFixture()
        original = fixture.__call__
        structure_calls = 0

        def malformed_once(role, prompt):
            nonlocal structure_calls
            value = original(role, prompt)
            if role == "opportunity_structure_observer":
                structure_calls += 1
                if structure_calls == 1:
                    value["observed_facts"] = [{"fact": "players repeat matches"}]
            return value

        _, _, record = self.run_fixture(malformed_once)
        self.assertEqual(structure_calls, 2)
        self.assertEqual(
            record["product_structure"]["observed_facts"],
            ["players repeat short matches"],
        )

    def test_uncontracted_structure_fields_are_not_retained(self):
        fixture = OpportunityFixture()
        original = fixture.__call__

        def extra_claim(role, prompt):
            value = original(role, prompt)
            if role == "opportunity_structure_observer":
                value["fabricated_claim"] = {"metric": "10M users"}
            return value

        _, _, record = self.run_fixture(extra_claim)
        self.assertNotIn("fabricated_claim", record["product_structure"])

    def test_requires_every_perspective_and_senior_lens(self):
        fixture = OpportunityFixture()
        original = fixture.__call__

        def missing_coverage(role, prompt):
            value = original(role, prompt)
            if role == "senior_opportunity_reframer":
                value["deep_reframes"] = value["deep_reframes"][:-1]
            return value

        with self.assertRaisesRegex(ValueError, "every senior lens"):
            self.run_fixture(missing_coverage)

    def test_reframer_can_repair_one_missing_lens_with_full_contract(self):
        fixture = OpportunityFixture()
        original = fixture.__call__
        reframer_calls = 0
        repair_prompt = ""

        def missing_once(role, prompt):
            nonlocal reframer_calls, repair_prompt
            value = original(role, prompt)
            if role == "senior_opportunity_reframer":
                reframer_calls += 1
                if reframer_calls == 1:
                    value["deep_reframes"] = value["deep_reframes"][:-1]
                else:
                    repair_prompt = prompt
            return value

        _, _, record = self.run_fixture(missing_once)
        self.assertEqual(reframer_calls, 2)
        self.assertEqual(len(record["deep_reframes"]), len(SENIOR_LENSES))
        self.assertIn("SENIOR LENS CONTRACT", repair_prompt)
        self.assertIn(SENIOR_LENSES[-1], repair_prompt)

    def test_no_signal_lens_cannot_be_manufactured_or_cited(self):
        fixture = OpportunityFixture()
        original = fixture.__call__

        def manufactured(role, prompt):
            value = original(role, prompt)
            if role == "senior_opportunity_reframer":
                row = value["deep_reframes"][0]
                row.update({
                    "applicability": "no_signal",
                    "evidence_status": "unsupported",
                    "why_no_signal": "No bounded architecture evidence exists.",
                    "evidence_needed": "A component and dependency map.",
                })
            return value

        with self.assertRaisesRegex(ValueError, "cannot manufacture"):
            self.run_fixture(manufactured)

    def test_no_signal_lens_cannot_ground_an_opportunity(self):
        fixture = OpportunityFixture()
        original = fixture.__call__
        no_signal_lens = SENIOR_LENSES[1]

        def cited_no_signal(role, prompt):
            value = original(role, prompt)
            if role == "senior_opportunity_reframer":
                row = value["deep_reframes"][1]
                row.update({
                    "applicability": "no_signal",
                    "observed_signal": "",
                    "hidden_assumption": "",
                    "reframe": "",
                    "implication": "",
                    "second_order_effect": "",
                    "design_invariant": "",
                    "disconfirming_observation": "",
                    "evidence_status": "unsupported",
                    "source_experience_ids": [],
                    "why_no_signal": "No local incident or near miss is available.",
                    "evidence_needed": "A bounded failure or near-miss record.",
                })
            if role == "multi_perspective_opportunity_synthesizer":
                row = value["opportunities"][0]
                row["senior_lenses"] = [
                    "second_order_and_feedback_effects",
                    no_signal_lens,
                ]
                row["reframe_lineage"][1]["reframe_id"] = (
                    f"reframe-{no_signal_lens}"
                )
            return value

        with self.assertRaisesRegex(ValueError, "unavailable senior reframe"):
            self.run_fixture(cited_no_signal)

    def test_whitespace_wrapped_no_signal_cannot_ground_an_opportunity(self):
        fixture = OpportunityFixture()
        original = fixture.__call__
        no_signal_lens = SENIOR_LENSES[1]

        def cited_no_signal(role, prompt):
            value = original(role, prompt)
            if role == "senior_opportunity_reframer":
                row = value["deep_reframes"][1]
                row.update({
                    "applicability": " no_signal ",
                    "observed_signal": "",
                    "hidden_assumption": "",
                    "reframe": "",
                    "implication": "",
                    "second_order_effect": "",
                    "design_invariant": "",
                    "disconfirming_observation": "",
                    "evidence_status": " unsupported ",
                    "source_experience_ids": [],
                    "why_no_signal": "No bounded failure evidence exists.",
                    "evidence_needed": "A relevant failure record.",
                })
            if role == "multi_perspective_opportunity_synthesizer":
                row = value["opportunities"][0]
                row["senior_lenses"] = [
                    "second_order_and_feedback_effects",
                    no_signal_lens,
                ]
                row["reframe_lineage"][1]["reframe_id"] = (
                    f"reframe-{no_signal_lens}"
                )
            return value

        with self.assertRaisesRegex(ValueError, "unavailable senior reframe"):
            self.run_fixture(cited_no_signal)

    def test_rejects_non_string_opportunity_text(self):
        fixture = OpportunityFixture()
        original = fixture.__call__

        def malformed(role, prompt):
            value = original(role, prompt)
            if role == "multi_perspective_opportunity_synthesizer":
                value["opportunities"][0]["business_effect"] = {"revenue": "up"}
            return value

        with self.assertRaisesRegex(ValueError, "must be a non-empty string"):
            self.run_fixture(malformed)

    def test_opportunity_repair_repeats_exact_types_and_lineage_ids(self):
        fixture = OpportunityFixture()
        original = fixture.__call__
        synthesis_calls = 0
        repair_prompt = ""

        def repairable(role, prompt):
            nonlocal synthesis_calls, repair_prompt
            value = original(role, prompt)
            if role == "multi_perspective_opportunity_synthesizer":
                synthesis_calls += 1
                if synthesis_calls == 1:
                    value["opportunities"][0]["opportunity_type"] = "deep_insight"
                else:
                    repair_prompt = prompt
            return value

        _, _, record = self.run_fixture(repairable)
        self.assertEqual(synthesis_calls, 2)
        self.assertEqual(
            record["opportunities"][0]["opportunity_type"],
            "established_pattern",
        )
        self.assertIn("product_specific_adaptation", repair_prompt)
        self.assertIn("finding-content_economy", repair_prompt)
        self.assertIn("reframe-operations_and_total_cost", repair_prompt)

    def test_opportunity_repair_repeats_the_complete_nested_contract(self):
        fixture = OpportunityFixture()
        original = fixture.__call__
        synthesis_calls = 0
        repair_prompt = ""

        def missing_probe_once(role, prompt):
            nonlocal synthesis_calls, repair_prompt
            value = original(role, prompt)
            if role == "multi_perspective_opportunity_synthesizer":
                synthesis_calls += 1
                if synthesis_calls == 1:
                    del value["opportunities"][0]["validation_probe"]
                else:
                    repair_prompt = prompt
            return value

        _, _, record = self.run_fixture(missing_probe_once)
        self.assertEqual(synthesis_calls, 2)
        self.assertIn("validation_probe:", repair_prompt)
        self.assertIn("PRODUCT STRUCTURE", repair_prompt)
        self.assertEqual(
            record["opportunities"][0]["validation_probe"]["kind"],
            "behavioral_exposure",
        )

    def test_rejects_fabricated_direct_experience(self):
        fixture = OpportunityFixture()
        original = fixture.__call__

        def fabricated(role, prompt):
            value = original(role, prompt)
            if role == "multi_perspective_opportunity_synthesizer":
                failure = value["opportunities"][0]["failure_basis"]
                failure["basis_type"] = "direct_experience"
                failure["source_experience_ids"] = ["outcome-invented"]
            return value

        with self.assertRaisesRegex(ValueError, "unavailable experience"):
            self.run_fixture(fabricated)

    def test_supported_reframe_can_use_bounded_experience(self):
        fixture = OpportunityFixture()
        original = fixture.__call__

        def experienced(role, prompt):
            value = original(role, prompt)
            if role == "senior_opportunity_reframer":
                row = value["deep_reframes"][1]
                row.update({
                    "applicability": "supported",
                    "evidence_status": "observed",
                    "source_experience_ids": ["outcome-1"],
                })
            if role == "multi_perspective_opportunity_synthesizer":
                failure = value["opportunities"][0]["failure_basis"]
                failure["basis_type"] = "direct_experience"
                failure["source_experience_ids"] = ["outcome-1"]
            return value

        _, _, record = self.run_fixture(
            experienced,
            experiences=[{
                "experience_id": "outcome-1",
                "observed": {
                    "reported_outcome_status": "failure",
                    "outcome_type": "adverse_result",
                },
            }],
        )
        self.assertEqual(
            record["opportunities"][0]["failure_basis"]["source_experience_ids"],
            ["outcome-1"],
        )

    def test_direct_failure_basis_rejects_success_only_experience(self):
        fixture = OpportunityFixture()
        original = fixture.__call__

        def success_as_failure(role, prompt):
            value = original(role, prompt)
            if role == "multi_perspective_opportunity_synthesizer":
                failure = value["opportunities"][0]["failure_basis"]
                failure["basis_type"] = "direct_experience"
                failure["source_experience_ids"] = ["outcome-success"]
            return value

        with self.assertRaisesRegex(ValueError, "direct failure basis"):
            self.run_fixture(
                success_as_failure,
                experiences=[{
                    "experience_id": "outcome-success",
                    "observed": {
                        "reported_outcome_status": "success",
                        "outcome_type": "validated_improvement",
                    },
                }],
            )

    def test_success_with_insufficient_evidence_type_is_not_a_failure_basis(self):
        fixture = OpportunityFixture()
        original = fixture.__call__

        def success_as_failure(role, prompt):
            value = original(role, prompt)
            if role == "multi_perspective_opportunity_synthesizer":
                failure = value["opportunities"][0]["failure_basis"]
                failure["basis_type"] = "direct_experience"
                failure["source_experience_ids"] = ["outcome-success"]
            return value

        with self.assertRaisesRegex(ValueError, "direct failure basis"):
            self.run_fixture(
                success_as_failure,
                experiences=[{
                    "experience_id": "outcome-success",
                    "observed": {
                        "reported_outcome_status": "success",
                        "outcome_type": "insufficient_evidence",
                    },
                }],
            )

    def test_legacy_blocked_outcome_can_support_a_direct_failure_basis(self):
        fixture = OpportunityFixture()
        original = fixture.__call__

        def blocked_experience(role, prompt):
            value = original(role, prompt)
            if role == "multi_perspective_opportunity_synthesizer":
                failure = value["opportunities"][0]["failure_basis"]
                failure["basis_type"] = "direct_experience"
                failure["source_experience_ids"] = ["outcome-blocked"]
            return value

        _, _, record = self.run_fixture(
            blocked_experience,
            experiences=[{
                "experience_id": "outcome-blocked",
                "observed": {
                    "status": "unknown",
                    "outcome_type": "blocked_by_environment",
                },
            }],
        )
        self.assertEqual(
            record["opportunities"][0]["failure_basis"]["basis_type"],
            "direct_experience",
        )

    def test_optional_string_arrays_normalize_null_to_empty(self):
        fixture = OpportunityFixture()
        original = fixture.__call__

        def null_optional_arrays(role, prompt):
            value = original(role, prompt)
            if role == "multi_perspective_opportunity_synthesizer":
                row = value["opportunities"][0]
                row["evidence_needed"] = None
                row["failure_basis"]["source_experience_ids"] = None
                row["validation_probe"]["authority_preconditions"] = None
            return value

        _, _, record = self.run_fixture(null_optional_arrays)
        row = record["opportunities"][0]
        self.assertEqual(row["evidence_needed"], [])
        self.assertEqual(row["failure_basis"]["source_experience_ids"], [])
        self.assertEqual(row["validation_probe"]["authority_preconditions"], [])

    def test_unknown_no_signal_content_is_not_retained_or_groundable(self):
        fixture = OpportunityFixture()
        original = fixture.__call__

        def hidden_recommendation(role, prompt):
            value = original(role, prompt)
            if role == "senior_opportunity_reframer":
                row = value["deep_reframes"][0]
                row["recommendation"] = "Ship the migration despite no evidence."
            return value

        _, _, record = self.run_fixture(hidden_recommendation)
        self.assertNotIn("recommendation", record["deep_reframes"][0])

    def test_consequence_graph_requires_a_computed_two_hop_path(self):
        fixture = OpportunityFixture()
        original = fixture.__call__

        def one_hop(role, prompt):
            value = original(role, prompt)
            if role == "multi_perspective_opportunity_synthesizer":
                effects = value["opportunities"][0]["consequence_graph"]["effects"]
                effects[1]["caused_by"] = "mechanism"
            return value

        with self.assertRaisesRegex(ValueError, "computed second-order"):
            self.run_fixture(one_hop)

    def test_validation_probe_cannot_be_a_meta_review(self):
        fixture = OpportunityFixture()
        original = fixture.__call__

        def meta_review(role, prompt):
            value = original(role, prompt)
            if role == "multi_perspective_opportunity_synthesizer":
                probe = value["opportunities"][0]["validation_probe"]
                probe["kind"] = "meta_review"
                probe["preparation_only"] = True
            return value

        with self.assertRaisesRegex(ValueError, "not an action probe"):
            self.run_fixture(meta_review)

    def test_validation_probe_requires_a_reality_terminal_output(self):
        fixture = OpportunityFixture()
        original = fixture.__call__

        def disguised_review(role, prompt):
            value = original(role, prompt)
            if role == "multi_perspective_opportunity_synthesizer":
                probe = value["opportunities"][0]["validation_probe"]
                probe["kind"] = "data_query"
                probe["terminal_output_kind"] = "readiness_report"
                probe["intervention"] = "Write a readiness review."
            return value

        with self.assertRaisesRegex(ValueError, "observed or measured reality"):
            self.run_fixture(disguised_review)

    def test_opportunity_count_is_bounded_to_five(self):
        fixture = OpportunityFixture()
        original = fixture.__call__

        def six_rows(role, prompt):
            value = original(role, prompt)
            if role == "multi_perspective_opportunity_synthesizer":
                seed = value["opportunities"][0]
                value["opportunities"] = []
                for index in range(6):
                    row = copy.deepcopy(seed)
                    row["opportunity_id"] = f"opportunity-{index}"
                    value["opportunities"].append(row)
            return value

        with self.assertRaisesRegex(ValueError, "at most 5"):
            self.run_fixture(six_rows)

    def test_eligible_critic_must_pass_every_senior_check(self):
        fixture = OpportunityFixture()
        original = fixture.__call__

        def failed_check(role, prompt):
            value = original(role, prompt)
            if role == "opportunity_reality_critic":
                value["assessments"][0]["second_order_accounted"] = False
            return value

        with self.assertRaisesRegex(ValueError, "failed senior judgment check"):
            self.run_fixture(failed_check)

    def test_critic_repair_receives_the_required_opportunity_context(self):
        fixture = OpportunityFixture()
        original = fixture.__call__
        critic_calls = 0
        repair_prompt = ""

        def missing_once(role, prompt):
            nonlocal critic_calls, repair_prompt
            value = original(role, prompt)
            if role == "opportunity_reality_critic":
                critic_calls += 1
                if critic_calls == 1:
                    value["assessments"] = []
                    value["top_opportunity_ids"] = []
                else:
                    repair_prompt = prompt
            return value

        _, _, record = self.run_fixture(missing_once)
        self.assertEqual(critic_calls, 2)
        self.assertEqual(record["critic"]["top_opportunity_ids"], ["opportunity-1"])
        self.assertIn("REQUIRED OPPORTUNITY IDS", repair_prompt)
        self.assertIn("Cross-mode seasonal journey", repair_prompt)

    def test_runtime_archive_separates_observation_from_interpretation(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = MissionStore(Path(temporary) / "missions")
            store.save_contract({
                "mission_id": "mission-aaaaaaaaaaaa",
                "mission": "Test the return loop.",
                "rationale": "The repeat loop is uncertain.",
                "success_metric": "Weekly return rate",
            })
            store.append_outcome({
                "outcome_id": "outcome-aaaaaaaaaaaa",
                "mission_contract_id": "mission-aaaaaaaaaaaa",
                "recorded_at": "2026-08-12T00:00:00+00:00",
                "execution_status": "completed",
                "reported_outcome_status": "mixed",
                "outcome_type": "insufficient_evidence",
                "observation": "Return rose but the comparison cohort was missing.",
                "evidence_source_type": "implementer_claim",
                "attribution": "unresolved",
            })
            store.append_outcome_interpretation({
                "outcome_id": "outcome-aaaaaaaaaaaa",
                "causal_signature": "missing-counterfactual",
                "mechanism_summary": "The probe could not isolate the mechanism.",
                "mission_disposition": "revise",
                "confidence": 55,
            })
            archive = build_opportunity_experience_archive(store)
        self.assertEqual(archive[0]["experience_id"], "outcome-aaaaaaaaaaaa")
        self.assertEqual(archive[0]["observed"]["reported_outcome_status"], "mixed")
        self.assertEqual(
            archive[0]["interpreted"]["causal_signature"],
            "missing-counterfactual",
        )
        self.assertTrue(
            archive[0]["epistemic_boundary"][
                "interpretation_is_analysis_not_observation"
            ]
        )

    def test_runtime_archive_preserves_legacy_failure_status(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = MissionStore(Path(temporary) / "missions")
            store.append_outcome({
                "outcome_version": "palamedes-mission-outcome/1",
                "outcome_id": "outcome-legacy000001",
                "mission_contract_id": "mission-legacy000001",
                "status": "failure",
                "observation": "The legacy probe failed.",
            })
            archive = build_opportunity_experience_archive(store)
        self.assertEqual(archive[0]["observed"]["status"], "failure")

    def test_autonomous_wrapper_passes_the_experience_archive(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = MissionStore(Path(temporary) / "missions")
            store.append_outcome({
                "outcome_id": "outcome-bbbbbbbbbbbb",
                "mission_contract_id": "mission-bbbbbbbbbbbb",
                "reported_outcome_status": "failure",
                "outcome_type": "adverse_result",
                "observation": "The probe increased operating load.",
            })
            captured = {}

            def fake_run(**kwargs):
                captured.update(kwargs)
                return {"opportunity_scout_id": "opportunity-aaaaaaaaaaaa"}

            with patch("palamedes_opportunity.run_opportunity_scout", fake_run):
                record = run_autonomous_opportunity_scout(
                    provider=type(
                        "FixtureProvider",
                        (),
                        {"provider_name": "fixture", "model": "fixture"},
                    )(),
                    mission_store=store,
                    context="bounded context",
                )
        self.assertEqual(record["opportunity_scout_id"], "opportunity-aaaaaaaaaaaa")
        self.assertEqual(
            captured["experiences"][0]["experience_id"],
            "outcome-bbbbbbbbbbbb",
        )

    def test_renderer_surfaces_the_senior_reasoning_and_action_probe(self):
        _, _, record = self.run_fixture()
        rendered = render_opportunity_scout(record)
        self.assertIn("reframe:", rendered)
        self.assertIn("second-order:", rendered)
        self.assertIn("failure basis:", rendered)
        self.assertIn("action probe:", rendered)
        self.assertIn("consequence depth: 2", rendered)

    def test_changed_perspective_finding_changes_the_record_identity(self):
        fixture_a = OpportunityFixture()
        _, _, record_a = self.run_fixture(fixture_a)
        fixture_b = OpportunityFixture()
        original = fixture_b.__call__

        def changed_finding(role, prompt):
            value = original(role, prompt)
            if role == "senior_opportunity_reframer":
                value["perspective_findings"][0]["finding"] = (
                    "A materially different bounded finding."
                )
            return value

        _, _, record_b = self.run_fixture(changed_finding)
        self.assertNotEqual(
            record_a["opportunity_scout_id"], record_b["opportunity_scout_id"]
        )


if __name__ == "__main__":
    unittest.main()
