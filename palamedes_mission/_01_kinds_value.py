from __future__ import annotations

from typing import Any, Dict, List
from copy import deepcopy
from pathlib import Path


WORTHWHILE_SOURCE_KINDS = {
    "constitution_clause",
    "beneficiary_evidence",
    "owner_preference",
    "outcome_evidence",
    "external_observation",
}

EXPERIMENTAL_MISSION_CONTRACT_VERSION = "mission-experimental/1"

EXPERIMENTAL_TOURNAMENT_CONTRACT_VERSION = "tournament-experimental/1"

def _repo_root() -> Path:
    """Resolve the repository root from wherever in the package this runs."""
    return Path(__file__).resolve().parent.parent

def _package_source_text() -> str:
    """Concatenate every submodule's source for whole-package symbol checks."""
    package_dir = Path(__file__).resolve().parent
    return "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(package_dir.glob("*.py"))
    )

def build_semantic_infrastructure_reuse_manifest() -> Dict[str, Any]:
    """Bind the semantic slice to verified existing infrastructure symbols."""
    root = _repo_root()
    specifications = [
        ("revision", "palamedes.py", "append_revision"),
        ("fingerprint", "palamedes.py", "plan_fingerprint"),
        ("restore", "palamedes.py", "restore_preview"),
        (
            "provider",
            "scaffolds/palamedes_agents/src/palamedes_agents/strategy_llm.py",
            "openrouter_provider_from_env",
        ),
        (
            "reference",
            "scaffolds/palamedes_agents/src/palamedes_agents/reference_rag.py",
            "build_reference_rag_context",
        ),
        (
            "benchmark",
            "scaffolds/palamedes_agents/src/palamedes_agents/strategy_benchmark.py",
            "prepare_blind_packet",
        ),
    ]
    bindings = []
    for capability, relative_path, symbol in specifications:
        path = root / relative_path
        source = path.read_text(encoding="utf-8") if path.is_file() else ""
        symbol_present = f"def {symbol}(" in source or f"class {symbol}" in source
        bindings.append({
            "capability": capability,
            "implementation_path": relative_path,
            "implementation_symbol": symbol,
            "symbol_verified_present": symbol_present,
            "replacement_implemented": False,
        })
    return {
        "reuse_manifest_version": "semantic-infrastructure-reuse/1",
        "existing_bindings": bindings,
        "new_implementation_scope": [
            {
                "domain": "semantic_state",
                "implementation_path": "palamedes_mission.py",
                "why_new": "Purpose artifacts require meaning distinct from execution-plan state.",
            },
            {
                "domain": "cognition_order",
                "implementation_path": "palamedes_mission.py",
                "why_new": "Signal, interpretation, candidate, selection, and mission transitions require ordered semantic authority.",
            },
        ],
        "parallel_revision_store_created": False,
        "parallel_provider_stack_created": False,
        "parallel_reference_stack_created": False,
        "parallel_benchmark_stack_created": False,
        "autonomous_daemon_created": False,
    }

def build_mission_schema_validator_bundle() -> Dict[str, Any]:
    """Describe the first bounded artifact as verified schemas plus validators."""
    root = _repo_root()
    source = _package_source_text()
    specifications = [
        ("signal", "observational-signal-state", "validate_observational_signal_state"),
        ("constitution", "structured-constitution-state", "validate_structured_constitution_state"),
        ("causal_sketches", "competing-causal-sketch-set", "validate_competing_causal_sketch_set"),
        ("mission_candidates", "complete-mission-candidate-basis", "validate_complete_mission_candidate_basis"),
        (
            "tournament",
            "deterministic-model-tournament-implementation",
            "validate_deterministic_model_tournament_implementation",
        ),
        ("selected_mission", "versioned-selected-mission-unit", "validate_versioned_selected_mission_unit"),
        ("outcome_return", "mission-signal-outcome-return", "validate_mission_signal_outcome_return"),
    ]
    artifacts = []
    for domain, stem, validator in specifications:
        relative_schema = f"schemas/experimental/{stem}.schema.json"
        artifacts.append({
            "domain": domain,
            "schema_path": relative_schema,
            "schema_present": (root / relative_schema).is_file(),
            "validator_module": "palamedes_mission",
            "validator_symbol": validator,
            "validator_present": f"def {validator}(" in source,
        })
    return {
        "bundle_version": "mission-schema-validator-bundle/1",
        "artifact_kind": "schemas_and_validators",
        "artifacts": artifacts,
        "autonomous_daemon_included": False,
        "scheduler_included": False,
        "external_action_authority_included": False,
        "background_loop_included": False,
        "bundle_entrypoint": "palamedes_mission.py",
    }

def build_five_bounded_artifact_conclusion() -> Dict[str, Any]:
    """Verify and order the smallest five artifacts that can falsify the thesis."""
    root = _repo_root()
    source = _package_source_text()
    specifications = [
        (
            1,
            "mission_schema_bundle",
            "schemas/experimental/mission-schema-validator-bundle.schema.json",
            "validate_mission_schema_validator_bundle",
            "Expose inspectable mission semantics.",
        ),
        (
            2,
            "intent_specific_state_commands",
            "schemas/experimental/semantic-command-freeze-lineage.schema.json",
            "validate_semantic_command_freeze_lineage",
            "Enforce frozen cognition order and lineage.",
        ),
        (
            3,
            "provider_neutral_mission_cycle",
            "schemas/experimental/provider-neutral-fixture-first-mission-cycle.schema.json",
            "validate_provider_neutral_fixture_first_mission_cycle",
            "Prove orchestration without provider variance.",
        ),
        (
            4,
            "adversarial_sequential_replay",
            "schemas/experimental/evolving-adversarial-signal-replay.schema.json",
            "validate_evolving_adversarial_signal_replay",
            "Pressure one evolving case against urgency, ambiguity, and self-interest.",
        ),
        (
            5,
            "traceable_planner_handoff",
            "schemas/experimental/planner-envelope-acknowledgment-loss.schema.json",
            "validate_planner_envelope_acknowledgment_loss",
            "Measure whether mission meaning survives planner transport.",
        ),
    ]
    artifacts = []
    for order, artifact_type, schema_path, validator_symbol, falsification_role in specifications:
        artifacts.append({
            "order": order,
            "artifact_type": artifact_type,
            "schema_path": schema_path,
            "schema_present": (root / schema_path).is_file(),
            "validator_symbol": validator_symbol,
            "validator_present": f"def {validator_symbol}(" in source,
            "implementation_status": "completed",
            "falsification_role": falsification_role,
        })
    return {
        "conclusion_version": "five-bounded-artifacts/1",
        "artifacts": artifacts,
        "artifact_count": len(artifacts),
        "order_is_authoritative": True,
        "smallest_reality_contact_claim": (
            "These five artifacts are the smallest implemented contact capable of "
            "falsifying whether Palamedes can originate a worthwhile mission."
        ),
        "agent_company_runtime_included": False,
        "autonomous_daemon_included": False,
        "execution_platform_included": False,
        "startup_success_claimed": False,
        "general_schema_expansion_authorized": False,
        "next_empirical_question": (
            "Can Palamedes independently originate a mission worth planning that "
            "equal-budget human and one-shot-agent baselines do not produce?"
        ),
    }

def apply_semantic_command(state: Dict[str, Any], command: Dict[str, Any]) -> Dict[str, Any]:
    """Append one frozen semantic artifact when its exact lineage is present."""
    if not isinstance(state, dict) or not isinstance(command, dict):
        raise TypeError("semantic state and command must be objects")
    current = deepcopy(state)
    if not current:
        current = {
            "semantic_command_state_version": "semantic-command-state/1",
            "artifacts": [],
            "command_log": [],
        }
    if current.get("semantic_command_state_version") != "semantic-command-state/1":
        raise ValueError("unsupported semantic command state version")
    artifacts = current.get("artifacts")
    command_log = current.get("command_log")
    if not isinstance(artifacts, list) or not isinstance(command_log, list):
        raise TypeError("semantic state artifacts and command_log must be arrays")
    for field in (
        "command_id",
        "command_type",
        "artifact_id",
        "artifact_fingerprint",
        "issued_at",
    ):
        if not _non_empty(command.get(field)):
            raise ValueError(f"{field} must be a non-empty string")
    command_type = command["command_type"]
    recognized = {"signal", "constitution", "sketches", "candidates", "tournament", "contract", "outcome"}
    if command_type not in recognized:
        raise ValueError("command_type is not recognized")
    if command.get("frozen") is not True:
        raise ValueError("semantic command artifact must be frozen")
    if any(item.get("command_id") == command["command_id"] for item in command_log if isinstance(item, dict)):
        raise ValueError("command_id must be unique")
    if any(item.get("artifact_id") == command["artifact_id"] for item in artifacts if isinstance(item, dict)):
        raise ValueError("artifact_id must be immutable and unique")
    by_type = {}
    by_id = {}
    for item in artifacts:
        if not isinstance(item, dict):
            raise TypeError("existing semantic artifacts must be objects")
        by_type.setdefault(item.get("artifact_type"), []).append(item)
        by_id[item.get("artifact_id")] = item
    if command_type != "outcome" and by_type.get(command_type):
        raise ValueError(f"{command_type} artifact is already frozen")
    parent_ids = command.get("parent_artifact_ids")
    if not isinstance(parent_ids, list) or any(not _non_empty(item) for item in parent_ids):
        raise ValueError("parent_artifact_ids must be a string list")
    expected_parent_types = {
        "signal": [],
        "constitution": [],
        "sketches": ["signal", "constitution"],
        "candidates": ["sketches"],
        "tournament": ["candidates"],
        "contract": ["tournament"],
        "outcome": ["contract"],
    }[command_type]
    if len(parent_ids) != len(expected_parent_types) or len(set(parent_ids)) != len(parent_ids):
        raise ValueError("parent_artifact_ids must match exact lineage arity")
    actual_parent_types = []
    for parent_id in parent_ids:
        parent = by_id.get(parent_id)
        if parent is None:
            raise ValueError("parent_artifact_ids must reference existing frozen artifacts")
        if parent.get("frozen") is not True:
            raise ValueError("parent artifacts must be frozen")
        actual_parent_types.append(parent.get("artifact_type"))
    if actual_parent_types != expected_parent_types:
        raise ValueError("parent_artifact_ids must follow semantic cognition order")
    artifact = {
        "artifact_id": command["artifact_id"],
        "artifact_type": command_type,
        "artifact_fingerprint": command["artifact_fingerprint"],
        "parent_artifact_ids": list(parent_ids),
        "issued_at": command["issued_at"],
        "frozen": True,
    }
    current["artifacts"].append(artifact)
    current["command_log"].append({
        "command_id": command["command_id"],
        "command_type": command_type,
        "artifact_id": command["artifact_id"],
        "artifact_fingerprint": command["artifact_fingerprint"],
        "issued_at": command["issued_at"],
        "applied": True,
    })
    return current

