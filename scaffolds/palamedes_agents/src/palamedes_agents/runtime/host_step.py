#!/usr/bin/env python3
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from palamedes_agents.adapters.palamedes_adapter import PalamedesAdapter, summarize_cycle_result
from palamedes_agents.runtime.decision_gate import evaluate_cycle_gate, evaluate_snapshot_gate
from palamedes_agents.runtime.host_events import build_error_event, build_success_event
from palamedes_agents.workflows.planner_loop import PlannerLoop
from palamedes_agents.workflows.research_loop import ResearchLoop
from palamedes_agents.workflows.review_loop import ReviewLoop
from palamedes_agents.workflows.strategy_loop import StrategyLoop


CONTRACT_PATH = Path(__file__).resolve().parents[1] / "contracts" / "host-action-contract.json"


def load_host_action_contract() -> Dict[str, Any]:
    with CONTRACT_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("host action contract must be a JSON object")
    return payload


def action_contract(role: str) -> Dict[str, Any]:
    payload = load_host_action_contract()
    role_profiles = payload.get("role_profiles", {})
    profiles = payload.get("profiles", {})
    actions = payload.get("actions", [])
    if not isinstance(role_profiles, dict) or not isinstance(profiles, dict) or not isinstance(actions, list):
        raise ValueError("invalid host action contract")
    profile_name = str(role_profiles.get(role, "")).strip()
    if not profile_name:
        raise ValueError(f"unknown host role: {role}")
    profile = profiles.get(profile_name)
    if not isinstance(profile, dict):
        raise ValueError(f"unknown host profile: {profile_name}")
    return {
        "version": str(payload.get("version", "")).strip(),
        "role": role,
        "profile": profile_name,
        "capabilities": [str(item).strip() for item in profile.get("capabilities", []) if str(item).strip()],
        "allowed_actions": [str(item).strip() for item in profile.get("allowed_actions", []) if str(item).strip()],
        "actions": [dict(item) for item in actions if isinstance(item, dict)],
    }


def required_capabilities_for_action(role: str, action: str) -> List[str]:
    normalized_action = str(action).strip()
    contract = action_contract(role)
    for item in contract["actions"]:
        if str(item.get("action", "")).strip() == normalized_action:
            return [str(name).strip() for name in item.get("required_capabilities", []) if str(name).strip()]
    raise ValueError(f"unknown host action: {normalized_action}")


def role_has_action_capabilities(role: str, action: str) -> bool:
    contract = action_contract(role)
    granted = {str(name).strip() for name in contract["capabilities"] if str(name).strip()}
    required = set(required_capabilities_for_action(role, action))
    return required.issubset(granted)


@dataclass
class HostStep:
    adapter: PalamedesAdapter
    role: str = "planner"
    strategy_provider: Any = None

    def _normalize_input(self, host_input: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(host_input, dict):
            raise ValueError("host_input must be an object")
        action = str(host_input.get("action", "")).strip()
        if not action:
            raise ValueError("host_input.action is required")
        payload = host_input.get("payload", {}) or {}
        if not isinstance(payload, dict):
            raise ValueError("host_input.payload must be an object")
        options = host_input.get("options", {}) or {}
        if not isinstance(options, dict):
            raise ValueError("host_input.options must be an object")
        return {"action": action, "payload": dict(payload), "options": dict(options)}

    def _restore_event(self, action_name: str) -> Dict[str, Any]:
        before = self.adapter.snapshot()
        preflight = evaluate_snapshot_gate(before)
        result = self.adapter.restore_previous()
        summary = summarize_cycle_result(result)
        gate = evaluate_cycle_gate(before, result)
        outcome = {
            "role": self.role,
            "session": {"profile": action_contract(self.role)["profile"]},
            "before": before,
            "preflight": preflight,
            "result": result,
            "summary": summary,
            "after": result.get("post_cycle", {}),
            "gate": gate,
        }
        return build_success_event(action_name, outcome)

    def _preview_event(self, action_name: str) -> Dict[str, Any]:
        preview = self.adapter.preview_restore_previous()
        return {
            "ok": True,
            "type": action_name,
            "role": self.role,
            "summary": {
                "role": self.role,
                "profile": action_contract(self.role)["profile"],
                "operation": "preview_restore_previous",
                "fingerprint": "",
                "changed_fields": [],
                "qa_result": "",
                "qa_score": None,
                "health_status": "",
                "decision": "continue",
                "reasons": [],
                "retried": False,
            },
            "gate": {"decision": "continue", "reasons": []},
            "session": {"profile": action_contract(self.role)["profile"]},
            "result": {"preview": preview},
            "error": None,
        }

    def run_event(self, host_input: Dict[str, Any]) -> Dict[str, Any]:
        try:
            normalized = self._normalize_input(host_input)
            action = normalized["action"]
            payload = normalized["payload"]
            options = normalized["options"]
            contract = action_contract(self.role)
            known_actions = {item["action"] for item in contract["actions"]}
            if action not in known_actions:
                raise ValueError(f"unsupported host action: {action}")
            if not role_has_action_capabilities(self.role, action):
                required = required_capabilities_for_action(self.role, action)
                raise ValueError(f"action requires capabilities for role {self.role}: {action} needs {', '.join(required)}")

            session_id = str(options.get("session_id", "")).strip()
            step_id = str(options.get("step_id", "")).strip()

            if action == "update_plan":
                return PlannerLoop(self.adapter, role=self.role).run_event(payload)
            if action in {"evaluate_experience_strategy", "generate_creative_directions", "analyze_outcome_learning"}:
                return StrategyLoop(self.adapter, role=self.role, provider=self.strategy_provider).run_event(payload, action_name=action)
            if action == "capture_evidence_cycle":
                return ResearchLoop(self.adapter, role=self.role).run_event(payload, session_id=session_id, step_id=step_id)
            if action == "run_reference_discovery":
                return ResearchLoop(self.adapter, role=self.role).reference_event(payload, session_id=session_id, step_id=step_id)
            if action == "request_review":
                return ReviewLoop(self.adapter, role=self.role).request_event(payload, session_id=session_id, step_id=step_id)
            if action == "resolve_review":
                return ReviewLoop(self.adapter, role=self.role).resolve_event(payload, session_id=session_id, step_id=step_id)
            if action == "preview_restore_previous":
                return self._preview_event("restore_preview")
            if action == "restore_previous":
                return self._restore_event("restore_applied")

            raise ValueError(f"unsupported host action: {action}")
        except ValueError as exc:
            message = str(exc)
            error_type = "permission_denied" if message.startswith("action requires capabilities for role ") else "invalid_action"
            return build_error_event(
                "host_step_failed",
                role=self.role,
                error_type=error_type,
                message=message,
                retryable=False,
                error_code=error_type,
            )
