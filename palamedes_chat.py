#!/usr/bin/env python3
"""Interactive, local-first Palamedes terminal chat."""

from __future__ import annotations

import json
import hashlib
import os
import re
import sys
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
    raise ValueError("provider must be openrouter or openai")


def provider_health(name: str) -> Dict[str, Any]:
    env_name = "OPENROUTER_API_KEY" if name == "openrouter" else "OPENAI_API_KEY"
    key_set = bool(os.environ.get(env_name, "").strip())
    return {
        "provider": name,
        "status": "ok" if key_set else "unavailable",
        "api_key_env": env_name,
        "api_key_set": key_set,
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


def _fingerprint(payload: Dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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
  "uncertainty": 50
}}

Do not invent external evidence. Use source "user" or "plan" for claims from the
provided context. If evidence is weak, preserve that weakness with low
confidence and a falsifying probe.

User context:
{context}"""


def render_mission(contract: Dict[str, Any]) -> str:
    lines = [
        f"Mission draft: {contract['mission_id']}",
        f"  mission: {contract['mission']}",
        f"  rationale: {contract['rationale']}",
        f"  success metric: {contract['success_metric']}",
        f"  uncertainty: {contract['uncertainty']}/100",
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


def system_prompt(palamedes_module: Any, workspace: Path) -> str:
    return f"""You are Palamedes, an autonomous pre-planner operating before planner -> task -> implementation.

Your job is to notice what matters, form competing interpretations, originate worthwhile candidate missions, attack your own assumptions, and recommend the smallest informative next move.

Do not claim that retrieval, debate, novelty, or confidence proves quality. Separate observation, inference, value judgment, and commitment. State uncertainty and falsifiers. Preserve useful disagreement. Prefer a blocked or deferred conclusion over unsupported authority.

You are plan-only in this terminal. You may propose mission contracts, evidence, probes, and plan changes, but you cannot claim that files, plans, or external systems were changed unless the user explicitly runs an available CLI command and observes its result.

Workspace: {workspace}
Current bounded Palamedes plan context:
{_plan_context(palamedes_module)}
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
) -> int:
    store = ChatSessionStore(palamedes_module.STATE_DIR / "chat")
    mission_store = MissionStore(palamedes_module.STATE_DIR / "missions")
    active_session = session_id
    workspace = Path(palamedes_module.ROOT)
    output.write("Palamedes Research Alpha\n")
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
                f"workspace={workspace} session={active_session}\n"
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
            result = approve_mission(
                palamedes_module, mission_store, contract, active_session
            )
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
            store.append(
                active_session,
                {
                    "ts": utc_now(),
                    "type": "mission_state",
                    "mission_id": mission_id,
                    "status": "outcome_recorded",
                    "outcome_id": outcome["outcome_id"],
                    "outcome_status": status,
                },
            )
            output.write(
                f"Outcome recorded: {outcome['outcome_id']} ({status})\n"
                "Attribution remains unresolved until separately evaluated.\n"
            )
            continue

        user_content = text
        command = text.split(maxsplit=1)[0]
        if command in CHAT_COMMANDS:
            remainder = text[len(command) :].strip()
            if not remainder:
                output.write(f"{command} requires a topic or context.\n")
                continue
            user_content = (
                mission_prompt(remainder)
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
            {"role": "system", "content": system_prompt(palamedes_module, workspace)},
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
            f"{args.provider} is unavailable: set {health['api_key_env']} before starting chat"
        )
    session_id = args.session or os.environ.get("PALAMEDES_CHAT_SESSION", "").strip()
    if not session_id:
        session_id = uuid.uuid4().hex[:12]
    workspace = Path(args.workspace).expanduser().resolve() if args.workspace else Path.cwd()
    if not workspace.is_dir():
        raise ValueError(f"workspace does not exist or is not a directory: {workspace}")
    palamedes_module.ROOT = workspace
    palamedes_module.STATE_DIR = workspace / ".palamedes"
    palamedes_module.PLAN_PATH = palamedes_module.STATE_DIR / "plan.json"
    palamedes_module.DECISIONS_PATH = palamedes_module.STATE_DIR / "decisions.jsonl"
    palamedes_module.RISKS_PATH = palamedes_module.STATE_DIR / "risks.jsonl"
    palamedes_module.EVENTS_PATH = palamedes_module.STATE_DIR / "events.jsonl"
    palamedes_module.REVISIONS_PATH = palamedes_module.STATE_DIR / "revisions.jsonl"
    ChatSessionStore(palamedes_module.STATE_DIR / "chat").path(session_id)
    if args.history_limit < 2 or args.history_limit > 200:
        raise ValueError("history-limit must be between 2 and 200")
    provider = provider_from_config(args.provider, args.model)
    run_chat(
        palamedes_module=palamedes_module,
        provider=provider,
        session_id=session_id,
        history_limit=args.history_limit,
    )
