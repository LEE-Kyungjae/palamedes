#!/usr/bin/env python3
from typing import Any, Dict


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def summarize_for_host(outcome: Dict[str, Any]) -> Dict[str, Any]:
    summary = _safe_dict(outcome.get("summary"))
    gate = _safe_dict(outcome.get("gate"))
    session = _safe_dict(outcome.get("session"))
    return {
        "role": str(outcome.get("role", "")).strip(),
        "profile": str(session.get("profile", "")).strip(),
        "operation": str(summary.get("operation", "")).strip(),
        "fingerprint": str(summary.get("fingerprint", "")).strip(),
        "changed_fields": list(summary.get("changed_fields", [])) if isinstance(summary.get("changed_fields", []), list) else [],
        "qa_result": str(summary.get("qa_result", "")).strip(),
        "qa_score": summary.get("qa_score"),
        "health_status": str(summary.get("health_status", "")).strip(),
        "decision": str(gate.get("decision", "")).strip(),
        "reasons": list(gate.get("reasons", [])) if isinstance(gate.get("reasons", []), list) else [],
        "retried": bool(summary.get("retried", False)),
    }


def build_success_event(event_type: str, outcome: Dict[str, Any]) -> Dict[str, Any]:
    normalized_type = str(event_type).strip()
    if not normalized_type:
        raise ValueError("event_type is required")
    summary = summarize_for_host(outcome)
    return {
        "ok": True,
        "type": normalized_type,
        "role": str(outcome.get("role", "")).strip(),
        "summary": summary,
        "gate": _safe_dict(outcome.get("gate")),
        "session": _safe_dict(outcome.get("session")),
        "result": _safe_dict(outcome.get("result")),
        "error": None,
    }


def build_error_event(
    event_type: str,
    *,
    role: str,
    error_type: str,
    message: str,
    retryable: bool = False,
    operation: str = "",
    step: str = "",
    error_code: str = "",
) -> Dict[str, Any]:
    normalized_type = str(event_type).strip()
    normalized_error_type = str(error_type).strip()
    if not normalized_type:
        raise ValueError("event_type is required")
    if not normalized_error_type:
        raise ValueError("error_type is required")
    return {
        "ok": False,
        "type": normalized_type,
        "role": str(role).strip(),
        "summary": None,
        "gate": {},
        "session": {},
        "result": {},
        "error": {
            "type": normalized_error_type,
            "error_code": str(error_code).strip() or normalized_error_type,
            "retryable": bool(retryable),
            "operation": str(operation).strip(),
            "step": str(step).strip(),
            "message": str(message),
        },
    }
