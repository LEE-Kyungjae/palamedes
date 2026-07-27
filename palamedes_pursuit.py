#!/usr/bin/env python3
"""Domain-general pursuit planning from a high-level human objective."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Dict, List

from palamedes_observe import utc_now


PURSUIT_VERSION = "palamedes-pursuit/1"
EPISTEMIC_TYPES = {
    "discover", "explain", "predict", "invent", "design", "decide",
    "evaluate", "author", "operate",
}
UNKNOWN_CLASSES = {
    "known", "retrievable", "inferential", "currently_unknowable", "decision_reversing",
}


def fingerprint(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


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


class PursuitStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.records = root / "records"

    def save(self, record: Dict[str, Any]) -> Path:
        self.records.mkdir(parents=True, exist_ok=True)
        path = self.records / f"{record['pursuit_id']}.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(path)
        return path

    def latest(self) -> Dict[str, Any] | None:
        paths = sorted(self.records.glob("pursuit-*.json"))
        if not paths:
            return None
        value = json.loads(paths[-1].read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None


def run_pursuit(
    *, ask: Callable[[str, str], Dict[str, Any]], store: PursuitStore, objective: str,
) -> Dict[str, Any]:
    """Compose an evidence-producing workflow without pretending it has executed."""
    if not objective.strip():
        raise ValueError("pursuit objective is required")

    intent = _object(ask("pursuit_intent_interpreter", f"""
Interpret the human outcome, not merely the nouns or requested artifact. Return
outcome, intended_audience, decision_or_change_enabled, quality_bar, constraints,
non_goals, and assumptions_requiring_confirmation. Do not choose a workflow yet.

OBJECTIVE:\n{objective}
"""), "intent")
    for field in ("outcome", "intended_audience", "decision_or_change_enabled", "quality_bar"):
        if not str(intent.get(field, "")).strip():
            raise ValueError(f"intent.{field} is required")

    routing = _object(ask("epistemic_task_router", f"""
Classify the work using only these composable types: {', '.join(sorted(EPISTEMIC_TYPES))}.
Return task_types, rationale_by_type, required_claim_level, deliverable_form, and
update_mode. Do not route by a hard-coded industry template.

INTENT:\n{json.dumps(intent, ensure_ascii=False)}
"""), "routing")
    task_types = set(_strings(routing.get("task_types"), "task_types"))
    if not task_types <= EPISTEMIC_TYPES:
        raise ValueError(f"unsupported epistemic task types: {sorted(task_types - EPISTEMIC_TYPES)}")

    unknown_map = _object(ask("unknown_map_builder", f"""
Before proposing output, map epistemic state. Return entries containing unknown_id,
class, question, why_it_matters, evidence_needed, source_time_sensitivity, and
decision_reversal_signal. Class must be one of: {', '.join(sorted(UNKNOWN_CLASSES))}.
Include at least one decision_reversing entry and never label an uncollected fact known.

OBJECTIVE:\n{objective}\nROUTING:\n{json.dumps(routing, ensure_ascii=False)}
"""), "unknown_map")
    unknowns = unknown_map.get("entries")
    if not isinstance(unknowns, list) or len(unknowns) < 3:
        raise ValueError("unknown map requires at least three entries")
    classes = set()
    for index, row in enumerate(unknowns):
        row = _object(row, f"unknowns[{index}]")
        unknown_class = str(row.get("class", ""))
        if unknown_class not in UNKNOWN_CLASSES:
            raise ValueError(f"unknowns[{index}].class is invalid")
        classes.add(unknown_class)
        for field in ("unknown_id", "question", "why_it_matters", "evidence_needed"):
            if not str(row.get(field, "")).strip():
                raise ValueError(f"unknowns[{index}].{field} is required")
    if "decision_reversing" not in classes:
        raise ValueError("unknown map requires a decision_reversing entry")

    composition = _object(ask("capability_and_domain_composer", f"""
Compose capabilities dynamically. Return capabilities, domain_protocol_acquisition,
execution_graph, evidence_policy, deliverable_compiler, autonomy_envelope, and
reobservation_policy. Every execution_graph node needs node_id, purpose, capability,
inputs, outputs, falsifier, cost_class, and depends_on. autonomy_envelope must separate
automatic_actions, approval_required_actions, and forbidden_actions. Research, purchase,
publication, contacting people, sensitive data, and real financial actions must not be
silently authorized. The graph must end in a usable deliverable and preserve citations,
timestamps, uncertainty, and provenance.

