#!/usr/bin/env python3
"""Source-bounded self/reference comparison for autonomous research agendas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from palamedes_observe import fingerprint, observation_context, utc_now


class ReferenceIntelligenceStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.runs_root = root / "runs"
        self.events_path = root / "events.jsonl"

    def save(self, record: Dict[str, Any]) -> Path:
        self.runs_root.mkdir(parents=True, exist_ok=True)
        path = self.runs_root / f"{record['reference_intelligence_id']}.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        self.root.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "ts": record["created_at"],
                        "type": "reference_intelligence_created",
                        "reference_intelligence_id": record[
                            "reference_intelligence_id"
                        ],
                        "reference_mode": record["reference_mode"],
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n"
            )
        return path

    def active_agendas(self, limit: int = 3) -> List[Dict[str, Any]]:
        if not self.runs_root.is_dir():
            return []
        records: List[Dict[str, Any]] = []
        for path in self.runs_root.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            agenda = payload.get("selected_agenda") if isinstance(payload, dict) else None
            if isinstance(agenda, dict) and agenda.get("status") == "selected":
                records.append(
                    {
                        "reference_intelligence_id": payload[
                            "reference_intelligence_id"
                        ],
                        **agenda,
                    }
                )
        records.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return records[:limit]

    def has_runs(self) -> bool:
        return self.runs_root.is_dir() and any(self.runs_root.glob("*.json"))


def _extract_json_object(raw: str) -> Dict[str, Any]:
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end < start:
        raise ValueError("reference intelligence provider returned no JSON object")
    payload = json.loads(raw[start : end + 1])
    if not isinstance(payload, dict):
        raise ValueError("reference intelligence output must be an object")
    return payload


def _source_catalog(snapshot: Dict[str, Any]) -> List[Dict[str, Any]]:
    context = observation_context(snapshot)
    sources: List[Dict[str, Any]] = []
    for index, document in enumerate(context.get("documents", [])):
        sources.append(
            {
                "source_id": f"workspace-document-{index + 1}",
                "source_class": "internal_product",
                "path": document["path"],
                "observed_at": context["observed_at"],
                "content_sha256": document["content_sha256"],
                "excerpt": document.get("excerpt", "")[:6000],
            }
        )
    reference = context.get("reference_root", {})
    for item in reference.get("repositories", []):
        knowledge = item.get("knowledge_document")
        if not isinstance(knowledge, dict) or not knowledge.get("excerpt"):
            continue
        sources.append(
            {
                "source_id": f"external-reference-{len([s for s in sources if s['source_class'] == 'external_reference']) + 1}",
                "source_class": "external_reference",
                "name": item.get("name", "unnamed"),
                "path": item.get("resolved_path", item.get("path", "")),
                "observed_at": context["observed_at"],
                "revision": item.get("head", ""),
                "content_sha256": knowledge.get("content_sha256", ""),
                "excerpt": knowledge["excerpt"][:4000],
            }
        )
    return sources


def _string_list(value: Any, field: str, *, allow_empty: bool = False) -> List[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ValueError(f"{field} must be a string array")
    cleaned = [item.strip() for item in value]
    if not allow_empty and not cleaned:
        raise ValueError(f"{field} cannot be empty")
    return cleaned


def run_reference_intelligence(
    *, provider: Any, store: ReferenceIntelligenceStore, snapshot: Dict[str, Any]
) -> Dict[str, Any]:
    sources = _source_catalog(snapshot)
    if not sources:
        raise ValueError("reference intelligence requires one bounded workspace source")
    source_ids = {item["source_id"] for item in sources}
    external_ids = {
        item["source_id"]
        for item in sources
        if item["source_class"] == "external_reference"
    }
    reference_mode = "workspace_plus_optional_references" if external_ids else "workspace_only"
    prompt = f"""Build a source-bounded project self-model and one research agenda.
