#!/usr/bin/env python3
import argparse
import json
import shlex
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from palamedes import (
    add_evidence,
    apply_replan_payload,
    build_reference_discovery_pack,
    cycle_snapshot,
    get_revision,
    list_revisions,
    load_plan,
    mutate_plan_state,
    now_iso,
    parse_csv,
    plan_fingerprint,
    plan_response,
    plan_summary,
    qa_autoreplan_result,
    qa_report,
    record_id,
    record_idempotency_result,
    reference_discovery_record,
    replay_idempotency_result,
    resolve_revision_reference,
    restore_preview,
    save_validated_plan,
    storage_health_report,
    validate_plan_shape,
    validate_development_probe_item,
    validate_inquiry_item,
    validate_open_question_item,
    validate_reference_encounter_item,
)


SCALAR_PLAN_FIELDS = [
    "goal",
    "success_metric",
    "deadline",
    "planning_horizon",
    "review_cadence",
    "selected_option",
]

LIST_PLAN_FIELDS = [
    "phase_plan",
    "constraints",
    "assumptions",
    "options",
    "plan_tasks",
    "execution_tasks",
    "dependencies",
    "experiments",
    "risks",
    "references",
    "insights",
    "direction_insights",
    "market_insights",
    "timing_insights",
    "differentiation_insights",
    "monetization_insights",
    "constraint_insights",
    "risk_signal_insights",
    "evolution_insights",
    "definition_of_done",
]

TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "name": "get_review",
        "description": "Return one human-review escalation record by request identifier.",
        "input_schema": {
            "type": "object",
            "properties": {
                "request_id": {"type": "string"},
            },
            "required": ["request_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "list_reviews",
        "description": "List human-review escalation records from the current plan state.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "scope": {"type": "string"},
                "assigned_to": {"type": "string"},
                "sort_by": {"type": "string", "enum": ["requested_at", "priority", "status", "stale_after"]},
                "order": {"type": "string", "enum": ["asc", "desc"]},
                "limit": {"type": "integer"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "request_review",
        "description": "Append a human-review escalation record to the current plan state.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expected_fingerprint": {"type": "string"},
                "idempotency_key": {"type": "string"},
                "request_id": {"type": "string"},
                "scope": {"type": "string"},
                "reason": {"type": "string"},
                "requested_by": {"type": "string"},
                "status": {"type": "string", "enum": ["open", "acknowledged", "resolved", "dismissed"]},
                "priority": {"type": "string"},
                "assigned_to": {"type": "string"},
                "stale_after": {"type": "string"},
                "sla_bucket": {"type": "string"},
                "review_recommendation": {"type": "string"},
                "review_reason": {"type": "string"},
                "related_evidence": {"type": "array", "items": {"type": "string"}},
                "related_references": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["scope", "reason"],
            "additionalProperties": False,
        },
    },
    {
        "name": "resolve_review",
        "description": "Update an existing human-review escalation record by request identifier.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expected_fingerprint": {"type": "string"},
                "idempotency_key": {"type": "string"},
                "request_id": {"type": "string"},
                "status": {"type": "string", "enum": ["acknowledged", "resolved", "dismissed"]},
                "resolution": {"type": "string"},
                "resolved_by": {"type": "string"},
                "assigned_to": {"type": "string"},
                "review_recommendation": {"type": "string"},
                "review_reason": {"type": "string"},
            },
            "required": ["request_id", "status"],
            "additionalProperties": False,
        },
    },
    {
        "name": "update_review",
        "description": "Update triage fields on an existing human-review escalation record without changing status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expected_fingerprint": {"type": "string"},
                "idempotency_key": {"type": "string"},
                "request_id": {"type": "string"},
                "priority": {"type": "string"},
                "assigned_to": {"type": "string"},
                "stale_after": {"type": "string"},
                "sla_bucket": {"type": "string"},
                "review_recommendation": {"type": "string"},
                "review_reason": {"type": "string"},
                "resolution": {"type": "string"},
            },
            "required": ["request_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_plan",
        "description": "Return the current Palamedes plan and derived summary.",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "get_qa",
        "description": "Return the weighted QA report for the current plan.",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "get_health",
        "description": "Return storage health, parseability, and recovery diagnostics.",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "validate_plan",
        "description": "Validate the current Palamedes plan structure and nested records.",
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "get_history",
        "description": "Return recent plan revisions with snapshot metadata.",
        "input_schema": {
            "type": "object",
            "properties": {"limit": {"type": "integer"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "restore_revision",
        "description": "Restore the current plan to a previously recorded revision snapshot.",
        "input_schema": {
            "type": "object",
            "properties": {
                "revision_id": {"type": "string"},
                "expected_fingerprint": {"type": "string"},
                "previous": {"type": "boolean"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "preview_restore",
        "description": "Preview the diff and summary impact of restoring a recorded revision snapshot.",
        "input_schema": {
            "type": "object",
            "properties": {
                "revision_id": {"type": "string"},
                "previous": {"type": "boolean"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "run_reference_discovery",
        "description": "Generate and optionally apply a structured reference-discovery pass for an open planning question.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expected_fingerprint": {"type": "string"},
                "question": {"type": "string"},
                "context": {"type": "string"},
                "references": {"type": "array", "items": {"type": "string"}},
                "rejected": {"type": "array", "items": {"type": "string"}},
                "source_urls": {"type": "array", "items": {"type": "string"}},
                "notes": {"type": "string"},
                "review_recommendation": {"type": "string", "enum": ["", "none", "human_review", "reviewer_agent"]},
                "review_reason": {"type": "string"},
                "apply": {"type": "boolean"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "capture_evidence_cycle",
        "description": "Run an evidence append followed by replan and return the integrated planning cycle snapshot.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expected_fingerprint": {"type": "string"},
                "idempotency_key": {"type": "string"},
                "history_limit": {"type": "integer"},
                "evidence": {
                    "type": "object",
                    "properties": {
                        "claim": {"type": "string"},
                        "source": {"type": "string"},
                        "confidence": {"type": "integer"},
                        "axis": {"type": "string"},
                        "date": {"type": "string"},
                        "reference": {"type": "string"},
                        "source_url": {"type": "string"},
                        "field": {"type": "string"},
                        "selector": {"type": "string"},
                        "observed_value": {},
                        "expected_value": {},
                        "note": {"type": "string"},
                        "evidence_type": {"type": "string"},
                        "review_recommendation": {"type": "string", "enum": ["", "none", "human_review", "reviewer_agent"]},
                        "review_reason": {"type": "string"},
                    },
                    "required": ["claim"],
                    "additionalProperties": False,
                },
                "replan": {
                    "type": "object",
                    "properties": {
                        "evidence": {"type": "string"},
                        "evidence_source": {"type": "string"},
                        "evidence_confidence": {"type": "integer"},
                        "evidence_axis": {"type": "string"},
                        "evidence_date": {"type": "string"},
                        "plan_task": {"type": "string"},
                        "execution_task": {"type": "string"},
                        "phase": {"type": "string"},
                        "reference": {"type": "string"},
                        "insight": {"type": "string"},
                        "direction_insight": {"type": "string"},
                        "market_insight": {"type": "string"},
                        "timing_insight": {"type": "string"},
                        "differentiation_insight": {"type": "string"},
                        "monetization_insight": {"type": "string"},
                        "constraint_insight": {"type": "string"},
                        "risk_signal_insight": {"type": "string"},
                        "evolution_insight": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
            },
            "required": ["evidence"],
            "additionalProperties": False,
        },
    },
    {
        "name": "replan",
        "description": "Append execution evidence or planning deltas and run QA with auto-replan if needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expected_fingerprint": {"type": "string"},
                "idempotency_key": {"type": "string"},
                "evidence": {"type": "string"},
                "evidence_source": {"type": "string"},
                "evidence_confidence": {"type": "integer"},
                "evidence_axis": {"type": "string"},
                "evidence_date": {"type": "string"},
                "plan_task": {"type": "string"},
                "execution_task": {"type": "string"},
                "phase": {"type": "string"},
                "reference": {"type": "string"},
                "insight": {"type": "string"},
                "direction_insight": {"type": "string"},
                "market_insight": {"type": "string"},
                "timing_insight": {"type": "string"},
                "differentiation_insight": {"type": "string"},
                "monetization_insight": {"type": "string"},
                "constraint_insight": {"type": "string"},
                "risk_signal_insight": {"type": "string"},
                "evolution_insight": {"type": "string"},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "update_plan",
        "description": "Update top-level plan fields using scalar strings and list values.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expected_fingerprint": {"type": "string"},
                "goal": {"type": "string"},
                "success_metric": {"type": "string"},
                "deadline": {"type": "string"},
                "planning_horizon": {"type": "string"},
                "review_cadence": {"type": "string"},
                "selected_option": {"type": "string"},
                "phase_plan": {"type": "array", "items": {"type": "string"}},
                "constraints": {"type": "array", "items": {"type": "string"}},
                "assumptions": {"type": "array", "items": {"type": "string"}},
                "options": {"type": "array", "items": {"type": "string"}},
                "plan_tasks": {"type": "array", "items": {"type": "string"}},
                "execution_tasks": {"type": "array", "items": {"type": "string"}},
                "dependencies": {"type": "array", "items": {"type": "string"}},
                "experiments": {"type": "array", "items": {"type": "string"}},
                "risks": {
                    "type": "array",
                    "items": {
                        "oneOf": [
                            {"type": "string"},
                            {
                                "type": "object",
                                "properties": {
                                    "risk": {"type": "string"},
                                    "signal": {"type": "string"},
                                    "mitigation": {"type": "string"},
                                },
                                "required": ["risk", "signal", "mitigation"],
                                "additionalProperties": True,
                            },
                        ]
                    },
                },
                "references": {"type": "array", "items": {"type": "string"}},
                "insights": {"type": "array", "items": {"type": "string"}},
                "direction_insights": {"type": "array", "items": {"type": "string"}},
                "market_insights": {"type": "array", "items": {"type": "string"}},
                "timing_insights": {"type": "array", "items": {"type": "string"}},
                "differentiation_insights": {"type": "array", "items": {"type": "string"}},
                "monetization_insights": {"type": "array", "items": {"type": "string"}},
                "constraint_insights": {"type": "array", "items": {"type": "string"}},
                "risk_signal_insights": {"type": "array", "items": {"type": "string"}},
                "evolution_insights": {"type": "array", "items": {"type": "string"}},
                "definition_of_done": {"type": "array", "items": {"type": "string"}},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "add_evidence",
        "description": "Append one structured evidence item and optional reference.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expected_fingerprint": {"type": "string"},
                "idempotency_key": {"type": "string"},
                "claim": {"type": "string"},
                "source": {"type": "string"},
                "confidence": {"type": "integer"},
                "axis": {"type": "string"},
                "date": {"type": "string"},
                "reference": {"type": "string"},
                "source_url": {"type": "string"},
                "field": {"type": "string"},
                "selector": {"type": "string"},
                "observed_value": {},
                "expected_value": {},
                "note": {"type": "string"},
                "evidence_type": {"type": "string"},
                "review_recommendation": {"type": "string", "enum": ["", "none", "human_review", "reviewer_agent"]},
                "review_reason": {"type": "string"},
            },
            "required": ["claim"],
            "additionalProperties": False,
        },
    },
    {
        "name": "add_hypothesis",
        "description": "Append one hypothesis log item and optional linked evidence.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expected_fingerprint": {"type": "string"},
                "idempotency_key": {"type": "string"},
                "hypothesis": {"type": "string"},
                "metric": {"type": "string"},
                "target": {"type": "string"},
                "window": {"type": "string"},
                "status": {"type": "string", "enum": ["open", "validated", "invalidated", "pivoted"]},
                "outcome": {"type": "string"},
                "evidence": {"type": "string"},
                "confidence": {"type": "integer"},
                "axis": {"type": "string"},
                "date": {"type": "string"},
            },
            "required": ["hypothesis"],
            "additionalProperties": False,
        },
    },
    {
        "name": "record_view_transition",
        "description": "Record why a project view changed without treating the new view as final truth.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expected_fingerprint": {"type": "string"},
                "idempotency_key": {"type": "string"},
                "previous_view": {"type": "string"},
                "trigger": {"type": "string"},
                "new_view": {"type": "string"},
                "new_blind_spots": {"type": "string"},
                "opened_paths": {"type": "array", "items": {"type": "string"}},
                "next_probe": {"type": "string"},
                "source": {"type": "string"},
                "references": {"type": "array", "items": {"type": "string"}},
                "plan_effect": {"type": "string", "enum": ["none", "observe", "add_probe", "reframe", "revise_plan", "stop", "restore"]},
                "plan_effect_reason": {"type": "string"},
            },
            "required": ["previous_view", "trigger", "new_view", "next_probe"],
            "additionalProperties": False,
        },
    },
    {
        "name": "record_inquiry_item",
        "description": "Record whether a statement is an observation, question, thought experiment, hypothesis, option, proposal, decision, commitment, or rejection.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expected_fingerprint": {"type": "string"},
                "idempotency_key": {"type": "string"},
                "statement": {"type": "string"},
                "kind": {"type": "string", "enum": ["observation", "question", "thought_experiment", "hypothesis", "option", "proposal", "decision", "commitment", "rejection"]},
                "status": {"type": "string", "enum": ["open", "exploring", "held", "validated", "invalidated", "adopted", "rejected", "closed"]},
                "intent": {"type": "string"},
                "commitment": {"type": "string", "enum": ["none", "considering", "decided", "committed"]},
                "source": {"type": "string"},
                "opened_questions": {"type": "array", "items": {"type": "string"}},
                "references": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["statement", "kind", "intent"],
            "additionalProperties": False,
        },
    },
    {
        "name": "record_reference_encounter",
        "description": "Record why a reference mattered and how it affected the project view.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expected_fingerprint": {"type": "string"},
                "idempotency_key": {"type": "string"},
                "reference": {"type": "string"},
                "encountered_while": {"type": "string"},
                "initial_interest": {"type": "string"},
                "relation": {"type": "string"},
                "effect": {"type": "string", "enum": ["none", "reinforced", "challenged", "opened_question", "reframed_problem", "adopted_pattern", "rejected_after_use"]},
                "adoption": {"type": "string", "enum": ["not_decided", "not_applicable", "adopted", "rejected", "removed_after_use"]},
                "later_outcome": {"type": "string"},
                "source": {"type": "string"},
            },
            "required": ["reference", "encountered_while", "initial_interest", "relation", "effect"],
            "additionalProperties": False,
        },
    },
    {
        "name": "record_development_probe",
        "description": "Record a development step as a bounded probe intended to reveal new information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expected_fingerprint": {"type": "string"},
                "idempotency_key": {"type": "string"},
                "id": {"type": "string"},
                "step": {"type": "string"},
                "expected_learning": {"type": "string"},
                "expected_result": {"type": "string"},
                "status": {"type": "string", "enum": ["planned", "running", "completed", "abandoned"]},
                "actual_observation": {"type": "string"},
                "unexpected_observation": {"type": "string"},
                "view_transition_id": {"type": "string"},
                "next_step": {"type": "string"},
                "source": {"type": "string"},
                "references": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["step", "expected_learning"],
            "additionalProperties": False,
        },
    },
    {
        "name": "record_open_question",
        "description": "Preserve an unresolved question with multiple perspectives, their visibility, and their blind spots.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expected_fingerprint": {"type": "string"},
                "idempotency_key": {"type": "string"},
                "id": {"type": "string"},
                "question": {"type": "string"},
                "perspectives": {"type": "array"},
                "resolution": {"type": "string", "enum": ["intentionally_open", "resolved", "deferred"]},
                "revisit_when": {"type": "string"},
                "source": {"type": "string"},
                "references": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["question", "perspectives", "revisit_when"],
            "additionalProperties": False,
        },
    },
]

