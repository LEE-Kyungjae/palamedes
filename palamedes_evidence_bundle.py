#!/usr/bin/env python3
"""Deterministic, authority-preserving evidence for product cognition roles."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Sequence

from palamedes_observe import utc_now


BUNDLE_VERSION = "palamedes-cognition-evidence/2"
LEGACY_BUNDLE_VERSION = "palamedes-cognition-evidence/1"
MAX_TEXT_CHARS = 1_600
MAX_TOTAL_BYTES = 96_000
MISSION_CITABLE_EPISTEMIC_CLASSES = frozenset(
    {"direct_observation", "host_verified"}
)
LANE_CAPS = {
    "product_signals": 16,
    "outcome_memory": 24,
    "knowledge": 24,
    "unknowns": 16,
    "thoughts": 12,
    "discoveries": 12,
    "opportunity_hypotheses": 5,
    "invention_candidates": 5,
    "selected_vision": 1,
    "research_agendas": 7,
    "reference_patterns": 8,
    "transfer_mappings": 8,
}


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _clip(value: Any, limit: int = MAX_TEXT_CHARS) -> str:
    text = str(value or "").strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _strings(value: Any, limit: int = 12) -> List[str]:
    if not isinstance(value, list):
        return []
    return [_clip(item, 600) for item in value if str(item or "").strip()][:limit]


def _bounded_json(
    value: Any, *, depth: int = 0, max_object_fields: int = 32
) -> Any:
    """Bound nested model/store material before it can monopolize a role context."""
    if depth >= 6:
        return _clip(value, 400)
    if isinstance(value, dict):
        return {
            _clip(key, 160): _bounded_json(
                item, depth=depth + 1, max_object_fields=max_object_fields
            )
            for key, item in list(sorted(value.items(), key=lambda pair: str(pair[0])))[:max_object_fields]
        }
    if isinstance(value, list):
        return [
            _bounded_json(
                item, depth=depth + 1, max_object_fields=max_object_fields
            )
            for item in value[:24]
        ]
    if isinstance(value, str):
        return _clip(value)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return _clip(value)


def _semantic_sort(
    rows: Iterable[Dict[str, Any]],
    *,
    time_fields: Sequence[str],
    id_fields: Sequence[str],
) -> List[Dict[str, Any]]:
    def first(row: Dict[str, Any], fields: Sequence[str]) -> str:
        return next(
            (str(row.get(field, "")) for field in fields if row.get(field)), ""
        )

    return sorted(
        rows,
        key=lambda row: (first(row, time_fields), first(row, id_fields)),
        reverse=True,
    )


def _read_json_records(
    root: Path,
    pattern: str,
    *,
    lane: str,
    diagnostics: List[Dict[str, str]],
) -> List[Dict[str, Any]]:
    if not root.is_dir():
        return []
    records = []
    for path in root.glob(pattern):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            diagnostics.append(
                {"lane": lane, "source": str(path), "reason": type(exc).__name__}
            )
            continue
        if isinstance(value, dict):
            records.append(value)
        else:
            diagnostics.append(
                {"lane": lane, "source": str(path), "reason": "not_an_object"}
            )
    return records


def _read_jsonl(
    path: Path, *, lane: str, diagnostics: List[Dict[str, str]]
) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        diagnostics.append(
            {"lane": lane, "source": str(path), "reason": type(exc).__name__}
        )
        return []
    records = []
    for index, line in enumerate(lines, start=1):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            diagnostics.append(
                {
                    "lane": lane,
                    "source": f"{path}:{index}",
                    "reason": "JSONDecodeError",
                }
            )
            continue
        if isinstance(value, dict):
            records.append(value)
    return records


def _evidence_item(
    *,
    kind: str,
    status: str,
    epistemic_class: str,
    decision_authority: str,
    observed_at: str,
    source_ids: Sequence[str],
    payload: Dict[str, Any],
    stable_identity: Dict[str, Any],
    confidence: int = 0,
    freshness: str = "unknown",
    scope_keys: Sequence[str] = (),
    payload_field_limit: int = 32,
) -> Dict[str, Any]:
    bounded_payload = _bounded_json(payload, max_object_fields=payload_field_limit)
    identity = {
        "kind": kind,
        "stable_identity": stable_identity,
        "payload": bounded_payload,
        "source_ids": sorted(set(source_ids)),
    }
    return {
        "item_id": f"evidence-{_fingerprint(identity)[:16]}",
        "kind": kind,
        "status": status,
        "freshness": freshness,
        "epistemic_class": epistemic_class,
        "decision_authority": decision_authority,
        "delivery_authority_granted": False,
        "observed_at": observed_at,
        "scope_keys": sorted(set(scope_keys)),
        "source_ids": sorted(set(source_ids)),
        "source_record_fingerprint": _fingerprint(identity),
        "confidence": max(0, min(100, int(confidence or 0))),
        "payload": bounded_payload,
    }


_CLAIM_FIELD_BY_KIND = {
    "capability": "statement",
    "integration_gap": "statement",
    "knowledge_claim": "claim",
    "mission_outcome_observation": "observation",
    "workspace_document": "excerpt",
}


def _mission_claim_entry(item: Dict[str, Any]) -> Dict[str, Any] | None:
    """Project only host-owned source content into a mission-citable claim.

    A citation identifies a bounded source record; it never certifies wording
    authored later by an inventor model.  Advisory material and model
    interpretations remain useful context but intentionally have no entry in
    this ledger.
    """
    if item.get("decision_authority") != "mission_citable":
        return None
    epistemic_class = str(item.get("epistemic_class", "")).strip()
    if epistemic_class not in MISSION_CITABLE_EPISTEMIC_CLASSES:
        return None
    payload = item.get("payload")
    if not isinstance(payload, dict):
        return None
    bounded_payload = _bounded_json(payload)
    claim_field = _CLAIM_FIELD_BY_KIND.get(str(item.get("kind", "")))
    source_claim = bounded_payload.get(claim_field) if claim_field else None
    source_claim_preserved_verbatim = bool(
        claim_field
        and isinstance(source_claim, str)
        and source_claim.strip()
    )
    claim = (
        source_claim.strip()
        if source_claim_preserved_verbatim
        else _canonical_json(bounded_payload)
    )
    if not claim:
        return None
    source_record_fingerprint = str(
        item.get("source_record_fingerprint", "")
    ).strip()
    if not source_record_fingerprint:
        return None
    source_id = str(item.get("item_id", "")).strip()
    if not source_id:
        return None
    return {
        "source_id": source_id,
        "kind": str(item.get("kind", "")).strip(),
        "claim": _clip(claim),
        "claim_field": claim_field or "$",
        "claim_payload": bounded_payload,
        "confidence": max(0, min(100, int(item.get("confidence", 0) or 0))),
        "epistemic_class": epistemic_class,
        "observed_at": str(item.get("observed_at", "")).strip(),
        "freshness": str(item.get("freshness", "")).strip(),
        "source_record_fingerprint": source_record_fingerprint,
        "source_ids": sorted(
            {
                str(source).strip()
                for source in item.get("source_ids", [])
                if str(source).strip()
            }
        ),
        "custody": {
            "owner": "host",
            "projection": "bounded_source_payload",
            "source_claim_preserved_verbatim": source_claim_preserved_verbatim,
            "candidate_language_certified": False,
        },
    }


def _derive_mission_claim_ledger(
    items: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    entries = [
        entry
        for item in items
        if isinstance(item, dict)
        for entry in [_mission_claim_entry(item)]
        if entry is not None
    ]
    return sorted(entries, key=lambda entry: entry["source_id"])


def _append_capped(
    target: List[Dict[str, Any]],
    rows: Sequence[Dict[str, Any]],
    *,
    lane: str,
    manifest: Dict[str, Any],
) -> None:
    cap = LANE_CAPS[lane]
    target.extend(rows[:cap])
    if len(rows) > cap:
        manifest["truncated_lanes"].append(
            {"lane": lane, "included": cap, "excluded": len(rows) - cap}
        )
        manifest["excluded"].extend(
            {
                "id": str(row.get("item_id", "")),
                "lane": lane,
                "reason": "lane_cap",
            }
            for row in rows[cap:]
        )


def _snapshot_parts(snapshot: Dict[str, Any]) -> tuple[Dict[str, Any], str, str]:
    signals = snapshot.get("signals") if isinstance(snapshot.get("signals"), dict) else snapshot
    observation_id = _clip(
        snapshot.get("observation_id") or signals.get("observation_id"), 200
    )
    snapshot_fingerprint = _clip(
        snapshot.get("snapshot_fingerprint")
        or signals.get("snapshot_fingerprint")
        or _fingerprint(signals),
        200,
    )
    return signals, observation_id, snapshot_fingerprint


def _project_alignment(
    state_root: Path,
    *,
    manifest: Dict[str, Any],
) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
    from palamedes_product_alignment import ProductAlignmentStore

    try:
        context = ProductAlignmentStore(state_root / "product-alignment").active_context()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        manifest["diagnostics"].append(
            {"lane": "product_alignment", "source": "store", "reason": type(exc).__name__}
        )
        return {
            "purposes": [],
            "constraints": [],
            "open_evidence_gates": [],
            "current_satisfaction": [],
        }, []
    def authority_rows(rows: Any, id_field: str) -> List[Dict[str, Any]]:
        projected = []
        for row in rows if isinstance(rows, list) else []:
            if not isinstance(row, dict) or not _clip(row.get(id_field), 200):
                continue
            projected.append({
                id_field: _clip(row.get(id_field), 200),
                "statement": _clip(row.get("statement")),
                "status": _clip(row.get("status"), 80),
                "scope": _clip(row.get("scope", row.get("surface_key")), 300),
                "source_ids": _strings(
                    row.get("source_ids", row.get("evidence_ids", [])), 24
                ),
                "delivery_authority_granted": False,
            })
        return projected

    authority = {
        "purposes": authority_rows(context.get("purposes", []), "purpose_id"),
        "constraints": authority_rows(
            context.get("constraints", []), "constraint_id"
        ),
        "open_evidence_gates": [],
        "current_satisfaction": [],
    }
    items = []
    for lane, rows, id_field, kind in (
        ("capabilities", context.get("capabilities", []), "capability_id", "capability"),
        ("integration_gaps", context.get("integration_gaps", []), "gap_id", "integration_gap"),
    ):
        for row in rows:
            if not isinstance(row, dict):
                continue
            row_id = _clip(row.get(id_field), 200)
            if not row_id:
                continue
            payload = {
                key: row.get(key)
                for key in (
                    id_field,
                    "statement",
                    "surface_key",
                    "observed_path",
                    "status",
                    "expected_capability_id",
                )
                if key in row
            }
            items.append(
                _evidence_item(
                    kind=kind,
                    status=_clip(row.get("status", "active"), 80),
                    epistemic_class="host_verified",
                    decision_authority="mission_citable",
                    observed_at=_clip(row.get("observed_at"), 100),
                    source_ids=_strings(
                        row.get("source_ids", row.get("evidence_ids", [])), 20
                    ),
                    payload=payload,
                    stable_identity={"lane": lane, "id": row_id},
                    freshness="current",
                    scope_keys=[_clip(row.get("surface_key"), 200)]
                    if row.get("surface_key")
                    else [],
                )
            )
    return authority, items


def _project_satisfaction(
    state_root: Path, *, manifest: Dict[str, Any]
) -> List[Dict[str, Any]]:
    from palamedes_satisfaction import assessment_is_current

    rows = _read_json_records(
        state_root / "satisfaction",
        "satisfaction-*.json",
        lane="satisfaction",
        diagnostics=manifest["diagnostics"],
    )
    by_requirement: Dict[str, Dict[str, Any]] = {}
    for row in _semantic_sort(
        rows,
        time_fields=("assessed_at", "observed_at"),
        id_fields=("assessment_id",),
    ):
        requirement_id = _clip(row.get("requirement_id"), 200)
        if requirement_id and requirement_id not in by_requirement:
            by_requirement[requirement_id] = row
    current = []
    for requirement_id, row in sorted(by_requirement.items()):
        try:
            live_current = assessment_is_current(state_root.parent, row)
        except (OSError, ValueError):
            live_current = False
        if not live_current:
            continue
        current.append({
            "assessment_id": _clip(row.get("assessment_id"), 200),
            "requirement_id": requirement_id,
            "requirement": _clip(row.get("requirement")),
            "claim_type": _clip(row.get("claim_type"), 100),
            "evidence_state": _clip(row.get("evidence_state"), 100),
            "disposition": _clip(row.get("disposition"), 100),
            "purpose_alignment": _clip(row.get("purpose_alignment"), 100),
            "observed_at": _clip(row.get("observed_at"), 100),
            "live_current": True,
            "delivery_authority_granted": False,
        })
    return current


def _project_workspace_signals(
    signals: Dict[str, Any], observation_id: str
) -> List[Dict[str, Any]]:
    rows = []
    observed_at = _clip(signals.get("observed_at"), 100)
    for document in signals.get("documents", []):
        if not isinstance(document, dict):
            continue
        path = _clip(document.get("path"), 400)
        digest = _clip(document.get("content_sha256"), 100)
        if not path or not digest:
            continue
        rows.append(
            _evidence_item(
                kind="workspace_document",
                status="observed",
                epistemic_class="direct_observation",
                decision_authority="mission_citable",
                observed_at=observed_at,
                source_ids=[f"document:{path}@{digest}"],
                payload={
                    "path": path,
                    "content_sha256": digest,
                    "headings": _strings(document.get("headings"), 12),
                    "excerpt": _clip(document.get("excerpt")),
                    "excerpt_truncated": bool(document.get("excerpt_truncated")),
                },
                stable_identity={"path": path, "content_sha256": digest},
                freshness="current",
            )
        )
    git = signals.get("git") if isinstance(signals.get("git"), dict) else {}
    if observation_id or git:
        rows.append(
            _evidence_item(
                kind="workspace_observation",
                status="observed",
                epistemic_class="direct_observation",
                decision_authority="mission_citable",
                observed_at=observed_at,
                source_ids=[observation_id] if observation_id else [],
                payload={
                    "observation_id": observation_id,
                    "git_head": _clip(git.get("head"), 100),
                    "branch": _clip(git.get("branch"), 200),
                    "change": signals.get("change", {}),
                    "test": signals.get("test", {}),
                },
                stable_identity={"observation_id": observation_id, "git_head": git.get("head", "")},
                freshness="current",
            )
        )
    return rows


def _project_outcomes(
    state_root: Path, *, diagnostics: List[Dict[str, str]]
) -> tuple[List[Dict[str, Any]], set[str]]:
    mission_root = state_root / "missions"
    outcomes = _read_jsonl(
        mission_root / "outcomes.jsonl", lane="outcomes", diagnostics=diagnostics
    )
    interpretations = _read_jsonl(
        mission_root / "outcome-interpretations.jsonl",
        lane="outcome_interpretations",
        diagnostics=diagnostics,
    )
    items = []
    for row in _semantic_sort(
        outcomes,
        time_fields=("recorded_at", "created_at"),
        id_fields=("outcome_id",),
    ):
        outcome_id = _clip(row.get("outcome_id"), 200)
        if not outcome_id:
            continue
        status = _clip(
            row.get("reported_outcome_status", row.get("status", "unknown")), 80
        ).lower()
        execution = _clip(row.get("execution_status"), 80).lower()
        outcome_type = _clip(row.get("outcome_type"), 120).lower()
        items.append(
            _evidence_item(
                kind="mission_outcome_observation",
                status=status or "unknown",
                epistemic_class="direct_observation",
                decision_authority="mission_citable",
                observed_at=_clip(row.get("recorded_at", row.get("created_at")), 100),
                source_ids=[outcome_id],
                payload={
                    "outcome_id": outcome_id,
                    "mission_contract_id": _clip(row.get("mission_contract_id"), 200),
                    "execution_status": execution,
                    "reported_outcome_status": status,
                    "outcome_type": outcome_type,
                    "observation": _clip(row.get("observation")),
                    "evidence_source_type": _clip(row.get("evidence_source_type"), 120),
                    "attribution": _clip(row.get("attribution"), 600),
                },
                stable_identity={"outcome_id": outcome_id, "custody": "immutable_report"},
                freshness="current",
            )
        )
    for row in _semantic_sort(
        interpretations,
        time_fields=("interpreted_at", "created_at"),
        id_fields=("outcome_interpretation_id", "outcome_id"),
    ):
        outcome_id = _clip(row.get("outcome_id"), 200)
        interpretation_id = _clip(
            row.get("outcome_interpretation_id") or f"interpretation:{outcome_id}", 240
        )
        if not outcome_id:
            continue
        items.append(
            _evidence_item(
                kind="mission_outcome_interpretation",
                status="analysis",
                epistemic_class="model_interpretation",
                decision_authority="advisory",
                observed_at=_clip(row.get("interpreted_at", row.get("created_at")), 100),
                source_ids=[outcome_id],
                payload={
                    "interpretation_id": interpretation_id,
                    "source_outcome_id": outcome_id,
                    "causal_signature": _clip(row.get("causal_signature"), 800),
                    "mechanism_summary": _clip(row.get("mechanism_summary")),
                    "finding": _clip(row.get("finding"), 400),
                    "mission_disposition": _clip(row.get("mission_disposition"), 120),
                    "confidence": row.get("confidence", 0),
                },
                stable_identity={"interpretation_id": interpretation_id},
                confidence=row.get("confidence", 0),
                freshness="unknown",
            )
        )
    return items, _derive_direct_failure_ids(items)


def direct_failure_outcome_id(item: Any) -> str:
    """Return the outcome ID only for a direct, structurally adverse observation.

    Explicit success always wins over inconsistent execution/type fields.  This
    predicate is host-owned so citation allow-lists cannot promote an otherwise
    successful outcome into failure-earned authority.
    """

    if not isinstance(item, dict):
        return ""
    if (
        item.get("kind") != "mission_outcome_observation"
        or item.get("epistemic_class") != "direct_observation"
        or item.get("decision_authority") != "mission_citable"
    ):
        return ""
    payload = item.get("payload")
    if not isinstance(payload, dict):
        return ""
    outcome_id = _clip(payload.get("outcome_id"), 200)
    if not outcome_id:
        return ""
    reported_status = _clip(
        payload.get("reported_outcome_status", item.get("status", "unknown")), 80
    ).lower()
    item_status = _clip(item.get("status"), 80).lower()
    if reported_status and item_status and reported_status != item_status:
        return ""
    if reported_status == "success":
        return ""
    execution_status = _clip(payload.get("execution_status"), 80).lower()
    outcome_type = _clip(payload.get("outcome_type"), 120).lower()
    if (
        reported_status in {"failure", "mixed", "blocked"}
        or execution_status in {"failed", "blocked"}
        or outcome_type in {"adverse_result", "blocked_by_environment"}
    ):
        return outcome_id
    return ""


def _derive_direct_failure_ids(items: Iterable[Dict[str, Any]]) -> set[str]:
    return {
        outcome_id
        for item in items
        if (outcome_id := direct_failure_outcome_id(item))
    }


def _project_knowledge(
    state_root: Path, *, diagnostics: List[Dict[str, str]]
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    root = state_root / "knowledge"
    claims = _read_json_records(
        root / "claims", "*.json", lane="knowledge", diagnostics=diagnostics
    )
    unknown_rows = _read_json_records(
        root / "unknowns", "*.json", lane="unknowns", diagnostics=diagnostics
    )
    knowledge = []
    for row in _semantic_sort(
        (item for item in claims if item.get("status") == "active"),
        time_fields=("last_verified_at", "created_at"),
        id_fields=("knowledge_id",),
    ):
        knowledge_id = _clip(row.get("knowledge_id"), 200)
        if not knowledge_id:
            continue
        # Knowledge claims are authored by the cognition provider and persisted
        # with model-supplied claim/profile fields.  The current knowledge store
        # has no independently checkable host-attestation record that binds the
        # exact claim text to its cited source records.  Consequently neither a
        # strong-sounding claim_type nor evidence_layer can upgrade this lane's
        # custody.  A future promotion path must verify such a host-owned chain;
        # fields embedded in this record are never sufficient by themselves.
        knowledge.append(
            _evidence_item(
                kind="knowledge_claim",
                status="active",
                epistemic_class="model_interpretation",
                decision_authority="advisory",
                observed_at=_clip(row.get("last_verified_at"), 100),
                source_ids=_strings(row.get("source_ids"), 24),
                payload={
                    "knowledge_id": knowledge_id,
                    "domain": _clip(row.get("domain"), 100),
                    "claim_type": _clip(row.get("claim_type"), 100),
                    "claim": _clip(row.get("claim")),
                    "scope": _clip(row.get("scope"), 600),
                    "perspective": _clip(row.get("perspective"), 300),
                    "known_exclusions": _strings(row.get("known_exclusions"), 8),
                },
                stable_identity={"knowledge_id": knowledge_id},
                confidence=row.get("confidence", 0),
                freshness="current",
            )
        )
    unknowns = []
    for row in _semantic_sort(
        (item for item in unknown_rows if item.get("status") == "open"),
        time_fields=("last_seen_at", "first_seen_at"),
        id_fields=("unknown_id",),
    ):
        unknown_id = _clip(row.get("unknown_id"), 200)
        if not unknown_id:
            continue
        unknowns.append(
            _evidence_item(
                kind="unknown_boundary",
                status="open",
                epistemic_class="unknown",
                decision_authority="none",
                observed_at=_clip(row.get("last_seen_at"), 100),
                source_ids=_strings([row.get("source_observation_id")], 1),
                payload={
                    "unknown_id": unknown_id,
                    "subject": _clip(row.get("subject"), 500),
                    "missing_knowledge": _clip(row.get("missing_knowledge")),
                    "decision_consequence": _clip(row.get("decision_consequence")),
                    "needed_source": _clip(row.get("needed_source"), 600),
                    "wake_condition": _clip(row.get("wake_condition"), 600),
                },
                stable_identity={"unknown_id": unknown_id},
                freshness="current",
            )
        )
    return knowledge, unknowns


def _project_thoughts(
    state_root: Path, *, diagnostics: List[Dict[str, str]]
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], set[str]]:
    root = state_root / "thoughts"
    thought_rows = _read_json_records(
        root / "thoughts", "*.json", lane="thoughts", diagnostics=diagnostics
    )
    discovery_rows = _read_json_records(
        root / "discoveries", "*.json", lane="discoveries", diagnostics=diagnostics
    )
    thoughts = []
    for row in sorted(
        (item for item in thought_rows if item.get("status") in {"incubating", "reinforced"}),
        key=lambda item: (
            float(item.get("strength", 0)),
            str(item.get("last_revisited_at", "")),
            str(item.get("thought_id", "")),
        ),
        reverse=True,
    ):
        thought_id = _clip(row.get("thought_id"), 200)
        if not thought_id:
            continue
        thoughts.append(
            _evidence_item(
                kind="incubated_thought",
                status=_clip(row.get("status"), 80),
                epistemic_class="hypothesis",
                decision_authority="advisory",
                observed_at=_clip(row.get("last_revisited_at", row.get("created_at")), 100),
                source_ids=_strings(row.get("source_observation_ids"), 12),
                payload={
                    "thought_id": thought_id,
                    "kind": _clip(row.get("kind"), 100),
                    "content": _clip(row.get("content")),
                    "unexplained_residue": _clip(row.get("unexplained_residue")),
                    "perspective": _clip(row.get("perspective"), 300),
                    "wake_conditions": _strings(row.get("wake_conditions"), 8),
                },
                stable_identity={"thought_id": thought_id},
                confidence=round(float(row.get("strength", 0)) * 100),
                freshness="unknown",
            )
        )
    discoveries = []
    mission_eligible_ids = set()
    for row in _semantic_sort(
        (item for item in discovery_rows if item.get("status") == "candidate"),
        time_fields=("created_at",),
        id_fields=("discovery_id",),
    ):
        discovery_id = _clip(row.get("discovery_id"), 200)
        if not discovery_id:
            continue
        promotion_state = _clip(row.get("promotion_state"), 100)
        if promotion_state == "mission_eligible":
            mission_eligible_ids.add(discovery_id)
        discoveries.append(
            _evidence_item(
                kind="discovery",
                status=promotion_state or "candidate",
                epistemic_class="hypothesis",
                decision_authority=(
                    "mission_citable" if promotion_state == "mission_eligible" else "advisory"
                ),
                observed_at=_clip(row.get("created_at"), 100),
                source_ids=_strings(row.get("grounding_knowledge_ids"), 16),
                payload={
                    "discovery_id": discovery_id,
                    "thesis": _clip(row.get("thesis")),
                    "old_framing": _clip(row.get("old_framing"), 800),
                    "new_framing": _clip(row.get("new_framing"), 800),
                    "assumption_replaced": _clip(row.get("assumption_replaced"), 600),
                    "changed_decision": _clip(row.get("changed_decision"), 800),
                    "smallest_probe": _clip(row.get("smallest_probe"), 800),
                    "disconfirmation": _clip(row.get("disconfirmation"), 800),
                    "promotion_state": promotion_state,
                },
                stable_identity={"discovery_id": discovery_id},
                freshness="unknown",
            )
        )
    return thoughts, discoveries, mission_eligible_ids


def _project_opportunities(
    state_root: Path, *, diagnostics: List[Dict[str, str]], manifest: Dict[str, Any]
) -> List[Dict[str, Any]]:
    records = _read_json_records(
        state_root / "opportunities" / "records",
        "opportunity-*.json",
        lane="opportunities",
        diagnostics=diagnostics,
    )
    ordered = _semantic_sort(
        records,
        time_fields=("created_at",),
        id_fields=("opportunity_scout_id",),
    )
    if not ordered:
        return []
    record = ordered[0]
    scout_id = _clip(record.get("opportunity_scout_id"), 200)
    assessments = {
        str(row.get("opportunity_id", "")): row
        for row in record.get("critic", {}).get("assessments", [])
        if isinstance(row, dict)
    }
    top_ids = record.get("critic", {}).get("top_opportunity_ids", [])
    items = []
    for opportunity_id in top_ids:
        row = next(
            (
                item
                for item in record.get("opportunities", [])
                if isinstance(item, dict) and item.get("opportunity_id") == opportunity_id
            ),
            None,
        )
        assessment = assessments.get(str(opportunity_id), {})
        senior_truths = all(
            assessment.get(field) is True
            for field in (
                "insight_survives_name_removal",
                "second_order_accounted",
                "failure_basis_honest",
                "operational_burden_accounted",
            )
        )
        if not isinstance(row, dict) or assessment.get("disposition") not in {"surface_now", "validate"} or not senior_truths:
            manifest["excluded"].append(
                {"id": str(opportunity_id), "lane": "opportunity_hypotheses", "reason": "critic_ineligible"}
            )
            continue
        items.append(
            _evidence_item(
                kind="product_opportunity_hypothesis",
                status=_clip(assessment.get("disposition"), 100),
                epistemic_class="hypothesis",
                decision_authority="advisory",
                observed_at=_clip(record.get("created_at"), 100),
                source_ids=[scout_id, str(opportunity_id)],
                payload={
                    "opportunity_scout_id": scout_id,
                    "opportunity_id": _clip(opportunity_id, 200),
                    "title": _clip(row.get("title"), 500),
                    "observation": _clip(row.get("observation")),
                    "latent_need": _clip(row.get("latent_need")),
                    "current_gap": _clip(row.get("current_gap")),
                    "mechanism": _clip(row.get("mechanism")),
                    "behavior_change": _clip(row.get("behavior_change")),
                    "business_effect": _clip(row.get("business_effect")),
                    "failure_condition": _clip(row.get("failure_condition")),
                    "validation_probe": row.get("validation_probe", {}),
                    "architecture_transfer_lineage": row.get("architecture_transfer_lineage", []),
                },
                stable_identity={"scout_id": scout_id, "opportunity_id": opportunity_id},
                freshness="unknown",
            )
        )
    return items


def _project_inventions(
    state_root: Path, *, diagnostics: List[Dict[str, str]], manifest: Dict[str, Any]
) -> List[Dict[str, Any]]:
    records = _read_json_records(
        state_root / "inventions" / "records",
        "invention-*.json",
        lane="inventions",
        diagnostics=diagnostics,
    )
    commitments = _read_jsonl(
        state_root / "inventions" / "commitments.jsonl",
        lane="invention_commitments",
        diagnostics=diagnostics,
    )
    committed = {
        (str(row.get("product_invention_id", "")), str(row.get("candidate_id", ""))): row
        for row in commitments
    }
    items = []
    for record in _semantic_sort(
        records,
        time_fields=("created_at",),
        id_fields=("product_invention_id",),
    ):
        invention_id = _clip(record.get("product_invention_id"), 200)
        frontier = {
            str(row.get("candidate_id", "")): row
            for row in record.get("frontier", [])
            if isinstance(row, dict)
        }
        for candidate in record.get("candidates", []):
            if not isinstance(candidate, dict):
                continue
            candidate_id = _clip(candidate.get("candidate_id"), 200)
            disposition = frontier.get(candidate_id, {}).get("disposition", "needs_evidence")
            commitment = committed.get((invention_id, candidate_id))
            if disposition in {"merge", "reject"} and commitment is None:
                manifest["excluded"].append(
                    {"id": candidate_id, "lane": "invention_candidates", "reason": disposition}
                )
                continue
            items.append(
                _evidence_item(
                    kind="invention_candidate",
                    status="human_selected_hypothesis" if commitment else _clip(disposition, 100),
                    epistemic_class="hypothesis",
                    decision_authority="advisory",
                    observed_at=_clip(
                        commitment.get("committed_at") if commitment else record.get("created_at"), 100
                    ),
                    source_ids=[invention_id, candidate_id],
                    payload={
                        "product_invention_id": invention_id,
                        "candidate_id": candidate_id,
                        "thesis": _clip(candidate.get("thesis")),
                        "hidden_opportunity": _clip(candidate.get("hidden_opportunity")),
                        "observed_basis": _strings(candidate.get("observed_basis"), 10),
                        "structural_delta": candidate.get("structural_delta", {}),
                        "falsification_condition": _clip(candidate.get("falsification_condition")),
                        "frontier_disposition": disposition,
                        "human_commitment_id": _clip(
                            commitment.get("invention_commitment_id") if commitment else "", 200
                        ),
                    },
                    stable_identity={"invention_id": invention_id, "candidate_id": candidate_id},
                    freshness="unknown",
                )
            )
    return items


def _project_visions(
    state_root: Path, *, diagnostics: List[Dict[str, str]], manifest: Dict[str, Any]
) -> List[Dict[str, Any]]:
    from palamedes_vision import selected_vision_context

    records = _read_json_records(
        state_root / "visions" / "records",
        "*.json",
        lane="visions",
        diagnostics=diagnostics,
    )
    ordered = _semantic_sort(
        records, time_fields=("created_at",), id_fields=("vision_genesis_id",)
    )
    for record in ordered:
        context = selected_vision_context(record)
        if not context:
            continue
        if not context.get("requirement_gate_passed"):
            manifest["excluded"].append(
                {
                    "id": str(context.get("vision_genesis_id", "")),
                    "lane": "selected_vision",
                    "reason": "requirement_gate_not_passed",
                }
            )
            continue
        vision_id = _clip(context.get("vision_genesis_id"), 200)
        return [
            _evidence_item(
                kind="selected_product_vision",
                status="selected",
                epistemic_class="hypothesis",
                decision_authority="advisory",
                observed_at=_clip(record.get("created_at"), 100),
                source_ids=[vision_id],
                payload={
                    "vision_genesis_id": vision_id,
                    "selected_world": context.get("selected_world"),
                    "vision_brief": _clip(context.get("vision_brief")),
                    "assumptions": _strings(context.get("assumptions"), 12),
                    "falsifiers": _strings(context.get("falsifiers"), 12),
                    "investment_envelope": context.get("investment_envelope", {}),
                },
                stable_identity={"vision_id": vision_id},
                freshness="unknown",
            )
        ]
    return []


def _project_agendas(
    state_root: Path, *, manifest: Dict[str, Any]
) -> List[Dict[str, Any]]:
    agendas = []
    readers: Sequence[tuple[str, Callable[[], List[Dict[str, Any]]]]] = ()
    try:
        from palamedes_prompt import PromptAgendaStore
        from palamedes_reference_intelligence import ReferenceIntelligenceStore

        readers = (
            (
                "prompt_agenda",
                lambda: PromptAgendaStore(state_root / "missions" / "prompt-intelligence").active_agendas(),
            ),
            (
                "reference_agenda",
                lambda: ReferenceIntelligenceStore(state_root / "missions" / "reference-intelligence").active_agendas(),
            ),
        )
    except ImportError:
        readers = ()
    for kind, reader in readers:
        try:
            rows = reader()
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            manifest["diagnostics"].append(
                {"lane": kind, "source": "store", "reason": type(exc).__name__}
            )
            continue
        for row in rows:
            row_id = _clip(
                row.get("prompt_agenda_id")
                or row.get("reference_intelligence_id")
                or _fingerprint(row)[:16],
                200,
            )
            agendas.append(
                _evidence_item(
                    kind=kind,
                    status=_clip(row.get("status", "selected"), 80),
                    epistemic_class="hypothesis",
                    decision_authority="advisory",
                    observed_at=_clip(row.get("created_at"), 100),
                    source_ids=[row_id],
                    payload={
                        "agenda_id": row_id,
                        "prompt": _clip(row.get("prompt")),
                        "rationale": _clip(row.get("rationale")),
                        "grounding_source_ids": _strings(row.get("grounding_source_ids"), 16),
                        "stop_conditions": _strings(row.get("stop_conditions"), 10),
                    },
                    stable_identity={"kind": kind, "agenda_id": row_id},
                    freshness="unknown",
                )
            )
    return agendas


def _project_architecture(
    packet: Dict[str, Any] | None,
    mappings: List[Dict[str, Any]] | None,
    *,
    target_fact_ids: set[str],
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    if packet is None and not mappings:
        return [], []
    if not isinstance(packet, dict):
        raise ValueError("architecture mappings require a GitNexus evidence packet")

    from palamedes_architecture_transfer import (
        reverify_gitnexus_evidence_packet,
        validate_architecture_transfers,
    )

    # Architecture packets cross a persisted/external trust boundary here.
    # Re-read their revision-pinned Git objects; packet hashes alone are
    # reproducible by an attacker and are not evidence of repository custody.
    validated_packet = reverify_gitnexus_evidence_packet(packet)
    validated_mappings = []
    if mappings:
        validated_mappings = validate_architecture_transfers(
            mappings,
            evidence_packet=validated_packet,
            target_fact_ids=target_fact_ids,
            max_transfers=LANE_CAPS["transfer_mappings"],
        )
    patterns = [
        _evidence_item(
            kind="reference_architecture_pattern",
            status="degraded" if validated_packet["status"] == "degraded" else "candidate",
            epistemic_class="direct_observation",
            decision_authority="advisory",
            observed_at="",
            source_ids=[source["source_id"]],
            payload={
                key: source.get(key)
                for key in (
                    "source_id",
                    "repo_snapshot_id",
                    "repository",
                    "repository_path",
                    "revision",
                    "native_symbol_id",
                    "evidence_kind",
                    "file_path",
                    "symbol",
                    "start_line",
                    "end_line",
                    "excerpt",
                    "excerpt_sha256",
                    "revision_file_sha256",
                    "query_ids",
                    "authority",
                    "reference_instructions_executed",
                    "decision_authority_granted",
                    "design_authority_granted",
                    "selection_authority_granted",
                    "delivery_authority_granted",
                    "code_reuse_authority_granted",
                )
            },
            stable_identity={
                "source_id": source["source_id"],
                "repo_snapshot_id": source["repo_snapshot_id"],
                "excerpt_sha256": source["excerpt_sha256"],
            },
            freshness="current",
        )
        for source in validated_packet["sources"][: LANE_CAPS["reference_patterns"]]
    ]
    projected_mappings = [
        _evidence_item(
            kind="cross_domain_architecture_transfer",
            status="candidate",
            epistemic_class="hypothesis",
            decision_authority="advisory",
            observed_at="",
            source_ids=mapping["source_ids"],
            payload={
                **mapping,
                "evidence_packet_id": validated_packet["packet_id"],
            },
            stable_identity={
                "transfer_id": mapping["transfer_id"],
                "evidence_packet_id": validated_packet["packet_id"],
                "target_evidence_ids": mapping["target_evidence_ids"],
            },
            freshness="unknown",
            # A normalized transfer plus its explicit integrity context has
            # more fields than generic evidence. Preserve that complete host
            # contract; the total bundle byte ceiling still bounds the lane.
            payload_field_limit=48,
        )
        for mapping in validated_mappings[: LANE_CAPS["transfer_mappings"]]
    ]
    return patterns, projected_mappings


def _bundle_identity(bundle: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "bundle_version": bundle["bundle_version"],
        "request": bundle["request"],
        "workspace": bundle["workspace"],
        "authority_context": bundle["authority_context"],
        "product_signals": bundle["product_signals"],
        "outcome_memory": bundle["outcome_memory"],
        "knowledge": bundle["knowledge"],
        "unknowns": bundle["unknowns"],
        "exploration_frontier": bundle["exploration_frontier"],
        "cross_domain_transfer": bundle["cross_domain_transfer"],
        "mission_claim_ledger": bundle["mission_claim_ledger"],
        "citation_allowlists": bundle["citation_allowlists"],
        "selection_manifest": bundle["selection_manifest"],
        "delivery_authority_granted": False,
    }


def _legacy_v1_bundle_identity(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Reconstruct the exact identity sealed by cognition-evidence v1.

    This intentionally remains separate from the current identity.  It exists
    only so a frozen cycle can prove its old envelope was not modified before
    the host derives the narrower v2 claim ledger.
    """

    return {
        "bundle_version": bundle["bundle_version"],
        "request": bundle["request"],
        "workspace": bundle["workspace"],
        "authority_context": bundle["authority_context"],
        "product_signals": bundle["product_signals"],
        "outcome_memory": bundle["outcome_memory"],
        "knowledge": bundle["knowledge"],
        "unknowns": bundle["unknowns"],
        "exploration_frontier": bundle["exploration_frontier"],
        "cross_domain_transfer": bundle["cross_domain_transfer"],
        "citation_allowlists": bundle["citation_allowlists"],
        "selection_manifest": bundle["selection_manifest"],
        "delivery_authority_granted": False,
    }


