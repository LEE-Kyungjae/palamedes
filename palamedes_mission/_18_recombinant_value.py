"""Research-backed diagnostics for recombinant mission candidates.

This module does not select or authorize a mission.  It preserves the existing
consequence, causal, constitutional, and human-authority gates while making the
structure hidden by a scalar novelty score inspectable.
"""

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ._01_kinds_value import _non_empty


_NOVELTY_MEASURES = {
    "relation_rarity",
    "structural_delta",
    "baseline_non_reducibility",
    "semantic_distance",
    "human_judgment",
}

_UNCERTAINTY_TREATMENTS = {"normal_progression", "bounded_probe", "defer"}

RECOMBINANT_EVALUATION_GUIDELINE = {
    "version": "recombinant-evaluation-guideline/1",
    "non_authorizing": True,
    "calibration_status": "provisional_ordinal_anchors",
    "score_bands": {
        "zero": {"minimum": 0.0, "maximum": 0.24},
        "mid": {"minimum": 0.25, "maximum": 0.74},
        "one": {"minimum": 0.75, "maximum": 1.0},
    },
    "dimensions": {
        "conventional_core_strength": {
            "zero": "no demonstrated connection to a working causal or operational baseline",
            "mid": "some known components are present but the end-to-end baseline is only partly demonstrated",
            "one": "the causal and operational core is demonstrated in the dated comparison population",
            "required_evidence": "comparison-population evidence and at least one verified baseline record",
        },
        "atypical_tail_strength": {
            "zero": "renaming, parameter variation, or a conventional additive bundle",
            "mid": "an uncommon relation is present but its newly possible outcome is only partly evidenced",
            "one": "a rare relation creates an evidenced outcome unavailable from the components independently",
            "required_evidence": "relation rarity, structural delta, and baseline non-reducibility evidence",
        },
        "local_knowledge_score": {
            "zero": "no demonstrated host capability can explain or validate the candidate",
            "mid": "the host can absorb the candidate after bounded learning or external validation",
            "one": "current host capabilities can explain, test, and maintain the candidate",
            "required_evidence": "a dated host-capability snapshot",
        },
        "comprehension_cost": {
            "zero": "no material concepts or validation skills are missing",
            "mid": "bounded missing knowledge has an identified learning or validation path",
            "one": "critical concepts are missing and no bounded validation path exists",
            "required_evidence": "named missing concepts and an independent-validator availability record",
        },
        "knowledge_maturity": {
            "zero": "the knowledge has no observed reuse or validation history",
            "mid": "the knowledge has limited repeat validation and remains context-sensitive",
            "one": "the knowledge has repeated validation across relevant contexts and remains current",
            "required_evidence": "dated validation, adoption, and obsolescence records",
        },
        "integration_cost": {
            "zero": "all required complements are available, compatible, and owned",
            "mid": "bounded integration gaps have owners and discriminating tests",
            "one": "critical complements are unavailable or incompatibility cannot be isolated",
            "required_evidence": "per-complement availability, compatibility, ownership, and integration evidence",
        },
        "outcome_variance": {
            "zero": "success and failure ranges are narrow and directly observable",
            "mid": "material uncertainty remains but a reversible discriminating probe exists",
            "one": "outcomes are highly dispersed and no observation can currently distinguish them",
            "required_evidence": "separate success signal, failure signal, falsifier, and treatment rationale",
        },
    },
    "dispositions": {
        "reject": "a hard gate fails or the claimed grounding is fabricated or temporally invalid",
        "defer": "the candidate may be viable but the declared probe cannot run with available complements",
        "preserve": "the grounded candidate is not actionable now but is explicitly retained on the exploration frontier",
        "bounded_probe": "hard gates pass and a reversible discriminating probe can run with ready complements",
        "progress": "hard gates pass, grounding is verified, complements are ready, and normal evidence progression is declared",
    },
}


def recombinant_evaluation_guideline() -> Dict[str, Any]:
    """Return immutable-by-copy scoring anchors and disposition semantics."""
    return deepcopy(RECOMBINANT_EVALUATION_GUIDELINE)


