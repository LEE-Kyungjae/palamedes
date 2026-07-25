#!/usr/bin/env python3
"""Observation-surface and coverage epistemics for bounded world claims."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from palamedes_observe import fingerprint, utc_now


EVIDENCE_LAYERS = {"expression", "exposure", "behavior", "outcome", "mixed"}
GENERALITY_LEVELS = {"existence_only", "bounded_group", "population"}
BASE_RATE_SURFACE_TYPES = {
    "analytics_baseline",
    "random_sample",
    "official_statistics",
}


class EpistemicStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.surfaces_root = root / "surfaces"
        self.coverage_path = root / "coverage.json"

    @staticmethod
    def _save(root: Path, record_id: str, payload: Dict[str, Any]) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{record_id}.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return path

    def save_surface(self, surface: Dict[str, Any]) -> Path:
        return self._save(self.surfaces_root, surface["surface_id"], surface)

    def save_coverage(self, coverage: Dict[str, Any]) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        temporary = self.coverage_path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.coverage_path)
        return self.coverage_path

    def active_surfaces(self) -> List[Dict[str, Any]]:
        records = []
        if not self.surfaces_root.is_dir():
            return records
        for path in sorted(self.surfaces_root.glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict):
                records.append(payload)
        return records

    def load_coverage(self) -> Dict[str, Any]:
        if not self.coverage_path.is_file():
            return {
                "coverage_is_complete": False,
                "ambient_baseline_available": False,
                "general_population_inference_allowed": False,
                "surface_type_counts": {},
                "missing_populations": [],
            }
        try:
            payload = json.loads(self.coverage_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {
                "coverage_is_complete": False,
                "ambient_baseline_available": False,
                "general_population_inference_allowed": False,
                "surface_type_counts": {},
                "missing_populations": [],
                "recovered_from_invalid_coverage": True,
            }
        return payload if isinstance(payload, dict) else {}


def derive_observation_surfaces(context: Dict[str, Any]) -> List[Dict[str, Any]]:
    observed_at = context["observed_at"]
    surfaces = []
    for item in context.get("documents", []):
        source_id = f"document:{item['path']}@{item['content_sha256']}"
        surfaces.append(
            _surface(
                source_id=source_id,
                origin_id=source_id,
                surface_type="internal_document",
                collection_method="bounded_primary_document_whitelist",
                selection_process=[
                    "team authored or selected the document",
                    "observer reads named primary files and a bounded docs subset",
                ],
                observed_population="documented product and organizational claims",
                missing_population=[
                    "actual user behavior",
                    "silent users and non-users",
                    "undocumented work and disagreement",
                ],
                visibility_bias=(
                    "intentional and legible decisions are more visible than lived use"
                ),
                observed_at=observed_at,
            )
        )
    for item in context.get("reference_root", {}).get("repositories", []):
        if "knowledge_document" not in item:
            continue
        source_id = f"ref:{item['name']}@{item.get('head', '')}"
        surfaces.append(
            _surface(
                source_id=source_id,
                origin_id=source_id,
                surface_type="curated_reference",
                collection_method="central_ref_first_eight_representative_readmes",
                selection_process=[
                    "a person or prior process curated the repository",
                    "repository authors chose what the README presents",
                    "observer applies an alphabetical and byte bound",
                ],
                observed_population="documented patterns in selected repositories",
                missing_population=[
                    "uncurated repositories",
                    "failed or undocumented implementations",
                    "ordinary users outside the repository audience",
                ],
                visibility_bias=(
                    "successful, publishable, and well-documented patterns are overvisible"
                ),
                observed_at=observed_at,
            )
        )
    for item in context.get("experiences", []):
        source_id = item.get("experience_id")
        if not source_id:
            continue
        surfaces.append(
            _surface(
                source_id=source_id,
                origin_id=source_id,
                surface_type="mission_outcome",
                collection_method=item.get(
                    "evidence_source_type", "implementer_claim"
                ),
                selection_process=[
                    "an implemented mission produced a returned outcome",
                    "the reporting party selected the observation wording",
                ],
                observed_population="the bounded mission and its observed result",
                missing_population=[
                    "independent attribution",
                    "unmeasured downstream effects",
                    "people outside the probe",
                ],
                visibility_bias="implemented and reported effects are more visible",
                observed_at=observed_at,
            )
        )
    for item in context.get("declared_surfaces", []):
        required = (
            "source_id",
            "surface_type",
            "collection_method",
            "selection_process",
            "observed_population",
            "missing_population",
            "visibility_bias",
            "origin_id",
        )
        if not isinstance(item, dict) or any(field not in item for field in required):
            raise ValueError("declared observation surface is incomplete")
        if not isinstance(item["selection_process"], list) or not isinstance(
            item["missing_population"], list
        ):
            raise ValueError("declared surface populations and selection must be arrays")
        surfaces.append(
            _surface(
                source_id=str(item["source_id"]).strip(),
                origin_id=str(item["origin_id"]).strip(),
                surface_type=str(item["surface_type"]).strip(),
                collection_method=str(item["collection_method"]).strip(),
                selection_process=[
                    str(value).strip() for value in item["selection_process"]
                ],
                observed_population=str(item["observed_population"]).strip(),
                missing_population=[
                    str(value).strip() for value in item["missing_population"]
                ],
                visibility_bias=str(item["visibility_bias"]).strip(),
                observed_at=observed_at,
            )
        )
    return surfaces


def _surface(
    *,
    source_id: str,
    origin_id: str,
    surface_type: str,
    collection_method: str,
    selection_process: List[str],
    observed_population: str,
    missing_population: List[str],
    visibility_bias: str,
    observed_at: str,
) -> Dict[str, Any]:
    identity = {
        "source_id": source_id,
        "surface_type": surface_type,
        "collection_method": collection_method,
        "origin_id": origin_id,
    }
    return {
        "surface_version": "palamedes-observation-surface/1",
        "surface_id": f"surface-{fingerprint(identity)[:12]}",
        "source_id": source_id,
        "origin_id": origin_id,
        "surface_type": surface_type,
        "collection_method": collection_method,
        "selection_process": selection_process,
        "observed_population": observed_population,
        "missing_population": missing_population,
        "visibility_bias": visibility_bias,
        "observed_at": observed_at,
    }


def persist_observation_epistemics(
    *,
    store: EpistemicStore,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    surfaces = derive_observation_surfaces(context)
    for surface in surfaces:
        store.save_surface(surface)
    counts: Dict[str, int] = {}
    missing = set()
    for surface in store.active_surfaces():
        surface_type = surface["surface_type"]
        counts[surface_type] = counts.get(surface_type, 0) + 1
        missing.update(surface.get("missing_population", []))
    total = sum(counts.values())
    origins: Dict[str, List[str]] = {}
    for surface in store.active_surfaces():
        origins.setdefault(surface["origin_id"], []).append(surface["surface_id"])
    overrepresented = sorted(
        surface_type
        for surface_type, count in counts.items()
        if total and count / total > 0.5
    )
    has_ambient_baseline = any(
        surface_type in {"random_sample", "analytics_baseline"}
        for surface_type in counts
    )
    coverage = {
        "coverage_version": "palamedes-observation-coverage/1",
        "updated_at": utc_now(),
        "surface_type_counts": counts,
        "overrepresented_surface_types": overrepresented,
        "missing_populations": sorted(missing),
        "ambient_baseline_available": has_ambient_baseline,
        "independent_origin_count": len(origins),
        "duplicate_origin_groups": [
            sorted(surface_ids)
            for surface_ids in origins.values()
            if len(surface_ids) > 1
        ],
        "general_population_inference_allowed": has_ambient_baseline,
        "coverage_is_complete": False,
    }
    store.save_coverage(coverage)
    return {
        "surfaces": surfaces,
        "surface_by_source": {
            surface["source_id"]: surface for surface in surfaces
        },
        "coverage": coverage,
    }


def validate_epistemic_profile(
    profile: Dict[str, Any],
    *,
    source_ids: List[str],
    surface_by_source: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    if not isinstance(profile, dict):
        raise ValueError("knowledge claim requires epistemic_profile")
    evidence_layer = profile.get("evidence_layer")
    generality = profile.get("generality")
    if evidence_layer not in EVIDENCE_LAYERS:
        raise ValueError("epistemic evidence_layer is invalid")
    if generality not in GENERALITY_LEVELS:
        raise ValueError("epistemic generality is invalid")
    normalized = {
        "evidence_layer": evidence_layer,
        "generality": generality,
    }
    for field in (
        "salience",
        "representativeness",
        "relevance",
        "independence",
        "persistence",
        "behavioral_support",
    ):
        value = profile.get(field)
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or not 0 <= value <= 100
        ):
            raise ValueError(f"epistemic {field} must be 0-100")
        normalized[field] = value
    base_rate = profile.get("base_rate")
    if not isinstance(base_rate, dict):
        raise ValueError("epistemic base_rate must be an object")
    available = base_rate.get("available")
    if not isinstance(available, bool):
        raise ValueError("epistemic base_rate.available must be boolean")
    denominator = base_rate.get("denominator")
    observations = base_rate.get("observations")
    if (
        not isinstance(denominator, int)
        or isinstance(denominator, bool)
        or denominator < 0
        or not isinstance(observations, int)
        or isinstance(observations, bool)
        or observations < 0
        or observations > denominator
    ):
        raise ValueError("epistemic base_rate counts are invalid")
    if available != (denominator > 0):
        raise ValueError("base_rate availability must match its denominator")
    normalized["base_rate"] = {
        "available": available,
        "observations": observations,
        "denominator": denominator,
        "window": str(base_rate.get("window", "")).strip(),
    }
    base_rate_source_ids = base_rate.get("source_ids", [])
    if not isinstance(base_rate_source_ids, list) or not all(
        isinstance(item, str) and item.strip() for item in base_rate_source_ids
    ):
        raise ValueError("epistemic base_rate.source_ids must be an array")
    if not set(base_rate_source_ids).issubset(source_ids):
        raise ValueError("base-rate source must also ground the claim")
    base_rate_surfaces = [
        surface_by_source[item]
        for item in base_rate_source_ids
        if item in surface_by_source
    ]
    base_rate_verified = bool(base_rate_source_ids) and all(
        surface["surface_type"] in BASE_RATE_SURFACE_TYPES
        for surface in base_rate_surfaces
    ) and len(base_rate_surfaces) == len(base_rate_source_ids)
    if available and not base_rate_verified:
        raise ValueError(
            "base rate requires analytics, random-sample, or official-statistics surface"
        )
    if not available and base_rate_source_ids:
        raise ValueError("unavailable base rate cannot cite base-rate sources")
    normalized["base_rate"]["source_ids"] = base_rate_source_ids
    normalized["base_rate"]["verified"] = base_rate_verified
    allowed = str(profile.get("allowed_inference", "")).strip()
    forbidden = profile.get("forbidden_inferences")
    if not allowed or not isinstance(forbidden, list) or not all(
        isinstance(item, str) and item.strip() for item in forbidden
    ):
        raise ValueError("epistemic inference boundary is incomplete")
    normalized["allowed_inference"] = allowed
    normalized["forbidden_inferences"] = [item.strip() for item in forbidden]
    surface_ids = []
    for source_id in source_ids:
        surface = surface_by_source.get(source_id)
        if surface is not None:
            surface_ids.append(surface["surface_id"])
    normalized["observation_surface_ids"] = surface_ids
    origins = {
        surface_by_source[source_id]["origin_id"]
        for source_id in source_ids
        if source_id in surface_by_source
    }
    independence_ceiling = (
        0
        if not source_ids
        else 50
        if len(source_ids) == 1
        else round(100 * len(origins) / len(source_ids))
    )
    if normalized["independence"] > independence_ceiling:
        raise ValueError(
            "claimed independence exceeds distinct origin lineage"
        )
    normalized["independence_ceiling"] = independence_ceiling
    if generality == "population" and (
        normalized["representativeness"] < 60
        or not normalized["base_rate"]["available"]
        or not normalized["base_rate"]["verified"]
        or evidence_layer in {"expression", "exposure"}
    ):
        raise ValueError(
            "population claim requires representative base-rate behavior or outcome evidence"
        )
    if generality == "bounded_group" and not surface_ids:
        raise ValueError("bounded-group claim requires an observation surface")
    return normalized
