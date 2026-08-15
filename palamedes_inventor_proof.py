#!/usr/bin/env python3
"""External, human-reviewed, outcome-bearing proof gate for Palamedes invention."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List

from palamedes_observe import utc_now
from palamedes_proof import (
    fingerprint,
    load_object,
    prepare_run,
    score_run,
    write_object,
)


SAFE_ID = re.compile(r"[a-z0-9][a-z0-9-]{2,63}")
AXES = (
    "opportunity_discovery",
    "causal_mechanism",
    "project_specificity",
    "falsifiability",
    "decision_usefulness",
)


def validate_inventor_portfolio(portfolio: Dict[str, Any]) -> List[str]:
    """Return violations of the external Inventor preregistration contract."""
    errors: List[str] = []
    if portfolio.get("inventor_proof_version") != "palamedes-inventor-proof/1":
        errors.append("inventor_proof_version must be palamedes-inventor-proof/1")
    protocol = portfolio.get("inventor_protocol")
    if not isinstance(protocol, dict):
        return errors + ["inventor_protocol must be an object"]
    required_true = (
        "external_projects_required",
        "independent_human_review_required",
        "equal_call_comparator_required",
        "probe_preregistered_before_reveal",
        "measured_outcomes_required",
        "failed_cases_retained",
    )
    for field in required_true:
        if protocol.get(field) is not True:
            errors.append(f"inventor_protocol.{field} must be true")
    if protocol.get("comparison_condition") != "tournament":
        errors.append("comparison_condition must be tournament")
    if protocol.get("treatment_condition") != "palamedes":
        errors.append("treatment_condition must be palamedes")
    if int(protocol.get("calls_per_condition", 0)) != 4:
        errors.append("calls_per_condition must be 4")
    cases = portfolio.get("cases")
    if not isinstance(cases, list) or len(cases) != 3:
        return errors + ["exactly three external cases are required"]
    owners = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"cases[{index}] must be an object")
            continue
        prefix = f"cases[{index}]"
        owner_id = str(case.get("owner_id", ""))
        if not SAFE_ID.fullmatch(owner_id):
            errors.append(f"{prefix}.owner_id must be a safe non-secret ID")
        if owner_id in owners:
            errors.append(f"duplicate owner_id: {owner_id}")
        owners.add(owner_id)
        if case.get("owner_relationship") != "independent_external":
            errors.append(f"{prefix}.owner_relationship must be independent_external")
        if case.get("palamedes_tuning_exposure") is not False:
            errors.append(f"{prefix}.palamedes_tuning_exposure must be false")
        probe = case.get("probe_preregistration")
        if not isinstance(probe, dict):
            errors.append(f"{prefix}.probe_preregistration must be an object")
            continue
        for field in (
            "decision_to_be_changed",
            "intervention_window",
            "primary_metric",
            "success_threshold",
            "failure_threshold",
            "measurement_source",
        ):
            if not str(probe.get(field, "")).strip():
                errors.append(f"{prefix}.probe_preregistration.{field} is required")
    gate = portfolio.get("inventor_success_gate")
    if not isinstance(gate, dict):
        errors.append("inventor_success_gate must be an object")
    else:
        expected = {
            "minimum_external_cases": 3,
            "minimum_independent_human_reviews_per_case": 3,
            "minimum_palamedes_preferred_cases": 2,
            "minimum_measured_probe_outcomes": 3,
            "minimum_positive_attributable_outcomes": 2,
        }
        for field, minimum in expected.items():
            if int(gate.get(field, 0)) < minimum:
                errors.append(f"inventor_success_gate.{field} must be at least {minimum}")
    return errors


def prepare_inventor_run(
    portfolio: Dict[str, Any], *, run_root: Path, run_id: str = ""
) -> Dict[str, Any]:
    errors = validate_inventor_portfolio(portfolio)
    if errors:
        raise ValueError("invalid inventor portfolio: " + "; ".join(errors))
    result = prepare_run(portfolio, run_root=run_root, run_id=run_id)
    run_path = Path(result["run_path"])
    custody = {
        "inventor_custody_version": "palamedes-inventor-custody/1",
        "run_id": result["run_id"],
        "prepared_at": utc_now(),
        "portfolio_fingerprint": fingerprint(portfolio),
        "answer_key_must_remain_private_until_reviews_complete": True,
        "external_evidence_fabrication_forbidden": True,
    }
    custody["custody_fingerprint"] = fingerprint(custody)
    write_object(run_path / "private" / "inventor-custody.json", custody)
    return result


def import_human_review(run_path: Path, response: Dict[str, Any]) -> Dict[str, Any]:
    """Import one independent human's complete origin-blinded review append-once."""
    packet = load_object(run_path / "blind" / "packet.json")
    manifest = load_object(run_path / "manifest.json")
    reviewer_id = str(response.get("reviewer_id", ""))
    if not SAFE_ID.fullmatch(reviewer_id):
        raise ValueError("reviewer_id must be a safe non-secret ID")
    if response.get("reviewer_kind") != "human":
        raise ValueError("reviewer_kind must be human")
    if response.get("reviewer_relationship") != "independent":
        raise ValueError("reviewer_relationship must be independent")
    if response.get("origin_visible") is not False:
        raise ValueError("origin_visible must be false")
    if not str(response.get("independence_attestation", "")).strip():
        raise ValueError("independence_attestation is required")
    case_owners = {
        case["case_id"]: case["owner_id"] for case in manifest["portfolio"]["cases"]
    }
    expected_cases = {case["case_id"] for case in packet["cases"]}
    rows = response.get("reviews")
    if not isinstance(rows, list) or {row.get("case_id") for row in rows} != expected_cases:
        raise ValueError("reviews must cover every blinded case exactly once")
    normalized = []
    for row in rows:
        case_id = row["case_id"]
        if reviewer_id == case_owners[case_id]:
            raise ValueError("a case owner cannot review their own case")
        review = row.get("review")
        if not isinstance(review, dict):
            raise ValueError(f"{case_id} review must be an object")
        if review.get("preferred") not in {"A", "B", "tie"}:
            raise ValueError(f"{case_id} preferred must be A, B, or tie")
        if not str(review.get("rationale", "")).strip():
            raise ValueError(f"{case_id} rationale is required")
        if not str(review.get("decision_difference", "")).strip():
            raise ValueError(f"{case_id} decision_difference is required")
        confidence = review.get("confidence")
        if not isinstance(confidence, int) or not 0 <= confidence <= 100:
            raise ValueError(f"{case_id} confidence must be an integer 0-100")
        scores = review.get("scores")
        for label in ("A", "B"):
            label_scores = scores.get(label) if isinstance(scores, dict) else None
            if not isinstance(label_scores, dict) or set(label_scores) != set(packet["rubric"]):
                raise ValueError(f"{case_id} scores.{label} must cover the rubric")
            if any(not isinstance(value, int) or not 1 <= value <= 5 for value in label_scores.values()):
                raise ValueError(f"{case_id} scores.{label} values must be integers 1-5")
        normalized.append({
            "case_id": case_id,
            "reviewer_id": reviewer_id,
            "reviewer_kind": "human",
            "reviewer_relationship": "independent",
            "origin_visible": False,
            "review": review,
        })
    record = {
        "blind_review_version": "palamedes-inventor-human-review/1",
        "run_id": packet["run_id"],
        "reviewer_id": reviewer_id,
        "reviewer_kind": "human",
        "reviewer_relationship": "independent",
        "independence_attestation": response["independence_attestation"],
        "reviewed_at": utc_now(),
        "reviews": normalized,
    }
    record["review_fingerprint"] = fingerprint(record)
    target = run_path / "reviews" / f"{reviewer_id}.json"
    if target.exists():
        raise ValueError(f"review is append-once and already exists: {target}")
    write_object(target, record)
    return record


