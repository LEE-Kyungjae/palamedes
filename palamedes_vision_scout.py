#!/usr/bin/env python3
"""Low-cost upstream founder-prompt scouting before full Vision Genesis."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from palamedes_observe import utc_now
from palamedes_vision import fingerprint


VISION_SCOUT_VERSION = "palamedes-vision-scout/4"


def _strings(value: Any, field: str, minimum: int = 1) -> List[str]:
    if not isinstance(value, list) or len(value) < minimum or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ValueError(f"{field} requires at least {minimum} strings")
    return [item.strip() for item in value]


def _source_quote_present(source_quote: str, context: str) -> bool:
    if source_quote in context:
        return True
    normalized_quote = re.sub(r"\s+", " ", source_quote).strip()
    normalized_context = re.sub(r"\s+", " ", context).strip()
    return bool(normalized_quote and normalized_quote in normalized_context)


def _source_anchors(context: str) -> Dict[str, str]:
    candidates: List[str] = []

    def collect(value: Any) -> None:
        if isinstance(value, str):
            normalized = re.sub(r"\s+", " ", value).strip()
            if 12 <= len(normalized) <= 600:
                candidates.append(normalized)
        elif isinstance(value, dict):
            for item in value.values():
                collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)

    try:
        parsed = json.loads(context)
    except json.JSONDecodeError:
        parsed = None
    if parsed is not None:
        collect(parsed)
    if not candidates:
        candidates.extend(
            part.strip()
            for part in re.split(r"(?<=[.!?])\s+|\n+", context)
            if 12 <= len(part.strip()) <= 600
        )
    unique = []
    for candidate in candidates:
        if candidate not in unique:
            unique.append(candidate)
    if not unique:
        raise ValueError("vision scout context contains no attributable source anchor")
    return {
        f"anchor-{index}": value
        for index, value in enumerate(unique[:16], start=1)
    }


class VisionScoutStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def save(self, record: Dict[str, Any]) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"{record['vision_scout_id']}.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return path

    def save_context(self, vision_scout_id: str, context: str) -> Path:
        if not re.fullmatch(r"vision-scout-[a-f0-9]{12}", vision_scout_id):
            raise ValueError("invalid vision scout ID")
        root = self.root / "contexts"
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{vision_scout_id}.json"
        payload = {
            "vision_scout_context_version": "palamedes-vision-scout-context/1",
            "vision_scout_id": vision_scout_id,
            "context": context,
            "context_fingerprint": fingerprint(context),
            "stored_at": utc_now(),
        }
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path

    def load_context(self, vision_scout_id: str) -> str:
        self.load(vision_scout_id)
        path = self.root / "contexts" / f"{vision_scout_id}.json"
        if not path.is_file():
            raise ValueError("vision scout context is unavailable")
        payload = json.loads(path.read_text(encoding="utf-8"))
        context = str(payload.get("context", ""))
        if fingerprint(context) != payload.get("context_fingerprint"):
            raise ValueError("vision scout context fingerprint mismatch")
        return context

    def register_probe(self, vision_scout_id: str, proposal: Dict[str, Any]) -> Dict[str, Any]:
        scout = self.load(vision_scout_id)
        if scout.get("status") != "candidate_for_human_review":
            raise ValueError("discarded vision scout cannot register a probe")
        root = self.root / "probes"
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{vision_scout_id}.json"
        if path.exists():
            raise ValueError("vision scout probe is already preregistered")
        hypothesis = str(proposal.get("hypothesis", "")).strip()
        metric_name = str(proposal.get("metric_name", "")).strip()
        operator = proposal.get("success_operator")
        threshold = proposal.get("threshold")
        minimum_sample_size = proposal.get("minimum_sample_size")
        max_duration_days = proposal.get("max_duration_days")
        data_source = str(proposal.get("data_source", "")).strip()
        if not all((hypothesis, metric_name, data_source)):
            raise ValueError("vision scout probe requires hypothesis, metric_name, and data_source")
        if operator not in {"gt", "gte", "lt", "lte"}:
            raise ValueError("vision scout probe success_operator is invalid")
        if not isinstance(threshold, (int, float)) or isinstance(threshold, bool):
            raise ValueError("vision scout probe threshold must be numeric")
        if (
            not isinstance(minimum_sample_size, int)
            or isinstance(minimum_sample_size, bool)
            or minimum_sample_size < 5
        ):
            raise ValueError("vision scout probe minimum_sample_size must be at least 5")
        if (
            not isinstance(max_duration_days, int)
            or isinstance(max_duration_days, bool)
            or not 1 <= max_duration_days <= 30
        ):
            raise ValueError("vision scout probe max_duration_days must be 1-30")
        identity = {
            "vision_scout_id": vision_scout_id,
            "hypothesis": hypothesis,
            "metric_name": metric_name,
            "success_operator": operator,
            "threshold": threshold,
            "minimum_sample_size": minimum_sample_size,
            "max_duration_days": max_duration_days,
            "data_source": data_source,
        }
        record = {
            "vision_scout_probe_version": "palamedes-vision-scout-probe/1",
            "probe_id": f"vision-scout-probe-{fingerprint(identity)[:12]}",
            **identity,
            "status": "preregistered",
            "registered_at": utc_now(),
        }
        path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return record

    def load_probe(self, vision_scout_id: str) -> Dict[str, Any]:
        self.load(vision_scout_id)
        path = self.root / "probes" / f"{vision_scout_id}.json"
        if not path.is_file():
            raise ValueError("vision scout probe is not preregistered")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("vision scout probe record must be an object")
        return payload

    def record_probe_outcome(
        self, vision_scout_id: str, outcome: Dict[str, Any]
    ) -> Dict[str, Any]:
        probe = self.load_probe(vision_scout_id)
        root = self.root / "probe-outcomes"
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{vision_scout_id}.json"
        if path.exists():
            raise ValueError("vision scout probe outcome is already recorded")
        if outcome.get("probe_id") != probe["probe_id"]:
            raise ValueError("vision scout probe outcome ID mismatch")
        observed_value = outcome.get("observed_value")
        sample_size = outcome.get("sample_size")
        provenance = outcome.get("measurement_provenance")
        source_reference = str(outcome.get("source_reference", "")).strip()
        observation = str(outcome.get("observation", "")).strip()
        if not isinstance(observed_value, (int, float)) or isinstance(observed_value, bool):
            raise ValueError("vision scout probe observed_value must be numeric")
        if (
            not isinstance(sample_size, int)
            or isinstance(sample_size, bool)
            or sample_size < probe["minimum_sample_size"]
        ):
            raise ValueError("vision scout probe sample size is below preregistration")
        if provenance not in {"measured", "external_dataset"}:
            raise ValueError("vision scout probe requires measured or external_dataset provenance")
        if not source_reference or not observation:
            raise ValueError("vision scout probe outcome requires source_reference and observation")
        comparisons = {
            "gt": observed_value > probe["threshold"],
            "gte": observed_value >= probe["threshold"],
            "lt": observed_value < probe["threshold"],
            "lte": observed_value <= probe["threshold"],
        }
        supports = comparisons[probe["success_operator"]]
        identity = {
            "vision_scout_id": vision_scout_id,
            "probe_id": probe["probe_id"],
            "observed_value": observed_value,
            "sample_size": sample_size,
            "measurement_provenance": provenance,
            "source_reference": source_reference,
        }
        record = {
            "vision_scout_probe_outcome_version": (
                "palamedes-vision-scout-probe-outcome/1"
            ),
            "probe_outcome_id": (
                f"vision-scout-probe-outcome-{fingerprint(identity)[:12]}"
            ),
            **identity,
            "metric_name": probe["metric_name"],
            "success_operator": probe["success_operator"],
            "threshold": probe["threshold"],
            "observation": observation,
            "supports_full_genesis_renewal": supports,
            "delivery_authority_granted": False,
            "recorded_at": utc_now(),
        }
        path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return record

    def probe_outcome(self, vision_scout_id: str) -> Optional[Dict[str, Any]]:
        path = self.root / "probe-outcomes" / f"{vision_scout_id}.json"
        if not path.is_file():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None

    def project_attempts(self) -> List[Dict[str, Any]]:
        path = self.root / "project-attempts.jsonl"
        if not path.is_file():
            return []
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
        return rows

    def project_checkpoint(self, attempt_id: str) -> Dict[str, Any]:
        path = self.root / "project-checkpoints" / f"{attempt_id}.json"
        if not path.is_file():
            return {"roles": {}}
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {"roles": {}}

    def save_project_checkpoint(
        self,
        attempt_id: str,
        role: str,
        output: Dict[str, Any],
        usage: Dict[str, Any],
    ) -> None:
        if not re.fullmatch(r"vision-scout-project-attempt-[a-f0-9]{12}", attempt_id):
            raise ValueError("invalid project Scout attempt ID")
        root = self.root / "project-checkpoints"
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{attempt_id}.json"
        payload = self.project_checkpoint(attempt_id)
        roles = payload.setdefault("roles", {})
        if role in roles:
            if roles[role].get("output") != output:
                raise ValueError("project Scout checkpoint output is immutable")
            return
        roles[role] = {
            "output": output,
            "usage": usage,
            "output_fingerprint": fingerprint(output),
            "saved_at": utc_now(),
        }
        payload.update(
            {
                "vision_scout_project_checkpoint_version": (
                    "palamedes-vision-scout-project-checkpoint/1"
                ),
                "attempt_id": attempt_id,
            }
        )
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def reserve_project_attempt(
        self, *, request_fingerprint: str, context_fingerprint: str
    ) -> Dict[str, Any]:
        attempt_key = fingerprint(
            {
                "vision_scout_version": VISION_SCOUT_VERSION,
                "request_fingerprint": request_fingerprint,
            }
        )
        prior = [
            row
            for row in self.project_attempts()
            if row.get("attempt_key") == attempt_key
        ]
        if prior:
            latest = prior[-1]
            resume_count = sum(row.get("status") == "resumed" for row in prior)
            if (
                latest.get("status") == "failed"
                and latest.get("error_type") == "RuntimeError"
                and resume_count < 2
                and self.project_checkpoint(latest["attempt_id"]).get("roles")
            ):
                resumed = dict(prior[0])
                resumed.update(
                    {
                        "status": "resumed",
                        "resume_count": resume_count + 1,
                        "resumed_at": utc_now(),
                    }
                )
                self._append_project_attempt(resumed)
                return resumed
            raise ValueError("project vision scout trial budget exhausted: 1/1")
        attempt = {
            "vision_scout_project_attempt_version": (
                "palamedes-vision-scout-project-attempt/1"
            ),
            "attempt_id": f"vision-scout-project-attempt-{attempt_key[:12]}",
            "attempt_key": attempt_key,
            "request_fingerprint": request_fingerprint,
            "context_fingerprint": context_fingerprint,
            "status": "started",
            "started_at": utc_now(),
        }
        self._append_project_attempt(attempt)
        return attempt

    def complete_project_attempt(
        self, attempt: Dict[str, Any], vision_scout_id: str, provider_usage: Dict[str, Any]
    ) -> None:
        completed = dict(attempt)
        completed.update(
            {
                "status": "completed",
                "vision_scout_id": vision_scout_id,
                "provider_usage": provider_usage,
                "completed_at": utc_now(),
            }
        )
        self._append_project_attempt(completed)

    def fail_project_attempt(
        self, attempt: Dict[str, Any], provider_usage: Dict[str, Any], error: Exception
    ) -> None:
        failed = dict(attempt)
        failed.update(
            {
                "status": "failed",
                "provider_usage": provider_usage,
                "error_type": type(error).__name__,
                "failed_at": utc_now(),
            }
        )
        self._append_project_attempt(failed)

    def _append_project_attempt(self, record: Dict[str, Any]) -> None:
        path = self.root / "project-attempts.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    def load(self, vision_scout_id: str) -> Dict[str, Any]:
        if not re.fullmatch(r"vision-scout-[a-f0-9]{12}", vision_scout_id):
            raise ValueError("invalid vision scout ID")
        path = self.root / f"{vision_scout_id}.json"
        if not path.is_file():
            raise ValueError("unknown vision scout")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("vision scout record must be an object")
        return payload

    def find_by_context(self, context: str) -> Optional[Dict[str, Any]]:
        context_fingerprint = fingerprint(context)
        if not self.root.is_dir():
            return None
        for path in sorted(self.root.glob("vision-scout-*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if payload.get("context_fingerprint") == context_fingerprint:
                return payload
        return None

    def find_by_request_fingerprint(
        self,
        request_fingerprint: str,
        vision_scout_version: str = VISION_SCOUT_VERSION,
    ) -> Optional[Dict[str, Any]]:
        if not request_fingerprint or not self.root.is_dir():
            return None
        for path in sorted(self.root.glob("vision-scout-*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if (
                payload.get("request_fingerprint") == request_fingerprint
                and payload.get("vision_scout_version") == vision_scout_version
            ):
                return payload
        return None


def run_vision_scout(
    *,
    ask: Callable[[str, str], Dict[str, Any]],
    store: VisionScoutStore,
    context: str,
) -> Dict[str, Any]:
    """Originate and screen a founder prompt in three provider calls, with no delivery authority."""
    source_anchors = _source_anchors(context)
    origin = ask(
        "vision_scout_originator",
        f"""Originate exactly three materially different upstream founder prompts from the
