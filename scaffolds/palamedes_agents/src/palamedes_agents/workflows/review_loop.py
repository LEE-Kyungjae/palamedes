#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Any, Dict

from palamedes_agents.adapters.palamedes_adapter import PalamedesAdapter, summarize_cycle_result
from palamedes_agents.runtime.decision_gate import evaluate_cycle_gate, evaluate_snapshot_gate
from palamedes_agents.runtime.host_events import build_success_event
from palamedes_agents.runtime.policies import apply_idempotency_policy
from palamedes_agents.skills.registry import build_runtime_session


@dataclass
class ReviewLoop:
    adapter: PalamedesAdapter
    role: str = "reviewer"

    def request_once(self, payload: Dict[str, Any], *, session_id: str = "", step_id: str = "") -> Dict[str, Any]:
        before = self.adapter.snapshot()
        session = build_runtime_session(self.role)
        prepared_payload = apply_idempotency_policy(
            "request_review",
            payload,
            session_id=session_id,
            step_id=step_id,
        )
        preflight = evaluate_snapshot_gate(before)
        result = self.adapter.request_review(prepared_payload)
        summary = summarize_cycle_result(result)
        after = result.get("post_cycle", {})
        gate = evaluate_cycle_gate(before, result)
        return {
            "role": self.role,
            "session": session,
            "before": before,
            "preflight": preflight,
            "payload": prepared_payload,
            "result": result,
            "summary": summary,
            "after": after,
            "gate": gate,
        }

    def resolve_once(self, payload: Dict[str, Any], *, session_id: str = "", step_id: str = "") -> Dict[str, Any]:
        before = self.adapter.snapshot()
        session = build_runtime_session(self.role)
        prepared_payload = apply_idempotency_policy(
            "resolve_review",
            payload,
            session_id=session_id,
            step_id=step_id,
        )
        preflight = evaluate_snapshot_gate(before)
        result = self.adapter.resolve_review(prepared_payload)
        summary = summarize_cycle_result(result)
        after = result.get("post_cycle", {})
        gate = evaluate_cycle_gate(before, result)
        return {
            "role": self.role,
            "session": session,
            "before": before,
            "preflight": preflight,
            "payload": prepared_payload,
            "result": result,
            "summary": summary,
            "after": after,
            "gate": gate,
        }

    def request_event(self, payload: Dict[str, Any], *, session_id: str = "", step_id: str = "") -> Dict[str, Any]:
        return build_success_event(
            "review_requested",
            self.request_once(payload, session_id=session_id, step_id=step_id),
        )

    def resolve_event(self, payload: Dict[str, Any], *, session_id: str = "", step_id: str = "") -> Dict[str, Any]:
        return build_success_event(
            "review_resolved",
            self.resolve_once(payload, session_id=session_id, step_id=step_id),
        )