def _utc_datetime(errors: List[str], value: Any, path: str) -> Optional[datetime]:
    if not _non_empty(value):
        errors.append(f"{path} must be a non-empty ISO-8601 timestamp")
        return None
    try:
        normalized = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        errors.append(f"{path} must be an ISO-8601 timestamp")
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        errors.append(f"{path} must include a timezone")
        return None
    return parsed.astimezone(timezone.utc)


def _score(errors: List[str], value: Any, path: str) -> float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not 0 <= value <= 1
    ):
        errors.append(f"{path} must be between zero and one")
        return 0.0
    return float(value)


def _score_anchor(score: float) -> str:
    if score <= 0.24:
        return "zero"
    if score <= 0.74:
        return "mid"
    return "one"


def _string_list(
    errors: List[str], value: Any, path: str, *, minimum: int = 0
) -> List[str]:
    if (
        not isinstance(value, list)
        or len(value) < minimum
        or not all(isinstance(item, str) and item.strip() for item in value)
    ):
        errors.append(
            f"{path} must be an array of non-empty strings"
            + (f" with at least {minimum} items" if minimum else "")
        )
        return []
    normalized = [item.strip() for item in value]
    if len(normalized) != len(set(normalized)):
        errors.append(f"{path} must not contain duplicates")
    return normalized


