#!/usr/bin/env python3
"""Multi-perspective product opportunity scouting before planning."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Dict, List

from palamedes_observe import utc_now


OPPORTUNITY_VERSION = "palamedes-opportunity-scout/1"
PERSPECTIVES = (
    "user_desire",
    "repeat_behavior",
    "monetization",
    "content_economy",
    "social_dynamics",
    "live_operations",
    "distribution",
    "platform_expansion",
    "user_and_business_risk",
)
OPPORTUNITY_TYPES = {
    "established_pattern",
    "product_specific_adaptation",
    "structural_invention",
}


def fingerprint(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _object(value: Any, field: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _strings(value: Any, field: str, minimum: int = 0) -> List[str]:
    if not isinstance(value, list) or len(value) < minimum or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ValueError(f"{field} requires at least {minimum} non-empty strings")
    return [item.strip() for item in value]


def _ask(
    ask: Callable[[str, str], Dict[str, Any]],
    role: str,
    prompt: str,
    required: tuple[str, ...],
    arrays: tuple[str, ...] = (),
) -> Dict[str, Any]:
    last_error = ""
    for attempt in range(2):
        repair = "" if attempt == 0 else f"""

The previous response violated the contract: {last_error}. Return one corrected JSON
object. Required fields: {json.dumps(required)}. Array fields: {json.dumps(arrays)}.
"""
        row = _object(ask(role, prompt + repair), role)
        missing = [field for field in required if field not in row]
        wrong_arrays = [
            field for field in arrays if field in row and not isinstance(row[field], list)
        ]
        if not missing and not wrong_arrays:
            return row
        last_error = "; ".join(
            filter(None, (
                f"missing {', '.join(missing)}" if missing else "",
                f"non-array {', '.join(wrong_arrays)}" if wrong_arrays else "",
            ))
        )
    raise ValueError(f"{role} failed JSON contract after repair: {last_error}")


def _opportunity(value: Any, index: int) -> Dict[str, Any]:
    row = _object(value, f"opportunities[{index}]")
    opportunity_id = str(row.get("opportunity_id", "")).strip()
    if not opportunity_id:
        raise ValueError("every opportunity requires opportunity_id")
    for field in (
        "title", "observation", "latent_need", "current_gap", "mechanism",
        "behavior_change", "business_effect", "product_fit", "fastest_test",
        "failure_condition",
    ):
        if not str(row.get(field, "")).strip():
            raise ValueError(f"{opportunity_id}.{field} is required")
    perspectives = _strings(
        row.get("perspectives"), f"{opportunity_id}.perspectives", minimum=2
    )
    unknown = sorted(set(perspectives) - set(PERSPECTIVES))
    if unknown:
        raise ValueError(
            f"{opportunity_id} has unknown perspectives: {', '.join(unknown)}"
        )
    opportunity_type = str(row.get("opportunity_type", "")).strip()
    if opportunity_type not in OPPORTUNITY_TYPES:
        raise ValueError(f"{opportunity_id}.opportunity_type is invalid")
    row["perspectives"] = perspectives
    row["evidence_needed"] = _strings(
        row.get("evidence_needed", []), f"{opportunity_id}.evidence_needed"
    )
    return row


def _critique(value: Any, ids: set[str], index: int) -> Dict[str, Any]:
    row = _object(value, f"assessments[{index}]")
    opportunity_id = str(row.get("opportunity_id", "")).strip()
    if opportunity_id not in ids:
        raise ValueError("assessment references an unknown opportunity")
    disposition = str(row.get("disposition", "")).strip()
    if disposition not in {"surface_now", "validate", "defer", "reject"}:
        raise ValueError(f"{opportunity_id}.disposition is invalid")
    for field in ("strongest_reason", "strongest_risk", "decision_rationale"):
        if not str(row.get(field, "")).strip():
            raise ValueError(f"{opportunity_id}.{field} is required")
    return row


class OpportunityStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.records = root / "records"

    def save(self, record: Dict[str, Any]) -> Path:
        self.records.mkdir(parents=True, exist_ok=True)
        path = self.records / f"{record['opportunity_scout_id']}.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return path

    def latest(self) -> Dict[str, Any] | None:
        if not self.records.is_dir():
            return None
        paths = list(self.records.glob("opportunity-*.json"))
        if not paths:
            return None
        latest_path = max(paths, key=lambda path: path.stat().st_mtime_ns)
        value = json.loads(latest_path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None


def run_opportunity_scout(
    *, ask: Callable[[str, str], Dict[str, Any]], store: OpportunityStore, context: str
) -> Dict[str, Any]:
    """Find useful product opportunities without selecting implementation work."""
    structure = _ask(ask, "opportunity_structure_observer", f"""
