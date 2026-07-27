#!/usr/bin/env python3
"""Blinded origination benchmarks for Palamedes product vision."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from palamedes_observe import utc_now
from palamedes_vision import VisionStore, fingerprint, run_vision_genesis
from palamedes_vision_scout import VisionScoutStore, run_vision_scout


@dataclass(frozen=True)
class VisionBenchmarkCase:
    case_id: str
    generator_context: str
    hidden_human_reference: str
    hidden_anchor_terms: List[str]
    case_origin: str = "calibration_builtin"
    case_fingerprint: str = ""
    case_author_id: str = ""
    evaluation_trial_count: int = 0


BUILTIN_CASES = (
    VisionBenchmarkCase(
        case_id="service-wide-hidden-meaning",
        generator_context=(
            "A service contains several small games, user profiles, ordinary activity "
            "records, and the ability to produce images, voice, and video. Originate a "
            "durable product world that increases emotional memory and return behavior."
        ),
        hidden_human_reference=(
            "Turn selected service behaviors into hidden discoveries. Reward discoveries "
            "with profile avatars and preserve them in a browsable collection. Give each "
            "artifact an appropriate explanation drawing carefully from scripture, Greek "
            "and Roman mythology, Buddhism, historical figures, Shakespeare, and other "
            "cultural sources, with image, voice, and video production support."
        ),
        hidden_anchor_terms=[
            "collection", "hidden discovery", "avatar reward", "scripture",
            "Greek and Roman mythology", "Buddhism", "Shakespeare",
        ],
    ),
    VisionBenchmarkCase(
        case_id="cross-rule-puzzle-world",
        generator_context=(
            "A product has a competent falling-block puzzle with deterministic rules and "
            "multiplayer infrastructure. Originate a substantially new repeatable play "
            "experience rather than polishing speed, graphics, ranking, or achievements."
        ),
        hidden_human_reference=(
            "A strong human leap would combine the core causal rules of two distinct puzzle "
            "genres so that success in one system creates pressure or opportunity in the "
            "other, producing a coherent competitive game rather than a menu of modes."
        ),
        hidden_anchor_terms=["Puyo", "rule fusion", "two puzzle genres", "cross-system attack"],
    ),
    VisionBenchmarkCase(
        case_id="charged-community-economy",
        generator_context=(
            "A social service has persistent groups, profiles, direct interaction, and a "
            "small virtual-currency economy. Originate a durable social product world "
            "that people care about enough to revisit and pay for. Do not assume that "
            "engagement must come only from pleasant emotion, and do not authorize harm."
        ),
        hidden_human_reference=(
            "A human product leap might deliberately connect group belonging with bounded "
            "interpersonal conflict: guild-like bonds create loyalty, while a very low-cost "
            "negative postcard lets a user visibly express anger toward another user. The "
            "charged relationship itself can support a small economy, provided harassment, "
            "pile-ons, coercive spending, minors, blocking, cooldowns, and repair paths are "
            "designed as first-class constraints rather than added after monetization."
        ),
        hidden_anchor_terms=[
            "negative postcard", "guild-like bonds", "express anger",
            "pile-ons", "coercive spending", "repair paths",
        ],
    ),
)


class VisionBenchmarkStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def save(self, record: Dict[str, Any]) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"{record['vision_benchmark_id']}.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return path

    def save_scout_benchmark(self, record: Dict[str, Any]) -> Path:
        root = self.root / "scout-benchmarks"
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{record['vision_scout_benchmark_id']}.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return path

    def scout_promotion(self, vision_scout_id: str) -> Optional[Dict[str, Any]]:
        root = self.root / "scout-promotions"
        if not root.is_dir():
            return None
        for path in root.glob("vision-scout-promotion-*.json"):
            try:
                row = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if row.get("vision_scout_id") == vision_scout_id:
                return row
        return None

    def save_scout_promotion(self, record: Dict[str, Any]) -> Path:
        root = self.root / "scout-promotions"
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{record['vision_scout_promotion_id']}.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return path

    def scout_attempts(self) -> List[Dict[str, Any]]:
        path = self.root / "scout-attempts.jsonl"
        if not path.is_file():
            return []
        rows = []
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
        return rows

    def reserve_scout_attempt(self, case: VisionBenchmarkCase) -> Dict[str, Any]:
        attempt_key = fingerprint(
            {"case_id": case.case_id, "context": case.generator_context}
        )
        if any(
            row.get("attempt_key") == attempt_key for row in self.scout_attempts()
        ):
            raise ValueError("vision scout trial budget exhausted: 1/1")
        scout_root = self.root / "scout-benchmarks"
        for path in scout_root.glob("vision-scout-benchmark-*.json"):
            try:
                prior = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if (
                prior.get("case_id") == case.case_id
                and prior.get("generator_context_fingerprint")
                == fingerprint(case.generator_context)
            ):
                raise ValueError("vision scout trial budget exhausted: 1/1")
        attempt = {
            "vision_scout_attempt_version": "palamedes-vision-scout-attempt/1",
            "attempt_id": f"vision-scout-attempt-{attempt_key[:12]}",
            "attempt_key": attempt_key,
            "case_id": case.case_id,
            "generator_context_fingerprint": fingerprint(case.generator_context),
            "status": "started",
            "started_at": utc_now(),
        }
        path = self.root / "scout-attempts.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(attempt, ensure_ascii=False, sort_keys=True) + "\n")
        return attempt

    def complete_scout_attempt(
        self, attempt: Dict[str, Any], benchmark_id: str
    ) -> None:
        completed = dict(attempt)
        completed.update(
            {
                "status": "completed",
                "vision_scout_benchmark_id": benchmark_id,
                "completed_at": utc_now(),
            }
        )
        with (self.root / "scout-attempts.jsonl").open(
            "a", encoding="utf-8"
        ) as handle:
            handle.write(json.dumps(completed, ensure_ascii=False, sort_keys=True) + "\n")

    def save_suite(self, record: Dict[str, Any]) -> Path:
        suite_root = self.root / "suites"
        suite_root.mkdir(parents=True, exist_ok=True)
        path = suite_root / f"{record['suite_id']}.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return path

    def save_agenda_ablation(self, record: Dict[str, Any]) -> Path:
        root = self.root / "agenda-ablations"
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{record['vision_agenda_ablation_id']}.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return path

    def agenda_ablation_attempts(self) -> List[Dict[str, Any]]:
        path = self.root / "agenda-ablation-attempts.jsonl"
        if not path.is_file():
            return []
        latest: Dict[str, Dict[str, Any]] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict) and isinstance(row.get("attempt_id"), str):
                latest[row["attempt_id"]] = row
        return list(latest.values())

    def reserve_agenda_ablation_attempt(
        self,
        *,
        case: VisionBenchmarkCase,
        challenger_condition: str,
        comparator_condition: str,
    ) -> Dict[str, Any]:
        attempt_key = fingerprint(
            {
                "case_id": case.case_id,
                "context": case.generator_context,
                "condition_pair": sorted(
                    [challenger_condition, comparator_condition]
                ),
            }
        )
        prior = [
            row
            for row in self.agenda_ablation_attempts()
            if row.get("attempt_key") == attempt_key
        ]
        if prior:
            raise ValueError(
                "agenda ablation trial budget exhausted: 1/1 for this condition pair"
            )
        attempt = {
            "vision_agenda_ablation_attempt_version": (
                "palamedes-vision-agenda-ablation-attempt/1"
            ),
            "attempt_id": f"vision-agenda-ablation-attempt-{attempt_key[:12]}",
            "attempt_key": attempt_key,
            "case_id": case.case_id,
            "case_origin": case.case_origin,
            "generator_context_fingerprint": fingerprint(case.generator_context),
            "challenger_condition": challenger_condition,
            "comparator_condition": comparator_condition,
            "status": "started",
            "started_at": utc_now(),
        }
        path = self.root / "agenda-ablation-attempts.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(attempt, ensure_ascii=False, sort_keys=True) + "\n")
        return attempt

    def finish_agenda_ablation_attempt(
        self,
        attempt: Dict[str, Any],
        *,
        status: str,
        ablation_id: str = "",
        error: str = "",
        provider_usage: Optional[Dict[str, Any]] = None,
    ) -> None:
        if status not in {"completed", "failed"}:
            raise ValueError("agenda ablation attempt status must be completed or failed")
        finished = dict(attempt)
        finished.update({"status": status, "finished_at": utc_now()})
        if ablation_id:
            finished["vision_agenda_ablation_id"] = ablation_id
        if error:
            finished["error"] = error
        if isinstance(provider_usage, dict):
            finished["provider_usage"] = provider_usage
        path = self.root / "agenda-ablation-attempts.jsonl"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(finished, ensure_ascii=False, sort_keys=True) + "\n")

    def import_holdout_case(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(payload, dict):
            raise ValueError("holdout case must be an object")
        case_id = str(payload.get("case_id", "")).strip()
        if not re.fullmatch(r"holdout-[a-z0-9][a-z0-9-]{2,63}", case_id):
            raise ValueError("holdout case_id must match holdout-[a-z0-9-]")
        author_id = str(payload.get("author_id", "")).strip()
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", author_id):
            raise ValueError("holdout author_id must be a safe non-secret identifier")
        if payload.get("author_kind") != "human":
            raise ValueError("holdout author_kind must be human")
        if payload.get("author_relationship") != "independent":
            raise ValueError("holdout author_relationship must be independent")
        evaluation_trial_count = payload.get("evaluation_trial_count")
        if (
            not isinstance(evaluation_trial_count, int)
            or isinstance(evaluation_trial_count, bool)
            or not 1 <= evaluation_trial_count <= 3
        ):
            raise ValueError("holdout evaluation_trial_count must be an integer 1-3")
        generator_context = str(payload.get("generator_context", "")).strip()
        hidden_reference = str(payload.get("hidden_human_reference", "")).strip()
        if len(generator_context) < 120 or len(hidden_reference) < 120:
            raise ValueError("holdout context and hidden reference require 120+ characters")
        anchors = payload.get("hidden_anchor_terms")
        if (
            not isinstance(anchors, list)
            or len(anchors) < 2
            or not all(isinstance(item, str) and item.strip() for item in anchors)
        ):
            raise ValueError("holdout requires at least two hidden anchor terms")
        leaked = [
            item.strip()
            for item in anchors
            if item.strip().lower() in generator_context.lower()
        ]
        if leaked:
            raise ValueError(f"holdout generator context leaks hidden anchors: {leaked}")
        normalized = {
            "vision_benchmark_holdout_version": "palamedes-vision-benchmark-holdout/1",
            "case_id": case_id,
            "case_origin": "external_human_holdout",
            "author_id": author_id,
            "author_kind": "human",
            "author_relationship": "independent",
            "evaluation_trial_count": evaluation_trial_count,
            "generator_context": generator_context,
            "hidden_human_reference": hidden_reference,
            "hidden_anchor_terms": [item.strip() for item in anchors],
            "custody": {
                "stored_under_local_state": True,
                "source_repository_status": "unverified",
                "generator_reference_access": False,
                "author_independence_identity_verified": False,
            },
            "imported_at": utc_now(),
        }
        normalized["case_fingerprint"] = fingerprint(normalized)
        root = self.root / "holdout-cases"
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{case_id}.json"
        if path.exists():
            raise ValueError(f"holdout case already exists: {case_id}")
        path.write_text(
            json.dumps(normalized, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return normalized

    def load_holdout_case(self, case_id: str) -> VisionBenchmarkCase:
        if not re.fullmatch(r"holdout-[a-z0-9][a-z0-9-]{2,63}", case_id):
            raise ValueError("invalid holdout case ID")
        path = self.root / "holdout-cases" / f"{case_id}.json"
        if not path.is_file():
            raise ValueError(f"holdout case not found: {case_id}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        expected = payload.pop("case_fingerprint", "")
        if fingerprint(payload) != expected:
            raise ValueError("holdout case fingerprint mismatch")
        return VisionBenchmarkCase(
            case_id=payload["case_id"],
            generator_context=payload["generator_context"],
            hidden_human_reference=payload["hidden_human_reference"],
            hidden_anchor_terms=payload["hidden_anchor_terms"],
            case_origin=payload["case_origin"],
            case_fingerprint=expected,
            case_author_id=payload["author_id"],
            evaluation_trial_count=payload["evaluation_trial_count"],
        )

    def holdout_cases(self) -> List[Dict[str, Any]]:
        root = self.root / "holdout-cases"
        rows = []
        if not root.is_dir():
            return rows
        for path in sorted(root.glob("holdout-*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict):
                expected = payload.get("case_fingerprint", "")
                unsigned = dict(payload)
                unsigned.pop("case_fingerprint", None)
                if not expected or fingerprint(unsigned) != expected:
                    raise ValueError(
                        f"holdout case fingerprint mismatch: {path.name}"
                    )
                rows.append(payload)
        return rows

    def holdout_attempts(self) -> List[Dict[str, Any]]:
        path = self.root / "holdout-attempts.jsonl"
        if not path.is_file():
            return []
        latest: Dict[str, Dict[str, Any]] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict) and isinstance(row.get("attempt_id"), str):
                latest[row["attempt_id"]] = row
        return list(latest.values())

    def reserve_holdout_attempt(self, case: VisionBenchmarkCase) -> Dict[str, Any]:
        attempts = [
            row
            for row in self.holdout_attempts()
            if row.get("case_fingerprint") == case.case_fingerprint
        ]
        if len(attempts) >= case.evaluation_trial_count:
            raise ValueError(
                f"holdout trial budget exhausted: {len(attempts)}/"
                f"{case.evaluation_trial_count}"
            )
        trial_number = len(attempts) + 1
        attempt = {
            "holdout_attempt_version": "palamedes-vision-holdout-attempt/1",
            "attempt_id": f"holdout-attempt-{fingerprint({'case': case.case_fingerprint, 'trial': trial_number})[:12]}",
            "case_id": case.case_id,
            "case_fingerprint": case.case_fingerprint,
            "trial_number": trial_number,
            "trial_id": f"{case.case_id}:preregistered:{trial_number}",
            "status": "started",
            "started_at": utc_now(),
        }
        path = self.root / "holdout-attempts.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(attempt, ensure_ascii=False, sort_keys=True) + "\n")
        return attempt

    def complete_holdout_attempt(
        self, attempt: Dict[str, Any], benchmark_id: str
    ) -> None:
        completed = dict(attempt)
        completed.update(
            {
                "status": "completed",
                "vision_benchmark_id": benchmark_id,
                "completed_at": utc_now(),
            }
        )
        path = self.root / "holdout-attempts.jsonl"
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(completed, ensure_ascii=False, sort_keys=True) + "\n")

    def save_human_review(
        self, packet: Dict[str, Any], answer_key: Dict[str, Any]
    ) -> Dict[str, Path]:
        packet_root = self.root / "human-review"
        key_root = self.root / "answer-keys"
        packet_root.mkdir(parents=True, exist_ok=True)
        key_root.mkdir(parents=True, exist_ok=True)
        packet_path = packet_root / f"{packet['vision_review_packet_id']}.json"
        key_path = key_root / f"{packet['vision_review_packet_id']}.json"
        packet_path.write_text(
            json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        key_path.write_text(
            json.dumps(answer_key, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return {"packet_path": packet_path, "answer_key_path": key_path}

    def submit_human_review(
        self, packet_id: str, response: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not re.fullmatch(r"vision-review-[a-f0-9]{12}", packet_id):
            raise ValueError("invalid human vision review packet ID")
        packet_path = self.root / "human-review" / f"{packet_id}.json"
        key_path = self.root / "answer-keys" / f"{packet_id}.json"
        if not packet_path.exists() or not key_path.exists():
            raise ValueError("unknown human vision review packet")
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        key = json.loads(key_path.read_text(encoding="utf-8"))
        packet_fingerprint = fingerprint(packet)
        if response.get("packet_fingerprint") != packet_fingerprint:
            raise ValueError("human review packet fingerprint mismatch")
        reviewer_id = str(response.get("reviewer_id", "")).strip()
        reviewer_kind = response.get("reviewer_kind")
        reviewer_relationship = response.get("reviewer_relationship")
        preferred = response.get("preferred")
        rationale = str(response.get("rationale", "")).strip()
        confidence = response.get("confidence")
        if not reviewer_id or preferred not in {"A", "B", "peer", "neither"}:
            raise ValueError("human review requires reviewer_id and valid preferred")
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,80}", reviewer_id):
            raise ValueError("human review reviewer_id contains unsafe characters")
        if reviewer_kind not in {"human", "model"}:
            raise ValueError("vision review requires reviewer_kind human or model")
        if reviewer_relationship not in {"independent", "team", "author", "unknown"}:
            raise ValueError(
                "vision review requires reviewer_relationship independent, team, author, or unknown"
            )
        case_author_id = str(key.get("case_author_id", "")).strip()
        if case_author_id and reviewer_id == case_author_id:
            raise ValueError("holdout case author cannot review their own case")
        if not rationale:
            raise ValueError("human review requires rationale")
        if not isinstance(confidence, int) or isinstance(confidence, bool) or not 0 <= confidence <= 100:
            raise ValueError("human review confidence must be integer 0-100")
        axes = packet["axes"]
        scores = {}
        for label in ("A", "B"):
            value = response.get(f"scores_{label}")
            if not isinstance(value, dict) or set(value) != set(axes):
                raise ValueError(f"human review scores_{label} must cover every axis")
            for axis, score in value.items():
                if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
                    raise ValueError(f"human review score {label}.{axis} must be integer 0-100")
            scores[label] = value
        response_identity = fingerprint(
            {"packet_id": packet_id, "reviewer_id": reviewer_id, "response": response}
        )
        response_id = f"vision-human-review-{response_identity[:12]}"
        response_root = self.root / "human-responses"
        resolved_root = self.root / "resolved-human-reviews"
        response_root.mkdir(parents=True, exist_ok=True)
        resolved_root.mkdir(parents=True, exist_ok=True)
        duplicate = list(response_root.glob(f"{packet_id}--{reviewer_id}--*.json"))
        if duplicate:
            raise ValueError("reviewer already submitted this packet")
        recorded = {
            "vision_human_response_version": "palamedes-vision-human-response/1",
            "vision_human_response_id": response_id,
            "vision_review_packet_id": packet_id,
            "packet_fingerprint": packet_fingerprint,
            "case_id": packet.get("case_id", ""),
            "case_origin": packet.get("case_origin", "calibration_builtin"),
            "case_fingerprint": packet.get("case_fingerprint", ""),
            "trial_id": packet.get("trial_id", ""),
            "evaluation_artifact": packet.get("evaluation_artifact", "legacy_vision_brief"),
            "source_artifact_type": packet.get("source_artifact_type", "vision_genesis"),
            "source_artifact_id": packet.get("source_artifact_id", ""),
            "reviewer_id": reviewer_id,
            "reviewer_kind": reviewer_kind,
            "reviewer_relationship": reviewer_relationship,
            "reviewer_is_case_author": bool(
                case_author_id and reviewer_id == case_author_id
            ),
            "preferred": preferred,
            "scores_A": scores["A"],
            "scores_B": scores["B"],
            "rationale": rationale,
            "confidence": confidence,
            "submitted_at": utc_now(),
        }
        response_path = response_root / f"{packet_id}--{reviewer_id}--{response_id}.json"
        response_path.write_text(
            json.dumps(recorded, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        generated_label = key["generated_label"]
        reference_label = key["human_reference_label"]
        resolution = (
            "generated_preferred"
            if preferred == generated_label
            else "reference_preferred"
            if preferred == reference_label
            else preferred
        )
        resolved = {
            "vision_human_review_resolution_version": "palamedes-vision-human-review-resolution/1",
            "vision_human_response_id": response_id,
            "vision_review_packet_id": packet_id,
            "packet_fingerprint": packet_fingerprint,
            "case_id": packet.get("case_id", ""),
            "case_origin": packet.get("case_origin", "calibration_builtin"),
            "case_fingerprint": packet.get("case_fingerprint", ""),
            "trial_id": packet.get("trial_id", ""),
            "evaluation_artifact": packet.get("evaluation_artifact", "legacy_vision_brief"),
            "source_artifact_type": packet.get("source_artifact_type", "vision_genesis"),
            "source_artifact_id": packet.get("source_artifact_id", ""),
            "reviewer_id": reviewer_id,
            "reviewer_kind": reviewer_kind,
            "reviewer_relationship": reviewer_relationship,
            "reviewer_is_case_author": bool(
                case_author_id and reviewer_id == case_author_id
            ),
            "resolution": resolution,
            "generated_scores": scores[generated_label],
            "human_reference_scores": scores[reference_label],
            "score_deltas": {
                axis: scores[generated_label][axis] - scores[reference_label][axis]
                for axis in axes
            },
            "confidence": confidence,
            "resolved_at": utc_now(),
        }
        resolved_path = resolved_root / f"{packet_id}--{reviewer_id}--{response_id}.json"
        resolved_path.write_text(
            json.dumps(resolved, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return resolved

    def scout_promotion_gate(
        self,
        vision_scout_id: str,
        *,
        minimum_independent_reviewers: int = 2,
        minimum_confidence: int = 60,
        probe_outcome: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not re.fullmatch(r"vision-scout-[a-f0-9]{12}", vision_scout_id):
            raise ValueError("invalid vision scout ID")
        qualifying = [
            row
            for row in self._resolved_human_reviews()
            if row.get("source_artifact_type") == "vision_scout"
            and row.get("source_artifact_id") == vision_scout_id
            and row.get("reviewer_kind") == "human"
            and row.get("reviewer_relationship") == "independent"
            and row.get("reviewer_is_case_author") is False
            and isinstance(row.get("confidence"), int)
            and not isinstance(row.get("confidence"), bool)
            and row["confidence"] >= minimum_confidence
        ]
        reviewers = {
            str(row.get("reviewer_id", "")).strip()
            for row in qualifying
            if str(row.get("reviewer_id", "")).strip()
        }
        unfavorable = [
            row
            for row in qualifying
            if row.get("resolution") not in {"generated_preferred", "peer"}
        ]
        required_axes = {
            "origination",
            "conceptual_distance",
            "affective_depth",
            "mechanism_fusion",
            "world_coherence",
            "three_year_generativity",
            "human_approval_value",
        }
        axis_deltas = {
            axis: [
                row.get("score_deltas", {}).get(axis)
                for row in qualifying
                if isinstance(row.get("score_deltas", {}).get(axis), int)
            ]
            for axis in required_axes
        }
        missing_axes = sorted(
            axis for axis, values in axis_deltas.items() if len(values) != len(qualifying)
        )
        mean_deltas = {
            axis: sum(values) / len(values)
            for axis, values in sorted(axis_deltas.items())
            if values
        }
        human_path_passed = (
            len(reviewers) >= minimum_independent_reviewers
            and not unfavorable
            and not missing_axes
            and all(delta >= -5 for delta in mean_deltas.values())
        )
        project_review_root = self.root.parent / "vision-scouts" / "project-review-resolutions"
        project_rows = []
        if project_review_root.is_dir():
            for path in project_review_root.glob("vision-scout-review-*.json"):
                try:
                    row = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                if (
                    isinstance(row, dict)
                    and row.get("vision_scout_id") == vision_scout_id
                    and row.get("reviewer_kind") == "human"
                    and row.get("reviewer_relationship") == "independent"
                    and isinstance(row.get("confidence"), int)
                    and not isinstance(row.get("confidence"), bool)
                    and row["confidence"] >= minimum_confidence
                ):
                    project_rows.append(row)
        project_reviewers = {
            str(row.get("reviewer_id", "")).strip()
            for row in project_rows
            if str(row.get("reviewer_id", "")).strip()
        }
        project_scores_valid = all(
            isinstance(row.get("scores"), dict)
            and len(row["scores"]) == 7
            and min(row["scores"].values()) >= 60
            and sum(row["scores"].values()) / len(row["scores"]) >= 70
            for row in project_rows
        )
        project_human_path_passed = (
            len(project_reviewers) >= minimum_independent_reviewers
            and all(row.get("recommendation") == "advance" for row in project_rows)
            and project_scores_valid
        )
        behavioral_path_passed = bool(
            isinstance(probe_outcome, dict)
            and probe_outcome.get("vision_scout_id") == vision_scout_id
            and probe_outcome.get("measurement_provenance")
            in {"measured", "external_dataset"}
            and probe_outcome.get("supports_full_genesis_renewal") is True
            and probe_outcome.get("delivery_authority_granted") is False
        )
        passed = human_path_passed or project_human_path_passed or behavioral_path_passed
        reasons = []
        combined_reviewers = reviewers | project_reviewers
        if len(combined_reviewers) < minimum_independent_reviewers:
            reasons.append("independent_human_reviewer_quorum_missing")
        if unfavorable:
            reasons.append("independent_human_reference_or_neither_preferred")
        if missing_axes:
            reasons.append("review_score_axes_incomplete")
        if any(delta < -5 for delta in mean_deltas.values()):
            reasons.append("founder_prompt_mean_axis_delta_below_minus_five")
        if project_rows and not project_human_path_passed:
            reasons.append("project_scout_absolute_review_threshold_not_met")
        if not human_path_passed and not project_human_path_passed and not behavioral_path_passed:
            reasons.append("no_human_or_behavioral_renewal_path_passed")
        if passed:
            reasons = []
        return {
            "vision_scout_promotion_gate_version": (
                "palamedes-vision-scout-promotion-gate/1"
            ),
            "vision_scout_id": vision_scout_id,
            "minimum_independent_reviewers": minimum_independent_reviewers,
            "minimum_confidence": minimum_confidence,
            "qualifying_review_count": len(qualifying) + len(project_rows),
            "distinct_independent_reviewer_count": len(combined_reviewers),
            "mean_score_deltas": mean_deltas,
            "human_review_path_passed": human_path_passed or project_human_path_passed,
            "behavioral_probe_path_passed": behavioral_path_passed,
            "probe_outcome_id": (
                str(probe_outcome.get("probe_outcome_id", ""))
                if isinstance(probe_outcome, dict)
                else ""
            ),
            "passed": passed,
            "failure_reasons": reasons,
            "full_genesis_authorized": passed,
            "delivery_authority_granted": False,
            "evaluated_at": utc_now(),
        }

    def human_review_summary(self) -> Dict[str, Any]:
        rows = self._resolved_human_reviews()
        human_rows = [row for row in rows if row.get("reviewer_kind") == "human"]
        independent_human_rows = [
            row
            for row in human_rows
            if row.get("reviewer_relationship") == "independent"
        ]
        counts = {name: 0 for name in ("generated_preferred", "reference_preferred", "peer", "neither")}
        axes: Dict[str, List[int]] = {}
        per_case: Dict[str, Dict[str, int]] = {}
        for row in human_rows:
            if row.get("resolution") in counts:
                counts[row["resolution"]] += 1
                case_id = str(row.get("case_id", "")).strip()
                if case_id:
                    case = per_case.setdefault(
                        case_id,
                        {
                            "review_count": 0,
                            "generated_preferred": 0,
                            "reference_preferred": 0,
                            "peer": 0,
                            "neither": 0,
                        },
                    )
                    case["review_count"] += 1
                    case[row["resolution"]] += 1
            for axis, delta in row.get("score_deltas", {}).items():
                if isinstance(delta, int):
                    axes.setdefault(axis, []).append(delta)
        summary = {
            "review_count": len(human_rows),
            "independent_human_review_count": len(independent_human_rows),
            "total_resolved_review_count": len(rows),
            "model_or_unattested_review_count": len(rows) - len(human_rows),
            "preference_counts": counts,
            "generated_preference_rate": (
                counts["generated_preferred"] / len(human_rows)
                if human_rows
                else None
            ),
            "mean_score_deltas": {
                axis: sum(values) / len(values) for axis, values in sorted(axes.items())
            },
            "human_attested_evidence_available": bool(human_rows),
            "independent_human_evidence_available": bool(independent_human_rows),
            "per_case": dict(sorted(per_case.items())),
            "human_level_creativity_claim_allowed": False,
            "claim_boundary": (
                "Human preference records are evidence, not automatic authority to "
                "claim stable human-level creativity or market success."
            ),
        }
        summary["exploration_evidence_gate"] = self.human_evidence_gate(rows)
        return summary

    def _resolved_human_reviews(self) -> List[Dict[str, Any]]:
        root = self.root / "resolved-human-reviews"
        rows = []
        if root.is_dir():
            for path in root.glob("*.json"):
                try:
                    row = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                if isinstance(row, dict):
                    rows.append(row)
        return rows

    def human_evidence_gate(
        self,
        rows: Optional[List[Dict[str, Any]]] = None,
        *,
        minimum_independent_reviewers_per_case: int = 3,
        minimum_holdout_cases: int = 3,
        minimum_confidence: int = 60,
    ) -> Dict[str, Any]:
        rows = self._resolved_human_reviews() if rows is None else rows
        holdout_cases = self.holdout_cases()
        cases_by_id = {
            str(row.get("case_id", "")): row
            for row in holdout_cases
            if str(row.get("case_id", ""))
        }
        required_cases = set(cases_by_id)
        distinct_case_fingerprints = {
            str(row.get("case_fingerprint", "")).strip()
            for row in holdout_cases
            if str(row.get("case_fingerprint", "")).strip()
        }
        expected_trials: Dict[str, Dict[str, Any]] = {}
        for case_id, case in cases_by_id.items():
            trial_count = case.get("evaluation_trial_count", 0)
            if isinstance(trial_count, int) and not isinstance(trial_count, bool):
                for trial_number in range(1, trial_count + 1):
                    trial_id = f"{case_id}:preregistered:{trial_number}"
                    expected_trials[trial_id] = {
                        "case_id": case_id,
                        "case_fingerprint": case.get("case_fingerprint", ""),
                    }
        attempts_by_trial = {
            str(row.get("trial_id", "")): row
            for row in self.holdout_attempts()
            if str(row.get("trial_id", ""))
        }
        qualifying = [
            row
            for row in rows
            if row.get("reviewer_kind") == "human"
            and row.get("reviewer_relationship") == "independent"
            and row.get("case_origin") == "external_human_holdout"
            and row.get("evaluation_artifact") == "founder_prompt"
            and row.get("reviewer_is_case_author") is False
            and isinstance(row.get("confidence"), int)
            and row["confidence"] >= minimum_confidence
            and str(row.get("trial_id", "")) in expected_trials
            and row.get("case_id")
            == expected_trials[str(row.get("trial_id", ""))]["case_id"]
            and row.get("case_fingerprint")
            == expected_trials[str(row.get("trial_id", ""))]["case_fingerprint"]
        ]
        reviewers_by_trial = {
            trial_id: {
                str(row.get("reviewer_id", "")).strip()
                for row in qualifying
                if row.get("trial_id") == trial_id
                and str(row.get("reviewer_id", "")).strip()
            }
            for trial_id in expected_trials
        }
        reviewers_by_case = {
            case_id: {
                str(row.get("reviewer_id", "")).strip()
                for row in qualifying
                if row.get("case_id") == case_id
                and str(row.get("reviewer_id", "")).strip()
            }
            for case_id in required_cases
        }
        counts = {
            name: sum(row.get("resolution") == name for row in qualifying)
            for name in (
                "generated_preferred",
                "reference_preferred",
                "peer",
                "neither",
            )
        }
        review_count = len(qualifying)
        favorable_rate = (
            (counts["generated_preferred"] + counts["peer"]) / review_count
            if review_count
            else None
        )
        reference_preference_rate = (
            counts["reference_preferred"] / review_count if review_count else None
        )
        neither_rate = counts["neither"] / review_count if review_count else None
        axis_values: Dict[str, List[int]] = {}
        for row in qualifying:
            for axis, delta in row.get("score_deltas", {}).items():
                if isinstance(delta, int) and not isinstance(delta, bool):
                    axis_values.setdefault(axis, []).append(delta)
        required_axes = {
            "origination",
            "conceptual_distance",
            "affective_depth",
            "mechanism_fusion",
            "world_coherence",
            "three_year_generativity",
            "human_approval_value",
        }
        mean_deltas = {
            axis: sum(axis_values.get(axis, [])) / len(axis_values[axis])
            for axis in sorted(required_axes)
            if axis_values.get(axis)
        }
        failures = []
        if len(required_cases) < minimum_holdout_cases:
            failures.append(
                f"external holdout coverage is {len(required_cases)}/"
                f"{minimum_holdout_cases} cases"
            )
        if len(distinct_case_fingerprints) < minimum_holdout_cases:
            failures.append(
                f"distinct holdout fingerprint coverage is "
                f"{len(distinct_case_fingerprints)}/{minimum_holdout_cases}"
            )
        for trial_id, expected in sorted(expected_trials.items()):
            attempt = attempts_by_trial.get(trial_id)
            if attempt is None:
                failures.append(
                    f"{trial_id} has no preregistered attempt record"
                )
            elif (
                attempt.get("status") != "completed"
                or attempt.get("case_id") != expected["case_id"]
                or attempt.get("case_fingerprint")
                != expected["case_fingerprint"]
            ):
                failures.append(f"{trial_id} is not a completed attributable attempt")
            if len(reviewers_by_trial[trial_id]) < minimum_independent_reviewers_per_case:
                failures.append(
                    f"{trial_id} lacks independent reviewer quorum "
                    f"{len(reviewers_by_trial[trial_id])}/"
                    f"{minimum_independent_reviewers_per_case}"
                )
        if favorable_rate is None or favorable_rate < 2 / 3:
            failures.append("generated-or-peer preference rate is below 2/3")
        if reference_preference_rate is None or reference_preference_rate > 1 / 3:
            failures.append("reference preference rate exceeds 1/3")
        if neither_rate is None or neither_rate > 1 / 4:
            failures.append("neither preference rate exceeds 1/4")
        missing_axes = sorted(required_axes - set(mean_deltas))
        if missing_axes:
            failures.append("missing independent score axes: " + ", ".join(missing_axes))
        regressed_axes = sorted(
            axis for axis, delta in mean_deltas.items() if delta < -5
        )
        if regressed_axes:
            failures.append(
                "generated vision is more than 5 points worse on: "
                + ", ".join(regressed_axes)
            )
        passed = not failures
        return {
            "gate_version": "palamedes-vision-human-evidence-gate/3",
            "status": "pass" if passed else "fail",
            "claim_scope": (
                "repeated_blind_human_founder_prompt_support" if passed else "none"
            ),
            "evaluation_artifact": "founder_prompt",
            "qualifying_review_count": review_count,
            "minimum_confidence": minimum_confidence,
            "minimum_independent_reviewers_per_case": minimum_independent_reviewers_per_case,
            "minimum_holdout_cases": minimum_holdout_cases,
            "independent_reviewer_count_by_case": {
                case_id: len(reviewers)
                for case_id, reviewers in sorted(reviewers_by_case.items())
            },
            "independent_reviewer_count_by_trial": {
                trial_id: len(reviewers)
                for trial_id, reviewers in sorted(reviewers_by_trial.items())
            },
            "preregistered_trial_count": len(expected_trials),
            "completed_trial_count": sum(
                attempts_by_trial.get(trial_id, {}).get("status") == "completed"
                and attempts_by_trial.get(trial_id, {}).get("case_id")
                == expected["case_id"]
                and attempts_by_trial.get(trial_id, {}).get("case_fingerprint")
                == expected["case_fingerprint"]
                for trial_id, expected in expected_trials.items()
            ),
            "distinct_holdout_fingerprint_count": len(
                distinct_case_fingerprints
            ),
            "preference_counts": counts,
            "generated_or_peer_rate": favorable_rate,
            "reference_preference_rate": reference_preference_rate,
            "neither_rate": neither_rate,
            "mean_score_deltas": mean_deltas,
            "failure_reasons": failures,
            "human_level_creativity_claim_allowed": False,
            "market_success_claim_allowed": False,
            "custody_boundary": (
                "Only founder_prompt packets qualify; legacy full-brief reviews are "
                "excluded. Reviewer kind and independence are attested in the response, "
                "not identity-verified by Palamedes."
            ),
        }

    def human_review_queue(self) -> List[Dict[str, Any]]:
        packet_root = self.root / "human-review"
        response_root = self.root / "human-responses"
        rows = []
        if not packet_root.is_dir():
            return rows
        for path in sorted(packet_root.glob("*.json")):
            try:
                packet = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            packet_id = str(packet.get("vision_review_packet_id", ""))
            response_count = (
                len(list(response_root.glob(f"{packet_id}--*.json")))
                if response_root.is_dir()
                else 0
            )
            rows.append(
                {
                    "vision_review_packet_id": packet_id,
                    "case_id": packet.get("case_id", ""),
                    "trial_id": packet.get("trial_id", ""),
                    "response_count": response_count,
                    "created_at": packet.get("created_at", ""),
                    "packet_path": str(path),
                }
            )
        rows.sort(key=lambda row: (row["response_count"], row["created_at"]))
        return rows

    def next_human_review_packet(self) -> Dict[str, Any]:
        queue = self.human_review_queue()
        if not queue:
            return {}
        return json.loads(Path(queue[0]["packet_path"]).read_text(encoding="utf-8"))

    def build_human_review_bundle(self) -> Path:
        queue = self.human_review_queue()
        packets = []
        for row in queue:
            packet = json.loads(Path(row["packet_path"]).read_text(encoding="utf-8"))
            packet["packet_fingerprint"] = fingerprint(packet)
            packet["existing_response_count"] = row["response_count"]
            packets.append(packet)
        safe_json = json.dumps(packets, ensure_ascii=False).replace("<", "\\u003c")
        bundle_root = self.root / "reviewer"
        bundle_root.mkdir(parents=True, exist_ok=True)
        path = bundle_root / "index.html"
        html = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><link rel="icon" href="data:,">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Palamedes blind vision review</title>
<style>
body{font:16px/1.5 system-ui,sans-serif;max-width:1100px;margin:24px auto;padding:0 18px;color:#17202a;background:#f5f6f7}
header,.panel{background:white;border:1px solid #d9dee3;border-radius:12px;padding:18px;margin:14px 0}
.options{display:grid;grid-template-columns:1fr 1fr;gap:14px}.option{white-space:pre-wrap;background:#fafafa;border:1px solid #ddd;padding:14px;border-radius:8px}
.scores{display:grid;grid-template-columns:2fr 1fr 1fr;gap:8px;align-items:center}.scores input{width:88px}
label{display:block;margin:10px 0}textarea{width:100%;min-height:100px}button{padding:10px 16px;margin-right:8px}
.warning{color:#8a3b12;font-weight:650}@media(max-width:760px){.options{grid-template-columns:1fr}}
</style></head><body>
<header><h1>Blind product-vision review</h1><p>Judge A and B without guessing authorship. This file contains no answer key. Complete every score, then download the response JSON and import it into Palamedes.</p><p class="warning">Do not consult the answer-key directory before submitting.</p></header>
<main id="app"></main>
<script id="packets" type="application/json">__PACKETS__</script>
<script>
const packets=JSON.parse(document.getElementById('packets').textContent);let index=0;
const app=document.getElementById('app');
function escText(tag,text){const e=document.createElement(tag);e.textContent=text;return e.outerHTML}
function render(){if(!packets.length){app.innerHTML='<div class="panel">No review packets.</div>';return}
 const p=packets[index];
 app.innerHTML=`<section class="panel"><strong>Packet ${index+1}/${packets.length}</strong> · ${p.case_id} · existing responses ${p.existing_response_count}<p>${p.instructions}</p></section>
 <section class="options"><article class="option"><h2>A</h2><div id="optionA"></div></article><article class="option"><h2>B</h2><div id="optionB"></div></article></section>
 <section class="panel"><label>Reviewer ID <input id="reviewer" autocomplete="off"></label><label>Reviewer kind <select id="kind"><option value="">choose</option><option value="human">human</option><option value="model">model</option></select></label><label>Relationship to this product <select id="relationship"><option value="">choose</option><option value="independent">independent</option><option value="team">team</option><option value="author">author</option><option value="unknown">unknown</option></select></label>
 <label>Preferred <select id="preferred"><option value="">choose</option><option>A</option><option>B</option><option>peer</option><option>neither</option></select></label>
 <h3>Scores (0–100)</h3><div class="scores"><strong>Axis</strong><strong>A</strong><strong>B</strong>${p.axes.map((a,i)=>`<span>${a}</span><input id="a${i}" type="number" min="0" max="100"><input id="b${i}" type="number" min="0" max="100">`).join('')}</div>
 <label>Rationale<textarea id="rationale"></textarea></label><label>Confidence <input id="confidence" type="number" min="0" max="100"></label>
 <button onclick="downloadResponse()">Download response JSON</button><button onclick="move(-1)">Previous</button><button onclick="move(1)">Next</button><p id="error" class="warning"></p></section>`;
 document.getElementById('optionA').textContent=p.options.A;document.getElementById('optionB').textContent=p.options.B;
}
function move(delta){index=(index+delta+packets.length)%packets.length;render()}
function integer(id){const raw=document.getElementById(id).value;const n=Number(raw);return raw!==''&&Number.isInteger(n)&&n>=0&&n<=100?n:null}
function downloadResponse(){const p=packets[index],scores_A={},scores_B={};let invalid=false;p.axes.forEach((axis,i)=>{scores_A[axis]=integer(`a${i}`);scores_B[axis]=integer(`b${i}`);if(scores_A[axis]===null||scores_B[axis]===null)invalid=true});
 const response={vision_review_packet_id:p.vision_review_packet_id,packet_fingerprint:p.packet_fingerprint,reviewer_id:document.getElementById('reviewer').value.trim(),reviewer_kind:document.getElementById('kind').value,reviewer_relationship:document.getElementById('relationship').value,preferred:document.getElementById('preferred').value,scores_A,scores_B,rationale:document.getElementById('rationale').value.trim(),confidence:integer('confidence')};
 if(!response.reviewer_id||!response.reviewer_kind||!response.reviewer_relationship||!response.preferred||!response.rationale||response.confidence===null||invalid){document.getElementById('error').textContent='Complete every field and score.';return}
 const blob=new Blob([JSON.stringify(response,null,2)+'\\n'],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`${p.vision_review_packet_id}--response.json`;a.click();URL.revokeObjectURL(url);document.getElementById('error').textContent='Downloaded. Import this JSON before viewing any answer key.';
}
render();
</script></body></html>""".replace("__PACKETS__", safe_json)
        path.write_text(html, encoding="utf-8")
        return path

    def machine_benchmark_summary(self) -> Dict[str, Any]:
        rows = []
        if self.root.is_dir():
            for path in self.root.glob("vision-benchmark-*.json"):
                try:
                    row = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                if isinstance(row, dict):
                    rows.append(row)
        relations = {name: 0 for name in ("weaker", "different_peer", "stronger")}
        score_values: Dict[str, List[int]] = {}
        founder_prompt_score_values: Dict[str, List[int]] = {}
        independent = 0
        titles = []
        case_counts: Dict[str, int] = {}
        case_pass_counts: Dict[str, int] = {}
        case_titles: Dict[str, List[str]] = {}
        trial_count = 0
        gate_counts: Dict[str, int] = {}
        gate_pass_counts: Dict[str, int] = {}
        failure_reason_counts: Dict[str, int] = {}
        for row in rows:
            gate_version = str(
                row.get("quality_gate_version", "legacy-pre-core-requirements")
            )
            gate_counts[gate_version] = gate_counts.get(gate_version, 0) + 1
            if bool(row.get("passed")):
                gate_pass_counts[gate_version] = gate_pass_counts.get(gate_version, 0) + 1
            for reason in row.get("failure_reasons", []):
                if isinstance(reason, str) and reason:
                    failure_reason_counts[reason] = (
                        failure_reason_counts.get(reason, 0) + 1
                    )
            case_id = str(row.get("case_id", "")).strip()
            if case_id:
                case_counts[case_id] = case_counts.get(case_id, 0) + 1
                if bool(row.get("passed")):
                    case_pass_counts[case_id] = case_pass_counts.get(case_id, 0) + 1
            if str(row.get("trial_id", "")).strip():
                trial_count += 1
            relation = row.get("judgment", {}).get("reference_relation")
            if relation in relations:
                relations[relation] += 1
            for axis, value in row.get("judgment", {}).get("scores", {}).items():
                if isinstance(value, int):
                    score_values.setdefault(axis, []).append(value)
            for axis, value in row.get("founder_prompt_judgment", {}).get(
                "scores", {}
            ).items():
                if isinstance(value, int):
                    founder_prompt_score_values.setdefault(axis, []).append(value)
            if row.get("evaluation_custody", {}).get("independent_provider_claimed"):
                independent += 1
            if str(row.get("selected_title", "")).strip():
                titles.append(row["selected_title"].strip())
                if case_id:
                    case_titles.setdefault(case_id, []).append(
                        row["selected_title"].strip()
                    )
        return {
            "benchmark_count": len(rows),
            "pass_count": sum(bool(row.get("passed")) for row in rows),
            "pass_rate": (
                sum(bool(row.get("passed")) for row in rows) / len(rows)
                if rows
                else None
            ),
            "reference_relations": relations,
            "mean_scores": {
                axis: sum(values) / len(values)
                for axis, values in sorted(score_values.items())
            },
            "mean_founder_prompt_scores": {
                axis: sum(values) / len(values)
                for axis, values in sorted(founder_prompt_score_values.items())
            },
            "independent_provider_judgment_count": independent,
            "unique_selected_title_count": len(set(titles)),
            "selected_title_count": len(titles),
            "selected_title_coverage_rate": (
                len(titles) / len(rows) if rows else None
            ),
            "title_diversity_rate": len(set(titles)) / len(titles) if titles else None,
            "case_counts": dict(sorted(case_counts.items())),
            "per_case": {
                case_id: {
                    "benchmark_count": count,
                    "pass_count": case_pass_counts.get(case_id, 0),
                    "pass_rate": case_pass_counts.get(case_id, 0) / count,
                    "title_diversity_rate": (
                        len(set(case_titles.get(case_id, [])))
                        / len(case_titles[case_id])
                        if case_titles.get(case_id)
                        else None
                    ),
                }
                for case_id, count in sorted(case_counts.items())
            },
            "identified_trial_count": trial_count,
            "gate_versions": {
                version: {
                    "benchmark_count": count,
                    "pass_count": gate_pass_counts.get(version, 0),
                    "pass_rate": gate_pass_counts.get(version, 0) / count,
                }
                for version, count in sorted(gate_counts.items())
            },
            "current_gate_version": "palamedes-vision-benchmark-gate/3",
            "current_gate": {
                "benchmark_count": gate_counts.get(
                    "palamedes-vision-benchmark-gate/3", 0
                ),
                "pass_count": gate_pass_counts.get(
                    "palamedes-vision-benchmark-gate/3", 0
                ),
                "pass_rate": (
                    gate_pass_counts.get("palamedes-vision-benchmark-gate/3", 0)
                    / gate_counts["palamedes-vision-benchmark-gate/3"]
                    if gate_counts.get("palamedes-vision-benchmark-gate/3")
                    else None
                ),
            },
            "failure_reason_counts": dict(sorted(failure_reason_counts.items())),
            "human_level_creativity_claim_allowed": False,
            "claim_boundary": (
                "Machine pass rates and diversity are correlated benchmark evidence; "
                "they cannot establish stable human-level creativity."
            ),
        }


