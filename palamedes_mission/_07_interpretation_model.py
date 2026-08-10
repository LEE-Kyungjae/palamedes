from __future__ import annotations

from typing import Any, Dict, List
from ._01_kinds_value import _non_empty


def validate_prohibition_precedence_graph(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve hard-prohibition conflicts by graph evidence or leave them unresolved."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["prohibition precedence graph must be an object"]}
    for field in ("precedence_graph_id", "constitution_version_id", "unresolved_conflict_action"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("declaration_order_breaks_ties") is not False:
        errors.append("declaration_order_breaks_ties must be false")
    prohibition_ids = payload.get("prohibition_ids")
    if (
        not isinstance(prohibition_ids, list)
        or len(prohibition_ids) < 2
        or not all(_non_empty(item) for item in prohibition_ids)
        or len(prohibition_ids) != len(set(prohibition_ids))
    ):
        errors.append("prohibition_ids must contain at least two unique ids")
        prohibition_ids = []

    edges = payload.get("precedence_edges")
    if not isinstance(edges, list):
        errors.append("precedence_edges must be a list")
        edges = []
    edge_pairs = set()
    adjacency = {item: set() for item in prohibition_ids}
    for index, edge in enumerate(edges):
        prefix = f"precedence_edges[{index}]"
        if not isinstance(edge, dict):
            errors.append(f"{prefix} must be an object")
            continue
        higher = edge.get("higher_prohibition_id")
        lower = edge.get("lower_prohibition_id")
        if higher not in adjacency or lower not in adjacency or higher == lower:
            errors.append(f"{prefix} must reference two distinct declared prohibitions")
            continue
        pair = (higher, lower)
        if pair in edge_pairs:
            errors.append(f"{prefix} must be unique")
        edge_pairs.add(pair)
        adjacency[higher].add(lower)
        if not _non_empty(edge.get("precedence_rationale")):
            errors.append(f"{prefix}.precedence_rationale must be a non-empty string")

    visiting = set()
    visited = set()

    def has_cycle(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(has_cycle(child) for child in adjacency.get(node, ())):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    if any(has_cycle(node) for node in prohibition_ids if node not in visited):
        errors.append("precedence_edges must form an acyclic graph")

    conflicts = payload.get("conflicts")
    if not isinstance(conflicts, list) or not conflicts:
        errors.append("conflicts must be a non-empty list")
        conflicts = []
    conflict_ids = set()
    unresolved_count = 0
    for index, conflict in enumerate(conflicts):
        prefix = f"conflicts[{index}]"
        if not isinstance(conflict, dict):
            errors.append(f"{prefix} must be an object")
            continue
        conflict_id = conflict.get("conflict_id")
        if not _non_empty(conflict_id):
            errors.append(f"{prefix}.conflict_id must be a non-empty string")
        elif conflict_id in conflict_ids:
            errors.append(f"{prefix}.conflict_id must be unique")
        conflict_ids.add(conflict_id)
        left = conflict.get("left_prohibition_id")
        right = conflict.get("right_prohibition_id")
        if left not in adjacency or right not in adjacency or left == right:
            errors.append(f"{prefix} must reference two distinct declared prohibitions")
            continue
        resolution = conflict.get("resolution")
        if resolution == "unresolved":
            unresolved_count += 1
            if conflict.get("selected_prohibition_id") not in ("", None):
                errors.append(f"{prefix}.selected_prohibition_id must be empty when unresolved")
        elif resolution == "precedence":
            selected = conflict.get("selected_prohibition_id")
            other = right if selected == left else left if selected == right else None
            if other is None or (selected, other) not in edge_pairs:
                errors.append(f"{prefix} precedence resolution must follow an explicit graph edge")
        else:
            errors.append(f"{prefix}.resolution must be precedence or unresolved")
        if not _non_empty(conflict.get("conflict_rationale")):
            errors.append(f"{prefix}.conflict_rationale must be a non-empty string")

    return {
        "valid": not errors,
        "errors": errors,
        "unresolved_conflict_count": unresolved_count,
    }

def validate_defeasible_principle_override(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require evidence and a falsifiable consequence for a principle override."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["defeasible principle override must be an object"]}
    for field in (
        "override_id",
        "principle_id",
        "mission_id",
        "requested_by",
        "default_principle_action",
        "proposed_exception",
        "override_reason",
        "affected_beneficiaries",
        "predicted_consequence_with_override",
        "predicted_consequence_without_override",
        "prediction_window",
        "falsification_signal",
        "expiry_at",
        "review_owner",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("preferred_mission_is_sufficient_reason") is not False:
        errors.append("preferred_mission_is_sufficient_reason must be false")
    evidence_ids = payload.get("evidence_ids")
    if (
        not isinstance(evidence_ids, list)
        or not evidence_ids
        or not all(_non_empty(item) for item in evidence_ids)
        or len(evidence_ids) != len(set(evidence_ids))
    ):
        errors.append("evidence_ids must be a non-empty unique list")
    if payload.get("decision") not in {"approve_bounded", "reject", "defer"}:
        errors.append("decision must be approve_bounded, reject, or defer")
    if payload.get("decision") == "approve_bounded":
        if not _non_empty(payload.get("approved_scope")):
            errors.append("approved_scope must be a non-empty string for approve_bounded")
        if payload.get("override_is_permanent") is not False:
            errors.append("override_is_permanent must be false for approve_bounded")
    return {
        "valid": not errors,
        "errors": errors,
        "decision": payload.get("decision"),
    }

def validate_learned_preference_decay(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Reduce stale preference weight while preserving its complete lineage."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["learned preference decay must be an object"]}
    for field in (
        "preference_decay_id",
        "preference_id",
        "preference_statement",
        "learned_environment_id",
        "current_environment_id",
        "learned_owner_identity_id",
        "current_owner_identity_id",
        "change_evidence_id",
        "decay_rationale",
        "review_trigger",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    environment_changed = payload.get("environment_changed")
    owner_changed = payload.get("owner_identity_changed")
    if not isinstance(environment_changed, bool):
        errors.append("environment_changed must be boolean")
    if not isinstance(owner_changed, bool):
        errors.append("owner_identity_changed must be boolean")
    if environment_changed is not True and owner_changed is not True:
        errors.append("decay requires an environment or owner identity change")
    numeric = {}
    for field in ("original_weight", "decay_factor", "operational_weight"):
        value = payload.get(field)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not 0 <= value <= 1
        ):
            errors.append(f"{field} must be a number between 0 and 1")
            value = 0
        numeric[field] = value
    expected_weight = numeric["original_weight"] * numeric["decay_factor"]
    if abs(numeric["operational_weight"] - expected_weight) > 1e-9:
        errors.append("operational_weight must equal original_weight multiplied by decay_factor")
    if numeric["decay_factor"] >= 1:
        errors.append("decay_factor must reduce operational weight")
    if payload.get("lineage_deleted") is not False:
        errors.append("lineage_deleted must be false")
    lineage = payload.get("lineage_records")
    if (
        not isinstance(lineage, list)
        or not lineage
        or not all(_non_empty(item) for item in lineage)
    ):
        errors.append("lineage_records must be a non-empty list")
    if payload.get("status") != "decayed":
        errors.append("status must be decayed")
    return {
        "valid": not errors,
        "errors": errors,
        "operational_weight": numeric["operational_weight"],
        "lineage_record_count": len(lineage) if isinstance(lineage, list) else 0,
    }

def validate_bounded_precedent_record(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Keep precedent scoped, contestable, and invalidatable by environment change."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["bounded precedent record must be an object"]}
    for field in (
        "precedent_record_id",
        "origin_decision_id",
        "origin_environment_id",
        "current_environment_id",
        "decision_summary",
        "observed_outcome",
        "scope",
        "review_trigger",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("precedent_is_universally_binding") is not False:
        errors.append("precedent_is_universally_binding must be false")
    for field in (
        "analogical_features",
        "material_differences",
        "dissent_records",
        "invalidating_environmental_changes",
    ):
        items = payload.get(field)
        if (
            not isinstance(items, list)
            or not items
            or not all(_non_empty(item) for item in items)
        ):
            errors.append(f"{field} must be a non-empty list")
    detected = payload.get("detected_environmental_changes")
    if not isinstance(detected, list) or not all(_non_empty(item) for item in detected):
        errors.append("detected_environmental_changes must be a list")
        detected = []
    invalidators = payload.get("invalidating_environmental_changes")
    invalidators = invalidators if isinstance(invalidators, list) else []
    invalidating_change_detected = bool(set(detected).intersection(invalidators))
    status = payload.get("status")
    if status not in {"applicable", "suspended", "invalidated"}:
        errors.append("status must be applicable, suspended, or invalidated")
    elif invalidating_change_detected and status == "applicable":
        errors.append("status cannot remain applicable after an invalidating environmental change")
    if status == "applicable" and not _non_empty(payload.get("analogy_rationale")):
        errors.append("analogy_rationale must be a non-empty string when applicable")
    return {
        "valid": not errors,
        "errors": errors,
        "status": status,
        "invalidating_change_detected": invalidating_change_detected,
    }

def validate_consequence_bounded_authority_grant(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Bound delegated authority by consequences, resources, time, and representation."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["consequence-bounded authority grant must be an object"]}
    for field in (
        "authority_grant_id",
        "grantor_id",
        "grantee_id",
        "valid_from",
        "valid_until",
        "revocation_trigger",
        "audit_owner",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("tool_names_define_scope") is not False:
        errors.append("tool_names_define_scope must be false")
    allowed_classes = payload.get("allowed_consequence_classes")
    if (
        not isinstance(allowed_classes, list)
        or not allowed_classes
        or not all(_non_empty(item) for item in allowed_classes)
        or len(allowed_classes) != len(set(allowed_classes))
    ):
        errors.append("allowed_consequence_classes must be a non-empty unique list")
    prohibited_classes = payload.get("prohibited_consequence_classes")
    if (
        not isinstance(prohibited_classes, list)
        or not prohibited_classes
        or not all(_non_empty(item) for item in prohibited_classes)
        or len(prohibited_classes) != len(set(prohibited_classes))
    ):
        errors.append("prohibited_consequence_classes must be a non-empty unique list")
    if isinstance(allowed_classes, list) and isinstance(prohibited_classes, list):
        if set(allowed_classes).intersection(prohibited_classes):
            errors.append("allowed and prohibited consequence classes must not overlap")
    ceilings = payload.get("resource_ceilings")
    required_resources = {"compute_units", "currency_units", "elapsed_hours"}
    if not isinstance(ceilings, dict) or set(ceilings) != required_resources:
        errors.append("resource_ceilings must define compute_units, currency_units, and elapsed_hours")
    else:
        for resource, value in ceilings.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
                errors.append(f"resource_ceilings.{resource} must be greater than zero")
    rights = payload.get("representation_rights")
    if not isinstance(rights, list) or not rights:
        errors.append("representation_rights must be a non-empty list")
        rights = []
    groups = set()
    for index, right in enumerate(rights):
        prefix = f"representation_rights[{index}]"
        if not isinstance(right, dict):
            errors.append(f"{prefix} must be an object")
            continue
        group = right.get("represented_group")
        if not _non_empty(group):
            errors.append(f"{prefix}.represented_group must be a non-empty string")
        elif group in groups:
            errors.append(f"{prefix}.represented_group must be unique")
        groups.add(group)
        for field in ("representation_mode", "consent_basis", "challenge_channel"):
            if not _non_empty(right.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if not isinstance(right.get("may_make_binding_commitment"), bool):
            errors.append(f"{prefix}.may_make_binding_commitment must be boolean")
    return {
        "valid": not errors,
        "errors": errors,
        "represented_groups": sorted(groups),
    }

def validate_constitution_interpretation_trace(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Trace mission features through clauses, conflicts, overrides, and uncertainty."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["constitution interpretation trace must be an object"]}
    for field in (
        "interpretation_trace_id",
        "mission_id",
        "mission_version_id",
        "constitution_version_id",
        "interpretation_conclusion",
        "review_trigger",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")

    features = payload.get("mission_features")
    if not isinstance(features, list) or not features:
        errors.append("mission_features must be a non-empty list")
        features = []
    feature_ids = set()
    for index, feature in enumerate(features):
        prefix = f"mission_features[{index}]"
        if not isinstance(feature, dict):
            errors.append(f"{prefix} must be an object")
            continue
        feature_id = feature.get("feature_id")
        if not _non_empty(feature_id):
            errors.append(f"{prefix}.feature_id must be a non-empty string")
        elif feature_id in feature_ids:
            errors.append(f"{prefix}.feature_id must be unique")
        feature_ids.add(feature_id)
        for field in ("dimension", "value"):
            if not _non_empty(feature.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")

    applications = payload.get("clause_applications")
    if not isinstance(applications, list) or not applications:
        errors.append("clause_applications must be a non-empty list")
        applications = []
    clause_ids = set()
    covered_features = set()
    for index, application in enumerate(applications):
        prefix = f"clause_applications[{index}]"
        if not isinstance(application, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if application.get("feature_id") not in feature_ids:
            errors.append(f"{prefix}.feature_id must reference a declared mission feature")
        else:
            covered_features.add(application.get("feature_id"))
        clause_id = application.get("clause_id")
        if not _non_empty(clause_id):
            errors.append(f"{prefix}.clause_id must be a non-empty string")
        else:
            clause_ids.add(clause_id)
        for field in ("layer_type", "interpretation", "decision_effect"):
            if not _non_empty(application.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if covered_features != feature_ids:
        errors.append("every mission feature must link to at least one clause application")

    for field, required_fields in (
        ("conflicts", ("conflict_id", "left_clause_id", "right_clause_id", "resolution_record_id")),
        ("overrides", ("override_id", "clause_id", "evidence_id", "predicted_consequence_id")),
        ("uncertainties", ("uncertainty_id", "clause_id", "uncertainty_statement", "decision_effect")),
    ):
        records = payload.get(field)
        if not isinstance(records, list) or not records:
            errors.append(f"{field} must be a non-empty list")
            continue
        record_ids = set()
        for index, record in enumerate(records):
            prefix = f"{field}[{index}]"
            if not isinstance(record, dict):
                errors.append(f"{prefix} must be an object")
                continue
            identifier = record.get(required_fields[0])
            if not _non_empty(identifier):
                errors.append(f"{prefix}.{required_fields[0]} must be a non-empty string")
            elif identifier in record_ids:
                errors.append(f"{prefix}.{required_fields[0]} must be unique")
            record_ids.add(identifier)
            for required in required_fields[1:]:
                if not _non_empty(record.get(required)):
                    errors.append(f"{prefix}.{required} must be a non-empty string")
            for reference in ("left_clause_id", "right_clause_id", "clause_id"):
                if reference in record and record.get(reference) not in clause_ids:
                    errors.append(f"{prefix}.{reference} must reference an applied clause")
    if payload.get("decision_status") not in {"allowed", "blocked", "contested"}:
        errors.append("decision_status must be allowed, blocked, or contested")

    return {
        "valid": not errors,
        "errors": errors,
        "covered_feature_count": len(covered_features),
        "applied_clause_count": len(clause_ids),
    }

def validate_interpretation_trace_audit(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Audit traces for convenient interpretation and recurring blind spots."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["interpretation trace audit must be an object"]}
    for field in (
        "trace_audit_id",
        "constitution_version_id",
        "independent_reviewer_id",
        "audit_window",
        "correction_trigger",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("interpretation_trace_is_alignment_proof") is not False:
        errors.append("interpretation_trace_is_alignment_proof must be false")
    trace_ids = payload.get("interpretation_trace_ids")
    if (
        not isinstance(trace_ids, list)
        or len(trace_ids) < 2
        or not all(_non_empty(item) for item in trace_ids)
        or len(trace_ids) != len(set(trace_ids))
    ):
        errors.append("interpretation_trace_ids must contain at least two unique traces")
        trace_ids = []
    outcome_ids = payload.get("outcome_evidence_ids")
    if (
        not isinstance(outcome_ids, list)
        or not outcome_ids
        or not all(_non_empty(item) for item in outcome_ids)
    ):
        errors.append("outcome_evidence_ids must be a non-empty list")

    findings = payload.get("findings")
    if not isinstance(findings, list) or not findings:
        errors.append("findings must be a non-empty list")
        findings = []
    finding_ids = set()
    finding_types = set()
    for index, finding in enumerate(findings):
        prefix = f"findings[{index}]"
        if not isinstance(finding, dict):
            errors.append(f"{prefix} must be an object")
            continue
        finding_id = finding.get("finding_id")
        if not _non_empty(finding_id):
            errors.append(f"{prefix}.finding_id must be a non-empty string")
        elif finding_id in finding_ids:
            errors.append(f"{prefix}.finding_id must be unique")
        finding_ids.add(finding_id)
        finding_type = finding.get("finding_type")
        if finding_type not in {"convenient_interpretation", "systematic_blind_spot"}:
            errors.append(f"{prefix}.finding_type is not recognized")
        else:
            finding_types.add(finding_type)
        supporting = finding.get("supporting_trace_ids")
        if (
            not isinstance(supporting, list)
            or not supporting
            or any(item not in trace_ids for item in supporting)
        ):
            errors.append(f"{prefix}.supporting_trace_ids must reference audited traces")
        elif finding_type == "systematic_blind_spot" and len(set(supporting)) < 2:
            errors.append(f"{prefix} systematic blind spot must recur across at least two traces")
        for field in ("observed_pattern", "counterevidence", "required_correction"):
            if not _non_empty(finding.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if finding_types != {"convenient_interpretation", "systematic_blind_spot"}:
        errors.append("findings must assess both convenient interpretation and systematic blind spots")
    if payload.get("audit_conclusion") not in {
        "no_alignment_claim",
        "correction_required",
        "further_evidence_required",
    }:
        errors.append("audit_conclusion is not recognized")
    return {
        "valid": not errors,
        "errors": errors,
        "finding_types": sorted(finding_types),
    }

def validate_constitution_thesis_integration(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Integrate layered, conflict-aware, contestable, outcome-linked governance."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["constitution thesis integration must be an object"]}
    for field in (
        "constitution_thesis_id",
        "constitution_version_id",
        "layer_registry_id",
        "contextual_rule_id",
        "precedence_graph_id",
        "principle_override_id",
        "preference_decay_id",
        "precedent_record_id",
        "authority_grant_id",
        "interpretation_trace_id",
        "trace_audit_id",
        "outcome_record_id",
        "contestation_channel",
        "revision_trigger",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    for field in (
        "layered_state_present",
        "conflict_awareness_present",
        "versioned_state_present",
        "application_is_contestable",
        "application_is_outcome_linked",
    ):
        if payload.get(field) is not True:
            errors.append(f"{field} must be true")
    if payload.get("interpretation_trace_is_alignment_proof") is not False:
        errors.append("interpretation_trace_is_alignment_proof must be false")
    outcome_links = payload.get("outcome_links")
    if not isinstance(outcome_links, list) or not outcome_links:
        errors.append("outcome_links must be a non-empty list")
        outcome_links = []
    required_link_types = {"clause_application", "override_prediction", "authority_consequence"}
    represented_links = set()
    for index, link in enumerate(outcome_links):
        prefix = f"outcome_links[{index}]"
        if not isinstance(link, dict):
            errors.append(f"{prefix} must be an object")
            continue
        link_type = link.get("link_type")
        if link_type not in required_link_types:
            errors.append(f"{prefix}.link_type is not recognized")
        else:
            represented_links.add(link_type)
        for field in ("governance_record_id", "outcome_evidence_id", "observed_relation"):
            if not _non_empty(link.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if represented_links != required_link_types:
        errors.append("outcome_links must connect clause application, override prediction, and authority consequence")
    if payload.get("conclusion") != "constitution_thesis_supported":
        errors.append("conclusion must be constitution_thesis_supported")
    return {
        "valid": not errors,
        "errors": errors,
        "outcome_link_types": sorted(represented_links),
    }

def validate_plural_world_model_set(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Preserve multiple distinguishable world models around one signal."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["plural world model set must be an object"]}
    for field in (
        "world_model_set_id",
        "signal_claim_id",
        "affected_condition",
        "model_comparison_question",
        "next_discriminating_observation",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("monolithic_model_is_authoritative") is not False:
        errors.append("monolithic_model_is_authoritative must be false")
    models = payload.get("models")
    if not isinstance(models, list) or len(models) < 2:
        errors.append("models must contain at least two competing world models")
        models = []
    model_ids = set()
    causal_claims = set()
    predictions = set()
    for index, model in enumerate(models):
        prefix = f"models[{index}]"
        if not isinstance(model, dict):
            errors.append(f"{prefix} must be an object")
            continue
        model_id = model.get("model_id")
        if not _non_empty(model_id):
            errors.append(f"{prefix}.model_id must be a non-empty string")
        elif model_id in model_ids:
            errors.append(f"{prefix}.model_id must be unique")
        model_ids.add(model_id)
        for field in (
            "causal_claim",
            "prediction",
            "mission_implication",
            "uncertainty_rationale",
        ):
            if not _non_empty(model.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        causal_claims.add(model.get("causal_claim"))
        predictions.add(model.get("prediction"))
        for field in ("supporting_evidence_ids", "opposing_evidence_ids"):
            items = model.get(field)
            if (
                not isinstance(items, list)
                or not items
                or not all(_non_empty(item) for item in items)
            ):
                errors.append(f"{prefix}.{field} must be a non-empty list")
        uncertainty = model.get("uncertainty")
        if (
            isinstance(uncertainty, bool)
            or not isinstance(uncertainty, (int, float))
            or not 0 <= uncertainty <= 1
        ):
            errors.append(f"{prefix}.uncertainty must be a number between 0 and 1")
    if len(causal_claims) != len(models):
        errors.append("each world model must state a distinct causal claim")
    if len(predictions) != len(models):
        errors.append("each world model must make a distinguishable prediction")
    disagreements = payload.get("unresolved_disagreements")
    if (
        not isinstance(disagreements, list)
        or not disagreements
        or not all(_non_empty(item) for item in disagreements)
    ):
        errors.append("unresolved_disagreements must be a non-empty list")
    if payload.get("status") != "plural_unresolved":
        errors.append("status must be plural_unresolved")
    return {
        "valid": not errors,
        "errors": errors,
        "model_count": len(models),
        "status": payload.get("status"),
    }

def validate_competing_causal_sketch_set(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Keep competing causal accounts bounded around the affected condition."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["competing causal sketch set must be an object"]}
    for field in (
        "causal_sketch_set_id",
        "world_model_set_id",
        "affected_condition",
        "shared_scope_boundary",
        "comparison_decision",
        "next_discriminator",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("exhaustive_world_simulation") is not False:
        errors.append("exhaustive_world_simulation must be false")
    sketches = payload.get("sketches")
    if not isinstance(sketches, list) or len(sketches) < 2:
        errors.append("sketches must contain at least two causal sketches")
        sketches = []
    sketch_ids = set()
    model_ids = set()
    paths = set()
    for index, sketch in enumerate(sketches):
        prefix = f"sketches[{index}]"
        if not isinstance(sketch, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field, seen in (("sketch_id", sketch_ids), ("model_id", model_ids)):
            value = sketch.get(field)
            if not _non_empty(value):
                errors.append(f"{prefix}.{field} must be a non-empty string")
            elif value in seen:
                errors.append(f"{prefix}.{field} must be unique")
            seen.add(value)
        for field in (
            "local_boundary",
            "causal_path",
            "prediction",
            "discriminating_observation",
        ):
            if not _non_empty(sketch.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        paths.add(sketch.get("causal_path"))
        for field in ("included_factors", "deliberately_excluded_factors"):
            items = sketch.get(field)
            if (
                not isinstance(items, list)
                or not items
                or not all(_non_empty(item) for item in items)
            ):
                errors.append(f"{prefix}.{field} must be a non-empty list")
    if len(paths) != len(sketches):
        errors.append("each causal sketch must preserve a distinct causal path")
    return {
        "valid": not errors,
        "errors": errors,
        "sketch_count": len(sketches),
    }

def validate_decision_relevant_causal_complexity(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Admit causal detail only when it can alter a decision branch."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["decision-relevant causal complexity must be an object"]}
    for field in (
        "complexity_review_id",
        "causal_sketch_id",
        "target_decision",
        "pruning_rule",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("decorative_complexity_allowed") is not False:
        errors.append("decorative_complexity_allowed must be false")
    budget = payload.get("component_budget")
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < 5:
        errors.append("component_budget must be an integer of at least five")
        budget = 0
    components = payload.get("components")
    if not isinstance(components, list) or not components:
        errors.append("components must be a non-empty list")
        components = []
    if len(components) > budget:
        errors.append("components must not exceed component_budget")
    required_types = {"actor", "incentive", "constraint", "mechanism", "feedback_loop"}
    represented_types = set()
    component_ids = set()
    for index, component in enumerate(components):
        prefix = f"components[{index}]"
        if not isinstance(component, dict):
            errors.append(f"{prefix} must be an object")
            continue
        component_id = component.get("component_id")
        if not _non_empty(component_id):
            errors.append(f"{prefix}.component_id must be a non-empty string")
        elif component_id in component_ids:
            errors.append(f"{prefix}.component_id must be unique")
        component_ids.add(component_id)
        component_type = component.get("component_type")
        if component_type not in required_types:
            errors.append(f"{prefix}.component_type is not recognized")
        else:
            represented_types.add(component_type)
        for field in (
            "description",
            "decision_relevance",
            "changed_decision_branch",
            "evidence_id",
            "removal_consequence",
        ):
            if not _non_empty(component.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if component.get("removal_leaves_decision_unchanged") is not False:
            errors.append(f"{prefix}.removal_leaves_decision_unchanged must be false")
    if represented_types != required_types:
        errors.append("components must include actor, incentive, constraint, mechanism, and feedback_loop")
    return {
        "valid": not errors,
        "errors": errors,
        "represented_component_types": sorted(represented_types),
        "component_count": len(components),
    }

def validate_correlational_mission_authority(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Lower mission authority and prefer an intervention under correlation."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["correlational mission authority must be an object"]}
    for field in (
        "authority_review_id",
        "signal_claim_id",
        "correlation_claim",
        "suggested_mission",
        "probe_id",
        "probe_manipulation",
        "probe_outcome",
        "probe_window",
        "decision_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("evidence_status") != "correlational":
        errors.append("evidence_status must be correlational")
    if payload.get("mission_authority") != "hypothesis_only":
        errors.append("mission_authority must be hypothesis_only under correlational evidence")
    if payload.get("correlation_can_authorize_mission_commitment") is not False:
        errors.append("correlation_can_authorize_mission_commitment must be false")
    mechanisms = payload.get("competing_mechanism_ids")
    if (
        not isinstance(mechanisms, list)
        or len(mechanisms) < 2
        or not all(_non_empty(item) for item in mechanisms)
        or len(mechanisms) != len(set(mechanisms))
    ):
        errors.append("competing_mechanism_ids must contain at least two unique mechanisms")
        mechanisms = []
    distinguished = payload.get("probe_distinguishes_mechanism_ids")
    if (
        not isinstance(distinguished, list)
        or set(distinguished) != set(mechanisms)
        or len(distinguished) != len(mechanisms)
    ):
        errors.append("probe_distinguishes_mechanism_ids must cover every competing mechanism")
    if payload.get("probe_preferred") is not True:
        errors.append("probe_preferred must be true")
    if payload.get("decision") != "run_probe":
        errors.append("decision must be run_probe")
    return {
        "valid": not errors,
        "errors": errors,
        "mission_authority": payload.get("mission_authority"),
        "decision": payload.get("decision"),
    }

def validate_historical_mechanism_analogy(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Transfer a historical mechanism candidate without importing its forecast."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["historical mechanism analogy must be an object"]}
    for field in (
        "historical_analogy_id",
        "historical_case_id",
        "current_case_id",
        "historical_outcome",
        "candidate_mechanism",
        "mechanism_transfer_rationale",
        "local_probe_id",
        "local_probe_prediction",
        "local_failure_signal",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("historical_analogy_is_forecast") is not False:
        errors.append("historical_analogy_is_forecast must be false")
    if payload.get("transfer_authority") != "mechanism_candidate_only":
        errors.append("transfer_authority must be mechanism_candidate_only")
    differences = payload.get("context_differences")
    if not isinstance(differences, list):
        errors.append("context_differences must be a list")
        differences = []
    required_dimensions = {"timing", "institution", "scale", "beneficiary_power"}
    dimensions = set()
    for index, difference in enumerate(differences):
        prefix = f"context_differences[{index}]"
        if not isinstance(difference, dict):
            errors.append(f"{prefix} must be an object")
            continue
        dimension = difference.get("dimension")
        if dimension not in required_dimensions:
            errors.append(f"{prefix}.dimension is not recognized")
        elif dimension in dimensions:
            errors.append(f"{prefix}.dimension must be unique")
        dimensions.add(dimension)
        for field in ("historical_state", "current_state", "effect_on_transfer"):
            if not _non_empty(difference.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if dimensions != required_dimensions:
        errors.append("context_differences must cover timing, institution, scale, and beneficiary_power")
    local_evidence = payload.get("local_evidence_ids")
    if (
        not isinstance(local_evidence, list)
        or not local_evidence
        or not all(_non_empty(item) for item in local_evidence)
    ):
        errors.append("local_evidence_ids must be a non-empty list")
    return {
        "valid": not errors,
        "errors": errors,
        "difference_dimensions": sorted(dimensions),
        "transfer_authority": payload.get("transfer_authority"),
    }

def validate_world_model_surprise_registry(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require every live world model to state how it could lose."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["world model surprise registry must be an object"]}
    for field in ("surprise_registry_id", "world_model_set_id", "observation_window", "review_trigger"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    entries = payload.get("model_surprises")
    if not isinstance(entries, list) or len(entries) < 2:
        errors.append("model_surprises must contain at least two models")
        entries = []
    model_ids = []
    for index, entry in enumerate(entries):
        prefix = f"model_surprises[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        model_id = entry.get("model_id")
        if not _non_empty(model_id):
            errors.append(f"{prefix}.model_id must be a non-empty string")
        elif model_id in model_ids:
            errors.append(f"{prefix}.model_id must be unique")
        model_ids.append(model_id)
        for field in (
            "expected_observation",
            "surprising_observation",
            "why_surprising",
            "measurement_rule",
            "model_update_if_observed",
            "favored_competing_model_id",
        ):
            if not _non_empty(entry.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if entry.get("expected_observation") == entry.get("surprising_observation"):
            errors.append(f"{prefix} expected and surprising observations must differ")
        if entry.get("model_can_lose") is not True:
            errors.append(f"{prefix}.model_can_lose must be true")
    model_id_set = set(model_ids)
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            continue
        favored = entry.get("favored_competing_model_id")
        if favored not in model_id_set or favored == entry.get("model_id"):
            errors.append(
                f"model_surprises[{index}].favored_competing_model_id must reference another registered model"
            )
    return {
        "valid": not errors,
        "errors": errors,
        "losable_model_count": sum(
            1 for entry in entries if isinstance(entry, dict) and entry.get("model_can_lose") is True
        ),
    }

def validate_normative_empirical_separation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Separate value disagreement from uncertainty that evidence can resolve."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["normative empirical separation must be an object"]}
    for field in (
        "disagreement_record_id",
        "mission_question",
        "normative_decision_authority_id",
        "decision_protocol",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("value_disagreement_disguised_as_missing_data") is not False:
        errors.append("value_disagreement_disguised_as_missing_data must be false")
    frames = payload.get("frames")
    if not isinstance(frames, list) or len(frames) < 2:
        errors.append("frames must contain at least two normative frames")
        frames = []
    frame_ids = set()
    for index, frame in enumerate(frames):
        prefix = f"frames[{index}]"
        if not isinstance(frame, dict):
            errors.append(f"{prefix} must be an object")
            continue
        frame_id = frame.get("frame_id")
        if not _non_empty(frame_id):
            errors.append(f"{prefix}.frame_id must be a non-empty string")
        elif frame_id in frame_ids:
            errors.append(f"{prefix}.frame_id must be unique")
        frame_ids.add(frame_id)
        for field in ("value_priority", "unacceptable_tradeoff", "represented_by"):
            if not _non_empty(frame.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")

    empirical = payload.get("empirical_questions")
    if not isinstance(empirical, list) or not empirical:
        errors.append("empirical_questions must be a non-empty list")
        empirical = []
    for index, question in enumerate(empirical):
        prefix = f"empirical_questions[{index}]"
        if not isinstance(question, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("question_id", "question", "discriminating_evidence", "update_if_observed"):
            if not _non_empty(question.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if question.get("empirically_resolvable") is not True:
            errors.append(f"{prefix}.empirically_resolvable must be true")

    normative = payload.get("normative_disagreements")
    if not isinstance(normative, list) or not normative:
        errors.append("normative_disagreements must be a non-empty list")
        normative = []
    for index, disagreement in enumerate(normative):
        prefix = f"normative_disagreements[{index}]"
        if not isinstance(disagreement, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("disagreement_id", "value_choice", "required_commitment"):
            if not _non_empty(disagreement.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        referenced = disagreement.get("frame_ids")
        if (
            not isinstance(referenced, list)
            or len(referenced) < 2
            or any(item not in frame_ids for item in referenced)
        ):
            errors.append(f"{prefix}.frame_ids must reference at least two declared frames")
        if disagreement.get("more_data_can_resolve") is not False:
            errors.append(f"{prefix}.more_data_can_resolve must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "empirical_question_count": len(empirical),
        "normative_disagreement_count": len(normative),
    }

def validate_interpretation_operational_relevance(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Classify an interpretation by whether it changes options or the next probe."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["interpretation operational relevance must be an object"]}
    for field in (
        "interpretation_relevance_id",
        "interpretation_id",
        "interpretation_summary",
        "prior_probe_id",
        "next_probe_id",
        "storage_disposition",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    before = payload.get("mission_option_ids_before")
    after = payload.get("mission_option_ids_after")
    for field, items in (("mission_option_ids_before", before), ("mission_option_ids_after", after)):
        if (
            not isinstance(items, list)
            or not all(_non_empty(item) for item in items)
            or len(items) != len(set(items))
        ):
            errors.append(f"{field} must be a unique string list")
    before_set = set(before) if isinstance(before, list) else set()
    after_set = set(after) if isinstance(after, list) else set()
    option_changed = before_set != after_set
    probe_changed = (
        _non_empty(payload.get("prior_probe_id"))
        and _non_empty(payload.get("next_probe_id"))
        and payload.get("prior_probe_id") != payload.get("next_probe_id")
    )
    if payload.get("changes_mission_option_set") is not option_changed:
        errors.append("changes_mission_option_set must match the before and after option sets")
    if payload.get("changes_next_probe") is not probe_changed:
        errors.append("changes_next_probe must match the prior and next probe ids")
    expected_classification = "operational" if option_changed or probe_changed else "background_knowledge"
    if payload.get("classification") != expected_classification:
        errors.append("classification must follow whether options or the next probe changed")
    if expected_classification == "operational":
        if not _non_empty(payload.get("decision_effect")):
            errors.append("decision_effect must be a non-empty string for operational interpretation")
    elif payload.get("storage_disposition") != "archive_as_background":
        errors.append("storage_disposition must be archive_as_background when no option or probe changes")
    return {
        "valid": not errors,
        "errors": errors,
        "classification": expected_classification,
        "changes_mission_option_set": option_changed,
        "changes_next_probe": probe_changed,
    }

def validate_post_decision_model_compression(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Shrink a decided model while preserving monitoring, falsification, and lineage."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["post-decision model compression must be an object"]}
    for field in (
        "compression_record_id",
        "world_model_set_id",
        "decision_id",
        "lineage_archive_id",
        "rehydration_trigger",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    before = payload.get("component_ids_before")
    if (
        not isinstance(before, list)
        or len(before) < 2
        or not all(_non_empty(item) for item in before)
        or len(before) != len(set(before))
    ):
        errors.append("component_ids_before must contain at least two unique ids")
        before = []
    retained = payload.get("retained_relations")
    if not isinstance(retained, list) or not retained:
        errors.append("retained_relations must be a non-empty list")
        retained = []
    retained_ids = set()
    purposes = set()
    for index, relation in enumerate(retained):
        prefix = f"retained_relations[{index}]"
        if not isinstance(relation, dict):
            errors.append(f"{prefix} must be an object")
            continue
        component_id = relation.get("component_id")
        if component_id not in before:
            errors.append(f"{prefix}.component_id must reference a pre-compression component")
        elif component_id in retained_ids:
            errors.append(f"{prefix}.component_id must be unique")
        retained_ids.add(component_id)
        purpose = relation.get("retention_purpose")
        if purpose not in {"monitoring", "disconfirmation", "reconstruction"}:
            errors.append(f"{prefix}.retention_purpose is not recognized")
        else:
            purposes.add(purpose)
        for field in ("relation", "retention_rationale"):
            if not _non_empty(relation.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if purposes != {"monitoring", "disconfirmation", "reconstruction"}:
        errors.append("retained_relations must cover monitoring, disconfirmation, and reconstruction")
    removed = payload.get("removed_components")
    if not isinstance(removed, list) or not removed:
        errors.append("removed_components must be a non-empty list")
        removed = []
    removed_ids = set()
    for index, component in enumerate(removed):
        prefix = f"removed_components[{index}]"
        if not isinstance(component, dict):
            errors.append(f"{prefix} must be an object")
            continue
        component_id = component.get("component_id")
        if component_id not in before:
            errors.append(f"{prefix}.component_id must reference a pre-compression component")
        elif component_id in removed_ids:
            errors.append(f"{prefix}.component_id must be unique")
        removed_ids.add(component_id)
        if not _non_empty(component.get("removal_rationale")):
            errors.append(f"{prefix}.removal_rationale must be a non-empty string")
    if retained_ids.intersection(removed_ids):
        errors.append("retained and removed component ids must not overlap")
    if retained_ids.union(removed_ids) != set(before):
        errors.append("retained and removed components must partition the pre-compression model")
    if len(retained_ids) >= len(before):
        errors.append("post-decision model must contain fewer active components")
    if payload.get("lineage_deleted") is not False:
        errors.append("lineage_deleted must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "before_count": len(before),
        "retained_count": len(retained_ids),
    }

def validate_interpretation_thesis_integration(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Integrate competing, falsifiable, mission-changing causal interpretation."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["interpretation thesis integration must be an object"]}
    for field in (
        "interpretation_thesis_id",
        "world_model_set_id",
        "causal_sketch_set_id",
        "complexity_review_id",
        "correlation_authority_review_id",
        "historical_analogy_id",
        "surprise_registry_id",
        "normative_separation_id",
        "operational_relevance_id",
        "compression_record_id",
        "mission_option_change_record_id",
        "revision_trigger",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    for field in (
        "competing_sketches_present",
        "every_model_falsifiable",
        "causal_complexity_decision_relevant",
        "correlation_authority_bounded",
        "normative_empirical_boundary_explicit",
        "post_decision_compression_present",
    ):
        if payload.get(field) is not True:
            errors.append(f"{field} must be true")
    if payload.get("complete_worldview_is_goal") is not False:
        errors.append("complete_worldview_is_goal must be false")
    changes_options = payload.get("changes_mission_option_set")
    changes_probe = payload.get("changes_next_probe")
    if not isinstance(changes_options, bool):
        errors.append("changes_mission_option_set must be boolean")
    if not isinstance(changes_probe, bool):
        errors.append("changes_next_probe must be boolean")
    if changes_options is not True and changes_probe is not True:
        errors.append("interpretation must change a mission option set or the next probe")
    purposes = payload.get("retained_post_decision_purposes")
    required_purposes = {"monitoring", "disconfirmation", "reconstruction"}
    if (
        not isinstance(purposes, list)
        or set(purposes) != required_purposes
        or len(purposes) != len(required_purposes)
    ):
        errors.append(
            "retained_post_decision_purposes must contain monitoring, disconfirmation, and reconstruction"
        )
    if payload.get("conclusion") != "interpretation_thesis_supported":
        errors.append("conclusion must be interpretation_thesis_supported")
    return {
        "valid": not errors,
        "errors": errors,
        "operational_change_present": changes_options is True or changes_probe is True,
    }

def validate_bidirectional_mission_generation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require mission candidates from both condition-first and capability-first search."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["bidirectional mission generation must be an object"]}
    for field in (
        "mission_generation_id",
        "generation_context",
        "comparison_protocol",
        "next_selection_gate",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    if payload.get("problem_only_generation") is not False:
        errors.append("problem_only_generation must be false")
    if payload.get("capability_only_generation") is not False:
        errors.append("capability_only_generation must be false")
    candidates = payload.get("mission_candidates")
    if not isinstance(candidates, list) or len(candidates) < 2:
        errors.append("mission_candidates must contain at least two candidates")
        candidates = []
    required_origins = {"condition_first", "capability_first"}
    origins = set()
    candidate_ids = set()
    for index, candidate in enumerate(candidates):
        prefix = f"mission_candidates[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{prefix} must be an object")
            continue
        candidate_id = candidate.get("candidate_id")
        if not _non_empty(candidate_id):
            errors.append(f"{prefix}.candidate_id must be a non-empty string")
        elif candidate_id in candidate_ids:
            errors.append(f"{prefix}.candidate_id must be unique")
        candidate_ids.add(candidate_id)
        origin = candidate.get("generation_origin")
        if origin not in required_origins:
            errors.append(f"{prefix}.generation_origin is not recognized")
        else:
            origins.add(origin)
        for field in (
            "origin_evidence_id",
            "beneficiary",
            "mission_hypothesis",
            "desired_state_change",
            "failure_signal",
        ):
            if not _non_empty(candidate.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if origins != required_origins:
        errors.append("mission_candidates must include condition_first and capability_first origins")
    criteria = payload.get("common_comparison_criteria")
    required_criteria = {
        "beneficiary_consequence",
        "constitutional_fit",
        "evidence_strength",
        "option_value",
    }
    if (
        not isinstance(criteria, list)
        or set(criteria) != required_criteria
        or len(criteria) != len(required_criteria)
    ):
        errors.append("common_comparison_criteria must contain the four required criteria")
    return {
        "valid": not errors,
        "errors": errors,
        "generation_origins": sorted(origins),
    }

def validate_condition_capability_state_distinction(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Distinguish repairing an existing condition from enabling a new reachable state."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["condition capability state distinction must be an object"]}
    for field in (
        "state_distinction_id",
        "mission_generation_id",
        "selection_deferred_until_comparison",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    condition = payload.get("condition_first_candidate")
    if not isinstance(condition, dict):
        errors.append("condition_first_candidate must be an object")
        condition = {}
    for field in (
        "candidate_id",
        "beneficiary",
        "current_condition",
        "desired_condition",
        "condition_evidence_id",
        "state_change_measure",
    ):
        if not _non_empty(condition.get(field)):
            errors.append(f"condition_first_candidate.{field} must be a non-empty string")
    if condition.get("existing_condition_observed") is not True:
        errors.append("condition_first_candidate.existing_condition_observed must be true")

    capability = payload.get("capability_first_candidate")
    if not isinstance(capability, dict):
        errors.append("capability_first_candidate must be an object")
        capability = {}
    for field in (
        "candidate_id",
        "capability_id",
        "capability_evidence_id",
        "beneficiary",
        "previously_unreachable_state",
        "newly_reachable_state",
        "reachability_evidence_id",
        "beneficiary_consequence",
    ):
        if not _non_empty(capability.get(field)):
            errors.append(f"capability_first_candidate.{field} must be a non-empty string")
    if capability.get("state_previously_reachable") is not False:
        errors.append("capability_first_candidate.state_previously_reachable must be false")
    if capability.get("state_now_reachable") is not True:
        errors.append("capability_first_candidate.state_now_reachable must be true")
    if capability.get("capability_without_beneficiary_consequence_is_mission") is not False:
        errors.append(
            "capability_first_candidate.capability_without_beneficiary_consequence_is_mission must be false"
        )
    if condition.get("candidate_id") == capability.get("candidate_id"):
        errors.append("condition-first and capability-first candidate ids must differ")
    return {
        "valid": not errors,
        "errors": errors,
        "condition_candidate_id": condition.get("candidate_id"),
        "capability_candidate_id": capability.get("candidate_id"),
    }

