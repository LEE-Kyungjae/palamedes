#!/usr/bin/env python3
"""Deterministic low-cost cycle preflight with explicit escalation reasons."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Iterable, List


ROUTER_VERSION = "palamedes-cost-router/1"
MODE_BUDGETS = {
    "lookup": {
        "provider_calls_min": 0,
        "provider_calls_max": 1,
        "token_budget_high": 25000,
        "time_minutes_high": 2,
    },
    "micro": {
        "provider_calls_min": 1,
        "provider_calls_max": 2,
        "token_budget_high": 50000,
        "time_minutes_high": 5,
    },
    "component": {
        "provider_calls_min": 2,
        "provider_calls_max": 4,
        "token_budget_high": 140000,
        "time_minutes_high": 15,
    },
    "product": {
        "provider_calls_min": 4,
        "provider_calls_max": 12,
        "token_budget_high": 400000,
        "time_minutes_high": 45,
    },
}
HIGH_RISK_FLAGS = {
    "security",
    "privacy",
    "payment",
    "destructive_delete",
    "migration",
    "public_api",
    "deployment",
    "storage_binding",
    "irreversible",
}
PRODUCT_ESCALATION_FLAGS = {"cross_surface", "product_invariant_conflict"}


def infer_route_request(
    objective: str,
    assessments: Iterable[Dict[str, Any]] = (),
) -> Dict[str, Any]:
    lowered = objective.lower()
    keyword_flags = {
        "security": ("security", "보안", "auth", "인증"),
        "privacy": ("privacy", "개인정보"),
        "payment": ("payment", "결제", "billing"),
        "destructive_delete": ("delete", "삭제", "purge"),
        "migration": ("migration", "마이그레이션", "schema change"),
        "public_api": ("public api", "공개 api"),
        "deployment": ("deploy", "배포", "production"),
        "storage_binding": ("storage", "저장소", "database", "db 연결"),
        "irreversible": ("irreversible", "비가역"),
        "product_invariant_conflict": ("invariant", "불변 조건", "제품 방향"),
        "cross_surface": ("cross-surface", "교차 surface", "전체 여정"),
    }
    flags = sorted(
        flag
        for flag, needles in keyword_flags.items()
        if any(needle in lowered for needle in needles)
    )
    local_markers = (
        "one file",
        "single file",
        "one function",
        "single function",
        "local fix",
        "한 파일",
        "함수 하나",
        "국소 수정",
        "작은 수정",
        "오타",
    )
    broad_markers = (
        "architecture",
        "아키텍처",
        "product",
        "제품",
        "journey",
        "전체",
        "multi",
        "여러 파일",
        "통합",
    )
    estimated_files = 1 if any(marker in lowered for marker in local_markers) else 4
    if any(marker in lowered for marker in broad_markers):
        estimated_files = max(estimated_files, 9)
    matched_assessment = None
    for assessment in assessments:
        requirement_id = str(assessment.get("requirement_id", "")).strip()
        if requirement_id and requirement_id.lower() in lowered:
            matched_assessment = assessment
            break
    return {
        "objective": objective,
        "estimated_files": estimated_files,
        "surface_keys": [],
        "risk_flags": flags,
        "satisfaction": matched_assessment or {},
        "inference_custody": "deterministic_keyword_preflight",
    }


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def route_cycle(request: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("cycle route request must be an object")
    objective = str(request.get("objective", "")).strip()
    if not objective:
        raise ValueError("cycle route objective is required")
    estimated_files = request.get("estimated_files", 1)
    if (
        not isinstance(estimated_files, int)
        or isinstance(estimated_files, bool)
        or estimated_files < 0
    ):
        raise ValueError("estimated_files must be a non-negative integer")
    surfaces = request.get("surface_keys", [])
    if not isinstance(surfaces, list) or not all(
        isinstance(item, str) and item.strip() for item in surfaces
    ):
        raise ValueError("surface_keys must be a string array")
    risk_flags = request.get("risk_flags", [])
    if not isinstance(risk_flags, list) or not all(
        isinstance(item, str) and item.strip() for item in risk_flags
    ):
        raise ValueError("risk_flags must be a string array")
    risk_flags = sorted(set(risk_flags))
    unknown_risks = sorted(set(risk_flags) - HIGH_RISK_FLAGS - PRODUCT_ESCALATION_FLAGS)
    satisfaction = request.get("satisfaction", {})
    disposition = (
        satisfaction.get("disposition") if isinstance(satisfaction, dict) else None
    )
    reasons: List[str] = []

    if disposition == "already_satisfied":
        mode = "lookup"
        reasons.append(
            "host-verified current snapshot already satisfies the requirement"
        )
    elif disposition == "refresh_evidence":
        mode = "lookup"
        reasons.append("implementation evidence exists but must be refreshed")
    elif set(risk_flags) & PRODUCT_ESCALATION_FLAGS or len(set(surfaces)) > 1:
        mode = "product"
        reasons.append("cross-surface or product-invariant reasoning is required")
    elif set(risk_flags) & HIGH_RISK_FLAGS:
        mode = "component"
        reasons.append(
            "high-risk operation requires adversarial and integration review"
        )
    elif estimated_files <= 1 and len(set(surfaces)) <= 1:
        mode = "micro"
        reasons.append("bounded single-surface change")
    elif estimated_files <= 8 and len(set(surfaces)) <= 1:
        mode = "component"
        reasons.append("multi-file integration boundary")
    else:
        mode = "product"
        reasons.append("broad scope exceeds component budget")
    if unknown_risks:
        prior = mode
        mode = "product"
        reasons.append(
            "unknown risk flags fail closed and require product-mode classification: "
            + ", ".join(unknown_risks)
        )
        if prior == "product":
            reasons.append("product mode was already selected")

    budget = dict(MODE_BUDGETS[mode])
    if disposition == "already_satisfied":
        budget.update(
            {
                "provider_calls_min": 0,
                "provider_calls_max": 0,
                "token_budget_high": 0,
                "time_minutes_high": 1,
            }
        )
    core = {
        "router_version": ROUTER_VERSION,
        "objective": objective,
        "mode": mode,
        "budget": budget,
        "reasons": reasons,
        "risk_flags": risk_flags,
        "surface_keys": sorted(set(surfaces)),
        "estimated_files": estimated_files,
        "satisfaction_disposition": disposition,
        "escalation_required": mode in {"component", "product"},
        "manual_override_allowed": True,
    }
    core["route_id"] = f"route-{_fingerprint(core)[:16]}"
    return core
