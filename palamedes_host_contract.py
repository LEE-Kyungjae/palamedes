#!/usr/bin/env python3
import json
from pathlib import Path
from typing import Any, Dict, List


HOST_ACTION_CONTRACT_PATH = Path(__file__).resolve().parent / "spec" / "host-action-contract.json"


def load_host_action_contract_file() -> Dict[str, Any]:
    with HOST_ACTION_CONTRACT_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("host action contract must be a JSON object")
    return payload


def host_action_contract(role: str = "planner") -> Dict[str, Any]:
    payload = load_host_action_contract_file()
    role_profiles = payload.get("role_profiles", {})
    if not isinstance(role_profiles, dict):
        raise ValueError("host action contract role_profiles must be an object")
    profile_name = role_profiles.get(role)
    if not isinstance(profile_name, str) or not profile_name.strip():
        raise ValueError(f"unknown host role: {role}")
    profiles = payload.get("profiles", {})
    if not isinstance(profiles, dict):
        raise ValueError("host action contract profiles must be an object")
    profile = profiles.get(profile_name)
    if not isinstance(profile, dict):
        raise ValueError(f"unknown host profile: {profile_name}")
    capabilities = profile.get("capabilities", [])
    if not isinstance(capabilities, list):
        raise ValueError(f"host profile capabilities must be an array: {profile_name}")
    actions = payload.get("actions", [])
    if not isinstance(actions, list):
        raise ValueError("host action contract actions must be an array")
    capability_names = {str(item).strip() for item in capabilities if str(item).strip()}
    resolved_actions: List[Dict[str, Any]] = []
    allowed_actions: List[str] = []
    for item in actions:
        if not isinstance(item, dict):
            raise ValueError("host action entries must be objects")
        action_name = str(item.get("action", "")).strip()
        if not action_name:
            raise ValueError("host action entries must include action")
        required = item.get("required_capabilities", [])
        if not isinstance(required, list):
            raise ValueError(f"host action required_capabilities must be an array: {action_name}")
        required_capabilities = [str(name).strip() for name in required if str(name).strip()]
        resolved_item = dict(item)
        resolved_item["required_capabilities"] = required_capabilities
        if set(required_capabilities).issubset(capability_names):
            allowed_actions.append(action_name)
        resolved_actions.append(resolved_item)
    return {
        "version": str(payload.get("version", "")).strip(),
        "role": role,
        "profile": profile_name,
        "allowed_actions": list(allowed_actions),
        "capabilities": list(capabilities),
        "actions": resolved_actions,
        "profiles": profiles,
        "role_profiles": role_profiles,
        "capability_catalog": list(payload.get("capabilities", [])),
        "input_schema": dict(payload.get("input_schema", {})),
        "contract_path": str(HOST_ACTION_CONTRACT_PATH),
    }


def allowed_host_actions(role: str) -> List[str]:
    contract = host_action_contract(role)
    return [str(item).strip() for item in contract["allowed_actions"]]


def required_capabilities_for_action(role: str, action: str) -> List[str]:
    normalized_action = str(action).strip()
    contract = host_action_contract(role)
    for item in contract["actions"]:
        if str(item.get("action", "")).strip() == normalized_action:
            return [str(name).strip() for name in item.get("required_capabilities", []) if str(name).strip()]
    raise ValueError(f"unknown host action: {normalized_action}")


def role_has_action_capabilities(role: str, action: str) -> bool:
    contract = host_action_contract(role)
    granted = {str(name).strip() for name in contract["capabilities"] if str(name).strip()}
    required = set(required_capabilities_for_action(role, action))
    return required.issubset(granted)
