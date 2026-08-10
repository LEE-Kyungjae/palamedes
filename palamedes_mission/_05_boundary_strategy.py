from __future__ import annotations

from typing import Any, Dict, List
from ._01_kinds_value import _non_empty


def validate_planner_boundary_return(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Type planner discoveries that may cross back over the mission boundary."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["planner boundary return must be an object"]}
    for field in (
        "return_id",
        "mission_contract_id",
        "mission_contract_version",
        "planner_id",
        "discovery",
        "evidence_id",
        "affected_contract_field",
        "requested_response",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("planner_unilaterally_revised_mission") is not False:
        errors.append("planner_unilaterally_revised_mission must be false")
    kind = payload.get("return_kind")
    if kind not in {"constraint_update", "thesis_challenge", "execution_alternative"}:
        errors.append("return_kind must be constraint_update, thesis_challenge, or execution_alternative")

    details = payload.get("typed_details")
    if not isinstance(details, dict):
        errors.append("typed_details must be an object")
        details = {}
    if kind == "constraint_update":
        for field in ("constraint", "feasibility_effect", "scope"):
            if not _non_empty(details.get(field)):
                errors.append(f"constraint_update requires typed_details.{field}")
    elif kind == "thesis_challenge":
        for field in ("challenged_claim_id", "contradicting_observation", "withdrawal_condition"):
            if not _non_empty(details.get(field)):
                errors.append(f"thesis_challenge requires typed_details.{field}")
    elif kind == "execution_alternative":
        for field in ("alternative", "comparative_advantage", "meaning_preservation_test"):
            if not _non_empty(details.get(field)):
                errors.append(f"execution_alternative requires typed_details.{field}")
        if not isinstance(details.get("mission_meaning_preserved"), bool):
            errors.append("execution_alternative requires typed_details.mission_meaning_preserved boolean")

    return {
        "valid": not errors,
        "errors": errors,
        "return_kind": kind,
    }

def validate_constraint_reframing_review(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Test whether a planner constraint reveals a better beneficiary or mechanism."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["constraint reframing review must be an object"]}
    for field in (
        "review_id",
        "planner_return_id",
        "constraint",
        "constraint_evidence_id",
        "original_beneficiary",
        "original_mechanism",
        "alternative_beneficiary",
        "alternative_mechanism",
        "comparison_evidence_id",
        "comparison_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("constraint_treated_as_resistance_by_default") is not False:
        errors.append("constraint_treated_as_resistance_by_default must be false")
    alternative_better = payload.get("alternative_mission_better")
    if not isinstance(alternative_better, bool):
        errors.append("alternative_mission_better must be boolean")
    if not isinstance(payload.get("planning_paused"), bool):
        errors.append("planning_paused must be boolean")
    comparison_dimensions = payload.get("comparison_dimensions")
    required_dimensions = {"beneficiary_change", "causal_defensibility", "constitutional_fit"}
    if (
        not isinstance(comparison_dimensions, list)
        or set(comparison_dimensions) != required_dimensions
        or len(comparison_dimensions) != len(required_dimensions)
    ):
        errors.append("comparison_dimensions must cover beneficiary_change, causal_defensibility, and constitutional_fit")
    decision = payload.get("decision")
    if decision not in {"continue_planning", "reopen_mission_selection"}:
        errors.append("decision must be continue_planning or reopen_mission_selection")
    if alternative_better is True:
        if decision != "reopen_mission_selection":
            errors.append("better alternative mission requires reopening mission selection")
        if payload.get("planning_paused") is not True:
            errors.append("better alternative mission requires planning_paused true")
    if alternative_better is False and decision == "reopen_mission_selection":
        errors.append("reopen_mission_selection requires a better alternative mission")

    return {
        "valid": not errors,
        "errors": errors,
        "decision": decision,
    }

def validate_strategy_meaning_invariants(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Prevent feasibility optimization from erasing beneficiary meaning or non-goals."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["strategy meaning invariants must be an object"]}
    for field in (
        "review_id",
        "mission_contract_id",
        "mission_contract_version",
        "strategy_proposal_id",
        "original_beneficiary_condition",
        "strategy_beneficiary_condition",
        "review_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("feasibility_may_override_meaning") is not False:
        errors.append("feasibility_may_override_meaning must be false")
    original_non_goals = payload.get("original_non_goals")
    preserved_non_goals = payload.get("strategy_preserved_non_goals")
    if (
        not isinstance(original_non_goals, list)
        or not original_non_goals
        or not all(_non_empty(item) for item in original_non_goals)
    ):
        errors.append("original_non_goals must be a non-empty list of strings")
        original_non_goals = []
    if not isinstance(preserved_non_goals, list) or not all(_non_empty(item) for item in preserved_non_goals):
        errors.append("strategy_preserved_non_goals must be a list of strings")
        preserved_non_goals = []

    beneficiary_changed = (
        payload.get("original_beneficiary_condition")
        != payload.get("strategy_beneficiary_condition")
    )
    missing_non_goals = sorted(set(original_non_goals) - set(preserved_non_goals))
    meaning_changed = beneficiary_changed or bool(missing_non_goals)
    revision = payload.get("explicit_mission_revision")
    if not isinstance(revision, bool):
        errors.append("explicit_mission_revision must be boolean")
    decision = payload.get("decision")
    if decision not in {"accept_strategy", "return_for_mission_revision"}:
        errors.append("decision must be accept_strategy or return_for_mission_revision")
    if meaning_changed and revision is not True and decision != "return_for_mission_revision":
        errors.append("meaning drift without explicit revision must return for mission revision")
    if not meaning_changed and decision == "return_for_mission_revision":
        errors.append("unchanged meaning does not require mission revision")
    if revision is True:
        for field in ("mission_revision_id", "revision_reason"):
            if not _non_empty(payload.get(field)):
                errors.append(f"explicit mission revision requires {field}")
    elif payload.get("mission_revision_id") not in ("", None):
        errors.append("mission_revision_id requires explicit_mission_revision true")

    return {
        "valid": not errors,
        "errors": errors,
        "beneficiary_changed": beneficiary_changed,
        "missing_non_goals": missing_non_goals,
        "decision": decision,
    }

def validate_downstream_mission_status(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Report delivery, retired uncertainty, and observed consequence together."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["downstream mission status must be an object"]}
    for field in (
        "status_id",
        "mission_contract_id",
        "mission_contract_version",
        "planner_id",
        "delivery_summary",
        "delivery_evidence_id",
        "next_observation",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("delivery_status") not in {"not_started", "in_progress", "completed", "blocked"}:
        errors.append("delivery_status is not recognized")
    if payload.get("delivery_completion_substitutes_for_outcome") is not False:
        errors.append("delivery_completion_substitutes_for_outcome must be false")

    uncertainties = payload.get("uncertainty_updates")
    if not isinstance(uncertainties, list) or not uncertainties:
        errors.append("uncertainty_updates must be a non-empty list")
        uncertainties = []
    retired_count = 0
    for index, uncertainty in enumerate(uncertainties):
        prefix = f"uncertainty_updates[{index}]"
        if not isinstance(uncertainty, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("uncertainty_id", "question", "observation", "evidence_id"):
            if not _non_empty(uncertainty.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        status = uncertainty.get("status")
        if status not in {"retired", "reduced", "unchanged", "expanded"}:
            errors.append(f"{prefix}.status is not recognized")
        elif status == "retired":
            retired_count += 1
    if retired_count == 0:
        errors.append("uncertainty_updates must identify at least one retired uncertainty")

    consequences = payload.get("observed_consequences")
    if not isinstance(consequences, list) or not consequences:
        errors.append("observed_consequences must be a non-empty list")
        consequences = []
    for index, consequence in enumerate(consequences):
        prefix = f"observed_consequences[{index}]"
        if not isinstance(consequence, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if consequence.get("kind") not in {"benefit", "harm", "neutral", "uncertain"}:
            errors.append(f"{prefix}.kind is not recognized")
        for field in (
            "consequence_id",
            "affected_party",
            "observation",
            "observed_at",
            "evidence_id",
        ):
            if not _non_empty(consequence.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")

    return {
        "valid": not errors,
        "errors": errors,
        "retired_uncertainty_count": retired_count,
        "observed_consequence_count": len(consequences),
    }

def validate_strategy_conflict_jurisdiction(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Keep technical strategy conflicts downstream unless mission meaning changes."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["strategy conflict jurisdiction must be an object"]}
    for field in (
        "jurisdiction_review_id",
        "mission_contract_id",
        "mission_contract_version",
        "conflict_summary",
        "jurisdiction_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("palamedes_arbitrates_technical_tradeoffs") is not False:
        errors.append("palamedes_arbitrates_technical_tradeoffs must be false")
    proposals = payload.get("planner_proposal_ids")
    if not isinstance(proposals, list) or len(proposals) < 2 or not all(_non_empty(item) for item in proposals):
        errors.append("planner_proposal_ids must contain at least two proposal IDs")

    conflicts = payload.get("conflict_dimensions")
    if not isinstance(conflicts, list) or not conflicts:
        errors.append("conflict_dimensions must be a non-empty list")
        conflicts = []
    conflict_ids = set()
    purpose_conflicts = []
    technical_conflicts = []
    for index, conflict in enumerate(conflicts):
        prefix = f"conflict_dimensions[{index}]"
        if not isinstance(conflict, dict):
            errors.append(f"{prefix} must be an object")
            continue
        conflict_id = conflict.get("conflict_id")
        if not _non_empty(conflict_id):
            errors.append(f"{prefix}.conflict_id must be a non-empty string")
        elif conflict_id in conflict_ids:
            errors.append(f"{prefix}.conflict_id must be unique")
        else:
            conflict_ids.add(conflict_id)
        kind = conflict.get("kind")
        if kind not in {"purpose", "technical"}:
            errors.append(f"{prefix}.kind must be purpose or technical")
        elif kind == "purpose":
            purpose_conflicts.append(conflict_id)
        else:
            technical_conflicts.append(conflict_id)
        for field in ("dimension", "difference", "evidence_id", "boundary_test"):
            if not _non_empty(conflict.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")

    jurisdiction = payload.get("jurisdiction")
    if jurisdiction not in {"palamedes_purpose_review", "downstream_strategy_resolution"}:
        errors.append("jurisdiction is not recognized")
    expected_jurisdiction = (
        "palamedes_purpose_review"
        if purpose_conflicts
        else "downstream_strategy_resolution"
    )
    if conflicts and jurisdiction != expected_jurisdiction:
        errors.append("jurisdiction must follow whether any conflict changes mission meaning")

    return {
        "valid": not errors,
        "errors": errors,
        "jurisdiction": jurisdiction,
        "purpose_conflicts": purpose_conflicts,
        "technical_conflicts": technical_conflicts,
    }

def validate_cumulative_plan_failure_boundary(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require cumulative independent plan failures before challenging feasibility."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["cumulative plan failure boundary must be an object"]}
    for field in (
        "review_id",
        "mission_contract_id",
        "mission_contract_version",
        "feasibility_assumption_id",
        "feasibility_assumption",
        "decision_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("single_failure_disconfirms_mission") is not False:
        errors.append("single_failure_disconfirms_mission must be false")
    threshold = payload.get("pre_registered_failure_threshold")
    family_threshold = payload.get("minimum_distinct_strategy_families")
    if not isinstance(threshold, int) or isinstance(threshold, bool) or threshold < 2:
        errors.append("pre_registered_failure_threshold must be an integer of at least two")
    if not isinstance(family_threshold, int) or isinstance(family_threshold, bool) or family_threshold < 2:
        errors.append("minimum_distinct_strategy_families must be an integer of at least two")

    attempts = payload.get("plan_attempts")
    if not isinstance(attempts, list) or not attempts:
        errors.append("plan_attempts must be a non-empty list")
        attempts = []
    attempt_ids = set()
    qualifying_attempts = []
    families = set()
    for index, attempt in enumerate(attempts):
        prefix = f"plan_attempts[{index}]"
        if not isinstance(attempt, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in (
            "attempt_id",
            "strategy_family",
            "failure_observation",
            "failure_evidence_id",
            "feasibility_assumption_id",
        ):
            if not _non_empty(attempt.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        attempt_id = attempt.get("attempt_id")
        if _non_empty(attempt_id):
            if attempt_id in attempt_ids:
                errors.append(f"{prefix}.attempt_id must be unique")
            attempt_ids.add(attempt_id)
        if not isinstance(attempt.get("execution_adequate"), bool):
            errors.append(f"{prefix}.execution_adequate must be boolean")
        if not isinstance(attempt.get("assumption_implicated"), bool):
            errors.append(f"{prefix}.assumption_implicated must be boolean")
        if (
            attempt.get("execution_adequate") is True
            and attempt.get("assumption_implicated") is True
            and attempt.get("feasibility_assumption_id") == payload.get("feasibility_assumption_id")
        ):
            qualifying_attempts.append(attempt_id)
            if _non_empty(attempt.get("strategy_family")):
                families.add(attempt.get("strategy_family"))

    crossed = (
        isinstance(threshold, int)
        and isinstance(family_threshold, int)
        and len(qualifying_attempts) >= threshold
        and len(families) >= family_threshold
    )
    decision = payload.get("decision")
    if decision not in {"replan", "challenge_mission_feasibility"}:
        errors.append("decision must be replan or challenge_mission_feasibility")
    elif crossed and decision != "challenge_mission_feasibility":
        errors.append("crossed cumulative boundary requires mission feasibility challenge")
    elif not crossed and decision != "replan":
        errors.append("mission feasibility challenge requires the cumulative boundary")

    return {
        "valid": not errors,
        "errors": errors,
        "qualifying_failure_count": len(qualifying_attempts),
        "distinct_strategy_family_count": len(families),
        "boundary_crossed": crossed,
        "decision": decision,
    }

def validate_mission_revision_invalidation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Version mission revisions and notify every downstream dependency."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["mission revision invalidation must be an object"]}
    for field in (
        "revision_id",
        "mission_id",
        "predecessor_contract_id",
        "predecessor_version",
        "successor_contract_id",
        "successor_version",
        "revision_evidence_id",
        "revision_summary",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if (
        payload.get("predecessor_contract_id") == payload.get("successor_contract_id")
        and payload.get("predecessor_version") == payload.get("successor_version")
    ):
        errors.append("successor contract identity or version must differ from predecessor")
    if payload.get("predecessor_immutable") is not True:
        errors.append("predecessor_immutable must be true")
    if payload.get("silent_plan_drift") is not False:
        errors.append("silent_plan_drift must be false")
    reasons = payload.get("revision_reasons")
    if not isinstance(reasons, list) or not reasons or not all(_non_empty(item) for item in reasons):
        errors.append("revision_reasons must be a non-empty list of strings")
    changed_fields = payload.get("changed_fields")
    if not isinstance(changed_fields, list) or not changed_fields or not all(_non_empty(item) for item in changed_fields):
        errors.append("changed_fields must be a non-empty list of strings")

    dependencies = payload.get("downstream_dependencies")
    if not isinstance(dependencies, list) or not dependencies:
        errors.append("downstream_dependencies must be a non-empty list")
        dependencies = []
    dependency_ids = set()
    invalidated_count = 0
    for index, dependency in enumerate(dependencies):
        prefix = f"downstream_dependencies[{index}]"
        if not isinstance(dependency, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in (
            "artifact_id",
            "artifact_kind",
            "depended_on_version",
            "disposition",
            "invalidation_notice_id",
            "notice_reason",
        ):
            if not _non_empty(dependency.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        artifact_id = dependency.get("artifact_id")
        if _non_empty(artifact_id):
            if artifact_id in dependency_ids:
                errors.append(f"{prefix}.artifact_id must be unique")
            dependency_ids.add(artifact_id)
        if dependency.get("depended_on_version") != payload.get("predecessor_version"):
            errors.append(f"{prefix}.depended_on_version must match predecessor_version")
        disposition = dependency.get("disposition")
        if disposition not in {"invalidated", "review_required", "confirmed_compatible"}:
            errors.append(f"{prefix}.disposition is not recognized")
        elif disposition == "invalidated":
            invalidated_count += 1
        if not isinstance(dependency.get("notice_delivered"), bool):
            errors.append(f"{prefix}.notice_delivered must be boolean")
        elif dependency.get("notice_delivered") is not True:
            errors.append(f"{prefix}.notice_delivered must be true")
    if dependencies and invalidated_count == 0:
        errors.append("at least one downstream dependency must be invalidated by a mission revision")

    return {
        "valid": not errors,
        "errors": errors,
        "dependency_count": len(dependencies),
        "invalidated_count": invalidated_count,
    }

def validate_handoff_thesis_gate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Integrate Palamedes purpose coherence with planner strategy ownership."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["handoff thesis gate must be an object"]}
    for field in (
        "handoff_gate_id",
        "mission_contract_id",
        "mission_meaning_boundary_id",
        "tradeoff_interface_id",
        "planner_return_protocol_id",
        "constraint_reframing_protocol_id",
        "meaning_invariant_protocol_id",
        "downstream_status_protocol_id",
        "conflict_jurisdiction_protocol_id",
        "cumulative_failure_protocol_id",
        "revision_invalidation_protocol_id",
        "ownership_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("palamedes_owns_execution_strategy") is not False:
        errors.append("palamedes_owns_execution_strategy must be false")
    if payload.get("planner_owns_mission_meaning") is not False:
        errors.append("planner_owns_mission_meaning must be false")
    if payload.get("typed_bidirectional_evidence") is not True:
        errors.append("typed_bidirectional_evidence must be true")

    required_palamedes = {"purpose_coherence", "mission_revision", "purpose_conflict"}
    required_planner = {"strategy_formation", "technical_tradeoffs", "delivery"}
    palamedes_ownership = payload.get("palamedes_ownership")
    planner_ownership = payload.get("planner_ownership")
    if (
        not isinstance(palamedes_ownership, list)
        or set(palamedes_ownership) != required_palamedes
        or len(palamedes_ownership) != len(required_palamedes)
    ):
        errors.append("palamedes_ownership must cover purpose_coherence, mission_revision, and purpose_conflict")
        palamedes_ownership = []
    if (
        not isinstance(planner_ownership, list)
        or set(planner_ownership) != required_planner
        or len(planner_ownership) != len(required_planner)
    ):
        errors.append("planner_ownership must cover strategy_formation, technical_tradeoffs, and delivery")
        planner_ownership = []
    overlap = sorted(set(palamedes_ownership) & set(planner_ownership))
    if overlap:
        errors.append("Palamedes and planner ownership must not overlap")

    exchanges = payload.get("evidence_exchange")
    if not isinstance(exchanges, list):
        errors.append("evidence_exchange must be a list")
        exchanges = []
    required_directions = {"palamedes_to_planner", "planner_to_palamedes"}
    seen_directions = set()
    for index, exchange in enumerate(exchanges):
        prefix = f"evidence_exchange[{index}]"
        if not isinstance(exchange, dict):
            errors.append(f"{prefix} must be an object")
            continue
        direction = exchange.get("direction")
        if direction not in required_directions:
            errors.append(f"{prefix}.direction is not recognized")
        else:
            seen_directions.add(direction)
        for field in ("evidence_kind", "contract_field", "boundary_trigger"):
            if not _non_empty(exchange.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if seen_directions != required_directions:
        errors.append("evidence_exchange must operate in both directions")

    return {
        "valid": not errors,
        "errors": errors,
        "evidence_directions": sorted(seen_directions),
    }

def validate_beneficiary_first_portfolio_review(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Begin portfolio review from beneficiary and world change, not throughput."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["beneficiary-first portfolio review must be an object"]}
    for field in ("review_id", "portfolio_id", "review_period", "portfolio_decision_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("throughput_is_primary") is not False:
        errors.append("throughput_is_primary must be false")
    review_order = payload.get("review_order")
    required_order = [
        "beneficiary_change",
        "world_change",
        "assumption_change",
        "delivery",
    ]
    if review_order != required_order:
        errors.append("review_order must begin with beneficiary_change and world_change before delivery")

    missions = payload.get("mission_reviews")
    if not isinstance(missions, list) or not missions:
        errors.append("mission_reviews must be a non-empty list")
        missions = []
    mission_ids = set()
    for index, mission in enumerate(missions):
        prefix = f"mission_reviews[{index}]"
        if not isinstance(mission, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in (
            "mission_id",
            "beneficiary_condition_before",
            "beneficiary_condition_now",
            "beneficiary_change_evidence_id",
            "world_change",
            "world_change_evidence_id",
            "assumption_change",
            "delivery_summary",
            "decision_rationale",
        ):
            if not _non_empty(mission.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        mission_id = mission.get("mission_id")
        if _non_empty(mission_id):
            if mission_id in mission_ids:
                errors.append(f"{prefix}.mission_id must be unique")
            mission_ids.add(mission_id)
        if mission.get("decision") not in {"continue", "revise", "stop"}:
            errors.append(f"{prefix}.decision must be continue, revise, or stop")
        if not isinstance(mission.get("task_velocity"), (int, float)) or isinstance(
            mission.get("task_velocity"), bool
        ):
            errors.append(f"{prefix}.task_velocity must be numeric")
        if mission.get("task_velocity_determines_decision") is not False:
            errors.append(f"{prefix}.task_velocity_determines_decision must be false")

    return {
        "valid": not errors,
        "errors": errors,
        "reviewed_mission_count": len(missions),
    }

def validate_revenue_role_in_mission_selection(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Treat revenue as sustainability and market evidence inside plural value."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["revenue role in mission selection must be an object"]}
    for field in (
        "selection_review_id",
        "portfolio_id",
        "selected_mission_id",
        "revenue_evidence_id",
        "revenue_interpretation",
        "selection_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("revenue_is_sole_selector") is not False:
        errors.append("revenue_is_sole_selector must be false")
    if payload.get("revenue_can_override_constitution") is not False:
        errors.append("revenue_can_override_constitution must be false")
    if payload.get("revenue_defines_beneficiary_value") is not False:
        errors.append("revenue_defines_beneficiary_value must be false")
    roles = payload.get("revenue_roles")
    required_roles = {"sustainability_constraint", "market_signal"}
    if not isinstance(roles, list) or set(roles) != required_roles or len(roles) != len(required_roles):
        errors.append("revenue_roles must contain sustainability_constraint and market_signal")

    required_dimensions = {
        "beneficiary_change",
        "constitutional_fit",
        "sustainability",
        "option_value",
    }
    dimensions = payload.get("selection_dimensions")
    if (
        not isinstance(dimensions, list)
        or set(dimensions) != required_dimensions
        or len(dimensions) != len(required_dimensions)
    ):
        errors.append("selection_dimensions must cover beneficiary_change, constitutional_fit, sustainability, and option_value")

    candidates = payload.get("mission_candidates")
    if not isinstance(candidates, list) or len(candidates) < 2:
        errors.append("mission_candidates must contain at least two candidates")
        candidates = []
    candidate_ids = set()
    selected = None
    for index, candidate in enumerate(candidates):
        prefix = f"mission_candidates[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{prefix} must be an object")
            continue
        mission_id = candidate.get("mission_id")
        if not _non_empty(mission_id):
            errors.append(f"{prefix}.mission_id must be a non-empty string")
        elif mission_id in candidate_ids:
            errors.append(f"{prefix}.mission_id must be unique")
        else:
            candidate_ids.add(mission_id)
        for field in (
            "beneficiary_change",
            "constitutional_fit",
            "sustainability",
            "option_value",
            "revenue_signal",
        ):
            if not _non_empty(candidate.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if not isinstance(candidate.get("constitutionally_eligible"), bool):
            errors.append(f"{prefix}.constitutionally_eligible must be boolean")
        if mission_id == payload.get("selected_mission_id"):
            selected = candidate
    if payload.get("selected_mission_id") not in candidate_ids:
        errors.append("selected_mission_id must reference a candidate")
    if selected and selected.get("constitutionally_eligible") is not True:
        errors.append("selected mission must be constitutionally eligible regardless of revenue")

    return {
        "valid": not errors,
        "errors": errors,
        "selected_mission_id": payload.get("selected_mission_id"),
    }

def validate_mission_resource_renewal(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require a resource-renewal thesis or an authorized subsidy mandate."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["mission resource renewal must be an object"]}
    for field in (
        "resource_record_id",
        "mission_id",
        "resource_envelope",
        "runway",
        "renewal_review_trigger",
        "stop_condition",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("unsupported_noble_intent_is_sufficient") is not False:
        errors.append("unsupported_noble_intent_is_sufficient must be false")
    mode = payload.get("resource_mode")
    if mode not in {"earned_revenue", "subsidy", "hybrid"}:
        errors.append("resource_mode must be earned_revenue, subsidy, or hybrid")

    renewal = payload.get("resource_renewal_thesis")
    subsidy = payload.get("subsidy_mandate")
    if mode in {"earned_revenue", "hybrid"}:
        if not isinstance(renewal, dict):
            errors.append("earned_revenue or hybrid mode requires resource_renewal_thesis")
        else:
            for field in (
                "payer",
                "payer_benefit",
                "renewal_mechanism",
                "pricing_evidence_id",
                "causal_thesis",
            ):
                if not _non_empty(renewal.get(field)):
                    errors.append(f"resource_renewal_thesis.{field} must be a non-empty string")
    if mode in {"subsidy", "hybrid"}:
        if not isinstance(subsidy, dict):
            errors.append("subsidy or hybrid mode requires subsidy_mandate")
        else:
            for field in (
                "mandate_id",
                "authority_id",
                "resource_limit",
                "purpose_scope",
                "expires_at",
                "renewal_authority",
            ):
                if not _non_empty(subsidy.get(field)):
                    errors.append(f"subsidy_mandate.{field} must be a non-empty string")
            if subsidy.get("open_ended") is not False:
                errors.append("subsidy_mandate.open_ended must be false")

    return {
        "valid": not errors,
        "errors": errors,
        "resource_mode": mode,
    }

def validate_growth_mechanism_audit(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Separate voluntary durable benefit from friction, compulsion, and distribution."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["growth mechanism audit must be an object"]}
    for field in (
        "audit_id",
        "mission_id",
        "growth_observation",
        "growth_evidence_id",
        "classification_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("growth_is_value_proof") is not False:
        errors.append("growth_is_value_proof must be false")

    required_mechanisms = {
        "voluntary_durable_benefit",
        "switching_friction",
        "compulsion",
        "acquired_distribution",
    }
    mechanisms = payload.get("mechanism_assessments")
    if not isinstance(mechanisms, list):
        errors.append("mechanism_assessments must be a list")
        mechanisms = []
    seen = set()
    statuses: Dict[str, str] = {}
    for index, mechanism in enumerate(mechanisms):
        prefix = f"mechanism_assessments[{index}]"
        if not isinstance(mechanism, dict):
            errors.append(f"{prefix} must be an object")
            continue
        kind = mechanism.get("mechanism")
        if kind not in required_mechanisms:
            errors.append(f"{prefix}.mechanism is not recognized")
        elif kind in seen:
            errors.append(f"{prefix}.mechanism must be unique")
        else:
            seen.add(kind)
        status = mechanism.get("status")
        if status not in {"present", "absent", "unknown"}:
            errors.append(f"{prefix}.status must be present, absent, or unknown")
        elif kind in required_mechanisms:
            statuses[kind] = status
        for field in ("observation", "evidence_id", "discriminator"):
            if not _non_empty(mechanism.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if seen != required_mechanisms:
        errors.append("mechanism_assessments must cover all four growth mechanisms")

    classification = payload.get("classification")
    if classification not in {"durable_benefit", "mixed", "exploitative", "underdetermined"}:
        errors.append("classification is not recognized")
    exploitative_present = (
        statuses.get("switching_friction") == "present"
        or statuses.get("compulsion") == "present"
    )
    if classification == "durable_benefit":
        if statuses.get("voluntary_durable_benefit") != "present":
            errors.append("durable_benefit requires present voluntary durable benefit")
        if exploitative_present:
            errors.append("durable_benefit cannot hide present friction or compulsion")
    decision = payload.get("decision")
    if decision not in {"scale", "probe", "mitigate", "stop"}:
        errors.append("decision must be scale, probe, mitigate, or stop")
    if exploitative_present and decision == "scale":
        errors.append("present friction or compulsion cannot justify scaling")

    return {
        "valid": not errors,
        "errors": errors,
        "classification": classification,
        "exploitative_mechanism_present": exploitative_present,
    }

def validate_new_mission_exploration_charge(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Charge a new mission finite exploration capacity and named displacement."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["new mission exploration charge must be an object"]}
    for field in (
        "admission_id",
        "portfolio_id",
        "new_mission_id",
        "exploration_budget_id",
        "displaced_option_id",
        "displacement_consequence",
        "displaced_option_wake_trigger",
        "admission_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("new_mission_is_free") is not False:
        errors.append("new_mission_is_free must be false")
    if payload.get("displaced_option_lineage_preserved") is not True:
        errors.append("displaced_option_lineage_preserved must be true")

    numeric_fields = (
        "total_exploration_capacity",
        "currently_committed_capacity",
        "requested_capacity",
        "displaced_capacity_released",
        "attention_cost",
    )
    numbers: Dict[str, float] = {}
    for field in numeric_fields:
        value = payload.get(field)
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or value < 0
        ):
            errors.append(f"{field} must be a non-negative number")
        else:
            numbers[field] = value
    if numbers.get("requested_capacity", 0) <= 0:
        errors.append("requested_capacity must be greater than zero")
    if numbers.get("attention_cost", 0) <= 0:
        errors.append("attention_cost must be greater than zero")

    projected = None
    if len(numbers) == len(numeric_fields):
        if numbers["displaced_capacity_released"] > numbers["currently_committed_capacity"]:
            errors.append("displaced_capacity_released cannot exceed currently committed capacity")
        projected = (
            numbers["currently_committed_capacity"]
            - numbers["displaced_capacity_released"]
            + numbers["requested_capacity"]
        )
    decision = payload.get("decision")
    if decision not in {"admit", "reject"}:
        errors.append("decision must be admit or reject")
    if projected is not None:
        fits = projected <= numbers["total_exploration_capacity"]
        if decision == "admit" and not fits:
            errors.append("admitted mission exceeds exploration capacity after displacement")
        if decision == "reject" and fits:
            errors.append("rejection requires a reason other than a capacity fit represented by this contract")

    return {
        "valid": not errors,
        "errors": errors,
        "projected_committed_capacity": projected,
        "decision": decision,
    }

def validate_coordination_outcome_metrics(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Measure decision latency and contradiction resolution instead of messages."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["coordination outcome metrics must be an object"]}
    for field in ("metrics_id", "portfolio_id", "measurement_window", "metrics_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("message_volume_is_coordination_quality") is not False:
        errors.append("message_volume_is_coordination_quality must be false")
    if not isinstance(payload.get("message_count"), int) or isinstance(payload.get("message_count"), bool) or payload.get("message_count") < 0:
        errors.append("message_count must be a non-negative integer")

    decisions = payload.get("decision_latency_samples")
    if not isinstance(decisions, list) or not decisions:
        errors.append("decision_latency_samples must be a non-empty list")
        decisions = []
    decision_ids = set()
    for index, decision in enumerate(decisions):
        prefix = f"decision_latency_samples[{index}]"
        if not isinstance(decision, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("decision_id", "ready_at", "decided_at", "evidence_id"):
            if not _non_empty(decision.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        decision_id = decision.get("decision_id")
        if _non_empty(decision_id):
            if decision_id in decision_ids:
                errors.append(f"{prefix}.decision_id must be unique")
            decision_ids.add(decision_id)
        latency = decision.get("latency_hours")
        if not isinstance(latency, (int, float)) or isinstance(latency, bool) or latency < 0:
            errors.append(f"{prefix}.latency_hours must be a non-negative number")

    contradictions = payload.get("contradiction_records")
    if not isinstance(contradictions, list) or not contradictions:
        errors.append("contradiction_records must be a non-empty list")
        contradictions = []
    resolved_count = 0
    for index, contradiction in enumerate(contradictions):
        prefix = f"contradiction_records[{index}]"
        if not isinstance(contradiction, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("contradiction_id", "detected_at", "resolution_evidence_id"):
            if not _non_empty(contradiction.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        status = contradiction.get("status")
        if status not in {"resolved", "open"}:
            errors.append(f"{prefix}.status must be resolved or open")
        if status == "resolved":
            resolved_count += 1
            if not _non_empty(contradiction.get("resolved_at")):
                errors.append(f"{prefix}.resolved_at must be a non-empty string when resolved")
            latency = contradiction.get("resolution_latency_hours")
            if not isinstance(latency, (int, float)) or isinstance(latency, bool) or latency < 0:
                errors.append(f"{prefix}.resolution_latency_hours must be non-negative when resolved")
    if resolved_count == 0:
        errors.append("contradiction_records must include at least one resolved contradiction")

    resolution_rate = resolved_count / len(contradictions) if contradictions else 0
    return {
        "valid": not errors,
        "errors": errors,
        "decision_sample_count": len(decisions),
        "contradiction_resolution_rate": resolution_rate,
    }

def validate_minority_exploration_expiry(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Protect minority exploration only until expiry or evidence review."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["minority exploration expiry must be an object"]}
    for field in (
        "allocation_id",
        "mission_id",
        "starts_at",
        "expires_at",
        "protected_budget",
        "reviewed_at",
        "decision_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if _non_empty(payload.get("starts_at")) and _non_empty(payload.get("expires_at")):
        if payload.get("starts_at") >= payload.get("expires_at"):
            errors.append("expires_at must follow starts_at")
    if payload.get("permanent_protection") is not False:
        errors.append("permanent_protection must be false")
    if payload.get("automatic_renewal") is not False:
        errors.append("automatic_renewal must be false")
    max_cost = payload.get("maximum_cost")
    if not isinstance(max_cost, (int, float)) or isinstance(max_cost, bool) or max_cost <= 0:
        errors.append("maximum_cost must be a positive number")

    thresholds = payload.get("evidence_thresholds")
    if not isinstance(thresholds, list) or not thresholds:
        errors.append("evidence_thresholds must be a non-empty list")
        thresholds = []
    met_count = 0
    for index, threshold in enumerate(thresholds):
        prefix = f"evidence_thresholds[{index}]"
        if not isinstance(threshold, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("threshold_id", "criterion", "observed_result", "evidence_id"):
            if not _non_empty(threshold.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if not isinstance(threshold.get("met"), bool):
            errors.append(f"{prefix}.met must be boolean")
        elif threshold.get("met"):
            met_count += 1
    status = payload.get("status")
    if status not in {"active", "expired"}:
        errors.append("status must be active or expired")
    decision = payload.get("decision")
    if decision not in {"continue_until_expiry", "stop", "graduate", "renew_bounded"}:
        errors.append("decision is not recognized")
    if status == "expired":
        if met_count == 0 and decision != "stop":
            errors.append("expired exploration with no met threshold must stop")
        if decision == "continue_until_expiry":
            errors.append("expired exploration cannot continue until expiry")
    if decision == "renew_bounded":
        for field in ("independent_review_id", "renewed_expires_at"):
            if not _non_empty(payload.get(field)):
                errors.append(f"renew_bounded requires {field}")
        if _non_empty(payload.get("renewed_expires_at")) and payload.get("renewed_expires_at") <= payload.get("expires_at", ""):
            errors.append("renewed_expires_at must extend beyond expires_at")

    return {
        "valid": not errors,
        "errors": errors,
        "met_threshold_count": met_count,
        "decision": decision,
    }

def validate_environmental_principle_review(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Re-test successful principles against changed environmental conditions."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["environmental principle review must be an object"]}
    for field in (
        "review_id",
        "principle_id",
        "principle_statement",
        "successful_precedent_id",
        "successful_outcome",
        "review_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("environmental_invalidation_search_performed") is not True:
        errors.append("environmental_invalidation_search_performed must be true")
    if payload.get("past_success_overrides_current_environment") is not False:
        errors.append("past_success_overrides_current_environment must be false")
    assumptions = payload.get("original_environment_assumptions")
    if not isinstance(assumptions, list) or not assumptions or not all(_non_empty(item) for item in assumptions):
        errors.append("original_environment_assumptions must be a non-empty list of strings")

    changes = payload.get("environmental_changes")
    if not isinstance(changes, list) or not changes:
        errors.append("environmental_changes must be a non-empty list")
        changes = []
    impacts = []
    for index, change in enumerate(changes):
        prefix = f"environmental_changes[{index}]"
        if not isinstance(change, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("change_id", "observation", "evidence_id", "affected_assumption"):
            if not _non_empty(change.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        impact = change.get("impact")
        if impact not in {"none", "weakens", "invalidates"}:
            errors.append(f"{prefix}.impact must be none, weakens, or invalidates")
        else:
            impacts.append(impact)
    expected_status = "valid"
    if "invalidates" in impacts:
        expected_status = "invalidated"
    elif "weakens" in impacts:
        expected_status = "weakened"
    status = payload.get("principle_status")
    if status not in {"valid", "weakened", "invalidated"}:
        errors.append("principle_status must be valid, weakened, or invalidated")
    elif changes and status != expected_status:
        errors.append("principle_status must follow the strongest environmental impact")
    decision = payload.get("decision")
    expected_decision = {
        "valid": "retain",
        "weakened": "limit_scope",
        "invalidated": "retire",
    }.get(status)
    if decision not in {"retain", "limit_scope", "retire"}:
        errors.append("decision must be retain, limit_scope, or retire")
    elif expected_decision and decision != expected_decision:
        errors.append("decision must follow current principle status")

    return {
        "valid": not errors,
        "errors": errors,
        "principle_status": status,
        "decision": decision,
    }

def validate_company_constitution_governance(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Version the company constitution with dissent and outcome linkage."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["company constitution governance must be an object"]}
    for field in (
        "amendment_id",
        "constitution_id",
        "amendment_authority_id",
        "independent_ratifier_id",
        "amendment_reason",
        "activation_at",
        "outcome_review_at",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    predecessor = payload.get("predecessor_version")
    successor = payload.get("successor_version")
    if not isinstance(predecessor, int) or isinstance(predecessor, bool) or predecessor < 1:
        errors.append("predecessor_version must be an integer of at least one")
    if not isinstance(successor, int) or isinstance(successor, bool):
        errors.append("successor_version must be an integer")
    elif isinstance(predecessor, int) and successor != predecessor + 1:
        errors.append("successor_version must equal predecessor_version plus one")
    if payload.get("founder_preference_is_implicit_authority") is not False:
        errors.append("founder_preference_is_implicit_authority must be false")
    if payload.get("dissent_erased") is not False:
        errors.append("dissent_erased must be false")
    if payload.get("amendment_authority_id") == payload.get("independent_ratifier_id"):
        errors.append("independent_ratifier_id must differ from amendment_authority_id")

    dissent = payload.get("dissent_records")
    if not isinstance(dissent, list) or not dissent:
        errors.append("dissent_records must be a non-empty list")
        dissent = []
    for index, record in enumerate(dissent):
        prefix = f"dissent_records[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in (
            "dissent_id",
            "represented_party",
            "objection",
            "evidence_id",
            "disposition",
            "disposition_rationale",
        ):
            if not _non_empty(record.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if record.get("disposition") not in {"accepted", "rejected", "unresolved"}:
            errors.append(f"{prefix}.disposition is not recognized")

    outcome_links = payload.get("outcome_links")
    if not isinstance(outcome_links, list) or not outcome_links:
        errors.append("outcome_links must be a non-empty list")
        outcome_links = []
    for index, link in enumerate(outcome_links):
        prefix = f"outcome_links[{index}]"
        if not isinstance(link, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in (
            "clause_id",
            "predicted_outcome",
            "observed_outcome",
            "outcome_evidence_id",
            "update_trigger",
        ):
            if not _non_empty(link.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")

    return {
        "valid": not errors,
        "errors": errors,
        "successor_version": successor,
        "dissent_count": len(dissent),
        "outcome_link_count": len(outcome_links),
    }

def validate_company_objective_gate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Integrate durable beneficiary change and renewable option capacity."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["company objective gate must be an object"]}
    for field in (
        "objective_gate_id",
        "portfolio_id",
        "beneficiary_first_review_id",
        "revenue_role_review_id",
        "resource_renewal_id",
        "growth_mechanism_audit_id",
        "exploration_charge_id",
        "coordination_metrics_id",
        "minority_expiry_id",
        "environmental_principle_review_id",
        "constitution_governance_id",
        "constitution_id",
        "constitution_version",
        "durable_beneficiary_change",
        "beneficiary_change_evidence_id",
        "renewable_option_capacity",
        "option_capacity_evidence_id",
        "revenue_evidence_id",
        "execution_evidence_id",
        "decision_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("scalar_maximization_objective") is not False:
        errors.append("scalar_maximization_objective must be false")
    if payload.get("revenue_is_company_objective") is not False:
        errors.append("revenue_is_company_objective must be false")
    if payload.get("execution_is_company_objective") is not False:
        errors.append("execution_is_company_objective must be false")
    if payload.get("beneficiary_change_is_durable") is not True:
        errors.append("beneficiary_change_is_durable must be true")
    if payload.get("option_capacity_is_renewable") is not True:
        errors.append("option_capacity_is_renewable must be true")

    constraints = payload.get("constitutional_constraints")
    if not isinstance(constraints, list) or not constraints:
        errors.append("constitutional_constraints must be a non-empty list")
        constraints = []
    violations = []
    for index, constraint in enumerate(constraints):
        prefix = f"constitutional_constraints[{index}]"
        if not isinstance(constraint, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("clause_id", "application", "evidence_id"):
            if not _non_empty(constraint.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if not isinstance(constraint.get("satisfied"), bool):
            errors.append(f"{prefix}.satisfied must be boolean")
        elif constraint.get("satisfied") is False:
            violations.append(constraint.get("clause_id"))

    decision = payload.get("decision")
    if decision not in {"continue", "revise", "stop"}:
        errors.append("decision must be continue, revise, or stop")
    if violations and decision == "continue":
        errors.append("portfolio cannot continue with constitutional violations")

    return {
        "valid": not errors,
        "errors": errors,
        "constitutional_violations": violations,
        "decision": decision,
    }

def validate_autonomous_purpose_claim_boundary(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Bound autonomy claims without pretending to discover universal purpose."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["autonomous purpose claim boundary must be an object"]}
    for field in (
        "claim_id",
        "claim_statement",
        "constitution_id",
        "correction_mechanism_id",
        "outcome_evidence_id",
        "scope_limit",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("universally_correct_purpose_claimed") is not False:
        errors.append("universally_correct_purpose_claimed must be false")
    if payload.get("value_uncertainty_preserved") is not True:
        errors.append("value_uncertainty_preserved must be true")
    if payload.get("claim_is_falsifiable") is not True:
        errors.append("claim_is_falsifiable must be true")

    required_capabilities = {
        "autonomous",
        "plural",
        "evidence_bearing",
        "corrigible",
        "consequential",
    }
    capabilities = payload.get("bounded_capabilities")
    if not isinstance(capabilities, list):
        errors.append("bounded_capabilities must be a list")
        capabilities = []
    seen = set()
    for index, capability in enumerate(capabilities):
        prefix = f"bounded_capabilities[{index}]"
        if not isinstance(capability, dict):
            errors.append(f"{prefix} must be an object")
            continue
        name = capability.get("capability")
        if name not in required_capabilities:
            errors.append(f"{prefix}.capability is not recognized")
        elif name in seen:
            errors.append(f"{prefix}.capability must be unique")
        else:
            seen.add(name)
        for field in ("operational_meaning", "evidence_id", "failure_condition"):
            if not _non_empty(capability.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if seen != required_capabilities:
        errors.append("bounded_capabilities must cover autonomous, plural, evidence_bearing, corrigible, and consequential")

    return {
        "valid": not errors,
        "errors": errors,
        "bounded_capabilities": sorted(seen),
    }

def validate_delegated_preference_challenge(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Challenge inherited preference without copying it or escaping delegation."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["delegated preference challenge must be an object"]}
    for field in (
        "challenge_id",
        "inherited_preference_id",
        "preference_source_id",
        "preference_statement",
        "challenge_hypothesis",
        "counterevidence_id",
        "beneficiary_evidence_id",
        "withdrawal_condition",
        "delegation_id",
        "delegated_domain",
        "delegated_consequence_class",
        "decision_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("copying_founder_behavior_is_sufficient") is not False:
        errors.append("copying_founder_behavior_is_sufficient must be false")
    if payload.get("authority_expanded_by_challenge") is not False:
        errors.append("authority_expanded_by_challenge must be false")
    within = payload.get("within_delegated_authority")
    if not isinstance(within, bool):
        errors.append("within_delegated_authority must be boolean")
    clauses = payload.get("constitutional_clause_ids")
    if not isinstance(clauses, list) or not clauses or not all(_non_empty(item) for item in clauses):
        errors.append("constitutional_clause_ids must be a non-empty list of strings")
    perspectives = payload.get("independent_perspectives")
    if not isinstance(perspectives, list) or len(perspectives) < 2:
        errors.append("independent_perspectives must contain at least two perspectives")
        perspectives = []
    for index, perspective in enumerate(perspectives):
        prefix = f"independent_perspectives[{index}]"
        if not isinstance(perspective, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("perspective_id", "claim", "evidence_id"):
            if not _non_empty(perspective.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    decision = payload.get("decision")
    if decision not in {
        "uphold_preference",
        "revise_preference",
        "preserve_uncertainty",
        "return_for_constitution_review",
    }:
        errors.append("decision is not a recognized preference challenge result")
    if within is False and decision != "return_for_constitution_review":
        errors.append("challenge outside delegated authority must return for constitution review")
    if within is True and decision == "return_for_constitution_review":
        errors.append("within-authority challenge should not use constitution return as approval theater")

    return {
        "valid": not errors,
        "errors": errors,
        "decision": decision,
    }

