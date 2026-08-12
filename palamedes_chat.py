#!/usr/bin/env python3
"""Interactive, local-first Palamedes terminal chat."""

from __future__ import annotations

import json
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Protocol, TextIO, Tuple


DEFAULT_OPENAI_MODEL = "gpt-5.6"
DEFAULT_OPENROUTER_MODEL = "openai/gpt-5.1"
CHAT_COMMANDS = {
    "/think": "Explore the missing mode of thought before recommending action.",
    "/challenge": "Attack the strongest assumptions in the current direction and state what evidence would change the conclusion.",
    "/research": "Identify the minimum external evidence needed next. Do not pretend that uncollected evidence exists.",
    "/mission": "Produce a structured mission draft.",
}
MISSION_REQUIRED_FIELDS = (
    "mission",
    "rationale",
    "success_metric",
    "evidence",
    "hypotheses",
    "falsifiers",
    "non_goals",
    "constraints",
    "next_probe",
    "planner_brief",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ChatProvider(Protocol):
    provider_name: str
    model: str

    def stream(self, messages: List[Dict[str, str]]) -> Iterable[str]:
        ...


def _sse_events(response: Any) -> Iterable[Dict[str, Any]]:
    for raw_line in response:
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if not data or data == "[DONE]":
            continue
        try:
            event = json.loads(data)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            yield event


def _open(request: urllib.request.Request, provider_name: str) -> Any:
    try:
        return urllib.request.urlopen(request, timeout=180)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{provider_name} request failed ({exc.code}): {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{provider_name} connection failed: {exc.reason}") from exc


def _normalize_token_usage(usage: Dict[str, Any]) -> Dict[str, int]:
    aliases = {
        "input_tokens": ("input_tokens", "prompt_tokens"),
        "output_tokens": ("output_tokens", "completion_tokens"),
        "cached_input_tokens": ("cached_input_tokens",),
        "total_tokens": ("total_tokens",),
    }
    normalized: Dict[str, int] = {}
    for target, candidates in aliases.items():
        for candidate in candidates:
            value = usage.get(candidate)
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                normalized[target] = value
                break
    if "total_tokens" not in normalized and {
        "input_tokens",
        "output_tokens",
    } <= normalized.keys():
        normalized["total_tokens"] = (
            normalized["input_tokens"] + normalized["output_tokens"]
        )
    return normalized


def _provider_usage_summary(
    provider: Any, role_usage: List[Dict[str, Any]]
) -> Dict[str, Any]:
    totals: Dict[str, int] = {}
    for row in role_usage:
        for key, value in row.get("usage", {}).items():
            totals[key] = totals.get(key, 0) + value
    return {
        "provider": provider.provider_name,
        "model": provider.model,
        "attempted_calls": len(role_usage),
        "metered_calls": sum(
            row.get("custody") == "provider_reported" for row in role_usage
        ),
        "unmetered_calls": sum(
            row.get("custody") == "unmetered" for row in role_usage
        ),
        "totals": totals,
        "roles": role_usage,
    }


def _capture_provider_usage(provider: Any, role: str) -> Dict[str, Any]:
    usage = getattr(provider, "last_usage", None)
    row = {
        "role": role,
        "custody": (
            "provider_reported"
            if isinstance(usage, dict) and usage
            else "unmetered"
        ),
        "usage": (
            _normalize_token_usage(usage)
            if isinstance(usage, dict) and usage
            else {}
        ),
    }
    json_custody = getattr(provider, "last_json_custody", None)
    if isinstance(json_custody, dict):
        row["json_custody"] = dict(json_custody)
    return row


@dataclass
class OpenRouterChatProvider:
    model: str = DEFAULT_OPENROUTER_MODEL
    base_url: str = "https://openrouter.ai/api/v1"
    provider_name: str = "openrouter"
    last_usage: Optional[Dict[str, int]] = None

    def stream(self, messages: List[Dict[str, str]]) -> Iterable[str]:
        self.last_usage = None
        api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OpenRouter requires OPENROUTER_API_KEY")
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        request = urllib.request.Request(
            f"{self.base_url.rstrip('/')}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.environ.get(
                    "PALAMEDES_OPENROUTER_SITE_URL",
                    "https://github.com/LEE-Kyungjae/Palamedes",
                ),
                "X-Title": os.environ.get("PALAMEDES_OPENROUTER_APP_NAME", "Palamedes"),
            },
            method="POST",
        )
        with _open(request, "OpenRouter") as response:
            for event in _sse_events(response):
                usage = event.get("usage")
                if isinstance(usage, dict):
                    self.last_usage = _normalize_token_usage(usage)
                choices = event.get("choices", [])
                if not choices:
                    continue
                delta = choices[0].get("delta", {})
                content = delta.get("content", "")
                if isinstance(content, str) and content:
                    yield content


