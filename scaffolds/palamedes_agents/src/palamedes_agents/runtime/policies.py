#!/usr/bin/env python3
from typing import Any, Dict, Optional


APPEND_STYLE_OPERATIONS = {
    "capture_evidence_cycle": "evidence-cycle",
    "request_review": "review-request",
    "resolve_review": "review-resolve",
}


def build_idempotency_key(*, session_id: str, step_id: str, operation: str) -> str:
    normalized_session = str(session_id).strip()
    normalized_step = str(step_id).strip()
    normalized_operation = str(operation).strip()
    if not normalized_session:
        raise ValueError("session_id is required")
    if not normalized_step:
        raise ValueError("step_id is required")
    if not normalized_operation:
        raise ValueError("operation is required")
    suffix = APPEND_STYLE_OPERATIONS.get(normalized_operation, normalized_operation.replace("_", "-"))
    return f"{normalized_session}:{normalized_step}:{suffix}"


def apply_idempotency_policy(
    operation: str,
    payload: Dict[str, Any],
    *,
    session_id: str = "",
    step_id: str = "",
) -> Dict[str, Any]:
    updated = dict(payload)
    normalized_operation = str(operation).strip()
    if normalized_operation not in APPEND_STYLE_OPERATIONS:
        return updated
    if str(updated.get("idempotency_key", "")).strip():
        return updated
    if not str(session_id).strip() or not str(step_id).strip():
        return updated
    updated["idempotency_key"] = build_idempotency_key(
        session_id=session_id,
        step_id=step_id,
        operation=normalized_operation,
    )
    return updated


def should_retry_stale_conflict(
    *,
    attempt_count: int,
    max_attempts: int = 2,
    retryable: bool = True,
    error_code: str = "",
) -> bool:
    if attempt_count < 1:
        raise ValueError("attempt_count must be positive")
    if max_attempts < 1:
        raise ValueError("max_attempts must be positive")
    if not retryable:
        return False
    normalized_error_code = str(error_code).strip()
    if normalized_error_code and normalized_error_code != "plan_fingerprint_mismatch":
        return False
    return attempt_count < max_attempts
