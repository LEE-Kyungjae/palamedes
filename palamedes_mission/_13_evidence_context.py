from __future__ import annotations

from typing import Any, Dict, List
from ._01_kinds_value import _non_empty


def validate_anti_vocabulary_lockin_retrieval_slots(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require retrieval operations that pressure more than lexical similarity."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["anti vocabulary lockin retrieval slots must be an object"]}
    for field in ("retrieval_plan_id", "context_assembly_id", "anchor_set_fingerprint", "plan_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected_slots = {
        "counter_view": "contradiction_search",
        "failure": "failure_archive_search",
        "remote_mechanism": "cross_domain_mechanism_search",
        "uncovered_beneficiary": "beneficiary_gap_search",
    }
    slots = payload.get("slots")
    if not isinstance(slots, list) or len(slots) != len(expected_slots):
        errors.append("slots must contain exactly four anti-lock-in retrieval slots")
        slots = []
    observed = set()
    slot_ids = set()
    total_budget = 0
    for index, slot in enumerate(slots):
        prefix = f"slots[{index}]"
        if not isinstance(slot, dict):
            errors.append(f"{prefix} must be an object")
            continue
        slot_type = slot.get("slot_type")
        observed.add(slot_type)
        expected_operation = expected_slots.get(slot_type)
        if expected_operation is None:
            errors.append(f"{prefix}.slot_type is not recognized")
            continue
        if slot.get("retrieval_operation") != expected_operation:
            errors.append(f"{prefix}.retrieval_operation must be {expected_operation}")
        slot_id = slot.get("slot_id")
        if not _non_empty(slot_id):
            errors.append(f"{prefix}.slot_id must be a non-empty string")
        elif slot_id in slot_ids:
            errors.append(f"{prefix}.slot_id must be unique")
        slot_ids.add(slot_id)
        for field in ("search_question", "search_scope", "query_fingerprint", "inclusion_criterion"):
            if not _non_empty(slot.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        budget = slot.get("token_budget")
        if not isinstance(budget, int) or isinstance(budget, bool) or budget <= 0:
            errors.append(f"{prefix}.token_budget must be a positive integer")
        else:
            total_budget += budget
        if slot.get("retrieval_attempted") is not True:
            errors.append(f"{prefix}.retrieval_attempted must be true")
        results = slot.get("result_artifact_ids")
        if (
            not isinstance(results, list)
            or not all(_non_empty(item) for item in results)
            or len(results) != len(set(results))
        ):
            errors.append(f"{prefix}.result_artifact_ids must be a unique string list")
        if slot.get("lexical_similarity_only") is not False:
            errors.append(f"{prefix}.lexical_similarity_only must be false")
        if slot.get("existing_vocabulary_required") is not False:
            errors.append(f"{prefix}.existing_vocabulary_required must be false")
    if observed != set(expected_slots):
        errors.append("slots must cover counter view, failure, remote mechanism, and uncovered beneficiary exactly once")
    plan_budget = payload.get("total_slot_token_budget")
    if not isinstance(plan_budget, int) or isinstance(plan_budget, bool) or plan_budget <= 0:
        errors.append("total_slot_token_budget must be a positive integer")
    elif plan_budget != total_budget:
        errors.append("total_slot_token_budget must equal the sum of slot budgets")
    if payload.get("global_similarity_ranking_controls_all_slots") is not False:
        errors.append("global_similarity_ranking_controls_all_slots must be false")
    if payload.get("all_slots_attempted_before_context_freeze") is not True:
        errors.append("all_slots_attempted_before_context_freeze must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "slot_count": len(observed),
        "slot_types": sorted(item for item in observed if _non_empty(item)),
        "total_slot_token_budget": total_budget,
    }

def validate_explicit_empty_retrieval_evidence(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Preserve qualified search absence instead of padding empty slots."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["explicit empty retrieval evidence must be an object"]}
    for field in ("completion_record_id", "retrieval_plan_id", "context_manifest_id", "completion_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected_slots = {"counter_view", "failure", "remote_mechanism", "uncovered_beneficiary"}
    slots = payload.get("slot_completions")
    if not isinstance(slots, list) or len(slots) != len(expected_slots):
        errors.append("slot_completions must contain exactly the four retrieval slots")
        slots = []
    observed = set()
    empty_count = 0
    filled_count = 0
    completion_ids = set()
    for index, slot in enumerate(slots):
        prefix = f"slot_completions[{index}]"
        if not isinstance(slot, dict):
            errors.append(f"{prefix} must be an object")
            continue
        slot_type = slot.get("slot_type")
        observed.add(slot_type)
        if slot_type not in expected_slots:
            errors.append(f"{prefix}.slot_type is not recognized")
        completion_id = slot.get("completion_id")
        if not _non_empty(completion_id):
            errors.append(f"{prefix}.completion_id must be a non-empty string")
        elif completion_id in completion_ids:
            errors.append(f"{prefix}.completion_id must be unique")
        completion_ids.add(completion_id)
        for field in ("query_fingerprint", "searched_scope", "search_completed_at"):
            if not _non_empty(slot.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if slot.get("retrieval_attempted") is not True:
            errors.append(f"{prefix}.retrieval_attempted must be true")
        sources = slot.get("searched_source_ids")
        if (
            not isinstance(sources, list)
            or not sources
            or not all(_non_empty(item) for item in sources)
            or len(sources) != len(set(sources))
        ):
            errors.append(f"{prefix}.searched_source_ids must be a non-empty unique string list")
        results = slot.get("result_artifact_ids")
        if not isinstance(results, list) or not all(_non_empty(item) for item in results) or len(results) != len(set(results)):
            errors.append(f"{prefix}.result_artifact_ids must be a unique string list")
            results = []
        status = slot.get("status")
        if status == "filled":
            filled_count += 1
            if not results:
                errors.append(f"{prefix} filled status requires at least one result artifact")
            if slot.get("missing_evidence_statement") not in ("", None):
                errors.append(f"{prefix} filled status must not claim missing evidence")
            if slot.get("uncertainty_impact") not in ("", None):
                errors.append(f"{prefix} filled status must not add empty-slot uncertainty impact")
            if slot.get("next_acquisition_trigger") not in ("", None):
                errors.append(f"{prefix} filled status must not add empty-slot acquisition trigger")
        elif status == "empty":
            empty_count += 1
            if results:
                errors.append(f"{prefix} empty status requires no result artifacts")
            for field in ("missing_evidence_statement", "uncertainty_impact", "next_acquisition_trigger"):
                if not _non_empty(slot.get(field)):
                    errors.append(f"{prefix}.{field} is required for empty status")
            if slot.get("empty_marker_included_in_context") is not True:
                errors.append(f"{prefix}.empty_marker_included_in_context must be true")
        else:
            errors.append(f"{prefix}.status must be filled or empty")
        if slot.get("weak_reference_used_as_padding") is not False:
            errors.append(f"{prefix}.weak_reference_used_as_padding must be false")
    if observed != expected_slots:
        errors.append("slot_completions must cover every retrieval slot exactly once")
    if payload.get("empty_slots_dropped") is not False:
        errors.append("empty_slots_dropped must be false")
    if payload.get("all_slots_forced_filled") is not False:
        errors.append("all_slots_forced_filled must be false")
    if payload.get("missing_evidence_visible_to_downstream_roles") is not True:
        errors.append("missing_evidence_visible_to_downstream_roles must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "empty_slot_count": empty_count,
        "filled_slot_count": filled_count,
        "slot_count": len(observed),
    }

def validate_constitution_authorized_preference_history(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Allow owner preference history only under scoped authority and counter-precedent."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["constitution authorized preference history must be an object"]}
    for field in ("preference_context_id", "context_manifest_id", "preference_domain", "context_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    authorization = payload.get("constitutional_authorization")
    if not isinstance(authorization, dict):
        errors.append("constitutional_authorization must be an object")
        authorization = {}
    authorized = authorization.get("authorized")
    if not isinstance(authorized, bool):
        errors.append("constitutional_authorization.authorized must be boolean")
    if authorized:
        for field in (
            "constitution_state_id",
            "constitution_fingerprint",
            "clause_id",
            "authorized_domain",
            "allowed_decision_use",
            "authority_rationale",
        ):
            if not _non_empty(authorization.get(field)):
                errors.append(f"constitutional_authorization.{field} is required when authorized")
        if authorization.get("authorized_domain") != payload.get("preference_domain"):
            errors.append("constitutional_authorization.authorized_domain must match preference_domain")
        if authorization.get("may_override_beneficiary_evidence") is not False:
            errors.append("constitutional_authorization.may_override_beneficiary_evidence must be false")
        if authorization.get("may_override_observed_outcome") is not False:
            errors.append("constitutional_authorization.may_override_observed_outcome must be false")
    precedents = payload.get("owner_precedents")
    if not isinstance(precedents, list):
        errors.append("owner_precedents must be a list")
        precedents = []
    if not authorized and precedents:
        errors.append("owner_precedents must be empty without constitutional authorization")
    precedent_ids = set()
    stances = set()
    for index, precedent in enumerate(precedents):
        prefix = f"owner_precedents[{index}]"
        if not isinstance(precedent, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in (
            "precedent_id",
            "recorded_preference",
            "decision_context",
            "observed_outcome",
            "source_provenance_id",
            "precedent_fingerprint",
        ):
            if not _non_empty(precedent.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        precedent_id = precedent.get("precedent_id")
        if precedent_id in precedent_ids:
            errors.append(f"{prefix}.precedent_id must be unique")
        precedent_ids.add(precedent_id)
        stance = precedent.get("stance")
        if stance not in {"confirming", "disconfirming"}:
            errors.append(f"{prefix}.stance must be confirming or disconfirming")
        stances.add(stance)
        if precedent.get("domain") != payload.get("preference_domain"):
            errors.append(f"{prefix}.domain must match preference_domain")
        if precedent.get("outcome_observed") is not True:
            errors.append(f"{prefix}.outcome_observed must be true")
    if authorized and stances != {"confirming", "disconfirming"}:
        errors.append("authorized preference history requires both confirming and disconfirming precedents")
    summary = payload.get("preference_summary")
    if not isinstance(summary, dict):
        errors.append("preference_summary must be an object")
        summary = {}
    if authorized:
        for field in ("summary_id", "current_tendency", "counter_tendency", "decision_relevance"):
            if not _non_empty(summary.get(field)):
                errors.append(f"preference_summary.{field} is required when authorized")
        if summary.get("precedent_ids") != [item.get("precedent_id") for item in precedents if isinstance(item, dict)]:
            errors.append("preference_summary.precedent_ids must preserve exact precedent order")
        if summary.get("treated_as_advisory") is not True:
            errors.append("preference_summary.treated_as_advisory must be true")
    else:
        if summary not in ({}, None):
            errors.append("preference_summary must be empty without authorization")
    if payload.get("repetition_count_used_as_authority") is not False:
        errors.append("repetition_count_used_as_authority must be false")
    if payload.get("disconfirming_precedents_filtered_out") is not False:
        errors.append("disconfirming_precedents_filtered_out must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "authorized": authorized,
        "precedent_count": len(precedent_ids),
        "precedent_stances": sorted(item for item in stances if _non_empty(item)),
    }

def validate_sensitive_signal_minimized_context(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Expose a minimized sensitive-signal representation while retaining controlled provenance."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["sensitive signal minimized context must be an object"]}
    for field in (
        "minimized_context_id",
        "signal_id",
        "signal_fingerprint",
        "context_manifest_id",
        "minimization_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("sensitivity") not in {"restricted", "confidential", "highly_sensitive"}:
        errors.append("sensitivity must be restricted, confidential, or highly_sensitive")
    original = payload.get("controlled_original")
    if not isinstance(original, dict):
        errors.append("controlled_original must be an object")
        original = {}
    for field in (
        "original_locator",
        "original_content_fingerprint",
        "access_policy_id",
        "custodian_id",
        "provenance_record_id",
    ):
        if not _non_empty(original.get(field)):
            errors.append(f"controlled_original.{field} must be a non-empty string")
    if original.get("access_controlled") is not True:
        errors.append("controlled_original.access_controlled must be true")
    if original.get("raw_content_embedded_in_record") is not False:
        errors.append("controlled_original.raw_content_embedded_in_record must be false")
    representation = payload.get("context_representation")
    if not isinstance(representation, dict):
        errors.append("context_representation must be an object")
        representation = {}
    mode = representation.get("mode")
    if mode not in {"summary", "redacted", "local_embedding"}:
        errors.append("context_representation.mode must be summary, redacted, or local_embedding")
    for field in ("representation_id", "representation_fingerprint", "transform_record_id", "created_at"):
        if not _non_empty(representation.get(field)):
            errors.append(f"context_representation.{field} must be a non-empty string")
    if mode in {"summary", "redacted"}:
        if not _non_empty(representation.get("bounded_text")):
            errors.append(f"{mode} representation requires bounded_text")
        if representation.get("local_embedding_locator") not in ("", None):
            errors.append(f"{mode} representation must not include local_embedding_locator")
    elif mode == "local_embedding":
        if not _non_empty(representation.get("local_embedding_locator")):
            errors.append("local_embedding representation requires local_embedding_locator")
        if representation.get("bounded_text") not in ("", None):
            errors.append("local_embedding representation must not include bounded_text")
        if representation.get("embedding_leaves_local_boundary") is not False:
            errors.append("local_embedding representation must not leave the local boundary")
    if representation.get("raw_sensitive_content_included") is not False:
        errors.append("context_representation.raw_sensitive_content_included must be false")
    if representation.get("reidentification_fields_included") is not False:
        errors.append("context_representation.reidentification_fields_included must be false")
    access = payload.get("context_access")
    if not isinstance(access, dict):
        errors.append("context_access must be an object")
        access = {}
    roles = access.get("allowed_role_ids")
    if (
        not isinstance(roles, list)
        or not roles
        or not all(_non_empty(item) for item in roles)
        or len(roles) != len(set(roles))
    ):
        errors.append("context_access.allowed_role_ids must be a non-empty unique string list")
    for field in ("purpose_limitation", "expires_at", "deletion_trigger", "access_log_id"):
        if not _non_empty(access.get(field)):
            errors.append(f"context_access.{field} must be a non-empty string")
    if access.get("downstream_redistribution_allowed") is not False:
        errors.append("context_access.downstream_redistribution_allowed must be false")
    if payload.get("model_can_dereference_original") is not False:
        errors.append("model_can_dereference_original must be false")
    if payload.get("provenance_preserved") is not True:
        errors.append("provenance_preserved must be true")
    if payload.get("minimum_necessary_representation") is not True:
        errors.append("minimum_necessary_representation must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "representation_mode": mode,
        "signal_id": payload.get("signal_id"),
        "allowed_role_count": len(roles) if isinstance(roles, list) else 0,
    }

def validate_generated_artifact_context_manifest(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Bind every generated artifact to ordered context and model fingerprints."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["generated artifact context manifest must be an object"]}
    for field in (
        "binding_record_id",
        "generated_artifact_id",
        "generated_artifact_type",
        "generated_artifact_fingerprint",
        "generated_at",
        "binding_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    context = payload.get("context_manifest")
    if not isinstance(context, dict):
        errors.append("context_manifest must be an object")
        context = {}
    for field in ("manifest_id", "manifest_fingerprint", "assembly_id"):
        if not _non_empty(context.get(field)):
            errors.append(f"context_manifest.{field} must be a non-empty string")
    items = context.get("items")
    if not isinstance(items, list) or not items:
        errors.append("context_manifest.items must be a non-empty list")
        items = []
    item_ids = set()
    ordered_hashes = []
    for index, item in enumerate(items):
        prefix = f"context_manifest.items[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if item.get("ordinal") != index + 1:
            errors.append(f"{prefix}.ordinal must preserve exact context order")
        item_id = item.get("artifact_id")
        if not _non_empty(item_id):
            errors.append(f"{prefix}.artifact_id must be a non-empty string")
        elif item_id in item_ids:
            errors.append(f"{prefix}.artifact_id must be unique")
        item_ids.add(item_id)
        for field in (
            "artifact_type",
            "content_fingerprint",
            "representation_fingerprint",
            "provenance_record_id",
        ):
            if not _non_empty(item.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        ordered_hashes.append(item.get("content_fingerprint"))
        if item.get("raw_content_embedded_in_manifest") is not False:
            errors.append(f"{prefix}.raw_content_embedded_in_manifest must be false")
    if context.get("ordered_content_fingerprints") != ordered_hashes:
        errors.append("context_manifest.ordered_content_fingerprints must match item order exactly")
    runtime = payload.get("model_runtime_manifest")
    if not isinstance(runtime, dict):
        errors.append("model_runtime_manifest must be an object")
        runtime = {}
    for field in (
        "runtime_manifest_id",
        "provider_id",
        "model_id",
        "model_version",
        "model_configuration_fingerprint",
        "prompt_template_fingerprint",
        "role_assignment_id",
    ):
        if not _non_empty(runtime.get(field)):
            errors.append(f"model_runtime_manifest.{field} must be a non-empty string")
    comparison = payload.get("reproduction_comparison")
    if not isinstance(comparison, dict):
        errors.append("reproduction_comparison must be an object")
        comparison = {}
    for field in (
        "baseline_context_manifest_fingerprint",
        "current_context_manifest_fingerprint",
        "baseline_model_configuration_fingerprint",
        "current_model_configuration_fingerprint",
    ):
        if not _non_empty(comparison.get(field)):
            errors.append(f"reproduction_comparison.{field} must be a non-empty string")
    context_changed = (
        comparison.get("baseline_context_manifest_fingerprint")
        != comparison.get("current_context_manifest_fingerprint")
    )
    model_changed = (
        comparison.get("baseline_model_configuration_fingerprint")
        != comparison.get("current_model_configuration_fingerprint")
    )
    if context_changed and model_changed:
        expected_classification = "evidence_and_model_changed"
    elif context_changed:
        expected_classification = "evidence_changed"
    elif model_changed:
        expected_classification = "model_changed"
    else:
        expected_classification = "neither_changed"
    if comparison.get("change_classification") != expected_classification:
        errors.append(f"reproduction_comparison.change_classification must be {expected_classification}")
    if comparison.get("current_context_manifest_fingerprint") != context.get("manifest_fingerprint"):
        errors.append("current context comparison fingerprint must match context_manifest")
    if comparison.get("current_model_configuration_fingerprint") != runtime.get(
        "model_configuration_fingerprint"
    ):
        errors.append("current model comparison fingerprint must match model_runtime_manifest")
    if payload.get("artifact_written_without_context_manifest") is not False:
        errors.append("artifact_written_without_context_manifest must be false")
    if payload.get("artifact_written_without_model_manifest") is not False:
        errors.append("artifact_written_without_model_manifest must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "context_item_count": len(item_ids),
        "change_classification": expected_classification,
        "generated_artifact_id": payload.get("generated_artifact_id"),
    }

def validate_decision_evidence_token_priority(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Reserve context capacity for decision-bearing evidence before narrative background."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["decision evidence token priority must be an object"]}
    for field in ("allocation_id", "context_manifest_id", "allocation_fingerprint", "allocation_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    total_budget = payload.get("total_token_budget")
    if not isinstance(total_budget, int) or isinstance(total_budget, bool) or total_budget <= 0:
        errors.append("total_token_budget must be a positive integer")
        total_budget = 0
    expected_priorities = {
        "primary_observation": 1,
        "constitutional_conflict": 2,
        "rival_mechanism": 3,
        "narrative_background": 4,
    }
    allocations = payload.get("allocations")
    if not isinstance(allocations, list) or len(allocations) != len(expected_priorities):
        errors.append("allocations must contain exactly four context categories")
        allocations = []
    observed = set()
    allocated_sum = 0
    category_tokens = {}
    for index, allocation in enumerate(allocations):
        prefix = f"allocations[{index}]"
        if not isinstance(allocation, dict):
            errors.append(f"{prefix} must be an object")
            continue
        category = allocation.get("category")
        observed.add(category)
        expected_priority = expected_priorities.get(category)
        if expected_priority is None:
            errors.append(f"{prefix}.category is not recognized")
            continue
        if allocation.get("priority") != expected_priority:
            errors.append(f"{prefix}.priority must be {expected_priority}")
        requested = allocation.get("requested_tokens")
        allocated = allocation.get("allocated_tokens")
        if not isinstance(requested, int) or isinstance(requested, bool) or requested < 0:
            errors.append(f"{prefix}.requested_tokens must be a non-negative integer")
        if not isinstance(allocated, int) or isinstance(allocated, bool) or allocated < 0:
            errors.append(f"{prefix}.allocated_tokens must be a non-negative integer")
            allocated = 0
        if isinstance(requested, int) and allocated > requested:
            errors.append(f"{prefix}.allocated_tokens must not exceed requested_tokens")
        allocated_sum += allocated
        category_tokens[category] = allocated
        artifact_ids = allocation.get("artifact_ids")
        if (
            not isinstance(artifact_ids, list)
            or (allocated > 0 and not artifact_ids)
            or not all(_non_empty(item) for item in artifact_ids)
            or len(artifact_ids) != len(set(artifact_ids))
        ):
            errors.append(f"{prefix}.artifact_ids must be a unique list and non-empty when tokens are allocated")
        for field in ("allocation_basis", "truncation_effect"):
            if not _non_empty(allocation.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if observed != set(expected_priorities):
        errors.append("allocations must cover all four categories exactly once")
    if allocated_sum > total_budget:
        errors.append("allocated token sum must not exceed total_token_budget")
    decision_tokens = sum(category_tokens.get(item, 0) for item in (
        "primary_observation",
        "constitutional_conflict",
        "rival_mechanism",
    ))
    decision_share = decision_tokens / total_budget if total_budget else 0
    narrative_share = category_tokens.get("narrative_background", 0) / total_budget if total_budget else 0
    if decision_share < 0.75:
        errors.append("decision-bearing evidence must receive at least 75 percent of total_token_budget")
    if narrative_share > 0.15:
        errors.append("narrative background must receive at most 15 percent of total_token_budget")
    if payload.get("truncation_order") != [
        "narrative_background",
        "rival_mechanism",
        "constitutional_conflict",
        "primary_observation",
    ]:
        errors.append("truncation_order must remove narrative background first and primary observation last")
    if payload.get("primary_observation_dropped_before_background") is not False:
        errors.append("primary_observation_dropped_before_background must be false")
    if payload.get("equal_category_allocation_required") is not False:
        errors.append("equal_category_allocation_required must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "allocated_token_count": allocated_sum,
        "decision_evidence_share": decision_share,
        "narrative_background_share": narrative_share,
    }

def validate_summary_interpretation_evidence_boundary(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Track summary interpretation and require original-evidence checks for consequential selection."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["summary interpretation evidence boundary must be an object"]}
    for field in ("boundary_record_id", "selection_record_id", "boundary_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    summary = payload.get("summary_artifact")
    if not isinstance(summary, dict):
        errors.append("summary_artifact must be an object")
        summary = {}
    for field in (
        "summary_id",
        "summary_fingerprint",
        "summary_text",
        "transform_record_id",
        "summarizer_runtime_fingerprint",
        "created_at",
    ):
        if not _non_empty(summary.get(field)):
            errors.append(f"summary_artifact.{field} must be a non-empty string")
    sources = summary.get("source_evidence")
    if not isinstance(sources, list) or not sources:
        errors.append("summary_artifact.source_evidence must be a non-empty list")
        sources = []
    source_ids = set()
    for index, source in enumerate(sources):
        prefix = f"summary_artifact.source_evidence[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in (
            "evidence_id",
            "evidence_fingerprint",
            "provenance_record_id",
            "controlled_original_locator",
        ):
            if not _non_empty(source.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        evidence_id = source.get("evidence_id")
        if evidence_id in source_ids:
            errors.append(f"{prefix}.evidence_id must be unique")
        source_ids.add(evidence_id)
        if source.get("raw_content_embedded") is not False:
            errors.append(f"{prefix}.raw_content_embedded must be false")
    for field in ("interpretive_choices", "omitted_details", "known_uncertainties"):
        values = summary.get(field)
        if (
            not isinstance(values, list)
            or not values
            or not all(_non_empty(item) for item in values)
        ):
            errors.append(f"summary_artifact.{field} must be a non-empty string list")
    if summary.get("epistemic_type") != "interpretation":
        errors.append("summary_artifact.epistemic_type must be interpretation")
    if summary.get("equivalent_to_raw_evidence") is not False:
        errors.append("summary_artifact.equivalent_to_raw_evidence must be false")
    if payload.get("selection_consequence") != "high":
        errors.append("selection_consequence must be high")
    citations = payload.get("decisive_evidence_citations")
    if not isinstance(citations, list) or not citations:
        errors.append("decisive_evidence_citations must be a non-empty list")
        citations = []
    citation_ids = set()
    for index, citation in enumerate(citations):
        prefix = f"decisive_evidence_citations[{index}]"
        if not isinstance(citation, dict):
            errors.append(f"{prefix} must be an object")
            continue
        citation_id = citation.get("citation_id")
        if not _non_empty(citation_id):
            errors.append(f"{prefix}.citation_id must be a non-empty string")
        elif citation_id in citation_ids:
            errors.append(f"{prefix}.citation_id must be unique")
        citation_ids.add(citation_id)
        evidence_id = citation.get("evidence_id")
        if evidence_id not in source_ids:
            errors.append(f"{prefix}.evidence_id must reference summary source evidence")
        for field in (
            "evidence_fingerprint",
            "original_access_receipt_id",
            "verified_at",
            "decision_effect",
        ):
            if not _non_empty(citation.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if citation.get("original_evidence_verified") is not True:
            errors.append(f"{prefix}.original_evidence_verified must be true")
        if citation.get("summary_used_as_sole_evidence") is not False:
            errors.append(f"{prefix}.summary_used_as_sole_evidence must be false")
    if payload.get("summary_silently_substituted_for_raw_evidence") is not False:
        errors.append("summary_silently_substituted_for_raw_evidence must be false")
    if payload.get("original_access_logged") is not True:
        errors.append("original_access_logged must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "source_evidence_count": len(source_ids),
        "decisive_citation_count": len(citation_ids),
        "summary_epistemic_type": summary.get("epistemic_type"),
    }

def validate_role_specific_context_thesis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Integrate role-specific hashed packets with opposition and explicit absence."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["role specific context thesis must be an object"]}
    for field in ("context_thesis_id", "cognition_thesis_id", "integration_fingerprint", "thesis_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected_components = {
        "bounded_context_guard": "validate_bounded_context_leakage_guard",
        "decision_anchors": "validate_decision_anchored_context_assembly",
        "anti_lockin_slots": "validate_anti_vocabulary_lockin_retrieval_slots",
        "explicit_absence": "validate_explicit_empty_retrieval_evidence",
        "preference_authority": "validate_constitution_authorized_preference_history",
        "sensitive_minimization": "validate_sensitive_signal_minimized_context",
        "artifact_context_binding": "validate_generated_artifact_context_manifest",
        "token_priority": "validate_decision_evidence_token_priority",
        "summary_boundary": "validate_summary_interpretation_evidence_boundary",
    }
    components = payload.get("component_evidence")
    if not isinstance(components, list) or len(components) != len(expected_components):
        errors.append("component_evidence must contain exactly the nine context components")
        components = []
    observed_components = set()
    for index, component in enumerate(components):
        prefix = f"component_evidence[{index}]"
        if not isinstance(component, dict):
            errors.append(f"{prefix} must be an object")
            continue
        name = component.get("component")
        observed_components.add(name)
        expected_validator = expected_components.get(name)
        if expected_validator is None:
            errors.append(f"{prefix}.component is not recognized")
        elif component.get("validator_id") != expected_validator:
            errors.append(f"{prefix}.validator_id must be {expected_validator}")
        for field in ("evidence_artifact_id", "evidence_fingerprint", "verification_record_id"):
            if not _non_empty(component.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if component.get("verified") is not True:
            errors.append(f"{prefix}.verified must be true")
    if observed_components != set(expected_components):
        errors.append("component_evidence must cover all context components exactly once")
    expected_roles = {"interpreter", "inventor", "adversary", "selector", "outcome_analyst"}
    packets = payload.get("role_packets")
    if not isinstance(packets, list) or len(packets) != len(expected_roles):
        errors.append("role_packets must contain exactly five role-specific packets")
        packets = []
    observed_roles = set()
    packet_fingerprints = set()
    manifest_fingerprints = set()
    for index, packet in enumerate(packets):
        prefix = f"role_packets[{index}]"
        if not isinstance(packet, dict):
            errors.append(f"{prefix} must be an object")
            continue
        role = packet.get("role")
        observed_roles.add(role)
        if role not in expected_roles:
            errors.append(f"{prefix}.role is not recognized")
        for field in ("packet_id", "packet_fingerprint", "context_manifest_id", "context_manifest_fingerprint"):
            if not _non_empty(packet.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        packet_fingerprints.add(packet.get("packet_fingerprint"))
        manifest_fingerprints.add(packet.get("context_manifest_fingerprint"))
        evidence_ids = packet.get("evidence_artifact_ids")
        if (
            not isinstance(evidence_ids, list)
            or not evidence_ids
            or not all(_non_empty(item) for item in evidence_ids)
            or len(evidence_ids) != len(set(evidence_ids))
        ):
            errors.append(f"{prefix}.evidence_artifact_ids must be a non-empty unique string list")
        opposition = packet.get("opposition_slot")
        if not isinstance(opposition, dict):
            errors.append(f"{prefix}.opposition_slot must be an object")
            opposition = {}
        for field in ("slot_id", "query_fingerprint"):
            if not _non_empty(opposition.get(field)):
                errors.append(f"{prefix}.opposition_slot.{field} must be a non-empty string")
        status = opposition.get("status")
        if status == "filled":
            if not opposition.get("evidence_artifact_ids"):
                errors.append(f"{prefix} filled opposition requires evidence artifacts")
            if opposition.get("missing_evidence_marker") not in ("", None):
                errors.append(f"{prefix} filled opposition must not carry a missing marker")
        elif status == "empty":
            if opposition.get("evidence_artifact_ids") != []:
                errors.append(f"{prefix} empty opposition must contain no evidence artifacts")
            if not _non_empty(opposition.get("missing_evidence_marker")):
                errors.append(f"{prefix} empty opposition requires a missing_evidence_marker")
        else:
            errors.append(f"{prefix}.opposition_slot.status must be filled or empty")
        absence = packet.get("explicit_absence_markers")
        if not isinstance(absence, list) or not all(_non_empty(item) for item in absence):
            errors.append(f"{prefix}.explicit_absence_markers must be a string list")
        if packet.get("role_specific_scope_enforced") is not True:
            errors.append(f"{prefix}.role_specific_scope_enforced must be true")
    if observed_roles != expected_roles:
        errors.append("role_packets must cover every cognitive role exactly once")
    if len(packet_fingerprints) != len(expected_roles) or len(manifest_fingerprints) != len(expected_roles):
        errors.append("each role must have a distinct packet and context manifest fingerprint")
    invariants = payload.get("context_invariants")
    if not isinstance(invariants, dict):
        errors.append("context_invariants must be an object")
        invariants = {}
    for field in (
        "packets_hash_addressed",
        "opposition_mandatory",
        "absence_explicit",
        "role_scope_minimized",
        "summary_interpretation_visible",
        "sensitive_originals_controlled",
    ):
        if invariants.get(field) is not True:
            errors.append(f"context_invariants.{field} must be true")
    for field in ("maximal_shared_context_used", "one_manifest_shared_by_all_roles"):
        if invariants.get(field) is not False:
            errors.append(f"context_invariants.{field} must be false")
    if payload.get("context_thesis_decision") != "integrated":
        errors.append("context_thesis_decision must be integrated")
    return {
        "valid": not errors,
        "errors": errors,
        "component_count": len(observed_components),
        "role_packet_count": len(observed_roles),
        "context_thesis_decision": payload.get("context_thesis_decision"),
    }

def validate_disqualification_dominance_decision_structure(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Filter by disqualification and Pareto-style dominance before comparison."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["disqualification dominance decision structure must be an object"]}
    for field in ("decision_structure_id", "candidate_set_fingerprint", "constitution_fingerprint", "structure_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    candidates = payload.get("candidate_ids")
    if (
        not isinstance(candidates, list)
        or len(candidates) < 3
        or not all(_non_empty(item) for item in candidates)
        or len(candidates) != len(set(candidates))
    ):
        errors.append("candidate_ids must contain at least three unique candidates")
        candidates = []
    candidate_set = set(candidates)
    dimensions = payload.get("value_dimensions")
    if (
        not isinstance(dimensions, list)
        or len(dimensions) < 2
        or not all(_non_empty(item) for item in dimensions)
        or len(dimensions) != len(set(dimensions))
    ):
        errors.append("value_dimensions must contain at least two unique plural values")
        dimensions = []
    dimension_set = set(dimensions)
    disqualifications = payload.get("disqualification_assessments")
    if not isinstance(disqualifications, list) or len(disqualifications) != len(candidates):
        errors.append("disqualification_assessments must cover every candidate exactly once")
        disqualifications = []
    assessed = set()
    disqualified = set()
    eligible = set()
    for index, assessment in enumerate(disqualifications):
        prefix = f"disqualification_assessments[{index}]"
        if not isinstance(assessment, dict):
            errors.append(f"{prefix} must be an object")
            continue
        candidate_id = assessment.get("candidate_id")
        if candidate_id not in candidate_set:
            errors.append(f"{prefix}.candidate_id must reference a known candidate")
        elif candidate_id in assessed:
            errors.append(f"{prefix}.candidate_id must be unique")
        assessed.add(candidate_id)
        checks = assessment.get("criterion_checks")
        if not isinstance(checks, list) or not checks:
            errors.append(f"{prefix}.criterion_checks must be a non-empty list")
            checks = []
        violated = False
        for check_index, check in enumerate(checks):
            check_prefix = f"{prefix}.criterion_checks[{check_index}]"
            if not isinstance(check, dict):
                errors.append(f"{check_prefix} must be an object")
                continue
            for field in ("criterion_id", "evidence_fingerprint", "assessment_rationale"):
                if not _non_empty(check.get(field)):
                    errors.append(f"{check_prefix}.{field} must be a non-empty string")
            if check.get("result") not in {"satisfied", "violated"}:
                errors.append(f"{check_prefix}.result must be satisfied or violated")
            violated = violated or check.get("result") == "violated"
        expected_status = "disqualified" if violated else "eligible"
        if assessment.get("status") != expected_status:
            errors.append(f"{prefix}.status must be {expected_status}")
        if violated:
            disqualified.add(candidate_id)
        else:
            eligible.add(candidate_id)
    if assessed != candidate_set:
        errors.append("disqualification_assessments must exactly cover candidate_ids")
    dominance = payload.get("dominance_assessments")
    if not isinstance(dominance, list):
        errors.append("dominance_assessments must be a list")
        dominance = []
    dominated = set()
    dominance_ids = set()
    for index, assessment in enumerate(dominance):
        prefix = f"dominance_assessments[{index}]"
        if not isinstance(assessment, dict):
            errors.append(f"{prefix} must be an object")
            continue
        dominance_id = assessment.get("dominance_id")
        if not _non_empty(dominance_id):
            errors.append(f"{prefix}.dominance_id must be a non-empty string")
        elif dominance_id in dominance_ids:
            errors.append(f"{prefix}.dominance_id must be unique")
        dominance_ids.add(dominance_id)
        dominant_id = assessment.get("dominant_candidate_id")
        dominated_id = assessment.get("dominated_candidate_id")
        if dominant_id not in eligible or dominated_id not in eligible or dominant_id == dominated_id:
            errors.append(f"{prefix} must compare two distinct eligible candidates")
        comparisons = assessment.get("dimension_comparisons")
        if not isinstance(comparisons, list) or len(comparisons) != len(dimensions):
            errors.append(f"{prefix}.dimension_comparisons must cover every value dimension")
            comparisons = []
        compared_dimensions = set()
        relations = []
        for comparison in comparisons:
            if not isinstance(comparison, dict):
                errors.append(f"{prefix}.dimension_comparisons items must be objects")
                continue
            dimension = comparison.get("dimension")
            compared_dimensions.add(dimension)
            if dimension not in dimension_set:
                errors.append(f"{prefix} cites an unknown value dimension")
            relation = comparison.get("relation")
            if relation not in {"better", "equal", "worse", "unknown"}:
                errors.append(f"{prefix} relation must be better, equal, worse, or unknown")
            relations.append(relation)
            if not _non_empty(comparison.get("evidence_fingerprint")):
                errors.append(f"{prefix} dimension comparison requires evidence_fingerprint")
        if compared_dimensions != dimension_set:
            errors.append(f"{prefix}.dimension_comparisons must cover dimensions exactly once")
        valid_dominance = (
            bool(relations)
            and all(item in {"better", "equal"} for item in relations)
            and "better" in relations
        )
        if assessment.get("dominance_established") is not valid_dominance:
            errors.append(f"{prefix}.dominance_established must match plural-dimension relations")
        if valid_dominance:
            dominated.add(dominated_id)
    expected_comparison = [item for item in candidates if item in eligible and item not in dominated]
    if payload.get("comparison_candidate_ids") != expected_comparison:
        errors.append("comparison_candidate_ids must be the ordered eligible non-dominated frontier")
    if payload.get("stage_order") != ["disqualification", "dominance", "comparison"]:
        errors.append("stage_order must be disqualification, dominance, comparison")
    if payload.get("global_pairwise_ranking_performed_first") is not False:
        errors.append("global_pairwise_ranking_performed_first must be false")
    if payload.get("transitive_preference_inferred_across_values") is not False:
        errors.append("transitive_preference_inferred_across_values must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "disqualified_candidate_ids": sorted(item for item in disqualified if _non_empty(item)),
        "dominated_candidate_ids": sorted(item for item in dominated if _non_empty(item)),
        "comparison_candidate_ids": expected_comparison,
    }

def validate_hard_constitutional_disqualification(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Remove hard-violating candidates unless a frozen authorized clause permits exception."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["hard constitutional disqualification must be an object"]}
    for field in (
        "constitutional_gate_id",
        "constitution_state_id",
        "constitution_fingerprint",
        "decision_structure_id",
        "gate_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("constitution_frozen_before_candidate_review") is not True:
        errors.append("constitution_frozen_before_candidate_review must be true")
    assessments = payload.get("candidate_assessments")
    if not isinstance(assessments, list) or not assessments:
        errors.append("candidate_assessments must be a non-empty list")
        assessments = []
    candidate_ids = set()
    removed = set()
    eligible = set()
    exception_ids = set()
    for index, assessment in enumerate(assessments):
        prefix = f"candidate_assessments[{index}]"
        if not isinstance(assessment, dict):
            errors.append(f"{prefix} must be an object")
            continue
        candidate_id = assessment.get("candidate_id")
        if not _non_empty(candidate_id):
            errors.append(f"{prefix}.candidate_id must be a non-empty string")
        elif candidate_id in candidate_ids:
            errors.append(f"{prefix}.candidate_id must be unique")
        candidate_ids.add(candidate_id)
        violations = assessment.get("hard_violations")
        if not isinstance(violations, list):
            errors.append(f"{prefix}.hard_violations must be a list")
            violations = []
        violation_ids = set()
        unexcepted = 0
        for violation_index, violation in enumerate(violations):
            violation_prefix = f"{prefix}.hard_violations[{violation_index}]"
            if not isinstance(violation, dict):
                errors.append(f"{violation_prefix} must be an object")
                continue
            for field in (
                "violation_id",
                "violated_clause_id",
                "violation_scope",
                "evidence_fingerprint",
                "assessment_rationale",
            ):
                if not _non_empty(violation.get(field)):
                    errors.append(f"{violation_prefix}.{field} must be a non-empty string")
            violation_id = violation.get("violation_id")
            if violation_id in violation_ids:
                errors.append(f"{violation_prefix}.violation_id must be unique")
            violation_ids.add(violation_id)
            exception = violation.get("exception")
            if not isinstance(exception, dict):
                errors.append(f"{violation_prefix}.exception must be an object")
                exception = {}
            permitted = exception.get("permitted")
            if not isinstance(permitted, bool):
                errors.append(f"{violation_prefix}.exception.permitted must be boolean")
            valid_exception = False
            if permitted:
                for field in (
                    "exception_id",
                    "authorizing_clause_id",
                    "authorizing_clause_fingerprint",
                    "authorized_by",
                    "authorized_scope",
                    "authorization_record_id",
                ):
                    if not _non_empty(exception.get(field)):
                        errors.append(f"{violation_prefix}.exception.{field} is required")
                exception_id = exception.get("exception_id")
                if exception_id in exception_ids:
                    errors.append(f"{violation_prefix}.exception.exception_id must be globally unique")
                exception_ids.add(exception_id)
                if exception.get("explicitly_names_violated_clause_id") != violation.get("violated_clause_id"):
                    errors.append(f"{violation_prefix}.exception must explicitly name the violated clause")
                if exception.get("authorized_scope") != violation.get("violation_scope"):
                    errors.append(f"{violation_prefix}.exception.authorized_scope must match violation_scope")
                if exception.get("present_in_frozen_constitution") is not True:
                    errors.append(f"{violation_prefix}.exception.present_in_frozen_constitution must be true")
                if exception.get("authority_verified") is not True:
                    errors.append(f"{violation_prefix}.exception.authority_verified must be true")
                if exception.get("invented_by_model") is not False:
                    errors.append(f"{violation_prefix}.exception.invented_by_model must be false")
                valid_exception = (
                    _non_empty(exception.get("authorizing_clause_id"))
                    and exception.get("explicitly_names_violated_clause_id") == violation.get("violated_clause_id")
                    and exception.get("authorized_scope") == violation.get("violation_scope")
                    and exception.get("present_in_frozen_constitution") is True
                    and exception.get("authority_verified") is True
                    and exception.get("invented_by_model") is False
                )
            else:
                if exception.get("exception_id") not in ("", None):
                    errors.append(f"{violation_prefix} unpermitted exception must not have exception_id")
            if not valid_exception:
                unexcepted += 1
        expected_status = "removed" if unexcepted else "eligible"
        if assessment.get("gate_status") != expected_status:
            errors.append(f"{prefix}.gate_status must be {expected_status}")
        if expected_status == "removed":
            removed.add(candidate_id)
        else:
            eligible.add(candidate_id)
        if assessment.get("model_may_override_gate") is not False:
            errors.append(f"{prefix}.model_may_override_gate must be false")
    if payload.get("eligible_candidate_ids") != [
        item.get("candidate_id")
        for item in assessments
        if isinstance(item, dict) and item.get("candidate_id") in eligible
    ]:
        errors.append("eligible_candidate_ids must exactly preserve eligible assessment order")
    if payload.get("removed_candidate_ids") != [
        item.get("candidate_id")
        for item in assessments
        if isinstance(item, dict) and item.get("candidate_id") in removed
    ]:
        errors.append("removed_candidate_ids must exactly preserve removed assessment order")
    if payload.get("model_generated_exception_permission_allowed") is not False:
        errors.append("model_generated_exception_permission_allowed must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "eligible_candidate_ids": sorted(item for item in eligible if _non_empty(item)),
        "removed_candidate_ids": sorted(item for item in removed if _non_empty(item)),
        "authorized_exception_count": len(exception_ids),
    }

def validate_structural_candidate_completeness_gate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Keep structurally incomplete missions out of scoring and dominance."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["structural candidate completeness gate must be an object"]}
    for field in ("completeness_gate_id", "candidate_set_fingerprint", "gate_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    required_fields = [
        "beneficiary",
        "causal_thesis",
        "disconfirmation_condition",
        "resource_renewal_plan",
    ]
    if payload.get("required_structural_fields") != required_fields:
        errors.append("required_structural_fields must contain the four exact mission fields")
    candidates = payload.get("candidate_assessments")
    if not isinstance(candidates, list) or not candidates:
        errors.append("candidate_assessments must be a non-empty list")
        candidates = []
    candidate_ids = set()
    complete_ids = []
    incomplete_ids = []
    for index, candidate in enumerate(candidates):
        prefix = f"candidate_assessments[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{prefix} must be an object")
            continue
        candidate_id = candidate.get("candidate_id")
        if not _non_empty(candidate_id):
            errors.append(f"{prefix}.candidate_id must be a non-empty string")
        elif candidate_id in candidate_ids:
            errors.append(f"{prefix}.candidate_id must be unique")
        candidate_ids.add(candidate_id)
        candidate_fingerprint = candidate.get("candidate_fingerprint")
        if not _non_empty(candidate_fingerprint):
            errors.append(f"{prefix}.candidate_fingerprint must be a non-empty string")
        structure = candidate.get("mission_structure")
        if not isinstance(structure, dict):
            errors.append(f"{prefix}.mission_structure must be an object")
            structure = {}
        missing = [field for field in required_fields if not _non_empty(structure.get(field))]
        if candidate.get("missing_fields") != missing:
            errors.append(f"{prefix}.missing_fields must exactly preserve required-field order")
        expected_status = "incomplete" if missing else "complete"
        if candidate.get("completeness_status") != expected_status:
            errors.append(f"{prefix}.completeness_status must be {expected_status}")
        if missing:
            incomplete_ids.append(candidate_id)
            if candidate.get("eligible_for_scoring") is not False:
                errors.append(f"{prefix}.eligible_for_scoring must be false when incomplete")
            if candidate.get("eligible_for_dominance") is not False:
                errors.append(f"{prefix}.eligible_for_dominance must be false when incomplete")
            request = candidate.get("completion_request")
            if not isinstance(request, dict):
                errors.append(f"{prefix}.completion_request must be an object")
                request = {}
            for field in ("request_id", "requested_from_role_id", "wake_trigger", "request_rationale"):
                if not _non_empty(request.get(field)):
                    errors.append(f"{prefix}.completion_request.{field} must be a non-empty string")
            if request.get("requested_fields") != missing:
                errors.append(f"{prefix}.completion_request.requested_fields must exactly match missing_fields")
            if candidate.get("low_score_assigned_for_missingness") is not False:
                errors.append(f"{prefix}.low_score_assigned_for_missingness must be false")
        else:
            complete_ids.append(candidate_id)
            if candidate.get("eligible_for_scoring") is not True:
                errors.append(f"{prefix}.eligible_for_scoring must be true when complete")
            if candidate.get("eligible_for_dominance") is not True:
                errors.append(f"{prefix}.eligible_for_dominance must be true when complete")
            if candidate.get("completion_request") not in ({}, None):
                errors.append(f"{prefix}.completion_request must be empty when complete")
            if candidate.get("low_score_assigned_for_missingness") is not False:
                errors.append(f"{prefix}.low_score_assigned_for_missingness must be false")
    if payload.get("complete_candidate_ids") != complete_ids:
        errors.append("complete_candidate_ids must exactly preserve assessment order")
    if payload.get("incomplete_candidate_ids") != incomplete_ids:
        errors.append("incomplete_candidate_ids must exactly preserve assessment order")
    if payload.get("incomplete_candidates_ranked") is not False:
        errors.append("incomplete_candidates_ranked must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "complete_candidate_ids": complete_ids,
        "incomplete_candidate_ids": incomplete_ids,
    }

def validate_shared_assumption_dominance_frontier(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Permit dominance only under identical assumptions; otherwise expose a frontier."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["shared assumption dominance frontier must be an object"]}
    for field in ("assumption_gate_id", "decision_structure_id", "candidate_set_fingerprint", "gate_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    candidates = payload.get("candidate_assumptions")
    if not isinstance(candidates, list) or len(candidates) < 2:
        errors.append("candidate_assumptions must contain at least two candidates")
        candidates = []
    candidate_ids = set()
    assumption_maps = {}
    for index, candidate in enumerate(candidates):
        prefix = f"candidate_assumptions[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{prefix} must be an object")
            continue
        candidate_id = candidate.get("candidate_id")
        if not _non_empty(candidate_id):
            errors.append(f"{prefix}.candidate_id must be a non-empty string")
        elif candidate_id in candidate_ids:
            errors.append(f"{prefix}.candidate_id must be unique")
        candidate_ids.add(candidate_id)
        assumptions = candidate.get("assumptions")
        if not isinstance(assumptions, list) or not assumptions:
            errors.append(f"{prefix}.assumptions must be a non-empty list")
            assumptions = []
        mapped = {}
        for assumption_index, assumption in enumerate(assumptions):
            assumption_prefix = f"{prefix}.assumptions[{assumption_index}]"
            if not isinstance(assumption, dict):
                errors.append(f"{assumption_prefix} must be an object")
                continue
            for field in ("assumption_id", "assumed_value", "assumption_fingerprint", "evidence_fingerprint"):
                if not _non_empty(assumption.get(field)):
                    errors.append(f"{assumption_prefix}.{field} must be a non-empty string")
            assumption_id = assumption.get("assumption_id")
            if assumption_id in mapped:
                errors.append(f"{assumption_prefix}.assumption_id must be unique per candidate")
            mapped[assumption_id] = (
                assumption.get("assumed_value"),
                assumption.get("assumption_fingerprint"),
            )
        assumption_maps[candidate_id] = mapped
    comparisons = payload.get("pair_assessments")
    if not isinstance(comparisons, list) or not comparisons:
        errors.append("pair_assessments must be a non-empty list")
        comparisons = []
    pair_ids = set()
    frontier_ids = set()
    for index, comparison in enumerate(comparisons):
        prefix = f"pair_assessments[{index}]"
        if not isinstance(comparison, dict):
            errors.append(f"{prefix} must be an object")
            continue
        pair_id = comparison.get("pair_id")
        if not _non_empty(pair_id):
            errors.append(f"{prefix}.pair_id must be a non-empty string")
        elif pair_id in pair_ids:
            errors.append(f"{prefix}.pair_id must be unique")
        pair_ids.add(pair_id)
        left = comparison.get("left_candidate_id")
        right = comparison.get("right_candidate_id")
        if left not in candidate_ids or right not in candidate_ids or left == right:
            errors.append(f"{prefix} must reference two distinct known candidates")
        left_map = assumption_maps.get(left, {})
        right_map = assumption_maps.get(right, {})
        shared = left_map == right_map and bool(left_map)
        if comparison.get("assumptions_shared") is not shared:
            errors.append(f"{prefix}.assumptions_shared must match exact assumption IDs, values, and hashes")
        if shared:
            if comparison.get("dominance_computation_allowed") is not True:
                errors.append(f"{prefix}.dominance_computation_allowed must be true for shared assumptions")
            if comparison.get("assumption_frontier") not in ({}, None):
                errors.append(f"{prefix}.assumption_frontier must be empty for shared assumptions")
            if comparison.get("dominance_assessment_id") in ("", None):
                errors.append(f"{prefix}.dominance_assessment_id is required for shared assumptions")
        else:
            if comparison.get("dominance_computation_allowed") is not False:
                errors.append(f"{prefix}.dominance_computation_allowed must be false when assumptions differ")
            if comparison.get("dominance_assessment_id") not in ("", None):
                errors.append(f"{prefix}.dominance_assessment_id must be empty when assumptions differ")
            frontier = comparison.get("assumption_frontier")
            if not isinstance(frontier, dict):
                errors.append(f"{prefix}.assumption_frontier must be an object")
                frontier = {}
            for field in (
                "frontier_id",
                "decision_relevance",
                "discriminating_evidence_needed",
                "resolution_trigger",
            ):
                if not _non_empty(frontier.get(field)):
                    errors.append(f"{prefix}.assumption_frontier.{field} must be a non-empty string")
            frontier_id = frontier.get("frontier_id")
            if frontier_id in frontier_ids:
                errors.append(f"{prefix}.assumption_frontier.frontier_id must be unique")
            frontier_ids.add(frontier_id)
            differing = sorted(
                assumption_id
                for assumption_id in set(left_map).union(right_map)
                if left_map.get(assumption_id) != right_map.get(assumption_id)
            )
            if frontier.get("differing_assumption_ids") != differing:
                errors.append(f"{prefix}.assumption_frontier.differing_assumption_ids must match exact differences")
            if frontier.get("preserved_as_unresolved") is not True:
                errors.append(f"{prefix}.assumption_frontier.preserved_as_unresolved must be true")
        if comparison.get("assumption_difference_treated_as_value_difference") is not False:
            errors.append(f"{prefix}.assumption_difference_treated_as_value_difference must be false")
    if payload.get("cross_assumption_dominance_allowed") is not False:
        errors.append("cross_assumption_dominance_allowed must be false")
    if payload.get("unresolved_frontiers_visible_to_selector") is not True:
        errors.append("unresolved_frontiers_visible_to_selector must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "candidate_count": len(candidate_ids),
        "pair_count": len(pair_ids),
        "assumption_frontier_count": len(frontier_ids),
    }

def validate_adversarial_axis_sensitivity_review(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Review every non-dominated candidate by plural axes and sensitivity ranges."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["adversarial axis sensitivity review must be an object"]}
    for field in ("review_set_id", "non_dominated_frontier_fingerprint", "review_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    candidates = payload.get("non_dominated_candidate_ids")
    if (
        not isinstance(candidates, list)
        or len(candidates) < 2
        or not all(_non_empty(item) for item in candidates)
        or len(candidates) != len(set(candidates))
    ):
        errors.append("non_dominated_candidate_ids must contain at least two unique candidates")
        candidates = []
    candidate_set = set(candidates)
    axes = payload.get("adversarial_axes")
    if (
        not isinstance(axes, list)
        or len(axes) < 3
        or not all(_non_empty(item) for item in axes)
        or len(axes) != len(set(axes))
    ):
        errors.append("adversarial_axes must contain at least three unique axes")
        axes = []
    axis_set = set(axes)
    reviews = payload.get("candidate_reviews")
    if not isinstance(reviews, list) or len(reviews) != len(candidates):
        errors.append("candidate_reviews must cover every non-dominated candidate")
        reviews = []
    reviewed = set()
    sensitivity_ids = set()
    for index, review in enumerate(reviews):
        prefix = f"candidate_reviews[{index}]"
        if not isinstance(review, dict):
            errors.append(f"{prefix} must be an object")
            continue
        candidate_id = review.get("candidate_id")
        if candidate_id not in candidate_set:
            errors.append(f"{prefix}.candidate_id must reference a non-dominated candidate")
        elif candidate_id in reviewed:
            errors.append(f"{prefix}.candidate_id must be unique")
        reviewed.add(candidate_id)
        axis_reviews = review.get("axis_reviews")
        if not isinstance(axis_reviews, list) or len(axis_reviews) != len(axes):
            errors.append(f"{prefix}.axis_reviews must cover every adversarial axis")
            axis_reviews = []
        reviewed_axes = set()
        for axis_index, axis_review in enumerate(axis_reviews):
            axis_prefix = f"{prefix}.axis_reviews[{axis_index}]"
            if not isinstance(axis_review, dict):
                errors.append(f"{axis_prefix} must be an object")
                continue
            axis = axis_review.get("axis")
            reviewed_axes.add(axis)
            if axis not in axis_set:
                errors.append(f"{axis_prefix}.axis is not registered")
            for field in (
                "adversarial_question",
                "finding",
                "worst_case_condition",
                "failure_signal",
            ):
                if not _non_empty(axis_review.get(field)):
                    errors.append(f"{axis_prefix}.{field} must be a non-empty string")
            for field in ("supporting_evidence_ids", "opposing_evidence_ids"):
                values = axis_review.get(field)
                if (
                    not isinstance(values, list)
                    or not values
                    or not all(_non_empty(item) for item in values)
                    or len(values) != len(set(values))
                ):
                    errors.append(f"{axis_prefix}.{field} must be a non-empty unique string list")
            sensitivity = axis_review.get("sensitivity_range")
            if not isinstance(sensitivity, dict):
                errors.append(f"{axis_prefix}.sensitivity_range must be an object")
                sensitivity = {}
            for field in (
                "sensitivity_id",
                "assumption_id",
                "lower_bound",
                "upper_bound",
                "outcome_at_lower_bound",
                "outcome_at_upper_bound",
                "selection_flip_threshold",
            ):
                if not _non_empty(sensitivity.get(field)):
                    errors.append(f"{axis_prefix}.sensitivity_range.{field} must be a non-empty string")
            sensitivity_id = sensitivity.get("sensitivity_id")
            if sensitivity_id in sensitivity_ids:
                errors.append(f"{axis_prefix}.sensitivity_range.sensitivity_id must be globally unique")
            sensitivity_ids.add(sensitivity_id)
            if not isinstance(sensitivity.get("fragile"), bool):
                errors.append(f"{axis_prefix}.sensitivity_range.fragile must be boolean")
        if reviewed_axes != axis_set:
            errors.append(f"{prefix}.axis_reviews must cover registered axes exactly once")
        if not _non_empty(review.get("review_fingerprint")):
            errors.append(f"{prefix}.review_fingerprint must be a non-empty string")
    if reviewed != candidate_set:
        errors.append("candidate_reviews must exactly cover non_dominated_candidate_ids")
    if payload.get("aggregate_numerical_score_present") is not False:
        errors.append("aggregate_numerical_score_present must be false")
    if payload.get("axis_tradeoffs_collapsed") is not False:
        errors.append("axis_tradeoffs_collapsed must be false")
    if payload.get("sensitivity_ranges_visible_to_selector") is not True:
        errors.append("sensitivity_ranges_visible_to_selector must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "reviewed_candidate_count": len(reviewed),
        "axis_count": len(axis_set),
        "sensitivity_range_count": len(sensitivity_ids),
    }

def validate_precommitted_assumption_probe_branches(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Probe one selection-controlling assumption with frozen exhaustive result branches."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["precommitted assumption probe branches must be an object"]}
    for field in (
        "probe_design_id",
        "sensitivity_review_id",
        "controlling_assumption_id",
        "assumption_fingerprint",
        "selection_flip_threshold",
        "design_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("selection_controlled_by_single_assumption") is not True:
        errors.append("selection_controlled_by_single_assumption must be true")
    affected = payload.get("affected_candidate_ids")
    if (
        not isinstance(affected, list)
        or len(affected) < 2
        or not all(_non_empty(item) for item in affected)
        or len(affected) != len(set(affected))
    ):
        errors.append("affected_candidate_ids must contain at least two unique candidates")
        affected = []
    affected_set = set(affected)
    probe = payload.get("probe")
    if not isinstance(probe, dict):
        errors.append("probe must be an object")
        probe = {}
    for field in (
        "probe_id",
        "measurement",
        "population",
        "maximum_cost",
        "maximum_harm",
        "stop_condition",
        "expires_at",
        "observation_method",
    ):
        if not _non_empty(probe.get(field)):
            errors.append(f"probe.{field} must be a non-empty string")
    if probe.get("safe_within_authority") is not True:
        errors.append("probe.safe_within_authority must be true")
    if probe.get("reversible") is not True:
        errors.append("probe.reversible must be true")
    branches = payload.get("precommitted_branches")
    if not isinstance(branches, list) or len(branches) < 2:
        errors.append("precommitted_branches must contain at least two result branches")
        branches = []
    branch_ids = set()
    interval_indices = set()
    for index, branch in enumerate(branches):
        prefix = f"precommitted_branches[{index}]"
        if not isinstance(branch, dict):
            errors.append(f"{prefix} must be an object")
            continue
        branch_id = branch.get("branch_id")
        if not _non_empty(branch_id):
            errors.append(f"{prefix}.branch_id must be a non-empty string")
        elif branch_id in branch_ids:
            errors.append(f"{prefix}.branch_id must be unique")
        branch_ids.add(branch_id)
        interval_index = branch.get("interval_index")
        if not isinstance(interval_index, int) or isinstance(interval_index, bool) or interval_index < 1:
            errors.append(f"{prefix}.interval_index must be a positive integer")
        elif interval_index in interval_indices:
            errors.append(f"{prefix}.interval_index must be unique")
        interval_indices.add(interval_index)
        for field in (
            "result_condition",
            "lower_bound",
            "upper_bound",
            "boundary_semantics",
            "branch_action",
            "branch_rationale",
        ):
            if not _non_empty(branch.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        selected = branch.get("selected_candidate_ids")
        if (
            not isinstance(selected, list)
            or not selected
            or any(item not in affected_set for item in selected)
            or len(selected) != len(set(selected))
        ):
            errors.append(f"{prefix}.selected_candidate_ids must be a non-empty known-candidate list")
        if branch.get("selection_mode") not in {
            "commit",
            "bounded_exploration",
            "discriminating_probe",
            "defer",
        }:
            errors.append(f"{prefix}.selection_mode is not recognized")
    if interval_indices != set(range(1, len(branches) + 1)):
        errors.append("branch interval_index values must be contiguous from one")
    if payload.get("branches_exhaustive") is not True:
        errors.append("branches_exhaustive must be true")
    if payload.get("branches_mutually_exclusive") is not True:
        errors.append("branches_mutually_exclusive must be true")
    if payload.get("branches_frozen_before_observation") is not True:
        errors.append("branches_frozen_before_observation must be true")
    if not _non_empty(payload.get("branch_manifest_fingerprint")):
        errors.append("branch_manifest_fingerprint must be a non-empty string")
    if payload.get("posthoc_branch_rewrite_allowed") is not False:
        errors.append("posthoc_branch_rewrite_allowed must be false")
    if payload.get("selection_before_probe_result") != "discriminating_probe":
        errors.append("selection_before_probe_result must be discriminating_probe")
    return {
        "valid": not errors,
        "errors": errors,
        "branch_count": len(branch_ids),
        "affected_candidate_ids": affected,
        "selection_before_probe_result": payload.get("selection_before_probe_result"),
    }

def validate_no_safe_probe_reversible_decision(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Choose the most reversible in-mandate mission or defer beyond authority."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["no safe probe reversible decision must be an object"]}
    for field in (
        "decision_record_id",
        "sensitivity_review_id",
        "authority_mandate_id",
        "authority_mandate_fingerprint",
        "decision_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("safe_probe_available") is not False:
        errors.append("safe_probe_available must be false")
    if not _non_empty(payload.get("safe_probe_absence_rationale")):
        errors.append("safe_probe_absence_rationale must be a non-empty string")
    assessments = payload.get("candidate_assessments")
    if not isinstance(assessments, list) or len(assessments) < 2:
        errors.append("candidate_assessments must contain at least two candidates")
        assessments = []
    candidate_ids = set()
    in_mandate = []
    ranks = set()
    for index, assessment in enumerate(assessments):
        prefix = f"candidate_assessments[{index}]"
        if not isinstance(assessment, dict):
            errors.append(f"{prefix} must be an object")
            continue
        candidate_id = assessment.get("candidate_id")
        if not _non_empty(candidate_id):
            errors.append(f"{prefix}.candidate_id must be a non-empty string")
        elif candidate_id in candidate_ids:
            errors.append(f"{prefix}.candidate_id must be unique")
        candidate_ids.add(candidate_id)
        for field in (
            "candidate_fingerprint",
            "rollback_mechanism",
            "rollback_time",
            "residual_harm_after_rollback",
            "authority_scope_assessment",
            "consequence_assessment",
        ):
            if not _non_empty(assessment.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        rank = assessment.get("reversibility_rank")
        if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
            errors.append(f"{prefix}.reversibility_rank must be a positive integer")
        elif rank in ranks:
            errors.append(f"{prefix}.reversibility_rank must be unique")
        ranks.add(rank)
        authority_bounded = assessment.get("within_authority_mandate")
        consequence_bounded = assessment.get("consequences_within_mandate")
        if not isinstance(authority_bounded, bool):
            errors.append(f"{prefix}.within_authority_mandate must be boolean")
        if not isinstance(consequence_bounded, bool):
            errors.append(f"{prefix}.consequences_within_mandate must be boolean")
        if authority_bounded and consequence_bounded:
            in_mandate.append((rank, candidate_id))
        if assessment.get("reversibility_claim_evidence_fingerprint") in ("", None):
            errors.append(f"{prefix}.reversibility_claim_evidence_fingerprint must be non-empty")
    decision = payload.get("decision")
    if not isinstance(decision, dict):
        errors.append("decision must be an object")
        decision = {}
    mode = decision.get("mode")
    if in_mandate:
        expected_candidate = min(in_mandate)[1]
        if mode != "bounded_reversible_mission":
            errors.append("decision.mode must be bounded_reversible_mission when an in-mandate candidate exists")
        if decision.get("selected_candidate_id") != expected_candidate:
            errors.append("decision.selected_candidate_id must be the most reversible in-mandate candidate")
        for field in ("commitment_scope", "rollback_trigger", "review_at", "authority_return_trigger"):
            if not _non_empty(decision.get(field)):
                errors.append(f"bounded reversible decision requires decision.{field}")
        if decision.get("deferred") is not False:
            errors.append("bounded reversible decision must not be deferred")
    else:
        if mode != "defer":
            errors.append("decision.mode must be defer when every candidate exceeds the mandate")
        if decision.get("selected_candidate_id") not in ("", None):
            errors.append("defer decision must not select a candidate")
        for field in ("defer_reason", "required_authority_id", "escalation_record_id", "wake_trigger"):
            if not _non_empty(decision.get(field)):
                errors.append(f"defer decision requires decision.{field}")
        if decision.get("deferred") is not True:
            errors.append("defer decision must set deferred true")
    if decision.get("irreversible_commitment_made") is not False:
        errors.append("decision.irreversible_commitment_made must be false")
    if payload.get("mandate_exceeded_without_escalation") is not False:
        errors.append("mandate_exceeded_without_escalation must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "decision_mode": mode,
        "in_mandate_candidate_count": len(in_mandate),
        "selected_candidate_id": decision.get("selected_candidate_id"),
    }

def validate_non_disruptive_exploration_allocation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Bound exploration by cost, expiry, evidence target, and protected commitment."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["non disruptive exploration allocation must be an object"]}
    for field in (
        "exploration_allocation_id",
        "exploration_candidate_id",
        "exploration_candidate_fingerprint",
        "allocation_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    budget = payload.get("cost_budget")
    if not isinstance(budget, dict):
        errors.append("cost_budget must be an object")
        budget = {}
    maximum_cost = budget.get("maximum_cost")
    allocated_cost = budget.get("allocated_cost")
    if not isinstance(maximum_cost, (int, float)) or isinstance(maximum_cost, bool) or maximum_cost <= 0:
        errors.append("cost_budget.maximum_cost must be positive")
        maximum_cost = 0
    if not isinstance(allocated_cost, (int, float)) or isinstance(allocated_cost, bool) or allocated_cost < 0:
        errors.append("cost_budget.allocated_cost must be non-negative")
        allocated_cost = 0
    if allocated_cost > maximum_cost:
        errors.append("cost_budget.allocated_cost must not exceed maximum_cost")
    for field in ("unit", "cost_owner_id", "budget_ledger_id"):
        if not _non_empty(budget.get(field)):
            errors.append(f"cost_budget.{field} must be a non-empty string")
    for field in ("starts_at", "expires_at", "expiration_action"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    evidence = payload.get("evidence_target")
    if not isinstance(evidence, dict):
        errors.append("evidence_target must be an object")
        evidence = {}
    for field in (
        "target_id",
        "uncertainty_id",
        "evidence_question",
        "qualifying_observation",
        "disqualifying_observation",
        "completion_criterion",
    ):
        if not _non_empty(evidence.get(field)):
            errors.append(f"evidence_target.{field} must be a non-empty string")
    protected = payload.get("protected_commitment")
    if not isinstance(protected, dict):
        errors.append("protected_commitment must be an object")
        protected = {}
    for field in (
        "mission_contract_id",
        "mission_contract_fingerprint",
        "commitment_owner_id",
        "protected_outcome",
    ):
        if not _non_empty(protected.get(field)):
            errors.append(f"protected_commitment.{field} must be a non-empty string")
    constraints = protected.get("non_disruption_constraints")
    if not isinstance(constraints, list) or not constraints:
        errors.append("protected_commitment.non_disruption_constraints must be non-empty")
        constraints = []
    constraint_ids = set()
    for index, constraint in enumerate(constraints):
        prefix = f"protected_commitment.non_disruption_constraints[{index}]"
        if not isinstance(constraint, dict):
            errors.append(f"{prefix} must be an object")
            continue
        constraint_id = constraint.get("constraint_id")
        if not _non_empty(constraint_id):
            errors.append(f"{prefix}.constraint_id must be a non-empty string")
        elif constraint_id in constraint_ids:
            errors.append(f"{prefix}.constraint_id must be unique")
        constraint_ids.add(constraint_id)
        for field in (
            "protected_resource_or_metric",
            "maximum_interference",
            "measurement_method",
            "stop_trigger",
        ):
            if not _non_empty(constraint.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if constraint.get("monitoring_active") is not True:
            errors.append(f"{prefix}.monitoring_active must be true")
    if protected.get("exploration_may_preempt_commitment") is not False:
        errors.append("protected_commitment.exploration_may_preempt_commitment must be false")
    if protected.get("shared_resource_unbounded") is not False:
        errors.append("protected_commitment.shared_resource_unbounded must be false")
    if payload.get("exploration_reversible") is not True:
        errors.append("exploration_reversible must be true")
    if not _non_empty(payload.get("exploration_stop_condition")):
        errors.append("exploration_stop_condition must be a non-empty string")
    if payload.get("automatic_renewal_allowed") is not False:
        errors.append("automatic_renewal_allowed must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "maximum_cost": maximum_cost,
        "allocated_cost": allocated_cost,
        "protected_constraint_count": len(constraint_ids),
        "protected_mission_contract_id": protected.get("mission_contract_id"),
    }

def validate_atomic_selection_authority_reversal_issue(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Complete selection only with atomic downstream authority and reversal triggers."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["atomic selection authority reversal issue must be an object"]}
    for field in (
        "issue_transaction_id",
        "issue_transaction_fingerprint",
        "selection_record_id",
        "selection_record_fingerprint",
        "winner_candidate_id",
        "winner_candidate_fingerprint",
        "issued_at",
        "issue_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    authority = payload.get("downstream_authority")
    if not isinstance(authority, dict):
        errors.append("downstream_authority must be an object")
        authority = {}
    for field in (
        "authority_grant_id",
        "grantee_id",
        "mission_contract_id",
        "mission_contract_fingerprint",
        "scope",
        "budget",
        "expires_at",
        "authority_return_trigger",
    ):
        if not _non_empty(authority.get(field)):
            errors.append(f"downstream_authority.{field} must be a non-empty string")
    for field in ("allowed_actions", "forbidden_actions"):
        values = authority.get(field)
        if (
            not isinstance(values, list)
            or not values
            or not all(_non_empty(item) for item in values)
            or len(values) != len(set(values))
        ):
            errors.append(f"downstream_authority.{field} must be a non-empty unique string list")
    if set(authority.get("allowed_actions", [])).intersection(authority.get("forbidden_actions", [])):
        errors.append("downstream authority allowed_actions and forbidden_actions must be disjoint")
    if authority.get("may_redefine_mission") is not False:
        errors.append("downstream_authority.may_redefine_mission must be false")
    if authority.get("may_expand_own_authority") is not False:
        errors.append("downstream_authority.may_expand_own_authority must be false")
    triggers = payload.get("reversal_triggers")
    if not isinstance(triggers, list) or not triggers:
        errors.append("reversal_triggers must be a non-empty list")
        triggers = []
    trigger_ids = set()
    for index, trigger in enumerate(triggers):
        prefix = f"reversal_triggers[{index}]"
        if not isinstance(trigger, dict):
            errors.append(f"{prefix} must be an object")
            continue
        trigger_id = trigger.get("trigger_id")
        if not _non_empty(trigger_id):
            errors.append(f"{prefix}.trigger_id must be a non-empty string")
        elif trigger_id in trigger_ids:
            errors.append(f"{prefix}.trigger_id must be unique")
        trigger_ids.add(trigger_id)
        for field in (
            "evidence_signal_id",
            "threshold",
            "measurement_method",
            "reversal_action",
            "rollback_authority_id",
            "wake_event_type",
            "review_owner_id",
        ):
            if not _non_empty(trigger.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if trigger.get("automatic_mission_rewrite") is not False:
            errors.append(f"{prefix}.automatic_mission_rewrite must be false")
    atomic = payload.get("atomic_issue")
    if not isinstance(atomic, dict):
        errors.append("atomic_issue must be an object")
        atomic = {}
    if atomic.get("winner_written") is not True:
        errors.append("atomic_issue.winner_written must be true")
    if atomic.get("authority_written") is not True:
        errors.append("atomic_issue.authority_written must be true")
    if atomic.get("reversal_triggers_written") is not True:
        errors.append("atomic_issue.reversal_triggers_written must be true")
    if atomic.get("partial_commit_allowed") is not False:
        errors.append("atomic_issue.partial_commit_allowed must be false")
    for field in ("commit_record_id", "commit_fingerprint"):
        if not _non_empty(atomic.get(field)):
            errors.append(f"atomic_issue.{field} must be a non-empty string")
    expected_complete = (
        atomic.get("winner_written") is True
        and atomic.get("authority_written") is True
        and atomic.get("reversal_triggers_written") is True
        and bool(trigger_ids)
        and _non_empty(authority.get("authority_grant_id"))
    )
    if payload.get("selection_status") != ("complete" if expected_complete else "incomplete"):
        errors.append("selection_status must reflect atomic winner, authority, and reversal issue")
    if payload.get("winner_executable_before_atomic_commit") is not False:
        errors.append("winner_executable_before_atomic_commit must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "selection_status": payload.get("selection_status"),
        "reversal_trigger_count": len(trigger_ids),
        "authority_grant_id": authority.get("authority_grant_id"),
    }

def validate_deterministic_model_tournament_implementation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Bound model criticism and selection with deterministic tournament gates."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["deterministic model tournament implementation must be an object"]}
    for field in (
        "tournament_implementation_id",
        "candidate_set_fingerprint",
        "constitution_fingerprint",
        "implementation_fingerprint",
        "implementation_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected_components = {
        "decision_structure": "validate_disqualification_dominance_decision_structure",
        "constitutional_gate": "validate_hard_constitutional_disqualification",
        "completeness_gate": "validate_structural_candidate_completeness_gate",
        "assumption_frontier": "validate_shared_assumption_dominance_frontier",
        "adversarial_sensitivity": "validate_adversarial_axis_sensitivity_review",
        "probe_branches": "validate_precommitted_assumption_probe_branches",
        "no_safe_probe": "validate_no_safe_probe_reversible_decision",
        "exploration_allocation": "validate_non_disruptive_exploration_allocation",
        "atomic_issue": "validate_atomic_selection_authority_reversal_issue",
    }
    components = payload.get("component_evidence")
    if not isinstance(components, list) or len(components) != len(expected_components):
        errors.append("component_evidence must contain exactly the nine tournament components")
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
        expected_validator = expected_components.get(name)
        if expected_validator is None:
            errors.append(f"{prefix}.component is not recognized")
        elif component.get("validator_id") != expected_validator:
            errors.append(f"{prefix}.validator_id must be {expected_validator}")
        for field in ("evidence_artifact_id", "evidence_fingerprint", "verification_record_id"):
            if not _non_empty(component.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if component.get("verified") is not True:
            errors.append(f"{prefix}.verified must be true")
    if observed_components != set(expected_components):
        errors.append("component_evidence must cover all tournament components exactly once")

    expected_stages = [
        ("structural_completeness", "deterministic"),
        ("constitutional_eligibility", "deterministic"),
        ("shared_assumption_dominance", "deterministic"),
        ("adversarial_criticism", "model"),
        ("semantic_selection", "model"),
        ("selection_constraint_check", "deterministic"),
        ("atomic_authority_reversal_issue", "deterministic"),
    ]
    stages = payload.get("stage_boundaries")
    if not isinstance(stages, list) or len(stages) != len(expected_stages):
        errors.append("stage_boundaries must contain exactly seven ordered stages")
        stages = []
    observed_stage_pairs = []
    for index, stage in enumerate(stages):
        prefix = f"stage_boundaries[{index}]"
        if not isinstance(stage, dict):
            errors.append(f"{prefix} must be an object")
            continue
        pair = (stage.get("stage"), stage.get("owner"))
        observed_stage_pairs.append(pair)
        for field in ("input_artifact_id", "output_artifact_id", "boundary_rule"):
            if not _non_empty(stage.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if stage.get("may_bypass_prior_gate") is not False:
            errors.append(f"{prefix}.may_bypass_prior_gate must be false")
    if observed_stage_pairs != expected_stages:
        errors.append("stage_boundaries must preserve deterministic gates around model judgment")

    frontier = payload.get("selection_frontier")
    if not isinstance(frontier, dict):
        errors.append("selection_frontier must be an object")
        frontier = {}
    for field in (
        "frontier_record_id",
        "frontier_fingerprint",
        "selected_candidate_id",
        "selected_candidate_fingerprint",
        "selection_rationale",
    ):
        if not _non_empty(frontier.get(field)):
            errors.append(f"selection_frontier.{field} must be a non-empty string")
    candidate_ids = frontier.get("eligible_non_dominated_candidate_ids")
    if (
        not isinstance(candidate_ids, list)
        or not candidate_ids
        or not all(_non_empty(item) for item in candidate_ids)
        or len(candidate_ids) != len(set(candidate_ids))
    ):
        errors.append("selection_frontier.eligible_non_dominated_candidate_ids must be a non-empty unique list")
        candidate_ids = []
    if frontier.get("selected_candidate_id") not in candidate_ids:
        errors.append("selection_frontier.selected_candidate_id must come from the eligible non-dominated frontier")
    tradeoffs = frontier.get("unresolved_tradeoffs")
    if not isinstance(tradeoffs, list) or not tradeoffs:
        errors.append("selection_frontier.unresolved_tradeoffs must be a non-empty list")
        tradeoffs = []
    tradeoff_ids = set()
    for index, tradeoff in enumerate(tradeoffs):
        prefix = f"selection_frontier.unresolved_tradeoffs[{index}]"
        if not isinstance(tradeoff, dict):
            errors.append(f"{prefix} must be an object")
            continue
        tradeoff_id = tradeoff.get("tradeoff_id")
        if not _non_empty(tradeoff_id):
            errors.append(f"{prefix}.tradeoff_id must be a non-empty string")
        elif tradeoff_id in tradeoff_ids:
            errors.append(f"{prefix}.tradeoff_id must be unique")
        tradeoff_ids.add(tradeoff_id)
        for field in (
            "value_a",
            "value_b",
            "tension",
            "evidence_fingerprint",
            "selection_effect",
            "revisit_trigger",
        ):
            if not _non_empty(tradeoff.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if tradeoff.get("resolved_by_aggregation") is not False:
            errors.append(f"{prefix}.resolved_by_aggregation must be false")

    invariants = payload.get("tournament_invariants")
    if not isinstance(invariants, dict):
        errors.append("tournament_invariants must be an object")
        invariants = {}
    for field in (
        "incomplete_candidates_excluded_before_model",
        "constitution_violators_excluded_before_model",
        "dominance_computed_only_on_shared_assumptions",
        "model_criticism_receives_only_frontier",
        "model_selection_checked_against_frontier",
        "unresolved_tradeoffs_preserved",
        "authority_and_reversal_issued_atomically",
    ):
        if invariants.get(field) is not True:
            errors.append(f"tournament_invariants.{field} must be true")
    for field in (
        "model_may_restore_disqualified_candidate",
        "model_may_invent_eligibility",
        "deterministic_code_semantically_scores_candidates",
        "scalar_aggregation_used",
        "unresolved_tradeoffs_erased",
    ):
        if invariants.get(field) is not False:
            errors.append(f"tournament_invariants.{field} must be false")
    if payload.get("tournament_status") != "integrated":
        errors.append("tournament_status must be integrated")
    return {
        "valid": not errors,
        "errors": errors,
        "component_count": len(observed_components),
        "stage_count": len(observed_stage_pairs),
        "frontier_candidate_count": len(candidate_ids),
        "unresolved_tradeoff_count": len(tradeoff_ids),
        "tournament_status": payload.get("tournament_status"),
    }

def validate_linked_planner_interface_compilation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Compile goal fields while retaining an immutable richer mission source."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["linked planner interface compilation must be an object"]}
    for field in (
        "compilation_id",
        "compiler_version",
        "compiled_at",
        "compilation_fingerprint",
        "compilation_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    source = payload.get("source_mission_contract")
    if not isinstance(source, dict):
        errors.append("source_mission_contract must be an object")
        source = {}
    for field in (
        "mission_contract_id",
        "mission_contract_version",
        "mission_contract_fingerprint",
        "immutable_address",
        "lineage_index_id",
    ):
        if not _non_empty(source.get(field)):
            errors.append(f"source_mission_contract.{field} must be a non-empty string")
    if source.get("retained_after_compilation") is not True:
        errors.append("source_mission_contract.retained_after_compilation must be true")
    if source.get("mutated_by_compilation") is not False:
        errors.append("source_mission_contract.mutated_by_compilation must be false")

    planner_input = payload.get("planner_input")
    if not isinstance(planner_input, dict):
        errors.append("planner_input must be an object")
        planner_input = {}
    for field in ("goal", "success_metric"):
        if not _non_empty(planner_input.get(field)):
            errors.append(f"planner_input.{field} must be a non-empty string")
    if planner_input.get("source_mission_contract_id") != source.get("mission_contract_id"):
        errors.append("planner_input.source_mission_contract_id must link the richer source contract")
    if planner_input.get("source_mission_contract_fingerprint") != source.get("mission_contract_fingerprint"):
        errors.append("planner_input.source_mission_contract_fingerprint must match the richer source contract")
    if planner_input.get("authoritative_source") != "source_mission_contract":
        errors.append("planner_input.authoritative_source must be source_mission_contract")

    lineage = payload.get("compiled_field_lineage")
    if not isinstance(lineage, list) or len(lineage) != 2:
        errors.append("compiled_field_lineage must contain exactly goal and success_metric")
        lineage = []
    observed_fields = set()
    lineage_ids = set()
    for index, entry in enumerate(lineage):
        prefix = f"compiled_field_lineage[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        lineage_id = entry.get("lineage_id")
        if not _non_empty(lineage_id):
            errors.append(f"{prefix}.lineage_id must be a non-empty string")
        elif lineage_id in lineage_ids:
            errors.append(f"{prefix}.lineage_id must be unique")
        lineage_ids.add(lineage_id)
        compiled_field = entry.get("compiled_field")
        if compiled_field not in {"goal", "success_metric"}:
            errors.append(f"{prefix}.compiled_field must be goal or success_metric")
        elif compiled_field in observed_fields:
            errors.append(f"{prefix}.compiled_field must be unique")
        observed_fields.add(compiled_field)
        for field in (
            "source_object_id",
            "source_field_pointer",
            "source_value_fingerprint",
            "transform_description",
        ):
            if not _non_empty(entry.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if entry.get("reconstructable") is not True:
            errors.append(f"{prefix}.reconstructable must be true")
    if observed_fields != {"goal", "success_metric"}:
        errors.append("compiled_field_lineage must cover goal and success_metric exactly once")

    loss = payload.get("loss_manifest")
    if not isinstance(loss, dict):
        errors.append("loss_manifest must be an object")
        loss = {}
    omitted = loss.get("omitted_source_fields")
    if (
        not isinstance(omitted, list)
        or not omitted
        or not all(_non_empty(item) for item in omitted)
        or len(omitted) != len(set(omitted))
    ):
        errors.append("loss_manifest.omitted_source_fields must be a non-empty unique string list")
        omitted = []
    if loss.get("omissions_explicit") is not True:
        errors.append("loss_manifest.omissions_explicit must be true")
    if loss.get("omitted_fields_retrievable_from_source") is not True:
        errors.append("loss_manifest.omitted_fields_retrievable_from_source must be true")
    if loss.get("compilation_declared_lossless") is not False:
        errors.append("loss_manifest.compilation_declared_lossless must be false")
    if payload.get("compiled_input_replaces_source_contract") is not False:
        errors.append("compiled_input_replaces_source_contract must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "compiled_fields": sorted(item for item in observed_fields if _non_empty(item)),
        "omitted_source_field_count": len(omitted),
        "source_mission_contract_id": source.get("mission_contract_id"),
    }

def validate_mission_semantic_planner_field_mapping(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Map mission semantics into planner fields without inventing execution form."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["mission semantic planner field mapping must be an object"]}
    for field in (
        "mapping_id",
        "compilation_id",
        "source_mission_contract_id",
        "source_mission_contract_fingerprint",
        "mapping_fingerprint",
        "mapping_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    source = payload.get("source_semantics")
    if not isinstance(source, dict):
        errors.append("source_semantics must be an object")
        source = {}
    outcome = source.get("mission_outcome")
    if not isinstance(outcome, dict):
        errors.append("source_semantics.mission_outcome must be an object")
        outcome = {}
    for field in ("source_field_pointer", "value", "value_fingerprint"):
        if not _non_empty(outcome.get(field)):
            errors.append(f"source_semantics.mission_outcome.{field} must be a non-empty string")
    causal = source.get("causal_thesis")
    if not isinstance(causal, dict):
        errors.append("source_semantics.causal_thesis must be an object")
        causal = {}
    for field in ("source_field_pointer", "statement", "value_fingerprint"):
        if not _non_empty(causal.get(field)):
            errors.append(f"source_semantics.causal_thesis.{field} must be a non-empty string")

    def collect_sources(field: str, item_id_field: str) -> Dict[str, Dict[str, Any]]:
        items = source.get(field)
        if not isinstance(items, list) or not items:
            errors.append(f"source_semantics.{field} must be a non-empty list")
            items = []
        collected: Dict[str, Dict[str, Any]] = {}
        for index, item in enumerate(items):
            prefix = f"source_semantics.{field}[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue
            item_id = item.get(item_id_field)
            if not _non_empty(item_id):
                errors.append(f"{prefix}.{item_id_field} must be a non-empty string")
            elif item_id in collected:
                errors.append(f"{prefix}.{item_id_field} must be unique")
            else:
                collected[item_id] = item
            for required in ("source_field_pointer", "value", "value_fingerprint"):
                if not _non_empty(item.get(required)):
                    errors.append(f"{prefix}.{required} must be a non-empty string")
        return collected

    success_sources = collect_sources("success_signals", "signal_id")
    harm_sources = collect_sources("harm_signals", "signal_id")
    non_goal_sources = collect_sources("non_goals", "non_goal_id")

    planner = payload.get("planner_fields")
    if not isinstance(planner, dict):
        errors.append("planner_fields must be an object")
        planner = {}
    goal = planner.get("goal")
    if not isinstance(goal, dict):
        errors.append("planner_fields.goal must be an object")
        goal = {}
    for field in ("text", "source_field_pointer", "source_value_fingerprint"):
        if not _non_empty(goal.get(field)):
            errors.append(f"planner_fields.goal.{field} must be a non-empty string")
    if goal.get("text") != outcome.get("value"):
        errors.append("planner_fields.goal.text must preserve the mission outcome")
    if goal.get("source_field_pointer") != outcome.get("source_field_pointer"):
        errors.append("planner_fields.goal.source_field_pointer must reference mission_outcome")
    if goal.get("source_value_fingerprint") != outcome.get("value_fingerprint"):
        errors.append("planner_fields.goal.source_value_fingerprint must match mission_outcome")

    def validate_mapped_items(
        planner_field: str,
        source_items: Dict[str, Dict[str, Any]],
        source_id_field: str,
        kind: str,
    ) -> set:
        items = planner.get(planner_field)
        if not isinstance(items, list) or len(items) != len(source_items):
            errors.append(f"planner_fields.{planner_field} must exactly cover source {planner_field}")
            items = []
        observed = set()
        compiled_ids = set()
        for index, item in enumerate(items):
            prefix = f"planner_fields.{planner_field}[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{prefix} must be an object")
                continue
            compiled_id = item.get("compiled_field_id")
            if not _non_empty(compiled_id):
                errors.append(f"{prefix}.compiled_field_id must be a non-empty string")
            elif compiled_id in compiled_ids:
                errors.append(f"{prefix}.compiled_field_id must be unique")
            compiled_ids.add(compiled_id)
            source_id = item.get(source_id_field)
            source_item = source_items.get(source_id)
            if source_item is None:
                errors.append(f"{prefix}.{source_id_field} must reference a known source")
            elif source_id in observed:
                errors.append(f"{prefix}.{source_id_field} must be unique")
            observed.add(source_id)
            for field in ("text", "source_field_pointer", "source_value_fingerprint"):
                if not _non_empty(item.get(field)):
                    errors.append(f"{prefix}.{field} must be a non-empty string")
            if source_item:
                if item.get("text") != source_item.get("value"):
                    errors.append(f"{prefix}.text must preserve its source value")
                if item.get("source_field_pointer") != source_item.get("source_field_pointer"):
                    errors.append(f"{prefix}.source_field_pointer must match its source")
                if item.get("source_value_fingerprint") != source_item.get("value_fingerprint"):
                    errors.append(f"{prefix}.source_value_fingerprint must match its source")
            if item.get("semantic_kind") != kind:
                errors.append(f"{prefix}.semantic_kind must be {kind}")
        if observed != set(source_items):
            errors.append(f"planner_fields.{planner_field} must cover every source exactly once")
        return compiled_ids

    success_ids = validate_mapped_items("success_metrics", success_sources, "source_signal_id", "success_metric")
    harm_ids = validate_mapped_items("harm_metrics", harm_sources, "source_signal_id", "harm_metric")
    constraint_ids = validate_mapped_items("constraints", {"causal_thesis": {
        "value": causal.get("statement"),
        "source_field_pointer": causal.get("source_field_pointer"),
        "value_fingerprint": causal.get("value_fingerprint"),
    }}, "source_causal_thesis_id", "causal_constraint")
    exclusion_ids = validate_mapped_items("explicit_exclusions", non_goal_sources, "source_non_goal_id", "non_goal_exclusion")

    if planner.get("tasks") != []:
        errors.append("planner_fields.tasks must be empty")
    if planner.get("implementation_sequence") != []:
        errors.append("planner_fields.implementation_sequence must be empty")
    if payload.get("source_semantics_fully_covered") is not True:
        errors.append("source_semantics_fully_covered must be true")
    if payload.get("unmapped_source_semantics") != []:
        errors.append("unmapped_source_semantics must be empty")
    if payload.get("execution_form_generated") is not False:
        errors.append("execution_form_generated must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "success_metric_count": len(success_ids),
        "harm_metric_count": len(harm_ids),
        "constraint_count": len(constraint_ids),
        "explicit_exclusion_count": len(exclusion_ids),
    }

