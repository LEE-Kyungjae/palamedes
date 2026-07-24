#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List, Tuple


SCAFFOLD_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = SCAFFOLD_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from palamedes_agents.adapters.palamedes_adapter import PalamedesAdapter, summarize_cycle_result
from palamedes_agents.runtime.decision_gate import evaluate_cycle_gate, evaluate_snapshot_gate
from palamedes_agents.runtime.host_events import build_error_event, build_success_event, summarize_for_host
from palamedes_agents.runtime.host_step import HostStep, action_contract, required_capabilities_for_action, role_has_action_capabilities
from palamedes_agents.runtime.policies import apply_idempotency_policy, build_idempotency_key, should_retry_stale_conflict
from palamedes_agents.strategy_llm import StaticStrategyProvider
from palamedes_agents.workflows.planner_loop import PlannerLoop
from palamedes_agents.workflows.research_loop import ResearchLoop
from palamedes_agents.workflows.review_loop import ReviewLoop
from palamedes_agents.workflows.strategy_loop import StrategyLoop, evaluate_strategy_payload, validate_strategy_report_shape


class FakePalamedesClient:
    def __init__(self, *, before_score: float = 0.8, after_score: float = 0.92, health_status: str = "ok", qa_result: str = "PASS") -> None:
        self.calls: List[Tuple[str, Dict[str, Any]]] = []
        self.goal = "initial goal"
        self.before_score = before_score
        self.after_score = after_score
        self.health_status = health_status
        self.qa_result = qa_result

    def get_cycle(self, *, history_limit: int = 10) -> Dict[str, Any]:
        self.calls.append(("get_cycle", {"history_limit": history_limit}))
        return {
            "plan": {"goal": self.goal},
            "qa": {"result": self.qa_result, "score": self.before_score},
            "health": {"status": self.health_status},
            "history_limit": history_limit,
            "fingerprint": "fp-before",
        }

    def apply_and_get_cycle(
        self,
        operation: str,
        payload: Dict[str, Any],
        *,
        history_limit: int = 10,
        expected_fingerprint: str = "",
        require_healthy: bool = False,
    ) -> Dict[str, Any]:
        self.calls.append(
            (
                operation,
                {
                    "payload": dict(payload),
                    "history_limit": history_limit,
                    "expected_fingerprint": expected_fingerprint,
                    "require_healthy": require_healthy,
                },
            )
        )
        if operation == "update_plan":
            self.goal = str(payload.get("goal", self.goal))
        return {
            "operation": operation,
            "changed_fields": sorted(payload.keys()),
            "post_fingerprint": "fp-after",
            "retried": False,
            "post_cycle": {
                "plan": {"goal": self.goal},
                "qa": {"result": self.qa_result, "score": self.after_score},
                "health": {"status": self.health_status},
            },
        }

    def capture_evidence_cycle(
        self,
        evidence_payload: Dict[str, Any],
        *,
        replan_payload=None,
        history_limit: int = 10,
        idempotency_key: str = "",
        expected_fingerprint: str = "",
        allow_retry: bool = False,
        require_healthy: bool = False,
    ) -> Dict[str, Any]:
        payload = dict(evidence_payload)
        if idempotency_key:
            payload["idempotency_key"] = idempotency_key
        self.calls.append(
            (
                "capture_evidence_cycle",
                {
                    "payload": payload,
                    "replan_payload": dict(replan_payload or {}),
                    "history_limit": history_limit,
                    "expected_fingerprint": expected_fingerprint,
                    "allow_retry": allow_retry,
                    "require_healthy": require_healthy,
                },
            )
        )
        return {
            "operation": "capture_evidence_cycle",
            "changed_fields": ["evidence"],
            "post_fingerprint": "fp-after",
            "retried": False,
            "post_cycle": {
                "plan": {"goal": self.goal},
                "qa": {"result": self.qa_result, "score": self.after_score},
                "health": {"status": self.health_status},
            },
        }

    def execute_tool(self, tool_name: str, payload: Dict[str, Any], *, expected_fingerprint: str = "") -> Dict[str, Any]:
        self.calls.append(
            (
                tool_name,
                {
                    "payload": dict(payload),
                    "expected_fingerprint": expected_fingerprint,
                },
            )
        )
        return {
            "ok": True,
            "tool_name": tool_name,
            "result_type": "reference_discovery",
            "fingerprint": "fp-after",
            "result": {"applied": bool(payload.get("apply", False))},
        }

    def preview_restore(self, *, previous: bool = False) -> Dict[str, Any]:
        self.calls.append(("preview_restore", {"previous": previous}))
        return {"selected_via": "previous" if previous else "revision_id"}


