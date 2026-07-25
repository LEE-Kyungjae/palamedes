#!/usr/bin/env python3
"""Persistent pre-mission thought incubation and discovery lineage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from palamedes_observe import fingerprint, observation_context, utc_now


THOUGHT_KINDS = {
    "question",
    "anomaly",
    "possibility",
    "tension",
    "risk",
    "analogy",
    "future_event",
}


class ThoughtStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.thoughts_root = root / "thoughts"
        self.discoveries_root = root / "discoveries"
        self.experiences_root = root / "experiences"
        self.events_path = root / "events.jsonl"

    def _save(self, root: Path, record_id: str, payload: Dict[str, Any]) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{record_id}.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return path

    def save_thought(self, thought: Dict[str, Any]) -> Path:
        return self._save(self.thoughts_root, thought["thought_id"], thought)

    def save_discovery(self, discovery: Dict[str, Any]) -> Path:
        return self._save(
            self.discoveries_root, discovery["discovery_id"], discovery
        )

    def save_experience(self, experience: Dict[str, Any]) -> Path:
        return self._save(
            self.experiences_root, experience["experience_id"], experience
        )

    def append_event(self, event: Dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

    @staticmethod
    def _load_records(root: Path) -> List[Dict[str, Any]]:
        records = []
        if not root.is_dir():
            return records
        for path in sorted(root.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict):
                records.append(payload)
        return records

    def active_thoughts(self, limit: int = 24) -> List[Dict[str, Any]]:
        records = [
            item
            for item in self._load_records(self.thoughts_root)
            if item.get("status") in {"incubating", "reinforced"}
        ]
        records.sort(
            key=lambda item: (
                float(item.get("strength", 0)),
                item.get("last_revisited_at", ""),
            ),
            reverse=True,
        )
        return records[:limit]

    def active_discoveries(self, limit: int = 12) -> List[Dict[str, Any]]:
        records = [
            item
            for item in self._load_records(self.discoveries_root)
            if item.get("status") == "candidate"
        ]
        records.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return records[:limit]

    def decay_unrevisited(
        self, revisited_thought_ids: set, amount: float = 0.05
    ) -> List[Dict[str, Any]]:
        changed = []
        now = utc_now()
        for thought in self.active_thoughts(1000):
            if thought["thought_id"] in revisited_thought_ids:
                continue
            strength = max(0.0, float(thought.get("strength", 0)) - amount)
            thought["strength"] = round(strength, 4)
            thought["status"] = "archived" if strength < 0.1 else "incubating"
            thought["last_decay_at"] = now
            self.save_thought(thought)
            self.append_event(
                {
                    "ts": now,
                    "type": (
                        "thought_archived"
                        if thought["status"] == "archived"
                        else "thought_decayed"
                    ),
                    "thought_id": thought["thought_id"],
                    "strength": thought["strength"],
                }
            )
            changed.append(thought)
        return changed

    def recent_experiences(self, limit: int = 12) -> List[Dict[str, Any]]:
        records = self._load_records(self.experiences_root)
        records.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return records[:limit]


def persist_mission_experience(
    *,
    store: ThoughtStore,
    contract: Dict[str, Any],
    outcome: Dict[str, Any],
    analysis: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    output = analysis.get("output", {}) if analysis else {}
    identity = {
        "mission_contract_id": contract["mission_id"],
        "outcome_id": outcome["outcome_id"],
    }
    experience = {
        "experience_version": "palamedes-mission-experience/1",
        "experience_id": f"experience-{fingerprint(identity)[:12]}",
        "mission_contract_id": contract["mission_id"],
        "outcome_id": outcome["outcome_id"],
        "decision": contract["mission"],
        "reason_at_decision_time": contract["rationale"],
        "expected_result": contract["success_metric"],
        "observed_result": outcome["observation"],
        "outcome_status": outcome["status"],
        "evidence_source_type": outcome.get(
            "evidence_source_type", "implementer_claim"
        ),
        "prediction_gap": str(
            output.get("observed_vs_expected", "not yet analyzed")
        ).strip(),
        "mission_disposition": output.get(
            "mission_disposition", "insufficient_evidence"
        ),
        "belief_updates": list(output.get("belief_updates", [])),
        "next_probe": str(
            output.get("next_probe", contract["next_probe"]["step"])
        ).strip(),
        "source_discovery_ids": list(contract.get("source_discovery_ids", [])),
        "created_at": utc_now(),
    }
    store.save_experience(experience)
    store.append_event(
        {
            "ts": experience["created_at"],
            "type": "mission_experience_created",
            "experience_id": experience["experience_id"],
            "mission_contract_id": contract["mission_id"],
            "outcome_id": outcome["outcome_id"],
        }
    )
    return experience


def _required_text(payload: Dict[str, Any], field: str) -> str:
    value = str(payload.get(field, "")).strip()
    if not value:
        raise ValueError(f"{field} must be a non-empty string")
    return value


def persist_thoughts(
    *,
    store: ThoughtStore,
    output: Dict[str, Any],
    observation_id: str,
) -> List[Dict[str, Any]]:
    candidates = output.get("thoughts")
    if not isinstance(candidates, list) or len(candidates) < 2:
        raise ValueError("noticer requires at least two thoughts")
    persisted = []
    existing = {item["thought_id"]: item for item in store.active_thoughts(1000)}
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("each thought must be an object")
        kind = candidate.get("kind")
        if kind not in THOUGHT_KINDS:
            raise ValueError(f"invalid thought kind: {kind}")
        content = _required_text(candidate, "content")
        residue = _required_text(candidate, "unexplained_residue")
        why_unresolved = _required_text(candidate, "why_unresolved")
        wake_conditions = candidate.get("wake_conditions")
        if not isinstance(wake_conditions, list) or not all(
            isinstance(item, str) and item.strip() for item in wake_conditions
        ):
            raise ValueError("thought wake_conditions must be a string array")
        identity = {
            "kind": kind,
            "content": content.casefold(),
            "unexplained_residue": residue.casefold(),
        }
        thought_id = f"thought-{fingerprint(identity)[:12]}"
        previous = existing.get(thought_id)
        now = utc_now()
        evidence_ids = list(previous.get("source_observation_ids", [])) if previous else []
        if observation_id not in evidence_ids:
            evidence_ids.append(observation_id)
        reinforcement_count = int(previous.get("reinforcement_count", 0)) + 1 if previous else 1
        thought = {
            "thought_version": "palamedes-thought/1",
            "thought_id": thought_id,
            "kind": kind,
            "content": content,
            "unexplained_residue": residue,
            "why_unresolved": why_unresolved,
            "source_observation_ids": evidence_ids,
            "wake_conditions": [item.strip() for item in wake_conditions],
            "strength": min(1.0, 0.2 + 0.12 * reinforcement_count),
            "reinforcement_count": reinforcement_count,
            "status": "reinforced" if previous else "incubating",
            "created_at": previous.get("created_at", now) if previous else now,
            "last_revisited_at": now,
            "mission_authority_granted": False,
        }
        store.save_thought(thought)
        store.append_event(
            {
                "ts": now,
                "type": "thought_reinforced" if previous else "thought_created",
                "thought_id": thought_id,
                "observation_id": observation_id,
            }
        )
        persisted.append(thought)
    return persisted


def persist_discoveries(
    *,
    store: ThoughtStore,
    output: Dict[str, Any],
    available_thought_ids: set,
) -> List[Dict[str, Any]]:
    candidates = output.get("discoveries")
    if not isinstance(candidates, list):
        raise ValueError("connector discoveries must be an array")
    persisted = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("each discovery must be an object")
        thought_ids = candidate.get("connected_thought_ids")
        if (
            not isinstance(thought_ids, list)
            or len(set(thought_ids)) < 2
            or not set(thought_ids).issubset(available_thought_ids)
        ):
            raise ValueError(
                "discovery must connect at least two available thought IDs"
            )
        thesis = _required_text(candidate, "thesis")
        discovery = {
            "discovery_version": "palamedes-discovery/1",
            "connected_thought_ids": sorted(set(thought_ids)),
            "thesis": thesis,
            "old_framing": _required_text(candidate, "old_framing"),
            "new_framing": _required_text(candidate, "new_framing"),
            "assumption_replaced": _required_text(candidate, "assumption_replaced"),
            "changed_decision": _required_text(candidate, "changed_decision"),
            "smallest_probe": _required_text(candidate, "smallest_probe"),
            "disconfirmation": _required_text(candidate, "disconfirmation"),
            "why_non_obvious": _required_text(candidate, "why_non_obvious"),
            "status": "candidate",
            "created_at": utc_now(),
            "mission_authority_granted": False,
        }
        identity = {
            "thought_ids": discovery["connected_thought_ids"],
            "thesis": thesis.casefold(),
        }
        discovery["discovery_id"] = f"discovery-{fingerprint(identity)[:12]}"
        store.save_discovery(discovery)
        store.append_event(
            {
                "ts": discovery["created_at"],
                "type": "discovery_created",
                "discovery_id": discovery["discovery_id"],
                "thought_ids": discovery["connected_thought_ids"],
            }
        )
        persisted.append(discovery)
    return persisted


def run_discovery_incubation(
    *,
    provider: Any,
    snapshot: Dict[str, Any],
    store: ThoughtStore,
) -> Dict[str, Any]:
    from palamedes_chat import _provider_json, _role_artifact

    existing = store.active_thoughts()
    experiences = store.recent_experiences()
    noticer_prompt = f"""ROLE: noticer
