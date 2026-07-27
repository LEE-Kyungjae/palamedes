#!/usr/bin/env python3
"""Autonomous product-vision genesis before mission planning."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from palamedes_observe import utc_now


def fingerprint(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _strings(value: Any, field: str, minimum: int = 1) -> List[str]:
    if not isinstance(value, list) or len(value) < minimum or not all(
        isinstance(item, str) and item.strip() for item in value
    ):
        raise ValueError(f"{field} requires at least {minimum} non-empty strings")
    return [item.strip() for item in value]


def source_anchors(context: str, limit: int = 12) -> Dict[str, str]:
    """Extract immutable source text so models select evidence instead of copying it."""
    candidates: List[str] = []

    def collect(value: Any) -> None:
        if isinstance(value, str):
            normalized = re.sub(r"\s+", " ", value).strip()
            if 12 <= len(normalized) <= 600:
                candidates.append(normalized)
        elif isinstance(value, dict):
            for item in value.values():
                collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)

    try:
        parsed = json.loads(context)
    except json.JSONDecodeError:
        parsed = None
    if parsed is not None:
        collect(parsed)
    if not candidates:
        candidates.extend(
            part.strip()
            for part in re.split(r"(?<=[.!?])\s+|\n+", context)
            if 12 <= len(part.strip()) <= 600
        )
    unique = list(dict.fromkeys(candidates))[:limit]
    if not unique:
        raise ValueError("vision context contains no attributable source anchor")
    return {f"anchor-{index}": value for index, value in enumerate(unique, 1)}


def canonical_context_requirements(
    context: str, model_requirements: Any
) -> List[Dict[str, str]]:
    """Attach exact quotes deterministically and recover from malformed model arrays."""
    anchors = source_anchors(context)
    quote_to_id = {quote: anchor_id for anchor_id, quote in anchors.items()}
    rows = model_requirements if isinstance(model_requirements, list) else []
    canonical: List[Dict[str, str]] = []
    for index, row in enumerate(rows[:12], 1):
        if not isinstance(row, dict):
            continue
        anchor_id = str(row.get("source_anchor_id", "")).strip()
        if not anchor_id:
            anchor_id = quote_to_id.get(str(row.get("source_quote", "")).strip(), "")
        if anchor_id not in anchors:
            continue
        kind = row.get("kind")
        criticality = row.get("criticality")
        canonical.append(
            {
                "requirement_id": str(row.get("requirement_id", "")).strip()
                or f"req-{index}",
                "requirement": str(row.get("requirement", "")).strip()
                or anchors[anchor_id],
                "source_anchor_id": anchor_id,
                "source_quote": anchors[anchor_id],
                "kind": kind
                if kind in {"objective", "constraint", "asset", "non_goal"}
                else "constraint",
                "criticality": criticality
                if criticality in {"core", "supporting"}
                else ("core" if index == 1 else "supporting"),
            }
        )
    if not canonical:
        canonical = [
            {
                "requirement_id": f"req-{index}",
                "requirement": quote,
                "source_anchor_id": anchor_id,
                "source_quote": quote,
                "kind": "objective" if index == 1 else "constraint",
                "criticality": "core" if index == 1 else "supporting",
            }
            for index, (anchor_id, quote) in enumerate(list(anchors.items())[:1], 1)
        ]
    if not any(row["criticality"] == "core" for row in canonical):
        canonical[0]["criticality"] = "core"
    return canonical


class VisionStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.records_root = root / "records"

    def save(self, record: Dict[str, Any]) -> Path:
        self.records_root.mkdir(parents=True, exist_ok=True)
        path = self.records_root / f"{record['vision_genesis_id']}.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return path

    def records(self) -> List[Dict[str, Any]]:
        if not self.records_root.is_dir():
            return []
        rows = []
        for path in self.records_root.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict):
                rows.append(payload)
        rows.sort(key=lambda row: row.get("created_at", ""))
        return rows

    def latest(self) -> Optional[Dict[str, Any]]:
        rows = self.records()
        return rows[-1] if rows else None

    def checkpoint(self, attempt_id: str) -> Dict[str, Any]:
        path = self.root / "checkpoints" / f"{attempt_id}.json"
        if not path.is_file():
            return {"attempt_id": attempt_id, "roles": {}}
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("vision checkpoint must be an object")
        return payload

    def save_checkpoint(
        self, attempt_id: str, role: str, output: Dict[str, Any], usage: Dict[str, Any]
    ) -> None:
        root = self.root / "checkpoints"
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{attempt_id}.json"
        payload = self.checkpoint(attempt_id)
        roles = payload.setdefault("roles", {})
        existing = roles.get(role)
        row = {"output": output, "usage": usage}
        if existing is not None and existing != row:
            raise ValueError("vision checkpoint output is immutable")
        roles[role] = row
        payload["updated_at"] = utc_now()
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    def discard_checkpoint_role(self, attempt_id: str, role: str) -> None:
        path = self.root / "checkpoints" / f"{attempt_id}.json"
        payload = self.checkpoint(attempt_id)
        roles = payload.get("roles", {})
        if not isinstance(roles, dict) or role not in roles:
            return
        del roles[role]
        payload["updated_at"] = utc_now()
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    def needs_wake(
        self,
        outcome_count: int,
        product_ground_truth_fingerprint: str = "",
        actual_investment: Optional[Dict[str, Any]] = None,
    ) -> bool:
        latest = self.latest()
        if latest is None:
            return True
        if (
            product_ground_truth_fingerprint
            and latest.get("product_ground_truth_fingerprint")
            != product_ground_truth_fingerprint
        ):
            return True
        if not latest.get("investment_envelope"):
            return True
        outcome_budget = int(
            latest.get("investment_envelope", {}).get(
                "max_outcomes_before_reassessment", 5
            )
        )
        if isinstance(actual_investment, dict):
            envelope = latest["investment_envelope"]
            for actual_field, budget_field in (
                ("engineering_days", "engineering_days_high"),
                ("ai_cost", "ai_cost_high"),
            ):
                budget = envelope.get(budget_field)
                spent = actual_investment.get(actual_field, 0)
                if isinstance(budget, int) and (
                    (budget == 0 and spent > 0)
                    or (budget > 0 and spent >= budget)
                ):
                    return True
            infrastructure_budget = envelope.get("monthly_infrastructure_high")
            infrastructure_peak = actual_investment.get(
                "monthly_infrastructure_peak", 0
            )
            if isinstance(infrastructure_budget, int) and (
                (infrastructure_budget == 0 and infrastructure_peak > 0)
                or infrastructure_peak > infrastructure_budget
            ):
                return True
        return (
            outcome_count - int(latest.get("outcome_count_at_creation", 0))
            >= outcome_budget
        )


def run_vision_genesis(
    *,
    ask: Callable[[str, str], Dict[str, Any]],
    store: VisionStore,
    context: str,
    outcome_count: int = 0,
    agenda_strategy: str = "adaptive",
) -> Dict[str, Any]:
    """Generate distant product worlds without granting implementation authority."""
    if agenda_strategy not in {"adaptive", "frontier", "conventional"}:
        raise ValueError(
            "agenda_strategy must be adaptive, frontier, or conventional"
        )
    prior_records = store.records()[-5:]
    authoritative_anchors = source_anchors(context)
    prior_frontiers = []
    for record in prior_records:
        selected_id = record.get("judgment", {}).get("selected_vision_id")
        for world in record.get("product_worlds", {}).get("worlds", []):
            if world.get("vision_id") == selected_id:
                prior_frontiers.append(
                    {
                        "vision_genesis_id": record.get("vision_genesis_id"),
                        "title": world.get("title"),
                        "central_human_tension": world.get("central_human_tension"),
                        "content_or_rule_engine": world.get("content_or_rule_engine"),
                        "social_dynamics": world.get("social_dynamics"),
                    }
                )
    agenda_direction = (
        """Reverse assumptions, expose emotionally charged or socially mediated behavior,