INTENT:\n{json.dumps(intent, ensure_ascii=False)}
ROUTING:\n{json.dumps(routing, ensure_ascii=False)}
UNKNOWN MAP:\n{json.dumps(unknown_map, ensure_ascii=False)}
"""), "composition")
    capabilities = _strings(composition.get("capabilities"), "capabilities", 2)
    graph = composition.get("execution_graph")
    if not isinstance(graph, list) or len(graph) < 3:
        raise ValueError("execution graph requires at least three nodes")
    node_ids = set()
    for index, node in enumerate(graph):
        node = _object(node, f"execution_graph[{index}]")
        for field in ("node_id", "purpose", "capability", "inputs", "outputs", "falsifier", "cost_class", "depends_on"):
            if field not in node or node[field] in (None, ""):
                raise ValueError(f"execution_graph[{index}].{field} is required")
        node_id = str(node["node_id"])
        if node_id in node_ids:
            raise ValueError("execution graph node IDs must be unique")
        node_ids.add(node_id)
    envelope = _object(composition.get("autonomy_envelope"), "autonomy_envelope")
    _strings(envelope.get("automatic_actions"), "automatic_actions")
    _strings(envelope.get("approval_required_actions"), "approval_required_actions")
    _strings(envelope.get("forbidden_actions"), "forbidden_actions")

    adversary = _object(ask("pursuit_adversary", f"""
Attack this pursuit for artifact theater, evidence laundering, false novelty, stale data,
uncalibrated prediction, missing expertise, unsafe autonomy, excessive cost, and a workflow
that merely mirrors the user's wording. Return critical_failures, repairable_gaps,
minimum_disconfirming_probes, and verdict (proceed, revise, or reject). Do not execute it.

COMPOSITION:\n{json.dumps(composition, ensure_ascii=False)}
"""), "adversary")
    verdict = str(adversary.get("verdict", ""))
    if verdict not in {"proceed", "revise", "reject"}:
        raise ValueError("pursuit adversary verdict must be proceed, revise, or reject")

    governor = _object(ask("pursuit_governor", f"""
Freeze one pursuit disposition: ready, needs_revision, needs_human_gate, or rejected.
Return disposition, rationale, first_executable_nodes, human_gates, stop_conditions,
expected_deliverable, and provenance. Do not add capabilities or graph nodes. Do not claim
research, retrieval, analysis, experiments, prediction, or writing have already happened.
Grant neither external-action nor publication authority.

INTENT:\n{json.dumps(intent, ensure_ascii=False)}
ROUTING:\n{json.dumps(routing, ensure_ascii=False)}
COMPOSITION:\n{json.dumps(composition, ensure_ascii=False)}
ADVERSARY:\n{json.dumps(adversary, ensure_ascii=False)}
"""), "governor")
    disposition = str(governor.get("disposition", ""))
    if disposition not in {"ready", "needs_revision", "needs_human_gate", "rejected"}:
        raise ValueError("pursuit disposition is invalid")
    first_nodes = _strings(governor.get("first_executable_nodes", []), "first_executable_nodes", 0)
    if not set(first_nodes) <= node_ids:
        raise ValueError("governor may start only existing execution nodes")
    for field in ("rationale", "human_gates", "stop_conditions", "expected_deliverable", "provenance"):
        if field not in governor:
            raise ValueError(f"governor.{field} is required")

    identity = {"objective": objective, "intent": intent, "routing": routing, "composition": composition, "governor": governor}
    record = {
        "pursuit_version": PURSUIT_VERSION,
        "pursuit_id": f"pursuit-{fingerprint(identity)[:12]}",
        "created_at": utc_now(),
        "status": disposition,
        "objective": objective,
        "objective_fingerprint": fingerprint(objective),
        "intent": intent,
        "epistemic_routing": routing,
        "unknown_map": unknown_map,
        "capability_composition": composition,
        "adversary": adversary,
        "governor": governor,
        "execution_started": False,
        "external_action_authority_granted": False,
        "publication_authority_granted": False,
        "financial_action_authority_granted": False,
    }
    store.save(record)
    return record
