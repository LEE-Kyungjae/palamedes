from __future__ import annotations

from typing import Any, Dict, List
from ._01_kinds_value import DESIRE_SIGNAL_KINDS, DESIRE_UPDATE_OPERATIONS, _non_empty


def validate_complaint_silence_evidence(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Prevent complaint visibility and silence from defining the distribution of cost."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["complaint evidence must be an object"]}
    for field in ("analysis_id", "complaint_summary", "collection_window"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    source_ids = payload.get("source_ids")
    if (
        not isinstance(source_ids, list)
        or not source_ids
        or any(not _non_empty(item) for item in source_ids)
    ):
        errors.append("source_ids must be a non-empty source ID array")
    if payload.get("silence_means_no_cost") is not False:
        errors.append("silence_means_no_cost must be false")
    for field in ("articulation_bias", "recency_bias", "visibility_bias"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")

    silent_groups = payload.get("silent_or_missing_groups")
    if not isinstance(silent_groups, list) or not silent_groups:
        errors.append("silent_or_missing_groups must be a non-empty array")
        silent_groups = []
    group_ids = set()
    for index, group in enumerate(silent_groups):
        prefix = f"silent_or_missing_groups[{index}]"
        if not isinstance(group, dict):
            errors.append(f"{prefix} must be an object")
            continue
        group_id = group.get("group_id")
        if not _non_empty(group_id):
            errors.append(f"{prefix}.group_id must be a non-empty string")
        elif group_id in group_ids:
            errors.append(f"{prefix}.group_id must be unique")
        else:
            group_ids.add(group_id)
        for field in ("why_missing", "independent_cost_check"):
            if not _non_empty(group.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    return {
        "valid": not errors,
        "errors": errors,
        "silent_group_ids": sorted(group_ids),
    }

def validate_market_payment_evidence(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Use payment to test mechanism viability without ranking beneficiary worth."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["market payment evidence must be an object"]}
    for field in (
        "evidence_id",
        "payment_observation",
        "mechanism_inference",
        "purchasing_power_limit",
        "social_worth_assessment",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    source_ids = payload.get("source_ids")
    if (
        not isinstance(source_ids, list)
        or not source_ids
        or any(not _non_empty(item) for item in source_ids)
    ):
        errors.append("source_ids must be a non-empty source ID array")
    if payload.get("payment_ranks_social_worth") is not False:
        errors.append("payment_ranks_social_worth must be false")
    if payload.get("revenue_is_mechanism_evidence") is not True:
        errors.append("revenue_is_mechanism_evidence must be true")

    groups = payload.get("nonpaying_or_underpowered_groups")
    if not isinstance(groups, list) or not groups:
        errors.append("nonpaying_or_underpowered_groups must be a non-empty array")
        groups = []
    group_ids = set()
    for index, group in enumerate(groups):
        prefix = f"nonpaying_or_underpowered_groups[{index}]"
        if not isinstance(group, dict):
            errors.append(f"{prefix} must be an object")
            continue
        group_id = group.get("group_id")
        if not _non_empty(group_id):
            errors.append(f"{prefix}.group_id must be a non-empty string")
        elif group_id in group_ids:
            errors.append(f"{prefix}.group_id must be unique")
        else:
            group_ids.add(group_id)
        for field in ("payment_constraint", "independent_value_evidence"):
            if not _non_empty(group.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    return {
        "valid": not errors,
        "errors": errors,
        "underpowered_group_ids": sorted(group_ids),
    }

def validate_desire_triangulation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require heterogeneous signals without letting one signal define desire."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["desire triangulation must be an object"]}
    for field in ("model_id", "group_id", "desire_hypothesis", "synthesis", "tension"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("single_signal_is_decisive") is not False:
        errors.append("single_signal_is_decisive must be false")
    confidence = payload.get("confidence")
    if not isinstance(confidence, int) or isinstance(confidence, bool) or not 0 <= confidence <= 100:
        errors.append("confidence must be an integer from 0 to 100")

    signals = payload.get("signals")
    if not isinstance(signals, list) or len(signals) < len(DESIRE_SIGNAL_KINDS):
        errors.append("signals must include all six heterogeneous desire signal kinds")
        signals = []
    seen_kinds = set()
    directions = set()
    for index, signal in enumerate(signals):
        prefix = f"signals[{index}]"
        if not isinstance(signal, dict):
            errors.append(f"{prefix} must be an object")
            continue
        kind = signal.get("kind")
        if kind not in DESIRE_SIGNAL_KINDS:
            errors.append(f"{prefix}.kind must be one of {sorted(DESIRE_SIGNAL_KINDS)}")
        elif kind in seen_kinds:
            errors.append(f"{prefix}.kind must be unique")
        else:
            seen_kinds.add(kind)
        direction = signal.get("direction")
        if direction not in {"supports", "challenges", "uncertain"}:
            errors.append(f"{prefix}.direction must be supports, challenges, or uncertain")
        else:
            directions.add(direction)
        for field in ("observation", "limitation"):
            if not _non_empty(signal.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        source_ids = signal.get("source_ids")
        if (
            not isinstance(source_ids, list)
            or not source_ids
            or any(not _non_empty(item) for item in source_ids)
        ):
            errors.append(f"{prefix}.source_ids must be a non-empty source ID array")
    missing = DESIRE_SIGNAL_KINDS - seen_kinds
    if missing:
        errors.append("signals missing kinds: " + ", ".join(sorted(missing)))
    if directions == {"supports"}:
        errors.append("triangulation must preserve at least one challenge or uncertainty")
    return {
        "valid": not errors,
        "errors": errors,
        "signal_kinds": sorted(seen_kinds),
        "directions": sorted(directions),
    }

def validate_emotional_intensity_outcome(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Separate durable relief or capability from manufactured engagement."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["emotional outcome must be an object"]}
    for field in (
        "assessment_id",
        "experience",
        "short_term_emotional_effect",
        "long_term_relief_or_capability",
        "autonomy_after_exposure",
        "compulsion_check",
        "measurement_window",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("emotional_intensity_equals_value") is not False:
        errors.append("emotional_intensity_equals_value must be false")
    if payload.get("engagement_equals_benefit") is not False:
        errors.append("engagement_equals_benefit must be false")
    source_ids = payload.get("source_ids")
    if (
        not isinstance(source_ids, list)
        or not source_ids
        or any(not _non_empty(item) for item in source_ids)
    ):
        errors.append("source_ids must be a non-empty source ID array")

    mechanisms = payload.get("intensity_mechanisms")
    if not isinstance(mechanisms, list) or not mechanisms:
        errors.append("intensity_mechanisms must be a non-empty array")
        mechanisms = []
    mechanism_ids = set()
    for index, mechanism in enumerate(mechanisms):
        prefix = f"intensity_mechanisms[{index}]"
        if not isinstance(mechanism, dict):
            errors.append(f"{prefix} must be an object")
            continue
        mechanism_id = mechanism.get("mechanism_id")
        if not _non_empty(mechanism_id):
            errors.append(f"{prefix}.mechanism_id must be a non-empty string")
        elif mechanism_id in mechanism_ids:
            errors.append(f"{prefix}.mechanism_id must be unique")
        else:
            mechanism_ids.add(mechanism_id)
        for field in ("mechanism", "detection"):
            if not _non_empty(mechanism.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    return {
        "valid": not errors,
        "errors": errors,
        "intensity_mechanism_ids": sorted(mechanism_ids),
    }

def validate_latent_desire_possibility(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Represent valuable possibilities that cannot yet appear as current demand."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["latent desire possibility must be an object"]}
    for field in (
        "possibility_id",
        "beneficiary_group_id",
        "possible_condition_change",
        "enabling_capability",
        "why_not_currently_expressible",
        "non_demand_value_basis",
        "disconfirming_condition",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("current_demand_defines_value") is not False:
        errors.append("current_demand_defines_value must be false")
    demand_status = payload.get("current_demand_status")
    if demand_status not in {"observed", "weak", "absent", "inexpressible"}:
        errors.append(
            "current_demand_status must be observed, weak, absent, or inexpressible"
        )
    source_ids = payload.get("source_ids")
    if (
        not isinstance(source_ids, list)
        or not source_ids
        or any(not _non_empty(item) for item in source_ids)
    ):
        errors.append("source_ids must be a non-empty source ID array")
    return {
        "valid": not errors,
        "errors": errors,
        "current_demand_status": demand_status,
    }

def validate_informed_possibility_exposure(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Expose authorship and test an imagined future without committing beneficiaries."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["possibility exposure must be an object"]}
    for field in (
        "exposure_id",
        "possibility_id",
        "affected_group_id",
        "excluded_perspectives",
        "exposure_artifact",
        "informed_preference_question",
        "rollback",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("reversible") is not True:
        errors.append("reversible must be true")
    if payload.get("creates_commitment") is not False:
        errors.append("creates_commitment must be false")
    risk_level = payload.get("risk_level")
    if risk_level not in {"minimal", "low"}:
        errors.append("risk_level must be minimal or low")
    cost_level = payload.get("cost_level")
    if cost_level not in {"negligible", "low"}:
        errors.append("cost_level must be negligible or low")

    authors = payload.get("imagined_by")
    if not isinstance(authors, list) or not authors:
        errors.append("imagined_by must be a non-empty array")
        authors = []
    author_ids = set()
    for index, author in enumerate(authors):
        prefix = f"imagined_by[{index}]"
        if not isinstance(author, dict):
            errors.append(f"{prefix} must be an object")
            continue
        author_id = author.get("actor_id")
        if not _non_empty(author_id):
            errors.append(f"{prefix}.actor_id must be a non-empty string")
        elif author_id in author_ids:
            errors.append(f"{prefix}.actor_id must be unique")
        else:
            author_ids.add(author_id)
        for field in ("standpoint", "interest"):
            if not _non_empty(author.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    assumptions = payload.get("encoded_assumptions")
    if (
        not isinstance(assumptions, list)
        or not assumptions
        or any(not _non_empty(item) for item in assumptions)
    ):
        errors.append("encoded_assumptions must be a non-empty string array")
    response_signals = payload.get("situated_response_signals")
    if (
        not isinstance(response_signals, list)
        or len(response_signals) < 2
        or any(not _non_empty(item) for item in response_signals)
    ):
        errors.append("situated_response_signals must contain at least two signals")
    return {
        "valid": not errors,
        "errors": errors,
        "imaginer_ids": sorted(author_ids),
    }

def validate_situated_desire_update(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Update a generative desire hypothesis from comprehending, situated responses."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["situated desire update must be an object"]}
    for field in (
        "update_id",
        "possibility_id",
        "exposure_id",
        "prior_hypothesis",
        "revised_hypothesis",
        "update_rationale",
        "remaining_uncertainty",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    operation = payload.get("operation")
    if operation not in DESIRE_UPDATE_OPERATIONS:
        errors.append(f"operation must be one of {sorted(DESIRE_UPDATE_OPERATIONS)}")
    prior_confidence = payload.get("prior_confidence")
    revised_confidence = payload.get("revised_confidence")
    for field, value in (
        ("prior_confidence", prior_confidence),
        ("revised_confidence", revised_confidence),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 100:
            errors.append(f"{field} must be an integer from 0 to 100")
    if isinstance(prior_confidence, int) and isinstance(revised_confidence, int):
        if operation == "strengthen" and revised_confidence <= prior_confidence:
            errors.append("strengthen requires revised_confidence > prior_confidence")
        if operation == "weaken" and revised_confidence >= prior_confidence:
            errors.append("weaken requires revised_confidence < prior_confidence")
        if operation == "retire" and revised_confidence != 0:
            errors.append("retire requires revised_confidence == 0")

    responses = payload.get("situated_responses")
    if not isinstance(responses, list) or len(responses) < 2:
        errors.append("situated_responses must contain at least two responses")
        responses = []
    response_ids = set()
    directions = set()
    for index, response in enumerate(responses):
        prefix = f"situated_responses[{index}]"
        if not isinstance(response, dict):
            errors.append(f"{prefix} must be an object")
            continue
        response_id = response.get("response_id")
        if not _non_empty(response_id):
            errors.append(f"{prefix}.response_id must be a non-empty string")
        elif response_id in response_ids:
            errors.append(f"{prefix}.response_id must be unique")
        else:
            response_ids.add(response_id)
        direction = response.get("direction")
        if direction not in {"supports", "challenges", "uncertain"}:
            errors.append(f"{prefix}.direction must be supports, challenges, or uncertain")
        else:
            directions.add(direction)
        if response.get("demonstrated_comprehension") is not True:
            errors.append(f"{prefix}.demonstrated_comprehension must be true")
        for field in ("context", "response", "source_id"):
            if not _non_empty(response.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if directions == {"supports"}:
        errors.append("situated responses must retain a challenge or uncertainty")
    return {
        "valid": not errors,
        "errors": errors,
        "operation": operation,
        "response_directions": sorted(directions),
    }

def validate_desire_centered_mission(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Center a mission on beneficiary capability or condition change, not demand."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["desire-centered mission must be an object"]}
    for field in (
        "mission_id",
        "beneficiary_group_id",
        "current_condition",
        "desired_condition",
        "capability_change",
        "change_mechanism",
        "demand_evidence_role",
        "value_state_id",
        "constitution_id",
        "desire_model_id",
        "disconfirming_condition",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("demand_defines_mission") is not False:
        errors.append("demand_defines_mission must be false")
    if payload.get("revenue_defines_success") is not False:
        errors.append("revenue_defines_success must be false")
    demand_sources = payload.get("demand_evidence_ids")
    if not isinstance(demand_sources, list) or any(
        not _non_empty(item) for item in demand_sources
    ):
        errors.append("demand_evidence_ids must be an array of source IDs")

    signals = payload.get("beneficiary_change_signals")
    if (
        not isinstance(signals, list)
        or len(signals) < 2
        or any(not _non_empty(item) for item in signals)
    ):
        errors.append("beneficiary_change_signals must contain at least two signals")
    safeguards = payload.get("safeguards")
    if (
        not isinstance(safeguards, list)
        or not safeguards
        or any(not _non_empty(item) for item in safeguards)
    ):
        errors.append("safeguards must be a non-empty string array")
    return {
        "valid": not errors,
        "errors": errors,
        "demand_evidence_count": len(demand_sources) if isinstance(demand_sources, list) else 0,
    }

def validate_capability_institution_mismatch(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Discover an opportunity from a new capability colliding with an old institution."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["capability-institution mismatch must be an object"]}
    for field in (
        "mismatch_id",
        "new_capability",
        "capability_change_date",
        "old_institution",
        "institutional_rule_or_assumption",
        "why_rule_persists",
        "blocked_condition_change",
        "affected_group_id",
        "mismatch_mechanism",
        "disconfirming_condition",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("trend_consensus_defines_opportunity") is not False:
        errors.append("trend_consensus_defines_opportunity must be false")
    consensus = payload.get("trend_consensus_status")
    if consensus not in {"absent", "forming", "established"}:
        errors.append("trend_consensus_status must be absent, forming, or established")
    capability_sources = payload.get("capability_source_ids")
    institution_sources = payload.get("institution_source_ids")
    for field, sources in (
        ("capability_source_ids", capability_sources),
        ("institution_source_ids", institution_sources),
    ):
        if (
            not isinstance(sources, list)
            or not sources
            or any(not _non_empty(item) for item in sources)
        ):
            errors.append(f"{field} must be a non-empty source ID array")
    return {
        "valid": not errors,
        "errors": errors,
        "trend_consensus_status": consensus,
    }

def validate_mismatch_beneficiary_burden(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require a capability mismatch to map to recurring beneficiary burden."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["mismatch burden must be an object"]}
    for field in ("assessment_id", "mismatch_id", "why_capability_is_relevant"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("capability_novelty_defines_value") is not False:
        errors.append("capability_novelty_defines_value must be false")

    burdens = payload.get("beneficiary_burdens")
    if not isinstance(burdens, list) or not burdens:
        errors.append("beneficiary_burdens must be a non-empty array")
        burdens = []
    burden_ids = set()
    burden_kinds = set()
    allowed_kinds = {"recurring_friction", "exclusion", "delay", "unrealized_possibility"}
    for index, burden in enumerate(burdens):
        prefix = f"beneficiary_burdens[{index}]"
        if not isinstance(burden, dict):
            errors.append(f"{prefix} must be an object")
            continue
        burden_id = burden.get("burden_id")
        if not _non_empty(burden_id):
            errors.append(f"{prefix}.burden_id must be a non-empty string")
        elif burden_id in burden_ids:
            errors.append(f"{prefix}.burden_id must be unique")
        else:
            burden_ids.add(burden_id)
        kind = burden.get("kind")
        if kind not in allowed_kinds:
            errors.append(f"{prefix}.kind must be one of {sorted(allowed_kinds)}")
        else:
            burden_kinds.add(kind)
        for field in (
            "affected_group_id",
            "observed_cost",
            "recurrence",
            "context",
            "source_id",
        ):
            if not _non_empty(burden.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if not _non_empty(payload.get("disconfirming_condition")):
        errors.append("disconfirming_condition must be a non-empty string")
    return {
        "valid": not errors,
        "errors": errors,
        "burden_kinds": sorted(burden_kinds),
    }

def validate_workaround_reframe(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Use a workaround anomaly to test a different problem frame."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["workaround reframe must be an object"]}
    for field in (
        "anomaly_id",
        "affected_group_id",
        "intended_workflow",
        "observed_workaround_or_violation",
        "actor_reason",
        "incremental_frame",
        "alternative_problem_frame",
        "frame_shift_rationale",
        "distinguishing_observation",
        "source_id",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("workaround_is_automatically_correct") is not False:
        errors.append("workaround_is_automatically_correct must be false")
    if payload.get("anomaly_is_only_error") is not False:
        errors.append("anomaly_is_only_error must be false")
    alternatives = payload.get("alternative_explanations")
    if (
        not isinstance(alternatives, list)
        or len(alternatives) < 2
        or any(not _non_empty(item) for item in alternatives)
    ):
        errors.append("alternative_explanations must contain at least two explanations")
    return {"valid": not errors, "errors": errors}

def validate_cross_context_workaround(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Separate a recurring workaround mechanism from a local quirk."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["cross-context workaround must be an object"]}
    for field in (
        "analysis_id",
        "mechanism_hypothesis",
        "shared_pattern",
        "boundary_conditions",
        "next_discriminating_context",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("generalizes_universally") is not False:
        errors.append("generalizes_universally must be false")
    strength = payload.get("mechanism_strength")
    if strength not in {"tentative", "supported", "contested"}:
        errors.append("mechanism_strength must be tentative, supported, or contested")

    contexts = payload.get("contexts")
    if not isinstance(contexts, list) or len(contexts) < 2:
        errors.append("contexts must contain at least two contexts")
        contexts = []
    context_ids = set()
    differences_found = False
    for index, context in enumerate(contexts):
        prefix = f"contexts[{index}]"
        if not isinstance(context, dict):
            errors.append(f"{prefix} must be an object")
            continue
        context_id = context.get("context_id")
        if not _non_empty(context_id):
            errors.append(f"{prefix}.context_id must be a non-empty string")
        elif context_id in context_ids:
            errors.append(f"{prefix}.context_id must be unique")
        else:
            context_ids.add(context_id)
        for field in (
            "population",
            "environment",
            "observed_workaround",
            "mechanism_evidence",
            "source_id",
        ):
            if not _non_empty(context.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        difference = context.get("difference")
        if not _non_empty(difference):
            errors.append(f"{prefix}.difference must be a non-empty string")
        else:
            differences_found = True
    if contexts and not differences_found:
        errors.append("contexts must preserve differences")
    return {
        "valid": not errors,
        "errors": errors,
        "context_ids": sorted(context_ids),
        "mechanism_strength": strength,
    }

def validate_repository_pattern_opportunity(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Connect repository collection patterns to beneficiary condition change."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["repository pattern opportunity must be an object"]}
    for field in (
        "pattern_id",
        "technical_pattern",
        "enabled_capability",
        "beneficiary_group_id",
        "current_condition",
        "possible_condition_change",
        "causal_bridge",
        "adoption_constraint",
        "disconfirming_condition",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("repository_popularity_defines_opportunity") is not False:
        errors.append("repository_popularity_defines_opportunity must be false")

    repositories = payload.get("repositories")
    if not isinstance(repositories, list) or len(repositories) < 2:
        errors.append("repositories must contain at least two references")
        repositories = []
    reference_ids = set()
    for index, repository in enumerate(repositories):
        prefix = f"repositories[{index}]"
        if not isinstance(repository, dict):
            errors.append(f"{prefix} must be an object")
            continue
        reference_id = repository.get("reference_id")
        if not _non_empty(reference_id):
            errors.append(f"{prefix}.reference_id must be a non-empty string")
        elif reference_id in reference_ids:
            errors.append(f"{prefix}.reference_id must be unique")
        else:
            reference_ids.add(reference_id)
        for field in ("repository", "revision", "pattern_evidence"):
            if not _non_empty(repository.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    beneficiary_sources = payload.get("beneficiary_evidence_ids")
    if (
        not isinstance(beneficiary_sources, list)
        or not beneficiary_sources
        or any(not _non_empty(item) for item in beneficiary_sources)
    ):
        errors.append("beneficiary_evidence_ids must be a non-empty source ID array")
    return {
        "valid": not errors,
        "errors": errors,
        "reference_ids": sorted(reference_ids),
    }

def validate_failure_archive_learning(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Learn missing viability conditions from plausible failed predecessors."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["failure archive learning must be an object"]}
    for field in (
        "analysis_id",
        "opportunity_hypothesis",
        "cross_failure_synthesis",
        "surviving_assumption",
        "disconfirming_condition",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("success_cases_are_sufficient") is not False:
        errors.append("success_cases_are_sufficient must be false")

    failures = payload.get("failed_predecessors")
    if not isinstance(failures, list) or not failures:
        errors.append("failed_predecessors must be a non-empty array")
        failures = []
    predecessor_ids = set()
    condition_kinds = set()
    allowed_kinds = {
        "timing",
        "trust",
        "distribution",
        "economics",
        "capability",
        "institutional_fit",
    }
    for index, failure in enumerate(failures):
        prefix = f"failed_predecessors[{index}]"
        if not isinstance(failure, dict):
            errors.append(f"{prefix} must be an object")
            continue
        predecessor_id = failure.get("predecessor_id")
        if not _non_empty(predecessor_id):
            errors.append(f"{prefix}.predecessor_id must be a non-empty string")
        elif predecessor_id in predecessor_ids:
            errors.append(f"{prefix}.predecessor_id must be unique")
        else:
            predecessor_ids.add(predecessor_id)
        condition_kind = failure.get("missing_condition_kind")
        if condition_kind not in allowed_kinds:
            errors.append(f"{prefix}.missing_condition_kind must be one of {sorted(allowed_kinds)}")
        else:
            condition_kinds.add(condition_kind)
        for field in (
            "plausible_thesis",
            "observed_failure",
            "missing_condition_evidence",
            "archive_limit",
            "source_id",
        ):
            if not _non_empty(failure.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    return {
        "valid": not errors,
        "errors": errors,
        "missing_condition_kinds": sorted(condition_kinds),
    }

def validate_changed_constraint_window(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require timing to name an evidenced constraint transition."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["changed constraint window must be an object"]}
    for field in (
        "window_id",
        "opportunity_id",
        "missing_condition_kind",
        "constraint",
        "before_state",
        "after_state",
        "change_date",
        "change_evidence",
        "why_previously_unviable",
        "why_now_viable",
        "durability_assessment",
        "reversal_signal",
        "source_id",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("generic_now_claim") is not False:
        errors.append("generic_now_claim must be false")
    confidence = payload.get("change_confidence")
    if not isinstance(confidence, int) or isinstance(confidence, bool) or not 0 <= confidence <= 100:
        errors.append("change_confidence must be an integer from 0 to 100")
    if (
        _non_empty(payload.get("before_state"))
        and payload.get("before_state") == payload.get("after_state")
    ):
        errors.append("before_state and after_state must differ")
    return {"valid": not errors, "errors": errors}

def validate_act_wait_comparison(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Compare acting with waiting, including natural learning and option closure."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["act-wait comparison must be an object"]}
    for field in (
        "comparison_id",
        "opportunity_id",
        "window_id",
        "act_now_consequence",
        "wait_consequence",
        "act_now_cost",
        "wait_cost",
        "decision_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if any(field in payload for field in ("aggregate_score", "urgency_score")):
        errors.append("act-wait comparison cannot use aggregate or urgency scores")
    decision = payload.get("decision")
    if decision not in {"act_now", "wait", "probe"}:
        errors.append("decision must be act_now, wait, or probe")
    for field in ("uncertainty_reducing_naturally", "options_closed_by_delay"):
        values = payload.get(field)
        if not isinstance(values, list) or any(not _non_empty(item) for item in values):
            errors.append(f"{field} must be an array of non-empty strings")
    closed_options = payload.get("options_closed_by_delay")
    natural_reduction = payload.get("uncertainty_reducing_naturally")
    if decision == "act_now" and isinstance(closed_options, list) and not closed_options:
        errors.append("act_now requires at least one option closed by delay")
    if decision == "wait":
        if not _non_empty(payload.get("wake_trigger")):
            errors.append("wait requires a wake_trigger")
        if isinstance(natural_reduction, list) and not natural_reduction:
            errors.append("wait requires uncertainty expected to reduce naturally")
    if decision == "probe" and not _non_empty(payload.get("probe")):
        errors.append("probe decision requires a probe")
    return {"valid": not errors, "errors": errors, "decision": decision}

def validate_opportunity_record(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Assemble the evidence lineage and cheapest discriminator for an opportunity."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["opportunity record must be an object"]}
    for field in (
        "opportunity_id",
        "anomaly_id",
        "affected_group_id",
        "current_condition",
        "possible_condition_change",
        "enabling_change_id",
        "window_id",
        "act_wait_comparison_id",
        "opportunity_hypothesis",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("fashionable_capability_defines_opportunity") is not False:
        errors.append("fashionable_capability_defines_opportunity must be false")
    predecessor_ids = payload.get("failed_predecessor_ids")
    if (
        not isinstance(predecessor_ids, list)
        or not predecessor_ids
        or any(not _non_empty(item) for item in predecessor_ids)
    ):
        errors.append("failed_predecessor_ids must be a non-empty ID array")

    exposure = payload.get("cheapest_discriminating_exposure")
    if not isinstance(exposure, dict):
        errors.append("cheapest_discriminating_exposure must be an object")
        exposure = {}
    for field in ("description", "cost", "risk", "rollback", "why_cheapest"):
        if not _non_empty(exposure.get(field)):
            errors.append(
                f"cheapest_discriminating_exposure.{field} must be a non-empty string"
            )
    if exposure.get("reversible") is not True:
        errors.append("cheapest_discriminating_exposure.reversible must be true")
    outcomes = exposure.get("distinguishing_outcomes")
    if (
        not isinstance(outcomes, list)
        or len(outcomes) < 2
        or any(not _non_empty(item) for item in outcomes)
    ):
        errors.append(
            "cheapest_discriminating_exposure.distinguishing_outcomes "
            "must contain at least two outcomes"
        )
    rejected = exposure.get("costlier_alternatives_rejected")
    if (
        not isinstance(rejected, list)
        or not rejected
        or any(not _non_empty(item) for item in rejected)
    ):
        errors.append(
            "cheapest_discriminating_exposure.costlier_alternatives_rejected "
            "must be a non-empty array"
        )
    return {"valid": not errors, "errors": errors}

def validate_opportunity_thesis_gate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Gate opportunity eligibility on consequence and time-bounded option opening."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["opportunity thesis gate must be an object"]}
    for field in (
        "gate_id",
        "opportunity_record_id",
        "consequential_mismatch",
        "affected_condition",
        "option_opening",
        "closure_mechanism",
        "window_evidence_id",
        "mismatch_evidence_id",
        "gate_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("fashionable_capability_is_sufficient") is not False:
        errors.append("fashionable_capability_is_sufficient must be false")
    if payload.get("consequence_established") is not True:
        errors.append("consequence_established must be true")
    if payload.get("time_bounded_option_established") is not True:
        errors.append("time_bounded_option_established must be true")
    decision = payload.get("gate_decision")
    if decision not in {"eligible", "ineligible"}:
        errors.append("gate_decision must be eligible or ineligible")
    prerequisites_met = (
        payload.get("consequence_established") is True
        and payload.get("time_bounded_option_established") is True
        and payload.get("fashionable_capability_is_sufficient") is False
    )
    if decision == "eligible" and not prerequisites_met:
        errors.append("eligible requires consequence and time-bounded option evidence")
    return {
        "valid": not errors,
        "errors": errors,
        "gate_decision": decision,
        "prerequisites_met": prerequisites_met,
    }

def validate_independent_mission_generation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require serious candidates to form independently from distinct evidence slices."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["independent mission generation must be an object"]}
    for field in ("batch_id", "opportunity_gate_id", "formation_protocol"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("sequential_cross_contamination_allowed") is not False:
        errors.append("sequential_cross_contamination_allowed must be false")

    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or len(candidates) < 3:
        errors.append("candidates must contain at least three serious alternatives")
        candidates = []
    candidate_ids = set()
    evidence_slices = set()
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
        for field in ("mission_thesis", "beneficiary_change", "mechanism"):
            if not _non_empty(candidate.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if candidate.get("formed_without_peer_candidates") is not True:
            errors.append(f"{prefix}.formed_without_peer_candidates must be true")
        visible_peers = candidate.get("peer_candidate_ids_visible")
        if visible_peers != []:
            errors.append(f"{prefix}.peer_candidate_ids_visible must be empty")
        evidence_ids = candidate.get("evidence_slice_ids")
        if (
            not isinstance(evidence_ids, list)
            or not evidence_ids
            or any(not _non_empty(item) for item in evidence_ids)
        ):
            errors.append(f"{prefix}.evidence_slice_ids must be a non-empty ID array")
        else:
            slice_key = tuple(sorted(evidence_ids))
            if slice_key in evidence_slices:
                errors.append(f"{prefix}.evidence_slice_ids must differ from other candidates")
            evidence_slices.add(slice_key)
    return {
        "valid": not errors,
        "errors": errors,
        "candidate_ids": sorted(candidate_ids),
        "distinct_evidence_slice_count": len(evidence_slices),
    }

def validate_common_candidate_normalization(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize sealed candidates against one constitution and resource envelope."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["candidate normalization must be an object"]}
    for field in (
        "normalization_id",
        "generation_batch_id",
        "constitution_id",
        "resource_envelope_id",
        "evaluation_as_of",
        "common_context_hash",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    version = payload.get("constitution_version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        errors.append("constitution_version must be an integer >= 1")
    if payload.get("candidate_theses_may_be_rewritten") is not False:
        errors.append("candidate_theses_may_be_rewritten must be false")

    candidates = payload.get("normalized_candidates")
    if not isinstance(candidates, list) or len(candidates) < 3:
        errors.append("normalized_candidates must contain at least three candidates")
        candidates = []
    candidate_ids = set()
    for index, candidate in enumerate(candidates):
        prefix = f"normalized_candidates[{index}]"
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
        for field in (
            "sealed_candidate_hash",
            "common_context_hash",
            "constitutional_fit",
            "resource_demand",
            "constraint_tensions",
        ):
            if not _non_empty(candidate.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if candidate.get("common_context_hash") != payload.get("common_context_hash"):
            errors.append(f"{prefix}.common_context_hash must match the batch context")
        if candidate.get("original_thesis_preserved") is not True:
            errors.append(f"{prefix}.original_thesis_preserved must be true")
    return {"valid": not errors, "errors": errors, "candidate_ids": sorted(candidate_ids)}

