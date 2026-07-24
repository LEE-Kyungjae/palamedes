#!/usr/bin/env python3
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = Path(__file__).resolve().parent
MANIFESTS_DIR = SKILLS_ROOT / "manifests"
PROFILES_PATH = SKILLS_ROOT / "profiles.json"
CONTRACT_PATH = PACKAGE_ROOT / "contracts" / "host-action-contract.json"


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON payload must be an object: {path}")
    return payload


def load_host_action_contract(role: str) -> Dict[str, Any]:
    payload = _load_json(CONTRACT_PATH)
    role_profiles = payload.get("role_profiles", {})
    profiles = payload.get("profiles", {})
    actions = payload.get("actions", [])
    if not isinstance(role_profiles, dict) or not isinstance(profiles, dict) or not isinstance(actions, list):
        raise ValueError("invalid host action contract payload")
    profile_name = str(role_profiles.get(role, "")).strip()
    if not profile_name:
        raise ValueError(f"unknown role: {role}")
    profile = profiles.get(profile_name)
    if not isinstance(profile, dict):
        raise ValueError(f"unknown host profile: {profile_name}")
    capabilities = [str(item).strip() for item in profile.get("capabilities", []) if str(item).strip()]
    allowed_actions = [str(item).strip() for item in profile.get("allowed_actions", []) if str(item).strip()]
    return {
        "role": role,
        "profile": profile_name,
        "capabilities": capabilities,
        "allowed_actions": allowed_actions,
        "actions": actions,
    }


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
        raise ValueError("profiles.json must contain a profiles object")
    return {
        str(name).strip(): dict(manifest)
        for name, manifest in profiles.items()
        if str(name).strip() and isinstance(manifest, dict)
    }


def resolve_profile(role: str) -> Dict[str, Any]:
    contract = load_host_action_contract(role)
    profiles = load_profile_manifests()
    profile = profiles.get(contract["profile"])
    if not profile:
        raise ValueError(f"missing profile manifest for {contract['profile']}")
    return {
        "role": contract["role"],
        "profile": contract["profile"],
        "capabilities": contract["capabilities"],
        "allowed_actions": contract["allowed_actions"],
        "default_skills": [str(item).strip() for item in profile.get("default_skills", []) if str(item).strip()],
    }


def resolve_skill_assignment(
    role: str,
    *,
    desired_skills: Optional[List[str]] = None,
    disabled_skills: Optional[List[str]] = None,
) -> Dict[str, Any]:
    profile = resolve_profile(role)
    manifests = load_skill_manifests()
    desired = [str(item).strip() for item in (desired_skills or profile["default_skills"]) if str(item).strip()]
    disabled = {str(item).strip() for item in (disabled_skills or []) if str(item).strip()}
    granted = {str(item).strip() for item in profile["capabilities"] if str(item).strip()}
    actual: List[str] = []
    omitted: List[Dict[str, str]] = []

    for skill_name in desired:
        manifest = manifests.get(skill_name)
        if not manifest:
            omitted.append({"name": skill_name, "reason": "missing_manifest"})
            continue
        if skill_name in disabled:
            omitted.append({"name": skill_name, "reason": "disabled_by_runtime"})
            continue
        required = {
            str(item).strip()
            for item in manifest.get("depends_on_capabilities", [])
            if str(item).strip()
        }
        if not required.issubset(granted):
            omitted.append({"name": skill_name, "reason": "missing_capability"})
            continue
        actual.append(skill_name)

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
