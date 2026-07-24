#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Any, Dict

from palamedes_sdk import PalamedesClient
from palamedes_client import PalamedesClientOperationError, PalamedesConflictError, PalamedesHealthGateError
from palamedes_host_contract import host_action_contract, required_capabilities_for_action, role_has_action_capabilities

from palamedes_reference_adapter import PalamedesKernelAdapter, summarize_for_host


@dataclass
class PlannerHostStep:
    adapter: PalamedesKernelAdapter
    role: str = "planner"

    def action_contract(self) -> Dict[str, Any]:
        return host_action_contract(self.role)

    def _normalize_input(self, planner_output: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(planner_output, dict):
            raise ValueError("planner_output must be an object")
        action = str(planner_output.get("action", "")).strip()
        if not action:
            raise ValueError("planner_output.action is required")
        payload = planner_output.get("payload", {}) or {}
        if not isinstance(payload, dict):
            raise ValueError("planner_output.payload must be an object")
        options = planner_output.get("options", {}) or {}
        if not isinstance(options, dict):
            raise ValueError("planner_output.options must be an object")
        return {"action": action, "payload": dict(payload), "options": dict(options)}

    def run(self, planner_output: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self._normalize_input(planner_output)
        action = normalized["action"]
        contract = self.action_contract()
        known_actions = {item["action"] for item in contract["actions"]}
        if action not in known_actions:
            raise ValueError(f"unsupported planner action: {action}")
        if not role_has_action_capabilities(self.role, action):
            required = required_capabilities_for_action(self.role, action)
            raise ValueError(
                f"action requires capabilities for role {self.role}: {action} needs {', '.join(required)}"
            )
        payload = normalized["payload"]
        options = normalized["options"]
        history_limit = int(options.get("history_limit", self.adapter.history_limit))
        expected_fingerprint = str(options.get("expected_fingerprint", "")).strip()
        allow_retry = bool(options.get("allow_retry", False))
        require_healthy = bool(options.get("require_healthy", self.adapter.require_healthy_writes))

        if action == "update_plan":
            result = self.adapter.client.apply_and_get_cycle_with_retry(
                "update_plan",
                payload,
                history_limit=history_limit,
                expected_fingerprint=expected_fingerprint,
                require_healthy=require_healthy,
                allow_non_idempotent_retry=allow_retry,
            )
            return {"type": "plan_update_applied", "action": action, "summary": summarize_for_host(result), "result": result}

        if action == "capture_evidence_cycle":
            result = self.adapter.client.capture_evidence_cycle(
                dict(payload.get("evidence", {}) or {}),
                replan_payload=dict(payload.get("replan", {}) or {}),
                history_limit=history_limit,
                idempotency_key=str(payload.get("idempotency_key", "")).strip(),
                expected_fingerprint=expected_fingerprint,
                allow_retry=allow_retry,
                require_healthy=require_healthy,
            )
            return {"type": "evidence_cycle_applied", "action": action, "summary": summarize_for_host(result), "result": result}

        if action == "request_review":
            result = self.adapter.client.apply_and_get_cycle_with_retry(
                "request_review",
                payload,
                history_limit=history_limit,
                expected_fingerprint=expected_fingerprint,
                require_healthy=require_healthy,
                allow_non_idempotent_retry=allow_retry,
            )
            return {"type": "review_requested", "action": action, "summary": summarize_for_host(result), "result": result}

        if action == "resolve_review":
            result = self.adapter.client.apply_and_get_cycle_with_retry(
                "resolve_review",
                payload,
                history_limit=history_limit,
                expected_fingerprint=expected_fingerprint,
                require_healthy=require_healthy,
                allow_non_idempotent_retry=allow_retry,
            )
            return {"type": "review_resolved", "action": action, "summary": summarize_for_host(result), "result": result}

        if action == "preview_restore_previous":
            preview = self.adapter.preview_restore_previous()
            return {"type": "restore_preview", "action": action, "preview": preview}

        if action == "restore_previous":
            result = self.adapter.client.apply_and_get_cycle_with_retry(
                "restore_revision",
                {"previous": True},
                history_limit=history_limit,
                expected_fingerprint=expected_fingerprint,
                require_healthy=require_healthy,
            )
            return {"type": "restore_applied", "action": action, "summary": summarize_for_host(result), "result": result}

        raise ValueError(f"unsupported planner action: {action}")

    def run_event(self, planner_output: Dict[str, Any]) -> Dict[str, Any]:
        try:
            event = self.run(planner_output)
            event["ok"] = True
            event["error"] = None
            return event
        except PalamedesConflictError as exc:
            return {
                "ok": False,
                "type": "conflict",
                "action": str((planner_output or {}).get("action", "")).strip(),
                "error": {
                    "type": "conflict",
                    "error_code": exc.error_code or "plan_fingerprint_mismatch",
                    "retryable": exc.retryable,
                    "operation": exc.operation,
                    "step": exc.step,
                    "expected_fingerprint": exc.expected_fingerprint,
                    "current_fingerprint": exc.current_fingerprint,
                    "message": str(exc),
                },
            }
        except PalamedesHealthGateError as exc:
            return {
                "ok": False,
                "type": "health_gate",
                "action": str((planner_output or {}).get("action", "")).strip(),
                "error": {
                    "type": "health_gate",
                    "error_code": "health_gate_blocked",
                    "retryable": False,
                    "operation": exc.operation,
                    "step": exc.step,
                    "status": exc.status,
                    "message": str(exc),
                },
            }
        except PalamedesClientOperationError as exc:
            cause_code = str(exc.payload.get("error_code", "")).strip() or "operation_failed"
            cause_retryable = bool(exc.payload.get("retryable", False))
            return {
                "ok": False,
                "type": "operation_error",
                "action": str((planner_output or {}).get("action", "")).strip(),
                "error": {
                    "type": "operation_error",
                    "error_code": cause_code,
                    "retryable": cause_retryable,
                    "operation": exc.operation,
                    "step": exc.step,
                    "status": exc.status,
                    "message": str(exc),
                },
            }
        except ValueError as exc:
            message = str(exc)
            error_type = "permission_denied" if message.startswith("action requires capabilities for role ") else "invalid_action"
            return {
                "ok": False,
                "type": error_type,
                "action": str((planner_output or {}).get("action", "")).strip(),
                "error": {
                    "type": error_type,
                    "error_code": error_type,
                    "retryable": False,
                    "message": message,
                },
            }


def example_planner_host() -> None:
    adapter = PalamedesKernelAdapter(PalamedesClient.from_http("127.0.0.1", 8787))
    host = PlannerHostStep(adapter)
    event = host.run(
        {
            "action": "update_plan",
            "payload": {
                "goal": "Narrow to a retained pilot segment",
                "success_metric": "Reach 5 retained pilots",
                "deadline": "2026-04-30",
            },
        }
    )
    print(event["type"])
    print(event["summary"])


if __name__ == "__main__":
    example_planner_host()
