import json
import tempfile
import unittest
from pathlib import Path

import palamedes
from palamedes_planning_brief import generate_planning_brief, write_generation


def direction_brief(note: str):
    return {
        "planning_brief_id": "model-placeholder",
        "mission_contract_id": "model-placeholder",
        "mission_contract_fingerprint": "model-placeholder",
        "planning_brief_fingerprint": "model-placeholder",
        "plan_scale": "service",
        "planning_stage": "direction",
        "outcome": f"Establish the next service direction: {note}",
        "beneficiary": "A user seeking a coherent realtime character experience.",
        "value_proposition": "Turn subsystem capability into a credible experience.",
        "resolution_basis": {
            "uncertainty": "high", "irreversibility": "medium",
            "coordination_cost": "high", "harm_potential": "low",
            "resolution_rationale": "The concept is not yet approved.",
        },
        "in_scope": ["select one experience direction"],
        "out_of_scope": ["implementation"],
        "success_signals": ["one concept is ready for comparison"],
        "stop_conditions": ["beneficiary evidence contradicts the direction"],
        "knowledge_ledger": [{
            "item_id": "unknown-user-fit", "status": "unresolved",
            "statement": "The preferred user loop is not verified.", "evidence_ids": [],
            "validation_probe": "Compare two bounded user experience concepts.",
        }],
        "experience_contract": None,
        "alternatives": [],
        "components": [],
        "external_dependencies": [],
        "effects": [],
        "phases": [],
        "decision_gates": [{
            "gate_id": "concept-ready", "question": "Is a concept evidence-backed?",
            "evidence_required": "A bounded concept comparison.",
            "on_pass": "Advance to concept planning.", "on_fail": "Return to discovery.",
            "authorizes_irreversible_effects": False,
        }],
        "resource_envelope": None,
        "execution_authority_issued": False,
        "mission_semantics_preserved": True,
        "planning_rationale": "Keep implementation open while making the decision boundary explicit.",
    }


class FakeProvider:
    provider_name = "fake"
    model = "fake-model"

    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.calls = 0
        self.last_usage = None

    def stream(self, _messages):
        payload = self.payloads[self.calls]
        self.calls += 1
        self.last_usage = {"input_tokens": 10, "output_tokens": 5}
        yield json.dumps(payload)


class PalamedesPlanningBriefTests(unittest.TestCase):
    def test_generation_uses_architect_and_adversarial_revision(self):
        draft = direction_brief("draft")
        revised = direction_brief("revised")
        draft["plan_scale"] = "feature"
        revised["planning_stage"] = "concept"
        provider = FakeProvider([draft, revised])
        result = generate_planning_brief(
            {"mission_id": "mission-test", "contract_fingerprint": "sha256:mission", "mission": "Choose a realtime direction."},
            provider,
            plan_scale="service",
            planning_stage="direction",
        )
        self.assertEqual(provider.calls, 2)
        self.assertTrue(result["final_validation"]["valid"])
        self.assertEqual(result["planning_brief"]["mission_contract_id"], "mission-test")
        self.assertEqual(result["planning_brief"]["mission_contract_fingerprint"], "sha256:mission")
        self.assertEqual(result["planning_brief"]["plan_scale"], "service")
        self.assertEqual(result["planning_brief"]["planning_stage"], "direction")
        self.assertFalse(result["execution_authority_issued"])

    def test_invalid_revision_is_not_accepted(self):
        invalid = direction_brief("invalid")
        invalid["decision_gates"] = []
        provider = FakeProvider([direction_brief("draft"), invalid])
        with self.assertRaisesRegex(ValueError, "failed deterministic validation"):
            generate_planning_brief({"mission": "Choose."}, provider, planning_stage="direction")

    def test_write_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "brief.json"
            path.write_text("owned", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "output already exists"):
                write_generation(path, {"planning_brief": {}})
            self.assertEqual(path.read_text(encoding="utf-8"), "owned")

    def test_parser_exposes_planning_brief_without_changing_existing_commands(self):
        parser = palamedes.build_parser()
        args = parser.parse_args([
            "planning-brief", "--mission", "mission.json", "--output", "brief.json",
            "--plan-scale", "service", "--planning-stage", "approval",
        ])
        self.assertEqual(args.func, palamedes.cmd_planning_brief)
        self.assertEqual(args.provider, "codex")


if __name__ == "__main__":
    unittest.main()
