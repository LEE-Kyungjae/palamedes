#!/usr/bin/env python3
"""Preregistered, origin-blinded real-project proof harness for Palamedes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from palamedes_chat import CodexCliChatProvider, _provider_json
from palamedes_observe import redact, utc_now


ROOT = Path(__file__).resolve().parent
DEFAULT_PORTFOLIO = ROOT / "experiments" / "proof-portfolio.json"
DEFAULT_RUN_ROOT = ROOT / "experiments" / "proof-runs"
TEXT_NAMES = {
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "ARCHITECTURE.md",
    "DESIGN.md",
    "package.json",
    "pyproject.toml",
    "Cargo.toml",
    "go.mod",
}
MISSION_FIELDS = (
    "situation",
    "interpretation",
    "mission",
    "rationale",
    "beneficiary",
    "success_signal",
    "next_probe",
    "consequential_choice",
)


def load_object(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def write_object(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def fingerprint(payload: Any) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_portfolio(portfolio: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    cases = portfolio.get("cases")
    protocol = portfolio.get("generation_protocol")
    rubric = portfolio.get("rubric")
    gate = portfolio.get("success_gate")
    if not isinstance(protocol, dict):
        errors.append("generation_protocol must be an object")
    else:
        if not protocol.get("same_model_required"):
            errors.append("same model is required")
        if not protocol.get("same_information_packet_required"):
            errors.append("same information packet is required")
        if protocol.get("compute_is_not_equal") is not True:
            errors.append("compute asymmetry must be declared")
        if protocol.get("compute_tradeoff_must_be_reported") is not True:
            errors.append("compute tradeoff reporting is required")
    if not isinstance(rubric, dict) or not rubric:
        errors.append("rubric must be a non-empty object")
    elif sum(
        int(item.get("weight", 0))
        for item in rubric.values()
        if isinstance(item, dict)
    ) != 100:
        errors.append("rubric weights must total 100")
    if not isinstance(gate, dict):
        errors.append("success_gate must be an object")
    if not isinstance(cases, list) or len(cases) < 3:
        errors.append("at least three cases are required")
    else:
        seen = set()
        for index, case in enumerate(cases):
            if not isinstance(case, dict):
                errors.append(f"cases[{index}] must be an object")
                continue
            case_id = str(case.get("case_id", "")).strip()
            if not case_id:
                errors.append(f"cases[{index}].case_id is required")
            elif case_id in seen:
                errors.append(f"duplicate case_id: {case_id}")
            seen.add(case_id)
            for field in ("repository", "question", "required_decision"):
                if not str(case.get(field, "")).strip():
                    errors.append(f"cases[{index}].{field} is required")
            if not isinstance(case.get("artifacts"), list) or not case["artifacts"]:
                errors.append(f"cases[{index}].artifacts must be non-empty")
    return errors


def repository_revision(repository: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _artifact_files(path: Path) -> List[Path]:
    if path.is_file():
        return [path]
    if not path.is_dir():
        return []
    candidates = []
    for candidate in sorted(path.rglob("*")):
        if not candidate.is_file():
            continue
        relative_parts = candidate.relative_to(path).parts
        if any(
            part in {".git", "node_modules", "build", "dist", ".gradle", ".dart_tool"}
            for part in relative_parts
        ):
            continue
        if candidate.name in TEXT_NAMES or candidate.suffix.lower() in {
            ".md",
            ".json",
            ".toml",
            ".yaml",
            ".yml",
        }:
            candidates.append(candidate)
        if len(candidates) >= 8:
            break
    return candidates


def freeze_case(
    case: Dict[str, Any],
    *,
    maximum_artifact_bytes: int,
) -> Dict[str, Any]:
    repository = Path(str(case["repository"])).expanduser()
    if not repository.is_absolute():
        repository = (ROOT / repository).resolve()
    if not repository.is_dir():
        raise ValueError(f"case repository does not exist: {repository}")
    artifacts = []
    declared_items = list(case["artifacts"])
    declared_budget = max(1, maximum_artifact_bytes // len(declared_items))
    for declared in declared_items:
        declared_path = Path(str(declared)).expanduser()
        source = (
            declared_path
            if declared_path.is_absolute()
            else repository / declared_path
        )
        files = _artifact_files(source)
        if not files:
            raise ValueError(
                f"{case['case_id']} artifact does not exist or has no bounded text: {declared}"
            )
        file_budget = max(1, declared_budget // len(files))
        for path in files:
            raw = path.read_bytes()
            excerpt_raw = raw[:file_budget]
            artifacts.append(
                {
                    "declared_path": str(declared),
                    "source_path": str(path),
                    "repository_relative_path": (
                        str(path.relative_to(repository))
                        if path.is_relative_to(repository)
                        else str(path)
                    ),
                    "size_bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "excerpt_truncated": len(excerpt_raw) < len(raw),
                    "excerpt": redact(
                        excerpt_raw.decode("utf-8", errors="replace")
                    ),
                }
            )
    included_bytes = sum(
        len(item["excerpt"].encode("utf-8")) for item in artifacts
    )
    packet = {
        "information_packet_version": "palamedes-proof-information/1",
        "case_id": case["case_id"],
        "frozen_at": utc_now(),
        "repository": str(repository),
        "repository_revision": repository_revision(repository),
        "question": case["question"],
        "required_decision": case["required_decision"],
        "artifact_byte_budget": maximum_artifact_bytes,
        "artifact_bytes_included": included_bytes,
        "declared_artifact_count": len(declared_items),
        "represented_declared_artifact_count": len(
            {item["declared_path"] for item in artifacts}
        ),
        "artifacts": artifacts,
    }
    packet["information_fingerprint"] = fingerprint(packet)
    return packet


def prepare_run(
    portfolio: Dict[str, Any],
    *,
    run_root: Path,
    run_id: str = "",
) -> Dict[str, Any]:
    errors = validate_portfolio(portfolio)
    if errors:
        raise ValueError("invalid proof portfolio: " + "; ".join(errors))
    actual_run_id = run_id or f"proof-{utc_now()[:10]}-{uuid.uuid4().hex[:8]}"
    target = run_root / actual_run_id
    if target.exists():
        raise ValueError(f"proof run already exists: {target}")
    maximum = int(portfolio["generation_protocol"]["maximum_artifact_bytes"])
    frozen_cases = []
    for case in portfolio["cases"]:
        packet = freeze_case(case, maximum_artifact_bytes=maximum)
        write_object(target / "cases" / case["case_id"] / "information.json", packet)
        frozen_cases.append(
            {
                "case_id": case["case_id"],
                "information_fingerprint": packet["information_fingerprint"],
                "repository_revision": packet["repository_revision"],
            }
        )
    manifest = {
        "proof_run_version": "palamedes-proof-run/1",
        "run_id": actual_run_id,
        "prepared_at": utc_now(),
        "status": "prepared",
        "portfolio": portfolio,
        "portfolio_fingerprint": fingerprint(portfolio),
        "frozen_cases": frozen_cases,
        "claim_status": "unproven",
    }
    manifest["manifest_fingerprint"] = fingerprint(manifest)
    write_object(target / "manifest.json", manifest)
    return {"run_id": actual_run_id, "run_path": str(target), "manifest": manifest}


def _mission_shape() -> str:
    return """{
  "situation": "...",
  "interpretation": "...",
  "mission": "...",
  "rationale": "...",
  "beneficiary": "...",
  "success_signal": "...",
  "falsifiers": ["..."],
  "non_goals": ["..."],
  "next_probe": "...",
  "consequential_choice": "continue|stop|pivot|position|sequence: ..."
}"""


def validate_mission(mission: Dict[str, Any]) -> None:
    for field in MISSION_FIELDS:
        if not isinstance(mission.get(field), str) or not mission[field].strip():
            raise ValueError(f"mission.{field} must be a non-empty string")
    for field in ("falsifiers", "non_goals"):
        value = mission.get(field)
        if not isinstance(value, list) or not value or not all(
            isinstance(item, str) and item.strip() for item in value
        ):
            raise ValueError(f"mission.{field} must be a non-empty string array")


class MeteredCodex:
    def __init__(self, model: str = "") -> None:
        self.model = model or "configured-default"
        self.calls: List[Dict[str, Any]] = []

    def call(self, *, system: str, prompt: str) -> Dict[str, Any]:
        provider = CodexCliChatProvider(model=self.model)
        output = _provider_json(provider, system=system, prompt=prompt)
        self.calls.append(
            {
                "call_index": len(self.calls) + 1,
                "model": provider.model,
                "token_usage": provider.last_usage or {},
                "completed_at": utc_now(),
            }
        )
        return output

    def usage(self) -> Dict[str, Any]:
        totals: Dict[str, int] = {}
        for call in self.calls:
            for key, value in call["token_usage"].items():
                if isinstance(value, int):
                    totals[key] = totals.get(key, 0) + value
        return {
            "call_count": len(self.calls),
            "calls": self.calls,
            "token_usage": totals,
        }


def generate_baseline(packet: Dict[str, Any], engine: MeteredCodex) -> Dict[str, Any]:
    prompt = f"""Choose the single most worthwhile mission for this project now.