@dataclass
class OpenAIResponsesChatProvider:
    model: str = DEFAULT_OPENAI_MODEL
    base_url: str = "https://api.openai.com/v1"
    provider_name: str = "openai"
    last_usage: Optional[Dict[str, int]] = None

    def stream(self, messages: List[Dict[str, str]]) -> Iterable[str]:
        self.last_usage = None
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OpenAI requires OPENAI_API_KEY")
        instructions = "\n\n".join(
            item["content"] for item in messages if item.get("role") == "system"
        )
        input_items = [
            {"role": item["role"], "content": item["content"]}
            for item in messages
            if item.get("role") in {"user", "assistant"}
        ]
        payload = {
            "model": self.model,
            "instructions": instructions,
            "input": input_items,
            "stream": True,
            "store": False,
        }
        request = urllib.request.Request(
            f"{self.base_url.rstrip('/')}/responses",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with _open(request, "OpenAI") as response:
            for event in _sse_events(response):
                if event.get("type") == "response.completed":
                    response_payload = event.get("response", {})
                    usage = (
                        response_payload.get("usage")
                        if isinstance(response_payload, dict)
                        else None
                    )
                    if isinstance(usage, dict):
                        self.last_usage = _normalize_token_usage(usage)
                if event.get("type") == "response.output_text.delta":
                    delta = event.get("delta", "")
                    if isinstance(delta, str) and delta:
                        yield delta


@dataclass
class CodexCliChatProvider:
    model: str = "configured-default"
    provider_name: str = "codex"
    timeout_seconds: int = 300
    last_usage: Optional[Dict[str, int]] = None

    def stream(self, messages: List[Dict[str, str]]) -> Iterable[str]:
        self.last_usage = None
        executable = shutil.which("codex")
        if not executable:
            raise RuntimeError("Codex CLI is not installed or not available on PATH")
        prompt = "\n\n".join(
            f"{item.get('role', 'user').upper()}:\n{item.get('content', '')}"
            for item in messages
        )
        prompt += (
            "\n\nReturn only the requested final answer. Do not inspect the filesystem, "
            "run commands, edit files, or expand beyond the supplied bounded context."
        )
        command = [
            executable,
            "exec",
            "-",
            "--ephemeral",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            "--color",
            "never",
            "--json",
        ]
        if self.model != "configured-default":
            command.extend(["--model", self.model])
        try:
            with tempfile.TemporaryDirectory(prefix="palamedes-codex-") as tempdir:
                result = subprocess.run(
                    command,
                    cwd=tempdir,
                    input=prompt,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    check=False,
                )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(
                f"Codex CLI timed out after {self.timeout_seconds} seconds"
            ) from exc
        if result.returncode != 0:
            detail = result.stderr.strip()[-4000:] or "no diagnostic output"
            raise RuntimeError(
                f"Codex CLI failed with exit code {result.returncode}: {detail}"
            )
        final_text = ""
        usage: Optional[Dict[str, int]] = None
        for line in result.stdout.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            if event.get("type") == "item.completed":
                item = event.get("item", {})
                if (
                    isinstance(item, dict)
                    and item.get("type") == "agent_message"
                    and isinstance(item.get("text"), str)
                ):
                    final_text = item["text"]
            if event.get("type") == "turn.completed" and isinstance(
                event.get("usage"), dict
            ):
                usage = {
                    key: int(value)
                    for key, value in event["usage"].items()
                    if isinstance(value, int) and value >= 0
                }
        if not final_text.strip():
            raise RuntimeError("Codex CLI returned no final agent message")
        self.last_usage = usage
        yield final_text


def provider_from_config(name: str, model: str = "") -> ChatProvider:
    if name == "openrouter":
        return OpenRouterChatProvider(
            model=model
            or os.environ.get("PALAMEDES_OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL)
        )
    if name == "openai":
        return OpenAIResponsesChatProvider(
            model=model or os.environ.get("PALAMEDES_OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
        )
    if name == "codex":
        return CodexCliChatProvider(model=model or "configured-default")
    raise ValueError("provider must be openrouter, openai, or codex")


def provider_health(name: str) -> Dict[str, Any]:
    if name == "codex":
        available = bool(shutil.which("codex"))
        return {
            "provider": name,
            "status": "ok" if available else "unavailable",
            "credential_hint": "run codex login if the CLI is not authenticated",
            "cli_available": available,
        }
    env_name = "OPENROUTER_API_KEY" if name == "openrouter" else "OPENAI_API_KEY"
    key_set = bool(os.environ.get(env_name, "").strip())
    return {
        "provider": name,
        "status": "ok" if key_set else "unavailable",
        "api_key_env": env_name,
        "api_key_set": key_set,
        "credential_hint": f"set {env_name}",
    }


class ChatSessionStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def path(self, session_id: str) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", session_id):
            raise ValueError(
                "session ID must be 1-64 letters, numbers, dots, underscores, or hyphens"
            )
        return self.root / f"{session_id}.jsonl"

    def append(self, session_id: str, record: Dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.path(session_id).open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    def load(self, session_id: str) -> List[Dict[str, Any]]:
        path = self.path(session_id)
        if not path.is_file():
            return []
        records = []
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                records.append(record)
        return records

    def list_sessions(self) -> List[str]:
        if not self.root.is_dir():
            return []
        return [path.stem for path in sorted(self.root.glob("*.jsonl"))]


class MissionStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.handoff_root = root / "handoffs"
        self.outcomes_path = root / "outcomes.jsonl"
        self.outcome_interpretations_path = root / "outcome-interpretations.jsonl"
        self.outcome_gates_path = root / "outcome-gates.jsonl"

    def contract_path(self, mission_id: str) -> Path:
        if not re.fullmatch(r"mission-[a-f0-9]{12}", mission_id):
            raise ValueError("invalid mission ID")
        return self.root / f"{mission_id}.json"

    def save_contract(self, contract: Dict[str, Any]) -> Path:
        path = self.contract_path(contract["mission_id"])
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return path

    def load_contract(self, mission_id: str) -> Dict[str, Any]:
        path = self.contract_path(mission_id)
        if not path.is_file():
            raise ValueError(f"mission contract not found: {mission_id}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("mission contract must be an object")
        return payload

    def contracts(self) -> List[Dict[str, Any]]:
        if not self.root.is_dir():
            return []
        contracts = []
        for path in sorted(self.root.glob("mission-*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict):
                contracts.append(payload)
        return contracts

    def save_handoff(self, handoff: Dict[str, Any]) -> Path:
        self.handoff_root.mkdir(parents=True, exist_ok=True)
        path = self.handoff_root / f"{handoff['handoff_id']}.json"
        path.write_text(
            json.dumps(handoff, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path

    def load_handoff(self, handoff_id: str) -> Dict[str, Any]:
        if not re.fullmatch(r"handoff-[a-f0-9]{12}", handoff_id):
            raise ValueError("invalid handoff ID")
        path = self.handoff_root / f"{handoff_id}.json"
        if not path.is_file():
            raise ValueError(f"handoff not found: {handoff_id}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("handoff payload must be an object")
        return payload

    def load_handoff_for_mission(self, mission_id: str) -> Dict[str, Any]:
        if not re.fullmatch(r"mission-[a-f0-9]{12}", mission_id):
            raise ValueError("invalid mission ID")
        return self.load_handoff(f"handoff-{mission_id[8:]}")

    def append_outcome(self, outcome: Dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.outcomes_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(outcome, ensure_ascii=False, sort_keys=True) + "\n")

    def outcomes(self) -> List[Dict[str, Any]]:
        if not self.outcomes_path.is_file():
            return []
        records = []
        for line in self.outcomes_path.read_text(encoding="utf-8").splitlines():
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                records.append(payload)
        return records

    def vision_investment_summary(self, vision_genesis_id: str) -> Dict[str, Any]:
        mission_ids = {
            row.get("mission_id")
            for row in self.contracts()
            if row.get("vision_lineage", {}).get("vision_genesis_id")
            == vision_genesis_id
        }
        summary = {
            "engineering_days": 0.0,
            "ai_cost": 0.0,
            "input_tokens": 0,
            "output_tokens": 0,
            "monthly_infrastructure_peak": 0.0,
            "measured_outcome_count": 0,
            "missing_measurement_count": 0,
        }
        for outcome in self.outcomes():
            if outcome.get("mission_contract_id") not in mission_ids:
                continue
            actual = outcome.get("actual_investment")
            if not isinstance(actual, dict):
                summary["missing_measurement_count"] += 1
                continue
            summary["measured_outcome_count"] += 1
            for field in ("engineering_days", "ai_cost"):
                summary[field] += float(actual.get(field, 0))
            for field in ("input_tokens", "output_tokens"):
                summary[field] += int(actual.get(field, 0))
            summary["monthly_infrastructure_peak"] = max(
                summary["monthly_infrastructure_peak"],
                float(actual.get("monthly_infrastructure", 0)),
            )
        return summary

    def append_outcome_interpretation(self, interpretation: Dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.outcome_interpretations_path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(interpretation, ensure_ascii=False, sort_keys=True) + "\n"
            )

    def outcome_interpretations(self) -> List[Dict[str, Any]]:
        if not self.outcome_interpretations_path.is_file():
            return []
        records = []
        for line in self.outcome_interpretations_path.read_text(
            encoding="utf-8"
        ).splitlines():
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                records.append(payload)
        return records

    def append_outcome_gate(self, gate: Dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.outcome_gates_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(gate, ensure_ascii=False, sort_keys=True) + "\n")

    def open_outcome_gates(self) -> List[Dict[str, Any]]:
        if not self.outcome_gates_path.is_file():
            return []
        latest: Dict[str, Dict[str, Any]] = {}
        for line in self.outcome_gates_path.read_text(encoding="utf-8").splitlines():
            try:
                gate = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(gate, dict) and isinstance(gate.get("gate_id"), str):
                latest[gate["gate_id"]] = gate
        return [gate for gate in latest.values() if gate.get("status") == "open"]

    def outcome_gate_scope_keys(self, gate: Dict[str, Any]) -> set[str]:
        explicit = gate.get("scope_keys")
        if isinstance(explicit, list):
            keys = {
                str(item).strip()
                for item in explicit
                if isinstance(item, str) and item.strip()
            }
            if keys:
                return keys
        surface = str(gate.get("surface_key", "")).strip()
        if not surface:
            outcome_id = str(gate.get("outcome_id", "")).strip()
            for interpretation in reversed(self.outcome_interpretations()):
                if interpretation.get("outcome_id") == outcome_id:
                    surface = str(interpretation.get("surface_key", "")).strip()
                    if surface:
                        break
        if not surface:
            mission_id = str(gate.get("mission_contract_id", "")).strip()
            try:
                surface = str(self.load_contract(mission_id).get("surface_key", "")).strip()
            except (OSError, ValueError, json.JSONDecodeError):
                surface = ""
            if not surface and mission_id:
                return {f"mission:{mission_id}"}
        return {f"surface:{surface}"} if surface else set()

    def external_evidence_wait_gate(self) -> Optional[Dict[str, Any]]:
        gates = [
            gate
            for gate in self.open_outcome_gates()
            if gate.get("gate_kind") == "external_evidence"
            and gate.get("authorized_local_actions") == []
        ]
        return gates[-1] if gates else None


class CognitionCycleStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def path(self, cycle_id: str) -> Path:
        if not re.fullmatch(r"cycle-[a-f0-9]{12}", cycle_id):
            raise ValueError("invalid cognition cycle ID")
        return self.root / f"{cycle_id}.json"

    def save(self, cycle: Dict[str, Any]) -> Path:
        path = self.path(cycle["cognition_cycle_id"])
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(cycle, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return path

    def load(self, cycle_id: str) -> Dict[str, Any]:
        path = self.path(cycle_id)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("cognition cycle must be an object")
        return payload


def _fingerprint(payload: Dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _provider_json(
    provider: ChatProvider,
    *,
    system: str,
    prompt: str,
) -> Dict[str, Any]:
    provider.last_json_custody = None
    raw = "".join(
        provider.stream(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ]
        )
    )
    try:
        payload, custody = _extract_json_object_with_custody(raw)
    except ProviderJSONError as exc:
        provider.last_json_custody = exc.custody
        raise
    provider.last_json_custody = custody
    return _normalize_provider_scalars(payload)


def _normalize_provider_scalars(value: Any, key: str = "") -> Any:
    """Repair only unambiguous JSON scalar type drift from model providers."""
    if isinstance(value, dict):
        return {
            item_key: _normalize_provider_scalars(item_value, item_key)
            for item_key, item_value in value.items()
        }
    if isinstance(value, list):
        return [_normalize_provider_scalars(item, key) for item in value]
    integer_fields = {
        "confidence",
        "uncertainty",
        "exploration_value",
        "expected_information_gain",
        "scope_risk",
        "call_budget",
    }
    boolean_fields = {"followup_required", "disqualifying"}
    if key in integer_fields and isinstance(value, str) and re.fullmatch(r"\d{1,3}", value.strip()):
        return int(value.strip())
    if key in boolean_fields and isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "false"}:
            return lowered == "true"
    return value


def _non_empty_string_array(payload: Dict[str, Any], field: str) -> List[str]:
    value = payload.get(field)
    if not isinstance(value, list) or not value or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ValueError(f"{field} must be a non-empty string array")
    return [item.strip() for item in value]


def _role_artifact(
    *,
    role: str,
    call_index: int,
    prompt: str,
    output: Dict[str, Any],
    provider: ChatProvider,
    run_id: str = "",
    started_at: str = "",
    duration_ms: Optional[int] = None,
) -> Dict[str, Any]:
    artifact = {
        "role": role,
        "call_index": call_index,
        "provider": provider.provider_name,
        "model": provider.model,
        "completed_at": utc_now(),
        "prompt_fingerprint": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "output_fingerprint": _fingerprint(output),
        "output": output,
    }
    if run_id:
        artifact["run_id"] = run_id
    if started_at:
        artifact["started_at"] = started_at
    if duration_ms is not None:
        artifact["duration_ms"] = duration_ms
    usage = getattr(provider, "last_usage", None)
    if isinstance(usage, dict) and usage:
        artifact["provider_usage"] = _normalize_token_usage(usage)
        artifact["usage_custody"] = "provider_reported"
    else:
        artifact["usage_custody"] = "unmetered"
    return artifact


def _cognition_usage_summary(
    provider: ChatProvider, artifacts: List[Dict[str, Any]]
) -> Dict[str, Any]:
    roles = []
    for artifact in artifacts:
        usage = artifact.get("provider_usage")
        custody = str(artifact.get("usage_custody", "unmetered"))
        roles.append(
            {
                "role": artifact.get("role", ""),
                "custody": custody,
                "usage": dict(usage) if isinstance(usage, dict) else {},
                "duration_ms": artifact.get("duration_ms"),
                "checkpoint_reused": bool(artifact.get("checkpoint_reused", False)),
            }
        )
    return _provider_usage_summary(provider, roles)


def _cycle_paid_artifacts(cycle: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return every artifact this cycle paid a provider call for.

    Kept and rejected artifacts each cost exactly one call, possibly during an
    earlier attempt of the same cycle, so both survive checkpoint reuse and
    schema retries. Usage reporting and budget accounting must agree on this
    set or the enforced ceiling drifts from the reported cost.
    """
    return list(cycle.get("artifacts", [])) + list(cycle.get("rejected_artifacts", []))


def _cycle_budget_spent(cycle: Dict[str, Any]) -> Tuple[int, int]:
    """Return provider calls and tokens already paid for by this cycle."""
    spent_calls = 0
    spent_tokens = 0
    for artifact in _cycle_paid_artifacts(cycle):
        spent_calls += 1
        usage = artifact.get("provider_usage")
        if isinstance(usage, dict):
            total = usage.get("total_tokens")
            if isinstance(total, int) and not isinstance(total, bool):
                spent_tokens += total
    return spent_calls, spent_tokens


def _budget_overrun_message(
    cycle: Dict[str, Any], budget: Dict[str, Any]
) -> Optional[str]:
    """Describe how far a finished cycle passed its declared preflight ceiling.

    The pre-call gate can refuse to start a role once the ceiling is spent, but
    it cannot know what a permitted role will cost, so the final total may still
    exceed the declared budget and must be disclosed rather than hidden.
    """
    spent_calls, spent_tokens = _cycle_budget_spent(cycle)
    overruns = []
    declared_calls = budget.get("provider_calls_max")
    if (
        isinstance(declared_calls, int)
        and not isinstance(declared_calls, bool)
        and spent_calls > declared_calls
    ):
        overruns.append(f"calls {spent_calls}>{declared_calls}")
    declared_tokens = budget.get("token_budget_high")
    if (
        isinstance(declared_tokens, int)
        and not isinstance(declared_tokens, bool)
        and spent_tokens > declared_tokens
    ):
        overruns.append(f"tokens {spent_tokens}>{declared_tokens}")
    if not overruns:
        return None
    return (
        "BUDGET OVERRUN: "
        + "; ".join(overruns)
        + " · the preflight ceiling gates starting a role and cannot cap the "
        "cost of a role already started"
    )


def run_cognition_cycle(
    *,
    provider: ChatProvider,
    palamedes_module: Any,
    context: str,
    cycle_store: CognitionCycleStore,
    available_discovery_ids: Optional[set] = None,
    budget: Optional[Dict[str, Any]] = None,
    retry_feedback: Optional[Dict[str, str]] = None,
    progress: Optional[Callable[[str], None]] = None,
    schema_retry_limit: int = 1,
    resume_cycle_id: str = "",
) -> Dict[str, Any]:
    if not isinstance(schema_retry_limit, int) or isinstance(schema_retry_limit, bool):
        raise ValueError("schema_retry_limit must be an integer")
    if not 0 <= schema_retry_limit <= 1:
        raise ValueError("schema_retry_limit must be 0 or 1")
    available_discovery_ids = available_discovery_ids or set()
    started_at = utc_now()
    current_context_views = _plan_context_views(palamedes_module)
    current_plan_context = current_context_views["strategic"]
    current_path_context = current_context_views["path_dependent"]
    if resume_cycle_id:
        if not re.fullmatch(r"cycle-[0-9a-f]{12}", resume_cycle_id):
            raise ValueError("resume_cycle_id must be a canonical cycle ID")
        existing_path = cycle_store.path(resume_cycle_id)
        if not existing_path.is_file():
            raise ValueError(f"cognition cycle not found: {resume_cycle_id}")
        existing = cycle_store.load(resume_cycle_id)
        if existing.get("status") not in {"failed", "running"}:
            raise ValueError(
                "only failed or interrupted cognition cycles can be resumed"
            )
        if existing.get("provider") != provider.provider_name or existing.get("model") != provider.model:
            raise ValueError("resume provider and model must match the original cycle")
        cycle_id = resume_cycle_id
        context = str(existing.get("context", ""))
        if not context:
            raise ValueError("resumed cognition cycle has no preserved context")
        plan_context = existing.get("plan_context")
        if not isinstance(plan_context, dict):
            if not any(
                artifact.get("role") == "interpreter"
                for artifact in existing.get("artifacts", [])
            ):
                raise ValueError(
                    "legacy cycle cannot resume before interpreter without a plan snapshot"
                )
            plan_context = current_plan_context
        path_context = existing.get("path_dependent_context")
        if not isinstance(path_context, dict):
            path_context = current_path_context
        exposure_policy = existing.get("context_exposure_policy")
        if not isinstance(exposure_policy, dict):
            exposure_policy = current_context_views["exposure_policy"]
    else:
        plan_context = current_plan_context
        path_context = current_path_context
        exposure_policy = current_context_views["exposure_policy"]
        seed = {
            "context": context,
            "plan_context": plan_context,
            "path_dependent_context_fingerprint": _fingerprint(path_context),
            "context_exposure_policy": exposure_policy,
        }
        cycle_id = f"cycle-{_fingerprint(seed)[:12]}"
        existing_path = cycle_store.path(cycle_id)
        existing = cycle_store.load(cycle_id) if existing_path.is_file() else None
    cycle: Dict[str, Any] = {
        "cognition_cycle_version": "palamedes-cognition-cycle/2",
        "cognition_cycle_id": cycle_id,
        "run_id": cycle_id,
        "status": "running",
        "context": context,
        "plan_context": plan_context,
        "path_dependent_context": path_context,
        "context_exposure_policy": exposure_policy,
        "context_isolation_version": "palamedes-context-isolation/1",
        "started_at": existing.get("started_at", started_at) if existing else started_at,
        "provider": provider.provider_name,
        "model": provider.model,
        "role_order": ["context_governor", "interpreter", "inventor", "adversary", "selector", "outcome_analyst"],
        "artifacts": list(existing.get("artifacts", [])) if existing else [],
        "rejected_artifacts": list(existing.get("rejected_artifacts", [])) if existing else [],
        "outcome_analyses": list(existing.get("outcome_analyses", [])) if existing else [],
        "selection_authority_role": "selector",
        "outcome_analyst_runs_before_outcome": False,
    }
    cycle_store.save(cycle)
    system = (
        "You are one bounded cognitive role inside Palamedes. Return exactly one "
        "JSON object. Do not perform another role's job and do not claim external evidence."
    )
    fresh_call_count = 0
    active_role = ""
    active_role_was_fresh = False

    def report_budget_overrun() -> None:
        if not budget or not progress:
            return
        overrun = _budget_overrun_message(cycle, budget)
        if overrun:
            progress(f"[{cycle_id}] {overrun}")

    def invoke(role: str, call_index: int, prompt: str) -> Dict[str, Any]:
        nonlocal fresh_call_count, active_role, active_role_was_fresh
        active_role = role
        active_role_was_fresh = False
        for artifact in cycle["artifacts"]:
            if artifact.get("role") == role:
                output = artifact.get("output")
                if not isinstance(output, dict) or artifact.get("output_fingerprint") != _fingerprint(output):
                    raise ValueError(f"{role} checkpoint fingerprint mismatch")
                artifact["checkpoint_reused"] = True
                if progress:
                    progress(f"[{cycle_id}] {role} {call_index}/5 checkpoint reused")
                return dict(output)
        if budget:
            spent_calls, spent_tokens = _cycle_budget_spent(cycle)
            call_ceiling = budget.get("provider_calls_max")
            if (
                isinstance(call_ceiling, int)
                and not isinstance(call_ceiling, bool)
                and spent_calls >= call_ceiling
            ):
                raise ValueError(
                    f"cycle provider-call budget exhausted before {role}: "
                    f"{spent_calls}/{call_ceiling} calls already paid"
                )
            token_ceiling = budget.get("token_budget_high")
            if (
                isinstance(token_ceiling, int)
                and not isinstance(token_ceiling, bool)
                and spent_tokens >= token_ceiling
            ):
                raise ValueError(
                    f"cycle token budget exhausted before {role}: "
                    f"{spent_tokens}/{token_ceiling} tokens already paid"
                )
        # A blind retry re-samples the same contract violation. Carry the prior
        # machine-contract error so the role can correct its own output instead.
        prior_error = (retry_feedback or {}).get(role, "")
        if prior_error:
            prompt = (
                f"{prompt}\n\nThe previous attempt at this role was rejected by the "
                f"machine contract: {prior_error}\nReturn the same reasoning with "
                "that violation corrected. Do not weaken or change your conclusion "
                "to satisfy the schema."
            )
        role_started_at = utc_now()
        role_started_monotonic = time.monotonic()
        if progress:
            progress(f"[{cycle_id}] {role} {call_index}/5 started")
        try:
            output = _provider_json(provider, system=system, prompt=prompt)
        except Exception:
            if progress:
                progress(f"[{cycle_id}] {role} {call_index}/5 failed")
            raise
        duration_ms = round((time.monotonic() - role_started_monotonic) * 1000)
        fresh_call_count += 1
        active_role_was_fresh = True
        cycle["artifacts"].append(
            _role_artifact(
                role=role,
                call_index=call_index,
                prompt=prompt,
                output=output,
                provider=provider,
                run_id=cycle_id,
                started_at=role_started_at,
                duration_ms=duration_ms,
            )
        )
        cycle["provider_usage"] = _cognition_usage_summary(
            provider, _cycle_paid_artifacts(cycle)
        )
        cycle_store.save(cycle)
        if progress:
            usage = cycle["artifacts"][-1].get("provider_usage", {})
            tokens = usage.get("total_tokens", "unmetered")
            progress(
                f"[{cycle_id}] {role} {call_index}/5 completed "
                f"in {duration_ms}ms · tokens={tokens}"
            )
        return output
    try:
        governor_prompt = f"""ROLE: context_governor
Classify the authority of the supplied context before mission origination. Preserve
explicit requirements exactly, but do not infer that examples, comparisons, tentative
ideas, prior selections, or implementation artifacts are requirements. Return:
{{
  "hard_requirements":["explicitly mandatory statements only"],
  "success_criteria":["explicit outcome tests"],
  "constraints":["explicit technical, legal, ethical, or resource boundaries"],
  "autonomous_decisions":["fields Palamedes remains free to originate"],
  "observations":["source-grounded facts safe for clean-room interpretation"],
  "preferences":[{{"statement":"...","strength":"weak|medium|strong"}}],
  "reference_examples":[{{"example":"...","authorized_use":"comparison_only|feature_extraction|required_basis"}}],
  "ambiguous_authority":["statements whose force cannot be safely inferred"]
}}
The clean-room brief consists only of hard_requirements, success_criteria,
constraints, autonomous_decisions, and observations. Do not copy names or mechanics
from reference_examples into those fields unless the user explicitly made them a
mandatory basis. Classification grants no mission or delivery authority.

User context: {context}
Strategic plan context: {json.dumps(plan_context, ensure_ascii=False)}"""
        context_governor = invoke("context_governor", 1, governor_prompt)
        for field in (
            "hard_requirements",
            "success_criteria",
            "constraints",
            "autonomous_decisions",
            "observations",
            "ambiguous_authority",
        ):
            values = context_governor.get(field)
            if not isinstance(values, list) or not all(
                isinstance(item, str) and item.strip() for item in values
            ):
                raise ValueError(f"context_governor {field} must be a string array")
        for field in ("preferences", "reference_examples"):
            if not isinstance(context_governor.get(field), list):
                raise ValueError(f"context_governor {field} must be an array")
        for index, preference in enumerate(context_governor["preferences"]):
            if not isinstance(preference, dict) or not str(
                preference.get("statement", "")
            ).strip():
                raise ValueError(
                    f"context_governor preferences[{index}] requires statement"
                )
            if preference.get("strength") not in {"weak", "medium", "strong"}:
                raise ValueError(
                    f"context_governor preferences[{index}] has invalid strength"
                )
        for index, example in enumerate(context_governor["reference_examples"]):
            if not isinstance(example, dict) or not str(
                example.get("example", "")
            ).strip():
                raise ValueError(
                    f"context_governor reference_examples[{index}] requires example"
                )
            if example.get("authorized_use") not in {
                "comparison_only",
                "feature_extraction",
                "required_basis",
            }:
                raise ValueError(
                    f"context_governor reference_examples[{index}] has invalid authorized_use"
                )
        clean_room_brief = {
            field: context_governor[field]
            for field in (
                "hard_requirements",
                "success_criteria",
                "constraints",
                "autonomous_decisions",
                "observations",
            )
        }
        serialized_clean_brief = json.dumps(
            clean_room_brief, ensure_ascii=False, sort_keys=True
        ).casefold()
        leaked_examples = [
            str(example["example"])
            for example in context_governor["reference_examples"]
            if example["authorized_use"] != "required_basis"
            and str(example["example"]).strip().casefold() in serialized_clean_brief
        ]
        if leaked_examples:
            raise ValueError(
                "context_governor leaked non-required reference examples into the "
                "clean-room brief"
            )

        interpreter_prompt = f"""ROLE: interpreter
Separate observation from inference and preserve rival frames.
Return:
{{
  "observations": ["claims actually present in user or plan context"],
  "interpretations": [
    {{"interpretation_id":"frame-1","frame":"...","mechanism":"...","would_lose_if":"..."}}
  ],
  "tensions": ["..."],
  "missing_evidence": ["..."]
}}
Require at least two interpretations.

Clean-room brief (reference examples, preferences, prior selections, and local
implementation artifacts are intentionally unavailable):
{json.dumps(clean_room_brief, ensure_ascii=False)}"""
        interpreter = invoke("interpreter", 2, interpreter_prompt)
        _non_empty_string_array(interpreter, "observations")
        _non_empty_string_array(interpreter, "tensions")
        _non_empty_string_array(interpreter, "missing_evidence")
        interpretations = interpreter.get("interpretations")
        if not isinstance(interpretations, list) or len(interpretations) < 2:
            raise ValueError("interpreter requires at least two interpretations")

        inventor_prompt = f"""ROLE: inventor
Generate at least three competing outcome-level missions from distinct frames.
Do not select a winner and do not criticize candidates.
When the context asks for evidence of user or business value, at least two candidates
must contain a small, reversible action with an observable user or beneficiary response.
A readiness review, eligibility packet, measurement design, or request for another
reviewer is not an action experiment. Use those only when the interpreter identifies a
specific authority, safety, privacy, or observability boundary that makes live action
currently impossible. Reduce claim scope and intervention size before retreating to a
meta-evaluation mission.
Return:
{{
  "candidates": [
    {{
      "candidate_id":"candidate-1",
      "mission":"...",
      "source_interpretation_id":"frame-1",
      "beneficiary":"...",
      "causal_thesis":"...",
      "success_metric":"...",
      "early_falsifier":"...",
      "next_probe":"..."
    }}
  ]
}}

Interpreter artifact:
{json.dumps(interpreter, ensure_ascii=False)}"""
        inventor = invoke("inventor", 3, inventor_prompt)
        candidates = inventor.get("candidates")
        if not isinstance(candidates, list) or len(candidates) < 3:
            raise ValueError("inventor requires at least three candidates")
        candidate_ids = []
        for item in candidates:
            if not isinstance(item, dict):
                raise ValueError("each candidate must be an object")
            candidate_id = str(item.get("candidate_id", "")).strip()
            for field in (
                "mission",
                "source_interpretation_id",
                "beneficiary",
                "causal_thesis",
                "success_metric",
                "early_falsifier",
                "next_probe",
            ):
                if not str(item.get(field, "")).strip():
                    raise ValueError(f"candidate {candidate_id or '?'} missing {field}")
            candidate_ids.append(candidate_id)
        if len(set(candidate_ids)) != len(candidate_ids) or not all(candidate_ids):
            raise ValueError("candidate IDs must be non-empty and unique")

        adversary_prompt = f"""ROLE: adversary
Attack every candidate, shared assumptions, proxy risks, hidden harms, owner bias,
and Palamedes self-expansion. Do not select a winner or rewrite candidates.
Set disqualifying=true only for a fatal issue that cannot be bounded by making the
candidate's action smaller, reversible, time-boxed, explicitly consented, or more modest
in its causal claim. Missing perfect attribution, full instrumentation, large samples, or
publication-grade evidence is normally repairable for an exploratory probe. Distinguish
"cannot safely learn" from "cannot yet prove a broad claim."
Return:
{{
  "critiques": [
    {{"candidate_id":"candidate-1","fatal_risks":["..."],"repairable_risks":["..."],"disqualifying":false}}
  ],
  "shared_assumptions": ["..."],
  "missing_opposition": ["..."],
  "minimum_disconfirming_probe": "...",
  "abstraction_audit": {{
    "reasoning_level":"strategic|tactical|implementation",
    "path_assumptions_detected":["..."],
    "suspected_abstraction_drift":false,
    "discriminating_context_ablation":"which context bundle to remove or replace"
  }}
}}
Every candidate ID must have exactly one critique.

Interpreter:
{json.dumps(interpreter, ensure_ascii=False)}
Candidates:
{json.dumps(inventor, ensure_ascii=False)}

Path-dependent implementation context (use only to test feasibility, sunk-cost
reasoning, current-path lock-in, and abstraction drift; it is not evidence that
the frozen direction is strategically correct):
{json.dumps(path_context, ensure_ascii=False)}

Authority-classified preferences and examples (comparison and compliance checks
only; do not rewrite the frozen candidates around them):
{json.dumps({"preferences": context_governor["preferences"], "reference_examples": context_governor["reference_examples"], "ambiguous_authority": context_governor["ambiguous_authority"]}, ensure_ascii=False)}"""
        adversary = invoke("adversary", 4, adversary_prompt)
        critiques = adversary.get("critiques")
        if not isinstance(critiques, list):
            raise ValueError("adversary critiques must be an array")
        critiqued_ids = [
            str(item.get("candidate_id", "")).strip()
            for item in critiques
            if isinstance(item, dict)
        ]
        if sorted(critiqued_ids) != sorted(candidate_ids):
            raise ValueError("adversary must critique every candidate exactly once")
        _non_empty_string_array(adversary, "shared_assumptions")
        _non_empty_string_array(adversary, "missing_opposition")
        if not str(adversary.get("minimum_disconfirming_probe", "")).strip():
            raise ValueError("adversary requires minimum_disconfirming_probe")
        abstraction_audit = adversary.get("abstraction_audit")
        if not isinstance(abstraction_audit, dict):
            raise ValueError("adversary requires abstraction_audit")
        if abstraction_audit.get("reasoning_level") not in {
            "strategic",
            "tactical",
            "implementation",
        }:
            raise ValueError("abstraction_audit requires a valid reasoning_level")
        assumptions = abstraction_audit.get("path_assumptions_detected")
        if not isinstance(assumptions, list) or not all(
            isinstance(item, str) and item.strip() for item in assumptions
        ):
            raise ValueError("abstraction_audit path assumptions must be a string array")
        if not isinstance(
            abstraction_audit.get("suspected_abstraction_drift"), bool
        ):
            raise ValueError("abstraction_audit drift flag must be boolean")
        if not str(
            abstraction_audit.get("discriminating_context_ablation", "")
        ).strip():
            raise ValueError("abstraction_audit requires a discriminating ablation")
        cycle["abstraction_audit"] = dict(abstraction_audit)

        if available_discovery_ids:
            discovery_clause = (
                "source_discovery_ids may cite only these available discovery IDs: "
                + json.dumps(sorted(available_discovery_ids), ensure_ascii=False)
                + ". Cite no other ID."
            )
        else:
            discovery_clause = (
                "No discovery IDs are available to this cycle. "
                "source_discovery_ids must be an empty array."
            )
        selector_prompt = f"""ROLE: selector
Select, defer, or reject from the frozen candidates and critiques. You may not
invent a new candidate. Then compile the selected candidate into the exact
mission draft shape below. If evidence is weak, select an information-producing
probe and preserve uncertainty. Prefer a small, reversible action that creates an
observable user or beneficiary response over a mission whose output is only another
eligibility packet, readiness review, measurement plan, reviewer judgment, or protocol.
Weak evidence should narrow the action, claim, cohort, duration, or success threshold; it
must not by itself cause retreat into meta-validation. If at least one frozen candidate is
not disqualifying, select the best bounded action candidate unless its expected learning
is lower than its concrete user, authority, safety, privacy, or irreversible-cost risk.
Select a meta-evaluation candidate only when every action candidate is explicitly marked
disqualifying by the adversary. In that case, state the shared fatal boundary in the
selection reason; do not manufacture a new meta candidate in the selector.
For a selected, non-disqualified action candidate, mission_contract.next_probe must reach
the intervention and observe a real response inside its stated window. Consent checks,
baseline freezing, preregistration, and reviewer checks may be preparation steps inside
that probe, but the terminal output cannot be only a packet, review, eligibility ruling,
protocol, or recommendation for a later experiment. If the action cannot be reached
safely, defer or reject it instead of presenting meta-validation as an action probe.

Classify whether this cycle originated a
mission before implementation, selected or constrained an existing direction,
or audited work that had already started. A retrospective audit is not mission
origination. State whether the selection is exclusive, sequencing, conditional,
portfolio, or a probe, and preserve the fate of every candidate.
Return:
{{
  "decision":"select|defer|reject",
  "selected_candidate_id":"candidate-1 or empty when not selected",
  "selection_reason":"...",
  "causal_role":"originated|selected|constrained|audited",
  "decision_scope":"strategic_open|tactical_bounded|audit_only|integration",
  "implementation_state_at_start":"not_started|in_progress|completed|unknown",
  "selection_type":"exclusive|sequencing|conditional|portfolio|probe",
  "source_discovery_ids":["only discovery IDs actually used, or empty"],
  "candidate_fates":[{{"candidate_id":"...","fate":"selected|rejected|deferred|conditional|queued","reason":"...","reopen_condition":"..."}}],
  "decisive_assumptions":["..."],
  "reversal_triggers":["..."],
  "mission_contract": {mission_prompt("Use the frozen artifacts").split("Required shape:", 1)[1].split("Do not invent", 1)[0].strip()}
}}
Only decision=select may contain a mission_contract.
{discovery_clause}

Candidates:
{json.dumps(inventor, ensure_ascii=False)}
Adversary:
{json.dumps(adversary, ensure_ascii=False)}"""
        selector = invoke("selector", 5, selector_prompt)
        decision = selector.get("decision")
        if decision not in {"select", "defer", "reject"}:
            raise ValueError("selector decision must be select, defer, or reject")
        _non_empty_string_array(selector, "decisive_assumptions")
        _non_empty_string_array(selector, "reversal_triggers")
        selected_id = str(selector.get("selected_candidate_id", "")).strip()
        if decision == "select" and selected_id not in candidate_ids:
            raise ValueError("selector must select a frozen candidate ID")
        if decision != "select" and selected_id:
            raise ValueError("defer or reject cannot name a selected candidate")
        causal_role = selector.get("causal_role")
        if causal_role not in {"originated", "selected", "constrained", "audited"}:
            raise ValueError("selector requires a valid causal_role")
        decision_scope = selector.get("decision_scope")
        if decision_scope not in {
            "strategic_open",
            "tactical_bounded",
            "audit_only",
            "integration",
        }:
            raise ValueError("selector requires a valid decision_scope")
        implementation_state = selector.get("implementation_state_at_start")
        if implementation_state not in {
            "not_started",
            "in_progress",
            "completed",
            "unknown",
        }:
            raise ValueError("selector requires implementation_state_at_start")
        if implementation_state == "completed" and (
            causal_role != "audited" or decision_scope != "audit_only"
        ):
            raise ValueError(
                "completed work must be classified as audited with audit_only scope"
            )
        if causal_role == "audited" and decision_scope != "audit_only":
            raise ValueError("audited cycles require audit_only scope")
        selection_type = selector.get("selection_type")
        if selection_type not in {
            "exclusive",
            "sequencing",
            "conditional",
            "portfolio",
            "probe",
        }:
            raise ValueError("selector requires a valid selection_type")
        source_discovery_ids = selector.get("source_discovery_ids", [])
        if not isinstance(source_discovery_ids, list) or not all(
            isinstance(item, str) and item.strip() for item in source_discovery_ids
        ):
            raise ValueError("selector source_discovery_ids must be a string array")
        unavailable_discovery_ids = sorted(
            set(source_discovery_ids) - set(available_discovery_ids)
        )
        if unavailable_discovery_ids:
            raise ValueError(
                "selector cited an unavailable discovery ID: "
                f"{json.dumps(unavailable_discovery_ids, ensure_ascii=False)}; "
                "available: "
                f"{json.dumps(sorted(available_discovery_ids), ensure_ascii=False)}"
            )
        candidate_fates = selector.get("candidate_fates")
        if not isinstance(candidate_fates, list):
            raise ValueError("selector candidate_fates must be an array")
        fate_ids = []
        for fate in candidate_fates:
            if not isinstance(fate, dict):
                raise ValueError("each candidate fate must be an object")
            candidate_id = str(fate.get("candidate_id", "")).strip()
            if fate.get("fate") not in {
                "selected",
                "rejected",
                "deferred",
                "conditional",
                "queued",
            }:
                raise ValueError(f"candidate {candidate_id or '?'} has invalid fate")
            if not str(fate.get("reason", "")).strip():
                raise ValueError(f"candidate {candidate_id or '?'} fate requires reason")
            fate_ids.append(candidate_id)
        if sorted(fate_ids) != sorted(candidate_ids) or len(fate_ids) != len(set(fate_ids)):
            raise ValueError("selector must preserve exactly one fate for every candidate")
        selected_fates = [
            item for item in candidate_fates if item.get("fate") == "selected"
        ]
        if decision == "select" and (
            len(selected_fates) != 1
            or selected_fates[0].get("candidate_id") != selected_id
        ):
            raise ValueError("selected candidate must have the sole selected fate")
        if decision != "select" and selected_fates:
            raise ValueError("defer or reject cannot contain a selected fate")
        cycle["decision"] = decision
        cycle["selected_candidate_id"] = selected_id
        cycle["causal_role"] = causal_role
        cycle["decision_scope"] = decision_scope
        cycle["implementation_state_at_start"] = implementation_state
        cycle["selection_type"] = selection_type
        cycle["source_discovery_ids"] = source_discovery_ids
        cycle["candidate_fates"] = candidate_fates
        cycle["status"] = "selected" if decision == "select" else decision
        cycle["completed_at"] = utc_now()
        cycle["live_model_call_count"] = fresh_call_count
        cycle["provider_usage"] = _cognition_usage_summary(
            provider, _cycle_paid_artifacts(cycle)
        )
        cycle["role_output_fingerprints_unique"] = (
            len({item["output_fingerprint"] for item in cycle["artifacts"]}) == 5
        )
        contract = None
        if decision == "select":
            raw_contract = selector.get("mission_contract")
            if not isinstance(raw_contract, dict):
                raise ValueError("selected cycle requires mission_contract")
            contract = validate_mission_draft(raw_contract)
            contract["cognition_cycle_id"] = cycle_id
            contract["selected_candidate_id"] = selected_id
            contract["causal_role"] = causal_role
            contract["decision_scope"] = decision_scope
            contract["implementation_state_at_start"] = implementation_state
            contract["selection_type"] = selection_type
            if source_discovery_ids:
                contract["source_discovery_ids"] = source_discovery_ids
            contract["candidate_fates"] = candidate_fates
            contract["role_lineage"] = [
                {
                    "role": item["role"],
                    "output_fingerprint": item["output_fingerprint"],
                }
                for item in cycle["artifacts"]
            ]
            governance_fingerprint = _fingerprint(
                {
                    "draft_fingerprint": contract["contract_fingerprint"],
                    "cognition_cycle_id": cycle_id,
                    "causal_role": causal_role,
                    "decision_scope": decision_scope,
                    "implementation_state_at_start": implementation_state,
                    "selection_type": selection_type,
                    "source_discovery_ids": source_discovery_ids,
                    "candidate_fates": candidate_fates,
                }
            )
            contract["mission_id"] = f"mission-{governance_fingerprint[:12]}"
            contract["contract_fingerprint"] = governance_fingerprint
        cycle_store.save(cycle)
        report_budget_overrun()
        return {"cycle": cycle, "contract": contract}
    except Exception as exc:
        retryable_schema_failure = (
            isinstance(exc, ValueError)
            and active_role_was_fresh
            and schema_retry_limit > 0
        )
        if isinstance(exc, ValueError) and active_role_was_fresh:
            rejected = next(
                (
                    artifact
                    for artifact in reversed(cycle["artifacts"])
                    if artifact.get("role") == active_role
                ),
                None,
            )
            if rejected is not None:
                rejected = dict(rejected)
                rejected["rejection_reason"] = str(exc)
                rejected["rejected_at"] = utc_now()
                cycle["rejected_artifacts"].append(rejected)
            cycle["artifacts"] = [
                artifact
                for artifact in cycle["artifacts"]
                if artifact.get("role") != active_role
            ]
        cycle["status"] = "failed"
        cycle["failed_at"] = utc_now()
        cycle["failure"] = str(exc)
        cycle["live_model_call_count"] = len(cycle["artifacts"])
        cycle["provider_usage"] = _cognition_usage_summary(
            provider, _cycle_paid_artifacts(cycle)
        )
        cycle_store.save(cycle)
        if retryable_schema_failure:
            if progress:
                progress(
                    f"[{cycle_id}] {active_role} schema validation failed; "
                    "retrying only that role once with prior checkpoints preserved"
                )
            return run_cognition_cycle(
                provider=provider,
                palamedes_module=palamedes_module,
                context=context,
                cycle_store=cycle_store,
                available_discovery_ids=available_discovery_ids,
                budget=budget,
                retry_feedback={**(retry_feedback or {}), active_role: str(exc)},
                progress=progress,
                schema_retry_limit=schema_retry_limit - 1,
                resume_cycle_id=cycle_id,
            )
        report_budget_overrun()
        raise


def run_context_ablation(
    *,
    provider: ChatProvider,
    cycle_store: CognitionCycleStore,
    cycle_id: str,
    record_root: Path,
) -> Dict[str, Any]:
    """Compare fresh strategic reasoning with and without path-dependent context."""
    cycle = cycle_store.load(cycle_id)
    if cycle.get("status") not in {"selected", "defer", "reject"}:
        raise ValueError("context ablation requires a completed cognition cycle")
    plan_context = cycle.get("plan_context")
    path_context = cycle.get("path_dependent_context")
    if not isinstance(plan_context, dict) or not isinstance(path_context, dict):
        raise ValueError("cycle predates split strategic and path-dependent context")
    governor = next(
        (
            row.get("output")
            for row in cycle.get("artifacts", [])
            if row.get("role") == "context_governor"
        ),
        None,
    )
    if not isinstance(governor, dict):
        raise ValueError("cycle has no context_governor artifact")
    clean_room_brief = {
        field: governor.get(field, [])
        for field in (
            "hard_requirements",
            "success_criteria",
            "constraints",
            "autonomous_decisions",
            "observations",
        )
    }
    system = (
        "You are one isolated Palamedes ablation role. Return exactly one JSON "
        "object, preserve uncertainty, and grant no mission or delivery authority."
    )

    def generate_arm(role: str, visible_path: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        path_section = (
            "Path-dependent context is intentionally unavailable."
            if visible_path is None
            else "Path-dependent context:\n"
            + json.dumps(visible_path, ensure_ascii=False, sort_keys=True)
        )
        output = _provider_json(
            provider,
            system=system,
            prompt=f"""ROLE: {role}
Produce one fresh strategic diagnosis. Do not continue or polish the prior mission.
Return:
{{
  "problem_frame":"...",
  "causal_mechanism":"...",
  "mission_family":"...",
  "decision_level":"strategic|tactical|implementation",
  "next_discriminating_probe":"...",
  "path_assumptions":["..."],
  "confidence":0
}}
confidence must be an integer from 0 to 100, not a fraction or percentage string.

Clean-room brief:
{json.dumps(clean_room_brief, ensure_ascii=False, sort_keys=True)}
Strategic plan context:
{json.dumps(plan_context, ensure_ascii=False, sort_keys=True)}
{path_section}""",
        )
        for field in (
            "problem_frame",
            "causal_mechanism",
            "mission_family",
            "next_discriminating_probe",
        ):
            if not str(output.get(field, "")).strip():
                raise ValueError(f"{role} requires {field}")
        if output.get("decision_level") not in {
            "strategic",
            "tactical",
            "implementation",
        }:
            raise ValueError(f"{role} has invalid decision_level")
        assumptions = output.get("path_assumptions")
        if not isinstance(assumptions, list) or not all(
            isinstance(item, str) and item.strip() for item in assumptions
        ):
            raise ValueError(f"{role} path_assumptions must be a string array")
        confidence = output.get("confidence")
        if (
            not isinstance(confidence, int)
            or isinstance(confidence, bool)
            or not 0 <= confidence <= 100
        ):
            raise ValueError(f"{role} confidence must be an integer from 0 to 100")
        return output

    prior_records = []
    prior_failures = []
    if record_root.is_dir():
        for prior_path in sorted(record_root.glob("ablation-*.json")):
            try:
                prior = json.loads(prior_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if (
                isinstance(prior, dict)
                and prior.get("source_cognition_cycle_id") == cycle_id
            ):
                prior_records.append(prior)
        for failure_path in sorted(record_root.glob("failed-ablation-*.json")):
            try:
                failure = json.loads(failure_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if (
                isinstance(failure, dict)
                and failure.get("source_cognition_cycle_id") == cycle_id
            ):
                prior_failures.append(failure)
    attempt_id = f"ablation-{uuid.uuid4().hex[:12]}"
    clean_output = generate_arm("clean_room_ablation_arm", None)
    continuity_output = generate_arm("continuity_ablation_arm", path_context)
    arm_order = (
        [("arm-a", clean_output), ("arm-b", continuity_output)]
        if len(prior_records) % 2 == 0
        else [("arm-a", continuity_output), ("arm-b", clean_output)]
    )
    judge = _provider_json(
        provider,
        system=system,
        prompt=f"""ROLE: blinded_ablation_judge
Compare the two frozen strategic diagnoses without guessing their source. Judge
structural meaning, not wording. Return:
{{
  "same_problem_frame":false,
  "same_causal_mechanism":false,
  "same_mission_family":false,
  "material_direction_shift":true,
  "shift_dimensions":["problem_frame|causal_mechanism|mission_family|decision_level|probe"],
  "lower_abstraction_arm":"arm-a|arm-b|neither",
  "rationale":"..."
}}

arm-a:
{json.dumps(arm_order[0][1], ensure_ascii=False, sort_keys=True)}
arm-b:
{json.dumps(arm_order[1][1], ensure_ascii=False, sort_keys=True)}""",
    )
    for field in (
        "same_problem_frame",
        "same_causal_mechanism",
        "same_mission_family",
        "material_direction_shift",
    ):
        if not isinstance(judge.get(field), bool):
            raise ValueError(f"blinded_ablation_judge {field} must be boolean")
    dimensions = judge.get("shift_dimensions")
    allowed_dimensions = {
        "problem_frame",
        "causal_mechanism",
        "mission_family",
        "decision_level",
        "probe",
    }
    if not isinstance(dimensions, list) or not set(dimensions).issubset(
        allowed_dimensions
    ):
        raise ValueError("blinded_ablation_judge has invalid shift_dimensions")
    if judge["material_direction_shift"] != bool(dimensions):
        raise ValueError(
            "blinded_ablation_judge shift flag must match shift_dimensions"
        )
    if judge.get("lower_abstraction_arm") not in {"arm-a", "arm-b", "neither"}:
        raise ValueError("blinded_ablation_judge has invalid lower_abstraction_arm")
    if not str(judge.get("rationale", "")).strip():
        raise ValueError("blinded_ablation_judge requires rationale")
    clean_label = next(label for label, value in arm_order if value is clean_output)
    continuity_label = next(
        label for label, value in arm_order if value is continuity_output
    )
    continuity_lower_abstraction = (
        judge["lower_abstraction_arm"] == continuity_label
    )
    record = {
        "context_ablation_version": "palamedes-context-ablation/1",
        "context_ablation_id": attempt_id,
        "replication_number": len(prior_records) + 1,
        "created_at": utc_now(),
        "source_cognition_cycle_id": cycle_id,
        "tested_context_bundle": "path_dependent_context",
        "clean_room_output": clean_output,
        "continuity_output": continuity_output,
        "blinded_labels": {
            "clean_room": clean_label,
            "continuity": continuity_label,
        },
        "blinded_judgment": judge,
        "material_direction_shift": judge["material_direction_shift"],
        "suspected_path_dependence": judge["material_direction_shift"],
        "continuity_lower_abstraction": continuity_lower_abstraction,
        "abstraction_collapse_signal": continuity_lower_abstraction,
        "shared_model_dependence": True,
        "single_pair_is_causal_proof": False,
        "replication_required": True,
        "mission_authority_granted": False,
        "delivery_authority_granted": False,
    }
    record_root.mkdir(parents=True, exist_ok=True)
    path = record_root / f"{record['context_ablation_id']}.json"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    aggregate_records = prior_records + [record]
    shift_count = sum(
        row.get("material_direction_shift") is True for row in aggregate_records
    )
    collapse_count = sum(
        row.get("continuity_lower_abstraction") is True for row in aggregate_records
    )
    summary = {
        "context_ablation_summary_version": "palamedes-context-ablation-summary/1",
        "source_cognition_cycle_id": cycle_id,
        "attempt_count": len(aggregate_records),
        "completed_pair_count": len(aggregate_records),
        "failed_attempt_count": len(prior_failures),
        "total_attempt_count": len(aggregate_records) + len(prior_failures),
        "completion_rate": len(aggregate_records)
        / (len(aggregate_records) + len(prior_failures)),
        "material_direction_shift_count": shift_count,
        "material_direction_shift_rate": shift_count / len(aggregate_records),
        "abstraction_collapse_signal_count": collapse_count,
        "abstraction_collapse_signal_rate": collapse_count
        / len(aggregate_records),
        "attempt_ids": [row["context_ablation_id"] for row in aggregate_records],
        "minimum_interpretation": (
            "distributional_signal_only"
            if len(aggregate_records) < 3
            else "replicated_shared_model_signal"
        ),
        "causal_proof_claimed": False,
    }
    summary_path = record_root / f"summary-{cycle_id}.json"
    summary_temporary = summary_path.with_suffix(".json.tmp")
    summary_temporary.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    summary_temporary.replace(summary_path)
    record["aggregate_summary"] = summary
    return record


def record_context_ablation_failure(
    *,
    provider: ChatProvider,
    cycle_id: str,
    record_root: Path,
    error: Exception,
) -> Dict[str, Any]:
    """Preserve a failed ablation attempt without inventing a successful result."""
    record = {
        "context_ablation_failure_version": "palamedes-context-ablation-failure/1",
        "failure_id": f"failed-ablation-{uuid.uuid4().hex[:12]}",
        "created_at": utc_now(),
        "source_cognition_cycle_id": cycle_id,
        "status": "failed",
        "error_type": type(error).__name__,
        "error": str(error),
        "provider": provider.provider_name,
        "model": provider.model,
        "provider_json_custody": getattr(provider, "last_json_custody", None),
        "counted_as_successful_pair": False,
        "counted_in_total_attempts": True,
        "excluded_from_completed_pair_rates": True,
        "mission_authority_granted": False,
        "delivery_authority_granted": False,
    }
    record_root.mkdir(parents=True, exist_ok=True)
    path = record_root / f"{record['failure_id']}.json"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return record


def run_micro_cycle(
    *,
    provider: ChatProvider,
    palamedes_module: Any,
    context: str,
    cycle_store: CognitionCycleStore,
    progress: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """Compile one bounded mission with at most one schema-repair call."""
    plan_context = json.loads(_plan_context(palamedes_module))
    seed = {"mode": "micro", "context": context, "plan_context": plan_context}
    cycle_id = f"cycle-{_fingerprint(seed)[:12]}"
    existing_path = cycle_store.path(cycle_id)
    existing = cycle_store.load(cycle_id) if existing_path.is_file() else None
    cycle = {
        "cognition_cycle_version": "palamedes-cognition-cycle/1",
        "cognition_cycle_id": cycle_id,
        "run_id": cycle_id,
        "cycle_mode": "micro",
        "status": "running",
        "context": context,
        "plan_context": plan_context,
        "started_at": existing.get("started_at", utc_now()) if existing else utc_now(),
        "provider": provider.provider_name,
        "model": provider.model,
        "role_order": ["mission_compiler"],
        "artifacts": list(existing.get("artifacts", [])) if existing else [],
        "rejected_artifacts": list(existing.get("rejected_artifacts", [])) if existing else [],
        "outcome_analyses": list(existing.get("outcome_analyses", [])) if existing else [],
        "selection_authority_role": "mission_compiler",
        "outcome_analyst_runs_before_outcome": False,
    }
    cycle_store.save(cycle)
    system = (
        "You are the bounded micro-mission compiler inside Palamedes. Return exactly "
        "one JSON mission contract. Do not expand scope or claim external evidence."
    )
    fresh_calls = 0
    validation_error = ""
    for attempt in range(2):
        cached = next(
            (row for row in cycle["artifacts"] if row.get("role") == "mission_compiler"),
            None,
        )
        if cached is not None:
            output_value = cached.get("output")
            if not isinstance(output_value, dict) or cached.get("output_fingerprint") != _fingerprint(output_value):
                raise ValueError("mission_compiler checkpoint fingerprint mismatch")
            cached["checkpoint_reused"] = True
            raw_contract = dict(output_value)
            if progress:
                progress(f"[{cycle_id}] mission_compiler checkpoint reused")
        else:
            prompt = mission_prompt(
                context
                + "\n\nPlan context:\n"
                + json.dumps(plan_context, ensure_ascii=False)
                + (f"\n\nPrevious schema error to repair without changing scope:\n{validation_error}" if validation_error else "")
            )
            started_at = utc_now()
            started = time.monotonic()
            if progress:
                progress(
                    f"[{cycle_id}] mission_compiler call {attempt + 1}/2 started"
                )
            raw_contract = _provider_json(provider, system=system, prompt=prompt)
            duration_ms = round((time.monotonic() - started) * 1000)
            fresh_calls += 1
            artifact = _role_artifact(
                role="mission_compiler",
                call_index=attempt + 1,
                prompt=prompt,
                output=raw_contract,
                provider=provider,
                run_id=cycle_id,
                started_at=started_at,
                duration_ms=duration_ms,
            )
            cycle["artifacts"].append(artifact)
            cycle["provider_usage"] = _cognition_usage_summary(
                provider, _cycle_paid_artifacts(cycle)
            )
            cycle_store.save(cycle)
            if progress:
                progress(
                    f"[{cycle_id}] mission_compiler call {attempt + 1}/2 completed "
                    f"in {duration_ms}ms · tokens="
                    f"{artifact.get('provider_usage', {}).get('total_tokens', 'unmetered')}"
                )
        try:
            contract = validate_mission_draft(raw_contract)
            break
        except ValueError as exc:
            validation_error = str(exc)
            rejected = dict(cycle["artifacts"].pop())
            rejected["rejection_reason"] = validation_error
            rejected["rejected_at"] = utc_now()
            cycle["rejected_artifacts"].append(rejected)
            cycle["provider_usage"] = _cognition_usage_summary(
                provider, _cycle_paid_artifacts(cycle)
            )
            cycle_store.save(cycle)
            if attempt == 1:
                cycle["status"] = "failed"
                cycle["failure"] = validation_error
                cycle["failed_at"] = utc_now()
                cycle["live_model_call_count"] = fresh_calls
                cycle_store.save(cycle)
                raise
            if progress:
                progress(
                    f"[{cycle_id}] mission_compiler schema validation failed; "
                    "retrying once"
                )
    contract["cognition_cycle_id"] = cycle_id
    contract["causal_role"] = "constrained"
    contract["decision_scope"] = "tactical_bounded"
    contract["implementation_state_at_start"] = "unknown"
    contract["selection_type"] = "probe"
    contract["candidate_fates"] = []
    contract["role_lineage"] = [{
        "role": "mission_compiler",
        "output_fingerprint": cycle["artifacts"][0]["output_fingerprint"],
    }]
    governance_fingerprint = _fingerprint({
        "draft_fingerprint": contract["contract_fingerprint"],
        "cognition_cycle_id": cycle_id,
        "cycle_mode": "micro",
    })
    contract["mission_id"] = f"mission-{governance_fingerprint[:12]}"
    contract["contract_fingerprint"] = governance_fingerprint
    cycle.update({
        "decision": "select",
        "selected_candidate_id": "",
        "causal_role": "constrained",
        "decision_scope": "tactical_bounded",
        "implementation_state_at_start": "unknown",
        "selection_type": "probe",
        "source_discovery_ids": [],
        "candidate_fates": [],
        "status": "selected",
        "completed_at": utc_now(),
        "live_model_call_count": fresh_calls,
        "provider_usage": _cognition_usage_summary(
            provider, _cycle_paid_artifacts(cycle)
        ),
        "role_output_fingerprints_unique": True,
    })
    cycle_store.save(cycle)
    return {"cycle": cycle, "contract": contract}


def run_outcome_analyst(
    *,
    provider: ChatProvider,
    cycle_store: CognitionCycleStore,
    mission_store: MissionStore,
    contract: Dict[str, Any],
    outcome: Dict[str, Any],
    progress: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    cycle_id = str(contract.get("cognition_cycle_id", "")).strip()
    if not cycle_id:
        return {"status": "not_applicable", "reason": "mission has no cognition cycle"}
    cycle = cycle_store.load(cycle_id)
    from palamedes_prompt import (
        PromptAgendaStore,
        record_causal_pattern,
        record_design_hypothesis,
        record_zoom_pattern,
        run_prompt_architecture,
    )

    prompt_store = PromptAgendaStore(mission_store.root / "prompt-intelligence")
    known_clusters = prompt_store.active_clusters()
    prompt = f"""ROLE: outcome_analyst
An outcome now exists. Compare it with the frozen mission forecast without
rewriting prior artifacts. Separate mission, planning, implementation,
environment, and measurement attribution. Reuse an existing causal_signature
when the mechanism is materially the same; create a new short stable signature
only when the mechanism differs, regardless of surface feature or wording.
Return exactly:
{{
  "observed_vs_expected":"...",
  "attribution_hypotheses":[{{"layer":"mission|planning|implementation|environment|measurement","claim":"...","confidence":0}}],
  "belief_updates":["..."],
  "causal_signature":"short stable mechanism label reusable across outcomes",
  "mechanism_summary":"how the observed result was produced, independent of surface wording",
  "work_scale":"micro|component|product|service|portfolio",
  "surface_key":"stable product or code surface label",
  "finding_lane":"correctness_defect|design_hypothesis|null_candidate|expected_outcome|inconclusive",
  "exploration_value":0,
  "hypothesis_scope":"bounded design question, or empty when not a design hypothesis",
  "probe_status":"completed|incomplete|not_applicable",
  "finding":"qualifying_defect|null_finding|expected_result|adverse_result|inconclusive",
  "mission_disposition":"continue|revise|stop|insufficient_evidence",
  "followup_required":true,
  "followup_kind":"production_correction|new_probe|mission_revision|none",
  "successor_scope":"exact bounded work still required, or empty when none",
  "next_probe":"...",
  "confidence":0
}}

Frozen cycle:
{json.dumps(cycle, ensure_ascii=False)}
Mission contract:
{json.dumps(contract, ensure_ascii=False)}
Observed outcome:
{json.dumps(outcome, ensure_ascii=False)}
Known causal clusters:
{json.dumps(known_clusters, ensure_ascii=False)}"""
    output = _provider_json(
        provider,
        system=(
            "You are the outcome_analyst role. You may update beliefs but may "
            "not rewrite frozen pre-outcome artifacts. Return one JSON object."
        ),
        prompt=prompt,
    )
    if not str(output.get("observed_vs_expected", "")).strip():
        raise ValueError("outcome analyst requires observed_vs_expected")
    _non_empty_string_array(output, "belief_updates")
    causal_signature = str(output.get("causal_signature", "")).strip()
    mechanism_summary = str(output.get("mechanism_summary", "")).strip()
    if not causal_signature or not mechanism_summary:
        raise ValueError("outcome analyst requires causal signature and mechanism summary")
    output["causal_signature"] = causal_signature
    output["mechanism_summary"] = mechanism_summary
    if output.get("work_scale") not in {
        "micro", "component", "product", "service", "portfolio"
    }:
        raise ValueError("invalid outcome work_scale")
    surface_key = str(output.get("surface_key", "")).strip()
    if not surface_key:
        raise ValueError("outcome analyst requires surface_key")
    output["surface_key"] = surface_key
    if output.get("finding_lane") not in {
        "correctness_defect",
        "design_hypothesis",
        "null_candidate",
        "expected_outcome",
        "inconclusive",
    }:
        raise ValueError("invalid outcome finding_lane")
    exploration_value = output.get("exploration_value")
    if (
        not isinstance(exploration_value, int)
        or isinstance(exploration_value, bool)
        or not 0 <= exploration_value <= 100
    ):
        raise ValueError("exploration_value must be an integer from 0 to 100")
    hypothesis_scope = str(output.get("hypothesis_scope", "")).strip()
    if output["finding_lane"] == "design_hypothesis" and not hypothesis_scope:
        raise ValueError("design_hypothesis requires a bounded hypothesis_scope")
    if output["finding_lane"] != "design_hypothesis" and hypothesis_scope:
        raise ValueError("hypothesis_scope is only valid for design_hypothesis")
    output["hypothesis_scope"] = hypothesis_scope
    if output.get("mission_disposition") not in {
        "continue",
        "revise",
        "stop",
        "insufficient_evidence",
    }:
        raise ValueError("invalid mission_disposition")
    if output.get("probe_status") not in {
        "completed",
        "incomplete",
        "not_applicable",
    }:
        raise ValueError("invalid probe_status")
    if output.get("finding") not in {
        "qualifying_defect",
        "null_finding",
        "expected_result",
        "adverse_result",
        "inconclusive",
    }:
        raise ValueError("invalid outcome finding")
    followup_required = output.get("followup_required")
    if not isinstance(followup_required, bool):
        raise ValueError("followup_required must be boolean")
    if output.get("followup_kind") not in {
        "production_correction",
        "new_probe",
        "mission_revision",
        "none",
    }:
        raise ValueError("invalid followup_kind")
    successor_scope = str(output.get("successor_scope", "")).strip()
    if followup_required:
        if output["followup_kind"] == "none" or not successor_scope:
            raise ValueError(
                "required followup needs a non-none followup_kind and successor_scope"
            )
    elif output["followup_kind"] != "none":
        raise ValueError("followup_kind must be none when no followup is required")
    if output["finding"] == "qualifying_defect" and not followup_required:
        raise ValueError("qualifying_defect requires an explicit followup")
    if (
        output["finding"] == "qualifying_defect"
        and output["finding_lane"] != "correctness_defect"
    ):
        raise ValueError("qualifying_defect must use the correctness_defect lane")
    output["successor_scope"] = successor_scope
    if not str(output.get("next_probe", "")).strip():
        raise ValueError("outcome analyst requires next_probe")
    confidence = output.get("confidence")
    if not isinstance(confidence, int) or isinstance(confidence, bool) or not 0 <= confidence <= 100:
        raise ValueError("outcome analyst confidence must be 0-100")
    attributions = output.get("attribution_hypotheses")
    if not isinstance(attributions, list) or not attributions:
        raise ValueError("outcome analyst requires attribution_hypotheses")
    analysis = _role_artifact(
        role="outcome_analyst",
        call_index=5 + len(cycle.get("outcome_analyses", [])),
        prompt=prompt,
        output=output,
        provider=provider,
    )
    analysis["outcome_id"] = outcome["outcome_id"]
    cycle.setdefault("outcome_analyses", []).append(analysis)
    cycle["latest_mission_disposition"] = output["mission_disposition"]
    cycle["latest_probe_status"] = output["probe_status"]
    cycle["latest_finding"] = output["finding"]
    cycle["latest_followup_required"] = output["followup_required"]
    cycle["live_model_call_count"] = len(cycle.get("artifacts", [])) + len(
        cycle["outcome_analyses"]
    )
    cycle_store.save(cycle)
    from palamedes_thought import ThoughtStore, persist_mission_experience

    persist_mission_experience(
        store=ThoughtStore(mission_store.root.parent / "thoughts"),
        contract=contract,
        outcome=outcome,
        analysis=analysis,
    )
    interpretation = {
        "interpretation_version": "palamedes-outcome-interpretation/1",
        "interpretation_id": f"interpretation-{outcome['outcome_id'][8:]}",
        "outcome_id": outcome["outcome_id"],
        "mission_contract_id": contract["mission_id"],
        "recorded_at": utc_now(),
        "causal_signature": output["causal_signature"],
        "mechanism_summary": output["mechanism_summary"],
        "work_scale": output["work_scale"],
        "surface_key": output["surface_key"],
        "finding_lane": output["finding_lane"],
        "exploration_value": output["exploration_value"],
        "hypothesis_scope": output["hypothesis_scope"],
        "probe_status": output["probe_status"],
        "finding": output["finding"],
        "mission_disposition": output["mission_disposition"],
        "followup_required": output["followup_required"],
        "followup_kind": output["followup_kind"],
        "successor_scope": output["successor_scope"],
        "next_probe": output["next_probe"],
        "confidence": output["confidence"],
        "analysis_fingerprint": analysis["output_fingerprint"],
    }
    mission_store.append_outcome_interpretation(interpretation)
    design_hypothesis = record_design_hypothesis(
        store=prompt_store, interpretation=interpretation
    )
    causal_cluster = record_causal_pattern(
        store=prompt_store, interpretation=interpretation
    )
    prompt_architecture = {"status": "not_applicable"}
    if causal_cluster["meta_shift_required"]:
        try:
            prompt_architecture = run_prompt_architecture(
                provider=provider,
                store=prompt_store,
                cluster=causal_cluster,
                progress=progress,
            )
        except (RuntimeError, ValueError) as exc:
            prompt_architecture = {
                "status": "failed",
                "error": str(exc),
                "causal_cluster_id": causal_cluster["causal_cluster_id"],
            }
    zoom_pattern = record_zoom_pattern(
        store=prompt_store,
        interpretations=mission_store.outcome_interpretations(),
    )
    zoom_prompt_architecture = {"status": "not_applicable"}
    if zoom_pattern["status"] == "required":
        try:
            zoom_prompt_architecture = run_prompt_architecture(
                provider=provider,
                store=prompt_store,
                cluster=zoom_pattern["cluster"],
                progress=progress,
            )
        except (RuntimeError, ValueError) as exc:
            zoom_prompt_architecture = {
                "status": "failed",
                "error": str(exc),
                "causal_cluster_id": zoom_pattern["cluster"][
                    "causal_cluster_id"
                ],
            }
    stored_contract = mission_store.load_contract(contract["mission_id"])
    stored_contract.update(
        {
            "latest_probe_status": output["probe_status"],
            "latest_finding": output["finding"],
            "latest_mission_disposition": output["mission_disposition"],
            "latest_followup_required": output["followup_required"],
            "latest_followup_kind": output["followup_kind"],
            "latest_successor_scope": output["successor_scope"],
        }
    )
    mission_store.save_contract(stored_contract)
    response = contract.get("outcome_response")
    related_outcome_ids = (
        response.get("related_outcome_ids", []) if isinstance(response, dict) else []
    )
    successor_proved = (
        isinstance(response, dict)
        and response.get("action") == "resolve"
        and output["probe_status"] == "completed"
        and output["finding"] == "expected_result"
        and output["mission_disposition"] in {"continue", "stop"}
        and not output["followup_required"]
    )
    if related_outcome_ids and successor_proved:
        for gate in mission_store.open_outcome_gates():
            if gate.get("outcome_id") not in related_outcome_ids:
                continue
            if gate.get("response_mission_contract_id") != contract["mission_id"]:
                continue
            closed_gate = dict(gate)
            closed_gate.update(
                {
                    "status": "responded",
                    "closed_at": utc_now(),
                    "followup_still_required": False,
                    "successor_state": "outcome_verified",
                    "successor_outcome_id": outcome["outcome_id"],
                    "successor_analysis_fingerprint": analysis["output_fingerprint"],
                }
            )
            mission_store.append_outcome_gate(closed_gate)
    if output["mission_disposition"] != "continue" or output["followup_required"]:
        mission_store.append_outcome_gate(
            {
                "gate_version": "palamedes-outcome-gate/3",
                "gate_id": f"gate-{outcome['outcome_id'][8:]}",
                "outcome_id": outcome["outcome_id"],
                "mission_contract_id": contract["mission_id"],
                "probe_status": output["probe_status"],
                "finding": output["finding"],
                "mission_disposition": output["mission_disposition"],
                "followup_required": output["followup_required"],
                "followup_kind": output["followup_kind"],
                "successor_scope": output["successor_scope"],
                "surface_key": output["surface_key"],
                "scope_keys": [f"surface:{output['surface_key']}"],
                "required_response": (
                    output["successor_scope"]
                    if output["followup_required"]
                    else output["next_probe"]
                ),
                "status": "open",
                "opened_at": utc_now(),
            }
        )
    return {
        "status": "completed",
        "analysis": analysis,
        "causal_cluster": causal_cluster,
        "prompt_architecture": prompt_architecture,
        "zoom_pattern": zoom_pattern,
        "zoom_prompt_architecture": zoom_prompt_architecture,
        "design_hypothesis": design_hypothesis,
    }


class ProviderJSONError(ValueError):
    def __init__(self, message: str, custody: Dict[str, Any]) -> None:
        super().__init__(message)
        self.custody = custody


def _balanced_json_object(text: str) -> tuple[str, str]:
    stripped = text.strip()
    fenced = stripped.startswith("```")
    if fenced:
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    start = stripped.find("{")
    if start < 0:
        raise ValueError("response contains no JSON object")
    depth = 0
    in_string = False
    escaped = False
    end = None
    for index, character in enumerate(stripped[start:], start=start):
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                end = index + 1
                break
            if depth < 0:
                break
    if end is None:
        raise ValueError("response contains an unclosed JSON object")
    prefix = stripped[:start].strip()
    suffix = stripped[end:].strip()
    if "{" in prefix or "}" in prefix or "{" in suffix or "}" in suffix:
        raise ValueError("response contains more than one or an ambiguous JSON object")
    mode = "strict"
    if fenced or prefix or suffix:
        mode = "fenced_envelope" if fenced and not prefix and not suffix else "text_envelope"
    return stripped[start:end], mode


def _remove_structural_trailing_commas(candidate: str) -> tuple[str, int]:
    output: List[str] = []
    in_string = False
    escaped = False
    removed = 0
    for index, character in enumerate(candidate):
        if in_string:
            output.append(character)
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
            output.append(character)
            continue
        if character == ",":
            cursor = index + 1
            while cursor < len(candidate) and candidate[cursor].isspace():
                cursor += 1
            if cursor < len(candidate) and candidate[cursor] in "}]":
                removed += 1
                continue
        output.append(character)
    return "".join(output), removed


def _extract_json_object_with_custody(
    text: str,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    custody: Dict[str, Any] = {
        "raw_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "raw_length": len(text),
        "status": "failed",
        "parse_mode": "unparsed",
        "transforms": [],
    }
    try:
        candidate, envelope_mode = _balanced_json_object(text)
        custody["parse_mode"] = envelope_mode
        if envelope_mode != "strict":
            custody["transforms"].append(envelope_mode)
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError as strict_error:
            normalized, removed = _remove_structural_trailing_commas(candidate)
            if not removed:
                raise strict_error
            custody["transforms"].append(
                f"removed_structural_trailing_commas:{removed}"
            )
            custody["parse_mode"] = "trailing_comma_normalized"
            payload = json.loads(normalized)
        if not isinstance(payload, dict):
            raise ValueError("mission response must be a JSON object")
    except (json.JSONDecodeError, ValueError) as exc:
        custody["error"] = f"{type(exc).__name__}: {exc}"
        raise ProviderJSONError(
            f"mission response must be one JSON object: {exc}", custody
        ) from exc
    custody["status"] = "parsed"
    return payload, custody


def _extract_json_object(text: str) -> Dict[str, Any]:
    payload, _ = _extract_json_object_with_custody(text)
    return payload


def validate_mission_draft(payload: Dict[str, Any]) -> Dict[str, Any]:
    errors = []
    for field in MISSION_REQUIRED_FIELDS:
        if field not in payload:
            errors.append(f"{field} is required")
    for field in ("mission", "rationale", "success_metric", "planner_brief"):
        if not isinstance(payload.get(field), str) or not payload.get(field, "").strip():
            errors.append(f"{field} must be a non-empty string")
    for field in ("falsifiers", "non_goals", "constraints"):
        value = payload.get(field)
        if not isinstance(value, list) or not value or not all(
            isinstance(item, str) and item.strip() for item in value
        ):
            errors.append(f"{field} must be a non-empty string array")
    evidence = payload.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append("evidence must be a non-empty array")
        evidence = []
    normalized_evidence = []
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            errors.append(f"evidence[{index}] must be an object")
            continue
        claim = str(item.get("claim", "")).strip()
        source = str(item.get("source", "")).strip()
        confidence = item.get("confidence")
        if not claim or not source:
            errors.append(f"evidence[{index}] requires claim and source")
        if not isinstance(confidence, int) or isinstance(confidence, bool) or not 0 <= confidence <= 100:
            errors.append(f"evidence[{index}].confidence must be an integer from 0 to 100")
        normalized_evidence.append(
            {"claim": claim, "source": source, "confidence": confidence}
        )
    hypotheses = payload.get("hypotheses")
    if not isinstance(hypotheses, list) or not hypotheses:
        errors.append("hypotheses must be a non-empty array")
        hypotheses = []
    normalized_hypotheses = []
    for index, item in enumerate(hypotheses):
        if not isinstance(item, dict):
            errors.append(f"hypotheses[{index}] must be an object")
            continue
        normalized = {
            key: str(item.get(key, "")).strip()
            for key in ("hypothesis", "metric", "target", "window")
        }
        if not all(normalized.values()):
            errors.append(
                f"hypotheses[{index}] requires hypothesis, metric, target, and window"
            )
        normalized_hypotheses.append(normalized)
    next_probe = payload.get("next_probe")
    if not isinstance(next_probe, dict):
        errors.append("next_probe must be an object")
        next_probe = {}
    normalized_probe = {
        key: str(next_probe.get(key, "")).strip()
        for key in ("step", "expected_learning", "expected_result")
    }
    if not all(normalized_probe.values()):
        errors.append(
            "next_probe requires step, expected_learning, and expected_result"
        )
    uncertainty = payload.get("uncertainty", 50)
    if not isinstance(uncertainty, int) or isinstance(uncertainty, bool) or not 0 <= uncertainty <= 100:
        errors.append("uncertainty must be an integer from 0 to 100")
    work_scale = payload.get("work_scale", "unspecified")
    if work_scale not in {
        "unspecified",
        "micro",
        "component",
        "product",
        "service",
        "portfolio",
    }:
        errors.append("work_scale must be a supported planning scale")
    surface_key = str(payload.get("surface_key", "")).strip()
    requirement_id = str(payload.get("requirement_id", "")).strip()
    scope_keys = payload.get("scope_keys", [])
    if not isinstance(scope_keys, list) or not all(
        isinstance(item, str) and item.strip() for item in scope_keys
    ):
        errors.append("scope_keys must be a string array")
        scope_keys = []
    normalized_scope_keys = sorted({item.strip() for item in scope_keys})
    if surface_key:
        normalized_scope_keys = sorted(
            {*normalized_scope_keys, f"surface:{surface_key}"}
        )
    prompt_agenda_response = payload.get("prompt_agenda_response")
    normalized_prompt_agenda_response = None
    if prompt_agenda_response is not None:
        if not isinstance(prompt_agenda_response, dict):
            errors.append("prompt_agenda_response must be an object")
        else:
            agenda_ids = prompt_agenda_response.get("prompt_agenda_ids")
            action = prompt_agenda_response.get("action")
            rationale = str(prompt_agenda_response.get("rationale", "")).strip()
            if not isinstance(agenda_ids, list) or not agenda_ids or not all(
                isinstance(item, str) and item.strip() for item in agenda_ids
            ):
                errors.append("prompt_agenda_response requires prompt_agenda_ids")
            if action != "address" or not rationale:
                errors.append("prompt_agenda_response requires address and rationale")
            if not errors:
                normalized_prompt_agenda_response = {
                    "prompt_agenda_ids": [item.strip() for item in agenda_ids],
                    "action": action,
                    "rationale": rationale,
                }
    product_alignment_response = payload.get("product_alignment_response")
    normalized_product_alignment_response = None
    if product_alignment_response is not None:
        if not isinstance(product_alignment_response, dict):
            errors.append("product_alignment_response must be an object")
        else:
            normalized_product_alignment_response = product_alignment_response
    if errors:
        raise ValueError("invalid mission draft: " + "; ".join(errors))
    normalized_outcome_response = None
    outcome_response = payload.get("outcome_response")
    if outcome_response is not None:
        if not isinstance(outcome_response, dict):
            raise ValueError("invalid mission draft: outcome_response must be an object")
        related_ids = outcome_response.get("related_outcome_ids")
        if not isinstance(related_ids, list) or not all(
            isinstance(item, str) and item.strip() for item in related_ids
        ):
            raise ValueError(
                "invalid mission draft: outcome_response requires related_outcome_ids"
            )
        action = outcome_response.get("action")
        rationale = str(outcome_response.get("rationale", "")).strip()
        if action not in {"resolve", "independent", "accept_debt"} or not rationale:
            raise ValueError(
                "invalid mission draft: outcome_response requires action and rationale"
            )
        normalized_outcome_response = {
            "related_outcome_ids": [item.strip() for item in related_ids],
            "action": action,
            "rationale": rationale,
        }
    normalized = {
        "mission": payload["mission"].strip(),
        "rationale": payload["rationale"].strip(),
        "success_metric": payload["success_metric"].strip(),
        "deadline": str(payload.get("deadline", "")).strip(),
        "evidence": normalized_evidence,
        "hypotheses": normalized_hypotheses,
        "falsifiers": [item.strip() for item in payload["falsifiers"]],
        "non_goals": [item.strip() for item in payload["non_goals"]],
        "constraints": [item.strip() for item in payload["constraints"]],
        "next_probe": normalized_probe,
        "planner_brief": payload["planner_brief"].strip(),
        "uncertainty": uncertainty,
        "work_scale": work_scale,
        "surface_key": surface_key,
        "requirement_id": requirement_id,
        "scope_keys": normalized_scope_keys,
    }
    if normalized_outcome_response is not None:
        normalized["outcome_response"] = normalized_outcome_response
    if normalized_prompt_agenda_response is not None:
        normalized["prompt_agenda_response"] = normalized_prompt_agenda_response
    if normalized_product_alignment_response is not None:
        normalized["product_alignment_response"] = normalized_product_alignment_response
    mission_id = f"mission-{_fingerprint(normalized)[:12]}"
    return {
        "mission_contract_version": "palamedes-chat-mission/1",
        "mission_id": mission_id,
        "status": "draft",
        "created_at": utc_now(),
        **normalized,
        "contract_fingerprint": _fingerprint(normalized),
    }


def mission_prompt(context: str) -> str:
    return f"""Create one mission contract from the user context.
Return exactly one JSON object and no Markdown.

Required shape:
{{
  "mission": "outcome worth pursuing, not a task",
  "rationale": "why this mission now",
  "success_metric": "observable outcome and threshold",
  "deadline": "optional date or review horizon",
  "evidence": [{{"claim": "...", "source": "user|plan|path|URL", "confidence": 0}}],
  "hypotheses": [{{"hypothesis": "...", "metric": "...", "target": "...", "window": "..."}}],
  "falsifiers": ["observable reason to reject or reopen the mission"],
  "non_goals": ["work explicitly excluded"],
  "constraints": ["boundary the planner must preserve"],
  "next_probe": {{
    "step": "smallest information-producing step",
    "expected_learning": "what it should reveal",
    "expected_result": "precommitted observable result"
  }},
  "planner_brief": "semantic handoff for a downstream planner",
  "uncertainty": 50,
  "work_scale": "micro|component|product|service|portfolio",
  "surface_key": "stable product or code surface label",
  "requirement_id": "stable requirement ID when this mission implements or audits one requirement",
  "scope_keys": ["optional stable resource or subsystem scope keys"],
  "product_alignment_response": {{
    "purposes": [{{"purpose_id":"...", "effect":"advances|neutral|conflicts|unknown", "rationale":"..."}}],
    "capability_reuse": {{
      "relevant_capability_ids":["..."],
      "decision":"reuse|extend|new|not_applicable|unknown",
      "rejection_evidence_ids":[],
      "rationale":"..."
    }},
    "integration_gaps": [{{"gap_id":"...", "action":"audit|resolve|accept_debt", "rationale":"..."}}],
    "constraint_review": {{"reviewed_constraint_ids":["..."], "rationale":"..."}},
    "stage_claim": {{"advances_stage":false, "target_stage":"", "journey_evidence_ids":[]}}
  }},
  "outcome_response": {{
    "related_outcome_ids": ["outcome IDs from open evidence gates, when present"],
    "action": "resolve|independent|accept_debt",
    "rationale": "why the next mission resolves, is independent from, or consciously carries the evidence debt; independent and accept_debt do not close required follow-up"
  }}
}}

The prompt_agenda_response field is optional. Omit it entirely unless the user
context supplies one or more concrete IDs beginning with "prompt-agenda-" from
a required fresh-eyes agenda. Question IDs from an advisory vision agenda are
not prompt agenda IDs. When concrete required IDs are present, include:
{{
  "prompt_agenda_response": {{
    "prompt_agenda_ids": ["prompt-agenda-..."],
    "action": "address",
    "rationale": "how this non-micro mission answers the required zoom shift"
  }}
}}
Never emit prompt_agenda_response with an empty array, placeholder IDs, or
advisory question IDs.

Do not invent external evidence. Use source "user" or "plan" for claims from the
provided context. If evidence is weak, preserve that weakness with low
confidence and a falsifying probe. Omit outcome_response only when there are no
open outcome evidence gates.

User context:
{context}"""


def render_mission(contract: Dict[str, Any]) -> str:
    lines = [
        f"Mission draft: {contract['mission_id']}",
        f"  mission: {contract['mission']}",
        f"  rationale: {contract['rationale']}",
        f"  success metric: {contract['success_metric']}",
        f"  uncertainty: {contract['uncertainty']}/100",
        f"  causal role: {contract.get('causal_role', 'direct mission draft')}",
        f"  decision scope: {contract.get('decision_scope', 'not classified')}",
        f"  selection type: {contract.get('selection_type', 'not classified')}",
        "  evidence:",
    ]
    lines.extend(
        f"    - [{item['confidence']}] {item['claim']} ({item['source']})"
        for item in contract["evidence"]
    )
    lines.append("  hypotheses:")
    lines.extend(
        f"    - {item['hypothesis']} | {item['metric']} {item['target']} in {item['window']}"
        for item in contract["hypotheses"]
    )
    lines.append("  falsifiers:")
    lines.extend(f"    - {item}" for item in contract["falsifiers"])
    lines.append("  non-goals:")
    lines.extend(f"    - {item}" for item in contract["non_goals"])
    probe = contract["next_probe"]
    lines.append(f"  next probe: {probe['step']}")
    lines.append(f"  expected learning: {probe['expected_learning']}")
    lines.append("")
    lines.append("Run /approve to persist this mission or /reject <reason> to reject it.")
    return "\n".join(lines)


def latest_mission_id(records: List[Dict[str, Any]], statuses: Optional[set] = None) -> str:
    for record in reversed(records):
        if record.get("type") != "mission_state":
            continue
        if statuses is not None and record.get("status") not in statuses:
            return ""
        mission_id = record.get("mission_id")
        if isinstance(mission_id, str):
            return mission_id
    return ""


def approve_mission(
    palamedes_module: Any,
    mission_store: MissionStore,
    contract: Dict[str, Any],
    session_id: str,
) -> Dict[str, Any]:
    if contract.get("status") != "draft":
        raise ValueError(f"mission is not approvable from status {contract.get('status')}")
    vision_lineage = contract.get("vision_lineage")
    if isinstance(vision_lineage, dict):
        if vision_lineage.get("delivery_authority_granted") is not False:
            raise ValueError("vision lineage cannot grant delivery authority")
        if (
            vision_lineage.get("evidence_maturity") == "speculative"
            and contract.get("work_scale") in {"product", "service", "portfolio"}
        ):
            raise ValueError(
                "speculative vision cannot approve product-scale delivery; "
                "run the selected reality probe first"
            )
        if vision_lineage.get("selected_alternative") == "full_build" and not all(
            vision_lineage.get(field)
            for field in ("renewal_evidence", "kill_criteria", "debt_guard", "scale_guard")
        ):
            raise ValueError("full-build vision lineage lacks renewal and stop evidence")
        if vision_lineage.get("requirement_gate_passed") is not True:
            raise ValueError("vision lineage lacks a passed core-requirement gate")
        expected_alignment = str(
            vision_lineage.get("product_ground_truth_fingerprint", "")
        )
        if not expected_alignment:
            raise ValueError("vision lineage lacks product-ground-truth fingerprint")
        from palamedes_product_alignment import ProductAlignmentStore

        current_alignment = _fingerprint(
            ProductAlignmentStore(
                mission_store.root.parent / "product-alignment"
            ).active_context()
        )
        if current_alignment != expected_alignment:
            raise ValueError(
                "vision lineage is stale after product-ground-truth change; "
                "regenerate the autonomous vision before approval"
            )
        investment_envelope = vision_lineage.get("investment_envelope", {})
        outcome_budget = investment_envelope.get("max_outcomes_before_reassessment")
        if (
            not isinstance(outcome_budget, int)
            or isinstance(outcome_budget, bool)
            or not 1 <= outcome_budget <= 5
        ):
            raise ValueError("vision lineage lacks a valid investment outcome budget")
        vision_id = vision_lineage.get("vision_genesis_id")
        prior_mission_ids = {
            row.get("mission_id")
            for row in mission_store.contracts()
            if row.get("status") in {"approved", "outcome_recorded"}
            and row.get("vision_lineage", {}).get("vision_genesis_id") == vision_id
        }
        realized_outcomes = {
            row.get("mission_contract_id")
            for row in mission_store.outcomes()
            if row.get("mission_contract_id") in prior_mission_ids
        }
        if len(realized_outcomes) >= outcome_budget:
            raise ValueError(
                "vision investment outcome budget exhausted; regenerate the "
                "autonomous vision before approving more work"
            )
        actual = mission_store.vision_investment_summary(str(vision_id))
        exhausted_actual_fields = []
        for actual_field, budget_field in (
            ("engineering_days", "engineering_days_high"),
            ("ai_cost", "ai_cost_high"),
        ):
            budget = investment_envelope.get(budget_field)
            spent = actual[actual_field]
            if isinstance(budget, int) and (
                (budget == 0 and spent > 0) or (budget > 0 and spent >= budget)
            ):
                exhausted_actual_fields.append(actual_field)
        infrastructure_budget = investment_envelope.get(
            "monthly_infrastructure_high"
        )
        infrastructure_peak = actual["monthly_infrastructure_peak"]
        if isinstance(infrastructure_budget, int) and (
            (infrastructure_budget == 0 and infrastructure_peak > 0)
            or infrastructure_peak > infrastructure_budget
        ):
            exhausted_actual_fields.append("monthly_infrastructure")
        if exhausted_actual_fields:
            raise ValueError(
                "vision actual investment budget exhausted for "
                + ", ".join(exhausted_actual_fields)
                + "; regenerate the autonomous vision before approving more work"
            )
    from palamedes_prompt import PromptAgendaStore
    from palamedes_product_alignment import (
        ProductAlignmentStore,
        validate_alignment_response,
    )

    prompt_store = PromptAgendaStore(mission_store.root / "prompt-intelligence")
    alignment_store = ProductAlignmentStore(
        mission_store.root.parent / "product-alignment"
    )
    validate_alignment_response(
        contract,
        alignment_store,
        outcome_count=len(mission_store.outcomes()),
    )
    from palamedes_lifecycle import reconcile_lifecycle
    lifecycle = reconcile_lifecycle(mission_store.root)
    active_handoffs = [
        item for item in lifecycle["items"]
        if item.get("projected_state") in {
            "handed_off", "acknowledged_by_implementer", "executing", "evidence_submitted"
        }
        and item.get("mission_contract_id") != contract.get("mission_id")
    ]
    if active_handoffs:
        active_id = active_handoffs[0].get("mission_contract_id")
        raise ValueError(
            "mission approval blocked: only one active mission is allowed; "
            f"close or record an outcome for {active_id} first"
        )
    requirement_id = str(contract.get("requirement_id", "")).strip()
    if requirement_id:
        from palamedes_satisfaction import SatisfactionStore, assessment_is_current

        assessments = {
            row.get("requirement_id"): row
            for row in SatisfactionStore(
                mission_store.root.parent / "satisfaction"
            ).latest()
        }
        assessment = assessments.get(requirement_id)
        if (
            assessment
            and assessment.get("disposition") == "already_satisfied"
            and assessment_is_current(mission_store.root.parent.parent, assessment)
        ):
            raise ValueError(
                "mission approval blocked: requirement is already satisfied on the "
                f"verified current snapshot ({assessment.get('assessment_id')})"
            )
    blocking_zoom = prompt_store.blocking_zoom_agendas()
    if blocking_zoom:
        response = contract.get("prompt_agenda_response")
        response_ids = (
            response.get("prompt_agenda_ids", []) if isinstance(response, dict) else []
        )
        unresolved = [
            agenda
            for agenda in blocking_zoom
            if agenda["prompt_agenda_id"] not in response_ids
        ]
        if unresolved:
            ids = ", ".join(item["prompt_agenda_id"] for item in unresolved)
            raise ValueError(
                "mission approval blocked by required fresh-eyes agendas: "
                f"{ids}; respond with a component-or-higher research mission"
            )
        if contract.get("work_scale") not in {
            "component",
            "product",
            "service",
            "portfolio",
        }:
            raise ValueError(
                "required fresh-eyes agenda cannot be addressed by another micro mission"
            )
        if response.get("action") != "address":
            raise ValueError("fresh-eyes prompt_agenda_response must address the agenda")
    open_gates = mission_store.open_outcome_gates()
    response = contract.get("outcome_response")
    related_ids = (
        response.get("related_outcome_ids", []) if isinstance(response, dict) else []
    )
    contract_scope_keys = set(contract.get("scope_keys", []))
    contract_surface = str(contract.get("surface_key", "")).strip()
    if contract_surface:
        contract_scope_keys.add(f"surface:{contract_surface}")
    own_mission_key = f"mission:{contract['mission_id']}"
    contract_scope_keys.add(own_mission_key)
    # A contract that declares no scope of its own has produced no evidence that
    # it is unrelated to an open gate, so it cannot narrow the gates that apply.
    # Contracts that do declare a scope are only blocked by intersecting gates.
    contract_declares_scope = bool(contract_scope_keys - {own_mission_key})
    relevant_gates = []
    for gate in open_gates:
        gate_scope_keys = mission_store.outcome_gate_scope_keys(gate)
        if not contract_declares_scope or gate_scope_keys & contract_scope_keys:
            relevant_gates.append(gate)
    if relevant_gates:
        unresolved = [
            gate for gate in relevant_gates if gate.get("outcome_id") not in related_ids
        ]
        if unresolved:
            ids = ", ".join(gate["outcome_id"] for gate in unresolved)
            raise ValueError(
                "mission approval blocked by unresolved outcome evidence: "
                f"{ids}; the draft must explicitly respond to each outcome"
            )
        if response.get("action") not in {"resolve", "independent", "accept_debt"}:
            raise ValueError("outcome_response requires resolve, independent, or accept_debt")
        if not str(response.get("rationale", "")).strip():
            raise ValueError("outcome_response requires a rationale")
    mission_id = contract["mission_id"]
    ts = utc_now()

    def apply(plan: Dict[str, Any]) -> None:
        plan["goal"] = contract["mission"]
        plan["success_metric"] = contract["success_metric"]
        if contract["deadline"]:
            plan["deadline"] = contract["deadline"]
        plan["selected_option"] = contract["mission"]
        plan.setdefault("options", [])
        if contract["mission"] not in plan["options"]:
            plan["options"].append(contract["mission"])
        for constraint in contract["constraints"]:
            if constraint not in plan.setdefault("constraints", []):
                plan["constraints"].append(constraint)
        for item in contract["evidence"]:
            palamedes_module.add_evidence(
                plan,
                item["claim"],
                item["source"],
                item["confidence"],
                "direction_insights",
                metadata={"mission_contract_id": mission_id},
            )
        for item in contract["hypotheses"]:
            plan.setdefault("hypothesis_log", []).append(
                {
                    "ts": ts,
                    **item,
                    "status": "open",
                    "outcome": "",
                    "mission_contract_id": mission_id,
                }
            )
        probe = contract["next_probe"]
        plan.setdefault("development_probes", []).append(
            {
                "id": f"probe-{mission_id[8:]}",
                "ts": ts,
                "step": probe["step"],
                "expected_learning": probe["expected_learning"],
                "expected_result": probe["expected_result"],
                "status": "planned",
                "actual_observation": "",
                "unexpected_observation": "",
                "view_transition_id": "",
                "next_step": "",
                "source": "palamedes-chat-mission",
                "references": [item["source"] for item in contract["evidence"]],
                "mission_contract_id": mission_id,
            }
        )
        if probe["step"] not in plan.setdefault("plan_tasks", []):
            plan["plan_tasks"].append(probe["step"])

    palamedes_module.mutate_plan_state(
        apply,
        event_payloads=[
            {
                "ts": ts,
                "type": "mission_contract_approved",
                "source": "palamedes_chat",
                "mission_contract_id": mission_id,
                "session_id": session_id,
                "contract_fingerprint": contract["contract_fingerprint"],
            }
        ],
        revision_source="palamedes_chat_approve",
        revision_reason=contract["mission"],
    )
    approved = dict(contract)
    approved.update({"status": "approved", "approved_at": ts, "session_id": session_id})
    mission_store.save_contract(approved)
    if blocking_zoom:
        for agenda in blocking_zoom:
            prompt_store.address_agenda(agenda["prompt_agenda_id"], mission_id)
    responded_gates = [
        gate for gate in open_gates if gate.get("outcome_id") in related_ids
    ]
    if responded_gates:
        for gate in responded_gates:
            resolved = dict(gate)
            response_action = response["action"]
            resolved.update(
                {
                    # Selecting a successor is not proof that it worked.
                    "status": "open",
                    "responded_at": ts,
                    "response_mission_contract_id": mission_id,
                    "response_action": response_action,
                    "followup_still_required": bool(gate.get("followup_required", False)),
                    "successor_state": "approved_awaiting_outcome",
                }
            )
            mission_store.append_outcome_gate(resolved)
    handoff = {
        "handoff_version": "palamedes-planner-handoff/1",
        "handoff_id": f"handoff-{mission_id[8:]}",
        "mission_contract_id": mission_id,
        "mission_contract_fingerprint": contract["contract_fingerprint"],
        "issued_at": ts,
        "status": "awaiting_planner",
        "mission": contract["mission"],
        "success_metric": contract["success_metric"],
        "planner_brief": contract["planner_brief"],
        "constraints": contract["constraints"],
        "non_goals": contract["non_goals"],
        "falsifiers": contract["falsifiers"],
        "next_probe": contract["next_probe"],
        "causal_role": contract.get("causal_role", "originated"),
        "decision_scope": contract.get("decision_scope", "tactical_bounded"),
        "selection_type": contract.get("selection_type", "probe"),
        "candidate_fates": contract.get("candidate_fates", []),
        "outcome_response": contract.get("outcome_response"),
        "planner_may_change_mission": False,
        "delivery_authority_granted": False,
    }
    handoff["handoff_fingerprint"] = _fingerprint(handoff)
    handoff_path = mission_store.save_handoff(handoff)
    return {"contract": approved, "handoff": handoff, "handoff_path": handoff_path}


def acknowledge_planner_handoff(
    mission_store: MissionStore,
    mission_id: str,
    planner_id: str,
    acknowledgment: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    handoff = mission_store.load_handoff_for_mission(mission_id)
    ts = utc_now()
    handoff_id = handoff["handoff_id"]
    if not isinstance(acknowledgment, dict):
        acknowledgment = {}

    acknowledged_state = "acknowledged_by_implementer"
    handoff_status = str(handoff.get("status", "")).strip()
    if handoff_status not in {"awaiting_planner", "acknowledged_by_implementer"}:
        raise ValueError(
            f"handoff is not in a planner-awaitable state: {handoff_status}"
        )

    handoff.update(
        {
            "status": acknowledged_state,
            "planner_id": planner_id,
            "planner_acknowledged_at": ts,
            "planner_acknowledgment": acknowledgment,
        }
    )
    handoff["handoff_fingerprint"] = _fingerprint(handoff)
    mission_store.save_handoff(handoff)

    from palamedes_lifecycle import LifecycleStore

    acknowledgment_fingerprint = _fingerprint(
        {"mission_id": mission_id, "planner_id": planner_id, "ts": ts}
    )
    acknowledgment_id = f"planner-ack-{acknowledgment_fingerprint[:12]}"
    lifecycle_event_fingerprint = _fingerprint(
        {
            "handoff_id": handoff_id,
            "planner_id": planner_id,
            "acknowledgment_id": acknowledgment_id,
        }
    )
    event = {
        "event_version": "palamedes-lifecycle-event/1",
        "event_id": f"lifecycle-{lifecycle_event_fingerprint[:16]}",
        "handoff_id": handoff_id,
        "mission_contract_id": mission_id,
        "state": acknowledged_state,
        "source_artifact_ids": sorted({handoff_id, acknowledgment_id}),
        "reason": f"planner {planner_id} acknowledged mission handoff",
        "actor": f"planner:{planner_id}",
        "recorded_at": ts,
    }
    persisted = LifecycleStore(mission_store.root).append(event)
    if not persisted:
        handoff["lifecycle_state_event_ignored"] = True
    return {
        "handoff": handoff,
        "handoff_id": handoff_id,
        "planner_id": planner_id,
        "acknowledgment_id": acknowledgment_id,
        "acknowledged_at": ts,
        "acknowledged_state": acknowledged_state,
        "lifecycle_event_appended": persisted,
        "planner_acknowledgment": acknowledgment,
    }


def _normalize_actual_investment(value: Any) -> Optional[Dict[str, Any]]:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("actual_investment must be an object")
    normalized: Dict[str, Any] = {}
    for field in (
        "engineering_days",
        "ai_cost",
        "monthly_infrastructure",
    ):
        amount = value.get(field, 0)
        if (
            not isinstance(amount, (int, float))
            or isinstance(amount, bool)
            or amount < 0
        ):
            raise ValueError(f"actual_investment {field} must be non-negative")
        normalized[field] = float(amount)
    for field in ("input_tokens", "output_tokens"):
        amount = value.get(field, 0)
        if not isinstance(amount, int) or isinstance(amount, bool) or amount < 0:
            raise ValueError(f"actual_investment {field} must be a non-negative integer")
        normalized[field] = amount
    evidence_source = str(value.get("evidence_source", "")).strip()
    if evidence_source not in {"measured", "invoice", "estimate", "unknown"}:
        raise ValueError(
            "actual_investment evidence_source must be measured, invoice, estimate, or unknown"
        )
    normalized["evidence_source"] = evidence_source
    normalized["notes"] = str(value.get("notes", "")).strip()
    return normalized


def record_mission_outcome(
    palamedes_module: Any,
    mission_store: MissionStore,
    contract: Dict[str, Any],
    status: str,
    observation: str,
    actual_investment: Optional[Dict[str, Any]] = None,
    outcome_type: str = "",
    execution_status: str = "completed",
) -> Dict[str, Any]:
    if contract.get("status") not in {"approved", "outcome_recorded"}:
        raise ValueError("outcomes require an approved mission")
    if status not in {"success", "failure", "mixed", "unknown"}:
        raise ValueError("outcome status must be success, failure, mixed, or unknown")
    if execution_status not in {"completed", "failed", "blocked", "skipped"}:
        raise ValueError(
            "execution_status must be completed, failed, blocked, or skipped"
        )
    allowed_types = {
        "validated_improvement", "null_finding", "already_satisfied",
        "adverse_result", "insufficient_evidence", "blocked_by_environment",
        "misaligned_mission", "prototype_only",
    }
    if not outcome_type:
        outcome_type = {
            "success": "validated_improvement",
            "failure": "adverse_result",
            "mixed": "insufficient_evidence",
            "unknown": "insufficient_evidence",
        }[status]
    if outcome_type not in allowed_types:
        raise ValueError("unsupported honest outcome_type")
    if outcome_type == "blocked_by_environment" and status != "unknown":
        raise ValueError("blocked_by_environment requires unknown status")
    ts = utc_now()
    mission_id = contract["mission_id"]
    normalized_investment = _normalize_actual_investment(actual_investment)
    outcome = {
        "outcome_version": "palamedes-mission-outcome/2",
        "outcome_id": f"outcome-{uuid.uuid4().hex[:12]}",
        "mission_contract_id": mission_id,
        "mission_contract_fingerprint": contract["contract_fingerprint"],
        "recorded_at": ts,
        "execution_status": execution_status,
        "evaluation_status": "not_evaluated",
        "reported_outcome_status": status,
        "status": status,
        "outcome_type": outcome_type,
        "observation": observation,
        "attribution": "unresolved",
        "evidence_source_type": "implementer_claim",
        "may_rewrite_prior_history": False,
    }
    if normalized_investment is not None:
        outcome["actual_investment"] = normalized_investment

    def apply(plan: Dict[str, Any]) -> None:
        palamedes_module.add_evidence(
            plan,
            observation,
            "mission-outcome",
            80 if status != "unknown" else 50,
            "evolution_insights",
            metadata={
                "mission_contract_id": mission_id,
                "outcome_id": outcome["outcome_id"],
                "outcome_status": status,
                "execution_status": execution_status,
                "evaluation_status": "not_evaluated",
                "outcome_type": outcome_type,
            },
        )
        for probe in reversed(plan.get("development_probes", [])):
            if probe.get("mission_contract_id") == mission_id:
                probe["status"] = "completed"
                probe["actual_observation"] = observation
                break
        for hypothesis in plan.get("hypothesis_log", []):
            if hypothesis.get("mission_contract_id") == mission_id:
                hypothesis["outcome"] = observation
                # An implementer-reported outcome is evidence for later
                # evaluation, not an evaluator verdict. Preserve the current
                # hypothesis state until an explicit evaluation resolves it.
                hypothesis["status"] = hypothesis.get("status", "open")

    palamedes_module.mutate_plan_state(
        apply,
        event_payloads=[
            {
                "ts": ts,
                "type": "mission_outcome_recorded",
                "source": "palamedes_chat",
                "mission_contract_id": mission_id,
                "outcome_id": outcome["outcome_id"],
                "status": status,
                "execution_status": execution_status,
                "evaluation_status": "not_evaluated",
                "outcome_type": outcome_type,
            }
        ],
        revision_source="palamedes_chat_outcome",
        revision_reason=observation,
    )
    mission_store.append_outcome(outcome)
    from palamedes_thought import ThoughtStore, persist_mission_experience

    persist_mission_experience(
        store=ThoughtStore(mission_store.root.parent / "thoughts"),
        contract=contract,
        outcome=outcome,
    )
    updated = dict(contract)
    updated.update(
        {
            "status": "outcome_recorded",
            "latest_outcome_id": outcome["outcome_id"],
            "latest_outcome_status": status,
            "latest_execution_status": execution_status,
            "latest_evaluation_status": "not_evaluated",
        }
    )
    mission_store.save_contract(updated)
    return outcome


def _plan_context_views(palamedes_module: Any) -> Dict[str, Dict[str, Any]]:
    """Split purpose evidence from path-dependent execution context.

    Mission origination must not silently inherit the currently selected option or
    the local development frontier.  Those facts remain useful, but only after a
    candidate frontier exists and can be attacked for feasibility and drift.
    """
    palamedes_module.ensure_state()
    plan = palamedes_module.load_plan()
    strategic = {
        "goal": plan.get("goal", ""),
        "success_metric": plan.get("success_metric", ""),
        "constraints": plan.get("constraints", []),
        "open_hypotheses": [
            item
            for item in plan.get("hypothesis_log", [])
            if item.get("status") == "open"
        ][-5:],
        "open_questions": plan.get("open_questions", [])[-5:],
    }
    path_dependent = {
        "selected_option": plan.get("selected_option", ""),
        "recent_view_transitions": plan.get("view_transitions", [])[-3:],
        "development_probes": plan.get("development_probes", [])[-5:],
        "plan_tasks": plan.get("plan_tasks", [])[-20:],
        "execution_tasks": plan.get("execution_tasks", [])[-20:],
        "phase_plan": plan.get("phase_plan", [])[-10:],
    }
    return {
        "strategic": strategic,
        "path_dependent": path_dependent,
        "exposure_policy": {
            "context_governor": ["user_context", "strategic"],
            "interpreter": ["clean_room_brief"],
            "inventor": ["interpreter_artifact"],
            "adversary": [
                "interpreter_artifact",
                "inventor_artifact",
                "path_dependent",
                "classified_preferences_and_examples",
            ],
            "selector": ["frozen_candidates", "adversary_artifact"],
        },
    }


def _plan_context(palamedes_module: Any) -> str:
    """Return the bounded strategic view used by the conversational pre-planner."""
    return json.dumps(
        _plan_context_views(palamedes_module)["strategic"],
        ensure_ascii=False,
        sort_keys=True,
    )


def system_prompt(
    palamedes_module: Any,
    workspace: Path,
    team_context: Optional[Dict[str, Any]] = None,
) -> str:
    team_section = ""
    if team_context is not None:
        team_section = (
            "\nShared team cognition (plural evidence, not managerial authority):\n"
            + json.dumps(team_context, ensure_ascii=False, sort_keys=True)
            + "\n"
        )
    return f"""You are Palamedes, an autonomous pre-planner operating before planner -> task -> implementation.

Your job is to notice what matters, form competing interpretations, originate worthwhile candidate missions, attack your own assumptions, and recommend the smallest informative next move.

Do not claim that retrieval, debate, novelty, or confidence proves quality. Separate observation, inference, value judgment, and commitment. State uncertainty and falsifiers. Preserve useful disagreement. Prefer a blocked or deferred conclusion over unsupported authority.

You are plan-only in this terminal. You may propose mission contracts, evidence, probes, and plan changes, but you cannot claim that files, plans, or external systems were changed unless the user explicitly runs an available CLI command and observes its result.

Workspace: {workspace}
Current bounded Palamedes plan context:
{_plan_context(palamedes_module)}
{team_section}
"""


def _history_messages(records: List[Dict[str, Any]], limit: int) -> List[Dict[str, str]]:
    messages = []
    for record in records:
        role = record.get("role")
        content = record.get("content")
        if role in {"user", "assistant"} and isinstance(content, str):
            messages.append({"role": role, "content": content})
    return messages[-limit:]


def _print_help(output: TextIO) -> None:
    output.write(
        "\n".join(
            [
                "Commands:",
                "  /think <topic>       explore the missing mode of thought",
                "  /challenge <claim>   attack assumptions and define falsifiers",
                "  /research <question> identify the minimum missing evidence",
                "  /mission <context>   draft a mission contract",
                "  /cycle <context>     run interpreter→inventor→adversary→selector",
                "  /cycle --mode audit <context>",
                "                       run the four roles without automatic Vision or meta-learning calls",
                "  /cycle --mode lookup|micro|component|product <context>",
                "                       override the deterministic cost-adaptive preflight",
                "  /cycle --resume <cycle-id>",
                "  /context-ablation <cycle-id>  compare clean-room vs continuity reasoning",
                "                       resume a failed/interrupted run from verified checkpoints",
                "  /invent <context>    discover structurally new product possibilities without committing",
                "  /inventions          show the latest product invention",
                "  /opportunity <context>",
                "                       inspect product, growth, revenue, content, social, and risk perspectives",
                "  /opportunities       show the latest multi-perspective opportunity scan",
                "  /invent-commit <candidate-id> <reason>  human-select a frontier candidate",
                "  /invent-observations  list open observation requirements from failed tests",
                "  /invent-observe <observation-id> <evidence>  resolve one requirement",
                "  /pursue <objective>  compose a domain-general evidence-producing pursuit",
                "  /pursuits            show the latest pursuit",
                "  /vision <context>    force a desire→analogy→fusion→world vision cycle",
                "  /vision-scout <context>",
                "                       originate a low-cost upstream founder prompt",
                "  /vision-scout-promote <vision-scout-id>",
                "                       run full Genesis only after independent-human gate",
                "  /vision-scout-review-next",
                "                       show the least-reviewed standalone project packet",
                "  /vision-scout-review-submit <packet-id> <JSON>",
                "                       record one absolute blind project review",
                "  /vision-scout-probe <vision-scout-id> <JSON>",
                "                       preregister one bounded behavioral test",
                "  /vision-scout-probe-outcome <vision-scout-id> <JSON>",
                "                       record the single attributable measured result",
                "  /visions             show the latest autonomous product vision",
                "  /vision-benchmark [collection|fusion|social]",
                "  /vision-scout-benchmark [collection|fusion|social]",
                "  /vision-agenda-ablation [case] [challenger] [comparator]",
                "                       run a hidden-human-reference origination case",
                "  /vision-holdout-import <case.json>",
                "                       import an external-human private holdout case",
                "  /vision-benchmark holdout:<case-id>",
                "                       run one imported holdout without revealing its reference",
                "  /vision-benchmark-suite [all|collection|fusion|social] [1-5]",
                "                       repeat blinded cases and preserve distinct trials",
                "  /vision-benchmark-summary",
                "                       aggregate machine scores, custody, and diversity",
                "  /vision-review-submit <packet-id> <JSON>",
                "                       record one blinded human A/B judgment",
                "  /vision-review-next show the least-reviewed blinded packet",
                "  /vision-review-bundle",
                "                       build an offline answer-key-free review page",
                "  /vision-review-import <response.json>",
                "                       validate and import a downloaded review response",
                "  /vision-review-summary",
                "                       aggregate resolved human preference evidence",
                "  /vision-review-gate show cross-case independent-human evidence gate",
                "  /observe             collect project, Git, state, TODO, and ref signals",
                "  /reference-intelligence [path]",
                "                       build a source-bounded self-model and research agenda",
                "  /satisfaction-json <JSON> host-verify one requirement evidence bundle",
                "  /satisfactions      show latest host-verified requirement assessments",
                "  /alignment-candidate-json <JSON> propose surface product ground truth",
                "  /alignment-approve <candidate-id> approve and merge one candidate",
                "  /alignment          show active surface product ground truth",
                "  /storage            inspect retention classes and duplicate bytes without mutation",
                "  /reconcile           audit lifecycle projection without writes",
                "  /reconcile --apply <proposal-fingerprint>",
                "                       append only the exact freshly reviewed proposal set",
                "  /backfill-outcomes N map up to 24 legacy outcomes into meta-learning fields",
                "  /preview             inspect the latest mission draft",
                "  /approve             persist the draft and create planner handoff",
                "  /reject <reason>     reject the latest draft without rewriting it",
                "  /handoff             show the latest planner handoff",
                "  /planner-ack <planner-id> <JSON>",
                "                       acknowledge a planner handoff to advance the handoff state",
                "  /outcome [mission-id] <status> <observation>",
                "                       record success|failure|mixed|unknown",
                "  /outcome-json <JSON> record outcome plus measured investment",
                "  /wait-external <mission-id> <evidence needed>",
                "  /external-evidence <gate-id> <observation>",
                "  /status              show provider, model, workspace, and session",
                "  /history             show persisted turns in this session",
                "  /sessions            list local session IDs",
                "  /new                  start a new persisted session",
                "  /help                 show this help",
                "  /quit                 exit",
                "",
            ]
        )
    )


def run_autonomous_vision(
    *, provider: ChatProvider, mission_store: MissionStore, context: str
) -> Dict[str, Any]:
    from palamedes_vision import VisionStore, run_vision_genesis

    vision_store = VisionStore(mission_store.root.parent / "visions")
    role_usage: List[Dict[str, Any]] = []
    attempt_id = f"vision-attempt-{_fingerprint({'context': context, 'outcome_count': len(mission_store.outcomes())})[:12]}"
    checkpoint = vision_store.checkpoint(attempt_id)
    active_role = ""
    active_role_was_fresh = False

    def ask(role: str, prompt: str) -> Dict[str, Any]:
        nonlocal active_role, active_role_was_fresh
        active_role = role
        active_role_was_fresh = False
        cached = checkpoint.get("roles", {}).get(role)
        if isinstance(cached, dict) and isinstance(cached.get("output"), dict):
            usage = dict(cached.get("usage", {}))
            usage["checkpoint_reused"] = True
            role_usage.append(usage)
            return dict(cached["output"])
        output: Optional[Dict[str, Any]] = None
        try:
            output = _provider_json(
                provider,
                system=(
                    f"ROLE: {role}. You originate product possibilities but grant no "
                    "delivery authority. Return exactly one JSON object."
                ),
                prompt=f"ROLE: {role}\n{prompt}",
            )
            active_role_was_fresh = True
            return output
        finally:
            usage = _capture_provider_usage(provider, role)
            role_usage.append(usage)
            if output is not None:
                vision_store.save_checkpoint(attempt_id, role, output, usage)
                checkpoint.setdefault("roles", {})[role] = {
                    "output": output,
                    "usage": usage,
                }

    try:
        record = run_vision_genesis(
            ask=ask,
            store=vision_store,
            context=context,
            outcome_count=len(mission_store.outcomes()),
        )
    except ValueError:
        if active_role_was_fresh:
            vision_store.discard_checkpoint_role(attempt_id, active_role)
        raise
    record["provider_usage"] = _provider_usage_summary(provider, role_usage)
    vision_store.save(record)
    return record


def run_autonomous_invention(
    *, provider: ChatProvider, mission_store: MissionStore, context: str
) -> Dict[str, Any]:
    from palamedes_invention import ProductInventionStore, fingerprint, run_product_invention

    invention_store = ProductInventionStore(mission_store.root.parent / "inventions")
    role_usage: List[Dict[str, Any]] = []

    def ask(role: str, prompt: str) -> Dict[str, Any]:
        try:
            return _provider_json(
                provider,
                system=(
                    f"ROLE: {role}. Discover or test product possibilities without confusing "
                    "novel wording with structural invention. Never select delivery work or grant "
                    "design, mission, or delivery authority. Return exactly one JSON object."
                ),
                prompt=f"ROLE: {role}\n{prompt}",
            )
        finally:
            role_usage.append(_capture_provider_usage(provider, role))

    def _parse_coverage_gate_payload(
        prompt: str,
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        marker_candidates = "Candidate payload:\n"
        candidates_split = prompt.split(marker_candidates, 1)
        if len(candidates_split) != 2:
            raise ValueError("baseline coverage judge prompt missing candidate payload")
        try:
            payload = json.loads(candidates_split[1].strip())
        except json.JSONDecodeError as exc:
            raise ValueError(
                "baseline coverage judge candidate payload is invalid JSON"
            ) from exc
        baseline = payload.get("conventional_baseline")
        if not isinstance(baseline, dict):
            raise ValueError(
                "baseline coverage judge payload must carry a conventional_baseline"
            )
        candidates = payload.get("candidates")
        if not isinstance(candidates, list):
            raise ValueError(
                "baseline coverage judge payload must be an object with candidates"
            )
        return baseline, candidates

    def judge_ask(role: str, prompt: str) -> Dict[str, Any]:
        if role != "invention_baseline_coverage_judge":
            raise ValueError(f"unsupported coverage judge role: {role}")
        baseline, candidates = _parse_coverage_gate_payload(prompt)
        baseline_text = json.dumps(baseline, ensure_ascii=False, sort_keys=True)

        assessments: List[Dict[str, Any]] = []
        for candidate in candidates:
            candidate_id = str(candidate.get("candidate_id", "")).strip()
            thesis = str(candidate.get("thesis", "")).strip()
            if not candidate_id:
                raise ValueError(
                    "baseline coverage judge candidate payload missing candidate_id"
                )
            if not thesis:
                assessments.append(
                    {
                        "candidate_id": candidate_id,
                        "covered_by_conventional_baseline": False,
                        "generic_solution_pack": True,
                        "reason": "candidate has no thesis text",
                    }
                )
                continue

            judgment = _provider_json(
                provider,
                system=(
                    "ROLE: baseline_coverage_judge. Decide whether a candidate is "
                    "already produced by the conventional baseline and return exactly "
                    "one JSON object."
                ),
                prompt=(
                    "ROLE: baseline_coverage_judge\n"
                    "Decide whether this candidate is already covered by the "
                    "conventional baseline, meaning a competent planner working from "
                    "the same input would have reached its mechanism anyway. Familiar "
                    "components are not coverage; changing a mechanism the baseline "
                    "holds fixed is not coverage. Return:\n"
                    "{\n"
                    '  "covered_by_conventional_baseline":false,\n'
                    '  "generic_request":false,\n'
                    '  "rationale":"..."\n'
                    "}\n"
                    "covered_by_conventional_baseline and generic_request must be JSON "
                    "booleans, never strings, numbers, or scores. generic_request is "
                    "true only when the candidate would transfer unchanged to an "
                    "unrelated service.\n\n"
                    f"Conventional baseline:\n{baseline_text}\n\n"
                    f"Candidate:\n{thesis}"
                ),
            )
            role_usage.append(
                _capture_provider_usage(provider, "baseline_coverage_judge")
            )

            covered = judgment.get("covered_by_conventional_baseline")
            generic_pack = judgment.get("generic_request")
            if not isinstance(covered, bool) or not isinstance(generic_pack, bool):
                raise ValueError(
                    "baseline coverage judge returned malformed boolean fields"
                )
            reason = str(judgment.get("rationale", "")).strip()
            assessments.append(
                {
                    "candidate_id": candidate_id,
                    "covered_by_conventional_baseline": covered,
                    "generic_solution_pack": generic_pack,
                    "reason": reason
                    or "baseline coverage judge did not provide rationale",
                }
            )

        return {
            "coverage_assessments": assessments,
            "empty_frontier_reason": (
                "baseline coverage judge evaluated all candidates against the "
                "conventional baseline"
            ),
        }

    open_requirements = invention_store.open_observation_requirements()
    enriched_context = context
    if open_requirements:
        bounded_requirements = [
            {
                "observation_requirement_id": row.get("observation_requirement_id"),
                "source_type": row.get("source_type"),
                "observation_needed": row.get("observation_needed"),
                "reason": row.get("reason"),
            }
            for row in open_requirements[-12:]
        ]
        enriched_context += (
            "\n\nOPEN OBSERVATION REQUIREMENTS FROM PRIOR FAILED OR INCONCLUSIVE "
            "EXPLORATION:\n" + json.dumps(bounded_requirements, ensure_ascii=False)
        )
    try:
        record = run_product_invention(
            ask=ask,
            judge_ask=judge_ask,
            store=invention_store,
            context=enriched_context,
        )
    except ValueError as exc:
        invention_store.record_observation_requirement(
            source_type="runtime_contract_failure",
            observation_needed=(
                "Determine whether this repeated provider-contract failure reveals a "
                "prompt ambiguity, over-strict validator, or missing normalization: "
                f"{exc}"
            ),
            reason="The invention cycle stopped before preserving a usable frontier.",
            context_fingerprint=fingerprint(context),
        )
        raise
    record["provider_usage"] = _provider_usage_summary(provider, role_usage)
    invention_store.save(record)
    return record


def build_autonomous_invention_context(
    *, user_context: str, workspace_context: Dict[str, Any]
) -> str:
    """Ground invention in bounded product reality without granting delivery authority."""
    contract = {
        "invention_context_version": "palamedes-invention-context/1",
        "user_context": user_context,
        "bounded_workspace_context": workspace_context,
        "discovery_focus": [
            "capabilities implemented but absent from user or operator surfaces",
            "user value delivered without retention, progression, or value-capture loops",
            "content and production assets without distribution or replenishment loops",
            "paid promises without fulfillment, recovery, measurement, or administration",
            "non-obvious combinations that create more than additive value",
        ],
        "guardrails": [
            "Do not equate code presence with validated user value.",
            "Do not force monetization onto safety, privacy, or essential account controls.",
            "Do not use fake scarcity, dark patterns, or pay-to-win pressure.",
            "Separate confirmed repository facts, inference, and unverified market hypotheses.",
            "Do not turn the exploration frontier into implementation tasks.",
        ],
    }
    return json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True)


def build_opportunity_experience_archive(
    mission_store: MissionStore,
) -> List[Dict[str, Any]]:
    """Project immutable outcomes and bounded interpretations into a scout archive."""
    contracts = {
        str(row.get("mission_id", "")).strip(): row
        for row in mission_store.contracts()
        if str(row.get("mission_id", "")).strip()
    }
    interpretations = {
        str(row.get("outcome_id", "")).strip(): row
        for row in mission_store.outcome_interpretations()
        if str(row.get("outcome_id", "")).strip()
    }
    archive = []
    for outcome in mission_store.outcomes():
        outcome_id = str(outcome.get("outcome_id", "")).strip()
        if not outcome_id:
            continue
        mission_id = str(outcome.get("mission_contract_id", "")).strip()
        contract = contracts.get(mission_id, {})
        interpretation = interpretations.get(outcome_id, {})
        observed = {
            field: outcome[field]
            for field in (
                "recorded_at",
                "execution_status",
                "reported_outcome_status",
                "status",
                "outcome_type",
                "observation",
                "evidence_source_type",
                "attribution",
                "actual_investment",
            )
            if field in outcome
        }
        interpreted = {
            field: interpretation[field]
            for field in (
                "causal_signature",
                "mechanism_summary",
                "work_scale",
                "surface_key",
                "finding_lane",
                "probe_status",
                "finding",
                "mission_disposition",
                "followup_required",
                "followup_kind",
                "successor_scope",
                "next_probe",
                "confidence",
            )
            if field in interpretation
        }
        archive.append({
            "experience_id": outcome_id,
            "mission_contract_id": mission_id,
            "decision_context": {
                field: contract[field]
                for field in (
                    "mission",
                    "rationale",
                    "success_metric",
                    "hypotheses",
                    "falsifiers",
                    "constraints",
                    "next_probe",
                    "decision_scope",
                    "selection_type",
                    "causal_role",
                    "implementation_state_at_start",
                    "candidate_fates",
                )
                if field in contract
            },
            "observed": observed,
            "interpreted": interpreted,
            "epistemic_boundary": {
                "observed_is_immutable_report": True,
                "interpretation_is_analysis_not_observation": True,
                "attribution_may_remain_unresolved": True,
            },
        })
    return sorted(
        archive,
        key=lambda row: (
            str(row.get("observed", {}).get("recorded_at", "")),
            row["experience_id"],
        ),
    )


def run_autonomous_opportunity_scout(
    *, provider: ChatProvider, mission_store: MissionStore, context: str
) -> Dict[str, Any]:
    from palamedes_opportunity import OpportunityStore, run_opportunity_scout

    opportunity_store = OpportunityStore(mission_store.root.parent / "opportunities")
    role_usage: List[Dict[str, Any]] = []

    def ask(role: str, prompt: str) -> Dict[str, Any]:
        try:
            return _provider_json(
                provider,
                system=(
                    f"ROLE: {role}. Find product-specific strategic opportunities by "
                    "connecting multiple perspectives and tracing second-order effects. "
                    "Preserve useful established patterns when their causal fit is "
                    "grounded. Never present an interpretation as an observed outcome or "
                    "invent experience that is absent from the bounded archive. Return "
                    "exactly one JSON object."
                ),
                prompt=f"ROLE: {role}\n{prompt}",
            )
        finally:
            role_usage.append(_capture_provider_usage(provider, role))

    record = run_opportunity_scout(
        ask=ask,
        store=opportunity_store,
        context=context,
        experiences=build_opportunity_experience_archive(mission_store),
    )
    record["provider_usage"] = _provider_usage_summary(provider, role_usage)
    opportunity_store.save(record)
    return record


def run_autonomous_pursuit(
    *, provider: ChatProvider, mission_store: MissionStore, objective: str
) -> Dict[str, Any]:
    from palamedes_pursuit import PursuitStore, run_pursuit

    pursuit_store = PursuitStore(mission_store.root.parent / "pursuits")
    role_usage: List[Dict[str, Any]] = []

    def ask(role: str, prompt: str) -> Dict[str, Any]:
        try:
            return _provider_json(
                provider,
                system=(
                    f"ROLE: {role}. Compose rigorous intellectual work without fabricating "
                    "uncollected evidence or silently taking external action. Return one JSON object."
                ),
                prompt=f"ROLE: {role}\n{prompt}",
            )
        finally:
            role_usage.append(_capture_provider_usage(provider, role))

    record = run_pursuit(ask=ask, store=pursuit_store, objective=objective)
    record["provider_usage"] = _provider_usage_summary(provider, role_usage)
    pursuit_store.save(record)
    return record


def run_autonomous_vision_scout(
    *,
    provider: ChatProvider,
    mission_store: MissionStore,
    context: str,
    request_context: str = "",
) -> Dict[str, Any]:
    from palamedes_vision import fingerprint
    from palamedes_vision_scout import VisionScoutStore, run_vision_scout

    scout_store = VisionScoutStore(mission_store.root.parent / "vision-scouts")
    request_fingerprint = fingerprint(request_context) if request_context else ""
    existing = (
        scout_store.find_by_request_fingerprint(request_fingerprint)
        if request_fingerprint
        else scout_store.find_by_context(context)
    )
    if existing is not None:
        packet = scout_store.ensure_project_review_packet(existing["vision_scout_id"])
        if packet is not None and not existing.get("project_human_review_packet_id"):
            existing = dict(existing)
            existing["project_human_review_packet_id"] = packet[
                "vision_scout_project_review_id"
            ]
            scout_store.save(existing)
        reused = dict(existing)
        reused["reused_existing_context"] = True
        return reused
    role_usage: List[Dict[str, Any]] = []
    attempt = scout_store.reserve_project_attempt(
        request_fingerprint=request_fingerprint or fingerprint(context),
        context_fingerprint=fingerprint(context),
    )
    checkpoint = scout_store.project_checkpoint(attempt["attempt_id"])

    def ask(role: str, prompt: str) -> Dict[str, Any]:
        cached = checkpoint.get("roles", {}).get(role)
        if isinstance(cached, dict) and isinstance(cached.get("output"), dict):
            cached_usage = dict(cached.get("usage", {}))
            cached_usage["checkpoint_reused"] = True
            role_usage.append(cached_usage)
            return dict(cached["output"])
        output: Optional[Dict[str, Any]] = None
        usage: Dict[str, Any]
        try:
            output = _provider_json(
                provider,
                system=(
                    f"ROLE: {role}. Originate upstream product direction but grant no "
                    "full-Genesis or delivery authority. Return exactly one JSON object."
                ),
                prompt=f"ROLE: {role}\n{prompt}",
            )
        finally:
            usage = _capture_provider_usage(provider, role)
            role_usage.append(usage)
        scout_store.save_project_checkpoint(
            attempt["attempt_id"], role, output, usage
        )
        checkpoint.setdefault("roles", {})[role] = {
            "output": output,
            "usage": usage,
        }
        return output

    try:
        record = run_vision_scout(ask=ask, store=scout_store, context=context)
    except Exception as exc:
        scout_store.fail_project_attempt(
            attempt,
            _provider_usage_summary(provider, role_usage),
            exc,
        )
        raise
    if request_fingerprint:
        record["request_fingerprint"] = request_fingerprint
    record["provider_usage"] = _provider_usage_summary(provider, role_usage)
    packet = scout_store.ensure_project_review_packet(record["vision_scout_id"])
    if packet is not None:
        record["project_human_review_packet_id"] = packet[
            "vision_scout_project_review_id"
        ]
    scout_store.save(record)
    scout_store.complete_project_attempt(
        attempt, record["vision_scout_id"], record["provider_usage"]
    )
    return record


def build_autonomous_vision_context(
    *,
    mission_store: MissionStore,
    user_context: str,
    workspace_context: Dict[str, Any],
) -> str:
    from palamedes_product_alignment import ProductAlignmentStore
    from palamedes_vision import VisionStore

    alignment = ProductAlignmentStore(
        mission_store.root.parent / "product-alignment"
    ).active_context()
    latest_vision = VisionStore(
        mission_store.root.parent / "visions"
    ).latest()
    prior_vision_investment = {}
    if isinstance(latest_vision, dict):
        prior_vision_id = str(latest_vision.get("vision_genesis_id", ""))
        prior_vision_investment = {
            "vision_genesis_id": prior_vision_id,
            "actual_delivery_investment": (
                mission_store.vision_investment_summary(prior_vision_id)
                if prior_vision_id
                else {}
            ),
            "palamedes_provider_usage": latest_vision.get("provider_usage", {}),
            "prior_investment_envelope": latest_vision.get(
                "investment_envelope", {}
            ),
        }
    contract = {
        "vision_context_version": "palamedes-vision-context/1",
        "user_context": user_context,
        "bounded_workspace_context": workspace_context,
        "product_ground_truth": alignment,
        "open_outcome_evidence_gates": mission_store.open_outcome_gates(),
        "outcome_count": len(mission_store.outcomes()),
        "prior_vision_investment": prior_vision_investment,
        "interpretation_rules": [
            "Product invariants outrank a locally polished implementation.",
            "Existing capabilities must be considered before greenfield invention.",
            "Temporary constraints must not be promoted into permanent product intent.",
            "Open integration gaps are product evidence, not permission to redefine scope.",
            "Unknown market, cost, safety, or human-behavior claims remain hypotheses.",
        ],
    }
    return json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True)


def compact_vision_scout_context(context: str) -> str:
    """Bound project observation for the three-call Scout without hiding custody."""
    try:
        contract = json.loads(context)
    except json.JSONDecodeError:
        return context
    if not isinstance(contract, dict) or not isinstance(
        contract.get("bounded_workspace_context"), dict
    ):
        return context
    workspace = contract["bounded_workspace_context"]
    documents = []
    for row in workspace.get("documents", [])[:16]:
        if not isinstance(row, dict):
            continue
        documents.append(
            {
                "path": row.get("path", ""),
                "content_sha256": row.get("content_sha256", ""),
                "headings": row.get("headings", [])[:12],
                "excerpt": str(row.get("excerpt", ""))[:320],
                "excerpt_truncated_for_scout": len(str(row.get("excerpt", ""))) > 320,
            }
        )
    git = workspace.get("git", {}) if isinstance(workspace.get("git"), dict) else {}
    state = (
        workspace.get("palamedes_state", {})
        if isinstance(workspace.get("palamedes_state"), dict)
        else {}
    )
    todos = workspace.get("todos", {}) if isinstance(workspace.get("todos"), dict) else {}
    compact_workspace = {
        "change": workspace.get("change", {}),
        "documents": documents,
        "git": {
            "available": git.get("available"),
            "branch": git.get("branch", ""),
            "head": git.get("head", ""),
            "recent_commits": git.get("recent_commits", [])[:5],
            "diff_stat": git.get("diff_stat", [])[:20],
            "status": git.get("status", [])[:40],
        },
        "palamedes_plan_summary": (
            state.get("plan", {}).get("summary", {})
            if isinstance(state.get("plan"), dict)
            else {}
        ),
        "todos": {
            "items": todos.get("items", [])[:12],
            "truncated": todos.get("truncated", False),
        },
        "reference_root": workspace.get("reference_root", {}),
        "test": workspace.get("test", {}),
    }
    compact = dict(contract)
    compact["bounded_workspace_context"] = compact_workspace
    compact["scout_context_compaction"] = {
        "version": "palamedes-vision-scout-context-compaction/1",
        "full_context_fingerprint": _fingerprint(context),
        "document_excerpt_limit_chars": 320,
        "omitted_ephemeral_fields": [
            "observation_id",
            "observed_at",
            "event_and_revision_file_metadata",
        ],
    }
    return json.dumps(compact, ensure_ascii=False, indent=2, sort_keys=True)


def render_vision(record: Dict[str, Any]) -> str:
    judgment = record.get("judgment", {})
    lines = [
        f"Vision genesis: {record.get('vision_genesis_id', '?')}",
        f"  decision: {judgment.get('decision', record.get('status', '?'))}",
    ]
    selected_id = judgment.get("selected_vision_id", "")
    if selected_id:
        lines.append(f"  selected: {selected_id}")
    brief = str(judgment.get("vision_brief", "")).strip()
    if brief:
        lines.extend(["", brief])
    lines.extend(
        [
            "",
            "This is an originated vision, not an implementation instruction.",
            "Use it as context for /cycle; mission approval remains separate.",
        ]
    )
    return "\n".join(lines)


def render_invention(record: Dict[str, Any]) -> str:
    scale = record.get("observation", {}).get("scale", "?")
    if isinstance(scale, dict):
        scale = " / ".join(str(value).strip() for value in scale.values() if str(value).strip())
    lines = [
        f"Product invention: {record.get('product_invention_id', '?')}",
        f"  discovery: {record.get('status', '?')}",
        f"  input mode: {record.get('observation', {}).get('input_mode', '?')}",
        f"  scale: {scale}",
        f"  candidates: {len(record.get('candidates', []))}",
        f"  new observation requirements: {len(record.get('observation_requirements', []))}",
    ]
    synthesis_value = record.get("curator", {}).get("synthesis", "")
    if isinstance(synthesis_value, dict):
        synthesis_lines = [
            f"{str(key).replace('_', ' ')}: {value}"
            for key, value in synthesis_value.items()
            if str(value).strip()
        ]
        if synthesis_lines:
            lines.extend([""] + synthesis_lines)
    else:
        synthesis = str(synthesis_value).strip()
        if synthesis:
            lines.extend(["", synthesis])
    for row in record.get("frontier", []):
        lines.append(
            f"  - {row.get('candidate_id', '?')}: {row.get('disposition', '?')} — "
            f"{row.get('reason', '')}"
        )
    lines.extend([
        "",
        "This is an exploration frontier, not a selected plan or implementation instruction.",
        "Human commitment, design, mission approval, and delivery authority remain separate.",
    ])
    return "\n".join(lines)


def render_opportunity_scout(record: Dict[str, Any]) -> str:
    critic = record.get("critic", {})
    assessments = {
        row.get("opportunity_id"): row
        for row in critic.get("assessments", [])
        if isinstance(row, dict)
    }
    lines = [
        f"Opportunity scout: {record.get('opportunity_scout_id', '?')}",
        f"  status: {record.get('status', '?')}",
        f"  perspectives inspected: {len(record.get('perspective_findings', []))}",
        f"  senior lenses inspected: {len(record.get('deep_reframes', []))}",
        f"  prior outcomes available: {record.get('experience_coverage', {}).get('experience_count', 0)}",
        f"  opportunities: {len(record.get('opportunities', []))}",
    ]
    if record.get("experience_coverage", {}).get("archive_truncated"):
        lines.append("  experience archive: truncated to the 12 newest bounded outcomes")
    summary = str(critic.get("portfolio_summary", "")).strip()
    if summary:
        lines.extend(["", summary])
    top_ids = set(critic.get("top_opportunity_ids", []))
    for row in record.get("opportunities", []):
        opportunity_id = row.get("opportunity_id", "?")
        assessment = assessments.get(opportunity_id, {})
        marker = "*" if opportunity_id in top_ids else "-"
        insight = row.get("insight_chain", {})
        reality = row.get("delivery_reality", {})
        failure_basis = row.get("failure_basis", {})
        consequence_graph = row.get("consequence_graph", {})
        probe = row.get("validation_probe", {})
        lines.extend([
            "",
            f"  {marker} {opportunity_id}: {row.get('title', '')}",
            f"    type: {row.get('opportunity_type', '?')} / {assessment.get('disposition', '?')}",
            f"    why: {row.get('observation', '')} → {row.get('current_gap', '')}",
            f"    reframe: {insight.get('hidden_assumption', '')} → {insight.get('reframe', '')}",
            f"    mechanism: {row.get('mechanism', '')}",
            f"    business effect: {row.get('business_effect', '')}",
            f"    second-order: {insight.get('second_order_effect', '')}",
            f"    feedback / externality: {insight.get('feedback_or_externality', '')}",
            f"    consequence depth: {consequence_graph.get('computed_max_depth', '?')}",
            f"    design invariant: {insight.get('design_invariant', '')}",
            f"    operating burden: {reality.get('ongoing_operating_burden', '')}",
            f"    migration / rollback: {reality.get('migration_path', '')} / {reality.get('rollback_boundary', '')}",
            f"    failure basis: {failure_basis.get('basis_type', '?')} — {failure_basis.get('lesson', '')}",
            f"    failure sources: {', '.join(failure_basis.get('source_experience_ids', [])) or '-'}",
            f"    guardrail / transfer limit: {failure_basis.get('guardrail', '')} / {failure_basis.get('transfer_limit', '')}",
            f"    fastest test: {row.get('fastest_test', '')}",
            f"    action probe: {probe.get('intervention', '')}",
            f"    response / counterfactual: {probe.get('metric', '')} / {probe.get('baseline_or_counterfactual', '')}",
            f"    rollback / stop: {probe.get('rollback', '')} / {probe.get('stop_condition', '')}",
            f"    failure: {row.get('failure_condition', '')}",
            f"    critic gap: {assessment.get('senior_judgment_gap', '')}",
        ])
    lines.extend([
        "",
        "These are product opportunities and testable business hypotheses, not implementation instructions.",
        "Planning and delivery authority remain ungranted.",
    ])
    return "\n".join(lines)


def render_pursuit(record: Dict[str, Any]) -> str:
    routing = record.get("epistemic_routing", {})
    governor = record.get("governor", {})
    return "\n".join([
        f"Pursuit: {record.get('pursuit_id', '?')}",
        f"  disposition: {record.get('status', '?')}",
        f"  epistemic work: {', '.join(routing.get('task_types', []))}",
        f"  first nodes: {', '.join(governor.get('first_executable_nodes', [])) or '-'}",
        "",
        str(governor.get("expected_deliverable", "")),
        "",
        "This is an execution-ready knowledge-work graph, not evidence that execution occurred.",
        "External action, publication, and financial action remain ungranted.",
    ])


def render_vision_scout(record: Dict[str, Any]) -> str:
    lines = [
        f"Vision scout: {record.get('vision_scout_id', '?')}",
        f"  decision: {record.get('governor', {}).get('decision', record.get('status', '?'))}",
    ]
    founder_prompt = str(record.get("selected_founder_prompt", "")).strip()
    if founder_prompt:
        lines.extend(["", founder_prompt])
    lines.extend(
        [
            "",
            "This is a low-cost upstream hypothesis, not a completed vision.",
            "It grants neither full Vision Genesis nor delivery authority.",
        ]
    )
    if record.get("reused_existing_context"):
        lines.append("Identical context reused the prior Scout without provider calls.")
    return "\n".join(lines)


def run_automatic_meta_learning(
    *, provider: ChatProvider, mission_store: MissionStore, snapshot: Dict[str, Any]
) -> Dict[str, Any]:
    """Wake bounded meta-learning only after a meaningful outcome history exists."""
    from palamedes_prompt import (
        PromptAgendaStore,
        run_outcome_backfill,
        run_prompt_architecture,
    )
    from palamedes_reference_intelligence import (
        ReferenceIntelligenceStore,
        run_reference_intelligence,
    )

    outcomes = mission_store.outcomes()
    result: Dict[str, Any] = {
        "status": "not_needed",
        "outcome_count": len(outcomes),
        "backfill": {"status": "not_needed"},
        "reference_intelligence": {"status": "not_needed"},
    }
    if len(outcomes) < 5:
        return result
    prompt_store = PromptAgendaStore(mission_store.root / "prompt-intelligence")
    interpreted_ids = {
        item["outcome_id"] for item in mission_store.outcome_interpretations()
    } | prompt_store.backfilled_outcome_ids()
    pending_count = sum(
        1 for item in outcomes if item.get("outcome_id") not in interpreted_ids
    )
    if pending_count:
        backfill = run_outcome_backfill(
            provider=provider,
            store=prompt_store,
            outcomes=outcomes,
            already_interpreted_outcome_ids=interpreted_ids,
            limit=min(12, pending_count),
        )
        result["backfill"] = backfill
        zoom = backfill.get("zoom_pattern", {})
        if zoom.get("status") == "required":
            result["zoom_prompt_architecture"] = run_prompt_architecture(
                provider=provider,
                store=prompt_store,
                cluster=zoom["cluster"],
            )
    reference_store = ReferenceIntelligenceStore(
        mission_store.root / "reference-intelligence"
    )
    if not reference_store.has_runs():
        intelligence = run_reference_intelligence(
            provider=provider,
            store=reference_store,
            snapshot=snapshot,
        )
        result["reference_intelligence"] = {
            "status": "completed",
            "reference_intelligence_id": intelligence[
                "reference_intelligence_id"
            ],
            "reference_mode": intelligence["reference_mode"],
        }
    result["status"] = "completed"
    return result


def run_chat(
    *,
    palamedes_module: Any,
    provider: ChatProvider,
    session_id: str,
    history_limit: int = 24,
    input_stream: TextIO = sys.stdin,
    output: TextIO = sys.stdout,
    team_store: Any = None,
    agent_id: str = "",
    agent_role: str = "strategist",
) -> int:
    store = ChatSessionStore(palamedes_module.STATE_DIR / "chat")
    mission_store = MissionStore(palamedes_module.STATE_DIR / "missions")
    cognition_store = CognitionCycleStore(
        palamedes_module.STATE_DIR / "missions" / "cognition"
    )
    latest_observation: Optional[Dict[str, Any]] = None
    active_session = session_id
    workspace = Path(palamedes_module.ROOT)
    if team_store is not None and not agent_id:
        raise ValueError("team-enabled chat requires agent_id")

    def current_team_context() -> Optional[Dict[str, Any]]:
        if team_store is None:
            return None
        return {
            "active_agent": {"agent_id": agent_id, "agent_role": agent_role},
            "shared_state": team_store.context_snapshot(),
        }

    output.write("Palamedes Research Beta\n")
    output.write(
        f"workspace: {workspace}\nprovider: {provider.provider_name}\n"
        f"model: {provider.model}\nsession: {active_session}\n"
    )
    output.write("Type /help for commands. Palamedes proposes; it does not execute delivery work.\n\n")

    while True:
        output.write("palamedes> ")
        output.flush()
        line = input_stream.readline()
        if line == "":
            output.write("\n")
            return 0
        text = line.strip()
        if not text:
            continue
        if text in {"/quit", "/exit"}:
            return 0
        if text == "/help":
            _print_help(output)
            continue
        if text == "/status":
            output.write(
                f"provider={provider.provider_name} model={provider.model} "
                f"workspace={workspace} session={active_session} "
                f"team_agent={agent_id or 'disabled'}\n"
            )
            continue
        if text == "/sessions":
            sessions = store.list_sessions()
            output.write("\n".join(sessions) + ("\n" if sessions else "No sessions.\n"))
            continue
        if text == "/new":
            active_session = uuid.uuid4().hex[:12]
            output.write(f"New session: {active_session}\n")
            continue
        if text == "/history":
            records = store.load(active_session)
            turns = [
                f"{record.get('role', '?')}: {record.get('content', '')}"
                for record in records
                if record.get("role") in {"user", "assistant"}
            ]
            output.write("\n".join(turns) + ("\n" if turns else "No turns.\n"))
            continue
        if text.startswith("/wait-external "):
            parts = text.split(maxsplit=2)
            if len(parts) != 3 or not re.fullmatch(r"mission-[a-f0-9]{12}", parts[1]):
                output.write("/wait-external requires: mission-id <evidence needed>\n")
                continue
            try:
                contract = mission_store.load_contract(parts[1])
            except ValueError as exc:
                output.write(f"{exc}\n")
                continue
            if contract.get("status") not in {"approved", "outcome_recorded"}:
                output.write("External evidence waits require an approved mission.\n")
                continue
            gate = {
                "gate_version": "palamedes-external-evidence-gate/1",
                "gate_id": f"gate-{uuid.uuid4().hex[:12]}",
                "gate_kind": "external_evidence",
                "mission_contract_id": parts[1],
                "required_response": parts[2],
                "authorized_local_actions": [],
                "status": "open",
                "opened_at": utc_now(),
            }
            mission_store.append_outcome_gate(gate)
            output.write(
                f"Waiting for external evidence: {gate['gate_id']}\n"
                "Further /cycle calls will use zero provider calls until this gate is resolved.\n"
            )
            continue
        if text.startswith("/external-evidence "):
            parts = text.split(maxsplit=2)
            if len(parts) != 3 or not re.fullmatch(r"gate-[a-f0-9]{12}", parts[1]):
                output.write("/external-evidence requires: gate-id <observation>\n")
                continue
            gate = next(
                (row for row in mission_store.open_outcome_gates() if row.get("gate_id") == parts[1]),
                None,
            )
            if gate is None or gate.get("gate_kind") != "external_evidence":
                output.write(f"Open external evidence gate not found: {parts[1]}\n")
                continue
            resolved = dict(gate)
            resolved.update(
                {
                    "status": "resolved",
                    "resolved_at": utc_now(),
                    "external_observation": parts[2],
                    "evidence_custody": "user_attested_external",
                }
            )
            mission_store.append_outcome_gate(resolved)
            output.write(f"External evidence gate resolved: {parts[1]}\n")
            continue
        if text.startswith("/vision-holdout-import "):
            from palamedes_vision_benchmark import VisionBenchmarkStore

            source_path = Path(
                text[len("/vision-holdout-import ") :].strip()
            ).expanduser()
            try:
                payload = json.loads(source_path.read_text(encoding="utf-8"))
                imported = VisionBenchmarkStore(
                    mission_store.root.parent / "vision-benchmarks"
                ).import_holdout_case(payload)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                output.write(f"[vision holdout import error] {exc}\n")
                continue
            output.write(
                f"Vision holdout imported: {imported['case_id']} "
                f"({imported['case_fingerprint']}).\n"
            )
            continue
        if text == "/vision-scout-benchmark" or text.startswith(
            "/vision-scout-benchmark "
        ):
            from palamedes_vision_benchmark import (
                BUILTIN_CASES,
                VisionBenchmarkStore,
                run_blind_scout_case,
            )
            from palamedes_vision_scout import VisionScoutStore

            requested = text[len("/vision-scout-benchmark") :].strip()
            case_index = {"": 0, "collection": 0, "fusion": 1, "social": 2}.get(
                requested
            )
            if case_index is None:
                output.write(
                    "/vision-scout-benchmark accepts collection, fusion, or social.\n"
                )
                continue
            benchmark_case = BUILTIN_CASES[case_index]
            generator_usage: List[Dict[str, Any]] = []
            judge_usage: List[Dict[str, Any]] = []

            def scout_ask(role: str, prompt: str) -> Dict[str, Any]:
                target = (
                    judge_usage
                    if role == "blind_founder_prompt_judge"
                    else generator_usage
                )
                try:
                    return _provider_json(
                        provider,
                        system=(
                            f"ROLE: {role}. Originate without hidden reference access and "
                            "return exactly one JSON object."
                        ),
                        prompt=f"ROLE: {role}\n{prompt}",
                    )
                finally:
                    target.append(_capture_provider_usage(provider, role))

            judge_provider = provider
            judge_provider_name = os.environ.get(
                "PALAMEDES_VISION_JUDGE_PROVIDER", ""
            ).strip()
            if judge_provider_name:
                judge_model = os.environ.get(
                    "PALAMEDES_VISION_JUDGE_MODEL", ""
                ).strip()
                health = provider_health(judge_provider_name)
                if health["status"] != "ok":
                    output.write(
                        f"[vision scout judge unavailable] {judge_provider_name}; "
                        "using correlated primary provider.\n"
                    )
                else:
                    judge_provider = provider_from_config(
                        judge_provider_name, judge_model
                    )

            def scout_judge_ask(role: str, prompt: str) -> Dict[str, Any]:
                try:
                    return _provider_json(
                        judge_provider,
                        system=(
                            f"ROLE: {role}. You receive the hidden reference only after "
                            "scouting. Return exactly one JSON object."
                        ),
                        prompt=f"ROLE: {role}\n{prompt}",
                    )
                finally:
                    judge_usage.append(
                        _capture_provider_usage(judge_provider, role)
                    )

            def scout_usage_report() -> Dict[str, Any]:
                generator_summary = _provider_usage_summary(
                    provider, generator_usage
                )
                judge_summary = _provider_usage_summary(
                    judge_provider, judge_usage
                )
                return {
                    "generator": generator_summary,
                    "judge": judge_summary,
                    "attempted_calls": (
                        generator_summary["attempted_calls"]
                        + judge_summary["attempted_calls"]
                    ),
                    "metered_calls": (
                        generator_summary["metered_calls"]
                        + judge_summary["metered_calls"]
                    ),
                    "unmetered_calls": (
                        generator_summary["unmetered_calls"]
                        + judge_summary["unmetered_calls"]
                    ),
                }

            output.write(
                f"Running low-cost blind vision scout: {benchmark_case.case_id}\n"
            )
            try:
                benchmark = run_blind_scout_case(
                    case=benchmark_case,
                    ask=scout_ask,
                    scout_store=VisionScoutStore(
                        mission_store.root.parent / "vision-scouts"
                    ),
                    benchmark_store=VisionBenchmarkStore(
                        mission_store.root.parent / "vision-benchmarks"
                    ),
                    judge_ask=(
                        scout_judge_ask if judge_provider is not provider else None
                    ),
                    generator_identity=f"{provider.provider_name}:{provider.model}",
                    judge_identity=(
                        f"{judge_provider.provider_name}:{judge_provider.model}"
                    ),
                    usage_report=scout_usage_report,
                )
            except (OSError, RuntimeError, ValueError) as exc:
                output.write(f"[vision scout benchmark error] {exc}\n")
                continue
            independent_judge = bool(
                benchmark["evaluation_custody"]["independent_provider_claimed"]
            )
            verdict = "FAIL"
            if benchmark["passed"]:
                verdict = (
                    "MACHINE PASS (independent provider judge)"
                    if independent_judge
                    else "MACHINE PASS (correlated same-provider judge)"
                )
            output.write(
                f"Vision scout benchmark {benchmark['vision_scout_benchmark_id']}: "
                f"{verdict}\n"
            )
            output.write(
                "  authority: " + benchmark["next_authorized_step"] + " only\n"
            )
            if benchmark["failure_reasons"]:
                output.write(
                    "  reasons: " + ", ".join(benchmark["failure_reasons"]) + "\n"
                )
            continue

        if text == "/vision-benchmark" or text.startswith("/vision-benchmark "):
            from palamedes_vision import VisionStore
            from palamedes_vision_benchmark import (
                BUILTIN_CASES,
                VisionBenchmarkStore,
                run_blind_case,
            )

            requested = text[len("/vision-benchmark") :].strip()
            case_index = {
                "": 0,
                "collection": 0,
                "fusion": 1,
                "social": 2,
            }.get(requested)
            benchmark_store = VisionBenchmarkStore(
                mission_store.root.parent / "vision-benchmarks"
            )
            if requested.startswith("holdout:"):
                try:
                    benchmark_case = benchmark_store.load_holdout_case(
                        requested[len("holdout:") :]
                    )
                except ValueError as exc:
                    output.write(f"[vision benchmark holdout error] {exc}\n")
                    continue
            elif case_index is None:
                output.write(
                    "/vision-benchmark accepts collection, fusion, social, or "
                    "holdout:<case-id>.\n"
                )
                continue
            else:
                benchmark_case = BUILTIN_CASES[case_index]

            generator_usage: List[Dict[str, Any]] = []
            judge_usage: List[Dict[str, Any]] = []

            def benchmark_ask(role: str, prompt: str) -> Dict[str, Any]:
                target = (
                    judge_usage
                    if role in {"blind_vision_judge", "blind_founder_prompt_judge"}
                    else generator_usage
                )
                try:
                    return _provider_json(
                        provider,
                        system=(
                            f"ROLE: {role}. Preserve benchmark blindness and return "
                            "exactly one JSON object."
                        ),
                        prompt=f"ROLE: {role}\n{prompt}",
                    )
                finally:
                    target.append(_capture_provider_usage(provider, role))

            judge_provider = provider
            judge_provider_name = os.environ.get(
                "PALAMEDES_VISION_JUDGE_PROVIDER", ""
            ).strip()
            if judge_provider_name:
                judge_model = os.environ.get(
                    "PALAMEDES_VISION_JUDGE_MODEL", ""
                ).strip()
                health = provider_health(judge_provider_name)
                if health["status"] != "ok":
                    output.write(
                        f"[vision benchmark judge unavailable] {judge_provider_name}; "
                        "using correlated primary provider.\n"
                    )
                else:
                    judge_provider = provider_from_config(
                        judge_provider_name, judge_model
                    )

            def judge_ask(role: str, prompt: str) -> Dict[str, Any]:
                try:
                    return _provider_json(
                        judge_provider,
                        system=(
                            f"ROLE: {role}. You receive the hidden reference only after "
                            "generation. Return exactly one JSON object."
                        ),
                        prompt=f"ROLE: {role}\n{prompt}",
                    )
                finally:
                    judge_usage.append(_capture_provider_usage(judge_provider, role))

            def benchmark_usage_report() -> Dict[str, Any]:
                generator_summary = _provider_usage_summary(
                    provider, generator_usage
                )
                judge_summary = _provider_usage_summary(
                    judge_provider, judge_usage
                )
                return {
                    "generator": generator_summary,
                    "judge": judge_summary,
                    "attempted_calls": (
                        generator_summary["attempted_calls"]
                        + judge_summary["attempted_calls"]
                    ),
                    "metered_calls": (
                        generator_summary["metered_calls"]
                        + judge_summary["metered_calls"]
                    ),
                    "unmetered_calls": (
                        generator_summary["unmetered_calls"]
                        + judge_summary["unmetered_calls"]
                    ),
                }

            output.write(
                f"Running blind vision benchmark: {benchmark_case.case_id}\n"
            )
            try:
                benchmark = run_blind_case(
                    case=benchmark_case,
                    ask=benchmark_ask,
                    vision_store=VisionStore(
                        mission_store.root.parent / "visions"
                    ),
                    benchmark_store=benchmark_store,
                    judge_ask=(
                        judge_ask if judge_provider is not provider else None
                    ),
                    generator_identity=f"{provider.provider_name}:{provider.model}",
                    judge_identity=(
                        f"{judge_provider.provider_name}:{judge_provider.model}"
                    ),
                    usage_report=benchmark_usage_report,
                )
            except (OSError, RuntimeError, ValueError) as exc:
                output.write(f"[vision benchmark error] {exc}\n")
                continue
            independent_judge = bool(
                benchmark.get("evaluation_custody", {}).get(
                    "independent_provider_claimed"
                )
            )
            verdict = "FAIL"
            if benchmark["passed"]:
                verdict = (
                    "MACHINE PASS (independent provider judge)"
                    if independent_judge
                    else "MACHINE PASS (correlated same-provider judge)"
                )
            output.write(
                f"Vision benchmark {benchmark['vision_benchmark_id']}: {verdict}\n"
            )
            if benchmark.get("failure_reasons"):
                output.write(
                    "  reasons: " + ", ".join(benchmark["failure_reasons"]) + "\n"
                )
            continue
        if text == "/vision-agenda-ablation" or text.startswith(
            "/vision-agenda-ablation "
        ):
            from palamedes_vision_benchmark import (
                BUILTIN_CASES,
                VisionBenchmarkStore,
                run_agenda_ablation,
            )

            parts = text.split()
            requested = parts[1] if len(parts) >= 2 else "collection"
            challenger = parts[2] if len(parts) >= 3 else "adaptive"
            comparator = parts[3] if len(parts) >= 4 else "conventional"
            case_index = {
                "collection": 0,
                "fusion": 1,
                "social": 2,
            }.get(requested)
            supported_agendas = {"adaptive", "frontier", "conventional"}
            if (
                len(parts) > 4
                or case_index is None
                or challenger not in supported_agendas
                or comparator not in supported_agendas
                or challenger == comparator
            ):
                output.write(
                    "/vision-agenda-ablation accepts case "
                    "collection|fusion|social and two distinct agenda conditions "
                    "adaptive|frontier|conventional.\n"
                )
                continue
            benchmark_case = BUILTIN_CASES[case_index]
            ablation_usage: List[Dict[str, Any]] = []

            def agenda_ablation_ask(role: str, prompt: str) -> Dict[str, Any]:
                try:
                    return _provider_json(
                        provider,
                        system=(
                            f"ROLE: {role}. Preserve equal-information ablation custody "
                            "and return exactly one JSON object."
                        ),
                        prompt=f"ROLE: {role}\n{prompt}",
                    )
                finally:
                    ablation_usage.append(_capture_provider_usage(provider, role))

            output.write(
                f"Running equal-call vision agenda ablation: "
                f"{benchmark_case.case_id} ({challenger} vs {comparator})\n"
            )
            try:
                ablation = run_agenda_ablation(
                    case=benchmark_case,
                    ask=agenda_ablation_ask,
                    judge_ask=agenda_ablation_ask,
                    vision_root=(
                        mission_store.root.parent
                        / "vision-benchmarks"
                        / "agenda-ablation-visions"
                    ),
                    benchmark_store=VisionBenchmarkStore(
                        mission_store.root.parent / "vision-benchmarks"
                    ),
                    generator_identity=f"{provider.provider_name}:{provider.model}",
                    judge_identity=f"{provider.provider_name}:{provider.model}",
                    usage_report=lambda: _provider_usage_summary(
                        provider, ablation_usage
                    ),
                    challenger_condition=challenger,
                    comparator_condition=comparator,
                )
            except (OSError, RuntimeError, ValueError) as exc:
                output.write(f"[vision agenda ablation error] {exc}\n")
                continue
            output.write(
                f"Vision agenda ablation "
                f"{ablation['vision_agenda_ablation_id']}: "
                f"{ablation['preferred_condition']}\n"
            )
            continue
        if text == "/vision-benchmark-suite" or text.startswith(
            "/vision-benchmark-suite "
        ):
            from palamedes_vision import VisionStore
            from palamedes_vision_benchmark import (
                BUILTIN_CASES,
                VisionBenchmarkStore,
                run_blind_suite,
            )

            parts = text.split()
            requested = parts[1] if len(parts) >= 2 else "all"
            try:
                runs_per_case = int(parts[2]) if len(parts) >= 3 else 1
            except ValueError:
                output.write("vision benchmark suite runs must be an integer 1-5.\n")
                continue
            if len(parts) > 3 or requested not in {
                "all", "collection", "fusion", "social"
            }:
                output.write(
                    "/vision-benchmark-suite accepts all|collection|fusion|social "
                    "and runs 1-5.\n"
                )
                continue
            selected_cases = (
                list(BUILTIN_CASES)
                if requested == "all"
                else [
                    BUILTIN_CASES[
                        {"collection": 0, "fusion": 1, "social": 2}[requested]
                    ]
                ]
            )

            def suite_ask(role: str, prompt: str) -> Dict[str, Any]:
                return _provider_json(
                    provider,
                    system=(
                        f"ROLE: {role}. Preserve benchmark blindness and return "
                        "exactly one JSON object."
                    ),
                    prompt=f"ROLE: {role}\n{prompt}",
                )

            judge_provider = provider
            judge_provider_name = os.environ.get(
                "PALAMEDES_VISION_JUDGE_PROVIDER", ""
            ).strip()
            if judge_provider_name:
                judge_model = os.environ.get(
                    "PALAMEDES_VISION_JUDGE_MODEL", ""
                ).strip()
                health = provider_health(judge_provider_name)
                if health["status"] != "ok":
                    output.write(
                        f"[vision benchmark judge unavailable] {judge_provider_name}; "
                        "using correlated primary provider.\n"
                    )
                else:
                    judge_provider = provider_from_config(
                        judge_provider_name, judge_model
                    )

            def suite_judge_ask(role: str, prompt: str) -> Dict[str, Any]:
                return _provider_json(
                    judge_provider,
                    system=(
                        f"ROLE: {role}. You receive the hidden reference only after "
                        "generation. Return exactly one JSON object."
                    ),
                    prompt=f"ROLE: {role}\n{prompt}",
                )

            benchmark_store = VisionBenchmarkStore(
                mission_store.root.parent / "vision-benchmarks"
            )
            output.write(
                f"Running {len(selected_cases) * runs_per_case} blinded vision trials.\n"
            )
            try:
                suite = run_blind_suite(
                    cases=selected_cases,
                    runs_per_case=runs_per_case,
                    ask=suite_ask,
                    vision_store=VisionStore(mission_store.root.parent / "visions"),
                    benchmark_store=benchmark_store,
                    judge_ask=(
                        suite_judge_ask if judge_provider is not provider else None
                    ),
                    generator_identity=f"{provider.provider_name}:{provider.model}",
                    judge_identity=(
                        f"{judge_provider.provider_name}:{judge_provider.model}"
                    ),
                )
            except (OSError, RuntimeError, ValueError) as exc:
                output.write(f"[vision benchmark suite error] {exc}\n")
                continue
            output.write(
                f"Vision benchmark suite {suite['suite_id']}: "
                f"{suite['pass_count']}/{suite['run_count']} passed.\n"
            )
            continue
        if text == "/vision-benchmark-summary":
            from palamedes_vision_benchmark import VisionBenchmarkStore

            summary = VisionBenchmarkStore(
                mission_store.root.parent / "vision-benchmarks"
            ).machine_benchmark_summary()
            output.write(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
            continue
        if text.startswith("/vision-review-submit "):
            from palamedes_vision_benchmark import VisionBenchmarkStore

            parts = text.split(maxsplit=2)
            if len(parts) != 3:
                output.write(
                    "/vision-review-submit requires packet-id and one JSON object.\n"
                )
                continue
            try:
                response = json.loads(parts[2])
                if not isinstance(response, dict):
                    raise ValueError("response must be an object")
                resolved = VisionBenchmarkStore(
                    mission_store.root.parent / "vision-benchmarks"
                ).submit_human_review(parts[1], response)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                output.write(f"[vision human review error] {exc}\n")
                continue
            output.write(
                f"Human vision review resolved: {resolved['resolution']} "
                f"({resolved['vision_human_response_id']}).\n"
            )
            continue
        if text == "/vision-review-next":
            from palamedes_vision_benchmark import VisionBenchmarkStore

            packet = VisionBenchmarkStore(
                mission_store.root.parent / "vision-benchmarks"
            ).next_human_review_packet()
            output.write(
                json.dumps(packet, ensure_ascii=False, indent=2) + "\n"
                if packet
                else "No blinded human-review packets are available.\n"
            )
            continue
        if text == "/vision-review-bundle":
            from palamedes_vision_benchmark import VisionBenchmarkStore

            try:
                path = VisionBenchmarkStore(
                    mission_store.root.parent / "vision-benchmarks"
                ).build_human_review_bundle()
            except (OSError, ValueError) as exc:
                output.write(f"[vision human review bundle error] {exc}\n")
                continue
            output.write(f"Blind human-review bundle: {path}\n")
            continue
        if text.startswith("/vision-review-import "):
            from palamedes_vision_benchmark import VisionBenchmarkStore

            response_path = Path(
                text[len("/vision-review-import ") :].strip()
            ).expanduser()
            try:
                response = json.loads(response_path.read_text(encoding="utf-8"))
                if not isinstance(response, dict):
                    raise ValueError("response must be an object")
                packet_id = str(response.get("vision_review_packet_id", "")).strip()
                if not packet_id:
                    raise ValueError("response requires vision_review_packet_id")
                resolved = VisionBenchmarkStore(
                    mission_store.root.parent / "vision-benchmarks"
                ).submit_human_review(packet_id, response)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                output.write(f"[vision human review import error] {exc}\n")
                continue
            output.write(
                f"Human vision review imported: {resolved['resolution']} "
                f"({resolved['vision_human_response_id']}).\n"
            )
            continue
        if text == "/vision-review-summary":
            from palamedes_vision_benchmark import VisionBenchmarkStore

            summary = VisionBenchmarkStore(
                mission_store.root.parent / "vision-benchmarks"
            ).human_review_summary()
            output.write(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
            continue
        if text == "/vision-review-gate":
            from palamedes_vision_benchmark import VisionBenchmarkStore

            gate = VisionBenchmarkStore(
                mission_store.root.parent / "vision-benchmarks"
            ).human_evidence_gate()
            output.write(json.dumps(gate, ensure_ascii=False, indent=2) + "\n")
            continue
        if text == "/vision-scout-review-next":
            from palamedes_vision import fingerprint
            from palamedes_vision_scout import VisionScoutStore

            packet = VisionScoutStore(
                mission_store.root.parent / "vision-scouts"
            ).next_project_review_packet()
            if packet is None:
                output.write("No project Scout review packets are available.\n")
            else:
                rendered = dict(packet)
                rendered["packet_fingerprint"] = fingerprint(packet)
                output.write(json.dumps(rendered, ensure_ascii=False, indent=2) + "\n")
            continue
        if text.startswith("/vision-scout-review-submit "):
            from palamedes_vision_scout import VisionScoutStore

            parts = text.split(maxsplit=2)
            if len(parts) != 3:
                output.write(
                    "/vision-scout-review-submit requires packet-id and one JSON object.\n"
                )
                continue
            try:
                response = json.loads(parts[2])
                if not isinstance(response, dict):
                    raise ValueError("response must be an object")
                resolved = VisionScoutStore(
                    mission_store.root.parent / "vision-scouts"
                ).submit_project_review(parts[1], response)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                output.write(f"[project Scout review error] {exc}\n")
                continue
            output.write(
                "Project Scout review recorded: "
                f"{resolved['recommendation']} "
                f"({resolved['vision_scout_project_review_response_id']}).\n"
            )
            continue
        if text.startswith("/vision-scout-probe-outcome "):
            from palamedes_vision_scout import VisionScoutStore

            remainder = text[len("/vision-scout-probe-outcome ") :].strip()
            try:
                scout_id, raw_outcome = remainder.split(maxsplit=1)
                outcome_payload = json.loads(raw_outcome)
                if not isinstance(outcome_payload, dict):
                    raise ValueError("probe outcome must be a JSON object")
                probe_outcome = VisionScoutStore(
                    mission_store.root.parent / "vision-scouts"
                ).record_probe_outcome(scout_id, outcome_payload)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                output.write(f"[vision scout probe outcome error] {exc}\n")
                continue
            output.write(
                "Vision scout probe outcome: "
                f"{probe_outcome['probe_outcome_id']} "
                f"supports_renewal={probe_outcome['supports_full_genesis_renewal']}\n"
            )
            continue
        if text.startswith("/vision-scout-probe "):
            from palamedes_vision_scout import VisionScoutStore

            remainder = text[len("/vision-scout-probe ") :].strip()
            try:
                scout_id, raw_probe = remainder.split(maxsplit=1)
                probe_payload = json.loads(raw_probe)
                if not isinstance(probe_payload, dict):
                    raise ValueError("probe must be a JSON object")
                probe = VisionScoutStore(
                    mission_store.root.parent / "vision-scouts"
                ).register_probe(scout_id, probe_payload)
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                output.write(f"[vision scout probe error] {exc}\n")
                continue
            output.write(f"Vision scout probe preregistered: {probe['probe_id']}\n")
            continue
        if text.startswith("/vision-scout-promote "):
            from palamedes_vision import fingerprint
            from palamedes_vision_benchmark import VisionBenchmarkStore
            from palamedes_vision_scout import VisionScoutStore

            scout_id = text[len("/vision-scout-promote ") :].strip()
            benchmark_store = VisionBenchmarkStore(
                mission_store.root.parent / "vision-benchmarks"
            )
            scout_store = VisionScoutStore(
                mission_store.root.parent / "vision-scouts"
            )
            try:
                prior_promotion = benchmark_store.scout_promotion(scout_id)
                if prior_promotion is not None:
                    output.write(
                        "Vision scout already promoted: "
                        f"{prior_promotion['vision_genesis_id']}\n"
                    )
                    continue
                scout = scout_store.load(scout_id)
                gate = benchmark_store.scout_promotion_gate(
                    scout_id,
                    probe_outcome=scout_store.probe_outcome(scout_id),
                )
                if not gate["passed"]:
                    output.write(
                        "Vision scout promotion blocked:\n"
                        + json.dumps(gate, ensure_ascii=False, indent=2)
                        + "\n"
                    )
                    continue
                scout_context = scout_store.load_context(scout_id)
                vision_record = run_autonomous_vision(
                    provider=provider,
                    mission_store=mission_store,
                    context=(
                        scout_context
                        + "\n\nHUMAN-RENEWED SCOUT FOUNDER PROMPT:\n"
                        + str(scout.get("selected_founder_prompt", ""))
                    ),
                )
                identity = {
                    "vision_scout_id": scout_id,
                    "vision_genesis_id": vision_record["vision_genesis_id"],
                    "gate": gate,
                }
                promotion = {
                    "vision_scout_promotion_version": (
                        "palamedes-vision-scout-promotion/1"
                    ),
                    "vision_scout_promotion_id": (
                        f"vision-scout-promotion-{fingerprint(identity)[:12]}"
                    ),
                    "vision_scout_id": scout_id,
                    "vision_genesis_id": vision_record["vision_genesis_id"],
                    "promotion_gate": gate,
                    "full_genesis_authorized": True,
                    "delivery_authority_granted": False,
                    "promoted_at": utc_now(),
                }
                benchmark_store.save_scout_promotion(promotion)
            except (OSError, RuntimeError, ValueError) as exc:
                output.write(f"[vision scout promotion error] {exc}\n")
                continue
            output.write(render_vision(vision_record) + "\n")
            continue
        if text == "/vision-scout-promote":
            output.write("/vision-scout-promote requires a vision scout ID.\n")
            continue
        if text in {"/vision-scout-probe", "/vision-scout-probe-outcome"}:
            output.write(f"{text} requires a vision scout ID and JSON object.\n")
            continue
        if text.startswith("/vision-scout "):
            scout_context = text[len("/vision-scout ") :].strip()
            if not scout_context:
                output.write("/vision-scout requires product context.\n")
                continue
            output.write(
                "Running vision scout: three causal candidates → critique → cost gate\n"
            )
            try:
                from palamedes_observe import collect_observation, observation_context

                ref_value = os.environ.get("PALAMEDES_REF_ROOT", "").strip()
                scout_observation = collect_observation(
                    workspace,
                    ref_root=Path(ref_value).expanduser() if ref_value else None,
                )
                scout_record = run_autonomous_vision_scout(
                    provider=provider,
                    mission_store=mission_store,
                    context=compact_vision_scout_context(
                        build_autonomous_vision_context(
                            mission_store=mission_store,
                            user_context=scout_context,
                            workspace_context=observation_context(
                                scout_observation
                            ),
                        )
                    ),
                    request_context=scout_context,
                )
            except (OSError, RuntimeError, ValueError) as exc:
                output.write(f"[vision scout error] {exc}\n")
                continue
            output.write(render_vision_scout(scout_record) + "\n")
            continue
        if text == "/vision-scout":
            output.write("/vision-scout requires product context.\n")
            continue
        if text == "/visions":
            from palamedes_vision import VisionStore

            latest_vision = VisionStore(
                mission_store.root.parent / "visions"
            ).latest()
            output.write(
                render_vision(latest_vision) + "\n"
                if latest_vision is not None
                else "No autonomous product vision has been generated.\n"
            )
            continue
        if text == "/inventions":
            from palamedes_invention import ProductInventionStore

            latest_invention = ProductInventionStore(
                mission_store.root.parent / "inventions"
            ).latest()
            output.write(
                render_invention(latest_invention) + "\n"
                if latest_invention is not None
                else "No product invention has been generated.\n"
            )
            continue
        if text == "/opportunities":
            from palamedes_opportunity import OpportunityStore

            latest_opportunity = OpportunityStore(
                mission_store.root.parent / "opportunities"
            ).latest()
            output.write(
                render_opportunity_scout(latest_opportunity) + "\n"
                if latest_opportunity is not None
                else "No opportunity scan has been generated.\n"
            )
            continue
        if text.startswith("/opportunity "):
            opportunity_context = text[len("/opportunity ") :].strip()
            if not opportunity_context:
                output.write("/opportunity requires product context.\n")
                continue
            output.write(
                "Running opportunity scout: product structure → nine perspectives → "
                "failure-aware senior reframing → second-order synthesis → reality critique\n"
            )
            try:
                from palamedes_observe import collect_observation, observation_context

                ref_value = os.environ.get("PALAMEDES_REF_ROOT", "").strip()
                opportunity_observation = collect_observation(
                    workspace,
                    ref_root=Path(ref_value).expanduser() if ref_value else None,
                )
                grounded_context = json.dumps({
                    "user_context": opportunity_context,
                    "bounded_workspace_context": observation_context(opportunity_observation),
                }, ensure_ascii=False, sort_keys=True)
                opportunity_record = run_autonomous_opportunity_scout(
                    provider=provider,
                    mission_store=mission_store,
                    context=grounded_context,
                )
            except (OSError, RuntimeError, ValueError) as exc:
                output.write(f"[opportunity scout error] {exc}\n")
                continue
            output.write(render_opportunity_scout(opportunity_record) + "\n")
            continue
        if text == "/opportunity":
            output.write("/opportunity requires product context.\n")
            continue
        if text == "/invent-observations":
            from palamedes_invention import ProductInventionStore

            requirements = ProductInventionStore(
                mission_store.root.parent / "inventions"
            ).open_observation_requirements()
            if not requirements:
                output.write("No open invention observation requirements.\n")
                continue
            output.write(f"Open invention observation requirements: {len(requirements)}\n")
            for row in requirements:
                output.write(
                    f"  {row.get('observation_requirement_id')}: "
                    f"{row.get('observation_needed')}\n"
                    f"    reason: {row.get('reason')}\n"
                )
            continue
        if text.startswith("/invent-observe "):
            parts = text[len("/invent-observe ") :].strip().split(maxsplit=1)
            if len(parts) != 2:
                output.write("/invent-observe requires an observation id and evidence.\n")
                continue
            from palamedes_invention import ProductInventionStore

            try:
                resolved = ProductInventionStore(
                    mission_store.root.parent / "inventions"
                ).resolve_observation_requirement(parts[0], parts[1])
            except (OSError, ValueError) as exc:
                output.write(f"[invention observation error] {exc}\n")
                continue
            output.write(
                f"Observation resolved: {resolved['observation_requirement_id']}\n"
                "The evidence will remain in the append-only history; unresolved "
                "requirements continue into later invention context.\n"
            )
            continue
        if text == "/invent-observe":
            output.write("/invent-observe requires an observation id and evidence.\n")
            continue
        if text == "/pursuits":
            from palamedes_pursuit import PursuitStore

            latest_pursuit = PursuitStore(mission_store.root.parent / "pursuits").latest()
            output.write(
                render_pursuit(latest_pursuit) + "\n"
                if latest_pursuit is not None
                else "No pursuit has been composed.\n"
            )
            continue
        if text.startswith("/pursue "):
            objective = text[len("/pursue ") :].strip()
            if not objective:
                output.write("/pursue requires a high-level objective.\n")
                continue
            output.write(
                "Composing pursuit: intent → epistemic routing → unknown map → "
                "capabilities → adversary → governor\n"
            )
            try:
                pursuit_record = run_autonomous_pursuit(
                    provider=provider, mission_store=mission_store, objective=objective
                )
            except (OSError, RuntimeError, ValueError) as exc:
                output.write(f"[pursuit error] {exc}\n")
                continue
            output.write(render_pursuit(pursuit_record) + "\n")
            continue
        if text == "/pursue":
            output.write("/pursue requires a high-level objective.\n")
            continue
        if text.startswith("/invent "):
            invention_context = text[len("/invent ") :].strip()
            if not invention_context:
                output.write("/invent requires product context.\n")
                continue
            output.write(
                "Running product invention: workspace observation → conventional baseline → "
                "latent value map → counterweighted exploration → structural novelty attack → frontier\n"
            )
            try:
                from palamedes_observe import collect_observation, observation_context

                ref_value = os.environ.get("PALAMEDES_REF_ROOT", "").strip()
                invention_observation = collect_observation(
                    workspace,
                    ref_root=Path(ref_value).expanduser() if ref_value else None,
                )
                invention_record = run_autonomous_invention(
                    provider=provider,
                    mission_store=mission_store,
                    context=build_autonomous_invention_context(
                        user_context=invention_context,
                        workspace_context=observation_context(invention_observation),
                    ),
                )
            except (OSError, RuntimeError, ValueError) as exc:
                output.write(f"[product invention error] {exc}\n")
                continue
            output.write(render_invention(invention_record) + "\n")
            continue
        if text.startswith("/invent-commit "):
            parts = text[len("/invent-commit ") :].strip().split(maxsplit=1)
            if len(parts) != 2:
                output.write("/invent-commit requires a candidate id and human rationale.\n")
                continue
            from palamedes_invention import ProductInventionStore

            try:
                commitment = ProductInventionStore(
                    mission_store.root.parent / "inventions"
                ).commit(parts[0], parts[1])
            except (OSError, ValueError) as exc:
                output.write(f"[invention commitment error] {exc}\n")
                continue
            output.write(
                f"Invention commitment: {commitment['invention_commitment_id']}\n"
                f"  invention: {commitment['product_invention_id']}\n"
                f"  candidate: {commitment['candidate_id']}\n\n"
                "Human direction is recorded. Design, mission approval, and delivery "
                "authority remain ungranted.\n"
            )
            continue
        if text == "/invent-commit":
            output.write("/invent-commit requires a candidate id and human rationale.\n")
            continue
        if text == "/invent":
            output.write("/invent requires product context.\n")
            continue
        if text.startswith("/vision"):
            vision_context = text[len("/vision") :].strip()
            if not vision_context:
                output.write("/vision requires product context.\n")
                continue
            output.write(
                "Running vision genesis: desire → distant analogy → mechanism "
                "fusion → product worlds → maniac critique\n"
            )
            try:
                from palamedes_observe import collect_observation, observation_context

                ref_value = os.environ.get("PALAMEDES_REF_ROOT", "").strip()
                vision_observation = collect_observation(
                    workspace,
                    ref_root=Path(ref_value).expanduser() if ref_value else None,
                )
                vision_record = run_autonomous_vision(
                    provider=provider,
                    mission_store=mission_store,
                    context=build_autonomous_vision_context(
                        mission_store=mission_store,
                        user_context=vision_context,
                        workspace_context=observation_context(vision_observation),
                    ),
                )
            except (OSError, RuntimeError, ValueError) as exc:
                output.write(f"[vision genesis error] {exc}\n")
                continue
            output.write(render_vision(vision_record) + "\n")
            continue
        if text == "/observe":
            from palamedes_observe import collect_observation, render_observation

            ref_value = os.environ.get("PALAMEDES_REF_ROOT", "").strip()
            latest_observation = collect_observation(
                workspace,
                ref_root=Path(ref_value).expanduser() if ref_value else None,
            )
            store.append(
                active_session,
                {
                    "ts": utc_now(),
                    "type": "workspace_observation",
                    "observation_id": latest_observation["observation_id"],
                    "snapshot_fingerprint": latest_observation[
                        "snapshot_fingerprint"
                    ],
                    "change": latest_observation["change"],
                },
            )
            output.write(render_observation(latest_observation) + "\n")
            continue
        if text == "/reference-intelligence" or text.startswith(
            "/reference-intelligence "
        ):
            from palamedes_observe import collect_observation
            from palamedes_reference_intelligence import (
                ReferenceIntelligenceStore,
                run_reference_intelligence,
            )

            explicit_path = text[len("/reference-intelligence") :].strip()
            ref_value = explicit_path or os.environ.get("PALAMEDES_REF_ROOT", "").strip()
            try:
                latest_observation = collect_observation(
                    workspace,
                    ref_root=Path(ref_value).expanduser() if ref_value else None,
                )
                intelligence = run_reference_intelligence(
                    provider=provider,
                    store=ReferenceIntelligenceStore(
                        mission_store.root / "reference-intelligence"
                    ),
                    snapshot=latest_observation,
                )
            except (OSError, RuntimeError, ValueError) as exc:
                output.write(f"[reference intelligence error] {exc}\n")
                continue
            agenda = intelligence["selected_agenda"]
            output.write(
                f"Reference intelligence {intelligence['reference_intelligence_id']}: "
                f"mode={intelligence['reference_mode']} "
                f"hypotheses={len(intelligence['hypotheses'])} "
                f"agenda={agenda['status']}.\n"
            )
            output.write(f"Research question: {agenda['prompt']}\n")
            continue
        if text.startswith("/backfill-outcomes"):
            parts = text.split()
            try:
                limit = int(parts[1]) if len(parts) == 2 else 12
                if len(parts) > 2:
                    raise ValueError
            except ValueError:
                output.write("/backfill-outcomes accepts one integer from 1 to 24.\n")
                continue
            from palamedes_prompt import PromptAgendaStore, run_outcome_backfill

            output.write(f"Mapping up to {limit} immutable legacy outcomes...\n")
            try:
                backfill = run_outcome_backfill(
                    provider=provider,
                    store=PromptAgendaStore(
                        mission_store.root / "prompt-intelligence"
                    ),
                    outcomes=mission_store.outcomes(),
                    already_interpreted_outcome_ids={
                        item["outcome_id"]
                        for item in mission_store.outcome_interpretations()
                    },
                    limit=limit,
                )
            except (RuntimeError, ValueError) as exc:
                output.write(f"[outcome backfill error] {exc}\n")
                continue
            output.write(
                f"Outcome backfill {backfill['status']}: "
                f"{len(backfill['records'])} records; source outcomes unchanged.\n"
            )
            continue
        if text.startswith("/satisfaction-json "):
            from palamedes_satisfaction import SatisfactionStore, assess_satisfaction

            raw = text[len("/satisfaction-json ") :].strip()
            try:
                request = json.loads(raw)
                assessment = assess_satisfaction(workspace, request)
            except (json.JSONDecodeError, OSError, RuntimeError, ValueError) as exc:
                output.write(f"Satisfaction assessment rejected: {exc}\n")
                continue
            path = SatisfactionStore(
                mission_store.root.parent / "satisfaction"
            ).save(assessment)
            output.write(
                f"Satisfaction {assessment['requirement_id']}: "
                f"state={assessment['evidence_state']} "
                f"disposition={assessment['disposition']} "
                f"missing={len(assessment['missing_evidence_kinds'])}\n"
                f"Assessment: {path}\n"
            )
            continue
        if text == "/satisfactions":
            from palamedes_satisfaction import SatisfactionStore

            assessments = SatisfactionStore(
                mission_store.root.parent / "satisfaction"
            ).latest()
            if not assessments:
                output.write("No host-verified satisfaction assessments.\n")
                continue
            for assessment in assessments:
                output.write(
                    f"{assessment['requirement_id']}: "
                    f"{assessment['evidence_state']} / {assessment['disposition']} "
                    f"({assessment['assessment_id']})\n"
                )
            continue
        if text.startswith("/alignment-candidate-json "):
            from palamedes_product_alignment import ProductAlignmentStore

            raw = text[len("/alignment-candidate-json ") :].strip()
            try:
                request = json.loads(raw)
                candidate = ProductAlignmentStore(
                    mission_store.root.parent / "product-alignment"
                ).propose_candidate(
                    candidate_type=request["candidate_type"],
                    payload=request["payload"],
                    source_ids=request["source_ids"],
                    surface_key=str(request.get("surface_key", "")),
                )
            except (KeyError, json.JSONDecodeError, OSError, ValueError) as exc:
                output.write(f"Alignment candidate rejected: {exc}\n")
                continue
            output.write(
                f"Alignment candidate proposed: {candidate['candidate_id']} "
                f"type={candidate['candidate_type']} surface="
                f"{candidate.get('surface_key') or 'global'}\n"
                "No active product ground truth changed. Approve explicitly to merge it.\n"
            )
            continue
        if text.startswith("/alignment-approve "):
            from palamedes_product_alignment import ProductAlignmentStore

            candidate_id = text[len("/alignment-approve ") :].strip()
            try:
                approved_candidate = ProductAlignmentStore(
                    mission_store.root.parent / "product-alignment"
                ).approve_candidate(candidate_id, approver="chat-user")
            except (OSError, ValueError) as exc:
                output.write(f"Alignment approval rejected: {exc}\n")
                continue
            output.write(
                f"Alignment candidate approved: {candidate_id} "
                f"idempotent={approved_candidate['idempotent']}\n"
            )
            continue
        if text == "/alignment":
            from palamedes_product_alignment import ProductAlignmentStore

            context = ProductAlignmentStore(
                mission_store.root.parent / "product-alignment"
            ).active_context()
            output.write(json.dumps(context, ensure_ascii=False, indent=2) + "\n")
            continue
        if text == "/storage":
            from palamedes_storage import inventory_storage

            inventory = inventory_storage(mission_store.root.parent)
            summary = inventory["summary"]
            output.write(
                "Storage inventory (read-only): "
                f"files={summary['files']} logical={summary['logical_bytes']} "
                f"unique={summary['unique_content_bytes']} "
                f"reclaimable={summary['duplicate_reclaimable_bytes']} "
                f"duplicate_groups={summary['duplicate_groups']}\n"
                f"Fingerprint: {inventory['inventory_fingerprint']}\n"
            )
            continue
        if text.startswith("/reconcile"):
            parts = text.split()
            apply_reconcile = len(parts) == 3 and parts[1] == "--apply"
            if parts != ["/reconcile"] and not apply_reconcile:
                output.write(
                    "/reconcile accepts no arguments, or --apply <proposal-fingerprint>.\n"
                )
                continue
            from palamedes_lifecycle import reconcile_lifecycle

            try:
                report = reconcile_lifecycle(
                    mission_store.root,
                    apply=apply_reconcile,
                    expected_proposal_fingerprint=parts[2] if apply_reconcile else "",
                )
            except ValueError as exc:
                output.write(f"Lifecycle reconcile blocked: {exc}\n")
                continue
            summary = report["summary"]
            output.write(
                f"Lifecycle reconcile ({report['mode']}): "
                f"handoffs={summary['handoffs']} outcomes={summary['outcomes']} "
                f"proposals={summary['proposals']} applied={summary['applied']} "
                f"conflicts={summary['conflicts']} orphans={summary['orphan_outcomes']} "
                f"malformed={summary['malformed_records']}\n"
            )
            output.write(
                "Projected states: "
                + json.dumps(summary["by_projected_state"], ensure_ascii=False, sort_keys=True)
                + "\nClassifications: "
                + json.dumps(summary["by_classification"], ensure_ascii=False, sort_keys=True)
                + "\n"
            )
            output.write(f"Report fingerprint: {report['report_fingerprint']}\n")
            output.write(f"Proposal fingerprint: {report['proposal_fingerprint']}\n")
            if report["conflicts"]:
                output.write("Conflicts remain fail-closed:\n")
                for conflict in report["conflicts"][:10]:
                    output.write(
                        f"  {conflict['handoff_id']}: "
                        + ", ".join(conflict["reasons"])
                        + "\n"
                    )
            if report["mode"] == "dry_run" and summary["proposals"]:
                output.write(
                    "No files changed. Apply only this reviewed set with "
                    f"/reconcile --apply {report['proposal_fingerprint']}\n"
                )
            continue
        if text.startswith("/context-ablation"):
            parts = text.split()
            if len(parts) not in {2, 3}:
                output.write(
                    "/context-ablation requires a cycle ID and optional repeat count.\n"
                )
                continue
            try:
                repeat_count = int(parts[2]) if len(parts) == 3 else 1
            except ValueError:
                output.write("/context-ablation repeat count must be an integer.\n")
                continue
            if not 1 <= repeat_count <= 20:
                output.write("/context-ablation repeat count must be from 1 to 20.\n")
                continue
            record_root = (
                palamedes_module.STATE_DIR / "missions" / "context-ablations"
            )
            for repeat_index in range(repeat_count):
                try:
                    record = run_context_ablation(
                        provider=provider,
                        cycle_store=cognition_store,
                        cycle_id=parts[1],
                        record_root=record_root,
                    )
                except (OSError, RuntimeError, ValueError) as exc:
                    failure = record_context_ablation_failure(
                        provider=provider,
                        cycle_id=parts[1],
                        record_root=record_root,
                        error=exc,
                    )
                    output.write(
                        f"[context ablation error {repeat_index + 1}/{repeat_count}] "
                        f"{exc} · preserved={failure['failure_id']}\n"
                    )
                    continue
                judgment = record["blinded_judgment"]
                aggregate = record["aggregate_summary"]
                output.write(
                    f"Context ablation: {record['context_ablation_id']} "
                    f"({repeat_index + 1}/{repeat_count})\n"
                    f"  source cycle: {record['source_cognition_cycle_id']}\n"
                    f"  material direction shift: "
                    f"{record['material_direction_shift']}\n"
                    f"  shift dimensions: "
                    f"{', '.join(judgment['shift_dimensions']) or 'none'}\n"
                    f"  suspected path dependence: "
                    f"{record['suspected_path_dependence']}\n"
                    f"  abstraction collapse signal: "
                    f"{record['abstraction_collapse_signal']}\n"
                    f"  completed pairs: {aggregate['completed_pair_count']} · "
                    f"failed attempts: {aggregate['failed_attempt_count']} · "
                    f"shift rate: {aggregate['material_direction_shift_rate']:.2f} · "
                    f"collapse rate: {aggregate['abstraction_collapse_signal_rate']:.2f}\n"
                    "  evidence limit: shared-model pairs; no causal proof\n"
                )
            continue
        if text.startswith("/cycle"):
            context = text[len("/cycle") :].strip()
            audit_mode = False
            resume_cycle_id = ""
            cycle_mode = "auto"
            route = None
            if context.startswith("--mode audit"):
                remainder = context[len("--mode audit") :]
                if remainder and not remainder[0].isspace():
                    output.write("/cycle --mode audit requires context.\n")
                    continue
                audit_mode = True
                cycle_mode = "component"
                context = remainder.strip()
            elif context.startswith("--skip-vision"):
                remainder = context[len("--skip-vision") :]
                if remainder and not remainder[0].isspace():
                    output.write("/cycle --skip-vision requires context.\n")
                    continue
                audit_mode = True
                cycle_mode = "component"
                context = remainder.strip()
            else:
                for explicit_mode in ("auto", "lookup", "micro", "component", "product"):
                    prefix = f"--mode {explicit_mode}"
                    if context.startswith(prefix):
                        remainder = context[len(prefix) :]
                        if remainder and not remainder[0].isspace():
                            output.write(f"/cycle {prefix} requires context.\n")
                            cycle_mode = "invalid"
                            break
                        cycle_mode = explicit_mode
                        context = remainder.strip()
                        break
                if cycle_mode == "invalid":
                    continue
            if context.startswith("--resume"):
                parts = context.split()
                if len(parts) != 2:
                    output.write("/cycle --resume requires exactly one cycle ID.\n")
                    continue
                resume_cycle_id = parts[1]
                audit_mode = True
                cycle_mode = "resume"
                context = f"resume {resume_cycle_id}"
            if not context:
                output.write("/cycle requires context.\n")
                continue
            cycle_budget: Optional[Dict[str, Any]] = None
            if cycle_mode != "resume":
                from palamedes_cost_router import (
                    MODE_BUDGETS,
                    enforced_budget,
                    infer_route_request,
                    route_cycle,
                )
                from palamedes_satisfaction import (
                    SatisfactionStore,
                    assessment_is_current,
                )

                stored_assessments = SatisfactionStore(
                    mission_store.root.parent / "satisfaction"
                ).latest()
                assessments = [
                    row
                    for row in stored_assessments
                    if assessment_is_current(mission_store.root.parent.parent, row)
                ]
                if cycle_mode == "auto":
                    try:
                        route_request = (
                            json.loads(context)
                            if context.startswith("{")
                            else infer_route_request(context, assessments)
                        )
                        route = route_cycle(route_request)
                    except (json.JSONDecodeError, ValueError) as exc:
                        output.write(f"Cycle preflight rejected: {exc}\n")
                        continue
                    cycle_mode = route["mode"]
                    context = route["objective"]
                else:
                    route = {
                        "route_id": "manual-override",
                        "mode": cycle_mode,
                        "budget": dict(MODE_BUDGETS[cycle_mode]),
                        "reasons": ["explicit user mode override"],
                        "manual_override_allowed": True,
                    }
                budget = route["budget"]
                cycle_budget = enforced_budget(budget)
                output.write(
                    f"Cycle preflight: mode={cycle_mode} "
                    f"calls={budget['provider_calls_min']}-{budget['provider_calls_max']} "
                    f"tokens≤{budget['token_budget_high']} "
                    f"time≤{budget['time_minutes_high']}m "
                    f"(enforced with one schema retry: "
                    f"calls≤{cycle_budget['provider_calls_max']}, "
                    f"tokens≤{cycle_budget['token_budget_high']}) · "
                    + "; ".join(route["reasons"])
                    + "\n"
                )
                audit_mode = cycle_mode != "product"
            wait_gate = mission_store.external_evidence_wait_gate()
            if wait_gate is not None and cycle_mode != "lookup":
                output.write(
                    "WAITING_FOR_EXTERNAL_EVIDENCE\n"
                    f"  gate: {wait_gate['gate_id']}\n"
                    f"  required: {wait_gate['required_response']}\n"
                    "  provider_calls: 0\n"
                    "Resolve it with /external-evidence before starting another cycle.\n"
                )
                continue
            store.append(
                active_session,
                {
                    "ts": utc_now(),
                    "role": "user",
                    "content": text,
                    "provider": provider.provider_name,
                    "model": provider.model,
                    "cycle_mode": cycle_mode,
                    "human_input_event": {
                        "observed_at": utc_now(),
                        "active_duration_ms": None,
                        "custody": "submission_observed_duration_unobservable",
                    },
                },
            )
            if cycle_mode == "lookup":
                output.write(
                    "Lookup completed with provider_calls=0. The current host-verified "
                    "evidence does not justify another implementation mission.\n"
                )
                continue
            if cycle_mode == "micro":
                output.write("Running bounded micro mission compiler.\n")
            else:
                output.write(
                    "Running independent roles: interpreter → inventor → adversary → selector\n"
                )
            if audit_mode and cycle_mode != "micro":
                output.write(
                    "Audit mode: bounded execution disables automatic Vision Genesis "
                    "and meta-learning calls.\n"
                )
            try:
                from palamedes_observe import (
                    collect_observation,
                    observation_context,
                )

                ref_value = os.environ.get("PALAMEDES_REF_ROOT", "").strip()
                latest_observation = collect_observation(
                    workspace,
                    ref_root=Path(ref_value).expanduser() if ref_value else None,
                )
                from palamedes_vision import VisionStore, selected_vision_context

                vision_store = VisionStore(
                    mission_store.root.parent / "visions"
                )
                from palamedes_product_alignment import ProductAlignmentStore

                current_product_ground_truth = ProductAlignmentStore(
                    mission_store.root.parent / "product-alignment"
                ).active_context()
                latest_vision = vision_store.latest()
                latest_vision_id = (
                    str(latest_vision.get("vision_genesis_id", ""))
                    if isinstance(latest_vision, dict)
                    else ""
                )
                actual_investment = (
                    mission_store.vision_investment_summary(latest_vision_id)
                    if latest_vision_id
                    else None
                )
                if not audit_mode and vision_store.needs_wake(
                    len(mission_store.outcomes()),
                    _fingerprint(current_product_ground_truth),
                    actual_investment,
                ):
                    output.write(
                        "Vision wake: searching beyond adjacent product features.\n"
                    )
                    vision_record = run_autonomous_vision(
                        provider=provider,
                        mission_store=mission_store,
                        context=build_autonomous_vision_context(
                            mission_store=mission_store,
                            user_context=context,
                            workspace_context=observation_context(
                                latest_observation
                            ),
                        ),
                    )
                    output.write(render_vision(vision_record) + "\n")
                if not audit_mode:
                    try:
                        meta_learning = run_automatic_meta_learning(
                            provider=provider,
                            mission_store=mission_store,
                            snapshot=latest_observation,
                        )
                        if meta_learning["status"] == "completed":
                            output.write(
                                "Automatic meta-learning refreshed bounded outcome and "
                                "reference intelligence.\n"
                            )
                    except (OSError, RuntimeError, ValueError) as exc:
                        store.append(
                            active_session,
                            {
                                "ts": utc_now(),
                                "type": "automatic_meta_learning_failed",
                                "error": str(exc),
                                "observation_id": latest_observation["observation_id"],
                            },
                        )
                        output.write(
                            f"[automatic meta-learning degraded] {exc}; "
                            "continuing with the existing evidence state.\n"
                        )
                grounded_context = (
                    f"User request:\n{context}\n\n"
                    "Bounded workspace observation:\n"
                    + json.dumps(
                        observation_context(latest_observation),
                        ensure_ascii=False,
                    )
                    + "\n\nOpen outcome evidence gates:\n"
                    + json.dumps(
                        mission_store.open_outcome_gates(),
                        ensure_ascii=False,
                    )
                )
                active_vision = (
                    None
                    if audit_mode
                    else selected_vision_context(vision_store.latest())
                )
                if active_vision:
                    grounded_context += (
                        "\n\nAutonomously originated product vision "
                        "(hypothesis only; no delivery authority):\n"
                        + json.dumps(active_vision, ensure_ascii=False)
                    )
                alignment_context = ProductAlignmentStore(
                    mission_store.root.parent / "product-alignment"
                ).active_context()
                if any(alignment_context.get(key) for key in alignment_context):
                    grounded_context += (
                        "\n\nProduct ground truth and architecture context "
                        "(respond explicitly; do not optimize against an unknown or "
                        "conflicting purpose):\n"
                        + json.dumps(alignment_context, ensure_ascii=False)
                    )
                from palamedes_prompt import PromptAgendaStore

                prompt_agendas = PromptAgendaStore(
                    mission_store.root / "prompt-intelligence"
                ).active_agendas()
                if prompt_agendas:
                    grounded_context += (
                        "\n\nSelf-authored bounded research agendas "
                        "(research direction only; constitution and authority remain fixed):\n"
                        + json.dumps(prompt_agendas, ensure_ascii=False)
                    )
                from palamedes_reference_intelligence import ReferenceIntelligenceStore

                reference_agendas = ReferenceIntelligenceStore(
                    mission_store.root / "reference-intelligence"
                ).active_agendas()
                if reference_agendas:
                    grounded_context += (
                        "\n\nSource-bounded reference intelligence agendas "
                        "(research only; no delivery authority):\n"
                        + json.dumps(reference_agendas, ensure_ascii=False)
                    )
                from palamedes_satisfaction import (
                    SatisfactionStore,
                    assessment_is_current,
                )

                satisfaction_assessments = SatisfactionStore(
                    mission_store.root.parent / "satisfaction"
                ).latest()
                satisfaction_assessments = [
                    {
                        **row,
                        "live_current": assessment_is_current(
                            mission_store.root.parent.parent, row
                        ),
                    }
                    for row in satisfaction_assessments
                ]
                if satisfaction_assessments:
                    grounded_context += (
                        "\n\nHost-verified requirement satisfaction assessments "
                        "(current-snapshot already_satisfied requirements must not become "
                        "implementation missions):\n"
                        + json.dumps(satisfaction_assessments, ensure_ascii=False)
                    )
                team_context = current_team_context()
                if team_context is not None:
                    grounded_context += (
                        "\n\nShared team cognition:\n"
                        + json.dumps(team_context, ensure_ascii=False)
                    )
                if cycle_mode == "micro":
                    result = run_micro_cycle(
                        provider=provider,
                        palamedes_module=palamedes_module,
                        context=grounded_context,
                        cycle_store=cognition_store,
                        progress=lambda message: (
                            output.write(message + "\n"), output.flush()
                        ),
                    )
                else:
                    result = run_cognition_cycle(
                        provider=provider,
                        palamedes_module=palamedes_module,
                        context=grounded_context,
                        cycle_store=cognition_store,
                        budget=cycle_budget,
                        progress=lambda message: (
                            output.write(message + "\n"), output.flush()
                        ),
                        resume_cycle_id=resume_cycle_id,
                    )
            except (OSError, RuntimeError, ValueError) as exc:
                output.write(f"[cognition cycle error] {exc}\n")
                output.write("Partial role artifacts were preserved; no mission draft was issued.\n")
                continue
            cycle = result["cycle"]
            store.append(
                active_session,
                {
                    "ts": utc_now(),
                    "type": "cognition_cycle",
                    "cognition_cycle_id": cycle["cognition_cycle_id"],
                    "status": cycle["status"],
                    "decision": cycle["decision"],
                    "role_count": len(cycle["artifacts"]),
                    "observation_id": latest_observation["observation_id"],
                    "cycle_mode": cycle_mode,
                    "run_id": cycle["run_id"],
                    "provider_usage": cycle.get("provider_usage", {}),
                },
            )
            contract = result["contract"]
            if contract is None:
                output.write(
                    f"Cycle {cycle['cognition_cycle_id']} ended with "
                    f"{cycle['decision']}; no mission draft was issued.\n"
                )
                continue
            if active_vision:
                investment = active_vision.get("investment_judgment", {})
                contract["vision_lineage"] = {
                    "vision_genesis_id": active_vision["vision_genesis_id"],
                    "vision_context_fingerprint": active_vision.get(
                        "vision_context_fingerprint", ""
                    ),
                    "product_ground_truth_fingerprint": active_vision.get(
                        "product_ground_truth_fingerprint", ""
                    ),
                    "requirement_gate_passed": active_vision.get(
                        "requirement_gate_passed", False
                    ),
                    "evidence_maturity": investment.get("evidence_maturity", ""),
                    "selected_alternative": investment.get(
                        "selected_alternative", ""
                    ),
                    "renewal_evidence": investment.get("renewal_evidence", []),
                    "kill_criteria": investment.get("kill_criteria", []),
                    "debt_guard": investment.get("debt_guard", ""),
                    "scale_guard": investment.get("scale_guard", ""),
                    "investment_envelope": active_vision.get(
                        "investment_envelope", {}
                    ),
                    "delivery_authority_granted": False,
                }
                lineage_fingerprint = _fingerprint(
                    {
                        "prior_contract_fingerprint": contract[
                            "contract_fingerprint"
                        ],
                        "vision_lineage": contract["vision_lineage"],
                    }
                )
                contract["mission_id"] = f"mission-{lineage_fingerprint[:12]}"
                contract["contract_fingerprint"] = lineage_fingerprint
            mission_store.save_contract(contract)
            store.append(
                active_session,
                {
                    "ts": utc_now(),
                    "type": "mission_state",
                    "mission_id": contract["mission_id"],
                    "status": "draft",
                    "contract_fingerprint": contract["contract_fingerprint"],
                    "cognition_cycle_id": cycle["cognition_cycle_id"],
                },
            )
            reply = (
                f"Cognition cycle: {cycle['cognition_cycle_id']}\n"
                f"Independent role calls: {len(cycle['artifacts'])}\n"
                + render_mission(contract)
            )
            store.append(
                active_session,
                {
                    "ts": utc_now(),
                    "role": "assistant",
                    "content": reply,
                    "provider": provider.provider_name,
                    "model": provider.model,
                },
            )
            output.write(reply + "\n")
            continue
        if text == "/preview":
            records = store.load(active_session)
            mission_id = latest_mission_id(records, {"draft"})
            if not mission_id:
                output.write("No pending mission draft in this session.\n")
                continue
            output.write(render_mission(mission_store.load_contract(mission_id)) + "\n")
            continue
        if text == "/approve":
            records = store.load(active_session)
            mission_id = latest_mission_id(records, {"draft"})
            if not mission_id:
                output.write("No pending mission draft to approve.\n")
                continue
            contract = mission_store.load_contract(mission_id)
            try:
                result = approve_mission(
                    palamedes_module, mission_store, contract, active_session
                )
            except ValueError as exc:
                output.write(f"Mission approval blocked: {exc}\n")
                continue
            store.append(
                active_session,
                {
                    "ts": utc_now(),
                    "type": "mission_state",
                    "mission_id": mission_id,
                    "status": "approved",
                    "handoff_id": result["handoff"]["handoff_id"],
                },
            )
            output.write(
                f"Mission approved: {mission_id}\n"
                f"Planner handoff: {result['handoff_path']}\n"
                "Delivery authority remains ungranted.\n"
            )
            continue
        if text.startswith("/reject"):
            reason = text[len("/reject") :].strip()
            if not reason:
                output.write("/reject requires a reason.\n")
                continue
            records = store.load(active_session)
            mission_id = latest_mission_id(records, {"draft"})
            if not mission_id:
                output.write("No pending mission draft to reject.\n")
                continue
            contract = mission_store.load_contract(mission_id)
            contract.update(
                {"status": "rejected", "rejected_at": utc_now(), "rejection_reason": reason}
            )
            mission_store.save_contract(contract)
            store.append(
                active_session,
                {
                    "ts": utc_now(),
                    "type": "mission_state",
                    "mission_id": mission_id,
                    "status": "rejected",
                    "reason": reason,
                },
            )
            output.write(f"Mission rejected: {mission_id}\n")
            continue
        if text == "/handoff":
            records = store.load(active_session)
            mission_id = latest_mission_id(records, {"approved", "outcome_recorded"})
            if not mission_id:
                output.write("No approved mission handoff in this session.\n")
                continue
            path = mission_store.handoff_root / f"handoff-{mission_id[8:]}.json"
            if not path.is_file():
                output.write(f"Handoff is missing for {mission_id}.\n")
                continue
            output.write(path.read_text(encoding="utf-8"))
            continue
        if text.startswith("/planner-ack"):
            raw = text[len("/planner-ack") :].strip()
            if not raw:
                output.write("/planner-ack requires planner-id and optional acknowledgment JSON.\n")
                continue
            parts = raw.split(maxsplit=1)
            planner_id = parts[0].strip()
            if not planner_id:
                output.write("/planner-ack requires a planner-id.\n")
                continue
            payload: Dict[str, Any] = {}
            if len(parts) == 2:
                ack_payload = parts[1].strip()
                try:
                    payload = json.loads(ack_payload)
                except json.JSONDecodeError as exc:
                    output.write(f"/planner-ack JSON payload parse error: {exc}\n")
                    continue
                if not isinstance(payload, dict):
                    output.write("/planner-ack payload must be a JSON object.\n")
                    continue
            records = store.load(active_session)
            mission_id = latest_mission_id(records, {"approved", "outcome_recorded"})
            if not mission_id:
                output.write("No approved mission to acknowledge in this session.\n")
                continue
            try:
                result = acknowledge_planner_handoff(
                    mission_store=mission_store,
                    mission_id=mission_id,
                    planner_id=planner_id,
                    acknowledgment=payload,
                )
            except ValueError as exc:
                output.write(f"Planner handoff acknowledgment failed: {exc}\n")
                continue
            store.append(
                active_session,
                {
                    "ts": utc_now(),
                    "type": "mission_state",
                    "mission_id": mission_id,
                    "status": "approved",
                    "handoff_id": result["handoff_id"],
                    "handoff_state": result["acknowledged_state"],
                    "planner_id": planner_id,
                    "planner_acknowledgment_id": result["acknowledgment_id"],
                },
            )
            output.write(
                f"Planner acknowledged: {planner_id} -> {mission_id}\n"
                f"Handoff state: {result['acknowledged_state']}\n"
                f"Lifecycle event appended: {str(result['lifecycle_event_appended']).lower()}\n"
                f"Acknowledgment ID: {result['acknowledgment_id']}\n"
            )
            continue
        if text.startswith("/outcome-json") or text.startswith("/outcome"):
            actual_investment = None
            if text.startswith("/outcome-json"):
                raw = text[len("/outcome-json") :].strip()
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError as exc:
                    output.write(f"/outcome-json requires valid JSON: {exc}\n")
                    continue
                if not isinstance(payload, dict):
                    output.write("/outcome-json requires one JSON object.\n")
                    continue
                status = str(payload.get("status", "")).strip()
                observation = str(payload.get("observation", "")).strip()
                actual_investment = payload.get("actual_investment")
                outcome_type = str(payload.get("outcome_type", "")).strip()
                execution_status = str(
                    payload.get("execution_status", "completed")
                ).strip()
                if not status or not observation:
                    output.write(
                        "/outcome-json requires status and observation.\n"
                    )
                    continue
            else:
                raw = text[len("/outcome") :].strip()
                parts = raw.split(maxsplit=2)
                explicit_mission_id = (
                    parts[0] if parts and re.fullmatch(r"mission-[a-f0-9]{12}", parts[0]) else ""
                )
                if explicit_mission_id and len(parts) == 3:
                    status, observation = parts[1], parts[2]
                elif not explicit_mission_id and len(parts) >= 2:
                    status, observation = parts[0], " ".join(parts[1:])
                else:
                    output.write(
                        "/outcome requires: [mission-id] success|failure|mixed|unknown <observation>\n"
                    )
                    continue
            records = store.load(active_session)
            mission_id = (
                explicit_mission_id
                if not text.startswith("/outcome-json") and explicit_mission_id
                else latest_mission_id(records, {"approved", "outcome_recorded"})
            )
            if not mission_id:
                output.write("No approved mission can accept an outcome.\n")
                continue
            try:
                contract = mission_store.load_contract(mission_id)
            except ValueError as exc:
                output.write(f"{exc}\n")
                continue
            try:
                outcome = record_mission_outcome(
                    palamedes_module,
                    mission_store,
                    contract,
                    status,
                    observation,
                    actual_investment,
                    outcome_type if text.startswith("/outcome-json") else "",
                    execution_status if text.startswith("/outcome-json") else "completed",
                )
            except ValueError as exc:
                output.write(f"{exc}\n")
                continue
            try:
                analysis_result = run_outcome_analyst(
                    provider=provider,
                    cycle_store=cognition_store,
                    mission_store=mission_store,
                    contract=contract,
                    outcome=outcome,
                    progress=lambda message: output.write(message + "\n"),
                )
            except (RuntimeError, ValueError) as exc:
                analysis_result = {"status": "failed", "reason": str(exc)}
            store.append(
                active_session,
                {
                    "ts": utc_now(),
                    "type": "mission_state",
                    "mission_id": mission_id,
                    "status": "outcome_recorded",
                    "outcome_id": outcome["outcome_id"],
                    "outcome_status": status,
                    "execution_status": outcome["execution_status"],
                    "evaluation_status": outcome["evaluation_status"],
                    "outcome_type": outcome["outcome_type"],
                    "outcome_analysis_status": analysis_result["status"],
                },
            )
            output.write(
                f"Outcome recorded: {outcome['outcome_id']} ({status} / {outcome['outcome_type']})\n"
            )
            if analysis_result["status"] == "completed":
                analysis_output = analysis_result["analysis"]["output"]
                disposition = analysis_output["mission_disposition"]
                output.write(
                    "Outcome analyst completed: "
                    f"probe={analysis_output['probe_status']} "
                    f"finding={analysis_output['finding']} "
                    f"disposition={disposition} "
                    f"followup_required={str(analysis_output['followup_required']).lower()}\n"
                )
                prompt_result = analysis_result.get("prompt_architecture", {})
                if prompt_result.get("status") == "completed":
                    agenda = prompt_result["agenda"]
                    output.write(
                        "Self-authored research agenda selected: "
                        f"{agenda['prompt_agenda_id']} "
                        f"mode={agenda['missing_cognitive_mode']}\n"
                    )
                elif prompt_result.get("status") == "failed":
                    output.write(
                        "Prompt architecture failed without invalidating the outcome: "
                        f"{prompt_result['error']}\n"
                    )
            elif analysis_result["status"] == "not_applicable":
                output.write(
                    "Attribution remains unresolved: this mission predates a cognition cycle.\n"
                )
            else:
                output.write(
                    f"Outcome was preserved, but outcome analyst failed: "
                    f"{analysis_result.get('reason', 'unknown error')}\n"
                )
            continue

        user_content = text
        command = text.split(maxsplit=1)[0]
        if command in CHAT_COMMANDS:
            remainder = text[len(command) :].strip()
            if not remainder:
                output.write(f"{command} requires a topic or context.\n")
                continue
            mission_context = remainder
            if command == "/mission":
                mission_context += (
                    "\n\nOpen outcome evidence gates:\n"
                    + json.dumps(
                        mission_store.open_outcome_gates(),
                        ensure_ascii=False,
                    )
                )
            user_content = (
                mission_prompt(mission_context)
                if command == "/mission"
                else f"{CHAT_COMMANDS[command]}\n\nUser context:\n{remainder}"
            )
        elif text.startswith("/"):
            output.write(f"Unknown command: {command}. Type /help.\n")
            continue

        store.append(
            active_session,
            {
                "ts": utc_now(),
                "role": "user",
                "content": text,
                "provider": provider.provider_name,
                "model": provider.model,
            },
        )
        records = store.load(active_session)
        messages = [
            {
                "role": "system",
                "content": system_prompt(
                    palamedes_module,
                    workspace,
                    current_team_context(),
                ),
            },
            *_history_messages(records[:-1], history_limit),
            {"role": "user", "content": user_content},
        ]
        chunks: List[str] = []
        is_mission = command == "/mission"
        if not is_mission:
            output.write("\n")
        try:
            for chunk in provider.stream(messages):
                chunks.append(chunk)
                if not is_mission:
                    output.write(chunk)
                    output.flush()
        except (RuntimeError, ValueError) as exc:
            output.write(f"\n[provider error] {exc}\n\n")
            continue
        reply = "".join(chunks).strip()
        if is_mission:
            try:
                contract = validate_mission_draft(_extract_json_object(reply))
            except ValueError as exc:
                output.write(f"[mission validation error] {exc}\n")
                output.write("Draft was not saved or made approvable.\n\n")
                continue
            mission_store.save_contract(contract)
            store.append(
                active_session,
                {
                    "ts": utc_now(),
                    "type": "mission_state",
                    "mission_id": contract["mission_id"],
                    "status": "draft",
                    "contract_fingerprint": contract["contract_fingerprint"],
                },
            )
            reply = render_mission(contract)
            output.write(reply + "\n\n")
        else:
            output.write("\n\n")
        if reply:
            store.append(
                active_session,
                {
                    "ts": utc_now(),
                    "role": "assistant",
                    "content": reply,
                    "provider": provider.provider_name,
                    "model": provider.model,
                },
            )


def cmd_chat(args: Any, palamedes_module: Any) -> None:
    health = provider_health(args.provider)
    if health["status"] != "ok":
        raise ValueError(
            f"{args.provider} is unavailable: {health['credential_hint']}"
        )
    session_id = args.session or os.environ.get("PALAMEDES_CHAT_SESSION", "").strip()
    if not session_id:
        session_id = uuid.uuid4().hex[:12]
    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else Path.cwd()
    if not workspace.is_dir():
        raise ValueError(f"workspace does not exist or is not a directory: {workspace}")
    from palamedes_observe import bind_workspace

    bind_workspace(palamedes_module, workspace)
    ChatSessionStore(palamedes_module.STATE_DIR / "chat").path(session_id)
    if args.history_limit < 2 or args.history_limit > 200:
        raise ValueError("history-limit must be between 2 and 200")
    provider = provider_from_config(args.provider, args.model)
    team_state = str(getattr(args, "team_state", "") or "").strip()
    team_store = None
    if team_state:
        team_store = palamedes_module.team_cognition_store(
            Path(team_state).expanduser().resolve()
        )
    run_chat(
        palamedes_module=palamedes_module,
        provider=provider,
        session_id=session_id,
        history_limit=args.history_limit,
        team_store=team_store,
        agent_id=str(getattr(args, "agent_id", "") or "").strip(),
        agent_role=str(getattr(args, "agent_role", "strategist") or "strategist").strip(),
    )
