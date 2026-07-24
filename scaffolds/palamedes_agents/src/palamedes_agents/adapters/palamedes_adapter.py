#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol


class PalamedesClientLike(Protocol):
    def get_cycle(self, *, history_limit: int = 10) -> Dict[str, Any]:
        ...

    def apply_and_get_cycle(
        self,
        operation: str,
        payload: Dict[str, Any],
        *,
        history_limit: int = 10,
        expected_fingerprint: str = "",
        require_healthy: bool = False,
    ) -> Dict[str, Any]:
        ...

    def execute_tool(self, tool_name: str, payload: Dict[str, Any], *, expected_fingerprint: str = "") -> Dict[str, Any]:
        ...

    def preview_restore(self, *, previous: bool = False) -> Dict[str, Any]:
        ...

    def capture_evidence_cycle(
        self,
        evidence_payload: Dict[str, Any],
        *,
        replan_payload: Optional[Dict[str, Any]] = None,
        history_limit: int = 10,
        idempotency_key: str = "",
        expected_fingerprint: str = "",
        allow_retry: bool = False,
        require_healthy: bool = False,
    ) -> Dict[str, Any]:
        ...


@dataclass
class PalamedesAdapter:
    client: PalamedesClientLike
    history_limit: int = 5
    require_healthy_writes: bool = True

    def snapshot(self) -> Dict[str, Any]:
        return self.client.get_cycle(history_limit=self.history_limit)

    def apply_plan_update(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.apply_and_get_cycle(
            "update_plan",
            payload,
            history_limit=self.history_limit,
            require_healthy=self.require_healthy_writes,
        )

    def capture_evidence_cycle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        evidence_payload = dict(payload.get("evidence", payload))
        replan_payload = payload.get("replan") if isinstance(payload.get("replan"), dict) else None
        return self.client.capture_evidence_cycle(
            evidence_payload,
            replan_payload=replan_payload,
            history_limit=self.history_limit,
            idempotency_key=str(payload.get("idempotency_key", "")).strip(),
            expected_fingerprint=str(payload.get("expected_fingerprint", "")).strip(),
            allow_retry=True,
            require_healthy=self.require_healthy_writes,
        )

    def run_reference_discovery(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        tool_result = self.client.execute_tool(
            "run_reference_discovery",
            payload,
            expected_fingerprint=str(payload.get("expected_fingerprint", "")).strip(),
        )
        post_cycle = self.snapshot()
        return {
            "operation": "run_reference_discovery",
            "changed_fields": ["reference_discoveries"] if bool(payload.get("apply", False)) else [],
            "post_fingerprint": str(post_cycle.get("fingerprint", "")).strip(),
            "retried": False,
            "tool_result": tool_result,
            "post_cycle": post_cycle,
        }

    def request_review(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.apply_and_get_cycle(
            "request_review",
            payload,
            history_limit=self.history_limit,
            require_healthy=self.require_healthy_writes,
        )

    def resolve_review(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.apply_and_get_cycle(
            "resolve_review",
            payload,
            history_limit=self.history_limit,
            require_healthy=self.require_healthy_writes,
        )

    def preview_restore_previous(self) -> Dict[str, Any]:
        return self.client.preview_restore(previous=True)

    def restore_previous(self) -> Dict[str, Any]:
        return self.client.apply_and_get_cycle(
            "restore_revision",
            {"previous": True},
            history_limit=self.history_limit,
            require_healthy=self.require_healthy_writes,
        )


def summarize_cycle_result(result: Dict[str, Any]) -> Dict[str, Any]:
    post_cycle = result.get("post_cycle", {})
    qa = post_cycle.get("qa", {}) if isinstance(post_cycle, dict) else {}
    health = post_cycle.get("health", {}) if isinstance(post_cycle, dict) else {}
    return {
        "operation": str(result.get("operation", "")).strip(),
        "fingerprint": str(result.get("post_fingerprint", "")).strip(),
        "changed_fields": list(result.get("changed_fields", [])) if isinstance(result.get("changed_fields", []), list) else [],
        "qa_result": str(qa.get("result", "")).strip(),
        "qa_score": qa.get("score"),
        "health_status": str(health.get("status", "")).strip(),
        "retried": bool(result.get("retried", False)),
    }