def _bundle_items(bundle: Dict[str, Any]) -> List[Dict[str, Any]]:
    items = list(bundle.get("product_signals", []))
    items.extend(bundle.get("outcome_memory", []))
    items.extend(bundle.get("knowledge", []))
    items.extend(bundle.get("unknowns", []))
    frontier = bundle.get("exploration_frontier", {})
    if isinstance(frontier, dict):
        for rows in frontier.values():
            if isinstance(rows, list):
                items.extend(rows)
    transfer = bundle.get("cross_domain_transfer", {})
    if isinstance(transfer, dict):
        items.extend(transfer.get("reference_patterns", []))
        items.extend(transfer.get("transfer_mappings", []))
    return items


def upgrade_cognition_evidence_bundle_v1(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Safely and deterministically migrate a frozen v1 bundle to v2.

    The v1 fingerprint is verified *before* any migration.  The host then
    re-derives the mission claim ledger from the frozen source items and makes
    its IDs the exact mission citation allow-list.  Legacy architecture
    mappings are excluded because v1 did not bind their source-side claims to
    exact excerpts; silently carrying them forward would bless evidence under
    a contract it never satisfied.

    The input object is never mutated.
    """

    if not isinstance(bundle, dict) or bundle.get("bundle_version") != LEGACY_BUNDLE_VERSION:
        raise ValueError("expected a cognition evidence v1 bundle")
    if bundle.get("delivery_authority_granted") is not False:
        raise ValueError("legacy evidence cannot grant delivery authority")
    try:
        expected_v1_id = (
            "evidence-"
            + _fingerprint(_legacy_v1_bundle_identity(bundle))[:16]
        )
    except (KeyError, TypeError) as exc:
        raise ValueError("legacy cognition evidence bundle is incomplete") from exc
    if bundle.get("bundle_id") != expected_v1_id:
        raise ValueError("legacy cognition evidence bundle fingerprint mismatch")

    upgraded: Dict[str, Any] = json.loads(_canonical_json(bundle))
    transfer = upgraded.get("cross_domain_transfer")
    if not isinstance(transfer, dict):
        raise ValueError("legacy cross_domain_transfer must be an object")
    legacy_mappings = transfer.get("transfer_mappings", [])
    if not isinstance(legacy_mappings, list):
        raise ValueError("legacy transfer_mappings must be an array")
    dropped_mapping_ids = [
        str(row.get("item_id", "")).strip()
        for row in legacy_mappings
        if isinstance(row, dict) and str(row.get("item_id", "")).strip()
    ]
    transfer["transfer_mappings"] = []

    manifest = upgraded.get("selection_manifest")
    if not isinstance(manifest, dict):
        raise ValueError("legacy selection_manifest must be an object")
    dropped = set(dropped_mapping_ids)
    for field in ("included", "freshness_unknown_ids"):
        values = manifest.get(field, [])
        if isinstance(values, list):
            manifest[field] = [value for value in values if value not in dropped]
    if legacy_mappings:
        diagnostics = manifest.setdefault("diagnostics", [])
        if not isinstance(diagnostics, list):
            raise ValueError("legacy selection diagnostics must be an array")
        diagnostics.append(
            {
                "lane": "cross_domain_transfer",
                "source": "legacy_v1",
                "reason": "legacy_unverified_transfer_mapping_excluded",
            }
        )
        excluded = manifest.setdefault("excluded", [])
        if not isinstance(excluded, list):
            raise ValueError("legacy selection exclusions must be an array")
        excluded.extend(
            {
                "id": item_id,
                "lane": "transfer_mappings",
                "reason": "legacy_unverified_transfer_mapping_excluded",
            }
            for item_id in dropped_mapping_ids
        )
        upgraded["status"] = "degraded"

    allowlists = upgraded.get("citation_allowlists")
    if not isinstance(allowlists, dict):
        raise ValueError("legacy citation allowlists are required")
    allowlists["transfer_mapping_ids"] = []
    upgraded["bundle_version"] = BUNDLE_VERSION
    upgraded["mission_claim_ledger"] = _derive_mission_claim_ledger(
        _bundle_items(upgraded)
    )
    allowlists["mission_source_ids"] = sorted(
        entry["source_id"] for entry in upgraded["mission_claim_ledger"]
    )
    allowlists["direct_failure_ids"] = sorted(
        _derive_direct_failure_ids(upgraded.get("outcome_memory", []))
    )
    upgraded["bundle_id"] = ""
    upgraded["bundle_id"] = (
        "evidence-" + _fingerprint(_bundle_identity(upgraded))[:16]
    )
    if len(_canonical_json(upgraded).encode("utf-8")) > MAX_TOTAL_BYTES:
        raise ValueError("upgraded cognition evidence exceeds the bounded total byte budget")
    validate_cognition_evidence_bundle(upgraded)
    return upgraded


def build_cognition_evidence_bundle(
    *,
    state_root: Path,
    snapshot: Dict[str, Any],
    user_request: str,
    mode: str,
    architecture_packet: Dict[str, Any] | None = None,
    transfer_mappings: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Build one immutable decision context without granting action authority."""
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot must be an object")
    if mode not in {"product", "audit", "watch", "component", "micro"}:
        raise ValueError("unsupported cognition evidence mode")
    state_root = Path(state_root)
    signals, observation_id, snapshot_fingerprint = _snapshot_parts(snapshot)
    manifest: Dict[str, Any] = {
        "included": [],
        "excluded": [],
        "truncated_lanes": [],
        "freshness_unknown_ids": [],
        "diagnostics": [],
    }
    authority_context, alignment_items = _project_alignment(
        state_root, manifest=manifest
    )
    authority_context["current_satisfaction"] = _project_satisfaction(
        state_root, manifest=manifest
    )
    product_signals: List[Dict[str, Any]] = []
    _append_capped(
        product_signals,
        _project_workspace_signals(signals, observation_id) + alignment_items,
        lane="product_signals",
        manifest=manifest,
    )
    outcome_memory, direct_failure_ids = _project_outcomes(
        state_root, diagnostics=manifest["diagnostics"]
    )
    outcome_memory = outcome_memory[: LANE_CAPS["outcome_memory"]]
    direct_failure_ids = _derive_direct_failure_ids(outcome_memory)
    knowledge, unknowns = _project_knowledge(
        state_root, diagnostics=manifest["diagnostics"]
    )
    thoughts, discoveries, mission_eligible_discoveries = _project_thoughts(
        state_root, diagnostics=manifest["diagnostics"]
    )
    opportunities = _project_opportunities(
        state_root, diagnostics=manifest["diagnostics"], manifest=manifest
    )
    inventions = _project_inventions(
        state_root, diagnostics=manifest["diagnostics"], manifest=manifest
    )
    visions = [] if mode == "audit" else _project_visions(
        state_root, diagnostics=manifest["diagnostics"], manifest=manifest
    )
    agendas = _project_agendas(state_root, manifest=manifest)
    target_fact_ids = {
        item["item_id"] for item in product_signals
    } | {item["item_id"] for item in knowledge[: LANE_CAPS["knowledge"]]}
    patterns, mappings = _project_architecture(
        architecture_packet,
        transfer_mappings,
        target_fact_ids=target_fact_ids,
    )
    frontier = {
        "thoughts": thoughts[: LANE_CAPS["thoughts"]],
        "discoveries": discoveries[: LANE_CAPS["discoveries"]],
        "opportunity_hypotheses": opportunities[: LANE_CAPS["opportunity_hypotheses"]],
        "invention_candidates": inventions[: LANE_CAPS["invention_candidates"]],
        "selected_vision": visions[:1],
        "research_agendas": agendas[: LANE_CAPS["research_agendas"]],
    }
    all_items = product_signals + outcome_memory + knowledge[:24] + unknowns[:16]
    for rows in frontier.values():
        all_items.extend(rows)
    all_items.extend(patterns)
    all_items.extend(mappings)
    manifest["included"] = [item["item_id"] for item in all_items]
    manifest["freshness_unknown_ids"] = [
        item["item_id"] for item in all_items if item.get("freshness") == "unknown"
    ]
    raw_gates = _read_jsonl(
        state_root / "missions" / "outcome-gates.jsonl",
        lane="outcome_gates",
        diagnostics=manifest["diagnostics"],
    )
    authority_context["open_evidence_gates"] = [
        {
            "gate_id": _clip(row.get("gate_id"), 200),
            "status": _clip(row.get("status"), 80),
            "required_response": _clip(row.get("required_response")),
            "reason": _clip(row.get("reason")),
            "mission_contract_id": _clip(row.get("mission_contract_id"), 200),
            "delivery_authority_granted": False,
        }
        for row in raw_gates
        if isinstance(row, dict) and row.get("status") == "open"
    ]
    claim_ledger = _derive_mission_claim_ledger(all_items)
    citation_ids = {entry["source_id"] for entry in claim_ledger}
    bundle: Dict[str, Any] = {
        "bundle_version": BUNDLE_VERSION,
        "bundle_id": "",
        "created_at": utc_now(),
        "request": {
            "mode": mode,
            "user_request": _clip(user_request, 4_000),
            "request_fingerprint": _fingerprint(user_request),
        },
        "workspace": {
            "observation_id": observation_id,
            "snapshot_fingerprint": snapshot_fingerprint,
            "git_head": _clip(signals.get("git", {}).get("head"), 100)
            if isinstance(signals.get("git"), dict)
            else "",
        },
        "status": "degraded" if manifest["diagnostics"] else "ready",
        "authority_context": authority_context,
        "product_signals": product_signals,
        "outcome_memory": outcome_memory,
        "knowledge": knowledge[: LANE_CAPS["knowledge"]],
        "unknowns": unknowns[: LANE_CAPS["unknowns"]],
        "exploration_frontier": frontier,
        "cross_domain_transfer": {
            "reference_patterns": patterns,
            "transfer_mappings": mappings,
        },
        "mission_claim_ledger": claim_ledger,
        "citation_allowlists": {
            "mission_source_ids": sorted(citation_ids),
            "mission_eligible_discovery_ids": sorted(mission_eligible_discoveries),
            "direct_failure_ids": sorted(direct_failure_ids),
            "reference_pattern_ids": sorted(
                item["item_id"] for item in patterns
            ),
            "transfer_mapping_ids": sorted(item["item_id"] for item in mappings),
        },
        "selection_manifest": manifest,
        "delivery_authority_granted": False,
    }
    bundle["bundle_id"] = f"evidence-{_fingerprint(_bundle_identity(bundle))[:16]}"
    if len(_canonical_json(bundle).encode("utf-8")) > MAX_TOTAL_BYTES:
        raise ValueError("cognition evidence exceeds the bounded total byte budget")
    validate_cognition_evidence_bundle(bundle)
    return bundle


def validate_cognition_evidence_bundle(bundle: Dict[str, Any]) -> None:
    if not isinstance(bundle, dict) or bundle.get("bundle_version") != BUNDLE_VERSION:
        raise ValueError("invalid cognition evidence bundle version")
    if bundle.get("delivery_authority_granted") is not False:
        raise ValueError("evidence cannot grant delivery authority")
    expected = f"evidence-{_fingerprint(_bundle_identity(bundle))[:16]}"
    if bundle.get("bundle_id") != expected:
        raise ValueError("cognition evidence bundle fingerprint mismatch")
    items = list(bundle.get("product_signals", []))
    items.extend(bundle.get("outcome_memory", []))
    items.extend(bundle.get("knowledge", []))
    items.extend(bundle.get("unknowns", []))
    for rows in bundle.get("exploration_frontier", {}).values():
        if isinstance(rows, list):
            items.extend(rows)
    items.extend(bundle.get("cross_domain_transfer", {}).get("reference_patterns", []))
    items.extend(bundle.get("cross_domain_transfer", {}).get("transfer_mappings", []))
    item_ids = []
    for item in items:
        if not isinstance(item, dict) or not str(item.get("item_id", "")).strip():
            raise ValueError("every evidence item requires item_id")
        if item.get("delivery_authority_granted") is not False:
            raise ValueError("evidence item cannot grant delivery authority")
        item_ids.append(item["item_id"])
    if len(item_ids) != len(set(item_ids)):
        raise ValueError("evidence item IDs must be unique")
    available = set(item_ids)
    expected_claim_ledger = _derive_mission_claim_ledger(items)
    if bundle.get("mission_claim_ledger") != expected_claim_ledger:
        raise ValueError("mission claim ledger must be the exact host projection")
    mission_claim_ids = {
        entry["source_id"] for entry in expected_claim_ledger
    }
    allowlists = bundle.get("citation_allowlists")
    if not isinstance(allowlists, dict):
        raise ValueError("citation allowlists are required")
    for field in (
        "mission_source_ids",
        "reference_pattern_ids",
        "transfer_mapping_ids",
    ):
        values = allowlists.get(field)
        if (
            not isinstance(values, list)
            or len(values) != len(set(values))
            or not set(values).issubset(available)
        ):
            raise ValueError(f"{field} cites unavailable evidence")
    if set(allowlists["mission_source_ids"]) != mission_claim_ids:
        raise ValueError("mission source allowlist must exactly match the claim ledger")
    expected_direct_failure_ids = sorted(
        _derive_direct_failure_ids(bundle.get("outcome_memory", []))
    )
    if allowlists.get("direct_failure_ids") != expected_direct_failure_ids:
        raise ValueError(
            "direct failure allowlist must exactly match host-derived adverse outcomes"
        )
    reference_items = {
        item["item_id"]: item
        for item in bundle.get("cross_domain_transfer", {}).get(
            "reference_patterns", []
        )
        if isinstance(item, dict)
    }
    raw_reference_source_ids = {
        source_id
        for item in reference_items.values()
        for source_id in item.get("source_ids", [])
    }
    target_fact_ids = {
        item["item_id"]
        for item in list(bundle.get("product_signals", []))
        + list(bundle.get("knowledge", []))
        if isinstance(item, dict)
    }
    for item in bundle.get("cross_domain_transfer", {}).get(
        "transfer_mappings", []
    ):
        if not isinstance(item, dict):
            raise ValueError("architecture transfer evidence must be an object")
        payload = item.get("payload")
        if not isinstance(payload, dict):
            raise ValueError("architecture transfer payload must be an object")
        if not set(item.get("source_ids", [])).issubset(raw_reference_source_ids):
            raise ValueError("architecture transfer cites unavailable reference evidence")
        if not set(payload.get("target_evidence_ids", [])).issubset(target_fact_ids):
            raise ValueError("architecture transfer cites unavailable target evidence")
        if payload.get("source_outcome_is_target_forecast") is not False:
            raise ValueError("architecture source outcome cannot become a target forecast")
        if payload.get("same_primary_job") is not False:
            raise ValueError("architecture transfer must be genuinely cross-domain")
        if (
            payload.get("transfer_contract_version")
            != "palamedes-architecture-transfer/2"
        ):
            raise ValueError("architecture transfer contract version is invalid")
        if payload.get("source_support_semantics_verified") is not False:
            raise ValueError(
                "architecture source support cannot claim semantic verification"
            )
        if (
            payload.get("source_support_verification")
            != "normalized_exact_excerpt_membership_only"
        ):
            raise ValueError("architecture source support boundary is invalid")
        if not isinstance(payload.get("source_claim_support"), list) or not payload[
            "source_claim_support"
        ]:
            raise ValueError("architecture source claim support is required")
        for field in (
            "decision_authority_granted",
            "design_authority_granted",
            "selection_authority_granted",
            "delivery_authority_granted",
            "code_reuse_authority_granted",
        ):
            if payload.get(field) is not False:
                raise ValueError(f"architecture transfer {field} must be exactly false")


def project_cognition_evidence(bundle: Dict[str, Any], role: str) -> Dict[str, Any]:
    """Return only the evidence class a role is constitutionally allowed to see."""
    validate_cognition_evidence_bundle(bundle)
    base = {
        "bundle_version": bundle["bundle_version"],
        "bundle_id": bundle["bundle_id"],
        "request": bundle["request"],
        "workspace": bundle["workspace"],
        "delivery_authority_granted": False,
    }
    if role == "context_governor":
        return {
            **base,
            "authority_context": bundle["authority_context"],
            "product_signals": bundle["product_signals"],
            "selection_manifest": bundle["selection_manifest"],
        }
    if role == "interpreter":
        return {
            **base,
            "product_signals": bundle["product_signals"],
            "direct_outcomes": [
                item
                for item in bundle["outcome_memory"]
                if item.get("epistemic_class") == "direct_observation"
            ],
            "knowledge": bundle["knowledge"],
            "unknowns": bundle["unknowns"],
        }
    if role == "independent_inventor":
        return {
            **base,
            "product_signals": bundle["product_signals"],
            "knowledge": bundle["knowledge"],
            "unknowns": bundle["unknowns"],
        }
    if role == "transfer_inventor":
        return {
            **base,
            "outcome_memory": bundle["outcome_memory"],
            "exploration_frontier": bundle["exploration_frontier"],
            "cross_domain_transfer": bundle["cross_domain_transfer"],
        }
    if role == "adversary":
        return {
            **base,
            "authority_context": bundle["authority_context"],
            "product_signals": bundle["product_signals"],
            "outcome_memory": bundle["outcome_memory"],
            "knowledge": bundle["knowledge"],
            "unknowns": bundle["unknowns"],
            "exploration_frontier": bundle["exploration_frontier"],
            "cross_domain_transfer": bundle["cross_domain_transfer"],
            "selection_manifest": bundle["selection_manifest"],
        }
    if role == "selector":
        return {
            **base,
            "blocking_authority_context": bundle["authority_context"],
            "citation_allowlists": bundle["citation_allowlists"],
        }
    raise ValueError(f"unsupported cognition evidence role: {role}")


def citation_allowlist(bundle: Dict[str, Any], purpose: str) -> set[str]:
    validate_cognition_evidence_bundle(bundle)
    field = {
        "mission": "mission_source_ids",
        "discovery": "mission_eligible_discovery_ids",
        "direct_failure": "direct_failure_ids",
        "reference_pattern": "reference_pattern_ids",
        "transfer_mapping": "transfer_mapping_ids",
    }.get(purpose)
    if field is None:
        raise ValueError(f"unsupported citation purpose: {purpose}")
    return set(bundle["citation_allowlists"].get(field, []))


def mission_claim_ledger(bundle: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Return a detached, host-owned map of exact mission-citable claims.

    Ledger claims come only from direct observations or host-verified source
    records.  Model interpretations, hypotheses, advisory references, and
    unknowns never appear here even when they remain visible to cognition roles.
    """
    validate_cognition_evidence_bundle(bundle)
    return {
        entry["source_id"]: json.loads(_canonical_json(entry))
        for entry in bundle["mission_claim_ledger"]
    }


def project_mission_evidence(
    bundle: Dict[str, Any],
    source_ids: Sequence[str],
    *,
    strict: bool = True,
) -> List[Dict[str, Any]]:
    """Project cited source IDs into their exact host-owned evidence wording.

    The caller supplies IDs, not prose.  Consequently an inventor's
    ``observed_signal`` cannot replace the source claim merely by citing one of
    these IDs.  With ``strict=True`` (the default), any advisory or unavailable
    ID fails closed; callers intentionally filtering a mixed candidate scope may
    opt into ``strict=False`` and must still reject an empty result.
    """
    if isinstance(source_ids, (str, bytes)) or not isinstance(source_ids, Sequence):
        raise ValueError("mission evidence source_ids must be an array")
    requested: List[str] = []
    for index, source_id in enumerate(source_ids):
        normalized = str(source_id or "").strip()
        if not normalized:
            raise ValueError(
                f"mission evidence source_ids[{index}] must be a non-empty string"
            )
        if normalized not in requested:
            requested.append(normalized)
    ledger = mission_claim_ledger(bundle)
    unavailable = [source_id for source_id in requested if source_id not in ledger]
    if strict and unavailable:
        raise ValueError(
            "mission evidence cites non-citable or unavailable source IDs: "
            + ", ".join(unavailable)
        )
    projected = []
    for source_id in requested:
        entry = ledger.get(source_id)
        if entry is None:
            continue
        projected.append(
            {
                "claim": entry["claim"],
                "source": source_id,
                "confidence": entry["confidence"],
                "epistemic_class": entry["epistemic_class"],
                "claim_payload": entry["claim_payload"],
                "custody": entry["custody"],
                "source_record_fingerprint": entry["source_record_fingerprint"],
            }
        )
    return projected
