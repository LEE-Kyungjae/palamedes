#!/usr/bin/env python3
import json
import os
import importlib.util
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

from deepplan_agents.strategy_prompt import build_strategy_prompt_bundle
from deepplan_agents.reference_rag import validate_reference_grounding
from deepplan_agents.workflows.strategy_loop import validate_strategy_report_shape


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
                    "name": "deepplan_strategy_report",
                    "schema": _schema_for_openai(schema),
                    "strict": True,
                }
            },
        )
        return _json_from_response(response)


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
    return OpenAIResponsesStrategyProvider(model=model or os.environ.get("DEEPPLAN_OPENAI_MODEL", "gpt-5.5"))


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
        "strategy_model": os.environ.get("DEEPPLAN_OPENAI_MODEL", "gpt-5.5"),
        "embedding_model": os.environ.get("DEEPPLAN_OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
    }