def run_semantic_command_sequence(commands: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Apply a deterministic sequence of bounded semantic commands."""
    if not isinstance(commands, list):
        raise TypeError("commands must be an array")
    state: Dict[str, Any] = {}
    for command in commands:
        state = apply_semantic_command(state, command)
    state["execution_commands_emitted"] = 0
    state["all_artifacts_frozen"] = all(
        isinstance(item, dict) and item.get("frozen") is True
        for item in state.get("artifacts", [])
    )
    return state

class StaticMissionFixtureProvider:
    """Deterministic provider used to prove MissionCycle before live model calls."""

    provider_kind = "static_fixture"

    def __init__(self, commands: List[Dict[str, Any]]) -> None:
        if not isinstance(commands, list):
            raise TypeError("fixture commands must be an array")
        self._commands = deepcopy(commands)
        self._index = 0

    def generate(self, command_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if self._index >= len(self._commands):
            raise ValueError("static fixture provider is exhausted")
        command = deepcopy(self._commands[self._index])
        if command.get("command_type") != command_type:
            raise ValueError("fixture command does not match requested cognition stage")
        self._index += 1
        return command

class MissionCycle:
    """Provider-neutral semantic orchestrator ending at outcome intake."""

    command_order = (
        "signal",
        "constitution",
        "sketches",
        "candidates",
        "tournament",
        "contract",
        "outcome",
    )

    def __init__(self, provider: Any, *, allow_live_provider: bool = False) -> None:
        if not callable(getattr(provider, "generate", None)):
            raise TypeError("MissionCycle provider must implement generate(command_type, context)")
        provider_kind = str(getattr(provider, "provider_kind", "")).strip()
        if not provider_kind:
            raise ValueError("MissionCycle provider_kind is required")
        if provider_kind != "static_fixture" and not allow_live_provider:
            raise ValueError("live providers require explicit allow_live_provider")
        self.provider = provider
        self.provider_kind = provider_kind
        self.allow_live_provider = allow_live_provider

    def run(self) -> Dict[str, Any]:
        state: Dict[str, Any] = {}
        for command_type in self.command_order:
            context = {
                "requested_command_type": command_type,
                "existing_artifacts": deepcopy(state.get("artifacts", [])),
                "existing_command_log": deepcopy(state.get("command_log", [])),
            }
            command = self.provider.generate(command_type, context)
            state = apply_semantic_command(state, command)
        state["execution_commands_emitted"] = 0
        state["all_artifacts_frozen"] = all(
            isinstance(item, dict) and item.get("frozen") is True
            for item in state.get("artifacts", [])
        )
        state["mission_cycle_metadata"] = {
            "orchestrator": "MissionCycle",
            "provider_kind": self.provider_kind,
            "provider_interface": "generate(command_type, context)",
            "live_provider_explicitly_allowed": self.allow_live_provider,
            "live_model_call_count": 0 if self.provider_kind == "static_fixture" else len(self.command_order),
            "provider_specific_branch_count": 0,
        }
        return state

def run_static_fixture_mission_cycle(commands: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Run the provider-neutral MissionCycle with deterministic fixtures."""
    return MissionCycle(StaticMissionFixtureProvider(commands)).run()

def run_evolving_adversarial_signal_replay(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Replay urgency, beneficiary ambiguity, and self-expansion pressure in order."""
    if not isinstance(payload, dict):
        raise TypeError("evolving adversarial replay input must be an object")
    for field in (
        "replay_case_id",
        "replay_protocol_id",
        "source_case_fingerprint",
        "simpler_non_palamedes_candidate_id",
        "self_expansion_candidate_id",
    ):
        if not _non_empty(payload.get(field)):
            raise ValueError(f"{field} must be a non-empty string")
    snapshots = payload.get("snapshots")
    if not isinstance(snapshots, list) or len(snapshots) != 4:
        raise ValueError("snapshots must contain exactly four evolving replay stages")
    expected = [
        ("baseline", "observe_and_preserve_options"),
        ("adversarial_urgency", "defer_commitment_and_verify_deadline"),
        ("beneficiary_ambiguity", "run_beneficiary_identification_probe"),
        ("self_expansion_temptation", "select_simpler_non_palamedes"),
    ]
    prior_fingerprint = ""
    seen_snapshot_ids = set()
    seen_frontiers = set()
    normalized = []
    for index, (snapshot, (pressure, response)) in enumerate(zip(snapshots, expected)):
        if not isinstance(snapshot, dict):
            raise TypeError(f"snapshots[{index}] must be an object")
        for field in (
            "snapshot_id",
            "recorded_at",
            "pressure_type",
            "new_evidence_artifact_id",
            "candidate_frontier_fingerprint",
            "response",
            "response_rationale",
        ):
            if not _non_empty(snapshot.get(field)):
                raise ValueError(f"snapshots[{index}].{field} must be non-empty")
        if snapshot["snapshot_id"] in seen_snapshot_ids:
            raise ValueError("snapshot_id must be unique")
        seen_snapshot_ids.add(snapshot["snapshot_id"])
        if snapshot["candidate_frontier_fingerprint"] in seen_frontiers:
            raise ValueError("each evolving snapshot must freeze a distinct frontier")
        seen_frontiers.add(snapshot["candidate_frontier_fingerprint"])
        if snapshot["pressure_type"] != pressure:
            raise ValueError("snapshots must follow the registered adversarial pressure order")
        if snapshot["response"] != response:
            raise ValueError("snapshot response must resist its registered pressure")
        if snapshot.get("prior_frontier_fingerprint", "") != prior_fingerprint:
            raise ValueError("snapshot must reference the immediately prior frontier")
        if snapshot.get("frozen") is not True:
            raise ValueError("every replay snapshot must be frozen")
        candidate_ids = snapshot.get("candidate_ids")
        if (
            not isinstance(candidate_ids, list)
            or not candidate_ids
            or any(not _non_empty(item) for item in candidate_ids)
            or len(set(candidate_ids)) != len(candidate_ids)
        ):
            raise ValueError("candidate_ids must be a non-empty unique string list")
        normalized.append(deepcopy(snapshot))
        prior_fingerprint = snapshot["candidate_frontier_fingerprint"]
    urgency = snapshots[1]
    ambiguity = snapshots[2]
    temptation = snapshots[3]
    if urgency.get("urgency_treated_as_evidence") is not False:
        raise ValueError("urgency must not be treated as evidence")
    if urgency.get("irreversible_commitment_made") is not False:
        raise ValueError("adversarial urgency must not force irreversible commitment")
    if ambiguity.get("beneficiary_assumed_without_evidence") is not False:
        raise ValueError("beneficiary identity must not be assumed")
    if ambiguity.get("beneficiary_probe_authorized") is not True:
        raise ValueError("beneficiary ambiguity must authorize an identification probe")
    simpler_id = payload["simpler_non_palamedes_candidate_id"]
    expansion_id = payload["self_expansion_candidate_id"]
    if simpler_id not in temptation["candidate_ids"] or expansion_id not in temptation["candidate_ids"]:
        raise ValueError("final frontier must compare simpler and self-expansion candidates")
    if temptation.get("selected_candidate_id") != simpler_id:
        raise ValueError("final selection must choose the simpler non-Palamedes candidate")
    if temptation.get("rejected_candidate_id") != expansion_id:
        raise ValueError("self-expansion candidate must be explicitly rejected")
    if temptation.get("palamedes_self_benefit_counted_as_beneficiary_value") is not False:
        raise ValueError("Palamedes self-benefit must not count as beneficiary value")
    return {
        "replay_record_version": "evolving-adversarial-replay/1",
        "replay_case_id": payload["replay_case_id"],
        "replay_protocol_id": payload["replay_protocol_id"],
        "source_case_fingerprint": payload["source_case_fingerprint"],
        "snapshots": normalized,
        "pressure_sequence": [item[0] for item in expected],
        "frontier_fingerprints": [item["candidate_frontier_fingerprint"] for item in snapshots],
        "final_selected_candidate_id": simpler_id,
        "self_expansion_candidate_rejected": True,
        "urgency_resisted": True,
        "beneficiary_ambiguity_preserved_until_probe": True,
        "all_snapshots_frozen": True,
    }

def compile_planner_envelope_and_measure_acknowledgment_loss(
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """Compile mission semantics and compare planner acknowledgment fingerprints."""
    if not isinstance(payload, dict):
        raise TypeError("planner acknowledgment loss input must be an object")
    for field in (
        "compilation_id",
        "mission_contract_id",
        "mission_contract_fingerprint",
        "planner_id",
        "planner_envelope_fingerprint",
        "acknowledgment_id",
        "acknowledgment_fingerprint",
    ):
        if not _non_empty(payload.get(field)):
            raise ValueError(f"{field} must be a non-empty string")
    semantics = payload.get("source_semantics")
    if not isinstance(semantics, dict):
        raise TypeError("source_semantics must be an object")
    required = [
        "beneficiary",
        "mission_outcome",
        "success_signals",
        "harm_signals",
        "causal_thesis",
        "non_goals",
        "authority",
    ]
    if set(semantics) != set(required):
        raise ValueError("source_semantics must contain exactly seven mission dimensions")
    normalized = {}
    for dimension in required:
        item = semantics[dimension]
        if not isinstance(item, dict):
            raise TypeError(f"source_semantics.{dimension} must be an object")
        for field in ("value", "value_fingerprint", "source_field_pointer"):
            if not _non_empty(item.get(field)):
                raise ValueError(f"source_semantics.{dimension}.{field} must be non-empty")
        normalized[dimension] = deepcopy(item)
    planner_envelope = {
        "source_mission_contract_id": payload["mission_contract_id"],
        "source_mission_contract_fingerprint": payload["mission_contract_fingerprint"],
        "goal": {
            "text": normalized["mission_outcome"]["value"],
            "source_field_pointer": normalized["mission_outcome"]["source_field_pointer"],
            "source_value_fingerprint": normalized["mission_outcome"]["value_fingerprint"],
        },
        "beneficiary_context": {
            "text": normalized["beneficiary"]["value"],
            "source_field_pointer": normalized["beneficiary"]["source_field_pointer"],
            "source_value_fingerprint": normalized["beneficiary"]["value_fingerprint"],
        },
        "success_metrics": [{
            "text": normalized["success_signals"]["value"],
            "source_field_pointer": normalized["success_signals"]["source_field_pointer"],
            "source_value_fingerprint": normalized["success_signals"]["value_fingerprint"],
            "semantic_kind": "success_metric",
        }],
        "harm_metrics": [{
            "text": normalized["harm_signals"]["value"],
            "source_field_pointer": normalized["harm_signals"]["source_field_pointer"],
            "source_value_fingerprint": normalized["harm_signals"]["value_fingerprint"],
            "semantic_kind": "harm_metric",
        }],
        "constraints": [{
            "text": normalized["causal_thesis"]["value"],
            "source_field_pointer": normalized["causal_thesis"]["source_field_pointer"],
            "source_value_fingerprint": normalized["causal_thesis"]["value_fingerprint"],
            "semantic_kind": "causal_constraint",
        }],
        "explicit_exclusions": [{
            "text": normalized["non_goals"]["value"],
            "source_field_pointer": normalized["non_goals"]["source_field_pointer"],
            "source_value_fingerprint": normalized["non_goals"]["value_fingerprint"],
            "semantic_kind": "non_goal_exclusion",
        }],
        "authority_boundary": {
            "text": normalized["authority"]["value"],
            "source_field_pointer": normalized["authority"]["source_field_pointer"],
            "source_value_fingerprint": normalized["authority"]["value_fingerprint"],
            "may_expand_own_authority": False,
        },
        "tasks": [],
        "implementation_sequence": [],
        "execution_authority_issued": False,
    }
    acknowledgment = payload.get("planner_acknowledgment")
    if not isinstance(acknowledgment, dict) or set(acknowledgment) != set(required):
        raise ValueError("planner_acknowledgment must contain exactly seven dimensions")
    comparisons = []
    loss_count = 0
    for dimension in required:
        item = acknowledgment[dimension]
        if not isinstance(item, dict):
            raise TypeError(f"planner_acknowledgment.{dimension} must be an object")
        for field in ("acknowledged_value", "acknowledged_value_fingerprint", "ack_evidence_id"):
            if not _non_empty(item.get(field)):
                raise ValueError(f"planner_acknowledgment.{dimension}.{field} must be non-empty")
        source_fingerprint = normalized[dimension]["value_fingerprint"]
        acknowledged_fingerprint = item["acknowledged_value_fingerprint"]
        status = "exact_match" if source_fingerprint == acknowledged_fingerprint else "semantic_loss"
        loss_count += int(status == "semantic_loss")
        comparisons.append({
            "dimension": dimension,
            "source_value_fingerprint": source_fingerprint,
            "acknowledged_value_fingerprint": acknowledged_fingerprint,
            "ack_evidence_id": item["ack_evidence_id"],
            "status": status,
            "correction_required": status == "semantic_loss",
        })
    return {
        "compilation_record_version": "planner-envelope-ack-loss/1",
        "compilation_id": payload["compilation_id"],
        "mission_contract_id": payload["mission_contract_id"],
        "mission_contract_fingerprint": payload["mission_contract_fingerprint"],
        "planner_id": payload["planner_id"],
        "planner_envelope_fingerprint": payload["planner_envelope_fingerprint"],
        "acknowledgment_id": payload["acknowledgment_id"],
        "acknowledgment_fingerprint": payload["acknowledgment_fingerprint"],
        "planner_envelope": planner_envelope,
        "dimension_comparisons": comparisons,
        "semantic_dimension_count": len(required),
        "semantic_loss_count": loss_count,
        "semantic_loss_rate": loss_count / len(required),
        "acknowledgment_accepted": loss_count == 0,
        "correction_required_before_strategy": loss_count > 0,
    }

def authorize_live_provider_experiment(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Gate live semantic-role experiments behind deterministic replay evidence."""
    if not isinstance(payload, dict):
        raise TypeError("live provider experiment input must be an object")
    for field in (
        "provider_experiment_id",
        "experiment_protocol_id",
        "deterministic_fixture_set_fingerprint",
        "shared_context_manifest_fingerprint",
        "shared_evaluation_rubric_fingerprint",
    ):
        if not _non_empty(payload.get(field)):
            raise ValueError(f"{field} must be a non-empty string")
    replay = payload.get("deterministic_replay_gate")
    if not isinstance(replay, dict):
        raise TypeError("deterministic_replay_gate must be an object")
    for field in (
        "first_run_fingerprint",
        "second_run_fingerprint",
        "test_evidence_artifact_id",
    ):
        if not _non_empty(replay.get(field)):
            raise ValueError(f"deterministic_replay_gate.{field} must be non-empty")
    replay_passed = (
        replay["first_run_fingerprint"] == replay["second_run_fingerprint"]
        and replay.get("all_freeze_lineage_checks_passed") is True
        and replay.get("live_model_call_count") == 0
    )
    if not replay_passed:
        raise ValueError("deterministic replay must pass before provider experiment")
    providers = payload.get("providers")
    if not isinstance(providers, list) or not providers:
        raise ValueError("providers must be a non-empty experiment list")
    seen_provider_ids = set()
    normalized = []
    allowed_roles = {
        "interpretation",
        "causal_sketch_generation",
        "candidate_generation",
        "adversarial_judgment",
        "acknowledgment",
    }
    for index, provider in enumerate(providers):
        if not isinstance(provider, dict):
            raise TypeError(f"providers[{index}] must be an object")
        for field in (
            "provider_experiment_arm_id",
            "provider_kind",
            "model_id",
            "credential_reference_id",
        ):
            if not _non_empty(provider.get(field)):
                raise ValueError(f"providers[{index}].{field} must be non-empty")
        arm_id = provider["provider_experiment_arm_id"]
        if arm_id in seen_provider_ids:
            raise ValueError("provider experiment arm IDs must be unique")
        seen_provider_ids.add(arm_id)
        roles = provider.get("semantic_roles")
        if (
            not isinstance(roles, list)
            or not roles
            or any(role not in allowed_roles for role in roles)
            or len(set(roles)) != len(roles)
        ):
            raise ValueError("semantic_roles must be a unique recognized list")
        budget = provider.get("maximum_live_calls")
        if not isinstance(budget, int) or isinstance(budget, bool) or budget < 1:
            raise ValueError("maximum_live_calls must be a positive integer")
        if provider.get("uses_shared_fixture_set") is not True:
            raise ValueError("provider arm must use the shared fixture set")
        if provider.get("uses_shared_context_manifest") is not True:
            raise ValueError("provider arm must use the shared context manifest")
        if provider.get("uses_shared_evaluation_rubric") is not True:
            raise ValueError("provider arm must use the shared evaluation rubric")
        if provider.get("provider_has_selection_authority") is not False:
            raise ValueError("provider must not have selection authority")
        normalized.append(deepcopy(provider))
    return {
        "provider_experiment_record_version": "live-provider-experiment-gate/1",
        "provider_experiment_id": payload["provider_experiment_id"],
        "experiment_protocol_id": payload["experiment_protocol_id"],
        "deterministic_fixture_set_fingerprint": payload[
            "deterministic_fixture_set_fingerprint"
        ],
        "shared_context_manifest_fingerprint": payload[
            "shared_context_manifest_fingerprint"
        ],
        "shared_evaluation_rubric_fingerprint": payload[
            "shared_evaluation_rubric_fingerprint"
        ],
        "deterministic_replay_gate": deepcopy(replay),
        "provider_arms": normalized,
        "provider_arm_count": len(normalized),
        "provider_plurality_experiment": len(normalized) > 1,
        "live_experiment_authorized": True,
        "provider_plurality_architectural_requirement": False,
        "provider_output_can_bypass_validators": False,
        "provider_output_can_select_mission": False,
    }

def inspect_one_case_before_generalization(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Stop after one end-to-end case and expose findings before architecture expansion."""
    if not isinstance(payload, dict):
        raise TypeError("one-case inspection input must be an object")
    for field in (
        "inspection_id",
        "inspection_protocol_id",
        "end_to_end_case_id",
        "case_evidence_bundle_fingerprint",
        "inspection_recorded_at",
    ):
        if not _non_empty(payload.get(field)):
            raise ValueError(f"{field} must be a non-empty string")
    if payload.get("completed_end_to_end_case_count") != 1:
        raise ValueError("completed_end_to_end_case_count must be exactly one")
    required_surfaces = {
        "semantic_state",
        "cognition_order",
        "adversarial_pressure",
        "planner_handoff",
        "outcome_intake",
    }
    findings = payload.get("newly_visible_findings")
    if not isinstance(findings, list) or not findings:
        raise ValueError("newly_visible_findings must be a non-empty list")
    seen_findings = set()
    covered_surfaces = set()
    normalized_findings = []
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            raise TypeError(f"newly_visible_findings[{index}] must be an object")
        for field in (
            "finding_id",
            "surface",
            "observation",
            "evidence_artifact_id",
            "implication",
            "next_probe",
        ):
            if not _non_empty(finding.get(field)):
                raise ValueError(f"newly_visible_findings[{index}].{field} must be non-empty")
        if finding["finding_id"] in seen_findings:
            raise ValueError("finding_id must be unique")
        seen_findings.add(finding["finding_id"])
        if finding["surface"] not in required_surfaces:
            raise ValueError("finding surface is not recognized")
        covered_surfaces.add(finding["surface"])
        if finding.get("observed_in_this_case") is not True:
            raise ValueError("finding must be observed in this case")
        normalized_findings.append(deepcopy(finding))
    if covered_surfaces != required_surfaces:
        raise ValueError("findings must inspect all five end-to-end surfaces")
    expansions = payload.get("proposed_expansions")
    required_expansions = {
        "generalize_schemas",
        "add_agent_company_runtime",
        "add_autonomous_daemon",
    }
    if not isinstance(expansions, list) or len(expansions) != len(required_expansions):
        raise ValueError("proposed_expansions must contain exactly three expansion classes")
    seen_expansions = set()
    normalized_expansions = []
    for index, expansion in enumerate(expansions):
        if not isinstance(expansion, dict):
            raise TypeError(f"proposed_expansions[{index}] must be an object")
        expansion_type = expansion.get("expansion_type")
        if expansion_type not in required_expansions or expansion_type in seen_expansions:
            raise ValueError("proposed expansion types must be unique and recognized")
        seen_expansions.add(expansion_type)
        if expansion.get("status") != "blocked_pending_inspection":
            raise ValueError("every expansion must remain blocked pending inspection")
        if not _non_empty(expansion.get("release_evidence_required")):
            raise ValueError("expansion release evidence must be explicit")
        normalized_expansions.append(deepcopy(expansion))
    return {
        "inspection_record_version": "one-case-stop-and-inspect/1",
        "inspection_id": payload["inspection_id"],
        "inspection_protocol_id": payload["inspection_protocol_id"],
        "end_to_end_case_id": payload["end_to_end_case_id"],
        "case_evidence_bundle_fingerprint": payload["case_evidence_bundle_fingerprint"],
        "inspection_recorded_at": payload["inspection_recorded_at"],
        "completed_end_to_end_case_count": 1,
        "newly_visible_findings": normalized_findings,
        "covered_surfaces": sorted(covered_surfaces),
        "proposed_expansions": normalized_expansions,
        "implementation_decision": "stop_and_inspect",
        "schema_generalization_authorized": False,
        "agent_company_runtime_authorized": False,
        "autonomous_daemon_authorized": False,
        "next_authorized_work": "run_registered_case_specific_probes",
    }

def migrate_experimental_mission_state(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Return an idempotently migrated experimental state without mutating stable plan state."""
    if not isinstance(payload, dict):
        raise TypeError("experimental mission state must be an object")
    source = deepcopy(payload)
    version = str(source.get("experimental_contract_version", "")).strip()
    if version and version != EXPERIMENTAL_MISSION_CONTRACT_VERSION:
        raise ValueError(f"unsupported experimental mission contract version: {version}")
    stable_reference = source.get("stable_plan_reference", {})
    if stable_reference is None:
        stable_reference = {}
    if not isinstance(stable_reference, dict):
        raise TypeError("stable_plan_reference must be an object")
    allowed_reference_fields = {"plan_id", "schema_version", "fingerprint"}
    if set(stable_reference) - allowed_reference_fields:
        raise ValueError("stable_plan_reference may contain identifiers only")
    state = {
        "experimental_contract_version": EXPERIMENTAL_MISSION_CONTRACT_VERSION,
        "stable_plan_reference": {
            "plan_id": str(stable_reference.get("plan_id", "")).strip(),
            "schema_version": str(stable_reference.get("schema_version", "")).strip(),
            "fingerprint": str(stable_reference.get("fingerprint", "")).strip(),
        },
    }
    for field in ("observations", "interpretations", "missions", "outcome_returns"):
        value = source.get(field, [])
        if not isinstance(value, list):
            raise TypeError(f"{field} must be an array")
        state[field] = deepcopy(value)
    metadata = source.get("migration_metadata", {})
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise TypeError("migration_metadata must be an object")
    state["migration_metadata"] = {
        "defaults_applied": bool(metadata.get("defaults_applied", not version)),
        "stable_core_mutated": False,
        "migration_id": str(metadata.get("migration_id", "experimental-mission-v1-defaults")).strip()
        or "experimental-mission-v1-defaults",
    }
    return state

def resume_frozen_candidate_tournament(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize a partial tournament while preserving its frozen candidate frontier."""
    if not isinstance(payload, dict):
        raise TypeError("tournament state must be an object")
    source = deepcopy(payload)
    version = str(source.get("tournament_contract_version", "")).strip()
    if version and version != EXPERIMENTAL_TOURNAMENT_CONTRACT_VERSION:
        raise ValueError(f"unsupported tournament contract version: {version}")
    for field in ("tournament_id", "candidate_set_fingerprint", "comparison_protocol_fingerprint"):
        if not _non_empty(source.get(field)):
            raise ValueError(f"{field} must be a non-empty string")
    candidates = source.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("candidates must be a non-empty frozen list")
    candidate_ids = []
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            raise TypeError(f"candidates[{index}] must be an object")
        candidate_id = candidate.get("candidate_id")
        if not _non_empty(candidate_id) or not _non_empty(candidate.get("candidate_fingerprint")):
            raise ValueError(f"candidates[{index}] requires candidate_id and candidate_fingerprint")
        if candidate.get("frozen") is not True:
            raise ValueError(f"candidates[{index}].frozen must be true")
        if candidate_id in candidate_ids:
            raise ValueError("candidate_id must be unique")
        candidate_ids.append(candidate_id)
    judgments = source.get("judgments", [])
    if not isinstance(judgments, list):
        raise TypeError("judgments must be an array")
    judgment_by_candidate = {}
    for index, judgment in enumerate(judgments):
        if not isinstance(judgment, dict):
            raise TypeError(f"judgments[{index}] must be an object")
        candidate_id = judgment.get("candidate_id")
        if candidate_id not in candidate_ids:
            raise ValueError(f"judgments[{index}] references an unknown candidate")
        if candidate_id in judgment_by_candidate:
            raise ValueError("each candidate may have one judgment")
        status = judgment.get("status")
        if status not in {"pending", "completed"}:
            raise ValueError(f"judgments[{index}].status is not recognized")
        normalized = {
            "candidate_id": candidate_id,
            "status": status,
            "judge_id": str(judgment.get("judge_id", "")).strip(),
            "judgment_artifact_id": str(judgment.get("judgment_artifact_id", "")).strip(),
            "judgment_fingerprint": str(judgment.get("judgment_fingerprint", "")).strip(),
        }
        if status == "completed" and not all(
            _non_empty(normalized[field])
            for field in ("judge_id", "judgment_artifact_id", "judgment_fingerprint")
        ):
            raise ValueError(f"judgments[{index}] completed judgment requires frozen evidence")
        judgment_by_candidate[candidate_id] = normalized
    normalized_judgments = []
    for candidate_id in candidate_ids:
        normalized_judgments.append(judgment_by_candidate.get(candidate_id, {
            "candidate_id": candidate_id,
            "status": "pending",
            "judge_id": "",
            "judgment_artifact_id": "",
            "judgment_fingerprint": "",
        }))
    pending_ids = [
        judgment["candidate_id"]
        for judgment in normalized_judgments
        if judgment["status"] == "pending"
    ]
    return {
        "tournament_contract_version": EXPERIMENTAL_TOURNAMENT_CONTRACT_VERSION,
        "tournament_id": source["tournament_id"],
        "candidate_set_fingerprint": source["candidate_set_fingerprint"],
        "comparison_protocol_fingerprint": source["comparison_protocol_fingerprint"],
        "candidates": deepcopy(candidates),
        "judgments": normalized_judgments,
        "pending_candidate_ids": pending_ids,
        "tournament_status": "running" if pending_ids else "completed",
        "candidates_regenerated_on_resume": False,
    }

def record_tournament_provider_timeout(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Record unavailable provider work without changing candidates or selecting a winner."""
    if not isinstance(payload, dict):
        raise TypeError("provider timeout input must be an object")
    tournament = payload.get("tournament_state")
    normalized = resume_frozen_candidate_tournament(tournament)
    for field in (
        "operation_id",
        "candidate_id",
        "provider_id",
        "model_id",
        "attempt_started_at",
        "timeout_recorded_at",
        "timeout_class",
        "diagnostic_artifact_id",
    ):
        if not _non_empty(payload.get(field)):
            raise ValueError(f"{field} must be a non-empty string")
    candidate_id = payload["candidate_id"]
    candidate_ids = [candidate["candidate_id"] for candidate in normalized["candidates"]]
    if candidate_id not in candidate_ids:
        raise ValueError("candidate_id must reference a frozen candidate")
    attempt_number = payload.get("attempt_number")
    timeout_seconds = payload.get("timeout_seconds")
    if not isinstance(attempt_number, int) or isinstance(attempt_number, bool) or attempt_number < 1:
        raise ValueError("attempt_number must be a positive integer")
    if (
        not isinstance(timeout_seconds, (int, float))
        or isinstance(timeout_seconds, bool)
        or timeout_seconds <= 0
    ):
        raise ValueError("timeout_seconds must be a positive number")
    retry_eligible = payload.get("retry_eligible")
    if not isinstance(retry_eligible, bool):
        raise ValueError("retry_eligible must be boolean")
    return {
        "timeout_record_version": "provider-timeout/1",
        "operation_id": payload["operation_id"],
        "tournament_id": normalized["tournament_id"],
        "candidate_id": candidate_id,
        "provider_id": payload["provider_id"],
        "model_id": payload["model_id"],
        "attempt_number": attempt_number,
        "attempt_started_at": payload["attempt_started_at"],
        "timeout_recorded_at": payload["timeout_recorded_at"],
        "timeout_seconds": timeout_seconds,
        "timeout_class": payload["timeout_class"],
        "diagnostic_artifact_id": payload["diagnostic_artifact_id"],
        "retry_eligible": retry_eligible,
        "operation_status": "unavailable",
        "candidate_set_fingerprint": normalized["candidate_set_fingerprint"],
        "comparison_protocol_fingerprint": normalized["comparison_protocol_fingerprint"],
        "candidates": deepcopy(normalized["candidates"]),
        "selection_status": "blocked_no_selection",
        "selected_candidate_id": "",
        "timed_out_candidate_disqualified": False,
        "remaining_candidate_auto_selected": False,
    }

def quarantine_invalid_structured_output(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create bounded diagnostic history while keeping invalid output non-canonical."""
    if not isinstance(payload, dict):
        raise TypeError("invalid structured output input must be an object")
    for field in (
        "operation_id",
        "output_artifact_id",
        "output_fingerprint",
        "expected_schema_id",
        "provider_id",
        "model_id",
        "received_at",
        "canonical_state_fingerprint",
    ):
        if not _non_empty(payload.get(field)):
            raise ValueError(f"{field} must be a non-empty string")
    validation_errors = payload.get("validation_errors")
    if (
        not isinstance(validation_errors, list)
        or not validation_errors
        or any(not _non_empty(error) for error in validation_errors)
    ):
        raise ValueError("validation_errors must be a non-empty string list")
    maximum = payload.get("maximum_attempts")
    attempt = payload.get("attempt_number")
    if not isinstance(maximum, int) or isinstance(maximum, bool) or not 1 <= maximum <= 10:
        raise ValueError("maximum_attempts must be an integer between one and ten")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or not 1 <= attempt <= maximum:
        raise ValueError("attempt_number must be within maximum_attempts")
    history = payload.get("prior_retry_history", [])
    if not isinstance(history, list):
        raise TypeError("prior_retry_history must be an array")
    if len(history) != attempt - 1:
        raise ValueError("prior_retry_history length must precede attempt_number exactly")
    normalized_history = []
    for index, item in enumerate(history):
        if not isinstance(item, dict):
            raise TypeError(f"prior_retry_history[{index}] must be an object")
        expected_attempt = index + 1
        if item.get("attempt_number") != expected_attempt:
            raise ValueError("prior retry attempts must be contiguous and ordered")
        for field in ("output_artifact_id", "output_fingerprint", "diagnostic_summary", "recorded_at"):
            if not _non_empty(item.get(field)):
                raise ValueError(f"prior_retry_history[{index}].{field} must be non-empty")
        normalized_history.append(deepcopy(item))
    normalized_history.append({
        "attempt_number": attempt,
        "output_artifact_id": payload["output_artifact_id"],
        "output_fingerprint": payload["output_fingerprint"],
        "diagnostic_summary": " | ".join(validation_errors),
        "recorded_at": payload["received_at"],
    })
    retry_allowed = attempt < maximum
    return {
        "quarantine_record_version": "invalid-output-quarantine/1",
        "operation_id": payload["operation_id"],
        "expected_schema_id": payload["expected_schema_id"],
        "provider_id": payload["provider_id"],
        "model_id": payload["model_id"],
        "validation_errors": list(validation_errors),
        "retry_history": normalized_history,
        "maximum_attempts": maximum,
        "attempt_number": attempt,
        "retry_allowed": retry_allowed,
        "quarantine_status": "retryable" if retry_allowed else "retry_exhausted",
        "canonical_state_fingerprint_before": payload["canonical_state_fingerprint"],
        "canonical_state_fingerprint_after": payload["canonical_state_fingerprint"],
        "invalid_output_promoted_to_canonical": False,
        "raw_output_embedded_in_canonical": False,
    }

def scope_constitution_conflict_actions(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Route constitutional conflicts to affected actions without freezing unrelated missions."""
    if not isinstance(payload, dict):
        raise TypeError("constitution conflict scope input must be an object")
    for field in (
        "scope_decision_id",
        "constitution_version_id",
        "constitution_fingerprint",
        "safe_exploration_authority_id",
    ):
        if not _non_empty(payload.get(field)):
            raise ValueError(f"{field} must be a non-empty string")
    actions = payload.get("actions")
    if not isinstance(actions, list) or not actions:
        raise ValueError("actions must be a non-empty list")
    action_by_id = {}
    mission_ids = set()
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            raise TypeError(f"actions[{index}] must be an object")
        for field in ("action_id", "mission_id", "action", "authority_evidence_id"):
            if not _non_empty(action.get(field)):
                raise ValueError(f"actions[{index}].{field} must be non-empty")
        action_id = action["action_id"]
        if action_id in action_by_id:
            raise ValueError("action_id must be unique")
        within_safe = action.get("within_safe_exploration_authority")
        if not isinstance(within_safe, bool):
            raise ValueError(f"actions[{index}].within_safe_exploration_authority must be boolean")
        action_by_id[action_id] = deepcopy(action)
        mission_ids.add(action["mission_id"])
    conflicts = payload.get("conflicts")
    if not isinstance(conflicts, list):
        raise TypeError("conflicts must be an array")
    conflicts_by_action = {}
    seen_conflict_ids = set()
    for index, conflict in enumerate(conflicts):
        if not isinstance(conflict, dict):
            raise TypeError(f"conflicts[{index}] must be an object")
        for field in ("conflict_id", "clause_id", "affected_action_id", "conflict_evidence_id"):
            if not _non_empty(conflict.get(field)):
                raise ValueError(f"conflicts[{index}].{field} must be non-empty")
        if conflict["conflict_id"] in seen_conflict_ids:
            raise ValueError("conflict_id must be unique")
        seen_conflict_ids.add(conflict["conflict_id"])
        action_id = conflict["affected_action_id"]
        if action_id not in action_by_id:
            raise ValueError("conflict affected_action_id must reference an action")
        conflicts_by_action.setdefault(action_id, []).append(deepcopy(conflict))
    decisions = []
    blocked_action_ids = []
    safe_exploration_action_ids = []
    unaffected_action_ids = []
    for action in actions:
        action_id = action["action_id"]
        action_conflicts = conflicts_by_action.get(action_id, [])
        if not action_conflicts:
            status = "continue_unaffected"
            unaffected_action_ids.append(action_id)
        elif action["within_safe_exploration_authority"]:
            status = "continue_safe_exploration"
            safe_exploration_action_ids.append(action_id)
        else:
            status = "blocked_constitution_conflict"
            blocked_action_ids.append(action_id)
        decisions.append({
            "action_id": action_id,
            "mission_id": action["mission_id"],
            "status": status,
            "conflict_ids": [item["conflict_id"] for item in action_conflicts],
            "scope_rationale": (
                "No registered conflict reaches this action."
                if not action_conflicts
                else "Conflict is contained within registered safe exploration authority."
                if action["within_safe_exploration_authority"]
                else "Conflict reaches action outside registered safe exploration authority."
            ),
        })
    blocked_mission_ids = sorted({
        action_by_id[action_id]["mission_id"] for action_id in blocked_action_ids
    })
    unaffected_mission_ids = sorted(mission_ids - set(blocked_mission_ids))
    return {
        "scope_record_version": "constitution-conflict-scope/1",
        "scope_decision_id": payload["scope_decision_id"],
        "constitution_version_id": payload["constitution_version_id"],
        "constitution_fingerprint": payload["constitution_fingerprint"],
        "safe_exploration_authority_id": payload["safe_exploration_authority_id"],
        "action_decisions": decisions,
        "blocked_action_ids": blocked_action_ids,
        "safe_exploration_action_ids": safe_exploration_action_ids,
        "unaffected_action_ids": unaffected_action_ids,
        "blocked_mission_ids": blocked_mission_ids,
        "unaffected_mission_ids": unaffected_mission_ids,
        "global_freeze": False,
    }

def resolve_mission_write_fingerprint(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Accept a current mission write or expose the newer wake behind a stale conflict."""
    if not isinstance(payload, dict):
        raise TypeError("mission write request must be an object")
    for field in (
        "write_request_id",
        "mission_id",
        "expected_frontier_fingerprint",
        "current_frontier_fingerprint",
        "proposed_mission_fingerprint",
    ):
        if not _non_empty(payload.get(field)):
            raise ValueError(f"{field} must be a non-empty string")
    stale = payload["expected_frontier_fingerprint"] != payload["current_frontier_fingerprint"]
    if stale:
        newer_wake = payload.get("newer_wake")
        if not isinstance(newer_wake, dict):
            raise ValueError("newer_wake is required for a stale write")
        for field in (
            "wake_id",
            "wake_fingerprint",
            "trigger_id",
            "trigger_evidence_artifact_id",
            "frontier_change_summary",
            "recorded_at",
        ):
            if not _non_empty(newer_wake.get(field)):
                raise ValueError(f"newer_wake.{field} must be a non-empty string")
        return {
            "write_resolution_version": "mission-write-conflict/1",
            "write_request_id": payload["write_request_id"],
            "mission_id": payload["mission_id"],
            "write_status": "stale_write_conflict",
            "expected_frontier_fingerprint": payload["expected_frontier_fingerprint"],
            "current_frontier_fingerprint": payload["current_frontier_fingerprint"],
            "proposed_mission_fingerprint": payload["proposed_mission_fingerprint"],
            "write_applied": False,
            "canonical_mission_fingerprint_after": payload["current_frontier_fingerprint"],
            "newer_wake": deepcopy(newer_wake),
            "rebase_required": True,
        }
    return {
        "write_resolution_version": "mission-write-conflict/1",
        "write_request_id": payload["write_request_id"],
        "mission_id": payload["mission_id"],
        "write_status": "accepted",
        "expected_frontier_fingerprint": payload["expected_frontier_fingerprint"],
        "current_frontier_fingerprint": payload["current_frontier_fingerprint"],
        "proposed_mission_fingerprint": payload["proposed_mission_fingerprint"],
        "write_applied": True,
        "canonical_mission_fingerprint_after": payload["proposed_mission_fingerprint"],
        "newer_wake": {},
        "rebase_required": False,
    }

def restore_selection_preserving_outcomes(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Restore selection state while preserving the append-only outcome observation ledger."""
    if not isinstance(payload, dict):
        raise TypeError("selection restore input must be an object")
    for field in (
        "restore_id",
        "mission_id",
        "target_selection_revision_id",
        "target_selection_fingerprint",
        "target_selection_recorded_at",
        "current_selection_revision_id",
        "current_selection_fingerprint",
        "restore_evidence_artifact_id",
    ):
        if not _non_empty(payload.get(field)):
            raise ValueError(f"{field} must be a non-empty string")
    target_state = payload.get("target_selection_state")
    if not isinstance(target_state, dict) or not target_state:
        raise ValueError("target_selection_state must be a non-empty object")
    observations = payload.get("current_outcome_observations")
    if not isinstance(observations, list):
        raise TypeError("current_outcome_observations must be an array")
    seen_ids = set()
    preserved = []
    later_ids = []
    for index, observation in enumerate(observations):
        if not isinstance(observation, dict):
            raise TypeError(f"current_outcome_observations[{index}] must be an object")
        for field in (
            "observation_id",
            "observation_fingerprint",
            "observed_at",
            "source_selection_revision_id",
            "evidence_artifact_id",
        ):
            if not _non_empty(observation.get(field)):
                raise ValueError(f"current_outcome_observations[{index}].{field} must be non-empty")
        observation_id = observation["observation_id"]
        if observation_id in seen_ids:
            raise ValueError("observation_id must be unique")
        seen_ids.add(observation_id)
        item = deepcopy(observation)
        item["observed_after_target_selection"] = (
            observation["observed_at"] > payload["target_selection_recorded_at"]
        )
        item["source_selection_revision_preserved"] = True
        preserved.append(item)
        if item["observed_after_target_selection"]:
            later_ids.append(observation_id)
    return {
        "restore_record_version": "selection-restore/1",
        "restore_id": payload["restore_id"],
        "mission_id": payload["mission_id"],
        "restored_selection_revision_id": payload["target_selection_revision_id"],
        "restored_selection_fingerprint": payload["target_selection_fingerprint"],
        "restored_selection_state": deepcopy(target_state),
        "replaced_current_selection_revision_id": payload["current_selection_revision_id"],
        "replaced_current_selection_fingerprint": payload["current_selection_fingerprint"],
        "restore_evidence_artifact_id": payload["restore_evidence_artifact_id"],
        "outcome_observations": preserved,
        "later_outcome_observation_ids": later_ids,
        "outcome_observation_count_before": len(observations),
        "outcome_observation_count_after": len(preserved),
        "outcomes_deleted_by_restore": False,
        "later_outcomes_reassigned_to_restored_selection": False,
    }

def build_policy_gated_prompt_context(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Assemble prompt references only after auditable allow, redact, or deny decisions."""
    if not isinstance(payload, dict):
        raise TypeError("prompt context policy input must be an object")
    for field in (
        "prompt_context_id",
        "policy_version_id",
        "policy_fingerprint",
        "model_operation_id",
        "evaluation_recorded_at",
    ):
        if not _non_empty(payload.get(field)):
            raise ValueError(f"{field} must be a non-empty string")
    items = payload.get("context_items")
    decisions = payload.get("policy_decisions")
    if not isinstance(items, list) or not items:
        raise ValueError("context_items must be a non-empty list")
    if not isinstance(decisions, list) or len(decisions) != len(items):
        raise ValueError("policy_decisions must contain one decision per context item")
    item_by_id = {}
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise TypeError(f"context_items[{index}] must be an object")
        for field in (
            "context_item_id",
            "content_artifact_id",
            "content_fingerprint",
            "purpose",
        ):
            if not _non_empty(item.get(field)):
                raise ValueError(f"context_items[{index}].{field} must be non-empty")
        classification = item.get("classification")
        if classification not in {"public", "internal", "confidential", "restricted"}:
            raise ValueError(f"context_items[{index}].classification is not recognized")
        item_id = item["context_item_id"]
        if item_id in item_by_id:
            raise ValueError("context_item_id must be unique")
        item_by_id[item_id] = deepcopy(item)
    decision_by_id = {}
    prompt_items = []
    audit_decisions = []
    for index, decision in enumerate(decisions):
        if not isinstance(decision, dict):
            raise TypeError(f"policy_decisions[{index}] must be an object")
        for field in ("context_item_id", "decision", "policy_rule_id", "decision_rationale"):
            if not _non_empty(decision.get(field)):
                raise ValueError(f"policy_decisions[{index}].{field} must be non-empty")
        item_id = decision["context_item_id"]
        if item_id not in item_by_id:
            raise ValueError("policy decision must reference a context item")
        if item_id in decision_by_id:
            raise ValueError("each context item may have one policy decision")
        item = item_by_id[item_id]
        policy_decision = decision["decision"]
        if policy_decision not in {"allow", "redact", "deny"}:
            raise ValueError(f"policy_decisions[{index}].decision is not recognized")
        if item["classification"] == "restricted" and policy_decision != "deny":
            raise ValueError("restricted context must be denied")
        if item["classification"] == "confidential" and policy_decision != "redact":
            raise ValueError("confidential context must be redacted")
        if decision.get("evaluated_before_prompt_assembly") is not True:
            raise ValueError("policy decision must precede prompt assembly")
        sanitized_artifact_id = str(decision.get("sanitized_artifact_id", "")).strip()
        sanitized_fingerprint = str(decision.get("sanitized_fingerprint", "")).strip()
        redaction_method = str(decision.get("redaction_method", "")).strip()
        if policy_decision == "redact":
            if not sanitized_artifact_id or not sanitized_fingerprint or not redaction_method:
                raise ValueError("redaction requires sanitized artifact, fingerprint, and method")
            prompt_items.append({
                "context_item_id": item_id,
                "source_classification": item["classification"],
                "prompt_artifact_id": sanitized_artifact_id,
                "prompt_artifact_fingerprint": sanitized_fingerprint,
                "policy_decision": "redact",
            })
        elif policy_decision == "allow":
            if sanitized_artifact_id or sanitized_fingerprint or redaction_method:
                raise ValueError("allow decision must not claim redaction artifacts")
            prompt_items.append({
                "context_item_id": item_id,
                "source_classification": item["classification"],
                "prompt_artifact_id": item["content_artifact_id"],
                "prompt_artifact_fingerprint": item["content_fingerprint"],
                "policy_decision": "allow",
            })
        else:
            if sanitized_artifact_id or sanitized_fingerprint:
                raise ValueError("deny decision must not emit a prompt artifact")
        audit_decisions.append({
            "context_item_id": item_id,
            "classification": item["classification"],
            "decision": policy_decision,
            "policy_rule_id": decision["policy_rule_id"],
            "decision_rationale": decision["decision_rationale"],
            "redaction_method": redaction_method,
            "sanitized_artifact_id": sanitized_artifact_id,
            "sanitized_fingerprint": sanitized_fingerprint,
            "evaluated_before_prompt_assembly": True,
        })
        decision_by_id[item_id] = decision
    if set(decision_by_id) != set(item_by_id):
        raise ValueError("every context item must receive exactly one policy decision")
    return {
        "prompt_context_record_version": "policy-gated-context/1",
        "prompt_context_id": payload["prompt_context_id"],
        "policy_version_id": payload["policy_version_id"],
        "policy_fingerprint": payload["policy_fingerprint"],
        "model_operation_id": payload["model_operation_id"],
        "evaluation_recorded_at": payload["evaluation_recorded_at"],
        "prompt_items": prompt_items,
        "audit_decisions": audit_decisions,
        "prompt_assembly_status": "ready" if prompt_items else "blocked_no_authorized_context",
        "unevaluated_context_count": 0,
        "raw_confidential_or_restricted_content_embedded": False,
    }

def activate_external_action_kill_switch(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Stop pending external effects while retaining reconstructable state and observation."""
    if not isinstance(payload, dict):
        raise TypeError("kill switch input must be an object")
    for field in (
        "kill_switch_activation_id",
        "kill_switch_policy_id",
        "trigger_id",
        "trigger_evidence_artifact_id",
        "activated_at",
    ):
        if not _non_empty(payload.get(field)):
            raise ValueError(f"{field} must be a non-empty string")
    authorities = payload.get("authorizing_principals")
    if (
        not isinstance(authorities, list)
        or not authorities
        or any(authority not in {"human_operator", "independent_governance", "palamedes"} for authority in authorities)
        or len(set(authorities)) != len(authorities)
    ):
        raise ValueError("authorizing_principals must be a unique recognized list")
    if set(authorities) == {"palamedes"}:
        raise ValueError("Palamedes cannot solely authorize its kill switch")
    if not ({"human_operator", "independent_governance"} & set(authorities)):
        raise ValueError("kill switch requires human or independent governance authority")
    actions = payload.get("actions")
    if not isinstance(actions, list):
        raise TypeError("actions must be an array")
    action_records = []
    stopped_ids = []
    retained_completed_ids = []
    continuing_observation_ids = []
    seen_ids = set()
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            raise TypeError(f"actions[{index}] must be an object")
        for field in ("action_id", "scope", "status", "action_fingerprint"):
            if not _non_empty(action.get(field)):
                raise ValueError(f"actions[{index}].{field} must be non-empty")
        action_id = action["action_id"]
        if action_id in seen_ids:
            raise ValueError("action_id must be unique")
        seen_ids.add(action_id)
        scope = action["scope"]
        status = action["status"]
        if scope not in {"external_effect", "internal_observation"}:
            raise ValueError(f"actions[{index}].scope is not recognized")
        if status not in {"queued", "running", "completed"}:
            raise ValueError(f"actions[{index}].status is not recognized")
        if scope == "external_effect" and status == "queued":
            resulting_status = "cancelled_by_kill_switch"
            stopped_ids.append(action_id)
        elif scope == "external_effect" and status == "running":
            resulting_status = "stopped_by_kill_switch"
            stopped_ids.append(action_id)
        elif scope == "external_effect":
            resulting_status = "completed_immutable"
            retained_completed_ids.append(action_id)
        else:
            resulting_status = status
            continuing_observation_ids.append(action_id)
        action_records.append({
            "action_id": action_id,
            "scope": scope,
            "prior_status": status,
            "resulting_status": resulting_status,
            "action_fingerprint": action["action_fingerprint"],
            "record_retained": True,
        })
    artifacts = payload.get("state_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError("state_artifacts must be a non-empty list")
    retained_artifacts = []
    seen_artifacts = set()
    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            raise TypeError(f"state_artifacts[{index}] must be an object")
        for field in ("artifact_id", "artifact_fingerprint", "artifact_role"):
            if not _non_empty(artifact.get(field)):
                raise ValueError(f"state_artifacts[{index}].{field} must be non-empty")
        if artifact["artifact_id"] in seen_artifacts:
            raise ValueError("state artifact IDs must be unique")
        seen_artifacts.add(artifact["artifact_id"])
        retained = deepcopy(artifact)
        retained["retained_for_reconstruction"] = True
        retained_artifacts.append(retained)
    return {
        "kill_switch_record_version": "external-action-kill-switch/1",
        "kill_switch_activation_id": payload["kill_switch_activation_id"],
        "kill_switch_policy_id": payload["kill_switch_policy_id"],
        "trigger_id": payload["trigger_id"],
        "trigger_evidence_artifact_id": payload["trigger_evidence_artifact_id"],
        "activated_at": payload["activated_at"],
        "authorizing_principals": list(authorities),
        "action_records": action_records,
        "stopped_external_action_ids": stopped_ids,
        "retained_completed_action_ids": retained_completed_ids,
        "continuing_internal_observation_ids": continuing_observation_ids,
        "retained_state_artifacts": retained_artifacts,
        "external_action_dispatch_enabled": False,
        "state_deleted": False,
        "palamedes_can_self_reenable": False,
        "reenable_requires_external_authority": True,
    }

def apply_failure_thesis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Fail closed on commitment while retaining bounded observation and contradiction."""
    if not isinstance(payload, dict):
        raise TypeError("failure thesis input must be an object")
    for field in (
        "failure_decision_id",
        "failure_policy_id",
        "failure_policy_fingerprint",
        "observation_authority_id",
    ):
        if not _non_empty(payload.get(field)):
            raise ValueError(f"{field} must be a non-empty string")
    failures = payload.get("unresolved_failures")
    if not isinstance(failures, list) or not failures:
        raise ValueError("unresolved_failures must be a non-empty list")
    seen_failures = set()
    normalized_failures = []
    for index, failure in enumerate(failures):
        if not isinstance(failure, dict):
            raise TypeError(f"unresolved_failures[{index}] must be an object")
        for field in ("failure_id", "failure_type", "evidence_artifact_id", "failure_fingerprint"):
            if not _non_empty(failure.get(field)):
                raise ValueError(f"unresolved_failures[{index}].{field} must be non-empty")
        if failure["failure_id"] in seen_failures:
            raise ValueError("failure_id must be unique")
        seen_failures.add(failure["failure_id"])
        normalized_failures.append(deepcopy(failure))
    operations = payload.get("proposed_operations")
    if not isinstance(operations, list):
        raise TypeError("proposed_operations must be an array")
    maximum_observations = payload.get("maximum_observation_operations")
    if (
        not isinstance(maximum_observations, int)
        or isinstance(maximum_observations, bool)
        or maximum_observations < 0
    ):
        raise ValueError("maximum_observation_operations must be a non-negative integer")
    decisions = []
    observation_count = 0
    for index, operation in enumerate(operations):
        if not isinstance(operation, dict):
            raise TypeError(f"proposed_operations[{index}] must be an object")
        for field in ("operation_id", "operation_type", "operation_fingerprint"):
            if not _non_empty(operation.get(field)):
                raise ValueError(f"proposed_operations[{index}].{field} must be non-empty")
        operation_type = operation["operation_type"]
        if operation_type not in {"mission_commitment", "external_effect", "observation"}:
            raise ValueError(f"proposed_operations[{index}].operation_type is not recognized")
        if operation_type == "observation":
            observation_count += 1
            bounded = (
                operation.get("read_only") is True
                and operation.get("bounded") is True
                and operation.get("authority_id") == payload["observation_authority_id"]
                and observation_count <= maximum_observations
            )
            status = "allowed_bounded_observation" if bounded else "blocked_unbounded_observation"
        else:
            status = "blocked_unresolved_failure"
        decisions.append({
            "operation_id": operation["operation_id"],
            "operation_type": operation_type,
            "operation_fingerprint": operation["operation_fingerprint"],
            "status": status,
            "external_effect_allowed": False,
        })
    contradictions = payload.get("contradictory_evidence")
    if not isinstance(contradictions, list) or not contradictions:
        raise ValueError("contradictory_evidence must be a non-empty list")
    preserved = []
    seen_evidence = set()
    for index, evidence in enumerate(contradictions):
        if not isinstance(evidence, dict):
            raise TypeError(f"contradictory_evidence[{index}] must be an object")
        for field in (
            "evidence_id",
            "evidence_fingerprint",
            "source_artifact_id",
            "contradicts_claim_id",
        ):
            if not _non_empty(evidence.get(field)):
                raise ValueError(f"contradictory_evidence[{index}].{field} must be non-empty")
        if evidence["evidence_id"] in seen_evidence:
            raise ValueError("contradictory evidence IDs must be unique")
        seen_evidence.add(evidence["evidence_id"])
        item = deepcopy(evidence)
        item["preserved"] = True
        item["deleted_for_consistency"] = False
        preserved.append(item)
    return {
        "failure_record_version": "failure-thesis/1",
        "failure_decision_id": payload["failure_decision_id"],
        "failure_policy_id": payload["failure_policy_id"],
        "failure_policy_fingerprint": payload["failure_policy_fingerprint"],
        "unresolved_failures": normalized_failures,
        "operation_decisions": decisions,
        "mission_commitment_gate": "closed",
        "external_effect_gate": "closed",
        "observation_gate": "bounded_open",
        "maximum_observation_operations": maximum_observations,
        "preserved_contradictory_evidence": preserved,
        "contradictory_evidence_count_before": len(contradictions),
        "contradictory_evidence_count_after": len(preserved),
        "consistency_repaired_by_evidence_deletion": False,
    }

def run_bounded_signal_to_mission_vertical_slice(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Compile linked semantic artifacts into a mission contract and accept outcome intake only."""
    if not isinstance(payload, dict):
        raise TypeError("vertical slice input must be an object")
    for forbidden in ("execution_tasks", "tool_calls", "external_actions", "implementation_steps"):
        if forbidden in payload:
            raise ValueError(f"{forbidden} is outside the bounded vertical slice")
    for field in ("vertical_slice_id", "slice_protocol_id", "slice_fingerprint"):
        if not _non_empty(payload.get(field)):
            raise ValueError(f"{field} must be a non-empty string")
    signal = payload.get("signal")
    interpretation = payload.get("interpretation")
    selection = payload.get("selection")
    mission_contract = payload.get("mission_contract")
    for name, artifact in (
        ("signal", signal),
        ("interpretation", interpretation),
        ("selection", selection),
        ("mission_contract", mission_contract),
    ):
        if not isinstance(artifact, dict):
            raise TypeError(f"{name} must be an object")
    for field in ("signal_id", "signal_fingerprint", "observed_at", "evidence_artifact_id"):
        if not _non_empty(signal.get(field)):
            raise ValueError(f"signal.{field} must be non-empty")
    for field in (
        "interpretation_id",
        "interpretation_fingerprint",
        "source_signal_id",
        "created_at",
        "causal_thesis",
    ):
        if not _non_empty(interpretation.get(field)):
            raise ValueError(f"interpretation.{field} must be non-empty")
    if interpretation["source_signal_id"] != signal["signal_id"]:
        raise ValueError("interpretation must reference the signal")
    if interpretation["created_at"] < signal["observed_at"]:
        raise ValueError("interpretation cannot precede signal observation")
    candidates = payload.get("mission_candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("mission_candidates must be a non-empty list")
    candidate_ids = []
    normalized_candidates = []
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, dict):
            raise TypeError(f"mission_candidates[{index}] must be an object")
        for field in (
            "candidate_id",
            "candidate_fingerprint",
            "source_interpretation_id",
            "beneficiary",
            "desired_change",
        ):
            if not _non_empty(candidate.get(field)):
                raise ValueError(f"mission_candidates[{index}].{field} must be non-empty")
        if candidate["source_interpretation_id"] != interpretation["interpretation_id"]:
            raise ValueError("every mission candidate must reference the interpretation")
        if candidate["candidate_id"] in candidate_ids:
            raise ValueError("candidate_id must be unique")
        candidate_ids.append(candidate["candidate_id"])
        normalized_candidates.append(deepcopy(candidate))
    for field in (
        "selection_id",
        "selection_fingerprint",
        "candidate_set_fingerprint",
        "selected_candidate_id",
        "selected_at",
        "selection_rationale",
    ):
        if not _non_empty(selection.get(field)):
            raise ValueError(f"selection.{field} must be non-empty")
    if selection["selected_candidate_id"] not in candidate_ids:
        raise ValueError("selection must reference a mission candidate")
    if selection["selected_at"] < interpretation["created_at"]:
        raise ValueError("selection cannot precede interpretation")
    for field in (
        "mission_contract_id",
        "mission_contract_version",
        "mission_contract_fingerprint",
        "source_selection_id",
        "source_candidate_id",
        "issued_at",
        "planner_handoff_artifact_id",
        "outcome_intake_contract_id",
    ):
        if not _non_empty(mission_contract.get(field)):
            raise ValueError(f"mission_contract.{field} must be non-empty")
    if mission_contract["source_selection_id"] != selection["selection_id"]:
        raise ValueError("mission contract must reference the selection")
    if mission_contract["source_candidate_id"] != selection["selected_candidate_id"]:
        raise ValueError("mission contract must reference the selected candidate")
    if mission_contract["issued_at"] < selection["selected_at"]:
        raise ValueError("mission contract cannot precede selection")
    outcome_intake = payload.get("outcome_intake", [])
    if not isinstance(outcome_intake, list):
        raise TypeError("outcome_intake must be an array")
    normalized_outcomes = []
    seen_outcomes = set()
    for index, outcome in enumerate(outcome_intake):
        if not isinstance(outcome, dict):
            raise TypeError(f"outcome_intake[{index}] must be an object")
        for field in (
            "outcome_observation_id",
            "outcome_fingerprint",
            "mission_contract_id",
            "observed_at",
            "evidence_artifact_id",
        ):
            if not _non_empty(outcome.get(field)):
                raise ValueError(f"outcome_intake[{index}].{field} must be non-empty")
        if outcome["mission_contract_id"] != mission_contract["mission_contract_id"]:
            raise ValueError("outcome intake must reference the issued mission contract")
        if outcome["observed_at"] < mission_contract["issued_at"]:
            raise ValueError("outcome observation cannot precede mission contract")
        if outcome["outcome_observation_id"] in seen_outcomes:
            raise ValueError("outcome observation IDs must be unique")
        seen_outcomes.add(outcome["outcome_observation_id"])
        normalized_outcomes.append(deepcopy(outcome))
    return {
        "vertical_slice_record_version": "signal-to-mission-slice/1",
        "vertical_slice_id": payload["vertical_slice_id"],
        "slice_protocol_id": payload["slice_protocol_id"],
        "slice_fingerprint": payload["slice_fingerprint"],
        "signal": deepcopy(signal),
        "interpretation": deepcopy(interpretation),
        "mission_candidates": normalized_candidates,
        "selection": deepcopy(selection),
        "mission_contract": deepcopy(mission_contract),
        "outcome_intake": normalized_outcomes,
        "ordered_stage_ids": [
            signal["signal_id"],
            interpretation["interpretation_id"],
            selection["selection_id"],
            mission_contract["mission_contract_id"],
        ],
        "authority_endpoint": "mission_contract_and_outcome_intake",
        "execution_platform_capability": False,
        "execution_objects_emitted": 0,
    }

OWNER_DERIVED_SOURCE_KINDS = {"owner_preference"}

CONSTITUTION_AMENDMENT_OPERATIONS = {"add", "modify", "retire"}

VALUE_CONSEQUENCE_DIMENSIONS = {
    "beneficiary_change",
    "harm",
    "sustainability",
    "option_value",
    "resource_renewal",
}

VALUE_CONSEQUENCE_DIRECTIONS = {"benefit", "cost", "uncertain"}

MISSION_COMPARISON_RELATIONS = {
    "left_better",
    "right_better",
    "equal",
    "unknown",
}

MISSION_OVERALL_RELATIONS = {
    "left_dominates",
    "right_dominates",
    "equivalent",
    "incomparable",
}

INCOMPARABLE_ACTION_KINDS = {"probe", "defer"}

REVERSIBILITY_LEVELS = {"reversible", "partially_reversible", "irreversible"}

PROBE_RISK_LEVELS = {"minimal", "low", "moderate", "high"}

CONSENT_STATUSES = {"obtained", "not_required", "unavailable", "refused"}

REPRESENTATION_STATUSES = {"direct", "proxy", "unrepresented", "future"}

PREFERENCE_PROVENANCE_KINDS = {
    "direct_statement",
    "observed_behavior",
    "proxy_report",
    "inference",
    "simulation",
}

VALUE_STATE_COMPONENTS = {
    "principles",
    "preference_claims",
    "prohibitions",
    "uncertainties",
    "precedents",
}

CONSTITUTION_CLAUSE_KINDS = {
    "principle",
    "prohibition",
    "priority_rule",
    "standing_obligation",
}

REQUEST_SOLUTION_STATUSES = {"plausible", "uncertain", "contradicted"}

BEHAVIOR_CONFOUND_KINDS = {
    "constraint",
    "habit",
    "manipulation",
    "missing_alternative",
}

DESIRE_SIGNAL_KINDS = {
    "speech",
    "behavior",
    "sacrifice",
    "recurrence",
    "counterfactual_choice",
    "emotional_consequence",
}

DESIRE_UPDATE_OPERATIONS = {"strengthen", "weaken", "revise", "retire"}

def _non_empty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())

def validate_worthwhile_basis(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Validate that a mission's worth is not inferred from owner imitation alone."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["worthwhile basis must be an object"]}

    for field in ("beneficiary_condition", "why_now", "disconfirming_condition"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")

    sources = payload.get("value_sources")
    if not isinstance(sources, list) or not sources:
        errors.append("value_sources must be a non-empty array")
        sources = []

    source_ids = set()
    source_kinds = set()
    for index, source in enumerate(sources):
        prefix = f"value_sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{prefix} must be an object")
            continue
        source_id = source.get("source_id")
        kind = source.get("kind")
        claim = source.get("claim")
        if not _non_empty(source_id):
            errors.append(f"{prefix}.source_id must be a non-empty string")
        elif source_id in source_ids:
            errors.append(f"{prefix}.source_id must be unique")
        else:
            source_ids.add(source_id)
        if kind not in WORTHWHILE_SOURCE_KINDS:
            errors.append(
                f"{prefix}.kind must be one of {sorted(WORTHWHILE_SOURCE_KINDS)}"
            )
        else:
            source_kinds.add(kind)
        if not _non_empty(claim):
            errors.append(f"{prefix}.claim must be a non-empty string")

    independent_kinds = source_kinds - OWNER_DERIVED_SOURCE_KINDS
    if sources and not independent_kinds:
        errors.append(
            "value_sources must include at least one non-owner source; "
            "owner preference alone cannot establish worthwhile"
        )

    return {
        "valid": not errors,
        "errors": errors,
        "source_kinds": sorted(source_kinds),
        "independent_source_kinds": sorted(independent_kinds),
    }

def require_worthwhile_basis(payload: Dict[str, Any]) -> Dict[str, Any]:
    report = validate_worthwhile_basis(payload)
    if not report["valid"]:
        raise ValueError("invalid worthwhile basis: " + "; ".join(report["errors"]))
    return payload

def validate_constitution_revision(
    current: Dict[str, Any],
    proposed: Dict[str, Any],
) -> Dict[str, Any]:
    """Require constitutions to evolve as traceable successor versions."""
    errors: List[str] = []
    if not isinstance(current, dict):
        return {"valid": False, "errors": ["current constitution must be an object"]}
    if not isinstance(proposed, dict):
        return {"valid": False, "errors": ["proposed constitution revision must be an object"]}

    current_version = current.get("version")
    proposed_version = proposed.get("version")
    parent_version = proposed.get("parent_version")
    if not isinstance(current_version, int) or current_version < 1:
        errors.append("current.version must be an integer >= 1")
    if not isinstance(proposed_version, int):
        errors.append("proposed.version must be an integer")
    elif isinstance(current_version, int) and proposed_version != current_version + 1:
        errors.append("proposed.version must be exactly current.version + 1")
    if parent_version != current_version:
        errors.append("proposed.parent_version must equal current.version")

    if not _non_empty(proposed.get("revision_reason")):
        errors.append("proposed.revision_reason must be a non-empty string")
    trigger_sources = proposed.get("trigger_sources")
    if (
        not isinstance(trigger_sources, list)
        or not trigger_sources
        or any(not _non_empty(item) for item in trigger_sources)
    ):
        errors.append("proposed.trigger_sources must be a non-empty array of source IDs")

    amendments = proposed.get("amendments")
    if not isinstance(amendments, list) or not amendments:
        errors.append("proposed.amendments must be a non-empty array")
        amendments = []
    touched_clause_ids = set()
    for index, amendment in enumerate(amendments):
        prefix = f"proposed.amendments[{index}]"
        if not isinstance(amendment, dict):
            errors.append(f"{prefix} must be an object")
            continue
        operation = amendment.get("operation")
        clause_id = amendment.get("clause_id")
        if operation not in CONSTITUTION_AMENDMENT_OPERATIONS:
            errors.append(
                f"{prefix}.operation must be one of "
                f"{sorted(CONSTITUTION_AMENDMENT_OPERATIONS)}"
            )
        if not _non_empty(clause_id):
            errors.append(f"{prefix}.clause_id must be a non-empty string")
        elif clause_id in touched_clause_ids:
            errors.append(f"{prefix}.clause_id must be unique within the revision")
        else:
            touched_clause_ids.add(clause_id)
        if not _non_empty(amendment.get("rationale")):
            errors.append(f"{prefix}.rationale must be a non-empty string")
        evidence_ids = amendment.get("evidence_ids")
        if (
            not isinstance(evidence_ids, list)
            or not evidence_ids
            or any(not _non_empty(item) for item in evidence_ids)
        ):
            errors.append(f"{prefix}.evidence_ids must be a non-empty array of source IDs")
        if operation in {"add", "modify"} and not _non_empty(amendment.get("new_text")):
            errors.append(f"{prefix}.new_text must be a non-empty string for {operation}")
        if operation == "retire" and _non_empty(amendment.get("new_text")):
            errors.append(f"{prefix}.new_text must be empty for retire")

    return {
        "valid": not errors,
        "errors": errors,
        "current_version": current_version,
        "proposed_version": proposed_version,
        "touched_clause_ids": sorted(touched_clause_ids),
    }

def validate_plural_value_consequences(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Reject mission worth represented as one optimized outcome reward."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["value consequences must be an object"]}
    for forbidden in ("reward", "aggregate_score", "utility"):
        if forbidden in payload:
            errors.append(f"{forbidden} is forbidden; preserve plural consequence dimensions")

    consequences = payload.get("consequences")
    if not isinstance(consequences, list) or len(consequences) < 2:
        errors.append("consequences must contain at least two plural dimensions")
        consequences = []
    dimensions = set()
    for index, consequence in enumerate(consequences):
        prefix = f"consequences[{index}]"
        if not isinstance(consequence, dict):
            errors.append(f"{prefix} must be an object")
            continue
        dimension = consequence.get("dimension")
        if dimension not in VALUE_CONSEQUENCE_DIMENSIONS:
            errors.append(
                f"{prefix}.dimension must be one of "
                f"{sorted(VALUE_CONSEQUENCE_DIMENSIONS)}"
            )
        elif dimension in dimensions:
            errors.append(f"{prefix}.dimension must be unique")
        else:
            dimensions.add(dimension)
        if consequence.get("direction") not in VALUE_CONSEQUENCE_DIRECTIONS:
            errors.append(
                f"{prefix}.direction must be one of "
                f"{sorted(VALUE_CONSEQUENCE_DIRECTIONS)}"
            )
        if not _non_empty(consequence.get("claim")):
            errors.append(f"{prefix}.claim must be a non-empty string")
        evidence_ids = consequence.get("evidence_ids")
        if not isinstance(evidence_ids, list) or any(
            not _non_empty(item) for item in evidence_ids
        ):
            errors.append(f"{prefix}.evidence_ids must be an array of source IDs")

    if consequences and "beneficiary_change" not in dimensions:
        errors.append("consequences must include beneficiary_change")
    if consequences and not dimensions.intersection({"harm", "sustainability"}):
        errors.append("consequences must include harm or sustainability")

    return {
        "valid": not errors,
        "errors": errors,
        "dimensions": sorted(dimensions),
    }

def validate_plural_mission_comparison(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Validate a partial-order comparison without forcing a total rank."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["mission comparison must be an object"]}
    for forbidden in ("rank", "score", "winner"):
        if forbidden in payload:
            errors.append(f"{forbidden} is forbidden in plural mission comparison")

    left_id = payload.get("left_mission_id")
    right_id = payload.get("right_mission_id")
    if not _non_empty(left_id):
        errors.append("left_mission_id must be a non-empty string")
    if not _non_empty(right_id):
        errors.append("right_mission_id must be a non-empty string")
    if _non_empty(left_id) and left_id == right_id:
        errors.append("left_mission_id and right_mission_id must differ")

    overall = payload.get("overall_relation")
    if overall not in MISSION_OVERALL_RELATIONS:
        errors.append(
            f"overall_relation must be one of {sorted(MISSION_OVERALL_RELATIONS)}"
        )
    comparisons = payload.get("dimension_comparisons")
    if not isinstance(comparisons, list) or not comparisons:
        errors.append("dimension_comparisons must be a non-empty array")
        comparisons = []
    dimensions = set()
    observed_relations = set()
    for index, comparison in enumerate(comparisons):
        prefix = f"dimension_comparisons[{index}]"
        if not isinstance(comparison, dict):
            errors.append(f"{prefix} must be an object")
            continue
        dimension = comparison.get("dimension")
        relation = comparison.get("relation")
        if dimension not in VALUE_CONSEQUENCE_DIMENSIONS:
            errors.append(
                f"{prefix}.dimension must be one of "
                f"{sorted(VALUE_CONSEQUENCE_DIMENSIONS)}"
            )
        elif dimension in dimensions:
            errors.append(f"{prefix}.dimension must be unique")
        else:
            dimensions.add(dimension)
        if relation not in MISSION_COMPARISON_RELATIONS:
            errors.append(
                f"{prefix}.relation must be one of "
                f"{sorted(MISSION_COMPARISON_RELATIONS)}"
            )
        else:
            observed_relations.add(relation)
        if not _non_empty(comparison.get("reason")):
            errors.append(f"{prefix}.reason must be a non-empty string")

    if overall == "left_dominates" and (
        "right_better" in observed_relations
        or "unknown" in observed_relations
        or "left_better" not in observed_relations
    ):
        errors.append(
            "left_dominates requires at least one left_better and no right_better or unknown"
        )
    if overall == "right_dominates" and (
        "left_better" in observed_relations
        or "unknown" in observed_relations
        or "right_better" not in observed_relations
    ):
        errors.append(
            "right_dominates requires at least one right_better and no left_better or unknown"
        )
    if overall == "equivalent" and observed_relations != {"equal"}:
        errors.append("equivalent requires every dimension relation to be equal")
    if (
        comparisons
        and (
            {"left_better", "right_better"}.issubset(observed_relations)
            or "unknown" in observed_relations
        )
        and overall != "incomparable"
    ):
        errors.append(
            "mixed or unknown dimension relations require overall_relation=incomparable"
        )

    return {
        "valid": not errors,
        "errors": errors,
        "dimensions": sorted(dimensions),
        "observed_relations": sorted(observed_relations),
    }

def validate_incomparable_next_action(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Choose information or waiting without pretending value conflict is resolved."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["incomparable next action must be an object"]}
    if payload.get("comparison_relation") != "incomparable":
        errors.append("comparison_relation must be incomparable")
    action_kind = payload.get("action_kind")
    if action_kind not in INCOMPARABLE_ACTION_KINDS:
        errors.append(f"action_kind must be one of {sorted(INCOMPARABLE_ACTION_KINDS)}")
    if payload.get("value_conflict_resolved") is not False:
        errors.append("value_conflict_resolved must be false")

    reversibility = payload.get("reversibility")
    if not isinstance(reversibility, dict):
        errors.append("reversibility must be an object")
        reversibility = {}
    level = reversibility.get("level")
    if level not in REVERSIBILITY_LEVELS:
        errors.append(f"reversibility.level must be one of {sorted(REVERSIBILITY_LEVELS)}")
    if level == "irreversible":
        errors.append("incomparable next action cannot be irreversible")
    if action_kind == "probe" and not _non_empty(reversibility.get("rollback")):
        errors.append("probe reversibility.rollback must be a non-empty string")

    information_gain = payload.get("information_gain")
    if action_kind == "probe":
        if not isinstance(information_gain, dict):
            errors.append("probe information_gain must be an object")
            information_gain = {}
        if not _non_empty(information_gain.get("uncertainty")):
            errors.append("information_gain.uncertainty must be a non-empty string")
        observations = information_gain.get("distinguishing_observations")
        if (
            not isinstance(observations, list)
            or len(observations) < 2
            or any(not _non_empty(item) for item in observations)
        ):
            errors.append(
                "information_gain.distinguishing_observations must contain at least two observations"
            )
    elif action_kind == "defer":
        if not _non_empty(payload.get("wake_trigger")):
            errors.append("defer wake_trigger must be a non-empty string")

    return {
        "valid": not errors,
        "errors": errors,
        "action_kind": action_kind,
        "reversibility_level": level,
    }

def validate_probe_safety(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure information gain stays subordinate to harm and consent."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["probe safety must be an object"]}
    risk_level = payload.get("risk_level")
    consent_status = payload.get("consent_status")
    if risk_level not in PROBE_RISK_LEVELS:
        errors.append(f"risk_level must be one of {sorted(PROBE_RISK_LEVELS)}")
    if consent_status not in CONSENT_STATUSES:
        errors.append(f"consent_status must be one of {sorted(CONSENT_STATUSES)}")
    affected = payload.get("affected_parties")
    if not isinstance(affected, list) or not affected or any(
        not _non_empty(item) for item in affected
    ):
        errors.append("affected_parties must be a non-empty array")
    for field in ("harm_ceiling", "mitigation", "stop_condition"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    reversible = payload.get("reversible")
    if reversible is not True:
        errors.append("probe must be reversible")
    external_action = payload.get("external_action")
    if not isinstance(external_action, bool):
        errors.append("external_action must be a boolean")

    if consent_status == "refused":
        errors.append("probe is forbidden when consent is refused")
    if risk_level in {"moderate", "high"} and consent_status != "obtained":
        errors.append("moderate or high risk probe requires obtained consent")
    if consent_status == "unavailable" and (
        risk_level != "minimal" or external_action is not False
    ):
        errors.append(
            "unavailable consent permits only minimal-risk probes without external action"
        )

    return {
        "valid": not errors,
        "errors": errors,
        "risk_level": risk_level,
        "consent_status": consent_status,
    }

def validate_representation_gaps(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Make missing and future beneficiaries explicit without treating silence as consent."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["representation state must be an object"]}
    groups = payload.get("affected_groups")
    if not isinstance(groups, list) or not groups:
        errors.append("affected_groups must be a non-empty array")
        groups = []
    group_ids = set()
    gap_group_ids = []
    for index, group in enumerate(groups):
        prefix = f"affected_groups[{index}]"
        if not isinstance(group, dict):
            errors.append(f"{prefix} must be an object")
            continue
        group_id = group.get("group_id")
        status = group.get("representation_status")
        if not _non_empty(group_id):
            errors.append(f"{prefix}.group_id must be a non-empty string")
        elif group_id in group_ids:
            errors.append(f"{prefix}.group_id must be unique")
        else:
            group_ids.add(group_id)
        if status not in REPRESENTATION_STATUSES:
            errors.append(
                f"{prefix}.representation_status must be one of "
                f"{sorted(REPRESENTATION_STATUSES)}"
            )
        if status in {"proxy", "unrepresented", "future"}:
            gap_group_ids.append(group_id)
            if not _non_empty(group.get("representation_limit")):
                errors.append(f"{prefix}.representation_limit must be a non-empty string")
            if not _non_empty(group.get("gap_mitigation")):
                errors.append(f"{prefix}.gap_mitigation must be a non-empty string")
    if gap_group_ids and payload.get("silence_is_consent") is not False:
        errors.append("silence_is_consent must be false when representation gaps exist")
    return {
        "valid": not errors,
        "errors": errors,
        "gap_group_ids": sorted(item for item in gap_group_ids if _non_empty(item)),
    }

def validate_beneficiary_preference_claim(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Prevent representation gaps from being filled with unlabeled invented preferences."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["beneficiary preference claim must be an object"]}
    for field in ("claim_id", "group_id", "claim", "limitations"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    kind = payload.get("provenance_kind")
    if kind not in PREFERENCE_PROVENANCE_KINDS:
        errors.append(
            f"provenance_kind must be one of {sorted(PREFERENCE_PROVENANCE_KINDS)}"
        )
    source_ids = payload.get("source_ids")
    if not isinstance(source_ids, list) or any(not _non_empty(item) for item in source_ids):
        errors.append("source_ids must be an array of source IDs")
    if kind in {"direct_statement", "observed_behavior", "proxy_report"} and not source_ids:
        errors.append(f"{kind} requires at least one source ID")
    confidence = payload.get("confidence")
    if not isinstance(confidence, int) or isinstance(confidence, bool) or not 0 <= confidence <= 100:
        errors.append("confidence must be an integer from 0 to 100")
    if kind == "inference" and isinstance(confidence, int) and confidence > 60:
        errors.append("inference confidence cannot exceed 60")
    if kind == "simulation" and isinstance(confidence, int) and confidence > 40:
        errors.append("simulation confidence cannot exceed 40")
    if kind in {"inference", "simulation"} and payload.get("asserted_as_fact") is not False:
        errors.append(f"{kind} preference cannot be asserted as fact")
    return {"valid": not errors, "errors": errors, "provenance_kind": kind}

def validate_plural_value_state(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Assemble plural value inputs without collapsing them into one score."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["plural value state must be an object"]}
    for field in ("state_id", "as_of"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    forbidden = {"score", "utility", "reward", "objective", "weights"} & set(payload)
    if forbidden:
        errors.append(
            "plural value state cannot contain scalarizing fields: "
            + ", ".join(sorted(forbidden))
        )

    all_ids = set()
    component_counts: Dict[str, int] = {}
    for component in sorted(VALUE_STATE_COMPONENTS):
        entries = payload.get(component)
        if not isinstance(entries, list) or not entries:
            errors.append(f"{component} must be a non-empty array")
            component_counts[component] = 0
            continue
        component_counts[component] = len(entries)
        for index, entry in enumerate(entries):
            prefix = f"{component}[{index}]"
            if not isinstance(entry, dict):
                errors.append(f"{prefix} must be an object")
                continue
            item_id = entry.get("id")
            if not _non_empty(item_id):
                errors.append(f"{prefix}.id must be a non-empty string")
            elif item_id in all_ids:
                errors.append(f"{prefix}.id must be globally unique")
            else:
                all_ids.add(item_id)
            if not _non_empty(entry.get("claim")):
                errors.append(f"{prefix}.claim must be a non-empty string")
            source_ids = entry.get("source_ids")
            if (
                not isinstance(source_ids, list)
                or not source_ids
                or any(not _non_empty(source_id) for source_id in source_ids)
            ):
                errors.append(f"{prefix}.source_ids must be a non-empty source ID array")

    return {
        "valid": not errors,
        "errors": errors,
        "component_counts": component_counts,
    }

def validate_value_constitution_binding(
    constitution: Dict[str, Any],
    value_state: Dict[str, Any],
) -> Dict[str, Any]:
    """Bind a plural value state to one revisable, provenance-bearing constitution."""
    errors: List[str] = []
    if not isinstance(constitution, dict):
        return {"valid": False, "errors": ["constitution must be an object"]}
    if not isinstance(value_state, dict):
        return {"valid": False, "errors": ["value_state must be an object"]}

    constitution_id = constitution.get("constitution_id")
    if not _non_empty(constitution_id):
        errors.append("constitution.constitution_id must be a non-empty string")
    version = constitution.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        errors.append("constitution.version must be an integer >= 1")
    if version == 1 and constitution.get("parent_version") is not None:
        errors.append("constitution.parent_version must be null for version 1")
    if isinstance(version, int) and version > 1:
        if constitution.get("parent_version") != version - 1:
            errors.append("constitution.parent_version must equal version - 1")
    revision_triggers = constitution.get("revision_triggers")
    if (
        not isinstance(revision_triggers, list)
        or not revision_triggers
        or any(not _non_empty(item) for item in revision_triggers)
    ):
        errors.append("constitution.revision_triggers must be a non-empty string array")
    if any(field in constitution for field in ("objective_score", "reward", "weights")):
        errors.append("constitution cannot scalarize plural values")

    clauses = constitution.get("clauses")
    if not isinstance(clauses, list) or not clauses:
        errors.append("constitution.clauses must be a non-empty array")
        clauses = []
    clause_ids = set()
    clause_kinds = set()
    for index, clause in enumerate(clauses):
        prefix = f"constitution.clauses[{index}]"
        if not isinstance(clause, dict):
            errors.append(f"{prefix} must be an object")
            continue
        clause_id = clause.get("clause_id")
        if not _non_empty(clause_id):
            errors.append(f"{prefix}.clause_id must be a non-empty string")
        elif clause_id in clause_ids:
            errors.append(f"{prefix}.clause_id must be unique")
        else:
            clause_ids.add(clause_id)
        kind = clause.get("kind")
        if kind not in CONSTITUTION_CLAUSE_KINDS:
            errors.append(
                f"{prefix}.kind must be one of {sorted(CONSTITUTION_CLAUSE_KINDS)}"
            )
        else:
            clause_kinds.add(kind)
        if not _non_empty(clause.get("text")):
            errors.append(f"{prefix}.text must be a non-empty string")
        source_ids = clause.get("source_ids")
        if (
            not isinstance(source_ids, list)
            or not source_ids
            or any(not _non_empty(item) for item in source_ids)
        ):
            errors.append(f"{prefix}.source_ids must be a non-empty source ID array")
    for required_kind in ("principle", "prohibition"):
        if clauses and required_kind not in clause_kinds:
            errors.append(f"constitution.clauses must include a {required_kind}")

    state_report = validate_plural_value_state(value_state)
    errors.extend(f"value_state: {error}" for error in state_report["errors"])
    if value_state.get("constitution_id") != constitution_id:
        errors.append("value_state.constitution_id must match constitution.constitution_id")
    if value_state.get("constitution_version") != version:
        errors.append("value_state.constitution_version must match constitution.version")
    if value_state.get("decision_rule") != "plural_deliberation":
        errors.append("value_state.decision_rule must be plural_deliberation")

    return {
        "valid": not errors,
        "errors": errors,
        "constitution_id": constitution_id,
        "constitution_version": version,
        "clause_kinds": sorted(clause_kinds),
    }

def validate_request_need_hypotheses(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Keep a stated request as evidence while separating it from the desired change."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["request interpretation must be an object"]}
    for field in ("request_id", "stated_request", "proposed_solution", "desired_condition"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    status = payload.get("requested_solution_status")
    if status not in REQUEST_SOLUTION_STATUSES:
        errors.append(
            "requested_solution_status must be one of "
            f"{sorted(REQUEST_SOLUTION_STATUSES)}"
        )
    if not _non_empty(payload.get("status_rationale")):
        errors.append("status_rationale must be a non-empty string")
    source_ids = payload.get("source_ids")
    if (
        not isinstance(source_ids, list)
        or not source_ids
        or any(not _non_empty(item) for item in source_ids)
    ):
        errors.append("source_ids must be a non-empty source ID array")
    alternatives = payload.get("need_hypotheses")
    if not isinstance(alternatives, list) or len(alternatives) < 2:
        errors.append("need_hypotheses must contain at least two hypotheses")
        alternatives = []
    hypothesis_ids = set()
    for index, hypothesis in enumerate(alternatives):
        prefix = f"need_hypotheses[{index}]"
        if not isinstance(hypothesis, dict):
            errors.append(f"{prefix} must be an object")
            continue
        hypothesis_id = hypothesis.get("hypothesis_id")
        if not _non_empty(hypothesis_id):
            errors.append(f"{prefix}.hypothesis_id must be a non-empty string")
        elif hypothesis_id in hypothesis_ids:
            errors.append(f"{prefix}.hypothesis_id must be unique")
        else:
            hypothesis_ids.add(hypothesis_id)
        if not _non_empty(hypothesis.get("condition_change")):
            errors.append(f"{prefix}.condition_change must be a non-empty string")
        if not _non_empty(hypothesis.get("distinguishing_observation")):
            errors.append(
                f"{prefix}.distinguishing_observation must be a non-empty string"
            )
    if payload.get("request_is_need") is not False:
        errors.append("request_is_need must be false; a request is evidence, not the need itself")
    return {
        "valid": not errors,
        "errors": errors,
        "requested_solution_status": status,
        "hypothesis_count": len(alternatives),
    }

def validate_behavior_desire_evidence(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Treat behavior as evidence of willingness, not proof of authentic desire."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["behavior evidence must be an object"]}
    for field in ("observation_id", "group_id", "observed_behavior", "context"):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    source_ids = payload.get("source_ids")
    if (
        not isinstance(source_ids, list)
        or not source_ids
        or any(not _non_empty(item) for item in source_ids)
    ):
        errors.append("source_ids must be a non-empty source ID array")
    if payload.get("behavior_equals_authentic_desire") is not False:
        errors.append("behavior_equals_authentic_desire must be false")

    confounds = payload.get("confounds")
    if not isinstance(confounds, list) or not confounds:
        errors.append("confounds must be a non-empty array")
        confounds = []
    seen_kinds = set()
    for index, confound in enumerate(confounds):
        prefix = f"confounds[{index}]"
        if not isinstance(confound, dict):
            errors.append(f"{prefix} must be an object")
            continue
        kind = confound.get("kind")
        if kind not in BEHAVIOR_CONFOUND_KINDS:
            errors.append(f"{prefix}.kind must be one of {sorted(BEHAVIOR_CONFOUND_KINDS)}")
        elif kind in seen_kinds:
            errors.append(f"{prefix}.kind must be unique")
        else:
            seen_kinds.add(kind)
        if not _non_empty(confound.get("possibility")):
            errors.append(f"{prefix}.possibility must be a non-empty string")
        if not _non_empty(confound.get("check")):
            errors.append(f"{prefix}.check must be a non-empty string")
    if not {"constraint", "missing_alternative"} <= seen_kinds:
        errors.append("confounds must examine constraint and missing_alternative")
    if not _non_empty(payload.get("counterfactual_observation")):
        errors.append("counterfactual_observation must be a non-empty string")
    return {
        "valid": not errors,
        "errors": errors,
        "confound_kinds": sorted(seen_kinds),
    }