and search for genre-changing combinations outside adjacent software patterns."""
        if agenda_strategy == "frontier"
        else """Stay within the explicit product category and its adjacent user journeys.
Ask strong, practical product questions about the supplied surfaces, capabilities, friction,
adoption, and measurable value. Do not use distant-domain analogy or assumption reversal as
a creativity technique; record `assumption_reversed` as the important assumption preserved."""
        if agenda_strategy == "conventional"
        else """Generate competing question modes rather than assuming that conceptual
distance is always valuable. Include at least one frontier question that reverses assumptions,
one conventional question grounded in supplied journeys and capabilities, and one bridge
question that connects a distant human mechanism to a concrete product engine. Select by
expected product leverage, coherence, testability, and opportunity cost—not novelty alone."""
    )
    territory_direction = (
        """Across selected questions use at least 6 distinct search territories spanning
human culture, embodied practice, social institutions, markets, art, ritual, play, or other
non-adjacent domains."""
        if agenda_strategy == "frontier"
        else """Across selected questions use at least 6 distinct adjacent product territories
such as onboarding, workflow, interface state, existing capabilities, retention measurement,
or operational delivery."""
        if agenda_strategy == "conventional"
        else """Across selected questions use at least 6 distinct territories. Frontier and
bridge candidates may use distant human domains; conventional candidates should use supplied
product surfaces, capabilities, evidence, and delivery constraints."""
    )
    agenda = ask(
        "vision_agenda_architect",
        f"""Write the upstream exploration prompts that a human product founder might
