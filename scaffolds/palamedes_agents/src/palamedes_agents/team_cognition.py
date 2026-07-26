#!/usr/bin/env python3
"""Shared epistemic state for many agents without making Palamedes their manager."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import tempfile
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional


SCHEMA_VERSION = "palamedes-team-cognition/v1"
OBSERVATION_KINDS = {"fact", "inference", "preference", "simulation", "commitment"}
HYPOTHESIS_STATUSES = {"open", "supported", "weakened", "rejected"}
MISSION_STATUSES = {"claimed", "released", "completed"}


class TeamCognitionConflict(RuntimeError):
    """Raised when an agent attempts a stale or conflicting team-state write."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _required_text(payload: Dict[str, Any], key: str) -> str:
    value = str(payload.get(key, "")).strip()
    if not value:
        raise ValueError(f"{key} is required")
    return value


class TeamCognitionStore:
    """Atomic, provenance-preserving ledger shared by a host's agent team."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")

    @staticmethod
    def empty_state() -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "world_version": 0,
            "observations": [],
            "hypotheses": [],
            "missions": [],
            "outcomes": [],
            "exploration_rounds": [],
        }

    @contextmanager
    def _locked(self) -> Iterator[None]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.lock_path.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _load_unlocked(self) -> Dict[str, Any]:
        if not self.path.exists():
            return self.empty_state()
        state = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(state, dict) or state.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("unsupported team cognition state")
        return state

    def _write_unlocked(self, state: Dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(
            prefix=self.path.name + ".",
            suffix=".tmp",
            dir=str(self.path.parent),
        )
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(state, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def snapshot(self) -> Dict[str, Any]:
        with self._locked():
            return json.loads(json.dumps(self._load_unlocked()))

    def context_snapshot(
        self,
        observation_limit: int = 20,
        hypothesis_limit: int = 20,
        mission_limit: int = 20,
        outcome_limit: int = 10,
        round_limit: int = 5,
    ) -> Dict[str, Any]:
        limits = [
            observation_limit,
            hypothesis_limit,
            mission_limit,
            outcome_limit,
            round_limit,
        ]
        if any(limit < 0 for limit in limits):
            raise ValueError("team context limits must be non-negative")
        state = self.snapshot()

        def tail(items: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
            return items[-limit:] if limit else []

        open_hypotheses = [
            item for item in state["hypotheses"] if item.get("status") in {"open", "supported", "weakened"}
        ]
        active_missions = [
            item for item in state["missions"] if item.get("status") == "claimed"
        ]
        visible_rounds = [
            item for item in state["exploration_rounds"] if item.get("phase") == "ready"
        ]
        return {
            "schema_version": state["schema_version"],
            "world_version": state["world_version"],
            "counts": {
                "observations": len(state["observations"]),
                "hypotheses": len(state["hypotheses"]),
                "active_missions": len(active_missions),
                "outcomes": len(state["outcomes"]),
                "exploration_rounds": len(state["exploration_rounds"]),
                "ready_exploration_rounds": len(visible_rounds),
            },
            "recent_observations": tail(state["observations"], observation_limit),
            "open_hypotheses": tail(open_hypotheses, hypothesis_limit),
            "active_missions": tail(active_missions, mission_limit),
            "recent_outcomes": tail(state["outcomes"], outcome_limit),
            "ready_exploration_rounds": tail(visible_rounds, round_limit),
        }

    @staticmethod
    def candidate_commitment(candidate: Dict[str, Any], nonce: str) -> str:
        if not isinstance(candidate, dict) or not candidate:
            raise ValueError("candidate must be a non-empty object")
        nonce = str(nonce).strip()
        if not nonce:
            raise ValueError("nonce is required")
        canonical = json.dumps(
            candidate,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(f"{canonical}\n{nonce}".encode("utf-8")).hexdigest()

    def _mutate(
        self,
        expected_world_version: Optional[int],
        mutation: Any,
    ) -> Dict[str, Any]:
        with self._locked():
            state = self._load_unlocked()
            current = int(state["world_version"])
            if expected_world_version is not None and expected_world_version != current:
                raise TeamCognitionConflict(
                    f"stale world version: expected {expected_world_version}, current {current}"
                )
            result = mutation(state)
            state["world_version"] = current + 1
            self._write_unlocked(state)
            return {
                "record": result,
                "world_version": state["world_version"],
                "schema_version": SCHEMA_VERSION,
            }

    def record_observation(
        self,
        payload: Dict[str, Any],
        expected_world_version: Optional[int] = None,
    ) -> Dict[str, Any]:
        kind = str(payload.get("kind", "fact")).strip()
        if kind not in OBSERVATION_KINDS:
            raise ValueError(f"invalid observation kind: {kind}")
        coverage = payload.get("coverage", {}) or {}
        if not isinstance(coverage, dict):
            raise ValueError("coverage must be an object")
        record = {
            "observation_id": str(payload.get("observation_id", "")).strip() or f"obs-{uuid.uuid4().hex[:12]}",
            "agent_id": _required_text(payload, "agent_id"),
            "agent_role": _required_text(payload, "agent_role"),
            "kind": kind,
            "content": _required_text(payload, "content"),
            "source": _required_text(payload, "source"),
            "observation_surface": _required_text(payload, "observation_surface"),
            "observed_at": str(payload.get("observed_at", "")).strip() or _now(),
            "commit_sha": str(payload.get("commit_sha", "")).strip(),
            "confidence": int(payload.get("confidence", 50)),
            "coverage": {
                "observed_population": str(coverage.get("observed_population", "")).strip(),
                "missing_perspectives": list(coverage.get("missing_perspectives", []) or []),
                "selection_bias": str(coverage.get("selection_bias", "")).strip(),
            },
        }
        if not 0 <= record["confidence"] <= 100:
            raise ValueError("confidence must be between 0 and 100")

        def append(state: Dict[str, Any]) -> Dict[str, Any]:
            if any(item["observation_id"] == record["observation_id"] for item in state["observations"]):
                raise TeamCognitionConflict(f"duplicate observation_id: {record['observation_id']}")
            state["observations"].append(record)
            return record

        return self._mutate(expected_world_version, append)

    def begin_exploration(
        self,
        payload: Dict[str, Any],
        expected_world_version: Optional[int] = None,
    ) -> Dict[str, Any]:
        participant_ids = [str(item).strip() for item in payload.get("participant_ids", [])]
        if len(participant_ids) < 2 or len(set(participant_ids)) != len(participant_ids):
            raise ValueError("participant_ids must contain at least two distinct agents")
        if any(not item for item in participant_ids):
            raise ValueError("participant_ids cannot contain empty values")
        record = {
            "round_id": _required_text(payload, "round_id"),
            "question": _required_text(payload, "question"),
            "participant_ids": participant_ids,
            "evidence_boundary": list(payload.get("evidence_boundary", []) or []),
            "phase": "commit",
            "commitments": [],
            "reveals": [],
            "created_at": _now(),
        }

        def append(state: Dict[str, Any]) -> Dict[str, Any]:
            if any(item["round_id"] == record["round_id"] for item in state["exploration_rounds"]):
                raise TeamCognitionConflict(f"duplicate round_id: {record['round_id']}")
            state["exploration_rounds"].append(record)
            return record

        return self._mutate(expected_world_version, append)

    def commit_candidate(
        self,
        round_id: str,
        agent_id: str,
        commitment: str,
        expected_world_version: Optional[int] = None,
    ) -> Dict[str, Any]:
        round_id = str(round_id).strip()
        agent_id = str(agent_id).strip()
        commitment = str(commitment).strip().lower()
        if not round_id or not agent_id:
            raise ValueError("round_id and agent_id are required")
        if len(commitment) != 64 or any(character not in "0123456789abcdef" for character in commitment):
            raise ValueError("commitment must be a SHA-256 hex digest")

        def commit(state: Dict[str, Any]) -> Dict[str, Any]:
            round_record = next(
                (item for item in state["exploration_rounds"] if item["round_id"] == round_id),
                None,
            )
            if round_record is None:
                raise ValueError(f"unknown round_id: {round_id}")
            if round_record["phase"] != "commit":
                raise TeamCognitionConflict(f"round {round_id} is not accepting commitments")
            if agent_id not in round_record["participant_ids"]:
                raise ValueError(f"agent {agent_id} is not a round participant")
            if any(item["agent_id"] == agent_id for item in round_record["commitments"]):
                raise TeamCognitionConflict(f"agent {agent_id} already committed")
            item = {"agent_id": agent_id, "commitment": commitment, "committed_at": _now()}
            round_record["commitments"].append(item)
            if len(round_record["commitments"]) == len(round_record["participant_ids"]):
                round_record["phase"] = "reveal"
            return item

        return self._mutate(expected_world_version, commit)

    def reveal_candidate(
        self,
        round_id: str,
        agent_id: str,
        candidate: Dict[str, Any],
        nonce: str,
        expected_world_version: Optional[int] = None,
    ) -> Dict[str, Any]:
        round_id = str(round_id).strip()
        agent_id = str(agent_id).strip()
        if not round_id or not agent_id:
            raise ValueError("round_id and agent_id are required")
        calculated = self.candidate_commitment(candidate, nonce)

        def reveal(state: Dict[str, Any]) -> Dict[str, Any]:
            round_record = next(
                (item for item in state["exploration_rounds"] if item["round_id"] == round_id),
                None,
            )
            if round_record is None:
                raise ValueError(f"unknown round_id: {round_id}")
            if round_record["phase"] != "reveal":
                raise TeamCognitionConflict(f"round {round_id} is not accepting reveals")
            committed = next(
                (item for item in round_record["commitments"] if item["agent_id"] == agent_id),
                None,
            )
            if committed is None:
                raise ValueError(f"agent {agent_id} has no commitment")
            if committed["commitment"] != calculated:
                raise TeamCognitionConflict("candidate reveal does not match commitment")
            if any(item["agent_id"] == agent_id for item in round_record["reveals"]):
                raise TeamCognitionConflict(f"agent {agent_id} already revealed")
            item = {
                "agent_id": agent_id,
                "candidate": candidate,
                "commitment": calculated,
                "revealed_at": _now(),
            }
            round_record["reveals"].append(item)
            if len(round_record["reveals"]) == len(round_record["participant_ids"]):
                round_record["phase"] = "ready"
            return item

        return self._mutate(expected_world_version, reveal)

    def propose_hypothesis(
        self,
        payload: Dict[str, Any],
        expected_world_version: Optional[int] = None,
    ) -> Dict[str, Any]:
        evidence_ids = list(payload.get("evidence_ids", []) or [])
        conflicts_with = list(payload.get("conflicts_with", []) or [])
        record = {
            "hypothesis_id": str(payload.get("hypothesis_id", "")).strip() or f"hyp-{uuid.uuid4().hex[:12]}",
            "agent_id": _required_text(payload, "agent_id"),
            "statement": _required_text(payload, "statement"),
            "mechanism": _required_text(payload, "mechanism"),
            "prediction": _required_text(payload, "prediction"),
            "falsifier": _required_text(payload, "falsifier"),
            "evidence_ids": evidence_ids,
            "conflicts_with": conflicts_with,
            "status": "open",
            "created_at": _now(),
        }

        def append(state: Dict[str, Any]) -> Dict[str, Any]:
            known_evidence = {item["observation_id"] for item in state["observations"]}
            missing_evidence = sorted(set(evidence_ids) - known_evidence)
            if missing_evidence:
                raise ValueError(f"unknown evidence_ids: {', '.join(missing_evidence)}")
            known_hypotheses = {item["hypothesis_id"] for item in state["hypotheses"]}
            missing_conflicts = sorted(set(conflicts_with) - known_hypotheses)
            if missing_conflicts:
                raise ValueError(f"unknown conflicts_with: {', '.join(missing_conflicts)}")
            if any(item["hypothesis_id"] == record["hypothesis_id"] for item in state["hypotheses"]):
                raise TeamCognitionConflict(f"duplicate hypothesis_id: {record['hypothesis_id']}")
            state["hypotheses"].append(record)
            return record

        return self._mutate(expected_world_version, append)

    def update_hypothesis(
        self,
        hypothesis_id: str,
        status: str,
        agent_id: str,
        reason: str,
        expected_world_version: Optional[int] = None,
    ) -> Dict[str, Any]:
        if status not in HYPOTHESIS_STATUSES:
            raise ValueError(f"invalid hypothesis status: {status}")
        agent_id = str(agent_id).strip()
        reason = str(reason).strip()
        if not agent_id:
            raise ValueError("agent_id is required")
        if not reason:
            raise ValueError("reason is required")

        def update(state: Dict[str, Any]) -> Dict[str, Any]:
            for item in state["hypotheses"]:
                if item["hypothesis_id"] == hypothesis_id:
                    item["status"] = status
                    item.setdefault("revisions", []).append(
                        {"agent_id": agent_id, "reason": reason, "status": status, "recorded_at": _now()}
                    )
                    return item
            raise ValueError(f"unknown hypothesis_id: {hypothesis_id}")

        return self._mutate(expected_world_version, update)

    def claim_mission(
        self,
        mission_id: str,
        agent_id: str,
        basis_hypothesis_ids: Optional[List[str]] = None,
        expected_world_version: Optional[int] = None,
    ) -> Dict[str, Any]:
        mission_id = str(mission_id).strip()
        agent_id = str(agent_id).strip()
        if not mission_id:
            raise ValueError("mission_id is required")
        if not agent_id:
            raise ValueError("agent_id is required")
        basis = list(basis_hypothesis_ids or [])
        with self._locked():
            state = self._load_unlocked()
            current = int(state["world_version"])
            if expected_world_version is not None and expected_world_version != current:
                raise TeamCognitionConflict(
                    f"stale world version: expected {expected_world_version}, current {current}"
                )
            known = {item["hypothesis_id"] for item in state["hypotheses"]}
            missing = sorted(set(basis) - known)
            if missing:
                raise ValueError(f"unknown basis_hypothesis_ids: {', '.join(missing)}")
            for item in state["missions"]:
                if item["mission_id"] == mission_id and item["status"] == "claimed":
                    if item["agent_id"] == agent_id:
                        return {
                            "record": item,
                            "world_version": current,
                            "schema_version": SCHEMA_VERSION,
                        }
                    raise TeamCognitionConflict(
                        f"mission {mission_id} is already claimed by {item['agent_id']}"
                    )
            record = {
                "mission_id": mission_id,
                "agent_id": agent_id,
                "basis_hypothesis_ids": basis,
                "status": "claimed",
                "claimed_at": _now(),
            }
            state["missions"].append(record)
            state["world_version"] = current + 1
            self._write_unlocked(state)
            return {
                "record": record,
                "world_version": state["world_version"],
                "schema_version": SCHEMA_VERSION,
            }

    def release_mission(
        self,
        mission_id: str,
        agent_id: str,
        status: str = "released",
        expected_world_version: Optional[int] = None,
    ) -> Dict[str, Any]:
        if status not in MISSION_STATUSES - {"claimed"}:
            raise ValueError(f"invalid release status: {status}")
        mission_id = str(mission_id).strip()
        agent_id = str(agent_id).strip()
        if not mission_id:
            raise ValueError("mission_id is required")
        if not agent_id:
            raise ValueError("agent_id is required")

        def release(state: Dict[str, Any]) -> Dict[str, Any]:
            for item in reversed(state["missions"]):
                if item["mission_id"] == mission_id and item["status"] == "claimed":
                    if item["agent_id"] != agent_id:
                        raise TeamCognitionConflict(
                            f"mission {mission_id} is owned by {item['agent_id']}, not {agent_id}"
                        )
                    item["status"] = status
                    item["closed_at"] = _now()
                    return item
            raise ValueError(f"no active claim for mission: {mission_id}")

        return self._mutate(expected_world_version, release)

    def record_outcome(
        self,
        payload: Dict[str, Any],
        expected_world_version: Optional[int] = None,
    ) -> Dict[str, Any]:
        attribution = payload.get("attribution", []) or []
        if not isinstance(attribution, list) or not attribution:
            raise ValueError("attribution must be a non-empty array")
        shares = 0
        normalized = []
        for item in attribution:
            if not isinstance(item, dict):
                raise ValueError("each attribution item must be an object")
            share = int(item.get("share", 0))
            if not 0 <= share <= 100:
                raise ValueError("each attribution share must be between 0 and 100")
            shares += share
            normalized.append(
                {
                    "agent_id": _required_text(item, "agent_id"),
                    "contribution": _required_text(item, "contribution"),
                    "share": share,
                }
            )
        if shares != 100:
            raise ValueError("attribution shares must total 100")
        record = {
            "outcome_id": str(payload.get("outcome_id", "")).strip() or f"out-{uuid.uuid4().hex[:12]}",
            "mission_id": _required_text(payload, "mission_id"),
            "result": _required_text(payload, "result"),
            "evidence": list(payload.get("evidence", []) or []),
            "attribution": normalized,
            "recorded_at": _now(),
        }

        def append(state: Dict[str, Any]) -> Dict[str, Any]:
            if any(item["outcome_id"] == record["outcome_id"] for item in state["outcomes"]):
                raise TeamCognitionConflict(f"duplicate outcome_id: {record['outcome_id']}")
            if not any(item["mission_id"] == record["mission_id"] for item in state["missions"]):
                raise ValueError(f"unknown mission_id: {record['mission_id']}")
            state["outcomes"].append(record)
            return record

        return self._mutate(expected_world_version, append)
