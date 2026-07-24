#!/usr/bin/env python3
"""Convert grounded strategy insights into Palamedes evidence/replan writes."""

import hashlib
from typing import Any, Dict, List

from palamedes_agents.adapters.palamedes_adapter import PalamedesAdapter
from palamedes_agents.workflows.strategy_loop import validate_strategy_report_shape


def _idempotency_key(insight: Dict[str, Any]) -> str:
    identity = "|".join(insight.get("reference_ids", [])) + "|" + str(insight.get("transferable_principle", ""))
    return "reference-insight-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]


def insight_write_payload(insight: Dict[str, Any]) -> Dict[str, Any]:
    reference_ids = [str(item) for item in insight.get("reference_ids", []) if str(item).strip()]
    urls = [str(item) for item in insight.get("source_urls", []) if str(item).strip()]
    assumptions = [str(item) for item in insight.get("transfer_assumptions", []) if str(item).strip()]
    disconfirming = str(insight.get("disconfirming_signal", "")).strip()
    principle = str(insight.get("transferable_principle", "")).strip()
    applied = str(insight.get("applied_to_plan", "")).strip()
    note_parts = []
    if assumptions:
        note_parts.append("Transfer assumptions: " + "; ".join(assumptions))
    if disconfirming:
        note_parts.append("Disconfirming signal: " + disconfirming)
    return {
        "idempotency_key": _idempotency_key(insight),
        "evidence": {
            "claim": principle,
            "source": str(insight.get("source", "reference-insight")).strip() or "reference-insight",
            "confidence": int(insight.get("confidence", 50)),
            "axis": "differentiation",
            "reference": ",".join(reference_ids),
            "source_url": urls[0] if urls else "",
            "note": " | ".join(note_parts),
            "evidence_type": "reference_extraction",
        },
        "replan": {
            "insight": principle,
            "differentiation_insight": applied,
        },
    }


def persist_reference_insights(adapter: PalamedesAdapter, report: Dict[str, Any]) -> Dict[str, Any]:
    errors = validate_strategy_report_shape(report)
    if errors:
        raise ValueError("invalid strategy report: " + "; ".join(errors))
    insights = report.get("reference_insights", [])
    results: List[Dict[str, Any]] = []
    for insight in insights:
        payload = insight_write_payload(insight)
        if not payload["evidence"]["claim"]:
            raise ValueError("reference insight transferable_principle must be non-empty before persistence")
        results.append(adapter.capture_evidence_cycle(payload))
    final_snapshot = adapter.snapshot()
    return {
        "ok": True,
        "type": "reference_insights_persisted",
        "applied_count": len(results),
        "idempotency_keys": [_idempotency_key(insight) for insight in insights],
        "results": results,
        "post_cycle": final_snapshot,
    }