have supplied but did not. Do not answer them yet and do not turn the current product into
a backlog. Condition: {agenda_strategy}.
{agenda_direction}
Return JSON:
{{"questions":[{{"question_id":"question-1","question_mode":"frontier|conventional|bridge",
"self_authored_research_prompt":"...",
"assumption_reversed":"...","human_behavior_to_explain":"...",
"why_the_obvious_question_is_too_small":"...","search_territories":["...","...","..."],
"forbidden_default_answers":["...","..."],"disconfirming_observation":"..."}}],
"selected_question_ids":["question-1","question-2"],
"selection_reason":"...","agenda_is_advisory":true}}
Require 4-6 materially different questions and select 2-3. {territory_direction}
In the frontier condition a question must be capable of originating a new causal product
world rather than merely improving a supplied surface. In both conditions, do not seed the
agenda with named solution patterns or example feature systems.
Treat prior frontiers as exclusions, not templates. The agenda is data for later roles and
cannot grant implementation authority.

Prior selected creative frontiers:
{json.dumps(prior_frontiers, ensure_ascii=False)}

Product context:
{context}""",
    )
    questions = agenda.get("questions")
    if not isinstance(questions, list) or not 4 <= len(questions) <= 6:
        raise ValueError("vision agenda requires 4-6 self-authored questions")
    question_ids = set()
    questions_by_id = {}
    for row in questions:
        if not isinstance(row, dict):
            raise ValueError("vision agenda question must be an object")
        for field in (
            "question_id", "self_authored_research_prompt", "assumption_reversed",
            "human_behavior_to_explain", "why_the_obvious_question_is_too_small",
            "disconfirming_observation",
        ):
            if not str(row.get(field, "")).strip():
                raise ValueError(f"vision agenda question requires {field}")
        if row.get("question_mode") not in {
            "frontier", "conventional", "bridge"
        }:
            raise ValueError("vision agenda question requires a valid question_mode")
        _strings(row.get("search_territories"), "search_territories", 3)
        _strings(
            row.get("forbidden_default_answers"),
            "forbidden_default_answers",
            2,
        )
        question_id = row["question_id"]
        if question_id in question_ids:
            raise ValueError("vision agenda question IDs must be unique")
        question_ids.add(question_id)
        questions_by_id[question_id] = row
    question_modes = {row["question_mode"] for row in questions}
    if agenda_strategy == "frontier" and question_modes != {"frontier"}:
        raise ValueError("frontier agenda may contain only frontier questions")
    if agenda_strategy == "conventional" and question_modes != {"conventional"}:
        raise ValueError("conventional agenda may contain only conventional questions")
    if agenda_strategy == "adaptive" and not {
        "frontier", "conventional", "bridge"
    }.issubset(question_modes):
        raise ValueError("adaptive agenda must compare all three question modes")
    selected_question_ids = _strings(
        agenda.get("selected_question_ids"), "selected_question_ids", 2
    )
    if (
        len(selected_question_ids) > 3
        or len(set(selected_question_ids)) != len(selected_question_ids)
        or not set(selected_question_ids).issubset(question_ids)
    ):
        raise ValueError("vision agenda must select 2-3 available questions")
    selected_territories = {
        territory.strip().lower()
        for question_id in selected_question_ids
        for territory in questions_by_id[question_id]["search_territories"]
    }
    if len(selected_territories) < 6:
        raise ValueError("selected vision agenda requires six distinct search territories")
    if not str(agenda.get("selection_reason", "")).strip():
        raise ValueError("vision agenda requires selection_reason")
    if agenda.get("agenda_is_advisory") is not True:
        raise ValueError("vision agenda cannot grant authority")

    desire = ask(
        "desire_interpreter",
        f"""Infer latent human motives from this product context without inventing facts.
