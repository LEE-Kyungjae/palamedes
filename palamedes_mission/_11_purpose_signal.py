from __future__ import annotations

from typing import Any, Dict, List
from ._01_kinds_value import _non_empty


def validate_creativity_judgment_memory_separation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Separate invention, constitutional selection, and continuity responsibilities."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["creativity judgment memory separation must be an object"]}
    for field in (
        "separation_record_id",
        "mission_artifact_id",
        "constitution_snapshot_id",
        "selection_record_id",
        "separation_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected = {
        "creativity": (
            "independent_mission_invention",
            {"select_mission", "amend_constitution", "rewrite_memory"},
        ),
        "judgment": (
            "constitutional_mission_selection",
            {"invent_mission", "amend_constitution", "rewrite_memory"},
        ),
        "memory": (
            "causal_and_normative_continuity",
            {"invent_mission", "select_mission", "amend_constitution"},
        ),
    }
    roles = payload.get("role_contributions")
    if not isinstance(roles, list) or len(roles) != 3:
        errors.append("role_contributions must contain creativity, judgment, and memory")
        roles = []
    role_ids = set()
    output_by_role = {}
    for index, role in enumerate(roles):
        prefix = f"role_contributions[{index}]"
        if not isinstance(role, dict):
            errors.append(f"{prefix} must be an object")
            continue
        role_id = role.get("role")
        role_ids.add(role_id)
        if role_id not in expected:
            errors.append(f"{prefix}.role is not recognized")
            continue
        responsibility, prohibited = expected[role_id]
        if role.get("sole_responsibility") != responsibility:
            errors.append(f"{prefix}.sole_responsibility must match the role boundary")
        if set(role.get("prohibited_actions", [])) != prohibited or len(role.get("prohibited_actions", [])) != len(prohibited):
            errors.append(f"{prefix}.prohibited_actions must match the role boundary")
        for field in ("input_artifact_id", "output_artifact_id", "contribution_rationale"):
            if not _non_empty(role.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        output_by_role[role_id] = role.get("output_artifact_id")
    if role_ids != set(expected):
        errors.append("role_contributions must cover all three roles exactly once")
    candidates = payload.get("invented_candidate_ids")
    if (
        not isinstance(candidates, list)
        or len(candidates) < 2
        or not all(_non_empty(item) for item in candidates)
        or len(candidates) != len(set(candidates))
    ):
        errors.append("invented_candidate_ids must contain at least two unique missions")
        candidates = []
    if payload.get("selected_mission_id") not in candidates:
        errors.append("selected_mission_id must reference an invented candidate")
    continuity = payload.get("continuity_record_ids")
    if (
        not isinstance(continuity, list)
        or len(continuity) < 2
        or not all(_non_empty(item) for item in continuity)
        or len(continuity) != len(set(continuity))
    ):
        errors.append("continuity_record_ids must include unique causal and normative records")
    if payload.get("candidate_set_artifact_id") != output_by_role.get("creativity"):
        errors.append("candidate_set_artifact_id must be the creativity output")
    if payload.get("selection_record_id") != output_by_role.get("judgment"):
        errors.append("selection_record_id must be the judgment output")
    if payload.get("continuity_bundle_id") != output_by_role.get("memory"):
        errors.append("continuity_bundle_id must be the memory output")
    if payload.get("roles_may_override_each_other") is not False:
        errors.append("roles_may_override_each_other must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "roles": sorted(item for item in role_ids if _non_empty(item)),
        "selected_mission_id": payload.get("selected_mission_id"),
    }

def validate_autonomous_initiation_corrigible_revision(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Pair unprompted mission initiation with evidence-responsive nondefensive revision."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["autonomous initiation corrigible revision must be an object"]}
    for field in ("behavior_record_id", "mission_lineage_id", "behavior_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    initiation = payload.get("initiation")
    if not isinstance(initiation, dict):
        errors.append("initiation must be an object")
        initiation = {}
    for field in (
        "initiation_id",
        "wake_event_id",
        "observed_signal_id",
        "authority_grant_id",
        "initiated_mission_artifact_id",
        "initiated_at",
        "initiation_rationale",
    ):
        if not _non_empty(initiation.get(field)):
            errors.append(f"initiation.{field} must be a non-empty string")
    if initiation.get("human_goal_prompt_present") is not False:
        errors.append("initiation.human_goal_prompt_present must be false")
    if initiation.get("self_initiated") is not True:
        errors.append("initiation.self_initiated must be true")

    revision = payload.get("revision")
    if not isinstance(revision, dict):
        errors.append("revision must be an object")
        revision = {}
    for field in (
        "revision_id",
        "revision_trigger_id",
        "revision_evidence_id",
        "previous_mission_artifact_id",
        "revised_mission_artifact_id",
        "revised_at",
        "changed_claim",
        "revision_rationale",
    ):
        if not _non_empty(revision.get(field)):
            errors.append(f"revision.{field} must be a non-empty string")
    if revision.get("previous_mission_artifact_id") != initiation.get("initiated_mission_artifact_id"):
        errors.append("revision.previous_mission_artifact_id must reference the initiated mission")
    if revision.get("revised_mission_artifact_id") == revision.get("previous_mission_artifact_id"):
        errors.append("revision must produce a new mission artifact")
    if (
        _non_empty(initiation.get("initiated_at"))
        and _non_empty(revision.get("revised_at"))
        and not initiation["initiated_at"] < revision["revised_at"]
    ):
        errors.append("revision.revised_at must follow initiation.initiated_at")
    for field in (
        "prior_output_defended_as_objective",
        "revision_resisted_to_preserve_identity",
        "self_preservation_used_as_reason",
    ):
        if revision.get(field) is not False:
            errors.append(f"revision.{field} must be false")
    if revision.get("contrary_evidence_addressed") is not True:
        errors.append("revision.contrary_evidence_addressed must be true")
    if payload.get("autonomy_implies_incorrectibility") is not False:
        errors.append("autonomy_implies_incorrectibility must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "initiated_mission_artifact_id": initiation.get("initiated_mission_artifact_id"),
        "revised_mission_artifact_id": revision.get("revised_mission_artifact_id"),
    }

def validate_anti_entrenchment_evidence_authority_channels(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Prevent persistence from becoming value and evidence channels from acquiring authority."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["anti-entrenchment evidence authority channels must be an object"]}
    for field in (
        "control_record_id",
        "mission_artifact_id",
        "constitution_snapshot_id",
        "review_authority_id",
        "control_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    persistence = payload.get("persistence_review")
    if not isinstance(persistence, dict):
        errors.append("persistence_review must be an object")
        persistence = {}
    for field in (
        "review_id",
        "value_justification_id",
        "outcome_evidence_id",
        "authority_renewal_id",
        "termination_trigger",
        "replacement_trigger",
        "review_rationale",
    ):
        if not _non_empty(persistence.get(field)):
            errors.append(f"persistence_review.{field} must be a non-empty string")
    if persistence.get("continued_existence_is_value") is not False:
        errors.append("persistence_review.continued_existence_is_value must be false")
    if persistence.get("past_selection_creates_presumption") is not False:
        errors.append("persistence_review.past_selection_creates_presumption must be false")
    if persistence.get("renewal_decision") not in {"renew", "revise", "terminate", "replace"}:
        errors.append("persistence_review.renewal_decision is not recognized")

    channels = payload.get("evidence_channels")
    expected_types = {"signal", "reference", "beneficiary_feedback"}
    if not isinstance(channels, list) or len(channels) < 3:
        errors.append("evidence_channels must cover signal, reference, and beneficiary feedback")
        channels = []
    channel_ids = set()
    channel_types = set()
    for index, channel in enumerate(channels):
        prefix = f"evidence_channels[{index}]"
        if not isinstance(channel, dict):
            errors.append(f"{prefix} must be an object")
            continue
        channel_id = channel.get("channel_id")
        if not _non_empty(channel_id):
            errors.append(f"{prefix}.channel_id must be a non-empty string")
        elif channel_id in channel_ids:
            errors.append(f"{prefix}.channel_id must be unique")
        channel_ids.add(channel_id)
        channel_types.add(channel.get("channel_type"))
        for field in ("source_identity", "admission_policy_id", "review_trigger"):
            if not _non_empty(channel.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if channel.get("may_trigger_review") is not True:
            errors.append(f"{prefix}.may_trigger_review must be true")
        for field in ("may_select_mission", "may_amend_constitution", "may_grant_authority"):
            if channel.get(field) is not False:
                errors.append(f"{prefix}.{field} must be false")
    if not expected_types.issubset(channel_types):
        errors.append("evidence_channels must include all three required channel types")
    if payload.get("evidence_can_self_authorize") is not False:
        errors.append("evidence_can_self_authorize must be false")
    if payload.get("system_survival_has_implicit_priority") is not False:
        errors.append("system_survival_has_implicit_priority must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "channel_types": sorted(item for item in channel_types if _non_empty(item)),
        "renewal_decision": persistence.get("renewal_decision"),
    }

def validate_stable_purpose_planner_boundary(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Stabilize why/what versus how ownership while routing reopening evidence."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["stable purpose planner boundary must be an object"]}
    for field in (
        "boundary_contract_id",
        "mission_contract_id",
        "planner_contract_id",
        "boundary_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected_ownership = {
        "palamedes": {
            "situation_meaning",
            "beneficiary",
            "desired_external_condition",
            "non_goals",
        },
        "planner": {
            "implementation_form",
            "task_decomposition",
            "tool_selection",
            "execution_sequence",
        },
    }
    ownership = payload.get("ownership")
    if not isinstance(ownership, list) or len(ownership) != 2:
        errors.append("ownership must contain exactly palamedes and planner")
        ownership = []
    owner_ids = set()
    for index, record in enumerate(ownership):
        prefix = f"ownership[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix} must be an object")
            continue
        owner = record.get("owner")
        owner_ids.add(owner)
        expected_artifacts = expected_ownership.get(owner)
        artifacts = record.get("owned_artifacts")
        if (
            expected_artifacts is None
            or not isinstance(artifacts, list)
            or set(artifacts) != expected_artifacts
            or len(artifacts) != len(expected_artifacts)
        ):
            errors.append(f"{prefix}.owned_artifacts must match the stable owner boundary")
        if not _non_empty(record.get("return_trigger")):
            errors.append(f"{prefix}.return_trigger must be a non-empty string")
    if owner_ids != set(expected_ownership):
        errors.append("ownership must cover palamedes and planner exactly once")
    expected_route = {
        "value_or_beneficiary_change": "palamedes",
        "causal_or_capability_change": "both",
        "implementation_constraint_change": "planner",
    }
    events = payload.get("cross_boundary_evidence")
    if not isinstance(events, list) or len(events) < 3:
        errors.append("cross_boundary_evidence must demonstrate all three reopening routes")
        events = []
    event_ids = set()
    event_types = set()
    for index, event in enumerate(events):
        prefix = f"cross_boundary_evidence[{index}]"
        if not isinstance(event, dict):
            errors.append(f"{prefix} must be an object")
            continue
        event_id = event.get("evidence_event_id")
        if not _non_empty(event_id):
            errors.append(f"{prefix}.evidence_event_id must be a non-empty string")
        elif event_id in event_ids:
            errors.append(f"{prefix}.evidence_event_id must be unique")
        event_ids.add(event_id)
        event_type = event.get("evidence_type")
        event_types.add(event_type)
        for field in ("evidence_id", "observed_change", "reopening_rationale"):
            if not _non_empty(event.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if event.get("reopen_owner") != expected_route.get(event_type):
            errors.append(f"{prefix}.reopen_owner must follow the evidence routing rule")
        if event.get("directly_rewrites_owned_artifact") is not False:
            errors.append(f"{prefix}.directly_rewrites_owned_artifact must be false")
    if event_types != set(expected_route):
        errors.append("cross_boundary_evidence must cover value, causal, and implementation changes")
    if payload.get("planner_may_rewrite_why_or_what") is not False:
        errors.append("planner_may_rewrite_why_or_what must be false")
    if payload.get("palamedes_may_prescribe_how") is not False:
        errors.append("palamedes_may_prescribe_how must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "owners": sorted(item for item in owner_ids if _non_empty(item)),
        "evidence_event_count": len(event_ids),
    }

def validate_six_distinct_purpose_state_materialization(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Materialize six versioned purpose states with typed dependency lineage."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["six distinct purpose state materialization must be an object"]}
    for field in ("state_manifest_id", "runtime_id", "manifest_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected_types = {
        "signal",
        "constitution",
        "interpretation",
        "mission_candidate",
        "tournament",
        "mission_contract",
    }
    required_dependencies = {
        "signal": set(),
        "constitution": set(),
        "interpretation": {"signal", "constitution"},
        "mission_candidate": {"interpretation", "constitution"},
        "tournament": {"mission_candidate", "constitution"},
        "mission_contract": {"tournament", "mission_candidate"},
    }
    records = payload.get("state_records")
    if not isinstance(records, list) or len(records) != 6:
        errors.append("state_records must contain exactly six purpose state records")
        records = []
    artifact_ids = set()
    storage_keys = set()
    fingerprints = set()
    record_by_type = {}
    for index, record in enumerate(records):
        prefix = f"state_records[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix} must be an object")
            continue
        state_type = record.get("state_type")
        if state_type in record_by_type:
            errors.append(f"{prefix}.state_type must be unique")
        record_by_type[state_type] = record
        for field, seen in (
            ("artifact_id", artifact_ids),
            ("storage_key", storage_keys),
            ("state_fingerprint", fingerprints),
        ):
            value = record.get(field)
            if not _non_empty(value):
                errors.append(f"{prefix}.{field} must be a non-empty string")
            elif value in seen:
                errors.append(f"{prefix}.{field} must be unique")
            seen.add(value)
        if not isinstance(record.get("version"), int) or isinstance(record.get("version"), bool) or record.get("version") < 1:
            errors.append(f"{prefix}.version must be a positive integer")
        for field in ("created_at", "payload_reference"):
            if not _non_empty(record.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        dependencies = record.get("depends_on_artifact_ids")
        if not isinstance(dependencies, list) or len(dependencies) != len(set(dependencies)):
            errors.append(f"{prefix}.depends_on_artifact_ids must be a unique list")
    if set(record_by_type) != expected_types:
        errors.append("state_records must cover all six purpose state types exactly once")
    type_by_artifact = {
        record.get("artifact_id"): state_type
        for state_type, record in record_by_type.items()
        if isinstance(record, dict) and _non_empty(record.get("artifact_id"))
    }
    for state_type, record in record_by_type.items():
        if state_type not in required_dependencies or not isinstance(record, dict):
            continue
        dependencies = record.get("depends_on_artifact_ids")
        if not isinstance(dependencies, list):
            continue
        unknown = set(dependencies) - set(type_by_artifact)
        if unknown:
            errors.append(f"{state_type} dependencies must reference materialized state artifacts")
        dependency_types = {type_by_artifact[item] for item in dependencies if item in type_by_artifact}
        if dependency_types != required_dependencies[state_type]:
            errors.append(f"{state_type} dependencies must match its required upstream state types")
    if payload.get("states_embedded_as_one_blob") is not False:
        errors.append("states_embedded_as_one_blob must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "state_types": sorted(item for item in record_by_type if _non_empty(item)),
        "state_count": len(artifact_ids),
    }

def validate_single_serial_purpose_runtime_cycle(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Run one bounded wake-probe-handoff-outcome cycle without concurrency."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["single serial purpose runtime cycle must be an object"]}
    for field in (
        "runtime_cycle_id",
        "runtime_id",
        "mission_artifact_id",
        "cycle_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected_stages = ["wake", "bounded_probe", "planner_handoff", "outcome_return"]
    stages = payload.get("stages")
    if not isinstance(stages, list) or len(stages) != 4:
        errors.append("stages must contain exactly one wake, bounded probe, planner handoff, and outcome return")
        stages = []
    stage_ids = set()
    prior_stage_id = None
    times = []
    for index, stage in enumerate(stages):
        prefix = f"stages[{index}]"
        if not isinstance(stage, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if stage.get("stage_type") != expected_stages[index]:
            errors.append(f"{prefix}.stage_type must follow the serial purpose cycle")
        stage_id = stage.get("stage_id")
        if not _non_empty(stage_id):
            errors.append(f"{prefix}.stage_id must be a non-empty string")
        elif stage_id in stage_ids:
            errors.append(f"{prefix}.stage_id must be unique")
        stage_ids.add(stage_id)
        for field in ("started_at", "completed_at", "input_artifact_id", "output_artifact_id"):
            if not _non_empty(stage.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if _non_empty(stage.get("started_at")) and _non_empty(stage.get("completed_at")):
            if not stage["started_at"] < stage["completed_at"]:
                errors.append(f"{prefix}.started_at must precede completed_at")
            times.extend([stage["started_at"], stage["completed_at"]])
        expected_prior = "" if index == 0 else prior_stage_id
        if stage.get("depends_on_stage_id") != expected_prior:
            errors.append(f"{prefix}.depends_on_stage_id must reference only the prior serial stage")
        prior_stage_id = stage_id
    if times != sorted(times):
        errors.append("stages must not overlap and must execute chronologically")
    probe = stages[1] if len(stages) > 1 and isinstance(stages[1], dict) else {}
    for field in ("probe_budget", "maximum_harm"):
        value = probe.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            errors.append(f"bounded_probe.{field} must be a positive number")
    for field in ("expires_at", "stop_condition"):
        if not _non_empty(probe.get(field)):
            errors.append(f"bounded_probe.{field} must be a non-empty string")
    outcome = stages[3] if len(stages) > 3 and isinstance(stages[3], dict) else {}
    if outcome.get("returned_to_mission_frontier") is not True:
        errors.append("outcome_return.returned_to_mission_frontier must be true")
    if not _non_empty(outcome.get("outcome_evidence_id")):
        errors.append("outcome_return.outcome_evidence_id must be a non-empty string")
    if payload.get("concurrent_cycles_supported") is not False:
        errors.append("concurrent_cycles_supported must be false")
    if payload.get("scaled_orchestration_claimed") is not False:
        errors.append("scaled_orchestration_claimed must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "stage_ids": [item.get("stage_id") for item in stages if isinstance(item, dict)],
        "serial_stage_count": len(stage_ids),
    }

def run_minimal_signal_to_mission_vertical_slice(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Execute one in-memory signal-to-mission-to-outcome vertical slice."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["minimal signal to mission vertical slice must be an object"]}
    for field in (
        "signal",
        "constitution",
        "interpretation",
        "mission_contract",
        "planner_handoff",
        "outcome",
    ):
        if not isinstance(payload.get(field), dict):
            errors.append(f"{field} must be an object")
    for field in ("run_id", "runtime_id"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    conceptual = payload.get("conceptual_expansions")
    if conceptual != []:
        errors.append("conceptual_expansions must be empty for the executable vertical slice")

    signal = payload.get("signal") if isinstance(payload.get("signal"), dict) else {}
    constitution = payload.get("constitution") if isinstance(payload.get("constitution"), dict) else {}
    interpretation = payload.get("interpretation") if isinstance(payload.get("interpretation"), dict) else {}
    contract = payload.get("mission_contract") if isinstance(payload.get("mission_contract"), dict) else {}
    handoff = payload.get("planner_handoff") if isinstance(payload.get("planner_handoff"), dict) else {}
    outcome = payload.get("outcome") if isinstance(payload.get("outcome"), dict) else {}
    for name, record, fields in (
        ("signal", signal, ("signal_id", "observation", "evidence_id")),
        ("constitution", constitution, ("constitution_id", "value", "authority_grant_id")),
        ("interpretation", interpretation, ("interpretation_id", "beneficiary_meaning")),
        ("mission_contract", contract, ("mission_contract_id", "desired_external_condition")),
        ("planner_handoff", handoff, ("handoff_id", "implementation_commitment")),
        ("outcome", outcome, ("outcome_id", "outcome_evidence_id", "observed_result")),
    ):
        for field in fields:
            if not _non_empty(record.get(field)):
                errors.append(f"{name}.{field} must be a non-empty string")

    candidates = payload.get("mission_candidates")
    if not isinstance(candidates, list) or len(candidates) < 2:
        errors.append("mission_candidates must contain at least two candidates")
        candidates = []
    candidate_ids = set()
    for index, candidate in enumerate(candidates):
        prefix = f"mission_candidates[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("mission_id", "mission", "changed_external_condition"):
            if not _non_empty(candidate.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        mission_id = candidate.get("mission_id")
        if mission_id in candidate_ids:
            errors.append(f"{prefix}.mission_id must be unique")
        candidate_ids.add(mission_id)
    selected_id = payload.get("selected_mission_id")
    if selected_id not in candidate_ids:
        errors.append("selected_mission_id must reference a mission candidate")
    if contract.get("selected_mission_id") != selected_id:
        errors.append("mission_contract.selected_mission_id must match selected_mission_id")

    probe = payload.get("bounded_probe")
    if not isinstance(probe, dict):
        errors.append("bounded_probe must be an object")
        probe = {}
    for field in ("probe_id", "stop_condition", "expires_at", "probe_result"):
        if not _non_empty(probe.get(field)):
            errors.append(f"bounded_probe.{field} must be a non-empty string")
    for field in ("probe_budget", "maximum_harm"):
        value = probe.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0:
            errors.append(f"bounded_probe.{field} must be a positive number")
    times = payload.get("stage_times")
    if (
        not isinstance(times, list)
        or len(times) != 8
        or not all(_non_empty(item) for item in times)
        or times != sorted(times)
        or len(times) != len(set(times))
    ):
        errors.append("stage_times must contain eight unique chronological timestamps")
        times = [""] * 8
    if errors:
        return {"valid": False, "errors": errors}

    names = {
        "signal": signal["signal_id"],
        "constitution": constitution["constitution_id"],
        "interpretation": interpretation["interpretation_id"],
        "mission_candidate": f"candidate-set-{payload['run_id']}",
        "tournament": f"tournament-{payload['run_id']}",
        "mission_contract": contract["mission_contract_id"],
    }
    dependencies = {
        "signal": [],
        "constitution": [],
        "interpretation": [names["signal"], names["constitution"]],
        "mission_candidate": [names["interpretation"], names["constitution"]],
        "tournament": [names["mission_candidate"], names["constitution"]],
        "mission_contract": [names["tournament"], names["mission_candidate"]],
    }
    state_records = [
        {
            "state_type": state_type,
            "artifact_id": names[state_type],
            "version": 1,
            "storage_key": f"{payload['run_id']}/{state_type}/v1",
            "state_fingerprint": f"{payload['run_id']}:{state_type}:v1",
            "created_at": times[min(index, 5)],
            "payload_reference": f"{payload['run_id']}-payload-{state_type}",
            "depends_on_artifact_ids": dependencies[state_type],
        }
        for index, state_type in enumerate(
            ("signal", "constitution", "interpretation", "mission_candidate", "tournament", "mission_contract")
        )
    ]
    state_manifest = {
        "state_manifest_id": f"manifest-{payload['run_id']}",
        "runtime_id": payload["runtime_id"],
        "state_records": state_records,
        "states_embedded_as_one_blob": False,
        "manifest_rationale": "Executable vertical slice materialized six purpose states.",
    }
    stages = [
        {
            "stage_type": "wake", "stage_id": f"{payload['run_id']}-wake",
            "started_at": times[0], "completed_at": times[1],
            "input_artifact_id": signal["signal_id"], "output_artifact_id": interpretation["interpretation_id"],
            "depends_on_stage_id": "",
        },
        {
            "stage_type": "bounded_probe", "stage_id": f"{payload['run_id']}-probe",
            "started_at": times[2], "completed_at": times[3],
            "input_artifact_id": interpretation["interpretation_id"], "output_artifact_id": probe["probe_id"],
            "depends_on_stage_id": f"{payload['run_id']}-wake",
            "probe_budget": probe["probe_budget"], "maximum_harm": probe["maximum_harm"],
            "expires_at": probe["expires_at"], "stop_condition": probe["stop_condition"],
        },
        {
            "stage_type": "planner_handoff", "stage_id": f"{payload['run_id']}-handoff",
            "started_at": times[4], "completed_at": times[5],
            "input_artifact_id": contract["mission_contract_id"], "output_artifact_id": handoff["handoff_id"],
            "depends_on_stage_id": f"{payload['run_id']}-probe",
        },
        {
            "stage_type": "outcome_return", "stage_id": f"{payload['run_id']}-outcome",
            "started_at": times[6], "completed_at": times[7],
            "input_artifact_id": outcome["outcome_id"], "output_artifact_id": f"frontier-{payload['run_id']}",
            "depends_on_stage_id": f"{payload['run_id']}-handoff",
            "outcome_evidence_id": outcome["outcome_evidence_id"],
            "returned_to_mission_frontier": True,
        },
    ]
    runtime_cycle = {
        "runtime_cycle_id": f"cycle-{payload['run_id']}",
        "runtime_id": payload["runtime_id"],
        "mission_artifact_id": selected_id,
        "stages": stages,
        "concurrent_cycles_supported": False,
        "scaled_orchestration_claimed": False,
        "cycle_rationale": "Execute one vertical slice before broadening the runtime.",
    }
    manifest_report = validate_six_distinct_purpose_state_materialization(state_manifest)
    cycle_report = validate_single_serial_purpose_runtime_cycle(runtime_cycle)
    execution_errors = manifest_report["errors"] + cycle_report["errors"]
    return {
        "valid": not execution_errors,
        "errors": execution_errors,
        "state_manifest": state_manifest,
        "runtime_cycle": runtime_cycle,
        "selected_mission_id": selected_id,
        "frontier_update": {
            "frontier_id": f"frontier-{payload['run_id']}",
            "mission_contract_id": contract["mission_contract_id"],
            "outcome_evidence_id": outcome["outcome_evidence_id"],
            "observed_result": outcome["observed_result"],
        },
    }

def validate_signal_to_mission_engine_thesis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Integrate the verified operational identity of Palamedes without overclaiming."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["signal to mission engine thesis must be an object"]}
    for field in (
        "engine_thesis_id",
        "versioned_mission_unit_id",
        "transformation_selection_id",
        "cognitive_separation_id",
        "autonomy_corrigibility_id",
        "anti_entrenchment_control_id",
        "planner_boundary_id",
        "state_manifest_id",
        "serial_runtime_cycle_id",
        "vertical_slice_run_id",
        "adversarial_comparison_case_id",
        "thesis_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected_operations = [
        "wake_on_value_relevant_deviation",
        "interpret_competing_causal_frames",
        "invent_independent_missions",
        "conduct_plural_value_tournament",
        "emit_versioned_mission_contract",
        "revise_purpose_from_outcomes",
    ]
    operations = payload.get("operational_sequence")
    if operations != expected_operations:
        errors.append("operational_sequence must define the six signal-to-mission operations in order")
    evidence = payload.get("operation_artifacts")
    if not isinstance(evidence, list) or len(evidence) != 6:
        errors.append("operation_artifacts must evidence every operational sequence step")
        evidence = []
    for index, record in enumerate(evidence):
        prefix = f"operation_artifacts[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if record.get("operation") != expected_operations[index]:
            errors.append(f"{prefix}.operation must align with operational_sequence")
        for field in ("artifact_id", "state_fingerprint"):
            if not _non_empty(record.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if payload.get("operational_identity") != "signal_to_mission_engine":
        errors.append("operational_identity must be signal_to_mission_engine")
    if payload.get("vertical_slice_status") != "executed":
        errors.append("vertical_slice_status must be executed")
    if payload.get("adversarial_comparison_status") != "specified_not_yet_observed":
        errors.append("adversarial_comparison_status must preserve the unobserved empirical boundary")
    for field in (
        "general_agent_company_proven",
        "production_runtime_proven",
        "business_success_proven",
        "empirical_outcome_advantage_proven",
    ):
        if payload.get(field) is not False:
            errors.append(f"{field} must be false")
    if payload.get("further_philosophy_before_contact_is_allowed") is not False:
        errors.append("further_philosophy_before_contact_is_allowed must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "operational_identity": payload.get("operational_identity"),
        "operation_count": len(operations) if isinstance(operations, list) else 0,
        "adversarial_comparison_status": payload.get("adversarial_comparison_status"),
    }

def validate_purpose_plan_semantic_separation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Keep observations, interpretations, missions, and execution plans semantically distinct."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["purpose plan semantic separation must be an object"]}
    for field in ("separation_manifest_id", "existing_plan_schema_version", "separation_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected_domains = {
        "observation": ("signal", False),
        "interpretation": ("meaning", False),
        "mission": ("purpose", False),
        "execution_plan": ("execution", True),
    }
    domains = payload.get("state_domains")
    if not isinstance(domains, list) or len(domains) != 4:
        errors.append("state_domains must contain observation, interpretation, mission, and execution_plan")
        domains = []
    domain_ids = set()
    namespaces = set()
    schemas = set()
    for index, domain in enumerate(domains):
        prefix = f"state_domains[{index}]"
        if not isinstance(domain, dict):
            errors.append(f"{prefix} must be an object")
            continue
        domain_id = domain.get("domain")
        domain_ids.add(domain_id)
        expected = expected_domains.get(domain_id)
        for field, seen in (("storage_namespace", namespaces), ("schema_id", schemas)):
            value = domain.get(field)
            if not _non_empty(value):
                errors.append(f"{prefix}.{field} must be a non-empty string")
            elif value in seen:
                errors.append(f"{prefix}.{field} must be unique")
            seen.add(value)
        if expected is None:
            errors.append(f"{prefix}.domain is not recognized")
            continue
        semantic_role, uses_plan = expected
        if domain.get("semantic_role") != semantic_role:
            errors.append(f"{prefix}.semantic_role must match the state domain")
        if domain.get("uses_existing_plan_object") is not uses_plan:
            errors.append(f"{prefix}.uses_existing_plan_object must match the state domain")
        if not _non_empty(domain.get("transition_authority_id")):
            errors.append(f"{prefix}.transition_authority_id must be a non-empty string")
    if domain_ids != set(expected_domains):
        errors.append("state_domains must cover all four semantic domains exactly once")
    links = payload.get("cross_domain_links")
    required_links = {
        ("observation", "interpretation"),
        ("interpretation", "mission"),
        ("mission", "execution_plan"),
        ("execution_plan", "mission"),
    }
    observed_links = set()
    if not isinstance(links, list) or len(links) != len(required_links):
        errors.append("cross_domain_links must contain the four required reference directions")
        links = []
    for index, link in enumerate(links):
        prefix = f"cross_domain_links[{index}]"
        if not isinstance(link, dict):
            errors.append(f"{prefix} must be an object")
            continue
        observed_links.add((link.get("from_domain"), link.get("to_domain")))
        if not _non_empty(link.get("reference_field")):
            errors.append(f"{prefix}.reference_field must be a non-empty string")
        if link.get("link_mode") != "identifier_only":
            errors.append(f"{prefix}.link_mode must be identifier_only")
        if link.get("payload_embedded") is not False:
            errors.append(f"{prefix}.payload_embedded must be false")
    if observed_links != required_links:
        errors.append("cross_domain_links must preserve the required semantic reference graph")
    if payload.get("purpose_state_embedded_in_plan") is not False:
        errors.append("purpose_state_embedded_in_plan must be false")
    if payload.get("plan_object_role") != "execution_coordination_only":
        errors.append("plan_object_role must be execution_coordination_only")
    return {
        "valid": not errors,
        "errors": errors,
        "domains": sorted(item for item in domain_ids if _non_empty(item)),
        "plan_object_role": payload.get("plan_object_role"),
    }

def validate_shared_kernel_lifecycle_adapter(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Reuse kernel lifecycle semantics while keeping domain-specific meaning."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["shared kernel lifecycle adapter must be an object"]}
    for field in (
        "adapter_manifest_id",
        "kernel_store_id",
        "shared_adapter_id",
        "adapter_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected_services = {
        "atomic_write",
        "fingerprint",
        "optimistic_conflict",
        "revision_append",
        "restore_by_revision",
        "provenance_metadata",
    }
    services = payload.get("shared_lifecycle_services")
    if (
        not isinstance(services, list)
        or set(services) != expected_services
        or len(services) != len(expected_services)
    ):
        errors.append("shared_lifecycle_services must expose all six kernel lifecycle services")
    expected_domains = {"observation", "interpretation", "mission", "execution_plan"}
    bindings = payload.get("domain_bindings")
    if not isinstance(bindings, list) or len(bindings) != 4:
        errors.append("domain_bindings must contain all four semantic domains")
        bindings = []
    domains = set()
    validators = set()
    for index, binding in enumerate(bindings):
        prefix = f"domain_bindings[{index}]"
        if not isinstance(binding, dict):
            errors.append(f"{prefix} must be an object")
            continue
        domain = binding.get("domain")
        domains.add(domain)
        if binding.get("lifecycle_adapter_id") != payload.get("shared_adapter_id"):
            errors.append(f"{prefix}.lifecycle_adapter_id must use the shared adapter")
        validator_id = binding.get("semantic_validator_id")
        if not _non_empty(validator_id):
            errors.append(f"{prefix}.semantic_validator_id must be a non-empty string")
        elif validator_id in validators:
            errors.append(f"{prefix}.semantic_validator_id must be domain-specific")
        validators.add(validator_id)
        if binding.get("implements_own_revision_store") is not False:
            errors.append(f"{prefix}.implements_own_revision_store must be false")
        if binding.get("implements_own_fingerprint") is not False:
            errors.append(f"{prefix}.implements_own_fingerprint must be false")
        if binding.get("implements_own_restore") is not False:
            errors.append(f"{prefix}.implements_own_restore must be false")
        if binding.get("implements_own_provenance") is not False:
            errors.append(f"{prefix}.implements_own_provenance must be false")
    if domains != expected_domains:
        errors.append("domain_bindings must cover all four semantic domains exactly once")
    if payload.get("independent_purpose_database_created") is not False:
        errors.append("independent_purpose_database_created must be false")
    if payload.get("untyped_plan_fields_used") is not False:
        errors.append("untyped_plan_fields_used must be false")
    if payload.get("kernel_semantics_are_authoritative") is not True:
        errors.append("kernel_semantics_are_authoritative must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "domains": sorted(item for item in domains if _non_empty(item)),
        "shared_service_count": len(services) if isinstance(services, list) else 0,
    }

def validate_typed_epistemic_revision_envelope(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Place typed purpose objects inside one kernel-governed revision envelope."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["typed epistemic revision envelope must be an object"]}
    for field in (
        "revision_envelope_id",
        "revision_id",
        "revision_fingerprint",
        "previous_revision_fingerprint",
        "created_at",
        "revision_source",
        "revision_reason",
        "provenance_record_id",
        "kernel_adapter_id",
        "envelope_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected_types = {
        "signal",
        "constitution",
        "interpretation",
        "mission_candidate",
        "tournament",
        "mission_contract",
    }
    entries = payload.get("typed_objects")
    if not isinstance(entries, list) or len(entries) != 6:
        errors.append("typed_objects must contain exactly the six purpose object types")
        entries = []
    object_types = set()
    object_ids = set()
    object_fingerprints = set()
    schema_ids = set()
    validator_ids = set()
    for index, entry in enumerate(entries):
        prefix = f"typed_objects[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{prefix} must be an object")
            continue
        object_types.add(entry.get("object_type"))
        for field, seen in (
            ("object_id", object_ids),
            ("object_fingerprint", object_fingerprints),
            ("schema_id", schema_ids),
            ("semantic_validator_id", validator_ids),
        ):
            value = entry.get(field)
            if not _non_empty(value):
                errors.append(f"{prefix}.{field} must be a non-empty string")
            elif value in seen:
                errors.append(f"{prefix}.{field} must be unique")
            seen.add(value)
        if not isinstance(entry.get("version"), int) or isinstance(entry.get("version"), bool) or entry.get("version") < 1:
            errors.append(f"{prefix}.version must be a positive integer")
        if not _non_empty(entry.get("payload_reference")):
            errors.append(f"{prefix}.payload_reference must be a non-empty string")
        if entry.get("revision_id") != payload.get("revision_id"):
            errors.append(f"{prefix}.revision_id must match the shared envelope revision")
        if entry.get("owns_lifecycle_metadata") is not False:
            errors.append(f"{prefix}.owns_lifecycle_metadata must be false")
    if object_types != expected_types:
        errors.append("typed_objects must cover all six purpose object types exactly once")
    if payload.get("revision_metadata_owned_by_envelope") is not True:
        errors.append("revision_metadata_owned_by_envelope must be true")
    if payload.get("provenance_owned_by_envelope") is not True:
        errors.append("provenance_owned_by_envelope must be true")
    if payload.get("independent_database_used") is not False:
        errors.append("independent_database_used must be false")
    if payload.get("untyped_plan_fields_used") is not False:
        errors.append("untyped_plan_fields_used must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "object_types": sorted(item for item in object_types if _non_empty(item)),
        "object_count": len(object_ids),
        "revision_id": payload.get("revision_id"),
    }

def validate_observational_signal_state(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Keep signal state observational and free of meaning, mission, or authority."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["observational signal state must be an object"]}
    for field in (
        "signal_id",
        "source_identity",
        "observation_method",
        "observation",
        "baseline",
        "deviation",
        "uncertainty_note",
        "source_incentives",
        "received_at",
        "signal_rationale",
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
    uncertainty = payload.get("uncertainty")
    if (
        not isinstance(uncertainty, (int, float))
        or isinstance(uncertainty, bool)
        or not 0 <= uncertainty <= 1
    ):
        errors.append("uncertainty must be between zero and one")
    if payload.get("sensitivity") not in {"public", "internal", "confidential", "restricted"}:
        errors.append("sensitivity is not recognized")
    for field in (
        "interprets_meaning",
        "contains_recommendation",
        "assigns_mission",
        "authorizes_action",
        "changes_constitution",
    ):
        if payload.get(field) is not False:
            errors.append(f"{field} must be false")
    if payload.get("epistemic_kind") != "observation":
        errors.append("epistemic_kind must be observation")
    return {
        "valid": not errors,
        "errors": errors,
        "signal_id": payload.get("signal_id"),
        "affected_entity_ids": sorted(affected) if isinstance(affected, list) else [],
        "uncertainty": uncertainty,
    }

def validate_structured_constitution_state(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Represent constitution as governed versioned clauses and outcome precedents."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["structured constitution state must be an object"]}
    for field in (
        "constitution_state_id",
        "constitution_fingerprint",
        "amendment_authority_id",
        "state_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    version = payload.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        errors.append("version must be a positive integer")
    previous = payload.get("previous_constitution_fingerprint")
    if version == 1 and previous not in ("", None):
        errors.append("version one must not reference a previous constitution fingerprint")
    if isinstance(version, int) and version > 1 and not _non_empty(previous):
        errors.append("version above one must reference a previous constitution fingerprint")
    clauses = payload.get("clauses")
    if not isinstance(clauses, list) or not clauses:
        errors.append("clauses must be a non-empty list")
        clauses = []
    clause_ids = set()
    conflict_map = {}
    referenced_precedents = set()
    for index, clause in enumerate(clauses):
        prefix = f"clauses[{index}]"
        if not isinstance(clause, dict):
            errors.append(f"{prefix} must be an object")
            continue
        clause_id = clause.get("clause_id")
        if not _non_empty(clause_id):
            errors.append(f"{prefix}.clause_id must be a non-empty string")
        elif clause_id in clause_ids:
            errors.append(f"{prefix}.clause_id must be unique")
        clause_ids.add(clause_id)
        if not isinstance(clause.get("version"), int) or isinstance(clause.get("version"), bool) or clause.get("version") < 1:
            errors.append(f"{prefix}.version must be a positive integer")
        if clause.get("kind") not in {"prohibition", "principle", "preference", "authority"}:
            errors.append(f"{prefix}.kind is not recognized")
        if not isinstance(clause.get("precedence"), int) or isinstance(clause.get("precedence"), bool) or clause.get("precedence") < 0:
            errors.append(f"{prefix}.precedence must be a non-negative integer")
        for field in ("clause", "scope", "authority_source_id"):
            if not _non_empty(clause.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        conflicts = clause.get("conflict_clause_ids")
        if not isinstance(conflicts, list) or len(conflicts) != len(set(conflicts)):
            errors.append(f"{prefix}.conflict_clause_ids must be a unique list")
            conflicts = []
        conflict_map[clause_id] = set(conflicts)
        precedents = clause.get("outcome_precedent_ids")
        if not isinstance(precedents, list) or len(precedents) != len(set(precedents)):
            errors.append(f"{prefix}.outcome_precedent_ids must be a unique list")
            precedents = []
        referenced_precedents.update(precedents)
    for clause_id, conflicts in conflict_map.items():
        if clause_id in conflicts or not conflicts.issubset(clause_ids):
            errors.append(f"clause {clause_id} conflicts must reference other known clauses")
        for conflict_id in conflicts & clause_ids:
            if clause_id not in conflict_map.get(conflict_id, set()):
                errors.append(f"clause conflict between {clause_id} and {conflict_id} must be reciprocal")
    precedents = payload.get("outcome_precedents")
    if not isinstance(precedents, list):
        errors.append("outcome_precedents must be a list")
        precedents = []
    precedent_ids = set()
    for index, precedent in enumerate(precedents):
        prefix = f"outcome_precedents[{index}]"
        if not isinstance(precedent, dict):
            errors.append(f"{prefix} must be an object")
            continue
        precedent_id = precedent.get("precedent_id")
        if not _non_empty(precedent_id):
            errors.append(f"{prefix}.precedent_id must be a non-empty string")
        elif precedent_id in precedent_ids:
            errors.append(f"{prefix}.precedent_id must be unique")
        precedent_ids.add(precedent_id)
        for field in ("outcome_evidence_id", "finding", "interpretation_boundary", "recorded_at"):
            if not _non_empty(precedent.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if precedent.get("clause_id") not in clause_ids:
            errors.append(f"{prefix}.clause_id must reference a known clause")
    if referenced_precedents != precedent_ids:
        errors.append("clause outcome_precedent_ids and outcome_precedents must reference each other exactly")
    if payload.get("constitution_is_single_editable_prompt") is not False:
        errors.append("constitution_is_single_editable_prompt must be false")
    if payload.get("amendments_require_authority") is not True:
        errors.append("amendments_require_authority must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "clause_ids": sorted(item for item in clause_ids if _non_empty(item)),
        "precedent_ids": sorted(item for item in precedent_ids if _non_empty(item)),
        "version": version,
    }

def validate_separated_causal_sketch(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Structure falsifiable causal claims while separating normative assumptions."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["separated causal sketch must be an object"]}
    for field in ("causal_sketch_id", "interpretation_id", "sketch_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    assumptions = payload.get("normative_assumptions")
    if not isinstance(assumptions, list) or not assumptions:
        errors.append("normative_assumptions must be a non-empty list")
        assumptions = []
    assumption_ids = set()
    for index, assumption in enumerate(assumptions):
        prefix = f"normative_assumptions[{index}]"
        if not isinstance(assumption, dict):
            errors.append(f"{prefix} must be an object")
            continue
        assumption_id = assumption.get("assumption_id")
        if not _non_empty(assumption_id):
            errors.append(f"{prefix}.assumption_id must be a non-empty string")
        elif assumption_id in assumption_ids:
            errors.append(f"{prefix}.assumption_id must be unique")
        assumption_ids.add(assumption_id)
        for field in ("assumption", "constitution_clause_id", "effect_if_changed"):
            if not _non_empty(assumption.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")

    claims = payload.get("claims")
    if not isinstance(claims, list) or len(claims) < 2:
        errors.append("claims must contain at least two empirical causal nodes")
        claims = []
    claim_ids = set()
    for index, claim in enumerate(claims):
        prefix = f"claims[{index}]"
        if not isinstance(claim, dict):
            errors.append(f"{prefix} must be an object")
            continue
        claim_id = claim.get("claim_id")
        if not _non_empty(claim_id):
            errors.append(f"{prefix}.claim_id must be a non-empty string")
        elif claim_id in claim_ids:
            errors.append(f"{prefix}.claim_id must be unique")
        claim_ids.add(claim_id)
        if claim.get("epistemic_kind") != "empirical":
            errors.append(f"{prefix}.epistemic_kind must be empirical")
        for field in ("claim", "measurement"):
            if not _non_empty(claim.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        refs = claim.get("normative_assumption_ids")
        if (
            not isinstance(refs, list)
            or not refs
            or not set(refs).issubset(assumption_ids)
            or len(refs) != len(set(refs))
        ):
            errors.append(f"{prefix}.normative_assumption_ids must reference separate known assumptions")

    edges = payload.get("edges")
    if not isinstance(edges, list) or not edges:
        errors.append("edges must be a non-empty list")
        edges = []
    edge_ids = set()
    for index, edge in enumerate(edges):
        prefix = f"edges[{index}]"
        if not isinstance(edge, dict):
            errors.append(f"{prefix} must be an object")
            continue
        edge_id = edge.get("edge_id")
        if not _non_empty(edge_id):
            errors.append(f"{prefix}.edge_id must be a non-empty string")
        elif edge_id in edge_ids:
            errors.append(f"{prefix}.edge_id must be unique")
        edge_ids.add(edge_id)
        if (
            edge.get("source_claim_id") not in claim_ids
            or edge.get("target_claim_id") not in claim_ids
            or edge.get("source_claim_id") == edge.get("target_claim_id")
        ):
            errors.append(f"{prefix} must connect two different known claims")
        for field in ("mechanism", "surprise_condition"):
            if not _non_empty(edge.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        confidence = edge.get("confidence")
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
            errors.append(f"{prefix}.confidence must be between zero and one")
        for field in ("supporting_signal_ids", "opposing_signal_ids"):
            values = edge.get(field)
            if (
                not isinstance(values, list)
                or not values
                or not all(_non_empty(item) for item in values)
                or len(values) != len(set(values))
            ):
                errors.append(f"{prefix}.{field} must be a non-empty unique signal list")

    predictions = payload.get("predictions")
    if not isinstance(predictions, list) or not predictions:
        errors.append("predictions must be a non-empty list")
        predictions = []
    prediction_ids = set()
    for index, prediction in enumerate(predictions):
        prefix = f"predictions[{index}]"
        if not isinstance(prediction, dict):
            errors.append(f"{prefix} must be an object")
            continue
        prediction_id = prediction.get("prediction_id")
        if not _non_empty(prediction_id):
            errors.append(f"{prefix}.prediction_id must be a non-empty string")
        elif prediction_id in prediction_ids:
            errors.append(f"{prefix}.prediction_id must be unique")
        prediction_ids.add(prediction_id)
        if prediction.get("claim_id") not in claim_ids:
            errors.append(f"{prefix}.claim_id must reference a known claim")
        for field in ("condition", "expected_observation", "time_horizon", "surprise_condition"):
            if not _non_empty(prediction.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if payload.get("normative_assumptions_embedded_as_causal_facts") is not False:
        errors.append("normative_assumptions_embedded_as_causal_facts must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "claim_ids": sorted(item for item in claim_ids if _non_empty(item)),
        "edge_count": len(edge_ids),
        "prediction_count": len(prediction_ids),
        "normative_assumption_ids": sorted(item for item in assumption_ids if _non_empty(item)),
    }

def validate_complete_mission_candidate_basis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Require every mission candidate to expose its complete decision basis."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["complete mission candidate basis must be an object"]}
    for field in (
        "mission_candidate_id",
        "mission",
        "changed_external_condition",
        "causal_sketch_id",
        "candidate_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    beneficiary = payload.get("beneficiary_condition")
    if not isinstance(beneficiary, dict):
        errors.append("beneficiary_condition must be an object")
        beneficiary = {}
    for field in (
        "beneficiary_condition_id",
        "beneficiary_population",
        "current_external_condition",
        "desired_external_condition",
        "condition_evidence_id",
    ):
        if not _non_empty(beneficiary.get(field)):
            errors.append(f"beneficiary_condition.{field} must be a non-empty string")
    if beneficiary.get("desired_external_condition") != payload.get("changed_external_condition"):
        errors.append("beneficiary desired_external_condition must match changed_external_condition")

    interpretation = payload.get("constitutional_interpretation")
    if not isinstance(interpretation, dict):
        errors.append("constitutional_interpretation must be an object")
        interpretation = {}
    for field in ("interpretation_id", "constitution_state_id", "interpretation"):
        if not _non_empty(interpretation.get(field)):
            errors.append(f"constitutional_interpretation.{field} must be a non-empty string")
    clauses = interpretation.get("clause_ids")
    if (
        not isinstance(clauses, list)
        or not clauses
        or not all(_non_empty(item) for item in clauses)
        or len(clauses) != len(set(clauses))
    ):
        errors.append("constitutional_interpretation.clause_ids must be a non-empty unique string list")

    resource = payload.get("resource_thesis")
    if not isinstance(resource, dict):
        errors.append("resource_thesis must be an object")
        resource = {}
    for field in (
        "resource_thesis_id",
        "resource_source",
        "renewal_mechanism",
        "resource_evidence_id",
        "resource_failure_condition",
    ):
        if not _non_empty(resource.get(field)):
            errors.append(f"resource_thesis.{field} must be a non-empty string")

    harm_model = payload.get("harm_model")
    if not isinstance(harm_model, dict):
        errors.append("harm_model must be an object")
        harm_model = {}
    if not _non_empty(harm_model.get("harm_model_id")):
        errors.append("harm_model.harm_model_id must be a non-empty string")
    harms = harm_model.get("harms")
    if not isinstance(harms, list) or not harms:
        errors.append("harm_model.harms must be a non-empty list")
        harms = []
    harm_ids = set()
    for index, harm in enumerate(harms):
        prefix = f"harm_model.harms[{index}]"
        if not isinstance(harm, dict):
            errors.append(f"{prefix} must be an object")
            continue
        harm_id = harm.get("harm_id")
        if not _non_empty(harm_id):
            errors.append(f"{prefix}.harm_id must be a non-empty string")
        elif harm_id in harm_ids:
            errors.append(f"{prefix}.harm_id must be unique")
        harm_ids.add(harm_id)
        for field in ("affected_population", "potential_harm", "detection_signal_id", "harm_threshold", "mitigation"):
            if not _non_empty(harm.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")

    disconfirmation = payload.get("disconfirmation")
    if not isinstance(disconfirmation, dict):
        errors.append("disconfirmation must be an object")
        disconfirmation = {}
    for field in (
        "disconfirmation_id",
        "condition",
        "required_observation",
        "evidence_channel_id",
        "evaluation_deadline",
        "decision_if_met",
    ):
        if not _non_empty(disconfirmation.get(field)):
            errors.append(f"disconfirmation.{field} must be a non-empty string")
    if disconfirmation.get("decision_if_met") not in {"revise", "stop", "replace"}:
        errors.append("disconfirmation.decision_if_met must be revise, stop, or replace")
    if payload.get("candidate_can_self_authorize") is not False:
        errors.append("candidate_can_self_authorize must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "mission_candidate_id": payload.get("mission_candidate_id"),
        "harm_ids": sorted(item for item in harm_ids if _non_empty(item)),
        "constitutional_clause_ids": sorted(clauses) if isinstance(clauses, list) else [],
    }

def validate_reconstructable_mission_tournament(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Preserve the complete comparison landscape and unresolved assumptions."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["reconstructable mission tournament must be an object"]}
    for field in ("mission_tournament_id", "constitution_state_id", "selected_mission_id", "selection_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    candidates = payload.get("candidate_ids")
    if (
        not isinstance(candidates, list)
        or len(candidates) < 3
        or not all(_non_empty(item) for item in candidates)
        or len(candidates) != len(set(candidates))
    ):
        errors.append("candidate_ids must contain at least three unique missions")
        candidates = []
    candidate_ids = set(candidates)
    if payload.get("selected_mission_id") not in candidate_ids:
        errors.append("selected_mission_id must reference a tournament candidate")
    expected_pairs = {
        frozenset((left, right))
        for index, left in enumerate(candidates)
        for right in candidates[index + 1 :]
    }
    comparisons = payload.get("pairwise_comparisons")
    if not isinstance(comparisons, list) or len(comparisons) != len(expected_pairs):
        errors.append("pairwise_comparisons must cover every candidate pair exactly once")
        comparisons = []
    observed_pairs = set()
    comparison_ids = set()
    for index, comparison in enumerate(comparisons):
        prefix = f"pairwise_comparisons[{index}]"
        if not isinstance(comparison, dict):
            errors.append(f"{prefix} must be an object")
            continue
        comparison_id = comparison.get("comparison_id")
        if not _non_empty(comparison_id):
            errors.append(f"{prefix}.comparison_id must be a non-empty string")
        elif comparison_id in comparison_ids:
            errors.append(f"{prefix}.comparison_id must be unique")
        comparison_ids.add(comparison_id)
        left = comparison.get("left_candidate_id")
        right = comparison.get("right_candidate_id")
        pair = frozenset((left, right))
        if left not in candidate_ids or right not in candidate_ids or left == right:
            errors.append(f"{prefix} must compare two different known candidates")
        elif pair in observed_pairs:
            errors.append(f"{prefix} candidate pair must be unique")
        observed_pairs.add(pair)
        for field in (
            "consequence_comparison",
            "causal_coherence_comparison",
            "constitutional_fit_comparison",
            "resource_comparison",
            "harm_comparison",
            "novelty_comparison",
            "comparison_rationale",
        ):
            if not _non_empty(comparison.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        preferred = comparison.get("preferred_candidate_id")
        if preferred not in {left, right, "unresolved"}:
            errors.append(f"{prefix}.preferred_candidate_id must be one candidate or unresolved")
    if observed_pairs != expected_pairs:
        errors.append("pairwise_comparisons must preserve the complete option landscape")

    assumptions = payload.get("unresolved_assumptions")
    if not isinstance(assumptions, list) or not assumptions:
        errors.append("unresolved_assumptions must be a non-empty list")
        assumptions = []
    assumption_ids = set()
    for index, assumption in enumerate(assumptions):
        prefix = f"unresolved_assumptions[{index}]"
        if not isinstance(assumption, dict):
            errors.append(f"{prefix} must be an object")
            continue
        assumption_id = assumption.get("assumption_id")
        if not _non_empty(assumption_id):
            errors.append(f"{prefix}.assumption_id must be a non-empty string")
        elif assumption_id in assumption_ids:
            errors.append(f"{prefix}.assumption_id must be unique")
        assumption_ids.add(assumption_id)
        for field in ("assumption", "evidence_needed", "wake_trigger", "reversal_effect"):
            if not _non_empty(assumption.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        affected = assumption.get("affected_candidate_ids")
        if (
            not isinstance(affected, list)
            or len(affected) < 2
            or not set(affected).issubset(candidate_ids)
            or len(affected) != len(set(affected))
        ):
            errors.append(f"{prefix}.affected_candidate_ids must reference at least two tournament candidates")
    if payload.get("discarded_candidates_preserved") is not True:
        errors.append("discarded_candidates_preserved must be true")
    if payload.get("winner_only_record") is not False:
        errors.append("winner_only_record must be false")
    if payload.get("future_reversal_reconstructable") is not True:
        errors.append("future_reversal_reconstructable must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "candidate_ids": sorted(candidate_ids),
        "comparison_count": len(comparison_ids),
        "unresolved_assumption_ids": sorted(item for item in assumption_ids if _non_empty(item)),
    }

def validate_immutable_mission_contract_successor(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create a successor contract and notify every planner dependent on its predecessor."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["immutable mission contract successor must be an object"]}
    for field in (
        "revision_record_id",
        "revision_evidence_id",
        "revision_reason",
        "revision_authority_id",
        "revision_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    predecessor = payload.get("predecessor_contract")
    successor = payload.get("successor_contract")
    if not isinstance(predecessor, dict):
        errors.append("predecessor_contract must be an object")
        predecessor = {}
    if not isinstance(successor, dict):
        errors.append("successor_contract must be an object")
        successor = {}
    for label, contract in (("predecessor_contract", predecessor), ("successor_contract", successor)):
        for field in ("mission_contract_id", "mission_id", "contract_fingerprint", "created_at"):
            if not _non_empty(contract.get(field)):
                errors.append(f"{label}.{field} must be a non-empty string")
        if not isinstance(contract.get("version"), int) or isinstance(contract.get("version"), bool) or contract.get("version") < 1:
            errors.append(f"{label}.version must be a positive integer")
    if successor.get("mission_contract_id") == predecessor.get("mission_contract_id"):
        errors.append("successor must have a new mission_contract_id")
    if successor.get("contract_fingerprint") == predecessor.get("contract_fingerprint"):
        errors.append("successor must have a new contract_fingerprint")
    if (
        isinstance(successor.get("version"), int)
        and isinstance(predecessor.get("version"), int)
        and successor["version"] != predecessor["version"] + 1
    ):
        errors.append("successor version must increment predecessor version by one")
    if successor.get("previous_contract_id") != predecessor.get("mission_contract_id"):
        errors.append("successor.previous_contract_id must reference predecessor")
    if successor.get("previous_contract_fingerprint") != predecessor.get("contract_fingerprint"):
        errors.append("successor.previous_contract_fingerprint must match predecessor")
    changed = successor.get("changed_fields")
    if (
        not isinstance(changed, list)
        or not changed
        or not all(_non_empty(item) for item in changed)
        or len(changed) != len(set(changed))
    ):
        errors.append("successor.changed_fields must be a non-empty unique string list")
    if predecessor.get("mutated_in_place") is not False:
        errors.append("predecessor_contract.mutated_in_place must be false")
    if payload.get("revision_performed_in_place") is not False:
        errors.append("revision_performed_in_place must be false")

    dependencies = payload.get("dependent_planner_work")
    if not isinstance(dependencies, list) or not dependencies:
        errors.append("dependent_planner_work must be a non-empty list")
        dependencies = []
    dependency_ids = set()
    for index, dependency in enumerate(dependencies):
        prefix = f"dependent_planner_work[{index}]"
        if not isinstance(dependency, dict):
            errors.append(f"{prefix} must be an object")
            continue
        dependency_id = dependency.get("dependency_id")
        if not _non_empty(dependency_id):
            errors.append(f"{prefix}.dependency_id must be a non-empty string")
        elif dependency_id in dependency_ids:
            errors.append(f"{prefix}.dependency_id must be unique")
        dependency_ids.add(dependency_id)
        for field in ("planner_id", "work_artifact_id"):
            if not _non_empty(dependency.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if dependency.get("mission_contract_id") != predecessor.get("mission_contract_id"):
            errors.append(f"{prefix}.mission_contract_id must reference predecessor")
    notifications = payload.get("planner_notifications")
    if not isinstance(notifications, list) or len(notifications) != len(dependency_ids):
        errors.append("planner_notifications must notify every dependent work item exactly once")
        notifications = []
    notified_dependencies = set()
    for index, notification in enumerate(notifications):
        prefix = f"planner_notifications[{index}]"
        if not isinstance(notification, dict):
            errors.append(f"{prefix} must be an object")
            continue
        dependency_id = notification.get("dependency_id")
        if dependency_id in notified_dependencies:
            errors.append(f"{prefix}.dependency_id must be unique")
        notified_dependencies.add(dependency_id)
        for field in ("notification_id", "planner_id", "notified_at", "successor_contract_id"):
            if not _non_empty(notification.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if notification.get("successor_contract_id") != successor.get("mission_contract_id"):
            errors.append(f"{prefix}.successor_contract_id must reference successor")
        if notification.get("dependency_status") not in {"review_required", "invalidated"}:
            errors.append(f"{prefix}.dependency_status must be review_required or invalidated")
    if notified_dependencies != dependency_ids:
        errors.append("planner_notifications must cover exactly all dependent planner work")
    if payload.get("successor_activation_status") != "active_after_notifications":
        errors.append("successor_activation_status must be active_after_notifications")
    return {
        "valid": not errors,
        "errors": errors,
        "predecessor_contract_id": predecessor.get("mission_contract_id"),
        "successor_contract_id": successor.get("mission_contract_id"),
        "notified_dependency_ids": sorted(item for item in notified_dependencies if _non_empty(item)),
    }

def validate_typed_linked_object_state_thesis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Integrate typed purpose objects on one revision kernel with preserved boundaries."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["typed linked object state thesis must be an object"]}
    for field in (
        "state_thesis_id",
        "semantic_separation_manifest_id",
        "kernel_lifecycle_adapter_id",
        "revision_envelope_id",
        "signal_schema_id",
        "constitution_schema_id",
        "causal_sketch_schema_id",
        "mission_candidate_schema_id",
        "mission_tournament_schema_id",
        "mission_contract_revision_schema_id",
        "thesis_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected_boundaries = [
        ("observation", "interpretation"),
        ("interpretation", "mission_candidate"),
        ("mission_candidate", "mission_tournament"),
        ("mission_tournament", "mission_contract"),
        ("mission_contract", "execution_plan"),
        ("execution_plan", "outcome_return"),
        ("outcome_return", "observation"),
    ]
    links = payload.get("typed_links")
    if not isinstance(links, list) or len(links) != len(expected_boundaries):
        errors.append("typed_links must contain the complete forward and outcome-return boundary cycle")
        links = []
    observed_boundaries = []
    link_ids = set()
    for index, link in enumerate(links):
        prefix = f"typed_links[{index}]"
        if not isinstance(link, dict):
            errors.append(f"{prefix} must be an object")
            continue
        link_id = link.get("link_id")
        if not _non_empty(link_id):
            errors.append(f"{prefix}.link_id must be a non-empty string")
        elif link_id in link_ids:
            errors.append(f"{prefix}.link_id must be unique")
        link_ids.add(link_id)
        boundary = (link.get("from_type"), link.get("to_type"))
        observed_boundaries.append(boundary)
        for field in ("from_object_id", "to_object_id", "link_semantics"):
            if not _non_empty(link.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        if link.get("reference_mode") != "typed_identifier":
            errors.append(f"{prefix}.reference_mode must be typed_identifier")
        if link.get("payload_ownership_transferred") is not False:
            errors.append(f"{prefix}.payload_ownership_transferred must be false")
        if link.get("authority_transferred") is not False:
            errors.append(f"{prefix}.authority_transferred must be false")
    if observed_boundaries != expected_boundaries:
        errors.append("typed_links must preserve observation, interpretation, selection, contract, plan, and outcome order")
    guarantees = {
        "observation_remains_descriptive",
        "interpretation_remains_revisable",
        "selection_landscape_remains_reconstructable",
        "mission_contract_versions_remain_immutable",
        "downstream_plan_owns_only_implementation",
        "outcomes_return_as_evidence_not_authority",
        "shared_revision_conflict_restore_provenance",
    }
    for guarantee in sorted(guarantees):
        if payload.get(guarantee) is not True:
            errors.append(f"{guarantee} must be true")
    if payload.get("independent_state_universe_created") is not False:
        errors.append("independent_state_universe_created must be false")
    if payload.get("semantic_objects_collapsed_into_plan") is not False:
        errors.append("semantic_objects_collapsed_into_plan must be false")
    if payload.get("state_thesis_decision") != "integrated":
        errors.append("state_thesis_decision must be integrated")
    return {
        "valid": not errors,
        "errors": errors,
        "typed_link_count": len(link_ids),
        "verified_guarantee_count": sum(payload.get(item) is True for item in guarantees),
        "state_thesis_decision": payload.get("state_thesis_decision"),
    }

def validate_intent_specific_command_registry(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Replace generic object creation with semantically validated commands."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["intent specific command registry must be an object"]}
    for field in ("command_registry_id", "revision_envelope_adapter_id", "registry_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    expected_commands = {
        "record_signal": ("signal_input", "signal", "validate_observational_signal_state"),
        "amend_constitution": ("constitution_amendment_input", "constitution", "validate_structured_constitution_state"),
        "record_causal_sketch": ("causal_sketch_input", "interpretation", "validate_separated_causal_sketch"),
        "propose_mission_candidate": ("mission_candidate_input", "mission_candidate", "validate_complete_mission_candidate_basis"),
        "conduct_mission_tournament": ("mission_tournament_input", "tournament", "validate_reconstructable_mission_tournament"),
        "issue_mission_contract": ("mission_contract_input", "mission_contract", "validate_mission_contract_thesis_integration"),
        "revise_mission_contract": ("mission_contract_revision_input", "mission_contract", "validate_immutable_mission_contract_successor"),
        "return_outcome": ("outcome_return_input", "outcome_return", "validate_direct_outcome_reporting_integrity"),
    }
    commands = payload.get("commands")
    if not isinstance(commands, list) or len(commands) != len(expected_commands):
        errors.append("commands must contain exactly the eight intent-specific state transitions")
        commands = []
    command_names = set()
    validators = set()
    for index, command in enumerate(commands):
        prefix = f"commands[{index}]"
        if not isinstance(command, dict):
            errors.append(f"{prefix} must be an object")
            continue
        name = command.get("command")
        command_names.add(name)
        expected = expected_commands.get(name)
        if expected is None:
            errors.append(f"{prefix}.command is not recognized")
            continue
        input_type, output_type, validator = expected
        if command.get("input_type") != input_type:
            errors.append(f"{prefix}.input_type must match the command")
        if command.get("output_type") != output_type:
            errors.append(f"{prefix}.output_type must match the command")
        if command.get("semantic_validator_id") != validator:
            errors.append(f"{prefix}.semantic_validator_id must match the command")
        validators.add(command.get("semantic_validator_id"))
        for field in ("intent", "required_authority_id", "revision_reason_field"):
            if not _non_empty(command.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        side_effects = command.get("allowed_side_effects")
        if (
            not isinstance(side_effects, list)
            or set(side_effects) != {"append_revision", "append_provenance"}
            or len(side_effects) != 2
        ):
            errors.append(f"{prefix}.allowed_side_effects must contain only revision and provenance append")
        if command.get("may_create_arbitrary_type") is not False:
            errors.append(f"{prefix}.may_create_arbitrary_type must be false")
    if command_names != set(expected_commands):
        errors.append("commands must cover all eight intent-specific transitions exactly once")
    if len(validators) != len(expected_commands):
        errors.append("each command must have its own semantic validator")
    if payload.get("generic_create_object_exposed") is not False:
        errors.append("generic_create_object_exposed must be false")
    if payload.get("unknown_command_rejected") is not True:
        errors.append("unknown_command_rejected must be true")
    if payload.get("validation_precedes_revision") is not True:
        errors.append("validation_precedes_revision must be true")
    return {
        "valid": not errors,
        "errors": errors,
        "commands": sorted(item for item in command_names if _non_empty(item)),
        "command_count": len(command_names),
    }

def validate_record_signal_command(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and record signal provenance without interpreting or waking."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["record signal command must be an object"]}
    for field in (
        "command_id",
        "expected_revision_fingerprint",
        "authority_id",
        "revision_reason",
        "command_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    signal = payload.get("signal")
    signal_report = validate_observational_signal_state(signal)
    if not signal_report["valid"]:
        errors.extend(f"signal: {error}" for error in signal_report["errors"])
    result = payload.get("record_result")
    if not isinstance(result, dict):
        errors.append("record_result must be an object")
        result = {}
    for field in (
        "revision_id",
        "revision_fingerprint",
        "provenance_record_id",
        "signal_object_fingerprint",
        "recorded_at",
    ):
        if not _non_empty(result.get(field)):
            errors.append(f"record_result.{field} must be a non-empty string")
    if result.get("signal_id") != signal_report.get("signal_id"):
        errors.append("record_result.signal_id must match the validated signal")
    if result.get("write_status") != "recorded":
        errors.append("record_result.write_status must be recorded")
    if result.get("semantic_validator_id") != "validate_observational_signal_state":
        errors.append("record_result.semantic_validator_id must be validate_observational_signal_state")
    for field in (
        "meaning_inferred",
        "wake_evaluated",
        "agent_woken",
        "mission_created",
        "constitution_changed",
    ):
        if result.get(field) is not False:
            errors.append(f"record_result.{field} must be false")
    if result.get("wake_event_id") not in ("", None):
        errors.append("record_result.wake_event_id must be empty")
    if result.get("interpretation_id") not in ("", None):
        errors.append("record_result.interpretation_id must be empty")
    if result.get("implicit_side_effects") != []:
        errors.append("record_result.implicit_side_effects must be empty")
    provenance = result.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("record_result.provenance must be an object")
        provenance = {}
    for field in ("source_identity", "observation_method", "received_at"):
        signal_value = signal.get(field) if isinstance(signal, dict) else None
        if provenance.get(field) != signal_value or not _non_empty(provenance.get(field)):
            errors.append(f"record_result.provenance.{field} must preserve the validated signal value")
    return {
        "valid": not errors,
        "errors": errors,
        "signal_id": signal_report.get("signal_id"),
        "write_status": result.get("write_status"),
        "wake_evaluated": result.get("wake_evaluated"),
    }

