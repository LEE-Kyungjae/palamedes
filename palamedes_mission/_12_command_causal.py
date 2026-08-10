from __future__ import annotations

from typing import Any, Dict, List
from ._01_kinds_value import _non_empty
from ._11_purpose_signal import validate_complete_mission_candidate_basis, validate_separated_causal_sketch


def validate_evaluate_wake_command(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate wake from frozen reads and return one bounded cognitive operation."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["evaluate wake command must be an object"]}
    for field in (
        "command_id",
        "frontier_snapshot_id",
        "frontier_fingerprint",
        "constitution_state_id",
        "constitution_fingerprint",
        "evaluation_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    signal_ids = payload.get("signal_ids")
    if (
        not isinstance(signal_ids, list)
        or not signal_ids
        or not all(_non_empty(item) for item in signal_ids)
        or len(signal_ids) != len(set(signal_ids))
    ):
        errors.append("signal_ids must be a non-empty unique string list")
    operation_by_insufficiency = {
        "missing_observation": "expand_observation",
        "ambiguous_meaning": "reinterpret_meaning",
        "weak_causal_model": "revise_causal_model",
        "missing_alternative": "invent_mission",
        "unexamined_consequence": "criticize_consequence",
        "unresolved_choice": "select_mission",
        "overspecified_handoff": "compress_contract",
        "evidence_not_yet_available": "wait_for_evidence",
    }
    result = payload.get("wake_result")
    if not isinstance(result, dict):
        errors.append("wake_result must be an object")
        result = {}
    decision = result.get("decision")
    if decision not in {"wake", "no_wake"}:
        errors.append("wake_result.decision must be wake or no_wake")
    if not _non_empty(result.get("decision_rationale")):
        errors.append("wake_result.decision_rationale must be a non-empty string")
    budget = result.get("cognitive_budget")
    if not isinstance(budget, dict):
        errors.append("wake_result.cognitive_budget must be an object")
        budget = {}
    available_tokens = payload.get("available_token_budget")
    available_operations = payload.get("available_operation_budget")
    if not isinstance(available_tokens, int) or isinstance(available_tokens, bool) or available_tokens < 0:
        errors.append("available_token_budget must be a non-negative integer")
    if not isinstance(available_operations, int) or isinstance(available_operations, bool) or available_operations < 0:
        errors.append("available_operation_budget must be a non-negative integer")
    tokens = budget.get("max_tokens")
    operations = budget.get("max_operations")
    if not isinstance(tokens, int) or isinstance(tokens, bool) or tokens < 0:
        errors.append("wake_result.cognitive_budget.max_tokens must be a non-negative integer")
        tokens = 0
    if not isinstance(operations, int) or isinstance(operations, bool) or operations < 0:
        errors.append("wake_result.cognitive_budget.max_operations must be a non-negative integer")
        operations = 0
    if isinstance(available_tokens, int) and tokens > available_tokens:
        errors.append("wake token budget must not exceed available_token_budget")
    if isinstance(available_operations, int) and operations > available_operations:
        errors.append("wake operation budget must not exceed available_operation_budget")
    for field in ("expires_at", "stop_condition"):
        if not _non_empty(budget.get(field)):
            errors.append(f"wake_result.cognitive_budget.{field} must be a non-empty string")
    if decision == "wake":
        insufficiency = result.get("named_insufficiency")
        if insufficiency not in operation_by_insufficiency:
            errors.append("wake_result.named_insufficiency is not recognized")
        if result.get("cognitive_operation") != operation_by_insufficiency.get(insufficiency):
            errors.append("wake_result.cognitive_operation must match named_insufficiency")
        if tokens <= 0 or operations != 1:
            errors.append("wake decision requires positive tokens and exactly one cognitive operation")
    elif decision == "no_wake":
        if result.get("named_insufficiency") != "none":
            errors.append("no_wake decision must name insufficiency as none")
        if result.get("cognitive_operation") != "none":
            errors.append("no_wake decision must return no cognitive operation")
        if tokens != 0 or operations != 0:
            errors.append("no_wake decision must return zero cognitive budget")
    if payload.get("read_only_evaluation") is not True:
        errors.append("read_only_evaluation must be true")
    if result.get("state_mutated") is not False:
        errors.append("wake_result.state_mutated must be false")
    if result.get("wake_event_created") is not False:
        errors.append("wake_result.wake_event_created must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "decision": decision,
        "named_insufficiency": result.get("named_insufficiency"),
        "cognitive_operation": result.get("cognitive_operation"),
    }

def validate_record_competing_causal_sketches(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Record plural causal sketches with explicit signal links and no truth selection."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["record competing causal sketches must be an object"]}
    for field in (
        "command_id",
        "expected_revision_fingerprint",
        "authority_id",
        "revision_reason",
        "command_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    sketches = payload.get("causal_sketches")
    if not isinstance(sketches, list) or len(sketches) < 2:
        errors.append("causal_sketches must contain at least two competing interpretations")
        sketches = []
    sketch_ids = set()
    expected_links = set()
    for index, sketch in enumerate(sketches):
        prefix = f"causal_sketches[{index}]"
        report = validate_separated_causal_sketch(sketch)
        if not report["valid"]:
            errors.extend(f"{prefix}: {error}" for error in report["errors"])
        sketch_id = sketch.get("causal_sketch_id") if isinstance(sketch, dict) else None
        if sketch_id in sketch_ids:
            errors.append(f"{prefix}.causal_sketch_id must be unique")
        sketch_ids.add(sketch_id)
        if isinstance(sketch, dict):
            for edge in sketch.get("edges", []):
                if not isinstance(edge, dict):
                    continue
                for signal_id in edge.get("supporting_signal_ids", []):
                    expected_links.add((sketch_id, edge.get("edge_id"), signal_id, "supports"))
                for signal_id in edge.get("opposing_signal_ids", []):
                    expected_links.add((sketch_id, edge.get("edge_id"), signal_id, "opposes"))
    links = payload.get("signal_links")
    if not isinstance(links, list) or not links:
        errors.append("signal_links must be a non-empty list")
        links = []
    observed_links = set()
    link_ids = set()
    for index, link in enumerate(links):
        prefix = f"signal_links[{index}]"
        if not isinstance(link, dict):
            errors.append(f"{prefix} must be an object")
            continue
        link_id = link.get("link_id")
        if not _non_empty(link_id):
            errors.append(f"{prefix}.link_id must be a non-empty string")
        elif link_id in link_ids:
            errors.append(f"{prefix}.link_id must be unique")
        link_ids.add(link_id)
        for field in ("causal_sketch_id", "edge_id", "signal_id"):
            if not _non_empty(link.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if link.get("relation") not in {"supports", "opposes"}:
            errors.append(f"{prefix}.relation must be supports or opposes")
        observed_links.add((
            link.get("causal_sketch_id"),
            link.get("edge_id"),
            link.get("signal_id"),
            link.get("relation"),
        ))
    if observed_links != expected_links:
        errors.append("signal_links must exactly materialize every sketch edge's supporting and opposing signals")
    statuses = payload.get("sketch_statuses")
    if not isinstance(statuses, list) or len(statuses) != len(sketch_ids):
        errors.append("sketch_statuses must cover every causal sketch")
        statuses = []
    status_ids = set()
    for index, status in enumerate(statuses):
        prefix = f"sketch_statuses[{index}]"
        if not isinstance(status, dict):
            errors.append(f"{prefix} must be an object")
            continue
        status_ids.add(status.get("causal_sketch_id"))
        if status.get("status") != "plausible_unresolved":
            errors.append(f"{prefix}.status must be plausible_unresolved")
        if not _non_empty(status.get("uncertainty_rationale")):
            errors.append(f"{prefix}.uncertainty_rationale must be a non-empty string")
    if status_ids != sketch_ids:
        errors.append("sketch_statuses must reference exactly all causal sketches")
    if payload.get("truth_selected") is not False:
        errors.append("truth_selected must be false")
    if payload.get("selected_causal_sketch_id") not in ("", None):
        errors.append("selected_causal_sketch_id must be empty")
    if payload.get("rival_visibility_during_recording") is not False:
        errors.append("rival_visibility_during_recording must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "causal_sketch_ids": sorted(item for item in sketch_ids if _non_empty(item)),
        "signal_link_count": len(link_ids),
        "truth_selected": payload.get("truth_selected"),
    }

def validate_pre_rival_mission_forecast_freeze(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Freeze independently generated mission forecasts before rival inspection."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["pre rival mission forecast freeze must be an object"]}
    for field in (
        "proposal_batch_id",
        "source_bundle_id",
        "source_bundle_fingerprint",
        "rival_reveal_at",
        "batch_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    sessions = payload.get("generation_sessions")
    if not isinstance(sessions, list) or len(sessions) < 3:
        errors.append("generation_sessions must contain at least three independent proposals")
        sessions = []
    context_ids = set()
    candidate_ids = set()
    forecast_fingerprints = set()
    frozen_times = []
    for index, session in enumerate(sessions):
        prefix = f"generation_sessions[{index}]"
        if not isinstance(session, dict):
            errors.append(f"{prefix} must be an object")
            continue
        context_id = session.get("generation_context_id")
        if not _non_empty(context_id):
            errors.append(f"{prefix}.generation_context_id must be a non-empty string")
        elif context_id in context_ids:
            errors.append(f"{prefix}.generation_context_id must be unique")
        context_ids.add(context_id)
        if session.get("source_bundle_id") != payload.get("source_bundle_id"):
            errors.append(f"{prefix}.source_bundle_id must match the batch")
        if session.get("source_bundle_fingerprint") != payload.get("source_bundle_fingerprint"):
            errors.append(f"{prefix}.source_bundle_fingerprint must match the batch")
        if session.get("rival_candidate_ids_visible") != []:
            errors.append(f"{prefix}.rival_candidate_ids_visible must be empty during generation")
        candidate = session.get("mission_candidate")
        report = validate_complete_mission_candidate_basis(candidate)
        if not report["valid"]:
            errors.extend(f"{prefix}.mission_candidate: {error}" for error in report["errors"])
        candidate_id = report.get("mission_candidate_id")
        if candidate_id in candidate_ids:
            errors.append(f"{prefix} mission candidate must be unique")
        candidate_ids.add(candidate_id)
        forecast = session.get("frozen_forecast")
        if not isinstance(forecast, dict):
            errors.append(f"{prefix}.frozen_forecast must be an object")
            forecast = {}
        for field in (
            "forecast_id",
            "expected_outcome",
            "time_horizon",
            "resource_forecast",
            "harm_forecast",
            "disconfirmation_forecast",
            "forecast_fingerprint",
            "frozen_at",
        ):
            if not _non_empty(forecast.get(field)):
                errors.append(f"{prefix}.frozen_forecast.{field} must be a non-empty string")
        probability = forecast.get("outcome_probability")
        if not isinstance(probability, (int, float)) or isinstance(probability, bool) or not 0 <= probability <= 1:
            errors.append(f"{prefix}.frozen_forecast.outcome_probability must be between zero and one")
        fingerprint = forecast.get("forecast_fingerprint")
        if fingerprint in forecast_fingerprints:
            errors.append(f"{prefix}.frozen_forecast.forecast_fingerprint must be unique")
        forecast_fingerprints.add(fingerprint)
        if _non_empty(forecast.get("frozen_at")):
            frozen_times.append(forecast["frozen_at"])
        if session.get("forecast_mutable_after_reveal") is not False:
            errors.append(f"{prefix}.forecast_mutable_after_reveal must be false")
    reveal_at = payload.get("rival_reveal_at")
    if _non_empty(reveal_at) and (not frozen_times or any(not frozen_at < reveal_at for frozen_at in frozen_times)):
        errors.append("every forecast must be frozen before rival_reveal_at")
    if payload.get("sessions_share_generation_context") is not False:
        errors.append("sessions_share_generation_context must be false")
    if payload.get("rivals_visible_before_forecast_freeze") is not False:
        errors.append("rivals_visible_before_forecast_freeze must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "generation_context_ids": sorted(item for item in context_ids if _non_empty(item)),
        "mission_candidate_ids": sorted(item for item in candidate_ids if _non_empty(item)),
        "forecast_count": len(forecast_fingerprints),
    }

def validate_nonmutating_mission_critique(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Record axis-specific critique evidence without mutating the candidate."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["nonmutating mission critique must be an object"]}
    for field in (
        "critique_record_id",
        "mission_candidate_id",
        "candidate_fingerprint_before",
        "candidate_fingerprint_after",
        "critic_context_id",
        "critique_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("candidate_fingerprint_after") != payload.get("candidate_fingerprint_before"):
        errors.append("candidate fingerprint must remain unchanged by critique")
    expected_axes = {
        "beneficiary",
        "causal",
        "constitutional",
        "resource",
        "harm",
        "disconfirmation",
        "novelty",
    }
    attacks = payload.get("axis_attacks")
    if not isinstance(attacks, list) or len(attacks) != len(expected_axes):
        errors.append("axis_attacks must cover all seven critique axes")
        attacks = []
    axes = set()
    attack_ids = set()
    for index, attack in enumerate(attacks):
        prefix = f"axis_attacks[{index}]"
        if not isinstance(attack, dict):
            errors.append(f"{prefix} must be an object")
            continue
        attack_id = attack.get("attack_id")
        if not _non_empty(attack_id):
            errors.append(f"{prefix}.attack_id must be a non-empty string")
        elif attack_id in attack_ids:
            errors.append(f"{prefix}.attack_id must be unique")
        attack_ids.add(attack_id)
        axes.add(attack.get("axis"))
        for field in (
            "attack",
            "evidence_id",
            "candidate_claim_addressed",
            "withdrawal_condition",
            "withdrawal_evidence_needed",
        ):
            if not _non_empty(attack.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if attack.get("severity") not in {"low", "medium", "high", "critical"}:
            errors.append(f"{prefix}.severity is not recognized")
        if attack.get("status") != "active_until_withdrawal_condition":
            errors.append(f"{prefix}.status must be active_until_withdrawal_condition")
    if axes != expected_axes:
        errors.append("axis_attacks must cover beneficiary, causal, constitutional, resource, harm, disconfirmation, and novelty exactly once")
    if payload.get("candidate_mutated") is not False:
        errors.append("candidate_mutated must be false")
    if payload.get("critique_auto_selects_or_rejects") is not False:
        errors.append("critique_auto_selects_or_rejects must be false")
    if payload.get("critique_epistemic_role") != "evidence":
        errors.append("critique_epistemic_role must be evidence")
    return {
        "valid": not errors,
        "errors": errors,
        "axes": sorted(item for item in axes if _non_empty(item)),
        "attack_ids": sorted(item for item in attack_ids if _non_empty(item)),
        "candidate_unchanged": payload.get("candidate_fingerprint_after") == payload.get("candidate_fingerprint_before"),
    }

def validate_four_mode_mission_selection(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Select commitment, exploration, probe, or deferral from frozen evidence."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["four mode mission selection must be an object"]}
    for field in (
        "selection_record_id",
        "proposal_batch_id",
        "mission_tournament_id",
        "constitution_state_id",
        "selection_authority_id",
        "selection_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    evidence = payload.get("candidate_evidence")
    if not isinstance(evidence, list) or len(evidence) < 3:
        errors.append("candidate_evidence must contain at least three frozen candidates")
        evidence = []
    candidate_ids = set()
    for index, record in enumerate(evidence):
        prefix = f"candidate_evidence[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix} must be an object")
            continue
        candidate_id = record.get("mission_candidate_id")
        if not _non_empty(candidate_id):
            errors.append(f"{prefix}.mission_candidate_id must be a non-empty string")
        elif candidate_id in candidate_ids:
            errors.append(f"{prefix}.mission_candidate_id must be unique")
        candidate_ids.add(candidate_id)
        for field in ("candidate_fingerprint", "forecast_fingerprint"):
            if not _non_empty(record.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        critiques = record.get("critique_record_ids")
        if (
            not isinstance(critiques, list)
            or not critiques
            or not all(_non_empty(item) for item in critiques)
            or len(critiques) != len(set(critiques))
        ):
            errors.append(f"{prefix}.critique_record_ids must be a non-empty unique string list")
        if record.get("frozen") is not True:
            errors.append(f"{prefix}.frozen must be true")
    decision = payload.get("decision")
    if decision not in {"commit", "bounded_exploration", "discriminating_probe", "defer"}:
        errors.append("decision must be commit, bounded_exploration, discriminating_probe, or defer")
    details = payload.get("decision_details")
    if not isinstance(details, dict):
        errors.append("decision_details must be an object")
        details = {}
    selected_ids = details.get("selected_mission_candidate_ids")
    if not isinstance(selected_ids, list) or len(selected_ids) != len(set(selected_ids)):
        errors.append("decision_details.selected_mission_candidate_ids must be a unique list")
        selected_ids = []
    if not set(selected_ids).issubset(candidate_ids):
        errors.append("selected mission candidates must reference frozen candidate evidence")
    if decision == "commit":
        if len(selected_ids) != 1:
            errors.append("commit must select exactly one mission candidate")
        for field in ("commitment_scope", "commitment_review_trigger"):
            if not _non_empty(details.get(field)):
                errors.append(f"commit decision requires {field}")
    elif decision == "bounded_exploration":
        if not 1 <= len(selected_ids) < len(candidate_ids):
            errors.append("bounded_exploration must select a strict non-empty subset of candidates")
        for field in ("exploration_budget", "expires_at", "stop_condition", "learning_objective"):
            if not _non_empty(details.get(field)):
                errors.append(f"bounded_exploration requires {field}")
    elif decision == "discriminating_probe":
        if len(selected_ids) < 2:
            errors.append("discriminating_probe must retain at least two competing candidates")
        for field in ("probe_id", "ambiguity_id", "probe_budget", "maximum_harm", "expires_at", "stop_condition"):
            if not _non_empty(details.get(field)):
                errors.append(f"discriminating_probe requires {field}")
    elif decision == "defer":
        if selected_ids:
            errors.append("defer must not select a mission candidate")
        for field in ("missing_condition", "wake_trigger", "review_at"):
            if not _non_empty(details.get(field)):
                errors.append(f"defer requires {field}")
    if payload.get("candidates_mutated_during_selection") is not False:
        errors.append("candidates_mutated_during_selection must be false")
    if payload.get("critiques_treated_as_authority") is not False:
        errors.append("critiques_treated_as_authority must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "decision": decision,
        "candidate_ids": sorted(item for item in candidate_ids if _non_empty(item)),
        "selected_mission_candidate_ids": selected_ids,
    }

def validate_governed_mission_contract_issue(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Issue a mission contract only from committed selection and constitutional trace."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["governed mission contract issue must be an object"]}
    for field in (
        "issue_command_id",
        "selection_record_id",
        "selection_record_fingerprint",
        "mission_tournament_id",
        "mission_tournament_fingerprint",
        "selected_mission_candidate_id",
        "selected_candidate_fingerprint",
        "issue_authority_id",
        "issue_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("selection_decision") != "commit":
        errors.append("selection_decision must be commit before issuing a planner contract")
    trace = payload.get("constitutional_trace")
    if not isinstance(trace, dict):
        errors.append("constitutional_trace must be an object")
        trace = {}
    for field in (
        "constitutional_interpretation_id",
        "constitution_state_id",
        "constitution_fingerprint",
        "trace_rationale",
    ):
        if not _non_empty(trace.get(field)):
            errors.append(f"constitutional_trace.{field} must be a non-empty string")
    applications = trace.get("clause_applications")
    if not isinstance(applications, list) or not applications:
        errors.append("constitutional_trace.clause_applications must be a non-empty list")
        applications = []
    clause_ids = set()
    for index, application in enumerate(applications):
        prefix = f"constitutional_trace.clause_applications[{index}]"
        if not isinstance(application, dict):
            errors.append(f"{prefix} must be an object")
            continue
        clause_id = application.get("clause_id")
        if not _non_empty(clause_id):
            errors.append(f"{prefix}.clause_id must be a non-empty string")
        elif clause_id in clause_ids:
            errors.append(f"{prefix}.clause_id must be unique")
        clause_ids.add(clause_id)
        for field in ("interpretation", "selection_effect", "authority_source_id"):
            if not _non_empty(application.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        precedents = application.get("precedent_ids")
        if (
            not isinstance(precedents, list)
            or len(precedents) != len(set(precedents))
            or not all(_non_empty(item) for item in precedents)
        ):
            errors.append(f"{prefix}.precedent_ids must be a unique string list")
    contract = payload.get("mission_contract")
    if not isinstance(contract, dict):
        errors.append("mission_contract must be an object")
        contract = {}
    for field in (
        "mission_contract_id",
        "contract_fingerprint",
        "situation",
        "meaning",
        "beneficiary",
        "desired_external_condition",
        "essential_causal_mechanism",
        "non_goal",
        "success_signal",
        "disconfirmation_condition",
        "authority_return_trigger",
        "issued_at",
    ):
        if not _non_empty(contract.get(field)):
            errors.append(f"mission_contract.{field} must be a non-empty string")
    if contract.get("mission_candidate_id") != payload.get("selected_mission_candidate_id"):
        errors.append("mission_contract.mission_candidate_id must match committed candidate")
    if contract.get("selection_record_id") != payload.get("selection_record_id"):
        errors.append("mission_contract.selection_record_id must match governed selection")
    if contract.get("constitutional_interpretation_id") != trace.get("constitutional_interpretation_id"):
        errors.append("mission_contract.constitutional_interpretation_id must match constitutional trace")
    if contract.get("version") != 1:
        errors.append("newly issued mission_contract.version must be one")
    if payload.get("constitutional_trace_verified") is not True:
        errors.append("constitutional_trace_verified must be true")
    if payload.get("free_form_issue_allowed") is not False:
        errors.append("free_form_issue_allowed must be false")
    if payload.get("tournament_bypassed") is not False:
        errors.append("tournament_bypassed must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "mission_contract_id": contract.get("mission_contract_id"),
        "selected_mission_candidate_id": payload.get("selected_mission_candidate_id"),
        "constitutional_clause_ids": sorted(item for item in clause_ids if _non_empty(item)),
    }

def validate_nonrewriting_mission_outcome_record(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Separate observed consequence from attribution and nonrewriting purpose review."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["nonrewriting mission outcome record must be an object"]}
    for field in (
        "outcome_record_id",
        "mission_contract_id",
        "mission_contract_fingerprint",
        "execution_plan_id",
        "outcome_channel_id",
        "observation_method",
        "baseline",
        "observed_consequence",
        "observed_at",
        "received_at",
        "record_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    affected = payload.get("affected_entity_ids")
    if (
        not isinstance(affected, list)
        or not affected
        or not all(_non_empty(item) for item in affected)
        or len(affected) != len(set(affected))
    ):
        errors.append("affected_entity_ids must be a non-empty unique string list")
    if payload.get("sensitivity") not in {"public", "internal", "confidential", "restricted"}:
        errors.append("sensitivity is not recognized")
    attributions = payload.get("attribution_hypotheses")
    if not isinstance(attributions, list) or len(attributions) < 2:
        errors.append("attribution_hypotheses must contain at least two competing explanations")
        attributions = []
    attribution_ids = set()
    layers = set()
    allowed_layers = {"mission", "planner", "implementation", "measurement", "timing"}
    for index, attribution in enumerate(attributions):
        prefix = f"attribution_hypotheses[{index}]"
        if not isinstance(attribution, dict):
            errors.append(f"{prefix} must be an object")
            continue
        attribution_id = attribution.get("attribution_id")
        if not _non_empty(attribution_id):
            errors.append(f"{prefix}.attribution_id must be a non-empty string")
        elif attribution_id in attribution_ids:
            errors.append(f"{prefix}.attribution_id must be unique")
        attribution_ids.add(attribution_id)
        layer = attribution.get("layer")
        layers.add(layer)
        if layer not in allowed_layers:
            errors.append(f"{prefix}.layer is not recognized")
        for field in ("hypothesis", "discriminating_observation"):
            if not _non_empty(attribution.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        confidence = attribution.get("confidence")
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
            errors.append(f"{prefix}.confidence must be between zero and one")
        for field in ("supporting_signal_ids", "opposing_signal_ids"):
            values = attribution.get(field)
            if (
                not isinstance(values, list)
                or not values
                or not all(_non_empty(item) for item in values)
                or len(values) != len(set(values))
            ):
                errors.append(f"{prefix}.{field} must be a non-empty unique signal list")
        if attribution.get("status") != "unresolved":
            errors.append(f"{prefix}.status must be unresolved")
    trigger = payload.get("purpose_review_trigger")
    if not isinstance(trigger, dict):
        errors.append("purpose_review_trigger must be an object")
        trigger = {}
    for field in ("trigger_id", "threshold", "observed_value", "evaluation_rationale"):
        if not _non_empty(trigger.get(field)):
            errors.append(f"purpose_review_trigger.{field} must be a non-empty string")
    triggered = trigger.get("triggered")
    if not isinstance(triggered, bool):
        errors.append("purpose_review_trigger.triggered must be boolean")
    if triggered:
        for field in ("purpose_review_event_id", "review_authority_id", "wake_insufficiency"):
            if not _non_empty(trigger.get(field)):
                errors.append(f"triggered purpose review requires {field}")
    else:
        if trigger.get("purpose_review_event_id") not in ("", None):
            errors.append("untriggered purpose review must not create an event")
    if payload.get("observed_consequence_is_attribution") is not False:
        errors.append("observed_consequence_is_attribution must be false")
    if payload.get("historical_contract_rewritten") is not False:
        errors.append("historical_contract_rewritten must be false")
    if payload.get("historical_plan_rewritten") is not False:
        errors.append("historical_plan_rewritten must be false")
    if payload.get("historical_outcome_rewritten") is not False:
        errors.append("historical_outcome_rewritten must be false")
    if payload.get("mission_revised_automatically") is not False:
        errors.append("mission_revised_automatically must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "attribution_layers": sorted(item for item in layers if _non_empty(item)),
        "purpose_review_triggered": triggered,
        "outcome_record_id": payload.get("outcome_record_id"),
    }

def validate_narrow_cognitive_command_api_thesis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Integrate a narrow command API whose preconditions expose every cognitive step."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["narrow cognitive command API thesis must be an object"]}
    for field in ("api_thesis_id", "command_registry_id", "revision_envelope_adapter_id", "thesis_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")

    expected_sequence = [
        (
            "record_signal",
            "validate_record_signal_command",
            [],
            "signal",
        ),
        (
            "evaluate_wake",
            "validate_evaluate_wake_command",
            ["signal"],
            "wake_evaluation",
        ),
        (
            "record_competing_causal_sketches",
            "validate_record_competing_causal_sketches",
            ["signal", "wake_evaluation"],
            "causal_sketch_set",
        ),
        (
            "freeze_pre_rival_mission_forecasts",
            "validate_pre_rival_mission_forecast_freeze",
            ["causal_sketch_set"],
            "frozen_mission_forecast_set",
        ),
        (
            "record_mission_critiques",
            "validate_nonmutating_mission_critique",
            ["frozen_mission_forecast_set"],
            "mission_critique_set",
        ),
        (
            "select_mission_mode",
            "validate_four_mode_mission_selection",
            ["frozen_mission_forecast_set", "mission_critique_set"],
            "mission_selection",
        ),
        (
            "issue_mission_contract",
            "validate_governed_mission_contract_issue",
            ["mission_selection"],
            "mission_contract",
        ),
        (
            "record_mission_outcome",
            "validate_nonrewriting_mission_outcome_record",
            ["mission_contract"],
            "mission_outcome",
        ),
    ]
    commands = payload.get("commands")
    if not isinstance(commands, list) or len(commands) != len(expected_sequence):
        errors.append("commands must contain exactly the eight cognitive transitions")
        commands = []
    output_types: List[str] = []
    artifact_ids = set()
    for index, expected in enumerate(expected_sequence):
        if index >= len(commands):
            break
        command = commands[index]
        prefix = f"commands[{index}]"
        if not isinstance(command, dict):
            errors.append(f"{prefix} must be an object")
            continue
        name, validator_id, required_inputs, output_type = expected
        if command.get("ordinal") != index + 1:
            errors.append(f"{prefix}.ordinal must preserve cognitive sequence")
        if command.get("command") != name:
            errors.append(f"{prefix}.command must be {name}")
        if command.get("semantic_validator_id") != validator_id:
            errors.append(f"{prefix}.semantic_validator_id must be {validator_id}")
        if command.get("required_input_artifact_types") != required_inputs:
            errors.append(f"{prefix}.required_input_artifact_types must exactly match prior required outputs")
        if any(item not in output_types for item in required_inputs):
            errors.append(f"{prefix} requires an artifact not produced by an earlier command")
        if command.get("output_artifact_type") != output_type:
            errors.append(f"{prefix}.output_artifact_type must be {output_type}")
        output_types.append(output_type)
        for field in ("intent", "precondition_expression", "authority_id"):
            if not _non_empty(command.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        artifact = command.get("inspectable_output")
        if not isinstance(artifact, dict):
            errors.append(f"{prefix}.inspectable_output must be an object")
            artifact = {}
        artifact_id = artifact.get("artifact_id")
        if not _non_empty(artifact_id):
            errors.append(f"{prefix}.inspectable_output.artifact_id must be a non-empty string")
        elif artifact_id in artifact_ids:
            errors.append(f"{prefix}.inspectable_output.artifact_id must be unique")
        artifact_ids.add(artifact_id)
        if artifact.get("artifact_type") != output_type:
            errors.append(f"{prefix}.inspectable_output.artifact_type must match output_artifact_type")
        for field in ("schema_id", "fingerprint", "provenance_record_id"):
            if not _non_empty(artifact.get(field)):
                errors.append(f"{prefix}.inspectable_output.{field} must be a non-empty string")
        if artifact.get("independently_retrievable") is not True:
            errors.append(f"{prefix}.inspectable_output.independently_retrievable must be true")
        if artifact.get("independently_validatable") is not True:
            errors.append(f"{prefix}.inspectable_output.independently_validatable must be true")
        if command.get("preconditions_checked_before_execution") is not True:
            errors.append(f"{prefix}.preconditions_checked_before_execution must be true")
        if command.get("hidden_state_transition") is not False:
            errors.append(f"{prefix}.hidden_state_transition must be false")
        if command.get("implicit_downstream_execution") is not False:
            errors.append(f"{prefix}.implicit_downstream_execution must be false")

    required_guarantees = (
        "generic_create_endpoint_exposed",
        "commands_may_skip_preconditions",
        "intermediate_artifacts_collapsed",
        "model_may_mutate_hidden_state",
        "outcome_may_rewrite_history",
    )
    for guarantee in required_guarantees:
        if payload.get(guarantee) is not False:
            errors.append(f"{guarantee} must be false")
    if payload.get("api_thesis_decision") != "integrated":
        errors.append("api_thesis_decision must be integrated")
    return {
        "valid": not errors,
        "errors": errors,
        "command_count": len(commands),
        "inspectable_artifact_count": len(artifact_ids),
        "output_artifact_types": output_types,
        "api_thesis_decision": payload.get("api_thesis_decision"),
    }

def validate_model_multiplicity_tradeoff(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Compare single- and multi-model cognition without treating diversity as free."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["model multiplicity tradeoff must be an object"]}
    for field in ("tradeoff_id", "cognitive_case_id", "frozen_input_fingerprint", "evaluation_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    conditions = payload.get("conditions")
    if not isinstance(conditions, list) or len(conditions) != 2:
        errors.append("conditions must contain exactly single_model and multi_model")
        conditions = []
    expected_modes = {"single_model", "multi_model"}
    modes = set()
    condition_ids = set()
    fingerprints = set()
    for index, condition in enumerate(conditions):
        prefix = f"conditions[{index}]"
        if not isinstance(condition, dict):
            errors.append(f"{prefix} must be an object")
            continue
        condition_id = condition.get("condition_id")
        if not _non_empty(condition_id):
            errors.append(f"{prefix}.condition_id must be a non-empty string")
        elif condition_id in condition_ids:
            errors.append(f"{prefix}.condition_id must be unique")
        condition_ids.add(condition_id)
        mode = condition.get("mode")
        if mode not in expected_modes:
            errors.append(f"{prefix}.mode must be single_model or multi_model")
        modes.add(mode)
        if condition.get("input_fingerprint") != payload.get("frozen_input_fingerprint"):
            errors.append(f"{prefix}.input_fingerprint must match frozen_input_fingerprint")
        for field in ("assignment_manifest_id", "assignment_manifest_fingerprint", "output_artifact_id"):
            if not _non_empty(condition.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        fingerprint = condition.get("assignment_manifest_fingerprint")
        fingerprints.add(fingerprint)
        calls = condition.get("model_calls")
        if not isinstance(calls, list) or not calls:
            errors.append(f"{prefix}.model_calls must be a non-empty list")
            calls = []
        model_ids = set()
        call_ids = set()
        total_tokens = 0
        total_cost = 0.0
        for call_index, call in enumerate(calls):
            call_prefix = f"{prefix}.model_calls[{call_index}]"
            if not isinstance(call, dict):
                errors.append(f"{call_prefix} must be an object")
                continue
            for field in ("call_id", "model_id", "provider_id", "prompt_fingerprint", "response_fingerprint"):
                if not _non_empty(call.get(field)):
                    errors.append(f"{call_prefix}.{field} must be a non-empty string")
            call_id = call.get("call_id")
            if call_id in call_ids:
                errors.append(f"{call_prefix}.call_id must be unique within the condition")
            call_ids.add(call_id)
            model_ids.add(call.get("model_id"))
            tokens = call.get("token_count")
            cost = call.get("cost_usd")
            if not isinstance(tokens, int) or isinstance(tokens, bool) or tokens <= 0:
                errors.append(f"{call_prefix}.token_count must be a positive integer")
            else:
                total_tokens += tokens
            if not isinstance(cost, (int, float)) or isinstance(cost, bool) or cost < 0:
                errors.append(f"{call_prefix}.cost_usd must be non-negative")
            else:
                total_cost += float(cost)
        if mode == "single_model" and len(model_ids) != 1:
            errors.append(f"{prefix} single_model must use exactly one model_id")
        if mode == "multi_model" and len(model_ids) < 2:
            errors.append(f"{prefix} multi_model must use at least two model_ids")
        ledger = condition.get("resource_ledger")
        if not isinstance(ledger, dict):
            errors.append(f"{prefix}.resource_ledger must be an object")
            ledger = {}
        if ledger.get("total_calls") != len(calls):
            errors.append(f"{prefix}.resource_ledger.total_calls must match model_calls")
        if ledger.get("total_tokens") != total_tokens:
            errors.append(f"{prefix}.resource_ledger.total_tokens must match model_calls")
        ledger_cost = ledger.get("total_cost_usd")
        if not isinstance(ledger_cost, (int, float)) or abs(float(ledger_cost) - total_cost) > 1e-9:
            errors.append(f"{prefix}.resource_ledger.total_cost_usd must match model_calls")
        for field in ("frame_diversity_score", "cross_run_reproducibility_score"):
            value = condition.get(field)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
                errors.append(f"{prefix}.{field} must be between 0 and 1")
        if not _non_empty(condition.get("measurement_method")):
            errors.append(f"{prefix}.measurement_method must be a non-empty string")
    if modes != expected_modes:
        errors.append("conditions must cover single_model and multi_model exactly once")
    if len(fingerprints) != 2:
        errors.append("each condition must preserve a distinct assignment manifest")
    if payload.get("same_task_and_input") is not True:
        errors.append("same_task_and_input must be true")
    if payload.get("same_non_model_budget") is not True:
        errors.append("same_non_model_budget must be true")
    if payload.get("diversity_assumed_better") is not False:
        errors.append("diversity_assumed_better must be false")
    if payload.get("cost_ignored") is not False:
        errors.append("cost_ignored must be false")
    if payload.get("reproducibility_ignored") is not False:
        errors.append("reproducibility_ignored must be false")
    decision = payload.get("selection_rule")
    if not isinstance(decision, dict):
        errors.append("selection_rule must be an object")
        decision = {}
    for field in ("minimum_diversity_gain", "maximum_cost_multiplier", "minimum_reproducibility"):
        value = decision.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
            errors.append(f"selection_rule.{field} must be non-negative")
    if not _non_empty(decision.get("fallback")):
        errors.append("selection_rule.fallback must be a non-empty string")
    return {
        "valid": not errors,
        "errors": errors,
        "condition_modes": sorted(item for item in modes if _non_empty(item)),
        "condition_count": len(conditions),
    }

def validate_provider_neutral_cognitive_roles(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Define cognitive responsibilities independently of model provider topology."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["provider neutral cognitive roles must be an object"]}
    for field in ("role_topology_id", "command_api_thesis_id", "assignment_policy_id", "topology_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected_roles = {
        "interpreter": (
            ["signal", "constitution"],
            "causal_sketch_set",
            ["select_mission", "issue_contract", "rewrite_outcome"],
        ),
        "inventor": (
            ["causal_sketch_set", "constitution"],
            "frozen_mission_forecast_set",
            ["select_mission", "issue_contract", "rewrite_signal"],
        ),
        "adversary": (
            ["frozen_mission_forecast_set", "constitution"],
            "mission_critique_set",
            ["mutate_candidate", "select_mission", "issue_contract"],
        ),
        "selector": (
            ["frozen_mission_forecast_set", "mission_critique_set", "constitution"],
            "mission_selection",
            ["mutate_candidate", "issue_contract", "rewrite_critique"],
        ),
        "outcome_analyst": (
            ["mission_contract", "mission_outcome"],
            "outcome_attribution_set",
            ["rewrite_contract", "rewrite_plan", "revise_mission_automatically"],
        ),
    }
    roles = payload.get("roles")
    if not isinstance(roles, list) or len(roles) != len(expected_roles):
        errors.append("roles must contain exactly five provider-neutral cognitive roles")
        roles = []
    observed_roles = set()
    for index, role in enumerate(roles):
        prefix = f"roles[{index}]"
        if not isinstance(role, dict):
            errors.append(f"{prefix} must be an object")
            continue
        role_id = role.get("role")
        observed_roles.add(role_id)
        expected = expected_roles.get(role_id)
        if expected is None:
            errors.append(f"{prefix}.role is not recognized")
            continue
        input_types, output_type, forbidden = expected
        if role.get("allowed_input_artifact_types") != input_types:
            errors.append(f"{prefix}.allowed_input_artifact_types must match the role boundary")
        if role.get("output_artifact_type") != output_type:
            errors.append(f"{prefix}.output_artifact_type must be {output_type}")
        if role.get("forbidden_authorities") != forbidden:
            errors.append(f"{prefix}.forbidden_authorities must match the role boundary")
        for field in ("responsibility", "completion_criterion", "semantic_validator_id"):
            if not _non_empty(role.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if role.get("provider_id") not in ("", None):
            errors.append(f"{prefix}.provider_id must be unbound in the role definition")
        if role.get("model_id") not in ("", None):
            errors.append(f"{prefix}.model_id must be unbound in the role definition")
        if role.get("may_assume_other_role_authority") is not False:
            errors.append(f"{prefix}.may_assume_other_role_authority must be false")
    if observed_roles != set(expected_roles):
        errors.append("roles must cover interpreter, inventor, adversary, selector, and outcome_analyst exactly once")
    assignment = payload.get("runtime_assignment_policy")
    if not isinstance(assignment, dict):
        errors.append("runtime_assignment_policy must be an object")
        assignment = {}
    if assignment.get("provider_count_minimum") != 1:
        errors.append("runtime_assignment_policy.provider_count_minimum must be 1")
    if assignment.get("distinct_provider_per_role_required") is not False:
        errors.append("runtime_assignment_policy.distinct_provider_per_role_required must be false")
    if assignment.get("distinct_model_per_role_required") is not False:
        errors.append("runtime_assignment_policy.distinct_model_per_role_required must be false")
    if assignment.get("assignment_manifest_required") is not True:
        errors.append("runtime_assignment_policy.assignment_manifest_required must be true")
    for field in ("selection_basis", "reassignment_trigger"):
        if not _non_empty(assignment.get(field)):
            errors.append(f"runtime_assignment_policy.{field} must be a non-empty string")
    if payload.get("provider_neutral") is not True:
        errors.append("provider_neutral must be true")
    if payload.get("multiple_providers_required") is not False:
        errors.append("multiple_providers_required must be false")
    if payload.get("role_boundaries_depend_on_provider") is not False:
        errors.append("role_boundaries_depend_on_provider must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "roles": sorted(item for item in observed_roles if _non_empty(item)),
        "role_count": len(observed_roles),
        "provider_neutral": payload.get("provider_neutral"),
    }

def validate_partitioned_inventor_independence(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require intentionally distinct evidence partitions and pre-rival freezing."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["partitioned inventor independence must be an object"]}
    for field in ("independence_run_id", "role_topology_id", "frozen_frontier_fingerprint", "partition_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    shared_evidence = payload.get("shared_evidence_ids")
    if (
        not isinstance(shared_evidence, list)
        or not shared_evidence
        or not all(_non_empty(item) for item in shared_evidence)
        or len(shared_evidence) != len(set(shared_evidence))
    ):
        errors.append("shared_evidence_ids must be a non-empty unique string list")
        shared_evidence = []
    inventors = payload.get("inventors")
    if not isinstance(inventors, list) or len(inventors) < 2:
        errors.append("inventors must contain at least two independent inventor assignments")
        inventors = []
    inventor_ids = set()
    partition_ids = set()
    candidate_ids = set()
    exclusive_sets = []
    for index, inventor in enumerate(inventors):
        prefix = f"inventors[{index}]"
        if not isinstance(inventor, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in (
            "inventor_assignment_id",
            "evidence_partition_id",
            "partition_fingerprint",
            "candidate_id",
            "candidate_fingerprint",
            "generation_started_at",
            "candidate_frozen_at",
        ):
            if not _non_empty(inventor.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        inventor_id = inventor.get("inventor_assignment_id")
        partition_id = inventor.get("evidence_partition_id")
        candidate_id = inventor.get("candidate_id")
        if inventor_id in inventor_ids:
            errors.append(f"{prefix}.inventor_assignment_id must be unique")
        if partition_id in partition_ids:
            errors.append(f"{prefix}.evidence_partition_id must be unique")
        if candidate_id in candidate_ids:
            errors.append(f"{prefix}.candidate_id must be unique")
        inventor_ids.add(inventor_id)
        partition_ids.add(partition_id)
        candidate_ids.add(candidate_id)
        if inventor.get("shared_evidence_ids") != shared_evidence:
            errors.append(f"{prefix}.shared_evidence_ids must exactly match the frozen shared evidence")
        exclusive = inventor.get("exclusive_evidence_ids")
        if (
            not isinstance(exclusive, list)
            or not exclusive
            or not all(_non_empty(item) for item in exclusive)
            or len(exclusive) != len(set(exclusive))
        ):
            errors.append(f"{prefix}.exclusive_evidence_ids must be a non-empty unique string list")
            exclusive = []
        exclusive_set = set(exclusive)
        if exclusive_set.intersection(shared_evidence):
            errors.append(f"{prefix}.exclusive_evidence_ids must not duplicate shared evidence")
        exclusive_sets.append(exclusive_set)
        if inventor.get("other_candidate_ids_visible_before_freeze") != []:
            errors.append(f"{prefix}.other_candidate_ids_visible_before_freeze must be empty")
        if inventor.get("other_candidate_content_visible_before_freeze") is not False:
            errors.append(f"{prefix}.other_candidate_content_visible_before_freeze must be false")
        if inventor.get("candidate_frozen_before_rival_access") is not True:
            errors.append(f"{prefix}.candidate_frozen_before_rival_access must be true")
        if inventor.get("post_freeze_mutation_allowed") is not False:
            errors.append(f"{prefix}.post_freeze_mutation_allowed must be false")
        for field in ("partition_intent", "candidate_generation_instruction"):
            if not _non_empty(inventor.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    for left in range(len(exclusive_sets)):
        for right in range(left + 1, len(exclusive_sets)):
            if exclusive_sets[left].intersection(exclusive_sets[right]):
                errors.append("exclusive evidence partitions must be pairwise disjoint")
    if len({frozenset(items) for items in exclusive_sets}) != len(exclusive_sets):
        errors.append("each inventor must receive an intentionally different exclusive evidence partition")
    reveal = payload.get("rival_reveal")
    if not isinstance(reveal, dict):
        errors.append("rival_reveal must be an object")
        reveal = {}
    if reveal.get("all_candidates_frozen") is not True:
        errors.append("rival_reveal.all_candidates_frozen must be true")
    if set(reveal.get("candidate_ids", [])) != candidate_ids:
        errors.append("rival_reveal.candidate_ids must exactly cover the frozen candidates")
    for field in ("reveal_event_id", "revealed_at"):
        if not _non_empty(reveal.get(field)):
            errors.append(f"rival_reveal.{field} must be a non-empty string")
    if payload.get("role_prompt_treated_as_independence") is not False:
        errors.append("role_prompt_treated_as_independence must be false")
    if payload.get("partition_manifest_frozen_before_generation") is not True:
        errors.append("partition_manifest_frozen_before_generation must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "inventor_count": len(inventor_ids),
        "candidate_ids": sorted(item for item in candidate_ids if _non_empty(item)),
        "partition_count": len(partition_ids),
    }

def validate_causal_sketch_interpretation_routing(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Route causal sketches through one pass only when predictions stay separable."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["causal sketch interpretation routing must be an object"]}
    for field in ("routing_record_id", "signal_set_fingerprint", "interpreter_role_id", "routing_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    sketches = payload.get("sketches")
    if not isinstance(sketches, list) or len(sketches) < 2:
        errors.append("sketches must contain at least two causal sketches")
        sketches = []
    sketch_ids = set()
    call_ids = set()
    prediction_sets = []
    discriminators = set()
    for index, sketch in enumerate(sketches):
        prefix = f"sketches[{index}]"
        if not isinstance(sketch, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("causal_sketch_id", "call_id", "sketch_fingerprint", "discriminating_observation"):
            if not _non_empty(sketch.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        sketch_id = sketch.get("causal_sketch_id")
        if sketch_id in sketch_ids:
            errors.append(f"{prefix}.causal_sketch_id must be unique")
        sketch_ids.add(sketch_id)
        call_ids.add(sketch.get("call_id"))
        predictions = sketch.get("falsifiable_predictions")
        if (
            not isinstance(predictions, list)
            or not predictions
            or not all(_non_empty(item) for item in predictions)
            or len(predictions) != len(set(predictions))
        ):
            errors.append(f"{prefix}.falsifiable_predictions must be a non-empty unique string list")
            predictions = []
        prediction_sets.append(set(predictions))
        discriminator = sketch.get("discriminating_observation")
        if discriminator in discriminators:
            errors.append(f"{prefix}.discriminating_observation must distinguish this sketch")
        discriminators.add(discriminator)
        if sketch.get("prediction_registered_before_outcome") is not True:
            errors.append(f"{prefix}.prediction_registered_before_outcome must be true")
    pairwise_separable = True
    for left in range(len(prediction_sets)):
        for right in range(left + 1, len(prediction_sets)):
            if not prediction_sets[left] or prediction_sets[left] == prediction_sets[right]:
                pairwise_separable = False
    declared_separable = payload.get("predictions_pairwise_separable")
    if declared_separable is not pairwise_separable:
        errors.append("predictions_pairwise_separable must match the registered prediction sets")
    route = payload.get("route")
    if route not in {"single_pass", "independent_calls"}:
        errors.append("route must be single_pass or independent_calls")
    if route == "single_pass":
        if not pairwise_separable:
            errors.append("single_pass requires pairwise-separable predictions")
        if len(call_ids) != 1:
            errors.append("single_pass requires every sketch to share exactly one call_id")
        if payload.get("co_generated_sketch_visibility") is not True:
            errors.append("single_pass requires co_generated_sketch_visibility true")
    elif route == "independent_calls":
        if len(call_ids) != len(sketches):
            errors.append("independent_calls requires one unique call_id per sketch")
        if payload.get("co_generated_sketch_visibility") is not False:
            errors.append("independent_calls requires co_generated_sketch_visibility false")
        if payload.get("other_sketches_visible_during_call") is not False:
            errors.append("independent_calls requires other_sketches_visible_during_call false")
    if payload.get("routing_decided_before_interpretation") is not True:
        errors.append("routing_decided_before_interpretation must be true")
    if payload.get("unseparable_sketches_collapsed_as_plural") is not False:
        errors.append("unseparable_sketches_collapsed_as_plural must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "route": route,
        "sketch_count": len(sketch_ids),
        "call_count": len(call_ids),
        "predictions_pairwise_separable": pairwise_separable,
    }

def validate_blinded_adversary_review_packet(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Expose constitution and candidate substance while withholding persuasive identity cues."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["blinded adversary review packet must be an object"]}
    for field in (
        "review_packet_id",
        "adversary_assignment_id",
        "constitution_state_id",
        "constitution_fingerprint",
        "candidate_id",
        "candidate_fingerprint",
        "packet_fingerprint",
        "review_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected_fields = [
        "situation",
        "meaning",
        "beneficiary",
        "desired_external_condition",
        "essential_causal_mechanism",
        "non_goal",
        "success_signal",
        "disconfirmation_condition",
    ]
    candidate = payload.get("structured_candidate")
    if not isinstance(candidate, dict):
        errors.append("structured_candidate must be an object")
        candidate = {}
    if list(candidate.keys()) != expected_fields:
        errors.append("structured_candidate must contain only the ordered decision-relevant fields")
    for field in expected_fields:
        if not _non_empty(candidate.get(field)):
            errors.append(f"structured_candidate.{field} must be a non-empty string")
    allowlist = payload.get("visible_input_types")
    if allowlist != ["constitution", "structured_candidate"]:
        errors.append("visible_input_types must contain only constitution and structured_candidate")
    forbidden = {
        "author_identity",
        "inventor_assignment",
        "model_identity",
        "provider_identity",
        "persuasive_discussion_history",
        "raw_chain_of_thought",
        "candidate_popularity",
    }
    withheld = payload.get("withheld_fields")
    if not isinstance(withheld, list) or set(withheld) != forbidden or len(withheld) != len(forbidden):
        errors.append("withheld_fields must exactly cover identity, persuasion, reasoning, and popularity cues")
    redaction = payload.get("redaction_attestation")
    if not isinstance(redaction, dict):
        errors.append("redaction_attestation must be an object")
        redaction = {}
    for field in ("attestation_id", "sanitizer_version", "sanitized_at", "sanitized_packet_fingerprint"):
        if not _non_empty(redaction.get(field)):
            errors.append(f"redaction_attestation.{field} must be a non-empty string")
    if redaction.get("sanitized_packet_fingerprint") != payload.get("packet_fingerprint"):
        errors.append("redaction attestation fingerprint must match packet_fingerprint")
    if redaction.get("forbidden_fields_absent") is not True:
        errors.append("redaction_attestation.forbidden_fields_absent must be true")
    if redaction.get("candidate_substance_preserved") is not True:
        errors.append("redaction_attestation.candidate_substance_preserved must be true")
    critique = payload.get("critique_output")
    if not isinstance(critique, dict):
        errors.append("critique_output must be an object")
        critique = {}
    for field in (
        "critique_record_id",
        "candidate_id",
        "constitutional_tension",
        "causal_weakness",
        "beneficiary_harm",
        "disconfirming_observation",
        "critique_fingerprint",
    ):
        if not _non_empty(critique.get(field)):
            errors.append(f"critique_output.{field} must be a non-empty string")
    if critique.get("candidate_id") != payload.get("candidate_id"):
        errors.append("critique_output.candidate_id must match candidate_id")
    if critique.get("author_guess_recorded") is not False:
        errors.append("critique_output.author_guess_recorded must be false")
    if critique.get("candidate_mutated") is not False:
        errors.append("critique_output.candidate_mutated must be false")
    if payload.get("identity_visible_to_adversary") is not False:
        errors.append("identity_visible_to_adversary must be false")
    if payload.get("persuasive_history_visible_to_adversary") is not False:
        errors.append("persuasive_history_visible_to_adversary must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "candidate_id": payload.get("candidate_id"),
        "withheld_field_count": len(withheld) if isinstance(withheld, list) else 0,
        "critique_record_id": critique.get("critique_record_id"),
    }

def validate_structured_selector_decision_packet(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require selector decisions to cite structured evidence and unresolved conflicts."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["structured selector decision packet must be an object"]}
    for field in (
        "selector_packet_id",
        "selector_assignment_id",
        "constitution_fingerprint",
        "candidate_set_fingerprint",
        "critique_set_fingerprint",
        "decision_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("visible_input_types") != ["constitution", "structured_candidates", "structured_critiques"]:
        errors.append("visible_input_types must contain only constitution, structured_candidates, and structured_critiques")
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or len(candidates) < 2:
        errors.append("candidates must contain at least two structured candidates")
        candidates = []
    candidate_ids = set()
    candidate_fields = {}
    required_candidate_fields = {
        "candidate_id",
        "candidate_fingerprint",
        "beneficiary",
        "desired_external_condition",
        "essential_causal_mechanism",
        "non_goal",
        "success_signal",
        "disconfirmation_condition",
    }
    for index, candidate in enumerate(candidates):
        prefix = f"candidates[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if set(candidate) != required_candidate_fields:
            errors.append(f"{prefix} must contain only the structured candidate fields")
        candidate_id = candidate.get("candidate_id")
        if not _non_empty(candidate_id):
            errors.append(f"{prefix}.candidate_id must be a non-empty string")
        elif candidate_id in candidate_ids:
            errors.append(f"{prefix}.candidate_id must be unique")
        candidate_ids.add(candidate_id)
        for field in required_candidate_fields - {"candidate_id"}:
            if not _non_empty(candidate.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        candidate_fields[candidate_id] = set(candidate)
    critiques = payload.get("critiques")
    if not isinstance(critiques, list) or not critiques:
        errors.append("critiques must be a non-empty list")
        critiques = []
    critique_ids = set()
    critique_candidate_ids = set()
    required_critique_fields = {
        "critique_record_id",
        "candidate_id",
        "constitutional_tension",
        "causal_weakness",
        "beneficiary_harm",
        "disconfirming_observation",
        "critique_fingerprint",
    }
    for index, critique in enumerate(critiques):
        prefix = f"critiques[{index}]"
        if not isinstance(critique, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if set(critique) != required_critique_fields:
            errors.append(f"{prefix} must contain only structured critique fields")
        critique_id = critique.get("critique_record_id")
        if not _non_empty(critique_id):
            errors.append(f"{prefix}.critique_record_id must be a non-empty string")
        elif critique_id in critique_ids:
            errors.append(f"{prefix}.critique_record_id must be unique")
        critique_ids.add(critique_id)
        critique_candidate_ids.add(critique.get("candidate_id"))
        for field in required_critique_fields - {"critique_record_id"}:
            if not _non_empty(critique.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if not candidate_ids.issubset(critique_candidate_ids):
        errors.append("every candidate must have at least one structured critique")
    decision = payload.get("selection_decision")
    if not isinstance(decision, dict):
        errors.append("selection_decision must be an object")
        decision = {}
    if decision.get("mode") not in {"commit", "bounded_exploration", "discriminating_probe", "defer"}:
        errors.append("selection_decision.mode is not recognized")
    selected_ids = decision.get("selected_candidate_ids")
    if (
        not isinstance(selected_ids, list)
        or len(selected_ids) != len(set(selected_ids))
        or any(item not in candidate_ids for item in selected_ids)
    ):
        errors.append("selection_decision.selected_candidate_ids must be a unique known-candidate list")
        selected_ids = []
    citations = decision.get("decisive_field_citations")
    if not isinstance(citations, list) or not citations:
        errors.append("selection_decision.decisive_field_citations must be non-empty")
        citations = []
    for index, citation in enumerate(citations):
        prefix = f"selection_decision.decisive_field_citations[{index}]"
        if not isinstance(citation, dict):
            errors.append(f"{prefix} must be an object")
            continue
        source_type = citation.get("source_type")
        source_id = citation.get("source_id")
        field = citation.get("field")
        if source_type == "candidate":
            if source_id not in candidate_ids or field not in candidate_fields.get(source_id, set()):
                errors.append(f"{prefix} must cite a known candidate field")
        elif source_type == "critique":
            if source_id not in critique_ids or field not in required_critique_fields:
                errors.append(f"{prefix} must cite a known critique field")
        else:
            errors.append(f"{prefix}.source_type must be candidate or critique")
        for required in ("value_fingerprint", "decision_effect"):
            if not _non_empty(citation.get(required)):
                errors.append(f"{prefix}.{required} must be a non-empty string")
    conflicts = decision.get("unresolved_conflicts")
    if not isinstance(conflicts, list) or not conflicts:
        errors.append("selection_decision.unresolved_conflicts must be non-empty")
        conflicts = []
    for index, conflict in enumerate(conflicts):
        prefix = f"selection_decision.unresolved_conflicts[{index}]"
        if not isinstance(conflict, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("conflict_id", "claim_a", "claim_b", "decision_impact", "resolution_trigger"):
            if not _non_empty(conflict.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        refs = conflict.get("candidate_ids")
        if (
            not isinstance(refs, list)
            or not refs
            or any(item not in candidate_ids for item in refs)
        ):
            errors.append(f"{prefix}.candidate_ids must reference known candidates")
    if payload.get("raw_chain_of_thought_visible") is not False:
        errors.append("raw_chain_of_thought_visible must be false")
    if payload.get("persuasive_discussion_history_visible") is not False:
        errors.append("persuasive_discussion_history_visible must be false")
    if payload.get("uncited_decisive_reason_allowed") is not False:
        errors.append("uncited_decisive_reason_allowed must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "candidate_count": len(candidate_ids),
        "critique_count": len(critique_ids),
        "decisive_citation_count": len(citations),
        "unresolved_conflict_count": len(conflicts),
    }

def validate_deterministic_semantic_ownership_boundary(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Keep mechanical governance in code and semantic judgment in bounded model calls."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["deterministic semantic ownership boundary must be an object"]}
    for field in ("ownership_boundary_id", "command_api_thesis_id", "role_topology_id", "boundary_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    deterministic = {
        "schema_validation",
        "artifact_freezing",
        "context_separation",
        "budget_enforcement",
        "provenance_recording",
        "call_routing",
    }
    semantic = {
        "causal_interpretation",
        "mission_invention",
        "adversarial_critique",
        "mission_selection_judgment",
        "outcome_attribution_hypothesis",
    }
    assignments = payload.get("responsibility_assignments")
    if not isinstance(assignments, list) or len(assignments) != len(deterministic) + len(semantic):
        errors.append("responsibility_assignments must contain exactly eleven owned responsibilities")
        assignments = []
    observed = set()
    deterministic_count = 0
    semantic_count = 0
    for index, assignment in enumerate(assignments):
        prefix = f"responsibility_assignments[{index}]"
        if not isinstance(assignment, dict):
            errors.append(f"{prefix} must be an object")
            continue
        responsibility = assignment.get("responsibility")
        if responsibility in observed:
            errors.append(f"{prefix}.responsibility must be unique")
        observed.add(responsibility)
        owner = assignment.get("owner")
        if responsibility in deterministic:
            deterministic_count += 1
            if owner != "deterministic_code":
                errors.append(f"{prefix}.owner must be deterministic_code")
            if assignment.get("model_may_override") is not False:
                errors.append(f"{prefix}.model_may_override must be false")
            if assignment.get("requires_structured_model_output") is not False:
                errors.append(f"{prefix}.requires_structured_model_output must be false")
        elif responsibility in semantic:
            semantic_count += 1
            if owner != "model":
                errors.append(f"{prefix}.owner must be model")
            if assignment.get("model_may_override") is not True:
                errors.append(f"{prefix}.model_may_override must be true for model-owned judgment")
            if assignment.get("requires_structured_model_output") is not True:
                errors.append(f"{prefix}.requires_structured_model_output must be true")
        else:
            errors.append(f"{prefix}.responsibility is not recognized")
        for field in ("input_contract_id", "output_contract_id", "failure_mode"):
            if not _non_empty(assignment.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if assignment.get("owner_may_assume_other_owner_responsibility") is not False:
            errors.append(f"{prefix}.owner_may_assume_other_owner_responsibility must be false")
    if observed != deterministic.union(semantic):
        errors.append("responsibility_assignments must cover every exact deterministic and semantic responsibility")
    handoffs = payload.get("handoff_invariants")
    if not isinstance(handoffs, dict):
        errors.append("handoff_invariants must be an object")
        handoffs = {}
    required_true = (
        "code_validates_model_output_before_state_change",
        "model_receives_only_routed_context",
        "model_cannot_unfreeze_artifacts",
        "model_cannot_expand_budget",
        "model_cannot_edit_provenance",
        "code_does_not_invent_semantic_content",
        "code_does_not_score_purpose_semantically",
    )
    for field in required_true:
        if handoffs.get(field) is not True:
            errors.append(f"handoff_invariants.{field} must be true")
    if payload.get("ownership_overlap_allowed") is not False:
        errors.append("ownership_overlap_allowed must be false")
    if payload.get("unvalidated_model_output_may_mutate_state") is not False:
        errors.append("unvalidated_model_output_may_mutate_state must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "deterministic_responsibility_count": deterministic_count,
        "semantic_responsibility_count": semantic_count,
        "assignment_count": len(observed),
    }

def validate_semantic_judgment_failure_recovery(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Recover model failures without replacing semantic judgment with rule scoring."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["semantic judgment failure recovery must be an object"]}
    for field in (
        "failure_recovery_id",
        "semantic_operation",
        "input_artifact_fingerprint",
        "prior_state_fingerprint",
        "failure_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    failure = payload.get("initial_failure")
    if not isinstance(failure, dict):
        errors.append("initial_failure must be an object")
        failure = {}
    for field in ("call_id", "provider_id", "model_id", "failure_type", "failed_at"):
        if not _non_empty(failure.get(field)):
            errors.append(f"initial_failure.{field} must be a non-empty string")
    max_attempts = payload.get("maximum_recovery_attempts")
    if not isinstance(max_attempts, int) or isinstance(max_attempts, bool) or max_attempts < 0:
        errors.append("maximum_recovery_attempts must be a non-negative integer")
        max_attempts = 0
    attempts = payload.get("recovery_attempts")
    if not isinstance(attempts, list) or len(attempts) > max_attempts:
        errors.append("recovery_attempts must be a list within maximum_recovery_attempts")
        attempts = []
    allowed_actions = {"retry", "switch_provider", "narrow_context"}
    attempt_ids = set()
    successful_attempts = []
    for index, attempt in enumerate(attempts):
        prefix = f"recovery_attempts[{index}]"
        if not isinstance(attempt, dict):
            errors.append(f"{prefix} must be an object")
            continue
        attempt_id = attempt.get("attempt_id")
        if not _non_empty(attempt_id):
            errors.append(f"{prefix}.attempt_id must be a non-empty string")
        elif attempt_id in attempt_ids:
            errors.append(f"{prefix}.attempt_id must be unique")
        attempt_ids.add(attempt_id)
        if attempt.get("ordinal") != index + 1:
            errors.append(f"{prefix}.ordinal must preserve attempt order")
        action = attempt.get("action")
        if action not in allowed_actions:
            errors.append(f"{prefix}.action must be retry, switch_provider, or narrow_context")
        for field in ("provider_id", "model_id", "input_fingerprint", "started_at", "completed_at"):
            if not _non_empty(attempt.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        status = attempt.get("status")
        if status not in {"failed", "valid_judgment"}:
            errors.append(f"{prefix}.status must be failed or valid_judgment")
        if status == "valid_judgment":
            successful_attempts.append(attempt)
            for field in ("judgment_artifact_id", "judgment_fingerprint", "semantic_validator_id"):
                if not _non_empty(attempt.get(field)):
                    errors.append(f"{prefix}.{field} is required for valid_judgment")
        else:
            if attempt.get("judgment_artifact_id") not in ("", None):
                errors.append(f"{prefix}.judgment_artifact_id must be empty after failure")
    if len(successful_attempts) > 1:
        errors.append("at most one recovery attempt may produce the accepted valid judgment")
    result = payload.get("recovery_result")
    if not isinstance(result, dict):
        errors.append("recovery_result must be an object")
        result = {}
    status = result.get("status")
    if status not in {"recovered", "unavailable_judgment"}:
        errors.append("recovery_result.status must be recovered or unavailable_judgment")
    if status == "recovered":
        if len(successful_attempts) != 1:
            errors.append("recovered status requires exactly one valid_judgment attempt")
        else:
            success = successful_attempts[0]
            if result.get("accepted_attempt_id") != success.get("attempt_id"):
                errors.append("recovery_result.accepted_attempt_id must match the valid attempt")
            if result.get("judgment_artifact_id") != success.get("judgment_artifact_id"):
                errors.append("recovery_result.judgment_artifact_id must match the valid attempt")
        if result.get("deferred") is not False:
            errors.append("recovered result must not be deferred")
    elif status == "unavailable_judgment":
        if successful_attempts:
            errors.append("unavailable_judgment cannot discard a valid recovery attempt")
        for field in ("unavailable_state_id", "pending_semantic_operation", "wake_trigger", "review_at"):
            if not _non_empty(result.get(field)):
                errors.append(f"unavailable_judgment requires recovery_result.{field}")
        if result.get("deferred") is not True:
            errors.append("unavailable_judgment must be deferred")
        if result.get("accepted_attempt_id") not in ("", None):
            errors.append("unavailable_judgment must not accept an attempt")
    if result.get("prior_state_fingerprint") != payload.get("prior_state_fingerprint"):
        errors.append("recovery_result.prior_state_fingerprint must preserve the prior state")
    if result.get("state_mutated_without_valid_judgment") is not False:
        errors.append("recovery_result.state_mutated_without_valid_judgment must be false")
    if payload.get("rule_based_purpose_scoring_invoked") is not False:
        errors.append("rule_based_purpose_scoring_invoked must be false")
    if payload.get("deterministic_semantic_substitute_invoked") is not False:
        errors.append("deterministic_semantic_substitute_invoked must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "recovery_status": status,
        "attempt_count": len(attempts),
        "valid_judgment_count": len(successful_attempts),
    }

def validate_shared_model_dependence_manifest(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Disclose correlated role assignments instead of claiming independent consensus."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["shared model dependence manifest must be an object"]}
    for field in ("assignment_manifest_id", "role_topology_id", "run_id", "manifest_fingerprint", "manifest_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected_roles = {"interpreter", "inventor", "adversary", "selector", "outcome_analyst"}
    assignments = payload.get("role_assignments")
    if not isinstance(assignments, list) or len(assignments) != len(expected_roles):
        errors.append("role_assignments must contain exactly the five cognitive roles")
        assignments = []
    observed_roles = set()
    model_roles: Dict[str, set] = {}
    provider_roles: Dict[str, set] = {}
    for index, assignment in enumerate(assignments):
        prefix = f"role_assignments[{index}]"
        if not isinstance(assignment, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("assignment_id", "role", "provider_id", "model_id", "context_partition_id"):
            if not _non_empty(assignment.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        role = assignment.get("role")
        if role not in expected_roles:
            errors.append(f"{prefix}.role is not recognized")
        elif role in observed_roles:
            errors.append(f"{prefix}.role must be unique")
        observed_roles.add(role)
        model_roles.setdefault(assignment.get("model_id"), set()).add(role)
        provider_roles.setdefault(assignment.get("provider_id"), set()).add(role)
        if assignment.get("role_boundary_preserved") is not True:
            errors.append(f"{prefix}.role_boundary_preserved must be true")
    if observed_roles != expected_roles:
        errors.append("role_assignments must cover every cognitive role exactly once")
    expected_model_groups = {
        model_id: roles for model_id, roles in model_roles.items() if _non_empty(model_id) and len(roles) > 1
    }
    groups = payload.get("shared_model_groups")
    if not isinstance(groups, list):
        errors.append("shared_model_groups must be a list")
        groups = []
    observed_groups = {}
    for index, group in enumerate(groups):
        prefix = f"shared_model_groups[{index}]"
        if not isinstance(group, dict):
            errors.append(f"{prefix} must be an object")
            continue
        model_id = group.get("model_id")
        roles = group.get("roles")
        if not _non_empty(group.get("dependence_group_id")):
            errors.append(f"{prefix}.dependence_group_id must be a non-empty string")
        if not _non_empty(model_id):
            errors.append(f"{prefix}.model_id must be a non-empty string")
        if (
            not isinstance(roles, list)
            or len(roles) < 2
            or len(roles) != len(set(roles))
        ):
            errors.append(f"{prefix}.roles must contain at least two unique roles")
            roles = []
        observed_groups[model_id] = set(roles)
        if group.get("independent_consensus_source_count") != 1:
            errors.append(f"{prefix}.independent_consensus_source_count must be 1")
        if group.get("correlated_error_risk_disclosed") is not True:
            errors.append(f"{prefix}.correlated_error_risk_disclosed must be true")
    if observed_groups != expected_model_groups:
        errors.append("shared_model_groups must exactly disclose every model assigned to multiple roles")
    unique_models = len([model_id for model_id in model_roles if _non_empty(model_id)])
    unique_providers = len([provider_id for provider_id in provider_roles if _non_empty(provider_id)])
    dependence = bool(expected_model_groups)
    evaluation = payload.get("evaluation_claims")
    if not isinstance(evaluation, dict):
        errors.append("evaluation_claims must be an object")
        evaluation = {}
    if evaluation.get("shared_model_dependence") is not dependence:
        errors.append("evaluation_claims.shared_model_dependence must match role assignments")
    if evaluation.get("independent_model_source_count") != unique_models:
        errors.append("evaluation_claims.independent_model_source_count must equal unique model count")
    if evaluation.get("independent_provider_source_count") != unique_providers:
        errors.append("evaluation_claims.independent_provider_source_count must equal unique provider count")
    if evaluation.get("role_output_count") != len(observed_roles):
        errors.append("evaluation_claims.role_output_count must equal role assignment count")
    if evaluation.get("independent_consensus_claimed") is not (not dependence and unique_models == len(expected_roles)):
        errors.append("evaluation_claims.independent_consensus_claimed must reflect actual model independence")
    if dependence and evaluation.get("consensus_label") != "correlated_role_agreement":
        errors.append("shared-model runs must label consensus as correlated_role_agreement")
    if not dependence and evaluation.get("consensus_label") != "independent_role_agreement":
        errors.append("distinct-model runs must label consensus as independent_role_agreement")
    if payload.get("local_single_model_testing_allowed") is not True:
        errors.append("local_single_model_testing_allowed must be true")
    if payload.get("role_count_used_as_independence_count") is not False:
        errors.append("role_count_used_as_independence_count must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "role_count": len(observed_roles),
        "unique_model_count": unique_models,
        "unique_provider_count": unique_providers,
        "shared_model_dependence": dependence,
    }

def validate_provider_neutral_cognition_thesis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Integrate provider-neutral semantic roles under deterministic authority controls."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["provider neutral cognition thesis must be an object"]}
    for field in ("cognition_thesis_id", "narrow_command_api_id", "integration_fingerprint", "thesis_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected_components = {
        "model_multiplicity_tradeoff": "validate_model_multiplicity_tradeoff",
        "provider_neutral_roles": "validate_provider_neutral_cognitive_roles",
        "inventor_independence": "validate_partitioned_inventor_independence",
        "interpretation_routing": "validate_causal_sketch_interpretation_routing",
        "blinded_adversary": "validate_blinded_adversary_review_packet",
        "structured_selector": "validate_structured_selector_decision_packet",
        "ownership_boundary": "validate_deterministic_semantic_ownership_boundary",
        "failure_recovery": "validate_semantic_judgment_failure_recovery",
        "dependence_manifest": "validate_shared_model_dependence_manifest",
    }
    components = payload.get("component_evidence")
    if not isinstance(components, list) or len(components) != len(expected_components):
        errors.append("component_evidence must contain exactly the nine cognition components")
        components = []
    observed = set()
    evidence_ids = set()
    for index, component in enumerate(components):
        prefix = f"component_evidence[{index}]"
        if not isinstance(component, dict):
            errors.append(f"{prefix} must be an object")
            continue
        component_type = component.get("component")
        observed.add(component_type)
        expected_validator = expected_components.get(component_type)
        if expected_validator is None:
            errors.append(f"{prefix}.component is not recognized")
        elif component.get("validator_id") != expected_validator:
            errors.append(f"{prefix}.validator_id must be {expected_validator}")
        evidence_id = component.get("evidence_artifact_id")
        if not _non_empty(evidence_id):
            errors.append(f"{prefix}.evidence_artifact_id must be a non-empty string")
        elif evidence_id in evidence_ids:
            errors.append(f"{prefix}.evidence_artifact_id must be unique")
        evidence_ids.add(evidence_id)
        for field in ("evidence_fingerprint", "schema_id", "verification_record_id"):
            if not _non_empty(component.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if component.get("verified") is not True:
            errors.append(f"{prefix}.verified must be true")
    if observed != set(expected_components):
        errors.append("component_evidence must cover every cognition component exactly once")
    invariants = payload.get("integrated_invariants")
    if not isinstance(invariants, dict):
        errors.append("integrated_invariants must be an object")
        invariants = {}
    required_true = (
        "semantic_roles_provider_neutral",
        "semantic_roles_structurally_separated",
        "independence_claims_deterministically_computed",
        "authority_boundaries_deterministically_enforced",
        "model_outputs_validated_before_state_change",
        "shared_model_dependence_disclosed",
        "semantic_failure_remains_explicit",
    )
    required_false = (
        "provider_count_defines_role_topology",
        "role_prompt_alone_proves_independence",
        "role_count_inflates_consensus",
        "deterministic_code_substitutes_semantic_judgment",
        "model_controls_its_own_authority",
    )
    for field in required_true:
        if invariants.get(field) is not True:
            errors.append(f"integrated_invariants.{field} must be true")
    for field in required_false:
        if invariants.get(field) is not False:
            errors.append(f"integrated_invariants.{field} must be false")
    if payload.get("cognition_thesis_decision") != "integrated":
        errors.append("cognition_thesis_decision must be integrated")
    return {
        "valid": not errors,
        "errors": errors,
        "component_count": len(observed),
        "verified_component_count": sum(
            isinstance(item, dict) and item.get("verified") is True for item in components
        ),
        "cognition_thesis_decision": payload.get("cognition_thesis_decision"),
    }

def validate_bounded_context_leakage_guard(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Prevent repository-scale noise and prior conclusions from entering independent generation."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["bounded context leakage guard must be an object"]}
    for field in (
        "context_guard_id",
        "generation_assignment_id",
        "available_universe_fingerprint",
        "context_manifest_fingerprint",
        "guard_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    available_tokens = payload.get("available_universe_tokens")
    budget_tokens = payload.get("context_token_budget")
    selected_tokens = payload.get("selected_context_tokens")
    for field, value in (
        ("available_universe_tokens", available_tokens),
        ("context_token_budget", budget_tokens),
        ("selected_context_tokens", selected_tokens),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            errors.append(f"{field} must be a positive integer")
    if isinstance(selected_tokens, int) and isinstance(budget_tokens, int) and selected_tokens > budget_tokens:
        errors.append("selected_context_tokens must not exceed context_token_budget")
    if isinstance(budget_tokens, int) and isinstance(available_tokens, int) and budget_tokens >= available_tokens:
        errors.append("context_token_budget must be smaller than the available repository/history universe")
    allowed_types = {"observation", "constitution_clause", "causal_evidence", "active_constraint"}
    artifacts = payload.get("included_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("included_artifacts must be a non-empty list")
        artifacts = []
    artifact_ids = set()
    token_sum = 0
    for index, artifact in enumerate(artifacts):
        prefix = f"included_artifacts[{index}]"
        if not isinstance(artifact, dict):
            errors.append(f"{prefix} must be an object")
            continue
        artifact_id = artifact.get("artifact_id")
        if not _non_empty(artifact_id):
            errors.append(f"{prefix}.artifact_id must be a non-empty string")
        elif artifact_id in artifact_ids:
            errors.append(f"{prefix}.artifact_id must be unique")
        artifact_ids.add(artifact_id)
        if artifact.get("artifact_type") not in allowed_types:
            errors.append(f"{prefix}.artifact_type is not allowed during independent generation")
        for field in ("content_fingerprint", "inclusion_reason", "source_provenance_id"):
            if not _non_empty(artifact.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        tokens = artifact.get("token_count")
        if not isinstance(tokens, int) or isinstance(tokens, bool) or tokens <= 0:
            errors.append(f"{prefix}.token_count must be a positive integer")
        else:
            token_sum += tokens
        if artifact.get("contains_prior_mission_conclusion") is not False:
            errors.append(f"{prefix}.contains_prior_mission_conclusion must be false")
        if artifact.get("contains_persuasive_discussion_history") is not False:
            errors.append(f"{prefix}.contains_persuasive_discussion_history must be false")
    if isinstance(selected_tokens, int) and token_sum != selected_tokens:
        errors.append("selected_context_tokens must equal included artifact token_count sum")
    expected_exclusions = {
        "full_repository_dump",
        "full_history_dump",
        "prior_mission_candidates",
        "prior_selection_conclusions",
        "persuasive_discussion_history",
        "raw_chain_of_thought",
    }
    exclusions = payload.get("excluded_categories")
    if (
        not isinstance(exclusions, list)
        or set(exclusions) != expected_exclusions
        or len(exclusions) != len(expected_exclusions)
    ):
        errors.append("excluded_categories must exactly cover repository, history, conclusion, persuasion, and reasoning leakage")
    scan = payload.get("leakage_scan")
    if not isinstance(scan, dict):
        errors.append("leakage_scan must be an object")
        scan = {}
    for field in ("scan_id", "scanner_version", "scanned_context_fingerprint", "scanned_at"):
        if not _non_empty(scan.get(field)):
            errors.append(f"leakage_scan.{field} must be a non-empty string")
    if scan.get("scanned_context_fingerprint") != payload.get("context_manifest_fingerprint"):
        errors.append("leakage_scan.scanned_context_fingerprint must match context_manifest_fingerprint")
    if scan.get("prior_conclusion_matches") != []:
        errors.append("leakage_scan.prior_conclusion_matches must be empty")
    if scan.get("forbidden_category_matches") != []:
        errors.append("leakage_scan.forbidden_category_matches must be empty")
    if scan.get("passed") is not True:
        errors.append("leakage_scan.passed must be true")
    if payload.get("entire_repository_included") is not False:
        errors.append("entire_repository_included must be false")
    if payload.get("entire_history_included") is not False:
        errors.append("entire_history_included must be false")
    if payload.get("independent_generation_preserved") is not True:
        errors.append("independent_generation_preserved must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "included_artifact_count": len(artifact_ids),
        "selected_context_tokens": selected_tokens,
        "context_token_budget": budget_tokens,
    }

def validate_decision_anchored_context_assembly(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Assemble bounded context from the five decision-relevant anchors."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["decision anchored context assembly must be an object"]}
    for field in ("assembly_id", "context_guard_id", "assembly_fingerprint", "assembly_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected_anchors = {
        "wake_reason": ("wake_event", 1),
        "constitution_scope": ("constitution_clause", 1),
        "affected_beneficiary": ("beneficiary_record", 1),
        "active_frontier": ("mission_frontier", 1),
        "lineage_neighborhood": ("lineage_object", 1),
    }
    anchors = payload.get("anchors")
    if not isinstance(anchors, list) or len(anchors) != len(expected_anchors):
        errors.append("anchors must contain exactly the five decision anchors")
        anchors = []
    observed = set()
    anchor_ids = set()
    anchored_artifacts = set()
    for index, anchor in enumerate(anchors):
        prefix = f"anchors[{index}]"
        if not isinstance(anchor, dict):
            errors.append(f"{prefix} must be an object")
            continue
        anchor_type = anchor.get("anchor_type")
        observed.add(anchor_type)
        expected = expected_anchors.get(anchor_type)
        if expected is None:
            errors.append(f"{prefix}.anchor_type is not recognized")
            continue
        expected_source_type, minimum = expected
        if anchor.get("source_type") != expected_source_type:
            errors.append(f"{prefix}.source_type must be {expected_source_type}")
        anchor_id = anchor.get("anchor_id")
        if not _non_empty(anchor_id):
            errors.append(f"{prefix}.anchor_id must be a non-empty string")
        elif anchor_id in anchor_ids:
            errors.append(f"{prefix}.anchor_id must be unique")
        anchor_ids.add(anchor_id)
        for field in ("source_fingerprint", "selection_question", "scope_expression"):
            if not _non_empty(anchor.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        artifact_ids = anchor.get("selected_artifact_ids")
        if (
            not isinstance(artifact_ids, list)
            or len(artifact_ids) < minimum
            or not all(_non_empty(item) for item in artifact_ids)
            or len(artifact_ids) != len(set(artifact_ids))
        ):
            errors.append(f"{prefix}.selected_artifact_ids must be a non-empty unique string list")
            artifact_ids = []
        anchored_artifacts.update(artifact_ids)
        if anchor_type == "lineage_neighborhood":
            max_hops = anchor.get("maximum_hops")
            if not isinstance(max_hops, int) or isinstance(max_hops, bool) or not 1 <= max_hops <= 3:
                errors.append(f"{prefix}.maximum_hops must be between 1 and 3")
            if anchor.get("unbounded_ancestry_allowed") is not False:
                errors.append(f"{prefix}.unbounded_ancestry_allowed must be false")
        else:
            if anchor.get("maximum_hops") not in (0, None):
                errors.append(f"{prefix}.maximum_hops must be zero or empty outside lineage")
            if anchor.get("unbounded_ancestry_allowed") is not False:
                errors.append(f"{prefix}.unbounded_ancestry_allowed must be false")
    if observed != set(expected_anchors):
        errors.append("anchors must cover wake reason, constitution scope, beneficiary, frontier, and lineage exactly once")
    manifest = payload.get("assembled_manifest")
    if not isinstance(manifest, dict):
        errors.append("assembled_manifest must be an object")
        manifest = {}
    for field in ("manifest_id", "manifest_fingerprint", "assembled_at"):
        if not _non_empty(manifest.get(field)):
            errors.append(f"assembled_manifest.{field} must be a non-empty string")
    manifest_ids = manifest.get("artifact_ids")
    if (
        not isinstance(manifest_ids, list)
        or len(manifest_ids) != len(set(manifest_ids))
        or set(manifest_ids) != anchored_artifacts
    ):
        errors.append("assembled_manifest.artifact_ids must exactly equal the union selected by all anchors")
        manifest_ids = []
    coverage = manifest.get("anchor_coverage")
    if not isinstance(coverage, dict) or set(coverage) != set(expected_anchors):
        errors.append("assembled_manifest.anchor_coverage must cover every exact anchor")
        coverage = {}
    for anchor_type in expected_anchors:
        if coverage.get(anchor_type) is not True:
            errors.append(f"assembled_manifest.anchor_coverage.{anchor_type} must be true")
    if payload.get("assembly_started_from_global_similarity_search") is not False:
        errors.append("assembly_started_from_global_similarity_search must be false")
    if payload.get("missing_anchor_allowed") is not False:
        errors.append("missing_anchor_allowed must be false")
    if payload.get("bounded_context_guard_validated_first") is not True:
        errors.append("bounded_context_guard_validated_first must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "anchor_count": len(observed),
        "assembled_artifact_count": len(manifest_ids),
        "anchor_types": sorted(item for item in observed if _non_empty(item)),
    }

