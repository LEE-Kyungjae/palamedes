import unittest

from palamedes_planning_handoff_proof import validate_execution_plan


class PlanningHandoffProofTests(unittest.TestCase):
    def _plan(self):
        return {
            "plan_summary": "A bounded plan.",
            "user_outcome": "One verified user loop.",
            "assumptions": [{
                "statement": "Hardware access is unresolved.",
                "status": "unresolved",
                "evidence_or_probe": "Inventory the target machine.",
            }],
            "workstreams": [{
                "workstream_id": "gate", "objective": "Verify prerequisites.",
                "inputs": ["mission"], "outputs": ["manifest"], "dependencies": [],
            }],
            "sequence": [{
                "phase": "feasibility", "workstream_ids": ["gate"],
                "entry_gate": "Mission is frozen.", "exit_gate": "Prerequisites pass.",
            }],
            "acceptance_tests": ["Manifest covers every prerequisite."],
            "risk_controls": ["Stop when a prerequisite has no bounded path."],
            "unresolved_questions": ["Who owns the target machine?"],
            "first_authorized_action": "Create the read-only prerequisite inventory.",
            "execution_authority_issued": False,
        }

    def test_validates_bounded_planner_handoff(self):
        self.assertEqual(validate_execution_plan(self._plan()), [])

    def test_rejects_unknown_workstream_and_execution_authority(self):
        plan = self._plan()
        plan["sequence"][0]["workstream_ids"] = ["missing"]
        plan["execution_authority_issued"] = True
        errors = validate_execution_plan(plan)
        self.assertIn("sequence[0].workstream_ids must reference declared workstreams", errors)
        self.assertIn("execution_authority_issued must be false", errors)


if __name__ == "__main__":
    unittest.main()