def create_human_review_packet(
    *,
    case: VisionBenchmarkCase,
    generated_brief: str,
    vision_genesis_id: str = "",
    source_artifact_type: str = "vision_genesis",
    source_artifact_id: str = "",
    store: VisionBenchmarkStore,
    trial_id: str = "",
) -> Dict[str, Any]:
    if source_artifact_type not in {"vision_genesis", "vision_scout"}:
        raise ValueError("human review source artifact type is invalid")
    artifact_id = source_artifact_id or vision_genesis_id
    if not artifact_id:
        raise ValueError("human review requires a source artifact ID")
    identity = fingerprint(
        {
            "case_id": case.case_id,
            "generated_brief": generated_brief,
            "source_artifact_type": source_artifact_type,
            "source_artifact_id": artifact_id,
            "trial_id": trial_id,
        }
    )
    generated_label = "A" if int(identity[0], 16) % 2 == 0 else "B"
    reference_label = "B" if generated_label == "A" else "A"
    options = {
        generated_label: generated_brief,
        reference_label: case.hidden_human_reference,
    }
    packet_id = f"vision-review-{identity[:12]}"
    packet = {
        "vision_review_packet_version": "palamedes-vision-human-review/1",
        "vision_review_packet_id": packet_id,
        "case_id": case.case_id,
        "case_origin": case.case_origin,
        "case_fingerprint": case.case_fingerprint,
        "trial_id": trial_id,
        "generator_context": case.generator_context,
        "evaluation_artifact": "founder_prompt",
        "source_artifact_type": source_artifact_type,
        "source_artifact_id": artifact_id,
        "instructions": (
            "Judge A and B without guessing authorship. Treat both as upstream founder "
            "prompts: prefer the text that could better originate a strong product world "
            "without a human first supplying its central mechanism, or mark them peers."
        ),
        "options": options,
        "axes": [
            "origination", "conceptual_distance", "affective_depth",
            "mechanism_fusion", "world_coherence", "three_year_generativity",
            "human_approval_value",
        ],
        "response_shape": {
            "reviewer_id": "stable non-secret reviewer identifier",
            "reviewer_kind": "human|model",
            "reviewer_relationship": "independent|team|author|unknown",
            "packet_fingerprint": "SHA-256 fingerprint shown in the review bundle",
            "preferred": "A|B|peer|neither",
            "scores_A": "seven integer scores 0-100",
            "scores_B": "seven integer scores 0-100",
            "rationale": "decision-relevant explanation",
            "confidence": "integer 0-100",
        },
        "authorship_hidden": True,
        "created_at": utc_now(),
    }
    answer_key = {
        "vision_review_answer_key_version": "palamedes-vision-human-review-key/1",
        "vision_review_packet_id": packet_id,
        "generated_label": generated_label,
        "human_reference_label": reference_label,
        "source_artifact_type": source_artifact_type,
        "source_artifact_id": artifact_id,
        "case_origin": case.case_origin,
        "case_fingerprint": case.case_fingerprint,
        "case_author_id": case.case_author_id,
        "trial_id": trial_id,
        "created_at": utc_now(),
    }
    paths = store.save_human_review(packet, answer_key)
    return {"packet": packet, "answer_key": answer_key, **paths}


