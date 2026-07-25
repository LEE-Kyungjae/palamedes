#!/usr/bin/env python3
"""Interactive, local-first Palamedes terminal chat."""

from __future__ import annotations

import json
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
    "/mission": "Produce the strongest current mission contract: mission, rationale, evidence, falsifiers, non-goals, uncertainty, and next probe.",
}


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

        user_content = text
        command = text.split(maxsplit=1)[0]
        if command in CHAT_COMMANDS:
            remainder = text[len(command) :].strip()
            if not remainder:
                output.write(f"{command} requires a topic or context.\n")
                continue
            user_content = f"{CHAT_COMMANDS[command]}\n\nUser context:\n{remainder}"
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
        output.write("\n")
        try:
            for chunk in provider.stream(messages):
                chunks.append(chunk)
                output.write(chunk)
                output.flush()
        except (RuntimeError, ValueError) as exc:
            output.write(f"\n[provider error] {exc}\n\n")
            continue
        reply = "".join(chunks).strip()
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
