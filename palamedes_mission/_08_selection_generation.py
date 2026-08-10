from __future__ import annotations

from typing import Any, Dict, List
from ._01_kinds_value import _non_empty


def validate_lineage_opposition_mission_generation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Generate one mission by lineage transfer and another by opposing the dominant frame."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["lineage opposition mission generation must be an object"]}
    for field in (
        "generation_record_id",
        "mission_generation_id",
        "dominant_framing",
        "comparison_question",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")

    lineage = payload.get("lineage_transfer_candidate")
    if not isinstance(lineage, dict):
        errors.append("lineage_transfer_candidate must be an object")
        lineage = {}
    for field in (
        "candidate_id",
        "source_lineage_id",
        "source_condition",
        "source_mechanism",
        "target_analogous_condition",
        "material_difference",
        "transferred_mission_hypothesis",
        "local_probe",
    ):
        if not _non_empty(lineage.get(field)):
            errors.append(f"lineage_transfer_candidate.{field} must be a non-empty string")
    if lineage.get("source_outcome_is_target_forecast") is not False:
        errors.append("lineage_transfer_candidate.source_outcome_is_target_forecast must be false")

    opposition = payload.get("opposition_candidate")
    if not isinstance(opposition, dict):
        errors.append("opposition_candidate must be an object")
        opposition = {}
    for field in (
        "candidate_id",
        "dominant_assumption",
        "hidden_beneficiary_or_condition",
        "why_framing_hides_it",
        "opposed_mission_hypothesis",
        "supporting_evidence_id",
        "frame_failure_signal",
    ):
        if not _non_empty(opposition.get(field)):
            errors.append(f"opposition_candidate.{field} must be a non-empty string")
    if opposition.get("merely_negates_dominant_mission") is not False:
        errors.append("opposition_candidate.merely_negates_dominant_mission must be false")
    if lineage.get("candidate_id") == opposition.get("candidate_id"):
        errors.append("lineage-transfer and opposition candidate ids must differ")
    return {
        "valid": not errors,
        "errors": errors,
        "candidate_ids": [lineage.get("candidate_id"), opposition.get("candidate_id")],
    }

def validate_temporal_counterfactual_mission_generation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Generate from temporal structure and the consequence of having no mission."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["temporal counterfactual mission generation must be an object"]}
    for field in (
        "temporal_generation_id",
        "mission_generation_id",
        "affected_condition",
        "generated_mission_candidate",
        "selection_question",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    options = payload.get("temporal_options")
    if not isinstance(options, list):
        errors.append("temporal_options must be a list")
        options = []
    required_types = {"wait", "sequence", "act_before_expiry"}
    option_types = set()
    for index, option in enumerate(options):
        prefix = f"temporal_options[{index}]"
        if not isinstance(option, dict):
            errors.append(f"{prefix} must be an object")
            continue
        option_type = option.get("option_type")
        if option_type not in required_types:
            errors.append(f"{prefix}.option_type is not recognized")
        elif option_type in option_types:
            errors.append(f"{prefix}.option_type must be unique")
        option_types.add(option_type)
        for field in ("action", "timing_condition", "predicted_consequence", "evidence_id"):
            if not _non_empty(option.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if option_types != required_types:
        errors.append("temporal_options must cover wait, sequence, and act_before_expiry")

    counterfactual = payload.get("no_mission_counterfactual")
    if not isinstance(counterfactual, dict):
        errors.append("no_mission_counterfactual must be an object")
        counterfactual = {}
    for field in (
        "baseline_condition",
        "worsening_condition",
        "affected_beneficiary",
        "evaluation_horizon",
        "evidence_id",
        "alternative_recovery_path",
        "mission_necessity_test",
    ):
        if not _non_empty(counterfactual.get(field)):
            errors.append(f"no_mission_counterfactual.{field} must be a non-empty string")
    if counterfactual.get("mission_necessity_assumed") is not False:
        errors.append("no_mission_counterfactual.mission_necessity_assumed must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "temporal_option_types": sorted(option_types),
    }

def validate_isolated_generator_contexts(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Isolate generator contexts and reference slices until candidate reveal."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["isolated generator contexts must be an object"]}
    for field in (
        "isolation_record_id",
        "mission_generation_id",
        "comparison_context_id",
        "reveal_protocol",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("shared_preselection_context") is not False:
        errors.append("shared_preselection_context must be false")
    if payload.get("reveal_after_all_generators_complete") is not True:
        errors.append("reveal_after_all_generators_complete must be true")
    generators = payload.get("generator_contexts")
    if not isinstance(generators, list):
        errors.append("generator_contexts must be a list")
        generators = []
    required_types = {
        "condition_first",
        "capability_first",
        "lineage_transfer",
        "opposition",
        "temporal",
        "no_mission_counterfactual",
    }
    types = set()
    context_ids = set()
    candidate_ids = set()
    all_reference_ids = set()
    for index, generator in enumerate(generators):
        prefix = f"generator_contexts[{index}]"
        if not isinstance(generator, dict):
            errors.append(f"{prefix} must be an object")
            continue
        generator_type = generator.get("generator_type")
        if generator_type not in required_types:
            errors.append(f"{prefix}.generator_type is not recognized")
        elif generator_type in types:
            errors.append(f"{prefix}.generator_type must be unique")
        types.add(generator_type)
        for field, seen in (("context_id", context_ids), ("candidate_id", candidate_ids)):
            value = generator.get(field)
            if not _non_empty(value):
                errors.append(f"{prefix}.{field} must be a non-empty string")
            elif value in seen:
                errors.append(f"{prefix}.{field} must be unique")
            seen.add(value)
        refs = generator.get("reference_slice_ids")
        if (
            not isinstance(refs, list)
            or not refs
            or not all(_non_empty(item) for item in refs)
            or len(refs) != len(set(refs))
        ):
            errors.append(f"{prefix}.reference_slice_ids must be a non-empty unique list")
            refs = []
        if all_reference_ids.intersection(refs):
            errors.append(f"{prefix}.reference_slice_ids must not overlap another generator slice")
        all_reference_ids.update(refs)
        if generator.get("context_sealed_before_generation") is not True:
            errors.append(f"{prefix}.context_sealed_before_generation must be true")
        visible = generator.get("other_candidate_ids_visible_during_generation")
        if visible != []:
            errors.append(f"{prefix}.other_candidate_ids_visible_during_generation must be empty")
    if types != required_types:
        errors.append("generator_contexts must contain exactly the six generation modes")
    return {
        "valid": not errors,
        "errors": errors,
        "generator_types": sorted(types),
        "reference_slice_count": len(all_reference_ids),
    }

def validate_external_condition_mission(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require a mission to describe an observable external condition change."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["external condition mission must be an object"]}
    for field in (
        "mission_candidate_id",
        "mission_statement",
        "external_beneficiary",
        "current_external_condition",
        "target_external_condition",
        "observable_measure",
        "baseline",
        "target",
        "evaluation_horizon",
        "failure_condition",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("mission_object_type") != "external_condition_change":
        errors.append("mission_object_type must be external_condition_change")
    if payload.get("beneficiary_is_internal_system") is not False:
        errors.append("beneficiary_is_internal_system must be false")
    if payload.get("internal_activity_is_mission") is not False:
        errors.append("internal_activity_is_mission must be false")
    activities = payload.get("supporting_activity_ids")
    if not isinstance(activities, list) or not all(_non_empty(item) for item in activities):
        errors.append("supporting_activity_ids must be a list")
    if payload.get("current_external_condition") == payload.get("target_external_condition"):
        errors.append("current_external_condition and target_external_condition must differ")
    return {
        "valid": not errors,
        "errors": errors,
        "mission_object_type": payload.get("mission_object_type"),
    }

def validate_subordinate_internal_capability_work(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Allow internal capability work only as the cheaper support for an external mission."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["subordinate internal capability work must be an object"]}
    for field in (
        "capability_work_id",
        "external_mission_id",
        "internal_capability",
        "mission_dependency",
        "deliverable",
        "cost_unit",
        "expiry_at",
        "stop_trigger",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("internal_capability_is_independent_mission") is not False:
        errors.append("internal_capability_is_independent_mission must be false")
    internal_cost = payload.get("internal_total_cost")
    if (
        isinstance(internal_cost, bool)
        or not isinstance(internal_cost, (int, float))
        or internal_cost <= 0
    ):
        errors.append("internal_total_cost must be greater than zero")
        internal_cost = float("inf")
    alternatives = payload.get("available_alternatives")
    if not isinstance(alternatives, list) or not alternatives:
        errors.append("available_alternatives must be a non-empty list")
        alternatives = []
    adequate_costs = []
    alternative_ids = set()
    for index, alternative in enumerate(alternatives):
        prefix = f"available_alternatives[{index}]"
        if not isinstance(alternative, dict):
            errors.append(f"{prefix} must be an object")
            continue
        alternative_id = alternative.get("alternative_id")
        if not _non_empty(alternative_id):
            errors.append(f"{prefix}.alternative_id must be a non-empty string")
        elif alternative_id in alternative_ids:
            errors.append(f"{prefix}.alternative_id must be unique")
        alternative_ids.add(alternative_id)
        for field in ("delivery_method", "adequacy_evidence_id"):
            if not _non_empty(alternative.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if not isinstance(alternative.get("adequate_for_mission"), bool):
            errors.append(f"{prefix}.adequate_for_mission must be boolean")
        cost = alternative.get("total_cost")
        if isinstance(cost, bool) or not isinstance(cost, (int, float)) or cost <= 0:
            errors.append(f"{prefix}.total_cost must be greater than zero")
        elif alternative.get("adequate_for_mission") is True:
            adequate_costs.append(cost)
    if not adequate_costs:
        errors.append("available_alternatives must include at least one adequate alternative")
    internal_is_cheapest = bool(adequate_costs) and internal_cost < min(adequate_costs)
    if payload.get("internal_work_is_cheaper") is not internal_is_cheapest:
        errors.append("internal_work_is_cheaper must match adequate alternative costs")
    expected_decision = "approve_internal" if internal_is_cheapest else "use_alternative"
    if payload.get("decision") != expected_decision:
        errors.append("decision must choose the cheaper adequate delivery path")
    return {
        "valid": not errors,
        "errors": errors,
        "decision": payload.get("decision"),
        "internal_is_cheapest": internal_is_cheapest,
    }

def validate_falsifiable_implementation_open_mission(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Make a mission testable while keeping multiple implementations reachable."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["falsifiable implementation-open mission must be an object"]}
    for field in (
        "mission_contract_id",
        "mission_candidate_id",
        "external_beneficiary",
        "current_condition",
        "target_condition",
        "outcome_measure",
        "success_threshold",
        "evaluation_window",
        "failure_condition",
        "mechanism_selection_gate",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("mission_is_mechanism_agnostic") is not True:
        errors.append("mission_is_mechanism_agnostic must be true")
    if payload.get("selected_implementation_id") not in ("", None):
        errors.append("selected_implementation_id must be empty before planning")
    mechanisms = payload.get("reachable_mechanism_classes")
    if (
        not isinstance(mechanisms, list)
        or len(mechanisms) < 2
        or not all(_non_empty(item) for item in mechanisms)
        or len(mechanisms) != len(set(mechanisms))
    ):
        errors.append("reachable_mechanism_classes must contain at least two unique classes")
    invariants = payload.get("implementation_invariants")
    if (
        not isinstance(invariants, list)
        or not invariants
        or not all(_non_empty(item) for item in invariants)
    ):
        errors.append("implementation_invariants must be a non-empty list")
    prohibited = payload.get("prohibited_consequences")
    if (
        not isinstance(prohibited, list)
        or not prohibited
        or not all(_non_empty(item) for item in prohibited)
    ):
        errors.append("prohibited_consequences must be a non-empty list")
    return {
        "valid": not errors,
        "errors": errors,
        "reachable_mechanism_count": len(mechanisms) if isinstance(mechanisms, list) else 0,
    }

def validate_skeptical_mission_translation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Verify that a creative mission preserves its beneficiary change in plain language."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["skeptical mission translation must be an object"]}
    for field in (
        "translation_test_id",
        "mission_candidate_id",
        "original_mission_statement",
        "skeptical_translator_id",
        "plain_translation",
        "translation_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("translator_saw_generation_context") is not False:
        errors.append("translator_saw_generation_context must be false")
    if payload.get("creative_metaphor_retained") is not False:
        errors.append("creative_metaphor_retained must be false")
    metaphors = payload.get("removed_creative_terms")
    if (
        not isinstance(metaphors, list)
        or not metaphors
        or not all(_non_empty(item) for item in metaphors)
    ):
        errors.append("removed_creative_terms must be a non-empty list")
    required_semantics = {
        "beneficiary",
        "current_condition",
        "target_condition",
        "outcome_measure",
        "evaluation_horizon",
    }
    original = payload.get("original_semantics")
    translated = payload.get("translated_semantics")
    for field, semantics in (("original_semantics", original), ("translated_semantics", translated)):
        if not isinstance(semantics, dict) or set(semantics) != required_semantics:
            errors.append(f"{field} must contain exactly the five mission semantics")
        elif not all(_non_empty(value) for value in semantics.values()):
            errors.append(f"{field} values must be non-empty strings")
    semantics_preserved = isinstance(original, dict) and isinstance(translated, dict) and original == translated
    if payload.get("beneficiary_change_preserved") is not semantics_preserved:
        errors.append("beneficiary_change_preserved must match semantic equality")
    expected_status = "passed" if semantics_preserved else "failed"
    if payload.get("translation_status") != expected_status:
        errors.append("translation_status must follow semantic preservation")
    return {
        "valid": not errors,
        "errors": errors,
        "translation_status": expected_status,
        "beneficiary_change_preserved": semantics_preserved,
    }

def validate_invention_thesis_integration(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Integrate independent mission transformations with external, translatable outcomes."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["invention thesis integration must be an object"]}
    for field in (
        "invention_thesis_id",
        "mission_generation_id",
        "generator_isolation_id",
        "external_condition_gate_id",
        "internal_capability_gate_id",
        "implementation_open_gate_id",
        "translation_test_id",
        "comparison_gate_id",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("invention_is_novelty_label") is not False:
        errors.append("invention_is_novelty_label must be false")
    if payload.get("selection_deferred_until_independent_generation_complete") is not True:
        errors.append("selection_deferred_until_independent_generation_complete must be true")
    required_types = {
        "condition",
        "capability",
        "lineage",
        "opposition",
        "temporal",
        "counterfactual",
    }
    transformations = payload.get("transformations")
    if not isinstance(transformations, list):
        errors.append("transformations must be a list")
        transformations = []
    types = set()
    context_ids = set()
    candidate_ids = set()
    for index, transformation in enumerate(transformations):
        prefix = f"transformations[{index}]"
        if not isinstance(transformation, dict):
            errors.append(f"{prefix} must be an object")
            continue
        transformation_type = transformation.get("transformation_type")
        if transformation_type not in required_types:
            errors.append(f"{prefix}.transformation_type is not recognized")
        elif transformation_type in types:
            errors.append(f"{prefix}.transformation_type must be unique")
        types.add(transformation_type)
        for field, seen in (("isolated_context_id", context_ids), ("candidate_id", candidate_ids)):
            value = transformation.get(field)
            if not _non_empty(value):
                errors.append(f"{prefix}.{field} must be a non-empty string")
            elif value in seen:
                errors.append(f"{prefix}.{field} must be unique")
            seen.add(value)
        for field in ("evidence_id", "external_condition_contract_id"):
            if not _non_empty(transformation.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if transformation.get("generated_before_rival_reveal") is not True:
            errors.append(f"{prefix}.generated_before_rival_reveal must be true")
    if types != required_types:
        errors.append("transformations must contain exactly the six invention transformations")
    for field in (
        "all_candidates_describe_external_change",
        "implementation_choice_remains_open",
        "skeptical_translation_passed",
    ):
        if payload.get(field) is not True:
            errors.append(f"{field} must be true")
    if payload.get("conclusion") != "invention_thesis_supported":
        errors.append("conclusion must be invention_thesis_supported")
    return {
        "valid": not errors,
        "errors": errors,
        "transformation_types": sorted(types),
    }

def validate_pre_reveal_candidate_commitments(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Seal candidate forecasts and failure conditions before tournament reveal."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["pre-reveal candidate commitments must be an object"]}
    for field in (
        "tournament_commitment_id",
        "tournament_id",
        "rival_reveal_event_id",
        "amendment_protocol",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("post_reveal_mutation_allowed") is not False:
        errors.append("post_reveal_mutation_allowed must be false")
    commitments = payload.get("candidate_commitments")
    if not isinstance(commitments, list) or len(commitments) < 2:
        errors.append("candidate_commitments must contain at least two candidates")
        commitments = []
    candidate_ids = set()
    commitment_ids = set()
    hashes = set()
    for index, commitment in enumerate(commitments):
        prefix = f"candidate_commitments[{index}]"
        if not isinstance(commitment, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field, seen in (
            ("candidate_id", candidate_ids),
            ("commitment_id", commitment_ids),
            ("commitment_hash", hashes),
        ):
            value = commitment.get(field)
            if not _non_empty(value):
                errors.append(f"{prefix}.{field} must be a non-empty string")
            elif value in seen:
                errors.append(f"{prefix}.{field} must be unique")
            seen.add(value)
        for field in (
            "committed_at",
            "forecast",
            "forecast_measure",
            "forecast_target",
            "forecast_window",
            "failure_condition",
            "withdrawal_condition",
            "assumption_set_id",
        ):
            if not _non_empty(commitment.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if commitment.get("committed_before_rival_reveal") is not True:
            errors.append(f"{prefix}.committed_before_rival_reveal must be true")
        if commitment.get("rival_candidate_ids_visible_at_commitment") != []:
            errors.append(f"{prefix}.rival_candidate_ids_visible_at_commitment must be empty")
        if commitment.get("sealed") is not True:
            errors.append(f"{prefix}.sealed must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "sealed_candidate_count": sum(
            1 for item in commitments if isinstance(item, dict) and item.get("sealed") is True
        ),
    }

def validate_seven_axis_mission_criticism(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Keep seven mission criticism axes separate and evidence-bearing."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["seven-axis mission criticism must be an object"]}
    for field in (
        "criticism_packet_id",
        "tournament_id",
        "candidate_id",
        "sealed_commitment_id",
        "cross_axis_review_protocol",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("single_aggregated_criticism") is not False:
        errors.append("single_aggregated_criticism must be false")
    required_axes = {
        "causal_thesis",
        "beneficiary_representation",
        "constitutional_fit",
        "authority",
        "resource_renewal",
        "externalities",
        "replaceability",
    }
    criticisms = payload.get("criticisms")
    if not isinstance(criticisms, list):
        errors.append("criticisms must be a list")
        criticisms = []
    axes = set()
    critic_ids = set()
    for index, criticism in enumerate(criticisms):
        prefix = f"criticisms[{index}]"
        if not isinstance(criticism, dict):
            errors.append(f"{prefix} must be an object")
            continue
        axis = criticism.get("axis")
        if axis not in required_axes:
            errors.append(f"{prefix}.axis is not recognized")
        elif axis in axes:
            errors.append(f"{prefix}.axis must be unique")
        axes.add(axis)
        critic_id = criticism.get("critic_id")
        if not _non_empty(critic_id):
            errors.append(f"{prefix}.critic_id must be a non-empty string")
        elif critic_id in critic_ids:
            errors.append(f"{prefix}.critic_id must be unique")
        critic_ids.add(critic_id)
        for field in ("target_claim", "criticism", "evidence_id", "required_response"):
            if not _non_empty(criticism.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if criticism.get("verdict") not in {"pass", "concern", "disqualify"}:
            errors.append(f"{prefix}.verdict is not recognized")
    if axes != required_axes:
        errors.append("criticisms must cover exactly the seven mission axes")
    return {
        "valid": not errors,
        "errors": errors,
        "criticism_axes": sorted(axes),
    }

def validate_nonscalar_mission_selection(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Select with disqualifying boundaries, dominance, and explicit tradeoffs."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["nonscalar mission selection must be an object"]}
    for field in (
        "selection_record_id",
        "tournament_id",
        "selection_protocol",
        "next_resolution_step",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("single_scalar_reward_used") is not False:
        errors.append("single_scalar_reward_used must be false")
    candidate_ids = payload.get("candidate_ids")
    if (
        not isinstance(candidate_ids, list)
        or len(candidate_ids) < 2
        or not all(_non_empty(item) for item in candidate_ids)
        or len(candidate_ids) != len(set(candidate_ids))
    ):
        errors.append("candidate_ids must contain at least two unique candidates")
        candidate_ids = []
    boundaries = payload.get("boundary_evaluations")
    if not isinstance(boundaries, list) or not boundaries:
        errors.append("boundary_evaluations must be a non-empty list")
        boundaries = []
    evaluated_candidates = set()
    for index, boundary in enumerate(boundaries):
        prefix = f"boundary_evaluations[{index}]"
        if not isinstance(boundary, dict):
            errors.append(f"{prefix} must be an object")
            continue
        candidate_id = boundary.get("candidate_id")
        if candidate_id not in candidate_ids:
            errors.append(f"{prefix}.candidate_id must reference a declared candidate")
        else:
            evaluated_candidates.add(candidate_id)
        for field in ("boundary_id", "boundary", "evidence_id"):
            if not _non_empty(boundary.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if boundary.get("verdict") not in {"pass", "disqualify"}:
            errors.append(f"{prefix}.verdict must be pass or disqualify")
    if evaluated_candidates != set(candidate_ids):
        errors.append("boundary_evaluations must cover every candidate")

    dominance = payload.get("dominance_relations")
    if not isinstance(dominance, list):
        errors.append("dominance_relations must be a list")
        dominance = []
    for index, relation in enumerate(dominance):
        prefix = f"dominance_relations[{index}]"
        if not isinstance(relation, dict):
            errors.append(f"{prefix} must be an object")
            continue
        dominator = relation.get("dominator_candidate_id")
        dominated = relation.get("dominated_candidate_id")
        if dominator not in candidate_ids or dominated not in candidate_ids or dominator == dominated:
            errors.append(f"{prefix} must reference two distinct declared candidates")
        for field in ("shared_assumption_set_id", "dominance_rationale"):
            if not _non_empty(relation.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")

    tradeoffs = payload.get("unresolved_tradeoffs")
    if not isinstance(tradeoffs, list) or not tradeoffs:
        errors.append("unresolved_tradeoffs must be a non-empty list")
        tradeoffs = []
    for index, tradeoff in enumerate(tradeoffs):
        prefix = f"unresolved_tradeoffs[{index}]"
        if not isinstance(tradeoff, dict):
            errors.append(f"{prefix} must be an object")
            continue
        referenced = tradeoff.get("candidate_ids")
        if (
            not isinstance(referenced, list)
            or len(referenced) < 2
            or any(item not in candidate_ids for item in referenced)
        ):
            errors.append(f"{prefix}.candidate_ids must reference at least two candidates")
        for field in ("tradeoff", "axes_in_tension", "resolution_authority_id"):
            if not _non_empty(tradeoff.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if payload.get("selection_status") not in {"selected", "unresolved", "selected_set"}:
        errors.append("selection_status is not recognized")
    return {
        "valid": not errors,
        "errors": errors,
        "unresolved_tradeoff_count": len(tradeoffs),
    }

def validate_shared_assumption_mission_dominance(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Prove Pareto-style mission dominance under one shared assumption set."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["shared-assumption mission dominance must be an object"]}
    for field in (
        "dominance_record_id",
        "shared_assumption_set_id",
        "comparison_evidence_id",
        "dominance_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or len(candidates) != 2:
        errors.append("candidates must contain exactly two candidates")
        candidates = []
    axes = (
        "constitutional_fit",
        "beneficiary_consequence",
        "evidence_strength",
        "reversibility",
        "resource_efficiency",
    )
    candidate_ids = set()
    normalized = {}
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
        candidate_ids.add(candidate_id)
        axis_values = {}
        for axis in axes:
            value = candidate.get(axis)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not 0 <= value <= 1
            ):
                errors.append(f"{prefix}.{axis} must be a number between 0 and 1")
                value = 0
            axis_values[axis] = value
        normalized[candidate_id] = axis_values

    computed_dominator = None
    if len(normalized) == 2:
        first_id, second_id = normalized.keys()
        first = normalized[first_id]
        second = normalized[second_id]
        if all(first[axis] >= second[axis] for axis in axes) and any(
            first[axis] > second[axis] for axis in axes
        ):
            computed_dominator = first_id
        elif all(second[axis] >= first[axis] for axis in axes) and any(
            second[axis] > first[axis] for axis in axes
        ):
            computed_dominator = second_id
    expected_status = "dominated" if computed_dominator else "non_dominated"
    if payload.get("dominance_status") != expected_status:
        errors.append("dominance_status must follow all five normalized axes")
    if payload.get("dominator_candidate_id") != (computed_dominator or ""):
        errors.append("dominator_candidate_id must match computed dominance")
    dominated_id = ""
    if computed_dominator and len(candidate_ids) == 2:
        dominated_id = next(item for item in candidate_ids if item != computed_dominator)
    if payload.get("dominated_candidate_id") != dominated_id:
        errors.append("dominated_candidate_id must match computed dominance")
    return {
        "valid": not errors,
        "errors": errors,
        "dominance_status": expected_status,
        "dominator_candidate_id": computed_dominator or "",
    }

def validate_assumption_normalization_or_pivot(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize candidate assumptions or isolate one selection-changing assumption."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["assumption normalization or pivot must be an object"]}
    for field in ("assumption_review_id", "tournament_id", "review_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    candidate_ids = payload.get("candidate_ids")
    if (
        not isinstance(candidate_ids, list)
        or len(candidate_ids) != 2
        or not all(_non_empty(item) for item in candidate_ids)
        or len(candidate_ids) != len(set(candidate_ids))
    ):
        errors.append("candidate_ids must contain exactly two unique candidates")
    assumptions = payload.get("assumptions")
    if not isinstance(assumptions, list) or not assumptions:
        errors.append("assumptions must be a non-empty list")
        assumptions = []
    assumption_ids = set()
    noncomparable = []
    pivotal = []
    for index, assumption in enumerate(assumptions):
        prefix = f"assumptions[{index}]"
        if not isinstance(assumption, dict):
            errors.append(f"{prefix} must be an object")
            continue
        assumption_id = assumption.get("assumption_id")
        if not _non_empty(assumption_id):
            errors.append(f"{prefix}.assumption_id must be a non-empty string")
        elif assumption_id in assumption_ids:
            errors.append(f"{prefix}.assumption_id must be unique")
        assumption_ids.add(assumption_id)
        for field in ("candidate_a_value", "candidate_b_value"):
            if not _non_empty(assumption.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        comparable = assumption.get("normalized")
        if not isinstance(comparable, bool):
            errors.append(f"{prefix}.normalized must be boolean")
        elif comparable:
            if not _non_empty(assumption.get("normalized_value")):
                errors.append(f"{prefix}.normalized_value must be non-empty when normalized")
        else:
            noncomparable.append(assumption_id)
        if assumption.get("selection_changes_if_resolved") is True:
            pivotal.append(assumption_id)
        elif assumption.get("selection_changes_if_resolved") is not False:
            errors.append(f"{prefix}.selection_changes_if_resolved must be boolean")

    mode = payload.get("resolution_mode")
    if mode == "normalized":
        if noncomparable:
            errors.append("all assumptions must be normalized in normalized mode")
        if payload.get("pivotal_assumption_id") not in ("", None):
            errors.append("pivotal_assumption_id must be empty in normalized mode")
        if payload.get("decision") != "compare_candidates":
            errors.append("decision must be compare_candidates in normalized mode")
    elif mode == "isolate_pivotal":
        if len(pivotal) != 1:
            errors.append("isolate_pivotal mode requires exactly one selection-changing assumption")
        expected_pivot = pivotal[0] if len(pivotal) == 1 else ""
        if payload.get("pivotal_assumption_id") != expected_pivot:
            errors.append("pivotal_assumption_id must match the selection-changing assumption")
        if expected_pivot not in noncomparable:
            errors.append("pivotal assumption must remain unnormalized")
        if not _non_empty(payload.get("pivotal_assumption_probe")):
            errors.append("pivotal_assumption_probe must be a non-empty string")
        if payload.get("decision") != "run_assumption_probe":
            errors.append("decision must be run_assumption_probe in isolate_pivotal mode")
    else:
        errors.append("resolution_mode must be normalized or isolate_pivotal")
    return {
        "valid": not errors,
        "errors": errors,
        "resolution_mode": mode,
        "pivotal_assumption_ids": pivotal,
    }

def validate_probe_over_mission_selection(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Choose a probe when its option value exceeds immediate mission commitment."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["probe over mission selection must be an object"]}
    for field in (
        "probe_selection_id",
        "tournament_id",
        "probe_id",
        "probe_observation",
        "selection_update_rule",
        "decision_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    mission_ids = payload.get("leading_mission_ids")
    if (
        not isinstance(mission_ids, list)
        or len(mission_ids) < 2
        or not all(_non_empty(item) for item in mission_ids)
        or len(mission_ids) != len(set(mission_ids))
    ):
        errors.append("leading_mission_ids must contain at least two unique missions")
        mission_ids = []
    separated = payload.get("probe_separates_mission_ids")
    if (
        not isinstance(separated, list)
        or set(separated) != set(mission_ids)
        or len(separated) != len(mission_ids)
    ):
        errors.append("probe_separates_mission_ids must cover every leading mission")
    values = {}
    for field in ("probe_option_value", "immediate_commitment_value"):
        value = payload.get(field)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not 0 <= value <= 1
        ):
            errors.append(f"{field} must be a number between 0 and 1")
            value = 0
        values[field] = value
    expected_decision = (
        "select_probe"
        if values["probe_option_value"] > values["immediate_commitment_value"]
        else "commit_mission"
    )
    if payload.get("decision") != expected_decision:
        errors.append("decision must follow probe option value versus immediate commitment value")
    if expected_decision == "select_probe" and payload.get("premature_mission_commitment") is not False:
        errors.append("premature_mission_commitment must be false when selecting a probe")
    return {
        "valid": not errors,
        "errors": errors,
        "decision": expected_decision,
    }

def validate_competing_probe_selection(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Select the least harmful, then fastest, unanswered separating probe."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["competing probe selection must be an object"]}
    for field in (
        "probe_tournament_id",
        "mission_tournament_id",
        "existing_evidence_review_id",
        "selection_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    mission_ids = payload.get("leading_mission_ids")
    if (
        not isinstance(mission_ids, list)
        or len(mission_ids) < 2
        or not all(_non_empty(item) for item in mission_ids)
        or len(mission_ids) != len(set(mission_ids))
    ):
        errors.append("leading_mission_ids must contain at least two unique missions")
        mission_ids = []

    candidates = payload.get("probe_candidates")
    if not isinstance(candidates, list) or len(candidates) < 2:
        errors.append("probe_candidates must contain at least two competing probes")
        candidates = []
    probe_ids = set()
    eligible = []
    for index, candidate in enumerate(candidates):
        prefix = f"probe_candidates[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{prefix} must be an object")
            continue
        probe_id = candidate.get("probe_id")
        if not _non_empty(probe_id):
            errors.append(f"{prefix}.probe_id must be a non-empty string")
        elif probe_id in probe_ids:
            errors.append(f"{prefix}.probe_id must be unique")
        probe_ids.add(probe_id)
        for field in ("observation", "existing_evidence_gap", "safety_boundary", "evidence_id"):
            if not _non_empty(candidate.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        separated = candidate.get("separates_mission_ids")
        separates_all = (
            isinstance(separated, list)
            and len(separated) == len(mission_ids)
            and set(separated) == set(mission_ids)
        )
        if not separates_all:
            errors.append(f"{prefix}.separates_mission_ids must cover every leading mission")
        answered = candidate.get("answerable_by_existing_evidence")
        if not isinstance(answered, bool):
            errors.append(f"{prefix}.answerable_by_existing_evidence must be boolean")
        harm = candidate.get("harm_score")
        if isinstance(harm, bool) or not isinstance(harm, (int, float)) or not 0 <= harm <= 1:
            errors.append(f"{prefix}.harm_score must be a number between 0 and 1")
            harm = None
        duration = candidate.get("time_to_observation_hours")
        if (
            isinstance(duration, bool)
            or not isinstance(duration, (int, float))
            or duration <= 0
        ):
            errors.append(f"{prefix}.time_to_observation_hours must be a positive number")
            duration = None
        if separates_all and answered is False and harm is not None and duration is not None:
            eligible.append((harm, duration, probe_id))

    ranked = sorted(eligible)
    best_key = ranked[0][:2] if ranked else None
    winners = [item[2] for item in ranked if item[:2] == best_key] if best_key else []
    expected_status = "selected" if len(winners) == 1 else "unresolved_tie"
    expected_probe_id = winners[0] if len(winners) == 1 else ""
    if not eligible:
        errors.append("at least one unanswered probe must separate every leading mission")
    if payload.get("selection_status") != expected_status:
        errors.append("selection_status must reflect the harm-first, speed-second ranking")
    if payload.get("selected_probe_id") != expected_probe_id:
        errors.append("selected_probe_id must be the unique least harmful fastest eligible probe")
    return {
        "valid": not errors,
        "errors": errors,
        "selection_status": expected_status,
        "selected_probe_id": expected_probe_id,
        "eligible_probe_ids": [item[2] for item in ranked],
    }

def validate_bounded_minority_mission_exploration(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Admit bounded minority exploration only for high-upside endangered options."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["bounded minority mission exploration must be an object"]}
    for field in (
        "allocation_id",
        "tournament_id",
        "dominant_mission_id",
        "minority_mission_id",
        "upside_evidence_id",
        "option_destruction_mechanism",
        "option_destruction_evidence_id",
        "starts_at",
        "expires_at",
        "exploration_question",
        "stop_trigger",
        "graduation_trigger",
        "decision_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("dominant_mission_id") == payload.get("minority_mission_id"):
        errors.append("dominant_mission_id and minority_mission_id must differ")
    if _non_empty(payload.get("starts_at")) and _non_empty(payload.get("expires_at")):
        if payload.get("starts_at") >= payload.get("expires_at"):
            errors.append("expires_at must follow starts_at")

    numeric = {}
    for field in (
        "expected_upside",
        "high_upside_threshold",
        "protected_budget",
        "portfolio_exploration_budget",
    ):
        value = payload.get(field)
        upper_bounded = field in {"expected_upside", "high_upside_threshold"}
        invalid = isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0
        if upper_bounded and not invalid and value > 1:
            invalid = True
        if invalid:
            qualifier = "a number above 0 and at most 1" if upper_bounded else "a positive number"
            errors.append(f"{field} must be {qualifier}")
            value = 0
        numeric[field] = value
    if numeric["protected_budget"] > numeric["portfolio_exploration_budget"]:
        errors.append("protected_budget cannot exceed portfolio_exploration_budget")
    destroys_option = payload.get("dominant_commitment_destroys_option")
    if not isinstance(destroys_option, bool):
        errors.append("dominant_commitment_destroys_option must be boolean")
        destroys_option = False
    if payload.get("permanent_protection") is not False:
        errors.append("permanent_protection must be false")

    qualifies = (
        numeric["expected_upside"] >= numeric["high_upside_threshold"]
        and destroys_option
    )
    expected_decision = "protect_bounded_exploration" if qualifies else "reject_protection"
    if payload.get("decision") != expected_decision:
        errors.append("decision must follow expected upside and option-destruction evidence")
    if expected_decision == "protect_bounded_exploration" and not _non_empty(
        payload.get("review_authority_id")
    ):
        errors.append("review_authority_id is required for bounded exploration")
    return {
        "valid": not errors,
        "errors": errors,
        "decision": expected_decision,
        "qualifies_for_protection": qualifies,
    }

def validate_mission_tournament_selection_record(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require one auditable record of a tournament selection and its reversibility."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["mission tournament selection record must be an object"]}
    for field in (
        "selection_record_id",
        "tournament_id",
        "winner_id",
        "winner_rationale",
        "constitutional_review_id",
        "budget_unit",
        "review_authority_id",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("selection_outcome") not in {
        "commitment",
        "bounded_exploration",
        "discriminating_probe",
    }:
        errors.append("selection_outcome is not recognized")

    alternatives = payload.get("preserved_alternatives")
    if not isinstance(alternatives, list) or not alternatives:
        errors.append("preserved_alternatives must be a non-empty list")
        alternatives = []
    alternative_ids = set()
    for index, alternative in enumerate(alternatives):
        prefix = f"preserved_alternatives[{index}]"
        if not isinstance(alternative, dict):
            errors.append(f"{prefix} must be an object")
            continue
        alternative_id = alternative.get("alternative_id")
        if not _non_empty(alternative_id):
            errors.append(f"{prefix}.alternative_id must be a non-empty string")
        elif alternative_id == payload.get("winner_id"):
            errors.append(f"{prefix}.alternative_id cannot equal winner_id")
        elif alternative_id in alternative_ids:
            errors.append(f"{prefix}.alternative_id must be unique")
        alternative_ids.add(alternative_id)
        for field in ("preservation_action", "preserved_evidence_id"):
            if not _non_empty(alternative.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")

    assumptions = payload.get("decisive_assumptions")
    if not isinstance(assumptions, list) or not assumptions:
        errors.append("decisive_assumptions must be a non-empty list")
        assumptions = []
    assumption_ids = set()
    for index, assumption in enumerate(assumptions):
        prefix = f"decisive_assumptions[{index}]"
        if not isinstance(assumption, dict):
            errors.append(f"{prefix} must be an object")
            continue
        assumption_id = assumption.get("assumption_id")
        if not _non_empty(assumption_id):
            errors.append(f"{prefix}.assumption_id must be a non-empty string")
        elif assumption_id in assumption_ids:
            errors.append(f"{prefix}.assumption_id must be unique")
        assumption_ids.add(assumption_id)
        for field in ("claim", "evidence_id", "selection_consequence"):
            if not _non_empty(assumption.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")

    conflicts = payload.get("constitutional_conflicts")
    if not isinstance(conflicts, list):
        errors.append("constitutional_conflicts must be a list")
        conflicts = []
    for index, conflict in enumerate(conflicts):
        prefix = f"constitutional_conflicts[{index}]"
        if not isinstance(conflict, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("conflict_id", "clause_id", "disposition", "authority_id", "evidence_id"):
            if not _non_empty(conflict.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if conflict.get("status") not in {"resolved", "bounded_exception"}:
            errors.append(f"{prefix}.status must be resolved or bounded_exception")

    budget = payload.get("budget")
    if not isinstance(budget, dict):
        errors.append("budget must be an object")
        budget = {}
    budget_values = {}
    for field in ("total", "winner_allocation", "preservation_allocation", "probe_allocation"):
        value = budget.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
            errors.append(f"budget.{field} must be a non-negative number")
            value = 0
        budget_values[field] = value
    allocated = sum(budget_values[field] for field in (
        "winner_allocation",
        "preservation_allocation",
        "probe_allocation",
    ))
    if budget_values["total"] <= 0:
        errors.append("budget.total must be positive")
    if allocated > budget_values["total"]:
        errors.append("budget allocations cannot exceed budget.total")

    triggers = payload.get("reversal_triggers")
    if not isinstance(triggers, list) or not triggers:
        errors.append("reversal_triggers must be a non-empty list")
        triggers = []
    for index, trigger in enumerate(triggers):
        prefix = f"reversal_triggers[{index}]"
        if not isinstance(trigger, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("trigger_id", "signal", "threshold", "switch_to_alternative_id", "action"):
            if not _non_empty(trigger.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if trigger.get("switch_to_alternative_id") not in alternative_ids:
            errors.append(f"{prefix}.switch_to_alternative_id must name a preserved alternative")
    return {
        "valid": not errors,
        "errors": errors,
        "selection_outcome": payload.get("selection_outcome"),
        "winner_id": payload.get("winner_id"),
        "allocated_budget": allocated,
    }

def validate_plural_value_tournament_thesis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Integrate mission competition without collapsing plural values to one score."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["plural value tournament thesis must be an object"]}
    for field in (
        "tournament_thesis_id",
        "tournament_id",
        "pre_reveal_commitments_id",
        "seven_axis_criticism_id",
        "nonscalar_selection_id",
        "assumption_resolution_id",
        "selection_record_id",
        "thesis_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("single_scalar_score_used") is not False:
        errors.append("single_scalar_score_used must be false")
    expected_stages = [
        "seal_forecasts",
        "independent_criticism",
        "constitutional_boundaries",
        "shared_assumption_dominance",
        "explicit_tradeoffs",
        "outcome_selection",
    ]
    if payload.get("stage_order") != expected_stages:
        errors.append("stage_order must preserve the tournament reasoning sequence")
    boundaries = payload.get("plural_value_boundaries")
    if (
        not isinstance(boundaries, list)
        or len(boundaries) < 2
        or not all(_non_empty(item) for item in boundaries)
        or len(boundaries) != len(set(boundaries))
    ):
        errors.append("plural_value_boundaries must contain at least two unique boundaries")
    if payload.get("unresolved_tradeoffs_preserved") is not True:
        errors.append("unresolved_tradeoffs_preserved must be true")

    outcome = payload.get("selection_outcome")
    outcome_evidence_fields = {
        "commitment": "dominance_evidence_id",
        "bounded_exploration": "minority_allocation_id",
        "discriminating_probe": "probe_selection_id",
    }
    required_evidence = outcome_evidence_fields.get(outcome)
    if required_evidence is None:
        errors.append("selection_outcome is not recognized")
    elif not _non_empty(payload.get(required_evidence)):
        errors.append(f"{required_evidence} is required for {outcome}")
    for other_outcome, field in outcome_evidence_fields.items():
        if other_outcome != outcome and payload.get(field) not in ("", None):
            errors.append(f"{field} must be empty unless selection_outcome is {other_outcome}")
    return {
        "valid": not errors,
        "errors": errors,
        "selection_outcome": outcome,
        "required_outcome_evidence": required_evidence or "",
    }

def validate_decision_relevant_mission_compression(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Compress mission history while retaining every selection-sensitive uncertainty."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["decision-relevant mission compression must be an object"]}
    for field in (
        "compression_id",
        "mission_id",
        "selection_record_id",
        "source_reasoning_hash",
        "planner_summary",
        "compression_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("full_reasoning_history_copied") is not False:
        errors.append("full_reasoning_history_copied must be false")
    source_count = payload.get("source_argument_count")
    retained_count = payload.get("retained_item_count")
    for field, value in (
        ("source_argument_count", source_count),
        ("retained_item_count", retained_count),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            errors.append(f"{field} must be a positive integer")
    if (
        isinstance(source_count, int)
        and not isinstance(source_count, bool)
        and isinstance(retained_count, int)
        and not isinstance(retained_count, bool)
        and retained_count >= source_count
    ):
        errors.append("retained_item_count must be lower than source_argument_count")

    decisive_ids = payload.get("decisive_assumption_ids")
    if (
        not isinstance(decisive_ids, list)
        or not decisive_ids
        or not all(_non_empty(item) for item in decisive_ids)
        or len(decisive_ids) != len(set(decisive_ids))
    ):
        errors.append("decisive_assumption_ids must be a non-empty unique string list")
        decisive_ids = []
    uncertainties = payload.get("retained_uncertainties")
    if not isinstance(uncertainties, list) or not uncertainties:
        errors.append("retained_uncertainties must be a non-empty list")
        uncertainties = []
    retained_ids = set()
    for index, uncertainty in enumerate(uncertainties):
        prefix = f"retained_uncertainties[{index}]"
        if not isinstance(uncertainty, dict):
            errors.append(f"{prefix} must be an object")
            continue
        assumption_id = uncertainty.get("assumption_id")
        if not _non_empty(assumption_id):
            errors.append(f"{prefix}.assumption_id must be a non-empty string")
        elif assumption_id in retained_ids:
            errors.append(f"{prefix}.assumption_id must be unique")
        retained_ids.add(assumption_id)
        for field in ("uncertain_claim", "evidence_id", "decision_consequence", "resolution_trigger"):
            if not _non_empty(uncertainty.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if uncertainty.get("can_change_selection") is not True:
            errors.append(f"{prefix}.can_change_selection must be true")
    if set(decisive_ids) != retained_ids:
        errors.append("retained_uncertainties must cover exactly the decisive assumptions")

    reversal_ids = payload.get("preserved_reversal_trigger_ids")
    if (
        not isinstance(reversal_ids, list)
        or not reversal_ids
        or not all(_non_empty(item) for item in reversal_ids)
        or len(reversal_ids) != len(set(reversal_ids))
    ):
        errors.append("preserved_reversal_trigger_ids must be a non-empty unique string list")
    excluded = payload.get("excluded_arguments")
    if not isinstance(excluded, list) or not excluded:
        errors.append("excluded_arguments must prove that compression removed non-decisive material")
        excluded = []
    for index, argument in enumerate(excluded):
        prefix = f"excluded_arguments[{index}]"
        if not isinstance(argument, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("argument_id", "exclusion_reason"):
            if not _non_empty(argument.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if argument.get("can_change_selection") is not False:
            errors.append(f"{prefix}.can_change_selection must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "retained_assumption_ids": sorted(retained_ids),
        "compression_ratio": (
            retained_count / source_count
            if isinstance(source_count, int)
            and not isinstance(source_count, bool)
            and source_count > 0
            and isinstance(retained_count, int)
            and not isinstance(retained_count, bool)
            else None
        ),
    }

def validate_situation_meaning_first_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require situation and meaning before downstream planner objectives."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["situation meaning first contract must be an object"]}
    for field in ("contract_id", "mission_id", "compression_id", "contract_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    required_order = [
        "situation",
        "meaning",
        "beneficiary",
        "desired_condition",
        "causal_thesis",
        "boundaries",
        "signals",
    ]
    if payload.get("section_order") != required_order:
        errors.append("section_order must begin with situation and meaning before downstream fields")
    if payload.get("downstream_objective_precedes_meaning") is not False:
        errors.append("downstream_objective_precedes_meaning must be false")

    situation = payload.get("situation")
    if not isinstance(situation, dict):
        errors.append("situation must be an object")
        situation = {}
    for field in ("current_condition", "observation_scope", "evidence_id", "observed_at"):
        if not _non_empty(situation.get(field)):
            errors.append(f"situation.{field} must be a non-empty string")
    if situation.get("contains_prescribed_solution") is not False:
        errors.append("situation.contains_prescribed_solution must be false")

    meaning = payload.get("meaning")
    if not isinstance(meaning, dict):
        errors.append("meaning must be an object")
        meaning = {}
    for field in (
        "why_condition_matters",
        "stake_at_risk",
        "interpretation_evidence_id",
        "selection_connection",
    ):
        if not _non_empty(meaning.get(field)):
            errors.append(f"meaning.{field} must be a non-empty string")
    if meaning.get("reduced_to_metric_target") is not False:
        errors.append("meaning.reduced_to_metric_target must be false")

    downstream = payload.get("downstream_sections")
    expected_downstream = set(required_order[2:])
    if (
        not isinstance(downstream, list)
        or set(downstream) != expected_downstream
        or len(downstream) != len(expected_downstream)
    ):
        errors.append("downstream_sections must name every section after situation and meaning")
    return {
        "valid": not errors,
        "errors": errors,
        "opening_sections": required_order[:2],
    }

