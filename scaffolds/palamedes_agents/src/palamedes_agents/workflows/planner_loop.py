#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Any, Dict

from palamedes_agents.adapters.palamedes_adapter import PalamedesAdapter, summarize_cycle_result
from palamedes_agents.runtime.decision_gate import evaluate_cycle_gate, evaluate_snapshot_gate
from palamedes_agents.runtime.host_events import build_success_event
from palamedes_agents.skills.registry import build_runtime_session


@dataclass
class PlannerLoop:
    adapter: PalamedesAdapter
    role: str = "planner"

    def run_once(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        before = self.adapter.snapshot()
        session = build_runtime_session(self.role)
        preflight = evaluate_snapshot_gate(before)
        result = self.adapter.apply_plan_update(payload)
        summary = summarize_cycle_result(result)
        after = result.get("post_cycle", {})
        gate = evaluate_cycle_gate(before, result)
        return {
            "role": self.role,
            "session": session,
            "before": before,
            "preflight": preflight,
            "result": result,
            "summary": summary,
            "after": after,
            "gate": gate,
        }

    def run_event(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return build_success_event("planner_step", self.run_once(payload))