Do not propose features, tasks, or missions. Extract at least two unresolved
residues from the observation: anomalies, tensions, questions, possibilities,
risks, analogies, or future events that the current product explanation does
not fully absorb. Preserve uncertainty rather than converting it into advice.
Return exactly:
{{
  "thoughts": [{{
    "kind":"question|anomaly|possibility|tension|risk|analogy|future_event",
    "content":"...",
    "unexplained_residue":"what remains unexplained",
    "why_unresolved":"...",
    "wake_conditions":["specific evidence that should reactivate this thought"]
  }}]
}}

Workspace observation:
{json.dumps(observation_context(snapshot), ensure_ascii=False)}
Existing thoughts:
{json.dumps(existing, ensure_ascii=False)}
Recent decision-to-outcome experiences:
{json.dumps(experiences, ensure_ascii=False)}"""
    noticer = _provider_json(
        provider,
        system=(
            "You are Palamedes' bounded noticer. Keep pre-mission thoughts alive "
            "without issuing work. Return one JSON object."
        ),
        prompt=noticer_prompt,
    )
    thoughts = persist_thoughts(
        store=store,
        output=noticer,
        observation_id=snapshot["observation_id"],
    )
    decayed = store.decay_unrevisited({item["thought_id"] for item in thoughts})
    available = {item["thought_id"]: item for item in store.active_thoughts()}
    connector_prompt = f"""ROLE: connector
