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
    team_store: Any = None

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
        if self.team_store is not None:
            agent_id = str(context.get("agent_id", "")).strip()
            if not agent_id:
                raise ValueError("team-enabled cycle requires context.agent_id")
            observation = context.get("observation")
            if observation:
                if not isinstance(observation, dict):
                    raise ValueError("context.observation must be an object")
                prepared_observation = dict(observation)
                prepared_observation.setdefault("agent_id", agent_id)
                prepared_observation.setdefault(
                    "agent_role", str(context.get("agent_role", "strategist")).strip()
                )
                recorded = self.team_store.record_observation(prepared_observation)
                events.append(
                    {
                        "ok": True,
                        "type": "team_observation_recorded",
                        "role": prepared_observation["agent_role"],
                        "result": recorded,
                        "error": None,
                    }
                )
            mission_id = str(context.get("mission_id", "")).strip()
            if mission_id:
                claimed = self.team_store.claim_mission(mission_id, agent_id)
                events.append(
                    {
                        "ok": True,
                        "type": "team_mission_claimed",
                        "role": str(context.get("agent_role", "strategist")).strip(),
                        "result": claimed,
                        "error": None,
                    }
                )
            payload = dict(payload)
            payload["team_cognition"] = self.team_store.context_snapshot()

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