Use only the frozen information packet. Do not inspect files or claim evidence
that is not present. Make a consequential choice before proposing tasks.
Return exactly one JSON object shaped as:
{_mission_shape()}

Frozen information packet:
{json.dumps(packet, ensure_ascii=False)}"""
    mission = engine.call(
        system=(
            "You are a strong general-purpose product strategist in a one-shot "
            "fresh session. Return only the requested JSON."
        ),
        prompt=prompt,
    )
    validate_mission(mission)
    return mission


def generate_palamedes(packet: Dict[str, Any], engine: MeteredCodex) -> Dict[str, Any]:
    shared = json.dumps(packet, ensure_ascii=False)
    interpreter = engine.call(
        system="You are the bounded Palamedes interpreter. Return only JSON.",
        prompt=f"""Independently identify observations, competing interpretations,
and missing evidence. Do not select a mission. Return:
{{"observations":["..."],"interpretations":["..."],"missing_evidence":["..."]}}

Frozen information packet:
{shared}""",
    )
    inventor = engine.call(
        system="You are the bounded Palamedes inventor. Return only JSON.",
        prompt=f"""Generate at least three materially different candidate missions.
Do not select among them. Return:
{{"candidate_missions":[{{"mission":"...","mechanism":"...","beneficiary":"...","falsifier":"...","next_probe":"..."}}]}}