class PalamedesAgentsAdapterTests(unittest.TestCase):
    def test_adapter_snapshot_and_apply_plan_update_delegate_to_client(self):
        client = FakePalamedesClient()
        adapter = PalamedesAdapter(client, history_limit=7, require_healthy_writes=True)

        before = adapter.snapshot()
        result = adapter.apply_plan_update({"goal": "new goal"})

        self.assertEqual(before["plan"]["goal"], "initial goal")
        self.assertEqual(result["post_cycle"]["plan"]["goal"], "new goal")
        self.assertEqual(
            client.calls,
            [
                ("get_cycle", {"history_limit": 7}),
                (
                    "update_plan",
                    {
                        "payload": {"goal": "new goal"},
                        "history_limit": 7,
                        "expected_fingerprint": "",
                        "require_healthy": True,
                    },
                ),
            ],
        )

    def test_adapter_exposes_review_and_restore_operations(self):
        client = FakePalamedesClient()
        adapter = PalamedesAdapter(client, history_limit=3, require_healthy_writes=False)

        adapter.capture_evidence_cycle({"claim": "signal", "source": "call", "confidence": 70})
        adapter.run_reference_discovery({"question": "Which references matter?", "apply": True})
        adapter.request_review({"scope": "plan", "reason": "Need reviewer"})
        adapter.resolve_review({"request_id": "review-1", "status": "resolved"})
        preview = adapter.preview_restore_previous()
        adapter.restore_previous()

        self.assertEqual(preview["selected_via"], "previous")
        self.assertEqual([item[0] for item in client.calls], ["capture_evidence_cycle", "run_reference_discovery", "get_cycle", "request_review", "resolve_review", "preview_restore", "restore_revision"])
        self.assertTrue(client.calls[0][1]["allow_retry"])

    def test_summarize_cycle_result_extracts_host_facing_fields(self):
        summary = summarize_cycle_result(
            {
                "operation": "update_plan",
                "post_fingerprint": "fp-after",
                "changed_fields": ["goal"],
                "retried": True,
                "post_cycle": {
                    "qa": {"result": "PASS", "score": 0.9},
                    "health": {"status": "ok"},
                },
            }
        )

        self.assertEqual(summary["operation"], "update_plan")
        self.assertEqual(summary["fingerprint"], "fp-after")
        self.assertEqual(summary["qa_result"], "PASS")
        self.assertEqual(summary["health_status"], "ok")
        self.assertTrue(summary["retried"])


