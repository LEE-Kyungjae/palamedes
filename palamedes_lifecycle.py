#!/usr/bin/env python3
"""Append-only mission lifecycle projection and conservative reconciliation."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


LIFECYCLE_VERSION = "palamedes-lifecycle-event/1"
RECONCILE_VERSION = "palamedes-lifecycle-reconcile/1"
AUDIT_VERSION = "palamedes-lifecycle-semantic-audit/1"
STATES = {
    "selected",
    "handed_off",
    "acknowledged_by_implementer",
    "executing",
    "evidence_submitted",
    "outcome_recorded",
    "closed",
    "follow_up_required",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fingerprint(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _read_jsonl(path: Path) -> tuple[List[Dict[str, Any]], List[int]]:
    rows: List[Dict[str, Any]] = []
    malformed: List[int] = []
    if not path.is_file():
        return rows, malformed
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            malformed.append(line_number)
            continue
        if isinstance(value, dict):
            rows.append(value)
        else:
            malformed.append(line_number)
    return rows, malformed


def _scope_keys(*values: Dict[str, Any]) -> List[str]:
    keys = set()
    for value in values:
        explicit = value.get("scope_keys", [])
        if isinstance(explicit, list):
            keys.update(
                item.strip()
                for item in explicit
                if isinstance(item, str) and item.strip()
            )
        surface = str(value.get("surface_key", "")).strip()
        if surface:
            keys.add(f"surface:{surface}")
    return sorted(keys)


class LifecycleStore:
    def __init__(self, mission_root: Path) -> None:
        self.mission_root = mission_root
        self.events_path = mission_root / "lifecycle-events.jsonl"

    def events(self) -> List[Dict[str, Any]]:
        rows, _ = _read_jsonl(self.events_path)
        return rows

    def append(self, event: Dict[str, Any]) -> bool:
        validated = validate_event(event)
        self.events_path.parent.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            handle.seek(0)
            existing_ids = set()
            for line in handle:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(row, dict):
                    existing_ids.add(row.get("event_id"))
            if validated["event_id"] in existing_ids:
                return False
            handle.seek(0, os.SEEK_END)
            handle.write(
                json.dumps(validated, ensure_ascii=False, sort_keys=True) + "\n"
            )
            handle.flush()
            os.fsync(handle.fileno())
        return True


def validate_event(event: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(event, dict):
        raise ValueError("lifecycle event must be an object")
    state = str(event.get("state", "")).strip()
    if state not in STATES:
        raise ValueError("lifecycle event has an unsupported state")
    for field, prefix in (
        ("event_id", "lifecycle-"),
        ("handoff_id", "handoff-"),
        ("mission_contract_id", "mission-"),
    ):
        if not str(event.get(field, "")).strip().startswith(prefix):
            raise ValueError(f"lifecycle event requires {field}")
    source_ids = event.get("source_artifact_ids")
    if (
        not isinstance(source_ids, list)
        or not source_ids
        or not all(isinstance(item, str) and item.strip() for item in source_ids)
    ):
        raise ValueError("lifecycle event requires source_artifact_ids")
    reason = str(event.get("reason", "")).strip()
    if not reason:
        raise ValueError("lifecycle event requires reason")
    normalized = dict(event)
    normalized["state"] = state
    normalized["source_artifact_ids"] = sorted({item.strip() for item in source_ids})
    normalized["scope_keys"] = _scope_keys(event)
    normalized["reason"] = reason
    normalized.setdefault("recorded_at", _utc_now())
    normalized.setdefault("event_version", LIFECYCLE_VERSION)
    normalized.setdefault("actor", "palamedes-reconciler")
    normalized.setdefault("correction_of_event_ids", [])
    return normalized


def _proposal(
    *,
    handoff: Dict[str, Any],
    contract: Dict[str, Any],
    state: str,
    source_artifact_ids: Iterable[str],
    reason: str,
) -> Dict[str, Any]:
    identity = {
        "handoff_id": handoff["handoff_id"],
        "mission_contract_id": handoff["mission_contract_id"],
        "state": state,
        "source_artifact_ids": sorted(set(source_artifact_ids)),
        "reconcile_version": RECONCILE_VERSION,
    }
    return validate_event(
        {
            "event_version": LIFECYCLE_VERSION,
            "event_id": f"lifecycle-{_fingerprint(identity)[:16]}",
            "handoff_id": handoff["handoff_id"],
            "mission_contract_id": handoff["mission_contract_id"],
            "state": state,
            "source_artifact_ids": identity["source_artifact_ids"],
            "scope_keys": _scope_keys(handoff, contract),
            "reason": reason,
            "reconcile_version": RECONCILE_VERSION,
            "recorded_at": _utc_now(),
            "actor": "palamedes-reconciler",
            "correction_of_event_ids": [],
        }
    )


def reconcile_lifecycle(
    mission_root: Path,
    *,
    apply: bool = False,
    expected_proposal_fingerprint: str = "",
) -> Dict[str, Any]:
    handoff_root = mission_root / "handoffs"
    handoffs = (
        [
            row
            for row in (
                _read_json(path) for path in sorted(handoff_root.glob("handoff-*.json"))
            )
            if isinstance(row, dict)
        ]
        if handoff_root.is_dir()
        else []
    )
    contracts = {
        row["mission_id"]: row
        for row in (
            _read_json(path) for path in sorted(mission_root.glob("mission-*.json"))
        )
        if isinstance(row, dict) and isinstance(row.get("mission_id"), str)
    }
    outcomes, malformed_outcomes = _read_jsonl(mission_root / "outcomes.jsonl")
    gates, malformed_gates = _read_jsonl(mission_root / "outcome-gates.jsonl")
    store = LifecycleStore(mission_root)
    events, malformed_events = _read_jsonl(store.events_path)

    outcomes_by_mission: Dict[str, List[Dict[str, Any]]] = {}
    for outcome in outcomes:
        outcomes_by_mission.setdefault(
            str(outcome.get("mission_contract_id", "")), []
        ).append(outcome)
    latest_gates: Dict[str, Dict[str, Any]] = {}
    for gate in gates:
        gate_id = str(gate.get("gate_id", ""))
        if gate_id:
            latest_gates[gate_id] = gate
    open_gates_by_mission: Dict[str, List[Dict[str, Any]]] = {}
    for gate in latest_gates.values():
        if gate.get("status") == "open":
            open_gates_by_mission.setdefault(
                str(gate.get("mission_contract_id", "")), []
            ).append(gate)
    events_by_handoff: Dict[str, List[Dict[str, Any]]] = {}
    for event in events:
        events_by_handoff.setdefault(str(event.get("handoff_id", "")), []).append(event)
    mission_handoff_counts: Dict[str, int] = {}
    for handoff in handoffs:
        mission_id = str(handoff.get("mission_contract_id", ""))
        mission_handoff_counts[mission_id] = (
            mission_handoff_counts.get(mission_id, 0) + 1
        )

    items, proposals, conflicts = [], [], []
    for handoff in handoffs:
        handoff_id = str(handoff.get("handoff_id", ""))
        mission_id = str(handoff.get("mission_contract_id", ""))
        contract = contracts.get(mission_id, {})
        linked_outcomes = outcomes_by_mission.get(mission_id, [])
        open_gates = open_gates_by_mission.get(mission_id, [])
        linked_events = events_by_handoff.get(handoff_id, [])
        item_conflicts = []
        if not handoff_id.startswith("handoff-") or not mission_id.startswith(
            "mission-"
        ):
            item_conflicts.append("invalid_identity")
        if mission_id not in contracts:
            item_conflicts.append("missing_contract")
        if mission_handoff_counts.get(mission_id, 0) > 1:
            item_conflicts.append("duplicate_handoff_for_mission")
        for event in linked_events:
            try:
                validate_event(event)
            except ValueError:
                item_conflicts.append("invalid_lifecycle_event")
                break
        proposal = None
        if item_conflicts:
            projected_state, classification = "unresolved", "conflict"
        else:
            latest_event = linked_events[-1] if linked_events else None
            projected_state = (
                str(latest_event["state"])
                if latest_event
                else (
                    "follow_up_required"
                    if open_gates
                    else "outcome_recorded" if linked_outcomes else "handed_off"
                )
            )
            desired_state = (
                "follow_up_required"
                if open_gates
                else "outcome_recorded" if linked_outcomes else "handed_off"
            )
            classification = (
                "valid_wait"
                if desired_state == "handed_off"
                else (
                    "open_follow_up"
                    if desired_state == "follow_up_required"
                    else "legacy_projection_gap" if not linked_events else "projected"
                )
            )
            if desired_state != "handed_off" and (
                not linked_events or projected_state != desired_state
            ):
                source_ids = [handoff_id]
                source_ids.extend(str(row.get("outcome_id")) for row in linked_outcomes)
                source_ids.extend(str(row.get("gate_id")) for row in open_gates)
                proposal = _proposal(
                    handoff=handoff,
                    contract=contract,
                    state=desired_state,
                    source_artifact_ids=source_ids,
                    reason="Backfill lifecycle projection from immutable handoff, outcome, and gate evidence.",
                )
                proposals.append(proposal)
        if item_conflicts:
            conflicts.append(
                {"handoff_id": handoff_id, "reasons": sorted(set(item_conflicts))}
            )
        items.append(
            {
                "handoff_id": handoff_id,
                "mission_contract_id": mission_id,
                "immutable_status": handoff.get("status"),
                "outcome_ids": [row.get("outcome_id") for row in linked_outcomes],
                "open_gate_ids": [row.get("gate_id") for row in open_gates],
                "lifecycle_event_ids": [row.get("event_id") for row in linked_events],
                "projected_state": projected_state,
                "classification": classification,
                "conflicts": sorted(set(item_conflicts)),
                "proposal_event_id": proposal.get("event_id") if proposal else None,
            }
        )

    known_missions = set(contracts)
    orphan_outcomes = [
        row.get("outcome_id")
        for mission_id, rows in outcomes_by_mission.items()
        if mission_id not in known_missions
        for row in rows
    ]
    proposal_fingerprint = _fingerprint(
        [
            {key: value for key, value in proposal.items() if key != "recorded_at"}
            for proposal in proposals
        ]
    )
    if apply and expected_proposal_fingerprint != proposal_fingerprint:
        raise ValueError(
            "reconcile apply requires the exact proposal fingerprint from a fresh dry-run"
        )
    applied = 0
    if apply:
        for proposal in proposals:
            if store.append(proposal):
                applied += 1
    report = {
        "reconcile_version": RECONCILE_VERSION,
        "proposal_fingerprint": proposal_fingerprint,
        "mode": "apply" if apply else "dry_run",
        "summary": {
            "handoffs": len(handoffs),
            "outcomes": len(outcomes),
            "existing_events": len(events),
            "proposals": len(proposals),
            "applied": applied,
            "conflicts": len(conflicts),
            "orphan_outcomes": len(orphan_outcomes),
            "malformed_records": len(malformed_outcomes)
            + len(malformed_gates)
            + len(malformed_events),
            "by_projected_state": dict(
                sorted(Counter(item["projected_state"] for item in items).items())
            ),
            "by_classification": dict(
                sorted(Counter(item["classification"] for item in items).items())
            ),
        },
        "items": items,
        "proposals": proposals,
        "conflicts": conflicts,
        "orphan_outcome_ids": orphan_outcomes,
        "malformed": {
            "outcomes": malformed_outcomes,
            "gates": malformed_gates,
            "events": malformed_events,
        },
    }
    fingerprint_payload = dict(report)
    fingerprint_payload["proposals"] = [
        {key: value for key, value in proposal.items() if key != "recorded_at"}
        for proposal in proposals
    ]
    report["report_fingerprint"] = _fingerprint(fingerprint_payload)
    report["generated_at"] = _utc_now()
    return report


def audit_lifecycle_events(mission_root: Path) -> Dict[str, Any]:
    """Independently replay reconciler event meaning from immutable sources.

    This is deliberately read-only.  Unsupported events yield deterministic
    correction proposals; they are never deleted or silently rewritten.
    """
    handoffs = {
        row["handoff_id"]: row
        for row in (
            _read_json(path)
            for path in sorted((mission_root / "handoffs").glob("handoff-*.json"))
        )
        if isinstance(row, dict) and isinstance(row.get("handoff_id"), str)
    }
    contracts = {
        row["mission_id"]: row
        for row in (
            _read_json(path) for path in sorted(mission_root.glob("mission-*.json"))
        )
        if isinstance(row, dict) and isinstance(row.get("mission_id"), str)
    }
    outcomes, malformed_outcomes = _read_jsonl(mission_root / "outcomes.jsonl")
    gates, malformed_gates = _read_jsonl(mission_root / "outcome-gates.jsonl")
    events, malformed_events = _read_jsonl(mission_root / "lifecycle-events.jsonl")
    outcomes_by_mission: Dict[str, List[Dict[str, Any]]] = {}
    for outcome in outcomes:
        outcomes_by_mission.setdefault(
            str(outcome.get("mission_contract_id", "")), []
        ).append(outcome)
    latest_gates: Dict[str, Dict[str, Any]] = {}
    for gate in gates:
        if gate.get("gate_id"):
            latest_gates[str(gate["gate_id"])] = gate
    open_gates_by_mission: Dict[str, List[Dict[str, Any]]] = {}
    for gate in latest_gates.values():
        if gate.get("status") == "open":
            open_gates_by_mission.setdefault(
                str(gate.get("mission_contract_id", "")), []
            ).append(gate)

    results: List[Dict[str, Any]] = []
    corrections: List[Dict[str, Any]] = []
    for event in events:
        reasons: List[str] = []
        try:
            normalized = validate_event(event)
        except ValueError as exc:
            results.append(
                {
                    "event_id": event.get("event_id"),
                    "supported": False,
                    "reasons": [f"invalid_event:{exc}"],
                }
            )
            continue
        handoff = handoffs.get(normalized["handoff_id"])
        mission_id = normalized["mission_contract_id"]
        contract = contracts.get(mission_id)
        if not handoff:
            reasons.append("missing_handoff")
        elif handoff.get("mission_contract_id") != mission_id:
            reasons.append("handoff_mission_mismatch")
        if not contract:
            reasons.append("missing_contract")
        linked_outcomes = outcomes_by_mission.get(mission_id, [])
        open_gates = open_gates_by_mission.get(mission_id, [])
        desired_state = (
            "follow_up_required"
            if open_gates
            else "outcome_recorded" if linked_outcomes else "handed_off"
        )
        expected_sources = {normalized["handoff_id"]}
        expected_sources.update(str(row.get("outcome_id")) for row in linked_outcomes)
        expected_sources.update(str(row.get("gate_id")) for row in open_gates)
        if normalized["state"] != desired_state:
            reasons.append("projected_state_mismatch")
        if set(normalized["source_artifact_ids"]) != expected_sources:
            reasons.append("source_artifact_set_mismatch")
        if (
            handoff
            and contract
            and normalized["scope_keys"] != _scope_keys(handoff, contract)
        ):
            reasons.append("scope_projection_mismatch")
        if normalized.get("reconcile_version") == RECONCILE_VERSION and handoff:
            identity = {
                "handoff_id": normalized["handoff_id"],
                "mission_contract_id": mission_id,
                "state": normalized["state"],
                "source_artifact_ids": normalized["source_artifact_ids"],
                "reconcile_version": RECONCILE_VERSION,
            }
            if normalized["event_id"] != f"lifecycle-{_fingerprint(identity)[:16]}":
                reasons.append("event_identity_mismatch")
        result = {
            "event_id": normalized["event_id"],
            "handoff_id": normalized["handoff_id"],
            "supported": not reasons,
            "reasons": sorted(set(reasons)),
            "observed_state": normalized["state"],
            "replayed_state": desired_state,
        }
        results.append(result)
        if reasons and handoff and contract:
            correction = _proposal(
                handoff=handoff,
                contract=contract,
                state=desired_state,
                source_artifact_ids=expected_sources,
                reason="Correct an unsupported lifecycle projection identified by semantic replay.",
            )
            correction["actor"] = "palamedes-lifecycle-semantic-auditor"
            correction["audit_version"] = AUDIT_VERSION
            correction["correction_of_event_ids"] = [normalized["event_id"]]
            correction_identity = {
                "audit_version": AUDIT_VERSION,
                "correction_of_event_ids": correction["correction_of_event_ids"],
                "handoff_id": correction["handoff_id"],
                "mission_contract_id": correction["mission_contract_id"],
                "state": correction["state"],
                "source_artifact_ids": correction["source_artifact_ids"],
            }
            correction["event_id"] = (
                f"lifecycle-{_fingerprint(correction_identity)[:16]}"
            )
            corrections.append(validate_event(correction))
    stable_results = [
        {key: value for key, value in row.items() if key != "recorded_at"}
        for row in results
    ]
    stable_corrections = [
        {key: value for key, value in row.items() if key != "recorded_at"}
        for row in corrections
    ]
    return {
        "audit_version": AUDIT_VERSION,
        "read_only": True,
        "summary": {
            "events": len(events),
            "supported": sum(1 for row in results if row["supported"]),
            "unsupported": sum(1 for row in results if not row["supported"]),
            "correction_proposals": len(corrections),
            "malformed_records": len(malformed_outcomes)
            + len(malformed_gates)
            + len(malformed_events),
        },
        "results": results,
        "correction_proposals": corrections,
        "audit_fingerprint": _fingerprint(
            {
                "audit_version": AUDIT_VERSION,
                "results": stable_results,
                "correction_proposals": stable_corrections,
            }
        ),
        "mutation_performed": False,
        "generated_at": _utc_now(),
    }