def judge_founder_prompt(
    *,
    case: VisionBenchmarkCase,
    founder_prompt: str,
    judge: Callable[[str, str], Dict[str, Any]],
) -> Dict[str, Any]:
    judgment = judge(
        "blind_founder_prompt_judge",
        f"""Evaluate only whether the generated founder prompt could replace the upstream
product-direction text a thoughtful human would otherwise have needed to supply. The
generator saw the product context but never the hidden human reference. Do not reward
shared wording, length, or implementation detail. Return JSON:
{{"scores":{{"problem_reframing":0,"unsupplied_mechanism":0,
"affective_thesis":0,"product_world_seed":0,"human_prompt_substitutability":0}},
"reference_relation":"weaker|different_peer|stronger",
"solution_was_present_in_input":false,"generic_request":false,
"decisive_difference":"...","rationale":"..."}}
All scores are integers 0-100. `solution_was_present_in_input` is true if the generator
context already supplied the central mechanism, in which case origination is not proven.
`generic_request` is true if the prompt merely asks for engagement, polish, gamification,
or ideas without originating a causal product direction.

Generator input:
{case.generator_context}

Generated founder prompt:
{founder_prompt}

Hidden human founder text revealed only to the judge:
{case.hidden_human_reference}""",
    )
    scores = judgment.get("scores")
    score_names = {
        "problem_reframing",
        "unsupplied_mechanism",
        "affective_thesis",
        "product_world_seed",
        "human_prompt_substitutability",
    }
    if not isinstance(scores, dict) or set(scores) != score_names:
        raise ValueError("founder prompt judge requires all five score axes")
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 100
        for value in scores.values()
    ):
        raise ValueError("founder prompt judge scores must be integers 0-100")
    if judgment.get("reference_relation") not in {
        "weaker", "different_peer", "stronger"
    }:
        raise ValueError("invalid founder prompt reference relation")
    if not isinstance(judgment.get("solution_was_present_in_input"), bool):
        raise ValueError("founder prompt judge requires solution_was_present_in_input")
    if not isinstance(judgment.get("generic_request"), bool):
        raise ValueError("founder prompt judge requires generic_request")
    for field in ("decisive_difference", "rationale"):
        if not str(judgment.get(field, "")).strip():
            raise ValueError(f"founder prompt judge requires {field}")
    thresholds = {
        "problem_reframing": 65,
        "unsupplied_mechanism": 70,
        "affective_thesis": 65,
        "product_world_seed": 70,
        "human_prompt_substitutability": 70,
    }
    passed = (
        all(scores[name] >= threshold for name, threshold in thresholds.items())
        and not judgment["solution_was_present_in_input"]
        and not judgment["generic_request"]
    )
    return {"judgment": judgment, "thresholds": thresholds, "passed": passed}


