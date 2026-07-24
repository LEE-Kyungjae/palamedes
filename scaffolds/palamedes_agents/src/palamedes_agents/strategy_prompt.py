#!/usr/bin/env python3
import json
from pathlib import Path
from typing import Any, Dict, List

from palamedes_agents.reference_rag import build_reference_rag_context


PACKAGE_ROOT = Path(__file__).resolve().parent
PROMPT_PATH = PACKAGE_ROOT / "prompts" / "strategist-system.md"
SCHEMA_PATH = PACKAGE_ROOT / "schemas" / "strategy-report.schema.json"


def load_strategy_system_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8").strip()


def load_strategy_report_schema() -> Dict[str, Any]:
    payload = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("strategy report schema must be a JSON object")
    return payload


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _strategy_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        key: value
        for key, value in payload.items()
        if key not in {"reference_corpus", "reference_store_path", "reference_semantic_scores"}
    }


def _compact_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    keys = [
        "goal",
        "success_metric",
        "selected_option",
        "planning_horizon",
        "review_cadence",
        "references",
        "reference_discoveries",
        "insights",
        "direction_insights",
        "market_insights",
        "differentiation_insights",
        "monetization_insights",
        "risk_signal_insights",
        "evidence",
        "hypothesis_log",
        "risks",
        "plan_tasks",
        "definition_of_done",
    ]
    compact: Dict[str, Any] = {}
    for key in keys:
        if key in plan:
            value = plan[key]
            if isinstance(value, list):
                compact[key] = value[:5]
            else:
                compact[key] = value
    return compact


def compact_strategy_snapshot(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    plan = _safe_dict(snapshot.get("plan"))
    qa = _safe_dict(snapshot.get("qa"))
    health = _safe_dict(snapshot.get("health"))
    checks = qa.get("checks", [])
    failed_checks = [
        {
            "name": str(item.get("name", "")).strip(),
            "detail": str(item.get("detail", "")).strip(),
            "critical": bool(item.get("critical", False)),
        }
        for item in checks
        if isinstance(item, dict) and not bool(item.get("passed", False))
    ][:5] if isinstance(checks, list) else []
    return {
        "fingerprint": str(snapshot.get("fingerprint", "")).strip(),
        "plan": _compact_plan(plan),
        "qa": {
            "result": str(qa.get("result", "")).strip(),
            "score": qa.get("score"),
            "threshold": qa.get("threshold"),
            "failed_checks": failed_checks,
        },
        "health": {
            "status": str(health.get("status", "")).strip(),
            "issues": health.get("issues", []) if isinstance(health.get("issues", []), list) else [],
        },
    }


def build_strategy_messages(payload: Dict[str, Any], snapshot: Dict[str, Any], *, action: str = "evaluate_experience_strategy") -> List[Dict[str, str]]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot must be an object")
    context = {
        "action": action,
        "idea_payload": _strategy_payload(payload),
        "palamedes_snapshot": compact_strategy_snapshot(snapshot),
        "reference_retrieval": build_reference_rag_context(payload),
        "required_output_schema": load_strategy_report_schema(),
    }
    return [
        {"role": "system", "content": load_strategy_system_prompt()},
        {
            "role": "user",
            "content": json.dumps(context, ensure_ascii=False, indent=2, sort_keys=True),
        },
    ]


def build_strategy_prompt_bundle(payload: Dict[str, Any], snapshot: Dict[str, Any], *, action: str = "evaluate_experience_strategy") -> Dict[str, Any]:
    return {
        "messages": build_strategy_messages(payload, snapshot, action=action),
        "schema": load_strategy_report_schema(),
        "reference_retrieval": build_reference_rag_context(payload),
    }