Map the product as it currently exists. Separate observed facts from inferences and
unknowns. Identify users, core actions, repeat loops, progression, content supply,
social surfaces, current value capture, operational cadence, distribution loops,
constraints, and underused capabilities. Absence of a mechanism is a hypothesis unless
the context proves it. Return observed_facts, inferences, unknowns, users, core_actions,
repeat_loops, progression, content_supply, social_surfaces, value_capture,
operational_cadence, distribution_loops, constraints, and underused_capabilities.

CONTEXT:\n{context}
""", required=(
        "observed_facts", "inferences", "unknowns", "users", "core_actions",
        "repeat_loops", "progression", "content_supply", "social_surfaces",
        "value_capture", "operational_cadence", "distribution_loops", "constraints",
        "underused_capabilities",
    ), arrays=(
        "observed_facts", "inferences", "unknowns", "users", "core_actions",
        "repeat_loops", "progression", "content_supply", "social_surfaces",
        "value_capture", "operational_cadence", "distribution_loops", "constraints",
        "underused_capabilities",
    ))
    try:
        for field, value in structure.items():
            _strings(value, f"structure.{field}")
    except ValueError as exc:
        structure = _ask(ask, "opportunity_structure_observer", f"""
Repair the product-structure object without changing its meaning. The nested contract
error was: {exc}. Every entry in every field must be a concise JSON string, never an
object, number, boolean, or nested array. Return the complete object with these fields:
observed_facts, inferences, unknowns, users, core_actions, repeat_loops, progression,
content_supply, social_surfaces, value_capture, operational_cadence, distribution_loops,
constraints, and underused_capabilities.

PREVIOUS OBJECT:\n{json.dumps(structure, ensure_ascii=False)}
""", required=(
            "observed_facts", "inferences", "unknowns", "users", "core_actions",
            "repeat_loops", "progression", "content_supply", "social_surfaces",
            "value_capture", "operational_cadence", "distribution_loops", "constraints",
            "underused_capabilities",
        ), arrays=(
            "observed_facts", "inferences", "unknowns", "users", "core_actions",
            "repeat_loops", "progression", "content_supply", "social_surfaces",
            "value_capture", "operational_cadence", "distribution_loops", "constraints",
            "underused_capabilities",
        ))
        for field, value in structure.items():
            _strings(value, f"structure.{field}")

    synthesis = _ask(ask, "multi_perspective_opportunity_synthesizer", f"""
Rotate through every perspective independently, then connect observations across at
least two perspectives to form opportunities: {json.dumps(PERSPECTIVES)}.

The goal is useful strategic initiative, not novelty theater. Preserve a familiar pattern
such as a battle pass, subscription, bundle, season, marketplace, referral loop, creator
tool, or recovery flow when the product structure makes its causal fit specific. Label it
established_pattern instead of rejecting it as generic. Use product_specific_adaptation
when a known pattern is materially reshaped for this product, and structural_invention
only for a genuinely new causal arrangement. Do not force monetization; include retention,
content, distribution, operational, and platform opportunities when stronger.