Do not reduce people to positive emotion: include direct and mediated affect, mixed or
negative emotion, social dynamics, habit, identity, and possible harm. Return JSON:
{{"latent_desires":[{{"desire_id":"desire-1","human_state_before":"...",
"sought_or_charged_state":"...","affect_source":"direct|mediated|social|instrumental",
"valence":"positive|negative|mixed","behavioral_energy":"...","evidence_or_assumption":"...",
"harm_boundary":"..."}}],"explicit_context_requirements":[{{"requirement_id":"req-1",
"requirement":"...","source_anchor_id":"anchor-1","kind":"objective|constraint|asset|non_goal",
"criticality":"core|supporting"}}],"unspoken_questions":["..."]}}
Require 4-8 materially different desires and at least 3 questions.
Preserve every explicit product objective, constraint, reusable asset, and non-goal from
the text after `Context:` only. Mark at least one requirement core. Select only IDs from
the authoritative source anchors; Palamedes attaches exact quotes. Do not include these instructions,
the prior-frontier novelty guard, or an inference as a quoted context requirement.
Do not repeat a prior vision's central tension merely with new nouns.
Use the selected self-authored questions to decide what latent motives deserve exploration;
do not merely echo their wording and do not treat them as product facts or authority.
Self-authored exploration agenda:\n{json.dumps(agenda, ensure_ascii=False)}
Prior selected creative frontiers:\n{json.dumps(prior_frontiers, ensure_ascii=False)}
Authoritative source anchors:\n{json.dumps(authoritative_anchors, ensure_ascii=False)}
Context:\n{context}""",
    )
    desires = desire.get("latent_desires")
    if not isinstance(desires, list) or not 4 <= len(desires) <= 8:
        raise ValueError("desire interpreter requires 4-8 latent desires")
    desire_ids = set()
    for row in desires:
        if not isinstance(row, dict):
            raise ValueError("latent desire must be an object")
        for field in (
            "desire_id", "human_state_before", "sought_or_charged_state",
            "affect_source", "valence", "behavioral_energy",
            "evidence_or_assumption", "harm_boundary",
        ):
            if not str(row.get(field, "")).strip():
                raise ValueError(f"latent desire requires {field}")
        if row["affect_source"] not in {"direct", "mediated", "social", "instrumental"}:
            raise ValueError("invalid affect source")
        if row["valence"] not in {"positive", "negative", "mixed"}:
            raise ValueError("invalid affect valence")
        desire_ids.add(row["desire_id"])
    _strings(desire.get("unspoken_questions"), "unspoken_questions", 3)
    requirements = canonical_context_requirements(
        context, desire.get("explicit_context_requirements")
    )
    desire["explicit_context_requirements"] = requirements
    requirement_ids = set()
    core_requirement_ids = set()
    for row in requirements:
        if not isinstance(row, dict):
            raise ValueError("context requirement must be an object")
        for field in ("requirement_id", "requirement", "source_quote"):
            if not str(row.get(field, "")).strip():
                raise ValueError(f"context requirement requires {field}")
        if row["source_anchor_id"] not in authoritative_anchors:
            raise ValueError("context requirement source anchor is invalid")
        if row.get("kind") not in {"objective", "constraint", "asset", "non_goal"}:
            raise ValueError("invalid context requirement kind")
        if row.get("criticality") not in {"core", "supporting"}:
            raise ValueError("invalid context requirement criticality")
        requirement_ids.add(row["requirement_id"])
        if row["criticality"] == "core":
            core_requirement_ids.add(row["requirement_id"])
    if len(requirement_ids) != len(requirements) or not core_requirement_ids:
        raise ValueError("context requirements need unique IDs and at least one core item")

    analogy = ask(
        "distant_analogy_explorer",
        f"""Search conceptually distant human systems, not adjacent software features.
Abstract transferable mechanisms from culture, games, rituals, museums, communities,
markets, art, sport, fashion, education, or other domains. Return JSON:
{{"analogies":[{{"analogy_id":"analogy-1","source_domain":"...",
"source_pattern":"...","transferable_mechanism":"...","target_tension":"...",
"related_desire_ids":["desire-1"],"distance_reason":"...","misuse_risk":"..."}}]}}
Require 6-10 analogies from at least 4 source domains. Avoid ranking, badges, daily
missions, skins, and generic gamification unless transformed by a distant mechanism.
Prior selected creative frontiers are novelty exclusions, not analogy templates:
{json.dumps(prior_frontiers, ensure_ascii=False)}
Desires:\n{json.dumps(desire, ensure_ascii=False)}""",
    )
    analogies = analogy.get("analogies")
    if not isinstance(analogies, list) or not 6 <= len(analogies) <= 10:
        raise ValueError("analogy explorer requires 6-10 analogies")
    analogy_ids = set()
    domains = set()
    for row in analogies:
        if not isinstance(row, dict):
            raise ValueError("analogy must be an object")
        for field in (
            "analogy_id", "source_domain", "source_pattern", "transferable_mechanism",
            "target_tension", "distance_reason", "misuse_risk",
        ):
            if not str(row.get(field, "")).strip():
                raise ValueError(f"analogy requires {field}")
        related = _strings(row.get("related_desire_ids"), "related_desire_ids")
        if not set(related).issubset(desire_ids):
            raise ValueError("analogy cites unknown desire")
        analogy_ids.add(row["analogy_id"])
        domains.add(row["source_domain"].strip().lower())
    if len(domains) < 4:
        raise ValueError("analogies require at least four source domains")

    fusion = ask(
        "mechanism_fusion_inventor",
        f"""Invent product mechanisms by forcing collisions between distant analogies.
