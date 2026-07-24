#!/usr/bin/env python3
"""Blind comparison utilities for Palamedes strategy reports."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


def load_json_object(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def validate_dataset(dataset: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    rubric = dataset.get("rubric")
    cases = dataset.get("cases")
    gate = dataset.get("success_gate")
    protocol = dataset.get("generation_protocol")
    if not isinstance(protocol, dict):
        errors.append("generation_protocol must be an object")
    else:
        for field in (
            "model_rule",
            "baseline_system_prompt",
            "palamedes_action",
            "report_schema",
            "artifact_rule",
            "run_rule",
        ):
            if not str(protocol.get(field, "")).strip():
                errors.append(f"generation_protocol.{field} is required")
    if not isinstance(rubric, dict) or not rubric:
        errors.append("rubric must be a non-empty object")
    else:
        total_weight = 0
        for name, item in rubric.items():
            if not isinstance(item, dict):
                errors.append(f"rubric.{name} must be an object")
                continue
            weight = item.get("weight")
            if not isinstance(weight, int) or weight <= 0:
                errors.append(f"rubric.{name}.weight must be a positive integer")
            else:
                total_weight += weight
        if total_weight != 100:
            errors.append("rubric weights must total 100")
    if not isinstance(cases, list) or len(cases) < 3:
        errors.append("cases must contain at least three items")
    else:
        seen = set()
        for index, case in enumerate(cases):
            if not isinstance(case, dict):
                errors.append(f"cases[{index}] must be an object")
                continue
            case_id = str(case.get("id", "")).strip()
            if not case_id:
                errors.append(f"cases[{index}].id is required")
            elif case_id in seen:
                errors.append(f"duplicate case id: {case_id}")
            seen.add(case_id)
            repository = Path(str(case.get("repository", "")))
            if not repository.is_dir():
                errors.append(f"case repository does not exist: {repository}")
            if not str(case.get("required_decision", "")).strip():
                errors.append(f"cases[{index}].required_decision is required")
    if not isinstance(gate, dict):
        errors.append("success_gate must be an object")
    return errors


def _labels(case_id: str, seed: str) -> Tuple[str, str]:
    digest = hashlib.sha256(f"{seed}:{case_id}".encode("utf-8")).digest()
    return ("A", "B") if digest[0] % 2 == 0 else ("B", "A")


def _report_path(directory: Path, case_id: str) -> Path:
    return directory / f"{case_id}.json"


def prepare_blind_packet(
    dataset: Dict[str, Any],
    *,
    baseline_dir: Path,
    candidate_dir: Path,
    seed: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    errors = validate_dataset(dataset)
    if errors:
        raise ValueError("invalid benchmark dataset: " + "; ".join(errors))
    packet_cases = []
    key_cases = []
    for case in dataset["cases"]:
        case_id = case["id"]
        baseline = load_json_object(_report_path(baseline_dir, case_id))
        candidate = load_json_object(_report_path(candidate_dir, case_id))
        baseline_label, candidate_label = _labels(case_id, seed)
        reports = {baseline_label: baseline, candidate_label: candidate}
        packet_cases.append(
            {
                "case_id": case_id,
                "question": case["question"],
                "project_stage": case["project_stage"],
                "required_decision": case["required_decision"],
                "reports": {"A": reports["A"], "B": reports["B"]},
            }
        )
        key_cases.append(
            {
                "case_id": case_id,
                "labels": {baseline_label: "baseline", candidate_label: "palamedes"},
            }
        )
    packet = {
        "version": dataset.get("version", "1"),
        "rubric": dataset["rubric"],
        "instructions": {
            "score_range": [1, 5],
            "required_fields": ["reviewer", "case_id", "scores", "attributable_decision"],
            "note": "Reviewers must not receive the separate answer key.",
        },
        "cases": packet_cases,
    }
    key = {
        "version": dataset.get("version", "1"),
        "seed_sha256": hashlib.sha256(seed.encode("utf-8")).hexdigest(),
        "success_gate": dataset["success_gate"],
        "cases": key_cases,
    }
    return packet, key


def _weighted_score(scores: Dict[str, Any], rubric: Dict[str, Any]) -> float:
    total = 0.0
    for dimension, item in rubric.items():
        value = scores.get(dimension)
        if not isinstance(value, (int, float)) or not 1 <= value <= 5:
            raise ValueError(f"score {dimension} must be between 1 and 5")
        total += float(value) * int(item["weight"])
    return round(total / 100.0, 3)


def score_reviews(
    packet: Dict[str, Any],
    key: Dict[str, Any],
    reviews: Iterable[Dict[str, Any]],
) -> Dict[str, Any]:
    rubric = packet.get("rubric", {})
    label_keys = {
        item["case_id"]: item["labels"]
        for item in key.get("cases", [])
        if isinstance(item, dict) and isinstance(item.get("labels"), dict)
    }
    known_cases = {item["case_id"] for item in packet.get("cases", [])}
    results = []
    reviewer_names = set()
    for review in reviews:
        case_id = str(review.get("case_id", "")).strip()
        reviewer = str(review.get("reviewer", "")).strip()
        if case_id not in known_cases or case_id not in label_keys:
            raise ValueError(f"unknown review case: {case_id}")
        if not reviewer:
            raise ValueError("reviewer is required")
        reviewer_names.add(reviewer)
        scores = review.get("scores")
        if not isinstance(scores, dict) or not isinstance(scores.get("A"), dict) or not isinstance(scores.get("B"), dict):
            raise ValueError("review scores must contain A and B objects")
        weighted = {
            "A": _weighted_score(scores["A"], rubric),
            "B": _weighted_score(scores["B"], rubric),
        }
        if weighted["A"] == weighted["B"]:
            preferred_label = "tie"
            preferred_system = "tie"
        else:
            preferred_label = "A" if weighted["A"] > weighted["B"] else "B"
            preferred_system = label_keys[case_id][preferred_label]
        results.append(
            {
                "case_id": case_id,
                "reviewer": reviewer,
                "weighted_scores": weighted,
                "preferred_label": preferred_label,
                "preferred_system": preferred_system,
                "attributable_decision": bool(review.get("attributable_decision", False)),
                "decision_note": str(review.get("decision_note", "")).strip(),
            }
        )
    case_results = []
    for case_id in sorted(known_cases):
        case_reviews = [item for item in results if item["case_id"] == case_id]
        palamedes_votes = sum(item["preferred_system"] == "palamedes" for item in case_reviews)
        baseline_votes = sum(item["preferred_system"] == "baseline" for item in case_reviews)
        winner = "tie"
        if palamedes_votes > baseline_votes:
            winner = "palamedes"
        elif baseline_votes > palamedes_votes:
            winner = "baseline"
        case_results.append(
            {
                "case_id": case_id,
                "review_count": len(case_reviews),
                "palamedes_votes": palamedes_votes,
                "baseline_votes": baseline_votes,
                "winner": winner,
                "attributable_decision": any(
                    item["preferred_system"] == "palamedes" and item["attributable_decision"]
                    for item in case_reviews
                ),
            }
        )
    gate = key.get("success_gate", {})
    palamedes_wins = sum(item["winner"] == "palamedes" for item in case_results)
    attributable = sum(item["attributable_decision"] for item in case_results)
    reviewed_cases = sum(item["review_count"] > 0 for item in case_results)
    passed = (
        reviewed_cases >= int(gate.get("minimum_cases", 3))
        and palamedes_wins >= int(gate.get("palamedes_preferred_cases", 2))
        and attributable >= int(gate.get("minimum_attributable_decisions", 1))
    )
    return {
        "ok": passed,
        "reviewer_count": len(reviewer_names),
        "reviewed_cases": reviewed_cases,
        "palamedes_wins": palamedes_wins,
        "attributable_decisions": attributable,
        "gate": gate,
        "case_results": case_results,
        "reviews": results,
    }
