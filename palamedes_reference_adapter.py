#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Any, Dict

from palamedes_sdk import (
    PalamedesClient,
    PalamedesClientOperationError,
    PalamedesConflictError,
    PalamedesHealthGateError,
)


@dataclass
class PalamedesKernelAdapter:
    client: PalamedesClient
    history_limit: int = 5
    require_healthy_writes: bool = True

    def snapshot(self) -> Dict[str, Any]:
        return self.client.get_cycle(history_limit=self.history_limit)

    def apply_plan_update(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.apply_and_get_cycle_with_retry(
            "update_plan",
            payload,
            history_limit=self.history_limit,
            require_healthy=self.require_healthy_writes,
        )

    def capture_evidence(self, payload: Dict[str, Any], *, allow_retry: bool = False) -> Dict[str, Any]:
        return self.client.apply_and_get_cycle_with_retry(
            "add_evidence",
            payload,
            history_limit=self.history_limit,
            require_healthy=self.require_healthy_writes,
            allow_non_idempotent_retry=allow_retry,
        )

    def restore_previous(self) -> Dict[str, Any]:
        return self.client.apply_and_get_cycle_with_retry(
            "restore_revision",
            {"previous": True},
            history_limit=self.history_limit,
            require_healthy=self.require_healthy_writes,
        )

    def preview_restore_previous(self) -> Dict[str, Any]:
        return self.client.preview_restore(previous=True)


def summarize_for_host(result: Dict[str, Any]) -> Dict[str, Any]:
    post_cycle = result.get("post_cycle", {})
    qa = post_cycle.get("qa", {})
    health = post_cycle.get("health", {})
    return {
        "operation": result.get("operation", ""),
        "fingerprint": result.get("post_fingerprint", ""),
        "changed_fields": result.get("changed_fields", []),
        "qa_result": qa.get("result", ""),
        "qa_score": qa.get("score"),
        "health_status": health.get("status", ""),
        "retried": bool(result.get("retried", False)),
    }


def example_host_step() -> None:
    adapter = PalamedesKernelAdapter(PalamedesClient.from_http("127.0.0.1", 8787))
    try:
        cycle = adapter.snapshot()
        print("Current goal:", cycle["plan"].get("goal", ""))
        result = adapter.apply_plan_update(
            {
                "goal": "Narrow to creator workflow automation",
                "success_metric": "Reach 5 retained pilots",
                "deadline": "2026-04-30",
            }
        )
        print(summarize_for_host(result))
    except PalamedesConflictError as exc:
        print(
            {
                "type": "conflict",
                "operation": exc.operation,
                "step": exc.step,
                "expected_fingerprint": exc.expected_fingerprint,
                "current_fingerprint": exc.current_fingerprint,
            }
        )
    except PalamedesHealthGateError as exc:
        print({"type": "health_gate", "operation": exc.operation, "status": exc.status})
    except PalamedesClientOperationError as exc:
        print({"type": "operation_error", "operation": exc.operation, "step": exc.step, "status": exc.status})


if __name__ == "__main__":
    example_host_step()
