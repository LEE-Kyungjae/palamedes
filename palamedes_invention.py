#!/usr/bin/env python3
"""Domain-general invention before commitment, design, or delivery planning."""

from __future__ import annotations

import hashlib
import json
import os
import fcntl
from pathlib import Path
from typing import Any, Callable, Dict, List

from palamedes_observe import utc_now


INVENTION_VERSION = "palamedes-product-invention/2"
INPUT_MODES = {"open_discovery", "goal_seeded", "idea_seeded", "direction_committed"}
TRANSFORMATION_LENSES = (
    "assumption_removal",
    "center_object_shift",
    "actor_or_authority_reversal",
    "information_or_value_flow_change",
    "temporal_reversal",
    "failure_as_resource",
    "cross_domain_causal_transfer",
)
STRUCTURAL_DIMENSIONS = (
    "capability",
    "actors_and_authority",
    "information_creation_and_ownership",
    "state_or_lifecycle",
    "decision_process",
    "value_or_cost_flow",
    "feedback_loop",
)
NOVELTY_TESTS = (
    "name_removal",
    "compositional_emergence",
    "service_specificity",
    "causal_coherence",
    "independent_contribution",
)

# Kept as import-compatible aliases for v1 consumers. V2 does not require them.
STRUCTURAL_AXES = STRUCTURAL_DIMENSIONS
PLAYABLE_FIELDS: tuple[str, ...] = ()


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


def _ask_object_contract(
    ask: Callable[[str, str], Dict[str, Any]],
    role: str,
    prompt: str,
    *,
    required_fields: tuple[str, ...],
    list_fields: tuple[str, ...] = (),
    nonempty_string_lists: tuple[str, ...] = (),
) -> Dict[str, Any]:
    """Make one bounded repair attempt for common provider schema drift."""
    last_error = ""
    for attempt in range(2):
        repair = "" if attempt == 0 else f"""

Your previous object violated the machine contract: {last_error}
Return a corrected JSON object only. Required top-level fields are:
{json.dumps(required_fields)}. These fields must be JSON arrays:
{json.dumps(list_fields)}. Do not omit fields; use [] or an empty string only when the
semantic instructions explicitly allow an empty value.
"""
        row = _object(ask(role, prompt + repair), role)
        missing = [field for field in required_fields if field not in row]
        wrong_lists = [field for field in list_fields if field in row and not isinstance(row[field], list)]
        invalid_string_lists = [
            field for field in nonempty_string_lists
            if not isinstance(row.get(field), list)
            or not row[field]
            or not all(isinstance(item, str) and item.strip() for item in row[field])
        ]
        if not missing and not wrong_lists and not invalid_string_lists:
            return row
        parts = []
        if missing:
            parts.append(f"missing fields: {', '.join(missing)}")
        if wrong_lists:
            parts.append(f"non-array fields: {', '.join(wrong_lists)}")
        if invalid_string_lists:
            parts.append(f"nonempty string-array fields required: {', '.join(invalid_string_lists)}")
        last_error = "; ".join(parts)
    raise ValueError(f"{role} failed JSON contract after repair: {last_error}")