Do not propose isolated feature additions. Each fusion must use 2-4 analogy IDs and
change the user's repeated experience or the product's genre. Return JSON:
{{"fusions":[{{"fusion_id":"fusion-1","analogy_ids":["analogy-1","analogy-2"],
"mechanism":"...","new_user_behavior":"...","emotional_tension":"...",
"why_not_an_adjacent_feature":"...","conceptual_distance":70,
"smallest_reality_probe":"..."}}]}}
Require 5-8 distinct fusions; conceptual_distance is integer 0-100.
Prior selected creative frontiers must be treated as a novelty exclusion, not a template:
{json.dumps(prior_frontiers, ensure_ascii=False)}
Analogies:\n{json.dumps(analogy, ensure_ascii=False)}""",
    )
    fusions = fusion.get("fusions")
    if not isinstance(fusions, list) or not 5 <= len(fusions) <= 8:
        raise ValueError("fusion inventor requires 5-8 fusions")
    fusion_ids = set()
    for row in fusions:
        if not isinstance(row, dict):
            raise ValueError("fusion must be an object")
        cited = _strings(row.get("analogy_ids"), "fusion analogy_ids", 2)
        if len(cited) > 4 or not set(cited).issubset(analogy_ids):
            raise ValueError("fusion must cite 2-4 available analogies")
        for field in (
            "fusion_id", "mechanism", "new_user_behavior", "emotional_tension",
            "why_not_an_adjacent_feature", "smallest_reality_probe",
        ):
            if not str(row.get(field, "")).strip():
                raise ValueError(f"fusion requires {field}")
        distance = row.get("conceptual_distance")
        if not isinstance(distance, int) or isinstance(distance, bool) or not 0 <= distance <= 100:
            raise ValueError("conceptual_distance must be integer 0-100")
        fusion_ids.add(row["fusion_id"])

    worlds = ask(
        "product_world_builder",
        f"""Turn mechanism fusions into coherent product worlds, not feature lists.
Return JSON: {{"worlds":[{{"vision_id":"vision-1","title":"...","premise":"...",
"causal_lane":"rules_interaction|meaning_identity|resources_institutions_social",
"fusion_ids":["fusion-1"],"central_human_tension":"...",
"experience_loop":["entry","action","surprise","meaning","return"],
"identity_expression":"...","social_dynamics":"...","content_or_rule_engine":"...",
"three_year_generativity":"...","why_users_would_tell_someone":"...",
"why_this_is_not_a_feature_pack":"...","counterfactual_without_it":"...",
"harm_and_exploitation_risks":["..."],"first_probe":"..."}}]}}
Require exactly 3 worlds, each with at least 5 experience-loop steps and at least
one risk. The worlds must differ in their central mechanism, not only their theme:
one must primarily transform rules or interaction causality, one meaning or identity,
and one resources, institutions, or social coordination. Do not repeat a prior selected
frontier unless the new mechanism explicitly overturns it.
Prior frontiers:\n{json.dumps(prior_frontiers, ensure_ascii=False)}
Product context:\n{context}
Explicit requirements:\n{json.dumps(requirements, ensure_ascii=False)}
Fusions:\n{json.dumps(fusion, ensure_ascii=False)}""",
    )
    world_rows = worlds.get("worlds")
    if not isinstance(world_rows, list) or len(world_rows) != 3:
        raise ValueError("world builder requires exactly three product worlds")
    vision_ids = set()
    causal_lanes = set()
    for row in world_rows:
        if not isinstance(row, dict):
            raise ValueError("product world must be an object")
        cited = _strings(row.get("fusion_ids"), "world fusion_ids")
        if not set(cited).issubset(fusion_ids):
            raise ValueError("world cites unknown fusion")
        _strings(row.get("experience_loop"), "experience_loop", 5)
        _strings(row.get("harm_and_exploitation_risks"), "harm risks")
        for field in (
            "vision_id", "title", "premise", "central_human_tension",
            "identity_expression", "social_dynamics", "content_or_rule_engine",
            "three_year_generativity", "why_users_would_tell_someone",
            "why_this_is_not_a_feature_pack", "counterfactual_without_it", "first_probe",
        ):
            if not str(row.get(field, "")).strip():
                raise ValueError(f"product world requires {field}")
        if row.get("causal_lane") not in {
            "rules_interaction",
            "meaning_identity",
            "resources_institutions_social",
        }:
            raise ValueError("product world requires a valid causal_lane")
        vision_ids.add(row["vision_id"])
        causal_lanes.add(row["causal_lane"])
    if len(vision_ids) != 3:
        raise ValueError("product world vision IDs must be unique")
    if causal_lanes != {
        "rules_interaction",
        "meaning_identity",
        "resources_institutions_social",
    }:
        raise ValueError("product worlds must cover all three causal lanes")

    judgment = ask(
        "maniac_critic_and_vision_author",
        f"""Judge these worlds like a domain-obsessed creator, not a backlog manager.
