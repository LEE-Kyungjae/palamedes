#!/usr/bin/env python3
"""Bounded self-authored research agendas from repeated outcome mechanisms."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from palamedes_observe import fingerprint, utc_now


class PromptAgendaStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.clusters_root = root / "causal-clusters"
        self.agendas_root = root / "prompt-agendas"
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

    def save_cluster(self, cluster: Dict[str, Any]) -> Path:
        return self._save(
            self.clusters_root, cluster["causal_cluster_id"], cluster
        )

    def save_agenda(self, agenda: Dict[str, Any]) -> Path:
        return self._save(self.agendas_root, agenda["prompt_agenda_id"], agenda)

    def append_event(self, event: Dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

    def load_cluster(self, cluster_id: str) -> Dict[str, Any]:
        path = self.clusters_root / f"{cluster_id}.json"
        if not path.is_file():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}

    def active_agendas(self, limit: int = 4) -> List[Dict[str, Any]]:
        if not self.agendas_root.is_dir():
            return []
        records = []
        for path in self.agendas_root.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict) and payload.get("status") == "selected":
                records.append(payload)
        records.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return records[:limit]

    def active_clusters(self, limit: int = 24) -> List[Dict[str, Any]]:
        if not self.clusters_root.is_dir():
            return []
        records = []
        for path in self.clusters_root.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict):
                records.append(payload)
        records.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
        return records[:limit]


def record_causal_pattern(
    *, store: PromptAgendaStore, interpretation: Dict[str, Any]
) -> Dict[str, Any]:
    signature = str(interpretation.get("causal_signature", "")).strip()
    mechanism = str(interpretation.get("mechanism_summary", "")).strip()
    if not signature or not mechanism:
        raise ValueError("causal pattern requires signature and mechanism summary")
    cluster_id = f"causal-cluster-{fingerprint(signature.casefold())[:12]}"
    previous = store.load_cluster(cluster_id)
    outcome_ids = list(previous.get("outcome_ids", []))
    if interpretation["outcome_id"] not in outcome_ids:
        outcome_ids.append(interpretation["outcome_id"])
    mission_ids = list(previous.get("mission_contract_ids", []))
    if interpretation["mission_contract_id"] not in mission_ids:
        mission_ids.append(interpretation["mission_contract_id"])
    count = len(outcome_ids)
    now = utc_now()
    cluster = {
        "causal_cluster_version": "palamedes-causal-cluster/1",
        "causal_cluster_id": cluster_id,
        "causal_signature": signature,
        "mechanism_summary": mechanism,
        "outcome_ids": outcome_ids,
        "mission_contract_ids": mission_ids,
        "recurrence_count": count,
        "meta_shift_required": count >= 2,
        "created_at": previous.get("created_at", now),
        "updated_at": now,
    }
    store.save_cluster(cluster)
    store.append_event(
        {
            "ts": now,
            "type": "causal_pattern_recorded",
            "causal_cluster_id": cluster_id,
            "outcome_id": interpretation["outcome_id"],
            "recurrence_count": count,
            "meta_shift_required": cluster["meta_shift_required"],
        }
    )
    return cluster


def _required_text(payload: Dict[str, Any], field: str) -> str:
    value = str(payload.get(field, "")).strip()
    if not value:
        raise ValueError(f"prompt architecture requires {field}")
    return value


def run_prompt_architecture(
    *, provider: Any, store: PromptAgendaStore, cluster: Dict[str, Any]
) -> Dict[str, Any]:
    from palamedes_chat import _provider_json, _role_artifact

    if not cluster.get("meta_shift_required"):
        return {"status": "not_applicable", "reason": "recurrence threshold not met"}
    existing = [
        item
        for item in store.active_agendas(100)
        if item.get("causal_cluster_id") == cluster["causal_cluster_id"]
    ]
    if existing:
        return {"status": "already_selected", "agenda": existing[0]}

    architect_prompt = f"""ROLE: prompt_architect
A causal mechanism has recurred across outcomes. Do not propose implementation.
Generate at least two competing research prompts that could move reasoning to a
higher abstraction instead of continuing symptom-by-symptom patches. The fixed
constitution—authority, evidence, privacy, budgets, approval, and falsification
rules—is immutable. You may design only the research question, perspective,
comparison, role sequence, and stopping logic.
Return exactly:
{{"missing_cognitive_mode":"...","prompt_candidates":[{{
  "prompt_id":"prompt-1","prompt":"...","perspective":"...",
  "expected_information_gain":0,"scope_risk":0,"falsifier":"...",
  "non_goals":["..."]
}}]}}

