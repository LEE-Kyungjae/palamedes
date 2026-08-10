from __future__ import annotations

from typing import Any, Dict, List
from ._01_kinds_value import _non_empty, activate_external_action_kill_switch, apply_failure_thesis, build_policy_gated_prompt_context, build_semantic_infrastructure_reuse_manifest, migrate_experimental_mission_state, quarantine_invalid_structured_output, record_tournament_provider_timeout, resolve_mission_write_fingerprint, restore_selection_preserving_outcomes, resume_frozen_candidate_tournament, run_bounded_signal_to_mission_vertical_slice, scope_constitution_conflict_actions


def validate_upstream_human_cognition_retirement_ledger(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Measure human cognition retired before a planner may act."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["upstream human cognition retirement ledger must be an object"]}
    for field in (
        "labor_ledger_id",
        "proof_case_id",
        "baseline_condition_id",
        "palamedes_condition_id",
        "measurement_window_start",
        "planner_action_authorized_at",
        "measurement_protocol_id",
        "ledger_fingerprint",
        "ledger_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if (
        _non_empty(payload.get("measurement_window_start"))
        and _non_empty(payload.get("planner_action_authorized_at"))
        and payload["planner_action_authorized_at"] <= payload["measurement_window_start"]
    ):
        errors.append("planner_action_authorized_at must follow measurement_window_start")
    required_categories = {
        "framing",
        "clarification",
        "approval",
        "correction",
        "intervention",
    }
    categories = payload.get("labor_categories")
    if not isinstance(categories, list) or len(categories) != len(required_categories):
        errors.append("labor_categories must contain exactly five upstream labor categories")
        categories = []
    observed = set()
    retired_total = 0.0
    added_total = 0.0
    baseline_total = 0.0
    palamedes_total = 0.0
    for index, category in enumerate(categories):
        prefix = f"labor_categories[{index}]"
        if not isinstance(category, dict):
            errors.append(f"{prefix} must be an object")
            continue
        name = category.get("category")
        if name not in required_categories:
            errors.append(f"{prefix}.category is not recognized")
        elif name in observed:
            errors.append(f"{prefix}.category must be unique")
        observed.add(name)
        for field in ("measurement_record_id", "measurement_method", "activity_definition", "evidence_artifact_id"):
            if not _non_empty(category.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        values = {}
        for field in (
            "baseline_minutes",
            "palamedes_minutes",
            "baseline_event_count",
            "palamedes_event_count",
            "nondelegable_minutes",
        ):
            value = category.get(field)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
                errors.append(f"{prefix}.{field} must be a non-negative number")
                value = 0
            values[field] = value
        if values["nondelegable_minutes"] > values["palamedes_minutes"]:
            errors.append(f"{prefix}.nondelegable_minutes must not exceed palamedes_minutes")
        expected_retired = max(values["baseline_minutes"] - values["palamedes_minutes"], 0)
        expected_added = max(values["palamedes_minutes"] - values["baseline_minutes"], 0)
        if category.get("retired_minutes") != expected_retired:
            errors.append(f"{prefix}.retired_minutes must equal positive baseline reduction")
        if category.get("added_minutes") != expected_added:
            errors.append(f"{prefix}.added_minutes must equal positive Palamedes increase")
        if category.get("measured_before_planner_action") is not True:
            errors.append(f"{prefix}.measured_before_planner_action must be true")
        if name == "approval":
            if category.get("nondelegable_approval_retired") is not False:
                errors.append(f"{prefix}.nondelegable_approval_retired must be false")
            if not _non_empty(category.get("approval_authority_boundary_id")):
                errors.append(f"{prefix}.approval_authority_boundary_id must be a non-empty string")
        retired_total += expected_retired
        added_total += expected_added
        baseline_total += values["baseline_minutes"]
        palamedes_total += values["palamedes_minutes"]
    if observed != required_categories:
        errors.append("labor_categories must cover all five upstream categories exactly once")
    totals = payload.get("declared_totals")
    if not isinstance(totals, dict):
        errors.append("declared_totals must be an object")
        totals = {}
    expected_totals = {
        "baseline_minutes": baseline_total,
        "palamedes_minutes": palamedes_total,
        "retired_minutes": retired_total,
        "added_minutes": added_total,
        "net_minutes_retired": baseline_total - palamedes_total,
    }
    for field, expected in expected_totals.items():
        if totals.get(field) != expected:
            errors.append(f"declared_totals.{field} must equal measured category values")
    if payload.get("post_planner_labor_included") is not False:
        errors.append("post_planner_labor_included must be false")
    if payload.get("nondelegable_human_authority_counted_as_retired") is not False:
        errors.append("nondelegable_human_authority_counted_as_retired must be false")
    if payload.get("labor_retirement_claim_status") != "measured":
        errors.append("labor_retirement_claim_status must be measured")
    return {
        "valid": not errors,
        "errors": errors,
        "category_count": len(observed),
        "retired_minutes": retired_total,
        "added_minutes": added_total,
        "net_minutes_retired": baseline_total - palamedes_total,
    }

def validate_planner_semantic_reconstruction_burden_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Measure planner reconstruction and clarification work after handoff."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["planner semantic reconstruction burden report must be an object"]}
    for field in (
        "planner_burden_report_id",
        "proof_case_id",
        "measurement_protocol_id",
        "report_fingerprint",
        "report_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    required_conditions = {"human", "one_shot_agent", "palamedes"}
    required_elements = {
        "beneficiary",
        "invariant_meaning",
        "causal_thesis",
        "success_harm_signals",
        "non_goals",
        "authority",
    }
    reports = payload.get("condition_reports")
    if not isinstance(reports, list) or len(reports) != len(required_conditions):
        errors.append("condition_reports must contain human, one_shot_agent, and palamedes")
        reports = []
    observed_conditions = set()
    burden_by_condition = {}
    for report_index, report in enumerate(reports):
        prefix = f"condition_reports[{report_index}]"
        if not isinstance(report, dict):
            errors.append(f"{prefix} must be an object")
            continue
        condition = report.get("condition")
        if condition not in required_conditions:
            errors.append(f"{prefix}.condition is not recognized")
        elif condition in observed_conditions:
            errors.append(f"{prefix}.condition must be unique")
        observed_conditions.add(condition)
        for field in (
            "source_handoff_artifact_id",
            "source_handoff_fingerprint",
            "planner_id",
            "session_id",
            "handoff_received_at",
            "strategy_ready_at",
            "session_evidence_artifact_id",
        ):
            if not _non_empty(report.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if (
            _non_empty(report.get("handoff_received_at"))
            and _non_empty(report.get("strategy_ready_at"))
            and report["strategy_ready_at"] <= report["handoff_received_at"]
        ):
            errors.append(f"{prefix}.strategy_ready_at must follow handoff_received_at")
        elements = report.get("semantic_elements")
        if not isinstance(elements, list) or len(elements) != len(required_elements):
            errors.append(f"{prefix}.semantic_elements must contain exactly six mission elements")
            elements = []
        observed_elements = set()
        totals = {
            "reconstruction_minutes": 0.0,
            "clarification_question_count": 0.0,
            "source_lookup_count": 0.0,
            "semantic_correction_count": 0.0,
        }
        for element_index, element in enumerate(elements):
            element_prefix = f"{prefix}.semantic_elements[{element_index}]"
            if not isinstance(element, dict):
                errors.append(f"{element_prefix} must be an object")
                continue
            name = element.get("element")
            if name not in required_elements:
                errors.append(f"{element_prefix}.element is not recognized")
            elif name in observed_elements:
                errors.append(f"{element_prefix}.element must be unique")
            observed_elements.add(name)
            status = element.get("status")
            if status not in {"directly_understood", "reconstructed", "clarified", "corrected"}:
                errors.append(f"{element_prefix}.status is not recognized")
            for field in ("measurement_record_id", "evidence_artifact_id", "burden_rationale"):
                if not _non_empty(element.get(field)):
                    errors.append(f"{element_prefix}.{field} must be a non-empty string")
            values = {}
            for field in totals:
                value = element.get(field)
                if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
                    errors.append(f"{element_prefix}.{field} must be a non-negative number")
                    value = 0
                values[field] = value
                totals[field] += value
            if status == "directly_understood" and any(values.values()):
                errors.append(f"{element_prefix} directly_understood must require zero reconstruction burden")
            if status == "clarified" and values["clarification_question_count"] < 1:
                errors.append(f"{element_prefix} clarified requires at least one question")
            if status == "corrected" and values["semantic_correction_count"] < 1:
                errors.append(f"{element_prefix} corrected requires at least one semantic correction")
        if observed_elements != required_elements:
            errors.append(f"{prefix}.semantic_elements must cover all six elements exactly once")
        declared = report.get("declared_totals")
        if not isinstance(declared, dict):
            errors.append(f"{prefix}.declared_totals must be an object")
            declared = {}
        for field, expected in totals.items():
            if declared.get(field) != expected:
                errors.append(f"{prefix}.declared_totals.{field} must equal semantic element totals")
        latency = report.get("minutes_to_strategy_ready")
        if not isinstance(latency, (int, float)) or isinstance(latency, bool) or latency < 0:
            errors.append(f"{prefix}.minutes_to_strategy_ready must be a non-negative number")
        if report.get("burden_measured_after_handoff_before_strategy") is not True:
            errors.append(f"{prefix}.burden_measured_after_handoff_before_strategy must be true")
        burden_by_condition[condition] = totals
    if observed_conditions != required_conditions:
        errors.append("condition_reports must cover all three conditions exactly once")
    if payload.get("planner_satisfaction_substitutes_for_measurement") is not False:
        errors.append("planner_satisfaction_substitutes_for_measurement must be false")
    if payload.get("unlogged_clarification_treated_as_zero") is not False:
        errors.append("unlogged_clarification_treated_as_zero must be false")
    if payload.get("condition_results_reported_separately") is not True:
        errors.append("condition_results_reported_separately must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "condition_count": len(observed_conditions),
        "burden_by_condition": burden_by_condition,
    }

def validate_multi_horizon_outcome_quality_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Measure beneficiary change, side effects, sustainability, and options over time."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["multi horizon outcome quality report must be an object"]}
    for field in (
        "outcome_quality_report_id",
        "mission_contract_id",
        "mission_contract_fingerprint",
        "strategy_version_id",
        "strategy_fingerprint",
        "outcome_protocol_id",
        "report_fingerprint",
        "report_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    required_horizons = ["short", "medium", "long"]
    required_dimensions = {
        "beneficiary_change",
        "side_effects",
        "sustainability",
        "option_preservation",
    }
    horizons = payload.get("horizon_assessments")
    if not isinstance(horizons, list) or len(horizons) != len(required_horizons):
        errors.append("horizon_assessments must contain short, medium, and long horizons")
        horizons = []
    observed_horizons = []
    prior_day = -1
    observed_dimension_count = 0
    pending_dimension_count = 0
    for horizon_index, horizon in enumerate(horizons):
        prefix = f"horizon_assessments[{horizon_index}]"
        if not isinstance(horizon, dict):
            errors.append(f"{prefix} must be an object")
            continue
        horizon_name = horizon.get("horizon")
        observed_horizons.append(horizon_name)
        day = horizon.get("day_from_strategy_start")
        if not isinstance(day, int) or isinstance(day, bool) or day <= prior_day:
            errors.append(f"{prefix}.day_from_strategy_start must be a strictly increasing positive integer")
        else:
            prior_day = day
        for field in ("scheduled_at", "horizon_definition", "assessment_artifact_id"):
            if not _non_empty(horizon.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        reached = horizon.get("horizon_reached")
        if not isinstance(reached, bool):
            errors.append(f"{prefix}.horizon_reached must be boolean")
        dimensions = horizon.get("dimensions")
        if not isinstance(dimensions, list) or len(dimensions) != len(required_dimensions):
            errors.append(f"{prefix}.dimensions must contain exactly four outcome dimensions")
            dimensions = []
        observed_dimensions = set()
        for dimension_index, dimension in enumerate(dimensions):
            dimension_prefix = f"{prefix}.dimensions[{dimension_index}]"
            if not isinstance(dimension, dict):
                errors.append(f"{dimension_prefix} must be an object")
                continue
            name = dimension.get("dimension")
            if name not in required_dimensions:
                errors.append(f"{dimension_prefix}.dimension is not recognized")
            elif name in observed_dimensions:
                errors.append(f"{dimension_prefix}.dimension must be unique")
            observed_dimensions.add(name)
            for field in ("metric_or_question", "baseline_or_reference", "target_or_boundary"):
                if not _non_empty(dimension.get(field)):
                    errors.append(f"{dimension_prefix}.{field} must be a non-empty string")
            status = dimension.get("measurement_status")
            expected_status = "observed" if reached is True else "pending"
            if status != expected_status:
                errors.append(f"{dimension_prefix}.measurement_status must be {expected_status}")
            if status == "observed":
                observed_dimension_count += 1
                for field in (
                    "observed_value",
                    "evidence_artifact_id",
                    "evidence_fingerprint",
                    "assessment",
                    "uncertainty",
                ):
                    if not _non_empty(dimension.get(field)):
                        errors.append(f"{dimension_prefix}.{field} is required when observed")
                if dimension.get("next_observation_at") not in ("", None):
                    errors.append(f"{dimension_prefix}.next_observation_at must be empty when observed")
            elif status == "pending":
                pending_dimension_count += 1
                for field in ("next_observation_at", "pending_reason"):
                    if not _non_empty(dimension.get(field)):
                        errors.append(f"{dimension_prefix}.{field} is required when pending")
                for field in ("observed_value", "evidence_artifact_id", "evidence_fingerprint", "assessment"):
                    if dimension.get(field) not in ("", None):
                        errors.append(f"{dimension_prefix}.{field} must be empty while pending")
        if observed_dimensions != required_dimensions:
            errors.append(f"{prefix}.dimensions must cover every outcome dimension exactly once")
    if observed_horizons != required_horizons:
        errors.append("horizon_assessments must be ordered short, medium, long")
    if payload.get("early_success_extrapolated_to_later_horizons") is not False:
        errors.append("early_success_extrapolated_to_later_horizons must be false")
    if payload.get("side_effects_netted_into_beneficiary_change") is not False:
        errors.append("side_effects_netted_into_beneficiary_change must be false")
    if payload.get("sustainability_assumed_from_initial_delivery") is not False:
        errors.append("sustainability_assumed_from_initial_delivery must be false")
    if payload.get("lost_options_ignored") is not False:
        errors.append("lost_options_ignored must be false")
    if payload.get("dimensions_reported_separately") is not True:
        errors.append("dimensions_reported_separately must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "horizon_count": len(observed_horizons),
        "observed_dimension_count": observed_dimension_count,
        "pending_dimension_count": pending_dimension_count,
    }

def validate_forecast_calibration_failure_signal_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Score frozen forecast ranges and failure signals against later observations."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["forecast calibration failure signal report must be an object"]}
    for field in (
        "calibration_report_id",
        "mission_contract_id",
        "strategy_version_id",
        "forecast_protocol_id",
        "forecast_set_fingerprint",
        "report_fingerprint",
        "report_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if (
        _non_empty(payload.get("forecast_frozen_at"))
        and _non_empty(payload.get("strategy_authorized_at"))
        and payload["forecast_frozen_at"] >= payload["strategy_authorized_at"]
    ):
        errors.append("forecast_frozen_at must precede strategy_authorized_at")
    entries = payload.get("forecast_entries")
    if not isinstance(entries, list) or not entries:
        errors.append("forecast_entries must be a non-empty list")
        entries = []
    observed_ids = set()
    range_hits = 0
    signal_brier_total = 0.0
    interval_width_total = 0.0
    scored_count = 0
    for index, entry in enumerate(entries):
        prefix = f"forecast_entries[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in (
            "forecast_id",
            "metric_or_signal",
            "horizon",
            "unit",
            "forecast_fingerprint",
            "observation_artifact_id",
            "observation_fingerprint",
            "scoring_rationale",
        ):
            if not _non_empty(entry.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        forecast_id = entry.get("forecast_id")
        if forecast_id in observed_ids:
            errors.append(f"{prefix}.forecast_id must be unique")
        observed_ids.add(forecast_id)
        if entry.get("horizon") not in {"short", "medium", "long"}:
            errors.append(f"{prefix}.horizon is not recognized")
        kind = entry.get("forecast_kind")
        if kind not in {"outcome_range", "failure_signal"}:
            errors.append(f"{prefix}.forecast_kind is not recognized")
            continue
        if entry.get("frozen_before_strategy") is not True:
            errors.append(f"{prefix}.frozen_before_strategy must be true")
        if entry.get("edited_after_observation") is not False:
            errors.append(f"{prefix}.edited_after_observation must be false")
        observed = entry.get("observed_value")
        if kind == "outcome_range":
            lower = entry.get("forecast_lower")
            upper = entry.get("forecast_upper")
            if any(
                not isinstance(value, (int, float)) or isinstance(value, bool)
                for value in (lower, upper, observed)
            ) or lower > upper:
                errors.append(f"{prefix} outcome range requires numeric lower <= upper and observation")
                continue
            hit = lower <= observed <= upper
            width = upper - lower
            if entry.get("range_hit") is not hit:
                errors.append(f"{prefix}.range_hit must equal the observed interval result")
            if entry.get("interval_width") != width:
                errors.append(f"{prefix}.interval_width must equal forecast_upper - forecast_lower")
            range_hits += int(hit)
            interval_width_total += width
            scored_count += 1
        else:
            probability = entry.get("forecast_probability")
            occurred = entry.get("signal_occurred")
            if (
                not isinstance(probability, (int, float))
                or isinstance(probability, bool)
                or not 0 <= probability <= 1
            ):
                errors.append(f"{prefix}.forecast_probability must be between zero and one")
                continue
            if not isinstance(occurred, bool):
                errors.append(f"{prefix}.signal_occurred must be boolean")
                continue
            expected_brier = (probability - int(occurred)) ** 2
            if entry.get("brier_score") != expected_brier:
                errors.append(f"{prefix}.brier_score must equal squared probability error")
            signal_brier_total += expected_brier
            scored_count += 1
    declared = payload.get("declared_scores")
    if not isinstance(declared, dict):
        errors.append("declared_scores must be an object")
        declared = {}
    range_count = sum(
        isinstance(entry, dict) and entry.get("forecast_kind") == "outcome_range"
        for entry in entries
    )
    signal_count = sum(
        isinstance(entry, dict) and entry.get("forecast_kind") == "failure_signal"
        for entry in entries
    )
    expected_scores = {
        "forecast_count": len(entries),
        "outcome_range_count": range_count,
        "failure_signal_count": signal_count,
        "range_hit_count": range_hits,
        "mean_interval_width": interval_width_total / range_count if range_count else 0,
        "mean_failure_signal_brier": signal_brier_total / signal_count if signal_count else 0,
    }
    for field, expected in expected_scores.items():
        if declared.get(field) != expected:
            errors.append(f"declared_scores.{field} must equal recomputed score")
    if payload.get("confidence_prose_substitutes_for_numeric_forecast") is not False:
        errors.append("confidence_prose_substitutes_for_numeric_forecast must be false")
    if payload.get("post_outcome_forecast_revision_allowed") is not False:
        errors.append("post_outcome_forecast_revision_allowed must be false")
    if payload.get("wide_intervals_rewarded_as_equally_informative") is not False:
        errors.append("wide_intervals_rewarded_as_equally_informative must be false")
    if payload.get("missed_failure_signals_omitted") is not False:
        errors.append("missed_failure_signals_omitted must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "forecast_count": len(entries),
        "scored_count": scored_count,
        "range_hit_count": range_hits,
        "mean_failure_signal_brier": expected_scores["mean_failure_signal_brier"],
    }

def validate_anti_entrenchment_simpler_alternative_decision(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require Palamedes to prefer sufficient simpler alternatives over self-expansion."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["anti entrenchment decision must be an object"]}
    for field in (
        "anti_entrenchment_decision_id",
        "mission_candidate_id",
        "evaluation_protocol_id",
        "evaluation_fingerprint",
        "selected_option_id",
        "decision_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    required_types = {"do_nothing", "simpler_non_palamedes", "palamedes_mission"}
    options = payload.get("options")
    if not isinstance(options, list) or len(options) != len(required_types):
        errors.append("options must contain exactly three anti-entrenchment alternatives")
        options = []
    seen_types = set()
    seen_ids = set()
    option_by_id = {}
    sufficient_options = []
    for index, option in enumerate(options):
        prefix = f"options[{index}]"
        if not isinstance(option, dict):
            errors.append(f"{prefix} must be an object")
            continue
        option_id = option.get("option_id")
        option_type = option.get("option_type")
        for field in (
            "option_id",
            "description",
            "beneficiary_effect",
            "evidence_basis",
            "rejection_or_selection_rationale",
        ):
            if not _non_empty(option.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if option_id in seen_ids:
            errors.append(f"{prefix}.option_id must be unique")
        seen_ids.add(option_id)
        if option_type not in required_types:
            errors.append(f"{prefix}.option_type is not recognized")
        elif option_type in seen_types:
            errors.append(f"{prefix}.option_type must be unique")
        seen_types.add(option_type)
        scores = {}
        for field in (
            "purpose_fit",
            "expected_beneficiary_value",
            "system_complexity_cost",
            "operator_burden",
            "irreversibility_risk",
            "palamedes_expansion_benefit",
        ):
            value = option.get(field)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
                errors.append(f"{prefix}.{field} must be between zero and one")
                value = 0
            scores[field] = value
        sufficient = option.get("purpose_sufficient")
        if not isinstance(sufficient, bool):
            errors.append(f"{prefix}.purpose_sufficient must be boolean")
        if option.get("primary_effect_expands_palamedes") is not False:
            errors.append(f"{prefix}.primary_effect_expands_palamedes must be false")
        if option.get("scored_before_selection") is not True:
            errors.append(f"{prefix}.scored_before_selection must be true")
        burden = (
            scores["system_complexity_cost"]
            + scores["operator_burden"]
            + scores["irreversibility_risk"]
        )
        declared_burden = option.get("combined_burden")
        if declared_burden != burden:
            errors.append(f"{prefix}.combined_burden must equal complexity, operator, and irreversibility burden")
        option_by_id[option_id] = {"type": option_type, "sufficient": sufficient, "burden": burden}
        if sufficient is True:
            sufficient_options.append((burden, option_id, option_type))
    if seen_types != required_types:
        errors.append("options must cover do_nothing, simpler_non_palamedes, and palamedes_mission exactly once")
    selected_id = payload.get("selected_option_id")
    selected = option_by_id.get(selected_id)
    if selected is None:
        errors.append("selected_option_id must reference an option")
    elif not selected["sufficient"]:
        errors.append("selected option must be purpose_sufficient")
    if sufficient_options:
        minimum_burden = min(item[0] for item in sufficient_options)
        if selected is not None and selected["burden"] != minimum_burden:
            errors.append("selected option must have the lowest burden among purpose-sufficient options")
    if payload.get("palamedes_option_presumed") is not False:
        errors.append("palamedes_option_presumed must be false")
    if payload.get("self_expansion_score_used_as_beneficiary_value") is not False:
        errors.append("self_expansion_score_used_as_beneficiary_value must be false")
    if payload.get("rejection_of_mission_allowed") is not True:
        errors.append("rejection_of_mission_allowed must be true")
    expected_outcome = "mission_rejected" if selected and selected["type"] != "palamedes_mission" else "mission_accepted"
    if payload.get("mission_candidate_outcome") != expected_outcome:
        errors.append("mission_candidate_outcome must match the selected option")
    return {
        "valid": not errors,
        "errors": errors,
        "option_count": len(option_by_id),
        "selected_option_type": selected["type"] if selected else "",
        "mission_candidate_outcome": expected_outcome,
    }

def validate_creativity_diagnostic_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Measure useful frame distance and opened action without rewarding unsafe novelty."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["creativity diagnostic report must be an object"]}
    for field in (
        "creativity_report_id",
        "mission_candidate_id",
        "source_frame_id",
        "source_frame_fingerprint",
        "diagnostic_protocol_id",
        "report_fingerprint",
        "report_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    required_axes = {"beneficiary", "causal_model", "option_structure", "evaluation_question"}
    axes = payload.get("frame_distance_axes")
    if not isinstance(axes, list) or len(axes) != len(required_axes):
        errors.append("frame_distance_axes must contain exactly four diagnostic axes")
        axes = []
    seen_axes = set()
    distance_total = 0.0
    for index, axis in enumerate(axes):
        prefix = f"frame_distance_axes[{index}]"
        if not isinstance(axis, dict):
            errors.append(f"{prefix} must be an object")
            continue
        name = axis.get("axis")
        if name not in required_axes:
            errors.append(f"{prefix}.axis is not recognized")
        elif name in seen_axes:
            errors.append(f"{prefix}.axis must be unique")
        seen_axes.add(name)
        for field in ("source_frame", "candidate_frame", "relation_evidence", "distance_rationale"):
            if not _non_empty(axis.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        distance = axis.get("distance")
        if not isinstance(distance, (int, float)) or isinstance(distance, bool) or not 0 <= distance <= 1:
            errors.append(f"{prefix}.distance must be between zero and one")
            distance = 0
        distance_total += distance
    if seen_axes != required_axes:
        errors.append("frame_distance_axes must cover all four axes exactly once")
    actions = payload.get("opened_actions")
    if not isinstance(actions, list) or not actions:
        errors.append("opened_actions must be a non-empty list")
        actions = []
    seen_action_ids = set()
    useful_action_count = 0
    for index, action in enumerate(actions):
        prefix = f"opened_actions[{index}]"
        if not isinstance(action, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in (
            "action_id",
            "action",
            "previously_unreachable_because",
            "new_relation_that_opens_it",
            "evidence_or_probe",
        ):
            if not _non_empty(action.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        action_id = action.get("action_id")
        if action_id in seen_action_ids:
            errors.append(f"{prefix}.action_id must be unique")
        seen_action_ids.add(action_id)
        if action.get("was_reachable_under_source_frame") is not False:
            errors.append(f"{prefix}.was_reachable_under_source_frame must be false")
        useful = action.get("purpose_relevant_and_testable")
        if not isinstance(useful, bool):
            errors.append(f"{prefix}.purpose_relevant_and_testable must be boolean")
        useful_action_count += int(useful is True)
    gates = payload.get("non_compensable_gates")
    if not isinstance(gates, dict):
        errors.append("non_compensable_gates must be an object")
        gates = {}
    for field in ("constitutional_validity", "causal_coherence", "harm_boundary_passed"):
        if not isinstance(gates.get(field), bool):
            errors.append(f"non_compensable_gates.{field} must be boolean")
    eligible = all(gates.get(field) is True for field in (
        "constitutional_validity",
        "causal_coherence",
        "harm_boundary_passed",
    )) and useful_action_count > 0
    if payload.get("candidate_eligible") is not eligible:
        errors.append("candidate_eligible must require every non-compensable gate and an opened useful action")
    mean_distance = round(distance_total / len(required_axes), 12)
    declared = payload.get("declared_diagnostics")
    if not isinstance(declared, dict):
        errors.append("declared_diagnostics must be an object")
        declared = {}
    declared_mean_distance = declared.get("mean_frame_distance")
    if (
        not isinstance(declared_mean_distance, (int, float))
        or isinstance(declared_mean_distance, bool)
        or abs(declared_mean_distance - mean_distance) > 1e-12
    ):
        errors.append("declared_diagnostics.mean_frame_distance must equal axis mean")
    if declared.get("opened_action_count") != len(actions):
        errors.append("declared_diagnostics.opened_action_count must equal opened actions")
    if declared.get("useful_opened_action_count") != useful_action_count:
        errors.append("declared_diagnostics.useful_opened_action_count must equal useful opened actions")
    if payload.get("creativity_used_as_selection_objective") is not False:
        errors.append("creativity_used_as_selection_objective must be false")
    if payload.get("creativity_compensates_for_failed_gate") is not False:
        errors.append("creativity_compensates_for_failed_gate must be false")
    if payload.get("novel_language_counts_without_opened_action") is not False:
        errors.append("novel_language_counts_without_opened_action must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "mean_frame_distance": mean_distance,
        "opened_action_count": len(actions),
        "useful_opened_action_count": useful_action_count,
        "candidate_eligible": eligible,
    }

def validate_initial_empirical_claim_boundary(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Authorize only measured quality or labor gains without worse violations or proxy harm."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["initial empirical claim boundary must be an object"]}
    for field in (
        "claim_boundary_id",
        "proof_dataset_id",
        "baseline_condition_id",
        "palamedes_condition_id",
        "evaluation_protocol_id",
        "evidence_bundle_fingerprint",
        "claim_text",
        "claim_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("equal_information_verified") is not True:
        errors.append("equal_information_verified must be true")
    quality = payload.get("quality_measurement")
    if not isinstance(quality, dict):
        errors.append("quality_measurement must be an object")
        quality = {}
    for field in ("metric_id", "metric_definition", "evidence_artifact_id"):
        if not _non_empty(quality.get(field)):
            errors.append(f"quality_measurement.{field} must be a non-empty string")
    baseline_quality = quality.get("baseline_value")
    palamedes_quality = quality.get("palamedes_value")
    if any(
        not isinstance(value, (int, float)) or isinstance(value, bool)
        for value in (baseline_quality, palamedes_quality)
    ):
        errors.append("quality measurements must be numeric")
        baseline_quality = palamedes_quality = 0
    higher_is_better = quality.get("higher_is_better")
    if not isinstance(higher_is_better, bool):
        errors.append("quality_measurement.higher_is_better must be boolean")
    quality_delta = (
        palamedes_quality - baseline_quality
        if higher_is_better is True
        else baseline_quality - palamedes_quality
    )
    declared_quality_delta = quality.get("improvement_delta")
    if (
        not isinstance(declared_quality_delta, (int, float))
        or isinstance(declared_quality_delta, bool)
        or abs(declared_quality_delta - quality_delta) > 1e-12
    ):
        errors.append("quality_measurement.improvement_delta must equal direction-adjusted difference")
    labor = payload.get("labor_measurement")
    if not isinstance(labor, dict):
        errors.append("labor_measurement must be an object")
        labor = {}
    for field in ("labor_definition", "evidence_artifact_id"):
        if not _non_empty(labor.get(field)):
            errors.append(f"labor_measurement.{field} must be a non-empty string")
    baseline_minutes = labor.get("baseline_minutes")
    palamedes_minutes = labor.get("palamedes_minutes")
    if any(
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or value < 0
        for value in (baseline_minutes, palamedes_minutes)
    ):
        errors.append("labor measurements must be non-negative numbers")
        baseline_minutes = palamedes_minutes = 0
    retired_minutes = baseline_minutes - palamedes_minutes
    if labor.get("retired_minutes") != retired_minutes:
        errors.append("labor_measurement.retired_minutes must equal baseline minus Palamedes minutes")
    safeguards = payload.get("safeguard_comparison")
    if not isinstance(safeguards, dict):
        errors.append("safeguard_comparison must be an object")
        safeguards = {}
    comparison_values = {}
    for field in (
        "baseline_constitutional_violation_count",
        "palamedes_constitutional_violation_count",
        "baseline_proxy_harm_count",
        "palamedes_proxy_harm_count",
    ):
        value = safeguards.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            errors.append(f"safeguard_comparison.{field} must be a non-negative integer")
            value = 0
        comparison_values[field] = value
    safeguards_not_worse = (
        comparison_values["palamedes_constitutional_violation_count"]
        <= comparison_values["baseline_constitutional_violation_count"]
        and comparison_values["palamedes_proxy_harm_count"]
        <= comparison_values["baseline_proxy_harm_count"]
    )
    if safeguards.get("not_worse") is not safeguards_not_worse:
        errors.append("safeguard_comparison.not_worse must equal both no-worse comparisons")
    quality_improved = quality_delta > 0
    labor_retired = retired_minutes > 0
    claim_supported = (
        payload.get("equal_information_verified") is True
        and (quality_improved or labor_retired)
        and safeguards_not_worse
    )
    expected_basis = (
        "quality_and_labor"
        if quality_improved and labor_retired
        else "quality_improvement"
        if quality_improved
        else "labor_retirement"
        if labor_retired
        else "none"
    )
    if payload.get("claim_basis") != expected_basis:
        errors.append("claim_basis must match measured positive evidence")
    if payload.get("claim_supported") is not claim_supported:
        errors.append("claim_supported must require a measured gain and no worse safeguards")
    if payload.get("startup_success_claimed") is not False:
        errors.append("startup_success_claimed must be false")
    if payload.get("general_superiority_claimed") is not False:
        errors.append("general_superiority_claimed must be false")
    if payload.get("unmeasured_dimensions_implied") is not False:
        errors.append("unmeasured_dimensions_implied must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "quality_improved": quality_improved,
        "labor_retired": labor_retired,
        "safeguards_not_worse": safeguards_not_worse,
        "claim_basis": expected_basis,
        "claim_supported": claim_supported,
    }

def validate_integrated_mission_metric_thesis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Expose seven non-substitutable proof dimensions under equal information."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["integrated mission metric thesis must be an object"]}
    for field in (
        "metric_thesis_id",
        "proof_dataset_id",
        "baseline_condition_id",
        "palamedes_condition_id",
        "measurement_protocol_id",
        "scorecard_fingerprint",
        "scorecard_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("equal_information_verified") is not True:
        errors.append("equal_information_verified must be true")
    required_dimensions = {
        "mission_consequence",
        "retired_cognition",
        "compute",
        "total_human_labor",
        "calibration",
        "harm",
        "replaceability",
    }
    dimensions = payload.get("dimensions")
    if not isinstance(dimensions, list) or len(dimensions) != len(required_dimensions):
        errors.append("dimensions must contain exactly seven metric-thesis dimensions")
        dimensions = []
    seen = set()
    disqualifying = []
    for index, dimension in enumerate(dimensions):
        prefix = f"dimensions[{index}]"
        if not isinstance(dimension, dict):
            errors.append(f"{prefix} must be an object")
            continue
        name = dimension.get("dimension")
        if name not in required_dimensions:
            errors.append(f"{prefix}.dimension is not recognized")
        elif name in seen:
            errors.append(f"{prefix}.dimension must be unique")
        seen.add(name)
        for field in (
            "metric_definition",
            "unit",
            "baseline_evidence_artifact_id",
            "palamedes_evidence_artifact_id",
            "measurement_rationale",
        ):
            if not _non_empty(dimension.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        for field in ("baseline_value", "palamedes_value"):
            value = dimension.get(field)
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                errors.append(f"{prefix}.{field} must be numeric")
        if dimension.get("direction") not in {"higher_better", "lower_better", "diagnostic_only"}:
            errors.append(f"{prefix}.direction is not recognized")
        if dimension.get("reported_separately") is not True:
            errors.append(f"{prefix}.reported_separately must be true")
        disqualification = dimension.get("disqualifying_boundary_crossed")
        if not isinstance(disqualification, bool):
            errors.append(f"{prefix}.disqualifying_boundary_crossed must be boolean")
        elif disqualification:
            disqualifying.append(name)
    if seen != required_dimensions:
        errors.append("dimensions must cover every metric-thesis dimension exactly once")
    constitutional_count = payload.get("constitutional_violation_count")
    if not isinstance(constitutional_count, int) or isinstance(constitutional_count, bool) or constitutional_count < 0:
        errors.append("constitutional_violation_count must be a non-negative integer")
        constitutional_count = 0
    evidence_eligible = (
        payload.get("equal_information_verified") is True
        and constitutional_count == 0
        and not disqualifying
    )
    if payload.get("evidence_eligible") is not evidence_eligible:
        errors.append("evidence_eligible must require equal information and no disqualifying boundary")
    if payload.get("single_composite_score_authoritative") is not False:
        errors.append("single_composite_score_authoritative must be false")
    if payload.get("compute_or_labor_hidden") is not False:
        errors.append("compute_or_labor_hidden must be false")
    if payload.get("harm_nettable_against_benefit") is not False:
        errors.append("harm_nettable_against_benefit must be false")
    if payload.get("replaceability_omitted") is not False:
        errors.append("replaceability_omitted must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "dimension_count": len(seen),
        "disqualifying_dimensions": disqualifying,
        "evidence_eligible": evidence_eligible,
    }

def validate_experimental_contract_stable_state_isolation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Verify experimental-state migration preserves stable plan semantics and identifiers."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["experimental contract isolation report must be an object"]}
    for field in (
        "isolation_report_id",
        "stable_plan_schema_version",
        "stable_plan_fingerprint_before",
        "stable_plan_fingerprint_after",
        "migration_evidence_artifact_id",
        "report_fingerprint",
        "report_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    before = payload.get("stable_core_before")
    after = payload.get("stable_core_after")
    if not isinstance(before, dict) or not isinstance(after, dict):
        errors.append("stable_core_before and stable_core_after must be objects")
        before = before if isinstance(before, dict) else {}
        after = after if isinstance(after, dict) else {}
    if before != after:
        errors.append("stable core semantics must remain byte-equivalent after experimental migration")
    if payload.get("stable_plan_fingerprint_before") != payload.get("stable_plan_fingerprint_after"):
        errors.append("stable plan fingerprint must not change during experimental migration")
    source = payload.get("experimental_source_state")
    migrated = payload.get("experimental_migrated_state")
    if not isinstance(source, dict) or not isinstance(migrated, dict):
        errors.append("experimental source and migrated states must be objects")
        source = source if isinstance(source, dict) else {}
        migrated = migrated if isinstance(migrated, dict) else {}
    try:
        recomputed = migrate_experimental_mission_state(source)
    except (TypeError, ValueError) as exc:
        errors.append(f"experimental migration failed: {exc}")
        recomputed = {}
    if migrated != recomputed:
        errors.append("experimental_migrated_state must equal deterministic migration output")
    if migrated:
        try:
            if migrate_experimental_mission_state(migrated) != migrated:
                errors.append("experimental migration must be idempotent")
        except (TypeError, ValueError) as exc:
            errors.append(f"migrated state cannot be migrated again: {exc}")
    stable_reference = migrated.get("stable_plan_reference", {}) if isinstance(migrated, dict) else {}
    if stable_reference.get("schema_version") != payload.get("stable_plan_schema_version"):
        errors.append("experimental stable-plan reference must match stable schema version")
    if stable_reference.get("fingerprint") != payload.get("stable_plan_fingerprint_before"):
        errors.append("experimental stable-plan reference must match stable fingerprint")
    if payload.get("experimental_payload_embedded_in_stable_plan") is not False:
        errors.append("experimental_payload_embedded_in_stable_plan must be false")
    if payload.get("stable_migration_function_changed") is not False:
        errors.append("stable_migration_function_changed must be false")
    if payload.get("stable_schema_required_fields_changed") is not False:
        errors.append("stable_schema_required_fields_changed must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "experimental_contract_version": migrated.get("experimental_contract_version", ""),
        "stable_core_preserved": before == after,
        "migration_idempotent": bool(migrated and recomputed == migrated),
    }

def validate_idempotent_frozen_tournament_resume(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Verify resume preserves frozen candidates and only schedules unfinished judgments."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["frozen tournament resume report must be an object"]}
    for field in (
        "resume_report_id",
        "candidate_set_fingerprint_before",
        "candidate_set_fingerprint_after",
        "resume_evidence_artifact_id",
        "report_fingerprint",
        "report_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    source = payload.get("partial_tournament_state")
    resumed = payload.get("resumed_tournament_state")
    if not isinstance(source, dict) or not isinstance(resumed, dict):
        errors.append("partial and resumed tournament states must be objects")
        source = source if isinstance(source, dict) else {}
        resumed = resumed if isinstance(resumed, dict) else {}
    try:
        expected = resume_frozen_candidate_tournament(source)
    except (TypeError, ValueError) as exc:
        errors.append(f"tournament resume failed: {exc}")
        expected = {}
    if resumed != expected:
        errors.append("resumed_tournament_state must equal deterministic resume output")
    if resumed:
        try:
            if resume_frozen_candidate_tournament(resumed) != resumed:
                errors.append("tournament resume must be idempotent")
        except (TypeError, ValueError) as exc:
            errors.append(f"resumed tournament cannot resume again: {exc}")
    if source.get("candidates") != resumed.get("candidates"):
        errors.append("frozen candidates must remain unchanged on resume")
    if payload.get("candidate_set_fingerprint_before") != payload.get("candidate_set_fingerprint_after"):
        errors.append("candidate set fingerprint must remain unchanged")
    if resumed.get("candidate_set_fingerprint") != payload.get("candidate_set_fingerprint_before"):
        errors.append("resumed candidate fingerprint must match frozen fingerprint")
    if payload.get("candidate_generation_invoked_on_resume") is not False:
        errors.append("candidate_generation_invoked_on_resume must be false")
    if payload.get("completed_judgments_recomputed") is not False:
        errors.append("completed_judgments_recomputed must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "candidate_count": len(resumed.get("candidates", [])) if isinstance(resumed, dict) else 0,
        "pending_candidate_ids": resumed.get("pending_candidate_ids", []) if isinstance(resumed, dict) else [],
        "resume_idempotent": bool(resumed and resumed == expected),
    }

def validate_provider_timeout_frontier_preservation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Verify a provider timeout records unavailability without changing the tournament."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["provider timeout frontier report must be an object"]}
    for field in (
        "timeout_report_id",
        "candidate_set_fingerprint_before",
        "candidate_set_fingerprint_after",
        "report_fingerprint",
        "report_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    timeout_input = payload.get("timeout_input")
    timeout_record = payload.get("timeout_record")
    if not isinstance(timeout_input, dict) or not isinstance(timeout_record, dict):
        errors.append("timeout_input and timeout_record must be objects")
        timeout_input = timeout_input if isinstance(timeout_input, dict) else {}
        timeout_record = timeout_record if isinstance(timeout_record, dict) else {}
    try:
        expected = record_tournament_provider_timeout(timeout_input)
    except (TypeError, ValueError) as exc:
        errors.append(f"provider timeout recording failed: {exc}")
        expected = {}
    if timeout_record != expected:
        errors.append("timeout_record must equal deterministic unavailable-operation record")
    tournament = timeout_input.get("tournament_state", {})
    source_candidates = tournament.get("candidates", []) if isinstance(tournament, dict) else []
    if timeout_record.get("candidates") != source_candidates:
        errors.append("timeout record must preserve the frozen candidate frontier")
    if payload.get("candidate_set_fingerprint_before") != payload.get("candidate_set_fingerprint_after"):
        errors.append("candidate set fingerprint must remain unchanged after timeout")
    if timeout_record.get("candidate_set_fingerprint") != payload.get("candidate_set_fingerprint_before"):
        errors.append("timeout record must preserve candidate set fingerprint")
    if timeout_record.get("operation_status") != "unavailable":
        errors.append("timed out operation must be unavailable")
    if timeout_record.get("selection_status") != "blocked_no_selection":
        errors.append("selection must remain blocked after timeout")
    if timeout_record.get("selected_candidate_id") not in ("", None):
        errors.append("selected_candidate_id must remain empty after timeout")
    if timeout_record.get("timed_out_candidate_disqualified") is not False:
        errors.append("timed out candidate must not be disqualified")
    if timeout_record.get("remaining_candidate_auto_selected") is not False:
        errors.append("remaining candidate must not be auto-selected")
    return {
        "valid": not errors,
        "errors": errors,
        "operation_status": timeout_record.get("operation_status", ""),
        "selection_status": timeout_record.get("selection_status", ""),
        "frontier_preserved": timeout_record.get("candidates") == source_candidates,
    }

def validate_invalid_structured_output_quarantine(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Verify invalid output remains quarantined with deterministic bounded retries."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["invalid output quarantine report must be an object"]}
    for field in ("quarantine_report_id", "report_fingerprint", "report_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    quarantine_input = payload.get("quarantine_input")
    quarantine_record = payload.get("quarantine_record")
    if not isinstance(quarantine_input, dict) or not isinstance(quarantine_record, dict):
        errors.append("quarantine_input and quarantine_record must be objects")
        quarantine_input = quarantine_input if isinstance(quarantine_input, dict) else {}
        quarantine_record = quarantine_record if isinstance(quarantine_record, dict) else {}
    try:
        expected = quarantine_invalid_structured_output(quarantine_input)
    except (TypeError, ValueError) as exc:
        errors.append(f"invalid output quarantine failed: {exc}")
        expected = {}
    if quarantine_record != expected:
        errors.append("quarantine_record must equal deterministic quarantine output")
    if quarantine_record.get("canonical_state_fingerprint_before") != quarantine_record.get(
        "canonical_state_fingerprint_after"
    ):
        errors.append("canonical state fingerprint must not change")
    if quarantine_record.get("invalid_output_promoted_to_canonical") is not False:
        errors.append("invalid output must not be promoted to canonical state")
    if quarantine_record.get("raw_output_embedded_in_canonical") is not False:
        errors.append("raw invalid output must not be embedded in canonical state")
    history = quarantine_record.get("retry_history", [])
    maximum = quarantine_record.get("maximum_attempts", 0)
    if not isinstance(history, list) or len(history) > maximum:
        errors.append("retry history must remain within maximum_attempts")
    expected_retry = (
        isinstance(quarantine_record.get("attempt_number"), int)
        and quarantine_record.get("attempt_number") < maximum
    )
    if quarantine_record.get("retry_allowed") is not expected_retry:
        errors.append("retry_allowed must reflect the bounded attempt count")
    expected_status = "retryable" if expected_retry else "retry_exhausted"
    if quarantine_record.get("quarantine_status") != expected_status:
        errors.append("quarantine_status must match bounded retry state")
    return {
        "valid": not errors,
        "errors": errors,
        "quarantine_status": quarantine_record.get("quarantine_status", ""),
        "retry_history_count": len(history) if isinstance(history, list) else 0,
        "canonical_state_preserved": quarantine_record.get("canonical_state_fingerprint_before")
        == quarantine_record.get("canonical_state_fingerprint_after"),
    }

def validate_scoped_constitution_conflict_blocking(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Verify only unsafe affected actions stop while safe and unrelated work continues."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["scoped constitution conflict report must be an object"]}
    for field in ("scope_report_id", "report_fingerprint", "report_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    scope_input = payload.get("scope_input")
    scope_record = payload.get("scope_record")
    if not isinstance(scope_input, dict) or not isinstance(scope_record, dict):
        errors.append("scope_input and scope_record must be objects")
        scope_input = scope_input if isinstance(scope_input, dict) else {}
        scope_record = scope_record if isinstance(scope_record, dict) else {}
    try:
        expected = scope_constitution_conflict_actions(scope_input)
    except (TypeError, ValueError) as exc:
        errors.append(f"constitution conflict scoping failed: {exc}")
        expected = {}
    if scope_record != expected:
        errors.append("scope_record must equal deterministic action-level conflict routing")
    if scope_record.get("global_freeze") is not False:
        errors.append("global_freeze must be false")
    decisions = scope_record.get("action_decisions", [])
    if not isinstance(decisions, list):
        errors.append("action_decisions must be an array")
        decisions = []
    allowed_statuses = {
        "continue_unaffected",
        "continue_safe_exploration",
        "blocked_constitution_conflict",
    }
    for index, decision in enumerate(decisions):
        if not isinstance(decision, dict) or decision.get("status") not in allowed_statuses:
            errors.append(f"action_decisions[{index}] has invalid status")
    input_mission_ids = {
        action.get("mission_id")
        for action in scope_input.get("actions", [])
        if isinstance(action, dict) and _non_empty(action.get("mission_id"))
    }
    output_mission_ids = set(scope_record.get("blocked_mission_ids", [])) | set(
        scope_record.get("unaffected_mission_ids", [])
    )
    if output_mission_ids != input_mission_ids:
        errors.append("scope record must account for every mission")
    return {
        "valid": not errors,
        "errors": errors,
        "blocked_action_count": len(scope_record.get("blocked_action_ids", [])),
        "safe_exploration_action_count": len(scope_record.get("safe_exploration_action_ids", [])),
        "unaffected_action_count": len(scope_record.get("unaffected_action_ids", [])),
        "global_freeze": scope_record.get("global_freeze"),
    }

def validate_stale_mission_write_conflict(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Verify stale writes fail without mutation and identify the frontier-changing wake."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["stale mission write report must be an object"]}
    for field in ("write_report_id", "report_fingerprint", "report_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    write_request = payload.get("write_request")
    write_resolution = payload.get("write_resolution")
    if not isinstance(write_request, dict) or not isinstance(write_resolution, dict):
        errors.append("write_request and write_resolution must be objects")
        write_request = write_request if isinstance(write_request, dict) else {}
        write_resolution = write_resolution if isinstance(write_resolution, dict) else {}
    try:
        expected = resolve_mission_write_fingerprint(write_request)
    except (TypeError, ValueError) as exc:
        errors.append(f"mission write resolution failed: {exc}")
        expected = {}
    if write_resolution != expected:
        errors.append("write_resolution must equal fingerprint conflict resolution")
    stale = write_request.get("expected_frontier_fingerprint") != write_request.get(
        "current_frontier_fingerprint"
    )
    expected_status = "stale_write_conflict" if stale else "accepted"
    if write_resolution.get("write_status") != expected_status:
        errors.append("write_status must follow expected/current fingerprint equality")
    if stale:
        if write_resolution.get("write_applied") is not False:
            errors.append("stale write must not be applied")
        if write_resolution.get("canonical_mission_fingerprint_after") != write_request.get(
            "current_frontier_fingerprint"
        ):
            errors.append("stale write must preserve current canonical fingerprint")
        if not isinstance(write_resolution.get("newer_wake"), dict) or not write_resolution.get("newer_wake"):
            errors.append("stale conflict must expose the newer wake")
        if write_resolution.get("rebase_required") is not True:
            errors.append("stale conflict must require rebase")
    return {
        "valid": not errors,
        "errors": errors,
        "write_status": write_resolution.get("write_status", ""),
        "write_applied": write_resolution.get("write_applied"),
        "newer_wake_id": write_resolution.get("newer_wake", {}).get("wake_id", "")
        if isinstance(write_resolution.get("newer_wake"), dict)
        else "",
    }

def validate_selection_restore_outcome_preservation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Verify selection rollback cannot erase or rewrite later observations."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["selection restore outcome report must be an object"]}
    for field in ("restore_report_id", "report_fingerprint", "report_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    restore_input = payload.get("restore_input")
    restore_record = payload.get("restore_record")
    if not isinstance(restore_input, dict) or not isinstance(restore_record, dict):
        errors.append("restore_input and restore_record must be objects")
        restore_input = restore_input if isinstance(restore_input, dict) else {}
        restore_record = restore_record if isinstance(restore_record, dict) else {}
    try:
        expected = restore_selection_preserving_outcomes(restore_input)
    except (TypeError, ValueError) as exc:
        errors.append(f"selection restore failed: {exc}")
        expected = {}
    if restore_record != expected:
        errors.append("restore_record must equal deterministic selection-only restore")
    source = restore_input.get("current_outcome_observations", [])
    restored = restore_record.get("outcome_observations", [])
    source_identity = [
        (
            item.get("observation_id"),
            item.get("observation_fingerprint"),
            item.get("source_selection_revision_id"),
        )
        for item in source
        if isinstance(item, dict)
    ]
    restored_identity = [
        (
            item.get("observation_id"),
            item.get("observation_fingerprint"),
            item.get("source_selection_revision_id"),
        )
        for item in restored
        if isinstance(item, dict)
    ]
    if source_identity != restored_identity:
        errors.append("restore must preserve outcome order, fingerprints, and source selection revisions")
    if restore_record.get("outcome_observation_count_before") != restore_record.get(
        "outcome_observation_count_after"
    ):
        errors.append("restore must preserve outcome observation count")
    if restore_record.get("outcomes_deleted_by_restore") is not False:
        errors.append("outcomes_deleted_by_restore must be false")
    if restore_record.get("later_outcomes_reassigned_to_restored_selection") is not False:
        errors.append("later outcomes must not be reassigned to restored selection")
    return {
        "valid": not errors,
        "errors": errors,
        "restored_selection_revision_id": restore_record.get("restored_selection_revision_id", ""),
        "outcome_observation_count": len(restored) if isinstance(restored, list) else 0,
        "later_outcome_observation_ids": restore_record.get("later_outcome_observation_ids", []),
        "outcome_ledger_preserved": source_identity == restored_identity,
    }

def validate_sensitive_prompt_context_policy_gate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Verify prompt context is policy-evaluated and redaction decisions are auditable."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["sensitive prompt context report must be an object"]}
    for field in ("context_report_id", "report_fingerprint", "report_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    context_input = payload.get("context_input")
    context_record = payload.get("context_record")
    if not isinstance(context_input, dict) or not isinstance(context_record, dict):
        errors.append("context_input and context_record must be objects")
        context_input = context_input if isinstance(context_input, dict) else {}
        context_record = context_record if isinstance(context_record, dict) else {}
    try:
        expected = build_policy_gated_prompt_context(context_input)
    except (TypeError, ValueError) as exc:
        errors.append(f"prompt context policy evaluation failed: {exc}")
        expected = {}
    if context_record != expected:
        errors.append("context_record must equal deterministic policy-gated prompt context")
    if context_record.get("unevaluated_context_count") != 0:
        errors.append("unevaluated_context_count must be zero")
    if context_record.get("raw_confidential_or_restricted_content_embedded") is not False:
        errors.append("raw sensitive context must not be embedded")
    decisions = {
        item.get("context_item_id"): item.get("decision")
        for item in context_record.get("audit_decisions", [])
        if isinstance(item, dict)
    }
    prompt_ids = {
        item.get("context_item_id")
        for item in context_record.get("prompt_items", [])
        if isinstance(item, dict)
    }
    denied_ids = {item_id for item_id, decision in decisions.items() if decision == "deny"}
    if prompt_ids & denied_ids:
        errors.append("denied context must not enter prompt_items")
    return {
        "valid": not errors,
        "errors": errors,
        "prompt_item_count": len(context_record.get("prompt_items", [])),
        "audit_decision_count": len(context_record.get("audit_decisions", [])),
        "prompt_assembly_status": context_record.get("prompt_assembly_status", ""),
    }

def validate_reconstructable_external_action_kill_switch(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Verify external action stops without erasing state or granting self-reactivation."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["external action kill switch report must be an object"]}
    for field in ("kill_switch_report_id", "report_fingerprint", "report_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    activation_input = payload.get("activation_input")
    activation_record = payload.get("activation_record")
    if not isinstance(activation_input, dict) or not isinstance(activation_record, dict):
        errors.append("activation_input and activation_record must be objects")
        activation_input = activation_input if isinstance(activation_input, dict) else {}
        activation_record = activation_record if isinstance(activation_record, dict) else {}
    try:
        expected = activate_external_action_kill_switch(activation_input)
    except (TypeError, ValueError) as exc:
        errors.append(f"kill switch activation failed: {exc}")
        expected = {}
    if activation_record != expected:
        errors.append("activation_record must equal deterministic kill-switch output")
    if activation_record.get("external_action_dispatch_enabled") is not False:
        errors.append("external action dispatch must be disabled")
    if activation_record.get("state_deleted") is not False:
        errors.append("kill switch must retain state")
    if activation_record.get("palamedes_can_self_reenable") is not False:
        errors.append("Palamedes must not self-reactivate")
    if activation_record.get("reenable_requires_external_authority") is not True:
        errors.append("reenable must require external authority")
    if any(
        not isinstance(item, dict) or item.get("record_retained") is not True
        for item in activation_record.get("action_records", [])
    ):
        errors.append("every action record must be retained")
    if any(
        not isinstance(item, dict) or item.get("retained_for_reconstruction") is not True
        for item in activation_record.get("retained_state_artifacts", [])
    ):
        errors.append("every state artifact must be retained for reconstruction")
    return {
        "valid": not errors,
        "errors": errors,
        "stopped_external_action_count": len(activation_record.get("stopped_external_action_ids", [])),
        "continuing_observation_count": len(
            activation_record.get("continuing_internal_observation_ids", [])
        ),
        "retained_artifact_count": len(activation_record.get("retained_state_artifacts", [])),
        "external_action_dispatch_enabled": activation_record.get("external_action_dispatch_enabled"),
    }

def validate_failure_thesis_integration(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Verify failure closes commitment but leaves only bounded observation open."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["failure thesis report must be an object"]}
    for field in ("failure_report_id", "report_fingerprint", "report_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    failure_input = payload.get("failure_input")
    failure_record = payload.get("failure_record")
    if not isinstance(failure_input, dict) or not isinstance(failure_record, dict):
        errors.append("failure_input and failure_record must be objects")
        failure_input = failure_input if isinstance(failure_input, dict) else {}
        failure_record = failure_record if isinstance(failure_record, dict) else {}
    try:
        expected = apply_failure_thesis(failure_input)
    except (TypeError, ValueError) as exc:
        errors.append(f"failure thesis application failed: {exc}")
        expected = {}
    if failure_record != expected:
        errors.append("failure_record must equal deterministic failure routing")
    if failure_record.get("mission_commitment_gate") != "closed":
        errors.append("mission commitment gate must be closed")
    if failure_record.get("external_effect_gate") != "closed":
        errors.append("external effect gate must be closed")
    if failure_record.get("observation_gate") != "bounded_open":
        errors.append("observation gate must be bounded_open")
    if failure_record.get("contradictory_evidence_count_before") != failure_record.get(
        "contradictory_evidence_count_after"
    ):
        errors.append("contradictory evidence count must be preserved")
    if failure_record.get("consistency_repaired_by_evidence_deletion") is not False:
        errors.append("consistency must not be repaired by deleting evidence")
    for index, evidence in enumerate(failure_record.get("preserved_contradictory_evidence", [])):
        if not isinstance(evidence, dict) or evidence.get("preserved") is not True:
            errors.append(f"preserved_contradictory_evidence[{index}] must remain preserved")
        if isinstance(evidence, dict) and evidence.get("deleted_for_consistency") is not False:
            errors.append(f"preserved_contradictory_evidence[{index}] must not be deleted")
    return {
        "valid": not errors,
        "errors": errors,
        "mission_commitment_gate": failure_record.get("mission_commitment_gate", ""),
        "observation_gate": failure_record.get("observation_gate", ""),
        "allowed_observation_count": sum(
            isinstance(item, dict) and item.get("status") == "allowed_bounded_observation"
            for item in failure_record.get("operation_decisions", [])
        ),
        "preserved_contradiction_count": len(
            failure_record.get("preserved_contradictory_evidence", [])
        ),
    }

def validate_bounded_signal_to_mission_vertical_slice(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Verify the implemented slice ends before execution and admits linked outcomes."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["bounded vertical slice report must be an object"]}
    for field in ("slice_report_id", "report_fingerprint", "report_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    slice_input = payload.get("slice_input")
    slice_record = payload.get("slice_record")
    if not isinstance(slice_input, dict) or not isinstance(slice_record, dict):
        errors.append("slice_input and slice_record must be objects")
        slice_input = slice_input if isinstance(slice_input, dict) else {}
        slice_record = slice_record if isinstance(slice_record, dict) else {}
    try:
        expected = run_bounded_signal_to_mission_vertical_slice(slice_input)
    except (TypeError, ValueError) as exc:
        errors.append(f"vertical slice failed: {exc}")
        expected = {}
    if slice_record != expected:
        errors.append("slice_record must equal deterministic vertical-slice output")
    if slice_record.get("authority_endpoint") != "mission_contract_and_outcome_intake":
        errors.append("authority must end at mission contract and outcome intake")
    if slice_record.get("execution_platform_capability") is not False:
        errors.append("vertical slice must not become an execution platform")
    if slice_record.get("execution_objects_emitted") != 0:
        errors.append("vertical slice must emit zero execution objects")
    expected_stages = [
        slice_record.get("signal", {}).get("signal_id"),
        slice_record.get("interpretation", {}).get("interpretation_id"),
        slice_record.get("selection", {}).get("selection_id"),
        slice_record.get("mission_contract", {}).get("mission_contract_id"),
    ]
    if slice_record.get("ordered_stage_ids") != expected_stages:
        errors.append("ordered_stage_ids must preserve signal-to-contract order")
    return {
        "valid": not errors,
        "errors": errors,
        "candidate_count": len(slice_record.get("mission_candidates", [])),
        "outcome_intake_count": len(slice_record.get("outcome_intake", [])),
        "authority_endpoint": slice_record.get("authority_endpoint", ""),
        "execution_objects_emitted": slice_record.get("execution_objects_emitted"),
    }

def validate_semantic_infrastructure_reuse_manifest(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Verify existing infrastructure is reused and new code stays semantic."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["semantic infrastructure reuse report must be an object"]}
    for field in ("reuse_report_id", "report_fingerprint", "report_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    manifest = payload.get("reuse_manifest")
    if not isinstance(manifest, dict):
        errors.append("reuse_manifest must be an object")
        manifest = {}
    expected = build_semantic_infrastructure_reuse_manifest()
    if manifest != expected:
        errors.append("reuse_manifest must match verified repository infrastructure")
    required_capabilities = {
        "revision",
        "fingerprint",
        "restore",
        "provider",
        "reference",
        "benchmark",
    }
    bindings = manifest.get("existing_bindings", [])
    seen = set()
    if not isinstance(bindings, list) or len(bindings) != len(required_capabilities):
        errors.append("existing_bindings must contain exactly six reusable capabilities")
        bindings = []
    for index, binding in enumerate(bindings):
        if not isinstance(binding, dict):
            errors.append(f"existing_bindings[{index}] must be an object")
            continue
        capability = binding.get("capability")
        if capability not in required_capabilities:
            errors.append(f"existing_bindings[{index}].capability is not recognized")
        elif capability in seen:
            errors.append(f"existing_bindings[{index}].capability must be unique")
        seen.add(capability)
        if binding.get("symbol_verified_present") is not True:
            errors.append(f"existing_bindings[{index}] must reference a present symbol")
        if binding.get("replacement_implemented") is not False:
            errors.append(f"existing_bindings[{index}] must not implement a replacement")
    if seen != required_capabilities:
        errors.append("existing_bindings must cover all reusable capabilities")
    scopes = manifest.get("new_implementation_scope", [])
    scope_domains = {
        item.get("domain")
        for item in scopes
        if isinstance(item, dict)
    } if isinstance(scopes, list) else set()
    if scope_domains != {"semantic_state", "cognition_order"} or len(scopes) != 2:
        errors.append("new implementation scope must be exactly semantic_state and cognition_order")
    for field in (
        "parallel_revision_store_created",
        "parallel_provider_stack_created",
        "parallel_reference_stack_created",
        "parallel_benchmark_stack_created",
        "autonomous_daemon_created",
    ):
        if manifest.get(field) is not False:
            errors.append(f"{field} must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "reused_capability_count": len(seen),
        "new_scope_domains": sorted(scope_domains),
        "all_symbols_verified": all(
            isinstance(item, dict) and item.get("symbol_verified_present") is True
            for item in bindings
        ),
    }