Each opportunity must follow observation -> latent_need -> current_gap -> mechanism ->
behavior_change -> business_effect. Require opportunity_id, title, opportunity_type,
perspectives (at least two exact enum values), observation, latent_need, current_gap,
mechanism, behavior_change, business_effect, product_fit, evidence_needed, fastest_test,
and failure_condition. Return perspective_findings (one entry for every perspective),
opportunities (0-5, only supported distinct opportunities), and no_opportunity_reason.
Do not produce implementation tasks or grant delivery authority.

PRODUCT STRUCTURE:\n{json.dumps(structure, ensure_ascii=False)}
""", required=("perspective_findings", "opportunities", "no_opportunity_reason"),
        arrays=("perspective_findings", "opportunities"))

    findings = synthesis["perspective_findings"]
    covered = {
        str(row.get("perspective", "")).strip()
        for row in findings if isinstance(row, dict)
    }
    if covered != set(PERSPECTIVES) or len(findings) != len(PERSPECTIVES):
        raise ValueError("perspective_findings must cover every perspective exactly")
    opportunities = [
        _opportunity(row, index)
        for index, row in enumerate(synthesis["opportunities"])
    ]
    ids = {row["opportunity_id"] for row in opportunities}
    if len(ids) != len(opportunities):
        raise ValueError("opportunity IDs must be unique")
    if not opportunities and not str(synthesis["no_opportunity_reason"]).strip():
        raise ValueError("an empty opportunity set requires no_opportunity_reason")

    if opportunities:
        challenge = _ask(ask, "opportunity_reality_critic", f"""
Critique each opportunity for causal fit, evidence quality, user benefit, revenue or
strategic effect, implementation and ongoing operating burden, cannibalization, and dark
pattern or pay-to-win risk. A familiar pattern is not a reason to reject it. Reject it only
when the product-specific causal chain is weak, harmful, or unsupported. Return exactly
one assessment per opportunity with opportunity_id, disposition (surface_now, validate,
defer, reject), strongest_reason, strongest_risk, and decision_rationale. Also return
portfolio_summary and top_opportunity_ids ordered by expected value adjusted for evidence
and burden. top_opportunity_ids may include only surface_now or validate items.

STRUCTURE:\n{json.dumps(structure, ensure_ascii=False)}
OPPORTUNITIES:\n{json.dumps(opportunities, ensure_ascii=False)}
""", required=("assessments", "portfolio_summary", "top_opportunity_ids"),
            arrays=("assessments", "top_opportunity_ids"))
        assessments = [
            _critique(row, ids, index)
            for index, row in enumerate(challenge["assessments"])
        ]
        if {row["opportunity_id"] for row in assessments} != ids:
            raise ValueError("critic must assess every opportunity exactly once")
        eligible = {
            row["opportunity_id"] for row in assessments
            if row["disposition"] in {"surface_now", "validate"}
        }
        top_ids = _strings(challenge["top_opportunity_ids"], "top_opportunity_ids")
        if len(top_ids) != len(set(top_ids)) or not set(top_ids).issubset(eligible):
            raise ValueError("top_opportunity_ids must be unique eligible opportunities")
    else:
        challenge = {
            "assessments": [],
            "portfolio_summary": synthesis["no_opportunity_reason"],
            "top_opportunity_ids": [],
        }
        assessments = []

    identity = {
        "context_fingerprint": fingerprint(context),
        "structure": structure,
        "opportunities": opportunities,
        "assessments": assessments,
    }
    record = {
        "opportunity_scout_version": OPPORTUNITY_VERSION,
        "opportunity_scout_id": f"opportunity-{fingerprint(identity)[:12]}",
        "created_at": utc_now(),
        "context_fingerprint": fingerprint(context),
        "perspectives": list(PERSPECTIVES),
        "product_structure": structure,
        "perspective_findings": findings,
        "opportunities": opportunities,
        "critic": {**challenge, "assessments": assessments},
        "status": "opportunities_found" if challenge["top_opportunity_ids"] else "needs_evidence",
        "selected_opportunity_id": "",
        "planning_authority_granted": False,
        "delivery_authority_granted": False,
    }
    store.save(record)
    return record