Look for a non-obvious relationship between thoughts from different signals,
times, or conceptual domains. Similarity alone is not discovery. A valid
connection must replace an assumption, reframe what the product may be, and
change a possible decision. Do not issue a mission or authorize implementation.
It is valid to return no discoveries.
Return exactly:
{{
  "discoveries": [{{
    "connected_thought_ids":["thought-...","thought-..."],
    "thesis":"...",
    "old_framing":"...",
    "new_framing":"...",
    "assumption_replaced":"...",
    "changed_decision":"...",
    "smallest_probe":"...",
    "disconfirmation":"...",
    "why_non_obvious":"..."
  }}]
}}

Available thoughts:
{json.dumps(list(available.values()), ensure_ascii=False)}"""
    connector = _provider_json(
        provider,
        system=(
            "You are Palamedes' bounded connector. Discover relationships but "
            "grant no mission or delivery authority. Return one JSON object."
        ),
        prompt=connector_prompt,
    )
    discoveries = persist_discoveries(
        store=store,
        output=connector,
        available_thought_ids=set(available),
    )
    artifacts = [
        _role_artifact(
            role="noticer",
            call_index=1,
            prompt=noticer_prompt,
            output=noticer,
            provider=provider,
        ),
        _role_artifact(
            role="connector",
            call_index=2,
            prompt=connector_prompt,
            output=connector,
            provider=provider,
        ),
    ]
    return {
        "status": "completed",
        "artifacts": artifacts,
        "model_call_count": 2,
        "thought_ids": [item["thought_id"] for item in thoughts],
        "decayed_thought_ids": [item["thought_id"] for item in decayed],
        "discovery_ids": [item["discovery_id"] for item in discoveries],
        "mission_draft_issued": False,
    }