def validate_recombinant_value_profile(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Validate evidence for rareness without turning it into mission authority."""
    errors: List[str] = []
    if not isinstance(payload, dict):
        return {
            "valid": False,
            "errors": ["recombinant value profile must be an object"],
        }

    for field in (
        "evaluation_id",
        "candidate_id",
        "comparison_population_id",
        "comparison_as_of",
        "evaluation_as_of",
        "evaluation_rationale",
    ):
        if not _non_empty(payload.get(field)):
            errors.append(f"{field} must be a non-empty string")
    comparison_as_of = _utc_datetime(errors, payload.get("comparison_as_of"), "comparison_as_of")
    evaluation_as_of = _utc_datetime(errors, payload.get("evaluation_as_of"), "evaluation_as_of")
    if comparison_as_of and evaluation_as_of and comparison_as_of > evaluation_as_of:
        errors.append("comparison_as_of must not be later than evaluation_as_of")

    profile = payload.get("recombinant_profile")
    if not isinstance(profile, dict):
        errors.append("recombinant_profile must be an object")
        profile = {}
    components = _string_list(
        errors, profile.get("known_components"), "recombinant_profile.known_components", minimum=2
    )
    core_strength = _score(
        errors,
        profile.get("conventional_core_strength"),
        "recombinant_profile.conventional_core_strength",
    )
    _string_list(
        errors,
        profile.get("conventional_core_evidence_ids"),
        "recombinant_profile.conventional_core_evidence_ids",
        minimum=1,
    )
    tail_strength = _score(
        errors,
        profile.get("atypical_tail_strength"),
        "recombinant_profile.atypical_tail_strength",
    )
    relations = profile.get("atypical_relations")
    if not isinstance(relations, list) or not relations:
        errors.append("recombinant_profile.atypical_relations must contain at least one relation")
        relations = []
    component_set = set(components)
    relation_ids = set()
    for index, relation in enumerate(relations):
        prefix = f"recombinant_profile.atypical_relations[{index}]"
        if not isinstance(relation, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in (
            "relation_id",
            "left_component",
            "right_component",
            "relation",
            "structural_delta",
            "rarity_evidence_id",
        ):
            if not _non_empty(relation.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        relation_id = relation.get("relation_id")
        if relation_id in relation_ids:
            errors.append(f"{prefix}.relation_id must be unique")
        relation_ids.add(relation_id)
        for field in ("left_component", "right_component"):
            component = relation.get(field)
            if _non_empty(component) and component not in component_set:
                errors.append(f"{prefix}.{field} must reference a known component")
        if (
            _non_empty(relation.get("left_component"))
            and relation.get("left_component") == relation.get("right_component")
        ):
            errors.append(f"{prefix} must connect two different components")
        _score(errors, relation.get("rarity_strength"), f"{prefix}.rarity_strength")

    measures = payload.get("novelty_measures")
    if not isinstance(measures, list) or len(measures) != len(_NOVELTY_MEASURES):
        errors.append("novelty_measures must contain exactly five triangulation measures")
        measures = []
    seen_measures = set()
    measure_scores: List[float] = []
    for index, measure in enumerate(measures):
        prefix = f"novelty_measures[{index}]"
        if not isinstance(measure, dict):
            errors.append(f"{prefix} must be an object")
            continue
        name = measure.get("measure")
        if name not in _NOVELTY_MEASURES:
            errors.append(f"{prefix}.measure is not recognized")
        elif name in seen_measures:
            errors.append(f"{prefix}.measure must be unique")
        seen_measures.add(name)
        measure_scores.append(_score(errors, measure.get("score"), f"{prefix}.score"))
        if not _non_empty(measure.get("evidence_id")):
            errors.append(f"{prefix}.evidence_id must be a non-empty string")
        if not _non_empty(measure.get("rationale")):
            errors.append(f"{prefix}.rationale must be a non-empty string")
    if seen_measures != _NOVELTY_MEASURES:
        errors.append("novelty_measures must cover every required measure exactly once")
    spread = max(measure_scores) - min(measure_scores) if measure_scores else 0.0
    expected_disagreement = spread > 0.25
    if payload.get("novelty_measure_disagreement") is not expected_disagreement:
        errors.append(
            "novelty_measure_disagreement must reflect a score spread greater than 0.25"
        )
    if expected_disagreement and not _non_empty(payload.get("disagreement_rationale")):
        errors.append("disagreement_rationale is required when novelty measures disagree")

    absorption = payload.get("absorption_profile")
    if not isinstance(absorption, dict):
        errors.append("absorption_profile must be an object")
        absorption = {}
    if not _non_empty(absorption.get("host_capability_snapshot_id")):
        errors.append("absorption_profile.host_capability_snapshot_id must be a non-empty string")
    local_score = _score(
        errors, absorption.get("local_knowledge_score"), "absorption_profile.local_knowledge_score"
    )
    comprehension_cost = _score(
        errors, absorption.get("comprehension_cost"), "absorption_profile.comprehension_cost"
    )
    _string_list(
        errors, absorption.get("missing_concepts"), "absorption_profile.missing_concepts"
    )
    if not isinstance(absorption.get("independent_validator_available"), bool):
        errors.append("absorption_profile.independent_validator_available must be boolean")
    if comprehension_cost > 0.66 and not absorption.get("missing_concepts"):
        errors.append("high comprehension cost requires at least one missing concept")

    temporality = payload.get("knowledge_temporality")
    if not isinstance(temporality, dict):
        errors.append("knowledge_temporality must be an object")
        temporality = {}
    for field in ("evidence_as_of", "last_validated_at", "maturity_rationale"):
        if not _non_empty(temporality.get(field)):
            errors.append(f"knowledge_temporality.{field} must be a non-empty string")
    evidence_as_of = _utc_datetime(
        errors, temporality.get("evidence_as_of"), "knowledge_temporality.evidence_as_of"
    )
    last_validated_at = _utc_datetime(
        errors, temporality.get("last_validated_at"), "knowledge_temporality.last_validated_at"
    )
    if evidence_as_of and last_validated_at and last_validated_at < evidence_as_of:
        errors.append("knowledge_temporality.last_validated_at must not precede evidence_as_of")
    for path, timestamp in (
        ("knowledge_temporality.evidence_as_of", evidence_as_of),
        ("knowledge_temporality.last_validated_at", last_validated_at),
    ):
        if timestamp and evaluation_as_of and timestamp > evaluation_as_of:
            errors.append(f"{path} must not be later than evaluation_as_of")
    maturity = _score(
        errors, temporality.get("maturity_score"), "knowledge_temporality.maturity_score"
    )
    adoption = _score(
        errors,
        temporality.get("adoption_saturation"),
        "knowledge_temporality.adoption_saturation",
    )
    obsolescence = _score(
        errors,
        temporality.get("obsolescence_risk"),
        "knowledge_temporality.obsolescence_risk",
    )

    complement_profile = payload.get("complement_profile")
    if not isinstance(complement_profile, dict):
        errors.append("complement_profile must be an object")
        complement_profile = {}
    complements_required = complement_profile.get("complements_required")
    if not isinstance(complements_required, bool):
        errors.append("complement_profile.complements_required must be boolean")
    integration_cost = _score(
        errors,
        complement_profile.get("integration_cost"),
        "complement_profile.integration_cost",
    )
    complements = complement_profile.get("complements")
    if not isinstance(complements, list):
        errors.append("complement_profile.complements must be an array")
        complements = []
    if complements_required is True and not complements:
        errors.append("required complements must enumerate at least one complement")
    complement_ids = set()
    unavailable_complements = 0
    for index, complement in enumerate(complements):
        prefix = f"complement_profile.complements[{index}]"
        if not isinstance(complement, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("complement_id", "capability", "availability_evidence_id", "owner"):
            if not _non_empty(complement.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")
        complement_id = complement.get("complement_id")
        if complement_id in complement_ids:
            errors.append(f"{prefix}.complement_id must be unique")
        complement_ids.add(complement_id)
        for field in ("available", "compatible"):
            if not isinstance(complement.get(field), bool):
                errors.append(f"{prefix}.{field} must be boolean")
        if complement.get("available") is not True or complement.get("compatible") is not True:
            unavailable_complements += 1
    if unavailable_complements and integration_cost == 0:
        errors.append("unavailable or incompatible complements require non-zero integration cost")

    uncertainty = payload.get("uncertainty_profile")
    if not isinstance(uncertainty, dict):
        errors.append("uncertainty_profile must be an object")
        uncertainty = {}
    expected_value = _score(
        errors, uncertainty.get("expected_value"), "uncertainty_profile.expected_value"
    )
    outcome_variance = _score(
        errors, uncertainty.get("outcome_variance"), "uncertainty_profile.outcome_variance"
    )
    treatment = uncertainty.get("treatment")
    if treatment not in _UNCERTAINTY_TREATMENTS:
        errors.append("uncertainty_profile.treatment is not recognized")
    for field in ("treatment_rationale", "success_signal", "failure_signal", "falsifier"):
        if not _non_empty(uncertainty.get(field)):
            errors.append(f"uncertainty_profile.{field} must be a non-empty string")
    if treatment == "bounded_probe":
        for field in ("probe", "probe_budget_id"):
            if not _non_empty(uncertainty.get(field)):
                errors.append(f"uncertainty_profile.{field} is required for a bounded probe")
        if uncertainty.get("probe_reversible") is not True:
            errors.append("uncertainty_profile.probe_reversible must be true for a bounded probe")
    if treatment == "defer" and not _non_empty(uncertainty.get("defer_until")):
        errors.append("uncertainty_profile.defer_until is required when treatment is defer")

    for field in (
        "inverted_u_hardcoded",
        "citation_impact_used_as_value",
        "novelty_overrides_constitutional_gates",
        "profile_authorizes_mission",
    ):
        if payload.get(field) is not False:
            errors.append(f"{field} must be false")

    dimension_scores = {
        "conventional_core_strength": core_strength,
        "atypical_tail_strength": tail_strength,
        "local_knowledge_score": local_score,
        "comprehension_cost": comprehension_cost,
        "knowledge_maturity": maturity,
        "integration_cost": integration_cost,
        "outcome_variance": outcome_variance,
    }
    rubric_assessments = payload.get("rubric_assessments")
    if not isinstance(rubric_assessments, list) or len(rubric_assessments) != len(
        dimension_scores
    ):
        errors.append("rubric_assessments must contain exactly seven guideline dimensions")
        rubric_assessments = []
    seen_dimensions = set()
    for index, assessment in enumerate(rubric_assessments):
        prefix = f"rubric_assessments[{index}]"
        if not isinstance(assessment, dict):
            errors.append(f"{prefix} must be an object")
            continue
        dimension = assessment.get("dimension")
        if dimension not in dimension_scores:
            errors.append(f"{prefix}.dimension is not recognized")
            continue
        if dimension in seen_dimensions:
            errors.append(f"{prefix}.dimension must be unique")
        seen_dimensions.add(dimension)
        score = _score(errors, assessment.get("score"), f"{prefix}.score")
        if score != dimension_scores[dimension]:
            errors.append(f"{prefix}.score must match the corresponding profile score")
        if assessment.get("anchor") != _score_anchor(score):
            errors.append(f"{prefix}.anchor must match the provisional score band")
        _string_list(
            errors,
            assessment.get("evidence_ids"),
            f"{prefix}.evidence_ids",
            minimum=1,
        )
        if not _non_empty(assessment.get("rationale")):
            errors.append(f"{prefix}.rationale must be a non-empty string")
    if seen_dimensions != set(dimension_scores):
        errors.append("rubric_assessments must cover every guideline dimension exactly once")

    return {
        "valid": not errors,
        "errors": errors,
        "candidate_id": payload.get("candidate_id"),
        "conventional_core_strength": core_strength,
        "atypical_tail_strength": tail_strength,
        "novelty_measure_spread": spread,
        "novelty_measure_disagreement": expected_disagreement,
        "local_knowledge_score": local_score,
        "comprehension_cost": comprehension_cost,
        "knowledge_maturity": maturity,
        "adoption_saturation": adoption,
        "obsolescence_risk": obsolescence,
        "integration_cost": integration_cost,
        "expected_value": expected_value,
        "outcome_variance": outcome_variance,
        "uncertainty_treatment": treatment,
        "unavailable_complement_count": unavailable_complements,
        "mission_authorized": False,
    }


def _collect_evidence_ids(payload: Dict[str, Any]) -> List[str]:
    profile = payload.get("recombinant_profile", {})
    evidence_ids = list(profile.get("conventional_core_evidence_ids", []))
    evidence_ids.extend(
        relation.get("rarity_evidence_id")
        for relation in profile.get("atypical_relations", [])
        if isinstance(relation, dict)
    )
    evidence_ids.extend(
        measure.get("evidence_id")
        for measure in payload.get("novelty_measures", [])
        if isinstance(measure, dict)
    )
    complement_profile = payload.get("complement_profile", {})
    evidence_ids.extend(
        complement.get("availability_evidence_id")
        for complement in complement_profile.get("complements", [])
        if isinstance(complement, dict)
    )
    evidence_ids.extend(
        evidence_id
        for assessment in payload.get("rubric_assessments", [])
        if isinstance(assessment, dict)
        for evidence_id in assessment.get("evidence_ids", [])
    )
    return [item for item in evidence_ids if _non_empty(item)]


def evaluate_grounded_recombinant_candidate(
    *,
    payload: Dict[str, Any],
    registries: Dict[str, Any],
    eligibility: Dict[str, Any],
) -> Dict[str, Any]:
    """Ground the profile and compute a non-authorizing candidate disposition."""
    profile_report = validate_recombinant_value_profile(payload)
    grounding_errors: List[str] = []
    if not isinstance(registries, dict):
        grounding_errors.append("registries must be an object")
        registries = {}
    evidence_records = registries.get("evidence_records")
    comparison_populations = registries.get("comparison_populations")
    capability_snapshots = registries.get("capability_snapshots")
    if not isinstance(evidence_records, dict):
        grounding_errors.append("registries.evidence_records must be an object keyed by evidence ID")
        evidence_records = {}
    if not isinstance(comparison_populations, dict):
        grounding_errors.append(
            "registries.comparison_populations must be an object keyed by population ID"
        )
        comparison_populations = {}
    if not isinstance(capability_snapshots, dict):
        grounding_errors.append(
            "registries.capability_snapshots must be an object keyed by snapshot ID"
        )
        capability_snapshots = {}

    evaluation_as_of = _utc_datetime(
        grounding_errors, payload.get("evaluation_as_of"), "evaluation_as_of"
    )
    for evidence_id in _collect_evidence_ids(payload):
        record = evidence_records.get(evidence_id)
        prefix = f"evidence_records[{evidence_id}]"
        if not isinstance(record, dict):
            grounding_errors.append(f"{prefix} must exist")
            continue
        if record.get("status") != "verified":
            grounding_errors.append(f"{prefix}.status must be verified")
        observed_at = _utc_datetime(grounding_errors, record.get("observed_at"), f"{prefix}.observed_at")
        if observed_at and evaluation_as_of and observed_at > evaluation_as_of:
            grounding_errors.append(f"{prefix} must not postdate the evaluation")
        if not _non_empty(record.get("source_id")):
            grounding_errors.append(f"{prefix}.source_id must be a non-empty string")

    population_id = payload.get("comparison_population_id")
    population = comparison_populations.get(population_id)
    if not isinstance(population, dict):
        grounding_errors.append(f"comparison_populations[{population_id}] must exist")
    else:
        if population.get("as_of") != payload.get("comparison_as_of"):
            grounding_errors.append("comparison population as_of must match comparison_as_of")
        candidate_count = population.get("candidate_count")
        if not isinstance(candidate_count, int) or isinstance(candidate_count, bool) or candidate_count < 2:
            grounding_errors.append("comparison population must contain at least two candidates")
        if not _non_empty(population.get("selection_rule")):
            grounding_errors.append("comparison population selection_rule must be documented")

    snapshot_id = payload.get("absorption_profile", {}).get("host_capability_snapshot_id")
    snapshot = capability_snapshots.get(snapshot_id)
    if not isinstance(snapshot, dict):
        grounding_errors.append(f"capability_snapshots[{snapshot_id}] must exist")
    else:
        snapshot_as_of = _utc_datetime(
            grounding_errors, snapshot.get("as_of"), f"capability_snapshots[{snapshot_id}].as_of"
        )
        if snapshot_as_of and evaluation_as_of and snapshot_as_of > evaluation_as_of:
            grounding_errors.append("host capability snapshot must not postdate the evaluation")
        _string_list(
            grounding_errors,
            snapshot.get("demonstrated_capabilities"),
            f"capability_snapshots[{snapshot_id}].demonstrated_capabilities",
            minimum=1,
        )

    eligibility_errors: List[str] = []
    if not isinstance(eligibility, dict):
        eligibility_errors.append("eligibility must be an object")
        eligibility = {}
    required_true = (
        "consequence_eligible",
        "causally_coherent",
        "constitutional_gates_passed",
        "structural_delta_verified",
    )
    for field in required_true:
        if eligibility.get(field) is not True:
            eligibility_errors.append(f"eligibility.{field} must be true")
    if eligibility.get("baseline_reducible") is not False:
        eligibility_errors.append("eligibility.baseline_reducible must be false")
    if eligibility.get("human_authority_preserved") is not True:
        eligibility_errors.append("eligibility.human_authority_preserved must be true")

    complement_profile = payload.get("complement_profile", {})
    complements = {
        item.get("complement_id"): item
        for item in complement_profile.get("complements", [])
        if isinstance(item, dict) and _non_empty(item.get("complement_id"))
    }
    all_complements_ready = all(
        item.get("available") is True and item.get("compatible") is True
        for item in complements.values()
    )
    treatment = payload.get("uncertainty_profile", {}).get("treatment")
    probe_complement_ids = eligibility.get("probe_complement_ids", [])
    probe_ids_valid = isinstance(probe_complement_ids, list) and all(
        isinstance(item, str) and item in complements for item in probe_complement_ids
    )
    probe_complements_ready = probe_ids_valid and all(
        complements[item].get("available") is True
        and complements[item].get("compatible") is True
        for item in probe_complement_ids
    )

    if not profile_report["valid"] or grounding_errors or eligibility_errors:
        disposition = "reject"
        disposition_reason = "profile, grounding, or hard-gate validation failed"
    elif treatment == "normal_progression" and all_complements_ready:
        disposition = "progress"
        disposition_reason = "grounding and hard gates pass and all complements are ready"
    elif treatment == "bounded_probe" and probe_complements_ready:
        disposition = "bounded_probe"
        disposition_reason = "a reversible discriminating probe can run with ready complements"
    elif eligibility.get("frontier_preservation_requested") is True:
        disposition = "preserve"
        disposition_reason = "the grounded candidate is retained without current execution authority"
    else:
        disposition = "defer"
        disposition_reason = "the declared treatment cannot proceed with currently ready complements"

    return {
        "valid": not profile_report["errors"] and not grounding_errors and not eligibility_errors,
        "profile_errors": profile_report["errors"],
        "grounding_errors": grounding_errors,
        "eligibility_errors": eligibility_errors,
        "candidate_id": payload.get("candidate_id"),
        "disposition": disposition,
        "disposition_reason": disposition_reason,
        "grounded_evidence_count": len(_collect_evidence_ids(payload)) - len(
            [error for error in grounding_errors if error.startswith("evidence_records[") and "must exist" in error]
        ),
        "all_complements_ready": all_complements_ready,
        "probe_complements_ready": probe_complements_ready,
        "guideline_version": RECOMBINANT_EVALUATION_GUIDELINE["version"],
        "mission_authorized": False,
        "human_decision_required": True,
    }
