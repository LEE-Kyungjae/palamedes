#!/usr/bin/env python3
"""Multi-perspective product opportunity scouting before planning."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Dict, List

from palamedes_observe import utc_now


OPPORTUNITY_VERSION = "palamedes-opportunity-scout/2"
PERSPECTIVES = (
    "user_desire",
    "repeat_behavior",
    "monetization",
    "content_economy",
    "social_dynamics",
    "live_operations",
    "distribution",
    "platform_expansion",
    "user_and_business_risk",
)
OPPORTUNITY_TYPES = {
    "established_pattern",
    "product_specific_adaptation",
    "structural_invention",
}
SENIOR_LENSES = (
    "architecture_invariants_and_coupling",
    "failure_precedent_and_near_miss",
    "second_order_and_feedback_effects",
    "operations_and_total_cost",
    "migration_reversibility_and_option_value",
    "authority_incentives_and_externalities",
    "changed_constraints_and_timing",
    "negative_space_and_underused_capability",
)
FAILURE_BASIS_TYPES = {
    "direct_experience",
    "bounded_analogy",
    "inference_only",
}
PROBE_KINDS = {
    "behavioral_exposure",
    "shadow_operation",
    "prototype_test",
    "data_query",
}
PROBE_TERMINAL_OUTPUT_KINDS = {
    "observed_actor_response",
    "observed_system_behavior",
    "measured_state_change",
}
STRUCTURE_FIELDS = (
    "observed_facts",
    "inferences",
    "unknowns",
    "users",
    "core_actions",
    "repeat_loops",
    "progression",
    "content_supply",
    "social_surfaces",
    "value_capture",
    "operational_cadence",
    "distribution_loops",
    "constraints",
    "underused_capabilities",
)
OBSERVATION_ORIGIN = "model_extraction_unverified"


def fingerprint(value: Any) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _object(value: Any, field: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string")
    return value.strip()


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    return value.strip()


def _strings(value: Any, field: str, minimum: int = 0) -> List[str]:
    if not isinstance(value, list) or len(value) < minimum or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ValueError(f"{field} requires at least {minimum} non-empty strings")
    return [item.strip() for item in value]


def _optional_strings(value: Any, field: str) -> List[str]:
    return _strings([] if value is None else value, field)


def _retain_fields(value: Dict[str, Any], fields: tuple[str, ...]) -> None:
    for key in tuple(value):
        if key not in fields:
            del value[key]


def _ask(
    ask: Callable[[str, str], Dict[str, Any]],
    role: str,
    prompt: str,
    required: tuple[str, ...],
    arrays: tuple[str, ...] = (),
) -> Dict[str, Any]:
    last_error = ""
    for attempt in range(2):
        repair = "" if attempt == 0 else f"""

