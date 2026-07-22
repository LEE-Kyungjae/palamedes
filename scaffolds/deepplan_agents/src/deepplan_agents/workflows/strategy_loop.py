#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

from deepplan_agents.adapters.deepplan_adapter import DeepPlanAdapter
from deepplan_agents.runtime.decision_gate import evaluate_snapshot_gate
from deepplan_agents.runtime.host_events import build_success_event
from deepplan_agents.skills.registry import build_runtime_session
from deepplan_agents.strategy_prompt import build_strategy_prompt_bundle
from deepplan_agents.reference_rag import validate_reference_grounding


GENERIC_TERMS = {
    "ai app",
    "ai tool",
    "dashboard",
    "todo",
    "crm",
    "productivity",
    "assistant",
    "agent platform",
    "workflow",
}

RISK_BOUNDARY_TERMS = {
    "addiction": "habit_exploitation",
    "addictive": "habit_exploitation",
    "rage": "toxic_conflict",
    "anger": "toxic_conflict",
    "revenge": "toxic_conflict",
    "envy": "status_anxiety",
    "jealousy": "status_anxiety",
    "shame": "shame_pressure",
    "casino": "gambling_like_loop",
    "loot box": "gambling_like_loop",
    "dark pattern": "dark_pattern",
}

EMOTION_TERMS = {
    "anxiety": "fear/control",
    "fear": "fear/control",
    "greed": "upside/greed",
    "money": "upside/greed",
    "status": "status",
    "envy": "status/envy",
    "anger": "anger/revenge",
    "revenge": "anger/revenge",
    "belonging": "belonging",
    "lonely": "belonging",
    "relief": "relief",
    "control": "control",
    "achievement": "achievement",
}

REQUIRED_FIELDS = {
    "problem_solution": ["target_user", "problem", "current_alternative", "pain_frequency", "solution"],
    "desire_emotion": ["desire", "emotion", "behavior_signals"],
    "experience_loop": ["trigger", "action", "reward", "monetization", "repeat_loop"],
    "reference_insight": ["references", "behavior_signals"],
    "monetization_trigger": ["monetization", "desire"],
    "differentiation": ["differentiation"],
}

REPORT_REQUIRED_KEYS = [
    "overall_score",
    "decision",
    "axes",
    "emotion_drivers",
    "risk_boundaries",
    "generic_patterns",
    "missing_fields",
    "risks",
    "recommendations",
    "research_questions",
    "next_actions",
    "positioning_rewrite",
    "monetization_moment",
    "reference_insights",
    "creative_directions",
    "personal_profile_updates",
    "project_context",
    "outcome_learning",
]

REPORT_AXIS_KEYS = [
    "problem_solution",
    "desire_emotion",
    "experience_loop",
    "monetization_trigger",
    "anti_generic",
    "reference_insight",
]


class StrategyProvider(Protocol):
    def complete_json(self, *, messages: List[Dict[str, str]], schema: Dict[str, Any]) -> Dict[str, Any]:
        ...


def _text(payload: Dict[str, Any], *keys: str) -> str:
    parts: List[str] = []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(str(item) for item in value)
    return " ".join(parts).strip()


def _count_present(payload: Dict[str, Any], keys: List[str]) -> int:
    count = 0
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            count += 1
        elif isinstance(value, list) and any(str(item).strip() for item in value):
            count += 1
    return count


def _score(required_count: int, present_count: int) -> int:
    if required_count <= 0:
        return 0
    return min(100, round((present_count / required_count) * 100))


def _generic_terms(text: str) -> List[str]:
    lower = text.lower()
    return sorted(term for term in GENERIC_TERMS if term in lower)


def _emotion_drivers(text: str) -> List[str]:
    lower = text.lower()
    drivers = sorted({driver for term, driver in EMOTION_TERMS.items() if term in lower})
    return drivers


def _risk_boundaries(text: str) -> List[str]:
    lower = text.lower()
    return sorted({risk for term, risk in RISK_BOUNDARY_TERMS.items() if term in lower})


def _has_value(payload: Dict[str, Any], key: str) -> bool:
    value = payload.get(key)
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(str(item).strip() for item in value)
    return value is not None


def _missing_fields(payload: Dict[str, Any]) -> Dict[str, List[str]]:
    return {
        axis: [key for key in keys if not _has_value(payload, key)]
        for axis, keys in REQUIRED_FIELDS.items()
    }


