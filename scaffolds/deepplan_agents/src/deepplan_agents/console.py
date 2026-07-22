#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

from deepplan_agents.adapters.deepplan_adapter import DeepPlanAdapter
from deepplan_agents.bootstrap import ClientConfig, build_client
from deepplan_agents.runtime.host_step import HostStep, action_contract
from deepplan_agents.reference_rag import build_reference_rag_context, reference_query, resolve_reference_corpus
from deepplan_agents.reference_collectors import collect_file, collect_url
from deepplan_agents.reference_eval import evaluate_reference_retrieval
from deepplan_agents.reference_embeddings import OpenAIReferenceEmbeddingProvider
from deepplan_agents.reference_store import ReferenceStore
from deepplan_agents.insight_persistence import persist_reference_insights
from deepplan_agents.skills.registry import build_runtime_session
from deepplan_agents.strategy_llm import openai_provider_from_env, openai_provider_health, run_strategy_llm, static_provider_from_json
from deepplan_agents.strategy_prompt import build_strategy_prompt_bundle
from deepplan_agents.strategy_routes import route_strategy_next_actions


DEFAULT_PAYLOADS: Dict[str, Dict[str, Any]] = {
    "evaluate_experience_strategy": {
        "idea": "AI planning checkpoint for builders before they ask agents to build.",
        "entry_mode": "new_project",
        "project_stage": "pre-build",
        "existing_artifacts": [],
        "pivot_signals": [],
        "target_user": "solo AI builders and early founders",
        "problem": "They build generic services quickly before validating problem, desire, differentiation, and repeat value.",
        "current_alternative": "They ask a coding agent to build immediately or use generic planning prompts.",
        "pain_frequency": "Every new product idea or major feature decision creates this risk.",
        "solution": "Evaluate problem-solution fit, emotional demand, experience loop, monetization trigger, and genericness before build.",
        "desire": "avoid wasted work and find a sharper money-making direction",
        "emotion": "anxiety, greed, control, status",
        "trigger": "before starting a build session",
        "action": "submit an idea and receive a continue, revise, or stop decision",
        "reward": "a sharper plan and clear reasons to continue, revise, or stop",
        "monetization": "paid planning intelligence for builders who want better odds before spending build time",
        "repeat_loop": "review each new idea, weekly planning cycle, and post-launch evidence cycle",
        "references": ["successful service loops", "failed AI wrappers", "user behavior data"],
        "behavior_signals": ["users ask AI agents for the same dashboards and AI wrappers", "successful services convert emotional demand into repeat behavior"],
        "differentiation": "pre-build product intelligence rather than another task or notes tool",
        "personal_profile": {
            "repeated_biases": ["solution-first planning"],
            "weak_axes": ["reference_insight"],
            "overused_solution_patterns": ["dashboard"]
        }
    },
    "generate_creative_directions": {
        "topic": "DeepPlan product intelligence for AI builders",
        "entry_mode": "mid_project",
        "project_stage": "prototype with a planning kernel and strategist scaffold",
        "existing_artifacts": ["current plan", "strategy prompt", "host action contract", "reference discovery loop"],
        "current_plan": "Shift from plan-state kernel to AI-first product intelligence that attacks weak ideas before build.",
        "constraints": ["DeepPlan remains plan-only", "strategy judgment must use AI", "host capabilities remain deterministic"],
        "pivot_signals": ["users need help during a project, not only before starting", "generic LLM-built services are too common"],
        "references": ["failed AI wrappers", "successful emotional service loops", "founder postmortems"],
        "behavior_signals": ["builders repeatedly ask agents for similar dashboards", "mid-project teams need rescue, pivot, and differentiation help"],
        "success_cases": ["services with strong emotional return loops"],
        "failure_cases": ["tools with features but no repeat behavior"],
        "papers": [],
        "reviews": [],
        "personal_profile": {
            "repeated_biases": ["starts from implementation before evidence"],
            "weak_axes": ["monetization_trigger", "reference_insight"],
            "overused_solution_patterns": ["dashboard", "assistant"]
        }
    },
    "analyze_outcome_learning": {
        "entry_mode": "mid_project",
        "project_stage": "prototype after first user trials",
        "existing_artifacts": ["current plan", "prototype", "usage notes", "user feedback"],
        "current_plan": "AI-first product intelligence for builders before or during a project.",
        "shipped_changes": ["AI-first strategist report schema", "creative direction action", "mid-project intake"],
        "usage_signals": ["users ask whether the idea is generic before building", "mid-project users bring artifacts and pivot pressure"],
        "revenue_signals": ["willingness to pay appears around avoiding wasted build time"],
        "retention_signals": ["repeat usage likely around each new idea, pivot, or weekly review"],
        "user_feedback": ["needs to work after a project already started", "must always use AI for judgment"],
        "failed_assumptions": ["pre-build-only positioning is too narrow"],
        "new_constraints": ["keep DeepPlan plan-only", "do not use rule-based strategy scoring"],
        "personal_profile": {
            "repeated_biases": ["implementation-first planning"],
            "weak_axes": ["outcome_learning"],
            "overused_solution_patterns": ["dashboard", "assistant"]
        }
    },
    "update_plan": {
        "goal": "Agent console planning pass",
        "success_metric": "Produce one reviewable planning cycle",
        "deadline": "2026-05-31",
    },
    "capture_evidence_cycle": {
        "claim": "Agent console can capture a planning signal and replan from it.",
        "source": "agent-console",
        "confidence": 70,
        "axis": "direction",
    },
    "run_reference_discovery": {
        "question": "Which references prove or disprove this product direction?",
        "context": "Strategy evaluation needs external behavior evidence before build.",
        "references": ["successful service loops", "failed AI wrappers"],
        "rejected": ["generic AI dashboard examples"],
        "apply": True,
    },
    "request_review": {
        "scope": "plan",
        "reason": "Agent console routed this planning cycle for human review.",
        "requested_by": "agent-console",
        "priority": "medium",
    },
    "resolve_review": {
        "request_id": "",
        "status": "resolved",
        "resolution": "Resolved from agent console.",
        "resolved_by": "agent-console",
    },
    "preview_restore_previous": {},
    "restore_previous": {},
}