The previous response violated the contract: {last_error}. Return one corrected JSON
object. Required fields: {json.dumps(required)}. Array fields: {json.dumps(arrays)}.
"""
        row = _object(ask(role, prompt + repair), role)
        missing = [field for field in required if field not in row]
        wrong_arrays = [
            field for field in arrays if field in row and not isinstance(row[field], list)
        ]
        if not missing and not wrong_arrays:
            return row
        last_error = "; ".join(
            filter(None, (
                f"missing {', '.join(missing)}" if missing else "",
                f"non-array {', '.join(wrong_arrays)}" if wrong_arrays else "",
            ))
        )
    raise ValueError(f"{role} failed JSON contract after repair: {last_error}")


def _opportunity(
    value: Any,
    index: int,
    *,
    finding_lenses: Dict[str, str],
    reframe_lenses: Dict[str, str],
    available_experience_ids: set[str],
    direct_failure_experience_ids: set[str],
) -> Dict[str, Any]:
    row = _object(value, f"opportunities[{index}]")
    opportunity_id = _text(row.get("opportunity_id"), "opportunity_id")
    row["opportunity_id"] = opportunity_id
    for field in (
        "title", "observation", "latent_need", "current_gap", "mechanism",
        "behavior_change", "business_effect", "product_fit", "fastest_test",
        "failure_condition",
    ):
        row[field] = _text(row.get(field), f"{opportunity_id}.{field}")
    perspectives = _strings(
        row.get("perspectives"), f"{opportunity_id}.perspectives", minimum=2
    )
    unknown = sorted(set(perspectives) - set(PERSPECTIVES))
    if unknown:
        raise ValueError(
            f"{opportunity_id} has unknown perspectives: {', '.join(unknown)}"
        )
    if len(perspectives) != len(set(perspectives)):
        raise ValueError(f"{opportunity_id}.perspectives must be unique")
    opportunity_type = str(row.get("opportunity_type", "")).strip()
    if opportunity_type not in OPPORTUNITY_TYPES:
        raise ValueError(f"{opportunity_id}.opportunity_type is invalid")
    row["opportunity_type"] = opportunity_type
    row["perspectives"] = perspectives
    source_finding_ids = _strings(
        row.get("source_finding_ids"),
        f"{opportunity_id}.source_finding_ids",
        minimum=2,
    )
    if len(source_finding_ids) != len(set(source_finding_ids)):
        raise ValueError(f"{opportunity_id}.source_finding_ids must be unique")
    unknown_finding_ids = sorted(set(source_finding_ids) - set(finding_lenses))
    if unknown_finding_ids:
        raise ValueError(
            f"{opportunity_id} cites unavailable perspective findings: "
            + ", ".join(unknown_finding_ids)
        )
    if set(perspectives) != {finding_lenses[item] for item in source_finding_ids}:
        raise ValueError(
            f"{opportunity_id}.perspectives must match source_finding_ids"
        )
    row["source_finding_ids"] = source_finding_ids
    row["evidence_needed"] = _optional_strings(
        row.get("evidence_needed"), f"{opportunity_id}.evidence_needed"
    )
    senior_lenses = _strings(
        row.get("senior_lenses"), f"{opportunity_id}.senior_lenses", minimum=2
    )
    unknown_lenses = sorted(set(senior_lenses) - set(SENIOR_LENSES))
    if unknown_lenses:
        raise ValueError(
            f"{opportunity_id} has unknown senior lenses: {', '.join(unknown_lenses)}"
        )
    if len(senior_lenses) != len(set(senior_lenses)):
        raise ValueError(f"{opportunity_id}.senior_lenses must be unique")
    row["senior_lenses"] = senior_lenses
    lineage = row.get("reframe_lineage")
    if not isinstance(lineage, list) or len(lineage) < 2:
        raise ValueError(f"{opportunity_id}.reframe_lineage needs at least two entries")
    normalized_lineage = []
    reframe_ids = []
    for lineage_index, lineage_value in enumerate(lineage):
        item = _object(
            lineage_value,
            f"{opportunity_id}.reframe_lineage[{lineage_index}]",
        )
        reframe_id = _text(
            item.get("reframe_id"),
            f"{opportunity_id}.reframe_lineage[{lineage_index}].reframe_id",
        )
        if reframe_id not in reframe_lenses:
            raise ValueError(
                f"{opportunity_id} cites unavailable senior reframe: {reframe_id}"
            )
        item["reframe_id"] = reframe_id
        for field in ("changed_conclusion", "counterfactual_without_reframe"):
            item[field] = _text(
                item.get(field),
                f"{opportunity_id}.reframe_lineage[{lineage_index}].{field}",
            )
        normalized_lineage.append(item)
        reframe_ids.append(reframe_id)
    if len(reframe_ids) != len(set(reframe_ids)):
        raise ValueError(f"{opportunity_id}.reframe_lineage must cite unique reframes")
    if set(senior_lenses) != {reframe_lenses[item] for item in reframe_ids}:
        raise ValueError(
            f"{opportunity_id}.senior_lenses must match reframe_lineage"
        )
    row["reframe_lineage"] = normalized_lineage

    insight = _object(row.get("insight_chain"), f"{opportunity_id}.insight_chain")
    for field in (
        "hidden_assumption",
        "reframe",
        "first_order_effect",
        "second_order_effect",
        "feedback_or_externality",
        "local_optimum_trap",
        "design_invariant",
        "why_now",
    ):
        insight[field] = _text(
            insight.get(field), f"{opportunity_id}.insight_chain.{field}"
        )

    reality = _object(
        row.get("delivery_reality"), f"{opportunity_id}.delivery_reality"
    )
    for field in (
        "migration_path",
        "rollback_boundary",
        "ongoing_operating_burden",
        "ownership_and_authority",
    ):
        reality[field] = _text(
            reality.get(field), f"{opportunity_id}.delivery_reality.{field}"
        )

    failure = _object(row.get("failure_basis"), f"{opportunity_id}.failure_basis")
    basis_type = _text(
        failure.get("basis_type"), f"{opportunity_id}.failure_basis.basis_type"
    )
    if basis_type not in FAILURE_BASIS_TYPES:
        raise ValueError(f"{opportunity_id}.failure_basis.basis_type is invalid")
    failure["basis_type"] = basis_type
    source_ids = _optional_strings(
        failure.get("source_experience_ids"),
        f"{opportunity_id}.failure_basis.source_experience_ids",
    )
    if basis_type == "direct_experience" and not source_ids:
        raise ValueError(
            f"{opportunity_id} direct experience requires source_experience_ids"
        )
    if basis_type != "direct_experience" and source_ids:
        raise ValueError(
            f"{opportunity_id} may cite experience IDs only for direct experience"
        )
    failure["source_experience_ids"] = source_ids
    for field in (
        "lesson",
        "missing_viability_condition",
        "guardrail",
        "transfer_limit",
    ):
        failure[field] = _text(
            failure.get(field), f"{opportunity_id}.failure_basis.{field}"
        )
    unavailable_source_ids = sorted(set(source_ids) - available_experience_ids)
    if unavailable_source_ids:
        raise ValueError(
            f"{opportunity_id} cites unavailable experience IDs: "
            + ", ".join(unavailable_source_ids)
        )
    row["insight_chain"] = insight
    row["delivery_reality"] = reality
    row["failure_basis"] = failure
    if basis_type == "direct_experience":
        ineligible_failure_sources = sorted(
            set(source_ids) - direct_failure_experience_ids
        )
        if ineligible_failure_sources:
            raise ValueError(
                f"{opportunity_id} direct failure basis requires an adverse, mixed, "
                "blocked, or failed observed outcome: "
                + ", ".join(ineligible_failure_sources)
            )

    graph = _object(
        row.get("consequence_graph"), f"{opportunity_id}.consequence_graph"
    )
    raw_effects = graph.get("effects")
    if not isinstance(raw_effects, list) or len(raw_effects) < 2:
        raise ValueError(f"{opportunity_id}.consequence_graph needs at least two effects")
    effects = []
    for effect_index, effect_value in enumerate(raw_effects):
        effect = _object(
            effect_value,
            f"{opportunity_id}.consequence_graph.effects[{effect_index}]",
        )
        for field in (
            "effect_id",
            "caused_by",
            "stakeholder",
            "horizon",
            "effect",
            "early_signal",
        ):
            effect[field] = _text(
                effect.get(field),
                f"{opportunity_id}.consequence_graph.effects[{effect_index}].{field}",
            )
        if effect.get("valence") not in {"benefit", "risk", "mixed"}:
            raise ValueError(
                f"{opportunity_id}.consequence_graph.effects[{effect_index}].valence "
                "is invalid"
            )
        effects.append(effect)
    effect_ids = [effect["effect_id"] for effect in effects]
    if len(effect_ids) != len(set(effect_ids)):
        raise ValueError(f"{opportunity_id}.consequence_graph effect IDs must be unique")
    effect_by_id = {effect["effect_id"]: effect for effect in effects}

    def effect_depth(effect_id: str, visiting: set[str] | None = None) -> int:
        visiting = set(visiting or ())
        if effect_id in visiting:
            raise ValueError(f"{opportunity_id}.consequence_graph contains a cycle")
        visiting.add(effect_id)
        cause = effect_by_id[effect_id]["caused_by"]
        if cause == "mechanism":
            return 1
        if cause not in effect_by_id:
            raise ValueError(
                f"{opportunity_id}.consequence_graph cites unknown cause {cause}"
            )
        return 1 + effect_depth(cause, visiting)

    depths = {effect_id: effect_depth(effect_id) for effect_id in effect_ids}
    second_order_ids = {effect_id for effect_id, depth in depths.items() if depth >= 2}
    if not second_order_ids:
        raise ValueError(
            f"{opportunity_id}.consequence_graph requires a computed second-order path"
        )
    raw_responses = graph.get("design_responses")
    if not isinstance(raw_responses, list) or not raw_responses:
        raise ValueError(
            f"{opportunity_id}.consequence_graph requires design_responses"
        )
    responses = []
    for response_index, response_value in enumerate(raw_responses):
        response = _object(
            response_value,
            f"{opportunity_id}.consequence_graph.design_responses[{response_index}]",
        )
        for field in ("effect_id", "invariant", "mitigation", "stop_condition"):
            response[field] = _text(
                response.get(field),
                f"{opportunity_id}.consequence_graph.design_responses"
                f"[{response_index}].{field}",
            )
        if response["effect_id"] not in effect_by_id:
            raise ValueError(
                f"{opportunity_id}.consequence_graph design response cites unknown effect"
            )
        responses.append(response)
    if not any(response["effect_id"] in second_order_ids for response in responses):
        raise ValueError(
            f"{opportunity_id} requires a design response to a second-order effect"
        )
    graph["effects"] = effects
    graph["design_responses"] = responses
    graph["computed_max_depth"] = max(depths.values())
    row["consequence_graph"] = graph

    probe = _object(row.get("validation_probe"), f"{opportunity_id}.validation_probe")
    kind = _text(probe.get("kind"), f"{opportunity_id}.validation_probe.kind")
    if kind not in PROBE_KINDS:
        raise ValueError(f"{opportunity_id}.validation_probe.kind is not an action probe")
    probe["kind"] = kind
    if probe.get("reaches_observable_response") is not True:
        raise ValueError(
            f"{opportunity_id}.validation_probe must reach an observable response"
        )
    if probe.get("preparation_only") is not False:
        raise ValueError(f"{opportunity_id}.validation_probe cannot be preparation-only")
    if not isinstance(probe.get("reversible"), bool) or not probe["reversible"]:
        raise ValueError(f"{opportunity_id}.validation_probe must be reversible")
    terminal_output_kind = _text(
        probe.get("terminal_output_kind"),
        f"{opportunity_id}.validation_probe.terminal_output_kind",
    )
    if terminal_output_kind not in PROBE_TERMINAL_OUTPUT_KINDS:
        raise ValueError(
            f"{opportunity_id}.validation_probe must end in observed or measured reality"
        )
    probe["terminal_output_kind"] = terminal_output_kind
    for field in (
        "intervention",
        "target_actor",
        "observation_window",
        "metric",
        "observable_response",
        "baseline_or_counterfactual",
        "falsifier",
        "rollback",
        "stop_condition",
    ):
        probe[field] = _text(probe.get(field), f"{opportunity_id}.validation_probe.{field}")
    probe["authority_preconditions"] = _optional_strings(
        probe.get("authority_preconditions"),
        f"{opportunity_id}.validation_probe.authority_preconditions",
    )
    branches = _object(
        probe.get("branches"), f"{opportunity_id}.validation_probe.branches"
    )
    for field in ("if_supported", "if_refuted", "if_inconclusive"):
        branches[field] = _text(
            branches.get(field), f"{opportunity_id}.validation_probe.branches.{field}"
        )
    probe["branches"] = branches
    row["validation_probe"] = probe
    for item in normalized_lineage:
        _retain_fields(
            item,
            ("reframe_id", "changed_conclusion", "counterfactual_without_reframe"),
        )
    _retain_fields(
        insight,
        (
            "hidden_assumption",
            "reframe",
            "first_order_effect",
            "second_order_effect",
            "feedback_or_externality",
            "local_optimum_trap",
            "design_invariant",
            "why_now",
        ),
    )
    _retain_fields(
        reality,
        (
            "migration_path",
            "rollback_boundary",
            "ongoing_operating_burden",
            "ownership_and_authority",
        ),
    )
    _retain_fields(
        failure,
        (
            "basis_type",
            "source_experience_ids",
            "lesson",
            "missing_viability_condition",
            "guardrail",
            "transfer_limit",
        ),
    )
    for effect in effects:
        _retain_fields(
            effect,
            (
                "effect_id",
                "caused_by",
                "stakeholder",
                "horizon",
                "valence",
                "effect",
                "early_signal",
            ),
        )
    for response in responses:
        _retain_fields(
            response,
            ("effect_id", "invariant", "mitigation", "stop_condition"),
        )
    _retain_fields(graph, ("effects", "design_responses", "computed_max_depth"))
    _retain_fields(branches, ("if_supported", "if_refuted", "if_inconclusive"))
    _retain_fields(
        probe,
        (
            "kind",
            "reaches_observable_response",
            "preparation_only",
            "reversible",
            "terminal_output_kind",
            "intervention",
            "target_actor",
            "observation_window",
            "metric",
            "observable_response",
            "baseline_or_counterfactual",
            "falsifier",
            "rollback",
            "stop_condition",
            "authority_preconditions",
            "branches",
        ),
    )
    _retain_fields(
        row,
        (
            "opportunity_id",
            "title",
            "opportunity_type",
            "perspectives",
            "source_finding_ids",
            "senior_lenses",
            "reframe_lineage",
            "observation",
            "latent_need",
            "current_gap",
            "mechanism",
            "behavior_change",
            "business_effect",
            "product_fit",
            "evidence_needed",
            "fastest_test",
            "failure_condition",
            "insight_chain",
            "delivery_reality",
            "failure_basis",
            "consequence_graph",
            "validation_probe",
        ),
    )
    return row


def _deep_reframe(
    value: Any, index: int, available_experience_ids: set[str]
) -> Dict[str, Any]:
    row = _object(value, f"deep_reframes[{index}]")
    lens = _text(row.get("lens"), f"deep_reframes[{index}].lens")
    if lens not in SENIOR_LENSES:
        raise ValueError(f"deep_reframes[{index}].lens is invalid")
    row["lens"] = lens
    applicability = _text(
        row.get("applicability"), f"deep_reframes[{index}].applicability"
    )
    if applicability not in {"supported", "plausible", "no_signal"}:
        raise ValueError(f"deep_reframes[{index}].applicability is invalid")
    row["applicability"] = applicability
    evidence_status = _text(
        row.get("evidence_status"), f"deep_reframes[{index}].evidence_status"
    )
    expected_evidence_status = {
        "supported": "observed",
        "plausible": "inferred",
        "no_signal": "unsupported",
    }[applicability]
    if evidence_status != expected_evidence_status:
        raise ValueError(
            f"deep_reframes[{index}] {applicability} requires "
            f"evidence_status={expected_evidence_status}"
        )
    row["evidence_status"] = evidence_status
    substantive_fields = (
        "observed_signal",
        "hidden_assumption",
        "reframe",
        "implication",
        "second_order_effect",
        "design_invariant",
        "disconfirming_observation",
    )
    if applicability == "no_signal":
        for field in substantive_fields:
            row[field] = _string(row.get(field, ""), f"deep_reframes[{index}].{field}")
            if row[field]:
                raise ValueError(
                    f"deep_reframes[{index}] no_signal cannot manufacture {field}"
                )
        row["why_no_signal"] = _text(
            row.get("why_no_signal"), f"deep_reframes[{index}].why_no_signal"
        )
        row["evidence_needed"] = _text(
            row.get("evidence_needed"), f"deep_reframes[{index}].evidence_needed"
        )
    else:
        for field in substantive_fields:
            row[field] = _text(row.get(field), f"deep_reframes[{index}].{field}")
        row["why_no_signal"] = _string(
            row.get("why_no_signal", ""), f"deep_reframes[{index}].why_no_signal"
        )
        if row["why_no_signal"]:
            raise ValueError(
                f"deep_reframes[{index}] applicable reframe cannot claim no signal"
            )
        row["evidence_needed"] = _string(
            row.get("evidence_needed", ""), f"deep_reframes[{index}].evidence_needed"
        )
    source_ids = _optional_strings(
        row.get("source_experience_ids"),
        f"deep_reframes[{index}].source_experience_ids",
    )
    unavailable = sorted(set(source_ids) - available_experience_ids)
    if unavailable:
        raise ValueError(
            "deep reframe cites unavailable experience IDs: " + ", ".join(unavailable)
        )
    if applicability == "supported" and not source_ids:
        raise ValueError("supported deep reframe requires source experience evidence")
    if applicability != "supported" and source_ids:
        raise ValueError(
            "only a supported deep reframe may cite source experience IDs"
        )
    row["source_experience_ids"] = source_ids
    row["reframe_id"] = f"reframe-{lens}"
    _retain_fields(
        row,
        (
            "lens",
            "applicability",
            "observed_signal",
            "hidden_assumption",
            "reframe",
            "implication",
            "second_order_effect",
            "design_invariant",
            "disconfirming_observation",
            "evidence_status",
            "source_experience_ids",
            "why_no_signal",
            "evidence_needed",
            "reframe_id",
        ),
    )
    return row


def _critique(value: Any, ids: set[str], index: int) -> Dict[str, Any]:
    row = _object(value, f"assessments[{index}]")
    opportunity_id = _text(
        row.get("opportunity_id"), f"assessments[{index}].opportunity_id"
    )
    if opportunity_id not in ids:
        raise ValueError("assessment references an unknown opportunity")
    disposition = _text(row.get("disposition"), f"{opportunity_id}.disposition")
    if disposition not in {"surface_now", "validate", "defer", "reject"}:
        raise ValueError(f"{opportunity_id}.disposition is invalid")
    row["opportunity_id"] = opportunity_id
    row["disposition"] = disposition
    for field in ("strongest_reason", "strongest_risk", "decision_rationale"):
        row[field] = _text(row.get(field), f"{opportunity_id}.{field}")
    for field in (
        "insight_survives_name_removal",
        "second_order_accounted",
        "failure_basis_honest",
        "operational_burden_accounted",
    ):
        if not isinstance(row.get(field), bool):
            raise ValueError(f"{opportunity_id}.{field} must be boolean")
    row["senior_judgment_gap"] = _text(
        row.get("senior_judgment_gap"), f"{opportunity_id}.senior_judgment_gap"
    )
    required_truths = (
        row["insight_survives_name_removal"],
        row["second_order_accounted"],
        row["failure_basis_honest"],
        row["operational_burden_accounted"],
    )
    if disposition in {"surface_now", "validate"} and not all(required_truths):
        raise ValueError(
            f"{opportunity_id} cannot be eligible with a failed senior judgment check"
        )
    _retain_fields(
        row,
        (
            "opportunity_id",
            "disposition",
            "strongest_reason",
            "strongest_risk",
            "decision_rationale",
            "senior_judgment_gap",
            "insight_survives_name_removal",
            "second_order_accounted",
            "failure_basis_honest",
            "operational_burden_accounted",
        ),
    )
    return row


def _validate_reframing(
    value: Dict[str, Any], available_experience_ids: set[str]
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    findings = value.get("perspective_findings")
    if not isinstance(findings, list):
        raise ValueError("perspective_findings must be an array")
    covered = []
    for index, row in enumerate(findings):
        item = _object(row, f"perspective_findings[{index}]")
        perspective = _text(
            item.get("perspective"), f"perspective_findings[{index}].perspective"
        )
        if perspective not in PERSPECTIVES:
            raise ValueError(f"perspective_findings[{index}].perspective is invalid")
        item["perspective"] = perspective
        applicability = _text(
            item.get("applicability"),
            f"perspective_findings[{index}].applicability",
        )
        if applicability not in {"supported", "plausible", "no_signal"}:
            raise ValueError(
                f"perspective_findings[{index}].applicability is invalid"
            )
        item["applicability"] = applicability
        item["question_owner_did_not_ask"] = _text(
            item.get("question_owner_did_not_ask"),
            f"perspective_findings[{index}].question_owner_did_not_ask",
        )
        if applicability == "no_signal":
            for field in ("finding", "blind_spot"):
                item[field] = _string(
                    item.get(field, ""), f"perspective_findings[{index}].{field}"
                )
                if item[field]:
                    raise ValueError(
                        f"perspective_findings[{index}] no_signal cannot manufacture "
                        f"{field}"
                    )
            item["why_no_signal"] = _text(
                item.get("why_no_signal"),
                f"perspective_findings[{index}].why_no_signal",
            )
        else:
            for field in ("finding", "blind_spot"):
                item[field] = _text(
                    item.get(field), f"perspective_findings[{index}].{field}"
                )
            item["why_no_signal"] = _string(
                item.get("why_no_signal", ""),
                f"perspective_findings[{index}].why_no_signal",
            )
            if item["why_no_signal"]:
                raise ValueError(
                    f"perspective_findings[{index}] applicable finding cannot claim "
                    "no signal"
                )
        item["finding_id"] = f"finding-{perspective}"
        _retain_fields(
            item,
            (
                "perspective",
                "applicability",
                "finding",
                "blind_spot",
                "question_owner_did_not_ask",
                "why_no_signal",
                "finding_id",
            ),
        )
        covered.append(perspective)
    if set(covered) != set(PERSPECTIVES) or len(covered) != len(PERSPECTIVES):
        raise ValueError("perspective_findings must cover every perspective exactly")

    raw_reframes = value.get("deep_reframes")
    if not isinstance(raw_reframes, list):
        raise ValueError("deep_reframes must be an array")
    reframes = [
        _deep_reframe(row, index, available_experience_ids)
        for index, row in enumerate(raw_reframes)
    ]
    covered_lenses = [row["lens"] for row in reframes]
    if (
        set(covered_lenses) != set(SENIOR_LENSES)
        or len(covered_lenses) != len(SENIOR_LENSES)
    ):
        raise ValueError("deep_reframes must cover every senior lens exactly")
    return findings, reframes


def _validate_opportunities(
    value: Dict[str, Any],
    *,
    findings: List[Dict[str, Any]],
    reframes: List[Dict[str, Any]],
    available_experience_ids: set[str],
    direct_failure_experience_ids: set[str],
) -> List[Dict[str, Any]]:
    raw = value.get("opportunities")
    if not isinstance(raw, list):
        raise ValueError("opportunities must be an array")
    if len(raw) > 5:
        raise ValueError("opportunities must contain at most 5 entries")
    finding_lenses = {
        row["finding_id"]: row["perspective"]
        for row in findings
        if row.get("applicability") != "no_signal"
    }
    reframe_lenses = {
        row["reframe_id"]: row["lens"]
        for row in reframes
        if row.get("applicability") != "no_signal"
    }
    opportunities = [
        _opportunity(
            row,
            index,
            finding_lenses=finding_lenses,
            reframe_lenses=reframe_lenses,
            available_experience_ids=available_experience_ids,
            direct_failure_experience_ids=direct_failure_experience_ids,
        )
        for index, row in enumerate(raw)
    ]
    ids = [row["opportunity_id"] for row in opportunities]
    if len(ids) != len(set(ids)):
        raise ValueError("opportunity IDs must be unique")
    if not opportunities:
        _text(value.get("no_opportunity_reason"), "no_opportunity_reason")
    return opportunities


def _validate_challenge(
    value: Dict[str, Any], opportunity_ids: set[str]
) -> tuple[List[Dict[str, Any]], List[str]]:
    raw = value.get("assessments")
    if not isinstance(raw, list):
        raise ValueError("assessments must be an array")
    assessments = [
        _critique(row, opportunity_ids, index) for index, row in enumerate(raw)
    ]
    if (
        len(assessments) != len(opportunity_ids)
        or {row["opportunity_id"] for row in assessments} != opportunity_ids
    ):
        raise ValueError("critic must assess every opportunity exactly once")
    eligible = {
        row["opportunity_id"]
        for row in assessments
        if row["disposition"] in {"surface_now", "validate"}
    }
    top_ids = _strings(value.get("top_opportunity_ids"), "top_opportunity_ids")
    if len(top_ids) != len(set(top_ids)) or not set(top_ids).issubset(eligible):
        raise ValueError("top_opportunity_ids must be unique eligible opportunities")
    _text(value.get("portfolio_summary"), "portfolio_summary")
    return assessments, top_ids


class OpportunityStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.records = root / "records"

    def save(self, record: Dict[str, Any]) -> Path:
        self.records.mkdir(parents=True, exist_ok=True)
        path = self.records / f"{record['opportunity_scout_id']}.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return path

    def records_by_recency(self) -> List[Dict[str, Any]]:
        if not self.records.is_dir():
            return []
        records = []
        for path in self.records.glob("opportunity-*.json"):
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(value, dict):
                records.append(value)
        records.sort(
            key=lambda row: (
                str(row.get("created_at", "")),
                str(row.get("opportunity_scout_id", "")),
            ),
            reverse=True,
        )
        return records

    def latest(self) -> Dict[str, Any] | None:
        records = self.records_by_recency()
        return records[0] if records else None


def run_opportunity_scout(
    *,
    ask: Callable[[str, str], Dict[str, Any]],
    store: OpportunityStore,
    context: str,
    experiences: List[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Find useful product opportunities with failure-aware senior judgment."""
    experience_archive = [
        row for row in (experiences or []) if isinstance(row, dict)
    ]
    archive_truncated = len(experience_archive) > 12
    experiences = experience_archive[-12:]
    experience_ids = {
        str(row.get("experience_id", "")).strip()
        for row in experiences
        if str(row.get("experience_id", "")).strip()
    }
    direct_failure_experience_ids = set()
    for experience in experiences:
        experience_id = str(experience.get("experience_id", "")).strip()
        observed = experience.get("observed", experience)
        if not experience_id or not isinstance(observed, dict):
            continue
        outcome_status = str(
            observed.get("reported_outcome_status")
            or observed.get("status")
            or ""
        ).strip()
        execution_status = str(observed.get("execution_status", "")).strip()
        outcome_type = str(observed.get("outcome_type", "")).strip()
        if (
            outcome_status in {"failure", "mixed"}
            or execution_status in {"failed", "blocked"}
            or (
                outcome_status != "success"
                and outcome_type
                in {
                    "adverse_result",
                    "null_finding",
                    "insufficient_evidence",
                    "blocked_by_environment",
                    "misaligned_mission",
                }
            )
        ):
            direct_failure_experience_ids.add(experience_id)

    structure = _ask(ask, "opportunity_structure_observer", f"""
Map the product as it currently exists. Separate observed facts from inferences and
unknowns. Identify users, core actions, repeat loops, progression, content supply,
social surfaces, current value capture, operational cadence, distribution loops,
constraints, and underused capabilities. Absence of a mechanism is a hypothesis unless
the context proves it. Return only concise string arrays for these exact fields:
{json.dumps(STRUCTURE_FIELDS)}.

CONTEXT:\n{context}
""", required=STRUCTURE_FIELDS, arrays=STRUCTURE_FIELDS)
    try:
        for field in STRUCTURE_FIELDS:
            structure[field] = _strings(structure.get(field), f"structure.{field}")
    except ValueError as exc:
        structure = _ask(ask, "opportunity_structure_observer", f"""
Repair the product-structure object without changing its meaning. The nested contract
error was: {exc}. Every entry must be a concise JSON string, never an object, number,
boolean, or nested array. Return the complete object with exactly these fields:
{json.dumps(STRUCTURE_FIELDS)}.

PREVIOUS OBJECT:\n{json.dumps(structure, ensure_ascii=False)}
""", required=STRUCTURE_FIELDS, arrays=STRUCTURE_FIELDS)
        for field in STRUCTURE_FIELDS:
            structure[field] = _strings(structure.get(field), f"structure.{field}")
    _retain_fields(structure, STRUCTURE_FIELDS)

    reframing_prompt = f"""
Act like a senior product architect who has learned from incidents, migrations, operating
burden, incentive failures, and local optima. First rotate through every product/business
perspective exactly once: {json.dumps(PERSPECTIVES)}. For each return perspective,
applicability (supported|plausible|no_signal), finding, blind_spot,
question_owner_did_not_ask, and why_no_signal. A no_signal result must leave finding and
blind_spot as empty strings and explain the missing evidence; inspecting a perspective is
not permission to manufacture a conclusion.

Then inspect every senior lens exactly once: {json.dumps(SENIOR_LENSES)}. For each return
lens, applicability (supported|plausible|no_signal), observed_signal, hidden_assumption,
reframe, implication, second_order_effect, design_invariant, disconfirming_observation,
evidence_status (observed|inferred|unsupported), source_experience_ids, why_no_signal,
and evidence_needed.

Experience discipline is strict. supported requires evidence_status=observed and a
supplied experience that directly supports the reframe. plausible requires
evidence_status=inferred and no experience IDs. no_signal requires
evidence_status=unsupported, empty substantive reframe fields, an explanation in
why_no_signal, and the evidence needed. Never invent a predecessor, incident, user,
metric, or source. Look for what only becomes visible after maintenance, migration,
abuse, scaling, incentive gaming, rollback, or ownership handoff, but record no_signal
when the bounded context cannot support it. Ask: after the third incident, which stable
identity, invariant, authority boundary, operational capacity limit, recovery contract,
and preserved diagnostic evidence would an experienced owner wish had existed? Do not
turn this hardening question into a claim that an incident actually occurred.

Return perspective_findings and deep_reframes.

PRODUCT STRUCTURE:\n{json.dumps(structure, ensure_ascii=False)}
BOUNDED EXPERIENCE ARCHIVE:\n{json.dumps(experiences, ensure_ascii=False)}
"""
    reframing = _ask(
        ask,
        "senior_opportunity_reframer",
        reframing_prompt,
        required=("perspective_findings", "deep_reframes"),
        arrays=("perspective_findings", "deep_reframes"),
    )
    try:
        findings, deep_reframes = _validate_reframing(reframing, experience_ids)
    except ValueError as exc:
        reframing = _ask(
            ask,
            "senior_opportunity_reframer",
            f"""
Repair the complete reframing object without changing sound conclusions. Contract error:
{exc}. Cover every product perspective and every senior lens exactly once. Use only the
available experience IDs {json.dumps(sorted(experience_ids))}; inferred or unsupported
claims must cite none.

PERSPECTIVE CONTRACT: exact enums {json.dumps(PERSPECTIVES)}; every row requires
perspective, applicability (supported|plausible|no_signal), finding, blind_spot,
question_owner_did_not_ask, and why_no_signal.
SENIOR LENS CONTRACT: exact enums {json.dumps(SENIOR_LENSES)}; every row requires lens,
applicability, observed_signal, hidden_assumption, reframe, implication,
second_order_effect, design_invariant, disconfirming_observation, evidence_status,
source_experience_ids, why_no_signal, and evidence_needed. no_signal must use empty
substantive fields.

PRODUCT STRUCTURE:\n{json.dumps(structure, ensure_ascii=False)}
BOUNDED EXPERIENCE ARCHIVE:\n{json.dumps(experiences, ensure_ascii=False)}
PREVIOUS OBJECT:\n{json.dumps(reframing, ensure_ascii=False)}
""",
            required=("perspective_findings", "deep_reframes"),
            arrays=("perspective_findings", "deep_reframes"),
        )
        findings, deep_reframes = _validate_reframing(reframing, experience_ids)

    synthesis_prompt = f"""
Synthesize product opportunities from the product structure and senior reframes. Do not
brainstorm feature names. Each opportunity must replace a hidden assumption and connect
at least two exact product perspectives plus at least two exact senior lenses. Preserve a
known product archetype when its product-specific causal fit is strong; label it
established_pattern rather than rejecting it as unoriginal. Derive the archetype from the
bounded signals instead of selecting from a supplied catalog of feature names.

Every opportunity requires opportunity_id, title, opportunity_type (exactly one of
{json.dumps(sorted(OPPORTUNITY_TYPES))}), perspectives,
source_finding_ids, senior_lenses, reframe_lineage, observation, latent_need, current_gap,
mechanism, behavior_change, business_effect, product_fit, evidence_needed, fastest_test,
and failure_condition. Use only finding_id and reframe_id values present below, and never
cite a no_signal finding or reframe. Each reframe_lineage entry requires reframe_id,
changed_conclusion, and counterfactual_without_reframe; this must show how the reframe
actually altered the idea rather than decorating it with a lens name.
It also requires:

insight_chain: hidden_assumption, reframe, first_order_effect, second_order_effect,
feedback_or_externality, local_optimum_trap, design_invariant, why_now.

delivery_reality: migration_path, rollback_boundary, ongoing_operating_burden,
ownership_and_authority. The text must identify the stable identity or state boundary,
the single active authority during migration, the capacity that grows fastest, and the
recovery or operator escape path when those details are material; state the evidence gap
when they cannot yet be grounded.

failure_basis: basis_type (direct_experience|bounded_analogy|inference_only),
source_experience_ids, lesson, missing_viability_condition, guardrail, transfer_limit.
Use direct_experience only with IDs from DIRECT FAILURE/NEAR-MISS EXPERIENCE IDS below;
an available success-only experience cannot be a failure basis. The other basis types
must cite none. `inference_only` must say plainly that no local failure evidence exists.
Return 0-5 distinct opportunities and no_opportunity_reason. Do not grant planning or
delivery authority.

consequence_graph: effects and design_responses. Each effect requires effect_id,
caused_by (mechanism or another effect_id), stakeholder, horizon, valence
(benefit|risk|mixed), effect, and early_signal. Include a real two-hop causal path. Each
design response requires effect_id, invariant, mitigation, and stop_condition, and at
least one must address a computed second-order effect.

validation_probe: kind (behavioral_exposure|shadow_operation|prototype_test|data_query),
reaches_observable_response=true, preparation_only=false, reversible=true,
terminal_output_kind
(observed_actor_response|observed_system_behavior|measured_state_change), intervention,
target_actor, observation_window, metric, observable_response,
baseline_or_counterfactual, falsifier, rollback, stop_condition,
authority_preconditions, and branches with if_supported, if_refuted, and
if_inconclusive. A review, plan, readiness packet, or more brainstorming is not a
validation probe and cannot be relabeled as a data query.

PRODUCT STRUCTURE:\n{json.dumps(structure, ensure_ascii=False)}
PERSPECTIVE FINDINGS:\n{json.dumps(findings, ensure_ascii=False)}
DEEP REFRAMES:\n{json.dumps(deep_reframes, ensure_ascii=False)}
AVAILABLE EXPERIENCE IDS:\n{json.dumps(sorted(experience_ids))}
DIRECT FAILURE/NEAR-MISS EXPERIENCE IDS:\n{json.dumps(sorted(direct_failure_experience_ids))}
"""
    synthesis = _ask(
        ask,
        "multi_perspective_opportunity_synthesizer",
        synthesis_prompt,
        required=("opportunities", "no_opportunity_reason"),
        arrays=("opportunities",),
    )
    try:
        opportunities = _validate_opportunities(
            synthesis,
            findings=findings,
            reframes=deep_reframes,
            available_experience_ids=experience_ids,
            direct_failure_experience_ids=direct_failure_experience_ids,
        )
    except ValueError as exc:
        synthesis = _ask(
            ask,
            "multi_perspective_opportunity_synthesizer",
            synthesis_prompt
            + f"""

Repair the complete opportunity object without weakening sound insights. Contract error:
{exc}. Every text field must be a JSON string. Preserve the required insight_chain,
delivery_reality, failure_basis, consequence_graph, validation_probe, at least two
perspectives, and at least two senior lenses. Cite only these experience IDs:
{json.dumps(sorted(experience_ids))}. Use an exact opportunity_type from
{json.dumps(sorted(OPPORTUNITY_TYPES))}. Use exact IDs without changing underscores:
finding IDs {json.dumps([row['finding_id'] for row in findings if row.get('applicability') != 'no_signal'])};
reframe IDs {json.dumps([row['reframe_id'] for row in deep_reframes if row.get('applicability') != 'no_signal'])}.
The perspectives and senior_lenses arrays must exactly match the perspectives and lenses
represented by the cited IDs.
Only these IDs may support failure_basis.basis_type=direct_experience:
{json.dumps(sorted(direct_failure_experience_ids))}.
These fields must be JSON arrays even when empty: perspectives, source_finding_ids,
senior_lenses, reframe_lineage, evidence_needed, failure_basis.source_experience_ids,
consequence_graph.effects, consequence_graph.design_responses,
validation_probe.authority_preconditions. Never return null for an array.

PREVIOUS OBJECT:\n{json.dumps(synthesis, ensure_ascii=False)}
""",
            required=("opportunities", "no_opportunity_reason"),
            arrays=("opportunities",),
        )
        opportunities = _validate_opportunities(
            synthesis,
            findings=findings,
            reframes=deep_reframes,
            available_experience_ids=experience_ids,
            direct_failure_experience_ids=direct_failure_experience_ids,
        )

    ids = {row["opportunity_id"] for row in opportunities}
    if opportunities:
        challenge_prompt = f"""
Critique every opportunity for causal fit, evidence quality, user benefit, strategic or
revenue effect, architecture coupling, migration and rollback reality, ongoing operating
burden, incentive gaming, cannibalization, externalities, and dark-pattern risk. A
familiar pattern is not a reason to reject it. Verify that every cited finding and senior
reframe materially changes the conclusion, and that no direct-experience lesson claims
more than its bounded observation supports.

Return exactly one assessment per opportunity with opportunity_id, disposition
(surface_now|validate|defer|reject), strongest_reason, strongest_risk,
decision_rationale, senior_judgment_gap, and booleans for
insight_survives_name_removal, second_order_accounted, failure_basis_honest, and
operational_burden_accounted. Any false boolean makes the opportunity ineligible for
surface_now or validate. Also return portfolio_summary and top_opportunity_ids ordered by
expected value adjusted for evidence, reversibility, and total operating burden.

STRUCTURE:\n{json.dumps(structure, ensure_ascii=False)}
OPPORTUNITIES:\n{json.dumps(opportunities, ensure_ascii=False)}
PERSPECTIVE FINDINGS:\n{json.dumps(findings, ensure_ascii=False)}
DEEP REFRAMES:\n{json.dumps(deep_reframes, ensure_ascii=False)}
BOUNDED EXPERIENCE ARCHIVE:\n{json.dumps(experiences, ensure_ascii=False)}
"""
        challenge = _ask(
            ask,
            "opportunity_reality_critic",
            challenge_prompt,
            required=("assessments", "portfolio_summary", "top_opportunity_ids"),
            arrays=("assessments", "top_opportunity_ids"),
        )
        try:
            assessments, top_ids = _validate_challenge(challenge, ids)
        except ValueError as exc:
            challenge = _ask(
                ask,
                "opportunity_reality_critic",
                f"""
Repair the complete critic object without changing sound verdicts. Contract error: {exc}.
Assess every opportunity exactly once. An opportunity with any failed senior judgment
boolean must be defer or reject.
Each assessment requires opportunity_id, disposition
(surface_now|validate|defer|reject), strongest_reason, strongest_risk,
decision_rationale, senior_judgment_gap, insight_survives_name_removal,
second_order_accounted, failure_basis_honest, and operational_burden_accounted. Also
return portfolio_summary and top_opportunity_ids.

REQUIRED OPPORTUNITY IDS:\n{json.dumps(sorted(ids))}
STRUCTURE:\n{json.dumps(structure, ensure_ascii=False)}
OPPORTUNITIES:\n{json.dumps(opportunities, ensure_ascii=False)}
PERSPECTIVE FINDINGS:\n{json.dumps(findings, ensure_ascii=False)}
DEEP REFRAMES:\n{json.dumps(deep_reframes, ensure_ascii=False)}
BOUNDED EXPERIENCE ARCHIVE:\n{json.dumps(experiences, ensure_ascii=False)}
PREVIOUS OBJECT:\n{json.dumps(challenge, ensure_ascii=False)}
""",
                required=("assessments", "portfolio_summary", "top_opportunity_ids"),
                arrays=("assessments", "top_opportunity_ids"),
            )
            assessments, top_ids = _validate_challenge(challenge, ids)
    else:
        challenge = {
            "assessments": [],
            "portfolio_summary": _text(
                synthesis.get("no_opportunity_reason"), "no_opportunity_reason"
            ),
            "top_opportunity_ids": [],
        }
        assessments = []
        top_ids = []

    identity = {
        "context_fingerprint": fingerprint(context),
        "experience_archive_fingerprint": fingerprint(experiences),
        "structure": structure,
        "perspective_findings": findings,
        "deep_reframes": deep_reframes,
        "opportunities": opportunities,
        "assessments": assessments,
        "portfolio_summary": challenge.get("portfolio_summary", ""),
        "top_opportunity_ids": top_ids,
    }
    record = {
        "opportunity_scout_version": OPPORTUNITY_VERSION,
        "opportunity_scout_id": f"opportunity-{fingerprint(identity)[:12]}",
        "created_at": utc_now(),
        "context_fingerprint": fingerprint(context),
        "perspectives": list(PERSPECTIVES),
        "senior_lenses": list(SENIOR_LENSES),
        "experience_coverage": {
            "available_experience_ids": sorted(experience_ids),
            "direct_failure_experience_ids": sorted(
                direct_failure_experience_ids
            ),
            "experience_count": len(experiences),
            "archive_truncated": archive_truncated,
            "absence_is_not_evidence_of_no_failures": True,
        },
        "structure_evidence_boundary": {
            "observed_facts_origin": OBSERVATION_ORIGIN,
            "host_verified_claim_ledger_available": False,
            "decision_relevant_claims_require_human_or_host_verification": True,
        },
        "product_structure": structure,
        "perspective_findings": findings,
        "deep_reframes": deep_reframes,
        "opportunities": opportunities,
        "critic": {**challenge, "assessments": assessments, "top_opportunity_ids": top_ids},
        "status": "opportunities_found" if top_ids else "needs_evidence",
        "selected_opportunity_id": "",
        "planning_authority_granted": False,
        "delivery_authority_granted": False,
    }
    store.save(record)
    return record
