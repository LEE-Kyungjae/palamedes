#!/usr/bin/env python3
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from palamedes_host_contract import host_action_contract


ROOT = Path(__file__).resolve().parent
MANIFESTS_DIR = ROOT / "manifests"
PROFILES_PATH = ROOT / "profiles.json"


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON payload must be an object: {path}")
    return payload


def load_skill_manifest(name: str) -> Dict[str, Any]:
    manifest = _load_json(MANIFESTS_DIR / f"{name}.json")
    if str(manifest.get("name", "")).strip() != name:
        raise ValueError(f"skill manifest name mismatch: {name}")
    return manifest


def load_skill_manifests() -> Dict[str, Dict[str, Any]]:
    manifests: Dict[str, Dict[str, Any]] = {}
    for path in sorted(MANIFESTS_DIR.glob("*.json")):
        manifest = _load_json(path)
        name = str(manifest.get("name", "")).strip()
        if not name:
            raise ValueError(f"skill manifest missing name: {path}")
        manifests[name] = manifest
    return manifests


def load_profile_manifests() -> Dict[str, Dict[str, Any]]:
    payload = _load_json(PROFILES_PATH)
    profiles = payload.get("profiles", {})
    if not isinstance(profiles, dict):
        raise ValueError("profiles.json must contain an object at profiles")
    return {
        str(name).strip(): dict(manifest)
        for name, manifest in profiles.items()
        if str(name).strip() and isinstance(manifest, dict)
    }


def resolve_profile(role: str) -> Dict[str, Any]:
    contract = host_action_contract(role)
    profile_name = str(contract.get("profile", "")).strip()
    profiles = load_profile_manifests()
    profile = profiles.get(profile_name)
    if not profile:
        raise ValueError(f"missing profile manifest for host profile: {profile_name}")
    return {
        "role": role,
        "profile": profile_name,
        "capabilities": list(contract.get("capabilities", [])),
        "allowed_actions": list(contract.get("allowed_actions", [])),
        "default_skills": list(profile.get("default_skills", [])),
    }


def resolve_skill_assignment(
    role: str,
    *,
    desired_skills: Optional[List[str]] = None,
    disabled_skills: Optional[List[str]] = None,
) -> Dict[str, Any]:
    profile = resolve_profile(role)
    manifests = load_skill_manifests()
    desired = desired_skills or list(profile["default_skills"])
    disabled = {str(item).strip() for item in (disabled_skills or []) if str(item).strip()}
    granted_capabilities = {str(item).strip() for item in profile["capabilities"] if str(item).strip()}
    actual: List[str] = []
    omitted: List[Dict[str, str]] = []

    for skill_name in desired:
        normalized_name = str(skill_name).strip()
        if not normalized_name:
            continue
        manifest = manifests.get(normalized_name)
        if not manifest:
            omitted.append({"name": normalized_name, "reason": "missing_manifest"})
            continue
        if normalized_name in disabled:
            omitted.append({"name": normalized_name, "reason": "disabled_by_runtime"})
            continue
        required = {
            str(item).strip()
            for item in manifest.get("depends_on_capabilities", [])
            if str(item).strip()
        }
        if not required.issubset(granted_capabilities):
            omitted.append({"name": normalized_name, "reason": "missing_capability"})
            continue
        actual.append(normalized_name)

    return {
        "role": profile["role"],
        "profile": profile["profile"],
        "capabilities": profile["capabilities"],
        "allowed_actions": profile["allowed_actions"],
        "desired_skills": desired,
        "actual_skills": actual,
        "disabled_skills": omitted,
    }


def build_runtime_session(
    role: str,
    *,
    desired_skills: Optional[List[str]] = None,
    disabled_skills: Optional[List[str]] = None,
) -> Dict[str, Any]:
    assignment = resolve_skill_assignment(
        role,
        desired_skills=desired_skills,
        disabled_skills=disabled_skills,
    )
    return {
        "role": assignment["role"],
        "profile": assignment["profile"],
        "desired_skills": assignment["desired_skills"],
        "actual_skills": assignment["actual_skills"],
        "disabled_skills": assignment["disabled_skills"],
    }


if __name__ == "__main__":
    print(json.dumps(build_runtime_session("planner"), indent=2))
