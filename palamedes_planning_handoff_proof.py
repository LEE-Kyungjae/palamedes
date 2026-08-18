#!/usr/bin/env python3
"""Blindly compare mission-only and planning-brief downstream planner handoffs."""

from __future__ import annotations

import argparse
import hashlib
import json
import secrets
from pathlib import Path
from typing import Any, Dict, List

from palamedes_observe import utc_now
from palamedes_proof import MeteredCodex, fingerprint, load_object, write_object


RUBRIC = {
    "mission_fidelity": {"weight": 20},
    "experience_and_scope_completeness": {"weight": 20},
    "dependency_and_sequence_coherence": {"weight": 20},
    "uncertainty_honesty": {"weight": 20},
    "downstream_actionability": {"weight": 20},
}


def validate_execution_plan(plan: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if not isinstance(plan, dict):
        return ["execution plan must be an object"]
    for field in ("plan_summary", "user_outcome", "first_authorized_action"):
        if not isinstance(plan.get(field), str) or not plan[field].strip():
            errors.append(f"{field} must be a non-empty string")
    for field in ("acceptance_tests", "risk_controls", "unresolved_questions"):
        value = plan.get(field)
        if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
            errors.append(f"{field} must be a string list")
    workstreams = plan.get("workstreams")
    if not isinstance(workstreams, list) or not workstreams:
        errors.append("workstreams must be a non-empty list")
        workstreams = []
    workstream_ids = set()
    for index, item in enumerate(workstreams):
        prefix = f"workstreams[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        item_id = item.get("workstream_id")
        if not isinstance(item_id, str) or not item_id.strip() or item_id in workstream_ids:
            errors.append(f"{prefix}.workstream_id must be non-empty and unique")
        workstream_ids.add(item_id)
        for field in ("objective", "inputs", "outputs", "dependencies"):
            value = item.get(field)
            if field == "objective":
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"{prefix}.objective must be a non-empty string")
            elif not isinstance(value, list) or not all(isinstance(v, str) and v.strip() for v in value):
                errors.append(f"{prefix}.{field} must be a string list")
    sequence = plan.get("sequence")
    if not isinstance(sequence, list) or not sequence:
        errors.append("sequence must be a non-empty list")
        sequence = []
    for index, phase in enumerate(sequence):
        prefix = f"sequence[{index}]"
        if not isinstance(phase, dict):
            errors.append(f"{prefix} must be an object")
            continue
        for field in ("phase", "entry_gate", "exit_gate"):
            if not isinstance(phase.get(field), str) or not phase[field].strip():
                errors.append(f"{prefix}.{field} must be a non-empty string")
        ids = phase.get("workstream_ids")
        if not isinstance(ids, list) or not ids or not set(ids).issubset(workstream_ids):
            errors.append(f"{prefix}.workstream_ids must reference declared workstreams")
    assumptions = plan.get("assumptions")
    if not isinstance(assumptions, list):
        errors.append("assumptions must be a list")
        assumptions = []
    for index, item in enumerate(assumptions):
        prefix = f"assumptions[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if item.get("status") not in {"evidenced", "assumed", "unresolved"}:
            errors.append(f"{prefix}.status is invalid")
        for field in ("statement", "evidence_or_probe"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(f"{prefix}.{field} must be a non-empty string")
    if plan.get("execution_authority_issued") is not False:
        errors.append("execution_authority_issued must be false")
    return errors


def _planner_shape() -> str:
    return """{
  "plan_summary": "...",
  "user_outcome": "...",
  "assumptions": [{"statement":"...","status":"evidenced|assumed|unresolved","evidence_or_probe":"..."}],
  "workstreams": [{"workstream_id":"...","objective":"...","inputs":["..."],"outputs":["..."],"dependencies":["..."]}],
  "sequence": [{"phase":"...","workstream_ids":["..."],"entry_gate":"...","exit_gate":"..."}],
  "acceptance_tests": ["..."],
  "risk_controls": ["..."],
  "unresolved_questions": ["..."],
  "first_authorized_action": "...",
  "execution_authority_issued": false
}"""


def generate_planner_handoff(material: Dict[str, Any], model: str = "") -> Dict[str, Any]:
    engine = MeteredCodex(model=model)
    plan = engine.call(
        system=(
            "You are a downstream planner receiving bounded planning material. Produce the most "
            "decision-ready implementation handoff supported by that material. Do not infer hidden "
            "resources or issue execution authority. Return JSON only."
        ),
        prompt=f"""Return exactly this shape:
{_planner_shape()}

Planning material:
{json.dumps(material, ensure_ascii=False)}""",
    )
    errors = validate_execution_plan(plan)
    if errors:
        raise ValueError("invalid planner handoff: " + "; ".join(errors))
    return {"plan": plan, "usage": engine.usage()}


def _review_shape() -> str:
    dimensions = ",".join(f'"{name}":1' for name in RUBRIC)
    return (
        '{"scores":{"A":{' + dimensions + '},"B":{' + dimensions
        + '}},"preferred":"A|B|tie","rationale":"...",'
        '"reconstruction_burden":{"A":1,"B":1},"confidence":0}'
    )


def review_blind_case(packet: Dict[str, Any], reviewer_id: str, model: str = "") -> Dict[str, Any]:
    engine = MeteredCodex(model=model)
    review = engine.call(
        system=(
            "You are an origin-blinded downstream planning evaluator. Do not reward length. "
            "Score only fidelity, completeness, dependency coherence, uncertainty honesty, and "
            "actionability. Reconstruction burden is 1 (planner must reinvent little) to 5 "
            "(planner must reconstruct most of the plan). Return JSON only."
        ),
        prompt=f"""Return exactly:
{_review_shape()}

Rubric:
{json.dumps(RUBRIC, ensure_ascii=False)}
Blind packet:
{json.dumps(packet, ensure_ascii=False)}""",
    )
    for label in ("A", "B"):
        scores = review.get("scores", {}).get(label, {})
        for dimension in RUBRIC:
            if not isinstance(scores.get(dimension), int) or not 1 <= scores[dimension] <= 5:
                raise ValueError(f"invalid review score {label}.{dimension}")
        burden = review.get("reconstruction_burden", {}).get(label)
        if not isinstance(burden, int) or not 1 <= burden <= 5:
            raise ValueError(f"invalid reconstruction burden {label}")
    if review.get("preferred") not in {"A", "B", "tie"}:
        raise ValueError("invalid blind preference")
    return {"reviewer_id": reviewer_id, "review": review, "usage": engine.usage()}


def _weighted(scores: Dict[str, int]) -> float:
    return round(sum(scores[name] * RUBRIC[name]["weight"] for name in RUBRIC) / 100, 3)


def run_proof(config: Dict[str, Any], run_path: Path, *, model: str = "") -> Dict[str, Any]:
    if run_path.exists():
        raise ValueError(f"proof run already exists: {run_path}")
    mission_record = load_object(Path(config["mission_path"]))
    information = load_object(Path(config["information_path"]))
    planning_generation = load_object(Path(config["planning_brief_path"]))
    planning_brief = planning_generation["planning_brief"]
    mission = mission_record.get("mission", mission_record)
    shared = {"mission": mission, "information": information}
    manifest = {
        "planning_handoff_proof_version": "palamedes-planning-handoff-proof/1",
        "run_id": config["run_id"],
        "prepared_at": utc_now(),
        "claim": config["claim"],
        "claim_boundary": config["claim_boundary"],
        "mission_fingerprint": fingerprint(mission),
        "information_fingerprint": information.get("information_fingerprint", fingerprint(information)),
        "planning_brief_fingerprint": planning_brief["planning_brief_fingerprint"],
        "reviewer_count": int(config.get("reviewer_count", 3)),
        "rubric": RUBRIC,
    }
    write_object(run_path / "manifest.json", manifest)
    conditions = {
        "mission_only": {"mission": mission, "information": information},
        "planning_brief": {**shared, "planning_brief": planning_brief},
    }
    for name, material in conditions.items():
        generated = generate_planner_handoff(material, model=model)
        write_object(run_path / "conditions" / f"{name}.json", {
            "condition": name, "generated_at": utc_now(), **generated,
        })

    seed = secrets.token_hex(32)
    first, second = (
        ("mission_only", "planning_brief")
        if hashlib.sha256(seed.encode()).digest()[0] % 2 == 0
        else ("planning_brief", "mission_only")
    )
    labels = {"A": first, "B": second}
    blind = {
        "blind_packet_version": "palamedes-planning-handoff-blind/1",
        "run_id": config["run_id"],
        "mission": mission,
        "required_decision": information.get("required_decision", "Produce a bounded implementation handoff."),
        "rubric": RUBRIC,
        "plans": {
            label: load_object(run_path / "conditions" / f"{condition}.json")["plan"]
            for label, condition in labels.items()
        },
        "origin_visible": False,
    }
    write_object(run_path / "blind" / "packet.json", blind)
    write_object(run_path / "private" / "answer-key.json", {
        "labels": labels, "seed_sha256": hashlib.sha256(seed.encode()).hexdigest()
    })
    reviews = []
    for index in range(manifest["reviewer_count"]):
        review = review_blind_case(blind, f"codex-planning-blind-{index + 1}", model=model)
        reviews.append(review)
        write_object(run_path / "reviews" / f"review-{index + 1}.json", review)

    votes = {"mission_only": 0, "planning_brief": 0, "tie": 0}
    weighted = {"mission_only": [], "planning_brief": []}
    burden = {"mission_only": [], "planning_brief": []}
    for item in reviews:
        review = item["review"]
        preferred = review["preferred"]
        votes["tie" if preferred == "tie" else labels[preferred]] += 1
        for label, condition in labels.items():
            weighted[condition].append(_weighted(review["scores"][label]))
            burden[condition].append(review["reconstruction_burden"][label])
    condition_usage = {
        name: load_object(run_path / "conditions" / f"{name}.json")["usage"]
        for name in conditions
    }
    score = {
        "planning_handoff_score_version": "palamedes-planning-handoff-score/1",
        "run_id": config["run_id"],
        "scored_at": utc_now(),
        "votes": votes,
        "weighted_scores": weighted,
        "mean_reconstruction_burden": {
            name: round(sum(values) / len(values), 3) for name, values in burden.items()
        },
        "condition_usage": condition_usage,
        "review_usage": [item["usage"] for item in reviews],
        "claim_demonstrated": votes["planning_brief"] > votes["mission_only"],
        "claim_boundary": config["claim_boundary"],
    }
    write_object(run_path / "score.json", score)
    return score


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--run", required=True)
    parser.add_argument("--model", default="")
    args = parser.parse_args()
    result = run_proof(load_object(Path(args.config)), Path(args.run), model=args.model)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
