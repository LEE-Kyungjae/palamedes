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
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Protocol, TextIO


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


@dataclass
class OpenRouterChatProvider:
    model: str = DEFAULT_OPENROUTER_MODEL
    base_url: str = "https://openrouter.ai/api/v1"
    provider_name: str = "openrouter"

    def stream(self, messages: List[Dict[str, str]]) -> Iterable[str]:
        api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OpenRouter requires OPENROUTER_API_KEY")
        payload = {"model": self.model, "messages": messages, "stream": True}
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

    def stream(self, messages: List[Dict[str, str]]) -> Iterable[str]:
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

    def save_handoff(self, handoff: Dict[str, Any]) -> Path:
        self.handoff_root.mkdir(parents=True, exist_ok=True)
        path = self.handoff_root / f"{handoff['handoff_id']}.json"
        path.write_text(
            json.dumps(handoff, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path

    def append_outcome(self, outcome: Dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.outcomes_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(outcome, ensure_ascii=False, sort_keys=True) + "\n")

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
    raw = "".join(
        provider.stream(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ]
        )
    )
    return _extract_json_object(raw)


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
) -> Dict[str, Any]:
    return {
        "role": role,
        "call_index": call_index,
        "provider": provider.provider_name,
        "model": provider.model,
        "completed_at": utc_now(),
        "prompt_fingerprint": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "output_fingerprint": _fingerprint(output),
        "output": output,
    }


def run_cognition_cycle(
    *,
    provider: ChatProvider,
    palamedes_module: Any,
    context: str,
    cycle_store: CognitionCycleStore,
    available_discovery_ids: Optional[set] = None,
) -> Dict[str, Any]:
    available_discovery_ids = available_discovery_ids or set()
    seed = {
        "context": context,
        "plan_context": json.loads(_plan_context(palamedes_module)),
        "started_at": utc_now(),
    }
    cycle_id = f"cycle-{_fingerprint(seed)[:12]}"
    cycle: Dict[str, Any] = {
        "cognition_cycle_version": "palamedes-cognition-cycle/1",
        "cognition_cycle_id": cycle_id,
        "status": "running",
        "context": context,
        "started_at": seed["started_at"],
        "provider": provider.provider_name,
        "model": provider.model,
        "role_order": ["interpreter", "inventor", "adversary", "selector", "outcome_analyst"],
        "artifacts": [],
        "outcome_analyses": [],
        "selection_authority_role": "selector",
        "outcome_analyst_runs_before_outcome": False,
    }
    cycle_store.save(cycle)
    system = (
        "You are one bounded cognitive role inside Palamedes. Return exactly one "
        "JSON object. Do not perform another role's job and do not claim external evidence."
    )
    try:
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

User context: {context}
Plan context: {_plan_context(palamedes_module)}"""
        interpreter = _provider_json(
            provider, system=system, prompt=interpreter_prompt
        )
        _non_empty_string_array(interpreter, "observations")
        _non_empty_string_array(interpreter, "tensions")
        _non_empty_string_array(interpreter, "missing_evidence")
        interpretations = interpreter.get("interpretations")
        if not isinstance(interpretations, list) or len(interpretations) < 2:
            raise ValueError("interpreter requires at least two interpretations")
        cycle["artifacts"].append(
            _role_artifact(
                role="interpreter",
                call_index=1,
                prompt=interpreter_prompt,
                output=interpreter,
                provider=provider,
            )
        )
        cycle_store.save(cycle)

        inventor_prompt = f"""ROLE: inventor
