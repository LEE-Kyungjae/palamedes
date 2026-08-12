#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

from palamedes_opportunity import OpportunityStore, PERSPECTIVES, run_opportunity_scout


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
        if role == "multi_perspective_opportunity_synthesizer":
            return {
                "perspective_findings": [
                    {"perspective": perspective, "finding": f"finding for {perspective}"}
                    for perspective in PERSPECTIVES
                ],
                "opportunities": [{
                    "opportunity_id": "opportunity-1",
                    "title": "Cross-mode seasonal journey",
                    "opportunity_type": "established_pattern",
                    "perspectives": ["repeat_behavior", "monetization", "content_economy"],
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
                }],
                "no_opportunity_reason": "",
            }
        if role == "opportunity_reality_critic":
            return {
                "assessments": [{
                    "opportunity_id": "opportunity-1",
                    "disposition": "validate",
                    "strongest_reason": "The repeat loop and event stream already exist.",
                    "strongest_risk": "Reward production may erase the margin.",
                    "decision_rationale": "Test retention before monetizing.",
                }],
                "portfolio_summary": "Validate a free season before adding payment.",
                "top_opportunity_ids": ["opportunity-1"],
            }
        raise AssertionError(role)


class OpportunityScoutTests(unittest.TestCase):
    def test_preserves_a_grounded_established_pattern(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = OpportunityFixture()
            store = OpportunityStore(Path(temporary) / "opportunities")
            record = run_opportunity_scout(
                ask=fixture, store=store, context="Assess the business opportunities."
            )
            self.assertEqual(fixture.calls, [
                "opportunity_structure_observer",
                "multi_perspective_opportunity_synthesizer",
                "opportunity_reality_critic",
            ])
            self.assertEqual(record["status"], "opportunities_found")
            self.assertEqual(
                record["opportunities"][0]["opportunity_type"], "established_pattern"
            )
            self.assertIn("monetization", record["opportunities"][0]["perspectives"])
            self.assertFalse(record["delivery_authority_granted"])
            self.assertEqual(store.latest()["opportunity_scout_id"], record["opportunity_scout_id"])

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

        with tempfile.TemporaryDirectory() as temporary:
            record = run_opportunity_scout(
                ask=malformed_once,
                store=OpportunityStore(Path(temporary) / "opportunities"),
                context="Assess opportunities.",
            )
        self.assertEqual(structure_calls, 2)
        self.assertEqual(record["product_structure"]["observed_facts"], [
            "players repeat short matches"
        ])

    def test_requires_every_perspective_to_be_inspected(self):
        fixture = OpportunityFixture()
        original = fixture.__call__

        def missing_perspective(role, prompt):
            value = original(role, prompt)
            if role == "multi_perspective_opportunity_synthesizer":
                value["perspective_findings"] = value["perspective_findings"][:-1]
            return value

        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "every perspective"):
                run_opportunity_scout(
                    ask=missing_perspective,
                    store=OpportunityStore(Path(temporary) / "opportunities"),
                    context="Assess opportunities.",
                )


if __name__ == "__main__":
    unittest.main()