def _candidate(value: Any, index: int) -> Dict[str, Any]:
    row = _object(value, f"candidates[{index}]")
    candidate_id = str(row.get("candidate_id", "")).strip()
    if not candidate_id:
        raise ValueError("every invention candidate requires candidate_id")
    for field in ("thesis", "hidden_opportunity", "falsification_condition"):
        if not str(row.get(field, "")).strip():
            raise ValueError(f"{candidate_id}.{field} is required")
    _strings(row.get("observed_basis"), f"{candidate_id}.observed_basis")
    _strings(row.get("transformation_lenses"), f"{candidate_id}.transformation_lenses")
    delta = _object(row.get("structural_delta"), f"{candidate_id}.structural_delta")
    for field in ("baseline_structure", "proposed_structure", "newly_possible_outcome"):
        if not str(delta.get(field, "")).strip():
            raise ValueError(f"{candidate_id}.structural_delta.{field} is required")
    changed = _strings(delta.get("changed_dimensions"), f"{candidate_id}.structural_delta.changed_dimensions")
    unknown = sorted(set(changed) - set(STRUCTURAL_DIMENSIONS))
    if unknown:
        raise ValueError(f"{candidate_id} has unknown structural dimensions: {', '.join(unknown)}")
    _strings(delta.get("causal_chain"), f"{candidate_id}.structural_delta.causal_chain", 2)
    origin_value = row.get("origin")
    if isinstance(origin_value, str):
        origin = {
            "type": origin_value,
            "palamedes_contribution": "not separately stated; independent contribution remains unverified",
        }
        row["origin"] = origin
    else:
        origin = _object(origin_value, f"{candidate_id}.origin")
    raw_origin_type = str(origin.get("type", "")).strip().lower().replace("-", "_").replace(" ", "_")
    origin_aliases = {
        "palamedes_originated": "palamedes",
        "model": "palamedes",
        "system": "palamedes",
        "human_originated": "human",
        "user": "human",
        "observation_derived": "observation",
        "evidence": "observation",
        "hybrid": "mixed",
        "joint": "mixed",
        "reference_derived": "reference",
    }
    canonical_origin = origin_aliases.get(raw_origin_type, raw_origin_type)
    if canonical_origin not in {"palamedes", "human", "observation", "mixed", "reference"}:
        keyword_origins = (
            ("palamedes", "palamedes"), ("model", "palamedes"), ("system", "palamedes"),
            ("human", "human"), ("user", "human"),
            ("observation", "observation"), ("evidence", "observation"),
            ("mixed", "mixed"), ("hybrid", "mixed"), ("joint", "mixed"),
            ("reference", "reference"),
        )
        canonical_origin = next(
            (mapped for keyword, mapped in keyword_origins if keyword in raw_origin_type),
            "unknown",
        )
    origin["raw_type"] = raw_origin_type
    origin["type"] = canonical_origin
    if not str(origin.get("palamedes_contribution", "")).strip():
        origin["palamedes_contribution"] = "not separately stated; independent contribution remains unverified"
        origin["contribution_verified"] = False
    else:
        origin["contribution_verified"] = True
    composition = _object(row.get("composition"), f"{candidate_id}.composition")
    _strings(composition.get("known_components", []), f"{candidate_id}.composition.known_components", 0)
    for field in ("novel_relation_or_condition", "emergent_outcome", "irreducibility_test"):
        if not str(composition.get(field, "")).strip():
            raise ValueError(f"{candidate_id}.composition.{field} is required")
    return row


def _assessment(value: Any, candidate_ids: set[str], index: int) -> Dict[str, Any]:
    row = _object(value, f"candidate_assessments[{index}]")
    candidate_id = str(row.get("candidate_id", "")).strip()
    if candidate_id not in candidate_ids:
        raise ValueError("assessment must reference an originated candidate")
    raw_verdict = str(row.get("verdict", "")).strip().lower().replace("-", "_").replace(" ", "_")
    if raw_verdict in {"survives", "survive", "pass", "passes", "viable", "preserve", "accept"}:
        verdict = "survives"
    elif raw_verdict in {"reject", "rejected", "fail", "fails", "invalid", "discard"}:
        verdict = "reject"
    else:
        verdict = "revise"
    row["raw_verdict"] = raw_verdict
    row["verdict"] = verdict
    tests = _object(row.get("tests"), f"{candidate_id}.tests")
    missing = [test for test in NOVELTY_TESTS if test not in tests]
    if missing:
        raise ValueError(f"{candidate_id} lacks novelty tests: {', '.join(missing)}")
    return row


class ProductInventionStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.records = root / "records"
        self.observation_events = root / "observation-requirements.jsonl"

    def _observation_rows(self) -> List[Dict[str, Any]]:
        if not self.observation_events.is_file():
            return []
        rows = []
        for line in self.observation_events.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
        return rows

    def _append_observation_event(self, event: Dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.observation_events.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            handle.seek(0, os.SEEK_END)
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def observation_requirements(self) -> List[Dict[str, Any]]:
        latest: Dict[str, Dict[str, Any]] = {}
        for row in self._observation_rows():
            requirement_id = str(row.get("observation_requirement_id", ""))
            if requirement_id:
                latest[requirement_id] = row
        return sorted(latest.values(), key=lambda row: str(row.get("created_at", "")))

    def open_observation_requirements(self) -> List[Dict[str, Any]]:
        return [row for row in self.observation_requirements() if row.get("status") == "open"]

    def record_observation_requirement(
        self, *, source_type: str, observation_needed: str, reason: str,
        source_invention_id: str = "", source_candidate_id: str = "",
        context_fingerprint: str = "",
    ) -> Dict[str, Any]:
        observation_needed = observation_needed.strip()
        reason = reason.strip()
        if not observation_needed or not reason:
            raise ValueError("observation requirement needs an observation and reason")
        dedup_key = fingerprint({
            "source_type": source_type.strip(),
            "observation_needed": " ".join(observation_needed.lower().split()),
        })
        for row in self.open_observation_requirements():
            same_meaning = (
                str(row.get("source_type", "")).strip() == source_type.strip()
                and " ".join(str(row.get("observation_needed", "")).lower().split())
                == " ".join(observation_needed.lower().split())
            )
            if row.get("dedup_key") == dedup_key or same_meaning:
                return row
        created_at = utc_now()
        requirement = {
            "observation_requirement_version": "palamedes-observation-requirement/1",
            "observation_requirement_id": f"observation-{dedup_key[:12]}",
            "event_type": "observation_required",
            "status": "open",
            "created_at": created_at,
            "updated_at": created_at,
            "source_type": source_type.strip(),
            "source_invention_id": source_invention_id,
            "source_candidate_id": source_candidate_id,
            "context_fingerprint": context_fingerprint,
            "observation_needed": observation_needed,
            "reason": reason,
            "dedup_key": dedup_key,
            "authority_granted": False,
        }
        self._append_observation_event(requirement)
        return requirement

    def resolve_observation_requirement(
        self, requirement_id: str, evidence: str, *, observer: str = "human"
    ) -> Dict[str, Any]:
        current = next(
            (row for row in self.open_observation_requirements() if row.get("observation_requirement_id") == requirement_id.strip()),
            None,
        )
        if current is None:
            raise ValueError("resolution requires an existing open observation requirement")
        if not evidence.strip():
            raise ValueError("observation resolution requires evidence")
        resolved = {
            **current,
            "event_type": "observation_resolved",
            "status": "resolved",
            "updated_at": utc_now(),
            "resolved_at": utc_now(),
            "observer": observer.strip() or "human",
            "evidence": evidence.strip(),
            "evidence_status": "human_report" if observer == "human" else "unverified_observation",
            "authority_granted": False,
        }
        self._append_observation_event(resolved)
        return resolved

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

    def commit(self, candidate_id: str, rationale: str) -> Dict[str, Any]:
        invention = self.latest()
        if invention is None:
            raise ValueError("no product invention exists to commit")
        candidate_id = candidate_id.strip()
        rationale = rationale.strip()
        if not rationale:
            raise ValueError("invention commitment requires a human rationale")
        candidates = {
            str(row.get("candidate_id", "")): row
            for row in invention.get("candidates", [])
            if isinstance(row, dict)
        }
        if candidate_id not in candidates:
            raise ValueError("commitment must reference an existing invention candidate")
        frontier = {
            str(row.get("candidate_id", "")): row
            for row in invention.get("frontier", [])
            if isinstance(row, dict)
        }
        if frontier.get(candidate_id, {}).get("disposition") in {"reject", "merge"}:
            raise ValueError("rejected or merged candidate cannot be committed without a new invention cycle")
        committed_at = utc_now()
        identity = {
            "product_invention_id": invention["product_invention_id"],
            "candidate_id": candidate_id,
            "rationale": rationale,
            "committed_at": committed_at,
        }
        commitment = {
            "invention_commitment_version": "palamedes-invention-commitment/1",
            "invention_commitment_id": f"commitment-{fingerprint(identity)[:12]}",
            **identity,
            "candidate_fingerprint": fingerprint(candidates[candidate_id]),
            "committed_by": "human",
            "design_authority_granted": False,
            "delivery_authority_granted": False,
            "mission_approval_granted": False,
        }
        self.root.mkdir(parents=True, exist_ok=True)
        with (self.root / "commitments.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(commitment, ensure_ascii=False, sort_keys=True) + "\n")
        return commitment


def run_product_invention(
    *, ask: Callable[[str, str], Dict[str, Any]], store: ProductInventionStore,
    context: str,
) -> Dict[str, Any]:
    """Explore a product possibility frontier without selecting or implementing it."""
    observation = _ask_object_contract(ask, "invention_context_observer", f"""
Classify the input as one of {', '.join(sorted(INPUT_MODES))}. Separate what the human
explicitly supplied from repository/operational facts, reasonable inferences, unknowns,
and constraints. Determine an appropriate reasoning and communication scale; a small
feature must not be rejected for lacking standalone market size, and a service strategy
must not be reduced to a feature spec. Return input_mode, stated_intent, supplied_ideas,
observed_facts, inferences, unknowns, constraints, and scale.

CONTEXT:\n{context}
""", required_fields=("input_mode", "stated_intent", "supplied_ideas", "observed_facts", "inferences", "unknowns", "constraints", "scale"), list_fields=("supplied_ideas", "observed_facts", "inferences", "unknowns", "constraints"))
    if observation.get("input_mode") not in INPUT_MODES:
        raise ValueError("observation.input_mode is invalid")
    for field in ("supplied_ideas", "observed_facts", "inferences", "unknowns", "constraints"):
        _strings(observation.get(field, []), f"observation.{field}", 0)
    if not str(observation.get("stated_intent", "")).strip() or not str(observation.get("scale", "")).strip():
        raise ValueError("observation requires stated_intent and scale")

    baseline = _ask_object_contract(ask, "conventional_baseline_mapper", f"""
Describe the high-probability answers a competent planner would produce from this input.
Record their underlying mechanisms, assumptions, and vocabulary traps. Suppress
conventional causal arrangements, not familiar components: known features remain valid
raw material when a new relation, order, condition, context, feedback loop, or value flow
creates an emergent result. These are a suppression baseline, not invention candidates. Include expected_solutions,
shared_mechanisms, dominant_assumptions, and forbidden_cosmetic_variations. Do not use
rarer names or metaphors to disguise the same mechanism.

OBSERVATION:\n{json.dumps(observation, ensure_ascii=False)}
""", required_fields=("expected_solutions", "shared_mechanisms", "dominant_assumptions", "forbidden_cosmetic_variations"), list_fields=("expected_solutions", "shared_mechanisms", "dominant_assumptions", "forbidden_cosmetic_variations"), nonempty_string_lists=("expected_solutions", "shared_mechanisms", "dominant_assumptions", "forbidden_cosmetic_variations"))
    for field in ("expected_solutions", "shared_mechanisms", "dominant_assumptions", "forbidden_cosmetic_variations"):
        _strings(baseline.get(field), f"baseline.{field}")

    invention = _ask_object_contract(ask, "counterweighted_inventor", f"""
Search beyond the conventional baseline by changing causal structure, not vocabulary.
Use multiple relevant lenses from: {', '.join(TRANSFORMATION_LENSES)}. Candidate count is
not a target: return only distinct discoveries, including zero when the evidence supports
no invention. Do not name or brand candidates; use neutral candidate IDs. For an
idea-seeded input, separately consider an extension, a different route to the same intent,
and a larger opportunity discovered from it, but keep only candidates with real structural
change. Existing features may be recombined; reject only combinations whose result is no
more than the sum of familiar parts. Every candidate requires candidate_id, thesis,
observed_basis, hidden_opportunity, transformation_lenses, structural_delta, composition,
origin, and falsification_condition. composition requires known_components (which may be
empty), novel_relation_or_condition, emergent_outcome, and irreducibility_test.
structural_delta requires baseline_structure, proposed_structure, changed_dimensions,
causal_chain, and newly_possible_outcome. changed_dimensions may contain ONLY these exact
enum values: {json.dumps(STRUCTURAL_DIMENSIONS)}. causal_chain is a separate string array
and must never appear inside changed_dimensions. Also return
search_notes and no_discovery_reason (required when candidates is empty). Do not produce
implementation tasks, schemas, APIs, prototypes, roadmaps, or selection.

OBSERVATION:\n{json.dumps(observation, ensure_ascii=False)}
BASELINE TO SUPPRESS:\n{json.dumps(baseline, ensure_ascii=False)}
""", required_fields=("candidates", "search_notes", "no_discovery_reason"), list_fields=("candidates", "search_notes"))
    raw_candidates = invention.get("candidates", [])
    if not isinstance(raw_candidates, list):
        raise ValueError("invention.candidates must be a list")
    try:
        candidates = [_candidate(row, index) for index, row in enumerate(raw_candidates)]
    except ValueError as exc:
        invention = _ask_object_contract(ask, "counterweighted_inventor", f"""
Repair the previously generated invention object without adding rhetorical names or
changing sound candidate theses. The nested machine-contract error was: {exc}
Return the complete corrected object. structural_delta.changed_dimensions accepts only
{json.dumps(STRUCTURAL_DIMENSIONS)}. structural_delta.causal_chain is a separate array.
composition requires known_components, novel_relation_or_condition, emergent_outcome,
and irreducibility_test.

PREVIOUS OBJECT:\n{json.dumps(invention, ensure_ascii=False)}
""", required_fields=("candidates", "search_notes", "no_discovery_reason"), list_fields=("candidates", "search_notes"))
        raw_candidates = invention.get("candidates", [])
        candidates = [_candidate(row, index) for index, row in enumerate(raw_candidates)]
    candidate_ids = {str(row["candidate_id"]) for row in candidates}
    if len(candidate_ids) != len(candidates):
        raise ValueError("candidate IDs must be unique")
    if not candidates and not str(invention.get("no_discovery_reason", "")).strip():
        raise ValueError("an empty invention frontier requires no_discovery_reason")

    adversary = _ask_object_contract(ask, "structural_novelty_adversary", f"""
Evaluate every candidate after removing its label and rhetoric. Apply all tests:
{', '.join(NOVELTY_TESTS)}. Do not reject a candidate merely because its components are
known. Test whether their relation, sequence, activation condition, context, authority,
feedback, or value capture produces an outcome unavailable from the parts independently.
Reject renamed features, conventional bundles with only additive value, UI-only changes,
generic ideas transferable unchanged to any service, unsupported causal leaps, and
restatements of the human seed. Consequence and causal coherence precede novelty. Return exactly one
candidate_assessment per candidate with candidate_id, verdict, tests, strongest_attack,
surviving_delta, evidence_gap, and minimum_disconfirming_observation. If the frontier is
empty, return an empty candidate_assessments list and explain why no forced candidate
should be manufactured.

OBSERVATION:\n{json.dumps(observation, ensure_ascii=False)}
BASELINE:\n{json.dumps(baseline, ensure_ascii=False)}
CANDIDATES:\n{json.dumps(candidates, ensure_ascii=False)}
""", required_fields=("candidate_assessments", "empty_frontier_reason"), list_fields=("candidate_assessments",))
    raw_assessments = adversary.get("candidate_assessments")
    if not isinstance(raw_assessments, list):
        raise ValueError("adversary.candidate_assessments must be a list")
    assessments = [_assessment(row, candidate_ids, index) for index, row in enumerate(raw_assessments)]
    if len(assessments) != len(candidate_ids) or {row["candidate_id"] for row in assessments} != candidate_ids:
        raise ValueError("adversary must assess every candidate exactly once")

    curator = _ask_object_contract(ask, "invention_frontier_curator", f"""
Preserve an exploration frontier; do not pick a winner and do not convert discoveries into
delivery work. Assign every candidate one disposition: preserve, deepen, needs_evidence,
merge, or reject. Return discovery_status (discovered, partial, or no_discovery),
frontier with candidate_id, disposition, reason, and next_question, plus synthesis,
human_decision_required, and presentation_outline scaled to the input. The outline must
explain why, the non-obvious discovery, structural change, value, uncertainty, and the
decision needed; it must not force market analysis onto a small supporting feature.

OBSERVATION:\n{json.dumps(observation, ensure_ascii=False)}
CANDIDATES:\n{json.dumps(candidates, ensure_ascii=False)}
ASSESSMENTS:\n{json.dumps(assessments, ensure_ascii=False)}
""", required_fields=("discovery_status", "frontier", "synthesis", "human_decision_required", "presentation_outline"), list_fields=("frontier", "presentation_outline"))
    raw_discovery_status = str(curator.get("discovery_status", "")).strip().lower().replace("-", "_").replace(" ", "_")
    discovery_aliases = {
        "discovery": "discovered", "success": "discovered", "viable": "discovered",
        "mixed": "partial", "uncertain": "partial", "needs_evidence": "partial",
        "none": "no_discovery", "not_discovered": "no_discovery", "failed": "no_discovery",
    }
    curator["raw_discovery_status"] = raw_discovery_status
    curator["discovery_status"] = discovery_aliases.get(raw_discovery_status, raw_discovery_status)
    if curator.get("discovery_status") not in {"discovered", "partial", "no_discovery"}:
        curator["discovery_status"] = "partial" if candidates else "no_discovery"
    frontier = curator.get("frontier")
    if not isinstance(frontier, list) or {str(row.get("candidate_id", "")) for row in frontier if isinstance(row, dict)} != candidate_ids:
        raise ValueError("curator must preserve every candidate in the frontier")
    for row in frontier:
        raw_disposition = str(row.get("disposition", "")).strip().lower().replace("-", "_").replace(" ", "_")
        disposition_aliases = {
            "keep": "preserve", "survives": "preserve", "viable": "preserve",
            "explore": "deepen", "develop": "deepen", "probe": "deepen",
            "evidence": "needs_evidence", "needs_more_evidence": "needs_evidence", "uncertain": "needs_evidence",
            "combine": "merge", "merged": "merge",
            "discard": "reject", "rejected": "reject", "fail": "reject",
        }
        row["raw_disposition"] = raw_disposition
        row["disposition"] = disposition_aliases.get(raw_disposition, raw_disposition)
        if row["disposition"] not in {"preserve", "deepen", "needs_evidence", "merge", "reject"}:
            row["disposition"] = "needs_evidence"
    if candidates and curator.get("discovery_status") == "no_discovery" and any(
        row.get("verdict") == "survives" for row in assessments
    ):
        raise ValueError("curator cannot erase a surviving discovery")
    if not candidates and curator.get("discovery_status") != "no_discovery":
        raise ValueError("empty frontier must report no_discovery")

    identity = {"context": context, "observation": observation, "baseline": baseline, "candidates": candidates, "curator": curator}
    invention_id = f"invention-{fingerprint(identity)[:12]}"
    observation_requirements = []
    for assessment in assessments:
        needed = str(assessment.get("minimum_disconfirming_observation", "")).strip()
        gap = str(assessment.get("evidence_gap", "")).strip()
        if needed and gap:
            observation_requirements.append(store.record_observation_requirement(
                source_type="candidate_disconfirmation_gap",
                observation_needed=needed,
                reason=gap,
                source_invention_id=invention_id,
                source_candidate_id=str(assessment.get("candidate_id", "")),
                context_fingerprint=fingerprint(context),
            ))
    record = {
        "product_invention_version": INVENTION_VERSION,
        "product_invention_id": invention_id,
        "status": curator["discovery_status"],
        "created_at": utc_now(),
        "context_fingerprint": fingerprint(context),
        "observation": observation,
        "conventional_baseline": baseline,
        "transformation_lenses": list(TRANSFORMATION_LENSES),
        "candidates": candidates,
        "adversary": {**adversary, "candidate_assessments": assessments},
        "frontier": frontier,
        "observation_requirements": observation_requirements,
        "curator": curator,
        "selected_candidate_id": "",
        "selected_playable_contract": None,
        "playable_contracts": [],
        "human_commit_required": True,
        "design_authority_granted": False,
        "delivery_authority_granted": False,
        "mission_approval_granted": False,
    }
    store.save(record)
    return record
