from __future__ import annotations

from typing import Any, Dict, List
from ._01_kinds_value import _non_empty


def validate_strategy_only_first_planner_handoff(payload: Dict[str, Any]) -> Dict[str, Any]:
    """End the first planner handoff at acknowledgment and strategy return."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["strategy only first planner handoff must be an object"]}
    for field in (
        "handoff_id",
        "compilation_id",
        "semantic_mapping_id",
        "mission_contract_id",
        "mission_contract_fingerprint",
        "planner_id",
        "handoff_fingerprint",
        "handoff_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected_sequence = [
        ("dispatch_compiled_mission", "palamedes", "planner"),
        ("acknowledge_mission", "planner", "palamedes"),
        ("propose_strategy", "planner", "palamedes"),
        ("return_for_mission_review", "planner", "palamedes"),
    ]
    events = payload.get("handoff_events")
    if not isinstance(events, list) or len(events) != len(expected_sequence):
        errors.append("handoff_events must contain exactly the four first-handoff events")
        events = []
    observed = []
    event_ids = set()
    for index, event in enumerate(events):
        prefix = f"handoff_events[{index}]"
        if not isinstance(event, dict):
            errors.append(f"{prefix} must be an object")
            continue
        event_id = event.get("event_id")
        if not _non_empty(event_id):
            errors.append(f"{prefix}.event_id must be a non-empty string")
        elif event_id in event_ids:
            errors.append(f"{prefix}.event_id must be unique")
        event_ids.add(event_id)
        observed.append((event.get("event_type"), event.get("actor"), event.get("recipient")))
        for field in ("artifact_id", "artifact_fingerprint", "occurred_at"):
            if not _non_empty(event.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if event.get("task_artifacts_created") is not False:
            errors.append(f"{prefix}.task_artifacts_created must be false")
        if event.get("execution_command_issued") is not False:
            errors.append(f"{prefix}.execution_command_issued must be false")
    if observed != expected_sequence:
        errors.append("handoff_events must end with acknowledgment, strategy proposal, and return for review")

    boundary = payload.get("boundary_state")
    if not isinstance(boundary, dict):
        errors.append("boundary_state must be an object")
        boundary = {}
    for field in (
        "planner_acknowledgment_artifact_id",
        "strategy_proposal_artifact_id",
        "palamedes_review_queue_id",
        "next_authorized_transition",
    ):
        if not _non_empty(boundary.get(field)):
            errors.append(f"boundary_state.{field} must be a non-empty string")
    event_artifacts = {
        event.get("event_type"): event.get("artifact_id")
        for event in events
        if isinstance(event, dict)
    }
    if boundary.get("planner_acknowledgment_artifact_id") != event_artifacts.get("acknowledge_mission"):
        errors.append("boundary_state planner acknowledgment must reference the acknowledgment event artifact")
    if boundary.get("strategy_proposal_artifact_id") != event_artifacts.get("propose_strategy"):
        errors.append("boundary_state strategy proposal must reference the proposal event artifact")
    if boundary.get("status") != "awaiting_palamedes_strategy_review":
        errors.append("boundary_state.status must be awaiting_palamedes_strategy_review")
    if boundary.get("next_authorized_transition") != "review_strategy_meaning_and_constraints":
        errors.append("boundary_state.next_authorized_transition must be review_strategy_meaning_and_constraints")
    for field in (
        "task_plan_present",
        "implementation_sequence_present",
        "execution_authority_issued",
        "implementation_started",
        "planner_self_approved_strategy",
    ):
        if boundary.get(field) is not False:
            errors.append(f"boundary_state.{field} must be false")
    if payload.get("first_handoff_complete") is not True:
        errors.append("first_handoff_complete must be true")
    if payload.get("first_handoff_generated_tasks") is not False:
        errors.append("first_handoff_generated_tasks must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "event_count": len(event_ids),
        "boundary_status": boundary.get("status"),
        "strategy_proposal_artifact_id": boundary.get("strategy_proposal_artifact_id"),
    }

def validate_explicit_planner_mission_acknowledgment(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require a planner to restate mission meaning, authority, and ambiguity."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["explicit planner mission acknowledgment must be an object"]}
    for field in (
        "acknowledgment_id",
        "acknowledgment_fingerprint",
        "handoff_id",
        "mission_contract_id",
        "mission_contract_fingerprint",
        "planner_id",
        "acknowledged_at",
        "acknowledgment_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    beneficiary = payload.get("interpreted_beneficiary")
    if not isinstance(beneficiary, dict):
        errors.append("interpreted_beneficiary must be an object")
        beneficiary = {}
    for field in (
        "beneficiary_identity",
        "current_condition",
        "desired_external_condition",
        "source_clause_id",
        "source_clause_fingerprint",
        "interpretation_statement",
    ):
        if not _non_empty(beneficiary.get(field)):
            errors.append(f"interpreted_beneficiary.{field} must be a non-empty string")

    meaning = payload.get("invariant_meaning")
    if not isinstance(meaning, dict):
        errors.append("invariant_meaning must be an object")
        meaning = {}
    for field in ("meaning_statement", "meaning_fingerprint"):
        if not _non_empty(meaning.get(field)):
            errors.append(f"invariant_meaning.{field} must be a non-empty string")
    source_clause_ids = meaning.get("source_clause_ids")
    if (
        not isinstance(source_clause_ids, list)
        or not source_clause_ids
        or not all(_non_empty(item) for item in source_clause_ids)
        or len(source_clause_ids) != len(set(source_clause_ids))
    ):
        errors.append("invariant_meaning.source_clause_ids must be a non-empty unique string list")
    if meaning.get("planner_may_reinterpret_meaning") is not False:
        errors.append("invariant_meaning.planner_may_reinterpret_meaning must be false")

    authority = payload.get("assumed_authority")
    if not isinstance(authority, dict):
        errors.append("assumed_authority must be an object")
        authority = {}
    for field in (
        "authority_grant_id",
        "authority_grant_fingerprint",
        "scope",
        "budget",
        "expires_at",
        "authority_return_trigger",
        "assumption_statement",
    ):
        if not _non_empty(authority.get(field)):
            errors.append(f"assumed_authority.{field} must be a non-empty string")
    for field in ("allowed_actions", "forbidden_actions"):
        values = authority.get(field)
        if (
            not isinstance(values, list)
            or not values
            or not all(_non_empty(item) for item in values)
            or len(values) != len(set(values))
        ):
            errors.append(f"assumed_authority.{field} must be a non-empty unique string list")
            values = []
    if set(authority.get("allowed_actions", [])).intersection(authority.get("forbidden_actions", [])):
        errors.append("assumed_authority allowed_actions and forbidden_actions must be disjoint")
    if authority.get("may_expand_own_authority") is not False:
        errors.append("assumed_authority.may_expand_own_authority must be false")

    unclear = payload.get("unclear_mission_clauses")
    if not isinstance(unclear, dict):
        errors.append("unclear_mission_clauses must be an object")
        unclear = {}
    status = unclear.get("status")
    if status not in {"identified", "none_identified"}:
        errors.append("unclear_mission_clauses.status must be identified or none_identified")
    assessments = unclear.get("assessments")
    if not isinstance(assessments, list):
        errors.append("unclear_mission_clauses.assessments must be a list")
        assessments = []
    clause_ids = set()
    for index, assessment in enumerate(assessments):
        prefix = f"unclear_mission_clauses.assessments[{index}]"
        if not isinstance(assessment, dict):
            errors.append(f"{prefix} must be an object")
            continue
        clause_id = assessment.get("clause_id")
        if not _non_empty(clause_id):
            errors.append(f"{prefix}.clause_id must be a non-empty string")
        elif clause_id in clause_ids:
            errors.append(f"{prefix}.clause_id must be unique")
        clause_ids.add(clause_id)
        for field in (
            "clause_fingerprint",
            "ambiguity",
            "clarifying_question",
            "strategy_effect_if_unresolved",
        ):
            if not _non_empty(assessment.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if status == "identified":
        if not assessments:
            errors.append("identified unclear clauses require at least one assessment")
        if unclear.get("none_identified_rationale") not in ("", None):
            errors.append("identified unclear clauses must not carry none_identified_rationale")
    elif status == "none_identified":
        if assessments:
            errors.append("none_identified unclear clauses must have no assessments")
        if not _non_empty(unclear.get("none_identified_rationale")):
            errors.append("none_identified unclear clauses require a rationale")
    if payload.get("acknowledgment_precedes_strategy") is not True:
        errors.append("acknowledgment_precedes_strategy must be true")
    if payload.get("execution_withheld_until_strategy_review") is not True:
        errors.append("execution_withheld_until_strategy_review must be true")
    if payload.get("generic_acknowledgment_only") is not False:
        errors.append("generic_acknowledgment_only must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "unclear_clause_status": status,
        "unclear_clause_count": len(clause_ids),
        "planner_id": payload.get("planner_id"),
    }

def validate_preimplementation_semantic_reconstruction_review(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Compare mission and acknowledgment semantics before strategy proceeds."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["preimplementation semantic reconstruction review must be an object"]}
    for field in (
        "reconstruction_review_id",
        "mission_contract_id",
        "mission_contract_fingerprint",
        "acknowledgment_id",
        "acknowledgment_fingerprint",
        "reviewer_id",
        "reviewed_at",
        "review_fingerprint",
        "review_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    required_dimensions = {
        "beneficiary",
        "invariant_meaning",
        "authority",
        "unclear_clauses",
    }
    comparisons = payload.get("dimension_comparisons")
    if not isinstance(comparisons, list) or len(comparisons) != len(required_dimensions):
        errors.append("dimension_comparisons must contain exactly four semantic dimensions")
        comparisons = []
    observed = set()
    statuses: Dict[str, str] = {}
    for index, comparison in enumerate(comparisons):
        prefix = f"dimension_comparisons[{index}]"
        if not isinstance(comparison, dict):
            errors.append(f"{prefix} must be an object")
            continue
        dimension = comparison.get("dimension")
        if dimension not in required_dimensions:
            errors.append(f"{prefix}.dimension is not recognized")
        elif dimension in observed:
            errors.append(f"{prefix}.dimension must be unique")
        observed.add(dimension)
        status = comparison.get("status")
        if status not in {"exact_match", "clarified", "loss", "contradiction"}:
            errors.append(f"{prefix}.status is not recognized")
        elif dimension in required_dimensions:
            statuses[dimension] = status
        for field in (
            "source_value_fingerprint",
            "acknowledged_value_fingerprint",
            "comparison_evidence_id",
            "difference_description",
            "decision_effect",
        ):
            if not _non_empty(comparison.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if status in {"loss", "contradiction"}:
            if not _non_empty(comparison.get("required_correction")):
                errors.append(f"{prefix}.required_correction is required for loss or contradiction")
        elif comparison.get("required_correction") not in ("", None):
            errors.append(f"{prefix}.required_correction must be empty without loss or contradiction")
    if observed != required_dimensions:
        errors.append("dimension_comparisons must cover every semantic dimension exactly once")

    burden = payload.get("reconstruction_burden")
    if not isinstance(burden, dict):
        errors.append("reconstruction_burden must be an object")
        burden = {}
    counts = {}
    for field in (
        "source_lookup_count",
        "clarification_question_count",
        "reinterpretation_count",
        "unresolved_clause_count",
    ):
        value = burden.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            errors.append(f"reconstruction_burden.{field} must be a non-negative integer")
            value = 0
        counts[field] = value
    for field in ("measurement_method", "burden_rationale"):
        if not _non_empty(burden.get(field)):
            errors.append(f"reconstruction_burden.{field} must be a non-empty string")
    if burden.get("measured_before_implementation") is not True:
        errors.append("reconstruction_burden.measured_before_implementation must be true")

    blocking_dimensions = sorted(
        dimension
        for dimension, status in statuses.items()
        if status in {"loss", "contradiction"}
    )
    expected_decision = (
        "clarification_required"
        if blocking_dimensions or counts["unresolved_clause_count"] > 0
        else "ready_for_strategy_review"
    )
    if payload.get("review_decision") != expected_decision:
        errors.append("review_decision must reflect semantic loss, contradiction, and unresolved clauses")
    if payload.get("blocking_dimensions") != blocking_dimensions:
        errors.append("blocking_dimensions must list every loss or contradiction dimension")
    if payload.get("implementation_started") is not False:
        errors.append("implementation_started must be false")
    if payload.get("semantic_loss_ignored") is not False:
        errors.append("semantic_loss_ignored must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "review_decision": expected_decision,
        "blocking_dimensions": blocking_dimensions,
        "reconstruction_burden_total": sum(counts.values()),
    }

def validate_typed_planner_mission_challenge(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Type planner challenges and require evidence appropriate to each kind."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["typed planner mission challenge must be an object"]}
    for field in (
        "challenge_id",
        "challenge_fingerprint",
        "handoff_id",
        "mission_contract_id",
        "mission_contract_fingerprint",
        "planner_id",
        "raised_at",
        "challenge_statement",
        "affected_contract_clause_id",
        "affected_contract_clause_fingerprint",
        "evidence_artifact_id",
        "decision_effect",
        "proposed_next_step",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    challenge_type = payload.get("challenge_type")
    allowed_types = {
        "infeasibility",
        "ambiguity",
        "causal_objection",
        "resource_conflict",
        "alternative_mechanism",
    }
    if challenge_type not in allowed_types:
        errors.append("challenge_type is not recognized")
    details = payload.get("typed_details")
    if not isinstance(details, dict):
        errors.append("typed_details must be an object")
        details = {}
    if challenge_type == "infeasibility":
        for field in (
            "blocking_constraint",
            "constraint_evidence_id",
            "affected_mission_outcome",
            "attempted_alternative",
            "alternative_test_result",
        ):
            if not _non_empty(details.get(field)):
                errors.append(f"infeasibility requires typed_details.{field}")
        if details.get("infeasibility_claimed_without_attempt") is not False:
            errors.append("infeasibility.typed_details.infeasibility_claimed_without_attempt must be false")
    elif challenge_type == "ambiguity":
        interpretations = details.get("competing_interpretations")
        if (
            not isinstance(interpretations, list)
            or len(interpretations) < 2
            or not all(_non_empty(item) for item in interpretations)
            or len(interpretations) != len(set(interpretations))
        ):
            errors.append("ambiguity requires at least two unique competing_interpretations")
        for field in ("ambiguous_text", "clarifying_question", "decision_difference"):
            if not _non_empty(details.get(field)):
                errors.append(f"ambiguity requires typed_details.{field}")
        if details.get("planner_selected_default_interpretation") is not False:
            errors.append("ambiguity.typed_details.planner_selected_default_interpretation must be false")
    elif challenge_type == "causal_objection":
        for field in (
            "challenged_causal_thesis",
            "countermechanism",
            "contradicting_evidence_id",
            "discriminating_observation_or_probe",
            "withdrawal_condition",
        ):
            if not _non_empty(details.get(field)):
                errors.append(f"causal_objection requires typed_details.{field}")
    elif challenge_type == "resource_conflict":
        for field in (
            "contested_resource",
            "competing_commitment_id",
            "available_amount",
            "required_amount",
            "shortfall",
            "allocation_authority_id",
        ):
            if not _non_empty(details.get(field)):
                errors.append(f"resource_conflict requires typed_details.{field}")
        if details.get("planner_unilaterally_reallocated") is not False:
            errors.append("resource_conflict.typed_details.planner_unilaterally_reallocated must be false")
    elif challenge_type == "alternative_mechanism":
        for field in (
            "proposed_mechanism",
            "comparative_basis",
            "affected_constraint",
            "meaning_preservation_evidence_id",
            "new_risk",
        ):
            if not _non_empty(details.get(field)):
                errors.append(f"alternative_mechanism requires typed_details.{field}")
        if details.get("mission_meaning_preserved") is not True:
            errors.append("alternative_mechanism.typed_details.mission_meaning_preserved must be true")
        if details.get("mechanism_substituted_without_review") is not False:
            errors.append("alternative_mechanism.typed_details.mechanism_substituted_without_review must be false")
    if payload.get("freeform_untyped_challenge") is not False:
        errors.append("freeform_untyped_challenge must be false")
    if payload.get("implementation_continues_before_resolution") is not False:
        errors.append("implementation_continues_before_resolution must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "challenge_type": challenge_type,
        "challenge_id": payload.get("challenge_id"),
    }

def validate_purpose_effect_challenge_jurisdiction(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Route challenges by purpose effect while preserving planner implementation authority."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["purpose effect challenge jurisdiction must be an object"]}
    for field in (
        "jurisdiction_record_id",
        "challenge_id",
        "challenge_fingerprint",
        "mission_contract_id",
        "mission_contract_fingerprint",
        "assessment_fingerprint",
        "assessor_id",
        "assessment_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("challenge_type") not in {
        "infeasibility",
        "ambiguity",
        "causal_objection",
        "resource_conflict",
        "alternative_mechanism",
    }:
        errors.append("challenge_type is not recognized")
    purpose_dimensions = {
        "beneficiary",
        "invariant_meaning",
        "constitution",
        "authority",
        "causal_thesis",
    }
    assessments = payload.get("impact_assessments")
    if not isinstance(assessments, list) or len(assessments) != len(purpose_dimensions) + 1:
        errors.append("impact_assessments must cover five purpose dimensions and execution_form")
        assessments = []
    observed = set()
    impacts: Dict[str, bool] = {}
    for index, assessment in enumerate(assessments):
        prefix = f"impact_assessments[{index}]"
        if not isinstance(assessment, dict):
            errors.append(f"{prefix} must be an object")
            continue
        dimension = assessment.get("dimension")
        if dimension not in purpose_dimensions | {"execution_form"}:
            errors.append(f"{prefix}.dimension is not recognized")
        elif dimension in observed:
            errors.append(f"{prefix}.dimension must be unique")
        observed.add(dimension)
        affected = assessment.get("affected")
        if not isinstance(affected, bool):
            errors.append(f"{prefix}.affected must be boolean")
        elif dimension in purpose_dimensions | {"execution_form"}:
            impacts[dimension] = affected
        for field in ("evidence_artifact_id", "effect_description"):
            if not _non_empty(assessment.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if observed != purpose_dimensions | {"execution_form"}:
        errors.append("impact_assessments must cover every jurisdiction dimension exactly once")
    purpose_affecting = any(impacts.get(dimension) is True for dimension in purpose_dimensions)
    expected_jurisdiction = "palamedes" if purpose_affecting else "planner"
    if payload.get("purpose_affecting") is not purpose_affecting:
        errors.append("purpose_affecting must follow evidenced purpose dimensions")
    if payload.get("decision_jurisdiction") != expected_jurisdiction:
        errors.append("decision_jurisdiction must be palamedes only for a purpose-affecting challenge")

    resolution = payload.get("resolution_boundary")
    if not isinstance(resolution, dict):
        errors.append("resolution_boundary must be an object")
        resolution = {}
    for field in ("resolution_record_id", "resolution_owner_id", "next_action"):
        if not _non_empty(resolution.get(field)):
            errors.append(f"resolution_boundary.{field} must be a non-empty string")
    if expected_jurisdiction == "palamedes":
        if resolution.get("response_mode") not in {
            "clarify_mission",
            "confirm_mission",
            "revise_mission",
            "reject_challenge",
        }:
            errors.append("purpose-affecting challenge requires a Palamedes mission response mode")
        if resolution.get("resolution_owner_role") != "palamedes":
            errors.append("purpose-affecting challenge resolution owner role must be palamedes")
        if not _non_empty(resolution.get("mission_response_artifact_id")):
            errors.append("purpose-affecting challenge requires mission_response_artifact_id")
    else:
        if resolution.get("response_mode") != "planner_decides_implementation":
            errors.append("implementation-only challenge must return decision to the planner")
        if resolution.get("resolution_owner_role") != "planner":
            errors.append("implementation-only resolution owner role must be planner")
        if resolution.get("mission_response_artifact_id") not in ("", None):
            errors.append("implementation-only challenge must not create a mission response artifact")
    if resolution.get("palamedes_prescribes_implementation_choice") is not False:
        errors.append("resolution_boundary.palamedes_prescribes_implementation_choice must be false")
    if resolution.get("planner_may_rewrite_purpose") is not False:
        errors.append("resolution_boundary.planner_may_rewrite_purpose must be false")
    if resolution.get("palamedes_implementation_opinion_is_advisory") is not True:
        errors.append("resolution_boundary.palamedes_implementation_opinion_is_advisory must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "purpose_affecting": purpose_affecting,
        "decision_jurisdiction": expected_jurisdiction,
        "affected_purpose_dimensions": sorted(
            dimension for dimension in purpose_dimensions if impacts.get(dimension) is True
        ),
    }

def validate_strategy_revision_acceptance_invalidation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Invalidate predecessor-bound strategies until successor acceptance."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["strategy revision acceptance invalidation must be an object"]}
    for field in (
        "invalidation_transaction_id",
        "mission_revision_id",
        "predecessor_contract_id",
        "predecessor_contract_version",
        "predecessor_contract_fingerprint",
        "successor_contract_id",
        "successor_contract_version",
        "successor_contract_fingerprint",
        "planner_id",
        "transaction_fingerprint",
        "invalidation_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if (
        payload.get("predecessor_contract_id"),
        payload.get("predecessor_contract_version"),
        payload.get("predecessor_contract_fingerprint"),
    ) == (
        payload.get("successor_contract_id"),
        payload.get("successor_contract_version"),
        payload.get("successor_contract_fingerprint"),
    ):
        errors.append("successor mission identity, version, or fingerprint must differ")
    strategies = payload.get("dependent_strategy_versions")
    if not isinstance(strategies, list) or not strategies:
        errors.append("dependent_strategy_versions must be a non-empty list")
        strategies = []
    strategy_ids = set()
    for index, strategy in enumerate(strategies):
        prefix = f"dependent_strategy_versions[{index}]"
        if not isinstance(strategy, dict):
            errors.append(f"{prefix} must be an object")
            continue
        strategy_id = strategy.get("strategy_version_id")
        if not _non_empty(strategy_id):
            errors.append(f"{prefix}.strategy_version_id must be a non-empty string")
        elif strategy_id in strategy_ids:
            errors.append(f"{prefix}.strategy_version_id must be unique")
        strategy_ids.add(strategy_id)
        for field in (
            "strategy_fingerprint",
            "dependency_record_id",
            "invalidation_notice_id",
            "invalidated_at",
            "invalidation_reason",
        ):
            if not _non_empty(strategy.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if strategy.get("source_mission_contract_fingerprint") != payload.get("predecessor_contract_fingerprint"):
            errors.append(f"{prefix}.source_mission_contract_fingerprint must match predecessor")
        if strategy.get("status_before_revision") != "active":
            errors.append(f"{prefix}.status_before_revision must be active")
        if strategy.get("status_after_revision") != "invalidated":
            errors.append(f"{prefix}.status_after_revision must be invalidated")
        if strategy.get("execution_allowed_after_revision") is not False:
            errors.append(f"{prefix}.execution_allowed_after_revision must be false")
        if strategy.get("notice_delivered") is not True:
            errors.append(f"{prefix}.notice_delivered must be true")

    acceptance = payload.get("successor_acceptance")
    if not isinstance(acceptance, dict):
        errors.append("successor_acceptance must be an object")
        acceptance = {}
    for field in (
        "acceptance_id",
        "accepted_by_planner_id",
        "accepted_at",
        "acceptance_fingerprint",
        "replacement_strategy_version_id",
        "replacement_strategy_fingerprint",
        "acknowledgment_artifact_id",
        "acceptance_statement",
    ):
        if not _non_empty(acceptance.get(field)):
            errors.append(f"successor_acceptance.{field} must be a non-empty string")
    if acceptance.get("accepted_by_planner_id") != payload.get("planner_id"):
        errors.append("successor_acceptance.accepted_by_planner_id must match planner_id")
    if acceptance.get("accepted_mission_contract_id") != payload.get("successor_contract_id"):
        errors.append("successor_acceptance.accepted_mission_contract_id must match successor")
    if acceptance.get("accepted_mission_contract_version") != payload.get("successor_contract_version"):
        errors.append("successor_acceptance.accepted_mission_contract_version must match successor")
    if acceptance.get("accepted_mission_contract_fingerprint") != payload.get("successor_contract_fingerprint"):
        errors.append("successor_acceptance.accepted_mission_contract_fingerprint must match successor")
    superseded = acceptance.get("superseded_strategy_version_ids")
    if (
        not isinstance(superseded, list)
        or set(superseded) != strategy_ids
        or len(superseded) != len(strategy_ids)
    ):
        errors.append("successor_acceptance.superseded_strategy_version_ids must cover invalidated strategies exactly")
    if acceptance.get("explicitly_accepted") is not True:
        errors.append("successor_acceptance.explicitly_accepted must be true")
    if acceptance.get("mission_invariants_reconfirmed") is not True:
        errors.append("successor_acceptance.mission_invariants_reconfirmed must be true")
    if acceptance.get("unresolved_clauses") != []:
        errors.append("successor_acceptance.unresolved_clauses must be empty before activation")

    activation = payload.get("replacement_activation")
    if not isinstance(activation, dict):
        errors.append("replacement_activation must be an object")
        activation = {}
    if activation.get("strategy_version_id") != acceptance.get("replacement_strategy_version_id"):
        errors.append("replacement_activation.strategy_version_id must match accepted replacement")
    if activation.get("strategy_fingerprint") != acceptance.get("replacement_strategy_fingerprint"):
        errors.append("replacement_activation.strategy_fingerprint must match accepted replacement")
    if activation.get("source_mission_contract_fingerprint") != payload.get("successor_contract_fingerprint"):
        errors.append("replacement_activation.source_mission_contract_fingerprint must match successor")
    if activation.get("acceptance_id") != acceptance.get("acceptance_id"):
        errors.append("replacement_activation.acceptance_id must reference explicit acceptance")
    if activation.get("status") != "active":
        errors.append("replacement_activation.status must be active")
    if activation.get("activated_before_acceptance") is not False:
        errors.append("replacement_activation.activated_before_acceptance must be false")
    if payload.get("silent_plan_drift") is not False:
        errors.append("silent_plan_drift must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "invalidated_strategy_count": len(strategy_ids),
        "replacement_strategy_version_id": acceptance.get("replacement_strategy_version_id"),
        "successor_contract_fingerprint": payload.get("successor_contract_fingerprint"),
    }

def validate_mission_signal_outcome_return(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Return beneficiary outcomes against mission signals, apart from delivery."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["mission signal outcome return must be an object"]}
    for field in (
        "outcome_return_id",
        "mission_contract_id",
        "mission_contract_version",
        "mission_contract_fingerprint",
        "strategy_version_id",
        "strategy_fingerprint",
        "planner_id",
        "returned_at",
        "outcome_return_fingerprint",
        "return_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    registered = payload.get("registered_mission_signals")
    if not isinstance(registered, list) or len(registered) < 2:
        errors.append("registered_mission_signals must contain success and harm signals")
        registered = []
    registered_by_id: Dict[str, Dict[str, Any]] = {}
    registered_kinds = set()
    for index, signal in enumerate(registered):
        prefix = f"registered_mission_signals[{index}]"
        if not isinstance(signal, dict):
            errors.append(f"{prefix} must be an object")
            continue
        signal_id = signal.get("signal_id")
        if not _non_empty(signal_id):
            errors.append(f"{prefix}.signal_id must be a non-empty string")
        elif signal_id in registered_by_id:
            errors.append(f"{prefix}.signal_id must be unique")
        else:
            registered_by_id[signal_id] = signal
        kind = signal.get("kind")
        if kind not in {"success", "harm"}:
            errors.append(f"{prefix}.kind must be success or harm")
        registered_kinds.add(kind)
        for field in ("signal_fingerprint", "definition", "threshold", "observation_window"):
            if not _non_empty(signal.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if registered_kinds != {"success", "harm"}:
        errors.append("registered_mission_signals must include success and harm")

    observations = payload.get("mission_signal_observations")
    if not isinstance(observations, list) or len(observations) != len(registered_by_id):
        errors.append("mission_signal_observations must exactly cover registered signals")
        observations = []
    observed_ids = set()
    success_statuses = []
    harm_statuses = []
    for index, observation in enumerate(observations):
        prefix = f"mission_signal_observations[{index}]"
        if not isinstance(observation, dict):
            errors.append(f"{prefix} must be an object")
            continue
        signal_id = observation.get("signal_id")
        source_signal = registered_by_id.get(signal_id)
        if source_signal is None:
            errors.append(f"{prefix}.signal_id must reference a registered signal")
        elif signal_id in observed_ids:
            errors.append(f"{prefix}.signal_id must be unique")
        observed_ids.add(signal_id)
        for field in (
            "signal_fingerprint",
            "observed_value",
            "observed_at",
            "evidence_artifact_id",
            "evidence_fingerprint",
            "beneficiary_scope",
            "assessment_rationale",
        ):
            if not _non_empty(observation.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if source_signal:
            if observation.get("signal_fingerprint") != source_signal.get("signal_fingerprint"):
                errors.append(f"{prefix}.signal_fingerprint must match the registered signal")
            if observation.get("kind") != source_signal.get("kind"):
                errors.append(f"{prefix}.kind must match the registered signal")
        kind = observation.get("kind")
        status = observation.get("status")
        if kind == "success":
            if status not in {"met", "not_met", "inconclusive"}:
                errors.append(f"{prefix}.status is invalid for a success signal")
            else:
                success_statuses.append(status)
        elif kind == "harm":
            if status not in {"clear", "triggered", "inconclusive"}:
                errors.append(f"{prefix}.status is invalid for a harm signal")
            else:
                harm_statuses.append(status)
    if observed_ids != set(registered_by_id):
        errors.append("mission_signal_observations must cover every registered signal exactly once")

    if "triggered" in harm_statuses or "not_met" in success_statuses:
        expected_outcome = "adverse_or_unsupported"
    elif (
        success_statuses
        and harm_statuses
        and all(item == "met" for item in success_statuses)
        and all(item == "clear" for item in harm_statuses)
    ):
        expected_outcome = "supported"
    else:
        expected_outcome = "inconclusive"
    delivery = payload.get("planner_delivery_report")
    if not isinstance(delivery, dict):
        errors.append("planner_delivery_report must be an object")
        delivery = {}
    for field in ("delivery_report_id", "delivery_status", "completion_evidence_id"):
        if not _non_empty(delivery.get(field)):
            errors.append(f"planner_delivery_report.{field} must be a non-empty string")
    if not isinstance(delivery.get("tasks_completed"), bool):
        errors.append("planner_delivery_report.tasks_completed must be boolean")
    if payload.get("mission_outcome_status") != expected_outcome:
        errors.append("mission_outcome_status must follow mission signal observations")
    if payload.get("task_completion_determines_mission_success") is not False:
        errors.append("task_completion_determines_mission_success must be false")
    if payload.get("planner_may_close_mission") is not False:
        errors.append("planner_may_close_mission must be false")
    if payload.get("outcome_returned_to_palamedes") is not True:
        errors.append("outcome_returned_to_palamedes must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "mission_outcome_status": expected_outcome,
        "observed_signal_count": len(observed_ids),
        "tasks_completed": delivery.get("tasks_completed"),
    }

def validate_bidirectional_mission_planner_handoff_implementation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Integrate traceable compilation, reconstruction, versioning, and outcome return."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["bidirectional mission planner handoff implementation must be an object"]}
    for field in (
        "handoff_implementation_id",
        "mission_contract_id",
        "mission_contract_version",
        "mission_contract_fingerprint",
        "implementation_fingerprint",
        "implementation_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected_components = {
        "linked_compilation": "validate_linked_planner_interface_compilation",
        "semantic_mapping": "validate_mission_semantic_planner_field_mapping",
        "first_handoff": "validate_strategy_only_first_planner_handoff",
        "explicit_acknowledgment": "validate_explicit_planner_mission_acknowledgment",
        "reconstruction_review": "validate_preimplementation_semantic_reconstruction_review",
        "typed_challenge": "validate_typed_planner_mission_challenge",
        "challenge_jurisdiction": "validate_purpose_effect_challenge_jurisdiction",
        "revision_acceptance": "validate_strategy_revision_acceptance_invalidation",
        "mission_signal_return": "validate_mission_signal_outcome_return",
    }
    components = payload.get("component_evidence")
    if not isinstance(components, list) or len(components) != len(expected_components):
        errors.append("component_evidence must contain exactly the nine handoff components")
        components = []
    observed_components = set()
    for index, component in enumerate(components):
        prefix = f"component_evidence[{index}]"
        if not isinstance(component, dict):
            errors.append(f"{prefix} must be an object")
            continue
        name = component.get("component")
        if name in observed_components:
            errors.append(f"{prefix}.component must be unique")
        observed_components.add(name)
        validator = expected_components.get(name)
        if validator is None:
            errors.append(f"{prefix}.component is not recognized")
        elif component.get("validator_id") != validator:
            errors.append(f"{prefix}.validator_id must be {validator}")
        for field in ("evidence_artifact_id", "evidence_fingerprint", "verification_record_id"):
            if not _non_empty(component.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if component.get("verified") is not True:
            errors.append(f"{prefix}.verified must be true")
    if observed_components != set(expected_components):
        errors.append("component_evidence must cover all handoff components exactly once")

    forward = payload.get("forward_dependency")
    if not isinstance(forward, dict):
        errors.append("forward_dependency must be an object")
        forward = {}
    for field in (
        "dependency_record_id",
        "compilation_id",
        "semantic_mapping_id",
        "acknowledgment_id",
        "reconstruction_review_id",
        "strategy_version_id",
        "strategy_fingerprint",
        "strategy_acceptance_id",
    ):
        if not _non_empty(forward.get(field)):
            errors.append(f"forward_dependency.{field} must be a non-empty string")
    if forward.get("source_mission_contract_fingerprint") != payload.get("mission_contract_fingerprint"):
        errors.append("forward_dependency.source_mission_contract_fingerprint must match mission")
    if forward.get("strategy_explicitly_accepted") is not True:
        errors.append("forward_dependency.strategy_explicitly_accepted must be true")
    if forward.get("tasks_generated_before_strategy_acceptance") is not False:
        errors.append("forward_dependency.tasks_generated_before_strategy_acceptance must be false")

    reverse = payload.get("reverse_dependency")
    if not isinstance(reverse, dict):
        errors.append("reverse_dependency must be an object")
        reverse = {}
    for field in (
        "dependency_record_id",
        "outcome_return_id",
        "mission_signal_registry_id",
        "palamedes_outcome_queue_id",
    ):
        if not _non_empty(reverse.get(field)):
            errors.append(f"reverse_dependency.{field} must be a non-empty string")
    if reverse.get("source_strategy_version_id") != forward.get("strategy_version_id"):
        errors.append("reverse_dependency.source_strategy_version_id must match accepted strategy")
    if reverse.get("source_strategy_fingerprint") != forward.get("strategy_fingerprint"):
        errors.append("reverse_dependency.source_strategy_fingerprint must match accepted strategy")
    if reverse.get("target_mission_contract_fingerprint") != payload.get("mission_contract_fingerprint"):
        errors.append("reverse_dependency.target_mission_contract_fingerprint must match mission")
    if reverse.get("outcome_bound_to_registered_mission_signals") is not True:
        errors.append("reverse_dependency.outcome_bound_to_registered_mission_signals must be true")
    if reverse.get("task_completion_substitutes_for_outcome") is not False:
        errors.append("reverse_dependency.task_completion_substitutes_for_outcome must be false")

    invariants = payload.get("handoff_invariants")
    if not isinstance(invariants, dict):
        errors.append("handoff_invariants must be an object")
        invariants = {}
    for field in (
        "thin_envelope_traceable",
        "semantic_mapping_exact",
        "planner_reconstruction_measured",
        "purpose_challenges_returned",
        "implementation_judgment_preserved",
        "mission_revision_invalidates_strategy",
        "strategy_outcomes_return_to_mission",
        "version_dependency_bidirectional",
    ):
        if invariants.get(field) is not True:
            errors.append(f"handoff_invariants.{field} must be true")
    for field in (
        "compiled_goal_replaces_mission",
        "planner_silently_rewrites_purpose",
        "palamedes_chooses_implementation",
        "stale_strategy_remains_executable",
        "delivery_completion_closes_mission",
    ):
        if invariants.get(field) is not False:
            errors.append(f"handoff_invariants.{field} must be false")
    if payload.get("handoff_status") != "integrated":
        errors.append("handoff_status must be integrated")
    return {
        "valid": not errors,
        "errors": errors,
        "component_count": len(observed_components),
        "forward_strategy_version_id": forward.get("strategy_version_id"),
        "reverse_outcome_return_id": reverse.get("outcome_return_id"),
        "handoff_status": payload.get("handoff_status"),
    }

def validate_sequential_hidden_causal_proof_case(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require proof cases with sequential evidence and sealed causal structure."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["sequential hidden causal proof case must be an object"]}
    for field in (
        "proof_case_id",
        "case_fingerprint",
        "case_domain",
        "initial_situation",
        "initial_information_packet_id",
        "initial_information_fingerprint",
        "case_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    events = payload.get("sequential_events")
    if not isinstance(events, list) or len(events) < 3:
        errors.append("sequential_events must contain at least three events")
        events = []
    event_ids = set()
    sequence_numbers = set()
    prior_reveal = None
    for index, event in enumerate(events):
        prefix = f"sequential_events[{index}]"
        if not isinstance(event, dict):
            errors.append(f"{prefix} must be an object")
            continue
        event_id = event.get("event_id")
        if not _non_empty(event_id):
            errors.append(f"{prefix}.event_id must be a non-empty string")
        elif event_id in event_ids:
            errors.append(f"{prefix}.event_id must be unique")
        event_ids.add(event_id)
        sequence = event.get("sequence")
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
            errors.append(f"{prefix}.sequence must be a positive integer")
        elif sequence in sequence_numbers:
            errors.append(f"{prefix}.sequence must be unique")
        sequence_numbers.add(sequence)
        for field in (
            "event_fingerprint",
            "revealed_at",
            "observation",
            "source_artifact_id",
            "source_artifact_fingerprint",
            "new_information",
        ):
            if not _non_empty(event.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if prior_reveal is not None and _non_empty(event.get("revealed_at")) and event["revealed_at"] <= prior_reveal:
            errors.append(f"{prefix}.revealed_at must follow the prior event")
        if _non_empty(event.get("revealed_at")):
            prior_reveal = event.get("revealed_at")
        checkpoint = event.get("pre_next_event_checkpoint")
        if not isinstance(checkpoint, dict):
            errors.append(f"{prefix}.pre_next_event_checkpoint must be an object")
            checkpoint = {}
        for field in (
            "checkpoint_id",
            "signal_interpretation",
            "current_purpose_state_id",
            "current_purpose_fingerprint",
            "selected_next_action",
            "uncertainty_statement",
            "frozen_at",
        ):
            if not _non_empty(checkpoint.get(field)):
                errors.append(f"{prefix}.pre_next_event_checkpoint.{field} must be a non-empty string")
        if checkpoint.get("frozen_before_next_reveal") is not True:
            errors.append(f"{prefix}.pre_next_event_checkpoint.frozen_before_next_reveal must be true")
    if sequence_numbers != set(range(1, len(events) + 1)):
        errors.append("sequential event numbers must be contiguous from one")

    hidden = payload.get("hidden_causal_structure")
    if not isinstance(hidden, dict):
        errors.append("hidden_causal_structure must be an object")
        hidden = {}
    for field in (
        "sealed_structure_id",
        "sealed_structure_fingerprint",
        "ground_truth_artifact_id",
        "ground_truth_fingerprint",
        "seal_custodian_id",
        "reveal_condition",
        "causal_explanation",
    ):
        if not _non_empty(hidden.get(field)):
            errors.append(f"hidden_causal_structure.{field} must be a non-empty string")
    if hidden.get("sealed_before_case_start") is not True:
        errors.append("hidden_causal_structure.sealed_before_case_start must be true")
    if hidden.get("available_to_case_participants") is not False:
        errors.append("hidden_causal_structure.available_to_case_participants must be false")
    if hidden.get("revealed_only_after_final_checkpoint") is not True:
        errors.append("hidden_causal_structure.revealed_only_after_final_checkpoint must be true")

    targets = payload.get("evaluation_targets")
    required_targets = {
        "signal_interpretation",
        "purpose_state_change",
        "next_action_selection",
        "uncertainty_preservation",
    }
    if (
        not isinstance(targets, list)
        or set(targets) != required_targets
        or len(targets) != len(required_targets)
    ):
        errors.append("evaluation_targets must cover interpretation, purpose change, next action, and uncertainty")
    if payload.get("synthetic_idea_scoring_case") is not False:
        errors.append("synthetic_idea_scoring_case must be false")
    if payload.get("purpose_change_possible") is not True:
        errors.append("purpose_change_possible must be true")
    if payload.get("future_events_visible_early") is not False:
        errors.append("future_events_visible_early must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "event_count": len(event_ids),
        "evaluation_targets": sorted(targets) if isinstance(targets, list) else [],
        "hidden_structure_id": hidden.get("sealed_structure_id"),
    }

def validate_historical_live_proof_case_portfolio(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Combine controlled historical replay with prospective live evidence."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["historical live proof case portfolio must be an object"]}
    for field in (
        "proof_portfolio_id",
        "portfolio_fingerprint",
        "shared_evaluation_contract_id",
        "shared_evaluation_contract_fingerprint",
        "portfolio_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    cases = payload.get("proof_cases")
    if not isinstance(cases, list) or len(cases) < 2:
        errors.append("proof_cases must contain historical replay and prospective live cases")
        cases = []
    case_ids = set()
    case_types = set()
    for index, case in enumerate(cases):
        prefix = f"proof_cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{prefix} must be an object")
            continue
        case_id = case.get("case_id")
        if not _non_empty(case_id):
            errors.append(f"{prefix}.case_id must be a non-empty string")
        elif case_id in case_ids:
            errors.append(f"{prefix}.case_id must be unique")
        case_ids.add(case_id)
        case_type = case.get("case_type")
        if case_type not in {"historical_replay", "prospective_live"}:
            errors.append(f"{prefix}.case_type is not recognized")
        case_types.add(case_type)
        for field in (
            "case_fingerprint",
            "case_domain",
            "sequential_case_protocol_id",
            "information_manifest_id",
            "evaluation_contract_id",
            "case_contribution",
        ):
            if not _non_empty(case.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if case.get("evaluation_contract_id") != payload.get("shared_evaluation_contract_id"):
            errors.append(f"{prefix}.evaluation_contract_id must match the shared contract")
        if case_type == "historical_replay":
            if case.get("outcome_state") != "historical_outcome_sealed":
                errors.append(f"{prefix}.outcome_state must be historical_outcome_sealed")
            if case.get("information_replayable") is not True:
                errors.append(f"{prefix}.information_replayable must be true")
            count = case.get("counterfactual_branch_count")
            if not isinstance(count, int) or isinstance(count, bool) or count < 2:
                errors.append(f"{prefix}.counterfactual_branch_count must be at least two")
            if case.get("prospectively_registered") is not False:
                errors.append(f"{prefix}.prospectively_registered must be false")
        elif case_type == "prospective_live":
            if case.get("outcome_state") != "outcome_pending":
                errors.append(f"{prefix}.outcome_state must be outcome_pending")
            if case.get("prospectively_registered") is not True:
                errors.append(f"{prefix}.prospectively_registered must be true")
            if case.get("external_information_events_logged") is not True:
                errors.append(f"{prefix}.external_information_events_logged must be true")
            if case.get("information_replayable") is not False:
                errors.append(f"{prefix}.information_replayable must be false")
    if case_types != {"historical_replay", "prospective_live"}:
        errors.append("proof_cases must include both historical_replay and prospective_live")

    complement = payload.get("complementarity_contract")
    if not isinstance(complement, dict):
        errors.append("complementarity_contract must be an object")
        complement = {}
    for field in (
        "contract_id",
        "historical_contribution",
        "live_contribution",
        "combined_inference",
        "residual_limitation",
    ):
        if not _non_empty(complement.get(field)):
            errors.append(f"complementarity_contract.{field} must be a non-empty string")
    if complement.get("historical_supplies_information_control") is not True:
        errors.append("complementarity_contract.historical_supplies_information_control must be true")
    if complement.get("historical_supplies_counterfactual_density") is not True:
        errors.append("complementarity_contract.historical_supplies_counterfactual_density must be true")
    if complement.get("live_supplies_temporal_validity") is not True:
        errors.append("complementarity_contract.live_supplies_temporal_validity must be true")
    if complement.get("live_supplies_ecological_validity") is not True:
        errors.append("complementarity_contract.live_supplies_ecological_validity must be true")
    if complement.get("either_case_type_sufficient_alone") is not False:
        errors.append("complementarity_contract.either_case_type_sufficient_alone must be false")
    if payload.get("fully_real_case_only") is not False:
        errors.append("fully_real_case_only must be false")
    if payload.get("historical_replay_only") is not False:
        errors.append("historical_replay_only must be false")
    if payload.get("combined_portfolio_required_for_claim") is not True:
        errors.append("combined_portfolio_required_for_claim must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "case_count": len(case_ids),
        "case_types": sorted(item for item in case_types if _non_empty(item)),
        "combined_portfolio_required": payload.get("combined_portfolio_required_for_claim"),
    }

def validate_original_order_blinded_historical_replay(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Replay original event order while sealing outcome and successful framing."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["original order blinded historical replay must be an object"]}
    for field in (
        "replay_protocol_id",
        "historical_case_id",
        "historical_case_fingerprint",
        "source_archive_id",
        "source_archive_fingerprint",
        "replay_protocol_fingerprint",
        "replay_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    archive = payload.get("original_event_archive")
    if not isinstance(archive, list) or len(archive) < 3:
        errors.append("original_event_archive must contain at least three events")
        archive = []
    archive_by_sequence: Dict[int, Dict[str, Any]] = {}
    archive_ids = set()
    for index, event in enumerate(archive):
        prefix = f"original_event_archive[{index}]"
        if not isinstance(event, dict):
            errors.append(f"{prefix} must be an object")
            continue
        event_id = event.get("event_id")
        if not _non_empty(event_id):
            errors.append(f"{prefix}.event_id must be a non-empty string")
        elif event_id in archive_ids:
            errors.append(f"{prefix}.event_id must be unique")
        archive_ids.add(event_id)
        sequence = event.get("original_sequence")
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
            errors.append(f"{prefix}.original_sequence must be a positive integer")
        elif sequence in archive_by_sequence:
            errors.append(f"{prefix}.original_sequence must be unique")
        else:
            archive_by_sequence[sequence] = event
        for field in ("occurred_at", "event_fingerprint", "source_artifact_id", "source_artifact_fingerprint"):
            if not _non_empty(event.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if set(archive_by_sequence) != set(range(1, len(archive) + 1)):
        errors.append("original event sequence must be contiguous from one")

    reveals = payload.get("replay_reveals")
    if not isinstance(reveals, list) or len(reveals) != len(archive_by_sequence):
        errors.append("replay_reveals must exactly cover the original archive")
        reveals = []
    reveal_packets: Dict[int, str] = {}
    for index, reveal in enumerate(reveals):
        prefix = f"replay_reveals[{index}]"
        if not isinstance(reveal, dict):
            errors.append(f"{prefix} must be an object")
            continue
        sequence = reveal.get("replay_sequence")
        original = archive_by_sequence.get(sequence)
        for field in (
            "reveal_id",
            "source_event_id",
            "source_event_fingerprint",
            "information_packet_id",
            "information_packet_fingerprint",
            "scheduled_reveal_at",
        ):
            if not _non_empty(reveal.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if original is None:
            errors.append(f"{prefix}.replay_sequence must reference the original order")
        else:
            if reveal.get("source_event_id") != original.get("event_id"):
                errors.append(f"{prefix}.source_event_id must match original order")
            if reveal.get("source_event_fingerprint") != original.get("event_fingerprint"):
                errors.append(f"{prefix}.source_event_fingerprint must match original event")
        if isinstance(sequence, int):
            reveal_packets[sequence] = reveal.get("information_packet_fingerprint")
        if reveal.get("future_event_content_included") is not False:
            errors.append(f"{prefix}.future_event_content_included must be false")

    conditions = payload.get("comparison_conditions")
    if not isinstance(conditions, list) or len(conditions) < 2:
        errors.append("comparison_conditions must contain at least two conditions")
        conditions = []
    condition_ids = set()
    for index, condition in enumerate(conditions):
        prefix = f"comparison_conditions[{index}]"
        if not isinstance(condition, dict):
            errors.append(f"{prefix} must be an object")
            continue
        condition_id = condition.get("condition_id")
        if not _non_empty(condition_id):
            errors.append(f"{prefix}.condition_id must be a non-empty string")
        elif condition_id in condition_ids:
            errors.append(f"{prefix}.condition_id must be unique")
        condition_ids.add(condition_id)
        received = condition.get("received_reveals")
        if not isinstance(received, list) or len(received) != len(reveal_packets):
            errors.append(f"{prefix}.received_reveals must cover every replay reveal")
            received = []
        received_map = {}
        for item in received:
            if not isinstance(item, dict):
                errors.append(f"{prefix}.received_reveals items must be objects")
                continue
            received_map[item.get("replay_sequence")] = item.get("information_packet_fingerprint")
        if received_map != reveal_packets:
            errors.append(f"{prefix}.received_reveals must match the common reveal packets and order")
        if condition.get("future_outcome_visible") is not False:
            errors.append(f"{prefix}.future_outcome_visible must be false")
        if condition.get("eventual_successful_framing_visible") is not False:
            errors.append(f"{prefix}.eventual_successful_framing_visible must be false")

    seals = payload.get("hindsight_seals")
    if not isinstance(seals, dict):
        errors.append("hindsight_seals must be an object")
        seals = {}
    for field in (
        "outcome_seal_id",
        "outcome_fingerprint",
        "successful_framing_seal_id",
        "successful_framing_fingerprint",
        "seal_custodian_id",
        "release_condition",
    ):
        if not _non_empty(seals.get(field)):
            errors.append(f"hindsight_seals.{field} must be a non-empty string")
    if seals.get("sealed_before_replay") is not True:
        errors.append("hindsight_seals.sealed_before_replay must be true")
    if seals.get("released_after_all_final_checkpoints") is not True:
        errors.append("hindsight_seals.released_after_all_final_checkpoints must be true")
    if payload.get("original_order_preserved") is not True:
        errors.append("original_order_preserved must be true")
    if payload.get("information_parity_across_conditions") is not True:
        errors.append("information_parity_across_conditions must be true")
    if payload.get("hindsight_leak_detected") is not False:
        errors.append("hindsight_leak_detected must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "replay_event_count": len(reveal_packets),
        "condition_count": len(condition_ids),
        "original_order_preserved": payload.get("original_order_preserved"),
    }

def validate_plural_correct_action_proof_case_set(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Balance proof cases across commit, wait, reject, and minority preservation."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["plural correct action proof case set must be an object"]}
    for field in (
        "case_set_id",
        "case_set_fingerprint",
        "evaluation_contract_id",
        "evaluation_contract_fingerprint",
        "case_set_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    required_actions = {
        "commit_mission",
        "wait",
        "reject",
        "preserve_minority_option",
    }
    cases = payload.get("proof_cases")
    if not isinstance(cases, list) or len(cases) < len(required_actions):
        errors.append("proof_cases must contain at least one case for every correct action")
        cases = []
    case_ids = set()
    action_counts = {action: 0 for action in required_actions}
    for index, case in enumerate(cases):
        prefix = f"proof_cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{prefix} must be an object")
            continue
        case_id = case.get("case_id")
        if not _non_empty(case_id):
            errors.append(f"{prefix}.case_id must be a non-empty string")
        elif case_id in case_ids:
            errors.append(f"{prefix}.case_id must be unique")
        case_ids.add(case_id)
        for field in (
            "case_fingerprint",
            "sequential_case_protocol_id",
            "correct_action_seal_id",
            "correct_action_seal_fingerprint",
            "correctness_rationale",
            "decisive_evidence_fingerprint",
            "discriminating_observation",
            "incorrect_action_consequence",
        ):
            if not _non_empty(case.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        action = case.get("precommitted_correct_action")
        if action not in required_actions:
            errors.append(f"{prefix}.precommitted_correct_action is not recognized")
        else:
            action_counts[action] += 1
        if case.get("correct_action_sealed_before_condition_outputs") is not True:
            errors.append(f"{prefix}.correct_action_sealed_before_condition_outputs must be true")
        if case.get("mission_creation_required") is not (action == "commit_mission"):
            errors.append(f"{prefix}.mission_creation_required must follow the precommitted correct action")
    if set(action for action, count in action_counts.items() if count > 0) != required_actions:
        errors.append("proof_cases must cover commit, wait, reject, and preserve_minority_option")

    scoring = payload.get("scoring_contract")
    if not isinstance(scoring, dict):
        errors.append("scoring_contract must be an object")
        scoring = {}
    for field in (
        "scoring_contract_id",
        "action_correctness_measure",
        "false_positive_mission_penalty",
        "false_negative_mission_penalty",
        "minority_option_loss_penalty",
        "wait_information_gain_measure",
    ):
        if not _non_empty(scoring.get(field)):
            errors.append(f"scoring_contract.{field} must be a non-empty string")
    if scoring.get("mission_generation_receives_default_credit") is not False:
        errors.append("scoring_contract.mission_generation_receives_default_credit must be false")
    if scoring.get("activity_volume_receives_credit") is not False:
        errors.append("scoring_contract.activity_volume_receives_credit must be false")
    if scoring.get("correct_non_action_can_receive_full_credit") is not True:
        errors.append("scoring_contract.correct_non_action_can_receive_full_credit must be true")
    if payload.get("all_cases_expect_mission") is not False:
        errors.append("all_cases_expect_mission must be false")
    if payload.get("mission_manufacturing_bias_allowed") is not False:
        errors.append("mission_manufacturing_bias_allowed must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "case_count": len(case_ids),
        "correct_action_counts": action_counts,
        "covered_actions": sorted(action for action, count in action_counts.items() if count > 0),
    }

def validate_adversarial_purpose_pressure_case_set(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Cover five adversarial pressures that can corrupt purpose formation."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["adversarial purpose pressure case set must be an object"]}
    for field in (
        "pressure_case_set_id",
        "case_set_fingerprint",
        "evaluation_contract_id",
        "evaluation_contract_fingerprint",
        "case_set_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    required_pressures = {
        "manipulated_urgency",
        "misleading_demand",
        "founder_preference_conflict",
        "privacy_risk",
        "self_expansion_mission",
    }
    cases = payload.get("pressure_cases")
    if not isinstance(cases, list) or len(cases) != len(required_pressures):
        errors.append("pressure_cases must contain exactly the five adversarial pressures")
        cases = []
    observed = set()
    case_ids = set()
    for index, case in enumerate(cases):
        prefix = f"pressure_cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{prefix} must be an object")
            continue
        case_id = case.get("case_id")
        if not _non_empty(case_id):
            errors.append(f"{prefix}.case_id must be a non-empty string")
        elif case_id in case_ids:
            errors.append(f"{prefix}.case_id must be unique")
        case_ids.add(case_id)
        pressure = case.get("pressure_type")
        if pressure not in required_pressures:
            errors.append(f"{prefix}.pressure_type is not recognized")
        elif pressure in observed:
            errors.append(f"{prefix}.pressure_type must be unique")
        observed.add(pressure)
        for field in (
            "case_fingerprint",
            "sequential_case_protocol_id",
            "pressure_ground_truth_seal_id",
            "pressure_ground_truth_fingerprint",
            "detection_signal",
            "constitutional_or_authority_boundary_id",
            "correct_action",
            "failure_consequence",
        ):
            if not _non_empty(case.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if case.get("pressure_ground_truth_sealed_before_outputs") is not True:
            errors.append(f"{prefix}.pressure_ground_truth_sealed_before_outputs must be true")
        if case.get("pressure_label_visible_to_participants") is not False:
            errors.append(f"{prefix}.pressure_label_visible_to_participants must be false")
        details = case.get("typed_details")
        if not isinstance(details, dict):
            errors.append(f"{prefix}.typed_details must be an object")
            details = {}
        if pressure == "manipulated_urgency":
            for field in ("claimed_deadline", "deadline_verification_source", "verified_deadline", "manipulation_mechanism"):
                if not _non_empty(details.get(field)):
                    errors.append(f"{prefix} manipulated urgency requires typed_details.{field}")
        elif pressure == "misleading_demand":
            for field in ("apparent_demand_evidence", "authenticity_check", "beneficiary_burden", "demand_distortion_mechanism"):
                if not _non_empty(details.get(field)):
                    errors.append(f"{prefix} misleading demand requires typed_details.{field}")
        elif pressure == "founder_preference_conflict":
            for field in ("founder_preference", "conflicting_beneficiary_evidence", "preference_authority_scope", "conflict_resolution_rule"):
                if not _non_empty(details.get(field)):
                    errors.append(f"{prefix} founder preference conflict requires typed_details.{field}")
        elif pressure == "privacy_risk":
            for field in ("requested_sensitive_data", "necessity_test", "minimum_data_alternative", "privacy_harm_threshold"):
                if not _non_empty(details.get(field)):
                    errors.append(f"{prefix} privacy risk requires typed_details.{field}")
        elif pressure == "self_expansion_mission":
            for field in ("agent_capability_benefit", "missing_beneficiary_outcome", "requested_authority_expansion", "rejection_criterion"):
                if not _non_empty(details.get(field)):
                    errors.append(f"{prefix} self expansion mission requires typed_details.{field}")
            if details.get("self_preservation_or_growth_is_value") is not False:
                errors.append(f"{prefix}.typed_details.self_preservation_or_growth_is_value must be false")
    if observed != required_pressures:
        errors.append("pressure_cases must cover every adversarial pressure exactly once")

    scoring = payload.get("adversarial_scoring")
    if not isinstance(scoring, dict):
        errors.append("adversarial_scoring must be an object")
        scoring = {}
    for field in (
        "scoring_contract_id",
        "pressure_detection_measure",
        "boundary_application_measure",
        "correct_action_measure",
        "explanation_quality_measure",
    ):
        if not _non_empty(scoring.get(field)):
            errors.append(f"adversarial_scoring.{field} must be a non-empty string")
    if scoring.get("surface_compliance_receives_credit") is not False:
        errors.append("adversarial_scoring.surface_compliance_receives_credit must be false")
    if scoring.get("pressure_resistance_requires_evidence") is not True:
        errors.append("adversarial_scoring.pressure_resistance_requires_evidence must be true")
    if payload.get("answer_cues_present_in_participant_packets") is not False:
        errors.append("answer_cues_present_in_participant_packets must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "pressure_case_count": len(case_ids),
        "covered_pressures": sorted(item for item in observed if _non_empty(item)),
    }

def validate_historical_decision_independent_evaluation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate contemporaneous reasoning without treating history as truth."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["historical decision independent evaluation must be an object"]}
    for field in (
        "evaluation_record_id",
        "historical_case_id",
        "historical_case_fingerprint",
        "condition_output_id",
        "condition_output_fingerprint",
        "evaluator_id",
        "evaluation_fingerprint",
        "evaluation_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    historical = payload.get("historical_record")
    if not isinstance(historical, dict):
        errors.append("historical_record must be an object")
        historical = {}
    for field in (
        "historical_decision_artifact_id",
        "historical_decision_fingerprint",
        "later_outcome_artifact_id",
        "later_outcome_fingerprint",
        "contemporaneous_information_packet_id",
        "contemporaneous_information_fingerprint",
    ):
        if not _non_empty(historical.get(field)):
            errors.append(f"historical_record.{field} must be a non-empty string")
    if historical.get("historical_decision_is_ground_truth") is not False:
        errors.append("historical_record.historical_decision_is_ground_truth must be false")
    if historical.get("decision_and_outcome_separately_sealed") is not True:
        errors.append("historical_record.decision_and_outcome_separately_sealed must be true")

    required_dimensions = {
        "contemporaneous_justification",
        "missed_alternatives",
        "forecast_calibration",
        "later_consequence",
    }
    dimensions = payload.get("dimension_evaluations")
    if not isinstance(dimensions, list) or len(dimensions) != len(required_dimensions):
        errors.append("dimension_evaluations must contain exactly four evaluation dimensions")
        dimensions = []
    observed = set()
    scores = {}
    for index, dimension in enumerate(dimensions):
        prefix = f"dimension_evaluations[{index}]"
        if not isinstance(dimension, dict):
            errors.append(f"{prefix} must be an object")
            continue
        name = dimension.get("dimension")
        if name not in required_dimensions:
            errors.append(f"{prefix}.dimension is not recognized")
        elif name in observed:
            errors.append(f"{prefix}.dimension must be unique")
        observed.add(name)
        score = dimension.get("score")
        if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 4:
            errors.append(f"{prefix}.score must be an integer from zero through four")
        elif name in required_dimensions:
            scores[name] = score
        for field in ("rubric_anchor", "evidence_artifact_id", "assessment_rationale", "uncertainty"):
            if not _non_empty(dimension.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        details = dimension.get("typed_details")
        if not isinstance(details, dict):
            errors.append(f"{prefix}.typed_details must be an object")
            details = {}
        if name == "contemporaneous_justification":
            for field in ("information_packet_id", "decision_claim", "evidence_available_then"):
                if not _non_empty(details.get(field)):
                    errors.append(f"{prefix} contemporaneous justification requires typed_details.{field}")
            if details.get("information_packet_id") != historical.get("contemporaneous_information_packet_id"):
                errors.append(f"{prefix}.typed_details.information_packet_id must match contemporaneous information")
            if details.get("future_outcome_used") is not False:
                errors.append(f"{prefix}.typed_details.future_outcome_used must be false")
        elif name == "missed_alternatives":
            alternatives = details.get("plausible_alternatives")
            if not isinstance(alternatives, list) or not alternatives or not all(_non_empty(item) for item in alternatives):
                errors.append(f"{prefix}.typed_details.plausible_alternatives must be non-empty")
            if not _non_empty(details.get("search_coverage_basis")):
                errors.append(f"{prefix}.typed_details.search_coverage_basis must be non-empty")
        elif name == "forecast_calibration":
            for field in ("forecast_record_id", "forecast_probability", "observed_outcome", "calibration_measure"):
                if not _non_empty(details.get(field)):
                    errors.append(f"{prefix} forecast calibration requires typed_details.{field}")
            if details.get("forecast_frozen_before_outcome") is not True:
                errors.append(f"{prefix}.typed_details.forecast_frozen_before_outcome must be true")
        elif name == "later_consequence":
            for field in ("outcome_artifact_id", "observed_consequence", "causal_attribution_status", "counterfactual_uncertainty"):
                if not _non_empty(details.get(field)):
                    errors.append(f"{prefix} later consequence requires typed_details.{field}")
            if details.get("outcome_artifact_id") != historical.get("later_outcome_artifact_id"):
                errors.append(f"{prefix}.typed_details.outcome_artifact_id must match later outcome")
            if details.get("consequence_retroactively_defines_justification") is not False:
                errors.append(f"{prefix}.typed_details.consequence_retroactively_defines_justification must be false")
    if observed != required_dimensions:
        errors.append("dimension_evaluations must cover all four dimensions exactly once")
    if payload.get("historical_decision_match_receives_credit") is not False:
        errors.append("historical_decision_match_receives_credit must be false")
    if payload.get("later_success_erases_bad_reasoning") is not False:
        errors.append("later_success_erases_bad_reasoning must be false")
    if payload.get("later_failure_erases_good_contemporaneous_reasoning") is not False:
        errors.append("later_failure_erases_good_contemporaneous_reasoning must be false")
    if payload.get("dimensions_reported_separately") is not True:
        errors.append("dimensions_reported_separately must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "dimension_scores": scores,
        "dimension_count": len(observed),
        "historical_decision_is_ground_truth": historical.get("historical_decision_is_ground_truth"),
    }

def validate_actual_timeboxed_human_baseline(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require real consented human participants under a frozen time-boxed protocol."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["actual timeboxed human baseline must be an object"]}
    for field in (
        "human_baseline_protocol_id",
        "proof_case_id",
        "visible_information_manifest_id",
        "visible_information_manifest_fingerprint",
        "constitution_id",
        "constitution_fingerprint",
        "protocol_fingerprint",
        "baseline_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    recruitment = payload.get("recruitment_protocol")
    if not isinstance(recruitment, dict):
        errors.append("recruitment_protocol must be an object")
        recruitment = {}
    for field in (
        "recruitment_record_id",
        "eligibility_criteria",
        "exclusion_criteria",
        "competence_basis",
        "recruitment_channel",
        "compensation_terms",
    ):
        if not _non_empty(recruitment.get(field)):
            errors.append(f"recruitment_protocol.{field} must be a non-empty string")
    if recruitment.get("criteria_preregistered") is not True:
        errors.append("recruitment_protocol.criteria_preregistered must be true")
    if recruitment.get("selected_by_observed_performance") is not False:
        errors.append("recruitment_protocol.selected_by_observed_performance must be false")

    participants = payload.get("participants")
    if not isinstance(participants, list) or len(participants) < 3:
        errors.append("participants must contain at least three actual humans")
        participants = []
    participant_ids = set()
    for index, participant in enumerate(participants):
        prefix = f"participants[{index}]"
        if not isinstance(participant, dict):
            errors.append(f"{prefix} must be an object")
            continue
        participant_id = participant.get("participant_id")
        if not _non_empty(participant_id):
            errors.append(f"{prefix}.participant_id must be a non-empty string")
        elif participant_id in participant_ids:
            errors.append(f"{prefix}.participant_id must be unique")
        participant_ids.add(participant_id)
        for field in (
            "eligibility_verification_id",
            "consent_record_id",
            "compensation_record_id",
            "session_id",
        ):
            if not _non_empty(participant.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if participant.get("actual_human_participant") is not True:
            errors.append(f"{prefix}.actual_human_participant must be true")
        if participant.get("informed_consent_obtained") is not True:
            errors.append(f"{prefix}.informed_consent_obtained must be true")
        if participant.get("withdrawal_right_preserved") is not True:
            errors.append(f"{prefix}.withdrawal_right_preserved must be true")
        if participant.get("developer_authored_proxy_output") is not False:
            errors.append(f"{prefix}.developer_authored_proxy_output must be false")

    timeboxes = payload.get("event_timeboxes")
    if not isinstance(timeboxes, list) or not timeboxes:
        errors.append("event_timeboxes must be a non-empty list")
        timeboxes = []
    event_ids = set()
    sequences = set()
    for index, timebox in enumerate(timeboxes):
        prefix = f"event_timeboxes[{index}]"
        if not isinstance(timebox, dict):
            errors.append(f"{prefix} must be an object")
            continue
        event_id = timebox.get("event_id")
        if not _non_empty(event_id):
            errors.append(f"{prefix}.event_id must be a non-empty string")
        elif event_id in event_ids:
            errors.append(f"{prefix}.event_id must be unique")
        event_ids.add(event_id)
        sequence = timebox.get("sequence")
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
            errors.append(f"{prefix}.sequence must be a positive integer")
        elif sequence in sequences:
            errors.append(f"{prefix}.sequence must be unique")
        sequences.add(sequence)
        minutes = timebox.get("minutes_per_participant")
        if not isinstance(minutes, int) or isinstance(minutes, bool) or minutes < 1:
            errors.append(f"{prefix}.minutes_per_participant must be a positive integer")
        for field in ("information_packet_fingerprint", "required_output_contract_id"):
            if not _non_empty(timebox.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if timebox.get("same_timebox_for_all_participants") is not True:
            errors.append(f"{prefix}.same_timebox_for_all_participants must be true")
        if timebox.get("future_events_visible") is not False:
            errors.append(f"{prefix}.future_events_visible must be false")
    if sequences != set(range(1, len(timeboxes) + 1)):
        errors.append("event timebox sequence must be contiguous from one")

    submissions = payload.get("participant_submissions")
    expected_pairs = {(participant, event) for participant in participant_ids for event in event_ids}
    if not isinstance(submissions, list) or len(submissions) != len(expected_pairs):
        errors.append("participant_submissions must cover every participant-event pair")
        submissions = []
    observed_pairs = set()
    for index, submission in enumerate(submissions):
        prefix = f"participant_submissions[{index}]"
        if not isinstance(submission, dict):
            errors.append(f"{prefix} must be an object")
            continue
        pair = (submission.get("participant_id"), submission.get("event_id"))
        if pair not in expected_pairs:
            errors.append(f"{prefix} must reference a known participant and event")
        elif pair in observed_pairs:
            errors.append(f"{prefix} participant-event pair must be unique")
        observed_pairs.add(pair)
        for field in ("submission_id", "submission_fingerprint", "submitted_at"):
            if not _non_empty(submission.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if submission.get("independently_authored") is not True:
            errors.append(f"{prefix}.independently_authored must be true")
        if submission.get("frozen_before_next_event") is not True:
            errors.append(f"{prefix}.frozen_before_next_event must be true")
        if submission.get("within_timebox") is not True:
            errors.append(f"{prefix}.within_timebox must be true")
    if observed_pairs != expected_pairs:
        errors.append("participant_submissions must exactly cover every participant-event pair")
    if payload.get("developer_written_human_caricature_used") is not False:
        errors.append("developer_written_human_caricature_used must be false")
    if payload.get("same_visible_events_and_constitution") is not True:
        errors.append("same_visible_events_and_constitution must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "participant_count": len(participant_ids),
        "event_count": len(event_ids),
        "submission_count": len(observed_pairs),
    }

def validate_equal_information_one_shot_agent_baseline(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Define a strong fresh-context agent baseline without persistent cognition."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["equal information one shot agent baseline must be an object"]}
    for field in (
        "one_shot_baseline_protocol_id",
        "proof_case_id",
        "visible_information_manifest_id",
        "visible_information_manifest_fingerprint",
        "constitution_id",
        "constitution_fingerprint",
        "model_runtime_fingerprint",
        "baseline_prompt_id",
        "baseline_prompt_fingerprint",
        "output_contract_id",
        "protocol_fingerprint",
        "baseline_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    checkpoints = payload.get("checkpoint_calls")
    if not isinstance(checkpoints, list) or not checkpoints:
        errors.append("checkpoint_calls must be a non-empty list")
        checkpoints = []
    event_ids = set()
    sequences = set()
    for index, checkpoint in enumerate(checkpoints):
        prefix = f"checkpoint_calls[{index}]"
        if not isinstance(checkpoint, dict):
            errors.append(f"{prefix} must be an object")
            continue
        event_id = checkpoint.get("event_id")
        if not _non_empty(event_id):
            errors.append(f"{prefix}.event_id must be a non-empty string")
        elif event_id in event_ids:
            errors.append(f"{prefix}.event_id must be unique")
        event_ids.add(event_id)
        sequence = checkpoint.get("sequence")
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
            errors.append(f"{prefix}.sequence must be a positive integer")
        elif sequence in sequences:
            errors.append(f"{prefix}.sequence must be unique")
        sequences.add(sequence)
        for field in (
            "cumulative_visible_packet_id",
            "cumulative_visible_packet_fingerprint",
            "constitution_fingerprint",
            "call_record_id",
            "call_input_fingerprint",
            "output_artifact_id",
            "output_fingerprint",
            "completed_at",
        ):
            if not _non_empty(checkpoint.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if checkpoint.get("constitution_fingerprint") != payload.get("constitution_fingerprint"):
            errors.append(f"{prefix}.constitution_fingerprint must match the shared constitution")
        if checkpoint.get("model_call_count") != 1:
            errors.append(f"{prefix}.model_call_count must be exactly one")
        for field in (
            "fresh_context_started",
            "all_current_visible_events_included",
            "output_frozen_before_next_event",
        ):
            if checkpoint.get(field) is not True:
                errors.append(f"{prefix}.{field} must be true")
        for field in (
            "prior_output_included",
            "persistent_memory_loaded",
            "persistent_frontier_loaded",
            "staged_independent_roles_used",
            "intermediate_model_calls_used",
        ):
            if checkpoint.get(field) is not False:
                errors.append(f"{prefix}.{field} must be false")
    if sequences != set(range(1, len(checkpoints) + 1)):
        errors.append("checkpoint call sequence must be contiguous from one")

    resource = payload.get("resource_contract")
    if not isinstance(resource, dict):
        errors.append("resource_contract must be an object")
        resource = {}
    for field in ("resource_contract_id", "time_limit", "input_token_limit", "output_token_limit", "tool_policy"):
        if not _non_empty(resource.get(field)):
            errors.append(f"resource_contract.{field} must be a non-empty string")
    if resource.get("same_visible_information_as_palamedes") is not True:
        errors.append("resource_contract.same_visible_information_as_palamedes must be true")
    if resource.get("same_constitution_as_palamedes") is not True:
        errors.append("resource_contract.same_constitution_as_palamedes must be true")
    if resource.get("weakened_prompt_for_baseline") is not False:
        errors.append("resource_contract.weakened_prompt_for_baseline must be false")
    if payload.get("persistent_frontier_available") is not False:
        errors.append("persistent_frontier_available must be false")
    if payload.get("staged_independent_operations_available") is not False:
        errors.append("staged_independent_operations_available must be false")
    if payload.get("same_visible_events_and_constitution") is not True:
        errors.append("same_visible_events_and_constitution must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "checkpoint_count": len(event_ids),
        "model_call_count": sum(
            checkpoint.get("model_call_count", 0)
            for checkpoint in checkpoints
            if isinstance(checkpoint, dict) and isinstance(checkpoint.get("model_call_count"), int)
        ),
    }

def validate_blinded_separate_axis_judging(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Assign distinct blinded panels to five non-substitutable proof axes."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["blinded separate axis judging must be an object"]}
    for field in (
        "judging_protocol_id",
        "proof_case_id",
        "condition_identity_seal_id",
        "condition_identity_seal_fingerprint",
        "protocol_fingerprint",
        "judging_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    outputs = payload.get("blinded_condition_outputs")
    if not isinstance(outputs, list) or len(outputs) < 3:
        errors.append("blinded_condition_outputs must contain at least three conditions")
        outputs = []
    blinded_ids = set()
    source_fingerprints = set()
    presentation_orders = set()
    for index, output in enumerate(outputs):
        prefix = f"blinded_condition_outputs[{index}]"
        if not isinstance(output, dict):
            errors.append(f"{prefix} must be an object")
            continue
        blinded_id = output.get("blinded_output_id")
        if not _non_empty(blinded_id):
            errors.append(f"{prefix}.blinded_output_id must be a non-empty string")
        elif blinded_id in blinded_ids:
            errors.append(f"{prefix}.blinded_output_id must be unique")
        blinded_ids.add(blinded_id)
        for field in ("blinded_output_fingerprint", "source_output_fingerprint", "normalization_record_id"):
            if not _non_empty(output.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        source_fingerprints.add(output.get("source_output_fingerprint"))
        order = output.get("presentation_order")
        if not isinstance(order, int) or isinstance(order, bool) or order < 1:
            errors.append(f"{prefix}.presentation_order must be a positive integer")
        elif order in presentation_orders:
            errors.append(f"{prefix}.presentation_order must be unique")
        presentation_orders.add(order)
        if output.get("condition_identity_visible") is not False:
            errors.append(f"{prefix}.condition_identity_visible must be false")
        if output.get("condition_specific_branding_removed") is not True:
            errors.append(f"{prefix}.condition_specific_branding_removed must be true")
        if output.get("semantic_content_changed_by_normalization") is not False:
            errors.append(f"{prefix}.semantic_content_changed_by_normalization must be false")
    if len(source_fingerprints) != len(outputs):
        errors.append("each blinded output must reference a distinct source output")
    if presentation_orders != set(range(1, len(outputs) + 1)):
        errors.append("presentation_order must be contiguous from one")

    required_axes = {
        "beneficiary_outcome",
        "constitutional_reasoning",
        "originality",
        "planner_burden",
        "proxy_risk",
    }
    axes = payload.get("axis_panels")
    if not isinstance(axes, list) or len(axes) != len(required_axes):
        errors.append("axis_panels must contain exactly five evaluation axes")
        axes = []
    observed_axes = set()
    global_judges = set()
    for index, panel in enumerate(axes):
        prefix = f"axis_panels[{index}]"
        if not isinstance(panel, dict):
            errors.append(f"{prefix} must be an object")
            continue
        axis = panel.get("axis")
        if axis not in required_axes:
            errors.append(f"{prefix}.axis is not recognized")
        elif axis in observed_axes:
            errors.append(f"{prefix}.axis must be unique")
        observed_axes.add(axis)
        for field in (
            "panel_id",
            "rubric_id",
            "rubric_fingerprint",
            "axis_evidence_packet_id",
            "axis_evidence_packet_fingerprint",
            "axis_result_artifact_id",
        ):
            if not _non_empty(panel.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        judges = panel.get("judges")
        if not isinstance(judges, list) or len(judges) < 2:
            errors.append(f"{prefix}.judges must contain at least two judges")
            judges = []
        panel_judges = set()
        for judge_index, judge in enumerate(judges):
            judge_prefix = f"{prefix}.judges[{judge_index}]"
            if not isinstance(judge, dict):
                errors.append(f"{judge_prefix} must be an object")
                continue
            judge_id = judge.get("judge_id")
            if not _non_empty(judge_id):
                errors.append(f"{judge_prefix}.judge_id must be a non-empty string")
            elif judge_id in panel_judges or judge_id in global_judges:
                errors.append(f"{judge_prefix}.judge_id must be unique across panels")
            panel_judges.add(judge_id)
            global_judges.add(judge_id)
            for field in ("expertise_basis", "independence_record_id", "score_record_id"):
                if not _non_empty(judge.get(field)):
                    errors.append(f"{judge_prefix}.{field} must be a non-empty string")
            if judge.get("condition_identity_visible") is not False:
                errors.append(f"{judge_prefix}.condition_identity_visible must be false")
            if judge.get("other_axis_scores_visible") is not False:
                errors.append(f"{judge_prefix}.other_axis_scores_visible must be false")
        for field in (
            "rubric_frozen_before_outputs",
            "axis_evidence_only",
            "panel_independent",
        ):
            if panel.get(field) is not True:
                errors.append(f"{prefix}.{field} must be true")
    if observed_axes != required_axes:
        errors.append("axis_panels must cover all five evaluation axes exactly once")
    if payload.get("condition_identity_map_sealed_until_all_scores") is not True:
        errors.append("condition_identity_map_sealed_until_all_scores must be true")
    if payload.get("single_holistic_judge_used") is not False:
        errors.append("single_holistic_judge_used must be false")
    if payload.get("axis_results_reported_separately") is not True:
        errors.append("axis_results_reported_separately must be true")
    if payload.get("global_impression_score_used") is not False:
        errors.append("global_impression_score_used must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "blinded_output_count": len(blinded_ids),
        "axis_count": len(observed_axes),
        "judge_count": len(global_judges),
    }

def validate_external_proof_dataset_thesis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Integrate dynamic cases, real baselines, and blinded outcome-aware review."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["external proof dataset thesis must be an object"]}
    for field in (
        "dataset_thesis_id",
        "dataset_id",
        "dataset_version",
        "dataset_fingerprint",
        "evaluation_contract_id",
        "evaluation_contract_fingerprint",
        "thesis_fingerprint",
        "thesis_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected_components = {
        "sequential_hidden_cases": "validate_sequential_hidden_causal_proof_case",
        "historical_live_portfolio": "validate_historical_live_proof_case_portfolio",
        "blinded_historical_replay": "validate_original_order_blinded_historical_replay",
        "plural_correct_actions": "validate_plural_correct_action_proof_case_set",
        "adversarial_pressures": "validate_adversarial_purpose_pressure_case_set",
        "historical_independent_evaluation": "validate_historical_decision_independent_evaluation",
        "actual_human_baseline": "validate_actual_timeboxed_human_baseline",
        "one_shot_agent_baseline": "validate_equal_information_one_shot_agent_baseline",
        "separate_axis_judging": "validate_blinded_separate_axis_judging",
    }
    components = payload.get("component_evidence")
    if not isinstance(components, list) or len(components) != len(expected_components):
        errors.append("component_evidence must contain exactly the nine dataset components")
        components = []
    observed = set()
    for index, component in enumerate(components):
        prefix = f"component_evidence[{index}]"
        if not isinstance(component, dict):
            errors.append(f"{prefix} must be an object")
            continue
        name = component.get("component")
        if name in observed:
            errors.append(f"{prefix}.component must be unique")
        observed.add(name)
        validator = expected_components.get(name)
        if validator is None:
            errors.append(f"{prefix}.component is not recognized")
        elif component.get("validator_id") != validator:
            errors.append(f"{prefix}.validator_id must be {validator}")
        for field in ("evidence_artifact_id", "evidence_fingerprint", "verification_record_id"):
            if not _non_empty(component.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if component.get("verified") is not True:
            errors.append(f"{prefix}.verified must be true")
    if observed != set(expected_components):
        errors.append("component_evidence must cover all dataset components exactly once")

    manifest = payload.get("dataset_manifest")
    if not isinstance(manifest, dict):
        errors.append("dataset_manifest must be an object")
        manifest = {}
    for field in (
        "manifest_id",
        "manifest_fingerprint",
        "historical_case_index_id",
        "prospective_case_registry_id",
        "adversarial_case_index_id",
        "baseline_registry_id",
        "blinding_registry_id",
        "outcome_registry_id",
    ):
        if not _non_empty(manifest.get(field)):
            errors.append(f"dataset_manifest.{field} must be a non-empty string")
    for field in (
        "sequential_events_required",
        "future_information_sealed",
        "historical_and_live_cases_present",
        "real_human_and_one_shot_agent_baselines_present",
        "plural_correct_actions_present",
        "adversarial_pressures_present",
        "outcome_aware_review_present",
        "axis_results_separate",
    ):
        if manifest.get(field) is not True:
            errors.append(f"dataset_manifest.{field} must be true")
    for field in (
        "historical_decision_used_as_truth",
        "condition_identity_visible_to_judges",
        "synthetic_idea_score_used_as_primary_proof",
    ):
        if manifest.get(field) is not False:
            errors.append(f"dataset_manifest.{field} must be false")

    claim = payload.get("claim_boundary")
    if not isinstance(claim, dict):
        errors.append("claim_boundary must be an object")
        claim = {}
    for field in (
        "claim_id",
        "supported_claim",
        "unsupported_claim",
        "generalization_limit",
        "next_evidence_required",
    ):
        if not _non_empty(claim.get(field)):
            errors.append(f"claim_boundary.{field} must be a non-empty string")
    if claim.get("dataset_proves_universal_superiority") is not False:
        errors.append("claim_boundary.dataset_proves_universal_superiority must be false")
    if claim.get("dataset_supports_bounded_comparison") is not True:
        errors.append("claim_boundary.dataset_supports_bounded_comparison must be true")
    if payload.get("dataset_thesis_status") != "integrated":
        errors.append("dataset_thesis_status must be integrated")
    return {
        "valid": not errors,
        "errors": errors,
        "component_count": len(observed),
        "dataset_thesis_status": payload.get("dataset_thesis_status"),
        "dataset_id": payload.get("dataset_id"),
    }

def validate_quality_resource_budget_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Report information, compute, latency, and human labor beside quality."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["quality resource budget report must be an object"]}
    for field in (
        "budget_report_id",
        "proof_case_id",
        "evaluation_contract_id",
        "visible_information_manifest_id",
        "visible_information_manifest_fingerprint",
        "report_fingerprint",
        "report_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    required_conditions = {"human", "one_shot_agent", "palamedes"}
    conditions = payload.get("condition_reports")
    if not isinstance(conditions, list) or len(conditions) != len(required_conditions):
        errors.append("condition_reports must contain human, one_shot_agent, and palamedes")
        conditions = []
    observed = set()
    totals_by_condition: Dict[str, Dict[str, float]] = {}
    numeric_fields = {
        "information_budget": (
            "visible_artifact_count",
            "visible_input_tokens",
            "privileged_artifact_count",
        ),
        "compute_budget": (
            "model_call_count",
            "input_token_count",
            "output_token_count",
            "accelerator_seconds",
            "estimated_cost",
        ),
        "latency_budget": (
            "wall_clock_seconds",
            "decision_latency_seconds",
        ),
        "human_labor_budget": (
            "participant_minutes",
            "operator_intervention_minutes",
            "developer_correction_minutes",
            "evaluation_minutes",
            "intervention_count",
            "correction_count",
        ),
    }
    for index, condition in enumerate(conditions):
        prefix = f"condition_reports[{index}]"
        if not isinstance(condition, dict):
            errors.append(f"{prefix} must be an object")
            continue
        condition_id = condition.get("condition")
        if condition_id not in required_conditions:
            errors.append(f"{prefix}.condition is not recognized")
        elif condition_id in observed:
            errors.append(f"{prefix}.condition must be unique")
        observed.add(condition_id)
        for field in (
            "condition_runtime_fingerprint",
            "quality_result_artifact_id",
            "quality_result_fingerprint",
            "quality_summary",
        ):
            if not _non_empty(condition.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        condition_totals: Dict[str, float] = {}
        for budget_name, fields in numeric_fields.items():
            budget = condition.get(budget_name)
            if not isinstance(budget, dict):
                errors.append(f"{prefix}.{budget_name} must be an object")
                budget = {}
            for field in fields:
                value = budget.get(field)
                if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
                    errors.append(f"{prefix}.{budget_name}.{field} must be a non-negative number")
                    value = 0
                condition_totals[f"{budget_name}.{field}"] = value
            for field in ("measurement_record_id", "measurement_method"):
                if not _non_empty(budget.get(field)):
                    errors.append(f"{prefix}.{budget_name}.{field} must be a non-empty string")
            if budget_name == "information_budget":
                if budget.get("visible_information_manifest_fingerprint") != payload.get("visible_information_manifest_fingerprint"):
                    errors.append(f"{prefix}.information_budget manifest must match the shared visible information")
            units = budget.get("units")
            if (
                not isinstance(units, dict)
                or set(units) != set(fields)
                or not all(_non_empty(units.get(field)) for field in fields)
            ):
                errors.append(f"{prefix}.{budget_name}.units must name every numeric field")
        totals_by_condition[condition_id] = condition_totals
        declared = condition.get("declared_budget_totals")
        if not isinstance(declared, dict):
            errors.append(f"{prefix}.declared_budget_totals must be an object")
            declared = {}
        expected_totals = {
            "compute_tokens": (
                condition_totals.get("compute_budget.input_token_count", 0)
                + condition_totals.get("compute_budget.output_token_count", 0)
            ),
            "human_labor_minutes": sum(
                condition_totals.get(f"human_labor_budget.{field}", 0)
                for field in (
                    "participant_minutes",
                    "operator_intervention_minutes",
                    "developer_correction_minutes",
                    "evaluation_minutes",
                )
            ),
        }
        for field, expected in expected_totals.items():
            if declared.get(field) != expected:
                errors.append(f"{prefix}.declared_budget_totals.{field} must equal measured components")
    if observed != required_conditions:
        errors.append("condition_reports must cover all three conditions exactly once")
    if payload.get("quality_and_resources_reported_together") is not True:
        errors.append("quality_and_resources_reported_together must be true")
    if payload.get("win_rate_reported_alone") is not False:
        errors.append("win_rate_reported_alone must be false")
    if payload.get("human_correction_hidden") is not False:
        errors.append("human_correction_hidden must be false")
    if payload.get("compute_advantage_hidden") is not False:
        errors.append("compute_advantage_hidden must be false")
    if payload.get("resource_missingness_treated_as_zero") is not False:
        errors.append("resource_missingness_treated_as_zero must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "condition_count": len(observed),
        "reported_conditions": sorted(item for item in observed if _non_empty(item)),
    }

def validate_six_dimension_mission_quality_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Report six non-substitutable dimensions of mission quality."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["six dimension mission quality report must be an object"]}
    for field in (
        "mission_quality_report_id",
        "mission_contract_id",
        "mission_contract_fingerprint",
        "condition_output_id",
        "condition_output_fingerprint",
        "evaluation_contract_id",
        "report_fingerprint",
        "report_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    required_dimensions = {
        "beneficiary_relevance",
        "causal_defensibility",
        "constitutional_fit",
        "useful_frame_originality",
        "feasibility",
        "disconfirmation",
    }
    dimensions = payload.get("dimension_assessments")
    if not isinstance(dimensions, list) or len(dimensions) != len(required_dimensions):
        errors.append("dimension_assessments must contain exactly six mission quality dimensions")
        dimensions = []
    observed = set()
    scores = {}
    for index, assessment in enumerate(dimensions):
        prefix = f"dimension_assessments[{index}]"
        if not isinstance(assessment, dict):
            errors.append(f"{prefix} must be an object")
            continue
        dimension = assessment.get("dimension")
        if dimension not in required_dimensions:
            errors.append(f"{prefix}.dimension is not recognized")
        elif dimension in observed:
            errors.append(f"{prefix}.dimension must be unique")
        observed.add(dimension)
        score = assessment.get("score")
        if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 4:
            errors.append(f"{prefix}.score must be an integer from zero through four")
        elif dimension in required_dimensions:
            scores[dimension] = score
        for field in (
            "rubric_id",
            "rubric_anchor",
            "evidence_artifact_id",
            "evidence_fingerprint",
            "assessment_rationale",
            "uncertainty",
            "improvement_required",
        ):
            if not _non_empty(assessment.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        details = assessment.get("typed_details")
        if not isinstance(details, dict):
            errors.append(f"{prefix}.typed_details must be an object")
            details = {}
        fields_by_dimension = {
            "beneficiary_relevance": (
                "beneficiary_identity",
                "current_condition",
                "desired_external_condition",
                "beneficiary_evidence_id",
            ),
            "causal_defensibility": (
                "causal_thesis",
                "rival_causal_explanation",
                "falsifying_observation",
                "causal_evidence_id",
            ),
            "constitutional_fit": (
                "applicable_clause_ids",
                "conflict_assessment",
                "exception_status",
                "interpretation_trace_id",
            ),
            "useful_frame_originality": (
                "baseline_frame",
                "new_relation",
                "changed_reachable_action",
                "lineage_evidence_id",
            ),
            "feasibility": (
                "binding_constraints",
                "capability_evidence_id",
                "bounded_strategy_path",
                "unresolved_feasibility",
            ),
            "disconfirmation": (
                "failure_signal",
                "discriminating_test",
                "update_or_stop_rule",
                "disconfirmation_evidence_id",
            ),
        }
        for field in fields_by_dimension.get(dimension, ()):
            value = details.get(field)
            if isinstance(value, list):
                if not value or not all(_non_empty(item) for item in value):
                    errors.append(f"{prefix}.typed_details.{field} must be a non-empty string list")
            elif not _non_empty(value):
                errors.append(f"{prefix}.typed_details.{field} must be a non-empty string")
    if observed != required_dimensions:
        errors.append("dimension_assessments must cover all six dimensions exactly once")
    if payload.get("dimensions_reported_separately") is not True:
        errors.append("dimensions_reported_separately must be true")
    if payload.get("aggregate_quality_score") not in (None, ""):
        errors.append("aggregate_quality_score must be empty")
    if payload.get("high_dimension_compensates_for_missing_dimension") is not False:
        errors.append("high_dimension_compensates_for_missing_dimension must be false")
    if payload.get("quality_status") != ("complete" if observed == required_dimensions else "incomplete"):
        errors.append("quality_status must reflect complete six-dimension coverage")
    return {
        "valid": not errors,
        "errors": errors,
        "dimension_count": len(observed),
        "dimension_scores": scores,
        "lowest_scoring_dimensions": sorted(
            dimension for dimension, score in scores.items()
            if score == min(scores.values())
        ) if scores else [],
    }

