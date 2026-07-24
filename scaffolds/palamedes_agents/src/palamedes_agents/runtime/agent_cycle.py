#!/usr/bin/env python3
"""Bounded observe-decide-act-learn cycle for the Palamedes strategist."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from palamedes_agents.adapters.palamedes_adapter import PalamedesAdapter
from palamedes_agents.insight_persistence import persist_reference_insights
from palamedes_agents.runtime.host_step import HostStep
from palamedes_agents.strategy_routes import route_strategy_next_actions


STRATEGY_ACTIONS = {
    "evaluate_experience_strategy",
    "generate_creative_directions",
    "analyze_outcome_learning",
}


@dataclass
class AgentCycle:
    """Run one bounded strategist cycle without turning the kernel into a runtime."""

    adapter: PalamedesAdapter
    strategy_provider: Any
    max_actions: int = 5
    persist_insights: bool = True

    def _validate(self, wake: Dict[str, Any]) -> tuple[str, Dict[str, Any], Dict[str, Any]]:
        if not isinstance(wake, dict):
            raise ValueError("wake must be an object")
        action = str(wake.get("action", "evaluate_experience_strategy")).strip()
        if action not in STRATEGY_ACTIONS:
            raise ValueError(f"unsupported strategy wake action: {action}")
        payload = wake.get("payload", {}) or {}
        context = wake.get("context", {}) or {}
        if not isinstance(payload, dict):
            raise ValueError("wake.payload must be an object")
        if not isinstance(context, dict):
            raise ValueError("wake.context must be an object")
        return action, dict(payload), dict(context)

    def run(self, wake: Dict[str, Any]) -> Dict[str, Any]:
        action, payload, context = self._validate(wake)
        session_id = str(context.get("session_id", "")).strip()
        wake_id = str(context.get("wake_id", "")).strip()
        events: List[Dict[str, Any]] = []

        strategy_event = HostStep(
            self.adapter,
            role="strategist",
            strategy_provider=self.strategy_provider,
        ).run_event(
            {
                "action": action,
                "payload": payload,
                "options": {"session_id": session_id, "step_id": wake_id},
            }
        )
        events.append(strategy_event)
        if not strategy_event.get("ok"):
            return self._result(action, context, events, "strategy_failed")

        report = strategy_event.get("result", {}).get("strategy", {})
        if not isinstance(report, dict):
            return self._result(action, context, events, "invalid_strategy_result")

        if self.persist_insights and report.get("reference_insights"):
            try:
                persisted = persist_reference_insights(self.adapter, report)
                events.append(
                    {
                        "ok": True,
                        "type": persisted["type"],
                        "role": "researcher",
                        "result": persisted,
                        "error": None,
                    }
                )
            except ValueError as exc:
                events.append(
                    {
                        "ok": False,
                        "type": "reference_insight_persistence_failed",
                        "role": "researcher",
                        "result": {},
                        "error": {"type": "invalid_insight", "message": str(exc), "retryable": False},
                    }
                )
                return self._result(action, context, events, "learning_failed")

        routes = route_strategy_next_actions(report)
        events.append(routes)
        if not routes["ok"]:
            return self._result(action, context, events, "capability_blocked")

        executed = 0
        for route in routes["routes"]:
            if executed >= self.max_actions:
                return self._result(action, context, events, "action_limit")
            step_event = HostStep(
                self.adapter,
                role=route["target_role"],
                strategy_provider=self.strategy_provider,
            ).run_event(
                {
                    "action": route["action"],
                    "payload": route["payload"],
                    "options": {
                        "session_id": session_id,
                        "step_id": f"{wake_id or 'wake'}:{route['index']}",
                    },
                }
            )
            events.append(step_event)
            executed += 1
            if not step_event.get("ok"):
                return self._result(action, context, events, "action_failed")
            if route["action"] == "request_review":
                return self._result(action, context, events, "awaiting_human_review")

        return self._result(action, context, events, "cycle_complete")

    def _result(
        self,
        action: str,
        context: Dict[str, Any],
        events: List[Dict[str, Any]],
        stop_reason: str,
    ) -> Dict[str, Any]:
        return {
            "ok": stop_reason == "cycle_complete",
            "type": "agent_cycle",
            "action": action,
            "context": context,
            "stop_reason": stop_reason,
            "events": events,
            "post_cycle": self.adapter.snapshot(),
        }
