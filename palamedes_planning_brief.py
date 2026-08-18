#!/usr/bin/env python3
"""Generate a scale-adaptive plan after mission selection and before execution."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional

from palamedes_chat import _provider_json, provider_from_config
from palamedes_mission import validate_scale_adaptive_planning_brief
from palamedes_observe import utc_now


PLAN_SCALES = ("auto", "decision", "feature", "content", "service", "platform")
PLAN_STAGES = ("direction", "concept", "approval", "delivery")


def _fingerprint(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _mission_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    nested = payload.get("mission")
    return nested if isinstance(nested, dict) else payload


def _anchor_brief(
    brief: Dict[str, Any],
    *,
    mission_id: str,
    mission_fingerprint: str,
    plan_scale: str,
    planning_stage: str,
) -> Dict[str, Any]:
    anchored = dict(brief)
    anchored["mission_contract_id"] = mission_id
    anchored["mission_contract_fingerprint"] = mission_fingerprint
    if plan_scale != "auto":
        anchored["plan_scale"] = plan_scale
    anchored["planning_stage"] = planning_stage
    content_fingerprint = _fingerprint(
        {key: value for key, value in anchored.items() if key not in {
            "planning_brief_id", "planning_brief_fingerprint"
        }}
    )
    anchored["planning_brief_id"] = f"planning-brief-{content_fingerprint[:12]}"
    anchored["planning_brief_fingerprint"] = content_fingerprint
    anchored["execution_authority_issued"] = False
    anchored["mission_semantics_preserved"] = True
    return anchored


def _system_prompt() -> str:
    return """You are the Palamedes post-mission planning architect.
Transform an already selected mission into a decision-ready planning brief, not merely advice.
Return one JSON object only. Do not issue execution authority.

Choose plan_scale from decision, feature, content, service, platform unless it is fixed by input.
Respect planning_stage:
- direction: define outcome, beneficiary, value, scope, evidence, uncertainty, and gates; leave concepts open.
- concept: for content/service/platform, add experience_contract, at least two alternatives with exactly one selected, components, dependencies, and effects.
- approval or delivery: additionally add phases and resource_envelope.

Required top-level fields:
planning_brief_id, mission_contract_id, mission_contract_fingerprint,
planning_brief_fingerprint, plan_scale, planning_stage, outcome, beneficiary,
value_proposition, resolution_basis, in_scope, out_of_scope, success_signals,
stop_conditions, knowledge_ledger, experience_contract, alternatives, components,
external_dependencies, effects, phases, decision_gates, resource_envelope,
execution_authority_issued, mission_semantics_preserved, planning_rationale.

resolution_basis has uncertainty, irreversibility, coordination_cost, harm_potential
(low/medium/high) and resolution_rationale.
knowledge_ledger items have item_id, status (observed/decided/assumed/unresolved),
statement, evidence_ids, validation_probe. Observed/decided claims need evidence;
assumed/unresolved claims need a probe.
components have component_id, kind, purpose, requires, provides, maturity
(existing/adapt/new/unresolved). Every requirement needs a component provider or explicit
external dependency.
effects have effect_id, description, reversibility (reversible/compensatable/irreversible),
rollback, compensation, approval_required. Reversible needs rollback, compensatable needs
compensation, irreversible needs approval_required and a decision gate whose
authorizes_irreversible_effects is true.
phases have phase_id, objective, component_ids, entry_gate, exit_gate, outputs.
decision_gates have gate_id, question, evidence_required, on_pass, on_fail,
authorizes_irreversible_effects.
resource_envelope has people, timebox, budget, critical_assets.

