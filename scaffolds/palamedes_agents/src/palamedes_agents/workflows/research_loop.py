#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Any, Dict

from palamedes_agents.adapters.palamedes_adapter import PalamedesAdapter, summarize_cycle_result
from palamedes_agents.runtime.decision_gate import evaluate_cycle_gate, evaluate_snapshot_gate
from palamedes_agents.runtime.host_events import build_success_event
from palamedes_agents.runtime.policies import apply_idempotency_policy
from palamedes_agents.skills.registry import build_runtime_session


@dataclass
class ResearchLoop:
    adapter: PalamedesAdapter
    role: str = "researcher"

    def run_once(self, payload: Dict[str, Any], *, session_id: str = "", step_id: str = "") -> Dict[str, Any]:
        before = self.adapter.snapshot()
        session = build_runtime_session(self.role)
        prepared_payload = apply_idempotency_policy(
            "capture_evidence_cycle",
            payload,
            session_id=session_id,
            step_id=step_id,
        )
        preflight = evaluate_snapshot_gate(before)
        result = self.adapter.capture_evidence_cycle(prepared_payload)
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

    def run_event(self, payload: Dict[str, Any], *, session_id: str = "", step_id: str = "") -> Dict[str, Any]:
        return build_success_event(
            "research_step",
            self.run_once(payload, session_id=session_id, step_id=step_id),
        )

    def reference_once(self, payload: Dict[str, Any], *, session_id: str = "", step_id: str = "") -> Dict[str, Any]:
        before = self.adapter.snapshot()
        session = build_runtime_session(self.role)
        preflight = evaluate_snapshot_gate(before)
        result = self.adapter.run_reference_discovery(dict(payload))
        summary = summarize_cycle_result(result)
        after = result.get("post_cycle", {})
        gate = evaluate_cycle_gate(before, result)
        return {
            "role": self.role,
            "session": session,
            "before": before,
            "preflight": preflight,
            "payload": dict(payload),
            "result": result,
            "summary": summary,
            "after": after,
            "gate": gate,
        }

    def reference_event(self, payload: Dict[str, Any], *, session_id: str = "", step_id: str = "") -> Dict[str, Any]:
        return build_success_event(
            "reference_discovery_step",
            self.reference_once(payload, session_id=session_id, step_id=step_id),
        )