product context. The user has not supplied a solution. Do not produce a feature backlog,
generic engagement advice, or variants that differ only in theme. One candidate must
transform rules/interaction causality, one meaning/identity, and one resources,
institutions, or social coordination. Include positive, negative, mixed, direct, mediated,
and social affect where causally relevant, while making harm boundaries explicit.
Return JSON:
{{"context_requirements":[{{"requirement_id":"req-1","source_anchor_id":"anchor-1",
"requirement":"...","criticality":"core|supporting"}}],
"candidates":[{{"candidate_id":"candidate-1",
"causal_lane":"rules_interaction|meaning_identity|resources_institutions_social",
"founder_prompt":"180-1200 character standalone direction a human founder could have
written but did not","human_tension":"...","unsupplied_mechanism":"...",
"affective_loop":"...","durable_expansion_engine":"...","harm_boundary":"...",
"smallest_disconfirming_probe":"..."}}]}}
Every source_anchor_id must select one ID from the authoritative list below. Do not copy,
rewrite, or invent source text; Palamedes attaches it after your response. At least one
requirement is core.
The founder prompt itself must introduce the mechanism and emotional/behavioral thesis,
without internal IDs, model narration, or named solutions from these instructions.

Authoritative source anchors:
{json.dumps(source_anchors, ensure_ascii=False, indent=2)}