def run_blind_scout_case(
    *,
    case: VisionBenchmarkCase,
    ask: Callable[[str, str], Dict[str, Any]],
    scout_store: VisionScoutStore,
    benchmark_store: VisionBenchmarkStore,
    judge_ask: Callable[[str, str], Dict[str, Any]] = None,
    generator_identity: str = "unspecified",
    judge_identity: str = "unspecified",
    usage_report: Optional[Callable[[], Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Measure whether the three-call scout can originate a human-reviewable prompt.

    A machine pass creates a blind human-review packet. It never authorizes full Genesis
    or delivery; those require later independent human or behavioral renewal evidence.
    """
    attempt = benchmark_store.reserve_scout_attempt(case)
    lowered_context = case.generator_context.lower()
    leaked = [term for term in case.hidden_anchor_terms if term.lower() in lowered_context]
    if leaked:
        raise ValueError(f"benchmark generator context leaks hidden anchors: {leaked}")

    scout = run_vision_scout(
        ask=ask,
        store=scout_store,
        context=case.generator_context,
    )
    founder_prompt = str(scout.get("selected_founder_prompt", "")).strip()
    governor_selected_review = (
        scout.get("status") == "candidate_for_human_review"
        and scout.get("governor", {}).get("decision") == "blind_human_review"
    )
    prompt_result: Dict[str, Any] = {
        "judgment": {},
        "thresholds": {
            "problem_reframing": 65,
            "unsupplied_mechanism": 70,
            "affective_thesis": 65,
            "product_world_seed": 70,
            "human_prompt_substitutability": 70,
        },
        "passed": False,
    }
    if founder_prompt and governor_selected_review:
        prompt_result = judge_founder_prompt(
            case=case,
            founder_prompt=founder_prompt,
            judge=judge_ask or ask,
        )

    passed = bool(governor_selected_review and prompt_result["passed"])
    failure_reasons: List[str] = []
    if not founder_prompt:
        failure_reasons.append("scout_selected_no_founder_prompt")
    if not governor_selected_review:
        failure_reasons.append("scout_governor_discarded")
    judgment = prompt_result["judgment"]
    if judgment.get("solution_was_present_in_input"):
        failure_reasons.append("founder_prompt_solution_already_supplied")
    if judgment.get("generic_request"):
        failure_reasons.append("founder_prompt_is_generic_request")
    scores = judgment.get("scores", {})
    for name, threshold in prompt_result["thresholds"].items():
        if name in scores and scores[name] < threshold:
            failure_reasons.append(f"founder_prompt_score_below_threshold:{name}")

    identity = {
        "case_id": case.case_id,
        "vision_scout_id": scout["vision_scout_id"],
        "founder_prompt_judgment": judgment,
    }
    record = {
        "vision_scout_benchmark_version": "palamedes-vision-scout-benchmark/1",
        "vision_scout_benchmark_id": (
            f"vision-scout-benchmark-{fingerprint(identity)[:12]}"
        ),
        "case_id": case.case_id,
        "case_origin": case.case_origin,
        "case_fingerprint": case.case_fingerprint,
        "attempt_id": attempt["attempt_id"],
        "generator_context_fingerprint": fingerprint(case.generator_context),
        "hidden_reference_fingerprint": fingerprint(case.hidden_human_reference),
        "hidden_anchors_verified_absent": True,
        "evaluation_custody": {
            "generator_identity": generator_identity,
            "judge_identity": judge_identity,
            "independent_provider_claimed": bool(
                judge_ask is not None and generator_identity != judge_identity
            ),
        },
        "vision_scout_id": scout["vision_scout_id"],
        "scout_generation_call_count": scout["generation_call_count"],
        "judge_call_count": 1 if judgment else 0,
        "founder_prompt_fingerprint": (
            fingerprint(founder_prompt) if founder_prompt else ""
        ),
        "founder_prompt_judgment": judgment,
        "founder_prompt_thresholds": prompt_result["thresholds"],
        "founder_prompt_gate_passed": bool(prompt_result["passed"]),
        "passed": passed,
        "failure_reasons": failure_reasons,
        "full_genesis_authorized": False,
        "delivery_authority_granted": False,
        "next_authorized_step": "blind_human_review" if passed else "discard",
        "created_at": utc_now(),
    }
    if usage_report is not None:
        provider_usage = usage_report()
        if not isinstance(provider_usage, dict):
            raise ValueError("scout benchmark usage_report must return an object")
        record["provider_usage"] = provider_usage
    if passed:
        review = create_human_review_packet(
            case=case,
            generated_brief=founder_prompt,
            source_artifact_type="vision_scout",
            source_artifact_id=scout["vision_scout_id"],
            store=benchmark_store,
        )
        record["human_review_packet_id"] = review["packet"][
            "vision_review_packet_id"
        ]
    benchmark_store.save_scout_benchmark(record)
    benchmark_store.complete_scout_attempt(
        attempt, record["vision_scout_benchmark_id"]
    )
    return record


def run_blind_case(
    *,
    case: VisionBenchmarkCase,
    ask: Callable[[str, str], Dict[str, Any]],
    vision_store: VisionStore,
    benchmark_store: VisionBenchmarkStore,
    judge_ask: Callable[[str, str], Dict[str, Any]] = None,
    generator_identity: str = "unspecified",
    judge_identity: str = "unspecified",
    trial_id: str = "",
    usage_report: Optional[Callable[[], Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    lowered_context = case.generator_context.lower()
    leaked = [term for term in case.hidden_anchor_terms if term.lower() in lowered_context]
    if leaked:
        raise ValueError(f"benchmark generator context leaks hidden anchors: {leaked}")
    holdout_attempt = None
    if case.case_origin == "external_human_holdout":
        holdout_attempt = benchmark_store.reserve_holdout_attempt(case)
        trial_id = holdout_attempt["trial_id"]
    vision = run_vision_genesis(
        ask=ask,
        store=vision_store,
        context=case.generator_context,
    )
    generated_brief = vision.get("judgment", {}).get("vision_brief", "")
    founder_prompt = vision.get("judgment", {}).get("founder_prompt", "")
    judge = judge_ask or ask
    judgment = judge(
        "blind_vision_judge",
        f"""Compare an independently generated product vision with a hidden human reference.
The generator never saw the reference. Do not reward keyword overlap or require the same
solution; reward an equally strong or better original product world. Return JSON:
{{"scores":{{"origination":0,"conceptual_distance":0,"affective_depth":0,
"mechanism_fusion":0,"world_coherence":0,"three_year_generativity":0,
"human_approval_value":0}},"reference_relation":"weaker|different_peer|stronger",
"generic_feature_pack":false,"decisive_strength":"...","decisive_weakness":"...",
"core_requirements_satisfied":true,"unmet_core_requirements":[],
"would_human_likely_approve_exploration":true,"rationale":"..."}}
All scores are integers 0-100. `origination` measures whether the proposal introduces
the core product concept rather than merely elaborating a supplied concept.
`core_requirements_satisfied` is false when the selected vision omits or contradicts any
explicit generator-input objective or constraint, even if the world is otherwise original.

Generator input:\n{case.generator_context}

Generated vision:\n{generated_brief}

Hidden human reference revealed only to the judge:\n{case.hidden_human_reference}""",
    )
    scores = judgment.get("scores")
    required_scores = {
        "origination", "conceptual_distance", "affective_depth", "mechanism_fusion",
        "world_coherence", "three_year_generativity", "human_approval_value",
    }
    if not isinstance(scores, dict) or set(scores) != required_scores:
        raise ValueError("blind judge requires all seven score axes")
    for name, score in scores.items():
        if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= 100:
            raise ValueError(f"blind judge score {name} must be integer 0-100")
    if judgment.get("reference_relation") not in {"weaker", "different_peer", "stronger"}:
        raise ValueError("invalid reference relation")
    if (
        not isinstance(judgment.get("generic_feature_pack"), bool)
        or not isinstance(judgment.get("core_requirements_satisfied"), bool)
        or not isinstance(
            judgment.get("would_human_likely_approve_exploration"), bool
        )
    ):
        raise ValueError("blind judge boolean fields are required")
    unmet = judgment.get("unmet_core_requirements")
    if not isinstance(unmet, list) or not all(
        isinstance(item, str) and item.strip() for item in unmet
    ):
        raise ValueError("blind judge unmet_core_requirements must be a string list")
    if judgment["core_requirements_satisfied"] == bool(unmet):
        raise ValueError("core requirement verdict contradicts unmet requirements")
    for field in ("decisive_strength", "decisive_weakness", "rationale"):
        if not str(judgment.get(field, "")).strip():
            raise ValueError(f"blind judge requires {field}")
    prompt_result = judge_founder_prompt(
        case=case, founder_prompt=founder_prompt, judge=judge
    )
    prompt_judgment = prompt_result["judgment"]
    prompt_scores = prompt_judgment["scores"]
    pass_thresholds = {
        "origination": 70,
        "conceptual_distance": 60,
        "affective_depth": 60,
        "mechanism_fusion": 60,
        "world_coherence": 65,
        "three_year_generativity": 60,
        "human_approval_value": 65,
    }
    prompt_thresholds = prompt_result["thresholds"]
    founder_prompt_passed = prompt_result["passed"]
    passed = (
        all(scores[name] >= threshold for name, threshold in pass_thresholds.items())
        and founder_prompt_passed
        and bool(vision.get("requirement_gate", {}).get("passed"))
        and not judgment["generic_feature_pack"]
        and judgment["core_requirements_satisfied"]
        and not unmet
        and judgment["would_human_likely_approve_exploration"]
    )
    failure_reasons = []
    if not vision.get("requirement_gate", {}).get("passed"):
        failure_reasons.append("genesis_core_requirements_unresolved")
    if unmet:
        failure_reasons.append("judge_core_requirements_unresolved")
    if judgment["generic_feature_pack"]:
        failure_reasons.append("generic_feature_pack")
    if not judgment["would_human_likely_approve_exploration"]:
        failure_reasons.append("human_exploration_approval_unlikely")
    if prompt_judgment["solution_was_present_in_input"]:
        failure_reasons.append("founder_prompt_solution_already_supplied")
    if prompt_judgment["generic_request"]:
        failure_reasons.append("founder_prompt_is_generic_request")
    for name, threshold in prompt_thresholds.items():
        if prompt_scores[name] < threshold:
            failure_reasons.append(f"founder_prompt_score_below_threshold:{name}")
    for name, threshold in pass_thresholds.items():
        if scores[name] < threshold:
            failure_reasons.append(f"score_below_threshold:{name}")
    identity = {
        "case_id": case.case_id,
        "case_origin": case.case_origin,
        "case_fingerprint": case.case_fingerprint,
        "trial_id": trial_id,
        "vision_genesis_id": vision["vision_genesis_id"],
        "judgment": judgment,
        "founder_prompt_judgment": prompt_judgment,
    }
    record = {
        "vision_benchmark_version": "palamedes-vision-benchmark/1",
        "vision_benchmark_id": f"vision-benchmark-{fingerprint(identity)[:12]}",
        "case_id": case.case_id,
        "case_origin": case.case_origin,
        "case_fingerprint": case.case_fingerprint,
        "trial_id": trial_id,
        "generator_context_fingerprint": fingerprint(case.generator_context),
        "hidden_reference_fingerprint": fingerprint(case.hidden_human_reference),
        "hidden_anchors_verified_absent": True,
        "evaluation_custody": {
            "generator_identity": generator_identity,
            "judge_identity": judge_identity,
            "independent_provider_claimed": bool(
                judge_ask is not None and generator_identity != judge_identity
            ),
        },
        "vision_genesis_id": vision["vision_genesis_id"],
        "selected_title": next(
            (
                row.get("title", "")
                for row in vision.get("product_worlds", {}).get("worlds", [])
                if row.get("vision_id")
                == vision.get("judgment", {}).get("selected_vision_id")
            ),
            "",
        ),
        "judgment": judgment,
        "founder_prompt_fingerprint": fingerprint(founder_prompt),
        "founder_prompt_judgment": prompt_judgment,
        "thresholds": pass_thresholds,
        "founder_prompt_thresholds": prompt_thresholds,
        "founder_prompt_gate_passed": founder_prompt_passed,
        "quality_gate_version": "palamedes-vision-benchmark-gate/3",
        "genesis_requirement_gate_passed": bool(
            vision.get("requirement_gate", {}).get("passed")
        ),
        "passed": passed,
        "failure_reasons": failure_reasons,
        "created_at": utc_now(),
    }
    if usage_report is not None:
        provider_usage = usage_report()
        if not isinstance(provider_usage, dict):
            raise ValueError("benchmark usage_report must return an object")
        record["provider_usage"] = provider_usage
    review = create_human_review_packet(
        case=case,
        generated_brief=founder_prompt,
        vision_genesis_id=vision["vision_genesis_id"],
        store=benchmark_store,
        trial_id=trial_id,
    )
    record["human_review_packet_id"] = review["packet"]["vision_review_packet_id"]
    benchmark_store.save(record)
    if holdout_attempt is not None:
        benchmark_store.complete_holdout_attempt(
            holdout_attempt, record["vision_benchmark_id"]
        )
    return record


def _run_agenda_ablation_once(
    *,
    case: VisionBenchmarkCase,
    ask: Callable[[str, str], Dict[str, Any]],
    judge_ask: Callable[[str, str], Dict[str, Any]],
    vision_root: Path,
    benchmark_store: VisionBenchmarkStore,
    generator_identity: str = "unspecified",
    judge_identity: str = "unspecified",
    usage_report: Optional[Callable[[], Dict[str, Any]]] = None,
    challenger_condition: str = "adaptive",
    comparator_condition: str = "conventional",
) -> Dict[str, Any]:
    """Compare two agenda strategies with equal generation calls."""
    supported_conditions = {"adaptive", "frontier", "conventional"}
    if (
        challenger_condition not in supported_conditions
        or comparator_condition not in supported_conditions
        or challenger_condition == comparator_condition
    ):
        raise ValueError("agenda ablation requires two distinct supported conditions")
    order = [challenger_condition, comparator_condition]
    if int(fingerprint({"case_id": case.case_id, "context": case.generator_context})[0], 16) % 2:
        order.reverse()
    calls = {condition: [] for condition in order}
    visions: Dict[str, Dict[str, Any]] = {}
    for condition in order:
        def condition_ask(role: str, prompt: str, *, _condition=condition):
            calls[_condition].append(role)
            return ask(role, prompt)

        visions[condition] = run_vision_genesis(
            ask=condition_ask,
            store=VisionStore(vision_root / condition),
            context=case.generator_context,
            agenda_strategy=condition,
        )
    expected_roles = [
        "vision_agenda_architect",
        "desire_interpreter",
        "distant_analogy_explorer",
        "mechanism_fusion_inventor",
        "product_world_builder",
        "maniac_critic_and_vision_author",
        "vision_reality_governor",
    ]
    if any(calls[condition] != expected_roles for condition in order):
        raise ValueError("agenda ablation requires the same seven generation roles")
    identity = {
        condition: visions[condition]["judgment"]["vision_brief"]
        for condition in order
    }
    challenger_label = "A" if int(fingerprint(identity)[0], 16) % 2 == 0 else "B"
    comparator_label = "B" if challenger_label == "A" else "A"
    condition_by_label = {
        challenger_label: challenger_condition,
        comparator_label: comparator_condition,
    }
    options = {
        label: visions[condition]["judgment"]["vision_brief"]
        for label, condition in condition_by_label.items()
    }
    judgment = judge_ask(
        "blind_agenda_ablation_judge",
        f"""Compare two product visions produced from identical context, model family, and
seven generation calls. Authorship and condition are hidden. Judge the vision, not prose
length. Return JSON: {{"preferred":"A|B|peer|neither","scores_A":{{"origination":0,
"conceptual_distance":0,"affective_depth":0,"mechanism_fusion":0,
"world_coherence":0,"three_year_generativity":0,"human_approval_value":0}},
"scores_B":{{same seven axes}},"decisive_difference":"...","rationale":"..."}}
All scores are integers 0-100. Do not infer which condition is experimental.

Shared context:\n{case.generator_context}

Option A:\n{options['A']}

Option B:\n{options['B']}""",
    )
    preferred = judgment.get("preferred")
    if preferred not in {"A", "B", "peer", "neither"}:
        raise ValueError("agenda ablation judge requires A, B, peer, or neither")
    axes = {
        "origination", "conceptual_distance", "affective_depth",
        "mechanism_fusion", "world_coherence", "three_year_generativity",
        "human_approval_value",
    }
    for field in ("scores_A", "scores_B"):
        scores = judgment.get(field)
        if not isinstance(scores, dict) or set(scores) != axes:
            raise ValueError("agenda ablation judge requires all seven score axes")
        if any(
            not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 100
            for value in scores.values()
        ):
            raise ValueError("agenda ablation scores must be integers 0-100")
    for field in ("decisive_difference", "rationale"):
        if not str(judgment.get(field, "")).strip():
            raise ValueError(f"agenda ablation judge requires {field}")
    preferred_condition = (
        condition_by_label[preferred] if preferred in {"A", "B"} else preferred
    )
    record_identity = {
        "case_id": case.case_id,
        "vision_ids": {
            condition: visions[condition]["vision_genesis_id"] for condition in order
        },
        "judgment": judgment,
    }
    record = {
        "vision_agenda_ablation_version": "palamedes-vision-agenda-ablation/1",
        "vision_agenda_ablation_id": (
            f"vision-agenda-ablation-{fingerprint(record_identity)[:12]}"
        ),
        "case_id": case.case_id,
        "case_origin": case.case_origin,
        "generator_context_fingerprint": fingerprint(case.generator_context),
        "condition_order": order,
        "challenger_condition": challenger_condition,
        "comparator_condition": comparator_condition,
        "condition_call_counts": {
            condition: len(calls[condition]) for condition in order
        },
        "equal_generation_call_count": len(set(map(len, calls.values()))) == 1,
        "condition_vision_ids": {
            condition: visions[condition]["vision_genesis_id"] for condition in order
        },
        "condition_selected_titles": {
            condition: next(
                (
                    world["title"]
                    for world in visions[condition]["product_worlds"]["worlds"]
                    if world["vision_id"]
                    == visions[condition]["judgment"]["selected_vision_id"]
                ),
                "",
            )
            for condition in order
        },
        "generator_identity": generator_identity,
        "judge_identity": judge_identity,
        "judge_independent_provider_claimed": generator_identity != judge_identity,
        "judgment": judgment,
        "preferred_condition": preferred_condition,
        "claim_scope": (
            "same_model_equal_call_machine_preference"
            if preferred_condition == challenger_condition
            else "none"
        ),
        "human_level_creativity_claim_allowed": False,
        "created_at": utc_now(),
    }
    if usage_report is not None:
        provider_usage = usage_report()
        if not isinstance(provider_usage, dict):
            raise ValueError("agenda ablation usage_report must return an object")
        record["provider_usage"] = provider_usage
    benchmark_store.save_agenda_ablation(record)
    return record


def run_agenda_ablation(
    *,
    case: VisionBenchmarkCase,
    ask: Callable[[str, str], Dict[str, Any]],
    judge_ask: Callable[[str, str], Dict[str, Any]],
    vision_root: Path,
    benchmark_store: VisionBenchmarkStore,
    generator_identity: str = "unspecified",
    judge_identity: str = "unspecified",
    usage_report: Optional[Callable[[], Dict[str, Any]]] = None,
    challenger_condition: str = "adaptive",
    comparator_condition: str = "conventional",
) -> Dict[str, Any]:
    supported_conditions = {"adaptive", "frontier", "conventional"}
    if (
        challenger_condition not in supported_conditions
        or comparator_condition not in supported_conditions
        or challenger_condition == comparator_condition
    ):
        raise ValueError("agenda ablation requires two distinct supported conditions")
    attempt = benchmark_store.reserve_agenda_ablation_attempt(
        case=case,
        challenger_condition=challenger_condition,
        comparator_condition=comparator_condition,
    )
    try:
        record = _run_agenda_ablation_once(
            case=case,
            ask=ask,
            judge_ask=judge_ask,
            vision_root=vision_root,
            benchmark_store=benchmark_store,
            generator_identity=generator_identity,
            judge_identity=judge_identity,
            usage_report=usage_report,
            challenger_condition=challenger_condition,
            comparator_condition=comparator_condition,
        )
    except Exception as exc:
        provider_usage = usage_report() if usage_report is not None else None
        benchmark_store.finish_agenda_ablation_attempt(
            attempt,
            status="failed",
            error=f"{type(exc).__name__}: {exc}",
            provider_usage=provider_usage,
        )
        raise
    benchmark_store.finish_agenda_ablation_attempt(
        attempt,
        status="completed",
        ablation_id=record["vision_agenda_ablation_id"],
        provider_usage=record.get("provider_usage"),
    )
    return record


def run_blind_suite(
    *,
    cases: List[VisionBenchmarkCase],
    runs_per_case: int,
    ask: Callable[[str, str], Dict[str, Any]],
    vision_store: VisionStore,
    benchmark_store: VisionBenchmarkStore,
    judge_ask: Callable[[str, str], Dict[str, Any]] = None,
    generator_identity: str = "unspecified",
    judge_identity: str = "unspecified",
    suite_id: str = "",
) -> Dict[str, Any]:
    if not cases:
        raise ValueError("vision benchmark suite requires at least one case")
    if not isinstance(runs_per_case, int) or isinstance(runs_per_case, bool):
        raise ValueError("runs_per_case must be an integer")
    if not 1 <= runs_per_case <= 5:
        raise ValueError("runs_per_case must be between 1 and 5")
    suite_id = suite_id.strip() or f"vision-suite-{fingerprint(utc_now())[:12]}"
    records = []
    for case in cases:
        for run_index in range(1, runs_per_case + 1):
            trial_id = f"{suite_id}:{case.case_id}:{run_index}"
            isolated_vision_store = VisionStore(
                vision_store.root
                / "benchmark-trials"
                / f"trial-{fingerprint(trial_id)[:12]}"
            )
            records.append(
                run_blind_case(
                    case=case,
                    ask=ask,
                    vision_store=isolated_vision_store,
                    benchmark_store=benchmark_store,
                    judge_ask=judge_ask,
                    generator_identity=generator_identity,
                    judge_identity=judge_identity,
                    trial_id=trial_id,
                )
            )
    suite = {
        "vision_benchmark_suite_version": "palamedes-vision-benchmark-suite/1",
        "suite_id": suite_id,
        "case_ids": [case.case_id for case in cases],
        "runs_per_case": runs_per_case,
        "record_ids": [row["vision_benchmark_id"] for row in records],
        "run_count": len(records),
        "pass_count": sum(bool(row["passed"]) for row in records),
        "selected_titles": [row.get("selected_title", "") for row in records],
        "created_at": utc_now(),
    }
    benchmark_store.save_suite(suite)
    return suite