def _research_questions(missing: Dict[str, List[str]], generic_hits: List[str]) -> List[str]:
    questions: List[str] = []
    if missing.get("problem_solution"):
        questions.append("Which narrow user repeatedly feels this problem, and what current alternative proves the pain exists?")
    if missing.get("desire_emotion"):
        questions.append("Which emotion or desire makes the user pay, return, share, or feel loss if they ignore the service?")
    if missing.get("experience_loop"):
        questions.append("What trigger, action, reward, payment moment, and return reason form the repeatable experience loop?")
    if missing.get("reference_insight"):
        questions.append("Which user behavior data, reviews, papers, failed products, or successful services generated the core insight?")
    if generic_hits:
        questions.append("What behavior, distribution, timing, emotional, or market wedge makes this more than another generic AI service?")
    return questions


def _positioning_rewrite(payload: Dict[str, Any], decision: str, generic_hits: List[str]) -> str:
    target = str(payload.get("target_user", "")).strip() or "a narrower user"
    problem = str(payload.get("problem", "")).strip() or "a repeated painful problem"
    emotion = str(payload.get("emotion", "")).strip() or str(payload.get("desire", "")).strip() or "a clear emotional driver"
    wedge = str(payload.get("differentiation", "")).strip() or "a sharper behavior, market, or timing wedge"
    if decision == "stop_and_research":
        return f"Do not build yet. First prove that {target} has {problem} and that {emotion} is strong enough to create repeat behavior."
    if generic_hits:
        return f"Reframe away from {', '.join(generic_hits)}. Position it for {target} around {problem}, with {wedge} as the reason it is not generic."
    return f"Position it as a product for {target} that resolves {problem} through {emotion}, with {wedge} as the first-session difference."


def _monetization_moment(payload: Dict[str, Any], emotion_hits: List[str]) -> str:
    monetization = str(payload.get("monetization", "")).strip()
    trigger = str(payload.get("trigger", "")).strip()
    emotion = ", ".join(emotion_hits) if emotion_hits else str(payload.get("emotion", "")).strip()
    if monetization and trigger:
        return f"The payment moment should appear at '{trigger}' when the user feels {emotion or 'the target desire'} and sees why {monetization} is worth paying for."
    if monetization:
        return f"The monetization path is present, but the exact trigger that makes payment feel natural is not yet clear: {monetization}."
    return "No clear monetization moment is defined yet."


def _next_actions(
    payload: Dict[str, Any],
    *,
    decision: str,
    risks: List[str],
    research_questions: List[str],
    positioning_rewrite: str,
) -> List[Dict[str, Any]]:
    actions: List[Dict[str, Any]] = []
    if decision == "stop_and_research":
        actions.append(
            {
                "target_role": "researcher",
                "action": "run_reference_discovery",
                "priority": "high",
                "reason": "Reference discovery is required before build because the strategy report found missing external behavior evidence.",
                "payload": {
                    "question": research_questions[0] if research_questions else "Which references prove or disprove this product direction?",
                    "context": str(payload.get("idea", "")).strip(),
                    "references": payload.get("references", []) if isinstance(payload.get("references", []), list) else [],
                    "apply": True,
                },
            }
        )
    if decision == "revise_before_build":
        actions.append(
            {
                "target_role": "planner",
                "action": "update_plan",
                "priority": "medium",
                "reason": "The idea may be viable, but positioning, emotional demand, or differentiation must be sharpened before build.",
                "payload": {
                    "selected_option": positioning_rewrite,
                    "risk_signal_insight": ", ".join(risks) if risks else "Revise before build.",
                },
            }
        )
    if decision == "review_risk_boundary" or "risk_boundary_needs_review" in risks:
        actions.append(
            {
                "target_role": "reviewer",
                "action": "request_review",
                "priority": "high",
                "reason": "Human review is required because the monetization loop may rely on risky emotional pressure.",
                "payload": {
                    "scope": "strategy",
                    "reason": "Review emotional monetization, trust, community, regulatory, and long-term retention boundaries.",
                    "requested_by": "strategist",
                    "priority": "high",
                    "related_references": payload.get("references", []) if isinstance(payload.get("references", []), list) else [],
                },
            }
        )
    if decision == "continue":
        actions.append(
            {
                "target_role": "planner",
                "action": "update_plan",
                "priority": "low",
                "reason": "The strategy is strong enough to preserve as the current planning direction.",
                "payload": {
                    "selected_option": positioning_rewrite,
                },
            }
        )
    return actions


