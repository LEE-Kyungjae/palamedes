#!/usr/bin/env python3
import copy
import json
import sys
import unittest
from pathlib import Path


SCAFFOLD_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = SCAFFOLD_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from palamedes_agents.adapters.palamedes_adapter import PalamedesAdapter
from palamedes_agents.runtime.agent_cycle import AgentCycle
from palamedes_agents.strategy_llm import StaticStrategyProvider
from scaffolds.palamedes_agents.tests.test_adapter_and_planner_loop import FakePalamedesClient
from scaffolds.palamedes_agents.tests.test_strategy_llm import VALID_REPORT


class AgentCycleTests(unittest.TestCase):
    def test_real_case_evaluation_contract_has_three_existing_repositories(self):
        dataset_path = SCAFFOLD_ROOT / "evals" / "agent-cycle-cases.json"
        dataset = json.loads(dataset_path.read_text(encoding="utf-8"))

        self.assertEqual(dataset["success_gate"]["minimum_cases"], 3)
        self.assertGreaterEqual(len(dataset["cases"]), 3)
        for case in dataset["cases"]:
            self.assertTrue(Path(case["repository"]).is_dir())
            self.assertTrue(case["required_decision"])

    def test_cycle_observes_decides_persists_and_executes(self):
        client = FakePalamedesClient()
        cycle = AgentCycle(
            PalamedesAdapter(client),
            StaticStrategyProvider(copy.deepcopy(VALID_REPORT)),
        )

        result = cycle.run(
            {
                "action": "evaluate_experience_strategy",
                "payload": {"idea": "AI planning checkpoint"},
                "context": {"session_id": "session-1", "wake_id": "wake-1"},
            }
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["stop_reason"], "cycle_complete")
        self.assertEqual(
            [event["type"] for event in result["events"]],
            [
                "strategy_step",
                "reference_insights_persisted",
                "strategy_action_routes",
                "planner_step",
            ],
        )
        call_names = [item[0] for item in client.calls]
        self.assertIn("capture_evidence_cycle", call_names)
        self.assertIn("update_plan", call_names)

    def test_cycle_stops_when_route_lacks_capability(self):
        report = copy.deepcopy(VALID_REPORT)
        report["next_actions"][0]["target_role"] = "reviewer"
        client = FakePalamedesClient()
        cycle = AgentCycle(
            PalamedesAdapter(client),
            StaticStrategyProvider(report),
            persist_insights=False,
        )

        result = cycle.run({"payload": {"idea": "AI planning checkpoint"}})

        self.assertFalse(result["ok"])
        self.assertEqual(result["stop_reason"], "capability_blocked")
        self.assertFalse(result["events"][-1]["ok"])

    def test_cycle_enforces_action_limit(self):
        report = copy.deepcopy(VALID_REPORT)
        report["next_actions"] = report["next_actions"] * 2
        client = FakePalamedesClient()
        cycle = AgentCycle(
            PalamedesAdapter(client),
            StaticStrategyProvider(report),
            max_actions=1,
            persist_insights=False,
        )

        result = cycle.run({"payload": {"idea": "AI planning checkpoint"}})

        self.assertFalse(result["ok"])
        self.assertEqual(result["stop_reason"], "action_limit")


if __name__ == "__main__":
    unittest.main()