Causal cluster:
{json.dumps(cluster, ensure_ascii=False)}"""
    architect = _provider_json(
        provider,
        system="You design bounded research prompts, never implementation authority.",
        prompt=architect_prompt,
    )
    _required_text(architect, "missing_cognitive_mode")
    candidates = architect.get("prompt_candidates")
    if not isinstance(candidates, list) or len(candidates) < 2:
        raise ValueError("prompt architect requires at least two candidates")
    candidate_ids = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("prompt candidate must be an object")
        candidate_id = _required_text(candidate, "prompt_id")
        for field in ("prompt", "perspective", "falsifier"):
            _required_text(candidate, field)
        for field in ("expected_information_gain", "scope_risk"):
            value = candidate.get(field)
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 100:
                raise ValueError(f"{field} must be an integer from 0 to 100")
        non_goals = candidate.get("non_goals")
        if not isinstance(non_goals, list) or not all(
            isinstance(item, str) and item.strip() for item in non_goals
        ):
            raise ValueError("prompt candidate non_goals must be a string array")
        candidate_ids.append(candidate_id)
    if len(set(candidate_ids)) != len(candidate_ids):
        raise ValueError("prompt candidate IDs must be unique")

    adversary_prompt = f"""ROLE: prompt_adversary
Attack every frozen prompt candidate for disguised TODO repetition,
self-confirmation, scope expansion, reopened closed evidence, unfalsifiability,
and failure to change a decision. Do not invent a new prompt or select a winner.
Return exactly:
{{"critiques":[{{"prompt_id":"prompt-1","fatal_risks":["..."],
"repairable_risks":["..."],"disqualifying":false}}]}}

Cluster:
{json.dumps(cluster, ensure_ascii=False)}
Frozen candidates:
{json.dumps(candidates, ensure_ascii=False)}"""
    adversary = _provider_json(
        provider,
        system="You adversarially test self-authored prompts without expanding them.",
        prompt=adversary_prompt,
    )
    critiques = adversary.get("critiques")
    if not isinstance(critiques, list) or {
        str(item.get("prompt_id", "")).strip()
        for item in critiques
        if isinstance(item, dict)
    } != set(candidate_ids):
        raise ValueError("prompt adversary must critique every candidate")

    selector_prompt = f"""ROLE: prompt_selector
Select at most one frozen research prompt by expected decision-changing
information value after scope risk and critique. You may defer all candidates.
Do not rewrite prompts or grant delivery authority.
Return exactly:
{{"decision":"select|defer","selected_prompt_id":"prompt ID or empty",
"rationale":"...","role_sequence":["..."],"call_budget":0,
"stop_conditions":["..."]}}

Cluster:
{json.dumps(cluster, ensure_ascii=False)}
Candidates:
{json.dumps(candidates, ensure_ascii=False)}
Critiques:
{json.dumps(critiques, ensure_ascii=False)}"""
    selector = _provider_json(
        provider,
        system="You select a bounded research agenda, not an implementation task.",
        prompt=selector_prompt,
    )
    decision = selector.get("decision")
    selected_id = str(selector.get("selected_prompt_id", "")).strip()
    if decision not in {"select", "defer"}:
        raise ValueError("prompt selector has invalid decision")
    if decision == "select" and selected_id not in candidate_ids:
        raise ValueError("prompt selector must select a frozen candidate")
    if decision == "defer" and selected_id:
        raise ValueError("deferred prompt agenda cannot select a candidate")
    _required_text(selector, "rationale")
    for field in ("role_sequence", "stop_conditions"):
        values = selector.get(field)
        if not isinstance(values, list) or not all(
            isinstance(item, str) and item.strip() for item in values
        ):
            raise ValueError(f"prompt selector {field} must be a string array")
    call_budget = selector.get("call_budget")
    if not isinstance(call_budget, int) or isinstance(call_budget, bool) or not 0 <= call_budget <= 8:
        raise ValueError("prompt selector call_budget must be an integer from 0 to 8")

    selected = next(
        (item for item in candidates if item["prompt_id"] == selected_id), None
    )
    now = utc_now()
    agenda_id = f"prompt-agenda-{fingerprint({'cluster': cluster['causal_cluster_id'], 'candidates': candidates})[:12]}"
    artifacts = [
        _role_artifact(role="prompt_architect", call_index=1, prompt=architect_prompt, output=architect, provider=provider),
        _role_artifact(role="prompt_adversary", call_index=2, prompt=adversary_prompt, output=adversary, provider=provider),
        _role_artifact(role="prompt_selector", call_index=3, prompt=selector_prompt, output=selector, provider=provider),
    ]
    agenda = {
        "prompt_agenda_version": "palamedes-prompt-agenda/1",
        "prompt_agenda_id": agenda_id,
        "causal_cluster_id": cluster["causal_cluster_id"],
        "recurrence_count": cluster["recurrence_count"],
        "missing_cognitive_mode": architect["missing_cognitive_mode"],
        "candidates": candidates,
        "critiques": critiques,
        "decision": decision,
        "selected_prompt": selected,
        "role_sequence": selector["role_sequence"],
        "call_budget": call_budget,
        "stop_conditions": selector["stop_conditions"],
        "rationale": selector["rationale"],
        "status": "selected" if decision == "select" else "deferred",
        "constitutional_constraints_mutable": False,
        "delivery_authority_granted": False,
        "artifacts": artifacts,
        "created_at": now,
    }
    store.save_agenda(agenda)
    store.append_event(
        {"ts": now, "type": "prompt_agenda_created", "prompt_agenda_id": agenda_id, "causal_cluster_id": cluster["causal_cluster_id"], "status": agenda["status"]}
    )
    return {"status": "completed", "agenda": agenda, "model_call_count": 3}
