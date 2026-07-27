#!/usr/bin/env python3
"""Product invention: originate playable systems before delivery planning."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Dict, List

from palamedes_observe import utc_now


INVENTION_VERSION = "palamedes-product-invention/1"
STRUCTURAL_AXES = (
    "player_relationship", "victory_condition", "information_structure",
    "resource_structure", "time_structure", "risk_owner", "emotion_source",
    "repeat_motive",
)
PLAYABLE_FIELDS = (
    "player_count", "team_structure", "initial_state", "turn_loop",
    "allowed_actions", "win_condition", "loss_condition", "resources",
    "player_interactions", "comeback_mechanism", "repeat_variation",
    "exploit_risks", "paper_prototype_10m",
)


def fingerprint(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _object(value: Any, field: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _strings(value: Any, field: str, minimum: int = 1) -> List[str]:
    if not isinstance(value, list) or len(value) < minimum or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ValueError(f"{field} requires at least {minimum} strings")
    return [item.strip() for item in value]


def _candidate(value: Any, index: int) -> Dict[str, Any]:
    row = _object(value, f"candidates[{index}]")
    candidate_id = str(row.get("candidate_id", "")).strip()
    if not candidate_id:
        raise ValueError("every invention candidate requires candidate_id")
    mechanics = _object(row.get("structural_mechanics"), f"{candidate_id}.structural_mechanics")
    missing = [axis for axis in STRUCTURAL_AXES if not str(mechanics.get(axis, "")).strip()]
    if missing:
        raise ValueError(f"{candidate_id} lacks structural axes: {', '.join(missing)}")
    for field in ("concept", "core_tension", "harm_boundary", "conceptual_distance"):
        if not str(row.get(field, "")).strip():
            raise ValueError(f"{candidate_id}.{field} is required")
    return row


def _contract(value: Any, candidate_ids: set[str], index: int) -> Dict[str, Any]:
    row = _object(value, f"playable_contracts[{index}]")
    candidate_id = str(row.get("candidate_id", "")).strip()
    if candidate_id not in candidate_ids:
        raise ValueError("playable contract must reference an originated candidate")
    missing = [field for field in PLAYABLE_FIELDS if not row.get(field)]
    if missing:
        raise ValueError(f"{candidate_id} lacks playable fields: {', '.join(missing)}")
    return row


class ProductInventionStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.records = root / "records"

    def save(self, record: Dict[str, Any]) -> Path:
        self.records.mkdir(parents=True, exist_ok=True)
        path = self.records / f"{record['product_invention_id']}.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(path)
        return path

    def latest(self) -> Dict[str, Any] | None:
        paths = sorted(self.records.glob("invention-*.json"))
        if not paths:
            return None
        value = json.loads(paths[-1].read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None


def run_product_invention(
    *, ask: Callable[[str, str], Dict[str, Any]], store: ProductInventionStore,
    context: str,
) -> Dict[str, Any]:
    """Run independent origination roles. The result never authorizes delivery."""
    affect = _object(ask("affect_dependency_mapper", f"""
Map why humans would return, pay, cooperate, compete, remember, or leave.
Separate direct product emotion from emotion mediated by other people or outcomes.
Name desired and uncomfortable emotions, social dependencies, conflict surfaces,
ethical harm boundaries, and explicitly supplied mechanics. Do not propose features yet.

CONTEXT:\n{context}
"""), "affect_map")
    _strings(affect.get("desired_emotions"), "desired_emotions")
    _strings(affect.get("uncomfortable_emotions"), "uncomfortable_emotions")
    _strings(affect.get("social_dependencies"), "social_dependencies")
    supplied = _strings(affect.get("explicitly_supplied_mechanics", []), "explicitly_supplied_mechanics", 0)

    invention = _object(ask("genre_rule_inventor", f"""
Originate at least five structurally distant product/game worlds from this affect map.
Do not return cosmetic collections, badges, progression skins, or adjacent variants as
separate concepts. Every candidate must specify: {', '.join(STRUCTURAL_AXES)}.
Also provide candidate_id, concept, core_tension, harm_boundary, conceptual_distance,
independently_originated_mechanics, and derivation_trace. Explicit user mechanics are:
{json.dumps(supplied, ensure_ascii=False)}