Generate at least three competing outcome-level missions from distinct frames.
Do not select a winner and do not criticize candidates.
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
        inventor = _provider_json(provider, system=system, prompt=inventor_prompt)
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
        cycle["artifacts"].append(
            _role_artifact(
                role="inventor",
                call_index=2,
                prompt=inventor_prompt,
                output=inventor,
                provider=provider,
            )
        )
        cycle_store.save(cycle)

        adversary_prompt = f"""ROLE: adversary
Attack every candidate, shared assumptions, proxy risks, hidden harms, owner bias,
and Palamedes self-expansion. Do not select a winner or rewrite candidates.
Return:
{{
  "critiques": [
    {{"candidate_id":"candidate-1","fatal_risks":["..."],"repairable_risks":["..."],"disqualifying":false}}
  ],
  "shared_assumptions": ["..."],
  "missing_opposition": ["..."],
  "minimum_disconfirming_probe": "..."
}}
Every candidate ID must have exactly one critique.

Interpreter:
{json.dumps(interpreter, ensure_ascii=False)}
Candidates:
{json.dumps(inventor, ensure_ascii=False)}"""
        adversary = _provider_json(provider, system=system, prompt=adversary_prompt)
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
        cycle["artifacts"].append(
            _role_artifact(
                role="adversary",
                call_index=3,
                prompt=adversary_prompt,
                output=adversary,
                provider=provider,
            )
        )
        cycle_store.save(cycle)

        selector_prompt = f"""ROLE: selector
Select, defer, or reject from the frozen candidates and critiques. You may not
invent a new candidate. Then compile the selected candidate into the exact
mission draft shape below. If evidence is weak, select an information-producing
probe and preserve uncertainty. Classify whether this cycle originated a
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

Candidates:
{json.dumps(inventor, ensure_ascii=False)}
Adversary:
{json.dumps(adversary, ensure_ascii=False)}"""
        selector = _provider_json(provider, system=system, prompt=selector_prompt)
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
        if not set(source_discovery_ids).issubset(available_discovery_ids):
            raise ValueError("selector cited an unavailable discovery ID")
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
        cycle["artifacts"].append(
            _role_artifact(
                role="selector",
                call_index=4,
                prompt=selector_prompt,
                output=selector,
                provider=provider,
            )
        )
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
        cycle["live_model_call_count"] = 4
        cycle["role_output_fingerprints_unique"] = (
            len({item["output_fingerprint"] for item in cycle["artifacts"]}) == 4
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
        return {"cycle": cycle, "contract": contract}
    except Exception as exc:
        cycle["status"] = "failed"
        cycle["failed_at"] = utc_now()
        cycle["failure"] = str(exc)
        cycle["live_model_call_count"] = len(cycle["artifacts"])
        cycle_store.save(cycle)
        raise


def run_outcome_analyst(
    *,
    provider: ChatProvider,
    cycle_store: CognitionCycleStore,
    mission_store: MissionStore,
    contract: Dict[str, Any],
    outcome: Dict[str, Any],
) -> Dict[str, Any]:
    cycle_id = str(contract.get("cognition_cycle_id", "")).strip()
    if not cycle_id:
        return {"status": "not_applicable", "reason": "mission has no cognition cycle"}
    cycle = cycle_store.load(cycle_id)
    prompt = f"""ROLE: outcome_analyst
An outcome now exists. Compare it with the frozen mission forecast without
rewriting prior artifacts. Separate mission, planning, implementation,
environment, and measurement attribution.
Return exactly:
{{
  "observed_vs_expected":"...",
  "attribution_hypotheses":[{{"layer":"mission|planning|implementation|environment|measurement","claim":"...","confidence":0}}],
  "belief_updates":["..."],
  "mission_disposition":"continue|revise|stop|insufficient_evidence",
  "next_probe":"...",
  "confidence":0
}}

Frozen cycle:
{json.dumps(cycle, ensure_ascii=False)}
Mission contract:
{json.dumps(contract, ensure_ascii=False)}
Observed outcome:
{json.dumps(outcome, ensure_ascii=False)}"""
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
    if output.get("mission_disposition") not in {
        "continue",
        "revise",
        "stop",
        "insufficient_evidence",
    }:
        raise ValueError("invalid mission_disposition")
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
    cycle["live_model_call_count"] = 4 + len(cycle["outcome_analyses"])
    cycle_store.save(cycle)
    from palamedes_thought import ThoughtStore, persist_mission_experience

    persist_mission_experience(
        store=ThoughtStore(mission_store.root.parent / "thoughts"),
        contract=contract,
        outcome=outcome,
        analysis=analysis,
    )
    if output["mission_disposition"] != "continue":
        mission_store.append_outcome_gate(
            {
                "gate_version": "palamedes-outcome-gate/1",
                "gate_id": f"gate-{outcome['outcome_id'][8:]}",
                "outcome_id": outcome["outcome_id"],
                "mission_contract_id": contract["mission_id"],
                "mission_disposition": output["mission_disposition"],
                "required_response": output["next_probe"],
                "status": "open",
                "opened_at": utc_now(),
            }
        )
    return {"status": "completed", "analysis": analysis}


def _extract_json_object(text: str) -> Dict[str, Any]:
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*", "", candidate)
        candidate = re.sub(r"\s*```$", "", candidate)
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValueError(f"mission response must be one JSON object: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("mission response must be a JSON object")
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
    }
    if normalized_outcome_response is not None:
        normalized["outcome_response"] = normalized_outcome_response
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
  "outcome_response": {{
    "related_outcome_ids": ["outcome IDs from open evidence gates, when present"],
    "action": "resolve|independent|accept_debt",
    "rationale": "why the next mission resolves, is independent from, or consciously carries the evidence debt"
  }}
}}

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
    open_gates = mission_store.open_outcome_gates()
    if open_gates:
        response = contract.get("outcome_response")
        related_ids = (
            response.get("related_outcome_ids", []) if isinstance(response, dict) else []
        )
        unresolved = [
            gate for gate in open_gates if gate.get("outcome_id") not in related_ids
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
    if open_gates:
        for gate in open_gates:
            resolved = dict(gate)
            resolved.update(
                {
                    "status": "responded",
                    "responded_at": ts,
                    "response_mission_contract_id": mission_id,
                    "response_action": contract["outcome_response"]["action"],
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


def record_mission_outcome(
    palamedes_module: Any,
    mission_store: MissionStore,
    contract: Dict[str, Any],
    status: str,
    observation: str,
) -> Dict[str, Any]:
    if contract.get("status") not in {"approved", "outcome_recorded"}:
        raise ValueError("outcomes require an approved mission")
    if status not in {"success", "failure", "mixed", "unknown"}:
        raise ValueError("outcome status must be success, failure, mixed, or unknown")
    ts = utc_now()
    mission_id = contract["mission_id"]
    outcome = {
        "outcome_version": "palamedes-mission-outcome/1",
        "outcome_id": f"outcome-{uuid.uuid4().hex[:12]}",
        "mission_contract_id": mission_id,
        "mission_contract_fingerprint": contract["contract_fingerprint"],
        "recorded_at": ts,
        "status": status,
        "observation": observation,
        "attribution": "unresolved",
        "evidence_source_type": "implementer_claim",
        "may_rewrite_prior_history": False,
    }

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
                hypothesis["status"] = (
                    "validated"
                    if status == "success"
                    else "invalidated"
                    if status == "failure"
                    else hypothesis.get("status", "open")
                )

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
        }
    )
    mission_store.save_contract(updated)
    return outcome


def _plan_context(palamedes_module: Any) -> str:
    palamedes_module.ensure_state()
    plan = palamedes_module.load_plan()
    fields = {
        "goal": plan.get("goal", ""),
        "success_metric": plan.get("success_metric", ""),
        "selected_option": plan.get("selected_option", ""),
        "constraints": plan.get("constraints", []),
        "open_hypotheses": [
            item
            for item in plan.get("hypothesis_log", [])
            if item.get("status") == "open"
        ][-5:],
        "recent_view_transitions": plan.get("view_transitions", [])[-3:],
        "open_questions": plan.get("open_questions", [])[-5:],
        "development_probes": plan.get("development_probes", [])[-5:],
    }
    return json.dumps(fields, ensure_ascii=False, sort_keys=True)


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
                "  /observe             collect project, Git, state, TODO, and ref signals",
                "  /preview             inspect the latest mission draft",
                "  /approve             persist the draft and create planner handoff",
                "  /reject <reason>     reject the latest draft without rewriting it",
                "  /handoff             show the latest planner handoff",
                "  /outcome <status> <observation>",
                "                       record success|failure|mixed|unknown",
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
        if text == "/observe":
            from palamedes_observe import collect_observation, render_observation

            ref_value = os.environ.get(
                "PALAMEDES_REF_ROOT", "/Users/ze/work/ref"
            ).strip()
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
        if text.startswith("/cycle"):
            context = text[len("/cycle") :].strip()
            if not context:
                output.write("/cycle requires context.\n")
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
            output.write(
                "Running independent roles: interpreter → inventor → adversary → selector\n"
            )
            try:
                from palamedes_observe import (
                    collect_observation,
                    observation_context,
                )

                ref_value = os.environ.get(
                    "PALAMEDES_REF_ROOT", "/Users/ze/work/ref"
                ).strip()
                latest_observation = collect_observation(
                    workspace,
                    ref_root=Path(ref_value).expanduser() if ref_value else None,
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
                team_context = current_team_context()
                if team_context is not None:
                    grounded_context += (
                        "\n\nShared team cognition:\n"
                        + json.dumps(team_context, ensure_ascii=False)
                    )
                result = run_cognition_cycle(
                    provider=provider,
                    palamedes_module=palamedes_module,
                    context=grounded_context,
                    cycle_store=cognition_store,
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
                },
            )
            contract = result["contract"]
            if contract is None:
                output.write(
                    f"Cycle {cycle['cognition_cycle_id']} ended with "
                    f"{cycle['decision']}; no mission draft was issued.\n"
                )
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
        if text.startswith("/outcome"):
            raw = text[len("/outcome") :].strip()
            parts = raw.split(maxsplit=1)
            if len(parts) != 2:
                output.write(
                    "/outcome requires: success|failure|mixed|unknown <observation>\n"
                )
                continue
            status, observation = parts
            records = store.load(active_session)
            mission_id = latest_mission_id(records, {"approved", "outcome_recorded"})
            if not mission_id:
                output.write("No approved mission can accept an outcome.\n")
                continue
            contract = mission_store.load_contract(mission_id)
            try:
                outcome = record_mission_outcome(
                    palamedes_module,
                    mission_store,
                    contract,
                    status,
                    observation,
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
                    "outcome_analysis_status": analysis_result["status"],
                },
            )
            output.write(
                f"Outcome recorded: {outcome['outcome_id']} ({status})\n"
            )
            if analysis_result["status"] == "completed":
                disposition = analysis_result["analysis"]["output"][
                    "mission_disposition"
                ]
                output.write(
                    f"Outcome analyst completed: disposition={disposition}\n"
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
