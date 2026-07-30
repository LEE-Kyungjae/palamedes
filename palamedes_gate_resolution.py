#!/usr/bin/env python3
"""Two-phase, evidence-bound closure for outcome follow-up gates."""
from __future__ import annotations
import fcntl, hashlib, json, os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

RESOLUTION_VERSION = "palamedes-gate-evidence-resolution/1"


def _utc_now():
    return datetime.now(timezone.utc).isoformat()


def _fingerprint(value):
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()


def _latest_gates(path: Path) -> Dict[str, Dict[str, Any]]:
    latest = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict) and str(row.get("gate_id", "")).startswith(
                "gate-"
            ):
                latest[row["gate_id"]] = row
    return latest


def _verified_evidence(evidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(evidence, list) or len(evidence) < 2:
        raise ValueError("gate resolution requires at least two evidence artifacts")
    normalized, kinds = [], set()
    for item in evidence:
        if not isinstance(item, dict):
            raise ValueError("gate evidence must be an object")
        kind, claim = (
            str(item.get("kind", "")).strip(),
            str(item.get("claim", "")).strip(),
        )
        path = Path(str(item.get("path", ""))).expanduser().resolve()
        expected = str(item.get("sha256", "")).strip()
        if not kind or not claim or not path.is_file() or len(expected) != 64:
            raise ValueError(
                "gate evidence requires kind, claim, existing path, and sha256"
            )
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"stale or mismatched gate evidence: {path}")
        kinds.add(kind)
        normalized.append(
            {
                "kind": kind,
                "claim": claim,
                "path": str(path),
                "sha256": actual,
                "size_bytes": path.stat().st_size,
            }
        )
    if "runtime_audit" not in kinds or not ({"test", "source"} & kinds):
        raise ValueError(
            "gate resolution requires runtime_audit plus test or source evidence"
        )
    return sorted(normalized, key=lambda row: (row["kind"], row["path"]))


def propose_gate_resolution(
    mission_root: Path,
    *,
    gate_id: str,
    evidence: List[Dict[str, Any]],
    coverage_assertions: List[str],
    reviewer: str,
) -> Dict[str, Any]:
    gate = _latest_gates(mission_root / "outcome-gates.jsonl").get(gate_id)
    if not gate or gate.get("status") != "open":
        raise ValueError("gate resolution requires an existing open gate")
    assertions = sorted({str(x).strip() for x in coverage_assertions if str(x).strip()})
    if not assertions or not reviewer.strip():
        raise ValueError("gate resolution requires coverage assertions and reviewer")
    core = {
        "resolution_version": RESOLUTION_VERSION,
        "gate_id": gate_id,
        "outcome_id": gate.get("outcome_id"),
        "mission_contract_id": gate.get("mission_contract_id"),
        "gate_required_response": gate.get("required_response"),
        "evidence": _verified_evidence(evidence),
        "coverage_assertions": assertions,
        "reviewer": reviewer.strip(),
        "authority_required": True,
        "mutation_performed": False,
    }
    core["proposal_fingerprint"] = _fingerprint(core)
    return core


def _append_once(path: Path, row: Dict[str, Any], identity_field: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.seek(0)
        for line in handle:
            try:
                existing = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(existing, dict) and existing.get(identity_field) == row.get(
                identity_field
            ):
                return False
        handle.seek(0, os.SEEK_END)
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return True


def apply_gate_resolution(
    mission_root: Path,
    *,
    gate_id: str,
    evidence: List[Dict[str, Any]],
    coverage_assertions: List[str],
    reviewer: str,
    expected_proposal_fingerprint: str,
) -> Dict[str, Any]:
    proposal = propose_gate_resolution(
        mission_root,
        gate_id=gate_id,
        evidence=evidence,
        coverage_assertions=coverage_assertions,
        reviewer=reviewer,
    )
    if proposal["proposal_fingerprint"] != expected_proposal_fingerprint:
        raise ValueError(
            "gate resolution apply requires the exact fresh proposal fingerprint"
        )
    resolution_id = f"gate-resolution-{proposal['proposal_fingerprint'][:16]}"
    resolution = {
        **proposal,
        "resolution_id": resolution_id,
        "recorded_at": _utc_now(),
        "mutation_performed": True,
    }
    _append_once(
        mission_root / "gate-resolution-events.jsonl", resolution, "resolution_id"
    )
    gate = _latest_gates(mission_root / "outcome-gates.jsonl")[gate_id]
    closed = {
        **gate,
        "status": "responded",
        "closed_at": _utc_now(),
        "followup_still_required": False,
        "successor_state": "evidence_verified",
        "resolution_id": resolution_id,
        "resolution_fingerprint": proposal["proposal_fingerprint"],
        "resolution_reviewer": reviewer.strip(),
        "gate_revision_id": resolution_id,
    }
    _append_once(mission_root / "outcome-gates.jsonl", closed, "gate_revision_id")
    return resolution
