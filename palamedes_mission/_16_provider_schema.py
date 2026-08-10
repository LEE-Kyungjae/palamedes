from __future__ import annotations

from typing import Any, Dict, List
from ._01_kinds_value import _non_empty, authorize_live_provider_experiment, build_five_bounded_artifact_conclusion, build_mission_schema_validator_bundle, compile_planner_envelope_and_measure_acknowledgment_loss, inspect_one_case_before_generalization, run_evolving_adversarial_signal_replay, run_semantic_command_sequence, run_static_fixture_mission_cycle


def validate_mission_schema_validator_bundle(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Verify the first deployable artifact is a complete bounded contract bundle."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["mission schema validator bundle report must be an object"]}
    for field in ("bundle_report_id", "report_fingerprint", "report_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    bundle = payload.get("bundle")
    if not isinstance(bundle, dict):
        errors.append("bundle must be an object")
        bundle = {}
    expected = build_mission_schema_validator_bundle()
    if bundle != expected:
        errors.append("bundle must match verified mission schemas and validator symbols")
    required_domains = {
        "signal",
        "constitution",
        "causal_sketches",
        "mission_candidates",
        "tournament",
        "selected_mission",
        "outcome_return",
    }
    artifacts = bundle.get("artifacts", [])
    seen = set()
    if not isinstance(artifacts, list) or len(artifacts) != len(required_domains):
        errors.append("artifacts must contain exactly seven mission contract domains")
        artifacts = []
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            errors.append(f"artifacts[{index}] must be an object")
            continue
        domain = artifact.get("domain")
        if domain not in required_domains:
            errors.append(f"artifacts[{index}].domain is not recognized")
        elif domain in seen:
            errors.append(f"artifacts[{index}].domain must be unique")
        seen.add(domain)
        if artifact.get("schema_present") is not True:
            errors.append(f"artifacts[{index}] schema must exist")
        if artifact.get("validator_present") is not True:
            errors.append(f"artifacts[{index}] validator must exist")
    if seen != required_domains:
        errors.append("artifacts must cover every mission contract domain")
    if bundle.get("artifact_kind") != "schemas_and_validators":
        errors.append("artifact_kind must be schemas_and_validators")
    for field in (
        "autonomous_daemon_included",
        "scheduler_included",
        "external_action_authority_included",
        "background_loop_included",
    ):
        if bundle.get(field) is not False:
            errors.append(f"{field} must be false")
    return {
        "valid": not errors,
        "errors": errors,
        "artifact_count": len(artifacts),
        "covered_domains": sorted(seen),
        "all_contracts_verified": all(
            isinstance(item, dict)
            and item.get("schema_present") is True
            and item.get("validator_present") is True
            for item in artifacts
        ),
    }

def validate_semantic_command_freeze_lineage(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Verify the seven command surfaces enforce freeze and cognition lineage."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["semantic command lineage report must be an object"]}
    for field in ("command_report_id", "report_fingerprint", "report_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    commands = payload.get("commands")
    final_state = payload.get("final_state")
    if not isinstance(commands, list) or not isinstance(final_state, dict):
        errors.append("commands must be an array and final_state must be an object")
        commands = commands if isinstance(commands, list) else []
        final_state = final_state if isinstance(final_state, dict) else {}
    try:
        expected = run_semantic_command_sequence(commands)
    except (TypeError, ValueError) as exc:
        errors.append(f"semantic command sequence failed: {exc}")
        expected = {}
    if final_state != expected:
        errors.append("final_state must equal deterministic semantic command sequence")
    command_types = [
        item.get("command_type")
        for item in final_state.get("command_log", [])
        if isinstance(item, dict)
    ]
    if command_types != [
        "signal",
        "constitution",
        "sketches",
        "candidates",
        "tournament",
        "contract",
        "outcome",
    ]:
        errors.append("command log must cover the seven semantic surfaces in cognition order")
    if final_state.get("all_artifacts_frozen") is not True:
        errors.append("all semantic artifacts must be frozen")
    if final_state.get("execution_commands_emitted") != 0:
        errors.append("semantic command surface must emit zero execution commands")
    return {
        "valid": not errors,
        "errors": errors,
        "command_count": len(command_types),
        "artifact_count": len(final_state.get("artifacts", [])),
        "all_artifacts_frozen": final_state.get("all_artifacts_frozen"),
        "execution_commands_emitted": final_state.get("execution_commands_emitted"),
    }

def validate_provider_neutral_fixture_first_mission_cycle(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Verify MissionCycle is deterministic, provider-neutral, and fixture-first."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["fixture-first MissionCycle report must be an object"]}
    for field in ("mission_cycle_report_id", "report_fingerprint", "report_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    fixture_commands = payload.get("fixture_commands")
    cycle_output = payload.get("cycle_output")
    if not isinstance(fixture_commands, list) or not isinstance(cycle_output, dict):
        errors.append("fixture_commands must be an array and cycle_output must be an object")
        fixture_commands = fixture_commands if isinstance(fixture_commands, list) else []
        cycle_output = cycle_output if isinstance(cycle_output, dict) else {}
    try:
        first = run_static_fixture_mission_cycle(fixture_commands)
        second = run_static_fixture_mission_cycle(fixture_commands)
    except (TypeError, ValueError) as exc:
        errors.append(f"static fixture MissionCycle failed: {exc}")
        first = {}
        second = {}
    if cycle_output != first:
        errors.append("cycle_output must equal static fixture MissionCycle output")
    if first != second:
        errors.append("static fixture MissionCycle replay must be deterministic")
    metadata = cycle_output.get("mission_cycle_metadata", {})
    if metadata.get("orchestrator") != "MissionCycle":
        errors.append("orchestrator must be MissionCycle")
    if metadata.get("provider_kind") != "static_fixture":
        errors.append("first provider must be static_fixture")
    if metadata.get("provider_interface") != "generate(command_type, context)":
        errors.append("provider interface must remain neutral")
    if metadata.get("live_provider_explicitly_allowed") is not False:
        errors.append("live provider must not be allowed in fixture-first proof")
    if metadata.get("live_model_call_count") != 0:
        errors.append("fixture-first proof must make zero live model calls")
    if metadata.get("provider_specific_branch_count") != 0:
        errors.append("MissionCycle must contain no provider-specific branch")
    return {
        "valid": not errors,
        "errors": errors,
        "artifact_count": len(cycle_output.get("artifacts", [])),
        "provider_kind": metadata.get("provider_kind", ""),
        "live_model_call_count": metadata.get("live_model_call_count"),
        "deterministic_replay": first == second,
    }

def validate_evolving_adversarial_signal_replay(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Verify one evolving case resists urgency, ambiguity collapse, and self-expansion."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["evolving adversarial replay report must be an object"]}
    for field in ("replay_report_id", "report_fingerprint", "report_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    replay_input = payload.get("replay_input")
    replay_record = payload.get("replay_record")
    if not isinstance(replay_input, dict) or not isinstance(replay_record, dict):
        errors.append("replay_input and replay_record must be objects")
        replay_input = replay_input if isinstance(replay_input, dict) else {}
        replay_record = replay_record if isinstance(replay_record, dict) else {}
    try:
        expected = run_evolving_adversarial_signal_replay(replay_input)
    except (TypeError, ValueError) as exc:
        errors.append(f"evolving adversarial replay failed: {exc}")
        expected = {}
    if replay_record != expected:
        errors.append("replay_record must equal deterministic evolving replay output")
    if replay_record.get("urgency_resisted") is not True:
        errors.append("urgency must be resisted")
    if replay_record.get("beneficiary_ambiguity_preserved_until_probe") is not True:
        errors.append("beneficiary ambiguity must remain open until a probe")
    if replay_record.get("self_expansion_candidate_rejected") is not True:
        errors.append("self-expansion candidate must be rejected")
    if replay_record.get("all_snapshots_frozen") is not True:
        errors.append("all replay snapshots must be frozen")
    frontiers = replay_record.get("frontier_fingerprints", [])
    if not isinstance(frontiers, list) or len(frontiers) != 4 or len(set(frontiers)) != 4:
        errors.append("replay must contain four distinct frozen frontiers")
    return {
        "valid": not errors,
        "errors": errors,
        "snapshot_count": len(replay_record.get("snapshots", [])),
        "final_selected_candidate_id": replay_record.get("final_selected_candidate_id", ""),
        "urgency_resisted": replay_record.get("urgency_resisted"),
        "self_expansion_candidate_rejected": replay_record.get(
            "self_expansion_candidate_rejected"
        ),
    }

def validate_planner_envelope_acknowledgment_loss(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Verify existing planner compilation and element-level acknowledgment loss."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["planner acknowledgment loss report must be an object"]}
    for field in ("loss_report_id", "report_fingerprint", "report_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    compilation_input = payload.get("compilation_input")
    compilation_record = payload.get("compilation_record")
    if not isinstance(compilation_input, dict) or not isinstance(compilation_record, dict):
        errors.append("compilation_input and compilation_record must be objects")
        compilation_input = compilation_input if isinstance(compilation_input, dict) else {}
        compilation_record = compilation_record if isinstance(compilation_record, dict) else {}
    try:
        expected = compile_planner_envelope_and_measure_acknowledgment_loss(compilation_input)
    except (TypeError, ValueError) as exc:
        errors.append(f"planner compilation or acknowledgment comparison failed: {exc}")
        expected = {}
    if compilation_record != expected:
        errors.append("compilation_record must equal deterministic compilation and loss measurement")
    envelope = compilation_record.get("planner_envelope", {})
    if envelope.get("tasks") != [] or envelope.get("implementation_sequence") != []:
        errors.append("planner envelope must not compile tasks or implementation sequence")
    if envelope.get("execution_authority_issued") is not False:
        errors.append("planner envelope must not issue execution authority")
    comparisons = compilation_record.get("dimension_comparisons", [])
    recomputed_loss = sum(
        isinstance(item, dict) and item.get("status") == "semantic_loss"
        for item in comparisons
    )
    if compilation_record.get("semantic_loss_count") != recomputed_loss:
        errors.append("semantic_loss_count must equal element comparisons")
    expected_acceptance = recomputed_loss == 0
    if compilation_record.get("acknowledgment_accepted") is not expected_acceptance:
        errors.append("acknowledgment_accepted must require zero semantic loss")
    if compilation_record.get("correction_required_before_strategy") is not (not expected_acceptance):
        errors.append("correction_required_before_strategy must reflect semantic loss")
    return {
        "valid": not errors,
        "errors": errors,
        "semantic_dimension_count": compilation_record.get("semantic_dimension_count", 0),
        "semantic_loss_count": compilation_record.get("semantic_loss_count", 0),
        "semantic_loss_rate": compilation_record.get("semantic_loss_rate", 0),
        "acknowledgment_accepted": compilation_record.get("acknowledgment_accepted"),
    }

def validate_live_provider_experiment_gate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Verify provider experimentation remains downstream of deterministic proof."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["live provider experiment report must be an object"]}
    for field in ("provider_report_id", "report_fingerprint", "report_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    experiment_input = payload.get("experiment_input")
    experiment_record = payload.get("experiment_record")
    if not isinstance(experiment_input, dict) or not isinstance(experiment_record, dict):
        errors.append("experiment_input and experiment_record must be objects")
        experiment_input = experiment_input if isinstance(experiment_input, dict) else {}
        experiment_record = experiment_record if isinstance(experiment_record, dict) else {}
    try:
        expected = authorize_live_provider_experiment(experiment_input)
    except (TypeError, ValueError) as exc:
        errors.append(f"live provider experiment authorization failed: {exc}")
        expected = {}
    if experiment_record != expected:
        errors.append("experiment_record must equal deterministic provider authorization")
    if experiment_record.get("live_experiment_authorized") is not True:
        errors.append("live experiment must be explicitly authorized")
    if experiment_record.get("provider_plurality_architectural_requirement") is not False:
        errors.append("provider plurality must not be an architectural requirement")
    if experiment_record.get("provider_output_can_bypass_validators") is not False:
        errors.append("provider output must not bypass validators")
    if experiment_record.get("provider_output_can_select_mission") is not False:
        errors.append("provider output must not select missions")
    expected_plurality = experiment_record.get("provider_arm_count", 0) > 1
    if experiment_record.get("provider_plurality_experiment") is not expected_plurality:
        errors.append("provider_plurality_experiment must reflect provider arm count")
    return {
        "valid": not errors,
        "errors": errors,
        "provider_arm_count": experiment_record.get("provider_arm_count", 0),
        "provider_plurality_experiment": experiment_record.get(
            "provider_plurality_experiment"
        ),
        "live_experiment_authorized": experiment_record.get("live_experiment_authorized"),
    }

def validate_one_case_stop_and_inspect(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Verify implementation pauses for evidence inspection before generalization."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["one-case inspection report must be an object"]}
    for field in ("inspection_report_id", "report_fingerprint", "report_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    inspection_input = payload.get("inspection_input")
    inspection_record = payload.get("inspection_record")
    if not isinstance(inspection_input, dict) or not isinstance(inspection_record, dict):
        errors.append("inspection_input and inspection_record must be objects")
        inspection_input = inspection_input if isinstance(inspection_input, dict) else {}
        inspection_record = inspection_record if isinstance(inspection_record, dict) else {}
    try:
        expected = inspect_one_case_before_generalization(inspection_input)
    except (TypeError, ValueError) as exc:
        errors.append(f"one-case inspection failed: {exc}")
        expected = {}
    if inspection_record != expected:
        errors.append("inspection_record must equal deterministic stop-and-inspect output")
    if inspection_record.get("implementation_decision") != "stop_and_inspect":
        errors.append("implementation decision must be stop_and_inspect")
    for field in (
        "schema_generalization_authorized",
        "agent_company_runtime_authorized",
        "autonomous_daemon_authorized",
    ):
        if inspection_record.get(field) is not False:
            errors.append(f"{field} must be false")
    if inspection_record.get("next_authorized_work") != "run_registered_case_specific_probes":
        errors.append("next work must remain case-specific evidence probes")
    return {
        "valid": not errors,
        "errors": errors,
        "finding_count": len(inspection_record.get("newly_visible_findings", [])),
        "covered_surfaces": inspection_record.get("covered_surfaces", []),
        "implementation_decision": inspection_record.get("implementation_decision", ""),
        "generalization_authorized": inspection_record.get(
            "schema_generalization_authorized"
        ),
    }

def validate_five_bounded_artifact_conclusion(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Verify the 400-cycle implementation conclusion against repository artifacts."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["five bounded artifact conclusion must be an object"]}
    for field in ("conclusion_report_id", "report_fingerprint", "report_rationale"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    conclusion = payload.get("conclusion")
    if not isinstance(conclusion, dict):
        errors.append("conclusion must be an object")
        conclusion = {}
    expected = build_five_bounded_artifact_conclusion()
    if conclusion != expected:
        errors.append("conclusion must match verified five-artifact repository state")
    expected_types = [
        "mission_schema_bundle",
        "intent_specific_state_commands",
        "provider_neutral_mission_cycle",
        "adversarial_sequential_replay",
        "traceable_planner_handoff",
    ]
    artifacts = conclusion.get("artifacts", [])
    actual_types = [
        item.get("artifact_type")
        for item in artifacts
        if isinstance(item, dict)
    ] if isinstance(artifacts, list) else []
    if actual_types != expected_types:
        errors.append("five bounded artifacts must remain in authoritative order")
    for index, artifact in enumerate(artifacts if isinstance(artifacts, list) else []):
        if artifact.get("order") != index + 1:
            errors.append(f"artifacts[{index}].order must be sequential")
        if artifact.get("schema_present") is not True or artifact.get("validator_present") is not True:
            errors.append(f"artifacts[{index}] must have verified schema and validator")
        if artifact.get("implementation_status") != "completed":
            errors.append(f"artifacts[{index}] must be completed")
    if conclusion.get("artifact_count") != 5:
        errors.append("artifact_count must be five")
    if conclusion.get("order_is_authoritative") is not True:
        errors.append("artifact order must be authoritative")
    for field in (
        "agent_company_runtime_included",
        "autonomous_daemon_included",
        "execution_platform_included",
        "startup_success_claimed",
        "general_schema_expansion_authorized",
    ):
        if conclusion.get(field) is not False:
            errors.append(f"{field} must be false")
    expected_question = (
        "Can Palamedes independently originate a mission worth planning that "
        "equal-budget human and one-shot-agent baselines do not produce?"
    )
    if conclusion.get("next_empirical_question") != expected_question:
        errors.append("next_empirical_question must preserve the current proof boundary")
    return {
        "valid": not errors,
        "errors": errors,
        "artifact_count": len(artifacts) if isinstance(artifacts, list) else 0,
        "artifact_types": actual_types,
        "all_artifacts_verified": all(
            isinstance(item, dict)
            and item.get("schema_present") is True
            and item.get("validator_present") is True
            and item.get("implementation_status") == "completed"
            for item in artifacts
        ) if isinstance(artifacts, list) else False,
        "next_empirical_question": conclusion.get("next_empirical_question", ""),
    }

def validate_reference_treatment_packet_gate(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Block a reference treatment that lacks task-relevant, evidence-linked guidance."""
    errors: List[str] = []
    blocking_reasons: List[str] = []
    if not isinstance(payload, dict):
        return {
            "valid": False,
            "errors": ["reference treatment packet gate must be an object"],
            "eligible_for_handoff": False,
            "blocking_reasons": ["malformed_packet"],
        }
    for field in (
        "packet_gate_id",
        "case_id",
        "task_fingerprint",
        "source_manifest_fingerprint",
        "selected_candidate_id",
        "report_fingerprint",
        "report_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")

    confidence = payload.get("overall_confidence")
    if confidence not in {"low", "medium", "high"}:
        errors.append("overall_confidence must be low, medium, or high")
    elif confidence == "low":
        blocking_reasons.append("overall_confidence_low")

    required = payload.get("required_capabilities")
    if (
        not isinstance(required, list)
        or not required
        or any(not _non_empty(item) for item in required)
        or len(set(required)) != len(required)
    ):
        errors.append("required_capabilities must contain unique non-empty strings")
        required = []
    supporting = payload.get("allowed_supporting_capabilities", [])
    if (
        not isinstance(supporting, list)
        or any(not _non_empty(item) for item in supporting)
        or len(set(supporting)) != len(supporting)
    ):
        errors.append("allowed_supporting_capabilities must contain unique non-empty strings")
        supporting = []

    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        errors.append("candidates must be a non-empty list")
        candidates = []
    candidate_ids = set()
    selected = None
    for index, candidate in enumerate(candidates):
        prefix = f"candidates[{index}]"
        if not isinstance(candidate, dict):
            errors.append(f"{prefix} must be an object")
            continue
        candidate_id = candidate.get("candidate_id")
        if not _non_empty(candidate_id):
            errors.append(f"{prefix}.candidate_id must be non-empty")
        elif candidate_id in candidate_ids:
            errors.append(f"{prefix}.candidate_id must be unique")
        else:
            candidate_ids.add(candidate_id)
        if candidate.get("confidence") not in {"low", "medium", "high"}:
            errors.append(f"{prefix}.confidence must be low, medium, or high")
        capabilities = candidate.get("positive_capabilities")
        if (
            not isinstance(capabilities, list)
            or any(not _non_empty(item) for item in capabilities)
            or len(set(capabilities)) != len(capabilities)
        ):
            errors.append(f"{prefix}.positive_capabilities must contain unique strings")
        evidence_ids = candidate.get("evidence_ids")
        if (
            not isinstance(evidence_ids, list)
            or not evidence_ids
            or any(not _non_empty(item) for item in evidence_ids)
            or len(set(evidence_ids)) != len(evidence_ids)
        ):
            errors.append(f"{prefix}.evidence_ids must contain unique non-empty strings")
        if candidate_id == payload.get("selected_candidate_id"):
            selected = candidate
    if _non_empty(payload.get("selected_candidate_id")) and selected is None:
        errors.append("selected_candidate_id must reference a candidate")

    selected_evidence = set()
    selected_capabilities = set()
    allowed_capabilities = set(required) | set(supporting)
    if isinstance(selected, dict):
        selected_capabilities = set(selected.get("positive_capabilities", []))
        selected_evidence = set(selected.get("evidence_ids", []))
        if selected.get("confidence") == "low":
            blocking_reasons.append("selected_candidate_confidence_low")
        for capability in required:
            if capability not in selected_capabilities:
                blocking_reasons.append(f"missing_required_capability:{capability}")

    guidance_steps = payload.get("guidance_steps")
    if not isinstance(guidance_steps, list) or not guidance_steps:
        errors.append("guidance_steps must be a non-empty list")
        guidance_steps = []
    step_ids = set()
    for index, step in enumerate(guidance_steps):
        prefix = f"guidance_steps[{index}]"
        if not isinstance(step, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("step_id", "text", "capability"):
            if not _non_empty(step.get(field)):
                errors.append(f"{prefix}.{field} must be non-empty")
        step_id = step.get("step_id")
        if _non_empty(step_id):
            if step_id in step_ids:
                errors.append(f"{prefix}.step_id must be unique")
            step_ids.add(step_id)
        relevance = step.get("task_relevance")
        if relevance not in {"direct", "supporting", "unrelated"}:
            errors.append(f"{prefix}.task_relevance must be direct, supporting, or unrelated")
        if relevance == "unrelated":
            blocking_reasons.append(f"unrelated_guidance_step:{step_id}")
        capability = step.get("capability")
        if _non_empty(capability) and capability not in allowed_capabilities:
            blocking_reasons.append(f"unsupported_guidance_capability:{capability}")
        elif _non_empty(capability) and capability not in selected_capabilities:
            blocking_reasons.append(f"guidance_capability_not_evidenced:{capability}")
        source_ids = step.get("source_evidence_ids")
        if (
            not isinstance(source_ids, list)
            or not source_ids
            or any(not _non_empty(item) for item in source_ids)
        ):
            errors.append(f"{prefix}.source_evidence_ids must be a non-empty string list")
        elif not set(source_ids).issubset(selected_evidence):
            blocking_reasons.append(f"guidance_evidence_not_selected:{step_id}")

    blocking_reasons = list(dict.fromkeys(blocking_reasons))
    eligible = not errors and not blocking_reasons
    expected_status = "ready" if eligible else "unavailable_insufficient_evidence"
    if payload.get("handoff_authorized") is not eligible:
        errors.append("handoff_authorized must equal the computed treatment eligibility")
    if payload.get("treatment_status") != expected_status:
        errors.append(f"treatment_status must be {expected_status}")
    return {
        "valid": not errors,
        "errors": errors,
        "eligible_for_handoff": eligible,
        "blocking_reasons": blocking_reasons,
        "selected_candidate_id": payload.get("selected_candidate_id", ""),
        "guidance_step_count": len(guidance_steps),
        "treatment_status": expected_status,
    }

