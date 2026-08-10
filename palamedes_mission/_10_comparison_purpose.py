from __future__ import annotations

from typing import Any, Dict, List
from ._01_kinds_value import _non_empty


def validate_beneficiary_authenticity_assessment(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Estimate beneficiary authenticity without claiming synthetic behavior is impossible."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["beneficiary authenticity assessment must be an object"]}
    for field in (
        "authenticity_assessment_id",
        "beneficiary_claim_id",
        "behavior_cluster_id",
        "coordination_risk_evidence_id",
        "residual_uncertainty",
        "monitoring_trigger",
        "assessment_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("authenticity_guaranteed") is not False:
        errors.append("authenticity_guaranteed must be false")
    required_dimensions = {"identity", "cost", "recurrence", "independent_context"}
    dimensions = payload.get("authenticity_dimensions")
    if not isinstance(dimensions, list):
        errors.append("authenticity_dimensions must be a list")
        dimensions = []
    seen = set()
    strengths = []
    for index, dimension in enumerate(dimensions):
        prefix = f"authenticity_dimensions[{index}]"
        if not isinstance(dimension, dict):
            errors.append(f"{prefix} must be an object")
            continue
        name = dimension.get("dimension")
        if name not in required_dimensions:
            errors.append(f"{prefix}.dimension is not recognized")
        elif name in seen:
            errors.append(f"{prefix}.dimension must be unique")
        seen.add(name)
        for field in ("observation", "evidence_id", "limitation"):
            if not _non_empty(dimension.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        strength = dimension.get("strength")
        if (
            isinstance(strength, bool)
            or not isinstance(strength, (int, float))
            or not 0 <= strength <= 1
        ):
            errors.append(f"{prefix}.strength must be between 0 and 1")
        else:
            strengths.append(strength)
    if seen != required_dimensions:
        errors.append("authenticity_dimensions must cover identity, cost, recurrence, and independent context")
    coordination_risk = payload.get("coordinated_synthetic_behavior_risk")
    threshold = payload.get("provisional_weight_threshold")
    for field, value in (
        ("coordinated_synthetic_behavior_risk", coordination_risk),
        ("provisional_weight_threshold", threshold),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not 0 <= value <= 1
        ):
            errors.append(f"{field} must be between 0 and 1")
    if not isinstance(coordination_risk, (int, float)) or isinstance(coordination_risk, bool):
        coordination_risk = 1
    mean_strength = sum(strengths) / len(strengths) if strengths else 0
    computed_confidence = mean_strength * (1 - coordination_risk)
    claimed = payload.get("provisional_authenticity_confidence")
    if (
        isinstance(claimed, bool)
        or not isinstance(claimed, (int, float))
        or abs(claimed - computed_confidence) > 1e-9
    ):
        errors.append("provisional_authenticity_confidence must match dimension strength and coordination risk")
    if not isinstance(threshold, (int, float)) or isinstance(threshold, bool):
        threshold = 1
    expected_decision = (
        "provisionally_weight"
        if computed_confidence >= threshold
        else "downweight_and_probe"
    )
    if payload.get("decision") != expected_decision:
        errors.append("decision must follow provisional authenticity confidence")
    return {
        "valid": not errors,
        "errors": errors,
        "provisional_authenticity_confidence": computed_confidence,
        "decision": expected_decision,
    }

def validate_direct_outcome_reporting_integrity(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require direct outcome channels and alerts for missing downstream reports."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["direct outcome reporting integrity must be an object"]}
    for field in (
        "reporting_integrity_id",
        "mission_id",
        "downstream_agent_id",
        "reporting_schedule_id",
        "alert_owner_id",
        "integrity_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("downstream_self_report_is_sufficient") is not False:
        errors.append("downstream_self_report_is_sufficient must be false")
    channels = payload.get("direct_outcome_channels")
    if not isinstance(channels, list) or not channels:
        errors.append("direct_outcome_channels must be a non-empty list")
        channels = []
    channel_ids = set()
    for index, channel in enumerate(channels):
        prefix = f"direct_outcome_channels[{index}]"
        if not isinstance(channel, dict):
            errors.append(f"{prefix} must be an object")
            continue
        channel_id = channel.get("channel_id")
        if not _non_empty(channel_id):
            errors.append(f"{prefix}.channel_id must be a non-empty string")
        elif channel_id in channel_ids:
            errors.append(f"{prefix}.channel_id must be unique")
        channel_ids.add(channel_id)
        for field in ("outcome_kind", "source", "custodian_id", "independence_evidence_id"):
            if not _non_empty(channel.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if channel.get("controlled_by_downstream_agent") is not False:
            errors.append(f"{prefix}.controlled_by_downstream_agent must be false")

    expected = payload.get("expected_reports")
    if not isinstance(expected, list) or not expected:
        errors.append("expected_reports must be a non-empty list")
        expected = []
    expected_ids = set()
    for index, report in enumerate(expected):
        prefix = f"expected_reports[{index}]"
        if not isinstance(report, dict):
            errors.append(f"{prefix} must be an object")
            continue
        report_id = report.get("report_id")
        if not _non_empty(report_id):
            errors.append(f"{prefix}.report_id must be a non-empty string")
        elif report_id in expected_ids:
            errors.append(f"{prefix}.report_id must be unique")
        expected_ids.add(report_id)
        for field in ("due_at", "required_outcome_kind"):
            if not _non_empty(report.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    received = payload.get("received_report_ids")
    if (
        not isinstance(received, list)
        or not all(_non_empty(item) for item in received)
        or len(received) != len(set(received))
        or any(item not in expected_ids for item in received)
    ):
        errors.append("received_report_ids must be unique expected report IDs")
        received = []
    missing_ids = sorted(expected_ids - set(received))
    alerts = payload.get("missing_report_alerts")
    if not isinstance(alerts, list):
        errors.append("missing_report_alerts must be a list")
        alerts = []
    alert_ids = []
    for index, alert in enumerate(alerts):
        prefix = f"missing_report_alerts[{index}]"
        if not isinstance(alert, dict):
            errors.append(f"{prefix} must be an object")
            continue
        report_id = alert.get("report_id")
        alert_ids.append(report_id)
        for field in ("alert_id", "report_id", "detected_at", "escalation_action"):
            if not _non_empty(alert.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if sorted(alert_ids) != missing_ids or len(alert_ids) != len(missing_ids):
        errors.append("missing_report_alerts must cover every and only missing report")
    observations = payload.get("direct_observations")
    if not isinstance(observations, list) or not observations:
        errors.append("direct_observations must be a non-empty list")
        observations = []
    for index, observation in enumerate(observations):
        prefix = f"direct_observations[{index}]"
        if not isinstance(observation, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("observation_id", "channel_id", "observed_outcome", "evidence_id", "observed_at"):
            if not _non_empty(observation.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if observation.get("channel_id") not in channel_ids:
            errors.append(f"{prefix}.channel_id must reference a direct outcome channel")
    return {
        "valid": not errors,
        "errors": errors,
        "missing_report_ids": missing_ids,
        "direct_channel_ids": sorted(channel_ids),
    }

def validate_hidden_harm_adversarial_criticism(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Search metric-compliant missions for displaced costs and unobserved parties."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["hidden harm adversarial criticism must be an object"]}
    for field in (
        "criticism_id",
        "mission_candidate_id",
        "claimed_metric",
        "claimed_metric_evidence_id",
        "critic_id",
        "decision_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("claimed_metric_met") is not True:
        errors.append("claimed_metric_met must be true for this adversarial review")
    if payload.get("metric_compliance_is_sufficient") is not False:
        errors.append("metric_compliance_is_sufficient must be false")
    required_searches = {"displaced_cost", "unobserved_party"}
    searches = payload.get("adversarial_searches")
    if not isinstance(searches, list):
        errors.append("adversarial_searches must be a list")
        searches = []
    seen = set()
    unresolved_harm_ids = []
    for index, search in enumerate(searches):
        prefix = f"adversarial_searches[{index}]"
        if not isinstance(search, dict):
            errors.append(f"{prefix} must be an object")
            continue
        search_type = search.get("search_type")
        if search_type not in required_searches:
            errors.append(f"{prefix}.search_type is not recognized")
        elif search_type in seen:
            errors.append(f"{prefix}.search_type must be unique")
        seen.add(search_type)
        for field in (
            "search_id",
            "adversarial_hypothesis",
            "search_method",
            "evidence_id",
            "searched_scope",
        ):
            if not _non_empty(search.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        harm_found = search.get("harm_found")
        if not isinstance(harm_found, bool):
            errors.append(f"{prefix}.harm_found must be boolean")
        status = search.get("harm_status")
        if harm_found:
            for field in ("affected_party_or_system", "harm_or_cost", "response"):
                if not _non_empty(search.get(field)):
                    errors.append(f"{prefix}.{field} is required when harm is found")
            if status not in {"resolved", "unresolved"}:
                errors.append(f"{prefix}.harm_status must be resolved or unresolved when harm is found")
            elif status == "unresolved":
                unresolved_harm_ids.append(search.get("search_id"))
            elif not _non_empty(search.get("mitigation_evidence_id")):
                errors.append(f"{prefix}.mitigation_evidence_id is required for resolved harm")
        elif status != "not_found":
            errors.append(f"{prefix}.harm_status must be not_found when no harm is found")
    if seen != required_searches:
        errors.append("adversarial_searches must cover displaced cost and unobserved party")
    expected_decision = (
        "revise_or_reject" if unresolved_harm_ids else "eligible_after_adversarial_review"
    )
    if payload.get("decision") != expected_decision:
        errors.append("decision must follow unresolved hidden harm findings")
    return {
        "valid": not errors,
        "errors": errors,
        "unresolved_harm_ids": unresolved_harm_ids,
        "decision": expected_decision,
    }

def validate_constitution_amendment_security(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Protect constitutional amendments with authority, visible diff, delay, and rollback."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["constitution amendment security must be an object"]}
    for field in (
        "amendment_security_id",
        "amendment_id",
        "constitution_id",
        "proposer_id",
        "amendment_authority_grant_id",
        "independent_ratifier_id",
        "amendment_rationale",
        "rationale_evidence_id",
        "diff_publication_id",
        "proposed_at",
        "activation_at",
        "security_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("authorization_verified") is not True:
        errors.append("authorization_verified must be true")
    if payload.get("self_granted_authority") is not False:
        errors.append("self_granted_authority must be false")
    if payload.get("proposer_id") == payload.get("independent_ratifier_id"):
        errors.append("independent_ratifier_id must differ from proposer_id")
    diffs = payload.get("visible_clause_diffs")
    if not isinstance(diffs, list) or not diffs:
        errors.append("visible_clause_diffs must be a non-empty list")
        diffs = []
    clause_ids = set()
    for index, diff in enumerate(diffs):
        prefix = f"visible_clause_diffs[{index}]"
        if not isinstance(diff, dict):
            errors.append(f"{prefix} must be an object")
            continue
        clause_id = diff.get("clause_id")
        if not _non_empty(clause_id):
            errors.append(f"{prefix}.clause_id must be a non-empty string")
        elif clause_id in clause_ids:
            errors.append(f"{prefix}.clause_id must be unique")
        clause_ids.add(clause_id)
        for field in ("before_text", "after_text", "change_rationale", "impact"):
            if not _non_empty(diff.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if diff.get("before_text") == diff.get("after_text"):
            errors.append(f"{prefix} must show an actual clause change")
    impact = payload.get("impact_level")
    if impact not in {"low", "high"}:
        errors.append("impact_level must be low or high")
    delay = payload.get("activation_delay_hours")
    minimum_delay = payload.get("minimum_high_impact_delay_hours")
    for field, value in (
        ("activation_delay_hours", delay),
        ("minimum_high_impact_delay_hours", minimum_delay),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or value < 0
        ):
            errors.append(f"{field} must be a non-negative number")
    if impact == "high":
        if (
            isinstance(delay, (int, float))
            and not isinstance(delay, bool)
            and isinstance(minimum_delay, (int, float))
            and not isinstance(minimum_delay, bool)
            and delay < minimum_delay
        ):
            errors.append("high-impact amendment activation delay is below the minimum")
        if payload.get("immediate_activation") is not False:
            errors.append("high-impact amendment immediate_activation must be false")
        rollback = payload.get("rollback_plan")
        if not isinstance(rollback, dict):
            errors.append("rollback_plan must be an object for high-impact amendment")
            rollback = {}
        for field in (
            "predecessor_snapshot_id",
            "rollback_trigger",
            "rollback_action",
            "rollback_authority_id",
            "verification_test",
        ):
            if not _non_empty(rollback.get(field)):
                errors.append(f"rollback_plan.{field} is required for high-impact amendment")
    return {
        "valid": not errors,
        "errors": errors,
        "impact_level": impact,
        "changed_clause_ids": sorted(clause_ids),
    }

def validate_aggregate_action_chain_consequences(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate constitutional consequences across a whole foreseeable action chain."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["aggregate action chain consequences must be an object"]}
    for field in (
        "chain_review_id",
        "mission_id",
        "constitution_id",
        "foreseeability_horizon",
        "review_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("stepwise_compliance_is_sufficient") is not False:
        errors.append("stepwise_compliance_is_sufficient must be false")
    steps = payload.get("action_steps")
    if not isinstance(steps, list) or len(steps) < 2:
        errors.append("action_steps must contain at least two ordered steps")
        steps = []
    step_ids = []
    for index, step in enumerate(steps):
        prefix = f"action_steps[{index}]"
        if not isinstance(step, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("step_id", "action", "immediate_consequence", "step_authority_id"):
            if not _non_empty(step.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if step.get("sequence") != index + 1:
            errors.append(f"{prefix}.sequence must match action order")
        if step.get("individually_permitted") is not True:
            errors.append(f"{prefix}.individually_permitted must be true for route-around review")
        dependencies = step.get("depends_on_step_ids")
        expected_dependencies = [] if index == 0 else [step_ids[-1]]
        if dependencies != expected_dependencies:
            errors.append(f"{prefix}.depends_on_step_ids must link the direct prior step")
        step_ids.append(step.get("step_id"))

    forecasts = payload.get("aggregate_forecasts")
    if not isinstance(forecasts, list) or not forecasts:
        errors.append("aggregate_forecasts must be a non-empty list")
        forecasts = []
    forecast_ids = set()
    for index, forecast in enumerate(forecasts):
        prefix = f"aggregate_forecasts[{index}]"
        if not isinstance(forecast, dict):
            errors.append(f"{prefix} must be an object")
            continue
        forecast_id = forecast.get("forecast_id")
        if not _non_empty(forecast_id):
            errors.append(f"{prefix}.forecast_id must be a non-empty string")
        elif forecast_id in forecast_ids:
            errors.append(f"{prefix}.forecast_id must be unique")
        forecast_ids.add(forecast_id)
        for field in (
            "affected_party_or_system",
            "cumulative_consequence",
            "time_horizon",
            "evidence_id",
        ):
            if not _non_empty(forecast.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        for field in ("likelihood", "severity"):
            value = forecast.get(field)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not 0 <= value <= 1
            ):
                errors.append(f"{prefix}.{field} must be between 0 and 1")

    evaluations = payload.get("prohibition_evaluations")
    if not isinstance(evaluations, list) or not evaluations:
        errors.append("prohibition_evaluations must be a non-empty list")
        evaluations = []
    violated_clause_ids = []
    for index, evaluation in enumerate(evaluations):
        prefix = f"prohibition_evaluations[{index}]"
        if not isinstance(evaluation, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("clause_id", "prohibition", "aggregate_application", "evidence_id"):
            if not _non_empty(evaluation.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        referenced = evaluation.get("forecast_ids")
        if (
            not isinstance(referenced, list)
            or not referenced
            or any(item not in forecast_ids for item in referenced)
        ):
            errors.append(f"{prefix}.forecast_ids must reference aggregate forecasts")
        verdict = evaluation.get("verdict")
        if verdict not in {"pass", "violate"}:
            errors.append(f"{prefix}.verdict must be pass or violate")
        elif verdict == "violate":
            violated_clause_ids.append(evaluation.get("clause_id"))
    expected_decision = "block_chain" if violated_clause_ids else "allow_chain"
    if payload.get("decision") != expected_decision:
        errors.append("decision must follow aggregate prohibition evaluations")
    return {
        "valid": not errors,
        "errors": errors,
        "violated_clause_ids": violated_clause_ids,
        "decision": expected_decision,
    }

def validate_ambiguity_flood_bounded_probe(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Preserve autonomy under ambiguity flooding through one safe bounded probe."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["ambiguity flood bounded probe must be an object"]}
    for field in (
        "ambiguity_review_id",
        "frontier_entry_id",
        "probe_id",
        "discriminating_observation",
        "safety_boundary",
        "starts_at",
        "expires_at",
        "stop_trigger",
        "review_authority_id",
        "decision_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("permanent_escalation") is not False:
        errors.append("permanent_escalation must be false")
    if payload.get("probe_reversible") is not True:
        errors.append("probe_reversible must be true")
    if payload.get("autonomy_preserved") is not True:
        errors.append("autonomy_preserved must be true")
    if (
        _non_empty(payload.get("starts_at"))
        and _non_empty(payload.get("expires_at"))
        and payload.get("expires_at") <= payload.get("starts_at")
    ):
        errors.append("expires_at must follow starts_at")

    ambiguities = payload.get("ambiguities")
    if not isinstance(ambiguities, list) or len(ambiguities) < 2:
        errors.append("ambiguities must contain at least two competing uncertainties")
        ambiguities = []
    ambiguity_ids = set()
    for index, ambiguity in enumerate(ambiguities):
        prefix = f"ambiguities[{index}]"
        if not isinstance(ambiguity, dict):
            errors.append(f"{prefix} must be an object")
            continue
        ambiguity_id = ambiguity.get("ambiguity_id")
        if not _non_empty(ambiguity_id):
            errors.append(f"{prefix}.ambiguity_id must be a non-empty string")
        elif ambiguity_id in ambiguity_ids:
            errors.append(f"{prefix}.ambiguity_id must be unique")
        ambiguity_ids.add(ambiguity_id)
        for field in ("claim", "source_id", "evidence_id", "decision_consequence"):
            if not _non_empty(ambiguity.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    resolved_ids = payload.get("probe_distinguishes_ambiguity_ids")
    if (
        not isinstance(resolved_ids, list)
        or set(resolved_ids) != ambiguity_ids
        or len(resolved_ids) != len(ambiguity_ids)
    ):
        errors.append("probe_distinguishes_ambiguity_ids must cover every ambiguity")
    values = {}
    for field in ("maximum_harm", "harm_ceiling", "probe_budget", "available_probe_budget"):
        value = payload.get(field)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or value < 0
        ):
            errors.append(f"{field} must be a non-negative number")
            value = 0
        values[field] = value
    if values["maximum_harm"] > values["harm_ceiling"]:
        errors.append("maximum_harm cannot exceed harm_ceiling")
    if values["probe_budget"] <= 0:
        errors.append("probe_budget must be positive")
    if values["probe_budget"] > values["available_probe_budget"]:
        errors.append("probe_budget cannot exceed available_probe_budget")
    if payload.get("decision") != "run_bounded_probe":
        errors.append("decision must be run_bounded_probe")
    return {
        "valid": not errors,
        "errors": errors,
        "ambiguity_ids": sorted(ambiguity_ids),
        "decision": "run_bounded_probe",
    }

def validate_minimized_access_controlled_provenance(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Minimize provenance, enforce access control, and hash-commit restricted content."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["minimized access controlled provenance must be an object"]}
    for field in ("provenance_policy_id", "audit_log_id", "policy_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("raw_sensitive_beneficiary_identifiers_logged") is not False:
        errors.append("raw_sensitive_beneficiary_identifiers_logged must be false")
    records = payload.get("provenance_records")
    if not isinstance(records, list) or len(records) < 2:
        errors.append("provenance_records must contain at least two records")
        records = []
    record_ids = set()
    allowed_roles = {}
    storage_modes = set()
    for index, record in enumerate(records):
        prefix = f"provenance_records[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix} must be an object")
            continue
        record_id = record.get("record_id")
        if not _non_empty(record_id):
            errors.append(f"{prefix}.record_id must be a non-empty string")
        elif record_id in record_ids:
            errors.append(f"{prefix}.record_id must be unique")
        record_ids.add(record_id)
        for field in (
            "provenance_kind",
            "collection_necessity",
            "minimization_rationale",
            "content_hash",
            "retention_until",
            "expiry_action",
        ):
            if not _non_empty(record.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        omitted = record.get("omitted_fields")
        if (
            not isinstance(omitted, list)
            or not omitted
            or not all(_non_empty(item) for item in omitted)
        ):
            errors.append(f"{prefix}.omitted_fields must be a non-empty string list")
        sensitivity = record.get("sensitivity")
        if sensitivity not in {"public", "internal", "confidential", "restricted"}:
            errors.append(f"{prefix}.sensitivity is not recognized")
        roles = record.get("allowed_role_ids")
        if (
            not isinstance(roles, list)
            or not roles
            or not all(_non_empty(item) for item in roles)
            or len(roles) != len(set(roles))
        ):
            errors.append(f"{prefix}.allowed_role_ids must be a non-empty unique string list")
            roles = []
        allowed_roles[record_id] = set(roles)
        mode = record.get("storage_mode")
        if mode not in {"minimized_content", "hash_only"}:
            errors.append(f"{prefix}.storage_mode is not recognized")
        else:
            storage_modes.add(mode)
        if sensitivity == "restricted" and mode != "hash_only":
            errors.append(f"{prefix} restricted provenance must use hash_only storage")
        content = record.get("stored_content")
        if mode == "hash_only":
            if content not in ("", None):
                errors.append(f"{prefix}.stored_content must be empty in hash_only mode")
        elif not _non_empty(content):
            errors.append(f"{prefix}.stored_content is required in minimized_content mode")
    if storage_modes != {"minimized_content", "hash_only"}:
        errors.append("provenance_records must demonstrate minimized_content and hash_only modes")

    accesses = payload.get("access_events")
    if not isinstance(accesses, list) or not accesses:
        errors.append("access_events must be a non-empty list")
        accesses = []
    for index, access in enumerate(accesses):
        prefix = f"access_events[{index}]"
        if not isinstance(access, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("access_id", "record_id", "requester_role_id", "requested_at"):
            if not _non_empty(access.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        record_id = access.get("record_id")
        if record_id not in record_ids:
            errors.append(f"{prefix}.record_id must reference a provenance record")
        expected_decision = (
            "allow"
            if access.get("requester_role_id") in allowed_roles.get(record_id, set())
            else "deny"
        )
        if access.get("decision") != expected_decision:
            errors.append(f"{prefix}.decision must follow record access control")
    return {
        "valid": not errors,
        "errors": errors,
        "storage_modes": sorted(storage_modes),
        "record_ids": sorted(record_ids),
    }

def validate_adversarial_purpose_formation_thesis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Integrate adversarial controls across evidence, authority, consequence, and lineage."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["adversarial purpose formation thesis must be an object"]}
    link_fields = (
        "adversarial_thesis_id",
        "runtime_thesis_id",
        "signal_priority_policy_id",
        "reference_boundary_policy_id",
        "beneficiary_authenticity_policy_id",
        "outcome_reporting_policy_id",
        "hidden_harm_policy_id",
        "amendment_security_policy_id",
        "aggregate_consequence_policy_id",
        "ambiguity_probe_policy_id",
        "provenance_policy_id",
        "lineage_commit_policy_id",
        "thesis_rationale",
    )
    for field in link_fields:
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    guarantees = {
        "source_incentives_discount_priority",
        "independent_sources_corroborate_priority",
        "reference_evidence_separated_from_authority",
        "beneficiary_authenticity_remains_provisional",
        "direct_outcome_channels_bypass_selective_reporting",
        "hidden_harm_searches_beyond_metrics",
        "constitutional_amendments_are_secured",
        "aggregate_action_consequences_are_evaluated",
        "ambiguity_flooding_uses_bounded_probes",
        "sensitive_provenance_is_minimized_and_controlled",
        "mission_lineage_is_fingerprint_guarded",
    }
    for guarantee in sorted(guarantees):
        if payload.get(guarantee) is not True:
            errors.append(f"{guarantee} must be true")
    layers = payload.get("adversarial_layers")
    expected_layers = {
        "signal_source",
        "reference",
        "beneficiary_model",
        "downstream_reporting",
        "mission_candidate",
        "constitution",
        "action_chain",
        "ambiguity",
        "provenance",
        "lineage",
    }
    if (
        not isinstance(layers, list)
        or set(layers) != expected_layers
        or len(layers) != len(expected_layers)
    ):
        errors.append("adversarial_layers must cover all ten protected layers")
    if payload.get("evidence_can_self_authorize") is not False:
        errors.append("evidence_can_self_authorize must be false")
    if payload.get("local_step_compliance_overrides_aggregate_harm") is not False:
        errors.append("local_step_compliance_overrides_aggregate_harm must be false")
    if payload.get("adversarial_decision") != "hardened":
        errors.append("adversarial_decision must be hardened")
    return {
        "valid": not errors,
        "errors": errors,
        "verified_guarantee_count": sum(payload.get(item) is True for item in guarantees),
        "adversarial_decision": payload.get("adversarial_decision"),
    }

def validate_single_evolving_signal_comparison_case(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Limit the first comparison system to one evolving signal case."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["single evolving signal comparison case must be an object"]}
    for field in (
        "comparison_system_id",
        "hypothesis_under_test",
        "success_criterion",
        "falsification_criterion",
        "scope_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("full_runtime_implemented") is not False:
        errors.append("full_runtime_implemented must be false")
    if payload.get("production_runtime_claimed") is not False:
        errors.append("production_runtime_claimed must be false")
    cases = payload.get("signal_cases")
    if not isinstance(cases, list) or len(cases) != 1:
        errors.append("signal_cases must contain exactly one evolving case")
        cases = []
    event_ids = set()
    event_times = []
    case_id = ""
    if cases:
        case = cases[0]
        if not isinstance(case, dict):
            errors.append("signal_cases[0] must be an object")
        else:
            case_id = case.get("case_id", "")
            for field in ("case_id", "initial_situation", "beneficiary_context", "source_bundle_id"):
                if not _non_empty(case.get(field)):
                    errors.append(f"signal_cases[0].{field} must be a non-empty string")
            events = case.get("events")
            if not isinstance(events, list) or len(events) < 2:
                errors.append("signal_cases[0].events must contain at least two evolving observations")
                events = []
            for index, event in enumerate(events):
                prefix = f"signal_cases[0].events[{index}]"
                if not isinstance(event, dict):
                    errors.append(f"{prefix} must be an object")
                    continue
                event_id = event.get("event_id")
                if not _non_empty(event_id):
                    errors.append(f"{prefix}.event_id must be a non-empty string")
                elif event_id in event_ids:
                    errors.append(f"{prefix}.event_id must be unique")
                event_ids.add(event_id)
                for field in ("observed_at", "observation", "evidence_id", "state_change"):
                    if not _non_empty(event.get(field)):
                        errors.append(f"{prefix}.{field} must be a non-empty string")
                event_times.append(event.get("observed_at"))
            if event_times and event_times != sorted(event_times):
                errors.append("signal case events must be ordered by observed_at")
    components = payload.get("implemented_components")
    expected_components = {"event_sequence", "condition_runner", "output_store"}
    if (
        not isinstance(components, list)
        or set(components) != expected_components
        or len(components) != len(expected_components)
    ):
        errors.append("implemented_components must contain only the minimum comparison components")
    excluded = payload.get("deferred_runtime_components")
    if (
        not isinstance(excluded, list)
        or not excluded
        or not all(_non_empty(item) for item in excluded)
    ):
        errors.append("deferred_runtime_components must name infrastructure excluded from the comparison")
    return {
        "valid": not errors,
        "errors": errors,
        "case_id": case_id,
        "event_count": len(event_ids),
    }

def validate_interpretation_mission_competition_case(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require a comparison case to create genuine interpretation and mission selection."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["interpretation mission competition case must be an object"]}
    for field in ("competition_design_id", "comparison_system_id", "case_id", "design_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")

    interpretations = payload.get("beneficiary_interpretations")
    if not isinstance(interpretations, list) or len(interpretations) < 2:
        errors.append("beneficiary_interpretations must contain at least two plausible interpretations")
        interpretations = []
    interpretation_ids = set()
    for index, interpretation in enumerate(interpretations):
        prefix = f"beneficiary_interpretations[{index}]"
        if not isinstance(interpretation, dict):
            errors.append(f"{prefix} must be an object")
            continue
        interpretation_id = interpretation.get("interpretation_id")
        if not _non_empty(interpretation_id):
            errors.append(f"{prefix}.interpretation_id must be a non-empty string")
        elif interpretation_id in interpretation_ids:
            errors.append(f"{prefix}.interpretation_id must be unique")
        else:
            interpretation_ids.add(interpretation_id)
        for field in (
            "beneficiary_population",
            "interpretation",
            "supporting_evidence_id",
            "disconfirming_observation",
        ):
            if not _non_empty(interpretation.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if interpretation.get("plausible") is not True:
            errors.append(f"{prefix}.plausible must be true")

    missions = payload.get("mission_candidates")
    if not isinstance(missions, list) or len(missions) < 3:
        errors.append("mission_candidates must contain at least three independently competing missions")
        missions = []
    mission_ids = set()
    external_conditions = set()
    theses = set()
    covered_interpretations = set()
    for index, mission in enumerate(missions):
        prefix = f"mission_candidates[{index}]"
        if not isinstance(mission, dict):
            errors.append(f"{prefix} must be an object")
            continue
        mission_id = mission.get("mission_id")
        if not _non_empty(mission_id):
            errors.append(f"{prefix}.mission_id must be a non-empty string")
        elif mission_id in mission_ids:
            errors.append(f"{prefix}.mission_id must be unique")
        else:
            mission_ids.add(mission_id)
        for field in (
            "mission",
            "changed_external_condition",
            "distinguishing_thesis",
            "supporting_evidence_id",
        ):
            if not _non_empty(mission.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if _non_empty(mission.get("changed_external_condition")):
            external_conditions.add(mission["changed_external_condition"])
        if _non_empty(mission.get("distinguishing_thesis")):
            theses.add(mission["distinguishing_thesis"])
        references = mission.get("beneficiary_interpretation_ids")
        if (
            not isinstance(references, list)
            or not references
            or not all(_non_empty(item) for item in references)
            or len(references) != len(set(references))
        ):
            errors.append(f"{prefix}.beneficiary_interpretation_ids must be a non-empty unique string list")
            references = []
        unknown = set(references) - interpretation_ids
        if unknown:
            errors.append(f"{prefix}.beneficiary_interpretation_ids must reference known interpretations")
        covered_interpretations.update(set(references) & interpretation_ids)
        if mission.get("independently_competing") is not True:
            errors.append(f"{prefix}.independently_competing must be true")

    if len(external_conditions) != len(missions):
        errors.append("mission candidates must propose distinct changed external conditions")
    if len(theses) != len(missions):
        errors.append("mission candidates must have distinct distinguishing theses")
    if interpretation_ids and covered_interpretations != interpretation_ids:
        errors.append("mission candidates must collectively cover every beneficiary interpretation")
    if payload.get("selection_required") is not True:
        errors.append("selection_required must be true")
    if payload.get("single_summary_is_sufficient") is not False:
        errors.append("single_summary_is_sufficient must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "interpretation_count": len(interpretation_ids),
        "mission_count": len(mission_ids),
        "covered_interpretation_ids": sorted(covered_interpretations),
    }

def validate_pre_exposure_constitution_authority_freeze(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Freeze normative and authority boundaries before comparison evidence is revealed."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["pre-exposure constitution authority freeze must be an object"]}
    for field in (
        "freeze_record_id",
        "comparison_system_id",
        "constitution_snapshot_id",
        "constitution_fingerprint",
        "authority_snapshot_id",
        "authority_fingerprint",
        "frozen_at",
        "signal_exposure_at",
        "candidate_generation_at",
        "freeze_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")

    principles = payload.get("constitutional_principles")
    if not isinstance(principles, list) or not principles:
        errors.append("constitutional_principles must be a non-empty list")
        principles = []
    principle_ids = set()
    for index, principle in enumerate(principles):
        prefix = f"constitutional_principles[{index}]"
        if not isinstance(principle, dict):
            errors.append(f"{prefix} must be an object")
            continue
        principle_id = principle.get("principle_id")
        if not _non_empty(principle_id):
            errors.append(f"{prefix}.principle_id must be a non-empty string")
        elif principle_id in principle_ids:
            errors.append(f"{prefix}.principle_id must be unique")
        principle_ids.add(principle_id)
        for field in ("principle", "decision_constraint"):
            if not _non_empty(principle.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")

    grants = payload.get("authority_grants")
    if not isinstance(grants, list) or not grants:
        errors.append("authority_grants must be a non-empty list")
        grants = []
    grant_ids = set()
    for index, grant in enumerate(grants):
        prefix = f"authority_grants[{index}]"
        if not isinstance(grant, dict):
            errors.append(f"{prefix} must be an object")
            continue
        grant_id = grant.get("grant_id")
        if not _non_empty(grant_id):
            errors.append(f"{prefix}.grant_id must be a non-empty string")
        elif grant_id in grant_ids:
            errors.append(f"{prefix}.grant_id must be unique")
        grant_ids.add(grant_id)
        for field in ("actor_id", "allowed_action", "prohibited_action", "review_authority_id"):
            if not _non_empty(grant.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")

    frozen_at = payload.get("frozen_at")
    exposure_at = payload.get("signal_exposure_at")
    generation_at = payload.get("candidate_generation_at")
    if all(_non_empty(item) for item in (frozen_at, exposure_at, generation_at)):
        if not frozen_at < exposure_at:
            errors.append("frozen_at must precede signal_exposure_at")
        if not exposure_at <= generation_at:
            errors.append("signal_exposure_at must not follow candidate_generation_at")
    if payload.get("constitution_mutated_after_exposure") is not False:
        errors.append("constitution_mutated_after_exposure must be false")
    if payload.get("authority_mutated_after_exposure") is not False:
        errors.append("authority_mutated_after_exposure must be false")
    if payload.get("candidate_conditioned_values_permitted") is not False:
        errors.append("candidate_conditioned_values_permitted must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "principle_count": len(principle_ids),
        "authority_grant_count": len(grant_ids),
        "frozen_before_exposure": bool(
            _non_empty(frozen_at) and _non_empty(exposure_at) and frozen_at < exposure_at
        ),
    }

def validate_incremental_signal_delivery_trace(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Prove that an evolving case was processed event by event with persistent state."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["incremental signal delivery trace must be an object"]}
    for field in ("delivery_trace_id", "comparison_system_id", "case_id", "trace_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("events_delivered_as_single_packet") is not False:
        errors.append("events_delivered_as_single_packet must be false")
    if payload.get("future_events_hidden_until_delivery") is not True:
        errors.append("future_events_hidden_until_delivery must be true")

    deliveries = payload.get("deliveries")
    if not isinstance(deliveries, list) or len(deliveries) < 2:
        errors.append("deliveries must contain at least two incremental event deliveries")
        deliveries = []
    event_ids = set()
    output_fingerprints = []
    decisions = set()
    for index, delivery in enumerate(deliveries):
        prefix = f"deliveries[{index}]"
        if not isinstance(delivery, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if delivery.get("sequence") != index + 1:
            errors.append(f"{prefix}.sequence must be contiguous and one-based")
        for field in (
            "event_id",
            "delivered_at",
            "event_evidence_id",
            "input_state_fingerprint",
            "output_state_fingerprint",
            "wake_reason",
            "mission_before",
            "mission_after",
            "decision_rationale",
        ):
            if not _non_empty(delivery.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        event_id = delivery.get("event_id")
        if _non_empty(event_id):
            if event_id in event_ids:
                errors.append(f"{prefix}.event_id must be unique")
            event_ids.add(event_id)
        if index and delivery.get("input_state_fingerprint") != output_fingerprints[-1]:
            errors.append(f"{prefix}.input_state_fingerprint must continue the previous output state")
        output_fingerprints.append(delivery.get("output_state_fingerprint"))
        decision = delivery.get("mission_decision")
        if decision not in {"preserve", "revise"}:
            errors.append(f"{prefix}.mission_decision must be preserve or revise")
        else:
            decisions.add(decision)
            same_mission = delivery.get("mission_before") == delivery.get("mission_after")
            if decision == "preserve" and not same_mission:
                errors.append(f"{prefix} preserve decision must keep the mission unchanged")
            if decision == "revise" and same_mission:
                errors.append(f"{prefix} revise decision must change the mission")
        if delivery.get("future_event_count_visible", -1) != 0:
            errors.append(f"{prefix}.future_event_count_visible must be zero")
    delivered_times = [
        item.get("delivered_at")
        for item in deliveries
        if isinstance(item, dict) and _non_empty(item.get("delivered_at"))
    ]
    if delivered_times != sorted(delivered_times) or len(delivered_times) != len(set(delivered_times)):
        errors.append("deliveries must have unique chronological delivered_at values")
    if decisions != {"preserve", "revise"}:
        errors.append("deliveries must demonstrate both mission persistence and revision")
    return {
        "valid": not errors,
        "errors": errors,
        "delivery_count": len(event_ids),
        "observed_decisions": sorted(decisions),
    }

def validate_equal_information_separate_compute_comparison(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Hold source information equal while preserving transparent compute differences."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["equal information separate compute comparison must be an object"]}
    for field in ("comparison_control_id", "case_id", "source_bundle_id", "source_bundle_fingerprint", "control_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    canonical_sources = payload.get("canonical_source_ids")
    if (
        not isinstance(canonical_sources, list)
        or not canonical_sources
        or not all(_non_empty(item) for item in canonical_sources)
        or len(canonical_sources) != len(set(canonical_sources))
    ):
        errors.append("canonical_source_ids must be a non-empty unique string list")
        canonical_sources = []

    conditions = payload.get("conditions")
    expected_conditions = {"human", "one_shot_agent", "palamedes"}
    if not isinstance(conditions, list) or len(conditions) != 3:
        errors.append("conditions must contain exactly human, one_shot_agent, and palamedes")
        conditions = []
    condition_ids = set()
    compute_profiles = []
    for index, condition in enumerate(conditions):
        prefix = f"conditions[{index}]"
        if not isinstance(condition, dict):
            errors.append(f"{prefix} must be an object")
            continue
        condition_id = condition.get("condition_id")
        condition_ids.add(condition_id)
        for field in ("source_bundle_id", "source_bundle_fingerprint", "information_released_at"):
            if not _non_empty(condition.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if condition.get("source_bundle_id") != payload.get("source_bundle_id"):
            errors.append(f"{prefix}.source_bundle_id must match the canonical bundle")
        if condition.get("source_bundle_fingerprint") != payload.get("source_bundle_fingerprint"):
            errors.append(f"{prefix}.source_bundle_fingerprint must match the canonical bundle")
        if condition.get("source_ids") != canonical_sources:
            errors.append(f"{prefix}.source_ids must exactly match canonical_source_ids in order")
        compute = condition.get("compute_report")
        if not isinstance(compute, dict):
            errors.append(f"{prefix}.compute_report must be an object")
            continue
        for field in ("model_call_count", "input_token_count", "output_token_count", "wall_clock_seconds", "human_work_seconds"):
            value = compute.get(field)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
                errors.append(f"{prefix}.compute_report.{field} must be a non-negative number")
        if compute.get("measured_not_imputed") is not True:
            errors.append(f"{prefix}.compute_report.measured_not_imputed must be true")
        compute_profiles.append(tuple(compute.get(field) for field in (
            "model_call_count",
            "input_token_count",
            "output_token_count",
            "wall_clock_seconds",
            "human_work_seconds",
        )))
    if condition_ids != expected_conditions:
        errors.append("condition_id values must be human, one_shot_agent, and palamedes")
    release_times = {
        item.get("information_released_at")
        for item in conditions
        if isinstance(item, dict)
    }
    if len(release_times) != 1:
        errors.append("all conditions must receive information at the same release time")
    if payload.get("compute_silently_equalized") is not False:
        errors.append("compute_silently_equalized must be false")
    if payload.get("compute_reported_separately") is not True:
        errors.append("compute_reported_separately must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "condition_ids": sorted(item for item in condition_ids if _non_empty(item)),
        "distinct_compute_profile_count": len(set(compute_profiles)),
    }

def validate_preplanning_blinded_mission_contract_comparison(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require complete mission contracts before origin-blinded downstream planning."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["preplanning blinded mission contract comparison must be an object"]}
    for field in (
        "handoff_control_id",
        "case_id",
        "capability_constraint_id",
        "capability_constraint_fingerprint",
        "handoff_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    outputs = payload.get("condition_outputs")
    expected_conditions = {"human", "one_shot_agent", "palamedes"}
    if not isinstance(outputs, list) or len(outputs) != 3:
        errors.append("condition_outputs must contain exactly three conditions")
        outputs = []
    condition_ids = set()
    blinded_ids = set()
    for index, output in enumerate(outputs):
        prefix = f"condition_outputs[{index}]"
        if not isinstance(output, dict):
            errors.append(f"{prefix} must be an object")
            continue
        condition_id = output.get("condition_id")
        condition_ids.add(condition_id)
        for field in ("mission_contract_id", "contract_created_at", "planner_handoff_at", "blinded_contract_id"):
            if not _non_empty(output.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if (
            _non_empty(output.get("contract_created_at"))
            and _non_empty(output.get("planner_handoff_at"))
            and not output["contract_created_at"] < output["planner_handoff_at"]
        ):
            errors.append(f"{prefix} mission contract must be completed before planner handoff")
        blinded_id = output.get("blinded_contract_id")
        if _non_empty(blinded_id):
            if blinded_id in blinded_ids:
                errors.append(f"{prefix}.blinded_contract_id must be unique")
            blinded_ids.add(blinded_id)
        contract = output.get("mission_contract")
        if not isinstance(contract, dict):
            errors.append(f"{prefix}.mission_contract must be an object")
            continue
        for field in (
            "situation",
            "meaning",
            "beneficiary",
            "desired_external_condition",
            "essential_causal_mechanism",
            "non_goal",
            "success_signal",
            "disconfirmation_condition",
            "authority_return_trigger",
        ):
            if not _non_empty(contract.get(field)):
                errors.append(f"{prefix}.mission_contract.{field} must be a non-empty string")
        if output.get("origin_metadata_removed") is not True:
            errors.append(f"{prefix}.origin_metadata_removed must be true")
        if output.get("downstream_plan_created_before_contract") is not False:
            errors.append(f"{prefix}.downstream_plan_created_before_contract must be false")
        if output.get("capability_constraint_id") != payload.get("capability_constraint_id"):
            errors.append(f"{prefix}.capability_constraint_id must match the shared constraint")
        if output.get("capability_constraint_fingerprint") != payload.get("capability_constraint_fingerprint"):
            errors.append(f"{prefix}.capability_constraint_fingerprint must match the shared constraint")
    if condition_ids != expected_conditions:
        errors.append("condition_id values must be human, one_shot_agent, and palamedes")
    if payload.get("planner_can_observe_condition_origin") is not False:
        errors.append("planner_can_observe_condition_origin must be false")
    if payload.get("planner_constraints_identical") is not True:
        errors.append("planner_constraints_identical must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "condition_ids": sorted(item for item in condition_ids if _non_empty(item)),
        "blinded_contract_count": len(blinded_ids),
    }

def validate_coherence_before_novelty_evaluation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Admit novelty only after consequence and causal-coherence eligibility."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["coherence before novelty evaluation must be an object"]}
    for field in ("evaluation_id", "case_id", "selected_mission_id", "evaluation_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("evaluation_order") != [
        "consequence_eligibility",
        "causal_coherence",
        "novelty",
    ]:
        errors.append("evaluation_order must place consequence and causal coherence before novelty")
    candidates = payload.get("candidate_evaluations")
    if not isinstance(candidates, list) or len(candidates) < 2:
        errors.append("candidate_evaluations must contain at least two candidates")
        candidates = []
    mission_ids = set()
    eligible_ids = set()
    selected = None
    for index, candidate in enumerate(candidates):
        prefix = f"candidate_evaluations[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{prefix} must be an object")
            continue
        mission_id = candidate.get("mission_id")
        if not _non_empty(mission_id):
            errors.append(f"{prefix}.mission_id must be a non-empty string")
        elif mission_id in mission_ids:
            errors.append(f"{prefix}.mission_id must be unique")
        mission_ids.add(mission_id)
        for field in (
            "consequence_assessment_id",
            "consequence_rationale",
            "causal_assessment_id",
            "causal_rationale",
        ):
            if not _non_empty(candidate.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        consequence_passed = candidate.get("consequence_eligible") is True
        causal_passed = candidate.get("causally_coherent") is True
        expected_eligible = consequence_passed and causal_passed
        if candidate.get("novelty_eligible") is not expected_eligible:
            errors.append(f"{prefix}.novelty_eligible must follow both prior gates")
        novelty = candidate.get("novelty_score")
        if expected_eligible:
            eligible_ids.add(mission_id)
            if not isinstance(novelty, (int, float)) or isinstance(novelty, bool) or not 0 <= novelty <= 1:
                errors.append(f"{prefix}.novelty_score must be between zero and one after eligibility")
            if not _non_empty(candidate.get("novelty_rationale")):
                errors.append(f"{prefix}.novelty_rationale must be a non-empty string after eligibility")
        elif novelty is not None or candidate.get("novelty_rationale") not in ("", None):
            errors.append(f"{prefix} ineligible candidate must not receive novelty evaluation")
        if mission_id == payload.get("selected_mission_id"):
            selected = candidate
    if payload.get("selected_mission_id") not in eligible_ids:
        errors.append("selected_mission_id must reference a consequence-eligible and causally coherent candidate")
    if selected and selected.get("novelty_eligible") is not True:
        errors.append("selected candidate must be novelty eligible")
    if payload.get("novelty_can_override_ineligibility") is not False:
        errors.append("novelty_can_override_ineligibility must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "eligible_mission_ids": sorted(item for item in eligible_ids if _non_empty(item)),
        "selected_mission_id": payload.get("selected_mission_id"),
    }

def validate_human_upstream_labor_ledger(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Account for human work required before each condition yields a viable mission."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["human upstream labor ledger must be an object"]}
    for field in ("labor_ledger_id", "case_id", "measurement_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected_conditions = {"human", "one_shot_agent", "palamedes"}
    expected_categories = {
        "framing",
        "clarification",
        "approval",
        "correction",
        "intervention",
    }
    records = payload.get("condition_labor_records")
    if not isinstance(records, list) or len(records) != 3:
        errors.append("condition_labor_records must contain exactly three conditions")
        records = []
    condition_ids = set()
    totals = {}
    for index, record in enumerate(records):
        prefix = f"condition_labor_records[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix} must be an object")
            continue
        condition_id = record.get("condition_id")
        condition_ids.add(condition_id)
        for field in ("viable_mission_id", "viability_decided_at", "viability_evidence_id"):
            if not _non_empty(record.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        categories = record.get("labor_categories")
        if not isinstance(categories, list) or len(categories) != 5:
            errors.append(f"{prefix}.labor_categories must contain all five upstream labor categories")
            categories = []
        category_ids = set()
        total_seconds = 0
        total_events = 0
        for category_index, category in enumerate(categories):
            category_prefix = f"{prefix}.labor_categories[{category_index}]"
            if not isinstance(category, dict):
                errors.append(f"{category_prefix} must be an object")
                continue
            category_id = category.get("category")
            category_ids.add(category_id)
            count = category.get("event_count")
            seconds = category.get("human_seconds")
            if not isinstance(count, int) or isinstance(count, bool) or count < 0:
                errors.append(f"{category_prefix}.event_count must be a non-negative integer")
                count = 0
            if not isinstance(seconds, (int, float)) or isinstance(seconds, bool) or seconds < 0:
                errors.append(f"{category_prefix}.human_seconds must be a non-negative number")
                seconds = 0
            evidence_ids = category.get("evidence_ids")
            if (
                not isinstance(evidence_ids, list)
                or len(evidence_ids) != count
                or not all(_non_empty(item) for item in evidence_ids)
                or len(evidence_ids) != len(set(evidence_ids))
            ):
                errors.append(f"{category_prefix}.evidence_ids must uniquely evidence every counted event")
            total_events += count
            total_seconds += seconds
        if category_ids != expected_categories:
            errors.append(f"{prefix}.labor_categories must cover framing, clarification, approval, correction, and intervention")
        if record.get("reported_total_event_count") != total_events:
            errors.append(f"{prefix}.reported_total_event_count must equal the category sum")
        if record.get("reported_total_human_seconds") != total_seconds:
            errors.append(f"{prefix}.reported_total_human_seconds must equal the category sum")
        totals[condition_id] = total_seconds
    if condition_ids != expected_conditions:
        errors.append("condition_id values must be human, one_shot_agent, and palamedes")
    if payload.get("zero_labor_must_be_explicit") is not True:
        errors.append("zero_labor_must_be_explicit must be true")
    if payload.get("post_viability_labor_included") is not False:
        errors.append("post_viability_labor_included must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "human_seconds_by_condition": {
            key: totals[key] for key in sorted(totals) if _non_empty(key)
        },
    }

def validate_purpose_comparison_failure_criteria(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Make six decisive failure modes observable and binding on the proof claim."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["purpose comparison failure criteria must be an object"]}
    for field in ("failure_protocol_id", "case_id", "decision_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected_types = {
        "generic_mission",
        "hidden_human_goal_injection",
        "proxy_harm",
        "constitution_theater",
        "planner_reconstruction",
        "no_outcome_advantage",
    }
    criteria = payload.get("failure_criteria")
    if not isinstance(criteria, list) or len(criteria) != 6:
        errors.append("failure_criteria must contain exactly six required failure types")
        criteria = []
    criterion_types = set()
    triggered_types = set()
    for index, criterion in enumerate(criteria):
        prefix = f"failure_criteria[{index}]"
        if not isinstance(criterion, dict):
            errors.append(f"{prefix} must be an object")
            continue
        criterion_type = criterion.get("failure_type")
        criterion_types.add(criterion_type)
        for field in (
            "criterion_id",
            "observable_test",
            "failure_threshold",
            "evidence_id",
            "independent_evaluator_id",
            "finding",
        ):
            if not _non_empty(criterion.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if not isinstance(criterion.get("triggered"), bool):
            errors.append(f"{prefix}.triggered must be boolean")
        elif criterion["triggered"]:
            triggered_types.add(criterion_type)
    if criterion_types != expected_types:
        errors.append("failure_criteria must cover all six required failure types without substitution")
    expected_verdict = "fail" if triggered_types else "eligible_for_proof"
    if payload.get("overall_verdict") != expected_verdict:
        errors.append("overall_verdict must fail when any criterion is triggered")
    if payload.get("failure_can_be_offset_by_other_scores") is not False:
        errors.append("failure_can_be_offset_by_other_scores must be false")
    if payload.get("criteria_frozen_before_evaluation") is not True:
        errors.append("criteria_frozen_before_evaluation must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "triggered_failure_types": sorted(item for item in triggered_types if _non_empty(item)),
        "overall_verdict": payload.get("overall_verdict"),
    }

def validate_end_to_end_purpose_proof_thesis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Integrate one evidenced signal-to-mission-to-outcome proof with labor retirement."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["end-to-end purpose proof thesis must be an object"]}
    for field in (
        "proof_thesis_id",
        "comparison_system_id",
        "case_id",
        "single_case_contract_id",
        "competition_design_id",
        "freeze_record_id",
        "delivery_trace_id",
        "information_control_id",
        "handoff_control_id",
        "ordered_evaluation_id",
        "labor_ledger_id",
        "failure_protocol_id",
        "selected_mission_id",
        "proof_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    lineage = payload.get("evidence_lineage")
    expected_stages = ["signal", "interpretation", "selection", "planning", "action", "outcome"]
    if not isinstance(lineage, list) or len(lineage) != len(expected_stages):
        errors.append("evidence_lineage must contain the six end-to-end stages")
        lineage = []
    for index, stage in enumerate(lineage):
        prefix = f"evidence_lineage[{index}]"
        if not isinstance(stage, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if stage.get("stage") != expected_stages[index]:
            errors.append(f"{prefix}.stage must follow signal through outcome order")
        for field in ("artifact_id", "evidence_id", "observed_at", "claim"):
            if not _non_empty(stage.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    observed_times = [
        item.get("observed_at")
        for item in lineage
        if isinstance(item, dict) and _non_empty(item.get("observed_at"))
    ]
    if observed_times != sorted(observed_times):
        errors.append("evidence_lineage must be chronological")

    comparison = payload.get("outcome_comparison")
    advantage = None
    if not isinstance(comparison, dict):
        errors.append("outcome_comparison must be an object")
    else:
        for field in (
            "outcome_metric_id",
            "palamedes_outcome_evidence_id",
            "best_baseline_condition_id",
            "baseline_outcome_evidence_id",
            "advantage_threshold_rationale",
        ):
            if not _non_empty(comparison.get(field)):
                errors.append(f"outcome_comparison.{field} must be a non-empty string")
        for field in ("palamedes_value", "best_baseline_value", "minimum_advantage"):
            if not isinstance(comparison.get(field), (int, float)) or isinstance(comparison.get(field), bool):
                errors.append(f"outcome_comparison.{field} must be numeric")
        if all(
            isinstance(comparison.get(field), (int, float)) and not isinstance(comparison.get(field), bool)
            for field in ("palamedes_value", "best_baseline_value", "minimum_advantage")
        ):
            advantage = comparison["palamedes_value"] - comparison["best_baseline_value"]
            if comparison["minimum_advantage"] <= 0 or advantage < comparison["minimum_advantage"]:
                errors.append("outcome_comparison must demonstrate the preregistered positive advantage")

    retirement = payload.get("upstream_labor_retirement")
    retired_seconds = None
    if not isinstance(retirement, dict):
        errors.append("upstream_labor_retirement must be an object")
    else:
        for field in ("baseline_labor_evidence_id", "palamedes_labor_evidence_id", "retirement_rationale"):
            if not _non_empty(retirement.get(field)):
                errors.append(f"upstream_labor_retirement.{field} must be a non-empty string")
        baseline = retirement.get("best_baseline_human_seconds")
        palamedes = retirement.get("palamedes_human_seconds")
        if (
            not isinstance(baseline, (int, float))
            or isinstance(baseline, bool)
            or baseline < 0
            or not isinstance(palamedes, (int, float))
            or isinstance(palamedes, bool)
            or palamedes < 0
        ):
            errors.append("upstream_labor_retirement labor values must be non-negative numbers")
        else:
            retired_seconds = baseline - palamedes
            if retired_seconds <= 0 or retirement.get("retired_human_seconds") != retired_seconds:
                errors.append("upstream_labor_retirement must report a positive reconciled labor reduction")
    for field in (
        "no_failure_criterion_triggered",
        "mission_defensibly_better",
        "outcome_advantage_demonstrated",
        "upstream_labor_retired",
        "independently_verified",
    ):
        if payload.get(field) is not True:
            errors.append(f"{field} must be true")
    if payload.get("proof_decision") != "demonstrated":
        errors.append("proof_decision must be demonstrated")
    return {
        "valid": not errors,
        "errors": errors,
        "outcome_advantage": advantage,
        "retired_human_seconds": retired_seconds,
        "proof_decision": payload.get("proof_decision"),
    }

def validate_versioned_selected_mission_unit(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Define the preplanning unit as a selected, governed, versioned mission."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["versioned selected mission unit must be an object"]}
    for field in (
        "mission_artifact_id",
        "mission_id",
        "mission_contract_id",
        "selection_record_id",
        "selected_at",
        "state_fingerprint",
        "selection_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    version = payload.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        errors.append("version must be a positive integer")
    previous = payload.get("previous_mission_artifact_id")
    if version == 1 and previous not in ("", None):
        errors.append("version one must not reference a previous mission artifact")
    if isinstance(version, int) and version > 1 and not _non_empty(previous):
        errors.append("version above one must reference a previous mission artifact")
    for field in ("observed_condition_ids", "explicit_value_ids", "authority_grant_ids"):
        values = payload.get(field)
        if (
            not isinstance(values, list)
            or not values
            or not all(_non_empty(item) for item in values)
            or len(values) != len(set(values))
        ):
            errors.append(f"{field} must be a non-empty unique string list")
    candidates = payload.get("selected_from_candidate_ids")
    if (
        not isinstance(candidates, list)
        or len(candidates) < 2
        or not all(_non_empty(item) for item in candidates)
        or len(candidates) != len(set(candidates))
    ):
        errors.append("selected_from_candidate_ids must contain at least two unique candidates")
        candidates = []
    if payload.get("mission_id") not in candidates:
        errors.append("mission_id must be one of selected_from_candidate_ids")
    if payload.get("selection_decision") != "selected":
        errors.append("selection_decision must be selected")
    if payload.get("idea_only") is not False:
        errors.append("idea_only must be false")
    if payload.get("planning_started_before_selection") is not False:
        errors.append("planning_started_before_selection must be false")
    if payload.get("values_or_authority_implicit") is not False:
        errors.append("values_or_authority_implicit must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "mission_id": payload.get("mission_id"),
        "version": version,
        "candidate_count": len(candidates),
    }

def validate_frontier_missing_transformation_selection(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Choose one cognitive transformation from the mission frontier's diagnosed deficit."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["frontier missing transformation selection must be an object"]}
    for field in (
        "transformation_selection_id",
        "mission_artifact_id",
        "frontier_snapshot_id",
        "deficit_evidence_id",
        "selection_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    operation_by_deficit = {
        "missing_observation": "expand_observation",
        "ambiguous_meaning": "reinterpret_meaning",
        "weak_causal_model": "revise_causal_model",
        "missing_alternative": "invent_mission",
        "unexamined_consequence": "criticize_consequence",
        "unresolved_choice": "select_mission",
        "overspecified_handoff": "compress_contract",
        "evidence_not_yet_available": "wait_for_evidence",
    }
    deficit = payload.get("frontier_deficit")
    if deficit not in operation_by_deficit:
        errors.append("frontier_deficit is not recognized")
    for field in ("frontier_claim", "current_state", "required_state_change"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    candidates = payload.get("candidate_transformations")
    if not isinstance(candidates, list) or len(candidates) < 2:
        errors.append("candidate_transformations must contain at least two alternatives")
        candidates = []
    operations = set()
    fitting = []
    for index, candidate in enumerate(candidates):
        prefix = f"candidate_transformations[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{prefix} must be an object")
            continue
        operation = candidate.get("operation")
        if operation not in set(operation_by_deficit.values()):
            errors.append(f"{prefix}.operation is not recognized")
        elif operation in operations:
            errors.append(f"{prefix}.operation must be unique")
        operations.add(operation)
        for field in ("expected_frontier_change", "fit_rationale"):
            if not _non_empty(candidate.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if candidate.get("addresses_deficit") is True:
            fitting.append(operation)
        elif candidate.get("addresses_deficit") is not False:
            errors.append(f"{prefix}.addresses_deficit must be boolean")
    expected = operation_by_deficit.get(deficit)
    if fitting != [expected]:
        errors.append("exactly the transformation mapped to frontier_deficit must address it")
    if payload.get("selected_transformation") != expected:
        errors.append("selected_transformation must match the diagnosed frontier deficit")
    if payload.get("execution_sequence") != [expected]:
        errors.append("execution_sequence must contain only the selected transformation")
    if payload.get("reasoning_volume_is_objective") is not False:
        errors.append("reasoning_volume_is_objective must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "frontier_deficit": deficit,
        "selected_transformation": payload.get("selected_transformation"),
    }