def record_probe_outcome(run_path: Path, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Record a preregistered real-world probe outcome without inferring success."""
    manifest = load_object(run_path / "manifest.json")
    case_id = str(payload.get("case_id", ""))
    cases = {case["case_id"]: case for case in manifest["portfolio"]["cases"]}
    if case_id not in cases:
        raise ValueError(f"unknown case_id: {case_id}")
    for field in ("started_at", "ended_at", "measurement_source", "raw_evidence", "owner_attestation"):
        if not str(payload.get(field, "")).strip():
            raise ValueError(f"probe outcome {field} is required")
    if payload.get("measurement_provenance") not in {"measured", "external_dataset"}:
        raise ValueError("measurement_provenance must be measured or external_dataset")
    if payload.get("selected_system") not in {"tournament", "palamedes", "neither"}:
        raise ValueError("selected_system must be tournament, palamedes, or neither")
    if not isinstance(payload.get("metric_value"), (int, float)):
        raise ValueError("metric_value must be numeric")
    if not isinstance(payload.get("attributable_decision"), bool):
        raise ValueError("attributable_decision must be boolean")
    if not isinstance(payload.get("threshold_passed"), bool):
        raise ValueError("threshold_passed must be boolean")
    preregistered = cases[case_id]["probe_preregistration"]
    if payload["measurement_source"] != preregistered["measurement_source"]:
        raise ValueError("measurement_source differs from preregistration")
    record = {
        "inventor_probe_outcome_version": "palamedes-inventor-probe-outcome/1",
        "recorded_at": utc_now(),
        "case_id": case_id,
        "probe_preregistration_fingerprint": fingerprint(preregistered),
        **payload,
    }
    record["outcome_fingerprint"] = fingerprint(record)
    target = run_path / "cases" / case_id / "inventor-probe-outcome.json"
    if target.exists():
        raise ValueError(f"probe outcome is append-once and already exists: {target}")
    write_object(target, record)
    return record


def score_inventor_run(run_path: Path) -> Dict[str, Any]:
    """Score the ordinary proof and then apply the stricter Inventor claim gate."""
    manifest = load_object(run_path / "manifest.json")
    errors = validate_inventor_portfolio(manifest["portfolio"])
    if errors:
        raise ValueError("invalid inventor portfolio: " + "; ".join(errors))
    base = score_run(run_path)
    gate = manifest["portfolio"]["inventor_success_gate"]
    human_counts = {case["case_id"]: 0 for case in manifest["portfolio"]["cases"]}
    key = load_object(run_path / "private" / "answer-key.json")
    labels = {row["case_id"]: row["labels"] for row in key["cases"]}
    human_votes = {case_id: {"palamedes": 0, "tournament": 0, "tie": 0} for case_id in human_counts}
    for path in sorted((run_path / "reviews").glob("*.json")):
        record = load_object(path)
        if record.get("reviewer_kind") != "human" or record.get("reviewer_relationship") != "independent":
            continue
        for row in record.get("reviews", []):
            if row.get("origin_visible") is False and int(row.get("review", {}).get("confidence", 0)) >= 60:
                case_id = row["case_id"]
                human_counts[case_id] += 1
                preferred = row["review"]["preferred"]
                system = "tie" if preferred == "tie" else labels[case_id][preferred]
                human_votes[case_id][system] += 1
    outcomes = []
    for case_id in human_counts:
        path = run_path / "cases" / case_id / "inventor-probe-outcome.json"
        if path.exists():
            outcomes.append(load_object(path))
    positive = sum(
        row.get("selected_system") == "palamedes"
        and row.get("attributable_decision") is True
        and row.get("threshold_passed") is True
        for row in outcomes
    )
    human_gate = all(
        count >= int(gate["minimum_independent_human_reviews_per_case"])
        for count in human_counts.values()
    )
    palamedes_preferred_cases = sum(
        votes["palamedes"] > votes["tournament"] for votes in human_votes.values()
    )
    quality_gate = (
        human_gate
        and palamedes_preferred_cases
        >= int(gate["minimum_palamedes_preferred_cases"])
    )
    outcome_gate = (
        len(outcomes) >= int(gate["minimum_measured_probe_outcomes"])
        and positive >= int(gate["minimum_positive_attributable_outcomes"])
    )
    result = {
        "inventor_score_version": "palamedes-inventor-score/1",
        "run_id": base["run_id"],
        "scored_at": utc_now(),
        "external_case_count": len(human_counts),
        "qualifying_human_reviews_by_case": human_counts,
        "qualifying_human_votes_by_case": human_votes,
        "palamedes_preferred_cases": palamedes_preferred_cases,
        "human_review_gate_passed": human_gate,
        "quality_gate_passed": quality_gate,
        "measured_probe_outcome_count": len(outcomes),
        "positive_attributable_outcome_count": positive,
        "outcome_gate_passed": outcome_gate,
        "inventor_claim_demonstrated": quality_gate and outcome_gate,
        "base_proof_score_fingerprint": fingerprint(base),
        "claim_boundary": "Repeated external-project invention support; not universal creativity, AGI, or startup-success proof.",
    }
    result["score_fingerprint"] = fingerprint(result)
    write_object(run_path / "inventor-score.json", result)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("validate")
    command.add_argument("--portfolio", required=True)
    command = sub.add_parser("prepare")
    command.add_argument("--portfolio", required=True)
    command.add_argument("--run-root", default="experiments/inventor-proof-runs")
    command.add_argument("--run-id", default="")
    command = sub.add_parser("import-review")
    command.add_argument("--run", required=True)
    command.add_argument("--response", required=True)
    command = sub.add_parser("probe-outcome")
    command.add_argument("--run", required=True)
    command.add_argument("--response", required=True)
    command = sub.add_parser("score")
    command.add_argument("--run", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "validate":
        errors = validate_inventor_portfolio(load_object(Path(args.portfolio)))
        result = {"valid": not errors, "errors": errors}
    elif args.command == "prepare":
        result = prepare_inventor_run(load_object(Path(args.portfolio)), run_root=Path(args.run_root), run_id=args.run_id)
    elif args.command == "import-review":
        result = import_human_review(Path(args.run), load_object(Path(args.response)))
    elif args.command == "probe-outcome":
        result = record_probe_outcome(Path(args.run), load_object(Path(args.response)))
    else:
        result = score_inventor_run(Path(args.run))
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