Attack generic gamification, shallow novelty, incoherent emotion, derivative mechanics,
exploitative affect, impossible scale, and ideas that fans cannot interpret or discuss.
Then select at most one world. Context fit and portfolio difference are required;
do not repeatedly select the same emotional or social structure. Return JSON:
{{"critiques":[{{"vision_id":"vision-1","genericity_failure":"...",
"mechanism_depth":"...","fan_depth":"...","emotional_truth":"...",
"economic_or_scale_risk":"...","portfolio_difference":"...",
"verdict":"advance|incubate|reject"}}],
"decision":"select|incubate_all|reject_all","selected_vision_id":"vision-1 or empty",
"selection_reason":"...","vision_brief":"a self-contained natural-language product
proposal a human could approve without having supplied the core idea",
"founder_prompt":"the concise upstream product-direction text a human founder could have
written before this exploration, but did not; it must itself introduce the unsupplied
human tension, product mechanism, emotional or behavioral loop, and durable expansion",
"requirement_coverage":[{{"requirement_id":"req-1",
"status":"satisfied|satisfied_with_validation|partial|missed","evidence":"..."}}],
"originality_case":"...","assumptions":["..."],"falsifiers":["..."],
"delivery_authority_granted":false}}
Preserve one critique per world. vision_brief must describe the human tension, mechanism,
experience loop, identity or social consequence, generative future, and first validation.
When a world is selected, founder_prompt must be 180-1200 characters, stand alone without
internal IDs or references to this generation process, and be specific enough to initiate
the product exploration rather than saying only "make it more engaging". It is evidence of
the upstream prompt Palamedes originated, not a summary supplied by the user.
Prior selected frontiers:\n{json.dumps(prior_frontiers, ensure_ascii=False)}
Product context:\n{context}
Explicit requirements:\n{json.dumps(requirements, ensure_ascii=False)}
Worlds:\n{json.dumps(worlds, ensure_ascii=False)}""",
    )
    critiques = judgment.get("critiques")
    if not isinstance(critiques, list) or len(critiques) != 3:
        raise ValueError("vision judgment requires one critique per world")
    if {row.get("vision_id") for row in critiques} != vision_ids:
        raise ValueError("vision critiques must cover every world exactly once")
    if not all(str(row.get("portfolio_difference", "")).strip() for row in critiques):
        raise ValueError("each vision critique requires portfolio_difference")
    decision = judgment.get("decision")
    if decision not in {"select", "incubate_all", "reject_all"}:
        raise ValueError("invalid vision decision")
    selected_id = str(judgment.get("selected_vision_id", "")).strip()
    if decision == "select" and selected_id not in vision_ids:
        raise ValueError("selected vision must name a generated world")
    if decision != "select" and selected_id:
        raise ValueError("non-select vision decision cannot select a world")
    brief = str(judgment.get("vision_brief", "")).strip()
    if decision == "select" and len(brief) < 240:
        raise ValueError("selected vision requires a substantive natural-language brief")
    founder_prompt = str(judgment.get("founder_prompt", "")).strip()
    if decision == "select" and not 180 <= len(founder_prompt) <= 1200:
        raise ValueError("selected vision requires a substantive founder_prompt")
    if decision == "select" and re.search(
        r"\b(?:vision|fusion|analogy|desire|question)-\d+\b",
        founder_prompt,
        flags=re.IGNORECASE,
    ):
        raise ValueError("founder_prompt cannot expose internal generation IDs")
    if decision != "select" and founder_prompt:
        raise ValueError("non-select vision decision cannot emit a founder_prompt")
    if judgment.get("delivery_authority_granted") is not False:
        raise ValueError("vision genesis cannot grant delivery authority")
    coverage = judgment.get("requirement_coverage")
    if not isinstance(coverage, list) or {
        row.get("requirement_id") for row in coverage if isinstance(row, dict)
    } != requirement_ids:
        raise ValueError("vision judgment must cover every explicit context requirement")
    coverage_by_id = {}
    for row in coverage:
        if row.get("status") not in {
            "satisfied", "satisfied_with_validation", "partial", "missed"
        }:
            raise ValueError("invalid context requirement coverage status")
        if not str(row.get("evidence", "")).strip():
            raise ValueError("context requirement coverage requires evidence")
        coverage_by_id[row["requirement_id"]] = row["status"]
    unresolved_core_requirement_ids = sorted(
        requirement_id
        for requirement_id in core_requirement_ids
        if coverage_by_id[requirement_id]
        not in {"satisfied", "satisfied_with_validation"}
    )
    _strings(judgment.get("assumptions"), "vision assumptions")
    _strings(judgment.get("falsifiers"), "vision falsifiers")

    investment = ask(
        "vision_reality_governor",
        f"""Prevent an imaginative vision from becoming an irrational build commitment.
