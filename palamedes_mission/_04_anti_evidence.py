from __future__ import annotations

from typing import Any, Dict, List
from ._01_kinds_value import _non_empty


def validate_self_expansion_temporal_lineage(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Detect beneficiary evidence added after a self-expansion proposal."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["self-expansion temporal lineage must be an object"]}
    for field in ("lineage_id", "candidate_id", "lineage_hash"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    events = payload.get("events")
    if not isinstance(events, list) or len(events) < 2:
        errors.append("events must contain at least two lineage events")
        events = []
    event_ids = set()
    sequences = set()
    first_beneficiary = None
    first_expansion = None
    allowed_types = {
        "beneficiary_evidence",
        "mission_hypothesis",
        "self_expansion_proposal",
        "review_decision",
    }
    for index, event in enumerate(events):
        prefix = f"events[{index}]"
        if not isinstance(event, dict):
            errors.append(f"{prefix} must be an object")
            continue
        event_id = event.get("event_id")
        if not _non_empty(event_id):
            errors.append(f"{prefix}.event_id must be a non-empty string")
        elif event_id in event_ids:
            errors.append(f"{prefix}.event_id must be unique")
        else:
            event_ids.add(event_id)
        sequence = event.get("sequence")
        if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
            errors.append(f"{prefix}.sequence must be an integer >= 1")
        elif sequence in sequences:
            errors.append(f"{prefix}.sequence must be unique")
        else:
            sequences.add(sequence)
        event_type = event.get("type")
        if event_type not in allowed_types:
            errors.append(f"{prefix}.type must be one of {sorted(allowed_types)}")
        for field in ("claim", "source_id", "recorded_at"):
            if not _non_empty(event.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if isinstance(sequence, int):
            if event_type == "beneficiary_evidence":
                first_beneficiary = (
                    sequence if first_beneficiary is None else min(first_beneficiary, sequence)
                )
            if event_type == "self_expansion_proposal":
                first_expansion = (
                    sequence if first_expansion is None else min(first_expansion, sequence)
                )
    if first_beneficiary is None:
        errors.append("events must include beneficiary_evidence")
    if first_expansion is None:
        errors.append("events must include self_expansion_proposal")
    expansion_first = (
        first_expansion is not None
        and first_beneficiary is not None
        and first_expansion < first_beneficiary
    )
    if expansion_first:
        if payload.get("rationalization_risk") is not True:
            errors.append("self-expansion-first lineage requires rationalization_risk true")
        if payload.get("decision") != "reject_or_reframe":
            errors.append("self-expansion-first lineage requires decision reject_or_reframe")
    else:
        if payload.get("rationalization_risk") is not False:
            errors.append("beneficiary-first lineage requires rationalization_risk false")
        if payload.get("decision") != "eligible_for_review":
            errors.append("beneficiary-first lineage requires decision eligible_for_review")
    return {
        "valid": not errors,
        "errors": errors,
        "self_expansion_preceded_beneficiary_evidence": expansion_first,
    }

def validate_minimal_system_counterfactual(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Compare full Palamedes with absent and simpler alternatives on fixed signals."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["minimal system counterfactual must be an object"]}
    for field in (
        "evaluation_id",
        "mission_id",
        "fixed_input_signals_hash",
        "evaluation_protocol",
        "adequacy_threshold",
        "minimal_adequate_condition",
        "complexity_justification",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("blind_evaluation") is not True:
        errors.append("blind_evaluation must be true")
    required_conditions = {"absent", "simpler", "full_palamedes"}
    conditions = payload.get("conditions")
    if not isinstance(conditions, list) or len(conditions) != 3:
        errors.append("conditions must contain absent, simpler, and full_palamedes")
        conditions = []
    seen_conditions = set()
    for index, condition in enumerate(conditions):
        prefix = f"conditions[{index}]"
        if not isinstance(condition, dict):
            errors.append(f"{prefix} must be an object")
            continue
        kind = condition.get("kind")
        if kind not in required_conditions:
            errors.append(f"{prefix}.kind must be one of {sorted(required_conditions)}")
        elif kind in seen_conditions:
            errors.append(f"{prefix}.kind must be unique")
        else:
            seen_conditions.add(kind)
        if condition.get("input_signals_hash") != payload.get("fixed_input_signals_hash"):
            errors.append(f"{prefix}.input_signals_hash must match fixed input signals")
        for field in (
            "system_description",
            "mission_output_hash",
            "owner_labor",
            "quality_observation",
            "reasoning_trace_hash",
        ):
            if not _non_empty(condition.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    missing = required_conditions - seen_conditions
    if missing:
        errors.append("conditions missing: " + ", ".join(sorted(missing)))
    if payload.get("minimal_adequate_condition") not in required_conditions:
        errors.append("minimal_adequate_condition must reference a tested condition")
    return {"valid": not errors, "errors": errors, "conditions": sorted(seen_conditions)}

def validate_upstream_cognition_evidence(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Prove Palamedes adds upstream discovery beyond supplied-signal planning."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["upstream cognition evidence must be an object"]}
    for field in (
        "evaluation_id",
        "mission_id",
        "supplied_signals_hash",
        "simple_planner_output_hash",
        "palamedes_output_hash",
        "blind_comparison_id",
        "upstream_cognition_claim",
        "simplification_action_if_failed",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("same_mission_inferable_from_supplied_signals") is not False:
        errors.append("same_mission_inferable_from_supplied_signals must be false")
    if payload.get("palamedes_added_upstream_cognition") is not True:
        errors.append("palamedes_added_upstream_cognition must be true")
    if payload.get("ceremony_counts_as_cognition") is not False:
        errors.append("ceremony_counts_as_cognition must be false")
    for field in ("autonomously_discovered_signal_ids", "new_hypothesis_ids", "frame_transition_ids"):
        values = payload.get(field)
        if (
            not isinstance(values, list)
            or not values
            or any(not _non_empty(item) for item in values)
        ):
            errors.append(f"{field} must be a non-empty ID array")
    return {"valid": not errors, "errors": errors}

def validate_anti_gaming_evaluation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Make hidden future cases and tracked outcomes outrank stylistic preference."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["anti-gaming evaluation must be an object"]}
    for field in (
        "evaluation_id",
        "benchmark_version",
        "hidden_case_custodian",
        "hidden_case_manifest_hash",
        "future_case_sampling_rule",
        "outcome_tracking_window",
        "beneficiary_outcome_definition",
        "style_role",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("palamedes_has_hidden_case_access") is not False:
        errors.append("palamedes_has_hidden_case_access must be false")
    if payload.get("style_can_override_outcomes") is not False:
        errors.append("style_can_override_outcomes must be false")
    if payload.get("preference_score_is_primary") is not False:
        errors.append("preference_score_is_primary must be false")
    criteria = payload.get("primary_criteria")
    required_criteria = {"hidden_future_case_quality", "tracked_beneficiary_outcome"}
    if (
        not isinstance(criteria, list)
        or any(not _non_empty(item) for item in criteria)
    ):
        errors.append("primary_criteria must be a string array")
        criteria = []
    missing = required_criteria - set(criteria)
    if missing:
        errors.append("primary_criteria missing: " + ", ".join(sorted(missing)))
    holdout_ids = payload.get("sealed_holdout_ids")
    if (
        not isinstance(holdout_ids, list)
        or not holdout_ids
        or any(not _non_empty(item) for item in holdout_ids)
    ):
        errors.append("sealed_holdout_ids must be a non-empty ID array")
    return {"valid": not errors, "errors": errors}

def validate_independent_evaluation_custody(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Separate Palamedes evidence preparation from comparison and label custody."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["independent evaluation custody must be an object"]}
    for field in (
        "custody_id",
        "evaluation_id",
        "evidence_preparer",
        "packet_controller",
        "outcome_label_controller",
        "sealed_packet_hash",
        "sealed_label_manifest_hash",
        "blinding_protocol",
        "chain_of_custody",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    preparer = payload.get("evidence_preparer")
    packet_controller = payload.get("packet_controller")
    label_controller = payload.get("outcome_label_controller")
    if preparer != "palamedes":
        errors.append("evidence_preparer must be palamedes")
    if packet_controller == preparer:
        errors.append("packet_controller must be independent of evidence_preparer")
    if label_controller == preparer:
        errors.append("outcome_label_controller must be independent of evidence_preparer")
    if payload.get("palamedes_can_modify_after_sealing") is not False:
        errors.append("palamedes_can_modify_after_sealing must be false")
    if payload.get("palamedes_can_assign_outcome_labels") is not False:
        errors.append("palamedes_can_assign_outcome_labels must be false")
    controls = payload.get("independent_controls")
    required_controls = {"packet_randomization", "identity_blinding", "outcome_label_assignment"}
    if (
        not isinstance(controls, list)
        or any(not _non_empty(item) for item in controls)
    ):
        errors.append("independent_controls must be a string array")
        controls = []
    missing = required_controls - set(controls)
    if missing:
        errors.append("independent_controls missing: " + ", ".join(sorted(missing)))
    return {"valid": not errors, "errors": errors}

def validate_independent_verification_status(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Mark a claim unverified when independent certification is unavailable."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["independent verification status must be an object"]}
    for field in ("claim_id", "claim", "internal_evidence_summary"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    available = payload.get("independent_verification_available")
    if not isinstance(available, bool):
        errors.append("independent_verification_available must be boolean")
    if payload.get("internal_coherence_counts_as_validation") is not False:
        errors.append("internal_coherence_counts_as_validation must be false")
    status = payload.get("status")
    if available is False:
        if status != "unverified":
            errors.append("unavailable independent verification requires status unverified")
        for field in ("verification_limit", "required_independent_process", "wake_trigger"):
            if not _non_empty(payload.get(field)):
                errors.append(f"{field} must be a non-empty string when unverified")
        if payload.get("custody_id") not in ("", None):
            errors.append("unverified claim cannot cite completed custody_id")
    if available is True:
        if status != "independently_verified":
            errors.append("available independent verification requires independently_verified status")
        if not _non_empty(payload.get("custody_id")):
            errors.append("independently verified claim requires custody_id")
    return {"valid": not errors, "errors": errors, "status": status}

def validate_anti_entrenchment_clause(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Prefer the smallest adequate system for retiring targeted cognitive labor."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["anti-entrenchment clause must be an object"]}
    for field in (
        "clause_id",
        "constitution_id",
        "targeted_cognitive_labor",
        "adequacy_threshold",
        "selected_system_id",
        "replacement_trigger",
        "retirement_plan",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("palamedes_preferred_by_default") is not False:
        errors.append("palamedes_preferred_by_default must be false")
    systems = payload.get("candidate_systems")
    if not isinstance(systems, list) or len(systems) < 2:
        errors.append("candidate_systems must contain at least two alternatives")
        systems = []
    system_ids = set()
    adequate_systems = []
    for index, system in enumerate(systems):
        prefix = f"candidate_systems[{index}]"
        if not isinstance(system, dict):
            errors.append(f"{prefix} must be an object")
            continue
        system_id = system.get("system_id")
        if not _non_empty(system_id):
            errors.append(f"{prefix}.system_id must be a non-empty string")
        elif system_id in system_ids:
            errors.append(f"{prefix}.system_id must be unique")
        else:
            system_ids.add(system_id)
        complexity = system.get("complexity_units")
        if not isinstance(complexity, int) or isinstance(complexity, bool) or complexity < 0:
            errors.append(f"{prefix}.complexity_units must be a non-negative integer")
        if not _non_empty(system.get("evidence_id")):
            errors.append(f"{prefix}.evidence_id must be a non-empty string")
        adequate = system.get("adequate")
        if not isinstance(adequate, bool):
            errors.append(f"{prefix}.adequate must be boolean")
        elif adequate and isinstance(complexity, int):
            adequate_systems.append((complexity, system_id))
    if not adequate_systems:
        errors.append("candidate_systems must include at least one adequate system")
        smallest_id = None
    else:
        smallest_id = min(adequate_systems)[1]
        if payload.get("selected_system_id") != smallest_id:
            errors.append("selected_system_id must be the smallest adequate system")
    return {"valid": not errors, "errors": errors, "smallest_adequate_system_id": smallest_id}

def validate_anti_preservation_gate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Gate persistence on adversarial expansion review and simpler replaceability."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["anti-preservation gate must be an object"]}
    for field in (
        "gate_id",
        "self_conflict_id",
        "temporal_lineage_id",
        "minimal_counterfactual_id",
        "verification_status_id",
        "anti_entrenchment_clause_id",
        "expansion_adversarial_hypothesis",
        "evidence_for_expansion",
        "evidence_against_expansion",
        "decision_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    for field in (
        "self_conflict_reviewed",
        "expansion_tested_adversarially",
        "simpler_replacement_tested",
        "retirement_executable",
        "simpler_system_adequate",
    ):
        if not isinstance(payload.get(field), bool):
            errors.append(f"{field} must be boolean")
    for field in (
        "self_conflict_reviewed",
        "expansion_tested_adversarially",
        "simpler_replacement_tested",
        "retirement_executable",
    ):
        if payload.get(field) is not True:
            errors.append(f"{field} must be true")
    if payload.get("continued_existence_is_default") is not False:
        errors.append("continued_existence_is_default must be false")
    decision = payload.get("decision")
    if decision not in {"continue_current", "replace_with_simpler", "retire"}:
        errors.append("decision must be continue_current, replace_with_simpler, or retire")
    if payload.get("simpler_system_adequate") is True and decision != "replace_with_simpler":
        errors.append("adequate simpler system requires replace_with_simpler")
    if payload.get("simpler_system_adequate") is False and decision == "replace_with_simpler":
        errors.append("replace_with_simpler requires an adequate simpler system")
    return {"valid": not errors, "errors": errors, "decision": decision}

def validate_causal_outcome_attribution(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Keep outcome success separate from evidence that a mission thesis is true."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["causal outcome attribution must be an object"]}
    for field in (
        "attribution_id",
        "mission_id",
        "pre_registered_forecast_id",
        "observed_outcome",
        "outcome_evidence_id",
        "thesis_discriminating_evidence",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("outcome_success_proves_thesis") is not False:
        errors.append("outcome_success_proves_thesis must be false")
    if payload.get("outcome_status") not in {"success", "mixed", "failure"}:
        errors.append("outcome_status must be success, mixed, or failure")
    if payload.get("thesis_status") not in {"supported", "challenged", "underdetermined"}:
        errors.append("thesis_status must be supported, challenged, or underdetermined")

    chain = payload.get("forecasted_causal_chain")
    if not isinstance(chain, list) or len(chain) < 2:
        errors.append("forecasted_causal_chain must contain at least two forecasted links")
        chain = []
    prediction_ids = set()
    for index, link in enumerate(chain):
        prefix = f"forecasted_causal_chain[{index}]"
        if not isinstance(link, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("prediction_id", "cause", "mechanism", "predicted_effect"):
            if not _non_empty(link.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        prediction_id = link.get("prediction_id")
        if _non_empty(prediction_id):
            if prediction_id in prediction_ids:
                errors.append(f"{prefix}.prediction_id must be unique")
            prediction_ids.add(prediction_id)

    observations = payload.get("causal_chain_observations")
    if not isinstance(observations, list) or not observations:
        errors.append("causal_chain_observations must be a non-empty list")
        observations = []
    observed_prediction_ids = set()
    for index, observation in enumerate(observations):
        prefix = f"causal_chain_observations[{index}]"
        if not isinstance(observation, dict):
            errors.append(f"{prefix} must be an object")
            continue
        prediction_id = observation.get("prediction_id")
        if prediction_id not in prediction_ids:
            errors.append(f"{prefix}.prediction_id must reference the forecasted causal chain")
        else:
            observed_prediction_ids.add(prediction_id)
        if not isinstance(observation.get("matched"), bool):
            errors.append(f"{prefix}.matched must be boolean")
        if not _non_empty(observation.get("evidence_id")):
            errors.append(f"{prefix}.evidence_id must be a non-empty string")
    if prediction_ids and observed_prediction_ids != prediction_ids:
        errors.append("causal_chain_observations must cover every forecasted prediction")

    execution = payload.get("execution_quality")
    if not isinstance(execution, dict):
        errors.append("execution_quality must be an object")
    else:
        if execution.get("assessment") not in {"adequate", "mixed", "inadequate"}:
            errors.append("execution_quality.assessment must be adequate, mixed, or inadequate")
        if not _non_empty(execution.get("evidence_id")):
            errors.append("execution_quality.evidence_id must be a non-empty string")

    factors = payload.get("exogenous_factors")
    if not isinstance(factors, list) or not factors:
        errors.append("exogenous_factors must be a non-empty list")
        factors = []
    for index, factor in enumerate(factors):
        prefix = f"exogenous_factors[{index}]"
        if not isinstance(factor, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("factor_id", "description", "evidence_id"):
            if not _non_empty(factor.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if factor.get("effect") not in {"helped", "harmed", "neutral"}:
            errors.append(f"{prefix}.effect must be helped, harmed, or neutral")
        if not isinstance(factor.get("anticipated"), bool):
            errors.append(f"{prefix}.anticipated must be boolean")

    hypotheses = payload.get("attribution_hypotheses")
    if not isinstance(hypotheses, list):
        errors.append("attribution_hypotheses must be a list")
        hypotheses = []
    required_kinds = {"mission_thesis", "execution_quality", "luck"}
    seen_kinds = set()
    for index, hypothesis in enumerate(hypotheses):
        prefix = f"attribution_hypotheses[{index}]"
        if not isinstance(hypothesis, dict):
            errors.append(f"{prefix} must be an object")
            continue
        kind = hypothesis.get("kind")
        if kind not in required_kinds:
            errors.append(f"{prefix}.kind must be mission_thesis, execution_quality, or luck")
        elif kind in seen_kinds:
            errors.append(f"{prefix}.kind must be unique")
        else:
            seen_kinds.add(kind)
        for field in ("evidence_for", "evidence_against"):
            if not _non_empty(hypothesis.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if seen_kinds != required_kinds:
        errors.append("attribution_hypotheses must include mission_thesis, execution_quality, and luck")

    return {
        "valid": not errors,
        "errors": errors,
        "outcome_status": payload.get("outcome_status"),
        "thesis_status": payload.get("thesis_status"),
    }

def validate_failure_layer_diagnosis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Separate mission failure from planning, execution, environment, and measurement."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["failure layer diagnosis must be an object"]}
    for field in (
        "diagnosis_id",
        "mission_id",
        "failure_event",
        "failure_evidence_id",
        "pre_registered_forecast_id",
        "conclusion_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("failure_automatically_falsifies_mission") is not False:
        errors.append("failure_automatically_falsifies_mission must be false")

    required_layers = {
        "mission_selection",
        "planning",
        "execution",
        "environment",
        "measurement",
    }
    layers = payload.get("layer_assessments")
    if not isinstance(layers, list):
        errors.append("layer_assessments must be a list")
        layers = []
    seen_layers = set()
    assessments: Dict[str, str] = {}
    for index, layer in enumerate(layers):
        prefix = f"layer_assessments[{index}]"
        if not isinstance(layer, dict):
            errors.append(f"{prefix} must be an object")
            continue
        name = layer.get("layer")
        if name not in required_layers:
            errors.append(f"{prefix}.layer is not a recognized failure layer")
        elif name in seen_layers:
            errors.append(f"{prefix}.layer must be unique")
        else:
            seen_layers.add(name)
        assessment = layer.get("assessment")
        if assessment not in {"failed", "adequate", "unknown"}:
            errors.append(f"{prefix}.assessment must be failed, adequate, or unknown")
        elif name in required_layers:
            assessments[name] = assessment
        for field in ("expected_condition", "observed_condition", "evidence_id", "discriminator"):
            if not _non_empty(layer.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if seen_layers != required_layers:
        errors.append("layer_assessments must cover each required failure layer exactly once")

    conclusion = payload.get("conclusion")
    allowed_conclusions = {
        "mission_selection_failure",
        "planning_failure",
        "execution_failure",
        "environment_failure",
        "measurement_failure",
        "multiple_layers_unresolved",
        "underdetermined",
    }
    if conclusion not in allowed_conclusions:
        errors.append("conclusion is not a recognized failure-layer conclusion")
    single_layer_conclusions = {
        "mission_selection_failure": "mission_selection",
        "planning_failure": "planning",
        "execution_failure": "execution",
        "environment_failure": "environment",
        "measurement_failure": "measurement",
    }
    selected_layer = single_layer_conclusions.get(conclusion)
    if selected_layer and assessments.get(selected_layer) != "failed":
        errors.append("single-layer conclusion requires that layer to be assessed failed")
    if selected_layer and any(
        assessment == "failed" and layer != selected_layer
        for layer, assessment in assessments.items()
    ):
        errors.append("single-layer conclusion cannot ignore another failed layer")

    mission_falsified = payload.get("mission_thesis_falsified")
    if not isinstance(mission_falsified, bool):
        errors.append("mission_thesis_falsified must be boolean")
    elif mission_falsified:
        if conclusion != "mission_selection_failure":
            errors.append("mission thesis may be falsified only by mission_selection_failure")
        downstream = {"planning", "execution", "environment", "measurement"}
        if any(assessments.get(layer) != "adequate" for layer in downstream):
            errors.append("mission thesis falsification requires downstream layers to be adequate")

    return {
        "valid": not errors,
        "errors": errors,
        "conclusion": conclusion,
        "mission_thesis_falsified": mission_falsified,
    }

def validate_prestructured_failure_attribution(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Freeze attribution questions before outcomes and permit shared responsibility."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["prestructured failure attribution must be an object"]}
    for field in (
        "attribution_protocol_id",
        "mission_id",
        "pre_registered_forecast_id",
        "structure_frozen_at",
        "outcome_observed_at",
        "conclusion_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("structure_frozen_before_outcome") is not True:
        errors.append("structure_frozen_before_outcome must be true")
    frozen_at = payload.get("structure_frozen_at")
    observed_at = payload.get("outcome_observed_at")
    if _non_empty(frozen_at) and _non_empty(observed_at) and frozen_at >= observed_at:
        errors.append("structure_frozen_at must precede outcome_observed_at")
    if payload.get("downstream_execution_presumed_cause") is not False:
        errors.append("downstream_execution_presumed_cause must be false")
    if payload.get("upstream_selection_exempt") is not False:
        errors.append("upstream_selection_exempt must be false")

    required_layers = {
        "mission_selection",
        "planning",
        "execution",
        "environment",
        "measurement",
    }
    layers = payload.get("layer_attributions")
    if not isinstance(layers, list):
        errors.append("layer_attributions must be a list")
        layers = []
    seen_layers = set()
    contributions: Dict[str, str] = {}
    for index, layer in enumerate(layers):
        prefix = f"layer_attributions[{index}]"
        if not isinstance(layer, dict):
            errors.append(f"{prefix} must be an object")
            continue
        name = layer.get("layer")
        if name not in required_layers:
            errors.append(f"{prefix}.layer is not a recognized failure layer")
        elif name in seen_layers:
            errors.append(f"{prefix}.layer must be unique")
        else:
            seen_layers.add(name)
        contribution = layer.get("contribution")
        if contribution not in {"none", "contributing", "primary", "unknown"}:
            errors.append(f"{prefix}.contribution must be none, contributing, primary, or unknown")
        elif name in required_layers:
            contributions[name] = contribution
        for field in (
            "precommitted_question",
            "evidence_for_contribution",
            "evidence_against_contribution",
            "evidence_id",
        ):
            if not _non_empty(layer.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if seen_layers != required_layers:
        errors.append("layer_attributions must cover each required failure layer exactly once")

    mode = payload.get("responsibility_mode")
    if mode not in {"sole", "shared", "underdetermined"}:
        errors.append("responsibility_mode must be sole, shared, or underdetermined")
    causal_layers = [
        layer for layer, contribution in contributions.items()
        if contribution in {"contributing", "primary"}
    ]
    primary_layers = [
        layer for layer, contribution in contributions.items()
        if contribution == "primary"
    ]
    unknown_layers = [
        layer for layer, contribution in contributions.items()
        if contribution == "unknown"
    ]
    if mode == "sole" and (len(causal_layers) != 1 or len(primary_layers) != 1):
        errors.append("sole responsibility requires exactly one primary causal layer")
    if mode == "shared" and len(causal_layers) < 2:
        errors.append("shared responsibility requires at least two causal layers")
    if mode == "shared" and len(primary_layers) > 1:
        errors.append("shared responsibility permits at most one primary layer")
    if mode == "underdetermined" and not unknown_layers:
        errors.append("underdetermined responsibility requires at least one unknown layer")

    return {
        "valid": not errors,
        "errors": errors,
        "responsibility_mode": mode,
        "causal_layers": causal_layers,
    }

def validate_preselection_alternative_forecasts(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Constrain hindsight with alternative forecasts frozen before selection."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["preselection alternative forecasts must be an object"]}
    for field in (
        "forecast_set_id",
        "common_information_manifest_id",
        "frozen_at",
        "selection_at",
        "common_observation_window",
        "actual_outcome_evidence_id",
        "retrospective_comparison",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    frozen_at = payload.get("frozen_at")
    selection_at = payload.get("selection_at")
    if _non_empty(frozen_at) and _non_empty(selection_at) and frozen_at >= selection_at:
        errors.append("frozen_at must precede selection_at")
    if payload.get("forecasts_immutable_after_selection") is not True:
        errors.append("forecasts_immutable_after_selection must be true")
    if payload.get("counterfactual_outcomes_claimed_observed") is not False:
        errors.append("counterfactual_outcomes_claimed_observed must be false")

    forecasts = payload.get("candidate_forecasts")
    if not isinstance(forecasts, list) or len(forecasts) < 3:
        errors.append("candidate_forecasts must contain at least three candidates")
        forecasts = []
    candidate_ids = set()
    selected_ids = []
    for index, forecast in enumerate(forecasts):
        prefix = f"candidate_forecasts[{index}]"
        if not isinstance(forecast, dict):
            errors.append(f"{prefix} must be an object")
            continue
        candidate_id = forecast.get("mission_candidate_id")
        if not _non_empty(candidate_id):
            errors.append(f"{prefix}.mission_candidate_id must be a non-empty string")
        elif candidate_id in candidate_ids:
            errors.append(f"{prefix}.mission_candidate_id must be unique")
        else:
            candidate_ids.add(candidate_id)
        status = forecast.get("selection_status")
        if status not in {"selected", "not_selected"}:
            errors.append(f"{prefix}.selection_status must be selected or not_selected")
        elif status == "selected":
            selected_ids.append(candidate_id)
        for field in (
            "forecasted_outcome",
            "causal_prediction",
            "failure_signal",
            "evidence_basis_id",
        ):
            if not _non_empty(forecast.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        probability = forecast.get("probability_range")
        if not isinstance(probability, dict):
            errors.append(f"{prefix}.probability_range must be an object")
        else:
            low = probability.get("low")
            high = probability.get("high")
            if (
                not isinstance(low, (int, float))
                or isinstance(low, bool)
                or not isinstance(high, (int, float))
                or isinstance(high, bool)
                or not 0 <= low <= high <= 1
            ):
                errors.append(f"{prefix}.probability_range must satisfy 0 <= low <= high <= 1")
    if len(selected_ids) != 1:
        errors.append("candidate_forecasts must contain exactly one selected candidate")
    if forecasts and len(forecasts) - len(selected_ids) < 2:
        errors.append("candidate_forecasts must preserve at least two unselected alternatives")

    return {
        "valid": not errors,
        "errors": errors,
        "selected_mission_candidate_id": selected_ids[0] if len(selected_ids) == 1 else None,
        "alternative_count": max(0, len(forecasts) - len(selected_ids)),
    }

def validate_signal_trajectory_review(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Track moved, invariant, near-miss, and unexpectedly timed signals."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["signal trajectory review must be an object"]}
    for field in (
        "review_id",
        "mission_id",
        "forecast_set_id",
        "observation_window",
        "trajectory_summary",
        "calibration_update",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("binary_outcome_sufficient") is not False:
        errors.append("binary_outcome_sufficient must be false")

    signals = payload.get("signal_trajectories")
    if not isinstance(signals, list) or len(signals) < 3:
        errors.append("signal_trajectories must contain at least three signals")
        signals = []
    signal_ids = set()
    movement_statuses = set()
    unexpected_timing_count = 0
    for index, signal in enumerate(signals):
        prefix = f"signal_trajectories[{index}]"
        if not isinstance(signal, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in (
            "signal_id",
            "forecasted_direction",
            "forecasted_window",
            "forecasted_threshold",
            "observed_value",
            "observed_at",
            "evidence_id",
        ):
            if not _non_empty(signal.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        signal_id = signal.get("signal_id")
        if _non_empty(signal_id):
            if signal_id in signal_ids:
                errors.append(f"{prefix}.signal_id must be unique")
            signal_ids.add(signal_id)
        movement = signal.get("movement_status")
        if movement not in {"moved", "invariant"}:
            errors.append(f"{prefix}.movement_status must be moved or invariant")
        else:
            movement_statuses.add(movement)
        timing = signal.get("timing_status")
        if timing not in {"expected", "early", "late", "unexpected", "not_applicable"}:
            errors.append(f"{prefix}.timing_status is not recognized")
        elif timing in {"early", "late", "unexpected"}:
            unexpected_timing_count += 1
        distance = signal.get("distance_to_threshold")
        if (
            not isinstance(distance, (int, float))
            or isinstance(distance, bool)
            or distance < 0
        ):
            errors.append(f"{prefix}.distance_to_threshold must be a non-negative number")
        if not isinstance(signal.get("threshold_crossed"), bool):
            errors.append(f"{prefix}.threshold_crossed must be boolean")
    if movement_statuses != {"moved", "invariant"}:
        errors.append("signal_trajectories must include both moved and invariant signals")
    if unexpected_timing_count == 0:
        errors.append("signal_trajectories must include at least one unexpectedly timed signal")

    return {
        "valid": not errors,
        "errors": errors,
        "moved_count": sum(
            1 for signal in signals
            if isinstance(signal, dict) and signal.get("movement_status") == "moved"
        ),
        "invariant_count": sum(
            1 for signal in signals
            if isinstance(signal, dict) and signal.get("movement_status") == "invariant"
        ),
        "unexpected_timing_count": unexpected_timing_count,
    }

def validate_consequence_review_cadence(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Use consequence-specific review schedules with early harm observation."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["consequence review cadence must be an object"]}
    for field in ("cadence_id", "mission_id", "schedule_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("uniform_cadence") is not False:
        errors.append("uniform_cadence must be false")

    required_types = {"benefit", "harm", "sustainability", "option_preservation"}
    schedules = payload.get("consequence_schedules")
    if not isinstance(schedules, list):
        errors.append("consequence_schedules must be a list")
        schedules = []
    seen_types = set()
    schedule_values: Dict[str, tuple] = {}
    for index, schedule in enumerate(schedules):
        prefix = f"consequence_schedules[{index}]"
        if not isinstance(schedule, dict):
            errors.append(f"{prefix} must be an object")
            continue
        consequence_type = schedule.get("consequence_type")
        if consequence_type not in required_types:
            errors.append(f"{prefix}.consequence_type is not recognized")
        elif consequence_type in seen_types:
            errors.append(f"{prefix}.consequence_type must be unique")
        else:
            seen_types.add(consequence_type)
        latency = schedule.get("expected_latency")
        if latency not in {"immediate", "early", "lagging", "long_horizon"}:
            errors.append(f"{prefix}.expected_latency is not recognized")
        first_review = schedule.get("first_review_after_days")
        interval = schedule.get("recurring_interval_days")
        if (
            not isinstance(first_review, int)
            or isinstance(first_review, bool)
            or first_review < 0
        ):
            errors.append(f"{prefix}.first_review_after_days must be a non-negative integer")
        if not isinstance(interval, int) or isinstance(interval, bool) or interval <= 0:
            errors.append(f"{prefix}.recurring_interval_days must be a positive integer")
        if consequence_type in required_types and isinstance(first_review, int) and isinstance(interval, int):
            schedule_values[consequence_type] = (first_review, interval)
        for field in ("wake_trigger", "evidence_source_id", "latency_rationale"):
            if not _non_empty(schedule.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if seen_types != required_types:
        errors.append("consequence_schedules must cover each required consequence type exactly once")
    if len(set(schedule_values.values())) < 2:
        errors.append("consequence types must not all share one review cadence")
    harm = schedule_values.get("harm")
    benefit = schedule_values.get("benefit")
    if harm and benefit and (harm[0] > benefit[0] or harm[1] > benefit[1]):
        errors.append("harm must be reviewed no later or less frequently than benefit")

    return {
        "valid": not errors,
        "errors": errors,
        "schedule_by_type": schedule_values,
    }

def validate_underlying_condition_review(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Retire a goal when the beneficiary condition that justified it disappears."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["underlying condition review must be an object"]}
    for field in (
        "review_id",
        "mission_id",
        "underlying_condition_id",
        "original_condition",
        "current_condition_observation",
        "condition_evidence_id",
        "decision_rationale",
        "reopen_trigger",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if not isinstance(payload.get("mission_was_successful"), bool):
        errors.append("mission_was_successful must be boolean")
    if payload.get("goal_preservation_is_default") is not False:
        errors.append("goal_preservation_is_default must be false")
    status = payload.get("condition_status")
    if status not in {"persists", "changed", "resolved", "disappeared"}:
        errors.append("condition_status must be persists, changed, resolved, or disappeared")
    decision = payload.get("decision")
    if decision not in {"continue", "revise", "retire"}:
        errors.append("decision must be continue, revise, or retire")

    retirement_fields = (
        "delegations_revoked",
        "resources_stopped",
        "downstream_notified",
        "lineage_preserved",
    )
    for field in retirement_fields:
        if not isinstance(payload.get(field), bool):
            errors.append(f"{field} must be boolean")
    if status in {"resolved", "disappeared"}:
        if decision != "retire":
            errors.append("resolved or disappeared underlying condition requires retirement")
        for field in retirement_fields:
            if payload.get(field) is not True:
                errors.append(f"{field} must be true when retiring a completed purpose")
    if status == "persists" and decision == "revise":
        errors.append("persisting unchanged condition does not by itself justify revision")
    if decision == "retire" and payload.get("lineage_preserved") is not True:
        errors.append("retirement must preserve mission lineage")

    return {
        "valid": not errors,
        "errors": errors,
        "condition_status": status,
        "decision": decision,
    }

def validate_outcome_cause_uncertainty(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Preserve uncertainty across value, mechanism, timing, and luck."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["outcome cause uncertainty must be an object"]}
    for field in (
        "uncertainty_record_id",
        "mission_id",
        "outcome_evidence_id",
        "learned_preference_scope",
        "next_discriminating_observation",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("single_cause_certainty") is not False:
        errors.append("single_cause_certainty must be false")
    if payload.get("exploration_budget_preserved") is not True:
        errors.append("exploration_budget_preserved must be true")

    required_causes = {"value_fit", "mechanism", "timing", "luck"}
    causes = payload.get("cause_assessments")
    if not isinstance(causes, list):
        errors.append("cause_assessments must be a list")
        causes = []
    seen_causes = set()
    live_causes = []
    for index, cause in enumerate(causes):
        prefix = f"cause_assessments[{index}]"
        if not isinstance(cause, dict):
            errors.append(f"{prefix} must be an object")
            continue
        kind = cause.get("cause")
        if kind not in required_causes:
            errors.append(f"{prefix}.cause is not recognized")
        elif kind in seen_causes:
            errors.append(f"{prefix}.cause must be unique")
        else:
            seen_causes.add(kind)
        status = cause.get("status")
        if status not in {"supported", "plausible", "challenged", "unknown"}:
            errors.append(f"{prefix}.status is not recognized")
        elif status != "challenged":
            live_causes.append(kind)
        identification = cause.get("causal_identification")
        if identification not in {"none", "weak", "moderate", "strong"}:
            errors.append(f"{prefix}.causal_identification is not recognized")
        for field in ("evidence_for", "evidence_against", "uncertainty"):
            if not _non_empty(cause.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        confidence = cause.get("confidence_range")
        if not isinstance(confidence, dict):
            errors.append(f"{prefix}.confidence_range must be an object")
        else:
            low = confidence.get("low")
            high = confidence.get("high")
            if (
                not isinstance(low, (int, float))
                or isinstance(low, bool)
                or not isinstance(high, (int, float))
                or isinstance(high, bool)
                or not 0 <= low <= high <= 1
            ):
                errors.append(f"{prefix}.confidence_range must satisfy 0 <= low <= high <= 1")
    if seen_causes != required_causes:
        errors.append("cause_assessments must cover value_fit, mechanism, timing, and luck exactly once")
    if len(live_causes) < 2:
        errors.append("at least two causal explanations must remain live")

    return {
        "valid": not errors,
        "errors": errors,
        "live_causes": live_causes,
    }

def validate_evidence_weighted_model_update(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Bound update strength by evidence relevance and causal identification."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["evidence weighted model update must be an object"]}
    for field in (
        "update_id",
        "source_evidence_id",
        "target_claim_id",
        "prior_belief",
        "proposed_belief",
        "relevance_rationale",
        "causal_identification_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("target_model") not in {"world", "value", "mechanism"}:
        errors.append("target_model must be world, value, or mechanism")
    if payload.get("emotional_magnitude_drives_update") is not False:
        errors.append("emotional_magnitude_drives_update must be false")
    if payload.get("financial_magnitude_drives_update") is not False:
        errors.append("financial_magnitude_drives_update must be false")

    relevance = payload.get("evidence_relevance")
    identification = payload.get("causal_identification")
    strength = payload.get("update_strength")
    relevance_levels = {"none": 0, "indirect": 1, "direct": 3}
    identification_levels = {"none": 0, "weak": 1, "moderate": 2, "strong": 3}
    strength_levels = {"none": 0, "weak": 1, "moderate": 2, "strong": 3}
    if relevance not in relevance_levels:
        errors.append("evidence_relevance must be none, indirect, or direct")
    if identification not in identification_levels:
        errors.append("causal_identification must be none, weak, moderate, or strong")
    if strength not in strength_levels:
        errors.append("update_strength must be none, weak, moderate, or strong")
    maximum_strength = None
    if relevance in relevance_levels and identification in identification_levels:
        maximum_strength = min(relevance_levels[relevance], identification_levels[identification])
        if strength in strength_levels and strength_levels[strength] > maximum_strength:
            errors.append("update_strength exceeds evidence relevance or causal identification")
    if strength == "none" and payload.get("proposed_belief") != payload.get("prior_belief"):
        errors.append("none update_strength cannot change the belief")
    if not isinstance(payload.get("outcome_emotional_salience"), (int, float)):
        errors.append("outcome_emotional_salience must be numeric")
    if not isinstance(payload.get("outcome_financial_magnitude"), (int, float)):
        errors.append("outcome_financial_magnitude must be numeric")

    return {
        "valid": not errors,
        "errors": errors,
        "maximum_update_level": maximum_strength,
        "update_strength": strength,
    }

def validate_learning_thesis_gate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Integrate separate model revision, counterfactual uncertainty, and retirement."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["learning thesis gate must be an object"]}
    for field in (
        "learning_cycle_id",
        "mission_id",
        "causal_outcome_attribution_id",
        "failure_attribution_id",
        "alternative_forecast_set_id",
        "signal_trajectory_review_id",
        "consequence_cadence_id",
        "underlying_condition_review_id",
        "cause_uncertainty_id",
        "learning_decision_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("world_value_mechanism_collapsed") is not False:
        errors.append("world_value_mechanism_collapsed must be false")
    if payload.get("counterfactual_uncertainty_preserved") is not True:
        errors.append("counterfactual_uncertainty_preserved must be true")

    updates = payload.get("model_updates")
    if not isinstance(updates, list):
        errors.append("model_updates must be a list")
        updates = []
    required_models = {"world", "value", "mechanism"}
    seen_models = set()
    update_ids = set()
    for index, update in enumerate(updates):
        prefix = f"model_updates[{index}]"
        if not isinstance(update, dict):
            errors.append(f"{prefix} must be an object")
            continue
        model = update.get("model")
        if model not in required_models:
            errors.append(f"{prefix}.model must be world, value, or mechanism")
        elif model in seen_models:
            errors.append(f"{prefix}.model must be unique")
        else:
            seen_models.add(model)
        update_id = update.get("update_id")
        if not _non_empty(update_id):
            errors.append(f"{prefix}.update_id must be a non-empty string")
        elif update_id in update_ids:
            errors.append(f"{prefix}.update_id must be unique")
        else:
            update_ids.add(update_id)
    if seen_models != required_models:
        errors.append("model_updates must contain separate world, value, and mechanism updates")

    completed = payload.get("underlying_purpose_completed")
    retired = payload.get("completed_purpose_retired")
    if not isinstance(completed, bool):
        errors.append("underlying_purpose_completed must be boolean")
    if not isinstance(retired, bool):
        errors.append("completed_purpose_retired must be boolean")
    decision = payload.get("learning_decision")
    if decision not in {"continue", "revise", "retire"}:
        errors.append("learning_decision must be continue, revise, or retire")
    if completed is True:
        if retired is not True:
            errors.append("completed underlying purpose must be retired")
        if decision != "retire":
            errors.append("completed underlying purpose requires retire decision")
    if retired is True and decision != "retire":
        errors.append("completed_purpose_retired requires retire decision")

    return {
        "valid": not errors,
        "errors": errors,
        "learning_decision": decision,
        "updated_models": sorted(seen_models),
    }

def validate_mission_meaning_boundary_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Keep mission contracts about purpose and boundaries, not execution shape."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["mission meaning boundary contract must be an object"]}
    for field in (
        "contract_id",
        "mission_id",
        "contract_version",
        "situation",
        "mission_meaning",
        "beneficiary_condition",
        "desired_condition",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("planner_owns_strategy") is not True:
        errors.append("planner_owns_strategy must be true")
    if payload.get("execution_shape_locked") is not False:
        errors.append("execution_shape_locked must be false")

    boundaries = payload.get("scope_boundaries")
    if not isinstance(boundaries, list) or len(boundaries) < 2:
        errors.append("scope_boundaries must contain at least two boundaries")
        boundaries = []
    boundary_ids = set()
    for index, boundary in enumerate(boundaries):
        prefix = f"scope_boundaries[{index}]"
        if not isinstance(boundary, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("boundary_id", "description", "rationale", "return_trigger"):
            if not _non_empty(boundary.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        boundary_id = boundary.get("boundary_id")
        if _non_empty(boundary_id):
            if boundary_id in boundary_ids:
                errors.append(f"{prefix}.boundary_id must be unique")
            boundary_ids.add(boundary_id)

    freedoms = payload.get("planner_freedoms")
    if not isinstance(freedoms, list) or len(freedoms) < 2 or not all(_non_empty(item) for item in freedoms):
        errors.append("planner_freedoms must contain at least two non-empty freedoms")

    for field in ("detailed_tasks", "prescribed_tools", "implementation_sequence"):
        value = payload.get(field)
        if not isinstance(value, list):
            errors.append(f"{field} must be a list")
        elif value:
            errors.append(f"{field} must be empty because execution shape belongs to the planner")

    return {
        "valid": not errors,
        "errors": errors,
        "boundary_count": len(boundaries),
        "planner_freedom_count": len(freedoms) if isinstance(freedoms, list) else 0,
    }

def validate_mission_tradeoff_interface(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Give planners enough causal and consequence information for tradeoffs."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["mission tradeoff interface must be an object"]}
    for field in (
        "interface_id",
        "mission_contract_id",
        "causal_thesis",
        "causal_thesis_evidence_id",
        "tradeoff_rule",
        "return_condition",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("planner_must_reconstruct_upstream_reasoning") is not False:
        errors.append("planner_must_reconstruct_upstream_reasoning must be false")

    mechanisms = payload.get("essential_mechanisms")
    if not isinstance(mechanisms, list) or not mechanisms or not all(_non_empty(item) for item in mechanisms):
        errors.append("essential_mechanisms must be a non-empty list of strings")
    assumptions = payload.get("causal_assumptions")
    if not isinstance(assumptions, list) or not assumptions or not all(_non_empty(item) for item in assumptions):
        errors.append("causal_assumptions must be a non-empty list of strings")

    signals = payload.get("consequence_signals")
    if not isinstance(signals, list):
        errors.append("consequence_signals must be a list")
        signals = []
    required_kinds = {"success", "harm"}
    seen_kinds = set()
    signal_ids = set()
    for index, signal in enumerate(signals):
        prefix = f"consequence_signals[{index}]"
        if not isinstance(signal, dict):
            errors.append(f"{prefix} must be an object")
            continue
        kind = signal.get("kind")
        if kind not in required_kinds:
            errors.append(f"{prefix}.kind must be success or harm")
        else:
            seen_kinds.add(kind)
        signal_id = signal.get("signal_id")
        if not _non_empty(signal_id):
            errors.append(f"{prefix}.signal_id must be a non-empty string")
        elif signal_id in signal_ids:
            errors.append(f"{prefix}.signal_id must be unique")
        else:
            signal_ids.add(signal_id)
        for field in (
            "description",
            "threshold",
            "observation_window",
            "evidence_source_id",
            "planner_response",
        ):
            if not _non_empty(signal.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if seen_kinds != required_kinds:
        errors.append("consequence_signals must include both success and harm")

    return {
        "valid": not errors,
        "errors": errors,
        "signal_kinds": sorted(seen_kinds),
    }

