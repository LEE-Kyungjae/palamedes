#!/usr/bin/env python3
import json
import os
import importlib.util
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

from palamedes_agents.strategy_prompt import build_strategy_prompt_bundle
from palamedes_agents.reference_rag import validate_reference_grounding
from palamedes_agents.workflows.strategy_loop import validate_strategy_report_shape


class StrategyLLMProvider(Protocol):
    def complete_json(self, *, messages: List[Dict[str, str]], schema: Dict[str, Any]) -> Dict[str, Any]:
        ...


@dataclass
class StaticStrategyProvider:
    report: Dict[str, Any]

    def complete_json(self, *, messages: List[Dict[str, str]], schema: Dict[str, Any]) -> Dict[str, Any]:
        return dict(self.report)


@dataclass
class OpenAIResponsesStrategyProvider:
    model: str = "gpt-5.5"
    client: Optional[Any] = None

    def _client(self) -> Any:
        if self.client is not None:
            return self.client
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("OpenAI provider requires the openai Python package") from exc
        return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def complete_json(self, *, messages: List[Dict[str, str]], schema: Dict[str, Any]) -> Dict[str, Any]:
        response = self._client().responses.create(
            model=self.model,
            input=messages,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "palamedes_strategy_report",
                    "schema": _schema_for_openai(schema),
                    "strict": True,
                }
            },
        )
        return _json_from_response(response)


@dataclass
class OpenRouterChatStrategyProvider:
    model: str = "openai/gpt-5.1"
    client: Optional[Any] = None
    base_url: str = "https://openrouter.ai/api/v1"

    def complete_json(self, *, messages: List[Dict[str, str]], schema: Dict[str, Any]) -> Dict[str, Any]:
        request_payload = {
            "model": self.model,
            "messages": messages,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "palamedes_strategy_report",
                    "strict": True,
                    "schema": _schema_for_openai(schema),
                },
            },
        }
        if self.client is not None:
            response = self.client.chat.completions.create(**request_payload)
            return _json_from_chat_completion(response)

        api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OpenRouter provider requires OPENROUTER_API_KEY")
        request = urllib.request.Request(
            f"{self.base_url.rstrip('/')}/chat/completions",
            data=json.dumps(request_payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.environ.get("PALAMEDES_OPENROUTER_SITE_URL", "https://github.com/LEE-Kyungjae/Palamedes"),
                "X-Title": os.environ.get("PALAMEDES_OPENROUTER_APP_NAME", "Palamedes"),
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenRouter request failed ({exc.code}): {detail}") from exc
        return _json_from_chat_completion(payload)


def _schema_for_openai(schema: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(schema)
    payload.pop("$schema", None)
    return payload


def _json_from_response(response: Any) -> Dict[str, Any]:
    parsed = getattr(response, "output_parsed", None)
    if isinstance(parsed, dict):
        return parsed
    output_text = getattr(response, "output_text", "")
    if isinstance(output_text, str) and output_text.strip():
        payload = json.loads(output_text)
        if isinstance(payload, dict):
            return payload
    output = getattr(response, "output", [])
    if isinstance(output, list):
        for item in output:
            content = getattr(item, "content", None)
            if content is None and isinstance(item, dict):
                content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                text = getattr(part, "text", None)
                if text is None and isinstance(part, dict):
                    text = part.get("text")
                if isinstance(text, str) and text.strip():
                    payload = json.loads(text)
                    if isinstance(payload, dict):
                        return payload
    raise ValueError("OpenAI response did not contain a JSON object")


def _json_from_chat_completion(response: Any) -> Dict[str, Any]:
    choices = response.get("choices", []) if isinstance(response, dict) else getattr(response, "choices", [])
    if not choices:
        raise ValueError("OpenRouter response did not contain choices")
    first = choices[0]
    message = first.get("message", {}) if isinstance(first, dict) else getattr(first, "message", {})
    content = message.get("content", "") if isinstance(message, dict) else getattr(message, "content", "")
    if isinstance(content, list):
        content = "".join(
            str(part.get("text", "")) if isinstance(part, dict) else str(getattr(part, "text", ""))
            for part in content
        )
    if not isinstance(content, str) or not content.strip():
        raise ValueError("OpenRouter response did not contain message content")
    payload = json.loads(content)
    if not isinstance(payload, dict):
        raise ValueError("OpenRouter response content was not a JSON object")
    return payload


def run_strategy_llm(
    provider: StrategyLLMProvider,
    *,
    payload: Dict[str, Any],
    snapshot: Dict[str, Any],
    action: str = "evaluate_experience_strategy",
) -> Dict[str, Any]:
    bundle = build_strategy_prompt_bundle(payload, snapshot, action=action)
    report = provider.complete_json(messages=bundle["messages"], schema=bundle["schema"])
    if not isinstance(report, dict):
        raise ValueError("strategy provider must return a JSON object")
    errors = validate_strategy_report_shape(report)
    errors.extend(validate_reference_grounding(report, bundle["reference_retrieval"]))
    if errors:
        raise ValueError("invalid strategy report: " + "; ".join(errors))
    return {
        "ok": True,
        "type": "strategy_llm_report",
        "provider": provider.__class__.__name__,
        "report": report,
        "prompt": {
            "message_count": len(bundle["messages"]),
            "schema_title": str(bundle["schema"].get("title", "")).strip(),
        },
    }


def static_provider_from_json(raw_json: str) -> StaticStrategyProvider:
    payload = json.loads(raw_json)
    if not isinstance(payload, dict):
        raise ValueError("static strategy report must be a JSON object")
    return StaticStrategyProvider(payload)


def openai_provider_from_env(*, model: str = "") -> OpenAIResponsesStrategyProvider:
    return OpenAIResponsesStrategyProvider(model=model or os.environ.get("PALAMEDES_OPENAI_MODEL", "gpt-5.5"))


def openrouter_provider_from_env(*, model: str = "") -> OpenRouterChatStrategyProvider:
    return OpenRouterChatStrategyProvider(
        model=model or os.environ.get("PALAMEDES_OPENROUTER_MODEL", "openai/gpt-5.1")
    )


def openai_provider_health() -> Dict[str, Any]:
    sdk_available = importlib.util.find_spec("openai") is not None
    api_key_set = bool(os.environ.get("OPENAI_API_KEY", "").strip())
    issues = []
    if not sdk_available:
        issues.append("openai_sdk_missing")
    if not api_key_set:
        issues.append("OPENAI_API_KEY_missing")
    return {
        "status": "ok" if not issues else "unavailable",
        "issues": issues,
        "sdk_available": sdk_available,
        "api_key_set": api_key_set,
        "strategy_model": os.environ.get("PALAMEDES_OPENAI_MODEL", "gpt-5.5"),
        "embedding_model": os.environ.get("PALAMEDES_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
    }


def openrouter_provider_health() -> Dict[str, Any]:
    api_key_set = bool(os.environ.get("OPENROUTER_API_KEY", "").strip())
    issues = [] if api_key_set else ["OPENROUTER_API_KEY_missing"]
    return {
        "status": "ok" if not issues else "unavailable",
        "issues": issues,
        "api_key_set": api_key_set,
        "strategy_model": os.environ.get("PALAMEDES_OPENROUTER_MODEL", "openai/gpt-5.1"),
        "base_url": "https://openrouter.ai/api/v1",
    }