TOOL_VALIDATORS = {
    "get_review": "validate_get_review_payload",
    "list_reviews": "validate_list_reviews_payload",
    "get_history": "validate_history_payload",
    "restore_revision": "validate_restore_payload",
    "preview_restore": "validate_preview_restore_payload",
    "run_reference_discovery": "validate_reference_discovery_payload",
    "capture_evidence_cycle": "validate_capture_evidence_cycle_payload",
    "replan": "validate_replan_payload",
    "update_plan": "validate_update_payload",
    "request_review": "validate_request_review_payload",
    "resolve_review": "validate_resolve_review_payload",
    "update_review": "validate_update_review_payload",
    "add_evidence": "validate_evidence_payload",
    "add_hypothesis": "validate_hypothesis_payload",
    "record_view_transition": "validate_view_transition_payload",
    "record_inquiry_item": "validate_inquiry_tool_payload",
    "record_reference_encounter": "validate_reference_encounter_tool_payload",
    "record_development_probe": "validate_development_probe_tool_payload",
    "record_open_question": "validate_open_question_tool_payload",
}

MUTATION_TOOLS = {
    "restore_revision",
    "run_reference_discovery",
    "capture_evidence_cycle",
    "replan",
    "update_plan",
    "request_review",
    "resolve_review",
    "update_review",
    "add_evidence",
    "add_hypothesis",
    "record_view_transition",
    "record_inquiry_item",
    "record_reference_encounter",
    "record_development_probe",
    "record_open_question",
}