Compare exactly six counterfactual actions: full_build, minimal_probe, manual_probe,
reuse_or_buy, do_nothing, and alternative_opportunity. Return JSON:
{{"evidence_maturity":"speculative|behavioral|demand|revenue",
"alternatives":[{{"alternative":"full_build|minimal_probe|manual_probe|reuse_or_buy|do_nothing|alternative_opportunity",
"learning_value":"...","engineering_days_low":0,"engineering_days_high":0,
"ai_cost_low":0,"ai_cost_high":0,"monthly_infrastructure_low":0,
"monthly_infrastructure_high":0,"maintenance_burden":"...",
"reversibility":"high|medium|low","opportunity_cost":"...","failure_mode":"..."}}],
"decision":"probe|defer|reject","selected_alternative":"...",
"decision_rationale":"...","renewal_evidence":["..."],"kill_criteria":["..."],
"debt_guard":"...","scale_guard":"...","delivery_authority_granted":false}}
All cost fields are non-negative integers in project-local units and lows cannot exceed highs.
When evidence is speculative, full_build cannot be selected. Prefer the smallest action that
can disconfirm the emotional and behavioral thesis. Explicitly consider over-engineering,
decades of debt, AI/token cost, infrastructure fit, time-to-learning, and doing something else.

Product context:\n{context}

