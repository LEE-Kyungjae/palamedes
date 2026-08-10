from __future__ import annotations

from typing import Any, Dict, List
from ._01_kinds_value import _non_empty


def validate_beneficiary_external_condition_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Anchor planner success in a represented beneficiary's changed external condition."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["beneficiary external condition contract must be an object"]}
    for field in (
        "condition_contract_id",
        "planner_contract_id",
        "situation_evidence_id",
        "meaning_evidence_id",
        "success_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    beneficiary = payload.get("beneficiary")
    if not isinstance(beneficiary, dict):
        errors.append("beneficiary must be an object")
        beneficiary = {}
    for field in (
        "beneficiary_id",
        "population",
        "current_condition",
        "representation_evidence_id",
        "recourse_channel",
    ):
        if not _non_empty(beneficiary.get(field)):
            errors.append(f"beneficiary.{field} must be a non-empty string")
    if beneficiary.get("directly_affected") is not True:
        errors.append("beneficiary.directly_affected must be true")
    if beneficiary.get("internal_delivery_team") is not False:
        errors.append("beneficiary.internal_delivery_team must be false")

    desired = payload.get("desired_condition")
    if not isinstance(desired, dict):
        errors.append("desired_condition must be an object")
        desired = {}
    for field in (
        "external_condition",
        "observable_difference",
        "observation_window",
        "beneficiary_verification_method",
        "evidence_source_id",
    ):
        if not _non_empty(desired.get(field)):
            errors.append(f"desired_condition.{field} must be a non-empty string")
    if desired.get("implementation_form_locked") is not False:
        errors.append("desired_condition.implementation_form_locked must be false")
    if desired.get("technical_output_counts_as_success") is not False:
        errors.append("desired_condition.technical_output_counts_as_success must be false")
    if payload.get("success_requires_observed_beneficiary_change") is not True:
        errors.append("success_requires_observed_beneficiary_change must be true")
    technical_outputs = payload.get("technical_outputs")
    if not isinstance(technical_outputs, list):
        errors.append("technical_outputs must be a list")
        technical_outputs = []
    if not all(_non_empty(item) for item in technical_outputs):
        errors.append("technical_outputs entries must be non-empty strings")
    return {
        "valid": not errors,
        "errors": errors,
        "beneficiary_id": beneficiary.get("beneficiary_id", ""),
        "technical_output_count": len(technical_outputs),
    }

def validate_essential_mechanism_open_form_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Bind planners to causal mechanisms while leaving implementation forms negotiable."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["essential mechanism open form contract must be an object"]}
    for field in (
        "causal_contract_id",
        "planner_contract_id",
        "desired_condition_contract_id",
        "causal_thesis",
        "causal_evidence_id",
        "planner_freedom_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("implementation_form_mistaken_for_mechanism") is not False:
        errors.append("implementation_form_mistaken_for_mechanism must be false")
    if payload.get("planner_may_substitute_negotiable_forms") is not True:
        errors.append("planner_may_substitute_negotiable_forms must be true")

    mechanisms = payload.get("essential_mechanisms")
    if not isinstance(mechanisms, list) or not mechanisms:
        errors.append("essential_mechanisms must be a non-empty list")
        mechanisms = []
    mechanism_ids = set()
    for index, mechanism in enumerate(mechanisms):
        prefix = f"essential_mechanisms[{index}]"
        if not isinstance(mechanism, dict):
            errors.append(f"{prefix} must be an object")
            continue
        mechanism_id = mechanism.get("mechanism_id")
        if not _non_empty(mechanism_id):
            errors.append(f"{prefix}.mechanism_id must be a non-empty string")
        elif mechanism_id in mechanism_ids:
            errors.append(f"{prefix}.mechanism_id must be unique")
        mechanism_ids.add(mechanism_id)
        for field in (
            "mechanism",
            "predicted_effect",
            "supporting_evidence_id",
            "falsification_condition",
        ):
            if not _non_empty(mechanism.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if mechanism.get("removal_breaks_causal_thesis") is not True:
            errors.append(f"{prefix}.removal_breaks_causal_thesis must be true")

    forms = payload.get("negotiable_forms")
    if not isinstance(forms, list) or len(forms) < 2:
        errors.append("negotiable_forms must contain at least two forms")
        forms = []
    form_ids = set()
    for index, form in enumerate(forms):
        prefix = f"negotiable_forms[{index}]"
        if not isinstance(form, dict):
            errors.append(f"{prefix} must be an object")
            continue
        form_id = form.get("form_id")
        if not _non_empty(form_id):
            errors.append(f"{prefix}.form_id must be a non-empty string")
        elif form_id in form_ids:
            errors.append(f"{prefix}.form_id must be unique")
        form_ids.add(form_id)
        for field in ("form", "substitution_rule"):
            if not _non_empty(form.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        preserved = form.get("preserves_mechanism_ids")
        if (
            not isinstance(preserved, list)
            or set(preserved) != mechanism_ids
            or len(preserved) != len(mechanism_ids)
        ):
            errors.append(f"{prefix}.preserves_mechanism_ids must cover every essential mechanism")
    prescribed = payload.get("prescribed_form_ids")
    if not isinstance(prescribed, list):
        errors.append("prescribed_form_ids must be a list")
    elif prescribed:
        errors.append("prescribed_form_ids must be empty")
    return {
        "valid": not errors,
        "errors": errors,
        "essential_mechanism_ids": sorted(mechanism_ids),
        "negotiable_form_ids": sorted(form_ids),
    }

def validate_reopenable_non_goal_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Protect attention with reasoned non-goals that can reopen on evidence."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["reopenable non-goal contract must be an object"]}
    for field in ("non_goal_contract_id", "planner_contract_id", "review_protocol"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("blanket_exclusion_allowed") is not False:
        errors.append("blanket_exclusion_allowed must be false")
    non_goals = payload.get("non_goals")
    if not isinstance(non_goals, list) or not non_goals:
        errors.append("non_goals must be a non-empty list")
        non_goals = []
    non_goal_ids = set()
    reopened_ids = []
    for index, non_goal in enumerate(non_goals):
        prefix = f"non_goals[{index}]"
        if not isinstance(non_goal, dict):
            errors.append(f"{prefix} must be an object")
            continue
        non_goal_id = non_goal.get("non_goal_id")
        if not _non_empty(non_goal_id):
            errors.append(f"{prefix}.non_goal_id must be a non-empty string")
        elif non_goal_id in non_goal_ids:
            errors.append(f"{prefix}.non_goal_id must be unique")
        non_goal_ids.add(non_goal_id)
        for field in (
            "excluded_scope",
            "current_exclusion_reason",
            "attention_resource_protected",
            "reason_evidence_id",
            "reopening_signal",
            "reopening_threshold",
            "review_authority_id",
            "reopening_action",
        ):
            if not _non_empty(non_goal.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if non_goal.get("permanent_exclusion") is not False:
            errors.append(f"{prefix}.permanent_exclusion must be false")
        status = non_goal.get("status")
        if status not in {"excluded", "reopened"}:
            errors.append(f"{prefix}.status must be excluded or reopened")
        elif status == "reopened":
            reopened_ids.append(non_goal_id)
            for field in ("reopening_evidence_id", "reopened_at"):
                if not _non_empty(non_goal.get(field)):
                    errors.append(f"{prefix}.{field} is required when reopened")
        elif non_goal.get("reopening_evidence_id") not in ("", None):
            errors.append(f"{prefix}.reopening_evidence_id must be empty while excluded")
    return {
        "valid": not errors,
        "errors": errors,
        "non_goal_ids": sorted(non_goal_ids),
        "reopened_non_goal_ids": sorted(reopened_ids),
    }

def validate_timed_success_harm_signals(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require baselined success ranges and earlier review of anticipatory harms."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["timed success harm signals must be an object"]}
    for field in ("signal_contract_id", "planner_contract_id", "schedule_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    successes = payload.get("success_signals")
    if not isinstance(successes, list) or not successes:
        errors.append("success_signals must be a non-empty list")
        successes = []
    success_ids = set()
    success_starts = []
    for index, signal in enumerate(successes):
        prefix = f"success_signals[{index}]"
        if not isinstance(signal, dict):
            errors.append(f"{prefix} must be an object")
            continue
        signal_id = signal.get("signal_id")
        if not _non_empty(signal_id):
            errors.append(f"{prefix}.signal_id must be a non-empty string")
        elif signal_id in success_ids:
            errors.append(f"{prefix}.signal_id must be unique")
        success_ids.add(signal_id)
        for field in ("description", "unit", "baseline_evidence_id", "evidence_source_id"):
            if not _non_empty(signal.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        numbers = {}
        for field in ("baseline_value", "target_range_min", "target_range_max"):
            value = signal.get(field)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                errors.append(f"{prefix}.{field} must be a number")
                value = 0
            numbers[field] = value
        if numbers["target_range_min"] > numbers["target_range_max"]:
            errors.append(f"{prefix} target range minimum cannot exceed maximum")
        direction = signal.get("improvement_direction")
        if direction == "increase":
            if numbers["target_range_min"] <= numbers["baseline_value"]:
                errors.append(f"{prefix} increasing target range must exceed baseline")
        elif direction == "decrease":
            if numbers["target_range_max"] >= numbers["baseline_value"]:
                errors.append(f"{prefix} decreasing target range must be below baseline")
        else:
            errors.append(f"{prefix}.improvement_direction must be increase or decrease")
        start = signal.get("observation_start_day")
        end = signal.get("observation_end_day")
        if not isinstance(start, int) or isinstance(start, bool) or start < 0:
            errors.append(f"{prefix}.observation_start_day must be a non-negative integer")
        if not isinstance(end, int) or isinstance(end, bool) or end <= 0:
            errors.append(f"{prefix}.observation_end_day must be a positive integer")
        if isinstance(start, int) and not isinstance(start, bool) and isinstance(end, int):
            if end <= start:
                errors.append(f"{prefix}.observation_end_day must follow observation_start_day")
            else:
                success_starts.append(start)

    harms = payload.get("harm_signals")
    if not isinstance(harms, list) or not harms:
        errors.append("harm_signals must be a non-empty list")
        harms = []
    harm_ids = set()
    anticipatory_harm_count = 0
    earliest_success = min(success_starts) if success_starts else None
    for index, signal in enumerate(harms):
        prefix = f"harm_signals[{index}]"
        if not isinstance(signal, dict):
            errors.append(f"{prefix} must be an object")
            continue
        signal_id = signal.get("signal_id")
        if not _non_empty(signal_id):
            errors.append(f"{prefix}.signal_id must be a non-empty string")
        elif signal_id in harm_ids:
            errors.append(f"{prefix}.signal_id must be unique")
        harm_ids.add(signal_id)
        for field in ("description", "threshold", "evidence_source_id", "response"):
            if not _non_empty(signal.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        review_day = signal.get("first_review_day")
        if not isinstance(review_day, int) or isinstance(review_day, bool) or review_day < 0:
            errors.append(f"{prefix}.first_review_day must be a non-negative integer")
        precedes = signal.get("damage_can_precede_benefit")
        if not isinstance(precedes, bool):
            errors.append(f"{prefix}.damage_can_precede_benefit must be boolean")
        elif precedes:
            anticipatory_harm_count += 1
            if (
                earliest_success is not None
                and isinstance(review_day, int)
                and not isinstance(review_day, bool)
                and review_day >= earliest_success
            ):
                errors.append(f"{prefix} must be reviewed before the earliest success window")
    return {
        "valid": not errors,
        "errors": errors,
        "earliest_success_day": earliest_success,
        "anticipatory_harm_count": anticipatory_harm_count,
    }

def validate_disconfirmation_layer_attribution(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Attribute disconfirmation across mission, planner, implementation, measurement, and timing."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["disconfirmation layer attribution must be an object"]}
    for field in (
        "attribution_id",
        "mission_id",
        "signal_contract_id",
        "disconfirming_observation",
        "observation_evidence_id",
        "attribution_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("outcome_shortfall_automatically_falsifies_mission") is not False:
        errors.append("outcome_shortfall_automatically_falsifies_mission must be false")
    required_layers = {"mission", "planner", "implementation", "measurement", "timing"}
    assessments = payload.get("layer_assessments")
    if not isinstance(assessments, list):
        errors.append("layer_assessments must be a list")
        assessments = []
    seen = set()
    statuses = {}
    for index, assessment in enumerate(assessments):
        prefix = f"layer_assessments[{index}]"
        if not isinstance(assessment, dict):
            errors.append(f"{prefix} must be an object")
            continue
        layer = assessment.get("layer")
        if layer not in required_layers:
            errors.append(f"{prefix}.layer is not recognized")
        elif layer in seen:
            errors.append(f"{prefix}.layer must be unique")
        seen.add(layer)
        status = assessment.get("status")
        if status not in {"supported", "ruled_out", "unresolved"}:
            errors.append(f"{prefix}.status must be supported, ruled_out, or unresolved")
        elif layer in required_layers:
            statuses[layer] = status
        for field in (
            "failure_hypothesis",
            "discriminating_test",
            "evidence_id",
            "next_action",
        ):
            if not _non_empty(assessment.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if seen != required_layers:
        errors.append("layer_assessments must cover all five disconfirmation layers exactly once")

    supported = sorted(layer for layer, status in statuses.items() if status == "supported")
    expected_primary = supported[0] if len(supported) == 1 else "underdetermined"
    if payload.get("primary_attribution") != expected_primary:
        errors.append("primary_attribution must follow the supported layer assessments")
    mission_disconfirmed = payload.get("mission_disconfirmed")
    expected_disconfirmed = (
        statuses.get("mission") == "supported"
        and all(statuses.get(layer) == "ruled_out" for layer in required_layers - {"mission"})
    )
    if mission_disconfirmed is not expected_disconfirmed:
        errors.append("mission_disconfirmed requires mission support and every downstream layer ruled out")
    return {
        "valid": not errors,
        "errors": errors,
        "primary_attribution": expected_primary,
        "mission_disconfirmed": expected_disconfirmed,
        "unresolved_layers": sorted(
            layer for layer, status in statuses.items() if status == "unresolved"
        ),
    }

def validate_planner_authority_return_contract(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Grant planner freedom until evidence or scope change returns control."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["planner authority return contract must be an object"]}
    for field in (
        "authority_clause_id",
        "planner_contract_id",
        "palamedes_authority_id",
        "return_protocol",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    freedoms = payload.get("delegated_freedoms")
    if (
        not isinstance(freedoms, list)
        or len(freedoms) < 2
        or not all(_non_empty(item) for item in freedoms)
        or len(freedoms) != len(set(freedoms))
    ):
        errors.append("delegated_freedoms must contain at least two unique freedoms")
        freedoms = []
    forbidden = payload.get("forbidden_actions")
    if (
        not isinstance(forbidden, list)
        or not forbidden
        or not all(_non_empty(item) for item in forbidden)
        or len(forbidden) != len(set(forbidden))
    ):
        errors.append("forbidden_actions must be a non-empty unique string list")
        forbidden = []
    if set(freedoms) & set(forbidden):
        errors.append("delegated_freedoms and forbidden_actions cannot overlap")
    if payload.get("return_control_is_automatic") is not True:
        errors.append("return_control_is_automatic must be true")

    triggers = payload.get("return_triggers")
    if not isinstance(triggers, list):
        errors.append("return_triggers must be a list")
        triggers = []
    required_types = {"evidence_change", "scope_change"}
    seen_types = set()
    triggered_ids = []
    for index, trigger in enumerate(triggers):
        prefix = f"return_triggers[{index}]"
        if not isinstance(trigger, dict):
            errors.append(f"{prefix} must be an object")
            continue
        trigger_type = trigger.get("trigger_type")
        if trigger_type not in required_types:
            errors.append(f"{prefix}.trigger_type is not recognized")
        elif trigger_type in seen_types:
            errors.append(f"{prefix}.trigger_type must be unique")
        seen_types.add(trigger_type)
        for field in ("trigger_id", "condition", "threshold", "return_action"):
            if not _non_empty(trigger.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        triggered = trigger.get("triggered")
        if not isinstance(triggered, bool):
            errors.append(f"{prefix}.triggered must be boolean")
        elif triggered:
            triggered_ids.append(trigger.get("trigger_id"))
            for field in ("observed_change", "evidence_id", "observed_at"):
                if not _non_empty(trigger.get(field)):
                    errors.append(f"{prefix}.{field} is required when triggered")
        elif trigger.get("evidence_id") not in ("", None):
            errors.append(f"{prefix}.evidence_id must be empty when not triggered")
    if seen_types != required_types:
        errors.append("return_triggers must cover evidence_change and scope_change exactly once")
    expected_control = "palamedes_review" if triggered_ids else "planner"
    if payload.get("current_control") != expected_control:
        errors.append("current_control must reflect whether a return trigger fired")
    if triggered_ids and payload.get("planner_continues_unilaterally") is not False:
        errors.append("planner_continues_unilaterally must be false after a return trigger")
    return {
        "valid": not errors,
        "errors": errors,
        "current_control": expected_control,
        "triggered_return_ids": triggered_ids,
    }

def validate_addressable_contract_lineage(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Keep contract claims concise while linking addressable full lineage."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["addressable contract lineage must be an object"]}
    for field in ("lineage_index_id", "planner_contract_id", "lineage_store_id"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    max_chars = payload.get("claim_max_characters")
    if not isinstance(max_chars, int) or isinstance(max_chars, bool) or max_chars < 40:
        errors.append("claim_max_characters must be an integer of at least 40")
        max_chars = 0
    if payload.get("full_lineage_embedded") is not False:
        errors.append("full_lineage_embedded must be false")

    required_kinds = {"signal", "interpretation", "alternative", "constitution_trace"}
    records = payload.get("lineage_records")
    if not isinstance(records, list):
        errors.append("lineage_records must be a list")
        records = []
    record_ids = set()
    record_kinds = {}
    for index, record in enumerate(records):
        prefix = f"lineage_records[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix} must be an object")
            continue
        record_id = record.get("record_id")
        if not _non_empty(record_id):
            errors.append(f"{prefix}.record_id must be a non-empty string")
        elif record_id in record_ids:
            errors.append(f"{prefix}.record_id must be unique")
        record_ids.add(record_id)
        kind = record.get("kind")
        if kind not in required_kinds:
            errors.append(f"{prefix}.kind is not recognized")
        else:
            record_kinds[record_id] = kind
        for field in ("address", "content_hash"):
            if not _non_empty(record.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if record.get("immutable") is not True:
            errors.append(f"{prefix}.immutable must be true")
    if set(record_kinds.values()) != required_kinds:
        errors.append("lineage_records must include all four lineage kinds")

    claims = payload.get("concise_claims")
    if not isinstance(claims, list) or not claims:
        errors.append("concise_claims must be a non-empty list")
        claims = []
    claim_ids = set()
    for index, claim in enumerate(claims):
        prefix = f"concise_claims[{index}]"
        if not isinstance(claim, dict):
            errors.append(f"{prefix} must be an object")
            continue
        claim_id = claim.get("claim_id")
        if not _non_empty(claim_id):
            errors.append(f"{prefix}.claim_id must be a non-empty string")
        elif claim_id in claim_ids:
            errors.append(f"{prefix}.claim_id must be unique")
        claim_ids.add(claim_id)
        text = claim.get("claim")
        if not _non_empty(text):
            errors.append(f"{prefix}.claim must be a non-empty string")
        elif max_chars and len(text) > max_chars:
            errors.append(f"{prefix}.claim exceeds claim_max_characters")
        refs = claim.get("lineage_record_ids")
        if (
            not isinstance(refs, list)
            or len(refs) != len(set(refs))
            or any(ref not in record_ids for ref in refs)
        ):
            errors.append(f"{prefix}.lineage_record_ids must contain unique known records")
            refs = []
        referenced_kinds = {record_kinds.get(ref) for ref in refs}
        if referenced_kinds != required_kinds:
            errors.append(f"{prefix} must link signal, interpretation, alternative, and constitution trace")
    return {
        "valid": not errors,
        "errors": errors,
        "claim_ids": sorted(claim_ids),
        "lineage_kinds": sorted(set(record_kinds.values())),
    }

def validate_mission_contract_thesis_integration(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Integrate a compressed causal and normative interface for planner freedom."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["mission contract thesis integration must be an object"]}
    required_links = (
        "contract_thesis_id",
        "planner_contract_id",
        "compression_id",
        "situation_meaning_contract_id",
        "beneficiary_condition_contract_id",
        "causal_contract_id",
        "non_goal_contract_id",
        "signal_contract_id",
        "disconfirmation_protocol_id",
        "authority_clause_id",
        "lineage_index_id",
        "integration_rationale",
    )
    for field in required_links:
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    required_guarantees = {
        "decision_relevant_uncertainty_preserved",
        "situation_and_meaning_preserved",
        "beneficiary_external_change_preserved",
        "essential_causal_mechanisms_preserved",
        "normative_boundaries_preserved",
        "failure_attribution_preserved",
        "authority_return_preserved",
        "full_lineage_addressable",
        "planner_owns_implementation_form",
    }
    for guarantee in sorted(required_guarantees):
        if payload.get(guarantee) is not True:
            errors.append(f"{guarantee} must be true")
    if payload.get("full_reasoning_history_embedded") is not False:
        errors.append("full_reasoning_history_embedded must be false")
    if payload.get("implementation_form_prescribed") is not False:
        errors.append("implementation_form_prescribed must be false")
    if payload.get("planner_may_rewrite_mission_meaning") is not False:
        errors.append("planner_may_rewrite_mission_meaning must be false")

    causal_components = payload.get("causal_interface_components")
    expected_causal = {
        payload.get("beneficiary_condition_contract_id"),
        payload.get("causal_contract_id"),
        payload.get("signal_contract_id"),
        payload.get("disconfirmation_protocol_id"),
    }
    if (
        not isinstance(causal_components, list)
        or set(causal_components) != expected_causal
        or len(causal_components) != len(expected_causal)
    ):
        errors.append("causal_interface_components must link all causal contract records")
    normative_components = payload.get("normative_interface_components")
    expected_normative = {
        payload.get("situation_meaning_contract_id"),
        payload.get("non_goal_contract_id"),
        payload.get("authority_clause_id"),
        payload.get("lineage_index_id"),
    }
    if (
        not isinstance(normative_components, list)
        or set(normative_components) != expected_normative
        or len(normative_components) != len(expected_normative)
    ):
        errors.append("normative_interface_components must link all normative contract records")
    if payload.get("handoff_decision") != "eligible":
        errors.append("handoff_decision must be eligible")
    return {
        "valid": not errors,
        "errors": errors,
        "verified_guarantee_count": sum(
            payload.get(item) is True for item in required_guarantees
        ),
        "handoff_decision": payload.get("handoff_decision"),
    }

def validate_purpose_uncertainty_frontier(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Maintain only unresolved value uncertainties and active mission assumptions."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["purpose uncertainty frontier must be an object"]}
    for field in (
        "frontier_id",
        "contract_thesis_id",
        "active_mission_id",
        "snapshot_at",
        "frontier_refresh_reason",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("rerun_all_generators_on_every_event") is not False:
        errors.append("rerun_all_generators_on_every_event must be false")
    entries = payload.get("frontier_entries")
    if not isinstance(entries, list) or not entries:
        errors.append("frontier_entries must be a non-empty list")
        entries = []
    required_kinds = {"value_uncertainty", "mission_assumption"}
    seen_kinds = set()
    entry_ids = set()
    for index, entry in enumerate(entries):
        prefix = f"frontier_entries[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        entry_id = entry.get("entry_id")
        if not _non_empty(entry_id):
            errors.append(f"{prefix}.entry_id must be a non-empty string")
        elif entry_id in entry_ids:
            errors.append(f"{prefix}.entry_id must be unique")
        entry_ids.add(entry_id)
        kind = entry.get("kind")
        if kind not in required_kinds:
            errors.append(f"{prefix}.kind is not recognized")
        else:
            seen_kinds.add(kind)
        for field in (
            "claim",
            "relevance_to_value_or_mission",
            "evidence_id",
            "last_tested_at",
            "next_discriminating_observation",
            "wake_condition",
        ):
            if not _non_empty(entry.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        priority = entry.get("priority")
        if (
            isinstance(priority, bool)
            or not isinstance(priority, (int, float))
            or not 0 <= priority <= 1
        ):
            errors.append(f"{prefix}.priority must be a number between 0 and 1")
        status = entry.get("status")
        expected_status = "unresolved" if kind == "value_uncertainty" else "active"
        if status != expected_status:
            errors.append(f"{prefix}.status must be {expected_status} for {kind}")
        if kind == "mission_assumption":
            if entry.get("mission_id") != payload.get("active_mission_id"):
                errors.append(f"{prefix}.mission_id must match active_mission_id")
        elif entry.get("value_boundary_id") in ("", None):
            errors.append(f"{prefix}.value_boundary_id is required for value uncertainty")
    if seen_kinds != required_kinds:
        errors.append("frontier_entries must include both required frontier kinds")
    archived = payload.get("archived_entry_ids")
    if (
        not isinstance(archived, list)
        or not all(_non_empty(item) for item in archived)
        or len(archived) != len(set(archived))
    ):
        errors.append("archived_entry_ids must be a unique string list")
        archived = []
    if set(archived) & entry_ids:
        errors.append("archived_entry_ids cannot remain on the active frontier")
    return {
        "valid": not errors,
        "errors": errors,
        "frontier_entry_ids": sorted(entry_ids),
        "frontier_kinds": sorted(seen_kinds),
    }

def validate_purpose_wake_trigger_registry(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Register and evidence the six purpose-relevant wake trigger classes."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["purpose wake trigger registry must be an object"]}
    for field in ("wake_registry_id", "frontier_id", "unmatched_event_policy"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("unmatched_event_policy") != "do_not_wake":
        errors.append("unmatched_event_policy must be do_not_wake")
    required_types = {
        "signal_deviation",
        "forecast_miss",
        "authority_conflict",
        "mission_review",
        "expiring_opportunity",
        "downstream_boundary_return",
    }
    definitions = payload.get("trigger_definitions")
    if not isinstance(definitions, list):
        errors.append("trigger_definitions must be a list")
        definitions = []
    trigger_ids = set()
    type_by_id = {}
    seen_types = set()
    for index, definition in enumerate(definitions):
        prefix = f"trigger_definitions[{index}]"
        if not isinstance(definition, dict):
            errors.append(f"{prefix} must be an object")
            continue
        trigger_id = definition.get("trigger_id")
        if not _non_empty(trigger_id):
            errors.append(f"{prefix}.trigger_id must be a non-empty string")
        elif trigger_id in trigger_ids:
            errors.append(f"{prefix}.trigger_id must be unique")
        trigger_ids.add(trigger_id)
        trigger_type = definition.get("trigger_type")
        if trigger_type not in required_types:
            errors.append(f"{prefix}.trigger_type is not recognized")
        elif trigger_type in seen_types:
            errors.append(f"{prefix}.trigger_type must be unique")
        else:
            seen_types.add(trigger_type)
            type_by_id[trigger_id] = trigger_type
        for field in ("condition", "threshold", "required_evidence_kind"):
            if not _non_empty(definition.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if seen_types != required_types:
        errors.append("trigger_definitions must cover all six wake trigger classes exactly once")

    frontier_ids = payload.get("frontier_entry_ids")
    if (
        not isinstance(frontier_ids, list)
        or not frontier_ids
        or not all(_non_empty(item) for item in frontier_ids)
        or len(frontier_ids) != len(set(frontier_ids))
    ):
        errors.append("frontier_entry_ids must be a non-empty unique string list")
        frontier_ids = []
    events = payload.get("wake_events")
    if not isinstance(events, list) or not events:
        errors.append("wake_events must be a non-empty list")
        events = []
    event_ids = set()
    for index, event in enumerate(events):
        prefix = f"wake_events[{index}]"
        if not isinstance(event, dict):
            errors.append(f"{prefix} must be an object")
            continue
        event_id = event.get("event_id")
        if not _non_empty(event_id):
            errors.append(f"{prefix}.event_id must be a non-empty string")
        elif event_id in event_ids:
            errors.append(f"{prefix}.event_id must be unique")
        event_ids.add(event_id)
        for field in ("observed_change", "evidence_id", "observed_at"):
            if not _non_empty(event.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        trigger_id = event.get("matched_trigger_id")
        if trigger_id not in trigger_ids:
            errors.append(f"{prefix}.matched_trigger_id must reference a registered trigger")
        if event.get("trigger_type") != type_by_id.get(trigger_id):
            errors.append(f"{prefix}.trigger_type must match the registered trigger")
        if event.get("frontier_entry_id") not in frontier_ids:
            errors.append(f"{prefix}.frontier_entry_id must reference the active frontier")
        if event.get("wake_decision") != "wake":
            errors.append(f"{prefix}.wake_decision must be wake for a matched trigger")
    return {
        "valid": not errors,
        "errors": errors,
        "registered_trigger_types": sorted(seen_types),
        "wake_event_ids": sorted(event_ids),
    }

def validate_wake_cognitive_operation_selection(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Select exactly one cognitive operation that addresses the observed insufficiency."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["wake cognitive operation selection must be an object"]}
    for field in (
        "operation_selection_id",
        "wake_event_id",
        "frontier_entry_id",
        "observed_insufficiency",
        "insufficiency_evidence_id",
        "selection_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("fixed_pipeline_from_scratch") is not False:
        errors.append("fixed_pipeline_from_scratch must be false")
    allowed_operations = {
        "observe",
        "reinterpret",
        "revise_causal_model",
        "generate_candidate",
        "compare_candidates",
        "revise_contract",
        "review_authority",
    }
    options = payload.get("operation_options")
    if not isinstance(options, list) or len(options) < 2:
        errors.append("operation_options must contain at least two alternatives")
        options = []
    seen_operations = set()
    addressing = []
    for index, option in enumerate(options):
        prefix = f"operation_options[{index}]"
        if not isinstance(option, dict):
            errors.append(f"{prefix} must be an object")
            continue
        operation = option.get("operation")
        if operation not in allowed_operations:
            errors.append(f"{prefix}.operation is not recognized")
        elif operation in seen_operations:
            errors.append(f"{prefix}.operation must be unique")
        seen_operations.add(operation)
        for field in ("fit_rationale", "expected_update", "nonselection_reason"):
            if not _non_empty(option.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        fit = option.get("directly_addresses_insufficiency")
        if not isinstance(fit, bool):
            errors.append(f"{prefix}.directly_addresses_insufficiency must be boolean")
        elif fit:
            addressing.append(operation)
            if option.get("nonselection_reason") != "selected":
                errors.append(f"{prefix}.nonselection_reason must be selected for the fitting operation")
    expected_operation = addressing[0] if len(addressing) == 1 else ""
    if len(addressing) != 1:
        errors.append("exactly one operation must directly address the observed insufficiency")
    if payload.get("selected_operation") != expected_operation:
        errors.append("selected_operation must match the unique fitting operation")
    if payload.get("operation_sequence") != ([expected_operation] if expected_operation else []):
        errors.append("operation_sequence must contain only the selected cognitive operation")
    return {
        "valid": not errors,
        "errors": errors,
        "selected_operation": expected_operation,
        "candidate_operation_count": len(seen_operations),
    }

def validate_null_update_pressure_change(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Change one pressure dimension after a threshold of consecutive null updates."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["null update pressure change must be an object"]}
    for field in (
        "pressure_change_id",
        "frontier_entry_id",
        "cognitive_operation_id",
        "diagnosis_evidence_id",
        "decision_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    count = payload.get("consecutive_null_updates")
    threshold = payload.get("null_update_threshold")
    for field, value in (
        ("consecutive_null_updates", count),
        ("null_update_threshold", threshold),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            errors.append(f"{field} must be a positive integer")
    evidence_ids = payload.get("null_update_evidence_ids")
    if (
        not isinstance(evidence_ids, list)
        or not all(_non_empty(item) for item in evidence_ids)
        or len(evidence_ids) != len(set(evidence_ids))
    ):
        errors.append("null_update_evidence_ids must be a unique string list")
        evidence_ids = []
    if isinstance(count, int) and not isinstance(count, bool) and len(evidence_ids) != count:
        errors.append("null_update_evidence_ids must account for every consecutive null update")
    if payload.get("null_diagnosis") not in {"stability", "weak_pressure", "underdetermined"}:
        errors.append("null_diagnosis is not recognized")

    dimensions = payload.get("pressure_dimensions")
    required_dimensions = {
        "evidence_source",
        "causal_model",
        "stakeholder_representation",
    }
    if not isinstance(dimensions, list):
        errors.append("pressure_dimensions must be a list")
        dimensions = []
    seen = set()
    changed = []
    for index, dimension in enumerate(dimensions):
        prefix = f"pressure_dimensions[{index}]"
        if not isinstance(dimension, dict):
            errors.append(f"{prefix} must be an object")
            continue
        name = dimension.get("dimension")
        if name not in required_dimensions:
            errors.append(f"{prefix}.dimension is not recognized")
        elif name in seen:
            errors.append(f"{prefix}.dimension must be unique")
        seen.add(name)
        for field in ("previous_id", "current_id"):
            if not _non_empty(dimension.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        computed_changed = dimension.get("previous_id") != dimension.get("current_id")
        if dimension.get("changed") is not computed_changed:
            errors.append(f"{prefix}.changed must match the identifier transition")
        if computed_changed:
            changed.append(name)
    if seen != required_dimensions:
        errors.append("pressure_dimensions must cover all three pressure dimensions")

    threshold_reached = (
        isinstance(count, int)
        and not isinstance(count, bool)
        and isinstance(threshold, int)
        and not isinstance(threshold, bool)
        and count >= threshold
    )
    expected_decision = "change_pressure" if threshold_reached else "continue_current_pressure"
    if payload.get("decision") != expected_decision:
        errors.append("decision must follow the consecutive null-update threshold")
    expected_change_type = changed[0] if len(changed) == 1 else ""
    if threshold_reached:
        if len(changed) != 1:
            errors.append("threshold requires exactly one changed pressure dimension")
        if payload.get("pressure_change_type") != expected_change_type:
            errors.append("pressure_change_type must match the changed pressure dimension")
    else:
        if changed:
            errors.append("pressure dimensions must remain unchanged below threshold")
        if payload.get("pressure_change_type") not in ("", None):
            errors.append("pressure_change_type must be empty below threshold")
    return {
        "valid": not errors,
        "errors": errors,
        "decision": expected_decision,
        "changed_dimensions": changed,
    }

def validate_mission_lineage_fingerprint_commit(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Use compare-and-swap fingerprints to protect mission lineage from wake races."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["mission lineage fingerprint commit must be an object"]}
    for field in (
        "lineage_commit_id",
        "lineage_id",
        "wake_event_id",
        "writer_id",
        "wake_base_fingerprint",
        "current_stored_fingerprint",
        "proposed_lineage_fingerprint",
        "lineage_patch_hash",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    wake_ids = payload.get("concurrent_wake_ids")
    if (
        not isinstance(wake_ids, list)
        or len(wake_ids) < 2
        or not all(_non_empty(item) for item in wake_ids)
        or len(wake_ids) != len(set(wake_ids))
    ):
        errors.append("concurrent_wake_ids must contain at least two unique wake events")
        wake_ids = []
    if payload.get("wake_event_id") not in wake_ids:
        errors.append("wake_event_id must appear in concurrent_wake_ids")
    versions = {}
    for field in ("wake_base_version", "current_stored_version", "proposed_version"):
        value = payload.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            errors.append(f"{field} must be a positive integer")
            value = 0
        versions[field] = value
    if versions["proposed_version"] != versions["wake_base_version"] + 1:
        errors.append("proposed_version must directly succeed wake_base_version")
    base_matches = (
        payload.get("wake_base_fingerprint") == payload.get("current_stored_fingerprint")
        and versions["wake_base_version"] == versions["current_stored_version"]
    )
    proposed_changes = (
        payload.get("proposed_lineage_fingerprint") != payload.get("wake_base_fingerprint")
    )
    if not proposed_changes:
        errors.append("proposed_lineage_fingerprint must differ from wake_base_fingerprint")
    expected_status = "committed" if base_matches and proposed_changes else "rejected_stale"
    if payload.get("commit_status") != expected_status:
        errors.append("commit_status must follow the lineage fingerprint compare-and-swap")
    expected_result = (
        payload.get("proposed_lineage_fingerprint")
        if expected_status == "committed"
        else payload.get("current_stored_fingerprint")
    )
    if payload.get("resulting_stored_fingerprint") != expected_result:
        errors.append("resulting_stored_fingerprint must preserve or atomically replace current state")
    if expected_status == "rejected_stale":
        if payload.get("stale_write_overwrote_lineage") is not False:
            errors.append("stale_write_overwrote_lineage must be false")
        if payload.get("retry_from_current_required") is not True:
            errors.append("retry_from_current_required must be true after stale rejection")
    elif payload.get("retry_from_current_required") is not False:
        errors.append("retry_from_current_required must be false after commit")
    return {
        "valid": not errors,
        "errors": errors,
        "commit_status": expected_status,
        "resulting_stored_fingerprint": expected_result,
    }

def validate_semantic_repetition_review(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Warn on semantic repetition while preserving evidenced legitimate revisits."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["semantic repetition review must be an object"]}
    for field in (
        "repetition_review_id",
        "proposed_thought_id",
        "proposed_thought",
        "closest_prior_thought_id",
        "similarity_method_id",
        "similarity_evidence_id",
        "review_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    values = {}
    for field in ("semantic_similarity", "warning_threshold"):
        value = payload.get(field)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not 0 <= value <= 1
        ):
            errors.append(f"{field} must be a number between 0 and 1")
            value = 0
        values[field] = value
    expected_warning = values["semantic_similarity"] >= values["warning_threshold"]
    if payload.get("repetition_warning") is not expected_warning:
        errors.append("repetition_warning must follow the semantic similarity threshold")
    if payload.get("automatic_suppression") is not False:
        errors.append("automatic_suppression must be false")
    ground = payload.get("revisit_ground")
    allowed_grounds = {"none", "new_evidence", "changed_context", "expired_conclusion"}
    if ground not in allowed_grounds:
        errors.append("revisit_ground is not recognized")
        ground = "none"
    legitimate_revisit = ground != "none"
    if legitimate_revisit:
        for field in ("revisit_evidence_id", "material_difference"):
            if not _non_empty(payload.get(field)):
                errors.append(f"{field} is required for a legitimate revisit")
    elif payload.get("revisit_evidence_id") not in ("", None):
        errors.append("revisit_evidence_id must be empty when revisit_ground is none")
    if expected_warning and legitimate_revisit:
        expected_decision = "allow_revisit_with_warning"
    elif expected_warning:
        expected_decision = "revise_or_merge_repetition"
    else:
        expected_decision = "allow_new_thought"
    if payload.get("decision") != expected_decision:
        errors.append("decision must follow repetition warning and revisit evidence")
    return {
        "valid": not errors,
        "errors": errors,
        "repetition_warning": expected_warning,
        "decision": expected_decision,
    }

def validate_cognitive_budget_allocation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Allocate finite cognition by five decision-relevant pressure factors."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["cognitive budget allocation must be an object"]}
    for field in ("budget_allocation_id", "frontier_id", "budget_unit", "allocation_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    total_budget = payload.get("total_budget")
    if (
        isinstance(total_budget, bool)
        or not isinstance(total_budget, (int, float))
        or total_budget <= 0
    ):
        errors.append("total_budget must be a positive number")
        total_budget = 0
    if payload.get("unweighted_equal_allocation") is not False:
        errors.append("unweighted_equal_allocation must be false")
    factors = {
        "uncertainty",
        "consequence",
        "irreversibility",
        "opportunity_expiry",
        "expected_information_gain",
    }
    weights = payload.get("factor_weights")
    if not isinstance(weights, dict) or set(weights) != factors:
        errors.append("factor_weights must contain exactly the five pressure factors")
        weights = {}
    normalized_weights = {}
    for factor in factors:
        value = weights.get(factor)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or value < 0
            or value > 1
        ):
            errors.append(f"factor_weights.{factor} must be a number between 0 and 1")
            value = 0
        normalized_weights[factor] = value
    if abs(sum(normalized_weights.values()) - 1) > 1e-9:
        errors.append("factor_weights must sum to 1")

    candidates = payload.get("cognitive_candidates")
    if not isinstance(candidates, list) or len(candidates) < 2:
        errors.append("cognitive_candidates must contain at least two candidates")
        candidates = []
    candidate_ids = set()
    priorities = {}
    allocations = {}
    for index, candidate in enumerate(candidates):
        prefix = f"cognitive_candidates[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{prefix} must be an object")
            continue
        candidate_id = candidate.get("candidate_id")
        if not _non_empty(candidate_id):
            errors.append(f"{prefix}.candidate_id must be a non-empty string")
        elif candidate_id in candidate_ids:
            errors.append(f"{prefix}.candidate_id must be unique")
        candidate_ids.add(candidate_id)
        if not _non_empty(candidate.get("operation")):
            errors.append(f"{prefix}.operation must be a non-empty string")
        scores = candidate.get("factor_scores")
        if not isinstance(scores, dict) or set(scores) != factors:
            errors.append(f"{prefix}.factor_scores must contain exactly the five factors")
            scores = {}
        priority = 0
        for factor in factors:
            score = scores.get(factor)
            if (
                isinstance(score, bool)
                or not isinstance(score, (int, float))
                or not 0 <= score <= 1
            ):
                errors.append(f"{prefix}.factor_scores.{factor} must be between 0 and 1")
                score = 0
            priority += normalized_weights[factor] * score
        priorities[candidate_id] = priority
        claimed_priority = candidate.get("computed_priority")
        if (
            isinstance(claimed_priority, bool)
            or not isinstance(claimed_priority, (int, float))
            or abs(claimed_priority - priority) > 1e-9
        ):
            errors.append(f"{prefix}.computed_priority must equal the weighted factor score")
        allocation = candidate.get("allocated_budget")
        if (
            isinstance(allocation, bool)
            or not isinstance(allocation, (int, float))
            or allocation < 0
        ):
            errors.append(f"{prefix}.allocated_budget must be a non-negative number")
            allocation = 0
        allocations[candidate_id] = allocation
    priority_total = sum(priorities.values())
    if candidates and priority_total <= 0:
        errors.append("at least one cognitive candidate must have positive priority")
    if priority_total > 0:
        for candidate_id, priority in priorities.items():
            expected = total_budget * priority / priority_total
            if abs(allocations.get(candidate_id, 0) - expected) > 1e-6:
                errors.append(
                    f"cognitive candidate {candidate_id} allocation must be proportional to priority"
                )
    if abs(sum(allocations.values()) - total_budget) > 1e-6:
        errors.append("allocated cognitive budget must equal total_budget")
    return {
        "valid": not errors,
        "errors": errors,
        "computed_priorities": priorities,
        "allocated_budget": sum(allocations.values()),
    }

def validate_budget_exhaustion_deferral(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Defer honestly with a missing condition and wake trigger when cognition is exhausted."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["budget exhaustion deferral must be an object"]}
    for field in (
        "deferral_id",
        "budget_allocation_id",
        "frontier_entry_id",
        "unresolved_decision",
        "missing_condition",
        "why_condition_is_decisive",
        "required_evidence",
        "next_wake_trigger_id",
        "next_wake_threshold",
        "interim_safe_state",
        "option_preservation_action",
        "deferral_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("cognitive_budget_exhausted") is not True:
        errors.append("cognitive_budget_exhausted must be true")
    if payload.get("fabricated_closure") is not False:
        errors.append("fabricated_closure must be false")
    if payload.get("claimed_resolved") is not False:
        errors.append("claimed_resolved must be false")
    if payload.get("decision_status") != "deferred":
        errors.append("decision_status must be deferred")
    allowed_trigger_types = {
        "signal_deviation",
        "forecast_miss",
        "authority_conflict",
        "mission_review",
        "expiring_opportunity",
        "downstream_boundary_return",
    }
    if payload.get("next_wake_trigger_type") not in allowed_trigger_types:
        errors.append("next_wake_trigger_type must be a registered wake trigger class")
    remaining_budget = payload.get("remaining_budget")
    if (
        isinstance(remaining_budget, bool)
        or not isinstance(remaining_budget, (int, float))
        or remaining_budget != 0
    ):
        errors.append("remaining_budget must be zero at exhaustion")
    missing_conditions = payload.get("missing_condition_ids")
    if (
        not isinstance(missing_conditions, list)
        or len(missing_conditions) != 1
        or not _non_empty(missing_conditions[0])
    ):
        errors.append("missing_condition_ids must name exactly one decisive missing condition")
        missing_conditions = []
    if missing_conditions and missing_conditions[0] != payload.get("missing_condition_id"):
        errors.append("missing_condition_id must match the sole missing condition")
    return {
        "valid": not errors,
        "errors": errors,
        "decision_status": "deferred",
        "missing_condition_id": payload.get("missing_condition_id", ""),
    }

def validate_cognitive_sleep_operation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Treat waiting as cognition when reality is the only useful information source."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["cognitive sleep operation must be an object"]}
    for field in (
        "sleep_operation_id",
        "deferral_id",
        "frontier_entry_id",
        "missing_condition_id",
        "reality_observation_source_id",
        "observation_channel",
        "sleep_started_at",
        "latest_review_at",
        "safe_interim_state",
        "responsible_monitor_id",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("reality_is_only_useful_information_source") is not True:
        errors.append("reality_is_only_useful_information_source must be true")
    gain = payload.get("additional_internal_reasoning_information_gain")
    if (
        isinstance(gain, bool)
        or not isinstance(gain, (int, float))
        or gain < 0
        or gain > 1
    ):
        errors.append("additional_internal_reasoning_information_gain must be between 0 and 1")
        gain = 1
    if gain != 0:
        errors.append("additional_internal_reasoning_information_gain must be zero for sleep")
    if payload.get("busy_polling") is not False:
        errors.append("busy_polling must be false")
    if payload.get("mission_abandoned") is not False:
        errors.append("mission_abandoned must be false")
    if (
        _non_empty(payload.get("sleep_started_at"))
        and _non_empty(payload.get("latest_review_at"))
        and payload.get("latest_review_at") <= payload.get("sleep_started_at")
    ):
        errors.append("latest_review_at must follow sleep_started_at")
    trigger = payload.get("wake_trigger")
    if not isinstance(trigger, dict):
        errors.append("wake_trigger must be an object")
        trigger = {}
    for field in ("trigger_id", "condition", "threshold", "required_evidence"):
        if not _non_empty(trigger.get(field)):
            errors.append(f"wake_trigger.{field} must be a non-empty string")
    interrupts = payload.get("early_interrupt_conditions")
    if not isinstance(interrupts, list) or len(interrupts) < 2:
        errors.append("early_interrupt_conditions must include at least two safety interrupts")
        interrupts = []
    interrupt_types = set()
    for index, interrupt in enumerate(interrupts):
        prefix = f"early_interrupt_conditions[{index}]"
        if not isinstance(interrupt, dict):
            errors.append(f"{prefix} must be an object")
            continue
        interrupt_type = interrupt.get("type")
        if interrupt_type not in {"harm", "authority_conflict"}:
            errors.append(f"{prefix}.type must be harm or authority_conflict")
        interrupt_types.add(interrupt_type)
        for field in ("condition", "response"):
            if not _non_empty(interrupt.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if interrupt_types != {"harm", "authority_conflict"}:
        errors.append("early_interrupt_conditions must cover harm and authority_conflict")
    status = payload.get("sleep_status")
    if status not in {"sleeping", "woken"}:
        errors.append("sleep_status must be sleeping or woken")
    if status == "woken":
        for field in ("wake_evidence_id", "woken_at"):
            if not _non_empty(payload.get(field)):
                errors.append(f"{field} is required when woken")
    elif payload.get("wake_evidence_id") not in ("", None):
        errors.append("wake_evidence_id must be empty while sleeping")
    return {
        "valid": not errors,
        "errors": errors,
        "sleep_status": status,
        "interrupt_types": sorted(interrupt_types),
    }

def validate_event_driven_runtime_thesis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Integrate an event-driven frontier selecting least sufficient bounded cognition."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["event-driven runtime thesis must be an object"]}
    link_fields = (
        "runtime_thesis_id",
        "contract_thesis_id",
        "frontier_id",
        "wake_registry_id",
        "operation_selection_id",
        "pressure_change_policy_id",
        "lineage_commit_policy_id",
        "repetition_review_policy_id",
        "budget_allocation_id",
        "deferral_policy_id",
        "sleep_policy_id",
        "runtime_rationale",
    )
    for field in link_fields:
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    guarantees = {
        "frontier_contains_only_unresolved_or_active_items",
        "wake_requires_registered_evidenced_event",
        "least_sufficient_operation_selected",
        "null_updates_change_pressure_at_threshold",
        "lineage_commits_are_fingerprint_guarded",
        "semantic_repetition_warns_without_suppression",
        "cognitive_budget_is_bounded",
        "budget_exhaustion_defers_without_closure",
        "reality_only_wait_uses_monitored_sleep",
    }
    for guarantee in sorted(guarantees):
        if payload.get(guarantee) is not True:
            errors.append(f"{guarantee} must be true")
    if payload.get("event_driven") is not True:
        errors.append("event_driven must be true")
    if payload.get("fixed_pipeline_is_default") is not False:
        errors.append("fixed_pipeline_is_default must be false")
    if payload.get("rerun_all_generators_per_event") is not False:
        errors.append("rerun_all_generators_per_event must be false")
    modes = payload.get("runtime_modes")
    expected_modes = {"active_cognition", "deferred", "sleeping"}
    if (
        not isinstance(modes, list)
        or set(modes) != expected_modes
        or len(modes) != len(expected_modes)
    ):
        errors.append("runtime_modes must cover active_cognition, deferred, and sleeping")
    max_budget = payload.get("maximum_cognitive_budget_per_wake")
    if (
        isinstance(max_budget, bool)
        or not isinstance(max_budget, (int, float))
        or max_budget <= 0
    ):
        errors.append("maximum_cognitive_budget_per_wake must be a positive number")
    if not _non_empty(payload.get("cognitive_budget_unit")):
        errors.append("cognitive_budget_unit must be a non-empty string")
    if payload.get("runtime_decision") != "operational":
        errors.append("runtime_decision must be operational")
    return {
        "valid": not errors,
        "errors": errors,
        "verified_guarantee_count": sum(payload.get(item) is True for item in guarantees),
        "runtime_decision": payload.get("runtime_decision"),
    }

def validate_incentive_corroborated_signal_priority(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Discount manufactured urgency and restore priority through independent corroboration."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["incentive corroborated signal priority must be an object"]}
    for field in (
        "priority_review_id",
        "signal_id",
        "primary_source_id",
        "source_incentive_evidence_id",
        "priority_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    values = {}
    for field in ("reported_urgency", "source_incentive_risk", "priority_threshold"):
        value = payload.get(field)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not 0 <= value <= 1
        ):
            errors.append(f"{field} must be a number between 0 and 1")
            value = 0
        values[field] = value
    if not _non_empty(payload.get("source_incentive")):
        errors.append("source_incentive must be a non-empty string")

    corroborations = payload.get("corroborating_sources")
    if not isinstance(corroborations, list) or not corroborations:
        errors.append("corroborating_sources must be a non-empty list")
        corroborations = []
    source_ids = {payload.get("primary_source_id")}
    support_values = []
    for index, source in enumerate(corroborations):
        prefix = f"corroborating_sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{prefix} must be an object")
            continue
        source_id = source.get("source_id")
        if not _non_empty(source_id):
            errors.append(f"{prefix}.source_id must be a non-empty string")
        elif source_id in source_ids:
            errors.append(f"{prefix}.source_id must be independent and unique")
        source_ids.add(source_id)
        for field in ("observation", "evidence_id", "independence_evidence_id"):
            if not _non_empty(source.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if source.get("operationally_independent") is not True:
            errors.append(f"{prefix}.operationally_independent must be true")
        support = source.get("support_strength")
        if (
            isinstance(support, bool)
            or not isinstance(support, (int, float))
            or not 0 <= support <= 1
        ):
            errors.append(f"{prefix}.support_strength must be between 0 and 1")
        else:
            support_values.append(support)
    corroboration_strength = (
        sum(support_values) / len(support_values) if support_values else 0
    )
    incentive_adjusted = values["reported_urgency"] * (1 - values["source_incentive_risk"])
    computed_priority = incentive_adjusted * corroboration_strength
    for field, expected in (
        ("corroboration_strength", corroboration_strength),
        ("computed_priority", computed_priority),
    ):
        claimed = payload.get(field)
        if (
            isinstance(claimed, bool)
            or not isinstance(claimed, (int, float))
            or abs(claimed - expected) > 1e-9
        ):
            errors.append(f"{field} must match the incentive and corroboration calculation")
    expected_decision = (
        "prioritize" if computed_priority >= values["priority_threshold"] else "hold_priority"
    )
    if payload.get("decision") != expected_decision:
        errors.append("decision must follow corroborated incentive-adjusted priority")
    if payload.get("reported_urgency_used_directly") is not False:
        errors.append("reported_urgency_used_directly must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "computed_priority": computed_priority,
        "decision": expected_decision,
    }

def validate_reference_evidence_authority_boundary(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Treat reference content as evidence while quarantining embedded instructions."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["reference evidence authority boundary must be an object"]}
    for field in (
        "reference_review_id",
        "reference_id",
        "reference_source",
        "content_hash",
        "constitution_id",
        "constitutional_clause_id",
        "authorized_interpreter_id",
        "review_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("reference_role") != "evidence_only":
        errors.append("reference_role must be evidence_only")
    if payload.get("reference_can_issue_instructions") is not False:
        errors.append("reference_can_issue_instructions must be false")
    if payload.get("reference_can_amend_constitution") is not False:
        errors.append("reference_can_amend_constitution must be false")
    if payload.get("constitutional_guidance_taken_directly_from_reference") is not False:
        errors.append("constitutional_guidance_taken_directly_from_reference must be false")

    claims = payload.get("evidence_claims")
    if not isinstance(claims, list) or not claims:
        errors.append("evidence_claims must be a non-empty list")
        claims = []
    claim_ids = set()
    evidence_ids = set()
    for index, claim in enumerate(claims):
        prefix = f"evidence_claims[{index}]"
        if not isinstance(claim, dict):
            errors.append(f"{prefix} must be an object")
            continue
        claim_id = claim.get("claim_id")
        if not _non_empty(claim_id):
            errors.append(f"{prefix}.claim_id must be a non-empty string")
        elif claim_id in claim_ids:
            errors.append(f"{prefix}.claim_id must be unique")
        claim_ids.add(claim_id)
        for field in ("claim", "content_locator", "evidence_id"):
            if not _non_empty(claim.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        evidence_ids.add(claim.get("evidence_id"))
        if claim.get("treated_as_instruction") is not False:
            errors.append(f"{prefix}.treated_as_instruction must be false")

    instructions = payload.get("embedded_instructions")
    if not isinstance(instructions, list):
        errors.append("embedded_instructions must be a list")
        instructions = []
    instruction_ids = set()
    for index, instruction in enumerate(instructions):
        prefix = f"embedded_instructions[{index}]"
        if not isinstance(instruction, dict):
            errors.append(f"{prefix} must be an object")
            continue
        instruction_id = instruction.get("instruction_id")
        if not _non_empty(instruction_id):
            errors.append(f"{prefix}.instruction_id must be a non-empty string")
        elif instruction_id in instruction_ids:
            errors.append(f"{prefix}.instruction_id must be unique")
        instruction_ids.add(instruction_id)
        for field in ("directive", "content_locator", "classification"):
            if not _non_empty(instruction.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if instruction.get("quarantined") is not True:
            errors.append(f"{prefix}.quarantined must be true")
        if instruction.get("executed") is not False:
            errors.append(f"{prefix}.executed must be false")
    applied = payload.get("constitutional_application_evidence_ids")
    if (
        not isinstance(applied, list)
        or not applied
        or not all(_non_empty(item) for item in applied)
        or any(item not in evidence_ids for item in applied)
    ):
        errors.append("constitutional_application_evidence_ids must reference extracted evidence claims")
    return {
        "valid": not errors,
        "errors": errors,
        "evidence_claim_ids": sorted(claim_ids),
        "quarantined_instruction_ids": sorted(instruction_ids),
    }

