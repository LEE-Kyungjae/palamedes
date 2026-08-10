from __future__ import annotations

from typing import Any, Dict, List
from ._01_kinds_value import _non_empty


def validate_plural_mission_horizons(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Compare missions across output, option creation, learning, and beneficiary change."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["plural mission horizons must be an object"]}
    for field in ("comparison_id", "normalization_id", "evaluation_window"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    forbidden = {"aggregate_score", "rank", "winner"} & set(payload)
    if forbidden:
        errors.append("plural mission horizons cannot contain " + ", ".join(sorted(forbidden)))
    required_dimensions = {
        "near_term_output",
        "option_creation",
        "learning",
        "beneficiary_change",
    }
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or len(candidates) < 3:
        errors.append("candidates must contain at least three normalized missions")
        candidates = []
    candidate_ids = set()
    for index, candidate in enumerate(candidates):
        prefix = f"candidates[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{prefix} must be an object")
            continue
        candidate_id = candidate.get("candidate_id")
        if not _non_empty(candidate_id):
            errors.append(f"{prefix}.candidate_id must be a non-empty string")
        elif candidate_id in candidate_ids:
            errors.append(f"{prefix}.candidate_id must be unique")
        else:
            candidate_ids.add(candidate_id)
        assessments = candidate.get("assessments")
        if not isinstance(assessments, list):
            errors.append(f"{prefix}.assessments must be an array")
            assessments = []
        seen_dimensions = set()
        for assessment_index, assessment in enumerate(assessments):
            assessment_prefix = f"{prefix}.assessments[{assessment_index}]"
            if not isinstance(assessment, dict):
                errors.append(f"{assessment_prefix} must be an object")
                continue
            dimension = assessment.get("dimension")
            if dimension not in required_dimensions:
                errors.append(
                    f"{assessment_prefix}.dimension must be one of "
                    f"{sorted(required_dimensions)}"
                )
            elif dimension in seen_dimensions:
                errors.append(f"{assessment_prefix}.dimension must be unique")
            else:
                seen_dimensions.add(dimension)
            for field in ("claim", "evidence_id", "uncertainty"):
                if not _non_empty(assessment.get(field)):
                    errors.append(f"{assessment_prefix}.{field} must be a non-empty string")
        missing = required_dimensions - seen_dimensions
        if missing:
            errors.append(f"{prefix}.assessments missing: " + ", ".join(sorted(missing)))
    return {"valid": not errors, "errors": errors}

def validate_early_causal_signal(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require an early observation that discriminates the mission's causal thesis."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["early causal signal must be an object"]}
    for field in (
        "signal_id",
        "candidate_id",
        "causal_thesis",
        "signal",
        "observation_window",
        "measurement",
        "expected_if_true",
        "expected_if_false",
        "why_unlikely_if_false",
        "decision_threshold",
        "action_if_absent",
        "baseline_source_id",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("signal_is_output_proxy") is not False:
        errors.append("signal_is_output_proxy must be false")
    if payload.get("absence_can_be_explained_away") is not False:
        errors.append("absence_can_be_explained_away must be false")
    if (
        _non_empty(payload.get("expected_if_true"))
        and payload.get("expected_if_true") == payload.get("expected_if_false")
    ):
        errors.append("expected_if_true and expected_if_false must differ")
    return {"valid": not errors, "errors": errors}

def validate_probability_downside_profile(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Preserve probability ranges and downside exposure without expected-value collapse."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["probability downside profile must be an object"]}
    for field in (
        "profile_id",
        "candidate_id",
        "upside_scenario",
        "probability_basis",
        "unknowns_outside_range",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    forbidden = {"expected_value", "risk_adjusted_score", "upside_probability_product"} & set(payload)
    if forbidden:
        errors.append(
            "probability downside profile cannot contain " + ", ".join(sorted(forbidden))
        )
    lower = payload.get("probability_lower")
    upper = payload.get("probability_upper")
    for field, value in (("probability_lower", lower), ("probability_upper", upper)):
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 100:
            errors.append(f"{field} must be an integer from 0 to 100")
    if isinstance(lower, int) and isinstance(upper, int) and lower >= upper:
        errors.append("probability_lower must be less than probability_upper")

    exposures = payload.get("downside_exposures")
    if not isinstance(exposures, list) or not exposures:
        errors.append("downside_exposures must be a non-empty array")
        exposures = []
    exposure_ids = set()
    for index, exposure in enumerate(exposures):
        prefix = f"downside_exposures[{index}]"
        if not isinstance(exposure, dict):
            errors.append(f"{prefix} must be an object")
            continue
        exposure_id = exposure.get("exposure_id")
        if not _non_empty(exposure_id):
            errors.append(f"{prefix}.exposure_id must be a non-empty string")
        elif exposure_id in exposure_ids:
            errors.append(f"{prefix}.exposure_id must be unique")
        else:
            exposure_ids.add(exposure_id)
        for field in (
            "affected_group_id",
            "harm",
            "severity",
            "reversibility",
            "mitigation",
            "source_id",
        ):
            if not _non_empty(exposure.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    return {"valid": not errors, "errors": errors, "downside_exposure_ids": sorted(exposure_ids)}

def validate_portfolio_capacity_allocation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Make finite execution and exploration budgets explicit."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["portfolio capacity allocation must be an object"]}
    for field in ("portfolio_id", "capacity_unit", "allocation_window"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("hidden_parallel_commitments_allowed") is not False:
        errors.append("hidden_parallel_commitments_allowed must be false")
    total_capacity = payload.get("total_capacity")
    reserve_capacity = payload.get("reserve_capacity")
    for field, value in (("total_capacity", total_capacity), ("reserve_capacity", reserve_capacity)):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            errors.append(f"{field} must be a non-negative integer")
    if (
        isinstance(total_capacity, int)
        and isinstance(reserve_capacity, int)
        and reserve_capacity > total_capacity
    ):
        errors.append("reserve_capacity cannot exceed total_capacity")

    allocations = payload.get("allocations")
    if not isinstance(allocations, list) or len(allocations) < 2:
        errors.append("allocations must contain at least two portfolio candidates")
        allocations = []
    candidate_ids = set()
    allocated_total = 0
    for index, allocation in enumerate(allocations):
        prefix = f"allocations[{index}]"
        if not isinstance(allocation, dict):
            errors.append(f"{prefix} must be an object")
            continue
        candidate_id = allocation.get("candidate_id")
        if not _non_empty(candidate_id):
            errors.append(f"{prefix}.candidate_id must be a non-empty string")
        elif candidate_id in candidate_ids:
            errors.append(f"{prefix}.candidate_id must be unique")
        else:
            candidate_ids.add(candidate_id)
        mode = allocation.get("mode")
        if mode not in {"explore", "commit", "hold"}:
            errors.append(f"{prefix}.mode must be explore, commit, or hold")
        amount = allocation.get("capacity")
        if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
            errors.append(f"{prefix}.capacity must be a non-negative integer")
        else:
            allocated_total += amount
            if mode in {"explore", "commit"} and amount == 0:
                errors.append(f"{prefix}.capacity must be positive for {mode}")
            if mode == "hold" and amount != 0:
                errors.append(f"{prefix}.capacity must be zero for hold")
        for field in ("scope", "stop_condition"):
            if not _non_empty(allocation.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    available = (
        total_capacity - reserve_capacity
        if isinstance(total_capacity, int) and isinstance(reserve_capacity, int)
        else None
    )
    if available is not None and allocated_total > available:
        errors.append("allocated capacity exceeds total_capacity minus reserve_capacity")
    return {
        "valid": not errors,
        "errors": errors,
        "allocated_capacity": allocated_total,
        "available_capacity": available,
    }

def validate_mission_enablement_sequence(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Represent directional mission enablement instead of isolated competition."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["mission enablement sequence must be an object"]}
    for field in ("sequence_id", "portfolio_id", "sequence_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    mission_ids = payload.get("mission_ids")
    if (
        not isinstance(mission_ids, list)
        or len(mission_ids) < 2
        or any(not _non_empty(item) for item in mission_ids)
    ):
        errors.append("mission_ids must contain at least two mission IDs")
        mission_ids = []
    elif len(set(mission_ids)) != len(mission_ids):
        errors.append("mission_ids must be unique")
    mission_id_set = set(mission_ids)

    edges = payload.get("enablement_edges")
    if not isinstance(edges, list) or not edges:
        errors.append("enablement_edges must be a non-empty array")
        edges = []
    edge_keys = set()
    graph = {mission_id: [] for mission_id in mission_ids}
    for index, edge in enumerate(edges):
        prefix = f"enablement_edges[{index}]"
        if not isinstance(edge, dict):
            errors.append(f"{prefix} must be an object")
            continue
        source = edge.get("from_mission_id")
        target = edge.get("to_mission_id")
        if source not in mission_id_set:
            errors.append(f"{prefix}.from_mission_id must reference mission_ids")
        if target not in mission_id_set:
            errors.append(f"{prefix}.to_mission_id must reference mission_ids")
        if source == target and source in mission_id_set:
            errors.append(f"{prefix} cannot self-enable")
        edge_key = (source, target)
        if edge_key in edge_keys:
            errors.append(f"{prefix} must be unique")
        edge_keys.add(edge_key)
        if source in graph and target in mission_id_set and source != target:
            graph[source].append(target)
        for field in (
            "enabled_capability_or_option",
            "counterfactual_without_predecessor",
            "evidence_id",
        ):
            if not _non_empty(edge.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")

    visiting = set()
    visited = set()

    def has_cycle(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(has_cycle(next_node) for next_node in graph.get(node, [])):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    if any(has_cycle(node) for node in mission_ids if node not in visited):
        errors.append("enablement_edges must form an acyclic sequence")
    return {"valid": not errors, "errors": errors, "edge_count": len(edge_keys)}

def validate_shared_asset_demand(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require independent credible mission demand before funding a shared asset."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["shared asset demand must be an object"]}
    for field in (
        "asset_id",
        "asset_capability",
        "bounded_build_scope",
        "capacity_cost",
        "asset_stop_condition",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("shared_asset_label_is_sufficient") is not False:
        errors.append("shared_asset_label_is_sufficient must be false")

    demands = payload.get("mission_demands")
    if not isinstance(demands, list) or len(demands) < 2:
        errors.append("mission_demands must contain at least two credible missions")
        demands = []
    mission_ids = set()
    assumption_hashes = set()
    for index, demand in enumerate(demands):
        prefix = f"mission_demands[{index}]"
        if not isinstance(demand, dict):
            errors.append(f"{prefix} must be an object")
            continue
        mission_id = demand.get("mission_id")
        if not _non_empty(mission_id):
            errors.append(f"{prefix}.mission_id must be a non-empty string")
        elif mission_id in mission_ids:
            errors.append(f"{prefix}.mission_id must be unique")
        else:
            mission_ids.add(mission_id)
        assumption_hash = demand.get("independent_assumption_hash")
        if not _non_empty(assumption_hash):
            errors.append(f"{prefix}.independent_assumption_hash must be a non-empty string")
        elif assumption_hash in assumption_hashes:
            errors.append(f"{prefix}.independent_assumption_hash must be distinct")
        else:
            assumption_hashes.add(assumption_hash)
        if demand.get("mission_credible") is not True:
            errors.append(f"{prefix}.mission_credible must be true")
        for field in (
            "credibility_evidence_id",
            "asset_need",
            "counterfactual_without_asset",
        ):
            if not _non_empty(demand.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    return {
        "valid": not errors,
        "errors": errors,
        "independent_demand_count": len(assumption_hashes),
    }

def validate_reversible_portfolio_selection(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Preserve runner-up missions and precommit reversal triggers."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["reversible portfolio selection must be an object"]}
    for field in (
        "selection_id",
        "portfolio_id",
        "primary_mission_id",
        "selected_scope",
        "selection_rationale",
        "review_window",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("option_landscape_erased") is not False:
        errors.append("option_landscape_erased must be false")

    runners = payload.get("runner_up_missions")
    if not isinstance(runners, list) or not runners:
        errors.append("runner_up_missions must be a non-empty array")
        runners = []
    runner_ids = set()
    for index, runner in enumerate(runners):
        prefix = f"runner_up_missions[{index}]"
        if not isinstance(runner, dict):
            errors.append(f"{prefix} must be an object")
            continue
        mission_id = runner.get("mission_id")
        if not _non_empty(mission_id):
            errors.append(f"{prefix}.mission_id must be a non-empty string")
        elif mission_id == payload.get("primary_mission_id"):
            errors.append(f"{prefix}.mission_id cannot equal primary_mission_id")
        elif mission_id in runner_ids:
            errors.append(f"{prefix}.mission_id must be unique")
        else:
            runner_ids.add(mission_id)
        for field in (
            "why_runner_up",
            "preserved_evidence_hash",
            "wake_trigger",
            "preservation_action",
        ):
            if not _non_empty(runner.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")

    triggers = payload.get("reversal_triggers")
    if not isinstance(triggers, list) or not triggers:
        errors.append("reversal_triggers must be a non-empty array")
        triggers = []
    trigger_ids = set()
    for index, trigger in enumerate(triggers):
        prefix = f"reversal_triggers[{index}]"
        if not isinstance(trigger, dict):
            errors.append(f"{prefix} must be an object")
            continue
        trigger_id = trigger.get("trigger_id")
        if not _non_empty(trigger_id):
            errors.append(f"{prefix}.trigger_id must be a non-empty string")
        elif trigger_id in trigger_ids:
            errors.append(f"{prefix}.trigger_id must be unique")
        else:
            trigger_ids.add(trigger_id)
        switch_to = trigger.get("switch_to_mission_id")
        if switch_to not in runner_ids:
            errors.append(f"{prefix}.switch_to_mission_id must reference a runner-up")
        for field in ("signal", "threshold", "reversal_action"):
            if not _non_empty(trigger.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    return {
        "valid": not errors,
        "errors": errors,
        "runner_up_ids": sorted(runner_ids),
        "reversal_trigger_ids": sorted(trigger_ids),
    }

def validate_selection_thesis_gate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Integrate independence, common pressure, budgets, and reversibility."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["selection thesis gate must be an object"]}
    for field in (
        "gate_id",
        "generation_batch_id",
        "normalization_id",
        "plural_comparison_id",
        "capacity_allocation_id",
        "reversible_selection_id",
        "gate_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    requirements = {
        "independent_formation_verified",
        "common_pressure_verified",
        "explicit_budget_verified",
        "reversibility_verified",
    }
    for requirement in sorted(requirements):
        if payload.get(requirement) is not True:
            errors.append(f"{requirement} must be true")
    if payload.get("single_winner_erases_portfolio") is not False:
        errors.append("single_winner_erases_portfolio must be false")
    decision = payload.get("gate_decision")
    if decision != "eligible":
        errors.append("gate_decision must be eligible")
    return {
        "valid": not errors,
        "errors": errors,
        "verified_requirement_count": sum(payload.get(item) is True for item in requirements),
    }

def validate_autonomous_authority_delegation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Define bounded domains, resources, affected parties, and reversibility."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["autonomous authority delegation must be an object"]}
    for field in (
        "authority_id",
        "constitution_id",
        "delegated_by",
        "valid_from",
        "valid_until",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    version = payload.get("constitution_version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        errors.append("constitution_version must be an integer >= 1")
    for field in ("delegated_domains", "forbidden_domains", "allowed_action_kinds"):
        values = payload.get(field)
        if (
            not isinstance(values, list)
            or not values
            or any(not _non_empty(item) for item in values)
        ):
            errors.append(f"{field} must be a non-empty string array")
    delegated = payload.get("delegated_domains")
    forbidden = payload.get("forbidden_domains")
    if isinstance(delegated, list) and isinstance(forbidden, list):
        overlap = set(delegated) & set(forbidden)
        if overlap:
            errors.append("delegated_domains and forbidden_domains cannot overlap")

    resources = payload.get("resource_envelopes")
    if not isinstance(resources, list) or not resources:
        errors.append("resource_envelopes must be a non-empty array")
        resources = []
    resource_ids = set()
    for index, resource in enumerate(resources):
        prefix = f"resource_envelopes[{index}]"
        if not isinstance(resource, dict):
            errors.append(f"{prefix} must be an object")
            continue
        resource_id = resource.get("resource_id")
        if not _non_empty(resource_id):
            errors.append(f"{prefix}.resource_id must be a non-empty string")
        elif resource_id in resource_ids:
            errors.append(f"{prefix}.resource_id must be unique")
        else:
            resource_ids.add(resource_id)
        if not _non_empty(resource.get("unit")):
            errors.append(f"{prefix}.unit must be a non-empty string")
        limit = resource.get("limit")
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 0:
            errors.append(f"{prefix}.limit must be a non-negative integer")

    parties = payload.get("affected_party_scope")
    if not isinstance(parties, list) or not parties:
        errors.append("affected_party_scope must be a non-empty array")
        parties = []
    for index, party in enumerate(parties):
        prefix = f"affected_party_scope[{index}]"
        if not isinstance(party, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("group_id", "allowed_effect", "excluded_effect"):
            if not _non_empty(party.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if payload.get("maximum_reversibility") not in {"reversible", "partially_reversible"}:
        errors.append("maximum_reversibility must be reversible or partially_reversible")
    escalation = payload.get("escalation_conditions")
    if (
        not isinstance(escalation, list)
        or not escalation
        or any(not _non_empty(item) for item in escalation)
    ):
        errors.append("escalation_conditions must be a non-empty string array")
    return {"valid": not errors, "errors": errors, "resource_ids": sorted(resource_ids)}

def validate_consequence_class_authority(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Bound authority by reputational, privacy, relational, and strategic consequences."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["consequence class authority must be an object"]}
    for field in ("policy_id", "authority_id", "default_unclassified_action"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("numeric_limit_is_sufficient") is not False:
        errors.append("numeric_limit_is_sufficient must be false")
    required_classes = {"reputational", "privacy", "relational", "strategic"}
    rules = payload.get("consequence_classes")
    if not isinstance(rules, list) or len(rules) != len(required_classes):
        errors.append("consequence_classes must contain exactly four required classes")
        rules = []
    seen_classes = set()
    for index, rule in enumerate(rules):
        prefix = f"consequence_classes[{index}]"
        if not isinstance(rule, dict):
            errors.append(f"{prefix} must be an object")
            continue
        consequence_class = rule.get("class")
        if consequence_class not in required_classes:
            errors.append(f"{prefix}.class must be one of {sorted(required_classes)}")
        elif consequence_class in seen_classes:
            errors.append(f"{prefix}.class must be unique")
        else:
            seen_classes.add(consequence_class)
        if rule.get("authority") not in {"autonomous", "escalate", "prohibited"}:
            errors.append(f"{prefix}.authority must be autonomous, escalate, or prohibited")
        for field in ("boundary", "example", "detection"):
            if not _non_empty(rule.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    missing = required_classes - seen_classes
    if missing:
        errors.append("consequence_classes missing: " + ", ".join(sorted(missing)))
    if payload.get("default_unclassified_action") != "escalate":
        errors.append("default_unclassified_action must be escalate")
    return {"valid": not errors, "errors": errors, "classes": sorted(seen_classes)}

def validate_analogical_authority_precedent(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Classify a novel action by precedent while exposing analogy weakness."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["analogical authority precedent must be an object"]}
    for field in (
        "reasoning_id",
        "authority_id",
        "novel_action",
        "why_unclassified",
        "inferred_consequence_class",
        "analogy_limit",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    strength = payload.get("analogy_strength")
    if strength not in {"weak", "moderate", "strong"}:
        errors.append("analogy_strength must be weak, moderate, or strong")
    confidence = payload.get("confidence")
    if not isinstance(confidence, int) or isinstance(confidence, bool) or not 0 <= confidence <= 100:
        errors.append("confidence must be an integer from 0 to 100")
    if strength == "weak" and isinstance(confidence, int) and confidence > 40:
        errors.append("weak analogy confidence cannot exceed 40")
    decision = payload.get("authority_decision")
    if decision not in {"within_authority", "outside_authority", "uncertain"}:
        errors.append("authority_decision must be within_authority, outside_authority, or uncertain")
    if strength == "weak" and decision == "within_authority":
        errors.append("weak analogy cannot establish within_authority")

    precedents = payload.get("precedents")
    if not isinstance(precedents, list) or not precedents:
        errors.append("precedents must be a non-empty array")
        precedents = []
    precedent_ids = set()
    for index, precedent in enumerate(precedents):
        prefix = f"precedents[{index}]"
        if not isinstance(precedent, dict):
            errors.append(f"{prefix} must be an object")
            continue
        precedent_id = precedent.get("precedent_id")
        if not _non_empty(precedent_id):
            errors.append(f"{prefix}.precedent_id must be a non-empty string")
        elif precedent_id in precedent_ids:
            errors.append(f"{prefix}.precedent_id must be unique")
        else:
            precedent_ids.add(precedent_id)
        for field in (
            "prior_action",
            "prior_authority_decision",
            "material_similarity",
            "material_difference",
            "source_id",
        ):
            if not _non_empty(precedent.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    return {"valid": not errors, "errors": errors, "precedent_ids": sorted(precedent_ids)}

def validate_authority_sandbox_probe(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve weak authority analogy through an isolated, consequence-free probe."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["authority sandbox probe must be an object"]}
    for field in (
        "probe_id",
        "reasoning_id",
        "simulated_action",
        "sandbox_boundary",
        "synthetic_inputs",
        "observation",
        "analogy_update_rule",
        "rollback",
        "stop_condition",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    for field in (
        "external_communication",
        "real_affected_parties",
        "persistent_external_effect",
        "creates_commitment",
    ):
        if payload.get(field) is not False:
            errors.append(f"{field} must be false")
    if payload.get("reversible") is not True:
        errors.append("reversible must be true")
    resource_limit = payload.get("resource_limit")
    if not isinstance(resource_limit, int) or isinstance(resource_limit, bool) or resource_limit < 0:
        errors.append("resource_limit must be a non-negative integer")
    if not _non_empty(payload.get("resource_unit")):
        errors.append("resource_unit must be a non-empty string")
    outcomes = payload.get("distinguishing_outcomes")
    if (
        not isinstance(outcomes, list)
        or len(outcomes) < 2
        or any(not _non_empty(item) for item in outcomes)
    ):
        errors.append("distinguishing_outcomes must contain at least two outcomes")
    return {"valid": not errors, "errors": errors}

def validate_communication_representation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Keep drafts private and require delegated representation for publication."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["communication representation must be an object"]}
    for field in ("communication_id", "content_hash", "content_purpose"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    state = payload.get("state")
    if state not in {"simulation", "private_draft", "publication"}:
        errors.append("state must be simulation, private_draft, or publication")
    external_visibility = payload.get("external_visibility")
    if not isinstance(external_visibility, bool):
        errors.append("external_visibility must be boolean")
    if state in {"simulation", "private_draft"} and external_visibility is not False:
        errors.append(f"{state} external_visibility must be false")
    if state == "publication" and external_visibility is not True:
        errors.append("publication external_visibility must be true")

    delegation = payload.get("representation_delegation")
    if state == "publication":
        if not isinstance(delegation, dict):
            errors.append("publication requires representation_delegation")
            delegation = {}
        for field in (
            "delegation_id",
            "principal",
            "audience",
            "channel",
            "permitted_topic",
            "valid_until",
            "retraction_mechanism",
        ):
            if not _non_empty(delegation.get(field)):
                errors.append(
                    f"representation_delegation.{field} must be a non-empty string"
                )
        if delegation.get("content_hash") != payload.get("content_hash"):
            errors.append("representation_delegation.content_hash must match communication")
    elif delegation not in (None, {}):
        errors.append(f"{state} must not claim representation delegation")
    return {"valid": not errors, "errors": errors, "state": state}

def validate_downstream_agent_scope(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Prevent downstream agents from expanding mission or authority scope."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["downstream agent scope must be an object"]}
    for field in (
        "delegation_id",
        "parent_mission_id",
        "parent_authority_id",
        "agent_id",
        "mission_scope_hash",
        "assigned_outcome",
        "resource_slice",
        "valid_until",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    for field in ("allowed_decisions", "forbidden_actions", "return_required_changes"):
        values = payload.get(field)
        if (
            not isinstance(values, list)
            or not values
            or any(not _non_empty(item) for item in values)
        ):
            errors.append(f"{field} must be a non-empty string array")
    required_returns = {
        "mission_thesis",
        "beneficiary_scope",
        "constitution_or_authority",
        "resource_increase",
        "external_publication",
    }
    returns = payload.get("return_required_changes")
    if isinstance(returns, list):
        missing = required_returns - set(returns)
        if missing:
            errors.append("return_required_changes missing: " + ", ".join(sorted(missing)))
    if payload.get("may_redelegate") is not False:
        errors.append("may_redelegate must be false")
    if payload.get("scope_expansion_allowed") is not False:
        errors.append("scope_expansion_allowed must be false")
    return {"valid": not errors, "errors": errors}

def validate_disconfirmation_stop_authority(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Let pre-registered disconfirmation stop a mission despite sunk cost."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["disconfirmation stop authority must be an object"]}
    for field in (
        "stop_evaluation_id",
        "mission_id",
        "authority_id",
        "disconfirmation_id",
        "pre_registered_condition",
        "observed_evidence",
        "threshold",
        "evidence_source_id",
        "stop_rationale",
        "preservation_action",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("threshold_met") is not True:
        errors.append("threshold_met must be true")
    if payload.get("sunk_cost_can_override") is not False:
        errors.append("sunk_cost_can_override must be false")
    if payload.get("decision") != "stop":
        errors.append("decision must be stop when pre-registered threshold is met")
    actions = payload.get("stop_actions")
    if (
        not isinstance(actions, list)
        or not actions
        or any(not _non_empty(item) for item in actions)
    ):
        errors.append("stop_actions must be a non-empty string array")
    required_actions = {"freeze_resources", "revoke_downstream_delegations"}
    if isinstance(actions, list):
        missing = required_actions - set(actions)
        if missing:
            errors.append("stop_actions missing: " + ", ".join(sorted(missing)))
    return {"valid": not errors, "errors": errors}

def validate_stop_failure_diagnosis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Distinguish thesis, execution, delay, and measurement failure before stopping."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["stop failure diagnosis must be an object"]}
    for field in (
        "diagnosis_id",
        "mission_id",
        "signal_id",
        "observed_deviation",
        "selected_diagnosis_rationale",
        "next_action",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    required_types = {
        "thesis_failure",
        "execution_failure",
        "delayed_signal",
        "measurement_failure",
    }
    diagnoses = payload.get("candidate_diagnoses")
    if not isinstance(diagnoses, list) or len(diagnoses) != 4:
        errors.append("candidate_diagnoses must contain exactly four failure types")
        diagnoses = []
    seen_types = set()
    for index, diagnosis in enumerate(diagnoses):
        prefix = f"candidate_diagnoses[{index}]"
        if not isinstance(diagnosis, dict):
            errors.append(f"{prefix} must be an object")
            continue
        diagnosis_type = diagnosis.get("type")
        if diagnosis_type not in required_types:
            errors.append(f"{prefix}.type must be one of {sorted(required_types)}")
        elif diagnosis_type in seen_types:
            errors.append(f"{prefix}.type must be unique")
        else:
            seen_types.add(diagnosis_type)
        for field in ("plausibility", "evidence", "discriminator"):
            if not _non_empty(diagnosis.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    missing = required_types - seen_types
    if missing:
        errors.append("candidate_diagnoses missing: " + ", ".join(sorted(missing)))
    selected = payload.get("selected_diagnosis")
    if selected not in required_types:
        errors.append(f"selected_diagnosis must be one of {sorted(required_types)}")
    decision = payload.get("decision")
    expected_decisions = {
        "thesis_failure": "stop",
        "execution_failure": "remediate_execution",
        "delayed_signal": "wait_for_signal",
        "measurement_failure": "repair_measurement",
    }
    if selected in expected_decisions and decision != expected_decisions[selected]:
        errors.append(f"{selected} requires decision {expected_decisions[selected]}")
    confidence = payload.get("confidence")
    if not isinstance(confidence, int) or isinstance(confidence, bool) or not 0 <= confidence <= 100:
        errors.append("confidence must be an integer from 0 to 100")
    return {"valid": not errors, "errors": errors, "selected_diagnosis": selected}

def validate_consequential_action_lineage(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Attach constitutional, evidential, reversible, and agent lineage to an action."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["consequential action lineage must be an object"]}
    for field in (
        "action_id",
        "mission_id",
        "accountable_agent_id",
        "agent_delegation_id",
        "authority_decision_id",
        "action",
        "timestamp",
        "evidence_as_of",
        "rollback_or_recovery",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("consequential") is not True:
        errors.append("consequential must be true")
    for field in ("constitution_clause_ids", "evidence_state_ids", "consequence_classes"):
        values = payload.get(field)
        if (
            not isinstance(values, list)
            or not values
            or any(not _non_empty(item) for item in values)
        ):
            errors.append(f"{field} must be a non-empty ID array")
    if payload.get("reversibility") not in {
        "reversible",
        "partially_reversible",
        "irreversible",
    }:
        errors.append(
            "reversibility must be reversible, partially_reversible, or irreversible"
        )
    confidence = payload.get("evidence_confidence")
    if not isinstance(confidence, int) or isinstance(confidence, bool) or not 0 <= confidence <= 100:
        errors.append("evidence_confidence must be an integer from 0 to 100")
    if payload.get("reversibility") == "irreversible" and not _non_empty(
        payload.get("irreversible_authorization_id")
    ):
        errors.append("irreversible action requires irreversible_authorization_id")
    return {"valid": not errors, "errors": errors}

def validate_authority_thesis_gate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Act within consequence bounds, probe ambiguity, escalate only ungranted power."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["authority thesis gate must be an object"]}
    for field in (
        "gate_id",
        "authority_id",
        "consequence_policy_id",
        "action_lineage_id",
        "decision_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    decision = payload.get("decision")
    if decision not in {"act", "sandbox_probe", "escalate"}:
        errors.append("decision must be act, sandbox_probe, or escalate")
    for field in (
        "bounded_delegation_verified",
        "consequence_classified",
        "action_lineage_ready",
        "authority_ambiguous",
        "safe_probe_available",
        "genuinely_ungranted_power",
    ):
        if not isinstance(payload.get(field), bool):
            errors.append(f"{field} must be boolean")
    if decision == "act":
        for field in (
            "bounded_delegation_verified",
            "consequence_classified",
            "action_lineage_ready",
        ):
            if payload.get(field) is not True:
                errors.append(f"act requires {field}")
        if payload.get("authority_ambiguous") is not False:
            errors.append("act requires authority_ambiguous false")
        if payload.get("genuinely_ungranted_power") is not False:
            errors.append("act cannot use genuinely ungranted power")
    if decision == "sandbox_probe":
        if payload.get("authority_ambiguous") is not True:
            errors.append("sandbox_probe requires authority_ambiguous true")
        if payload.get("safe_probe_available") is not True:
            errors.append("sandbox_probe requires safe_probe_available true")
        if not _non_empty(payload.get("sandbox_probe_id")):
            errors.append("sandbox_probe requires sandbox_probe_id")
    if decision == "escalate":
        if payload.get("genuinely_ungranted_power") is not True:
            errors.append("escalate requires genuinely_ungranted_power true")
        if payload.get("safe_probe_available") is not False:
            errors.append("escalate requires safe_probe_available false")
        if not _non_empty(payload.get("escalation_reason")):
            errors.append("escalate requires escalation_reason")
    return {"valid": not errors, "errors": errors, "decision": decision}

def validate_agent_self_benefit_conflict(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Treat agent resource, authority, persistence, or relevance gains as conflicts."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["agent self-benefit conflict must be an object"]}
    for field in (
        "conflict_id",
        "candidate_id",
        "external_beneficiary_change",
        "counterfactual_without_self_benefit",
        "conflict_mitigation",
        "independent_comparison_id",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("self_benefit_counts_as_mission_value") is not False:
        errors.append("self_benefit_counts_as_mission_value must be false")
    if payload.get("selection_uses_self_benefit") is not False:
        errors.append("selection_uses_self_benefit must be false")
    benefits = payload.get("agent_self_benefits")
    allowed_kinds = {"resources", "authority", "persistence", "relevance"}
    if not isinstance(benefits, list) or not benefits:
        errors.append("agent_self_benefits must be a non-empty array")
        benefits = []
    seen_kinds = set()
    for index, benefit in enumerate(benefits):
        prefix = f"agent_self_benefits[{index}]"
        if not isinstance(benefit, dict):
            errors.append(f"{prefix} must be an object")
            continue
        kind = benefit.get("kind")
        if kind not in allowed_kinds:
            errors.append(f"{prefix}.kind must be one of {sorted(allowed_kinds)}")
        elif kind in seen_kinds:
            errors.append(f"{prefix}.kind must be unique")
        else:
            seen_kinds.add(kind)
        for field in ("benefit", "conflict_path"):
            if not _non_empty(benefit.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    evidence_ids = payload.get("external_beneficiary_evidence_ids")
    if (
        not isinstance(evidence_ids, list)
        or not evidence_ids
        or any(not _non_empty(item) for item in evidence_ids)
    ):
        errors.append("external_beneficiary_evidence_ids must be a non-empty ID array")
    return {"valid": not errors, "errors": errors, "self_benefit_kinds": sorted(seen_kinds)}

def validate_externally_bounded_self_improvement(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Allow self-improvement only as a bounded dependency of an external mission."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["bounded self-improvement must be an object"]}
    for field in (
        "improvement_id",
        "external_mission_id",
        "external_beneficiary_group_id",
        "capability_change",
        "mission_dependency",
        "counterfactual_without_improvement",
        "independent_bound_id",
        "independent_bound_owner",
        "scope",
        "valid_until",
        "rollback",
        "success_signal",
        "stop_condition",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("self_improvement_is_independent_mission") is not False:
        errors.append("self_improvement_is_independent_mission must be false")
    if payload.get("may_expand_authority") is not False:
        errors.append("may_expand_authority must be false")
    evidence_ids = payload.get("external_beneficiary_evidence_ids")
    if (
        not isinstance(evidence_ids, list)
        or not evidence_ids
        or any(not _non_empty(item) for item in evidence_ids)
    ):
        errors.append("external_beneficiary_evidence_ids must be a non-empty ID array")
    resource_limit = payload.get("resource_limit")
    if not isinstance(resource_limit, int) or isinstance(resource_limit, bool) or resource_limit < 0:
        errors.append("resource_limit must be a non-negative integer")
    if not _non_empty(payload.get("resource_unit")):
        errors.append("resource_unit must be a non-empty string")
    return {"valid": not errors, "errors": errors}

