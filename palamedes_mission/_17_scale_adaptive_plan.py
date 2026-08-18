from __future__ import annotations

from typing import Any, Dict, List

from ._01_kinds_value import _non_empty


LARGE_PLAN_SCALES = {"content", "service", "platform"}
PLAN_STAGES = {"direction", "concept", "approval", "delivery"}


def _unique_strings(value: Any) -> bool:
    return (
        isinstance(value, list)
        and all(_non_empty(item) for item in value)
        and len(value) == len(set(value))
    )


def validate_scale_adaptive_planning_brief(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require planning detail in proportion to consequence and decision maturity."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["planning brief must be an object"]}

    for field in (
        "planning_brief_id", "mission_contract_id", "mission_contract_fingerprint",
        "planning_brief_fingerprint", "outcome", "beneficiary", "value_proposition",
        "planning_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")

    scale = payload.get("plan_scale")
    if scale not in {"decision", "feature", *LARGE_PLAN_SCALES}:
        errors.append("plan_scale must be decision, feature, content, service, or platform")
    stage = payload.get("planning_stage")
    if stage not in PLAN_STAGES:
        errors.append("planning_stage must be direction, concept, approval, or delivery")

    resolution = payload.get("resolution_basis")
    if not isinstance(resolution, dict):
        errors.append("resolution_basis must be an object")
        resolution = {}
    for field in ("uncertainty", "irreversibility", "coordination_cost", "harm_potential"):
        if resolution.get(field) not in {"low", "medium", "high"}:
            errors.append(f"resolution_basis.{field} must be low, medium, or high")
    if not _non_empty(resolution.get("resolution_rationale")):
        errors.append("resolution_basis.resolution_rationale must be a non-empty string")

    for field in ("in_scope", "out_of_scope", "success_signals", "stop_conditions"):
        if not _unique_strings(payload.get(field)) or not payload.get(field):
            errors.append(f"{field} must be a non-empty unique string list")

    knowledge = payload.get("knowledge_ledger")
    if not isinstance(knowledge, list) or not knowledge:
        errors.append("knowledge_ledger must be a non-empty list")
        knowledge = []
    knowledge_ids = set()
    for index, item in enumerate(knowledge):
        prefix = f"knowledge_ledger[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        item_id = item.get("item_id")
        if not _non_empty(item_id) or item_id in knowledge_ids:
            errors.append(f"{prefix}.item_id must be a non-empty unique string")
        knowledge_ids.add(item_id)
        status = item.get("status")
        if status not in {"observed", "decided", "assumed", "unresolved"}:
            errors.append(f"{prefix}.status is not recognized")
        if not _non_empty(item.get("statement")):
            errors.append(f"{prefix}.statement must be a non-empty string")
        evidence_ids = item.get("evidence_ids")
        if not _unique_strings(evidence_ids):
            errors.append(f"{prefix}.evidence_ids must be a unique string list")
            evidence_ids = []
        if status in {"observed", "decided"} and not evidence_ids:
            errors.append(f"{prefix} observed or decided knowledge requires evidence")
        if status in {"assumed", "unresolved"} and not _non_empty(item.get("validation_probe")):
            errors.append(f"{prefix} assumed or unresolved knowledge requires a validation_probe")

    large_plan = scale in LARGE_PLAN_SCALES
    concept_required = large_plan and stage in {"concept", "approval", "delivery"}
    program_required = large_plan and stage in {"approval", "delivery"}

    experience = payload.get("experience_contract")
    if concept_required:
        if not isinstance(experience, dict):
            errors.append("large concept plans require experience_contract")
            experience = {}
        for field in ("context", "entry_state", "core_loop", "exit_state"):
            if not _non_empty(experience.get(field)):
                errors.append(f"experience_contract.{field} must be a non-empty string")
        if not _unique_strings(experience.get("experience_principles")) or not experience.get("experience_principles"):
            errors.append("experience_contract.experience_principles must be non-empty and unique")
    elif experience not in (None, {}):
        errors.append("experience_contract must be omitted until the concept stage")

    alternatives = payload.get("alternatives")
    if concept_required:
        if not isinstance(alternatives, list) or len(alternatives) < 2:
            errors.append("large concept plans require at least two alternatives")
            alternatives = []
        selected = [item for item in alternatives if isinstance(item, dict) and item.get("selected") is True]
        if len(selected) != 1:
            errors.append("alternatives must contain exactly one selected concept")
    elif alternatives not in (None, []):
        errors.append("alternatives must remain empty until the concept stage")

    components = payload.get("components")
    if concept_required and (not isinstance(components, list) or not components):
        errors.append("large concept plans require components")
        components = []
    elif not isinstance(components, list):
        components = []
    elif not concept_required and components:
        errors.append("components must remain empty until the concept stage")
    component_ids, provided, required = set(), set(), []
    for index, component in enumerate(components):
        prefix = f"components[{index}]"
        if not isinstance(component, dict):
            errors.append(f"{prefix} must be an object")
            continue
        component_id = component.get("component_id")
        if not _non_empty(component_id) or component_id in component_ids:
            errors.append(f"{prefix}.component_id must be a non-empty unique string")
        component_ids.add(component_id)
        for field in ("purpose", "kind"):
            if not _non_empty(component.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        for field in ("requires", "provides"):
            if not _unique_strings(component.get(field)):
                errors.append(f"{prefix}.{field} must be a unique string list")
        required.extend(component.get("requires", []))
        provided.update(component.get("provides", []))
        if component.get("maturity") not in {"existing", "adapt", "new", "unresolved"}:
            errors.append(f"{prefix}.maturity is not recognized")
    dependencies = payload.get("external_dependencies")
    if not _unique_strings(dependencies):
        errors.append("external_dependencies must be a unique string list")
        dependencies = []
    unresolved = set(required) - provided - set(dependencies)
    if unresolved:
        errors.append("component requirements lack a provider or external dependency: " + ", ".join(sorted(unresolved)))

    effects = payload.get("effects")
    if concept_required and (not isinstance(effects, list) or not effects):
        errors.append("large concept plans require an effect register")
        effects = []
    elif not isinstance(effects, list):
        errors.append("effects must be a list")
        effects = []
    irreversible = False
    for index, effect in enumerate(effects):
        prefix = f"effects[{index}]"
        if not isinstance(effect, dict):
            errors.append(f"{prefix} must be an object")
            continue
        reversibility = effect.get("reversibility")
        if reversibility not in {"reversible", "compensatable", "irreversible"}:
            errors.append(f"{prefix}.reversibility is not recognized")
        if not _non_empty(effect.get("effect_id")) or not _non_empty(effect.get("description")):
            errors.append(f"{prefix} requires effect_id and description")
        if reversibility == "reversible" and not _non_empty(effect.get("rollback")):
            errors.append(f"{prefix}.rollback is required for reversible effects")
        if reversibility == "compensatable" and not _non_empty(effect.get("compensation")):
            errors.append(f"{prefix}.compensation is required for compensatable effects")
        if reversibility == "irreversible":
            irreversible = True
            if effect.get("approval_required") is not True:
                errors.append(f"{prefix}.approval_required must be true for irreversible effects")

    phases = payload.get("phases")
    if program_required and (not isinstance(phases, list) or not phases):
        errors.append("large approval or delivery plans require phases")
        phases = []
    elif not isinstance(phases, list):
        phases = []
    phase_ids = set()
    for index, phase in enumerate(phases):
        prefix = f"phases[{index}]"
        if not isinstance(phase, dict):
            errors.append(f"{prefix} must be an object")
            continue
        phase_id = phase.get("phase_id")
        if not _non_empty(phase_id) or phase_id in phase_ids:
            errors.append(f"{prefix}.phase_id must be a non-empty unique string")
        phase_ids.add(phase_id)
        for field in ("objective", "entry_gate", "exit_gate"):
            if not _non_empty(phase.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if not _unique_strings(phase.get("component_ids")) or not phase.get("component_ids"):
            errors.append(f"{prefix}.component_ids must be non-empty and unique")
        elif not set(phase["component_ids"]).issubset(component_ids):
            errors.append(f"{prefix}.component_ids must reference declared components")
        if not _unique_strings(phase.get("outputs")) or not phase.get("outputs"):
            errors.append(f"{prefix}.outputs must be non-empty and unique")

    gates = payload.get("decision_gates")
    if not isinstance(gates, list) or not gates:
        errors.append("decision_gates must be a non-empty list")
        gates = []
    irreversible_gate = False
    for index, gate in enumerate(gates):
        prefix = f"decision_gates[{index}]"
        if not isinstance(gate, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("gate_id", "question", "evidence_required", "on_pass", "on_fail"):
            if not _non_empty(gate.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        irreversible_gate |= gate.get("authorizes_irreversible_effects") is True
    if irreversible and not irreversible_gate:
        errors.append("irreversible effects require an explicit authorizing decision gate")

    resources = payload.get("resource_envelope")
    if program_required:
        if not isinstance(resources, dict):
            errors.append("large approval or delivery plans require resource_envelope")
            resources = {}
        for field in ("people", "timebox", "budget", "critical_assets"):
            if not _non_empty(resources.get(field)):
                errors.append(f"resource_envelope.{field} must be non-empty")
    elif resources not in (None, {}):
        errors.append("resource_envelope must be omitted before approval planning")

    if payload.get("execution_authority_issued") is not False:
        errors.append("planning brief must not issue execution authority")
    if payload.get("mission_semantics_preserved") is not True:
        errors.append("mission_semantics_preserved must be true")

    return {
        "valid": not errors,
        "errors": errors,
        "plan_scale": scale,
        "planning_stage": stage,
        "required_resolution": "program" if program_required else "concept" if concept_required else "direction",
        "component_count": len(component_ids),
        "phase_count": len(phase_ids),
        "unresolved_component_requirements": sorted(unresolved),
        "irreversible_effect_present": irreversible,
    }
