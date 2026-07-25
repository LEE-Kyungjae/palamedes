#!/usr/bin/env python3
"""Temporal, scoped, provenance-bearing knowledge for Palamedes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from palamedes_observe import fingerprint, utc_now


KNOWLEDGE_DOMAINS = {"internal_product", "external_world"}
CLAIM_TYPES = {"fact", "interpretation", "norm", "capability", "constraint"}


class KnowledgeStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.claims_root = root / "claims"
        self.unknowns_root = root / "unknowns"
        self.events_path = root / "events.jsonl"

    @staticmethod
    def _save(root: Path, record_id: str, payload: Dict[str, Any]) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{record_id}.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return path

    def save_claim(self, claim: Dict[str, Any]) -> Path:
        return self._save(self.claims_root, claim["knowledge_id"], claim)

    def save_unknown(self, unknown: Dict[str, Any]) -> Path:
        return self._save(self.unknowns_root, unknown["unknown_id"], unknown)

    def append_event(self, event: Dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

    @staticmethod
    def _load(root: Path) -> List[Dict[str, Any]]:
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

    def active_claims(self, limit: int = 40) -> List[Dict[str, Any]]:
        records = [
            item
            for item in self._load(self.claims_root)
            if item.get("status") == "active"
        ]
        records.sort(key=lambda item: item.get("last_verified_at", ""), reverse=True)
        return records[:limit]

    def open_unknowns(self, limit: int = 30) -> List[Dict[str, Any]]:
        records = [
            item
            for item in self._load(self.unknowns_root)
            if item.get("status") == "open"
        ]
        records.sort(key=lambda item: item.get("last_seen_at", ""), reverse=True)
        return records[:limit]


def observation_source_ids(context: Dict[str, Any]) -> set:
    source_ids = {context["observation_id"]}
    source_ids.update(
        f"document:{item['path']}@{item['content_sha256']}"
        for item in context.get("documents", [])
    )
    source_ids.update(
        str(item.get("source_id", "")).strip()
        for item in context.get("declared_surfaces", [])
        if isinstance(item, dict) and str(item.get("source_id", "")).strip()
    )
    source_ids.update(
        f"ref:{item['name']}@{item.get('head', '')}"
        for item in context.get("reference_root", {}).get("repositories", [])
    )
    source_ids.update(
        item["experience_id"]
        for item in context.get("experiences", [])
        if isinstance(item, dict) and item.get("experience_id")
    )
    return source_ids


def _text(payload: Dict[str, Any], field: str) -> str:
    value = str(payload.get(field, "")).strip()
    if not value:
        raise ValueError(f"knowledge {field} must be a non-empty string")
    return value


def _strings(payload: Dict[str, Any], field: str, *, allow_empty: bool) -> List[str]:
    value = payload.get(field)
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ValueError(f"knowledge {field} must be a string array")
    if not allow_empty and not value:
        raise ValueError(f"knowledge {field} must not be empty")
    return [item.strip() for item in value]


def persist_knowledge_updates(
    *,
    store: KnowledgeStore,
    output: Dict[str, Any],
    context: Dict[str, Any],
) -> Dict[str, Any]:
    from palamedes_epistemics import (
        EpistemicStore,
        persist_observation_epistemics,
        validate_epistemic_profile,
    )

    epistemics = persist_observation_epistemics(
        store=EpistemicStore(store.root.parent / "epistemics"),
        context=context,
    )
    candidates = output.get("knowledge_claims", [])
    unknown_candidates = output.get("unknown_boundaries", [])
    if not isinstance(candidates, list):
        raise ValueError("knowledge_claims must be an array")
    if not isinstance(unknown_candidates, list):
        raise ValueError("unknown_boundaries must be an array")
    change_reasons = set(context.get("change", {}).get("reasons", []))
    if change_reasons.intersection(
        {
            "git_head_changed",
            "git_status_changed",
            "document_set_or_content_changed",
        }
    ) and not unknown_candidates:
        raise ValueError(
            "product or document change requires an explicit unknown boundary"
        )
    allowed_sources = observation_source_ids(context)
    existing = {item["knowledge_id"]: item for item in store.active_claims(1000)}
    persisted_claims = []
    now = utc_now()
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("each knowledge claim must be an object")
        domain = candidate.get("domain")
        claim_type = candidate.get("claim_type")
        if domain not in KNOWLEDGE_DOMAINS or claim_type not in CLAIM_TYPES:
            raise ValueError("knowledge claim has invalid domain or claim_type")
        sources = _strings(candidate, "source_ids", allow_empty=False)
        if not set(sources).issubset(allowed_sources):
            raise ValueError("knowledge claim cites an unavailable source")
        confidence = candidate.get("confidence")
        if (
            not isinstance(confidence, int)
            or isinstance(confidence, bool)
            or not 0 <= confidence <= 100
        ):
            raise ValueError("knowledge confidence must be 0-100")
        epistemic_profile = validate_epistemic_profile(
            candidate.get("epistemic_profile"),
            source_ids=sources,
            surface_by_source=epistemics["surface_by_source"],
        )
        normalized = {
            "domain": domain,
            "claim_type": claim_type,
            "claim": _text(candidate, "claim"),
            "scope": _text(candidate, "scope"),
            "perspective": _text(candidate, "perspective"),
        }
        knowledge_id = f"knowledge-{fingerprint(normalized)[:12]}"
        previous = existing.get(knowledge_id)
        normative_assumptions = _strings(
            candidate, "normative_assumptions", allow_empty=True
        )
        if claim_type == "norm" and not normative_assumptions:
            raise ValueError("norm claims require explicit normative_assumptions")
        claim = {
            "knowledge_version": "palamedes-temporal-knowledge/1",
            "knowledge_id": knowledge_id,
            **normalized,
            "source_ids": sources,
            "confidence": confidence,
            "epistemic_profile": epistemic_profile,
            "valid_from": str(candidate.get("valid_from", context["observed_at"])).strip(),
            "valid_to": "",
            "last_verified_at": context["observed_at"],
            "affected_stakeholders": _strings(
                candidate, "affected_stakeholders", allow_empty=False
            ),
            "normative_assumptions": normative_assumptions,
            "known_exclusions": _strings(
                candidate, "known_exclusions", allow_empty=True
            ),
            "supersedes": _strings(candidate, "supersedes", allow_empty=True),
            "status": "active",
            "created_at": previous.get("created_at", now) if previous else now,
        }
        for superseded_id in claim["supersedes"]:
            superseded = next(
                (
                    item
                    for item in store.active_claims(1000)
                    if item["knowledge_id"] == superseded_id
                ),
                None,
            )
            if superseded is None:
                raise ValueError("knowledge claim supersedes an unavailable claim")
            superseded["status"] = "superseded"
            superseded["valid_to"] = claim["valid_from"]
            superseded["superseded_by"] = knowledge_id
            store.save_claim(superseded)
        store.save_claim(claim)
        store.append_event(
            {
                "ts": now,
                "type": "knowledge_verified" if previous else "knowledge_created",
                "knowledge_id": knowledge_id,
                "observation_id": context["observation_id"],
            }
        )
        persisted_claims.append(claim)

    persisted_unknowns = []
    existing_unknowns = {
        item["unknown_id"]: item for item in store.open_unknowns(1000)
    }
    for candidate in unknown_candidates:
        if not isinstance(candidate, dict):
            raise ValueError("each unknown boundary must be an object")
        unknown = {
            "unknown_version": "palamedes-knowledge-unknown/1",
            "subject": _text(candidate, "subject"),
            "missing_knowledge": _text(candidate, "missing_knowledge"),
            "decision_consequence": _text(candidate, "decision_consequence"),
            "needed_source": _text(candidate, "needed_source"),
            "wake_condition": _text(candidate, "wake_condition"),
            "source_observation_id": context["observation_id"],
            "status": "open",
            "first_seen_at": now,
            "last_seen_at": now,
        }
        identity = {
            "subject": unknown["subject"].casefold(),
            "missing": unknown["missing_knowledge"].casefold(),
        }
        unknown["unknown_id"] = f"unknown-{fingerprint(identity)[:12]}"
        previous_unknown = existing_unknowns.get(unknown["unknown_id"])
        if previous_unknown:
            unknown["first_seen_at"] = previous_unknown["first_seen_at"]
        store.save_unknown(unknown)
        store.append_event(
            {
                "ts": now,
                "type": "unknown_boundary_recorded",
                "unknown_id": unknown["unknown_id"],
                "observation_id": context["observation_id"],
            }
        )
        persisted_unknowns.append(unknown)
    return {
        "claims": persisted_claims,
        "unknowns": persisted_unknowns,
        "surfaces": epistemics["surfaces"],
        "coverage": epistemics["coverage"],
    }
