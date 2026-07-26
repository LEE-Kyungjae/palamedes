#!/usr/bin/env python3

import json
import tempfile
import unittest
from pathlib import Path

from palamedes_prompt import (
    PromptAgendaStore,
    record_causal_pattern,
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


if __name__ == "__main__":
    unittest.main()