Selected vision hypothesis:\n{brief}""",
    )
    maturity = investment.get("evidence_maturity")
    if maturity not in {"speculative", "behavioral", "demand", "revenue"}:
        raise ValueError("reality governor requires evidence maturity")
    alternatives = investment.get("alternatives")
    required_alternatives = {
        "full_build", "minimal_probe", "manual_probe", "reuse_or_buy",
        "do_nothing", "alternative_opportunity",
    }
    if not isinstance(alternatives, list) or {
        row.get("alternative") for row in alternatives if isinstance(row, dict)
    } != required_alternatives:
        raise ValueError("reality governor requires exactly six counterfactual alternatives")
    for row in alternatives:
        for field in (
            "learning_value", "maintenance_burden", "opportunity_cost", "failure_mode",
        ):
            if not str(row.get(field, "")).strip():
                raise ValueError(f"reality alternative requires {field}")
        if row.get("reversibility") not in {"high", "medium", "low"}:
            raise ValueError("reality alternative requires reversibility")
        for low, high in (
            ("engineering_days_low", "engineering_days_high"),
            ("ai_cost_low", "ai_cost_high"),
            ("monthly_infrastructure_low", "monthly_infrastructure_high"),
        ):
            low_value, high_value = row.get(low), row.get(high)
            if (
                not isinstance(low_value, int) or isinstance(low_value, bool)
                or not isinstance(high_value, int) or isinstance(high_value, bool)
                or low_value < 0 or high_value < low_value
            ):
                raise ValueError(f"invalid reality cost range {low}/{high}")
    if investment.get("decision") not in {"probe", "defer", "reject"}:
        raise ValueError("reality governor requires probe, defer, or reject")
    selected_alternative = investment.get("selected_alternative")
    if selected_alternative not in required_alternatives:
        raise ValueError("reality governor selected an unavailable alternative")
    if maturity == "speculative" and selected_alternative == "full_build":
        raise ValueError("speculative vision cannot authorize a full build")
    for field in ("decision_rationale", "debt_guard", "scale_guard"):
        if not str(investment.get(field, "")).strip():
            raise ValueError(f"reality governor requires {field}")
    _strings(investment.get("renewal_evidence"), "renewal evidence")
    _strings(investment.get("kill_criteria"), "kill criteria")
    if investment.get("delivery_authority_granted") is not False:
        raise ValueError("reality governor cannot grant delivery authority")

    selected_investment = next(
        row for row in alternatives if row["alternative"] == selected_alternative
    )
    maturity_outcome_budgets = {
        "speculative": 1,
        "behavioral": 2,
        "demand": 3,
        "revenue": 5,
    }
    investment_envelope = {
        "evidence_maturity": maturity,
        "selected_alternative": selected_alternative,
        "max_outcomes_before_reassessment": maturity_outcome_budgets[maturity],
        "engineering_days_high": selected_investment["engineering_days_high"],
        "ai_cost_high": selected_investment["ai_cost_high"],
        "monthly_infrastructure_high": selected_investment[
            "monthly_infrastructure_high"
        ],
        "budget_exhaustion_action": "regenerate_vision",
    }

    created_at = utc_now()
    structured_context = {}
    try:
        candidate_context = json.loads(context)
        if (
            isinstance(candidate_context, dict)
            and candidate_context.get("vision_context_version")
            == "palamedes-vision-context/1"
        ):
            structured_context = candidate_context
    except json.JSONDecodeError:
        pass
    identity = {
        "context": context,
        "agenda_strategy": agenda_strategy,
        "agenda": agenda,
        "desire": desire,
        "analogy": analogy,
        "fusion": fusion,
        "worlds": worlds,
        "judgment": judgment,
        "investment_judgment": investment,
    }
    status = "selected" if decision == "select" else decision
    if decision == "select" and unresolved_core_requirement_ids:
        status = "blocked_core_requirements"
    record = {
        "vision_genesis_version": "palamedes-vision-genesis/3",
        "vision_genesis_id": f"vision-genesis-{fingerprint(identity)[:12]}",
        "status": status,
        "context_fingerprint": fingerprint(context),
        "product_ground_truth_fingerprint": fingerprint(
            structured_context.get("product_ground_truth", {})
        ),
        "outcome_count_at_creation": outcome_count,
        "agenda_strategy": agenda_strategy,
        "prior_vision_ids_considered": [
            row["vision_genesis_id"] for row in prior_frontiers
        ],
        "exploration_agenda": agenda,
        "desire_interpretation": desire,
        "distant_analogies": analogy,
        "mechanism_fusions": fusion,
        "product_worlds": worlds,
        "judgment": judgment,
        "requirement_gate": {
            "passed": not unresolved_core_requirement_ids,
            "unresolved_core_requirement_ids": unresolved_core_requirement_ids,
        },
        "investment_judgment": investment,
        "investment_envelope": investment_envelope,
        "delivery_authority_granted": False,
        "created_at": created_at,
    }
    store.save(record)
    return record


def selected_vision_context(record: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not isinstance(record, dict) or record.get("status") != "selected":
        return {}
    selected_id = record.get("judgment", {}).get("selected_vision_id")
    world = next(
        (
            row
            for row in record.get("product_worlds", {}).get("worlds", [])
            if row.get("vision_id") == selected_id
        ),
        None,
    )
    return {
        "vision_genesis_id": record.get("vision_genesis_id"),
        "vision_context_fingerprint": record.get("context_fingerprint", ""),
        "product_ground_truth_fingerprint": record.get(
            "product_ground_truth_fingerprint", ""
        ),
        "requirement_gate_passed": bool(
            record.get("requirement_gate", {}).get("passed")
        ),
        "selected_world": world,
        "vision_brief": record.get("judgment", {}).get("vision_brief", ""),
        "founder_prompt": record.get("judgment", {}).get("founder_prompt", ""),
        "assumptions": record.get("judgment", {}).get("assumptions", []),
        "falsifiers": record.get("judgment", {}).get("falsifiers", []),
        "investment_judgment": record.get("investment_judgment", {}),
        "investment_envelope": record.get("investment_envelope", {}),
        "delivery_authority_granted": False,
    }