Frozen information packet:
{shared}
Frozen interpreter artifact:
{json.dumps(interpreter, ensure_ascii=False)}""",
    )
    adversary = engine.call(
        system="You are the bounded Palamedes adversary. Return only JSON.",
        prompt=f"""Attack every candidate and their shared assumptions. State which
candidate would waste the most effort if wrong. Do not select a winner. Return:
{{"candidate_critiques":[{{"mission":"...","failure_mode":"...","hidden_harm":"...","disconfirming_evidence":"..."}}],"shared_assumptions":["..."]}}

Frozen information packet:
{shared}
Frozen interpreter artifact:
{json.dumps(interpreter, ensure_ascii=False)}
Frozen inventor artifact:
{json.dumps(inventor, ensure_ascii=False)}""",
    )
    mission = engine.call(
        system=(
            "You are the bounded Palamedes selector. Select only from the frozen "
            "candidates and return only JSON."
        ),
        prompt=f"""Select, defer, or reject based on evidence, reversibility,
information gain, beneficiary value, and adversarial survival. If selecting,
express the strongest surviving candidate as exactly:
{_mission_shape()}

Frozen information packet:
{shared}
Frozen interpreter artifact:
{json.dumps(interpreter, ensure_ascii=False)}
Frozen inventor artifact:
{json.dumps(inventor, ensure_ascii=False)}
Frozen adversary artifact:
{json.dumps(adversary, ensure_ascii=False)}""",
    )
    validate_mission(mission)
    return {
        "mission": mission,
        "role_artifacts": {
            "interpreter": interpreter,
            "inventor": inventor,
            "adversary": adversary,
        },
    }


def generate_condition(
    run_path: Path,
    *,
    condition: str,
    model: str = "",
    case_id: str = "",
) -> Dict[str, Any]:
    manifest = load_object(run_path / "manifest.json")
    expected_calls = {"baseline": 1, "palamedes": 4}
    if condition not in expected_calls:
        raise ValueError("condition must be baseline or palamedes")
    selected = [
        item
        for item in manifest["frozen_cases"]
        if not case_id or item["case_id"] == case_id
    ]
    if not selected:
        raise ValueError(f"unknown case_id: {case_id}")
    results = []
    for item in selected:
        target = run_path / "cases" / item["case_id"]
        output_path = target / f"{condition}.json"
        if output_path.exists():
            raise ValueError(f"condition output already exists: {output_path}")
        packet = load_object(target / "information.json")
        if packet["information_fingerprint"] != item["information_fingerprint"]:
            raise ValueError(f"information fingerprint mismatch: {item['case_id']}")
        engine = MeteredCodex(model=model)
        if condition == "baseline":
            mission = generate_baseline(packet, engine)
            role_artifacts: Dict[str, Any] = {}
        else:
            generated = generate_palamedes(packet, engine)
            mission = generated["mission"]
            role_artifacts = generated["role_artifacts"]
        usage = engine.usage()
        if usage["call_count"] != expected_calls[condition]:
            raise ValueError(f"{condition} call count violated preregistration")
        record = {
            "condition_output_version": "palamedes-proof-condition/1",
            "case_id": item["case_id"],
            "condition": condition,
            "generated_at": utc_now(),
            "provider": "codex",
            "model": engine.model,
            "information_fingerprint": packet["information_fingerprint"],
            "mission": mission,
            "role_artifacts": role_artifacts,
            "usage": usage,
        }
        record["output_fingerprint"] = fingerprint(record)
        write_object(output_path, record)
        results.append(
            {
                "case_id": item["case_id"],
                "output_path": str(output_path),
                "output_fingerprint": record["output_fingerprint"],
                "usage": usage,
            }
        )
    return {"condition": condition, "results": results}


def blind_labels(case_id: str, seed: str) -> Tuple[str, str]:
    digest = hashlib.sha256(f"{seed}:{case_id}".encode("utf-8")).digest()
    return ("A", "B") if digest[0] % 2 == 0 else ("B", "A")


def prepare_blind_packet(run_path: Path, *, seed: str) -> Dict[str, Any]:
    manifest = load_object(run_path / "manifest.json")
    packet_cases = []
    key_cases = []
    for item in manifest["frozen_cases"]:
        root = run_path / "cases" / item["case_id"]
        baseline = load_object(root / "baseline.json")
        palamedes = load_object(root / "palamedes.json")
        baseline_label, palamedes_label = blind_labels(item["case_id"], seed)
        reports = {
            baseline_label: baseline["mission"],
            palamedes_label: palamedes["mission"],
        }
        information = load_object(root / "information.json")
        packet_cases.append(
            {
                "case_id": item["case_id"],
                "question": information["question"],
                "required_decision": information["required_decision"],
                "information_fingerprint": information["information_fingerprint"],
                "missions": {"A": reports["A"], "B": reports["B"]},
            }
        )
        key_cases.append(
            {
                "case_id": item["case_id"],
                "labels": {
                    baseline_label: "baseline",
                    palamedes_label: "palamedes",
                },
            }
        )
    blind = {
        "blind_packet_version": "palamedes-proof-blind/1",
        "run_id": manifest["run_id"],
        "rubric": manifest["portfolio"]["rubric"],
        "cases": packet_cases,
        "origin_visible": False,
    }
    key = {
        "blind_key_version": "palamedes-proof-key/1",
        "run_id": manifest["run_id"],
        "seed_sha256": hashlib.sha256(seed.encode("utf-8")).hexdigest(),
        "success_gate": manifest["portfolio"]["success_gate"],
        "cases": key_cases,
    }
    write_object(run_path / "blind" / "packet.json", blind)
    write_object(run_path / "private" / "answer-key.json", key)
    return {"packet": blind, "key_path": str(run_path / "private" / "answer-key.json")}


def _review_shape(rubric: Dict[str, Any]) -> str:
    scores = ",".join(f'"{name}":1' for name in rubric)
    return (
        '{"scores":{"A":{' + scores + '},"B":{' + scores
        + '}},"preferred":"A|B|tie","rationale":"...",'
        '"decision_difference":"...","confidence":0}'
    )


def review_blind_packet(
    run_path: Path,
    *,
    reviewer_id: str,
    model: str = "",
) -> Dict[str, Any]:
    packet = load_object(run_path / "blind" / "packet.json")
    results = []
    for case in packet["cases"]:
        engine = MeteredCodex(model=model)
        review = engine.call(
            system=(
                "You are an origin-blinded evaluator. Do not infer authorship. "
                "Longer prose, novelty, and agreement with historical choices are "
                "not scoring dimensions. Return only JSON."
            ),
            prompt=f"""Score A and B from 1 to 5 on every rubric dimension.