The user must not be required to maintain a reference collection. External references are optional.
When external sources are absent, do not invent competitors or comparative conclusions: record
knowledge gaps and formulate a research question instead. README statements are claims, not proof.
Separate observed capability, inference, value judgment, and implementation authority.
Return JSON only:
{{
  "self_model": {{
    "capabilities":[{{"claim":"...","evidence_source_ids":["..."],"confidence":0}}],
    "unknowns":["..."]
  }},
  "hypotheses":[{{
    "kind":"gap|complement|differentiator|knowledge_gap",
    "claim":"...",
    "supporting_source_ids":["..."],
    "missing_evidence":"...",
    "falsifier":"...",
    "exploration_value":0
  }}],
  "selected_agenda": {{
    "status":"selected|deferred",
    "prompt":"bounded question, never an implementation command",
    "rationale":"...",
    "grounding_source_ids":["..."],
    "external_research_required":false,
    "stop_conditions":["..."]
  }}
}}
Use at most 8 capabilities and 3 hypotheses. Confidence and exploration_value are integers 0-100.
Available immutable observations:
{json.dumps(sources, ensure_ascii=False)}"""
    raw = "".join(
        provider.stream(
            [
                {
                    "role": "system",
                    "content": "You create research direction, not delivery authority.",
                },
                {"role": "user", "content": prompt},
            ]
        )
    )
    output = _extract_json_object(raw)
    self_model = output.get("self_model")
    if not isinstance(self_model, dict):
        raise ValueError("self_model must be an object")
    capabilities = self_model.get("capabilities")
    if not isinstance(capabilities, list) or not 1 <= len(capabilities) <= 8:
        raise ValueError("self_model capabilities must contain 1-8 items")
    for item in capabilities:
        if not isinstance(item, dict) or not str(item.get("claim", "")).strip():
            raise ValueError("each capability requires a claim")
        evidence_ids = _string_list(item.get("evidence_source_ids"), "evidence_source_ids")
        if not set(evidence_ids).issubset(source_ids):
            raise ValueError("capability cites unavailable source")
        confidence = item.get("confidence")
        if not isinstance(confidence, int) or not 0 <= confidence <= 100:
            raise ValueError("capability confidence must be integer 0-100")
    _string_list(self_model.get("unknowns"), "unknowns", allow_empty=True)
    hypotheses = output.get("hypotheses")
    if not isinstance(hypotheses, list) or not 1 <= len(hypotheses) <= 3:
        raise ValueError("hypotheses must contain 1-3 items")
    valid_kinds = {"gap", "complement", "differentiator", "knowledge_gap"}
    for item in hypotheses:
        if not isinstance(item, dict) or item.get("kind") not in valid_kinds:
            raise ValueError("invalid hypothesis kind")
        supporting = _string_list(
            item.get("supporting_source_ids"), "supporting_source_ids"
        )
        if not set(supporting).issubset(source_ids):
            raise ValueError("hypothesis cites unavailable source")
        if not external_ids and item["kind"] != "knowledge_gap":
            raise ValueError("workspace-only mode may emit knowledge_gap hypotheses only")
        for field in ("claim", "missing_evidence", "falsifier"):
            if not str(item.get(field, "")).strip():
                raise ValueError(f"hypothesis requires {field}")
        value = item.get("exploration_value")
        if not isinstance(value, int) or not 0 <= value <= 100:
            raise ValueError("exploration_value must be integer 0-100")
    agenda = output.get("selected_agenda")
    if not isinstance(agenda, dict) or agenda.get("status") not in {
        "selected",
        "deferred",
    }:
        raise ValueError("selected_agenda requires selected or deferred status")
    grounding = _string_list(
        agenda.get("grounding_source_ids"), "grounding_source_ids"
    )
    if not set(grounding).issubset(source_ids):
        raise ValueError("agenda cites unavailable source")
    for field in ("prompt", "rationale"):
        if not str(agenda.get(field, "")).strip():
            raise ValueError(f"selected_agenda requires {field}")
    _string_list(agenda.get("stop_conditions"), "stop_conditions")
    if not isinstance(agenda.get("external_research_required"), bool):
        raise ValueError("external_research_required must be boolean")
    now = utc_now()
    identity = {
        "observation_id": snapshot["observation_id"],
        "source_ids": sorted(source_ids),
        "output": output,
    }
    record = {
        "reference_intelligence_version": "palamedes-reference-intelligence/1",
        "reference_intelligence_id": f"reference-intelligence-{fingerprint(identity)[:12]}",
        "observation_id": snapshot["observation_id"],
        "reference_mode": reference_mode,
        "sources": sources,
        "self_model": self_model,
        "hypotheses": hypotheses,
        "selected_agenda": {
            **agenda,
            "delivery_authority_granted": False,
            "created_at": now,
        },
        "created_at": now,
    }
    store.save(record)
    return record
