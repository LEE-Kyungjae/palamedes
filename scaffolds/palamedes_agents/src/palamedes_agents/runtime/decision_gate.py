#!/usr/bin/env python3
from typing import Any, Dict, List, Optional


def _as_number(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def evaluate_snapshot_gate(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    health = snapshot.get("health", {}) if isinstance(snapshot, dict) else {}
    qa = snapshot.get("qa", {}) if isinstance(snapshot, dict) else {}
    health_status = str(health.get("status", "")).strip() or "unknown"
    qa_result = str(qa.get("result", "")).strip()
    reasons: List[str] = []
    decision = "continue"
    should_block_writes = False
    should_route_to_reviewer = False

    if health_status != "ok":
        decision = "block"
        should_block_writes = True
        reasons.append(f"health_not_ok:{health_status}")
    elif qa_result == "CRITICAL_FAILURE":
        decision = "review"
        should_route_to_reviewer = True
        reasons.append("qa_critical_failure")

    return {
        "decision": decision,
        "should_continue": decision == "continue",
        "should_block_writes": should_block_writes,
        "should_route_to_reviewer": should_route_to_reviewer,
        "health_status": health_status,
        "qa_result": qa_result,
        "reasons": reasons,
    }


def evaluate_cycle_gate(before: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    post_cycle = result.get("post_cycle", {}) if isinstance(result, dict) else {}
    health = post_cycle.get("health", {}) if isinstance(post_cycle, dict) else {}
    qa = post_cycle.get("qa", {}) if isinstance(post_cycle, dict) else {}
    before_qa = before.get("qa", {}) if isinstance(before, dict) else {}
    health_status = str(health.get("status", "")).strip() or "unknown"
    qa_result = str(qa.get("result", "")).strip()
    before_score = _as_number(before_qa.get("score"))
    after_score = _as_number(qa.get("score"))
    reasons: List[str] = []
    decision = "continue"
    should_block_writes = False
    should_route_to_reviewer = False

    if health_status != "ok":
        decision = "block"
        should_block_writes = True
        reasons.append(f"health_not_ok:{health_status}")
    elif qa_result == "CRITICAL_FAILURE":
        decision = "review"
        should_route_to_reviewer = True
        reasons.append("qa_critical_failure")
    elif before_score is not None and after_score is not None and after_score < before_score:
        decision = "review"
        should_route_to_reviewer = True
        reasons.append("qa_score_regressed")
    elif before_score is not None and after_score is not None and after_score > before_score:
        reasons.append("qa_score_improved")

    return {
        "decision": decision,
        "should_continue": decision == "continue",
        "should_block_writes": should_block_writes,
        "should_route_to_reviewer": should_route_to_reviewer,
        "health_status": health_status,
        "qa_result": qa_result,
        "before_qa_score": before_score,
        "after_qa_score": after_score,
        "reasons": reasons,
    }
