#!/usr/bin/env python3
"""Event-driven Palamedes workspace watcher with bounded cognition."""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from palamedes_observe import (
    bind_workspace,
    collect_observation,
    fingerprint,
    observation_context,
    utc_now,
)


def select_wake_policy(
    snapshot: Dict[str, Any],
    *,
    wake_initial: bool = False,
) -> Dict[str, Any]:
    reasons = set(snapshot.get("change", {}).get("reasons", []))
    if not snapshot.get("change", {}).get("changed"):
        return _policy("wait", [], 0, "no decision-relevant change")
    if reasons == {"initial_observation"} and not wake_initial:
        return _policy(
            "wait",
            [],
            0,
            "initial observation establishes a baseline without spending cognition",
        )
    if "mission_outcome_appended" in reasons:
        return _policy(
            "outcome_review",
            ["outcome_analyst"],
            1,
            "a new mission outcome requires post-outcome belief revision",
        )
    if "test_failed" in reasons:
        return _policy(
            "diagnose_failure",
            ["interpreter", "adversary"],
            2,
            "a failed test needs interpretation and adversarial pressure",
        )
    significant = reasons - {"initial_observation", "git_status_changed"}
    if len(significant) >= 3:
        return _policy(
            "full_cycle",
            ["interpreter", "inventor", "adversary", "selector"],
            4,
            "multiple independent signal classes changed",
        )
    if "reference_repository_set_or_head_changed" in reasons:
        return _policy(
            "explore_reference_change",
            ["interpreter", "inventor"],
            2,
            "new reference material may open a different mission frame",
        )
    if "document_set_or_content_changed" in reasons:
        return _policy(
            "reinterpret_document_change",
            ["interpreter"],
            1,
            "project meaning changed in a primary document",
        )
    if "palamedes_plan_changed" in reasons:
        return _policy(
            "challenge_plan_change",
            ["adversary", "selector"],
            2,
            "a commitment changed and should be challenged before further execution",
        )
    if reasons.intersection({"git_head_changed", "git_status_changed"}):
        return _policy(
            "inspect_code_change",
            ["interpreter", "adversary"],
            2,
            "implementation changed and may contradict the current mission",
        )
    return _policy("wait", [], 0, "no configured cognitive operation fits the change")


def _policy(operation: str, roles: List[str], calls: int, rationale: str) -> Dict[str, Any]:
    return {
        "wake_policy_version": "palamedes-wake-policy/1",
        "operation": operation,
        "roles": roles,
        "maximum_model_calls": calls,
        "rationale": rationale,
        "delivery_authority_granted": False,
    }


def wake_key(snapshot: Dict[str, Any], policy: Dict[str, Any]) -> str:
    signals = snapshot.get("signals", {})
    stable = {
        "operation": policy["operation"],
        "reasons": sorted(snapshot.get("change", {}).get("reasons", [])),
        "git": {
            "head": signals.get("git", {}).get("head"),
            "status": signals.get("git", {}).get("status"),
        },
        "documents": [
            (item.get("path"), item.get("content_sha256"))
            for item in signals.get("documents", {}).get("documents", [])
        ],
        "plan": signals.get("palamedes_state", {}).get("plan", {}).get(
            "content_sha256"
        ),
        "outcomes": signals.get("palamedes_state", {}).get("outcomes", {}).get(
            "content_sha256"
        ),
        "refs": [
            (item.get("name"), item.get("head"))
            for item in signals.get("reference_root", {}).get("repositories", [])
        ],
        "test": {
            "command": signals.get("test", {}).get("command"),
            "returncode": signals.get("test", {}).get("returncode"),
        },
    }
    return fingerprint(stable)


class WatchStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.state_path = root / "state.json"
        self.events_path = root / "events.jsonl"
        self.wakes_root = root / "wakes"

    def load_state(self) -> Dict[str, Any]:
        if not self.state_path.is_file():
            return {
                "watch_state_version": "palamedes-watch-state/1",
                "total_model_calls": 0,
                "iteration_count": 0,
                "last_wake_key": "",
            }
        try:
            payload = json.loads(self.state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {
                "watch_state_version": "palamedes-watch-state/1",
                "total_model_calls": 0,
                "iteration_count": 0,
                "last_wake_key": "",
                "recovered_from_invalid_state": True,
            }
        return payload if isinstance(payload, dict) else {}

    def save_state(self, state: Dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.state_path)

    def append_event(self, event: Dict[str, Any]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")

    def save_wake(self, wake: Dict[str, Any]) -> Path:
        self.wakes_root.mkdir(parents=True, exist_ok=True)
        path = self.wakes_root / f"{wake['wake_id']}.json"
        path.write_text(
            json.dumps(wake, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return path


class WatchLock:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.acquired = False

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                existing_pid = int(self.path.read_text(encoding="utf-8").strip())
            except (OSError, ValueError):
                existing_pid = 0
            if existing_pid and _pid_alive(existing_pid):
                raise ValueError(f"watch already running with PID {existing_pid}")
            self.path.unlink(missing_ok=True)
        descriptor = os.open(
            str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600
        )
        os.write(descriptor, str(os.getpid()).encode("ascii"))
        os.close(descriptor)
        self.acquired = True
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.acquired:
            self.path.unlink(missing_ok=True)


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class CountingProvider:
    """Count attempted provider streams, including calls that fail mid-wake."""

    def __init__(self, provider: Any) -> None:
        self.provider = provider
        self.provider_name = getattr(provider, "provider_name", "unknown")
        self.model = getattr(provider, "model", "unknown")
        self.call_count = 0

    def stream(self, messages: List[Dict[str, str]]):
        self.call_count += 1
        yield from self.provider.stream(messages)


def _validate_partial_output(role: str, output: Dict[str, Any]) -> None:
    if not output:
        raise ValueError(f"{role} returned an empty object")
    required = {
        "interpreter": "observations",
        "inventor": "candidate_missions",
        "adversary": "falsifiers",
        "selector": "recommendation",
        "outcome_analyst": "belief_updates",
    }
    field = required[role]
    value = output.get(field)
    if isinstance(value, str):
        valid = bool(value.strip())
    else:
        valid = isinstance(value, list) and bool(value)
    if not valid:
        raise ValueError(f"{role} output requires non-empty {field}")


def run_partial_operation(
    *,
    provider: Any,
    policy: Dict[str, Any],
    snapshot: Dict[str, Any],
) -> Dict[str, Any]:
    from palamedes_chat import _provider_json, _role_artifact

    artifacts = []
    inherited: List[Dict[str, Any]] = []
    schemas = {
        "interpreter": '{"observations":["..."],"interpretations":["..."],"missing_evidence":["..."]}',
        "inventor": '{"candidate_missions":["..."],"mechanism_transfers":["..."],"next_probes":["..."]}',
        "adversary": '{"falsifiers":["..."],"hidden_harms":["..."],"shared_assumptions":["..."]}',
        "selector": '{"recommendation":"continue|reopen|defer|stop","rationale":"...","reversal_triggers":["..."]}',
        "outcome_analyst": '{"belief_updates":["..."],"attribution_hypotheses":["..."],"next_probe":"..."}',
    }
    for index, role in enumerate(policy["roles"], start=1):
        prompt = f"""ROLE: {role}
Perform only this bounded wake role. Do not issue tasks, change files, or claim
that an unobserved outcome occurred. Return exactly one JSON object shaped as:
{schemas[role]}

Wake operation: {policy['operation']}
Wake rationale: {policy['rationale']}
Workspace observation:
{json.dumps(observation_context(snapshot), ensure_ascii=False)}
Prior role artifacts in this wake:
{json.dumps(inherited, ensure_ascii=False)}"""
        output = _provider_json(
            provider,
            system=(
                "You are a bounded Palamedes wake role. Return one JSON object. "
                "Your authority ends at analysis."
            ),
            prompt=prompt,
        )
        _validate_partial_output(role, output)
        artifact = _role_artifact(
            role=role,
            call_index=index,
            prompt=prompt,
            output=output,
            provider=provider,
        )
        artifacts.append(artifact)
        inherited.append({"role": role, "output": output})
    return {
        "status": "completed",
        "artifacts": artifacts,
        "model_call_count": len(artifacts),
        "mission_draft_issued": False,
    }


def execute_wake(
    *,
    policy: Dict[str, Any],
    snapshot: Dict[str, Any],
    provider: Any,
    palamedes_module: Any,
) -> Dict[str, Any]:
    if policy["operation"] == "wait":
        return {
            "status": "wait",
            "artifacts": [],
            "model_call_count": 0,
            "mission_draft_issued": False,
        }
    if policy["operation"] == "full_cycle":
        from palamedes_chat import (
            CognitionCycleStore,
            MissionStore,
            run_cognition_cycle,
        )

        result = run_cognition_cycle(
            provider=provider,
            palamedes_module=palamedes_module,
            context=(
                "Autonomous wake from bounded workspace changes:\n"
                + json.dumps(observation_context(snapshot), ensure_ascii=False)
            ),
            cycle_store=CognitionCycleStore(
                palamedes_module.STATE_DIR / "missions" / "cognition"
            ),
        )
        contract = result["contract"]
        if contract:
            MissionStore(palamedes_module.STATE_DIR / "missions").save_contract(
                contract
            )
        return {
            "status": result["cycle"]["status"],
            "cognition_cycle_id": result["cycle"]["cognition_cycle_id"],
            "model_call_count": result["cycle"]["live_model_call_count"],
            "mission_draft_issued": contract is not None,
            "mission_id": contract["mission_id"] if contract else "",
        }
    return run_partial_operation(
        provider=provider, policy=policy, snapshot=snapshot
    )


def watch_once(
    *,
    workspace: Path,
    store: WatchStore,
    palamedes_module: Any,
    ref_root: Optional[Path],
    test_command: str,
    test_timeout: int,
    provider: Optional[Any],
    auto_cognition: bool,
    wake_initial: bool,
    max_calls_per_wake: int,
    max_calls_total: int,
) -> Dict[str, Any]:
    snapshot = collect_observation(
        workspace,
        ref_root=ref_root,
        test_command=test_command,
        test_timeout=test_timeout,
    )
    policy = select_wake_policy(snapshot, wake_initial=wake_initial)
    key = wake_key(snapshot, policy)
    state = store.load_state()
    duplicate = bool(key and key == state.get("last_wake_key"))
    if duplicate and policy["operation"] != "wait":
        policy = _policy(
            "wait",
            [],
            0,
            "the same signal state already received a wake decision",
        )
    calls_remaining = max(0, max_calls_total - int(state.get("total_model_calls", 0)))
    budget_blocked = (
        policy["maximum_model_calls"] > max_calls_per_wake
        or policy["maximum_model_calls"] > calls_remaining
    )
    wake = {
        "watch_wake_version": "palamedes-watch-wake/1",
        "wake_id": f"wake-{uuid.uuid4().hex[:12]}",
        "created_at": utc_now(),
        "observation_id": snapshot["observation_id"],
        "snapshot_fingerprint": snapshot["snapshot_fingerprint"],
        "wake_key": key,
        "policy": policy,
        "duplicate_signal_suppressed": duplicate,
        "auto_cognition_enabled": auto_cognition,
        "budget": {
            "max_calls_per_wake": max_calls_per_wake,
            "max_calls_total": max_calls_total,
            "calls_used_before": int(state.get("total_model_calls", 0)),
            "calls_remaining_before": calls_remaining,
            "blocked": budget_blocked,
        },
        "execution": {
            "status": "not_requested",
            "model_call_count": 0,
            "mission_draft_issued": False,
        },
    }
    if policy["operation"] == "wait":
        wake["execution"]["status"] = "wait"
    elif not auto_cognition:
        wake["execution"]["status"] = "policy_only"
    elif budget_blocked:
        wake["execution"]["status"] = "budget_blocked"
    elif provider is None:
        wake["execution"]["status"] = "provider_unavailable"
    else:
        counted_provider = CountingProvider(provider)
        try:
            wake["execution"] = execute_wake(
                policy=policy,
                snapshot=snapshot,
                provider=counted_provider,
                palamedes_module=palamedes_module,
            )
            wake["execution"]["model_call_count"] = counted_provider.call_count
        except (OSError, RuntimeError, ValueError) as exc:
            wake["execution"] = {
                "status": "failed",
                "failure": str(exc),
                "model_call_count": counted_provider.call_count,
                "mission_draft_issued": False,
            }
    used = int(wake["execution"].get("model_call_count", 0))
    wake["budget"]["calls_used_after"] = int(
        state.get("total_model_calls", 0)
    ) + used
    path = store.save_wake(wake)
    store.append_event(
        {
            "ts": wake["created_at"],
            "type": "watch_wake",
            "wake_id": wake["wake_id"],
            "observation_id": wake["observation_id"],
            "operation": policy["operation"],
            "execution_status": wake["execution"]["status"],
            "model_call_count": used,
            "wake_path": str(path),
        }
    )
    state.update(
        {
            "watch_state_version": "palamedes-watch-state/1",
            "last_iteration_at": utc_now(),
            "last_observation_id": snapshot["observation_id"],
            "last_wake_id": wake["wake_id"],
            "last_wake_key": key if policy["operation"] != "wait" else state.get("last_wake_key", ""),
            "total_model_calls": int(state.get("total_model_calls", 0)) + used,
            "iteration_count": int(state.get("iteration_count", 0)) + 1,
        }
    )
    store.save_state(state)
    return wake


def render_wake(wake: Dict[str, Any]) -> str:
    return "\n".join(
        [
            f"Wake: {wake['wake_id']}",
            f"  observation: {wake['observation_id']}",
            f"  operation: {wake['policy']['operation']}",
            f"  roles: {', '.join(wake['policy']['roles']) or 'none'}",
            f"  rationale: {wake['policy']['rationale']}",
            f"  execution: {wake['execution']['status']}",
            f"  model calls: {wake['execution'].get('model_call_count', 0)}",
            f"  draft issued: {wake['execution'].get('mission_draft_issued', False)}",
            f"  budget blocked: {wake['budget']['blocked']}",
        ]
    )


def cmd_watch(args: Any, palamedes_module: Any) -> None:
    workspace = (
        Path(args.workspace).expanduser().resolve()
        if args.workspace
        else Path.cwd().resolve()
    )
    bind_workspace(palamedes_module, workspace)
    ref_value = args.ref_root or os.environ.get(
        "PALAMEDES_REF_ROOT", "/Users/ze/work/ref"
    )
    ref_root = Path(ref_value).expanduser() if ref_value else None
    provider = None
    if args.auto_cognition:
        from palamedes_chat import provider_from_config, provider_health

        health = provider_health(args.provider)
        if health["status"] != "ok":
            raise ValueError(
                f"{args.provider} is unavailable: set {health['api_key_env']}"
            )
        provider = provider_from_config(args.provider, args.model)
    store = WatchStore(palamedes_module.STATE_DIR / "watch")
    iteration = 0
    with WatchLock(store.root / "watch.lock"):
        while True:
            wake = watch_once(
                workspace=workspace,
                store=store,
                palamedes_module=palamedes_module,
                ref_root=ref_root,
                test_command=args.test_command,
                test_timeout=args.test_timeout,
                provider=provider,
                auto_cognition=args.auto_cognition,
                wake_initial=args.wake_initial,
                max_calls_per_wake=args.max_calls_per_wake,
                max_calls_total=args.max_calls_total,
            )
            if args.json:
                print(json.dumps(wake, ensure_ascii=False, sort_keys=True))
            else:
                print(render_wake(wake), flush=True)
            iteration += 1
            if args.once or (args.max_iterations and iteration >= args.max_iterations):
                return
            try:
                time.sleep(args.interval)
            except KeyboardInterrupt:
                return
