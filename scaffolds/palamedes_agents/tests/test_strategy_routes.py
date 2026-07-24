#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path


SCAFFOLD_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = SCAFFOLD_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from palamedes_agents.strategy_routes import route_strategy_next_actions
from scaffolds.palamedes_agents.tests.test_strategy_llm import VALID_REPORT


class PalamedesStrategyRouteTests(unittest.TestCase):
    def test_route_strategy_next_actions_accepts_capable_target_role(self):
        result = route_strategy_next_actions(VALID_REPORT)

        self.assertTrue(result["ok"])
        self.assertEqual(result["type"], "strategy_action_routes")
        self.assertEqual(result["routes"][0]["target_role"], "planner")
        self.assertEqual(result["routes"][0]["action"], "update_plan")
        self.assertTrue(result["routes"][0]["executable"])

    def test_route_strategy_next_actions_blocks_incapable_target_role(self):
        report = dict(VALID_REPORT)
        action = dict(VALID_REPORT["next_actions"][0])
        action["target_role"] = "reviewer"
        action["action"] = "update_plan"
        report["next_actions"] = [action]

        result = route_strategy_next_actions(report)

        self.assertFalse(result["ok"])
        self.assertFalse(result["routes"][0]["executable"])
        self.assertEqual(result["routes"][0]["blocker"], "target_role_lacks_action_capability")


if __name__ == "__main__":
    unittest.main()
