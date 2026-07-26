#!/usr/bin/env python3

import json
import tempfile
import unittest
from pathlib import Path

from palamedes_prompt import (
    PromptAgendaStore,
    record_causal_pattern,
    record_design_hypothesis,
    record_zoom_pattern,
    run_outcome_backfill,
    run_prompt_architecture,
)


class StaticPromptProvider:
    provider_name = "static"
    model = "fixture"

    def __init__(self):
        self.calls = []

    def stream(self, messages):
        self.calls.append(messages)
        prompt = messages[-1]["content"]
        if prompt.startswith("ROLE: prompt_architect"):
            yield json.dumps(
                {
                    "missing_cognitive_mode": "causal abstraction",
                    "prompt_candidates": [
                        {
                            "prompt_id": "prompt-1",
                            "prompt": "Test whether one state projection explains the repeated defects.",
                            "perspective": "system boundary",
                            "expected_information_gain": 86,
                            "scope_risk": 30,
                            "falsifier": "The defects have independent causes.",
                            "non_goals": ["Immediate refactoring"],
                        },
                        {
                            "prompt_id": "prompt-2",
                            "prompt": "Enumerate the remaining state rows.",
                            "perspective": "coverage matrix",
                            "expected_information_gain": 48,
                            "scope_risk": 72,
                            "falsifier": "New defect density is low.",
                            "non_goals": ["Product expansion"],
                        },
                    ],
                }
            )
            return
        if prompt.startswith("ROLE: prompt_adversary"):
            yield json.dumps(
                {
                    "critiques": [
                        {
                            "prompt_id": "prompt-1",
                            "fatal_risks": [],
                            "repairable_risks": ["The proposed projection may be too broad"],
                            "disqualifying": False,
                        },
                        {
                            "prompt_id": "prompt-2",
                            "fatal_risks": ["It continues symptom enumeration"],
                            "repairable_risks": [],
                            "disqualifying": True,
                        },
                    ]
                }
            )
            return
        if prompt.startswith("ROLE: prompt_selector"):
            yield json.dumps(
                {
                    "decision": "select",
                    "selected_prompt_id": "prompt-1",
                    "rationale": "It can change the next architectural decision with bounded scope.",
                    "role_sequence": ["pattern_synthesizer", "counterexample_hunter"],
                    "call_budget": 2,
                    "stop_conditions": ["The repeated mechanisms prove independent"],
                }
            )
            return
        raise AssertionError("unexpected prompt role")


def interpretation(number):
    suffix = f"{number:012x}"
    return {
        "outcome_id": f"outcome-{suffix}",
        "mission_contract_id": f"mission-{suffix}",
        "causal_signature": "presentation-state-precedence",
        "mechanism_summary": "Committed state outranked the active presentation boundary.",
    }


class PalamedesPromptTests(unittest.TestCase):
    def test_repeated_causal_signature_generates_competing_bounded_agenda(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = PromptAgendaStore(Path(tempdir) / "prompt-intelligence")
            first = record_causal_pattern(
                store=store, interpretation=interpretation(1)
            )
            second = record_causal_pattern(
                store=store, interpretation=interpretation(2)
            )
            provider = StaticPromptProvider()
            result = run_prompt_architecture(
                provider=provider, store=store, cluster=second
            )
            repeated = run_prompt_architecture(
                provider=provider, store=store, cluster=second
            )

        self.assertFalse(first["meta_shift_required"])
        self.assertTrue(second["meta_shift_required"])
        self.assertEqual(second["recurrence_count"], 2)
        self.assertEqual(result["status"], "completed")
        agenda = result["agenda"]
        self.assertEqual(agenda["missing_cognitive_mode"], "causal abstraction")
        self.assertEqual(agenda["selected_prompt"]["prompt_id"], "prompt-1")
        self.assertFalse(agenda["constitutional_constraints_mutable"])
        self.assertFalse(agenda["delivery_authority_granted"])
        self.assertEqual(
            [item["role"] for item in agenda["artifacts"]],
            ["prompt_architect", "prompt_adversary", "prompt_selector"],
        )
        self.assertEqual(repeated["status"], "already_selected")
        self.assertEqual(len(provider.calls), 3)

    def test_five_micro_outcomes_on_one_surface_require_fresh_eyes_zoom(self):
        records = []
        for number in range(1, 6):
            item = interpretation(number)
            item.update(
                {
                    "work_scale": "micro",
                    "surface_key": "game-screen",
                }
            )
            records.append(item)
        with tempfile.TemporaryDirectory() as tempdir:
            store = PromptAgendaStore(Path(tempdir) / "prompt-intelligence")
            result = record_zoom_pattern(store=store, interpretations=records)

        self.assertEqual(result["status"], "required")
        cluster = result["cluster"]
        self.assertTrue(cluster["fresh_eyes_required"])
        self.assertEqual(cluster["zoom_shift_from"], "micro")
        self.assertEqual(cluster["zoom_shift_to"], "component_or_product")
        self.assertEqual(cluster["recurrence_count"], 5)

    def test_contractless_design_possibility_is_incubated_without_authority(self):
        item = interpretation(9)
        item.update(
            {
                "surface_key": "throw-shadow",
                "finding_lane": "design_hypothesis",
                "hypothesis_scope": "Compare fixed and height-responsive shadows.",
                "exploration_value": 64,
            }
        )
        with tempfile.TemporaryDirectory() as tempdir:
            store = PromptAgendaStore(Path(tempdir) / "prompt-intelligence")
            result = record_design_hypothesis(store=store, interpretation=item)
            saved = json.loads(
                next(store.hypotheses_root.glob("*.json")).read_text()
            )

        self.assertEqual(result["status"], "recorded")
        self.assertEqual(saved["status"], "incubating")
        self.assertFalse(saved["mission_authority_granted"])
        self.assertIn("No correctness", saved["claim_limit"])

    def test_legacy_outcome_backfill_is_read_only_and_builds_meta_memory(self):
        class BackfillProvider(StaticPromptProvider):
            def stream(self, messages):
                self.calls.append(messages)
                if messages[-1]["content"].startswith(
                    "ROLE: retrospective_outcome_mapper"
                ):
                    yield json.dumps(
                        {
                            "interpretations": [
                                {
                                    "outcome_id": "outcome-000000000001",
                                    "causal_signature": "phase-state-confusion",
                                    "mechanism_summary": "Committed state controlled temporary presentation.",
                                    "work_scale": "micro",
                                    "surface_key": "throw-stage",
                                    "finding_lane": "correctness_defect",
                                    "exploration_value": 75,
                                    "hypothesis_scope": "",
                                }
                            ]
                        }
                    )
                    return
                yield from super().stream(messages)

        raw = {
            "outcome_id": "outcome-000000000001",
            "mission_contract_id": "mission-000000000001",
            "status": "success",
            "observation": "A presentation mismatch was corrected.",
        }
        provider = BackfillProvider()
        with tempfile.TemporaryDirectory() as tempdir:
            store = PromptAgendaStore(Path(tempdir) / "prompt-intelligence")
            result = run_outcome_backfill(
                provider=provider,
                store=store,
                outcomes=[raw],
                already_interpreted_outcome_ids=set(),
                limit=1,
            )
            saved = json.loads(
                next(store.backfill_root.glob("*.json")).read_text()
            )

        self.assertEqual(result["status"], "completed")
        self.assertTrue(saved["source_outcome_immutable"])
        self.assertEqual(saved["causal_signature"], "phase-state-confusion")
        self.assertEqual(raw["status"], "success")


if __name__ == "__main__":
    unittest.main()