Product context:
{context}""",
    )
    requirements = origin.get("context_requirements")
    if not isinstance(requirements, list) or not requirements:
        raise ValueError("vision scout requires context requirements")
    requirement_ids = set()
    core_requirements = set()
    for row in requirements:
        if not isinstance(row, dict):
            raise ValueError("vision scout requirement must be an object")
        for field in ("requirement_id", "source_anchor_id", "requirement"):
            if not str(row.get(field, "")).strip():
                raise ValueError(f"vision scout requirement requires {field}")
        if row["source_anchor_id"] not in source_anchors:
            raise ValueError("vision scout requirement source anchor is invalid")
        row["source_quote"] = source_anchors[row["source_anchor_id"]]
        if row.get("criticality") not in {"core", "supporting"}:
            raise ValueError("vision scout requirement criticality is invalid")
        if row["requirement_id"] in requirement_ids:
            raise ValueError("vision scout requirement IDs must be unique")
        requirement_ids.add(row["requirement_id"])
        if row["criticality"] == "core":
            core_requirements.add(row["requirement_id"])
    if not core_requirements:
        raise ValueError("vision scout requires at least one core requirement")

    candidates = origin.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 3:
        raise ValueError("vision scout requires exactly three candidates")
    candidate_ids = set()
    lanes = set()
    for row in candidates:
        if not isinstance(row, dict):
            raise ValueError("vision scout candidate must be an object")
        for field in (
            "candidate_id", "founder_prompt", "human_tension",
            "unsupplied_mechanism", "affective_loop", "durable_expansion_engine",
            "harm_boundary", "smallest_disconfirming_probe",
        ):
            if not str(row.get(field, "")).strip():
                raise ValueError(f"vision scout candidate requires {field}")
        prompt = row["founder_prompt"].strip()
        if not 180 <= len(prompt) <= 1200:
            raise ValueError("vision scout founder_prompt must be 180-1200 characters")
        if re.search(
            r"\b(?:candidate|vision|fusion|analogy|desire|question)-\d+\b",
            prompt,
            flags=re.IGNORECASE,
        ):
            raise ValueError("vision scout founder_prompt exposes internal IDs")
        if row.get("causal_lane") not in {
            "rules_interaction", "meaning_identity", "resources_institutions_social"
        }:
            raise ValueError("vision scout candidate causal lane is invalid")
        if row["candidate_id"] in candidate_ids:
            raise ValueError("vision scout candidate IDs must be unique")
        candidate_ids.add(row["candidate_id"])
        lanes.add(row["causal_lane"])
    if lanes != {
        "rules_interaction", "meaning_identity", "resources_institutions_social"
    }:
        raise ValueError("vision scout candidates must cover all causal lanes")

    critique = ask(
        "vision_scout_critic",
        f"""Act as a founder-level critic, not an encouraging brainstormer. Reject generic
