#!/usr/bin/env python3
import json
import copy
import sys
import unittest
from pathlib import Path


SCAFFOLD_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = SCAFFOLD_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from palamedes_agents.strategy_llm import (
    OpenAIResponsesStrategyProvider,
    OpenRouterChatStrategyProvider,
    StaticStrategyProvider,
    run_strategy_llm,
)


VALID_REPORT = {
    "overall_score": 82,
    "decision": "revise_before_build",
    "axes": {
        "problem_solution": 80,
        "desire_emotion": 90,
        "experience_loop": 75,
        "monetization_trigger": 85,
        "anti_generic": 80,
        "reference_insight": 80,
    },
    "emotion_drivers": ["fear/control", "upside/greed"],
    "risk_boundaries": [],
    "generic_patterns": ["dashboard"],
    "missing_fields": {"reference_insight": []},
    "risks": ["generic_llm_service_pattern"],
    "recommendations": ["Sharpen the wedge before build."],
    "research_questions": ["Which behavior data proves this wedge?"],
    "next_actions": [
        {
            "target_role": "planner",
            "action": "update_plan",
            "priority": "medium",
            "reason": "Sharpen positioning before build.",
            "payload": {"selected_option": "Reframe as pre-build product intelligence."},
        }
    ],
    "positioning_rewrite": "Reframe as pre-build product intelligence.",
    "monetization_moment": "Charge when the user avoids wasted build time.",
    "reference_insights": [
        {
            "source": "failed AI wrapper launches",
            "reference_ids": ["failed-ai-wrapper-launches"],
            "source_urls": ["https://example.com/failed-ai-wrapper-launches"],
            "evidence_quotes": ["Builders shipped before proving repeated demand."],
            "observed_behavior": "Builders ship similar tools before proving demand.",
            "emotion_driver": "fear/control",
            "monetization_moment": "Before expensive build time starts.",
            "repeat_loop": "Every new idea goes through the gate.",
            "transferable_principle": "Convert pre-build anxiety into a paid decision checkpoint.",
            "applied_to_plan": "Make the product a strategy gate, not a dashboard.",
            "transfer_assumptions": ["Solo builders experience meaningful pre-build uncertainty."],
            "disconfirming_signal": "Builders proceed at the same rate after receiving the checkpoint.",
            "confidence": 78,
        }
    ],
    "creative_directions": [
        {
            "name": "Pre-build Strategy Gate",
            "target_user": "solo AI builders",
            "problem": "They cannot tell generic AI ideas from emotionally demanded services.",
            "experience_loop": "Idea trigger, pressure test, sharper direction, repeat for every build.",
            "emotional_wedge": "anxiety relief and control",
            "monetization_trigger": "The moment before coding begins.",
            "reference_basis": "failed AI wrapper launches",
            "why_not_generic": "It kills weak build requests instead of generating another app shell.",
        }
    ],
    "personal_profile_updates": {
        "repeated_biases": ["starts from solution before behavior evidence"],
        "weak_axes": ["reference_insight"],
        "overused_solution_patterns": ["dashboard"],
        "recommended_next_prompts": ["Bring three behavior references before asking for a build."],
    },
    "project_context": {
        "entry_mode": "new_project",
        "stage": "pre-build",
        "existing_artifacts_used": [],
        "mid_project_risks": [],
    },
    "outcome_learning": {
        "observed_outcomes": ["builders ask for pre-build checks"],
        "interpretation": ["Avoided build waste is the strongest early signal."],
        "plan_adjustments": ["Keep strategy gate before execution."],
        "next_evidence": ["Measure repeat use across idea and pivot cycles."],
        "profile_implications": ["Watch for solution-first planning."],
    },
}


class PalamedesStrategyLLMTests(unittest.TestCase):
    def test_run_strategy_llm_validates_provider_report(self):
        result = run_strategy_llm(
            StaticStrategyProvider(VALID_REPORT),
            payload={"idea": "AI planning checkpoint"},
            snapshot={"plan": {"goal": "Improve product strategy"}, "qa": {"result": "PASS"}, "health": {"status": "ok"}},
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["type"], "strategy_llm_report")
        self.assertEqual(result["prompt"]["schema_title"], "PalamedesStrategyReport")
        self.assertEqual(result["report"]["decision"], "revise_before_build")

    def test_openai_provider_uses_responses_json_schema(self):
        class FakeResponses:
            def __init__(self) -> None:
                self.calls = []

            def create(self, **kwargs):
                self.calls.append(kwargs)

                class Response:
                    output_text = json.dumps(VALID_REPORT)

                return Response()

        class FakeClient:
            def __init__(self) -> None:
                self.responses = FakeResponses()

        client = FakeClient()
        provider = OpenAIResponsesStrategyProvider(model="test-model", client=client)
        report = provider.complete_json(
            messages=[{"role": "system", "content": "system"}, {"role": "user", "content": "user"}],
            schema={"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object"},
        )

        self.assertEqual(report["decision"], "revise_before_build")
        call = client.responses.calls[0]
        self.assertEqual(call["model"], "test-model")
        self.assertEqual(call["text"]["format"]["type"], "json_schema")
        self.assertTrue(call["text"]["format"]["strict"])
        self.assertNotIn("$schema", call["text"]["format"]["schema"])

    def test_openrouter_provider_uses_chat_completions_json_schema(self):
        class FakeCompletions:
            def __init__(self) -> None:
                self.calls = []

            def create(self, **kwargs):
                self.calls.append(kwargs)
                return {"choices": [{"message": {"content": json.dumps(VALID_REPORT)}}]}

        class FakeClient:
            def __init__(self) -> None:
                self.chat = type("Chat", (), {"completions": FakeCompletions()})()

        client = FakeClient()
        provider = OpenRouterChatStrategyProvider(model="vendor/test-model", client=client)
        report = provider.complete_json(
            messages=[{"role": "system", "content": "system"}, {"role": "user", "content": "user"}],
            schema={"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object"},
        )

        self.assertEqual(report["decision"], "revise_before_build")
        call = client.chat.completions.calls[0]
        self.assertEqual(call["model"], "vendor/test-model")
        self.assertEqual(call["response_format"]["type"], "json_schema")
        self.assertNotIn("$schema", call["response_format"]["json_schema"]["schema"])

    def test_run_strategy_llm_rejects_invalid_provider_report(self):
        with self.assertRaises(ValueError) as ctx:
            run_strategy_llm(
                StaticStrategyProvider({"decision": "continue"}),
                payload={"idea": "weak"},
                snapshot={},
            )

        self.assertIn("invalid strategy report", str(ctx.exception))

    def test_run_strategy_llm_enforces_insufficient_retrieval_gate(self):
        report = copy.deepcopy(VALID_REPORT)
        report["decision"] = "continue"
        with self.assertRaises(ValueError) as ctx:
            run_strategy_llm(
                StaticStrategyProvider(report),
                payload={
                    "idea": "generic product idea",
                    "reference_corpus": [
                        {
                            "reference_id": "thin-ref",
                            "source": "Thin reference",
                            "source_type": "failure_case",
                            "problem": "generic product idea",
                        }
                    ],
                },
                snapshot={},
            )

        self.assertIn("requires decision=stop_and_research", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