def _json_dumps(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def _load_payload(args: argparse.Namespace) -> Dict[str, Any]:
    if args.payload_json and args.payload_file:
        raise ValueError("use either --payload-json or --payload-file, not both")
    if args.payload_json:
        payload = json.loads(args.payload_json)
    elif args.payload_file:
        payload = json.loads(Path(args.payload_file).read_text(encoding="utf-8"))
    else:
        payload = dict(DEFAULT_PAYLOADS.get(args.action, {}))
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    return payload


def _reference_store(args: argparse.Namespace) -> ReferenceStore:
    return ReferenceStore(Path(str(args.reference_db)))


def _attach_reference_store(payload: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    prepared = dict(payload)
    path = Path(str(args.reference_db))
    if not prepared.get("reference_corpus") and path.exists():
        prepared["reference_store_path"] = str(path)
    if str(getattr(args, "embedding_provider", "none")) == "openai":
        patterns = resolve_reference_corpus(prepared)
        if patterns:
            provider = OpenAIReferenceEmbeddingProvider(model=str(args.embedding_model))
            prepared["reference_semantic_scores"] = provider.semantic_scores(reference_query(prepared), patterns)
    return prepared


def _client_config(args: argparse.Namespace) -> ClientConfig:
    mode = "http" if args.base_url else "in-process"
    return ClientConfig(
        mode=mode,
        base_url=str(args.base_url or ""),
        history_limit=int(args.history_limit),
        require_healthy_writes=not bool(args.allow_unhealthy_writes),
    )


def build_adapter(args: argparse.Namespace) -> DeepPlanAdapter:
    config = _client_config(args)
    return DeepPlanAdapter(
        build_client(config),
        history_limit=config.history_limit,
        require_healthy_writes=config.require_healthy_writes,
    )


def _strategy_provider_from_args(args: argparse.Namespace) -> Any:
    provider_name = str(getattr(args, "provider", "") or "").strip()
    if not provider_name:
        return None
    if provider_name == "openai":
        return openai_provider_from_env(model=str(getattr(args, "model", "") or "").strip())
    if provider_name == "static":
        raw_json = str(getattr(args, "static_report_json", "") or "")
        raw_file = str(getattr(args, "static_report_file", "") or "")
        if raw_json and raw_file:
            raise ValueError("use either --static-report-json or --static-report-file, not both")
        if not raw_json and not raw_file:
            raise ValueError("static provider requires --static-report-json or --static-report-file")
        return static_provider_from_json(raw_json or Path(raw_file).read_text(encoding="utf-8"))
    raise ValueError(f"unknown strategy provider: {provider_name}")


def cmd_agents(_: argparse.Namespace) -> int:
    roles = ["planner", "strategist", "researcher", "reviewer"]
    payload = {"ok": True, "roles": []}
    for role in roles:
        contract = action_contract(role)
        session = build_runtime_session(role)
        payload["roles"].append(
            {
                "role": role,
                "profile": contract["profile"],
                "capabilities": contract["capabilities"],
                "allowed_actions": contract["allowed_actions"],
                "skills": session["actual_skills"],
            }
        )
    print(_json_dumps(payload))
    return 0


def cmd_snapshot(args: argparse.Namespace) -> int:
    adapter = build_adapter(args)
    snapshot = adapter.snapshot()
    print(_json_dumps({"ok": True, "type": "snapshot", "snapshot": snapshot}))
    return 0


def cmd_provider_health(_: argparse.Namespace) -> int:
    health = openai_provider_health()
    print(_json_dumps({"ok": health["status"] == "ok", "type": "provider_health", "health": health}))
    return 0 if health["status"] == "ok" else 1


def cmd_run(args: argparse.Namespace) -> int:
    payload = _load_payload(args)
    if args.action in {"evaluate_experience_strategy", "generate_creative_directions"}:
        payload = _attach_reference_store(payload, args)
    options: Dict[str, Any] = {}
    if args.session_id:
        options["session_id"] = args.session_id
    if args.step_id:
        options["step_id"] = args.step_id

    adapter = build_adapter(args)
    event = HostStep(adapter, role=args.role, strategy_provider=_strategy_provider_from_args(args)).run_event(
        {
            "action": args.action,
            "payload": payload,
            "options": options,
        }
    )
    print(_json_dumps(event))
    return 0 if event.get("ok") else 1


def cmd_prompt(args: argparse.Namespace) -> int:
    payload = _attach_reference_store(_load_payload(args), args)
    adapter = build_adapter(args)
    snapshot = adapter.snapshot()
    bundle = build_strategy_prompt_bundle(payload, snapshot, action=args.action)
    print(_json_dumps({"ok": True, "type": "strategy_prompt", "bundle": bundle}))
    return 0


def cmd_retrieve(args: argparse.Namespace) -> int:
    payload = _attach_reference_store(_load_payload(args), args)
    retrieval = build_reference_rag_context(payload)
    if not retrieval:
        raise ValueError("retrieve command requires a non-empty reference_corpus")
    print(_json_dumps({"ok": True, "type": "reference_retrieval", "retrieval": retrieval}))
    return 0 if retrieval["quality_gate"]["status"] == "sufficient" else 1


def cmd_llm(args: argparse.Namespace) -> int:
    payload = _attach_reference_store(_load_payload(args), args)
    provider = _strategy_provider_from_args(args)
    if provider is None:
        raise ValueError("llm command requires --provider openai or --provider static")
    adapter = build_adapter(args)
    snapshot = adapter.snapshot()
    result = run_strategy_llm(provider, payload=payload, snapshot=snapshot, action=args.action)
    print(_json_dumps(result))
    return 0


def cmd_reference_ingest(args: argparse.Namespace) -> int:
    items = []
    if args.input_file:
        items.extend(collect_file(Path(args.input_file), source_type=args.source_type))
    if args.url:
        items.append(collect_url(args.url, source_type=args.source_type))
    if not items:
        raise ValueError("reference-ingest requires --input-file or --url")
    result = _reference_store(args).ingest(items)
    print(_json_dumps({"ok": True, "type": "reference_ingest", "store": str(args.reference_db), **result}))
    return 0


def cmd_reference_list(args: argparse.Namespace) -> int:
    store = _reference_store(args)
    patterns = store.list(source_type=args.source_type, limit=args.limit)
    print(_json_dumps({"ok": True, "type": "reference_list", "store": str(args.reference_db), "count": len(patterns), "patterns": patterns}))
    return 0


def cmd_reference_health(args: argparse.Namespace) -> int:
    health = _reference_store(args).health()
    print(_json_dumps({"ok": health["status"] == "ok", "type": "reference_health", "health": health}))
    return 0 if health["status"] == "ok" else 1


def cmd_reference_eval(args: argparse.Namespace) -> int:
    dataset = json.loads(Path(args.dataset_file).read_text(encoding="utf-8"))
    if not isinstance(dataset, dict):
        raise ValueError("reference evaluation dataset must be an object")
    corpus = dataset.get("corpus")
    if not isinstance(corpus, list):
        corpus = _reference_store(args).list()
    result = evaluate_reference_retrieval(dataset, corpus)
    print(_json_dumps({"type": "reference_evaluation", **result}))
    return 0 if result["ok"] else 1


def cmd_insight_apply(args: argparse.Namespace) -> int:
    report = json.loads(Path(args.report_file).read_text(encoding="utf-8"))
    if not isinstance(report, dict):
        raise ValueError("strategy report must be an object")
    result = persist_reference_insights(build_adapter(args), report)
    print(_json_dumps(result))
    return 0


def _load_report(args: argparse.Namespace) -> Dict[str, Any]:
    if args.report_json and args.report_file:
        raise ValueError("use either --report-json or --report-file, not both")
    if args.report_json:
        report = json.loads(args.report_json)
    elif args.report_file:
        report = json.loads(Path(args.report_file).read_text(encoding="utf-8"))
    else:
        raise ValueError("route command requires --report-json or --report-file")
    if not isinstance(report, dict):
        raise ValueError("report must be a JSON object")
    return report


def cmd_route(args: argparse.Namespace) -> int:
    report = _load_report(args)
    result = route_strategy_next_actions(report)
    print(_json_dumps(result))
    return 0 if result.get("ok") else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run DeepPlan agents against a local planning workspace.")
    parser.add_argument("--base-url", default="", help="Optional DeepPlan HTTP base URL, e.g. http://127.0.0.1:8787")
    parser.add_argument("--history-limit", type=int, default=5)
    parser.add_argument("--allow-unhealthy-writes", action="store_true")
    parser.add_argument("--reference-db", default=".deeplan/references.sqlite3", help="Persistent Insight RAG reference store.")
    parser.add_argument("--embedding-provider", choices=["none", "openai"], default="none", help="Optional semantic scorer for hybrid retrieval.")
    parser.add_argument("--embedding-model", default="text-embedding-3-small")
    sub = parser.add_subparsers(dest="command", required=True)

    agents = sub.add_parser("agents", help="List available agent roles, profiles, actions, and skills.")
    agents.set_defaults(func=cmd_agents)

    snapshot = sub.add_parser("snapshot", help="Read the current DeepPlan cycle snapshot.")
    snapshot.set_defaults(func=cmd_snapshot)

    provider_health = sub.add_parser("provider-health", help="Check OpenAI SDK and API-key readiness for strategy and embedding providers.")
    provider_health.set_defaults(func=cmd_provider_health)

    run = sub.add_parser("run", help="Run one role-aware agent action.")
    run.add_argument("--role", choices=["planner", "strategist", "researcher", "reviewer"], required=True)
    run.add_argument(
        "--action",
        choices=sorted(DEFAULT_PAYLOADS.keys()),
        required=True,
    )
    run.add_argument("--payload-json", default="")
    run.add_argument("--payload-file", default="")
    run.add_argument("--session-id", default="")
    run.add_argument("--step-id", default="")
    run.add_argument("--provider", choices=["openai", "static"], default="")
    run.add_argument("--model", default="")
    run.add_argument("--static-report-json", default="")
    run.add_argument("--static-report-file", default="")
    run.set_defaults(func=cmd_run)

    prompt = sub.add_parser("prompt", help="Build the strategist LLM prompt bundle without calling a provider.")
    prompt.add_argument(
        "--action",
        choices=["evaluate_experience_strategy", "generate_creative_directions", "analyze_outcome_learning"],
        default="evaluate_experience_strategy",
    )
    prompt.add_argument("--payload-json", default="")
    prompt.add_argument("--payload-file", default="")
    prompt.set_defaults(func=cmd_prompt)

    retrieve = sub.add_parser("retrieve", help="Retrieve diverse reference patterns and evaluate evidence sufficiency without calling a model.")
    retrieve.add_argument("--payload-json", default="")
    retrieve.add_argument("--payload-file", default="")
    retrieve.set_defaults(func=cmd_retrieve, action="evaluate_experience_strategy")

    ingest = sub.add_parser("reference-ingest", help="Collect and persist reference patterns from JSON, JSONL, text, or an HTTP(S) URL.")
    ingest.add_argument("--input-file", default="")
    ingest.add_argument("--url", default="")
    ingest.add_argument("--source-type", choices=["success_case", "failure_case", "counter_view", "paper", "review", "behavior_evidence", "other"], default="other")
    ingest.set_defaults(func=cmd_reference_ingest)

    reference_list = sub.add_parser("reference-list", help="List persisted reference patterns.")
    reference_list.add_argument("--source-type", choices=["success_case", "failure_case", "counter_view", "paper", "review", "behavior_evidence", "other"], default="")
    reference_list.add_argument("--limit", type=int, default=100)
    reference_list.set_defaults(func=cmd_reference_list)

    reference_health = sub.add_parser("reference-health", help="Check the persistent reference store schema and SQLite integrity.")
    reference_health.set_defaults(func=cmd_reference_health)

    reference_eval = sub.add_parser("reference-eval", help="Evaluate retrieval recall, ranking, viewpoint coverage, and sufficiency gating.")
    reference_eval.add_argument("--dataset-file", required=True)
    reference_eval.set_defaults(func=cmd_reference_eval)

    insight_apply = sub.add_parser("insight-apply", help="Persist grounded reference insights into DeepPlan evidence, insights, and revision history.")
    insight_apply.add_argument("--report-file", required=True)
    insight_apply.set_defaults(func=cmd_insight_apply)

    llm = sub.add_parser("llm", help="Run the strategist LLM boundary with an AI provider.")
    llm.add_argument(
        "--action",
        choices=["evaluate_experience_strategy", "generate_creative_directions", "analyze_outcome_learning"],
        default="evaluate_experience_strategy",
    )
    llm.add_argument("--payload-json", default="")
    llm.add_argument("--payload-file", default="")
    llm.add_argument("--provider", choices=["openai", "static"], default="openai")
    llm.add_argument("--model", default="")
    llm.add_argument("--static-report-json", default="")
    llm.add_argument("--static-report-file", default="")
    llm.set_defaults(func=cmd_llm)

    route = sub.add_parser("route", help="Validate and route strategist next_actions to target roles.")
    route.add_argument("--report-json", default="")
    route.add_argument("--report-file", default="")
    route.set_defaults(func=cmd_route)

    return parser


def main(argv: Any = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:
        print(_json_dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
