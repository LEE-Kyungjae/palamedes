#!/usr/bin/env python3
"""Host-verified already-satisfied and claim-evidence assessment."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


ASSESSMENT_VERSION = "palamedes-satisfaction-assessment/1"
CLAIM_REQUIREMENTS = {
    "function_rule": {"symbol", "test"},
    "integration": {"symbol", "call_path", "integration_test"},
    "layout": {"symbol", "render"},
    "accessibility": {"symbol", "accessibility_test", "render_small_large_text"},
    "multiplayer": {"symbol", "two_device_e2e"},
    "reconnect": {"symbol", "disconnect_recovery_e2e"},
    "fun": {"human_playtest"},
    "retention": {"behavior_data"},
    "release": {"functional", "operational", "security", "performance", "localization"},
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _run_git(workspace: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(workspace), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
        timeout=20,
    )
    return result.stdout if result.returncode == 0 else ""


def workspace_snapshot(workspace: Path) -> Dict[str, Any]:
    workspace = workspace.resolve()
    head = _run_git(workspace, "rev-parse", "HEAD").strip()
    diff = _run_git(workspace, "diff", "--no-ext-diff", "--binary", "HEAD")
    untracked = sorted(
        line.strip()
        for line in _run_git(
            workspace, "ls-files", "--others", "--exclude-standard"
        ).splitlines()
        if line.strip()
    )
    if not head:
        untracked = sorted(
            str(path.relative_to(workspace))
            for path in workspace.rglob("*")
            if path.is_file()
            and not path.is_symlink()
            and ".palamedes" not in path.relative_to(workspace).parts
            and ".git" not in path.relative_to(workspace).parts
        )
    untracked_hashes = []
    for relative in untracked:
        path = (workspace / relative).resolve()
        try:
            path.relative_to(workspace)
        except ValueError:
            continue
        if path.is_file() and path.stat().st_size <= 1_000_000:
            untracked_hashes.append(
                {
                    "path": relative,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                }
            )
        else:
            untracked_hashes.append(
                {"path": relative, "sha256": "unhashed-large-or-nonfile"}
            )
    worktree_material = {
        "head": head,
        "diff_sha256": hashlib.sha256(diff.encode("utf-8")).hexdigest(),
        "untracked": untracked_hashes,
    }
    return {
        "git_head": head,
        "worktree_fingerprint": _fingerprint(worktree_material),
        "dirty": bool(diff or untracked),
    }


def _resolve_evidence_path(workspace: Path, relative: str) -> Optional[Path]:
    if not relative:
        return None
    path = (workspace / relative).resolve()
    try:
        path.relative_to(workspace.resolve())
    except ValueError:
        return None
    return path


def _artifact_verified(workspace: Path, item: Dict[str, Any]) -> bool:
    path = _resolve_evidence_path(workspace, str(item.get("path", "")))
    if path is None or not path.is_file():
        return False
    expected = str(item.get("sha256", "")).strip()
    if expected and hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        return False
    needle = str(item.get("contains", ""))
    if needle:
        try:
            if needle not in path.read_text(encoding="utf-8", errors="replace"):
                return False
        except OSError:
            return False
    return True


def _parse_time(value: str) -> Optional[datetime]:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def assess_satisfaction(
    workspace: Path,
    request: Dict[str, Any],
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    if not isinstance(request, dict):
        raise ValueError("satisfaction request must be an object")
    requirement_id = str(request.get("requirement_id", "")).strip()
    requirement = str(request.get("requirement", "")).strip()
    claim_type = str(request.get("claim_type", "")).strip()
    if not requirement_id or not requirement:
        raise ValueError("requirement_id and requirement are required")
    if claim_type not in CLAIM_REQUIREMENTS:
        raise ValueError("unsupported claim_type")
    alignment = str(request.get("purpose_alignment", "unknown"))
    if alignment not in {"aligned", "conflicts", "unknown"}:
        raise ValueError("purpose_alignment must be aligned, conflicts, or unknown")
    snapshot = workspace_snapshot(workspace)
    evidence_snapshot = request.get("snapshot")
    if evidence_snapshot is None:
        evidence_snapshot = dict(snapshot)
    if not isinstance(evidence_snapshot, dict):
        evidence_snapshot = {}
    snapshot_matches = (
        evidence_snapshot.get("git_head") == snapshot["git_head"]
        and evidence_snapshot.get("worktree_fingerprint")
        == snapshot["worktree_fingerprint"]
    )
    ttl_days = request.get("ttl_days", 30)
    if not isinstance(ttl_days, int) or isinstance(ttl_days, bool) or ttl_days < 0:
        raise ValueError("ttl_days must be a non-negative integer")
    clock = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    observed_value = request.get("observed_at") or clock.isoformat()
    observed_at = _parse_time(str(observed_value))
    fresh = (
        bool(observed_at) and (clock - observed_at).total_seconds() <= ttl_days * 86400
    )

    evidence = request.get("evidence", [])
    if not isinstance(evidence, list):
        raise ValueError("evidence must be an array")
    verified_kinds, attested_kinds, rejected = set(), set(), []
    accepted = []
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            rejected.append({"index": index, "reason": "not_an_object"})
            continue
        kind = str(item.get("kind", "")).strip()
        custody = str(item.get("custody", "")).strip()
        if not kind or custody not in {
            "host_observed",
            "human_observed",
            "external_attested",
        }:
            rejected.append({"index": index, "kind": kind, "reason": "invalid_custody"})
            continue
        attested_kinds.add(kind)
        if kind in {
            "symbol",
            "call_path",
            "test",
            "integration_test",
            "render",
            "accessibility_test",
            "render_small_large_text",
            "two_device_e2e",
            "disconnect_recovery_e2e",
            "functional",
            "operational",
            "security",
            "performance",
            "localization",
        } and not _artifact_verified(workspace, item):
            rejected.append(
                {"index": index, "kind": kind, "reason": "artifact_unverified"}
            )
            continue
        accepted.append(
            {
                "index": index,
                "kind": kind,
                "custody": custody,
                "path": str(item.get("path", "")),
                "sha256": str(item.get("sha256", "")),
                "contains": str(item.get("contains", "")),
                "supports": str(item.get("supports", requirement_id)),
            }
        )
        verified_kinds.add(kind)

    required = CLAIM_REQUIREMENTS[claim_type]
    missing = sorted(required - verified_kinds)
    if alignment == "conflicts":
        evidence_state = "misaligned_implementation"
        disposition = "misaligned_mission"
    elif (not snapshot_matches or not fresh) and required.issubset(attested_kinds):
        evidence_state = "verified_stale"
        disposition = "refresh_evidence"
    elif "symbol" not in verified_kinds and claim_type not in {"fun", "retention"}:
        evidence_state = "not_found"
        disposition = "implementation_needed"
    elif (
        claim_type in {"integration", "multiplayer", "reconnect"}
        and "call_path" not in verified_kinds
        and not required.issubset(verified_kinds)
    ):
        evidence_state = "partially_satisfied"
        disposition = "implementation_or_integration_needed"
    elif missing:
        evidence_state = "implemented_unverified" if verified_kinds else "not_found"
        disposition = "evidence_needed"
    elif not snapshot_matches or not fresh:
        evidence_state = "verified_stale"
        disposition = "refresh_evidence"
    elif alignment != "aligned":
        evidence_state = "verified_current_snapshot"
        disposition = "alignment_review_needed"
    else:
        evidence_state = "verified_current_snapshot"
        disposition = "already_satisfied"

    core = {
        "assessment_version": ASSESSMENT_VERSION,
        "requirement_id": requirement_id,
        "requirement": requirement,
        "claim_type": claim_type,
        "surface_key": str(request.get("surface_key", "")).strip(),
        "purpose_alignment": alignment,
        "evidence_state": evidence_state,
        "disposition": disposition,
        "required_evidence_kinds": sorted(required),
        "verified_evidence_kinds": sorted(verified_kinds),
        "attested_evidence_kinds": sorted(attested_kinds),
        "missing_evidence_kinds": missing,
        "accepted_evidence": accepted,
        "rejected_evidence": rejected,
        "claim_evidence_matrix": [
            {
                "evidence_kind": kind,
                "required": True,
                "verified": kind in verified_kinds,
                "accepted_indices": [
                    row["index"] for row in accepted if row["kind"] == kind
                ],
                "does_not_support": [
                    candidate
                    for candidate in sorted(verified_kinds)
                    if candidate != kind
                ],
            }
            for kind in sorted(required)
        ],
        "current_snapshot": snapshot,
        "evidence_snapshot_matches": snapshot_matches,
        "evidence_fresh": fresh,
        "observed_at": observed_value,
        "ttl_days": ttl_days,
    }
    core["assessment_id"] = f"satisfaction-{_fingerprint(core)[:16]}"
    core["assessed_at"] = _utc_now()
    return core


class SatisfactionStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def save(self, assessment: Dict[str, Any]) -> Path:
        path = self.root / f"{assessment['assessment_id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(assessment, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return path

    def latest(self) -> List[Dict[str, Any]]:
        by_requirement: Dict[str, Dict[str, Any]] = {}
        order_by_requirement: Dict[str, tuple[str, int]] = {}
        if not self.root.is_dir():
            return []
        for path in self.root.glob("satisfaction-*.json"):
            try:
                row = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(row, dict) and isinstance(row.get("requirement_id"), str):
                requirement_id = row["requirement_id"]
                order = (
                    str(row.get("assessed_at") or row.get("observed_at") or ""),
                    path.stat().st_mtime_ns,
                )
                if order >= order_by_requirement.get(requirement_id, ("", -1)):
                    by_requirement[requirement_id] = row
                    order_by_requirement[requirement_id] = order
        return list(by_requirement.values())


def assessment_is_current(workspace: Path, assessment: Dict[str, Any]) -> bool:
    """Revalidate a persisted assessment against the live workspace and TTL."""
    current = workspace_snapshot(workspace)
    recorded = assessment.get("current_snapshot", {})
    if not isinstance(recorded, dict):
        return False
    snapshot_matches = (
        recorded.get("git_head") == current["git_head"]
        and recorded.get("worktree_fingerprint") == current["worktree_fingerprint"]
    )
    observed_at = _parse_time(str(assessment.get("observed_at", "")))
    ttl_days = assessment.get("ttl_days", 30)
    if not isinstance(ttl_days, int) or isinstance(ttl_days, bool) or ttl_days < 0:
        return False
    fresh = (
        bool(observed_at)
        and (datetime.now(timezone.utc) - observed_at).total_seconds()
        <= ttl_days * 86400
    )
    return snapshot_matches and fresh