gamification, a supplied solution merely restated, adjacent feature bundles, incoherent
affect, unbounded harm, and mechanisms that cannot seed years of product evolution. Return
JSON:
{{"critiques":[{{"candidate_id":"candidate-1","problem_reframing":"...",
"mechanism_originality":"...","affective_truth":"...","world_seed":"...",
"context_fit":"...","cost_or_harm_risk":"...","verdict":"advance|reject"}}],
"decision":"select|reject_all","selected_candidate_id":"candidate-1 or empty",
"selected_founder_prompt":"exact candidate text or empty","selection_reason":"...",
"requirement_coverage":[{{"requirement_id":"req-1",
"status":"satisfied|partial|missed","evidence":"..."}}],
"assumptions":["..."],"falsifiers":["..."],
"delivery_authority_granted":false}}
Select at most one. Do not rewrite the selected prompt; copy it exactly so authorship and
cost custody remain attributable to the originator call.

Product context:
{context}

Originator output:
{json.dumps(origin, ensure_ascii=False)}""",
    )
    critiques = critique.get("critiques")
    if not isinstance(critiques, list) or len(critiques) != 3:
        raise ValueError("vision scout critic requires three critiques")
    if {row.get("candidate_id") for row in critiques} != candidate_ids:
        raise ValueError("vision scout critiques must cover every candidate")
    for row in critiques:
        for field in (
            "problem_reframing", "mechanism_originality", "affective_truth",
            "world_seed", "context_fit", "cost_or_harm_risk",
        ):
            if not str(row.get(field, "")).strip():
                raise ValueError(f"vision scout critique requires {field}")
        if row.get("verdict") not in {"advance", "reject"}:
            raise ValueError("vision scout critique verdict is invalid")
    decision = critique.get("decision")
    selected_id = str(critique.get("selected_candidate_id", "")).strip()
    selected_prompt = str(critique.get("selected_founder_prompt", "")).strip()
    if decision not in {"select", "reject_all"}:
        raise ValueError("vision scout critic decision is invalid")
    candidates_by_id = {row["candidate_id"]: row for row in candidates}
    if decision == "select":
        if selected_id not in candidate_ids:
            raise ValueError("vision scout selected unknown candidate")
        if selected_prompt != candidates_by_id[selected_id]["founder_prompt"].strip():
            raise ValueError("vision scout critic must copy the selected founder prompt")
    elif selected_id or selected_prompt:
        raise ValueError("vision scout reject_all cannot select a candidate")
    if not str(critique.get("selection_reason", "")).strip():
        raise ValueError("vision scout critic requires selection_reason")
    coverage = critique.get("requirement_coverage")
    if not isinstance(coverage, list) or {
        row.get("requirement_id") for row in coverage if isinstance(row, dict)
    } != requirement_ids:
        raise ValueError("vision scout critic must cover every requirement")
    coverage_by_id = {}
    for row in coverage:
        if row.get("status") not in {"satisfied", "partial", "missed"}:
            raise ValueError("vision scout requirement coverage status is invalid")
        if not str(row.get("evidence", "")).strip():
            raise ValueError("vision scout requirement coverage requires evidence")
        coverage_by_id[row["requirement_id"]] = row["status"]
    unresolved_core = sorted(
        requirement_id
        for requirement_id in core_requirements
        if coverage_by_id[requirement_id] != "satisfied"
    )
    _strings(critique.get("assumptions"), "vision scout assumptions")
    _strings(critique.get("falsifiers"), "vision scout falsifiers")
    if critique.get("delivery_authority_granted") is not False:
        raise ValueError("vision scout cannot grant delivery authority")

    governor = ask(
        "vision_scout_governor",
        f"""Decide whether this low-cost scout deserves no further work, one blind human
