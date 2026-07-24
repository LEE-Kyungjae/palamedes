"""Minimal scaffold package for palamedes-agents."""

from .adapters.palamedes_adapter import PalamedesAdapter, summarize_cycle_result
from .runtime.decision_gate import evaluate_cycle_gate, evaluate_snapshot_gate
from .runtime.agent_cycle import AgentCycle
from .runtime.host_events import build_error_event, build_success_event, summarize_for_host
from .runtime.host_step import HostStep, action_contract, required_capabilities_for_action, role_has_action_capabilities
from .runtime.policies import apply_idempotency_policy, build_idempotency_key, should_retry_stale_conflict
from .workflows.planner_loop import PlannerLoop
from .workflows.research_loop import ResearchLoop
from .workflows.review_loop import ReviewLoop

__all__ = [
    "PalamedesAdapter",
    "AgentCycle",
    "PlannerLoop",
    "ResearchLoop",
    "ReviewLoop",
    "summarize_cycle_result",
    "evaluate_cycle_gate",
    "evaluate_snapshot_gate",
    "HostStep",
    "action_contract",
    "required_capabilities_for_action",
    "role_has_action_capabilities",
    "build_error_event",
    "build_success_event",
    "summarize_for_host",
    "apply_idempotency_policy",
    "build_idempotency_key",
    "should_retry_stale_conflict",
]