class PlannerLoopTests(unittest.TestCase):
    def test_runtime_policies_build_idempotency_keys_and_gate_stale_retry(self):
        key = build_idempotency_key(
            session_id="session-42",
            step_id="research-3",
            operation="capture_evidence_cycle",
        )
        payload = apply_idempotency_policy(
            "request_review",
            {"scope": "plan", "reason": "Need owner"},
            session_id="session-42",
            step_id="review-1",
        )

        self.assertEqual(key, "session-42:research-3:evidence-cycle")
        self.assertEqual(payload["idempotency_key"], "session-42:review-1:review-request")
        self.assertTrue(should_retry_stale_conflict(attempt_count=1, max_attempts=2, error_code="plan_fingerprint_mismatch"))
        self.assertFalse(should_retry_stale_conflict(attempt_count=2, max_attempts=2, error_code="plan_fingerprint_mismatch"))

    def test_host_events_wrap_success_and_error_shapes(self):
        outcome = {
            "role": "planner",
            "session": {"profile": "planner_full"},
            "summary": {
                "operation": "update_plan",
                "fingerprint": "fp-after",
                "changed_fields": ["goal"],
                "qa_result": "PASS",
                "qa_score": 0.9,
                "health_status": "ok",
                "retried": False,
            },
            "gate": {"decision": "continue", "reasons": ["qa_score_improved"]},
            "result": {"operation": "update_plan"},
        }
        summary = summarize_for_host(outcome)
        success = build_success_event("planner_step", outcome)
        error = build_error_event(
            "planner_step_failed",
            role="planner",
            error_type="conflict",
            message="plan fingerprint mismatch",
            retryable=True,
            operation="update_plan",
            step="mutation",
        )

        self.assertEqual(summary["profile"], "planner_full")
        self.assertEqual(success["type"], "planner_step")
        self.assertTrue(success["ok"])
        self.assertEqual(success["summary"]["decision"], "continue")
        self.assertFalse(error["ok"])
        self.assertEqual(error["error"]["type"], "conflict")
        self.assertTrue(error["error"]["retryable"])

    def test_host_step_dispatches_actions_and_enforces_role_capabilities(self):
        contract = action_contract("reviewer")
        client = FakePalamedesClient()
        adapter = PalamedesAdapter(client, history_limit=4, require_healthy_writes=True)
        reviewer_step = HostStep(adapter, role="reviewer")
        planner_step = HostStep(adapter, role="planner")

        requested = reviewer_step.run_event(
            {
                "action": "request_review",
                "payload": {"scope": "plan", "reason": "Need reviewer decision"},
                "options": {"session_id": "session-42", "step_id": "review-1"},
            }
        )
        denied = reviewer_step.run_event(
            {
                "action": "update_plan",
                "payload": {"goal": "should not be allowed"},
            }
        )
        planned = planner_step.run_event(
            {
                "action": "update_plan",
                "payload": {"goal": "allowed planner update"},
            }
        )

        self.assertEqual(contract["profile"], "reviewer_restore")
        self.assertEqual(required_capabilities_for_action("reviewer", "resolve_review"), ["review.resolve"])
        self.assertTrue(role_has_action_capabilities("reviewer", "resolve_review"))
        self.assertFalse(role_has_action_capabilities("reviewer", "update_plan"))
        self.assertTrue(role_has_action_capabilities("researcher", "run_reference_discovery"))
        self.assertTrue(requested["ok"])
        self.assertEqual(requested["type"], "review_requested")
        self.assertFalse(denied["ok"])
        self.assertEqual(denied["error"]["type"], "permission_denied")
        self.assertTrue(planned["ok"])
        self.assertEqual(planned["type"], "planner_step")

    def test_decision_gate_blocks_unhealthy_snapshot_and_routes_critical_failure(self):
        snapshot_block = evaluate_snapshot_gate({"health": {"status": "error"}, "qa": {"result": "PASS", "score": 0.8}})
        cycle_review = evaluate_cycle_gate(
            {"qa": {"score": 0.8}, "health": {"status": "ok"}},
            {"post_cycle": {"qa": {"result": "CRITICAL_FAILURE", "score": 0.4}, "health": {"status": "ok"}}},
        )

        self.assertEqual(snapshot_block["decision"], "block")
        self.assertTrue(snapshot_block["should_block_writes"])
        self.assertEqual(cycle_review["decision"], "review")
        self.assertTrue(cycle_review["should_route_to_reviewer"])

    def test_planner_loop_runs_one_update_with_runtime_session(self):
        client = FakePalamedesClient()
        adapter = PalamedesAdapter(client, history_limit=4, require_healthy_writes=True)
        loop = PlannerLoop(adapter)

        outcome = loop.run_once({"goal": "planner loop goal"})
        event = loop.run_event({"goal": "planner loop goal"})

        self.assertEqual(outcome["role"], "planner")
        self.assertEqual(outcome["session"]["profile"], "planner_full")
        self.assertEqual(outcome["before"]["plan"]["goal"], "initial goal")
        self.assertEqual(outcome["after"]["plan"]["goal"], "planner loop goal")
        self.assertEqual(outcome["preflight"]["decision"], "continue")
        self.assertEqual(outcome["gate"]["decision"], "continue")
        self.assertEqual(outcome["summary"]["qa_result"], "PASS")
        self.assertTrue(event["ok"])
        self.assertEqual(event["type"], "planner_step")
        self.assertEqual(event["summary"]["operation"], "update_plan")
        self.assertEqual(
            [item[0] for item in client.calls],
            ["get_cycle", "update_plan", "get_cycle", "update_plan"],
        )

    def test_planner_loop_routes_to_reviewer_when_qa_score_regresses(self):
        client = FakePalamedesClient(before_score=0.8, after_score=0.5, health_status="ok", qa_result="PASS")
        adapter = PalamedesAdapter(client, history_limit=4, require_healthy_writes=True)
        loop = PlannerLoop(adapter)

        outcome = loop.run_once({"goal": "planner loop regression"})

        self.assertEqual(outcome["gate"]["decision"], "review")
        self.assertIn("qa_score_regressed", outcome["gate"]["reasons"])

    def test_research_loop_runs_capture_evidence_cycle_with_runtime_session(self):
        client = FakePalamedesClient()
        adapter = PalamedesAdapter(client, history_limit=4, require_healthy_writes=True)
        loop = ResearchLoop(adapter)

        outcome = loop.run_once(
            {
                "evidence": {"claim": "Found repeated friction", "source": "interview", "confidence": 72},
                "replan": {"plan_task": "Tighten onboarding hypothesis"},
            },
            session_id="session-42",
            step_id="research-3",
        )
        event = loop.run_event(
            {
                "evidence": {"claim": "Found repeated friction", "source": "interview", "confidence": 72},
                "replan": {"plan_task": "Tighten onboarding hypothesis"},
            },
            session_id="session-42",
            step_id="research-3",
        )

        self.assertEqual(outcome["role"], "researcher")
        self.assertEqual(outcome["session"]["profile"], "researcher_capture")
        self.assertEqual(outcome["gate"]["decision"], "continue")
        self.assertEqual(outcome["payload"]["idempotency_key"], "session-42:research-3:evidence-cycle")
        self.assertEqual(client.calls[1][1]["payload"]["idempotency_key"], "session-42:research-3:evidence-cycle")
        self.assertEqual(outcome["summary"]["operation"], "capture_evidence_cycle")
        self.assertTrue(event["ok"])
        self.assertEqual(event["type"], "research_step")
        self.assertEqual(event["summary"]["operation"], "capture_evidence_cycle")
        self.assertEqual(
            [item[0] for item in client.calls],
            ["get_cycle", "capture_evidence_cycle", "get_cycle", "capture_evidence_cycle"],
        )

    def test_research_loop_runs_reference_discovery_with_runtime_session(self):
        client = FakePalamedesClient()
        adapter = PalamedesAdapter(client, history_limit=4, require_healthy_writes=True)
        loop = ResearchLoop(adapter)

        event = loop.reference_event(
            {
                "question": "Which references prove this idea?",
                "context": "AI planning checkpoint",
                "references": ["failed AI wrappers"],
                "apply": True,
            },
            session_id="session-42",
            step_id="reference-1",
        )

        self.assertTrue(event["ok"])
        self.assertEqual(event["type"], "reference_discovery_step")
        self.assertEqual(event["summary"]["operation"], "run_reference_discovery")
        self.assertIn("reference_discoveries", event["summary"]["changed_fields"])

    def test_review_loop_can_request_and_resolve_with_runtime_session(self):
        client = FakePalamedesClient()
        adapter = PalamedesAdapter(client, history_limit=4, require_healthy_writes=True)
        loop = ReviewLoop(adapter)

        requested = loop.request_once(
            {"scope": "plan", "reason": "Need owner decision"},
            session_id="session-42",
            step_id="review-1",
        )
        resolved = loop.resolve_once(
            {"request_id": "review-1", "status": "resolved"},
            session_id="session-42",
            step_id="review-2",
        )
        requested_event = loop.request_event(
            {"scope": "plan", "reason": "Need owner decision"},
            session_id="session-42",
            step_id="review-1",
        )
        resolved_event = loop.resolve_event(
            {"request_id": "review-1", "status": "resolved"},
            session_id="session-42",
            step_id="review-2",
        )

        self.assertEqual(requested["role"], "reviewer")
        self.assertEqual(requested["session"]["profile"], "reviewer_restore")
        self.assertEqual(requested["gate"]["decision"], "continue")
        self.assertEqual(requested["payload"]["idempotency_key"], "session-42:review-1:review-request")
        self.assertEqual(requested["summary"]["operation"], "request_review")
        self.assertEqual(resolved["payload"]["idempotency_key"], "session-42:review-2:review-resolve")
        self.assertEqual(resolved["summary"]["operation"], "resolve_review")
        self.assertEqual(requested_event["type"], "review_requested")
        self.assertEqual(resolved_event["type"], "review_resolved")
        self.assertEqual(
            [item[0] for item in client.calls],
            [
                "get_cycle",
                "request_review",
                "get_cycle",
                "resolve_review",
                "get_cycle",
                "request_review",
                "get_cycle",
                "resolve_review",
            ],
        )

    def test_strategy_loop_flags_generic_ideas_before_build(self):
        client = FakePalamedesClient()
        adapter = PalamedesAdapter(client, history_limit=4, require_healthy_writes=True)
        report = evaluate_strategy_payload(
            {
                "idea": "AI productivity dashboard and assistant",
                "target_user": "builders",
                "solution": "dashboard",
            },
            {"goal": "Build another AI tool"},
        )
        loop = StrategyLoop(adapter, provider=StaticStrategyProvider(report))
        event = loop.run_event(
            {
                "idea": "AI productivity dashboard and assistant",
                "target_user": "builders",
                "solution": "dashboard",
            }
        )

        self.assertIn("dashboard", report["generic_patterns"])
        self.assertIn(report["decision"], {"revise_before_build", "stop_and_research"})
        self.assertTrue(event["ok"])
        self.assertEqual(event["type"], "strategy_step")
        self.assertEqual(event["summary"]["operation"], "evaluate_experience_strategy")
        self.assertIn("generic_llm_service_pattern", event["gate"]["reasons"])
        self.assertIn("research_questions", event["result"]["strategy"])
        self.assertIn("positioning_rewrite", event["result"]["strategy"])
        self.assertIn("monetization_moment", event["result"]["strategy"])
        self.assertIn("next_actions", event["result"]["strategy"])
        self.assertEqual(event["result"]["strategy"]["next_actions"][0]["action"], "run_reference_discovery")
        self.assertEqual(event["result"]["strategy"]["next_actions"][0]["target_role"], "researcher")
        self.assertEqual(event["result"]["strategy"]["next_actions"][0]["priority"], "high")
        self.assertEqual(validate_strategy_report_shape(event["result"]["strategy"]), [])

    def test_strategy_loop_scores_experience_and_emotional_demand(self):
        report = evaluate_strategy_payload(
            {
                "idea": "Pre-build decision checkpoint for AI builders",
                "target_user": "solo AI builders",
                "problem": "They waste weeks building generic services before validating demand.",
                "current_alternative": "They ask coding agents to build immediately.",
                "pain_frequency": "Every new product idea and weekly build cycle.",
                "solution": "Challenge problem, desire, loop, monetization, and differentiation before build.",
                "desire": "make more money and avoid wasted work",
                "emotion": "anxiety, greed, control",
                "trigger": "before asking an agent to build",
                "action": "submit an idea for strategic attack",
                "reward": "clear continue, revise, or stop decision",
                "monetization": "paid planning intelligence",
                "repeat_loop": "use for each new build idea and weekly review",
                "references": ["failed AI wrappers", "successful retention loops"],
                "behavior_signals": ["builders repeatedly make similar AI dashboards"],
                "differentiation": "anti-generic planning intelligence",
            },
            {},
        )

        self.assertGreaterEqual(report["overall_score"], 80)
        self.assertIn("fear/control", report["emotion_drivers"])
        self.assertIn("upside/greed", report["emotion_drivers"])
        self.assertIn("Position it", report["positioning_rewrite"])
        self.assertIn("payment moment", report["monetization_moment"])
        self.assertTrue(report["next_actions"])
        self.assertEqual(validate_strategy_report_shape(report), [])

    def test_strategy_loop_surfaces_negative_emotion_risk_boundary(self):
        report = evaluate_strategy_payload(
            {
                "idea": "Competitive game item store",
                "target_user": "competitive players",
                "problem": "Players want revenge after losing status to rivals.",
                "current_alternative": "They grind manually or leave the match.",
                "pain_frequency": "Every time a rival attacks them.",
                "solution": "Sell revenge boosts after an attack.",
                "desire": "recover status",
                "emotion": "anger, revenge, envy",
                "trigger": "after a rival attack",
                "action": "buy a revenge boost",
                "reward": "recover status immediately",
                "monetization": "paid revenge items",
                "repeat_loop": "rival attacks create repeated revenge moments",
                "references": ["competitive game economies"],
                "behavior_signals": ["players spend after emotional loss"],
                "differentiation": "emotion-triggered monetization",
            },
            {},
        )

        self.assertIn("toxic_conflict", report["risk_boundaries"])
        self.assertIn("status_anxiety", report["risk_boundaries"])
        self.assertEqual(report["decision"], "review_risk_boundary")
        self.assertIn("risk_boundary_needs_review", report["risks"])
        self.assertEqual(report["next_actions"][0]["action"], "request_review")
        self.assertEqual(report["next_actions"][0]["target_role"], "reviewer")


if __name__ == "__main__":
    unittest.main()
