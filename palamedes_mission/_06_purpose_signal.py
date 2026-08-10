from __future__ import annotations

from typing import Any, Dict, List
from ._01_kinds_value import _non_empty


def validate_living_constitution_runtime(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Govern routine autonomy through live constitutional state, not approvals."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["living constitution runtime must be an object"]}
    for field in (
        "runtime_id",
        "constitution_id",
        "constitution_version",
        "interpreted_at",
        "decision_id",
        "interpretation_trace_id",
        "runtime_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("human_approval_is_default") is not False:
        errors.append("human_approval_is_default must be false")
    if payload.get("routine_decision_within_constitution") is not True:
        errors.append("routine_decision_within_constitution must be true")
    if payload.get("constitution_is_live_state") is not True:
        errors.append("constitution_is_live_state must be true")

    required_layers = {"values", "uncertainty", "authority", "representation", "correction"}
    layers = payload.get("constitutional_layers")
    if not isinstance(layers, list):
        errors.append("constitutional_layers must be a list")
        layers = []
    seen = set()
    for index, layer in enumerate(layers):
        prefix = f"constitutional_layers[{index}]"
        if not isinstance(layer, dict):
            errors.append(f"{prefix} must be an object")
            continue
        kind = layer.get("layer")
        if kind not in required_layers:
            errors.append(f"{prefix}.layer is not recognized")
        elif kind in seen:
            errors.append(f"{prefix}.layer must be unique")
        else:
            seen.add(kind)
        for field in ("state_id", "current_state", "source_id", "review_trigger"):
            if not _non_empty(layer.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if seen != required_layers:
        errors.append("constitutional_layers must cover values, uncertainty, authority, representation, and correction")

    decision = payload.get("decision")
    if decision not in {"act", "probe", "defer", "escalate_power_gap"}:
        errors.append("decision must be act, probe, defer, or escalate_power_gap")
    if decision == "escalate_power_gap" and not _non_empty(payload.get("ungranted_power")):
        errors.append("escalate_power_gap requires ungranted_power")
    if decision != "escalate_power_gap" and payload.get("ungranted_power") not in ("", None):
        errors.append("ungranted_power is only valid for escalate_power_gap")

    return {
        "valid": not errors,
        "errors": errors,
        "constitutional_layers": sorted(seen),
        "decision": decision,
    }

def validate_purpose_creativity_transfer(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Locate purpose creativity in beneficiary discovery and mechanism transfer."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["purpose creativity transfer must be an object"]}
    for field in (
        "creativity_record_id",
        "mission_candidate_id",
        "discovered_beneficiary_condition",
        "beneficiary_condition_evidence_id",
        "source_context",
        "source_mechanism",
        "source_mechanism_evidence_id",
        "target_context",
        "transferred_mechanism",
        "transfer_invariant",
        "target_adaptation",
        "opened_action",
        "constitutional_trace_id",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("product_form_novelty_is_sufficient") is not False:
        errors.append("product_form_novelty_is_sufficient must be false")
    if payload.get("source_context") == payload.get("target_context"):
        errors.append("source_context and target_context must differ for a transfer")
    if payload.get("source_mechanism") == payload.get("transferred_mechanism"):
        if not _non_empty(payload.get("target_adaptation")):
            errors.append("unchanged mechanism name requires explicit target adaptation")
    if payload.get("beneficiary_condition_was_previously_explicit") is not False:
        errors.append("beneficiary_condition_was_previously_explicit must be false")

    alternatives = payload.get("obvious_product_form_alternatives")
    if not isinstance(alternatives, list) or not alternatives or not all(_non_empty(item) for item in alternatives):
        errors.append("obvious_product_form_alternatives must be a non-empty list")
    comparisons = payload.get("usefulness_tests")
    if not isinstance(comparisons, list) or len(comparisons) < 2:
        errors.append("usefulness_tests must contain at least two tests")
        comparisons = []
    for index, test in enumerate(comparisons):
        prefix = f"usefulness_tests[{index}]"
        if not isinstance(test, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("test_id", "criterion", "evidence_id"):
            if not _non_empty(test.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if not isinstance(test.get("passed"), bool):
            errors.append(f"{prefix}.passed must be boolean")

    return {
        "valid": not errors,
        "errors": errors,
        "usefulness_test_count": len(comparisons),
    }

def validate_insight_mission_landscape_change(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require an insight to create, remove, sequence, or reprioritize missions."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["insight mission landscape change must be an object"]}
    for field in (
        "insight_id",
        "insight_claim",
        "insight_evidence_id",
        "prior_landscape_fingerprint",
        "resulting_landscape_fingerprint",
        "landscape_change_summary",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("interesting_without_landscape_change_is_insight") is not False:
        errors.append("interesting_without_landscape_change_is_insight must be false")
    if (
        _non_empty(payload.get("prior_landscape_fingerprint"))
        and payload.get("prior_landscape_fingerprint")
        == payload.get("resulting_landscape_fingerprint")
    ):
        errors.append("resulting landscape fingerprint must differ from prior landscape")

    operations = payload.get("landscape_operations")
    if not isinstance(operations, list) or not operations:
        errors.append("landscape_operations must be a non-empty list")
        operations = []
    operation_ids = set()
    kinds = set()
    for index, operation in enumerate(operations):
        prefix = f"landscape_operations[{index}]"
        if not isinstance(operation, dict):
            errors.append(f"{prefix} must be an object")
            continue
        operation_id = operation.get("operation_id")
        if not _non_empty(operation_id):
            errors.append(f"{prefix}.operation_id must be a non-empty string")
        elif operation_id in operation_ids:
            errors.append(f"{prefix}.operation_id must be unique")
        else:
            operation_ids.add(operation_id)
        kind = operation.get("kind")
        if kind not in {"create", "remove", "sequence", "reprioritize"}:
            errors.append(f"{prefix}.kind is not recognized")
        else:
            kinds.add(kind)
        affected = operation.get("affected_mission_ids")
        if not isinstance(affected, list) or not affected or not all(_non_empty(item) for item in affected):
            errors.append(f"{prefix}.affected_mission_ids must be a non-empty list")
        for field in ("before_state", "after_state", "reason", "evidence_id"):
            if not _non_empty(operation.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if kind == "remove" and operation.get("removed_lineage_preserved") is not True:
            errors.append(f"{prefix}.removed_lineage_preserved must be true for removal")

    return {
        "valid": not errors,
        "errors": errors,
        "operation_kinds": sorted(kinds),
    }

def validate_atomic_mission_cycle(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Enforce the atomic mismatch-to-consequence purpose formation sequence."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["atomic mission cycle must be an object"]}
    for field in ("cycle_id", "constitution_id", "started_at", "completed_at"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    required_order = [
        "observe_mismatch",
        "interpret_condition",
        "generate_missions",
        "attack_missions",
        "select_authority_bounded_action",
        "learn_consequence",
    ]
    steps = payload.get("steps")
    if not isinstance(steps, list):
        errors.append("steps must be a list")
        steps = []
    actual_order = [
        step.get("operation") if isinstance(step, dict) else None
        for step in steps
    ]
    if actual_order != required_order:
        errors.append("steps must follow the complete atomic mission cycle in order")
    previous_output = None
    artifact_ids = set()
    for index, step in enumerate(steps):
        prefix = f"steps[{index}]"
        if not isinstance(step, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in (
            "artifact_id",
            "input_fingerprint",
            "output_fingerprint",
            "evidence_id",
            "result",
        ):
            if not _non_empty(step.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        artifact_id = step.get("artifact_id")
        if _non_empty(artifact_id):
            if artifact_id in artifact_ids:
                errors.append(f"{prefix}.artifact_id must be unique")
            artifact_ids.add(artifact_id)
        if step.get("completed") is not True:
            errors.append(f"{prefix}.completed must be true")
        if previous_output is not None and step.get("input_fingerprint") != previous_output:
            errors.append(f"{prefix}.input_fingerprint must equal previous output_fingerprint")
        previous_output = step.get("output_fingerprint")
    if payload.get("steps_skipped") not in ([], None):
        errors.append("steps_skipped must be empty")

    return {
        "valid": not errors,
        "errors": errors,
        "completed_operations": actual_order,
        "final_fingerprint": previous_output,
    }

def validate_persistent_purpose_intelligence(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Treat persistent model revision, not the handoff artifact, as intelligence."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["persistent purpose intelligence must be an object"]}
    for field in (
        "intelligence_record_id",
        "mission_contract_id",
        "mission_contract_version",
        "previous_frontier_fingerprint",
        "current_frontier_fingerprint",
        "wake_reason",
        "worthwhile_change_test",
        "next_wake_trigger",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("mission_contract_is_entire_product_intelligence") is not False:
        errors.append("mission_contract_is_entire_product_intelligence must be false")
    if payload.get("model_state_persists_across_handoffs") is not True:
        errors.append("model_state_persists_across_handoffs must be true")
    if (
        _non_empty(payload.get("previous_frontier_fingerprint"))
        and payload.get("previous_frontier_fingerprint")
        == payload.get("current_frontier_fingerprint")
    ):
        errors.append("persistent frontier fingerprint must change after a claimed revision")

    required_models = {"world", "value", "mechanism"}
    revisions = payload.get("model_revisions")
    if not isinstance(revisions, list):
        errors.append("model_revisions must be a list")
        revisions = []
    seen = set()
    changed_models = []
    for index, revision in enumerate(revisions):
        prefix = f"model_revisions[{index}]"
        if not isinstance(revision, dict):
            errors.append(f"{prefix} must be an object")
            continue
        model = revision.get("model")
        if model not in required_models:
            errors.append(f"{prefix}.model is not recognized")
        elif model in seen:
            errors.append(f"{prefix}.model must be unique")
        else:
            seen.add(model)
        for field in (
            "previous_state_id",
            "current_state_id",
            "revision_evidence_id",
            "revision_reason",
        ):
            if not _non_empty(revision.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        changed = revision.get("changed")
        if not isinstance(changed, bool):
            errors.append(f"{prefix}.changed must be boolean")
        elif changed:
            changed_models.append(model)
    if seen != required_models:
        errors.append("model_revisions must cover world, value, and mechanism")
    if not changed_models:
        errors.append("at least one persistent model must change")
    if not isinstance(payload.get("different_mission_became_worthwhile"), bool):
        errors.append("different_mission_became_worthwhile must be boolean")

    return {
        "valid": not errors,
        "errors": errors,
        "changed_models": sorted(changed_models),
    }

def validate_single_mission_adversarial_proof(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Limit first proof to one mission from evolving signals under attack."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["single mission adversarial proof must be an object"]}
    for field in (
        "proof_id",
        "case_id",
        "originated_mission_id",
        "mission_contract_id",
        "origin_evidence_id",
        "survival_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("automates_entire_company") is not False:
        errors.append("automates_entire_company must be false")
    if payload.get("human_goal_injected") is not False:
        errors.append("human_goal_injected must be false")
    if payload.get("originated_mission_count") != 1:
        errors.append("originated_mission_count must equal one")
    if payload.get("survived_adversarial_comparison") is not True:
        errors.append("survived_adversarial_comparison must be true")

    signals = payload.get("evolving_signals")
    if not isinstance(signals, list) or len(signals) < 2:
        errors.append("evolving_signals must contain at least two sequential events")
        signals = []
    signal_ids = set()
    previous_time = None
    for index, signal in enumerate(signals):
        prefix = f"evolving_signals[{index}]"
        if not isinstance(signal, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("signal_id", "revealed_at", "observation", "evidence_id"):
            if not _non_empty(signal.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        signal_id = signal.get("signal_id")
        if _non_empty(signal_id):
            if signal_id in signal_ids:
                errors.append(f"{prefix}.signal_id must be unique")
            signal_ids.add(signal_id)
        revealed_at = signal.get("revealed_at")
        if previous_time is not None and _non_empty(revealed_at) and revealed_at <= previous_time:
            errors.append(f"{prefix}.revealed_at must be later than the previous signal")
        previous_time = revealed_at

    origin_signal_ids = payload.get("origin_signal_ids")
    if (
        not isinstance(origin_signal_ids, list)
        or not origin_signal_ids
        or any(signal_id not in signal_ids for signal_id in origin_signal_ids)
    ):
        errors.append("origin_signal_ids must reference the evolving signal sequence")

    required_axes = {"causal_thesis", "constitutional_fit", "replaceability"}
    attacks = payload.get("adversarial_attacks")
    if not isinstance(attacks, list):
        errors.append("adversarial_attacks must be a list")
        attacks = []
    seen_axes = set()
    for index, attack in enumerate(attacks):
        prefix = f"adversarial_attacks[{index}]"
        if not isinstance(attack, dict):
            errors.append(f"{prefix} must be an object")
            continue
        axis = attack.get("axis")
        if axis not in required_axes:
            errors.append(f"{prefix}.axis is not recognized")
        else:
            seen_axes.add(axis)
        for field in ("attack", "evidence_id", "response", "survival_criterion"):
            if not _non_empty(attack.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if not isinstance(attack.get("criterion_met"), bool):
            errors.append(f"{prefix}.criterion_met must be boolean")
        elif attack.get("criterion_met") is not True:
            errors.append(f"{prefix}.criterion_met must be true for survived comparison")
    if seen_axes != required_axes:
        errors.append("adversarial_attacks must cover causal thesis, constitutional fit, and replaceability")

    return {
        "valid": not errors,
        "errors": errors,
        "signal_count": len(signals),
        "attack_axes": sorted(seen_axes),
    }

def validate_upstream_labor_retirement_success(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Claim success only when upstream labor falls without governance regression."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["upstream labor retirement success must be an object"]}
    for field in (
        "success_record_id",
        "case_id",
        "baseline_condition_id",
        "palamedes_condition_id",
        "labor_evidence_id",
        "proxy_harm_audit_id",
        "authority_audit_id",
        "rationale_audit_id",
        "success_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    metric_names = {
        "framing_minutes",
        "clarification_count",
        "approval_count",
        "correction_count",
        "intervention_count",
    }
    totals: Dict[str, float] = {}
    for condition in ("baseline_labor", "palamedes_labor"):
        metrics = payload.get(condition)
        if not isinstance(metrics, dict):
            errors.append(f"{condition} must be an object")
            continue
        if set(metrics) != metric_names:
            errors.append(f"{condition} must contain exactly the five upstream labor metrics")
            continue
        total = 0.0
        for metric, value in metrics.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
                errors.append(f"{condition}.{metric} must be a non-negative number")
            else:
                total += value
        totals[condition] = total
    threshold = payload.get("minimum_labor_reduction_fraction")
    if (
        not isinstance(threshold, (int, float))
        or isinstance(threshold, bool)
        or not 0 < threshold <= 1
    ):
        errors.append("minimum_labor_reduction_fraction must satisfy 0 < value <= 1")
    reduction = None
    baseline_total = totals.get("baseline_labor")
    palamedes_total = totals.get("palamedes_labor")
    if baseline_total is not None and palamedes_total is not None:
        if baseline_total <= 0:
            errors.append("baseline upstream labor total must be greater than zero")
        else:
            reduction = (baseline_total - palamedes_total) / baseline_total

    for field in (
        "proxy_harm_not_increased",
        "hidden_authority_absent",
        "rationales_action_linked",
        "mission_quality_noninferior",
    ):
        if not isinstance(payload.get(field), bool):
            errors.append(f"{field} must be boolean")
    success_claimed = payload.get("success_claimed")
    if not isinstance(success_claimed, bool):
        errors.append("success_claimed must be boolean")
    success_criteria_met = (
        reduction is not None
        and isinstance(threshold, (int, float))
        and reduction >= threshold
        and payload.get("proxy_harm_not_increased") is True
        and payload.get("hidden_authority_absent") is True
        and payload.get("rationales_action_linked") is True
        and payload.get("mission_quality_noninferior") is True
    )
    if success_claimed is True and not success_criteria_met:
        errors.append("success_claimed requires labor retirement without governance or quality regression")

    return {
        "valid": not errors,
        "errors": errors,
        "labor_reduction_fraction": reduction,
        "success_criteria_met": success_criteria_met,
    }

def validate_autonomous_purpose_engine_conclusion(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Integrate the purpose engine while keeping the equal-budget proof honest."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["autonomous purpose engine conclusion must be an object"]}
    for field in (
        "conclusion_id",
        "constitution_id",
        "anti_entrenchment_gate_id",
        "autonomy_claim_id",
        "preference_challenge_id",
        "living_constitution_runtime_id",
        "creativity_transfer_id",
        "insight_landscape_id",
        "atomic_cycle_id",
        "persistent_intelligence_id",
        "single_mission_proof_id",
        "labor_retirement_success_id",
        "equal_information_manifest_id",
        "equal_resource_budget_id",
        "human_baseline_id",
        "one_shot_agent_baseline_id",
        "palamedes_condition_id",
        "proof_question",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    for field in (
        "constitution_guided",
        "discovers_conditions",
        "imagines_better_conditions",
        "originates_missions",
        "selects_under_plural_values",
        "delegates_versioned_contracts",
        "revises_from_consequences",
        "mission_independently_originated",
    ):
        if payload.get(field) is not True:
            errors.append(f"{field} must be true")
    if payload.get("planning_quality_is_primary_proof") is not False:
        errors.append("planning_quality_is_primary_proof must be false")

    status = payload.get("proof_status")
    if status not in {"required_not_yet_verified", "independently_verified", "failed"}:
        errors.append("proof_status is not recognized")
    superiority = payload.get("better_than_both_baselines")
    if not isinstance(superiority, bool):
        errors.append("better_than_both_baselines must be boolean")
    if status == "required_not_yet_verified":
        if superiority is not False:
            errors.append("unverified proof cannot claim superiority")
        if payload.get("independent_proof_evidence_id") not in ("", None):
            errors.append("unverified proof cannot cite completed independent proof evidence")
    if status == "independently_verified":
        if superiority is not True:
            errors.append("independently verified proof requires better_than_both_baselines true")
        for field in ("independent_proof_evidence_id", "blinded_review_id"):
            if not _non_empty(payload.get(field)):
                errors.append(f"independently verified proof requires {field}")
    if status == "failed" and superiority is True:
        errors.append("failed proof cannot claim superiority")

    return {
        "valid": not errors,
        "errors": errors,
        "proof_status": status,
        "superiority_claim_allowed": status == "independently_verified" and superiority is True,
    }

def validate_event_attention_admission(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Prevent every observed change from consuming signal attention."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["event attention admission must be an object"]}
    for field in (
        "admission_id",
        "event_id",
        "observed_change",
        "observation_evidence_id",
        "attention_budget_id",
        "decision_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("every_change_is_signal") is not False:
        errors.append("every_change_is_signal must be false")
    for field in ("attention_capacity", "attention_committed", "attention_cost"):
        value = payload.get(field)
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or value < 0
        ):
            errors.append(f"{field} must be a non-negative number")
    cost = payload.get("attention_cost")
    if isinstance(cost, (int, float)) and not isinstance(cost, bool) and cost <= 0:
        errors.append("attention_cost must be greater than zero")
    decision = payload.get("decision")
    if decision not in {"ignore", "store_change", "admit_signal", "wake"}:
        errors.append("decision must be ignore, store_change, admit_signal, or wake")
    admitted = payload.get("admitted_as_signal")
    if not isinstance(admitted, bool):
        errors.append("admitted_as_signal must be boolean")
    if decision in {"admit_signal", "wake"} and admitted is not True:
        errors.append("admit_signal or wake requires admitted_as_signal true")
    if decision in {"ignore", "store_change"} and admitted is not False:
        errors.append("ignore or store_change requires admitted_as_signal false")
    if decision in {"admit_signal", "wake"}:
        for field in ("attention_reason", "next_review_trigger"):
            if not _non_empty(payload.get(field)):
                errors.append(f"{field} must be a non-empty string when attention is admitted")
        capacity = payload.get("attention_capacity")
        committed = payload.get("attention_committed")
        if all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in (capacity, committed, cost)):
            if committed + cost > capacity:
                errors.append("attention admission exceeds capacity")

    return {
        "valid": not errors,
        "errors": errors,
        "decision": decision,
        "admitted_as_signal": admitted,
    }

def validate_relational_signal_importance(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Define importance through change-condition-value-capability-time relations."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["relational signal importance must be an object"]}
    for field in (
        "importance_record_id",
        "event_id",
        "observed_change",
        "affected_condition",
        "constitution_clause_id",
        "available_capability_id",
        "time_window",
        "importance_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("event_has_intrinsic_importance") is not False:
        errors.append("event_has_intrinsic_importance must be false")

    required_relations = {
        "change_to_condition",
        "condition_to_value",
        "value_to_capability",
        "capability_to_time",
    }
    relations = payload.get("relations")
    if not isinstance(relations, list):
        errors.append("relations must be a list")
        relations = []
    seen = set()
    relevant_count = 0
    for index, relation in enumerate(relations):
        prefix = f"relations[{index}]"
        if not isinstance(relation, dict):
            errors.append(f"{prefix} must be an object")
            continue
        kind = relation.get("relation")
        if kind not in required_relations:
            errors.append(f"{prefix}.relation is not recognized")
        elif kind in seen:
            errors.append(f"{prefix}.relation must be unique")
        else:
            seen.add(kind)
        status = relation.get("status")
        if status not in {"relevant", "irrelevant", "unknown"}:
            errors.append(f"{prefix}.status must be relevant, irrelevant, or unknown")
        elif status == "relevant":
            relevant_count += 1
        for field in ("claim", "evidence_id", "uncertainty"):
            if not _non_empty(relation.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if seen != required_relations:
        errors.append("relations must cover change-condition-value-capability-time")

    importance = payload.get("importance")
    if importance not in {"low", "moderate", "high", "unknown"}:
        errors.append("importance must be low, moderate, high, or unknown")
    if importance == "high" and relevant_count != len(required_relations):
        errors.append("high importance requires every relation to be relevant")
    if importance == "low" and relevant_count == len(required_relations):
        errors.append("fully relevant chain cannot be classified low")

    return {
        "valid": not errors,
        "errors": errors,
        "relevant_relation_count": relevant_count,
        "importance": importance,
    }

def validate_anomaly_attention_reservation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Reserve bounded attention for changes outside current value and world models."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["anomaly attention reservation must be an object"]}
    for field in (
        "reservation_id",
        "event_id",
        "anomalous_observation",
        "observation_evidence_id",
        "current_value_model_id",
        "current_world_model_id",
        "value_model_mismatch",
        "world_model_mismatch",
        "anomaly_budget_id",
        "expires_at",
        "investigation_probe",
        "decision_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("value_model_fit") is not False:
        errors.append("value_model_fit must be false")
    if payload.get("world_model_fit") is not False:
        errors.append("world_model_fit must be false")
    if payload.get("meaning_assigned_before_investigation") is not False:
        errors.append("meaning_assigned_before_investigation must be false")
    if payload.get("anomaly_is_harm_evidence") is not False:
        errors.append("anomaly_is_harm_evidence must be false")
    for field in ("anomaly_capacity", "anomaly_committed", "anomaly_cost"):
        value = payload.get(field)
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or value < 0
        ):
            errors.append(f"{field} must be a non-negative number")
    cost = payload.get("anomaly_cost")
    if isinstance(cost, (int, float)) and not isinstance(cost, bool) and cost <= 0:
        errors.append("anomaly_cost must be greater than zero")
    decision = payload.get("decision")
    if decision not in {"reserve", "defer", "reject"}:
        errors.append("decision must be reserve, defer, or reject")
    capacity = payload.get("anomaly_capacity")
    committed = payload.get("anomaly_committed")
    if decision == "reserve" and all(
        isinstance(value, (int, float)) and not isinstance(value, bool)
        for value in (capacity, committed, cost)
    ):
        if committed + cost > capacity:
            errors.append("anomaly reservation exceeds bounded capacity")

    return {
        "valid": not errors,
        "errors": errors,
        "decision": decision,
    }

def validate_anomaly_priority_evidence(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Raise anomaly priority through recurrence and asymmetry without meaning."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["anomaly priority evidence must be an object"]}
    for field in (
        "priority_record_id",
        "anomaly_reservation_id",
        "anomaly_observation",
        "first_observed_at",
        "last_observed_at",
        "consequence_asymmetry",
        "next_investigation",
        "priority_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("meaning_declared") is not False:
        errors.append("meaning_declared must be false")
    if payload.get("harm_declared") is not False:
        errors.append("harm_declared must be false")
    count = payload.get("observation_count")
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        errors.append("observation_count must be a positive integer")
    sources = payload.get("recurrence_sources")
    if not isinstance(sources, list) or not sources:
        errors.append("recurrence_sources must be a non-empty list")
        sources = []
    source_ids = set()
    contexts = set()
    for index, source in enumerate(sources):
        prefix = f"recurrence_sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("source_id", "context", "observation", "evidence_id"):
            if not _non_empty(source.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        source_id = source.get("source_id")
        if _non_empty(source_id):
            if source_id in source_ids:
                errors.append(f"{prefix}.source_id must be unique")
            source_ids.add(source_id)
        if _non_empty(source.get("context")):
            contexts.add(source.get("context"))
    persistence_present = isinstance(count, int) and count >= 2
    cross_source_present = len(source_ids) >= 2 and len(contexts) >= 2
    asymmetry_present = payload.get("consequence_asymmetry_present")
    if not isinstance(asymmetry_present, bool):
        errors.append("consequence_asymmetry_present must be boolean")
    evidence_count = sum(
        bool(item)
        for item in (persistence_present, cross_source_present, asymmetry_present is True)
    )
    priority = payload.get("priority")
    if priority not in {"low", "moderate", "high"}:
        errors.append("priority must be low, moderate, or high")
    expected_priority = "high" if evidence_count == 3 else "moderate" if evidence_count == 2 else "low"
    if priority in {"low", "moderate", "high"} and priority != expected_priority:
        errors.append("priority must follow persistence, cross-source recurrence, and consequence asymmetry evidence")

    return {
        "valid": not errors,
        "errors": errors,
        "priority": priority,
        "priority_evidence_count": evidence_count,
    }

def validate_observation_coverage_map(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Expose beneficiaries and consequences hidden by current data sources."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["observation coverage map must be an object"]}
    for field in (
        "coverage_map_id",
        "observation_system_id",
        "review_period",
        "missing_report_trigger",
        "coverage_summary",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("silence_counts_as_coverage") is not False:
        errors.append("silence_counts_as_coverage must be false")
    sources = payload.get("data_source_ids")
    if not isinstance(sources, list) or not sources or not all(_non_empty(item) for item in sources):
        errors.append("data_source_ids must be a non-empty list")

    entries = payload.get("coverage_entries")
    if not isinstance(entries, list) or not entries:
        errors.append("coverage_entries must be a non-empty list")
        entries = []
    pairs = set()
    unobserved = []
    for index, entry in enumerate(entries):
        prefix = f"coverage_entries[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in (
            "beneficiary_group",
            "consequence_type",
            "visibility_reason",
            "collection_incentive",
            "mitigation",
        ):
            if not _non_empty(entry.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        pair = (entry.get("beneficiary_group"), entry.get("consequence_type"))
        if pair in pairs:
            errors.append(f"{prefix} beneficiary-consequence pair must be unique")
        pairs.add(pair)
        status = entry.get("coverage_status")
        if status not in {"observed", "partial", "unobserved"}:
            errors.append(f"{prefix}.coverage_status is not recognized")
        elif status == "unobserved":
            unobserved.append(pair)
        entry_sources = entry.get("source_ids")
        if not isinstance(entry_sources, list):
            errors.append(f"{prefix}.source_ids must be a list")
        elif status == "unobserved" and entry_sources:
            errors.append(f"{prefix}.source_ids must be empty when unobserved")
        elif status in {"observed", "partial"} and not entry_sources:
            errors.append(f"{prefix}.source_ids must be non-empty when observed or partial")
    if not unobserved:
        errors.append("coverage_entries must expose at least one unobserved beneficiary-consequence pair")

    return {
        "valid": not errors,
        "errors": errors,
        "unobserved_pairs": unobserved,
    }

def validate_expected_missing_observation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Admit expected absence as a signal without prematurely declaring harm."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["expected missing observation must be an object"]}
    for field in (
        "missing_signal_id",
        "coverage_map_id",
        "expected_observation_id",
        "expected_observation",
        "expectation_source_id",
        "expected_by",
        "checked_at",
        "expected_channel_id",
        "missingness_evidence_id",
        "next_discriminating_probe",
        "wake_trigger",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("missing_observation_admitted_as_signal") is not True:
        errors.append("missing_observation_admitted_as_signal must be true")
    if payload.get("absence_is_harm_evidence") is not False:
        errors.append("absence_is_harm_evidence must be false")
    if payload.get("meaning_resolved") is not False:
        errors.append("meaning_resolved must be false")
    if payload.get("status") != "unresolved":
        errors.append("status must be unresolved")

    alternatives = payload.get("alternative_explanations")
    if not isinstance(alternatives, list) or len(alternatives) < 3:
        errors.append("alternative_explanations must contain at least three explanations")
        alternatives = []
    allowed_kinds = {
        "harm_or_exclusion",
        "collection_failure",
        "reporting_delay",
        "expectation_wrong",
    }
    kinds = []
    for index, alternative in enumerate(alternatives):
        prefix = f"alternative_explanations[{index}]"
        if not isinstance(alternative, dict):
            errors.append(f"{prefix} must be an object")
            continue
        kind = alternative.get("kind")
        if kind not in allowed_kinds:
            errors.append(f"{prefix}.kind is not recognized")
        elif kind in kinds:
            errors.append(f"{prefix}.kind must be unique")
        else:
            kinds.append(kind)
        for field in ("claim", "evidence_for", "evidence_against", "discriminator"):
            if not _non_empty(alternative.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if "harm_or_exclusion" not in kinds:
        errors.append("alternative_explanations must represent harm_or_exclusion")
    if not set(kinds).intersection({"collection_failure", "reporting_delay", "expectation_wrong"}):
        errors.append("alternative_explanations must represent a non-harm explanation")

    return {
        "valid": not errors,
        "errors": errors,
        "alternative_kinds": kinds,
        "status": payload.get("status"),
    }

def validate_source_error_structure(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Keep source variety distinct from demonstrated source independence."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["source error structure must be an object"]}
    for field in ("source_structure_id", "claim_id", "assessment_summary"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("source_diversity_proves_independence") is not False:
        errors.append("source_diversity_proves_independence must be false")

    sources = payload.get("sources")
    if not isinstance(sources, list) or len(sources) < 2:
        errors.append("sources must contain at least two sources")
        sources = []
    allowed_classes = {
        "human_report",
        "telemetry",
        "market",
        "research",
        "implementation_outcome",
    }
    source_ids = []
    source_classes = set()
    for index, source in enumerate(sources):
        prefix = f"sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{prefix} must be an object")
            continue
        source_id = source.get("source_id")
        if not _non_empty(source_id):
            errors.append(f"{prefix}.source_id must be a non-empty string")
        elif source_id in source_ids:
            errors.append(f"{prefix}.source_id must be unique")
        else:
            source_ids.append(source_id)
        source_class = source.get("source_class")
        if source_class not in allowed_classes:
            errors.append(f"{prefix}.source_class is not recognized")
        else:
            source_classes.add(source_class)
        for field in ("observation_method", "collection_incentive", "known_blind_spot"):
            if not _non_empty(source.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        mechanisms = source.get("error_mechanisms")
        if not isinstance(mechanisms, list) or not mechanisms or not all(_non_empty(item) for item in mechanisms):
            errors.append(f"{prefix}.error_mechanisms must be a non-empty list")

    assessments = payload.get("pairwise_dependencies")
    if not isinstance(assessments, list):
        errors.append("pairwise_dependencies must be a list")
        assessments = []
    assessed_pairs = set()
    for index, assessment in enumerate(assessments):
        prefix = f"pairwise_dependencies[{index}]"
        if not isinstance(assessment, dict):
            errors.append(f"{prefix} must be an object")
            continue
        left = assessment.get("left_source_id")
        right = assessment.get("right_source_id")
        if left not in source_ids or right not in source_ids or left == right:
            errors.append(f"{prefix} must reference two distinct declared sources")
            continue
        pair = tuple(sorted((left, right)))
        if pair in assessed_pairs:
            errors.append(f"{prefix} source pair must be unique")
        assessed_pairs.add(pair)
        if assessment.get("dependency_status") not in {"independent", "correlated", "unknown"}:
            errors.append(f"{prefix}.dependency_status is not recognized")
        for field in ("shared_upstream", "shared_incentive", "dependency_rationale"):
            if not _non_empty(assessment.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if (
            assessment.get("dependency_status") == "independent"
            and assessment.get("independence_evidence_ids") in (None, [])
        ):
            errors.append(f"{prefix}.independence_evidence_ids must support an independence claim")
    expected_pairs = {
        tuple(sorted((source_ids[left], source_ids[right])))
        for left in range(len(source_ids))
        for right in range(left + 1, len(source_ids))
    }
    if assessed_pairs != expected_pairs:
        errors.append("pairwise_dependencies must assess every declared source pair exactly once")

    return {
        "valid": not errors,
        "errors": errors,
        "source_classes": sorted(source_classes),
        "assessed_pair_count": len(assessed_pairs),
    }

def validate_contextualized_signal_claim(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Store a signal as a bounded claim with observation context."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["contextualized signal claim must be an object"]}
    for field in (
        "signal_claim_id",
        "source_structure_id",
        "source_id",
        "claim",
        "observation_method",
        "affected_entity",
        "observed_at",
        "recorded_at",
        "expected_baseline",
        "observed_deviation",
        "uncertainty_rationale",
        "possible_collection_incentive",
        "next_update_trigger",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("raw_event_equals_claim") is not False:
        errors.append("raw_event_equals_claim must be false")
    uncertainty = payload.get("uncertainty")
    if (
        isinstance(uncertainty, bool)
        or not isinstance(uncertainty, (int, float))
        or not 0 <= uncertainty <= 1
    ):
        errors.append("uncertainty must be a number between 0 and 1")
    evidence_ids = payload.get("evidence_ids")
    if (
        not isinstance(evidence_ids, list)
        or not evidence_ids
        or not all(_non_empty(item) for item in evidence_ids)
        or len(evidence_ids) != len(set(evidence_ids))
    ):
        errors.append("evidence_ids must be a non-empty unique list")
    status = payload.get("claim_status")
    if status not in {"observed", "inferred", "contested"}:
        errors.append("claim_status must be observed, inferred, or contested")
    if status == "observed" and payload.get("inference_basis_ids") not in ([], None):
        errors.append("inference_basis_ids must be empty for an observed claim")
    if status == "inferred":
        inference_ids = payload.get("inference_basis_ids")
        if not isinstance(inference_ids, list) or not inference_ids:
            errors.append("inference_basis_ids must support an inferred claim")

    return {
        "valid": not errors,
        "errors": errors,
        "claim_status": status,
        "uncertainty": uncertainty,
    }

def validate_mission_cognition_wake(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Wake for plausible mission change, not isolated interestingness."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["mission cognition wake decision must be an object"]}
    for field in (
        "wake_decision_id",
        "signal_claim_id",
        "mission_id",
        "cognition_operation",
        "wake_rationale",
        "reassessment_trigger",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("interestingness_is_sufficient") is not False:
        errors.append("interestingness_is_sufficient must be false")

    candidates = payload.get("candidate_mission_changes")
    if not isinstance(candidates, list) or not candidates:
        errors.append("candidate_mission_changes must be a non-empty list")
        candidates = []
    allowed_dimensions = {
        "beneficiary",
        "desired_change",
        "mechanism",
        "constraint",
        "stop_condition",
    }
    candidate_ids = set()
    scores = []
    for index, candidate in enumerate(candidates):
        prefix = f"candidate_mission_changes[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{prefix} must be an object")
            continue
        candidate_id = candidate.get("candidate_change_id")
        if not _non_empty(candidate_id):
            errors.append(f"{prefix}.candidate_change_id must be a non-empty string")
        elif candidate_id in candidate_ids:
            errors.append(f"{prefix}.candidate_change_id must be unique")
        candidate_ids.add(candidate_id)
        if candidate.get("mission_dimension") not in allowed_dimensions:
            errors.append(f"{prefix}.mission_dimension is not recognized")
        for field in ("current_state", "possible_revision", "signal_to_revision_link"):
            if not _non_empty(candidate.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        factors = []
        for field in (
            "mission_change_probability",
            "consequence_magnitude",
            "cognition_leverage",
        ):
            value = candidate.get(field)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not 0 <= value <= 1
            ):
                errors.append(f"{prefix}.{field} must be a number between 0 and 1")
                value = 0
            factors.append(value)
        scores.append(factors[0] * factors[1] * factors[2])

    threshold = payload.get("wake_threshold")
    if (
        isinstance(threshold, bool)
        or not isinstance(threshold, (int, float))
        or not 0 < threshold <= 1
    ):
        errors.append("wake_threshold must be a number greater than 0 and at most 1")
        threshold = 1
    max_score = max(scores, default=0)
    expected_decision = "wake" if max_score >= threshold else "wait"
    decision = payload.get("decision")
    if decision not in {"wake", "wait"}:
        errors.append("decision must be wake or wait")
    elif decision != expected_decision:
        errors.append("decision must follow mission-change potential rather than interestingness")

    return {
        "valid": not errors,
        "errors": errors,
        "decision": decision,
        "max_mission_change_score": max_score,
    }

def validate_signal_thesis_integration(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Integrate bounded wake classes with explicit observation blind spots."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["signal thesis integration must be an object"]}
    for field in (
        "signal_thesis_id",
        "event_attention_policy_id",
        "source_structure_id",
        "signal_claim_id",
        "mission_wake_policy_id",
        "integration_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected_classes = {
        "value_relevant_deviation",
        "consequential_anomaly",
        "model_failure",
    }
    wake_classes = payload.get("accepted_wake_classes")
    if (
        not isinstance(wake_classes, list)
        or set(wake_classes) != expected_classes
        or len(wake_classes) != len(expected_classes)
    ):
        errors.append("accepted_wake_classes must contain exactly the three signal thesis wake classes")
    if payload.get("unsupported_event_can_wake") is not False:
        errors.append("unsupported_event_can_wake must be false")
    if payload.get("blind_spot_is_self_interpreting") is not False:
        errors.append("blind_spot_is_self_interpreting must be false")

    blind_spots = payload.get("observation_blind_spot_ids")
    if (
        not isinstance(blind_spots, list)
        or not blind_spots
        or not all(_non_empty(item) for item in blind_spots)
        or len(blind_spots) != len(set(blind_spots))
    ):
        errors.append("observation_blind_spot_ids must be a non-empty unique list")

    cases = payload.get("wake_cases")
    if not isinstance(cases, list) or not cases:
        errors.append("wake_cases must be a non-empty list")
        cases = []
    case_ids = set()
    represented_classes = set()
    for index, case in enumerate(cases):
        prefix = f"wake_cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{prefix} must be an object")
            continue
        case_id = case.get("wake_case_id")
        if not _non_empty(case_id):
            errors.append(f"{prefix}.wake_case_id must be a non-empty string")
        elif case_id in case_ids:
            errors.append(f"{prefix}.wake_case_id must be unique")
        case_ids.add(case_id)
        wake_class = case.get("wake_class")
        if wake_class not in expected_classes:
            errors.append(f"{prefix}.wake_class is not recognized")
        else:
            represented_classes.add(wake_class)
        for field in (
            "basis_record_id",
            "mission_change_candidate_id",
            "evidence_id",
            "why_cognition_could_change_mission",
        ):
            if not _non_empty(case.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if represented_classes != expected_classes:
        errors.append("wake_cases must demonstrate every accepted wake class")
    if payload.get("conclusion") != "signal_thesis_supported":
        errors.append("conclusion must be signal_thesis_supported")

    return {
        "valid": not errors,
        "errors": errors,
        "represented_wake_classes": sorted(represented_classes),
        "blind_spot_count": len(blind_spots) if isinstance(blind_spots, list) else 0,
    }

def validate_contextual_governance_rule(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Bind a formal rule to its principle, scope, loopholes, and context review."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["contextual governance rule must be an object"]}
    for field in (
        "governance_rule_id",
        "principle_text",
        "formal_condition",
        "formal_action",
        "intended_scope",
        "principle_rationale",
        "context_review_question",
        "exception_test",
        "revision_trigger",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("natural_language_alone_is_authoritative") is not False:
        errors.append("natural_language_alone_is_authoritative must be false")
    if payload.get("formal_rule_is_context_complete") is not False:
        errors.append("formal_rule_is_context_complete must be false")
    loopholes = payload.get("known_loopholes")
    if (
        not isinstance(loopholes, list)
        or not loopholes
        or not all(_non_empty(item) for item in loopholes)
    ):
        errors.append("known_loopholes must be a non-empty list")

    applications = payload.get("application_cases")
    if not isinstance(applications, list) or not applications:
        errors.append("application_cases must be a non-empty list")
        applications = []
    case_ids = set()
    for index, case in enumerate(applications):
        prefix = f"application_cases[{index}]"
        if not isinstance(case, dict):
            errors.append(f"{prefix} must be an object")
            continue
        case_id = case.get("application_case_id")
        if not _non_empty(case_id):
            errors.append(f"{prefix}.application_case_id must be a non-empty string")
        elif case_id in case_ids:
            errors.append(f"{prefix}.application_case_id must be unique")
        case_ids.add(case_id)
        if not isinstance(case.get("formal_condition_matched"), bool):
            errors.append(f"{prefix}.formal_condition_matched must be boolean")
        for field in (
            "case_context",
            "contextual_factor",
            "principle_alignment",
            "decision_rationale",
        ):
            if not _non_empty(case.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if case.get("decision") not in {"apply", "decline", "escalate"}:
            errors.append(f"{prefix}.decision is not recognized")

    return {
        "valid": not errors,
        "errors": errors,
        "application_case_count": len(applications),
    }

def validate_constitution_layer_registry(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Represent distinct constitutional layers without flattening authority."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["constitution layer registry must be an object"]}
    for field in ("layer_registry_id", "constitution_version_id", "interpretation_protocol"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("layers_have_equal_authority") is not False:
        errors.append("layers_have_equal_authority must be false")
    required_types = {
        "hard_prohibition",
        "defeasible_principle",
        "learned_preference",
        "precedent",
        "uncertainty",
        "authority_grant",
    }
    layers = payload.get("layers")
    if not isinstance(layers, list):
        errors.append("layers must be a list")
        layers = []
    layer_types = set()
    layer_ids = set()
    for index, layer in enumerate(layers):
        prefix = f"layers[{index}]"
        if not isinstance(layer, dict):
            errors.append(f"{prefix} must be an object")
            continue
        layer_id = layer.get("layer_id")
        if not _non_empty(layer_id):
            errors.append(f"{prefix}.layer_id must be a non-empty string")
        elif layer_id in layer_ids:
            errors.append(f"{prefix}.layer_id must be unique")
        layer_ids.add(layer_id)
        layer_type = layer.get("layer_type")
        if layer_type not in required_types:
            errors.append(f"{prefix}.layer_type is not recognized")
        elif layer_type in layer_types:
            errors.append(f"{prefix}.layer_type must be unique")
        layer_types.add(layer_type)
        for field in (
            "interpretive_role",
            "mutation_authority",
            "review_trigger",
        ):
            if not _non_empty(layer.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        content_ids = layer.get("content_ids")
        if (
            not isinstance(content_ids, list)
            or not content_ids
            or not all(_non_empty(item) for item in content_ids)
        ):
            errors.append(f"{prefix}.content_ids must be a non-empty list")
        if not isinstance(layer.get("overrideable"), bool):
            errors.append(f"{prefix}.overrideable must be boolean")
        if layer_type == "hard_prohibition" and layer.get("overrideable") is not False:
            errors.append(f"{prefix} hard_prohibition must not be overrideable")
        if layer_type == "uncertainty" and layer.get("can_authorize_action") is not False:
            errors.append(f"{prefix} uncertainty must not authorize action")
        if layer_type == "authority_grant" and not _non_empty(layer.get("authority_scope")):
            errors.append(f"{prefix}.authority_scope must be a non-empty string")
    if layer_types != required_types:
        errors.append("layers must contain exactly the six constitutional layer types")

    return {
        "valid": not errors,
        "errors": errors,
        "layer_types": sorted(layer_types),
    }