AFFECT MAP:\n{json.dumps(affect, ensure_ascii=False)}
"""), "invention")
    candidates = [_candidate(row, index) for index, row in enumerate(invention.get("candidates", []))]
    if len(candidates) < 5:
        raise ValueError("product invention requires at least five distant candidates")
    candidate_ids = {str(row["candidate_id"]) for row in candidates}
    if len(candidate_ids) != len(candidates):
        raise ValueError("candidate IDs must be unique")

    compiler = _object(ask("playable_contract_compiler", f"""
Compile every candidate into a falsifiable playable contract. Each contract must contain
candidate_id and: {', '.join(PLAYABLE_FIELDS)}. Preserve the candidate; do not invent a
replacement. A 10-minute paper prototype must test the core tension, not visual polish.

CANDIDATES:\n{json.dumps(candidates, ensure_ascii=False)}
"""), "compiler")
    contracts = [_contract(row, candidate_ids, index) for index, row in enumerate(compiler.get("playable_contracts", []))]
    if len(contracts) != len(candidate_ids) or {row["candidate_id"] for row in contracts} != candidate_ids:
        raise ValueError("every candidate requires exactly one playable contract")

    adversary = _object(ask("invention_adversary", f"""
Attack each playable world for fake fun, social harm, coercion, balance collapse, content
burden, infrastructure burden, exploitability, and excessive iteration cost. Keep
possibility (could be valuable) separate from investment (worth testing now). Return
candidate_assessments for every candidate and a minimum_disconfirming_probe.

CONTRACTS:\n{json.dumps(contracts, ensure_ascii=False)}
"""), "adversary")
    assessments = adversary.get("candidate_assessments")
    if not isinstance(assessments, list) or {str(row.get("candidate_id", "")) for row in assessments if isinstance(row, dict)} != candidate_ids:
        raise ValueError("adversary must assess every candidate")

    selector = _object(ask("invention_selector", f"""
Choose select, probe, or reject. You may select only an existing candidate_id and may not
invent a new concept. Preserve a fate for every candidate. Return decision,
selected_candidate_id (empty on reject), rationale, candidate_fates, smallest_prototype,
and provenance with origin, decisive_seed, palamedes_contribution, conceptual_distance,
would_exist_without_user_seed, and derivation_trace. Origin must be palamedes, human,
reference, or mixed. This grants no mission approval or delivery authority.

CANDIDATES:\n{json.dumps(candidates, ensure_ascii=False)}
CONTRACTS:\n{json.dumps(contracts, ensure_ascii=False)}
ADVERSARY:\n{json.dumps(adversary, ensure_ascii=False)}
"""), "selector")
    decision = str(selector.get("decision", ""))
    if decision not in {"select", "probe", "reject"}:
        raise ValueError("selector decision must be select, probe, or reject")
    selected_id = str(selector.get("selected_candidate_id", "")).strip()
    if decision != "reject" and selected_id not in candidate_ids:
        raise ValueError("selector must choose an existing candidate")
    if decision == "reject" and selected_id:
        raise ValueError("rejected invention cannot select a candidate")
    fates = selector.get("candidate_fates")
    if not isinstance(fates, list) or {str(row.get("candidate_id", "")) for row in fates if isinstance(row, dict)} != candidate_ids:
        raise ValueError("selector must preserve every candidate fate")
    provenance = _object(selector.get("provenance"), "selector.provenance")
    if provenance.get("origin") not in {"palamedes", "human", "reference", "mixed"}:
        raise ValueError("provenance.origin is invalid")
    for field in ("decisive_seed", "palamedes_contribution", "conceptual_distance", "would_exist_without_user_seed", "derivation_trace"):
        if field not in provenance:
            raise ValueError(f"provenance.{field} is required")

    identity = {"context": context, "affect": affect, "candidates": candidates, "selector": selector}
    record = {
        "product_invention_version": INVENTION_VERSION,
        "product_invention_id": f"invention-{fingerprint(identity)[:12]}",
        "status": decision,
        "created_at": utc_now(),
        "context_fingerprint": fingerprint(context),
        "affect_dependency_map": affect,
        "candidates": candidates,
        "playable_contracts": contracts,
        "adversary": adversary,
        "selector": selector,
        "selected_candidate_id": selected_id,
        "selected_playable_contract": next((row for row in contracts if row["candidate_id"] == selected_id), None),
        "provenance": provenance,
        "delivery_authority_granted": False,
        "mission_approval_granted": False,
    }
    store.save(record)
    return record