review packet, or the expensive seven-role Vision Genesis. Evidence is speculative and no
delivery may be authorized. Return JSON:
{{"alternatives":[{{"alternative":"discard|blind_human_review|full_genesis",
"estimated_next_provider_calls":0,"learning_value":"...","opportunity_cost":"...",
"failure_mode":"..."}}],"decision":"discard|blind_human_review",
"decision_rationale":"...","full_genesis_renewal_evidence":["..."],
"kill_criteria":["..."],"delivery_authority_granted":false}}
Include exactly all three alternatives. `full_genesis` cannot be selected from speculative
model-only evidence; it requires a later human or behavioral renewal signal. Prefer discard
when core requirements are unresolved or all candidates were rejected.

Context:
{context}

Critic output:
{json.dumps(critique, ensure_ascii=False)}
Unresolved core requirements:
{json.dumps(unresolved_core)}""",
    )
    alternatives = governor.get("alternatives")
    expected_alternatives = {"discard", "blind_human_review", "full_genesis"}
    if not isinstance(alternatives, list) or {
        row.get("alternative") for row in alternatives if isinstance(row, dict)
    } != expected_alternatives:
        raise ValueError("vision scout governor requires all three alternatives")
    for row in alternatives:
        calls = row.get("estimated_next_provider_calls")
        if not isinstance(calls, int) or isinstance(calls, bool) or calls < 0:
            raise ValueError("vision scout next provider calls must be non-negative integer")
        for field in ("learning_value", "opportunity_cost", "failure_mode"):
            if not str(row.get(field, "")).strip():
                raise ValueError(f"vision scout alternative requires {field}")
    if governor.get("decision") not in {"discard", "blind_human_review"}:
        raise ValueError("vision scout cannot directly select full Genesis")
    if decision != "select" or unresolved_core:
        if governor["decision"] != "discard":
            raise ValueError("vision scout must discard rejected or misaligned candidates")
    for field in ("decision_rationale",):
        if not str(governor.get(field, "")).strip():
            raise ValueError(f"vision scout governor requires {field}")
    _strings(governor.get("full_genesis_renewal_evidence"), "scout renewal evidence")
    _strings(governor.get("kill_criteria"), "scout kill criteria")
    if governor.get("delivery_authority_granted") is not False:
        raise ValueError("vision scout governor cannot grant delivery authority")

    identity = {
        "context": context,
        "origin": origin,
        "critique": critique,
        "governor": governor,
    }
    record = {
        "vision_scout_version": VISION_SCOUT_VERSION,
        "vision_scout_id": f"vision-scout-{fingerprint(identity)[:12]}",
        "status": (
            "candidate_for_human_review"
            if governor["decision"] == "blind_human_review"
            else "discarded"
        ),
        "context_fingerprint": fingerprint(context),
        "originator": origin,
        "critique": critique,
        "governor": governor,
        "selected_founder_prompt": selected_prompt,
        "unresolved_core_requirement_ids": unresolved_core,
        "generation_call_count": 3,
        "full_genesis_authorized": False,
        "delivery_authority_granted": False,
        "created_at": utc_now(),
    }
    store.save(record)
    store.save_context(record["vision_scout_id"], context)
    return record