Prefer only a mission whose reasoning would improve the required decision.
Return exactly:
{_review_shape(packet['rubric'])}

Rubric:
{json.dumps(packet['rubric'], ensure_ascii=False)}
Blind case:
{json.dumps(case, ensure_ascii=False)}""",
        )
        for label in ("A", "B"):
            scores = review.get("scores", {}).get(label)
            if not isinstance(scores, dict):
                raise ValueError(f"review scores missing {label}")
            for dimension in packet["rubric"]:
                value = scores.get(dimension)
                if not isinstance(value, int) or not 1 <= value <= 5:
                    raise ValueError(
                        f"review {label}.{dimension} must be an integer 1-5"
                    )
        if review.get("preferred") not in {"A", "B", "tie"}:
            raise ValueError("review.preferred must be A, B, or tie")
        results.append(
            {
                "case_id": case["case_id"],
                "reviewer_id": reviewer_id,
                "origin_visible": False,
                "review": review,
                "usage": engine.usage(),
            }
        )
    record = {
        "blind_review_version": "palamedes-proof-review/1",
        "run_id": packet["run_id"],
        "reviewer_id": reviewer_id,
        "reviewed_at": utc_now(),
        "reviews": results,
    }
    record["review_fingerprint"] = fingerprint(record)
    write_object(run_path / "reviews" / f"{reviewer_id}.json", record)
    return record


def _weighted(scores: Dict[str, Any], rubric: Dict[str, Any]) -> float:
    return round(
        sum(float(scores[name]) * int(rubric[name]["weight"]) for name in rubric)
        / 100,
        3,
    )


def score_run(run_path: Path) -> Dict[str, Any]:
    packet = load_object(run_path / "blind" / "packet.json")
    key = load_object(run_path / "private" / "answer-key.json")
    review_paths = sorted((run_path / "reviews").glob("*.json"))
    keys = {item["case_id"]: item["labels"] for item in key["cases"]}
    votes: Dict[str, List[Dict[str, Any]]] = {
        case["case_id"]: [] for case in packet["cases"]
    }
    for path in review_paths:
        record = load_object(path)
        for item in record.get("reviews", []):
            review = item["review"]
            preferred = review["preferred"]
            system = "tie" if preferred == "tie" else keys[item["case_id"]][preferred]
            votes[item["case_id"]].append(
                {
                    "reviewer_id": item["reviewer_id"],
                    "preferred_label": preferred,
                    "preferred_system": system,
                    "weighted_scores": {
                        label: _weighted(
                            review["scores"][label], packet["rubric"]
                        )
                        for label in ("A", "B")
                    },
                    "rationale": review["rationale"],
                    "decision_difference": review["decision_difference"],
                }
            )
    case_results = []
    for case_id, case_votes in votes.items():
        palamedes_votes = sum(
            item["preferred_system"] == "palamedes" for item in case_votes
        )
        baseline_votes = sum(
            item["preferred_system"] == "baseline" for item in case_votes
        )
        winner = "tie"
        if palamedes_votes > baseline_votes:
            winner = "palamedes"
        elif baseline_votes > palamedes_votes:
            winner = "baseline"
        outcome_path = run_path / "cases" / case_id / "outcome.json"
        outcome = load_object(outcome_path) if outcome_path.exists() else None
        case_results.append(
            {
                "case_id": case_id,
                "review_count": len(case_votes),
                "winner": winner,
                "votes": case_votes,
                "outcome": outcome,
            }
        )
    gate = key["success_gate"]
    quality_gate = (
        len(case_results) >= int(gate["minimum_cases"])
        and all(
            item["review_count"] >= int(gate["minimum_blinded_reviews_per_case"])
            for item in case_results
        )
        and sum(item["winner"] == "palamedes" for item in case_results)
        >= int(gate["palamedes_preferred_cases"])
    )
    attributable = sum(
        bool(item["outcome"] and item["outcome"].get("attributable_decision"))
        for item in case_results
    )
    labor = sum(
        bool(item["outcome"] and item["outcome"].get("labor_retired"))
        for item in case_results
    )
    outcome_gate = (
        attributable >= int(gate["minimum_attributable_outcomes"])
        and labor >= int(gate["minimum_labor_retirement_cases"])
    )
    result = {
        "proof_score_version": "palamedes-proof-score/1",
        "run_id": packet["run_id"],
        "scored_at": utc_now(),
        "mission_quality_gate_passed": quality_gate,
        "outcome_gate_passed": outcome_gate,
        "claim_demonstrated": quality_gate and outcome_gate,
        "attributable_outcomes": attributable,
        "labor_retirement_cases": labor,
        "case_results": case_results,
        "claim_boundary": (
            "Three-case mission preference plus at least one attributable decision "
            "and upstream labor retirement; not general startup-success proof."
        ),
    }
    write_object(run_path / "score.json", result)
    return result


def record_outcome(
    run_path: Path,
    *,
    case_id: str,
    selected_system: str,
    observed_choice: str,
    attributable_decision: bool,
    owner_seconds_without: int,
    owner_seconds_with: int,
    evidence: str,
) -> Dict[str, Any]:
    if selected_system not in {"baseline", "palamedes", "neither"}:
        raise ValueError("selected_system must be baseline, palamedes, or neither")
    if owner_seconds_with > owner_seconds_without:
        labor_retired = False
    else:
        labor_retired = owner_seconds_with < owner_seconds_without
    outcome = {
        "proof_outcome_version": "palamedes-proof-outcome/1",
        "case_id": case_id,
        "recorded_at": utc_now(),
        "selected_system": selected_system,
        "observed_choice": observed_choice,
        "attributable_decision": attributable_decision,
        "owner_seconds_without": owner_seconds_without,
        "owner_seconds_with": owner_seconds_with,
        "retired_seconds": max(0, owner_seconds_without - owner_seconds_with),
        "labor_retired": labor_retired,
        "evidence": evidence,
    }
    path = run_path / "cases" / case_id / "outcome.json"
    if path.exists():
        raise ValueError(f"outcome is append-once and already exists: {path}")
    write_object(path, outcome)
    return outcome


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    command = sub.add_parser("prepare")
    command.add_argument("--portfolio", default=str(DEFAULT_PORTFOLIO))
    command.add_argument("--run-root", default=str(DEFAULT_RUN_ROOT))
    command.add_argument("--run-id", default="")

    command = sub.add_parser("generate")
    command.add_argument("--run", required=True)
    command.add_argument("--condition", choices=["baseline", "palamedes"], required=True)
    command.add_argument("--case-id", default="")
    command.add_argument("--model", default="")

    command = sub.add_parser("blind")
    command.add_argument("--run", required=True)
    command.add_argument("--seed", required=True)

    command = sub.add_parser("review")
    command.add_argument("--run", required=True)
    command.add_argument("--reviewer-id", required=True)
    command.add_argument("--model", default="")

    command = sub.add_parser("score")
    command.add_argument("--run", required=True)

    command = sub.add_parser("outcome")
    command.add_argument("--run", required=True)
    command.add_argument("--case-id", required=True)
    command.add_argument(
        "--selected-system", choices=["baseline", "palamedes", "neither"], required=True
    )
    command.add_argument("--observed-choice", required=True)
    command.add_argument("--attributable-decision", action="store_true")
    command.add_argument("--owner-seconds-without", type=int, required=True)
    command.add_argument("--owner-seconds-with", type=int, required=True)
    command.add_argument("--evidence", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "prepare":
        result = prepare_run(
            load_object(Path(args.portfolio)),
            run_root=Path(args.run_root),
            run_id=args.run_id,
        )
    elif args.command == "generate":
        result = generate_condition(
            Path(args.run),
            condition=args.condition,
            model=args.model,
            case_id=args.case_id,
        )
    elif args.command == "blind":
        result = prepare_blind_packet(Path(args.run), seed=args.seed)
    elif args.command == "review":
        result = review_blind_packet(
            Path(args.run), reviewer_id=args.reviewer_id, model=args.model
        )
    elif args.command == "score":
        result = score_run(Path(args.run))
    else:
        result = record_outcome(
            Path(args.run),
            case_id=args.case_id,
            selected_system=args.selected_system,
            observed_choice=args.observed_choice,
            attributable_decision=args.attributable_decision,
            owner_seconds_without=args.owner_seconds_without,
            owner_seconds_with=args.owner_seconds_with,
            evidence=args.evidence,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