def validate_strategy_report_shape(report: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for key in REPORT_REQUIRED_KEYS:
        if key not in report:
            errors.append(f"missing report field: {key}")
    score = report.get("overall_score")
    if not isinstance(score, int) or isinstance(score, bool) or score < 0 or score > 100:
        errors.append("overall_score must be an integer from 0 to 100")
    if report.get("decision") not in {"continue", "revise_before_build", "stop_and_research", "review_risk_boundary"}:
        errors.append("decision is invalid")
    axes = report.get("axes")
    if not isinstance(axes, dict):
        errors.append("axes must be an object")
    else:
        for key in REPORT_AXIS_KEYS:
            value = axes.get(key)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > 100:
                errors.append(f"axes.{key} must be an integer from 0 to 100")
    for key in ["emotion_drivers", "risk_boundaries", "generic_patterns", "risks", "recommendations", "research_questions"]:
        value = report.get(key)
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            errors.append(f"{key} must be an array of strings")
    next_actions = report.get("next_actions")
    if not isinstance(next_actions, list):
        errors.append("next_actions must be an array")
    else:
        for index, action in enumerate(next_actions):
            if not isinstance(action, dict):
                errors.append(f"next_actions[{index}] must be an object")
                continue
            if not isinstance(action.get("action"), str) or not action.get("action", "").strip():
                errors.append(f"next_actions[{index}].action must be a non-empty string")
            if action.get("target_role") not in {"planner", "researcher", "reviewer", "strategist"}:
                errors.append(f"next_actions[{index}].target_role is invalid")
            if action.get("priority") not in {"low", "medium", "high"}:
                errors.append(f"next_actions[{index}].priority is invalid")
            if not isinstance(action.get("reason"), str) or not action.get("reason", "").strip():
                errors.append(f"next_actions[{index}].reason must be a non-empty string")
            if not isinstance(action.get("payload"), dict):
                errors.append(f"next_actions[{index}].payload must be an object")
    if not isinstance(report.get("missing_fields"), dict):
        errors.append("missing_fields must be an object")
    for key in ["positioning_rewrite", "monetization_moment"]:
        if not isinstance(report.get(key), str):
            errors.append(f"{key} must be a string")
    reference_insights = report.get("reference_insights")
    if not isinstance(reference_insights, list) or not all(isinstance(item, dict) for item in reference_insights):
        errors.append("reference_insights must be an array of objects")
    else:
        required = {"source", "observed_behavior", "emotion_driver", "monetization_moment", "repeat_loop", "transferable_principle", "applied_to_plan", "disconfirming_signal"}
        for index, item in enumerate(reference_insights):
            missing = [key for key in sorted(required) if not isinstance(item.get(key), str)]
            if missing:
                errors.append(f"reference_insights[{index}] missing string fields: {', '.join(missing)}")
            for key in ["reference_ids", "source_urls", "evidence_quotes", "transfer_assumptions"]:
                value = item.get(key)
                if not isinstance(value, list) or not all(isinstance(entry, str) for entry in value):
                    errors.append(f"reference_insights[{index}].{key} must be an array of strings")
            confidence = item.get("confidence")
            if not isinstance(confidence, int) or isinstance(confidence, bool) or confidence < 0 or confidence > 100:
                errors.append(f"reference_insights[{index}].confidence must be an integer from 0 to 100")
    creative_directions = report.get("creative_directions")
    if not isinstance(creative_directions, list) or not all(isinstance(item, dict) for item in creative_directions):
        errors.append("creative_directions must be an array of objects")
    else:
        required = {"name", "target_user", "problem", "experience_loop", "emotional_wedge", "monetization_trigger", "reference_basis", "why_not_generic"}
        for index, item in enumerate(creative_directions):
            missing = [key for key in sorted(required) if not isinstance(item.get(key), str)]
            if missing:
                errors.append(f"creative_directions[{index}] missing string fields: {', '.join(missing)}")
    personal_updates = report.get("personal_profile_updates")
    if not isinstance(personal_updates, dict):
        errors.append("personal_profile_updates must be an object")
    else:
        for key in ["repeated_biases", "weak_axes", "overused_solution_patterns", "recommended_next_prompts"]:
            value = personal_updates.get(key)
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                errors.append(f"personal_profile_updates.{key} must be an array of strings")
    project_context = report.get("project_context")
    if not isinstance(project_context, dict):
        errors.append("project_context must be an object")
    else:
        for key in ["entry_mode", "stage", "existing_artifacts_used", "mid_project_risks"]:
            value = project_context.get(key)
            if key in {"existing_artifacts_used", "mid_project_risks"}:
                if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                    errors.append(f"project_context.{key} must be an array of strings")
            elif not isinstance(value, str):
                errors.append(f"project_context.{key} must be a string")
    outcome_learning = report.get("outcome_learning")
    if not isinstance(outcome_learning, dict):
        errors.append("outcome_learning must be an object")
    else:
        for key in ["observed_outcomes", "interpretation", "plan_adjustments", "next_evidence", "profile_implications"]:
            value = outcome_learning.get(key)
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                errors.append(f"outcome_learning.{key} must be an array of strings")
    return errors


def evaluate_strategy_payload(payload: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy fixture generator for tests.

    Product strategy execution must use an AI provider through StrategyLoop.
    This helper stays deterministic so tests can build valid report fixtures
    without making network or model calls.
    """
    idea_text = _text(
        payload,
        "idea",
        "target_user",
        "problem",
        "solution",
        "desire",
        "emotion",
        "current_alternative",
        "pain_frequency",
        "monetization",
        "repeat_loop",
        "trigger",
        "action",
        "reward",
        "differentiation",
        "behavior_signals",
        "references",
    )
    plan_text = _text(plan, "goal", "success_metric", "selected_option")
    combined = f"{idea_text} {plan_text}".strip()
    generic_hits = _generic_terms(combined)
    emotion_hits = _emotion_drivers(combined)
    boundary_hits = _risk_boundaries(combined)
    missing = _missing_fields(payload)

    problem_solution = _score(5, _count_present(payload, REQUIRED_FIELDS["problem_solution"]))
    desire_emotion = _score(3, _count_present(payload, ["desire", "emotion", "behavior_signals"]))
    experience_loop = _score(5, _count_present(payload, REQUIRED_FIELDS["experience_loop"]))
    reference_insight = _score(2, _count_present(payload, ["references", "behavior_signals"]))
    monetization = _score(2, _count_present(payload, ["monetization", "desire"]))
    anti_generic = max(0, 100 - (len(generic_hits) * 15))
    if "differentiation" in payload and str(payload.get("differentiation", "")).strip():
        anti_generic = min(100, anti_generic + 15)

    axes = {
        "problem_solution": problem_solution,
        "desire_emotion": desire_emotion,
        "experience_loop": experience_loop,
        "monetization_trigger": monetization,
        "anti_generic": anti_generic,
        "reference_insight": reference_insight,
    }
    overall = round(sum(axes.values()) / len(axes))
    risks: List[str] = []
    recommendations: List[str] = []

    if problem_solution < 75:
        risks.append("problem_solution_weak")
        recommendations.append("Narrow the target user, painful problem, current alternative, and solution fit before adding features.")
    if desire_emotion < 67:
        risks.append("emotional_demand_unclear")
        recommendations.append("Name the desire or emotion that makes the user pay, return, share, or feel loss if they ignore the service.")
    if experience_loop < 75:
        risks.append("repeat_experience_loop_weak")
        recommendations.append("Define trigger, emotional state, action, reward, monetization moment, and return reason as one loop.")
    if reference_insight < 100:
        risks.append("reference_to_insight_gap")
        recommendations.append("Extract behavior patterns from references instead of relying on internal brainstorming.")
    if generic_hits:
        risks.append("generic_llm_service_pattern")
        recommendations.append("Replace generic feature differentiation with a behavior, market, timing, distribution, or emotional wedge.")
    if boundary_hits:
        risks.append("risk_boundary_needs_review")
        recommendations.append("Separate emotional pull from exploitative loops; define trust, community, regulatory, and long-term retention boundaries.")

    decision = "continue"
    if overall < 60 or "generic_llm_service_pattern" in risks:
        decision = "revise_before_build"
    if overall < 45:
        decision = "stop_and_research"
    if boundary_hits and decision == "continue":
        decision = "review_risk_boundary"

    research_questions = _research_questions(missing, generic_hits)
    positioning_rewrite = _positioning_rewrite(payload, decision, generic_hits)
    report = {
        "overall_score": overall,
        "decision": decision,
        "axes": axes,
        "emotion_drivers": emotion_hits,
        "risk_boundaries": boundary_hits,
        "generic_patterns": generic_hits,
        "missing_fields": missing,
        "risks": risks,
        "recommendations": recommendations,
        "research_questions": research_questions,
        "next_actions": _next_actions(
            payload,
            decision=decision,
            risks=risks,
            research_questions=research_questions,
            positioning_rewrite=positioning_rewrite,
        ),
        "positioning_rewrite": positioning_rewrite,
        "monetization_moment": _monetization_moment(payload, emotion_hits),
        "reference_insights": [
            {
                "source": str(item),
                "reference_ids": [str(item)],
                "source_urls": [],
                "evidence_quotes": [],
                "observed_behavior": "Needs AI extraction from the referenced behavior source.",
                "emotion_driver": ", ".join(emotion_hits) if emotion_hits else "unknown",
                "monetization_moment": str(payload.get("monetization", "")).strip(),
                "repeat_loop": str(payload.get("repeat_loop", "")).strip(),
                "transferable_principle": "Use this only as a test fixture; product execution must use AI extraction.",
                "applied_to_plan": positioning_rewrite,
                "transfer_assumptions": ["The referenced behavior applies to the current target user."],
                "disconfirming_signal": "The behavior does not recur in direct evidence from the target user.",
                "confidence": 50,
            }
            for item in payload.get("references", [])
            if str(item).strip()
        ],
        "creative_directions": [
            {
                "name": "AI provider required",
                "target_user": str(payload.get("target_user", "")).strip(),
                "problem": str(payload.get("problem", "")).strip(),
                "experience_loop": str(payload.get("repeat_loop", "")).strip(),
                "emotional_wedge": ", ".join(emotion_hits) if emotion_hits else str(payload.get("emotion", "")).strip(),
                "monetization_trigger": str(payload.get("monetization", "")).strip(),
                "reference_basis": ", ".join(str(item) for item in payload.get("references", []) if str(item).strip()),
                "why_not_generic": str(payload.get("differentiation", "")).strip(),
            }
        ],
        "personal_profile_updates": {
            "repeated_biases": ["AI extraction required"],
            "weak_axes": [key for key, missing_items in missing.items() if missing_items],
            "overused_solution_patterns": generic_hits,
            "recommended_next_prompts": research_questions[:3],
        },
        "project_context": {
            "entry_mode": str(payload.get("entry_mode", "")).strip() or "new_project",
            "stage": str(payload.get("project_stage", "")).strip() or "unknown",
            "existing_artifacts_used": [str(item) for item in payload.get("existing_artifacts", []) if str(item).strip()],
            "mid_project_risks": [str(item) for item in payload.get("pivot_signals", []) if str(item).strip()],
        },
        "outcome_learning": {
            "observed_outcomes": [str(item) for item in payload.get("usage_signals", []) if str(item).strip()],
            "interpretation": ["AI interpretation required"],
            "plan_adjustments": [positioning_rewrite],
            "next_evidence": research_questions[:3],
            "profile_implications": ["AI extraction required"],
        },
    }
    errors = validate_strategy_report_shape(report)
    if errors:
        raise ValueError("; ".join(errors))
    return report


@dataclass
class StrategyLoop:
    adapter: DeepPlanAdapter
    role: str = "strategist"
    provider: Optional[StrategyProvider] = None

    def run_once(self, payload: Dict[str, Any], *, action_name: str = "evaluate_experience_strategy") -> Dict[str, Any]:
        before = self.adapter.snapshot()
        session = build_runtime_session(self.role)
        preflight = evaluate_snapshot_gate(before)
        if self.provider is None:
            raise ValueError("evaluate_experience_strategy requires an AI strategy provider")
        bundle = build_strategy_prompt_bundle(payload, before, action=action_name)
        strategy = self.provider.complete_json(messages=bundle["messages"], schema=bundle["schema"])
        if not isinstance(strategy, dict):
            raise ValueError("AI strategy provider must return a JSON object")
        errors = validate_strategy_report_shape(strategy)
        errors.extend(validate_reference_grounding(strategy, bundle["reference_retrieval"]))
        if errors:
            raise ValueError("invalid AI strategy report: " + "; ".join(errors))
        gate = {
            "decision": strategy["decision"],
            "reasons": list(strategy["risks"]),
        }
        return {
            "role": self.role,
            "session": session,
            "before": before,
            "preflight": preflight,
            "result": {"strategy": strategy, "payload": payload},
            "summary": {
                "operation": action_name,
                "fingerprint": str(before.get("fingerprint", "")).strip(),
                "changed_fields": [],
                "qa_result": str(before.get("qa", {}).get("result", "")).strip() if isinstance(before.get("qa"), dict) else "",
                "qa_score": before.get("qa", {}).get("score") if isinstance(before.get("qa"), dict) else None,
                "health_status": str(before.get("health", {}).get("status", "")).strip() if isinstance(before.get("health"), dict) else "",
                "retried": False,
            },
            "after": before,
            "gate": gate,
        }

    def run_event(self, payload: Dict[str, Any], *, action_name: str = "evaluate_experience_strategy") -> Dict[str, Any]:
        return build_success_event("strategy_step", self.run_once(payload, action_name=action_name))