def ensure_object_payload(payload: Dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")


def is_json_value(value: Any) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(is_json_value(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and is_json_value(item) for key, item in value.items())
    return False


def validate_expected_fingerprint(payload: Dict[str, Any]) -> None:
    if "expected_fingerprint" in payload and not isinstance(payload["expected_fingerprint"], str):
        raise ValueError("expected_fingerprint must be a string")


def validate_idempotency_key(payload: Dict[str, Any]) -> None:
    if "idempotency_key" in payload and not isinstance(payload["idempotency_key"], str):
        raise ValueError("idempotency_key must be a string")


def validate_update_payload(payload: Dict[str, Any]) -> None:
    ensure_object_payload(payload)
    validate_expected_fingerprint(payload)
    allowed = set(SCALAR_PLAN_FIELDS + LIST_PLAN_FIELDS + ["expected_fingerprint"])
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValueError(f"unknown update_plan fields: {', '.join(unknown)}")

    for field in SCALAR_PLAN_FIELDS:
        if field in payload and not isinstance(payload[field], str):
            raise ValueError(f"{field} must be a string")

    for field in LIST_PLAN_FIELDS:
        if field not in payload:
            continue
        value = payload[field]
        if not isinstance(value, list):
            raise ValueError(f"{field} must be an array")
        if field == "risks":
            for index, item in enumerate(value):
                if isinstance(item, str) and item.strip():
                    continue
                if isinstance(item, dict) and all(isinstance(item.get(key), str) and item.get(key, "").strip() for key in ["risk", "signal", "mitigation"]):
                    continue
                raise ValueError(f"risks[{index}] must be a non-empty string or an object with risk/signal/mitigation")
            continue
        if not all(isinstance(item, str) for item in value):
            raise ValueError(f"{field} must contain only strings")


def validate_get_review_payload(payload: Dict[str, Any]) -> None:
    ensure_object_payload(payload)
    allowed = {"request_id"}
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValueError(f"unknown get_review fields: {', '.join(unknown)}")
    if not isinstance(payload.get("request_id"), str) or not str(payload.get("request_id", "")).strip():
        raise ValueError("request_id is required")


def validate_history_payload(payload: Dict[str, Any]) -> None:
    ensure_object_payload(payload)
    allowed = {"limit"}
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValueError(f"unknown get_history fields: {', '.join(unknown)}")
    if "limit" in payload and (not isinstance(payload["limit"], int) or isinstance(payload["limit"], bool)):
        raise ValueError("limit must be an integer")


def validate_list_reviews_payload(payload: Dict[str, Any]) -> None:
    ensure_object_payload(payload)
    allowed = {"status", "scope", "assigned_to", "sort_by", "order", "limit"}
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValueError(f"unknown list_reviews fields: {', '.join(unknown)}")
    for key in ["status", "scope", "assigned_to", "sort_by", "order"]:
        if key in payload and not isinstance(payload[key], str):
            raise ValueError(f"{key} must be a string")
    if "sort_by" in payload and str(payload.get("sort_by", "")).strip() not in {"requested_at", "priority", "status", "stale_after"}:
        raise ValueError("sort_by must be one of: requested_at, priority, status, stale_after")
    if "order" in payload and str(payload.get("order", "")).strip() not in {"asc", "desc"}:
        raise ValueError("order must be one of: asc, desc")
    if "limit" in payload and (not isinstance(payload["limit"], int) or isinstance(payload["limit"], bool)):
        raise ValueError("limit must be an integer")


def validate_restore_payload(payload: Dict[str, Any]) -> None:
    ensure_object_payload(payload)
    validate_expected_fingerprint(payload)
    allowed = {"revision_id", "expected_fingerprint", "previous"}
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValueError(f"unknown restore_revision fields: {', '.join(unknown)}")
    if "previous" in payload and not isinstance(payload["previous"], bool):
        raise ValueError("previous must be a boolean")
    revision_id = payload.get("revision_id", "")
    if "previous" in payload and payload["previous"]:
        return
    if not isinstance(revision_id, str) or not revision_id.strip():
        raise ValueError("revision_id is required unless previous=true")


def validate_preview_restore_payload(payload: Dict[str, Any]) -> None:
    ensure_object_payload(payload)
    allowed = {"revision_id", "previous"}
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValueError(f"unknown preview_restore fields: {', '.join(unknown)}")
    if "previous" in payload and not isinstance(payload["previous"], bool):
        raise ValueError("previous must be a boolean")
    revision_id = payload.get("revision_id", "")
    if "previous" in payload and payload["previous"]:
        return
    if not isinstance(revision_id, str) or not revision_id.strip():
        raise ValueError("revision_id is required unless previous=true")


def validate_evidence_payload(payload: Dict[str, Any]) -> None:
    ensure_object_payload(payload)
    validate_expected_fingerprint(payload)
    validate_idempotency_key(payload)
    allowed = {
        "claim",
        "source",
        "confidence",
        "axis",
        "date",
        "reference",
        "source_url",
        "field",
        "selector",
        "observed_value",
        "expected_value",
        "note",
        "evidence_type",
        "review_recommendation",
        "review_reason",
        "expected_fingerprint",
        "idempotency_key",
    }
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValueError(f"unknown add_evidence fields: {', '.join(unknown)}")
    claim = payload.get("claim", "")
    if not isinstance(claim, str) or not claim.strip():
        raise ValueError("claim is required")
    for key in [
        "source",
        "axis",
        "date",
        "reference",
        "source_url",
        "field",
        "selector",
        "note",
        "evidence_type",
        "review_recommendation",
        "review_reason",
    ]:
        if key in payload and not isinstance(payload[key], str):
            raise ValueError(f"{key} must be a string")
    if "confidence" in payload and (not isinstance(payload["confidence"], int) or isinstance(payload["confidence"], bool)):
        raise ValueError("confidence must be an integer")
    for key in ["observed_value", "expected_value"]:
        if key in payload and not is_json_value(payload[key]):
            raise ValueError(f"{key} must be valid JSON data")


def validate_reference_discovery_payload(payload: Dict[str, Any]) -> None:
    ensure_object_payload(payload)
    validate_expected_fingerprint(payload)
    allowed = {
        "expected_fingerprint",
        "question",
        "context",
        "references",
        "rejected",
        "source_urls",
        "notes",
        "review_recommendation",
        "review_reason",
        "apply",
    }
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValueError(f"unknown run_reference_discovery fields: {', '.join(unknown)}")
    for key in ["question", "context", "notes", "review_recommendation", "review_reason"]:
        if key in payload and not isinstance(payload[key], str):
            raise ValueError(f"{key} must be a string")
    for key in ["references", "rejected", "source_urls"]:
        if key not in payload:
            continue
        value = payload[key]
        if not isinstance(value, list):
            raise ValueError(f"{key} must be an array")
        if not all(isinstance(item, str) for item in value):
            raise ValueError(f"{key} must contain only strings")
    if "apply" in payload and not isinstance(payload["apply"], bool):
        raise ValueError("apply must be a boolean")


def validate_capture_evidence_cycle_payload(payload: Dict[str, Any]) -> None:
    ensure_object_payload(payload)
    validate_expected_fingerprint(payload)
    validate_idempotency_key(payload)
    allowed = {"expected_fingerprint", "idempotency_key", "history_limit", "evidence", "replan"}
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValueError(f"unknown capture_evidence_cycle fields: {', '.join(unknown)}")
    if "history_limit" in payload and (not isinstance(payload["history_limit"], int) or isinstance(payload["history_limit"], bool)):
        raise ValueError("history_limit must be an integer")
    evidence_payload = payload.get("evidence")
    if not isinstance(evidence_payload, dict):
        raise ValueError("evidence is required")
    validate_evidence_payload(evidence_payload)
    if "expected_fingerprint" in evidence_payload:
        raise ValueError("evidence.expected_fingerprint is not allowed")
    if "idempotency_key" in evidence_payload:
        raise ValueError("evidence.idempotency_key is not allowed")
    replan_payload = payload.get("replan", {})
    if not isinstance(replan_payload, dict):
        raise ValueError("replan must be an object")
    validate_replan_payload(replan_payload)
    if "expected_fingerprint" in replan_payload:
        raise ValueError("replan.expected_fingerprint is not allowed")
    if "idempotency_key" in replan_payload:
        raise ValueError("replan.idempotency_key is not allowed")


def validate_hypothesis_payload(payload: Dict[str, Any]) -> None:
    ensure_object_payload(payload)
    validate_expected_fingerprint(payload)
    validate_idempotency_key(payload)
    allowed = {"hypothesis", "metric", "target", "window", "status", "outcome", "evidence", "confidence", "axis", "date", "expected_fingerprint", "idempotency_key"}
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValueError(f"unknown add_hypothesis fields: {', '.join(unknown)}")
    hypothesis = payload.get("hypothesis", "")
    if not isinstance(hypothesis, str) or not hypothesis.strip():
        raise ValueError("hypothesis is required")
    for key in ["metric", "target", "window", "status", "outcome", "evidence", "axis", "date"]:
        if key in payload and not isinstance(payload[key], str):
            raise ValueError(f"{key} must be a string")
    if "confidence" in payload and (not isinstance(payload["confidence"], int) or isinstance(payload["confidence"], bool)):
        raise ValueError("confidence must be an integer")
    status = str(payload.get("status", "open")).strip() or "open"
    if status not in {"open", "validated", "invalidated", "pivoted"}:
        raise ValueError("status must be one of: open, validated, invalidated, pivoted")


def validate_view_transition_payload(payload: Dict[str, Any]) -> None:
    ensure_object_payload(payload)
    validate_expected_fingerprint(payload)
    validate_idempotency_key(payload)
    allowed = {
        "expected_fingerprint",
        "idempotency_key",
        "previous_view",
        "trigger",
        "new_view",
        "new_blind_spots",
        "opened_paths",
        "next_probe",
        "source",
        "references",
        "plan_effect",
        "plan_effect_reason",
    }
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValueError(f"unknown record_view_transition fields: {', '.join(unknown)}")
    for key in ["previous_view", "trigger", "new_view", "next_probe"]:
        value = payload.get(key, "")
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} is required")
    for key in ["new_blind_spots", "source", "plan_effect", "plan_effect_reason"]:
        if key in payload and not isinstance(payload[key], str):
            raise ValueError(f"{key} must be a string")
    if payload.get("plan_effect", "none") not in {"none", "observe", "add_probe", "reframe", "revise_plan", "stop", "restore"}:
        raise ValueError("plan_effect is invalid")
    for key in ["opened_paths", "references"]:
        if key not in payload:
            continue
        value = payload[key]
        if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
            raise ValueError(f"{key} must contain only non-empty strings")


def _validate_tool_record(payload: Dict[str, Any], allowed: set, required: List[str], validator, normalized: Dict[str, Any], tool_name: str) -> None:
    ensure_object_payload(payload)
    validate_expected_fingerprint(payload)
    validate_idempotency_key(payload)
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValueError(f"unknown {tool_name} fields: {', '.join(unknown)}")
    for key in required:
        value = payload.get(key)
        if value is None or value == "" or value == []:
            raise ValueError(f"{key} is required")
    errors = validator(normalized, 0)
    if errors:
        raise ValueError("; ".join(errors))


def validate_inquiry_tool_payload(payload: Dict[str, Any]) -> None:
    ts = "validation"
    normalized = {
        "ts": ts,
        "statement": payload.get("statement", ""),
        "kind": payload.get("kind", ""),
        "status": payload.get("status", "open"),
        "intent": payload.get("intent", ""),
        "commitment": payload.get("commitment", "none"),
        "source": payload.get("source", "agent"),
        "opened_questions": payload.get("opened_questions", []),
        "references": payload.get("references", []),
    }
    allowed = set(normalized) - {"ts"} | {"expected_fingerprint", "idempotency_key"}
    _validate_tool_record(payload, allowed, ["statement", "kind", "intent"], validate_inquiry_item, normalized, "record_inquiry_item")


def validate_reference_encounter_tool_payload(payload: Dict[str, Any]) -> None:
    normalized = {
        "ts": "validation",
        "reference": payload.get("reference", ""),
        "encountered_while": payload.get("encountered_while", ""),
        "initial_interest": payload.get("initial_interest", ""),
        "relation": payload.get("relation", ""),
        "effect": payload.get("effect", ""),
        "adoption": payload.get("adoption", "not_decided"),
        "later_outcome": payload.get("later_outcome", ""),
        "source": payload.get("source", "agent"),
    }
    allowed = set(normalized) - {"ts"} | {"expected_fingerprint", "idempotency_key"}
    _validate_tool_record(payload, allowed, ["reference", "encountered_while", "initial_interest", "relation", "effect"], validate_reference_encounter_item, normalized, "record_reference_encounter")


def validate_development_probe_tool_payload(payload: Dict[str, Any]) -> None:
    normalized = {
        "id": payload.get("id", "validation"),
        "ts": "validation",
        "step": payload.get("step", ""),
        "expected_learning": payload.get("expected_learning", ""),
        "expected_result": payload.get("expected_result", ""),
        "status": payload.get("status", "planned"),
        "actual_observation": payload.get("actual_observation", ""),
        "unexpected_observation": payload.get("unexpected_observation", ""),
        "view_transition_id": payload.get("view_transition_id", ""),
        "next_step": payload.get("next_step", ""),
        "source": payload.get("source", "agent"),
        "references": payload.get("references", []),
    }
    allowed = set(normalized) - {"ts"} | {"expected_fingerprint", "idempotency_key"}
    _validate_tool_record(payload, allowed, ["step", "expected_learning"], validate_development_probe_item, normalized, "record_development_probe")


def validate_open_question_tool_payload(payload: Dict[str, Any]) -> None:
    normalized = {
        "id": payload.get("id", "validation"),
        "ts": "validation",
        "question": payload.get("question", ""),
        "perspectives": payload.get("perspectives", []),
        "resolution": payload.get("resolution", "intentionally_open"),
        "revisit_when": payload.get("revisit_when", ""),
        "source": payload.get("source", "agent"),
        "references": payload.get("references", []),
    }
    allowed = set(normalized) - {"ts"} | {"expected_fingerprint", "idempotency_key"}
    _validate_tool_record(payload, allowed, ["question", "perspectives", "revisit_when"], validate_open_question_item, normalized, "record_open_question")


def validate_replan_payload(payload: Dict[str, Any]) -> None:
    ensure_object_payload(payload)
    validate_expected_fingerprint(payload)
    validate_idempotency_key(payload)
    allowed = {
        "expected_fingerprint",
        "idempotency_key",
        "evidence",
        "evidence_source",
        "evidence_confidence",
        "evidence_axis",
        "evidence_date",
        "plan_task",
        "execution_task",
        "phase",
        "reference",
        "insight",
        "direction_insight",
        "market_insight",
        "timing_insight",
        "differentiation_insight",
        "monetization_insight",
        "constraint_insight",
        "risk_signal_insight",
        "evolution_insight",
    }
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValueError(f"unknown replan fields: {', '.join(unknown)}")
    for key, value in payload.items():
        if key == "evidence_confidence":
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError("evidence_confidence must be an integer")
            continue
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string")


def merge_plan_updates(plan: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    for field in SCALAR_PLAN_FIELDS:
        if field in payload and isinstance(payload[field], str):
            plan[field] = payload[field].strip()
    for field in LIST_PLAN_FIELDS:
        if field in payload and isinstance(payload[field], list):
            plan[field] = payload[field]
    return plan


def validate_request_review_payload(payload: Dict[str, Any]) -> None:
    ensure_object_payload(payload)
    validate_expected_fingerprint(payload)
    validate_idempotency_key(payload)
    allowed = {
        "expected_fingerprint",
        "idempotency_key",
        "request_id",
        "scope",
        "reason",
        "requested_by",
        "status",
        "priority",
        "assigned_to",
        "stale_after",
        "sla_bucket",
        "review_recommendation",
        "review_reason",
        "related_evidence",
        "related_references",
    }
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValueError(f"unknown request_review fields: {', '.join(unknown)}")
    for key in ["request_id", "scope", "reason", "requested_by", "status", "priority", "assigned_to", "stale_after", "sla_bucket", "review_recommendation", "review_reason"]:
        if key in payload and not isinstance(payload[key], str):
            raise ValueError(f"{key} must be a string")
    for key in ["scope", "reason"]:
        if not isinstance(payload.get(key), str) or not str(payload.get(key, "")).strip():
            raise ValueError(f"{key} is required")
    for key in ["related_evidence", "related_references"]:
        if key not in payload:
            continue
        value = payload[key]
        if not isinstance(value, list):
            raise ValueError(f"{key} must be an array")
        if not all(isinstance(item, str) and item.strip() for item in value):
            raise ValueError(f"{key} must contain only non-empty strings")


def validate_resolve_review_payload(payload: Dict[str, Any]) -> None:
    ensure_object_payload(payload)
    validate_expected_fingerprint(payload)
    validate_idempotency_key(payload)
    allowed = {
        "expected_fingerprint",
        "idempotency_key",
        "request_id",
        "status",
        "resolution",
        "resolved_by",
        "assigned_to",
        "review_recommendation",
        "review_reason",
    }
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValueError(f"unknown resolve_review fields: {', '.join(unknown)}")
    for key in ["request_id", "status", "resolution", "resolved_by", "assigned_to", "review_recommendation", "review_reason"]:
        if key in payload and not isinstance(payload[key], str):
            raise ValueError(f"{key} must be a string")
    for key in ["request_id", "status"]:
        if not isinstance(payload.get(key), str) or not str(payload.get(key, "")).strip():
            raise ValueError(f"{key} is required")


def validate_update_review_payload(payload: Dict[str, Any]) -> None:
    ensure_object_payload(payload)
    validate_expected_fingerprint(payload)
    validate_idempotency_key(payload)
    allowed = {
        "expected_fingerprint",
        "idempotency_key",
        "request_id",
        "priority",
        "assigned_to",
        "stale_after",
        "sla_bucket",
        "review_recommendation",
        "review_reason",
        "resolution",
    }
    unknown = sorted(set(payload) - allowed)
    if unknown:
        raise ValueError(f"unknown update_review fields: {', '.join(unknown)}")
    if not isinstance(payload.get("request_id"), str) or not str(payload.get("request_id", "")).strip():
        raise ValueError("request_id is required")
    for key in ["priority", "assigned_to", "stale_after", "sla_bucket", "review_recommendation", "review_reason", "resolution"]:
        if key in payload and not isinstance(payload[key], str):
            raise ValueError(f"{key} must be a string")
    mutable_fields = {"priority", "assigned_to", "stale_after", "sla_bucket", "review_recommendation", "review_reason", "resolution"}
    if not any(key in payload for key in mutable_fields):
        raise ValueError("at least one review field must be provided")


def list_tools() -> List[Dict[str, Any]]:
    return TOOL_SCHEMAS


def review_priority_rank(value: Any) -> int:
    priority = str(value or "").strip().lower()
    ranks = {
        "critical": 4,
        "high": 3,
        "normal": 2,
        "medium": 2,
        "low": 1,
        "": 0,
    }
    return ranks.get(priority, 0)


def enrich_tool_result(name: str, result_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    enriched = dict(payload)
    enriched["ok"] = True
    enriched["tool_name"] = name
    enriched["result_type"] = result_type
    return enriched


def maybe_replay_idempotent_tool_result(name: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    idempotency_key = str(payload.get("idempotency_key", "")).strip()
    if not idempotency_key:
        return None
    replayed = replay_idempotency_result(name, idempotency_key)
    if not replayed:
        return None
    return enrich_tool_result(name, "mutation", replayed)


def finalize_idempotent_tool_result(name: str, payload: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    idempotency_key = str(payload.get("idempotency_key", "")).strip()
    if not idempotency_key:
        return result
    return record_idempotency_result(name, idempotency_key, result)


def tool_schema_contract_report() -> Dict[str, Any]:
    schema_names = {item["name"] for item in TOOL_SCHEMAS}
    expected_names = {
        "get_review",
        "list_reviews",
        "request_review",
        "resolve_review",
        "update_review",
        "get_plan",
        "get_qa",
        "get_health",
        "validate_plan",
        "get_history",
        "restore_revision",
        "preview_restore",
        "run_reference_discovery",
        "capture_evidence_cycle",
        "replan",
        "update_plan",
        "add_evidence",
        "add_hypothesis",
        "record_view_transition",
        "record_inquiry_item",
        "record_reference_encounter",
        "record_development_probe",
        "record_open_question",
    }
    missing = sorted(expected_names - schema_names)
    unexpected = sorted(schema_names - expected_names)
    missing_validators = sorted(name for name in schema_names if name in TOOL_VALIDATORS and TOOL_VALIDATORS[name] not in globals())
    additional_properties_true = sorted(
        item["name"]
        for item in TOOL_SCHEMAS
        if item.get("input_schema", {}).get("additionalProperties") is not False
    )
    mutation_tools_missing_expected_fingerprint = sorted(
        item["name"]
        for item in TOOL_SCHEMAS
        if item["name"] in MUTATION_TOOLS
        and "expected_fingerprint" not in item.get("input_schema", {}).get("properties", {})
    )
    return {
        "matches": not any(
            [
                missing,
                unexpected,
                missing_validators,
                additional_properties_true,
                mutation_tools_missing_expected_fingerprint,
            ]
        ),
        "tool_count": len(TOOL_SCHEMAS),
        "missing": missing,
        "unexpected": unexpected,
        "missing_validators": missing_validators,
        "additional_properties_true": additional_properties_true,
        "mutation_tools_missing_expected_fingerprint": mutation_tools_missing_expected_fingerprint,
    }


def append_structured_record_tool(
    name: str,
    payload: Dict[str, Any],
    validator,
    collection: str,
    record: Dict[str, Any],
    event_type: str,
    reason: str,
) -> Dict[str, Any]:
    validator(payload)
    replayed = maybe_replay_idempotent_tool_result(name, payload)
    if replayed:
        return replayed
    plan = mutate_plan_state(
        lambda current: current.setdefault(collection, []).append(record),
        event_payloads=[
            {
                "ts": record["ts"],
                "type": event_type,
                "source": name,
                "record_id": str(record.get("id", "")),
            }
        ],
        expected_fingerprint=payload.get("expected_fingerprint"),
        revision_source=name,
        revision_reason=reason,
    )
    response = {
        "plan": plan,
        "record": record,
        "summary": plan_summary(plan),
        "validation": validate_plan_shape(plan),
        "fingerprint": plan_response(plan)["fingerprint"],
        "qa": qa_report(plan),
    }
    return enrich_tool_result(
        name,
        "mutation",
        finalize_idempotent_tool_result(name, payload, response),
    )


def execute_tool(name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if name == "get_plan":
        plan = load_plan()
        return enrich_tool_result(name, "plan", plan_response(plan))

    if name == "get_review":
        validate_get_review_payload(payload)
        request_id = str(payload.get("request_id", "")).strip()
        plan = load_plan()
        review_request = next(
            (
                item
                for item in plan.get("human_escalations", [])
                if isinstance(item, dict) and str(item.get("id", "")).strip() == request_id
            ),
            None,
        )
        if not review_request:
            raise ValueError(f"unknown review request: {request_id}")
        return enrich_tool_result(
            name,
            "review",
            {
                "review": review_request,
            },
        )

    if name == "list_reviews":
        validate_list_reviews_payload(payload)
        plan = load_plan()
        status_filter = str(payload.get("status", "")).strip()
        scope_filter = str(payload.get("scope", "")).strip()
        assigned_to_filter = str(payload.get("assigned_to", "")).strip()
        sort_by = str(payload.get("sort_by", "")).strip() or "requested_at"
        order = str(payload.get("order", "")).strip() or "desc"
        limit = int(payload.get("limit", 20) or 20)
        items = [
            item
            for item in plan.get("human_escalations", [])
            if isinstance(item, dict)
            and (not status_filter or str(item.get("status", "")).strip() == status_filter)
            and (not scope_filter or str(item.get("scope", "")).strip() == scope_filter)
            and (not assigned_to_filter or str(item.get("assigned_to", "")).strip() == assigned_to_filter)
        ]
        reverse = order == "desc"
        if sort_by == "priority":
            items = sorted(
                items,
                key=lambda item: (
                    review_priority_rank(item.get("priority", "")),
                    str(item.get("requested_at", "")).strip(),
                    str(item.get("id", "")).strip(),
                ),
                reverse=reverse,
            )
        elif sort_by == "status":
            items = sorted(
                items,
                key=lambda item: (
                    str(item.get("status", "")).strip(),
                    str(item.get("requested_at", "")).strip(),
                    str(item.get("id", "")).strip(),
                ),
                reverse=reverse,
            )
        elif sort_by == "stale_after":
            items_with_deadline = [
                item for item in items if str(item.get("stale_after", "")).strip()
            ]
            items_without_deadline = [
                item for item in items if not str(item.get("stale_after", "")).strip()
            ]
            items_with_deadline = sorted(
                items_with_deadline,
                key=lambda item: (
                    str(item.get("stale_after", "")).strip(),
                    str(item.get("requested_at", "")).strip(),
                    str(item.get("id", "")).strip(),
                ),
                reverse=reverse,
            )
            items = items_with_deadline + items_without_deadline
        else:
            items = sorted(
                items,
                key=lambda item: str(item.get("requested_at", "")).strip(),
                reverse=reverse,
            )
        items = items[: max(0, limit)]
        return enrich_tool_result(
            name,
            "reviews",
            {
                "reviews": items,
                "count": len(items),
                "filters": {
                    "status": status_filter,
                    "scope": scope_filter,
                    "assigned_to": assigned_to_filter,
                    "sort_by": sort_by,
                    "order": order,
                    "limit": limit,
                },
            },
        )

    if name == "request_review":
        validate_request_review_payload(payload)
        replayed = maybe_replay_idempotent_tool_result(name, payload)
        if replayed:
            return replayed
        scope = str(payload.get("scope", "")).strip()
        reason = str(payload.get("reason", "")).strip()
        request_id = str(payload.get("request_id", "")).strip() or f"review-{uuid4().hex[:12]}"
        request_record = {
            "id": request_id,
            "status": str(payload.get("status", "")).strip() or "open",
            "scope": scope,
            "reason": reason,
            "requested_at": now_iso(),
            "requested_by": str(payload.get("requested_by", "")).strip() or "palamedes",
            "priority": str(payload.get("priority", "")).strip() or "normal",
            "assigned_to": str(payload.get("assigned_to", "")).strip(),
            "stale_after": str(payload.get("stale_after", "")).strip(),
            "sla_bucket": str(payload.get("sla_bucket", "")).strip(),
            "review_recommendation": str(payload.get("review_recommendation", "")).strip(),
            "review_reason": str(payload.get("review_reason", "")).strip(),
            "related_evidence": [item.strip() for item in payload.get("related_evidence", []) if isinstance(item, str) and item.strip()],
            "related_references": [item.strip() for item in payload.get("related_references", []) if isinstance(item, str) and item.strip()],
        }
        plan = mutate_plan_state(
            lambda current_plan: current_plan.setdefault("human_escalations", []).append(request_record),
            event_payloads=[
                {
                    "ts": now_iso(),
                    "type": "human_review_requested",
                    "source": "request_review",
                    "request_id": request_id,
                    "scope": scope,
                }
            ],
            expected_fingerprint=payload.get("expected_fingerprint"),
            revision_source="request_review",
            revision_reason=reason,
        )
        response = {
            "plan": plan,
            "review_request": request_record,
            "summary": plan_summary(plan),
            "validation": validate_plan_shape(plan),
            "fingerprint": plan_response(plan)["fingerprint"],
            "qa": qa_report(plan),
        }
        return enrich_tool_result(name, "mutation", finalize_idempotent_tool_result(name, payload, response))

    if name == "resolve_review":
        validate_resolve_review_payload(payload)
        replayed = maybe_replay_idempotent_tool_result(name, payload)
        if replayed:
            return replayed
        request_id = str(payload.get("request_id", "")).strip()
        status = str(payload.get("status", "")).strip()
        resolution = str(payload.get("resolution", "")).strip()
        resolved_by = str(payload.get("resolved_by", "")).strip() or "palamedes"

        def apply_resolution(current_plan: Dict[str, Any]) -> None:
            escalations = current_plan.get("human_escalations", [])
            if not isinstance(escalations, list):
                raise ValueError("human_escalations must be an array")
            for item in escalations:
                if not isinstance(item, dict):
                    continue
                if str(item.get("id", "")).strip() != request_id:
                    continue
                item["status"] = status
                item["resolved_at"] = now_iso()
                item["resolved_by"] = resolved_by
                if resolution:
                    item["resolution"] = resolution
                if "assigned_to" in payload:
                    item["assigned_to"] = str(payload.get("assigned_to", "")).strip()
                if "review_recommendation" in payload:
                    item["review_recommendation"] = str(payload.get("review_recommendation", "")).strip()
                if "review_reason" in payload:
                    item["review_reason"] = str(payload.get("review_reason", "")).strip()
                return
            raise ValueError(f"unknown review request: {request_id}")

        plan = mutate_plan_state(
            apply_resolution,
            event_payloads=[
                {
                    "ts": now_iso(),
                    "type": "human_review_updated",
                    "source": "resolve_review",
                    "request_id": request_id,
                    "status": status,
                }
            ],
            expected_fingerprint=payload.get("expected_fingerprint"),
            revision_source="resolve_review",
            revision_reason=f"{request_id}:{status}",
        )
        review_request = next(
            (
                item
                for item in plan.get("human_escalations", [])
                if isinstance(item, dict) and str(item.get("id", "")).strip() == request_id
            ),
            None,
        )
        response = {
            "plan": plan,
            "review_request": review_request or {},
            "summary": plan_summary(plan),
            "validation": validate_plan_shape(plan),
            "fingerprint": plan_response(plan)["fingerprint"],
            "qa": qa_report(plan),
        }
        return enrich_tool_result(name, "mutation", finalize_idempotent_tool_result(name, payload, response))

    if name == "update_review":
        validate_update_review_payload(payload)
        replayed = maybe_replay_idempotent_tool_result(name, payload)
        if replayed:
            return replayed
        request_id = str(payload.get("request_id", "")).strip()

        def apply_update(current_plan: Dict[str, Any]) -> None:
            escalations = current_plan.get("human_escalations", [])
            if not isinstance(escalations, list):
                raise ValueError("human_escalations must be an array")
            for item in escalations:
                if not isinstance(item, dict):
                    continue
                if str(item.get("id", "")).strip() != request_id:
                    continue
                for key in ["priority", "assigned_to", "stale_after", "sla_bucket", "review_recommendation", "review_reason", "resolution"]:
                    if key in payload:
                        item[key] = str(payload.get(key, "")).strip()
                return
            raise ValueError(f"unknown review request: {request_id}")

        plan = mutate_plan_state(
            apply_update,
            event_payloads=[
                {
                    "ts": now_iso(),
                    "type": "human_review_triaged",
                    "source": "update_review",
                    "request_id": request_id,
                }
            ],
            expected_fingerprint=payload.get("expected_fingerprint"),
            revision_source="update_review",
            revision_reason=request_id,
        )
        review_request = next(
            (
                item
                for item in plan.get("human_escalations", [])
                if isinstance(item, dict) and str(item.get("id", "")).strip() == request_id
            ),
            None,
        )
        response = {
            "plan": plan,
            "review_request": review_request or {},
            "summary": plan_summary(plan),
            "validation": validate_plan_shape(plan),
            "fingerprint": plan_response(plan)["fingerprint"],
            "qa": qa_report(plan),
        }
        return enrich_tool_result(name, "mutation", finalize_idempotent_tool_result(name, payload, response))

    if name == "get_qa":
        return enrich_tool_result(name, "qa", qa_report(load_plan()))

    if name == "get_health":
        return enrich_tool_result(name, "health", storage_health_report())

    if name == "get_history":
        validate_history_payload(payload)
        return enrich_tool_result(name, "history", {"revisions": list_revisions(int(payload.get("limit", 10)))})

    if name == "validate_plan":
        return enrich_tool_result(name, "validation", validate_plan_shape(load_plan()))

    if name == "restore_revision":
        validate_restore_payload(payload)
        revision = resolve_revision_reference(str(payload.get("revision_id", "")).strip(), bool(payload.get("previous", False)))
        plan = mutate_plan_state(
            lambda current_plan: (
                current_plan.clear(),
                current_plan.update(json.loads(json.dumps(revision["plan"]))),
            ),
            event_payloads=[
                {
                    "ts": now_iso(),
                    "type": "plan_restored",
                    "source": "restore_revision",
                    "revision_id": revision["revision_id"],
                }
            ],
            expected_fingerprint=payload.get("expected_fingerprint"),
            revision_source="restore_revision",
            revision_reason=f"restore:{revision['revision_id']}",
        )
        response = plan_response(plan)
        response["restored_revision_id"] = revision["revision_id"]
        response["qa"] = qa_report(plan)
        return enrich_tool_result(name, "mutation", response)

    if name == "preview_restore":
        validate_preview_restore_payload(payload)
        return enrich_tool_result(
            name,
            "restore_preview",
            restore_preview(str(payload.get("revision_id", "")).strip(), previous=bool(payload.get("previous", False))),
        )

    if name == "run_reference_discovery":
        validate_reference_discovery_payload(payload)
        plan = load_plan()
        question = str(payload.get("question", "")).strip() or str(plan.get("goal", "")).strip()
        pack = build_reference_discovery_pack(
            question=question,
            context=str(payload.get("context", "")).strip(),
            references=payload.get("references", []),
            rejected=payload.get("rejected", []),
            source_urls=payload.get("source_urls", []),
            notes=str(payload.get("notes", "")).strip(),
            review_recommendation=str(payload.get("review_recommendation", "")).strip(),
            review_reason=str(payload.get("review_reason", "")).strip(),
        )
        response = {
            "question": pack["question"],
            "context": pack["context"],
            "search_mode": pack["search_mode"],
            "trigger_signals": pack["trigger_signals"],
            "selection_criteria": pack["selection_criteria"],
            "candidate_queries": pack["candidate_queries"],
            "shortlisted_references": pack["shortlisted_references"],
            "rejected_references": pack["rejected_references"],
            "decision": pack["decision"],
            "plan_updates": pack["plan_updates"],
        }
        if bool(payload.get("apply", False)):
            record = reference_discovery_record(pack)
            result = mutate_plan_state(
                lambda current_plan: (
                    current_plan.setdefault("reference_discoveries", []).append(record),
                    current_plan.setdefault("references", []).extend(pack["shortlisted_references"]) if pack["shortlisted_references"] else None,
                    current_plan.setdefault("plan_tasks", []).extend(
                        [item for item in pack["plan_updates"]["plan_tasks"] if item not in current_plan.get("plan_tasks", [])]
                    ),
                    current_plan.setdefault("execution_tasks", []).extend(
                        [item for item in pack["plan_updates"]["execution_tasks"] if item not in current_plan.get("execution_tasks", [])]
                    ),
                    current_plan.setdefault("evolution_insights", []).extend(
                        [item for item in pack["plan_updates"]["evolution_insights"] if item not in current_plan.get("evolution_insights", [])]
                    ),
                    add_evidence(
                        current_plan,
                        f"Reference discovery logged for '{pack['question']}' via {pack['search_mode']}.",
                        "reference-discovery",
                        72,
                        "evolution",
                    ),
                ),
                expected_fingerprint=payload.get("expected_fingerprint"),
                revision_source="run_reference_discovery",
                revision_reason=pack["question"],
            )
            response["applied"] = True
            response["plan"] = result
            response["summary"] = plan_summary(result)
            response["validation"] = validate_plan_shape(result)
            response["fingerprint"] = plan_fingerprint(result)
            response["qa"] = qa_report(result)
        return enrich_tool_result(name, "reference_discovery", response)

    if name == "capture_evidence_cycle":
        validate_capture_evidence_cycle_payload(payload)
        history_limit = int(payload.get("history_limit", 10))
        before = cycle_snapshot(history_limit=history_limit)
        cycle_key = str(payload.get("idempotency_key", "")).strip()
        evidence_key = f"{cycle_key}:evidence" if cycle_key else ""
        replan_key = f"{cycle_key}:replan" if cycle_key else ""

        evidence_payload = dict(payload.get("evidence", {}) or {})
        if payload.get("expected_fingerprint"):
            evidence_payload["expected_fingerprint"] = payload.get("expected_fingerprint")
        if evidence_key:
            evidence_payload["idempotency_key"] = evidence_key
        evidence_result = execute_tool("add_evidence", evidence_payload)

        replan_payload = dict(payload.get("replan", {}) or {})
        evidence_fingerprint = str(evidence_result.get("fingerprint", "")).strip()
        if evidence_fingerprint:
            replan_payload["expected_fingerprint"] = evidence_fingerprint
        if replan_key:
            replan_payload["idempotency_key"] = replan_key
        replan_result = execute_tool("replan", replan_payload)

        after = cycle_snapshot(history_limit=history_limit)
        response = {
            "operation": "capture_evidence_cycle",
            "result_type": "planning_cycle",
            "pre_fingerprint": before.get("fingerprint", ""),
            "post_fingerprint": after.get("fingerprint", ""),
            "fingerprint": after.get("fingerprint", ""),
            "changed_fields": sorted(
                key
                for key in set(before.get("plan", {})) | set(after.get("plan", {}))
                if before.get("plan", {}).get(key) != after.get("plan", {}).get(key)
            ),
            "qa_delta": int(after.get("qa", {}).get("score", 0)) - int(before.get("qa", {}).get("score", 0)),
            "evidence_result": evidence_result,
            "replan_result": replan_result,
            "step_results": {
                "add_evidence": evidence_result,
                "replan": replan_result,
            },
            "pre_cycle": before,
            "post_cycle": after,
        }
        if cycle_key:
            response["idempotency_key"] = cycle_key
        return enrich_tool_result(name, "planning_cycle", response)

    if name == "replan":
        validate_replan_payload(payload)
        replayed = maybe_replay_idempotent_tool_result(name, payload)
        if replayed:
            return replayed
        result = mutate_plan_state(
            lambda plan: apply_replan_payload(plan, payload),
            include_autoreplan=True,
            expected_fingerprint=payload.get("expected_fingerprint"),
            revision_source="replan",
            revision_reason=str(payload.get("evidence", "")).strip(),
        )
        response = {
            "plan": result["plan"],
            "summary": plan_summary(result["plan"]),
            "validation": validate_plan_shape(result["plan"]),
            "fingerprint": plan_fingerprint(result["plan"]),
            "qa": result["qa"],
            "auto_replan": result["auto_replan"],
        }
        return enrich_tool_result(name, "mutation", finalize_idempotent_tool_result(name, payload, response))

    if name == "update_plan":
        validate_update_payload(payload)
        result = mutate_plan_state(
            lambda plan: merge_plan_updates(plan, payload),
            include_autoreplan=True,
            expected_fingerprint=payload.get("expected_fingerprint"),
            revision_source="update_plan",
            revision_reason=str(payload.get("goal", "")).strip(),
        )
        return enrich_tool_result(name, "mutation", {
            "plan": result["plan"],
            "summary": plan_summary(result["plan"]),
            "validation": validate_plan_shape(result["plan"]),
            "fingerprint": plan_fingerprint(result["plan"]),
            "qa": result["qa"],
            "auto_replan": result["auto_replan"],
        })

    if name == "add_evidence":
        validate_evidence_payload(payload)
        replayed = maybe_replay_idempotent_tool_result(name, payload)
        if replayed:
            return replayed
        claim = str(payload.get("claim", "")).strip()
        evidence_metadata = {
            key: payload[key]
            for key in [
                "reference",
                "source_url",
                "field",
                "selector",
                "observed_value",
                "expected_value",
                "note",
                "evidence_type",
                "review_recommendation",
                "review_reason",
            ]
            if key in payload
        }
        plan = mutate_plan_state(
            lambda plan: (
                add_evidence(
                    plan,
                    claim,
                    str(payload.get("source", "agent")).strip() or "agent",
                    int(payload.get("confidence", 60)),
                    str(payload.get("axis", "")).strip(),
                    str(payload.get("date", "")).strip(),
                    evidence_metadata,
                ),
                plan.setdefault("references", []).append(payload["reference"].strip())
                if isinstance(payload.get("reference"), str) and payload["reference"].strip()
                else None,
            ),
            expected_fingerprint=payload.get("expected_fingerprint"),
            revision_source="add_evidence",
            revision_reason=claim,
        )
        response = {"plan": plan, "summary": plan_summary(plan), "validation": validate_plan_shape(plan), "fingerprint": plan_response(plan)["fingerprint"], "qa": qa_report(plan)}
        return enrich_tool_result(
            name,
            "mutation",
            finalize_idempotent_tool_result(name, payload, response),
        )

    if name == "add_hypothesis":
        validate_hypothesis_payload(payload)
        replayed = maybe_replay_idempotent_tool_result(name, payload)
        if replayed:
            return replayed
        hypothesis = str(payload.get("hypothesis", "")).strip()
        status = str(payload.get("status", "open")).strip() or "open"
        evidence = str(payload.get("evidence", "")).strip()
        plan = mutate_plan_state(
            lambda plan: (
                plan.setdefault("hypothesis_log", []).append(
                    {
                        "ts": now_iso(),
                        "hypothesis": hypothesis,
                        "metric": str(payload.get("metric", "")).strip(),
                        "target": str(payload.get("target", "")).strip(),
                        "window": str(payload.get("window", "")).strip(),
                        "status": status,
                        "outcome": str(payload.get("outcome", "")).strip(),
                    }
                ),
                add_evidence(
                    plan,
                    evidence,
                    "hypothesis-test",
                    int(payload.get("confidence", 60)),
                    str(payload.get("axis", "")).strip(),
                    str(payload.get("date", "")).strip(),
                )
                if evidence
                else None,
            ),
            expected_fingerprint=payload.get("expected_fingerprint"),
            revision_source="add_hypothesis",
            revision_reason=hypothesis,
        )
        response = {"plan": plan, "summary": plan_summary(plan), "validation": validate_plan_shape(plan), "fingerprint": plan_response(plan)["fingerprint"], "qa": qa_report(plan)}
        return enrich_tool_result(
            name,
            "mutation",
            finalize_idempotent_tool_result(name, payload, response),
        )

    if name == "record_view_transition":
        validate_view_transition_payload(payload)
        replayed = maybe_replay_idempotent_tool_result(name, payload)
        if replayed:
            return replayed
        transition = {
            "ts": now_iso(),
            "previous_view": str(payload.get("previous_view", "")).strip(),
            "trigger": str(payload.get("trigger", "")).strip(),
            "new_view": str(payload.get("new_view", "")).strip(),
            "new_blind_spots": str(payload.get("new_blind_spots", "")).strip(),
            "opened_paths": list(payload.get("opened_paths", [])),
            "next_probe": str(payload.get("next_probe", "")).strip(),
            "source": str(payload.get("source", "")).strip() or "agent",
            "references": list(payload.get("references", [])),
            "plan_effect": str(payload.get("plan_effect", "none")).strip() or "none",
            "plan_effect_reason": str(payload.get("plan_effect_reason", "")).strip(),
        }
        plan = mutate_plan_state(
            lambda plan: plan.setdefault("view_transitions", []).append(transition),
            event_payloads=[
                {
                    "ts": transition["ts"],
                    "type": "view_transition_recorded",
                    "source": "record_view_transition",
                    "trigger": transition["trigger"],
                    "new_view": transition["new_view"],
                }
            ],
            expected_fingerprint=payload.get("expected_fingerprint"),
            revision_source="record_view_transition",
            revision_reason=transition["trigger"],
        )
        response = {
            "plan": plan,
            "transition": transition,
            "summary": plan_summary(plan),
            "validation": validate_plan_shape(plan),
            "fingerprint": plan_response(plan)["fingerprint"],
            "qa": qa_report(plan),
        }
        return enrich_tool_result(
            name,
            "mutation",
            finalize_idempotent_tool_result(name, payload, response),
        )

    if name == "record_inquiry_item":
        record = {
            "ts": now_iso(),
            "statement": str(payload.get("statement", "")).strip(),
            "kind": str(payload.get("kind", "")).strip(),
            "status": str(payload.get("status", "open")).strip() or "open",
            "intent": str(payload.get("intent", "")).strip(),
            "commitment": str(payload.get("commitment", "none")).strip() or "none",
            "source": str(payload.get("source", "agent")).strip() or "agent",
            "opened_questions": list(payload.get("opened_questions", [])),
            "references": list(payload.get("references", [])),
        }
        return append_structured_record_tool(name, payload, validate_inquiry_tool_payload, "inquiry_items", record, "inquiry_item_recorded", record["statement"])

    if name == "record_reference_encounter":
        record = {
            "ts": now_iso(),
            "reference": str(payload.get("reference", "")).strip(),
            "encountered_while": str(payload.get("encountered_while", "")).strip(),
            "initial_interest": str(payload.get("initial_interest", "")).strip(),
            "relation": str(payload.get("relation", "")).strip(),
            "effect": str(payload.get("effect", "")).strip(),
            "adoption": str(payload.get("adoption", "not_decided")).strip() or "not_decided",
            "later_outcome": str(payload.get("later_outcome", "")).strip(),
            "source": str(payload.get("source", "agent")).strip() or "agent",
        }
        return append_structured_record_tool(name, payload, validate_reference_encounter_tool_payload, "reference_encounters", record, "reference_encounter_recorded", record["reference"])

    if name == "record_development_probe":
        ts = now_iso()
        step = str(payload.get("step", "")).strip()
        record = {
            "id": str(payload.get("id", "")).strip() or record_id("probe", step, ts),
            "ts": ts,
            "step": step,
            "expected_learning": str(payload.get("expected_learning", "")).strip(),
            "expected_result": str(payload.get("expected_result", "")).strip(),
            "status": str(payload.get("status", "planned")).strip() or "planned",
            "actual_observation": str(payload.get("actual_observation", "")).strip(),
            "unexpected_observation": str(payload.get("unexpected_observation", "")).strip(),
            "view_transition_id": str(payload.get("view_transition_id", "")).strip(),
            "next_step": str(payload.get("next_step", "")).strip(),
            "source": str(payload.get("source", "agent")).strip() or "agent",
            "references": list(payload.get("references", [])),
        }
        return append_structured_record_tool(name, payload, validate_development_probe_tool_payload, "development_probes", record, "development_probe_recorded", record["step"])

    if name == "record_open_question":
        ts = now_iso()
        question = str(payload.get("question", "")).strip()
        record = {
            "id": str(payload.get("id", "")).strip() or record_id("question", question, ts),
            "ts": ts,
            "question": question,
            "perspectives": list(payload.get("perspectives", [])),
            "resolution": str(payload.get("resolution", "intentionally_open")).strip() or "intentionally_open",
            "revisit_when": str(payload.get("revisit_when", "")).strip(),
            "source": str(payload.get("source", "agent")).strip() or "agent",
            "references": list(payload.get("references", [])),
        }
        return append_structured_record_tool(name, payload, validate_open_question_tool_payload, "open_questions", record, "open_question_recorded", record["question"])

    raise ValueError(f"unknown tool: {name}")


def coerce_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered.isdigit() or (lowered.startswith("-") and lowered[1:].isdigit()):
        return int(lowered)
    return value


def parse_assignment_tokens(tokens: List[str]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    for token in tokens:
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        if key in LIST_PLAN_FIELDS:
            payload[key] = parse_csv(value)
        else:
            payload[key] = coerce_scalar(value)
    return payload


def slash_to_tool(command: str) -> Tuple[str, Dict[str, Any]]:
    tokens = shlex.split(command)
    if not tokens:
        raise ValueError("empty input")
    head = tokens[0].strip()
    payload = parse_assignment_tokens(tokens[1:])

    mapping = {
        "/palamedes": "update_plan",
        "/palamedes.plan": "update_plan",
        "/palamedes.replan": "replan",
        "/palamedes.capture": "capture_evidence_cycle",
        "/palamedes.review": "get_review",
        "/palamedes.reviews": "list_reviews",
        "/palamedes.show": "get_plan",
        "/palamedes.history": "get_history",
        "/palamedes.restore": "restore_revision",
        "/palamedes.restore-preview": "preview_restore",
        "/palamedes.discover": "run_reference_discovery",
        "/palamedes.health": "get_health",
        "/palamedes.qa": "get_qa",
        "/palamedes.validate": "validate_plan",
        "/palamedes.review-request": "request_review",
        "/palamedes.review-resolve": "resolve_review",
        "/palamedes.review-update": "update_review",
        "/palamedes.evidence": "add_evidence",
        "/palamedes.hypothesis": "add_hypothesis",
        "/palamedes.view": "record_view_transition",
        "/palamedes.inquiry": "record_inquiry_item",
        "/palamedes.encounter": "record_reference_encounter",
        "/palamedes.probe": "record_development_probe",
        "/palamedes.question": "record_open_question",
    }
    tool_name = mapping.get(head)
    if not tool_name:
        raise ValueError(f"unsupported slash command: {head}")
    if tool_name == "record_view_transition":
        for key in ["opened_paths", "references"]:
            if isinstance(payload.get(key), str):
                payload[key] = parse_csv(payload[key])
    if tool_name == "record_inquiry_item":
        for key in ["opened_questions", "references"]:
            if isinstance(payload.get(key), str):
                payload[key] = parse_csv(payload[key])
    if tool_name == "record_development_probe" and isinstance(payload.get("references"), str):
        payload["references"] = parse_csv(payload["references"])
    if tool_name == "record_open_question":
        if isinstance(payload.get("references"), str):
            payload["references"] = parse_csv(payload["references"])
        if isinstance(payload.get("perspectives"), str):
            try:
                payload["perspectives"] = json.loads(payload["perspectives"])
            except json.JSONDecodeError as exc:
                raise ValueError(f"perspectives must be valid JSON: {exc}") from exc
    return tool_name, payload


def natural_language_to_tool(text: str) -> Tuple[str, Dict[str, Any]]:
    stripped = text.strip()
    lowered = stripped.lower()
    if stripped.startswith("/"):
        return slash_to_tool(stripped)
    if any(phrase in lowered for phrase in ["qa", "quality check", "quality status"]):
        return "get_qa", {}
    if any(phrase in lowered for phrase in ["health", "status health", "storage health"]):
        return "get_health", {}
    if lowered.startswith("preview restore "):
        return "preview_restore", parse_assignment_tokens(shlex.split(stripped[len("preview restore ") :]))
    if lowered == "preview previous revision":
        return "preview_restore", {"previous": True}
    if any(phrase in lowered for phrase in ["list reviews", "show reviews", "open reviews"]):
        return "list_reviews", {}
    if lowered.startswith("show review "):
        return "get_review", parse_assignment_tokens(shlex.split(stripped[len("show review ") :]))
    if any(phrase in lowered for phrase in ["history", "revision history", "plan history"]):
        return "get_history", {}
    if any(phrase in lowered for phrase in ["validate plan", "plan validation", "check plan structure"]):
        return "validate_plan", {}
    if lowered.startswith("capture evidence cycle "):
        return "capture_evidence_cycle", parse_assignment_tokens(shlex.split(stripped[len("capture evidence cycle ") :]))
    if lowered.startswith("replan "):
        return "replan", parse_assignment_tokens(shlex.split(stripped[len("replan ") :]))
    if lowered.startswith("reference discovery "):
        return "run_reference_discovery", parse_assignment_tokens(shlex.split(stripped[len("reference discovery ") :]))
    if lowered.startswith("discover references "):
        return "run_reference_discovery", parse_assignment_tokens(shlex.split(stripped[len("discover references ") :]))
    if any(phrase in lowered for phrase in ["show plan", "current plan", "plan summary", "what is the plan"]):
        return "get_plan", {}
    if lowered.startswith("restore revision "):
        return "restore_revision", parse_assignment_tokens(shlex.split(stripped[len("restore revision ") :]))
    if lowered == "restore previous revision":
        return "restore_revision", {"previous": True}
    if lowered.startswith("add evidence "):
        return "add_evidence", parse_assignment_tokens(shlex.split(stripped[len("add evidence ") :]))
    if lowered.startswith("request review "):
        return "request_review", parse_assignment_tokens(shlex.split(stripped[len("request review ") :]))
    if lowered.startswith("resolve review "):
        return "resolve_review", parse_assignment_tokens(shlex.split(stripped[len("resolve review ") :]))
    if lowered.startswith("update review "):
        return "update_review", parse_assignment_tokens(shlex.split(stripped[len("update review ") :]))
    if lowered.startswith("update plan "):
        return "update_plan", parse_assignment_tokens(shlex.split(stripped[len("update plan ") :]))
    if lowered.startswith("add hypothesis "):
        return "add_hypothesis", parse_assignment_tokens(shlex.split(stripped[len("add hypothesis ") :]))
    if lowered.startswith("record view "):
        return slash_to_tool(f"/palamedes.view {stripped[len('record view '):]}")
    if lowered.startswith("record inquiry "):
        return slash_to_tool(f"/palamedes.inquiry {stripped[len('record inquiry '):]}")
    if lowered.startswith("record reference encounter "):
        return slash_to_tool(f"/palamedes.encounter {stripped[len('record reference encounter '):]}")
    if lowered.startswith("record development probe "):
        return slash_to_tool(f"/palamedes.probe {stripped[len('record development probe '):]}")
    if lowered.startswith("record open question "):
        return slash_to_tool(f"/palamedes.question {stripped[len('record open question '):]}")
    raise ValueError("could not map input to a Palamedes tool")


def cmd_tools(_: argparse.Namespace) -> None:
    print(json.dumps({"tools": list_tools()}, indent=2, ensure_ascii=False))


def cmd_run(args: argparse.Namespace) -> None:
    try:
        tool_name, payload = natural_language_to_tool(args.input)
    except ValueError as exc:
        raise SystemExit(str(exc))
    envelope = {"tool": tool_name, "input": payload}
    if args.dry_run:
        print(json.dumps(envelope, indent=2, ensure_ascii=False))
        return
    try:
        result = execute_tool(tool_name, payload)
    except ValueError as exc:
        raise SystemExit(str(exc))
    print(json.dumps({"tool": tool_name, "input": payload, "result": result}, indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Palamedes local agent wrapper")
    sub = parser.add_subparsers(dest="command", required=True)

    s = sub.add_parser("tools")
    s.set_defaults(func=cmd_tools)

    s = sub.add_parser("run")
    s.add_argument("--input", type=str, required=True)
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(func=cmd_run)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