Use concrete project elements only when supported by supplied evidence. Do not convert missing
access, people, cost, dates, or assets into facts. Mark them unresolved and define a probe.
Planning detail must clarify consequential choices without pretending implementation already began."""


def _prompt_payload(
    mission: Dict[str, Any],
    *,
    plan_scale: str,
    planning_stage: str,
    context: str,
    prior_brief: Optional[Dict[str, Any]] = None,
    validation_errors: Optional[list[str]] = None,
) -> str:
    payload: Dict[str, Any] = {
        "mission": mission,
        "requested_plan_scale": plan_scale,
        "required_planning_stage": planning_stage,
        "bounded_context": context[:50000],
    }
    if prior_brief is not None:
        payload["prior_brief"] = prior_brief
        payload["deterministic_validation_errors"] = validation_errors or []
        payload["revision_instruction"] = (
            "Act as an adversarial planning reviewer. Return a complete revised brief. Preserve "
            "the mission, remove false precision, close component dependencies, and make the "
            "experience, phases, effects, resources, and decision gates concrete enough for the stage."
        )
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def generate_planning_brief(
    mission_record: Dict[str, Any],
    provider: Any,
    *,
    plan_scale: str = "auto",
    planning_stage: str = "approval",
    context: str = "",
) -> Dict[str, Any]:
    if plan_scale not in PLAN_SCALES:
        raise ValueError(f"unsupported plan scale: {plan_scale}")
    if planning_stage not in PLAN_STAGES:
        raise ValueError(f"unsupported planning stage: {planning_stage}")
    if not isinstance(mission_record, dict) or not mission_record:
        raise ValueError("mission record must be a non-empty object")
    mission = _mission_payload(mission_record)
    mission_fingerprint = str(
        mission_record.get("contract_fingerprint")
        or mission_record.get("output_fingerprint")
        or _fingerprint(mission)
    )
    mission_id = str(
        mission_record.get("mission_id")
        or mission.get("mission_id")
        or f"mission-{mission_fingerprint[:12]}"
    )

    usage = []
    draft = _provider_json(
        provider,
        system=_system_prompt(),
        prompt=_prompt_payload(
            mission, plan_scale=plan_scale, planning_stage=planning_stage, context=context
        ),
    )
    usage.append(dict(getattr(provider, "last_usage", None) or {}))
    draft = _anchor_brief(
        draft,
        mission_id=mission_id,
        mission_fingerprint=mission_fingerprint,
        plan_scale=plan_scale,
        planning_stage=planning_stage,
    )
    draft_report = validate_scale_adaptive_planning_brief(draft)

    revised = _provider_json(
        provider,
        system=_system_prompt(),
        prompt=_prompt_payload(
            mission,
            plan_scale=plan_scale,
            planning_stage=planning_stage,
            context=context,
            prior_brief=draft,
            validation_errors=draft_report["errors"],
        ),
    )
    usage.append(dict(getattr(provider, "last_usage", None) or {}))
    revised = _anchor_brief(
        revised,
        mission_id=mission_id,
        mission_fingerprint=mission_fingerprint,
        plan_scale=plan_scale,
        planning_stage=planning_stage,
    )
    final_report = validate_scale_adaptive_planning_brief(revised)
    if not final_report["valid"]:
        raise ValueError(
            "revised planning brief failed deterministic validation: "
            + "; ".join(final_report["errors"])
        )
    return {
        "planning_generation_version": "palamedes-planning-generation/1",
        "generated_at": utc_now(),
        "mission_contract_id": mission_id,
        "mission_contract_fingerprint": mission_fingerprint,
        "call_count": 2,
        "draft": draft,
        "draft_validation": draft_report,
        "planning_brief": revised,
        "final_validation": final_report,
        "provider_usage": usage,
        "execution_authority_issued": False,
    }


def write_generation(path: Path, result: Dict[str, Any]) -> None:
    if path.exists():
        raise ValueError(f"output already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def cmd_planning_brief(args: Any) -> None:
    mission_path = Path(args.mission).expanduser().resolve()
    mission = json.loads(mission_path.read_text(encoding="utf-8"))
    if not isinstance(mission, dict):
        raise ValueError("mission file must contain a JSON object")
    context = ""
    if args.context_file:
        context = Path(args.context_file).expanduser().resolve().read_text(encoding="utf-8")
    provider = provider_from_config(
        args.provider,
        args.model,
        base_url=args.provider_base_url,
        api_key_env=args.provider_api_key_env,
    )
    result = generate_planning_brief(
        mission,
        provider,
        plan_scale=args.plan_scale,
        planning_stage=args.planning_stage,
        context=context,
    )
    output = Path(args.output).expanduser().resolve()
    write_generation(output, result)
    print(json.dumps({
        "ok": True,
        "output": str(output),
        "planning_brief_id": result["planning_brief"]["planning_brief_id"],
        "plan_scale": result["planning_brief"]["plan_scale"],
        "planning_stage": result["planning_brief"]["planning_stage"],
        "call_count": result["call_count"],
        "valid": result["final_validation"]["valid"],
    }, ensure_ascii=False, indent=2, sort_keys=True))
