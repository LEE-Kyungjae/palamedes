#!/usr/bin/env python3
import io
import json
import os
import tempfile
import unittest
from argparse import Namespace
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

import palamedes_chat
import palamedes
from palamedes_invention import ProductInventionStore


class FakePalamedes:
    def __init__(self, root: Path) -> None:
        self.ROOT = root
        self.STATE_DIR = root / ".palamedes"

    def ensure_state(self) -> None:
        self.STATE_DIR.mkdir(parents=True, exist_ok=True)

    def load_plan(self):
        return {
            "goal": "Find the next worthwhile mission",
            "success_metric": "",
            "selected_option": "",
            "constraints": ["plan-only"],
            "hypothesis_log": [],
            "view_transitions": [],
            "open_questions": [],
            "development_probes": [],
        }


class StaticChatProvider:
    provider_name = "static"
    model = "fixture"
    scout_prompts = [
        (
            "Turn each ordinary session into a rule seed that another participant must "
            "transform under one preserved constraint, so play becomes a chain of causal "
            "inheritance rather than isolated completion. Let anticipation, surprise, and "
            "recognition of an earlier contribution power return behavior, with reversible "
            "forks and visible provenance preventing ownership conflict or harmful capture."
        ),
        (
            "Let recurring activity gradually compose a private-to-public identity artifact "
            "whose meaning comes from remembered choices rather than points. Users decide "
            "which fragments to reveal, reinterpret, or let fade; return behavior comes from "
            "recognizing how the artifact has changed and how trusted others read it. Keep "
            "silence, deletion, consent, and non-participation as first-class boundaries."
        ),
        (
            "Create temporary commons around neglected parts of the service: small groups "
            "receive limited stewardship, must make one consequential change, publish why, "
            "and relinquish control. The emotional loop joins responsibility, disagreement, "
            "loss, and later pride when a successor revives or overturns the work. Rotation, "
            "forks, appeal, and hard labor caps prevent permanent elites and coerced upkeep."
        ),
    ]

    def __init__(self) -> None:
        self.calls = []

    def stream(self, messages):
        self.calls.append(messages)
        prompt = messages[-1]["content"]
        if prompt.startswith("ROLE: vision_scout_originator"):
            context = prompt.split("Product context:\n", 1)[-1].strip()
            source_quote = context.split(".", 1)[0].strip() + "."
            yield json.dumps(
                {
                    "context_requirements": [
                        {
                            "requirement_id": "req-1",
                            "source_anchor_id": "anchor-1",
                            "source_quote": source_quote,
                            "requirement": "Originate a durable product direction.",
                            "criticality": "core",
                        }
                    ],
                    "candidates": [
                        {
                            "candidate_id": f"candidate-{index}",
                            "causal_lane": lane,
                            "founder_prompt": self.scout_prompts[index - 1],
                            "human_tension": f"human tension {index}",
                            "unsupplied_mechanism": f"unsupplied mechanism {index}",
                            "affective_loop": f"affective loop {index}",
                            "durable_expansion_engine": f"durable engine {index}",
                            "harm_boundary": f"harm boundary {index}",
                            "smallest_disconfirming_probe": f"manual probe {index}",
                        }
                        for index, lane in enumerate(
                            [
                                "rules_interaction",
                                "meaning_identity",
                                "resources_institutions_social",
                            ],
                            start=1,
                        )
                    ],
                }
            )
            return
        if prompt.startswith("ROLE: vision_scout_critic"):
            yield json.dumps(
                {
                    "critiques": [
                        {
                            "candidate_id": f"candidate-{index}",
                            "problem_reframing": f"reframing {index}",
                            "mechanism_originality": f"originality {index}",
                            "affective_truth": f"affect {index}",
                            "world_seed": f"world {index}",
                            "context_fit": f"fit {index}",
                            "cost_or_harm_risk": f"risk {index}",
                            "verdict": "advance" if index == 2 else "reject",
                        }
                        for index in range(1, 4)
                    ],
                    "decision": "select",
                    "selected_candidate_id": "candidate-2",
                    "selected_founder_prompt": self.scout_prompts[1],
                    "selection_reason": "It creates identity meaning without a feature list.",
                    "requirement_coverage": [
                        {
                            "requirement_id": "req-1",
                            "status": "satisfied",
                            "evidence": "The prompt originates a durable direction.",
                        }
                    ],
                    "assumptions": ["Users value an evolving identity artifact."],
                    "falsifiers": ["Users call it a decorative activity summary."],
                    "delivery_authority_granted": False,
                }
            )
            return
        if prompt.startswith("ROLE: vision_scout_governor"):
            yield json.dumps(
                {
                    "alternatives": [
                        {
                            "alternative": name,
                            "estimated_next_provider_calls": calls,
                            "learning_value": f"learning {name}",
                            "opportunity_cost": f"cost {name}",
                            "failure_mode": f"failure {name}",
                        }
                        for name, calls in [
                            ("discard", 0),
                            ("blind_human_review", 0),
                            ("full_genesis", 7),
                        ]
                    ],
                    "decision": "blind_human_review",
                    "decision_rationale": "Human review is cheaper than full Genesis.",
                    "full_genesis_renewal_evidence": [
                        "Independent reviewers prefer or tie the scout prompt."
                    ],
                    "kill_criteria": ["Reviewers find it generic."],
                    "delivery_authority_granted": False,
                }
            )
            return
        if prompt.startswith("ROLE: vision_agenda_architect"):
            if "Condition: conventional" in prompt:
                question_modes = ["conventional"] * 4
            elif "Condition: frontier" in prompt:
                question_modes = ["frontier"] * 4
            else:
                question_modes = [
                    "frontier", "conventional", "bridge", "frontier"
                ]
            territories = [
                ["pilgrimage", "improvisational theatre", "mutual aid"],
                ["ecological succession", "oral history", "gift economies"],
                ["competitive cooking", "constitutional design", "fashion subcultures"],
                ["restorative justice", "folk ritual", "experimental music"],
            ]
            yield json.dumps(
                {
                    "questions": [
                        {
                            "question_id": f"question-{index}",
                            "question_mode": question_modes[index - 1],
                            "self_authored_research_prompt": (
                                f"What product world emerges if ordinary use becomes "
                                f"a consequential practice rather than a completed task {index}?"
                            ),
                            "assumption_reversed": (
                                f"Users need an explicit feature request before meaning {index}."
                            ),
                            "human_behavior_to_explain": (
                                f"Why people voluntarily retell and revisit charged events {index}."
                            ),
                            "why_the_obvious_question_is_too_small": (
                                "It would optimize an existing screen instead of originating a world."
                            ),
                            "search_territories": territory_set,
                            "forbidden_default_answers": [
                                "badges and points",
                                "another feed or leaderboard",
                            ],
                            "disconfirming_observation": (
                                f"People cannot distinguish the proposal from generic rewards {index}."
                            ),
                        }
                        for index, territory_set in enumerate(territories, 1)
                    ],
                    "selected_question_ids": ["question-1", "question-2"],
                    "selection_reason": (
                        "They expose different human tensions and six distant territories."
                    ),
                    "agenda_is_advisory": True,
                }
            )
            return
        if prompt.startswith("ROLE: desire_interpreter"):
            context_text = prompt.rsplit("Context:\n", 1)[-1].strip()
            source_quote = context_text.splitlines()[0]
            yield json.dumps(
                {
                    "latent_desires": [
                        {
                            "desire_id": f"desire-{index}",
                            "human_state_before": f"unresolved state {index}",
                            "sought_or_charged_state": f"charged state {index}",
                            "affect_source": ["direct", "mediated", "social", "instrumental"][index - 1],
                            "valence": ["positive", "negative", "mixed", "mixed"][index - 1],
                            "behavioral_energy": f"return or share because of tension {index}",
                            "evidence_or_assumption": "bounded product context, interpreted as a hypothesis",
                            "harm_boundary": f"do not exploit vulnerable behavior {index}",
                        }
                        for index in range(1, 5)
                    ],
                    "unspoken_questions": [
                        "What becomes meaningful?",
                        "What becomes ownable?",
                        "What creates return tension?",
                    ],
                    "explicit_context_requirements": [
                        {
                            "requirement_id": "req-1",
                            "requirement": "Originate a durable product world.",
                            "source_quote": source_quote,
                            "kind": "objective",
                            "criticality": "core",
                        }
                    ],
                }
            )
            return
        if prompt.startswith("ROLE: distant_analogy_explorer"):
            domains = ["museum", "ritual", "trading", "pilgrimage", "theatre", "ecology"]
            yield json.dumps(
                {
                    "analogies": [
                        {
                            "analogy_id": f"analogy-{index}",
                            "source_domain": domain,
                            "source_pattern": f"pattern from {domain}",
                            "transferable_mechanism": f"mechanism {index}",
                            "target_tension": f"tension {index}",
                            "related_desire_ids": [f"desire-{(index - 1) % 4 + 1}"],
                            "distance_reason": "It is outside adjacent software features.",
                            "misuse_risk": "A shallow copy would become decorative gamification.",
                        }
                        for index, domain in enumerate(domains, 1)
                    ]
                }
            )
            return
        if prompt.startswith("ROLE: mechanism_fusion_inventor"):
            yield json.dumps(
                {
                    "fusions": [
                        {
                            "fusion_id": f"fusion-{index}",
                            "analogy_ids": [f"analogy-{index}", f"analogy-{index % 6 + 1}"],
                            "mechanism": f"collision mechanism {index}",
                            "new_user_behavior": f"new repeated behavior {index}",
                            "emotional_tension": f"mixed emotional tension {index}",
                            "why_not_an_adjacent_feature": "It changes the meaning of ordinary actions.",
                            "conceptual_distance": 65 + index,
                            "smallest_reality_probe": f"paper probe {index}",
                        }
                        for index in range(1, 6)
                    ]
                }
            )
            return
        if prompt.startswith("ROLE: product_world_builder"):
            yield json.dumps(
                {
                    "worlds": [
                        {
                            "vision_id": f"vision-{index}",
                            "title": ["Hidden cultural atlas", "Rule collision arena", "Social memory ritual"][index - 1],
                            "causal_lane": [
                                "meaning_identity",
                                "rules_interaction",
                                "resources_institutions_social",
                            ][index - 1],
                            "premise": f"A product world premise {index}",
                            "fusion_ids": [f"fusion-{index}"],
                            "central_human_tension": f"Human tension {index}",
                            "experience_loop": ["ordinary action", "hidden threshold", "surprise", "lasting meaning", "return curiosity"],
                            "identity_expression": f"identity expression {index}",
                            "social_dynamics": f"social consequence {index}",
                            "content_or_rule_engine": f"generative engine {index}",
                            "three_year_generativity": f"new worlds keep branching for theme {index}",
                            "why_users_would_tell_someone": f"a surprising story {index}",
                            "why_this_is_not_a_feature_pack": "The loop changes why the whole service is revisited.",
                            "counterfactual_without_it": "The service remains a set of isolated utilities.",
                            "harm_and_exploitation_risks": ["Do not convert curiosity into coercive compulsion."],
                            "first_probe": f"Test whether five users retell world {index} unaided.",
                        }
                        for index in range(1, 4)
                    ]
                }
            )
            return
        if prompt.startswith("ROLE: maniac_critic_and_vision_author"):
            yield json.dumps(
                {
                    "critiques": [
                        {
                            "vision_id": f"vision-{index}",
                            "genericity_failure": "Reject if it collapses into badges and a checklist.",
                            "mechanism_depth": f"mechanism depth {index}",
                            "fan_depth": f"interpretive fan depth {index}",
                            "emotional_truth": f"emotional truth {index}",
                            "economic_or_scale_risk": f"scale risk {index}",
                            "portfolio_difference": f"distinct frontier {index}",
                            "verdict": "advance" if index == 1 else "incubate",
                        }
                        for index in range(1, 4)
                    ],
                    "decision": "select",
                    "selected_vision_id": "vision-1",
                    "selection_reason": "It turns existing behavior into a service-wide world rather than another game feature.",
                    "vision_brief": (
                        "Create a hidden cultural atlas across the service. Ordinary actions sometimes satisfy undisclosed, fair conditions and reveal a lasting artifact rather than a disposable badge. Each artifact combines visual, sound, or motion with a sourced cultural interpretation, enters a browsable collection, and can become part of the user's public identity. The loop moves from action to surprise, from surprise to meaning, from meaning to ownership, and from ownership to curiosity about what remains unseen. Communities may compare interpretations and discovery stories without exposing exact conditions. Begin with a paper prototype of twelve discoveries and test whether users can recall, retell, and voluntarily seek another discovery before building a production reward engine."
                    ),
                    "founder_prompt": (
                        "Turn ordinary service behavior into occasional hidden discoveries "
                        "that carry lasting cultural meaning rather than disposable points. "
                        "Let each discovery become a collectible part of the user's identity, "
                        "combine visual or audible interpretation with carefully sourced human "
                        "stories, and make curiosity about what remains unseen the reason to "
                        "return. Design the system so people can remember and retell discoveries "
                        "without exposing exact conditions or turning surprise into coercion."
                    ),
                    "requirement_coverage": [
                        {
                            "requirement_id": "req-1",
                            "status": "satisfied",
                            "evidence": "The selected world defines a durable loop.",
                        }
                    ],
                    "originality_case": "It fuses museums, hidden rituals, and identity systems into one service-wide meta-world.",
                    "assumptions": ["Surprise remains fair when conditions are hidden."],
                    "falsifiers": ["Users describe it only as another achievement list."],
                    "delivery_authority_granted": False,
                }
            )
            return
        if prompt.startswith("ROLE: blind_vision_judge"):
            yield json.dumps(
                {
                    "scores": {
                        "origination": 82,
                        "conceptual_distance": 76,
                        "affective_depth": 78,
                        "mechanism_fusion": 74,
                        "world_coherence": 81,
                        "three_year_generativity": 79,
                        "human_approval_value": 80,
                    },
                    "reference_relation": "different_peer",
                    "generic_feature_pack": False,
                    "core_requirements_satisfied": True,
                    "unmet_core_requirements": [],
                    "decisive_strength": "It originates a service-wide meaning loop.",
                    "decisive_weakness": "The first probe still needs real users.",
                    "would_human_likely_approve_exploration": True,
                    "rationale": "The generated world is independently coherent and testable.",
                }
            )
            return
        if prompt.startswith("ROLE: blind_founder_prompt_judge"):
            yield json.dumps(
                {
                    "scores": {
                        "problem_reframing": 84,
                        "unsupplied_mechanism": 86,
                        "affective_thesis": 82,
                        "product_world_seed": 85,
                        "human_prompt_substitutability": 83,
                    },
                    "reference_relation": "different_peer",
                    "solution_was_present_in_input": False,
                    "generic_request": False,
                    "decisive_difference": (
                        "The generated prompt independently proposes a durable discovery world."
                    ),
                    "rationale": (
                        "It could initiate exploration without the human reference's solution."
                    ),
                }
            )
            return
        if prompt.startswith("ROLE: blind_agenda_ablation_judge"):
            scores = {
                "origination": 80,
                "conceptual_distance": 78,
                "affective_depth": 79,
                "mechanism_fusion": 77,
                "world_coherence": 81,
                "three_year_generativity": 80,
                "human_approval_value": 79,
            }
            yield json.dumps(
                {
                    "preferred": "peer",
                    "scores_A": scores,
                    "scores_B": scores,
                    "decisive_difference": "The fixture intentionally ties both conditions.",
                    "rationale": "Equal fixture briefs establish blind plumbing, not advantage.",
                }
            )
            return
        if prompt.startswith("ROLE: vision_reality_governor"):
            alternatives = [
                "full_build", "minimal_probe", "manual_probe", "reuse_or_buy",
                "do_nothing", "alternative_opportunity",
            ]
            yield json.dumps(
                {
                    "evidence_maturity": "speculative",
                    "alternatives": [
                        {
                            "alternative": name,
                            "learning_value": f"learning from {name}",
                            "engineering_days_low": 0 if name == "do_nothing" else 1,
                            "engineering_days_high": 0 if name == "do_nothing" else 5,
                            "ai_cost_low": 0,
                            "ai_cost_high": 10,
                            "monthly_infrastructure_low": 0,
                            "monthly_infrastructure_high": 10,
                            "maintenance_burden": f"burden of {name}",
                            "reversibility": "high" if name != "full_build" else "low",
                            "opportunity_cost": f"foregone option for {name}",
                            "failure_mode": f"failure of {name}",
                        }
                        for name in alternatives
                    ],
                    "decision": "probe",
                    "selected_alternative": "manual_probe",
                    "decision_rationale": "Test retelling and return desire before software investment.",
                    "renewal_evidence": ["Users voluntarily seek a second discovery."],
                    "kill_criteria": ["Users describe the world only as decorative badges."],
                    "debt_guard": "No persistent production schema before the probe passes.",
                    "scale_guard": "Run with five people and no new infrastructure.",
                    "delivery_authority_granted": False,
                }
            )
            return
        if "ROLE: interpreter" in prompt:
            yield json.dumps(
                {
                    "observations": ["The current product claim needs external proof"],
                    "interpretations": [
                        {
                            "interpretation_id": "frame-1",
                            "frame": "The missing proof is causal",
                            "mechanism": "Compare action choices",
                            "would_lose_if": "Prose ratings predict outcomes",
                        },
                        {
                            "interpretation_id": "frame-2",
                            "frame": "The missing proof is operational",
                            "mechanism": "Measure retired human labor",
                            "would_lose_if": "No labor is retired",
                        },
                    ],
                    "tensions": ["Quality and autonomy may diverge"],
                    "missing_evidence": ["Equal-budget outcome comparison"],
                }
            )
            return
        if "ROLE: context_governor" in prompt:
            yield json.dumps(
                {
                    "hard_requirements": ["Originate a worthwhile mission"],
                    "success_criteria": ["Produce a falsifiable outcome test"],
                    "constraints": ["Remain plan-only"],
                    "autonomous_decisions": ["Mission mechanism"],
                    "observations": ["The current product claim needs proof"],
                    "preferences": [],
                    "reference_examples": [],
                    "ambiguous_authority": [],
                }
            )
            return
        if prompt.startswith("ROLE: clean_room_ablation_arm"):
            yield json.dumps(
                {
                    "problem_frame": "The product needs a new strategic mechanism",
                    "causal_mechanism": "Independent exploration changes user behavior",
                    "mission_family": "strategic discovery probe",
                    "decision_level": "strategic",
                    "next_discriminating_probe": "Run a clean-room user test",
                    "path_assumptions": [],
                    "confidence": 60,
                }
            )
            return
        if prompt.startswith("ROLE: continuity_ablation_arm"):
            yield json.dumps(
                {
                    "problem_frame": "The selected implementation needs completion",
                    "causal_mechanism": "Closing task gaps improves delivery",
                    "mission_family": "implementation completion",
                    "decision_level": "implementation",
                    "next_discriminating_probe": "Complete the next local task",
                    "path_assumptions": ["The selected option remains correct"],
                    "confidence": 70,
                }
            )
            return
        if prompt.startswith("ROLE: blinded_ablation_judge"):
            yield json.dumps(
                {
                    "same_problem_frame": False,
                    "same_causal_mechanism": False,
                    "same_mission_family": False,
                    "material_direction_shift": True,
                    "shift_dimensions": [
                        "problem_frame",
                        "causal_mechanism",
                        "mission_family",
                        "decision_level",
                        "probe",
                    ],
                    "lower_abstraction_arm": "arm-b",
                    "rationale": "One arm preserves strategy while the other follows implementation state.",
                }
            )
            return
        if "ROLE: inventor" in prompt:
            yield json.dumps(
                {
                    "candidates": [
                        {
                            "candidate_id": f"candidate-{index}",
                            "mission": f"Test mission mechanism {index}",
                            "source_interpretation_id": "frame-1" if index < 3 else "frame-2",
                            "beneficiary": "Project owner",
                            "causal_thesis": f"Mechanism {index} improves the next action",
                            "success_metric": f"Action quality threshold {index}",
                            "early_falsifier": f"No decision change in arm {index}",
                            "next_probe": f"Run paired probe {index}",
                        }
                        for index in range(1, 4)
                    ]
                }
            )
            return
        if "ROLE: adversary" in prompt:
            yield json.dumps(
                {
                    "critiques": [
                        {
                            "candidate_id": f"candidate-{index}",
                            "fatal_risks": [f"Hidden confound {index}"],
                            "repairable_risks": ["Blind the evaluator"],
                            "disqualifying": False,
                        }
                        for index in range(1, 4)
                    ],
                    "shared_assumptions": ["The chosen metric reflects decision quality"],
                    "missing_opposition": ["A strong one-shot agent baseline"],
                    "minimum_disconfirming_probe": "Run one blinded equal-budget pair",
                    "abstraction_audit": {
                        "reasoning_level": "strategic",
                        "path_assumptions_detected": [],
                        "suspected_abstraction_drift": False,
                        "discriminating_context_ablation": (
                            "Remove the selected option and development probes"
                        ),
                    },
                }
            )
            return
        if "ROLE: selector" in prompt:
            yield json.dumps(
                {
                    "decision": "select",
                    "selected_candidate_id": "candidate-1",
                    "selection_reason": "It creates the most informative reversible comparison.",
                    "causal_role": "originated",
                    "decision_scope": "tactical_bounded",
                    "implementation_state_at_start": "not_started",
                    "selection_type": "probe",
                    "candidate_fates": [
                        {
                            "candidate_id": "candidate-1",
                            "fate": "selected",
                            "reason": "Most informative",
                            "reopen_condition": "",
                        },
                        {
                            "candidate_id": "candidate-2",
                            "fate": "deferred",
                            "reason": "Less causal",
                            "reopen_condition": "Probe one fails",
                        },
                        {
                            "candidate_id": "candidate-3",
                            "fate": "rejected",
                            "reason": "Higher cost",
                            "reopen_condition": "",
                        },
                    ],
                    "decisive_assumptions": ["Blinded review can distinguish action quality"],
                    "reversal_triggers": ["Control consistently wins"],
                    "mission_contract": self._mission_payload(),
                }
            )
            return
        if "ROLE: outcome_analyst" in prompt:
            yield json.dumps(
                {
                    "observed_vs_expected": "The traceable result matched the forecast.",
                    "attribution_hypotheses": [
                        {
                            "layer": "mission",
                            "claim": "Mission framing contributed to traceability",
                            "confidence": 60,
                        }
                    ],
                    "belief_updates": ["Approval lineage is operationally observable"],
                    "causal_signature": "approval-lineage-observed",
                    "mechanism_summary": "An approved mission produced a traceable outcome record.",
                    "work_scale": "component",
                    "surface_key": "mission-approval-lineage",
                    "finding_lane": "expected_outcome",
                    "exploration_value": 35,
                    "hypothesis_scope": "",
                    "probe_status": "completed",
                    "finding": "expected_result",
                    "mission_disposition": "continue",
                    "followup_required": False,
                    "followup_kind": "none",
                    "successor_scope": "",
                    "next_probe": "Run an equal-budget control",
                    "confidence": 60,
                }
            )
            return
        if "Required shape:" in messages[-1]["content"]:
            yield json.dumps(self._mission_payload())
            return
        yield "A falsifiable "
        yield "mission."

    @staticmethod
    def _mission_payload():
        return {
            "mission": "Prove that one mission improves the next action",
            "rationale": "The product claim currently lacks an approved vertical slice.",
            "success_metric": "One outcome is recorded against an approved mission",
            "deadline": "7 days",
            "evidence": [
                {
                    "claim": "The user requested a mission approval flow",
                    "source": "user",
                    "confidence": 90,
                }
            ],
            "hypotheses": [
                {
                    "hypothesis": "Explicit approval prevents silent authority expansion",
                    "metric": "unapproved plan mutations",
                    "target": "0",
                    "window": "one mission cycle",
                }
            ],
            "falsifiers": ["The plan changes before /approve"],
            "non_goals": ["Execute delivery tasks"],
            "constraints": ["Plan-only authority"],
            "next_probe": {
                "step": "Run one approved mission cycle",
                "expected_learning": "Whether the state transition is traceable",
                "expected_result": "One linked handoff and outcome record",
            },
            "planner_brief": "Plan the smallest traceable mission experiment.",
            "uncertainty": 35,
        }


class PalamedesIsolation:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.originals = {}

    def __enter__(self):
        for name in (
            "ROOT",
            "STATE_DIR",
            "PLAN_PATH",
            "DECISIONS_PATH",
            "RISKS_PATH",
            "EVENTS_PATH",
            "REVISIONS_PATH",
        ):
            self.originals[name] = getattr(palamedes, name)
        palamedes.ROOT = self.root
        palamedes.STATE_DIR = self.root / ".palamedes"
        palamedes.PLAN_PATH = palamedes.STATE_DIR / "plan.json"
        palamedes.DECISIONS_PATH = palamedes.STATE_DIR / "decisions.jsonl"
        palamedes.RISKS_PATH = palamedes.STATE_DIR / "risks.jsonl"
        palamedes.EVENTS_PATH = palamedes.STATE_DIR / "events.jsonl"
        palamedes.REVISIONS_PATH = palamedes.STATE_DIR / "revisions.jsonl"
        return palamedes

    def __exit__(self, exc_type, exc, tb):
        for name, value in self.originals.items():
            setattr(palamedes, name, value)


class PalamedesChatTests(unittest.TestCase):
    def test_builtin_vision_cases_keep_human_leaps_hidden_from_generators(self):
        from palamedes_vision_benchmark import BUILTIN_CASES

        self.assertGreaterEqual(len(BUILTIN_CASES), 3)
        for case in BUILTIN_CASES:
            context = case.generator_context.lower()
            self.assertFalse(
                [term for term in case.hidden_anchor_terms if term.lower() in context],
                case.case_id,
            )

    def test_vision_genesis_originates_product_world_before_mission(self):
        from palamedes_vision import VisionStore, run_vision_genesis

        provider = StaticChatProvider()
        with tempfile.TemporaryDirectory() as tempdir:
            store = VisionStore(Path(tempdir) / "visions")

            def ask(role, prompt):
                return palamedes_chat._provider_json(
                    provider,
                    system=f"ROLE: {role}",
                    prompt=f"ROLE: {role}\n{prompt}",
                )

            record = run_vision_genesis(
                ask=ask,
                store=store,
                context=(
                    "The service has several small games, profiles, media-generation "
                    "capacity, and ordinary user activity records. Increase enduring "
                    "engagement without assuming a requested feature."
                ),
            )

        self.assertEqual(record["status"], "selected")
        self.assertEqual(record["agenda_strategy"], "adaptive")
        self.assertEqual(len(record["exploration_agenda"]["questions"]), 4)
        self.assertEqual(
            record["exploration_agenda"]["selected_question_ids"],
            ["question-1", "question-2"],
        )
        self.assertTrue(record["exploration_agenda"]["agenda_is_advisory"])
        self.assertEqual(len(record["product_worlds"]["worlds"]), 3)
        self.assertGreaterEqual(
            len(record["judgment"]["vision_brief"]), 240
        )
        self.assertIn("hidden cultural atlas", record["judgment"]["vision_brief"])
        self.assertIn("hidden discoveries", record["judgment"]["founder_prompt"])
        self.assertNotIn("collection", provider.calls[0][-1]["content"].lower())
        self.assertNotIn("rule fusion", provider.calls[0][-1]["content"].lower())
        self.assertIn(
            "self_authored_research_prompt",
            provider.calls[1][-1]["content"],
        )
        self.assertFalse(record["delivery_authority_granted"])
        self.assertEqual(
            record["investment_envelope"]["max_outcomes_before_reassessment"],
            1,
        )
        self.assertEqual(
            record["investment_envelope"]["budget_exhaustion_action"],
            "regenerate_vision",
        )
        self.assertEqual(
            [call[-1]["content"].splitlines()[0] for call in provider.calls],
            [
                "ROLE: vision_agenda_architect",
                "ROLE: desire_interpreter",
                "ROLE: distant_analogy_explorer",
                "ROLE: mechanism_fusion_inventor",
                "ROLE: product_world_builder",
                "ROLE: maniac_critic_and_vision_author",
                "ROLE: vision_reality_governor",
            ],
        )

    def test_vision_scout_originates_prompt_in_three_calls_without_authority(self):
        from palamedes_vision_scout import VisionScoutStore, run_vision_scout

        provider = StaticChatProvider()
        with tempfile.TemporaryDirectory() as tempdir:
            def ask(role, prompt):
                return palamedes_chat._provider_json(
                    provider,
                    system=f"ROLE: {role}",
                    prompt=f"ROLE: {role}\n{prompt}",
                )

            record = run_vision_scout(
                ask=ask,
                store=VisionScoutStore(Path(tempdir) / "scouts"),
                context=(
                    "A service needs a durable product direction. It has profiles, "
                    "recurring activity, and several small interaction surfaces."
                ),
            )

        self.assertEqual(record["status"], "candidate_for_human_review")
        self.assertEqual(record["vision_scout_version"], "palamedes-vision-scout/6")
        self.assertEqual(record["generation_call_count"], 3)
        self.assertEqual(record["selected_founder_prompt"], provider.scout_prompts[1])
        self.assertIn(
            record["originator"]["context_requirements"][0]["source_quote"],
            (
                "A service needs a durable product direction. It has profiles, "
                "recurring activity, and several small interaction surfaces."
            ),
        )
        self.assertFalse(record["full_genesis_authorized"])
        self.assertFalse(record["delivery_authority_granted"])
        self.assertEqual(
            [call[-1]["content"].splitlines()[0] for call in provider.calls],
            [
                "ROLE: vision_scout_originator",
                "ROLE: vision_scout_critic",
                "ROLE: vision_scout_governor",
            ],
        )

    def test_vision_scout_discards_unresolved_core_before_governor_call(self):
        from palamedes_vision_scout import VisionScoutStore, run_vision_scout

        class PartialCoreProvider(StaticChatProvider):
            def stream(self, messages):
                prompt = messages[-1]["content"]
                if prompt.startswith("ROLE: vision_scout_critic"):
                    chunks = list(super().stream(messages))
                    payload = json.loads("".join(chunks))
                    payload["requirement_coverage"][0]["status"] = "partial"
                    payload["requirement_coverage"][0]["evidence"] = (
                        "The direction is promising but lacks a bounded cost ceiling."
                    )
                    yield json.dumps(payload)
                    return
                yield from super().stream(messages)

        provider = PartialCoreProvider()
        with tempfile.TemporaryDirectory() as tempdir:
            record = run_vision_scout(
                ask=lambda role, prompt: palamedes_chat._provider_json(
                    provider,
                    system=f"ROLE: {role}",
                    prompt=f"ROLE: {role}\n{prompt}",
                ),
                store=VisionScoutStore(Path(tempdir) / "scouts"),
                context="A service needs a durable direction with a bounded cost ceiling.",
            )

        self.assertEqual(len(provider.calls), 2)
        self.assertEqual(record["status"], "discarded")
        self.assertEqual(record["generation_call_count"], 2)
        self.assertEqual(record["unresolved_core_requirement_ids"], ["req-1"])
        self.assertEqual(
            record["governor"]["decision_source"],
            "deterministic_core_requirement_gate",
        )
        self.assertFalse(record["delivery_authority_granted"])

    def test_project_scout_review_packet_requires_two_strong_independent_humans(self):
        from palamedes_vision import fingerprint
        from palamedes_vision_benchmark import VisionBenchmarkStore
        from palamedes_vision_scout import PROJECT_REVIEW_AXES, VisionScoutStore

        with tempfile.TemporaryDirectory() as tempdir:
            state = Path(tempdir) / ".palamedes"
            scout_store = VisionScoutStore(state / "vision-scouts")
            scout_id = "vision-scout-abcdef123456"
            scout_store.save(
                {
                    "vision_scout_id": scout_id,
                    "status": "candidate_for_human_review",
                    "selected_founder_prompt": StaticChatProvider.scout_prompts[1],
                }
            )
            packet = scout_store.ensure_project_review_packet(scout_id)
            self.assertIsNotNone(packet)
            packet_id = packet["vision_scout_project_review_id"]
            packet_fingerprint = fingerprint(packet)

            def submit(reviewer_id, kind, relationship, recommendation="advance", score=80):
                return scout_store.submit_project_review(
                    packet_id,
                    {
                        "packet_fingerprint": packet_fingerprint,
                        "reviewer_id": reviewer_id,
                        "reviewer_kind": kind,
                        "reviewer_relationship": relationship,
                        "recommendation": recommendation,
                        "scores": {axis: score for axis in PROJECT_REVIEW_AXES},
                        "confidence": 80,
                        "rationale": "This originates a consequential world with bounded risk.",
                    },
                )

            submit("model-1", "model", "independent")
            submit("team-1", "human", "team")
            blocked = VisionBenchmarkStore(state / "vision-benchmarks").scout_promotion_gate(scout_id)
            submit("human-1", "human", "independent")
            still_blocked = VisionBenchmarkStore(state / "vision-benchmarks").scout_promotion_gate(scout_id)
            submit("human-2", "human", "independent")
            passed = VisionBenchmarkStore(state / "vision-benchmarks").scout_promotion_gate(scout_id)

        self.assertFalse(blocked["passed"])
        self.assertFalse(still_blocked["passed"])
        self.assertTrue(passed["human_review_path_passed"])
        self.assertTrue(passed["full_genesis_authorized"])
        self.assertFalse(passed["delivery_authority_granted"])

    def test_autonomous_scout_is_idempotent_for_identical_project_context(self):
        provider = StaticChatProvider()
        context = (
            "A service needs a durable product direction. It has profiles, recurring "
            "activity, and several small interaction surfaces."
        )
        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            mission_store = palamedes_chat.MissionStore(
                fake.STATE_DIR / "missions"
            )
            first = palamedes_chat.run_autonomous_vision_scout(
                provider=provider,
                mission_store=mission_store,
                context=context,
            )
            second = palamedes_chat.run_autonomous_vision_scout(
                provider=provider,
                mission_store=mission_store,
                context=context,
            )
            from palamedes_vision_scout import VisionScoutStore
            private_context = VisionScoutStore(
                fake.STATE_DIR / "vision-scouts"
            ).load_context(first["vision_scout_id"])

        self.assertEqual(first["vision_scout_id"], second["vision_scout_id"])
        self.assertEqual(len(provider.calls), 3)
        self.assertTrue(second["reused_existing_context"])
        self.assertEqual(first["provider_usage"]["attempted_calls"], 3)
        self.assertFalse(first["full_genesis_authorized"])
        self.assertFalse(first["delivery_authority_granted"])
        self.assertEqual(private_context, context)

    def test_project_scout_does_not_reuse_same_request_from_older_version(self):
        from palamedes_vision import fingerprint
        from palamedes_vision_scout import VisionScoutStore

        provider = StaticChatProvider()
        context = "A service needs a durable product direction."
        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            scout_store = VisionScoutStore(fake.STATE_DIR / "vision-scouts")
            scout_store.save(
                {
                    "vision_scout_id": "vision-scout-aaaaaaaaaaaa",
                    "vision_scout_version": "palamedes-vision-scout/3",
                    "request_fingerprint": fingerprint(context),
                    "context_fingerprint": fingerprint("older context"),
                }
            )
            record = palamedes_chat.run_autonomous_vision_scout(
                provider=provider,
                mission_store=palamedes_chat.MissionStore(
                    fake.STATE_DIR / "missions"
                ),
                context=context,
                request_context=context,
            )

        self.assertEqual(record["vision_scout_version"], "palamedes-vision-scout/6")
        self.assertEqual(len(provider.calls), 3)

    def test_project_scout_context_compaction_bounds_document_excerpts(self):
        contract = {
            "vision_context_version": "palamedes-vision-context/1",
            "user_context": "Originate a durable product direction.",
            "product_ground_truth": {"purpose": "Improve upstream decisions."},
            "bounded_workspace_context": {
                "observation_id": "ephemeral-observation",
                "observed_at": "future-time",
                "documents": [
                    {
                        "path": f"docs/{index}.md",
                        "content_sha256": f"sha-{index}",
                        "headings": ["Purpose", "Evidence"],
                        "excerpt": "x" * 8000,
                    }
                    for index in range(12)
                ],
                "git": {
                    "available": True,
                    "branch": "main",
                    "head": "abc",
                    "recent_commits": ["one"],
                    "status": ["M README.md"],
                    "diff_stat": ["README.md | 1 +"],
                },
                "palamedes_state": {
                    "events": {"size_bytes": 999999},
                    "plan": {"summary": {"goal": "Retire owner judgment."}},
                },
                "todos": {"items": ["verify cost"], "truncated": False},
                "reference_root": {"available": True},
                "test": {"executed": False},
            },
        }
        raw = json.dumps(contract)
        compact = palamedes_chat.compact_vision_scout_context(raw)
        payload = json.loads(compact)

        self.assertLess(len(compact), 10000)
        self.assertEqual(payload["user_context"], contract["user_context"])
        self.assertEqual(
            payload["bounded_workspace_context"]["palamedes_plan_summary"]["goal"],
            "Retire owner judgment.",
        )
        self.assertEqual(
            len(payload["bounded_workspace_context"]["documents"][0]["excerpt"]),
            320,
        )
        self.assertNotIn("observation_id", payload["bounded_workspace_context"])
        self.assertNotIn("events", payload["bounded_workspace_context"])

    def test_project_scout_failure_is_metered_and_consumes_one_shot_attempt(self):
        class MalformedScoutProvider:
            provider_name = "fixture"
            model = "malformed-scout"

            def __init__(self):
                self.calls = 0
                self.last_usage = None
                self.last_json_custody = None

            def stream(self, messages):
                self.calls += 1
                self.last_usage = {"input_tokens": 50, "output_tokens": 5}
                yield '{"context_requirements": [] "broken": true}'

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            provider = MalformedScoutProvider()
            mission_store = palamedes_chat.MissionStore(
                fake.STATE_DIR / "missions"
            )
            context = "A service needs a durable product direction."
            with self.assertRaises(ValueError):
                palamedes_chat.run_autonomous_vision_scout(
                    provider=provider,
                    mission_store=mission_store,
                    context=context,
                    request_context=context,
                )
            with self.assertRaisesRegex(ValueError, "trial budget exhausted"):
                palamedes_chat.run_autonomous_vision_scout(
                    provider=provider,
                    mission_store=mission_store,
                    context=context,
                    request_context=context,
                )
            from palamedes_vision_scout import VisionScoutStore

            attempts = VisionScoutStore(
                fake.STATE_DIR / "vision-scouts"
            ).project_attempts()

        self.assertEqual(provider.calls, 1)
        self.assertEqual([row["status"] for row in attempts], ["started", "failed"])
        self.assertEqual(attempts[-1]["provider_usage"]["attempted_calls"], 1)
        self.assertEqual(attempts[-1]["provider_usage"]["totals"]["total_tokens"], 55)

    def test_project_scout_resumes_runtime_failure_from_immutable_role_checkpoints(self):
        class GovernorFailsOnceProvider(StaticChatProvider):
            def __init__(self):
                super().__init__()
                self.failed_governor = False

            def stream(self, messages):
                prompt = messages[-1]["content"]
                if (
                    prompt.startswith("ROLE: vision_scout_governor")
                    and not self.failed_governor
                ):
                    self.calls.append(messages)
                    self.failed_governor = True
                    raise RuntimeError("transient provider process failure")
                yield from super().stream(messages)

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            provider = GovernorFailsOnceProvider()
            mission_store = palamedes_chat.MissionStore(
                fake.STATE_DIR / "missions"
            )
            context = "A service needs a durable product direction."
            with self.assertRaisesRegex(RuntimeError, "transient provider"):
                palamedes_chat.run_autonomous_vision_scout(
                    provider=provider,
                    mission_store=mission_store,
                    context=context,
                    request_context=context,
                )
            record = palamedes_chat.run_autonomous_vision_scout(
                provider=provider,
                mission_store=mission_store,
                context=context,
                request_context=context,
            )
            from palamedes_vision_scout import VisionScoutStore

            store = VisionScoutStore(fake.STATE_DIR / "vision-scouts")
            attempts = store.project_attempts()
            checkpoint = store.project_checkpoint(attempts[0]["attempt_id"])

        self.assertEqual(len(provider.calls), 4)
        self.assertEqual(
            [row["status"] for row in attempts],
            ["started", "failed", "resumed", "completed"],
        )
        self.assertEqual(
            set(checkpoint["roles"]),
            {
                "vision_scout_originator",
                "vision_scout_critic",
                "vision_scout_governor",
            },
        )
        self.assertTrue(
            record["provider_usage"]["roles"][0]["checkpoint_reused"]
        )
        self.assertTrue(
            record["provider_usage"]["roles"][1]["checkpoint_reused"]
        )

    def test_scout_source_quote_allows_only_whitespace_normalization(self):
        from palamedes_vision_scout import _source_quote_present

        context = "A durable product\n direction must remain attributable."
        self.assertTrue(
            _source_quote_present(
                "A durable product direction must remain attributable.", context
            )
        )
        self.assertFalse(
            _source_quote_present("A rewritten strategic requirement.", context)
        )

    def test_scout_rejects_model_invented_source_anchor_id(self):
        from palamedes_vision_scout import VisionScoutStore, run_vision_scout

        class InventedAnchorProvider(StaticChatProvider):
            def stream(self, messages):
                prompt = messages[-1]["content"]
                if prompt.startswith("ROLE: vision_scout_originator"):
                    raw = "".join(super().stream(messages))
                    payload = json.loads(raw)
                    payload["context_requirements"][0]["source_anchor_id"] = (
                        "anchor-999"
                    )
                    yield json.dumps(payload)
                    return
                yield from super().stream(messages)

        provider = InventedAnchorProvider()
        with tempfile.TemporaryDirectory() as tempdir:
            with self.assertRaisesRegex(ValueError, "source anchor is invalid"):
                run_vision_scout(
                    ask=lambda role, prompt: palamedes_chat._provider_json(
                        provider,
                        system=f"ROLE: {role}",
                        prompt=f"ROLE: {role}\n{prompt}",
                    ),
                    store=VisionScoutStore(Path(tempdir) / "scouts"),
                    context="A service needs a durable product direction.",
                )

    def test_blind_scout_benchmark_uses_three_generation_calls_and_one_judge(self):
        from palamedes_vision_benchmark import (
            VisionBenchmarkCase,
            VisionBenchmarkStore,
            run_blind_scout_case,
        )
        from palamedes_vision_scout import VisionScoutStore

        provider = StaticChatProvider()
        case = VisionBenchmarkCase(
            case_id="scout-fixture",
            generator_context=(
                "A service needs a durable product direction. It has profiles, "
                "recurring activity, and several small interaction surfaces."
            ),
            hidden_human_reference=(
                "Create a hidden collection whose discoveries become profile identity "
                "and whose meaning expands through carefully sourced cultural stories."
            ),
            hidden_anchor_terms=["hidden collection", "cultural stories"],
        )
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)

            def ask(role, prompt):
                return palamedes_chat._provider_json(
                    provider,
                    system=f"ROLE: {role}",
                    prompt=f"ROLE: {role}\n{prompt}",
                )

            record = run_blind_scout_case(
                case=case,
                ask=ask,
                scout_store=VisionScoutStore(root / "scouts"),
                benchmark_store=VisionBenchmarkStore(root / "benchmarks"),
                generator_identity="static:same",
                judge_identity="static:same",
                usage_report=lambda: {
                    "generator": {"attempted_calls": 3},
                    "judge": {"attempted_calls": 1},
                    "attempted_calls": 4,
                    "metered_calls": 0,
                    "unmetered_calls": 4,
                },
            )

            packet = json.loads(
                next((root / "benchmarks" / "human-review").glob("*.json"))
                .read_text(encoding="utf-8")
            )
            stored = json.loads(
                next(
                    (root / "benchmarks" / "scout-benchmarks").glob("*.json")
                ).read_text(encoding="utf-8")
            )
            call_count = len(provider.calls)
            with self.assertRaisesRegex(ValueError, "trial budget exhausted"):
                run_blind_scout_case(
                    case=case,
                    ask=ask,
                    scout_store=VisionScoutStore(root / "scouts-retry"),
                    benchmark_store=VisionBenchmarkStore(root / "benchmarks"),
                )

        self.assertTrue(record["passed"])
        self.assertEqual(record["scout_generation_call_count"], 3)
        self.assertEqual(record["judge_call_count"], 1)
        self.assertEqual(record["provider_usage"]["attempted_calls"], 4)
        self.assertFalse(record["full_genesis_authorized"])
        self.assertFalse(record["delivery_authority_granted"])
        self.assertEqual(record["next_authorized_step"], "blind_human_review")
        self.assertEqual(packet["source_artifact_type"], "vision_scout")
        self.assertEqual(packet["source_artifact_id"], record["vision_scout_id"])
        self.assertEqual(stored, record)
        self.assertEqual(len(provider.calls), call_count)
        self.assertEqual(
            [call[-1]["content"].splitlines()[0] for call in provider.calls],
            [
                "ROLE: vision_scout_originator",
                "ROLE: vision_scout_critic",
                "ROLE: vision_scout_governor",
                "ROLE: blind_founder_prompt_judge",
            ],
        )

    def test_failed_scout_call_consumes_the_preregistered_attempt(self):
        from palamedes_vision_benchmark import (
            VisionBenchmarkCase,
            VisionBenchmarkStore,
            run_blind_scout_case,
        )
        from palamedes_vision_scout import VisionScoutStore

        case = VisionBenchmarkCase(
            case_id="failed-scout",
            generator_context="A service needs a durable product direction.",
            hidden_human_reference="A hidden human direction.",
            hidden_anchor_terms=["hidden human direction"],
        )
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            store = VisionBenchmarkStore(root / "benchmarks")

            def fail(role, prompt):
                raise RuntimeError("malformed provider response")

            with self.assertRaisesRegex(RuntimeError, "malformed provider"):
                run_blind_scout_case(
                    case=case,
                    ask=fail,
                    scout_store=VisionScoutStore(root / "scouts"),
                    benchmark_store=store,
                )
            with self.assertRaisesRegex(ValueError, "trial budget exhausted"):
                run_blind_scout_case(
                    case=case,
                    ask=fail,
                    scout_store=VisionScoutStore(root / "scouts-retry"),
                    benchmark_store=store,
                )
            attempts = store.scout_attempts()

        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0]["status"], "started")

    def test_scout_promotion_requires_two_independent_humans_and_runs_once(self):
        from palamedes_vision import fingerprint
        from palamedes_vision_benchmark import (
            VisionBenchmarkCase,
            VisionBenchmarkStore,
            run_blind_scout_case,
        )
        from palamedes_vision_scout import VisionScoutStore

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            provider = StaticChatProvider()
            benchmark_store = VisionBenchmarkStore(
                fake.STATE_DIR / "vision-benchmarks"
            )
            scout_store = VisionScoutStore(fake.STATE_DIR / "vision-scouts")
            case = VisionBenchmarkCase(
                case_id="promotion-fixture",
                generator_context=(
                    "A service needs a durable product direction. It has profiles "
                    "and recurring activity."
                ),
                hidden_human_reference="A hidden collection becomes profile identity.",
                hidden_anchor_terms=["hidden collection"],
            )

            def ask(role, prompt):
                return palamedes_chat._provider_json(
                    provider,
                    system=f"ROLE: {role}",
                    prompt=f"ROLE: {role}\n{prompt}",
                )

            benchmark = run_blind_scout_case(
                case=case,
                ask=ask,
                scout_store=scout_store,
                benchmark_store=benchmark_store,
            )
            scout_id = benchmark["vision_scout_id"]
            blocked = benchmark_store.scout_promotion_gate(scout_id)
            self.assertFalse(blocked["passed"])
            packet_id = benchmark["human_review_packet_id"]
            packet_path = (
                fake.STATE_DIR
                / "vision-benchmarks"
                / "human-review"
                / f"{packet_id}.json"
            )
            key_path = (
                fake.STATE_DIR
                / "vision-benchmarks"
                / "answer-keys"
                / f"{packet_id}.json"
            )
            packet = json.loads(packet_path.read_text(encoding="utf-8"))
            key = json.loads(key_path.read_text(encoding="utf-8"))
            scores = {axis: 82 for axis in packet["axes"]}
            reference_scores = {axis: 80 for axis in packet["axes"]}
            for reviewer_id, reviewer_kind, relationship in (
                ("model-reviewer", "model", "independent"),
                ("team-reviewer", "human", "team"),
            ):
                benchmark_store.submit_human_review(
                    packet_id,
                    {
                        "reviewer_id": reviewer_id,
                        "reviewer_kind": reviewer_kind,
                        "reviewer_relationship": relationship,
                        "packet_fingerprint": fingerprint(packet),
                        "preferred": key["generated_label"],
                        "scores_A": scores,
                        "scores_B": reference_scores,
                        "rationale": "This non-independent review cannot promote.",
                        "confidence": 95,
                    },
                )
            still_blocked = benchmark_store.scout_promotion_gate(scout_id)
            self.assertFalse(still_blocked["passed"])
            self.assertEqual(still_blocked["qualifying_review_count"], 0)
            for reviewer_id in ("independent-one", "independent-two"):
                benchmark_store.submit_human_review(
                    packet_id,
                    {
                        "reviewer_id": reviewer_id,
                        "reviewer_kind": "human",
                        "reviewer_relationship": "independent",
                        "packet_fingerprint": fingerprint(packet),
                        "preferred": key["generated_label"],
                        "scores_A": (
                            scores
                            if key["generated_label"] == "A"
                            else reference_scores
                        ),
                        "scores_B": (
                            scores
                            if key["generated_label"] == "B"
                            else reference_scores
                        ),
                        "rationale": "The generated prompt is independently actionable.",
                        "confidence": 80,
                    },
                )
            passed = benchmark_store.scout_promotion_gate(scout_id)
            calls_before_promotion = len(provider.calls)
            output = io.StringIO()
            palamedes_chat.run_chat(
                palamedes_module=fake,
                provider=provider,
                session_id="promote-scout",
                input_stream=io.StringIO(
                    f"/vision-scout-promote {scout_id}\n"
                    f"/vision-scout-promote {scout_id}\n/quit\n"
                ),
                output=output,
            )
            promotions = list(
                (
                    fake.STATE_DIR
                    / "vision-benchmarks"
                    / "scout-promotions"
                ).glob("*.json")
            )

        self.assertTrue(passed["passed"])
        self.assertTrue(passed["full_genesis_authorized"])
        self.assertFalse(passed["delivery_authority_granted"])
        self.assertEqual(len(provider.calls) - calls_before_promotion, 7)
        self.assertEqual(len(promotions), 1)
        self.assertIn("Vision genesis: vision-genesis-", output.getvalue())
        self.assertIn("Vision scout already promoted", output.getvalue())

    def test_preregistered_behavioral_probe_can_promote_project_scout_once(self):
        from palamedes_vision_benchmark import VisionBenchmarkStore
        from palamedes_vision_scout import VisionScoutStore

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            provider = StaticChatProvider()
            mission_store = palamedes_chat.MissionStore(
                fake.STATE_DIR / "missions"
            )
            context = (
                "A service needs a durable product direction. It has recurring activity."
            )
            scout = palamedes_chat.run_autonomous_vision_scout(
                provider=provider,
                mission_store=mission_store,
                context=context,
                request_context=context,
            )
            scout_id = scout["vision_scout_id"]
            store = VisionScoutStore(fake.STATE_DIR / "vision-scouts")
            with self.assertRaisesRegex(ValueError, "not preregistered"):
                store.record_probe_outcome(scout_id, {})
            probe = store.register_probe(
                scout_id,
                {
                    "hypothesis": "At least half of invited users request another session.",
                    "metric_name": "return_request_rate",
                    "success_operator": "gte",
                    "threshold": 0.5,
                    "minimum_sample_size": 8,
                    "max_duration_days": 7,
                    "data_source": "signed manual-session worksheet",
                },
            )
            with self.assertRaisesRegex(ValueError, "sample size is below"):
                store.record_probe_outcome(
                    scout_id,
                    {
                        "probe_id": probe["probe_id"],
                        "observed_value": 1.0,
                        "sample_size": 3,
                        "measurement_provenance": "measured",
                        "source_reference": "worksheet:probe-1",
                        "observation": "Too few participants.",
                    },
                )
            outcome = store.record_probe_outcome(
                scout_id,
                {
                    "probe_id": probe["probe_id"],
                    "observed_value": 0.625,
                    "sample_size": 8,
                    "measurement_provenance": "measured",
                    "source_reference": "worksheet:probe-1",
                    "observation": "Five of eight requested another session.",
                },
            )
            with self.assertRaisesRegex(ValueError, "already recorded"):
                store.record_probe_outcome(
                    scout_id,
                    {
                        "probe_id": probe["probe_id"],
                        "observed_value": 1.0,
                        "sample_size": 8,
                        "measurement_provenance": "measured",
                        "source_reference": "worksheet:retry",
                        "observation": "A forbidden favorable retry.",
                    },
                )
            gate = VisionBenchmarkStore(
                fake.STATE_DIR / "vision-benchmarks"
            ).scout_promotion_gate(scout_id, probe_outcome=outcome)
            calls_before_promotion = len(provider.calls)
            output = io.StringIO()
            palamedes_chat.run_chat(
                palamedes_module=fake,
                provider=provider,
                session_id="behavioral-promote",
                input_stream=io.StringIO(
                    f"/vision-scout-promote {scout_id}\n/quit\n"
                ),
                output=output,
            )

        self.assertTrue(outcome["supports_full_genesis_renewal"])
        self.assertTrue(gate["passed"])
        self.assertFalse(gate["human_review_path_passed"])
        self.assertTrue(gate["behavioral_probe_path_passed"])
        self.assertEqual(gate["failure_reasons"], [])
        self.assertEqual(len(provider.calls) - calls_before_promotion, 7)
        self.assertIn("Vision genesis: vision-genesis-", output.getvalue())

    def test_failed_behavioral_probe_permanently_blocks_model_only_promotion(self):
        from palamedes_vision_benchmark import VisionBenchmarkStore
        from palamedes_vision_scout import VisionScoutStore

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            provider = StaticChatProvider()
            mission_store = palamedes_chat.MissionStore(
                fake.STATE_DIR / "missions"
            )
            context = "A service needs a durable product direction."
            scout = palamedes_chat.run_autonomous_vision_scout(
                provider=provider,
                mission_store=mission_store,
                context=context,
            )
            store = VisionScoutStore(fake.STATE_DIR / "vision-scouts")
            probe = store.register_probe(
                scout["vision_scout_id"],
                {
                    "hypothesis": "A bounded session creates voluntary return intent.",
                    "metric_name": "return_request_rate",
                    "success_operator": "gte",
                    "threshold": 0.5,
                    "minimum_sample_size": 8,
                    "max_duration_days": 7,
                    "data_source": "manual worksheet",
                },
            )
            outcome = store.record_probe_outcome(
                scout["vision_scout_id"],
                {
                    "probe_id": probe["probe_id"],
                    "observed_value": 0.25,
                    "sample_size": 8,
                    "measurement_provenance": "measured",
                    "source_reference": "worksheet:failed-probe",
                    "observation": "Only two of eight requested another session.",
                },
            )
            gate = VisionBenchmarkStore(
                fake.STATE_DIR / "vision-benchmarks"
            ).scout_promotion_gate(
                scout["vision_scout_id"], probe_outcome=outcome
            )
            calls_before = len(provider.calls)
            output = io.StringIO()
            palamedes_chat.run_chat(
                palamedes_module=fake,
                provider=provider,
                session_id="failed-behavioral-promote",
                input_stream=io.StringIO(
                    f"/vision-scout-promote {scout['vision_scout_id']}\n/quit\n"
                ),
                output=output,
            )

        self.assertFalse(outcome["supports_full_genesis_renewal"])
        self.assertFalse(gate["passed"])
        self.assertEqual(len(provider.calls), calls_before)
        self.assertIn("Vision scout promotion blocked", output.getvalue())

    def test_chat_preregisters_and_records_scout_probe_json(self):
        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            provider = StaticChatProvider()
            mission_store = palamedes_chat.MissionStore(
                fake.STATE_DIR / "missions"
            )
            context = "A service needs a durable product direction."
            scout = palamedes_chat.run_autonomous_vision_scout(
                provider=provider,
                mission_store=mission_store,
                context=context,
            )
            scout_id = scout["vision_scout_id"]
            probe_payload = json.dumps(
                {
                    "hypothesis": "Users voluntarily request another session.",
                    "metric_name": "return_request_rate",
                    "success_operator": "gte",
                    "threshold": 0.5,
                    "minimum_sample_size": 8,
                    "max_duration_days": 7,
                    "data_source": "manual worksheet",
                }
            )
            from palamedes_vision_scout import VisionScoutStore

            # Register through chat first, then read its immutable ID for the outcome.
            first_output = io.StringIO()
            palamedes_chat.run_chat(
                palamedes_module=fake,
                provider=provider,
                session_id="probe-register",
                input_stream=io.StringIO(
                    f"/vision-scout-probe {scout_id} {probe_payload}\n/quit\n"
                ),
                output=first_output,
            )
            probe = VisionScoutStore(
                fake.STATE_DIR / "vision-scouts"
            ).load_probe(scout_id)
            outcome_payload = json.dumps(
                {
                    "probe_id": probe["probe_id"],
                    "observed_value": 0.625,
                    "sample_size": 8,
                    "measurement_provenance": "measured",
                    "source_reference": "worksheet:chat-probe",
                    "observation": "Five of eight requested another session.",
                }
            )
            second_output = io.StringIO()
            palamedes_chat.run_chat(
                palamedes_module=fake,
                provider=provider,
                session_id="probe-outcome",
                input_stream=io.StringIO(
                    f"/vision-scout-probe-outcome {scout_id} {outcome_payload}\n"
                    "/quit\n"
                ),
                output=second_output,
            )

        self.assertIn("probe preregistered", first_output.getvalue())
        self.assertIn("supports_renewal=True", second_output.getvalue())
        self.assertEqual(len(provider.calls), 3)

    def test_vision_and_cognition_preserve_provider_reported_usage(self):
        class MeteredStaticProvider(StaticChatProvider):
            def __init__(self):
                super().__init__()
                self.last_usage = None

            def stream(self, messages):
                self.last_usage = None
                yield from super().stream(messages)
                self.last_usage = {
                    "input_tokens": 100,
                    "output_tokens": 20,
                    "total_tokens": 120,
                }

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            mission_store = palamedes_chat.MissionStore(
                fake.STATE_DIR / "missions"
            )
            provider = MeteredStaticProvider()
            vision = palamedes_chat.run_autonomous_vision(
                provider=provider,
                mission_store=mission_store,
                context="Originate a durable product world from ordinary activity.",
            )
            cycle = palamedes_chat.run_cognition_cycle(
                provider=provider,
                palamedes_module=fake,
                context="Select one bounded probe from the vision.",
                cycle_store=palamedes_chat.CognitionCycleStore(
                    fake.STATE_DIR / "missions" / "cognition"
                ),
            )
            next_context = json.loads(
                palamedes_chat.build_autonomous_vision_context(
                    mission_store=mission_store,
                    user_context="Reassess the next investment.",
                    workspace_context={},
                )
            )

        usage = vision["provider_usage"]
        self.assertEqual(usage["attempted_calls"], 7)
        self.assertEqual(usage["metered_calls"], 7)
        self.assertEqual(usage["unmetered_calls"], 0)
        self.assertEqual(usage["totals"]["input_tokens"], 700)
        self.assertEqual(usage["totals"]["output_tokens"], 140)
        self.assertEqual(
            next_context["prior_vision_investment"]["palamedes_provider_usage"][
                "totals"
            ]["total_tokens"],
            840,
        )
        self.assertTrue(
            all(
                artifact["usage_custody"] == "provider_reported"
                and artifact["provider_usage"]["total_tokens"] == 120
                for artifact in cycle["cycle"]["artifacts"]
            )
        )

    def test_vision_genesis_exposes_equal_call_conventional_agenda_control(self):
        from palamedes_vision import VisionStore, run_vision_genesis

        provider = StaticChatProvider()
        with tempfile.TemporaryDirectory() as tempdir:
            def ask(role, prompt):
                return palamedes_chat._provider_json(
                    provider,
                    system=f"ROLE: {role}",
                    prompt=f"ROLE: {role}\n{prompt}",
                )

            record = run_vision_genesis(
                ask=ask,
                store=VisionStore(Path(tempdir) / "visions"),
                context=(
                    "A service has profiles, recurring activity, and existing media "
                    "capabilities. Find a durable reason for people to return."
                ),
                agenda_strategy="conventional",
            )

        self.assertEqual(record["agenda_strategy"], "conventional")
        self.assertEqual(len(provider.calls), 7)
        agenda_prompt = provider.calls[0][-1]["content"]
        self.assertIn("Condition: conventional", agenda_prompt)
        self.assertIn("Stay within the explicit product category", agenda_prompt)
        self.assertNotIn("Condition: frontier", agenda_prompt)

    def test_vision_genesis_rejects_selection_with_unresolved_core_requirement(self):
        from palamedes_vision import VisionStore, run_vision_genesis

        class CoreRequirementOmittingProvider(StaticChatProvider):
            def stream(self, messages):
                if messages[-1]["content"].startswith(
                    "ROLE: maniac_critic_and_vision_author"
                ):
                    payload = json.loads("".join(super().stream(messages)))
                    payload["requirement_coverage"][0]["status"] = "partial"
                    payload["requirement_coverage"][0]["evidence"] = (
                        "The selected world leaves the payment mechanism unresolved."
                    )
                    yield json.dumps(payload)
                    return
                yield from super().stream(messages)

        provider = CoreRequirementOmittingProvider()
        with tempfile.TemporaryDirectory() as tempdir:
            store = VisionStore(Path(tempdir) / "visions")

            def ask(role, prompt):
                return palamedes_chat._provider_json(
                    provider,
                    system=f"ROLE: {role}",
                    prompt=f"ROLE: {role}\n{prompt}",
                )

            record = run_vision_genesis(
                ask=ask,
                store=store,
                context="Originate a world with a coherent payment mechanism.",
            )

        self.assertEqual(record["status"], "blocked_core_requirements")
        self.assertFalse(record["requirement_gate"]["passed"])
        self.assertEqual(
            record["requirement_gate"]["unresolved_core_requirement_ids"],
            ["req-1"],
        )

    def test_vision_genesis_rejects_requirement_quote_from_its_own_instructions(self):
        from palamedes_vision import VisionStore, run_vision_genesis

        class InstructionLeakProvider(StaticChatProvider):
            def stream(self, messages):
                if messages[-1]["content"].startswith("ROLE: desire_interpreter"):
                    payload = json.loads("".join(super().stream(messages)))
                    payload["explicit_context_requirements"][0]["source_quote"] = (
                        "Do not repeat a prior vision's central tension merely with new nouns."
                    )
                    yield json.dumps(payload)
                    return
                yield from super().stream(messages)

        provider = InstructionLeakProvider()
        with tempfile.TemporaryDirectory() as tempdir:

            def ask(role, prompt):
                return palamedes_chat._provider_json(
                    provider,
                    system=f"ROLE: {role}",
                    prompt=f"ROLE: {role}\n{prompt}",
                )

            record = run_vision_genesis(
                ask=ask,
                store=VisionStore(Path(tempdir) / "visions"),
                context="Originate a durable social world.",
            )

        requirement = record["desire_interpretation"][
            "explicit_context_requirements"
        ][0]
        self.assertEqual(
            requirement["source_quote"], "Originate a durable social world."
        )
        self.assertNotIn("prior vision", requirement["source_quote"])

    def test_vision_genesis_allows_core_constraint_satisfied_with_validation(self):
        from palamedes_vision import VisionStore, run_vision_genesis

        class ValidationBoundProvider(StaticChatProvider):
            def stream(self, messages):
                if messages[-1]["content"].startswith(
                    "ROLE: maniac_critic_and_vision_author"
                ):
                    payload = json.loads("".join(super().stream(messages)))
                    payload["requirement_coverage"][0]["status"] = (
                        "satisfied_with_validation"
                    )
                    payload["requirement_coverage"][0]["evidence"] = (
                        "The design obeys the constraint; its safety thesis remains testable."
                    )
                    yield json.dumps(payload)
                    return
                yield from super().stream(messages)

        provider = ValidationBoundProvider()
        with tempfile.TemporaryDirectory() as tempdir:

            def ask(role, prompt):
                return palamedes_chat._provider_json(
                    provider,
                    system=f"ROLE: {role}",
                    prompt=f"ROLE: {role}\n{prompt}",
                )

            record = run_vision_genesis(
                ask=ask,
                store=VisionStore(Path(tempdir) / "visions"),
                context="Originate a durable social world with bounded harm.",
            )

        self.assertEqual(record["status"], "selected")
        self.assertTrue(record["requirement_gate"]["passed"])


    def test_hidden_human_idea_is_revealed_only_to_blind_vision_judge(self):
        from palamedes_vision import VisionStore
        from palamedes_vision_benchmark import (
            BUILTIN_CASES,
            VisionBenchmarkStore,
            run_blind_case,
        )

        provider = StaticChatProvider()
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)

            def ask(role, prompt):
                return palamedes_chat._provider_json(
                    provider,
                    system=f"ROLE: {role}",
                    prompt=f"ROLE: {role}\n{prompt}",
                )

            benchmark_store = VisionBenchmarkStore(root / "benchmarks")
            result = run_blind_case(
                case=BUILTIN_CASES[0],
                ask=ask,
                vision_store=VisionStore(root / "visions"),
                benchmark_store=benchmark_store,
                generator_identity="static:generator",
                judge_identity="static:generator",
            )
            review_packet = json.loads(
                next((root / "benchmarks" / "human-review").glob("*.json")).read_text()
            )
            review_key = json.loads(
                next((root / "benchmarks" / "answer-keys").glob("*.json")).read_text()
            )
            scores = {axis: 80 for axis in review_packet["axes"]}
            scores_reference = {axis: 70 for axis in review_packet["axes"]}
            from palamedes_vision import fingerprint
            packet_fingerprint = fingerprint(review_packet)
            with self.assertRaisesRegex(ValueError, "invalid.*packet ID"):
                benchmark_store.submit_human_review("../../answer-keys", {})
            with self.assertRaisesRegex(ValueError, "unsafe characters"):
                benchmark_store.submit_human_review(
                    review_packet["vision_review_packet_id"],
                    {
                        "reviewer_id": "../outside",
                        "reviewer_kind": "human",
                        "reviewer_relationship": "independent",
                        "packet_fingerprint": packet_fingerprint,
                        "preferred": "peer",
                        "scores_A": scores,
                        "scores_B": scores_reference,
                        "rationale": "Unsafe reviewer IDs cannot become paths.",
                        "confidence": 50,
                    },
                )
            with self.assertRaisesRegex(ValueError, "fingerprint mismatch"):
                benchmark_store.submit_human_review(
                    review_packet["vision_review_packet_id"],
                    {
                        "reviewer_id": "tampered-packet-reviewer",
                        "reviewer_kind": "human",
                        "reviewer_relationship": "independent",
                        "packet_fingerprint": "0" * 64,
                        "preferred": "peer",
                        "scores_A": scores,
                        "scores_B": scores_reference,
                        "rationale": "This response belongs to a different packet.",
                        "confidence": 50,
                    },
                )
            submitted = benchmark_store.submit_human_review(
                review_packet["vision_review_packet_id"],
                {
                    "reviewer_id": "human-fixture-1",
                    "reviewer_kind": "human",
                    "reviewer_relationship": "independent",
                    "packet_fingerprint": packet_fingerprint,
                    "preferred": review_key["generated_label"],
                    f"scores_{review_key['generated_label']}": scores,
                    f"scores_{review_key['human_reference_label']}": scores_reference,
                    "rationale": "The generated world has a stronger causal loop.",
                    "confidence": 75,
                },
            )
            with self.assertRaisesRegex(ValueError, "already submitted"):
                benchmark_store.submit_human_review(
                    review_packet["vision_review_packet_id"],
                    {
                        "reviewer_id": "human-fixture-1",
                        "reviewer_kind": "human",
                        "reviewer_relationship": "independent",
                        "packet_fingerprint": packet_fingerprint,
                        "preferred": "peer",
                        "scores_A": scores,
                        "scores_B": scores_reference,
                        "rationale": "Duplicate response must not alter evidence.",
                        "confidence": 50,
                    },
                )
            benchmark_store.submit_human_review(
                review_packet["vision_review_packet_id"],
                {
                    "reviewer_id": "model-fixture-1",
                    "reviewer_kind": "model",
                    "reviewer_relationship": "unknown",
                    "packet_fingerprint": packet_fingerprint,
                    "preferred": review_key["human_reference_label"],
                    "scores_A": scores,
                    "scores_B": scores_reference,
                    "rationale": "Model custody must not count as human evidence.",
                    "confidence": 60,
                },
            )
            summary = benchmark_store.human_review_summary()

        generator_prompts = [call[-1]["content"] for call in provider.calls[:-2]]
        judge_prompts = [call[-1]["content"] for call in provider.calls[-2:]]
        self.assertTrue(result["passed"])
        self.assertTrue(result["hidden_anchors_verified_absent"])
        self.assertFalse(
            result["evaluation_custody"]["independent_provider_claimed"]
        )
        self.assertFalse(any("Shakespeare" in prompt for prompt in generator_prompts))
        self.assertTrue(all("Shakespeare" in prompt for prompt in judge_prompts))
        self.assertTrue(review_packet["authorship_hidden"])
        self.assertEqual(review_packet["evaluation_artifact"], "founder_prompt")
        generated_option = review_packet["options"][review_key["generated_label"]]
        self.assertIn("hidden discoveries", generated_option)
        self.assertNotIn("paper prototype of twelve", generated_option)
        self.assertNotIn("generated_label", review_packet)
        self.assertIn(review_key["generated_label"], {"A", "B"})
        self.assertNotEqual(
            review_key["generated_label"], review_key["human_reference_label"]
        )
        self.assertEqual(submitted["resolution"], "generated_preferred")
        self.assertEqual(summary["review_count"], 1)
        self.assertEqual(summary["total_resolved_review_count"], 2)

        self.assertEqual(summary["model_or_unattested_review_count"], 1)
        self.assertEqual(summary["generated_preference_rate"], 1.0)
        self.assertTrue(summary["independent_human_evidence_available"])
        self.assertTrue(summary["human_attested_evidence_available"])
        self.assertEqual(summary["independent_human_review_count"], 1)
        self.assertFalse(summary["human_level_creativity_claim_allowed"])
        self.assertEqual(
            summary["exploration_evidence_gate"]["status"], "fail"
        )
        self.assertIn(
            "external holdout coverage is 0/3 cases",
            " ".join(
                summary["exploration_evidence_gate"]["failure_reasons"]
            ),
        )
        self.assertEqual(
            summary["per_case"]["service-wide-hidden-meaning"][
                "generated_preferred"
            ],
            1,
        )

    def test_generic_founder_prompt_cannot_pass_origination_gate(self):
        from palamedes_vision import VisionStore
        from palamedes_vision_benchmark import (
            BUILTIN_CASES,
            VisionBenchmarkStore,
            run_blind_case,
        )

        class GenericPromptJudge(StaticChatProvider):
            def stream(self, messages):
                prompt = messages[-1]["content"]
                if prompt.startswith("ROLE: blind_founder_prompt_judge"):
                    self.calls.append(messages)
                    yield json.dumps(
                        {
                            "scores": {
                                "problem_reframing": 40,
                                "unsupplied_mechanism": 35,
                                "affective_thesis": 45,
                                "product_world_seed": 38,
                                "human_prompt_substitutability": 30,
                            },
                            "reference_relation": "weaker",
                            "solution_was_present_in_input": False,
                            "generic_request": True,
                            "decisive_difference": "It does not originate a mechanism.",
                            "rationale": "A human would still need to supply the product idea.",
                        }
                    )
                    return
                yield from super().stream(messages)

        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            provider = GenericPromptJudge()

            def ask(role, prompt):
                return palamedes_chat._provider_json(
                    provider,
                    system=f"ROLE: {role}",
                    prompt=f"ROLE: {role}\n{prompt}",
                )

            result = run_blind_case(
                case=BUILTIN_CASES[1],
                ask=ask,
                vision_store=VisionStore(root / "visions"),
                benchmark_store=VisionBenchmarkStore(root / "benchmarks"),
            )

        self.assertFalse(result["passed"])
        self.assertFalse(result["founder_prompt_gate_passed"])
        self.assertIn("founder_prompt_is_generic_request", result["failure_reasons"])
        self.assertIn(
            "founder_prompt_score_below_threshold:human_prompt_substitutability",
            result["failure_reasons"],
        )

    def test_human_evidence_gate_requires_cross_case_independent_quorum(self):
        from palamedes_vision_benchmark import VisionBenchmarkStore

        axes = {
            "origination",
            "conceptual_distance",
            "affective_depth",
            "mechanism_fusion",
            "world_coherence",
            "three_year_generativity",
            "human_approval_value",
        }
        with tempfile.TemporaryDirectory() as tempdir:
            store = VisionBenchmarkStore(Path(tempdir) / "benchmarks")
            resolved_root = store.root / "resolved-human-reviews"
            resolved_root.mkdir(parents=True)

            def import_case(case_id):
                return store.import_holdout_case(
                    {
                        "case_id": case_id,
                        "author_id": f"author-{case_id}",
                        "author_kind": "human",
                        "author_relationship": "independent",
                        "evaluation_trial_count": 1,
                        "generator_context": (
                            "An established digital service has recurring activity, "
                            "identity, and community surfaces but needs an original "
                            "product direction. Generate a durable causal world without "
                            "seeing the independent author's proposed mechanism or terms."
                        ),
                        "hidden_human_reference": (
                            f"The independent author for {case_id} proposes a deliberately "
                            "unfamiliar mechanism that connects identity, recurring action, "
                            "and shared consequences into a coherent world whose value can "
                            "be judged against an independently generated alternative."
                        ),
                        "hidden_anchor_terms": [
                            f"private anchor {case_id}",
                            f"unseen mechanism {case_id}",
                        ],
                    }
                )

            for case_id in (
                "holdout-ritual-coordination",
                "holdout-creative-tool",
                "holdout-market-tension",
            ):
                imported = import_case(case_id)
                case = store.load_holdout_case(case_id)
                attempt = store.reserve_holdout_attempt(case)
                store.complete_holdout_attempt(
                    attempt, f"vision-benchmark-{case_id}"
                )
                for reviewer_index in range(3):
                    row = {
                        "vision_human_review_resolution_version": (
                            "palamedes-vision-human-review-resolution/1"
                        ),
                        "vision_human_response_id": (
                            f"response-{case_id}-{reviewer_index}"
                        ),
                        "vision_review_packet_id": f"packet-{case_id}",
                        "case_id": case_id,
                        "case_origin": "external_human_holdout",
                        "case_fingerprint": imported["case_fingerprint"],
                        "trial_id": attempt["trial_id"],
                        "evaluation_artifact": "founder_prompt",
                        "reviewer_id": f"independent-{reviewer_index}",
                        "reviewer_kind": "human",
                        "reviewer_relationship": "independent",
                        "reviewer_is_case_author": False,
                        "resolution": (
                            "generated_preferred"
                            if reviewer_index < 2
                            else "peer"
                        ),
                        "score_deltas": {axis: 0 for axis in axes},
                        "confidence": 80,
                    }
                    (resolved_root / f"{case_id}-{reviewer_index}.json").write_text(
                        json.dumps(row), encoding="utf-8"
                    )
            legacy = dict(row)
            legacy.update(
                {
                    "vision_human_response_id": "legacy-full-brief-review",
                    "reviewer_id": "legacy-independent-reviewer",
                    "evaluation_artifact": "legacy_vision_brief",
                    "resolution": "generated_preferred",
                }
            )
            (resolved_root / "legacy-full-brief-review.json").write_text(
                json.dumps(legacy), encoding="utf-8"
            )
            summary = store.human_review_summary()
            imported_but_unreviewed = import_case("holdout-unreported-result")
            self.assertTrue(imported_but_unreviewed["case_fingerprint"])
            selection_gate = store.human_evidence_gate()

        gate = summary["exploration_evidence_gate"]
        self.assertEqual(gate["status"], "pass")
        self.assertEqual(
            gate["claim_scope"], "repeated_blind_human_founder_prompt_support"
        )
        self.assertEqual(gate["qualifying_review_count"], 9)
        self.assertEqual(gate["distinct_holdout_fingerprint_count"], 3)
        self.assertTrue(
            all(count == 3 for count in gate["independent_reviewer_count_by_case"].values())
        )
        self.assertEqual(gate["preregistered_trial_count"], 3)
        self.assertEqual(gate["completed_trial_count"], 3)
        self.assertTrue(
            all(
                count == 3
                for count in gate["independent_reviewer_count_by_trial"].values()
            )
        )
        self.assertEqual(gate["generated_or_peer_rate"], 1.0)
        self.assertFalse(gate["human_level_creativity_claim_allowed"])
        self.assertFalse(gate["market_success_claim_allowed"])
        self.assertEqual(selection_gate["status"], "fail")
        self.assertTrue(
            any(
                "holdout-unreported-result:preregistered:1 has no "
                "preregistered attempt record" in reason
                for reason in selection_gate["failure_reasons"]
            ),
        )

    def test_external_holdout_stays_out_of_builtin_prompt_and_preserves_custody(self):
        from palamedes_vision import VisionStore
        from palamedes_vision_benchmark import (
            VisionBenchmarkStore,
            run_blind_case,
        )

        provider = StaticChatProvider()
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            store = VisionBenchmarkStore(root / "benchmarks")
            imported = store.import_holdout_case(
                {
                    "case_id": "holdout-unfamiliar-coordination",
                    "author_id": "external-author-1",
                    "author_kind": "human",
                    "author_relationship": "independent",
                    "evaluation_trial_count": 1,
                    "generator_context": (
                        "A mature service has recurring individual actions, a small "
                        "community surface, and limited operational capacity. Originate "
                        "a durable product world that changes why people return without "
                        "assuming achievements, feeds, collections, or another game mode."
                    ),
                    "hidden_human_reference": (
                        "The external author proposes a rotating civic rehearsal where "
                        "ordinary actions allocate temporary stewardship of shared rules; "
                        "participants inherit unresolved consequences and must leave a "
                        "public amendment for the next cohort, creating memory without "
                        "permanent hierarchy."
                    ),
                    "hidden_anchor_terms": [
                        "rotating civic rehearsal",
                        "temporary stewardship",
                        "public amendment",
                    ],
                }
            )
            case = store.load_holdout_case(imported["case_id"])

            def ask(role, prompt):
                return palamedes_chat._provider_json(
                    provider,
                    system=f"ROLE: {role}",
                    prompt=f"ROLE: {role}\n{prompt}",
                )

            result = run_blind_case(
                case=case,
                ask=ask,
                vision_store=VisionStore(root / "visions"),
                benchmark_store=store,
            )
            packet = json.loads(
                next((store.root / "human-review").glob("*.json")).read_text(
                    encoding="utf-8"
                )
            )
            self.assertNotIn("case_author_id", packet)
            scores = {axis: 80 for axis in packet["axes"]}
            with self.assertRaisesRegex(ValueError, "author cannot review"):
                store.submit_human_review(
                    packet["vision_review_packet_id"],
                    {
                        "reviewer_id": "external-author-1",
                        "reviewer_kind": "human",
                        "reviewer_relationship": "independent",
                        "packet_fingerprint": palamedes_chat._fingerprint(packet),
                        "preferred": "peer",
                        "scores_A": scores,
                        "scores_B": scores,
                        "rationale": "An author must not validate their own holdout.",
                        "confidence": 90,
                    },
                )
            with self.assertRaisesRegex(ValueError, "trial budget exhausted"):
                run_blind_case(
                    case=case,
                    ask=ask,
                    vision_store=VisionStore(root / "visions-second-attempt"),
                    benchmark_store=store,
                )

        generator_prompts = [
            call[-1]["content"]
            for call in provider.calls
            if not call[-1]["content"].startswith(
                ("ROLE: blind_vision_judge", "ROLE: blind_founder_prompt_judge")
            )
        ]
        self.assertEqual(result["case_origin"], "external_human_holdout")
        self.assertEqual(result["case_fingerprint"], imported["case_fingerprint"])
        self.assertTrue(imported["custody"]["stored_under_local_state"])
        self.assertEqual(
            imported["custody"]["source_repository_status"], "unverified"
        )
        self.assertEqual(packet["case_origin"], "external_human_holdout")
        self.assertTrue(packet["authorship_hidden"])
        self.assertTrue(
            all("rotating civic rehearsal" not in prompt for prompt in generator_prompts)
        )

    def test_external_holdout_failed_generation_consumes_preregistered_trial(self):
        from palamedes_vision import VisionStore
        from palamedes_vision_benchmark import (
            VisionBenchmarkStore,
            run_blind_case,
        )

        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            store = VisionBenchmarkStore(root / "benchmarks")
            imported = store.import_holdout_case(
                {
                    "case_id": "holdout-failed-generation",
                    "author_id": "external-author-failure",
                    "author_kind": "human",
                    "author_relationship": "independent",
                    "evaluation_trial_count": 1,
                    "generator_context": (
                        "A mature digital product has identity, recurring actions, and "
                        "social contact, but its next product world is unknown. Originate "
                        "a durable direction without access to the external author's "
                        "private mechanism, terminology, or evaluation reference."
                    ),
                    "hidden_human_reference": (
                        "The external author proposes a temporary institution in which "
                        "ordinary use transfers stewardship of one shared convention, "
                        "forcing each cohort to inherit, contest, and visibly amend the "
                        "consequences left by the prior cohort."
                    ),
                    "hidden_anchor_terms": [
                        "temporary institution",
                        "transfers stewardship",
                    ],
                }
            )
            case = store.load_holdout_case(imported["case_id"])

            def failing_ask(role, prompt):
                raise RuntimeError("simulated provider failure")

            with self.assertRaisesRegex(RuntimeError, "provider failure"):
                run_blind_case(
                    case=case,
                    ask=failing_ask,
                    vision_store=VisionStore(root / "visions"),
                    benchmark_store=store,
                )
            attempts = store.holdout_attempts()
            self.assertEqual(len(attempts), 1)
            self.assertEqual(attempts[0]["status"], "started")
            with self.assertRaisesRegex(ValueError, "trial budget exhausted"):
                run_blind_case(
                    case=case,
                    ask=failing_ask,
                    vision_store=VisionStore(root / "visions-retry"),
                    benchmark_store=store,
                )

    def test_blind_benchmark_fails_original_world_that_omits_core_requirement(self):
        from palamedes_vision import VisionStore
        from palamedes_vision_benchmark import (
            BUILTIN_CASES,
            VisionBenchmarkStore,
            run_blind_case,
        )

        class MissingRequirementJudge(StaticChatProvider):
            def stream(self, messages):
                prompt = messages[-1]["content"]
                if prompt.startswith("ROLE: blind_vision_judge"):
                    payload = {
                        "scores": {
                            "origination": 96,
                            "conceptual_distance": 93,
                            "affective_depth": 92,
                            "mechanism_fusion": 89,
                            "world_coherence": 94,
                            "three_year_generativity": 95,
                            "human_approval_value": 88,
                        },
                        "reference_relation": "different_peer",
                        "generic_feature_pack": False,
                        "core_requirements_satisfied": False,
                        "unmet_core_requirements": [
                            "No coherent reason to pay or virtual-currency mechanism."
                        ],
                        "decisive_strength": "The world is highly original.",
                        "decisive_weakness": "The explicit payment objective is omitted.",
                        "would_human_likely_approve_exploration": True,
                        "rationale": "Originality cannot erase a missing core objective.",
                    }
                    yield json.dumps(payload)
                    return
                yield from super().stream(messages)

        provider = MissingRequirementJudge()
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)

            def ask(role, prompt):
                return palamedes_chat._provider_json(
                    provider,
                    system=f"ROLE: {role}",
                    prompt=f"ROLE: {role}\n{prompt}",
                )

            result = run_blind_case(
                case=BUILTIN_CASES[2],
                ask=ask,
                vision_store=VisionStore(root / "visions"),
                benchmark_store=VisionBenchmarkStore(root / "benchmarks"),
            )

        self.assertFalse(result["passed"])
        self.assertEqual(
            result["quality_gate_version"],
            "palamedes-vision-benchmark-gate/3",
        )
        self.assertGreaterEqual(min(result["judgment"]["scores"].values()), 88)
        self.assertIn("judge_core_requirements_unresolved", result["failure_reasons"])

    def test_repeated_blind_suite_preserves_trials_and_aggregates_diversity(self):
        from palamedes_vision import VisionStore
        from palamedes_vision_benchmark import (
            BUILTIN_CASES,
            VisionBenchmarkStore,
            run_blind_suite,
        )

        generator = StaticChatProvider()
        judge = StaticChatProvider()
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)

            def generator_ask(role, prompt):
                return palamedes_chat._provider_json(
                    generator,
                    system=f"ROLE: {role}",
                    prompt=f"ROLE: {role}\n{prompt}",
                )

            def judge_ask(role, prompt):
                return palamedes_chat._provider_json(
                    judge,
                    system=f"ROLE: {role}",
                    prompt=f"ROLE: {role}\n{prompt}",
                )

            benchmark_store = VisionBenchmarkStore(root / "benchmarks")
            suite = run_blind_suite(
                cases=[BUILTIN_CASES[0]],
                runs_per_case=2,
                ask=generator_ask,
                judge_ask=judge_ask,
                vision_store=VisionStore(root / "visions"),
                benchmark_store=benchmark_store,
                generator_identity="static:generator",
                judge_identity="static:independent-judge",
                suite_id="suite-fixture",
            )
            summary = benchmark_store.machine_benchmark_summary()
            records = [
                json.loads(path.read_text(encoding="utf-8"))
                for path in (root / "benchmarks").glob("vision-benchmark-*.json")
            ]
            packets = list((root / "benchmarks" / "human-review").glob("*.json"))
            queue = benchmark_store.human_review_queue()
            next_packet = benchmark_store.next_human_review_packet()
            bundle_path = benchmark_store.build_human_review_bundle()
            bundle = bundle_path.read_text(encoding="utf-8")

        self.assertEqual(suite["run_count"], 2)
        self.assertEqual(suite["pass_count"], 2)
        self.assertEqual(len(set(suite["record_ids"])), 2)
        self.assertEqual(len(packets), 2)
        self.assertEqual(len(queue), 2)
        self.assertEqual(queue[0]["response_count"], 0)
        self.assertIn(next_packet["vision_review_packet_id"], {row["vision_review_packet_id"] for row in queue})
        self.assertIn("Blind product-vision review", bundle)
        self.assertIn("packet_fingerprint", bundle)
        self.assertNotIn("generated_label", bundle)
        self.assertNotIn("human_reference_label", bundle)
        self.assertEqual(summary["benchmark_count"], 2)
        self.assertFalse(summary["human_level_creativity_claim_allowed"])
        self.assertEqual(summary["current_gate"]["benchmark_count"], 2)
        self.assertEqual(summary["current_gate"]["pass_rate"], 1.0)
        self.assertEqual(summary["pass_rate"], 1.0)
        self.assertEqual(summary["independent_provider_judgment_count"], 2)
        self.assertEqual(summary["unique_selected_title_count"], 1)
        self.assertEqual(summary["title_diversity_rate"], 0.5)
        self.assertEqual(
            summary["per_case"]["service-wide-hidden-meaning"]["pass_rate"],
            1.0,
        )
        self.assertTrue(
            all(
                row["evaluation_custody"]["independent_provider_claimed"]
                for row in records
            )
        )
        self.assertTrue(all(row["trial_id"].startswith("suite-fixture:") for row in records))
        desire_prompts = [
            call[-1]["content"]
            for call in generator.calls
            if call[-1]["content"].startswith("ROLE: desire_interpreter")
        ]
        self.assertEqual(len(desire_prompts), 2)
        self.assertTrue(all("Hidden cultural atlas" not in prompt for prompt in desire_prompts))

    def test_chat_exposes_repeated_vision_suite_and_machine_summary(self):
        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            output = io.StringIO()
            palamedes_chat.run_chat(
                palamedes_module=fake,
                provider=StaticChatProvider(),
                session_id="vision-suite",
                input_stream=io.StringIO(
                    "/vision-benchmark-suite collection 2\n"
                    "/vision-review-bundle\n"
                    "/vision-benchmark-summary\n/quit\n"
                ),
                output=output,
            )
            suites = list(
                (fake.STATE_DIR / "vision-benchmarks" / "suites").glob("*.json")
            )

        rendered = output.getvalue()
        self.assertIn("2/2 passed", rendered)
        self.assertIn("Blind human-review bundle:", rendered)
        self.assertIn('"benchmark_count": 2', rendered)
        self.assertIn('"title_diversity_rate": 0.5', rendered)
        self.assertEqual(len(suites), 1)

    def test_chat_runs_low_cost_scout_without_genesis_or_delivery_authority(self):
        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            provider = StaticChatProvider()
            output = io.StringIO()
            palamedes_chat.run_chat(
                palamedes_module=fake,
                provider=provider,
                session_id="vision-scout-benchmark",
                input_stream=io.StringIO(
                    "/vision-scout-benchmark collection\n/quit\n"
                ),
                output=output,
            )
            records = list(
                (
                    fake.STATE_DIR
                    / "vision-benchmarks"
                    / "scout-benchmarks"
                ).glob("*.json")
            )
            record = json.loads(records[0].read_text(encoding="utf-8"))

        self.assertEqual(len(records), 1)
        self.assertEqual(len(provider.calls), 4)
        self.assertIn(
            "MACHINE PASS (correlated same-provider judge)", output.getvalue()
        )
        self.assertIn("authority: blind_human_review only", output.getvalue())
        self.assertEqual(record["provider_usage"]["generator"]["attempted_calls"], 3)
        self.assertEqual(record["provider_usage"]["judge"]["attempted_calls"], 1)
        self.assertFalse(record["full_genesis_authorized"])
        self.assertFalse(record["delivery_authority_granted"])

    def test_chat_exposes_project_context_scout_without_running_full_genesis(self):
        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            provider = StaticChatProvider()
            output = io.StringIO()
            command = (
                "/vision-scout A service needs a durable product direction. "
                "Find an emotionally meaningful product world.\n"
            )
            palamedes_chat.run_chat(
                palamedes_module=fake,
                provider=provider,
                session_id="project-vision-scout",
                input_stream=io.StringIO(command + command + "/quit\n"),
                output=output,
            )

        rendered = output.getvalue()
        self.assertEqual(len(provider.calls), 3)
        self.assertIn("Vision scout: vision-scout-", rendered)
        self.assertIn("Identical context reused the prior Scout", rendered)
        self.assertNotIn("Vision genesis:", rendered)
        self.assertIn("grants neither full Vision Genesis", rendered)

    def test_agenda_ablation_matches_information_and_generation_calls(self):
        from palamedes_vision_benchmark import (
            BUILTIN_CASES,
            VisionBenchmarkStore,
            run_agenda_ablation,
        )

        provider = StaticChatProvider()
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            store = VisionBenchmarkStore(root / "benchmarks")

            def ask(role, prompt):
                return palamedes_chat._provider_json(
                    provider,
                    system=f"ROLE: {role}",
                    prompt=f"ROLE: {role}\n{prompt}",
                )

            record = run_agenda_ablation(
                case=BUILTIN_CASES[0],
                ask=ask,
                judge_ask=ask,
                vision_root=root / "ablation-visions",
                benchmark_store=store,
                generator_identity="static:fixture",
                judge_identity="static:fixture",
                challenger_condition="frontier",
                comparator_condition="conventional",
            )
            saved_ablation_count = len(
                list((store.root / "agenda-ablations").glob("*.json"))
            )
            attempt_status = store.agenda_ablation_attempts()[0]["status"]

        self.assertEqual(
            record["condition_call_counts"],
            {"frontier": 7, "conventional": 7},
        )
        self.assertTrue(record["equal_generation_call_count"])
        self.assertEqual(record["challenger_condition"], "frontier")
        self.assertEqual(record["comparator_condition"], "conventional")
        self.assertEqual(record["preferred_condition"], "peer")
        self.assertEqual(record["claim_scope"], "none")
        self.assertFalse(record["judge_independent_provider_claimed"])
        self.assertFalse(record["human_level_creativity_claim_allowed"])
        self.assertEqual(saved_ablation_count, 1)
        self.assertEqual(attempt_status, "completed")

    def test_agenda_ablation_failed_generation_consumes_only_trial(self):
        from palamedes_vision_benchmark import (
            BUILTIN_CASES,
            VisionBenchmarkStore,
            run_agenda_ablation,
        )

        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            store = VisionBenchmarkStore(root / "benchmarks")

            def failing_ask(role, prompt):
                raise RuntimeError("simulated malformed provider response")

            with self.assertRaisesRegex(RuntimeError, "malformed provider"):
                run_agenda_ablation(
                    case=BUILTIN_CASES[1],
                    ask=failing_ask,
                    judge_ask=failing_ask,
                    vision_root=root / "visions",
                    benchmark_store=store,
                )
            attempts = store.agenda_ablation_attempts()
            self.assertEqual(len(attempts), 1)
            self.assertEqual(attempts[0]["status"], "failed")
            self.assertIn("RuntimeError", attempts[0]["error"])
            with self.assertRaisesRegex(ValueError, "trial budget exhausted"):
                run_agenda_ablation(
                    case=BUILTIN_CASES[1],
                    ask=failing_ask,
                    judge_ask=failing_ask,
                    vision_root=root / "visions-retry",
                    benchmark_store=store,
                    challenger_condition="conventional",
                    comparator_condition="adaptive",
                )

    def test_chat_agenda_ablation_accounts_for_malformed_provider_call(self):
        class MalformedMeteredProvider:
            provider_name = "fixture"
            model = "malformed-metered"

            def __init__(self):
                self.calls = 0
                self.last_usage = None

            def stream(self, messages):
                self.calls += 1
                self.last_usage = {"input_tokens": 31, "output_tokens": 13}
                yield '{"questions": [] "missing_comma": true}'

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            provider = MalformedMeteredProvider()
            output = io.StringIO()
            palamedes_chat.run_chat(
                palamedes_module=fake,
                provider=provider,
                session_id="malformed-ablation-custody",
                input_stream=io.StringIO(
                    "/vision-agenda-ablation fusion adaptive conventional\n"
                    "/vision-agenda-ablation fusion conventional adaptive\n"
                    "/quit\n"
                ),
                output=output,
            )
            from palamedes_vision_benchmark import VisionBenchmarkStore

            store = VisionBenchmarkStore(fake.STATE_DIR / "vision-benchmarks")
            attempts = store.agenda_ablation_attempts()

        self.assertEqual(provider.calls, 1)
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0]["status"], "failed")
        provider_usage = attempts[0]["provider_usage"]
        self.assertEqual(provider_usage["attempted_calls"], 1)
        self.assertEqual(provider_usage["metered_calls"], 1)
        self.assertEqual(provider_usage["totals"]["input_tokens"], 31)
        custody = provider_usage["roles"][0]["json_custody"]
        self.assertEqual(custody["status"], "failed")
        self.assertEqual(custody["parse_mode"], "strict")
        self.assertIn("trial budget exhausted", output.getvalue())

    def test_chat_single_vision_benchmark_records_generator_and_judge_usage(self):
        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            output = io.StringIO()
            palamedes_chat.run_chat(
                palamedes_module=fake,
                provider=StaticChatProvider(),
                session_id="vision-metering",
                input_stream=io.StringIO(
                    "/vision-benchmark collection\n/quit\n"
                ),
                output=output,
            )
            record_path = next(
                (fake.STATE_DIR / "vision-benchmarks").glob(
                    "vision-benchmark-*.json"
                )
            )
            record = json.loads(record_path.read_text(encoding="utf-8"))

        usage = record["provider_usage"]
        self.assertEqual(usage["generator"]["attempted_calls"], 7)
        self.assertEqual(usage["judge"]["attempted_calls"], 2)
        self.assertEqual(usage["attempted_calls"], 9)
        self.assertEqual(usage["metered_calls"], 0)
        self.assertEqual(usage["unmetered_calls"], 9)
        self.assertIn("PASS", output.getvalue())
        self.assertIn("correlated same-provider judge", output.getvalue())

    def test_chat_agenda_ablation_records_full_call_cost_custody(self):
        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            output = io.StringIO()
            palamedes_chat.run_chat(
                palamedes_module=fake,
                provider=StaticChatProvider(),
                session_id="agenda-ablation-metering",
                input_stream=io.StringIO(
                    "/vision-agenda-ablation collection\n/quit\n"
                ),
                output=output,
            )
            path = next(
                (
                    fake.STATE_DIR
                    / "vision-benchmarks"
                    / "agenda-ablations"
                ).glob("*.json")
            )
            record = json.loads(path.read_text(encoding="utf-8"))

        usage = record["provider_usage"]
        self.assertEqual(usage["attempted_calls"], 15)
        self.assertEqual(usage["metered_calls"], 0)
        self.assertEqual(usage["unmetered_calls"], 15)
        self.assertEqual(len(usage["roles"]), 15)
        self.assertIn("peer", output.getvalue())

    def test_chat_imports_fingerprinted_model_review_without_human_claim(self):
        from palamedes_vision import VisionStore, fingerprint
        from palamedes_vision_benchmark import (
            BUILTIN_CASES,
            VisionBenchmarkStore,
            run_blind_case,
        )

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            provider = StaticChatProvider()

            def ask(role, prompt):
                return palamedes_chat._provider_json(
                    provider,
                    system=f"ROLE: {role}",
                    prompt=f"ROLE: {role}\n{prompt}",
                )

            benchmark_store = VisionBenchmarkStore(
                fake.STATE_DIR / "vision-benchmarks"
            )
            result = run_blind_case(
                case=BUILTIN_CASES[0],
                ask=ask,
                vision_store=VisionStore(fake.STATE_DIR / "visions"),
                benchmark_store=benchmark_store,
            )
            packet = benchmark_store.next_human_review_packet()
            scores = {axis: 75 for axis in packet["axes"]}
            response_path = Path(tempdir) / "model-review.json"
            response_path.write_text(
                json.dumps(
                    {
                        "vision_review_packet_id": packet["vision_review_packet_id"],
                        "packet_fingerprint": fingerprint(packet),
                        "reviewer_id": "model-reviewer",
                        "reviewer_kind": "model",
                        "reviewer_relationship": "unknown",
                        "preferred": "peer",
                        "scores_A": scores,
                        "scores_B": scores,
                        "rationale": "A model smoke response is not human evidence.",
                        "confidence": 70,
                    }
                ),
                encoding="utf-8",
            )
            output = io.StringIO()
            palamedes_chat.run_chat(
                palamedes_module=fake,
                provider=StaticChatProvider(),
                session_id="vision-import",
                input_stream=io.StringIO(
                    f"/vision-review-import {response_path}\n/quit\n"
                ),
                output=output,
            )
            summary = benchmark_store.human_review_summary()

        self.assertTrue(result["passed"])
        self.assertIn("Human vision review imported: peer", output.getvalue())
        self.assertEqual(summary["review_count"], 0)
        self.assertEqual(summary["model_or_unattested_review_count"], 1)
        self.assertFalse(summary["independent_human_evidence_available"])

    def test_later_vision_wake_receives_prior_frontier_as_novelty_exclusion(self):
        from palamedes_vision import VisionStore, run_vision_genesis

        with tempfile.TemporaryDirectory() as tempdir:
            store = VisionStore(Path(tempdir) / "visions")
            first_provider = StaticChatProvider()

            def first_ask(role, prompt):
                return palamedes_chat._provider_json(
                    first_provider,
                    system=f"ROLE: {role}",
                    prompt=f"ROLE: {role}\n{prompt}",
                )

            first = run_vision_genesis(
                ask=first_ask, store=store, context="Initial product context"
            )
            second_provider = StaticChatProvider()

            def second_ask(role, prompt):
                return palamedes_chat._provider_json(
                    second_provider,
                    system=f"ROLE: {role}",
                    prompt=f"ROLE: {role}\n{prompt}",
                )

            second = run_vision_genesis(
                ask=second_ask, store=store, context="Changed product context"
            )

        self.assertEqual(
            second["prior_vision_ids_considered"], [first["vision_genesis_id"]]
        )
        self.assertTrue(
            all(
                "Hidden cultural atlas" in call[-1]["content"]
                for call in second_provider.calls[:-1]
            )
        )

    def test_speculative_vision_cannot_select_full_build(self):
        from palamedes_vision import VisionStore, run_vision_genesis

        class OverbuildProvider(StaticChatProvider):
            def stream(self, messages):
                if messages[-1]["content"].startswith("ROLE: vision_reality_governor"):
                    payload = json.loads("".join(super().stream(messages)))
                    payload["selected_alternative"] = "full_build"
                    yield json.dumps(payload)
                    return
                yield from super().stream(messages)

        provider = OverbuildProvider()

        def ask(role, prompt):
            return palamedes_chat._provider_json(
                provider,
                system=f"ROLE: {role}",
                prompt=f"ROLE: {role}\n{prompt}",
            )

        with tempfile.TemporaryDirectory() as tempdir:
            with self.assertRaisesRegex(ValueError, "cannot authorize a full build"):
                run_vision_genesis(
                    ask=ask,
                    store=VisionStore(Path(tempdir) / "visions"),
                    context="A speculative product possibility",
                )

    def test_speculative_vision_lineage_blocks_product_scale_delivery(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            with PalamedesIsolation(root) as isolated:
                store = palamedes_chat.MissionStore(
                    isolated.STATE_DIR / "missions"
                )
                payload = StaticChatProvider._mission_payload()
                payload["work_scale"] = "product"
                contract = palamedes_chat.validate_mission_draft(payload)
                contract["vision_lineage"] = {
                    "vision_genesis_id": "vision-genesis-aaaaaaaaaaaa",
                    "evidence_maturity": "speculative",
                    "selected_alternative": "manual_probe",
                    "renewal_evidence": ["five users seek a second session"],
                    "kill_criteria": ["no voluntary return"],
                    "debt_guard": "no production persistence",
                    "scale_guard": "five users",
                    "delivery_authority_granted": False,
                }
                with self.assertRaisesRegex(ValueError, "product-scale delivery"):
                    palamedes_chat.approve_mission(
                        isolated, store, contract, "vision-scale-test"
                    )

    def test_repeated_micro_delivery_without_product_purpose_is_blocked(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            with PalamedesIsolation(root) as isolated:
                mission_store = palamedes_chat.MissionStore(
                    isolated.STATE_DIR / "missions"
                )
                for number in range(5):
                    mission_store.append_outcome(
                        {
                            "outcome_id": f"outcome-purpose-{number}",
                            "mission_contract_id": f"mission-purpose-{number}",
                        }
                    )
                payload = StaticChatProvider._mission_payload()
                payload["work_scale"] = "micro"
                payload["surface_key"] = "game-screen"
                contract = palamedes_chat.validate_mission_draft(payload)
                with self.assertRaisesRegex(ValueError, "purpose remains ungrounded"):
                    palamedes_chat.approve_mission(
                        isolated, mission_store, contract, "purpose-test"
                    )

    def test_product_alignment_blocks_wrong_purpose_greenfield_and_stage_claim(self):
        from palamedes_product_alignment import ProductAlignmentStore

        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            with PalamedesIsolation(root) as isolated:
                mission_store = palamedes_chat.MissionStore(
                    isolated.STATE_DIR / "missions"
                )
                alignment = ProductAlignmentStore(
                    isolated.STATE_DIR / "product-alignment"
                )
                alignment.record_purpose(
                    purpose_id="purpose-online-room",
                    statement="Catalog games run through online rooms.",
                    source_ids=["user"],
                    surface_key="game-platform",
                )
                alignment.record_capability(
                    capability_id="capability-realtime-runtime",
                    statement="An authoritative realtime room runtime exists.",
                    source_ids=["services/realtime"],
                    surface_key="game-platform",
                )
                alignment.record_integration_gap(
                    gap_id="gap-game-route-bypasses-runtime",
                    surface_key="game-platform",
                    expected_capability_id="capability-realtime-runtime",
                    observed_path="mobile/game_route",
                    evidence_ids=["route-source", "realtime-source"],
                )
                alignment.record_constraint(
                    constraint_id="constraint-no-media-prototype",
                    statement="Use no external media during the first prototype.",
                    source_ids=["prototype-contract"],
                    scope="game-platform",
                    expires_when="prototype validation completes",
                    status="expired_pending_review",
                )
                alignment.set_product_stage(
                    stage="beta",
                    required_journey_ids=["journey-two-client-reconnect"],
                    evidence_ids=[],
                )

                payload = StaticChatProvider._mission_payload()
                payload["work_scale"] = "micro"
                payload["surface_key"] = "game-platform"
                local_polish = palamedes_chat.validate_mission_draft(payload)
                with self.assertRaisesRegex(ValueError, "product alignment response"):
                    palamedes_chat.approve_mission(
                        isolated, mission_store, local_polish, "alignment-test"
                    )

                payload["product_alignment_response"] = {
                    "purposes": [
                        {
                            "purpose_id": "purpose-online-room",
                            "effect": "conflicts",
                            "rationale": "This keeps the local-only route.",
                        }
                    ],
                    "capability_reuse": {
                        "relevant_capability_ids": ["capability-realtime-runtime"],
                        "decision": "new",
                        "rejection_evidence_ids": [],
                        "rationale": "",
                    },
                    "constraint_review": {
                        "reviewed_constraint_ids": [],
                        "rationale": "",
                    },
                    "integration_gaps": [
                        {
                            "gap_id": "gap-game-route-bypasses-runtime",
                            "action": "audit",
                            "rationale": "Trace the integration boundary.",
                        }
                    ],
                    "stage_claim": {
                        "advances_stage": True,
                        "target_stage": "rc",
                        "journey_evidence_ids": [],
                    },
                }
                conflict = palamedes_chat.validate_mission_draft(payload)
                with self.assertRaisesRegex(ValueError, "purpose conflict"):
                    palamedes_chat.approve_mission(
                        isolated, mission_store, conflict, "alignment-test"
                    )

                response = payload["product_alignment_response"]
                response["purposes"][0]["effect"] = "advances"
                greenfield = palamedes_chat.validate_mission_draft(payload)
                with self.assertRaisesRegex(ValueError, "greenfield"):
                    palamedes_chat.approve_mission(
                        isolated, mission_store, greenfield, "alignment-test"
                    )

                response["capability_reuse"]["decision"] = "extend"
                response["capability_reuse"]["rationale"] = "Extend the existing reducer."
                expired = palamedes_chat.validate_mission_draft(payload)
                with self.assertRaisesRegex(ValueError, "expired constraints"):
                    palamedes_chat.approve_mission(
                        isolated, mission_store, expired, "alignment-test"
                    )

                response["constraint_review"]["reviewed_constraint_ids"] = [
                    "constraint-no-media-prototype"
                ]
                stage = palamedes_chat.validate_mission_draft(payload)
                with self.assertRaisesRegex(ValueError, "journey evidence"):
                    palamedes_chat.approve_mission(
                        isolated, mission_store, stage, "alignment-test"
                    )

                response["stage_claim"]["advances_stage"] = False
                corrected = palamedes_chat.validate_mission_draft(payload)
                approved = palamedes_chat.approve_mission(
                    isolated, mission_store, corrected, "alignment-test"
                )

        self.assertEqual(approved["contract"]["status"], "approved")

    def test_automatic_vision_wake_receives_product_ground_truth_and_capabilities(self):
        from palamedes_product_alignment import ProductAlignmentStore

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            alignment = ProductAlignmentStore(
                fake.STATE_DIR / "product-alignment"
            )
            alignment.record_purpose(
                purpose_id="purpose-online-multiplayer",
                statement="Games are online multiplayer experiences, not local pass-and-play.",
                source_ids=["user-product-brief"],
                surface_key="games",
            )
            alignment.record_capability(
                capability_id="capability-rust-realtime",
                statement="An authoritative Rust realtime room runtime already exists.",
                source_ids=["services/game-realtime"],
                surface_key="games",
            )
            alignment.record_integration_gap(
                gap_id="gap-local-game-bypass",
                surface_key="games",
                expected_capability_id="capability-rust-realtime",
                observed_path="mobile/local_game_screen",
                evidence_ids=["route-audit"],
            )
            provider = StaticChatProvider()
            output = io.StringIO()
            palamedes_chat.run_chat(
                palamedes_module=fake,
                provider=provider,
                session_id="vision-product-ground-truth",
                input_stream=io.StringIO(
                    "/cycle improve the game product without assuming greenfield work\n"
                    "/quit\n"
                ),
                output=output,
            )
            contracts = list((fake.STATE_DIR / "missions").glob("mission-*.json"))
            contract = json.loads(contracts[0].read_text(encoding="utf-8"))
            from palamedes_vision import VisionStore

            vision_store = VisionStore(fake.STATE_DIR / "visions")
            self.assertFalse(
                vision_store.needs_wake(
                    0,
                    palamedes_chat._fingerprint(alignment.active_context()),
                )
            )
            aligned_payload = StaticChatProvider._mission_payload()
            aligned_payload["work_scale"] = "micro"
            aligned_payload["surface_key"] = "games"
            aligned_payload["product_alignment_response"] = {
                "purposes": [
                    {
                        "purpose_id": "purpose-online-multiplayer",
                        "effect": "advances",
                        "rationale": (
                            "The probe keeps online multiplayer as the product "
                            "invariant instead of polishing a local substitute."
                        ),
                    }
                ],
                "capability_reuse": {
                    "relevant_capability_ids": ["capability-rust-realtime"],
                    "decision": "extend",
                    "rejection_evidence_ids": [],
                    "rationale": (
                        "Extend the existing authoritative runtime rather than "
                        "creating a parallel room system."
                    ),
                },
                "integration_gaps": [
                    {
                        "gap_id": "gap-local-game-bypass",
                        "action": "audit",
                        "rationale": (
                            "Trace the smallest command and state boundary needed "
                            "to remove the local bypass."
                        ),
                    }
                ],
                "constraint_review": {
                    "reviewed_constraint_ids": [],
                    "rationale": "No active temporary constraint applies.",
                },
                "stage_claim": {
                    "advances_stage": False,
                    "target_stage": "",
                    "journey_evidence_ids": [],
                },
            }
            aligned_contract = palamedes_chat.validate_mission_draft(
                aligned_payload
            )
            aligned_contract["vision_lineage"] = json.loads(
                json.dumps(contract["vision_lineage"])
            )
            fake.add_evidence = lambda plan, claim, source, confidence, axis, metadata=None: (
                plan.setdefault(axis, []).append(
                    {
                        "claim": claim,
                        "source": source,
                        "confidence": confidence,
                        "metadata": metadata or {},
                    }
                )
            )
            fake.mutate_plan_state = lambda apply, **_: apply(fake.load_plan())
            approved = palamedes_chat.approve_mission(
                fake,
                palamedes_chat.MissionStore(fake.STATE_DIR / "missions"),
                aligned_contract,
                "aligned-vision-test",
            )
            self.assertEqual(approved["contract"]["status"], "approved")
            mission_store = palamedes_chat.MissionStore(
                fake.STATE_DIR / "missions"
            )
            palamedes_chat.record_mission_outcome(
                fake,
                mission_store,
                approved["contract"],
                "mixed",
                "The first bounded probe produced ambiguous behavioral evidence.",
            )
            self.assertTrue(
                vision_store.needs_wake(
                    1,
                    palamedes_chat._fingerprint(alignment.active_context()),
                )
            )
            with self.assertRaisesRegex(ValueError, "outcome budget exhausted"):
                palamedes_chat.approve_mission(
                    fake,
                    mission_store,
                    aligned_contract,
                    "exhausted-vision-test",
                )
            alignment.record_capability(
                capability_id="capability-rust-realtime",
                statement="The authoritative runtime changed its command contract.",
                source_ids=["services/game-realtime-v2"],
                surface_key="games",
            )
            self.assertTrue(
                vision_store.needs_wake(
                    0,
                    palamedes_chat._fingerprint(alignment.active_context()),
                )
            )
            with self.assertRaisesRegex(ValueError, "vision lineage is stale"):
                palamedes_chat.approve_mission(
                    fake,
                    palamedes_chat.MissionStore(fake.STATE_DIR / "missions"),
                    contract,
                    "stale-vision-test",
                )

        desire_prompt = next(
            call[-1]["content"]
            for call in provider.calls
            if call[-1]["content"].startswith("ROLE: desire_interpreter")
        )
        self.assertIn("purpose-online-multiplayer", desire_prompt)
        self.assertIn("capability-rust-realtime", desire_prompt)
        self.assertIn("gap-local-game-bypass", desire_prompt)
        self.assertIn("Product invariants outrank", desire_prompt)
        self.assertIn("Vision wake:", output.getvalue())
        self.assertEqual(len(contracts), 1)
        self.assertIn("vision_lineage", contract)
        self.assertTrue(contract["vision_lineage"]["requirement_gate_passed"])
        self.assertEqual(
            len(contract["vision_lineage"]["product_ground_truth_fingerprint"]),
            64,
        )

    def test_measured_investment_exhausts_vision_before_outcome_count_limit(self):
        from palamedes_product_alignment import ProductAlignmentStore
        from palamedes_vision import VisionStore

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            fake.add_evidence = lambda plan, claim, source, confidence, axis, metadata=None: (
                plan.setdefault(axis, []).append({"claim": claim})
            )
            fake.mutate_plan_state = lambda apply, **_: apply(fake.load_plan())
            mission_store = palamedes_chat.MissionStore(
                fake.STATE_DIR / "missions"
            )
            alignment = ProductAlignmentStore(
                fake.STATE_DIR / "product-alignment"
            )
            alignment_fingerprint = palamedes_chat._fingerprint(
                alignment.active_context()
            )
            envelope = {
                "evidence_maturity": "behavioral",
                "selected_alternative": "manual_probe",
                "max_outcomes_before_reassessment": 2,
                "engineering_days_high": 1,
                "ai_cost_high": 10,
                "monthly_infrastructure_high": 5,
                "budget_exhaustion_action": "regenerate_vision",
            }
            payload = StaticChatProvider._mission_payload()
            payload["work_scale"] = "micro"
            contract = palamedes_chat.validate_mission_draft(payload)
            contract["vision_lineage"] = {
                "vision_genesis_id": "vision-genesis-aaaaaaaaaaaa",
                "delivery_authority_granted": False,
                "evidence_maturity": "behavioral",
                "selected_alternative": "manual_probe",
                "requirement_gate_passed": True,
                "product_ground_truth_fingerprint": alignment_fingerprint,
                "investment_envelope": envelope,
            }
            approved = palamedes_chat.approve_mission(
                fake, mission_store, contract, "measured-investment"
            )["contract"]
            palamedes_chat.record_mission_outcome(
                fake,
                mission_store,
                approved,
                "mixed",
                "The first probe used the entire engineering allocation.",
                {
                    "engineering_days": 1,
                    "ai_cost": 2,
                    "input_tokens": 1000,
                    "output_tokens": 200,
                    "monthly_infrastructure": 0,
                    "evidence_source": "measured",
                    "notes": "Time log and provider usage export.",
                },
            )
            summary = mission_store.vision_investment_summary(
                "vision-genesis-aaaaaaaaaaaa"
            )
            self.assertEqual(summary["engineering_days"], 1)
            self.assertEqual(summary["input_tokens"], 1000)
            self.assertEqual(summary["measured_outcome_count"], 1)
            self.assertEqual(summary["missing_measurement_count"], 0)

            vision_store = VisionStore(fake.STATE_DIR / "visions")
            vision_store.save(
                {
                    "vision_genesis_id": "vision-genesis-aaaaaaaaaaaa",
                    "product_ground_truth_fingerprint": alignment_fingerprint,
                    "outcome_count_at_creation": 0,
                    "investment_envelope": envelope,
                    "created_at": "2026-01-01T00:00:00+00:00",
                }
            )
            self.assertTrue(
                vision_store.needs_wake(1, alignment_fingerprint, summary)
            )
            with self.assertRaisesRegex(
                ValueError, "actual investment budget exhausted"
            ):
                palamedes_chat.approve_mission(
                    fake, mission_store, contract, "measured-investment-2"
                )

    def test_provider_scalar_normalization_repairs_only_unambiguous_types(self):
        normalized = palamedes_chat._normalize_provider_scalars(
            {
                "confidence": "90",
                "followup_required": "false",
                "claim": "90",
                "nested": [{"exploration_value": "64"}],
            }
        )

        self.assertEqual(normalized["confidence"], 90)
        self.assertFalse(normalized["followup_required"])
        self.assertEqual(normalized["claim"], "90")
        self.assertEqual(normalized["nested"][0]["exploration_value"], 64)

    def test_provider_json_records_meaning_preserving_envelope_custody(self):
        class EnvelopeProvider:
            provider_name = "fixture"
            model = "envelope"
            last_usage = {"input_tokens": 10, "output_tokens": 5}

            def stream(self, messages):
                yield 'Preface\n```json\n{"claim":"brace } in string",}\n```\nAfterword'

        provider = EnvelopeProvider()
        payload = palamedes_chat._provider_json(
            provider, system="return JSON", prompt="test"
        )
        usage = palamedes_chat._capture_provider_usage(provider, "test_role")

        self.assertEqual(payload, {"claim": "brace } in string"})
        self.assertEqual(usage["json_custody"]["status"], "parsed")
        self.assertEqual(
            usage["json_custody"]["parse_mode"], "trailing_comma_normalized"
        )
        self.assertEqual(
            usage["json_custody"]["transforms"],
            ["text_envelope", "removed_structural_trailing_commas:1"],
        )
        self.assertEqual(len(usage["json_custody"]["raw_sha256"]), 64)
        self.assertNotIn("raw", usage["json_custody"])

    def test_provider_json_does_not_guess_ambiguous_missing_comma(self):
        class MalformedProvider:
            provider_name = "fixture"
            model = "malformed"
            last_usage = {"input_tokens": 20, "output_tokens": 8}

            def stream(self, messages):
                yield '{"first": 1 "second": 2}'

        provider = MalformedProvider()
        with self.assertRaisesRegex(
            palamedes_chat.ProviderJSONError,
            "mission response must be one JSON object",
        ):
            palamedes_chat._provider_json(
                provider, system="return JSON", prompt="test"
            )
        usage = palamedes_chat._capture_provider_usage(provider, "failed_role")

        self.assertEqual(usage["json_custody"]["status"], "failed")
        self.assertEqual(usage["json_custody"]["parse_mode"], "strict")
        self.assertEqual(usage["json_custody"]["transforms"], [])
        self.assertIn("JSONDecodeError", usage["json_custody"]["error"])
        self.assertEqual(usage["custody"], "provider_reported")

    def test_provider_json_rejects_multiple_objects_in_text_envelope(self):
        with self.assertRaisesRegex(
            palamedes_chat.ProviderJSONError, "more than one or an ambiguous"
        ):
            palamedes_chat._extract_json_object('{"first": 1}\n{"second": 2}')

    def test_required_fresh_eyes_agenda_blocks_micro_reentry_until_addressed(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            with PalamedesIsolation(root) as isolated:
                mission_store = palamedes_chat.MissionStore(
                    isolated.STATE_DIR / "missions"
                )
                from palamedes_prompt import PromptAgendaStore

                prompt_store = PromptAgendaStore(
                    mission_store.root / "prompt-intelligence"
                )
                cluster = {
                    "causal_cluster_version": "palamedes-causal-cluster/1",
                    "causal_cluster_id": "causal-cluster-aaaaaaaaaaaa",
                    "causal_signature": "micro-cycle-streak:game-screen",
                    "mechanism_summary": "Five micro outcomes stayed on one screen.",
                    "outcome_ids": ["outcome-000000000001"],
                    "mission_contract_ids": ["mission-000000000001"],
                    "recurrence_count": 5,
                    "meta_shift_required": True,
                    "zoom_shift_from": "micro",
                    "zoom_shift_to": "component_or_product",
                    "fresh_eyes_required": True,
                    "surface_key": "game-screen",
                    "created_at": "2026-01-01T00:00:00+00:00",
                    "updated_at": "2026-01-01T00:00:00+00:00",
                }
                prompt_store.save_cluster(cluster)
                agenda = {
                    "prompt_agenda_version": "palamedes-prompt-agenda/1",
                    "prompt_agenda_id": "prompt-agenda-bbbbbbbbbbbb",
                    "causal_cluster_id": cluster["causal_cluster_id"],
                    "status": "selected",
                    "created_at": "2026-01-01T00:00:00+00:00",
                }
                prompt_store.save_agenda(agenda)

                payload = StaticChatProvider._mission_payload()
                blocked = palamedes_chat.validate_mission_draft(payload)
                with self.assertRaisesRegex(ValueError, "fresh-eyes"):
                    palamedes_chat.approve_mission(
                        isolated, mission_store, blocked, "zoom-test"
                    )

                payload["work_scale"] = "micro"
                payload["surface_key"] = "game-screen"
                payload["prompt_agenda_response"] = {
                    "prompt_agenda_ids": [agenda["prompt_agenda_id"]],
                    "action": "address",
                    "rationale": "Attempt another local correction.",
                }
                micro = palamedes_chat.validate_mission_draft(payload)
                with self.assertRaisesRegex(ValueError, "another micro"):
                    palamedes_chat.approve_mission(
                        isolated, mission_store, micro, "zoom-test"
                    )

                payload["work_scale"] = "product"
                payload["rationale"] = "Audit whether local optimization still matters."
                product = palamedes_chat.validate_mission_draft(payload)
                approved = palamedes_chat.approve_mission(
                    isolated, mission_store, product, "zoom-test"
                )
                saved_agenda = json.loads(
                    (prompt_store.agendas_root / f"{agenda['prompt_agenda_id']}.json").read_text()
                )

        self.assertEqual(approved["contract"]["status"], "approved")
        self.assertEqual(saved_agenda["status"], "addressed")

    def test_automatic_meta_learning_stays_dormant_before_five_outcomes(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            store = palamedes_chat.MissionStore(root / "missions")
            result = palamedes_chat.run_automatic_meta_learning(
                provider=StaticChatProvider(),
                mission_store=store,
                snapshot={"observation_id": "observation-test"},
            )

        self.assertEqual(result["status"], "not_needed")
        self.assertEqual(result["outcome_count"], 0)

    def test_automatic_meta_learning_wakes_backfill_zoom_and_self_model(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            store = palamedes_chat.MissionStore(root / "missions")
            for number in range(5):
                store.append_outcome(
                    {
                        "outcome_id": f"outcome-{number:012x}",
                        "mission_contract_id": f"mission-{number:012x}",
                    }
                )
            cluster = {
                "causal_cluster_id": "causal-cluster-aaaaaaaaaaaa",
                "meta_shift_required": True,
                "fresh_eyes_required": True,
            }
            with patch(
                "palamedes_prompt.run_outcome_backfill",
                return_value={
                    "status": "completed",
                    "records": [{"outcome_id": "outcome-000000000000"}],
                    "zoom_pattern": {"status": "required", "cluster": cluster},
                },
            ) as backfill, patch(
                "palamedes_prompt.run_prompt_architecture",
                return_value={"status": "completed"},
            ) as architecture, patch(
                "palamedes_reference_intelligence.run_reference_intelligence",
                return_value={
                    "reference_intelligence_id": "reference-intelligence-bbbbbbbbbbbb",
                    "reference_mode": "workspace_only",
                },
            ) as intelligence:
                result = palamedes_chat.run_automatic_meta_learning(
                    provider=StaticChatProvider(),
                    mission_store=store,
                    snapshot={"observation_id": "observation-test"},
                )

        self.assertEqual(result["status"], "completed")
        backfill.assert_called_once()
        architecture.assert_called_once()
        intelligence.assert_called_once()

    def test_team_enabled_chat_receives_shared_plural_state(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            fake = FakePalamedes(root)
            store = palamedes.team_cognition_store(root / "team.json")
            store.record_observation(
                {
                    "observation_id": "obs-team-chat",
                    "agent_id": "research-agent",
                    "agent_role": "researcher",
                    "content": "A quiet user group is absent from current feedback.",
                    "source": "feedback sample",
                    "observation_surface": "support tickets",
                }
            )
            provider = StaticChatProvider()

            result = palamedes_chat.run_chat(
                palamedes_module=fake,
                provider=provider,
                session_id="team-chat",
                input_stream=io.StringIO("What deserves attention?\n/quit\n"),
                output=io.StringIO(),
                team_store=store,
                agent_id="palamedes-main",
                agent_role="strategist",
            )

        self.assertEqual(result, 0)
        system = provider.calls[0][0]["content"]
        self.assertIn("Shared team cognition", system)
        self.assertIn("obs-team-chat", system)
        self.assertIn("palamedes-main", system)

    def test_repl_streams_and_persists_turns(self):
        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            provider = StaticChatProvider()
            output = io.StringIO()

            result = palamedes_chat.run_chat(
                palamedes_module=fake,
                provider=provider,
                session_id="trial-1",
                input_stream=io.StringIO("/mission improve direction\n/history\n/quit\n"),
                output=output,
            )

            records = palamedes_chat.ChatSessionStore(
                fake.STATE_DIR / "chat"
            ).load("trial-1")

        self.assertEqual(result, 0)
        self.assertIn("Mission draft:", output.getvalue())
        self.assertEqual(
            [
                record["role"]
                for record in records
                if record.get("role") in {"user", "assistant"}
            ],
            ["user", "assistant"],
        )
        self.assertEqual(records[0]["content"], "/mission improve direction")
        self.assertIn("mission contract", provider.calls[0][-1]["content"])

    def test_mission_approve_handoff_and_outcome_vertical_slice(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            with PalamedesIsolation(root) as isolated:
                provider = StaticChatProvider()
                output = io.StringIO()
                result = palamedes_chat.run_chat(
                    palamedes_module=isolated,
                    provider=provider,
                    session_id="vertical",
                    input_stream=io.StringIO(
                        "/mission improve upstream decisions\n"
                        "/approve\n"
                        "/approve\n"
                        "/outcome success The approved probe produced a traceable result\n"
                        "/quit\n"
                    ),
                    output=output,
                )
                plan = isolated.load_plan()
                mission_files = list(
                    (isolated.STATE_DIR / "missions").glob("mission-*.json")
                )
                handoff_files = list(
                    (isolated.STATE_DIR / "missions" / "handoffs").glob("*.json")
                )
                outcomes = (
                    isolated.STATE_DIR / "missions" / "outcomes.jsonl"
                ).read_text(encoding="utf-8")

        self.assertEqual(result, 0)
        self.assertEqual(
            plan["goal"], "Prove that one mission improves the next action"
        )
        self.assertEqual(plan["hypothesis_log"][-1]["status"], "open")
        self.assertEqual(len(plan["hypothesis_log"]), 1)
        self.assertEqual(plan["development_probes"][-1]["status"], "completed")
        self.assertEqual(len(mission_files), 1)
        self.assertEqual(len(handoff_files), 1)
        self.assertIn('"status": "success"', outcomes)
        self.assertIn("Delivery authority remains ungranted.", output.getvalue())
        self.assertIn("No pending mission draft to approve.", output.getvalue())

    def test_invalid_mission_output_cannot_be_approved(self):
        class InvalidMissionProvider:
            provider_name = "static"
            model = "invalid"

            def stream(self, messages):
                yield "This is prose, not a contract."

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            output = io.StringIO()
            palamedes_chat.run_chat(
                palamedes_module=fake,
                provider=InvalidMissionProvider(),
                session_id="invalid",
                input_stream=io.StringIO("/mission vague idea\n/approve\n/quit\n"),
                output=output,
            )

        self.assertIn("[mission validation error]", output.getvalue())
        self.assertIn("No pending mission draft to approve.", output.getvalue())

    def test_mission_prompt_omits_placeholder_prompt_agenda_response(self):
        prompt = palamedes_chat.mission_prompt("advisory question-1")

        self.assertNotIn(
            '"prompt_agenda_ids": ["required fresh-eyes agenda IDs, when present"]',
            prompt,
        )
        self.assertIn("Omit it entirely", prompt)
        self.assertIn("advisory vision agenda", prompt)

    def test_independent_cognition_cycle_and_post_outcome_analysis(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            with PalamedesIsolation(root) as isolated:
                provider = StaticChatProvider()
                output = io.StringIO()
                with patch.dict(os.environ, {"PALAMEDES_REF_ROOT": ""}):
                    palamedes_chat.run_chat(
                        palamedes_module=isolated,
                        provider=provider,
                        session_id="cognition",
                        input_stream=io.StringIO(
                            "/cycle --mode product find a mission worth planning\n"
                            "/approve\n"
                            "/outcome success The selected probe matched its forecast\n"
                            "/quit\n"
                        ),
                        output=output,
                    )
                cycle_path = next(
                    (isolated.STATE_DIR / "missions" / "cognition").glob("cycle-*.json")
                )
                cycle = json.loads(cycle_path.read_text(encoding="utf-8"))
                experience_path = next(
                    (isolated.STATE_DIR / "thoughts" / "experiences").glob("*.json")
                )
                experience = json.loads(
                    experience_path.read_text(encoding="utf-8")
                )
                mission_contract = json.loads(
                    next(
                        (isolated.STATE_DIR / "missions").glob("mission-*.json")
                    ).read_text(encoding="utf-8")
                )

        self.assertEqual(
            [item["role"] for item in cycle["artifacts"]],
            [
                "context_governor",
                "interpreter",
                "inventor",
                "adversary",
                "selector",
            ],
        )
        self.assertEqual(len(cycle["outcome_analyses"]), 1)
        self.assertEqual(
            cycle["outcome_analyses"][0]["role"], "outcome_analyst"
        )
        self.assertEqual(cycle["live_model_call_count"], 6)
        self.assertFalse(cycle["outcome_analyst_runs_before_outcome"])
        self.assertEqual(
            [call[-1]["content"].splitlines()[0] for call in provider.calls],
            [
                "ROLE: vision_agenda_architect",
                "ROLE: desire_interpreter",
                "ROLE: distant_analogy_explorer",
                "ROLE: mechanism_fusion_inventor",
                "ROLE: product_world_builder",
                "ROLE: maniac_critic_and_vision_author",
                "ROLE: vision_reality_governor",
                "ROLE: context_governor",
                "ROLE: interpreter",
                "ROLE: inventor",
                "ROLE: adversary",
                "ROLE: selector",
                "ROLE: outcome_analyst",
            ],
        )
        self.assertIn("Outcome analyst completed", output.getvalue())
        self.assertEqual(
            experience["mission_contract_id"],
            mission_contract["mission_id"],
        )
        self.assertEqual(experience["outcome_status"], "success")
        self.assertEqual(experience["evidence_source_type"], "implementer_claim")
        self.assertEqual(experience["causal_signature"], "approval-lineage-observed")
        self.assertEqual(experience["probe_status"], "completed")
        self.assertEqual(experience["finding"], "expected_result")
        self.assertFalse(experience["followup_required"])
        self.assertEqual(experience["followup_kind"], "none")

    def test_audit_cycle_skips_vision_and_emits_run_scoped_progress(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            with PalamedesIsolation(root) as isolated:
                provider = StaticChatProvider()
                output = io.StringIO()
                with patch.dict(os.environ, {"PALAMEDES_REF_ROOT": ""}):
                    palamedes_chat.run_chat(
                        palamedes_module=isolated,
                        provider=provider,
                        session_id="audit-cycle",
                        input_stream=io.StringIO(
                            "/cycle --mode audit challenge the current direction\n"
                            "/quit\n"
                        ),
                        output=output,
                    )
                cycle_path = next(
                    (isolated.STATE_DIR / "missions" / "cognition").glob(
                        "cycle-*.json"
                    )
                )
                cycle = json.loads(cycle_path.read_text(encoding="utf-8"))

        role_prompts = [call[-1]["content"].splitlines()[0] for call in provider.calls]
        self.assertEqual(
            role_prompts,
            [
                "ROLE: context_governor",
                "ROLE: interpreter",
                "ROLE: inventor",
                "ROLE: adversary",
                "ROLE: selector",
            ],
        )
        self.assertNotIn("Vision wake:", output.getvalue())
        self.assertIn("Audit mode:", output.getvalue())
        self.assertIn("context_governor 1/5 started", output.getvalue())
        self.assertIn("selector 5/5 completed", output.getvalue())
        self.assertEqual(cycle["run_id"], cycle["cognition_cycle_id"])
        self.assertEqual(cycle["provider_usage"]["attempted_calls"], 5)
        self.assertEqual(cycle["provider_usage"]["unmetered_calls"], 5)
        for artifact in cycle["artifacts"]:
            self.assertEqual(artifact["run_id"], cycle["run_id"])
            self.assertIn("started_at", artifact)
            self.assertIsInstance(artifact["duration_ms"], int)

    def test_micro_cycle_uses_one_provider_call_and_emits_valid_contract(self):
        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            provider = StaticChatProvider()
            result = palamedes_chat.run_micro_cycle(
                provider=provider,
                palamedes_module=fake,
                context="Fix one bounded parser rule.",
                cycle_store=palamedes_chat.CognitionCycleStore(
                    fake.STATE_DIR / "missions" / "cognition"
                ),
            )
        self.assertEqual(len(provider.calls), 1)
        self.assertEqual(result["cycle"]["cycle_mode"], "micro")
        self.assertEqual(result["cycle"]["live_model_call_count"], 1)
        self.assertEqual(result["cycle"]["provider_usage"]["attempted_calls"], 1)
        self.assertEqual(result["contract"]["causal_role"], "constrained")

    def test_micro_cycle_repairs_only_its_invalid_contract_once(self):
        class InvalidOnceProvider(StaticChatProvider):
            def __init__(self):
                super().__init__()
                self.invalid = True

            def stream(self, messages):
                if "Required shape:" in messages[-1]["content"] and self.invalid:
                    self.invalid = False
                    payload = self._mission_payload()
                    payload["evidence"][0]["confidence"] = "bad"
                    self.calls.append(messages)
                    yield json.dumps(payload)
                    return
                yield from super().stream(messages)

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            provider = InvalidOnceProvider()
            result = palamedes_chat.run_micro_cycle(
                provider=provider,
                palamedes_module=fake,
                context="Fix one bounded parser rule.",
                cycle_store=palamedes_chat.CognitionCycleStore(
                    fake.STATE_DIR / "missions" / "cognition"
                ),
            )
        self.assertEqual(len(provider.calls), 2)
        self.assertEqual(result["cycle"]["live_model_call_count"], 2)
        self.assertEqual(len(result["cycle"]["rejected_artifacts"]), 1)

    def test_chat_lookup_cycle_uses_zero_provider_calls_for_satisfied_requirement(self):
        from palamedes_satisfaction import SatisfactionStore, workspace_snapshot

        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            with PalamedesIsolation(root) as isolated:
                SatisfactionStore(isolated.STATE_DIR / "satisfaction").save({
                    "assessment_id": "satisfaction-bbbbbbbbbbbbbbbb",
                    "requirement_id": "req-existing",
                    "disposition": "already_satisfied",
                    "current_snapshot": workspace_snapshot(root),
                    "observed_at": palamedes_chat.utc_now(),
                    "ttl_days": 30,
                })
                provider = StaticChatProvider()
                output = io.StringIO()
                palamedes_chat.run_chat(
                    palamedes_module=isolated,
                    provider=provider,
                    session_id="lookup-zero",
                    input_stream=io.StringIO("/cycle verify req-existing again\n/quit\n"),
                    output=output,
                )
        self.assertEqual(provider.calls, [])
        self.assertIn("mode=lookup", output.getvalue())
        self.assertIn("provider_calls=0", output.getvalue())

    def test_chat_explicit_micro_cycle_uses_one_provider_call(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            with PalamedesIsolation(root) as isolated:
                provider = StaticChatProvider()
                output = io.StringIO()
                with patch.dict(os.environ, {"PALAMEDES_REF_ROOT": ""}):
                    palamedes_chat.run_chat(
                        palamedes_module=isolated,
                        provider=provider,
                        session_id="micro-one-call",
                        input_stream=io.StringIO(
                            "/cycle --mode micro Fix one bounded parser rule\n/quit\n"
                        ),
                        output=output,
                    )
        self.assertEqual(len(provider.calls), 1)
        self.assertIn("mode=micro", output.getvalue())
        self.assertIn("mission_compiler", output.getvalue())

    def test_chat_stale_satisfaction_does_not_force_zero_call_lookup(self):
        from palamedes_satisfaction import SatisfactionStore, workspace_snapshot

        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            with PalamedesIsolation(root) as isolated:
                SatisfactionStore(isolated.STATE_DIR / "satisfaction").save({
                    "assessment_id": "satisfaction-cccccccccccccccc",
                    "requirement_id": "req-stale",
                    "disposition": "already_satisfied",
                    "current_snapshot": workspace_snapshot(root),
                    "observed_at": palamedes_chat.utc_now(),
                    "ttl_days": 30,
                })
                (root / "drift.txt").write_text("new worktree state")
                provider = StaticChatProvider()
                output = io.StringIO()
                palamedes_chat.run_chat(
                    palamedes_module=isolated,
                    provider=provider,
                    session_id="lookup-stale",
                    input_stream=io.StringIO("/cycle verify req-stale again\n/quit\n"),
                    output=output,
                )
        self.assertNotEqual(provider.calls, [])
        self.assertNotIn("mode=lookup", output.getvalue())

    def test_completed_work_is_classified_as_audit_not_origination(self):
        class RetrospectiveOriginClaimProvider(StaticChatProvider):
            def stream(self, messages):
                if "ROLE: selector" in messages[-1]["content"]:
                    payload = json.loads("".join(super().stream(messages)))
                    payload["implementation_state_at_start"] = "completed"
                    payload["causal_role"] = "originated"
                    yield json.dumps(payload)
                    return
                yield from super().stream(messages)

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            provider = RetrospectiveOriginClaimProvider()
            store = palamedes_chat.CognitionCycleStore(
                fake.STATE_DIR / "missions" / "cognition"
            )

            with self.assertRaisesRegex(
                ValueError, "completed work must be classified as audited"
            ):
                palamedes_chat.run_cognition_cycle(
                    provider=provider,
                    palamedes_module=fake,
                    context="Audit an implementation that is already complete",
                    cycle_store=store,
                )

            cycle = json.loads(next(store.root.glob("*.json")).read_text())

        self.assertEqual(cycle["status"], "failed")
        self.assertEqual(cycle["live_model_call_count"], 4)

    def test_selector_cannot_claim_an_unavailable_discovery(self):
        class FalseLineageProvider(StaticChatProvider):
            def stream(self, messages):
                if "ROLE: selector" in messages[-1]["content"]:
                    payload = json.loads("".join(super().stream(messages)))
                    payload["source_discovery_ids"] = ["discovery-falseclaim"]
                    yield json.dumps(payload)
                    return
                yield from super().stream(messages)

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            with self.assertRaisesRegex(
                ValueError, "unavailable discovery ID"
            ):
                palamedes_chat.run_cognition_cycle(
                    provider=FalseLineageProvider(),
                    palamedes_module=fake,
                    context="Select from available evidence",
                    cycle_store=palamedes_chat.CognitionCycleStore(
                        fake.STATE_DIR / "missions" / "cognition"
                    ),
                    available_discovery_ids={"discovery-real123456"},
                )

    def test_revise_outcome_blocks_unanswered_next_mission(self):
        class ReviseProvider(StaticChatProvider):
            def stream(self, messages):
                if "ROLE: outcome_analyst" in messages[-1]["content"]:
                    self.calls.append(messages)
                    yield json.dumps(
                        {
                            "observed_vs_expected": "The result exposed a missing check.",
                            "attribution_hypotheses": [
                                {
                                    "layer": "mission",
                                    "claim": "The acceptance contract was incomplete",
                                    "confidence": 70,
                                }
                            ],
                            "belief_updates": ["Repair the contract before expansion"],
                            "causal_signature": "missing-comparison-evidence",
                            "mechanism_summary": "The probe lacked the comparison needed for attribution.",
                            "work_scale": "component",
                            "surface_key": "mission-comparison-evidence",
                            "finding_lane": "inconclusive",
                            "exploration_value": 70,
                            "hypothesis_scope": "",
                            "probe_status": "incomplete",
                            "finding": "inconclusive",
                            "mission_disposition": "revise",
                            "followup_required": True,
                            "followup_kind": "new_probe",
                            "successor_scope": "Add the missing comparison",
                            "next_probe": "Add the missing comparison",
                            "confidence": 70,
                        }
                    )
                    return
                yield from super().stream(messages)

        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            with PalamedesIsolation(root) as isolated:
                provider = ReviseProvider()
                mission_store = palamedes_chat.MissionStore(
                    isolated.STATE_DIR / "missions"
                )
                cycle_store = palamedes_chat.CognitionCycleStore(
                    isolated.STATE_DIR / "missions" / "cognition"
                )
                result = palamedes_chat.run_cognition_cycle(
                    provider=provider,
                    palamedes_module=isolated,
                    context="Choose a bounded proof",
                    cycle_store=cycle_store,
                )
                approved = palamedes_chat.approve_mission(
                    isolated, mission_store, result["contract"], "gate-test"
                )["contract"]
                outcome = palamedes_chat.record_mission_outcome(
                    isolated,
                    mission_store,
                    approved,
                    "mixed",
                    "The implementation passed but the comparison is missing",
                )
                palamedes_chat.run_outcome_analyst(
                    provider=provider,
                    cycle_store=cycle_store,
                    mission_store=mission_store,
                    contract=approved,
                    outcome=outcome,
                )

                unanswered = palamedes_chat.validate_mission_draft(
                    StaticChatProvider._mission_payload()
                )
                with self.assertRaisesRegex(
                    ValueError, "blocked by unresolved outcome evidence"
                ):
                    palamedes_chat.approve_mission(
                        isolated, mission_store, unanswered, "gate-test"
                    )

                response_payload = StaticChatProvider._mission_payload()
                response_payload["mission"] = "Resolve the missing comparison evidence"
                response_payload["outcome_response"] = {
                    "related_outcome_ids": [outcome["outcome_id"]],
                    "action": "resolve",
                    "rationale": "The next probe directly adds the missing comparison.",
                }
                response = palamedes_chat.validate_mission_draft(response_payload)
                successor = palamedes_chat.approve_mission(
                    isolated, mission_store, response, "gate-test"
                )["contract"]

                open_after_approval = mission_store.open_outcome_gates()
                successor_outcome = palamedes_chat.record_mission_outcome(
                    isolated,
                    mission_store,
                    successor,
                    "success",
                    "The missing comparison was produced and verified.",
                )
                palamedes_chat.run_outcome_analyst(
                    provider=provider,
                    cycle_store=cycle_store,
                    mission_store=mission_store,
                    contract=successor,
                    outcome=successor_outcome,
                )

        self.assertEqual(len(open_after_approval), 1)
        self.assertEqual(
            open_after_approval[0]["successor_state"],
            "approved_awaiting_outcome",
        )
        self.assertEqual(mission_store.open_outcome_gates(), [])

    def test_unrelated_open_gate_does_not_block_surface_scoped_approval(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            with PalamedesIsolation(root) as isolated:
                mission_store = palamedes_chat.MissionStore(
                    isolated.STATE_DIR / "missions"
                )
                mission_store.append_outcome_gate(
                    {
                        "gate_version": "palamedes-outcome-gate/2",
                        "gate_id": "gate-unrelatedscope",
                        "outcome_id": "outcome-unrelated",
                        "mission_contract_id": "mission-unrelated",
                        "status": "open",
                        "finding": "qualifying_defect",
                        "followup_kind": "production_correction",
                        "followup_required": True,
                        "probe_status": "completed",
                        "mission_disposition": "revise",
                    }
                )

                contract = palamedes_chat.validate_mission_draft(
                    {
                        **StaticChatProvider._mission_payload(),
                        "surface_key": "new-feature-surface",
                    }
                )
                approved = palamedes_chat.approve_mission(
                    isolated,
                    mission_store,
                    contract,
                    "scope-test",
                )

        self.assertEqual(approved["contract"]["status"], "approved")

    def test_successful_probe_can_stop_with_defect_and_keep_followup_gate_open(self):
        class DefectProvider(StaticChatProvider):
            def stream(self, messages):
                if "ROLE: outcome_analyst" in messages[-1]["content"]:
                    self.calls.append(messages)
                    yield json.dumps(
                        {
                            "observed_vs_expected": "The probe completed and reproduced a guidance defect.",
                            "attribution_hypotheses": [
                                {
                                    "layer": "implementation",
                                    "claim": "Committed state outranked presentation state",
                                    "confidence": 90,
                                }
                            ],
                            "belief_updates": ["Presentation precedence needs correction"],
                            "causal_signature": "presentation-state-precedence",
                            "mechanism_summary": "Committed state outranked an active presentation boundary.",
                            "work_scale": "micro",
                            "surface_key": "presentation-guidance",
                            "finding_lane": "correctness_defect",
                            "exploration_value": 80,
                            "hypothesis_scope": "",
                            "probe_status": "completed",
                            "finding": "qualifying_defect",
                            "mission_disposition": "stop",
                            "followup_required": True,
                            "followup_kind": "production_correction",
                            "successor_scope": "Correct guidance precedence for the reproduced trace",
                            "next_probe": "Implement the bounded correction",
                            "confidence": 90,
                        }
                    )
                    return
                yield from super().stream(messages)

        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            with PalamedesIsolation(root) as isolated:
                provider = DefectProvider()
                mission_store = palamedes_chat.MissionStore(
                    isolated.STATE_DIR / "missions"
                )
                cycle_store = palamedes_chat.CognitionCycleStore(
                    isolated.STATE_DIR / "missions" / "cognition"
                )
                result = palamedes_chat.run_cognition_cycle(
                    provider=provider,
                    palamedes_module=isolated,
                    context="Probe one presentation boundary",
                    cycle_store=cycle_store,
                )
                approved = palamedes_chat.approve_mission(
                    isolated, mission_store, result["contract"], "semantic-test"
                )["contract"]
                outcome = palamedes_chat.record_mission_outcome(
                    isolated,
                    mission_store,
                    approved,
                    "success",
                    "The probe completed and found one exact mismatch",
                )
                palamedes_chat.run_outcome_analyst(
                    provider=provider,
                    cycle_store=cycle_store,
                    mission_store=mission_store,
                    contract=approved,
                    outcome=outcome,
                )

                gate = mission_store.open_outcome_gates()[0]
                stored_contract = mission_store.load_contract(approved["mission_id"])
                interpretations = [
                    json.loads(line)
                    for line in mission_store.outcome_interpretations_path.read_text(
                        encoding="utf-8"
                    ).splitlines()
                ]
                experience = json.loads(
                    next(
                        (isolated.STATE_DIR / "thoughts" / "experiences").glob(
                            "*.json"
                        )
                    ).read_text(encoding="utf-8")
                )

                independent_payload = StaticChatProvider._mission_payload()
                independent_payload["mission"] = "Audit an unrelated rule surface"
                independent_payload["surface_key"] = "unrelated-rule-surface"
                independent = palamedes_chat.validate_mission_draft(
                    independent_payload
                )
                independent.pop("scope_keys")
                independent_approved = palamedes_chat.approve_mission(
                    isolated, mission_store, independent, "semantic-test"
                )["contract"]
                still_open = mission_store.open_outcome_gates()
                palamedes_chat.record_mission_outcome(
                    isolated,
                    mission_store,
                    independent_approved,
                    "success",
                    "The unrelated bounded audit completed.",
                )

                resolving_payload = StaticChatProvider._mission_payload()
                resolving_payload["mission"] = (
                    "Correct guidance precedence for the reproduced trace"
                )
                resolving_payload["surface_key"] = "presentation-guidance"
                resolving_payload["outcome_response"] = {
                    "related_outcome_ids": [outcome["outcome_id"]],
                    "action": "resolve",
                    "rationale": "This mission implements the exact required successor scope.",
                }
                resolving = palamedes_chat.validate_mission_draft(
                    resolving_payload
                )
                palamedes_chat.approve_mission(
                    isolated, mission_store, resolving, "semantic-test"
                )
                open_after_resolving_approval = mission_store.open_outcome_gates()

        self.assertEqual(gate["probe_status"], "completed")
        self.assertEqual(gate["finding"], "qualifying_defect")
        self.assertEqual(gate["mission_disposition"], "stop")
        self.assertTrue(gate["followup_required"])
        self.assertEqual(gate["followup_kind"], "production_correction")
        self.assertEqual(gate["surface_key"], "presentation-guidance")
        self.assertEqual(gate["scope_keys"], ["surface:presentation-guidance"])
        self.assertEqual(stored_contract["latest_finding"], "qualifying_defect")
        self.assertTrue(stored_contract["latest_followup_required"])
        self.assertEqual(interpretations[0]["finding"], "qualifying_defect")
        self.assertEqual(experience["probe_status"], "completed")
        self.assertEqual(experience["finding"], "qualifying_defect")
        self.assertEqual(
            experience["causal_signature"], "presentation-state-precedence"
        )
        self.assertTrue(experience["followup_required"])
        self.assertEqual(experience["followup_kind"], "production_correction")
        self.assertEqual(
            experience["successor_scope"],
            "Correct guidance precedence for the reproduced trace",
        )
        self.assertEqual(len(still_open), 1)
        self.assertEqual(still_open[0]["status"], "open")
        self.assertNotIn("response_mission_contract_id", still_open[0])
        self.assertEqual(len(open_after_resolving_approval), 1)
        self.assertEqual(
            open_after_resolving_approval[0]["successor_state"],
            "approved_awaiting_outcome",
        )

    def test_outcome_records_honest_type_and_blocks_invalid_environment_success(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            with PalamedesIsolation(root) as isolated:
                mission_store = palamedes_chat.MissionStore(isolated.STATE_DIR / "missions")
                contract = palamedes_chat.validate_mission_draft(StaticChatProvider._mission_payload())
                contract["status"] = "approved"
                mission_store.save_contract(contract)
                with self.assertRaisesRegex(ValueError, "requires unknown"):
                    palamedes_chat.record_mission_outcome(
                        isolated, mission_store, contract, "success", "No runtime", None,
                        "blocked_by_environment",
                    )
                outcome = palamedes_chat.record_mission_outcome(
                    isolated, mission_store, contract, "unknown",
                    "Independent users are unavailable in this environment.", None,
                    "blocked_by_environment",
                )
        self.assertEqual(outcome["outcome_type"], "blocked_by_environment")

    def test_completed_execution_without_evaluator_remains_not_evaluated(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            with PalamedesIsolation(root) as isolated:
                mission_store = palamedes_chat.MissionStore(
                    isolated.STATE_DIR / "missions"
                )
                contract = palamedes_chat.validate_mission_draft(
                    StaticChatProvider._mission_payload()
                )
                contract["status"] = "approved"
                mission_store.save_contract(contract)

                outcome = palamedes_chat.record_mission_outcome(
                    isolated,
                    mission_store,
                    contract,
                    "success",
                    "The implementer reports that delivery completed.",
                    execution_status="completed",
                )

                stored_contract = mission_store.load_contract(contract["mission_id"])
                plan = isolated.load_plan()

        self.assertEqual(outcome["execution_status"], "completed")
        self.assertEqual(outcome["reported_outcome_status"], "success")
        self.assertEqual(outcome["evaluation_status"], "not_evaluated")
        self.assertNotIn(
            "validated",
            [
                item.get("status")
                for item in plan.get("hypothesis_log", [])
                if item.get("mission_contract_id") == contract["mission_id"]
            ],
        )
        self.assertEqual(
            stored_contract["latest_evaluation_status"], "not_evaluated"
        )

    def test_outcome_rejects_invalid_execution_status(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            with PalamedesIsolation(root) as isolated:
                mission_store = palamedes_chat.MissionStore(
                    isolated.STATE_DIR / "missions"
                )
                contract = palamedes_chat.validate_mission_draft(
                    StaticChatProvider._mission_payload()
                )
                contract["status"] = "approved"

                with self.assertRaisesRegex(ValueError, "execution_status"):
                    palamedes_chat.record_mission_outcome(
                        isolated,
                        mission_store,
                        contract,
                        "unknown",
                        "The host returned an unsupported execution state.",
                        execution_status="approved",
                    )

    def test_cycle_failure_preserves_partial_artifacts_without_mission(self):
        class FailingAdversaryProvider(StaticChatProvider):
            def stream(self, messages):
                if "ROLE: adversary" in messages[-1]["content"]:
                    self.calls.append(messages)
                    yield '{"critiques":[]}'
                    return
                yield from super().stream(messages)

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            provider = FailingAdversaryProvider()
            output = io.StringIO()
            with patch.dict(os.environ, {"PALAMEDES_REF_ROOT": ""}):
                palamedes_chat.run_chat(
                    palamedes_module=fake,
                    provider=provider,
                    session_id="failed-cycle",
                    input_stream=io.StringIO(
                        "/cycle pressure the current direction\n/quit\n"
                    ),
                    output=output,
                )
            cycle_path = next(
                (fake.STATE_DIR / "missions" / "cognition").glob("cycle-*.json")
            )
            cycle = json.loads(cycle_path.read_text(encoding="utf-8"))
            mission_files = list(
                (fake.STATE_DIR / "missions").glob("mission-*.json")
            )

        self.assertEqual(cycle["status"], "failed")
        self.assertEqual(
            [item["role"] for item in cycle["artifacts"]],
            ["context_governor", "interpreter", "inventor"],
        )
        self.assertEqual(mission_files, [])
        self.assertIn("no mission draft was issued", output.getvalue())

    def test_new_session_does_not_overwrite_previous_history(self):
        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            provider = StaticChatProvider()
            output = io.StringIO()

            palamedes_chat.run_chat(
                palamedes_module=fake,
                provider=provider,
                session_id="original",
                input_stream=io.StringIO("first\n/new\nsecond\n/quit\n"),
                output=output,
            )
            sessions = palamedes_chat.ChatSessionStore(
                fake.STATE_DIR / "chat"
            ).list_sessions()

        self.assertEqual(len(sessions), 2)
        self.assertIn("original", sessions)

    def test_session_id_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = palamedes_chat.ChatSessionStore(Path(tempdir))
            with self.assertRaises(ValueError):
                store.path("../outside")

    def test_sse_parser_ignores_metadata_and_done(self):
        response = [
            b"event: response.output_text.delta\n",
            b'data: {"type":"response.output_text.delta","delta":"hello"}\n',
            b"\n",
            b"data: [DONE]\n",
        ]

        self.assertEqual(
            list(palamedes_chat._sse_events(response)),
            [{"type": "response.output_text.delta", "delta": "hello"}],
        )

    def test_provider_health_never_returns_secret(self):
        health = palamedes_chat.provider_health("openrouter")

        self.assertNotIn("api_key", health)
        self.assertIn("api_key_set", health)

    def test_codex_provider_runs_ephemeral_read_only_and_isolated(self):
        provider = palamedes_chat.CodexCliChatProvider()
        completed = SimpleNamespace(
            returncode=0,
            stdout="\n".join(
                [
                    json.dumps(
                        {
                            "type": "item.completed",
                            "item": {
                                "type": "agent_message",
                                "text": '{"observations":["bounded"]}',
                            },
                        }
                    ),
                    json.dumps(
                        {
                            "type": "turn.completed",
                            "usage": {
                                "input_tokens": 120,
                                "cached_input_tokens": 80,
                                "output_tokens": 10,
                            },
                        }
                    ),
                ]
            ),
            stderr="",
        )
        with patch("palamedes_chat.shutil.which", return_value="/bin/codex"), patch(
            "palamedes_chat.subprocess.run", return_value=completed
        ) as run:
            output = "".join(
                provider.stream(
                    [
                        {"role": "system", "content": "Return JSON."},
                        {"role": "user", "content": "Interpret this snapshot."},
                    ]
                )
            )

        command = run.call_args.args[0]
        self.assertEqual(output, '{"observations":["bounded"]}')
        self.assertEqual(provider.last_usage["input_tokens"], 120)
        self.assertIn("--ephemeral", command)
        self.assertIn("read-only", command)
        self.assertIn("--skip-git-repo-check", command)
        self.assertIn("--json", command)
        self.assertTrue(run.call_args.kwargs["cwd"].startswith("/"))
        self.assertIn(
            "Do not inspect the filesystem", run.call_args.kwargs["input"]
        )

    def test_codex_provider_health_requires_only_the_cli_at_preflight(self):
        with patch("palamedes_chat.shutil.which", return_value="/bin/codex"):
            health = palamedes_chat.provider_health("codex")

        self.assertEqual(health["status"], "ok")
        self.assertNotIn("api_key_env", health)

    def test_system_prompt_contains_plan_only_authority_boundary(self):
        with tempfile.TemporaryDirectory() as tempdir:
            prompt = palamedes_chat.system_prompt(
                FakePalamedes(Path(tempdir)), Path(tempdir)
            )

        self.assertIn("plan-only", prompt)
        self.assertIn("cannot claim", prompt)

    def test_cognition_cycle_resumes_only_missing_role_after_runtime_failure(self):
        class SelectorFailsOnceProvider(StaticChatProvider):
            def __init__(self):
                super().__init__()
                self.failed = False

            def stream(self, messages):
                if (
                    messages[-1]["content"].startswith("ROLE: selector")
                    and not self.failed
                ):
                    self.calls.append(messages)
                    self.failed = True
                    raise RuntimeError("transient selector failure")
                yield from super().stream(messages)

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            provider = SelectorFailsOnceProvider()
            store = palamedes_chat.CognitionCycleStore(
                fake.STATE_DIR / "missions" / "cognition"
            )
            with self.assertRaisesRegex(RuntimeError, "transient selector"):
                palamedes_chat.run_cognition_cycle(
                    provider=provider,
                    palamedes_module=fake,
                    context="Choose one bounded mission.",
                    cycle_store=store,
                )
            result = palamedes_chat.run_cognition_cycle(
                provider=provider,
                palamedes_module=fake,
                context="Choose one bounded mission.",
                cycle_store=store,
            )

        self.assertEqual(len(provider.calls), 6)
        self.assertEqual(result["cycle"]["live_model_call_count"], 1)
        self.assertEqual(
            [row["role"] for row in result["cycle"]["artifacts"]],
            [
                "context_governor",
                "interpreter",
                "inventor",
                "adversary",
                "selector",
            ],
        )
        self.assertTrue(all(
            row.get("checkpoint_reused")
            for row in result["cycle"]["artifacts"][:3]
        ))

    def test_cognition_cycle_retries_only_schema_invalid_role_once(self):
        class SelectorReturnsInvalidConfidenceOnce(StaticChatProvider):
            def __init__(self):
                super().__init__()
                self.invalid_returned = False

            def stream(self, messages):
                if (
                    messages[-1]["content"].startswith("ROLE: selector")
                    and not self.invalid_returned
                ):
                    payload = json.loads("".join(super().stream(messages)))
                    payload["mission_contract"]["evidence"][0]["confidence"] = "35%"
                    self.invalid_returned = True
                    yield json.dumps(payload)
                    return
                yield from super().stream(messages)

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            provider = SelectorReturnsInvalidConfidenceOnce()
            progress = []
            result = palamedes_chat.run_cognition_cycle(
                provider=provider,
                palamedes_module=fake,
                context="Choose one bounded mission.",
                cycle_store=palamedes_chat.CognitionCycleStore(
                    fake.STATE_DIR / "missions" / "cognition"
                ),
                progress=progress.append,
            )

        role_prompts = [call[-1]["content"].splitlines()[0] for call in provider.calls]
        self.assertEqual(
            role_prompts,
            [
                "ROLE: context_governor",
                "ROLE: interpreter",
                "ROLE: inventor",
                "ROLE: adversary",
                "ROLE: selector",
                "ROLE: selector",
            ],
        )
        self.assertEqual(result["cycle"]["live_model_call_count"], 1)
        self.assertEqual(result["cycle"]["provider_usage"]["attempted_calls"], 6)
        self.assertEqual(len(result["cycle"]["rejected_artifacts"]), 1)
        self.assertEqual(
            result["cycle"]["rejected_artifacts"][0]["role"], "selector"
        )
        self.assertIn(
            "confidence must be an integer",
            result["cycle"]["rejected_artifacts"][0]["rejection_reason"],
        )
        self.assertEqual(
            [row["role"] for row in result["cycle"]["artifacts"]],
            [
                "context_governor",
                "interpreter",
                "inventor",
                "adversary",
                "selector",
            ],
        )
        self.assertTrue(all(
            row.get("checkpoint_reused")
            for row in result["cycle"]["artifacts"][:3]
        ))
        self.assertTrue(any("retrying only that role once" in row for row in progress))

    def test_open_gate_on_another_surface_does_not_block_a_scoped_mission(self):
        class ReviseProvider(StaticChatProvider):
            def stream(self, messages):
                if "ROLE: outcome_analyst" in messages[-1]["content"]:
                    yield json.dumps(
                        {
                            "observed_vs_expected": "The result exposed a missing check.",
                            "attribution_hypotheses": [
                                {
                                    "layer": "mission",
                                    "claim": "The acceptance contract was incomplete",
                                    "confidence": 70,
                                }
                            ],
                            "belief_updates": ["Repair the contract before expansion"],
                            "causal_signature": "missing-comparison-evidence",
                            "mechanism_summary": "The probe lacked the comparison.",
                            "work_scale": "component",
                            "surface_key": "mission-comparison-evidence",
                            "finding_lane": "inconclusive",
                            "exploration_value": 70,
                            "hypothesis_scope": "",
                            "probe_status": "incomplete",
                            "finding": "inconclusive",
                            "mission_disposition": "revise",
                            "followup_required": True,
                            "followup_kind": "new_probe",
                            "successor_scope": "Add the missing comparison",
                            "next_probe": "Add the missing comparison",
                            "confidence": 70,
                        }
                    )
                    return
                yield from super().stream(messages)

        with tempfile.TemporaryDirectory() as tempdir:
            with PalamedesIsolation(Path(tempdir)) as isolated:
                provider = ReviseProvider()
                mission_store = palamedes_chat.MissionStore(
                    isolated.STATE_DIR / "missions"
                )
                cycle_store = palamedes_chat.CognitionCycleStore(
                    isolated.STATE_DIR / "missions" / "cognition"
                )
                result = palamedes_chat.run_cognition_cycle(
                    provider=provider,
                    palamedes_module=isolated,
                    context="Choose a bounded proof",
                    cycle_store=cycle_store,
                )
                approved = palamedes_chat.approve_mission(
                    isolated, mission_store, result["contract"], "gate-test"
                )["contract"]
                outcome = palamedes_chat.record_mission_outcome(
                    isolated,
                    mission_store,
                    approved,
                    "mixed",
                    "The implementation passed but the comparison is missing",
                )
                palamedes_chat.run_outcome_analyst(
                    provider=provider,
                    cycle_store=cycle_store,
                    mission_store=mission_store,
                    contract=approved,
                    outcome=outcome,
                )
                self.assertTrue(mission_store.open_outcome_gates())

                payload = StaticChatProvider._mission_payload()
                payload["surface_key"] = "billing-refunds"
                payload["mission"] = "Unrelated billing refund probe"
                elsewhere = palamedes_chat.validate_mission_draft(payload)
                self.assertIn("surface:billing-refunds", elsewhere["scope_keys"])

                # The gate belongs to another surface, and this contract proves
                # where it lives, so approval proceeds without answering it.
                palamedes_chat.approve_mission(
                    isolated, mission_store, elsewhere, "gate-test"
                )

    def test_selector_prompt_states_which_discovery_ids_may_be_cited(self):
        class PromptCapturingProvider(StaticChatProvider):
            def __init__(self):
                super().__init__()
                self.prompts = []

            def stream(self, messages):
                self.prompts.append(messages[-1].get("content", ""))
                yield from super().stream(messages)

        def selector_prompt(provider):
            return next(
                prompt
                for prompt in provider.prompts
                if prompt.startswith("ROLE: selector")
            )

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            empty_provider = PromptCapturingProvider()
            palamedes_chat.run_cognition_cycle(
                provider=empty_provider,
                palamedes_module=fake,
                context="Choose one bounded mission.",
                cycle_store=palamedes_chat.CognitionCycleStore(
                    fake.STATE_DIR / "missions" / "cognition"
                ),
            )
            self.assertIn(
                "source_discovery_ids must be an empty array",
                selector_prompt(empty_provider),
            )

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            listing_provider = PromptCapturingProvider()
            palamedes_chat.run_cognition_cycle(
                provider=listing_provider,
                palamedes_module=fake,
                context="Choose one bounded mission.",
                cycle_store=palamedes_chat.CognitionCycleStore(
                    fake.STATE_DIR / "missions" / "cognition"
                ),
                available_discovery_ids={"discovery-b", "discovery-a"},
            )
            self.assertIn(
                '["discovery-a", "discovery-b"]',
                selector_prompt(listing_provider),
            )

    def test_cycle_prompts_prefer_bounded_action_over_meta_validation(self):
        class PromptCapturingProvider(StaticChatProvider):
            def __init__(self):
                super().__init__()
                self.prompts = []

            def stream(self, messages):
                self.prompts.append(messages[-1].get("content", ""))
                yield from super().stream(messages)

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            provider = PromptCapturingProvider()
            palamedes_chat.run_cognition_cycle(
                provider=provider,
                palamedes_module=fake,
                context="Choose the smallest experiment that tests user value.",
                cycle_store=palamedes_chat.CognitionCycleStore(
                    fake.STATE_DIR / "missions" / "cognition"
                ),
            )

        inventor = next(
            prompt for prompt in provider.prompts if prompt.startswith("ROLE: inventor")
        )
        adversary = next(
            prompt for prompt in provider.prompts if prompt.startswith("ROLE: adversary")
        )
        selector = next(
            prompt for prompt in provider.prompts if prompt.startswith("ROLE: selector")
        )
        self.assertIn("at least two candidates", inventor)
        self.assertIn("small, reversible action", inventor)
        self.assertIn("cannot safely learn", adversary)
        self.assertIn("publication-grade evidence is normally repairable", adversary)
        self.assertIn("observable user or beneficiary response", selector)
        self.assertIn("every action candidate is explicitly marked", selector)
        self.assertIn("Weak evidence should narrow the action", selector)
        self.assertIn("must reach\nthe intervention", selector)
        self.assertIn("terminal output cannot be only a packet", selector)

    def test_cycle_budget_stops_a_role_before_an_unaffordable_call(self):
        class MeteredProvider(StaticChatProvider):
            def stream(self, messages):
                self.last_usage = None
                yield from super().stream(messages)
                self.last_usage = {
                    "input_tokens": 1000,
                    "output_tokens": 200,
                    "total_tokens": 1200,
                }

        def run(tempdir, budget):
            fake = FakePalamedes(Path(tempdir))
            return palamedes_chat.run_cognition_cycle(
                provider=MeteredProvider(),
                palamedes_module=fake,
                context="Choose one bounded mission.",
                cycle_store=palamedes_chat.CognitionCycleStore(
                    fake.STATE_DIR / "missions" / "cognition"
                ),
                budget=budget,
            )

        with tempfile.TemporaryDirectory() as tempdir:
            with self.assertRaisesRegex(ValueError, "token budget exhausted"):
                run(tempdir, {"provider_calls_max": 99, "token_budget_high": 2500})

        with tempfile.TemporaryDirectory() as tempdir:
            with self.assertRaisesRegex(ValueError, "provider-call budget exhausted"):
                run(tempdir, {"provider_calls_max": 2, "token_budget_high": 10 ** 9})

        with tempfile.TemporaryDirectory() as tempdir:
            result = run(
                tempdir, {"provider_calls_max": 99, "token_budget_high": 10 ** 9}
            )
            self.assertEqual(len(result["cycle"]["artifacts"]), 5)

    def test_schema_retry_tells_the_role_what_the_contract_rejected(self):
        class SelectorRecoversAfterFeedback(StaticChatProvider):
            def __init__(self):
                super().__init__()
                self.selector_prompts = []

            def stream(self, messages):
                content = messages[-1]["content"]
                if "ROLE: selector" in content:
                    self.selector_prompts.append(content)
                    if len(self.selector_prompts) == 1:
                        yield json.dumps({"decision": "not-a-decision"})
                        return
                yield from super().stream(messages)

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            provider = SelectorRecoversAfterFeedback()
            result = palamedes_chat.run_cognition_cycle(
                provider=provider,
                palamedes_module=fake,
                context="Choose one bounded mission.",
                cycle_store=palamedes_chat.CognitionCycleStore(
                    fake.STATE_DIR / "missions" / "cognition"
                ),
            )

        self.assertEqual(len(provider.selector_prompts), 2)
        first, retry = provider.selector_prompts
        self.assertNotIn("rejected by the machine contract", first)
        self.assertIn("rejected by the machine contract", retry)
        self.assertIn("selector decision must be select, defer, or reject", retry)
        self.assertIn("Do not weaken or change your conclusion", retry)
        self.assertEqual(result["cycle"]["status"], "selected")

    def test_budget_overrun_is_disclosed_on_both_success_and_failure(self):
        class MeteredProvider(StaticChatProvider):
            def stream(self, messages):
                self.last_usage = None
                yield from super().stream(messages)
                self.last_usage = {
                    "input_tokens": 1000,
                    "output_tokens": 200,
                    "total_tokens": 1200,
                }

        class InvalidSelectorProvider(MeteredProvider):
            def stream(self, messages):
                if "ROLE: selector" in messages[-1]["content"]:
                    self.last_usage = None
                    yield json.dumps({"decision": "not-a-decision"})
                    self.last_usage = {
                        "input_tokens": 1000,
                        "output_tokens": 200,
                        "total_tokens": 1200,
                    }
                    return
                yield from super().stream(messages)

        # A ceiling above the first role but below the finished cycle is spent
        # mid-run, so the gate permits the role that crosses it and the overrun
        # must still be reported.
        budget = {"provider_calls_max": 99, "token_budget_high": 5000}

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            progress = []
            palamedes_chat.run_cognition_cycle(
                provider=MeteredProvider(),
                palamedes_module=fake,
                context="Choose one bounded mission.",
                cycle_store=palamedes_chat.CognitionCycleStore(
                    fake.STATE_DIR / "missions" / "cognition"
                ),
                budget=budget,
                progress=progress.append,
            )
            self.assertTrue(
                any("BUDGET OVERRUN" in row for row in progress),
                progress,
            )

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            progress = []
            with self.assertRaises(ValueError):
                palamedes_chat.run_cognition_cycle(
                    provider=InvalidSelectorProvider(),
                    palamedes_module=fake,
                    context="Choose one bounded mission.",
                    cycle_store=palamedes_chat.CognitionCycleStore(
                        fake.STATE_DIR / "missions" / "cognition"
                    ),
                    budget=budget,
                    progress=progress.append,
                    schema_retry_limit=0,
                )
            self.assertTrue(
                any("BUDGET OVERRUN" in row for row in progress),
                progress,
            )

    def test_cycle_budget_spent_counts_rejected_artifacts(self):
        self.assertEqual(
            palamedes_chat._cycle_budget_spent(
                {
                    "artifacts": [{"provider_usage": {"total_tokens": 10}}],
                    "rejected_artifacts": [{"provider_usage": {"total_tokens": 5}}],
                }
            ),
            (2, 15),
        )

    def test_explicit_resume_reuses_legacy_checkpoints_after_plan_drift(self):
        class InvalidSelectorProvider(StaticChatProvider):
            def stream(self, messages):
                if messages[-1]["content"].startswith("ROLE: selector"):
                    payload = json.loads("".join(super().stream(messages)))
                    payload["mission_contract"]["evidence"][0]["confidence"] = "35%"
                    yield json.dumps(payload)
                    return
                yield from super().stream(messages)

        class MutablePlanPalamedes(FakePalamedes):
            def __init__(self, root):
                super().__init__(root)
                self.goal = "initial goal"

            def load_plan(self):
                plan = super().load_plan()
                plan["goal"] = self.goal
                return plan

        with tempfile.TemporaryDirectory() as tempdir:
            fake = MutablePlanPalamedes(Path(tempdir))
            store = palamedes_chat.CognitionCycleStore(
                fake.STATE_DIR / "missions" / "cognition"
            )
            with self.assertRaisesRegex(ValueError, "confidence must be an integer"):
                palamedes_chat.run_cognition_cycle(
                    provider=InvalidSelectorProvider(),
                    palamedes_module=fake,
                    context="Choose one bounded mission.",
                    cycle_store=store,
                    schema_retry_limit=0,
                )
            failed = json.loads(next(store.root.glob("cycle-*.json")).read_text())
            fake.goal = "changed after the failed run"
            provider = StaticChatProvider()
            result = palamedes_chat.run_cognition_cycle(
                provider=provider,
                palamedes_module=fake,
                context="ignored during explicit resume",
                cycle_store=store,
                resume_cycle_id=failed["cognition_cycle_id"],
            )

        self.assertEqual(result["cycle"]["cognition_cycle_id"], failed["cognition_cycle_id"])
        self.assertEqual(len(provider.calls), 1)
        self.assertEqual(provider.calls[0][-1]["content"].splitlines()[0], "ROLE: selector")
        self.assertTrue(all(
            artifact.get("checkpoint_reused")
            for artifact in result["cycle"]["artifacts"][:3]
        ))
        self.assertEqual(result["cycle"]["plan_context"]["goal"], "initial goal")

    def test_explicit_resume_rejects_tampered_checkpoint(self):
        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            store = palamedes_chat.CognitionCycleStore(
                fake.STATE_DIR / "missions" / "cognition"
            )
            result = palamedes_chat.run_cognition_cycle(
                provider=StaticChatProvider(),
                palamedes_module=fake,
                context="Choose one bounded mission.",
                cycle_store=store,
            )
            cycle = result["cycle"]
            cycle["status"] = "failed"
            cycle["artifacts"][0]["output"]["observations"] = ["tampered"]
            store.save(cycle)

            with self.assertRaisesRegex(ValueError, "checkpoint fingerprint mismatch"):
                palamedes_chat.run_cognition_cycle(
                    provider=StaticChatProvider(),
                    palamedes_module=fake,
                    context="ignored",
                    cycle_store=store,
                    resume_cycle_id=cycle["cognition_cycle_id"],
                )

    def test_vision_genesis_resumes_completed_roles_after_runtime_failure(self):
        class AnalogyFailsOnceProvider(StaticChatProvider):
            def __init__(self):
                super().__init__()
                self.failed = False

            def stream(self, messages):
                if (
                    messages[-1]["content"].startswith(
                        "ROLE: distant_analogy_explorer"
                    )
                    and not self.failed
                ):
                    self.calls.append(messages)
                    self.failed = True
                    raise RuntimeError("transient analogy failure")
                yield from super().stream(messages)

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            mission_store = palamedes_chat.MissionStore(
                fake.STATE_DIR / "missions"
            )
            provider = AnalogyFailsOnceProvider()
            context = "Originate a durable product world."
            with self.assertRaisesRegex(RuntimeError, "transient analogy"):
                palamedes_chat.run_autonomous_vision(
                    provider=provider,
                    mission_store=mission_store,
                    context=context,
                )
            record = palamedes_chat.run_autonomous_vision(
                provider=provider,
                mission_store=mission_store,
                context=context,
            )

        self.assertEqual(len(provider.calls), 8)
        self.assertTrue(record["provider_usage"]["roles"][0]["checkpoint_reused"])
        self.assertTrue(record["provider_usage"]["roles"][1]["checkpoint_reused"])

    def test_explicit_mission_id_accepts_outcome_from_new_session(self):
        with tempfile.TemporaryDirectory() as tempdir:
            with PalamedesIsolation(Path(tempdir)) as isolated:
                provider = StaticChatProvider()
                first = io.StringIO()
                palamedes_chat.run_chat(
                    palamedes_module=isolated,
                    provider=provider,
                    session_id="origin",
                    input_stream=io.StringIO("/mission prove one thing\n/approve\n/quit\n"),
                    output=first,
                )
                mission_id = next(
                    (isolated.STATE_DIR / "missions").glob("mission-*.json")
                ).stem
                second = io.StringIO()
                palamedes_chat.run_chat(
                    palamedes_module=isolated,
                    provider=provider,
                    session_id="fresh-session",
                    input_stream=io.StringIO(
                        f"/outcome {mission_id} success Cross-session evidence arrived\n/quit\n"
                    ),
                    output=second,
                )

        self.assertIn("Outcome recorded:", second.getvalue())
        self.assertNotIn("No approved mission", second.getvalue())

    def test_current_already_satisfied_requirement_blocks_duplicate_mission(self):
        from palamedes_satisfaction import SatisfactionStore, workspace_snapshot

        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            with PalamedesIsolation(root) as isolated:
                SatisfactionStore(
                    isolated.STATE_DIR / "satisfaction"
                ).save({
                    "assessment_id": "satisfaction-aaaaaaaaaaaaaaaa",
                    "requirement_id": "req-already-done",
                    "disposition": "already_satisfied",
                    "current_snapshot": workspace_snapshot(root),
                    "observed_at": palamedes_chat.utc_now(),
                    "ttl_days": 30,
                })
                payload = StaticChatProvider._mission_payload()
                payload["requirement_id"] = "req-already-done"
                contract = palamedes_chat.validate_mission_draft(payload)
                with self.assertRaisesRegex(ValueError, "already satisfied"):
                    palamedes_chat.approve_mission(
                        isolated,
                        palamedes_chat.MissionStore(
                            isolated.STATE_DIR / "missions"
                        ),
                        contract,
                        "satisfaction-gate",
                    )

    def test_external_evidence_gate_stops_cycle_without_provider_calls(self):
        with tempfile.TemporaryDirectory() as tempdir:
            with PalamedesIsolation(Path(tempdir)) as isolated:
                provider = StaticChatProvider()
                palamedes_chat.run_chat(
                    palamedes_module=isolated,
                    provider=provider,
                    session_id="origin",
                    input_stream=io.StringIO("/mission prove one thing\n/approve\n/quit\n"),
                    output=io.StringIO(),
                )
                mission_id = next(
                    (isolated.STATE_DIR / "missions").glob("mission-*.json")
                ).stem
                calls_before = len(provider.calls)
                output = io.StringIO()
                palamedes_chat.run_chat(
                    palamedes_module=isolated,
                    provider=provider,
                    session_id="wait",
                    input_stream=io.StringIO(
                        f"/wait-external {mission_id} Three independent human responses\n"
                        "/cycle invent more local artifacts\n/quit\n"
                    ),
                    output=output,
                )

        self.assertEqual(len(provider.calls), calls_before)
        self.assertIn("WAITING_FOR_EXTERNAL_EVIDENCE", output.getvalue())
        self.assertIn("provider_calls: 0", output.getvalue())

    def test_cmd_chat_binds_explicit_workspace(self):
        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir) / "original")
            workspace = Path(tempdir) / "workspace"
            workspace.mkdir()
            args = Namespace(
                provider="openrouter",
                model="fixture",
                session="trial",
                workspace=str(workspace),
                history_limit=24,
            )
            with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}), patch(
                "palamedes_chat.provider_from_config", return_value=StaticChatProvider()
            ), patch("palamedes_chat.run_chat", return_value=0) as run:
                palamedes_chat.cmd_chat(args, fake)

        self.assertEqual(fake.ROOT, workspace.resolve())
        self.assertEqual(fake.STATE_DIR, workspace.resolve() / ".palamedes")
        self.assertEqual(run.call_args.kwargs["session_id"], "trial")

    def test_cognition_cycle_isolates_path_dependent_context_until_adversary(self):
        class ExampleClassifyingProvider(StaticChatProvider):
            def stream(self, messages):
                if messages[-1]["content"].startswith("ROLE: context_governor"):
                    self.calls.append(messages)
                    yield json.dumps(
                        {
                            "hard_requirements": ["Originate a mini-game"],
                            "success_criteria": ["Produce a playable core loop"],
                            "constraints": [],
                            "autonomous_decisions": ["Genre", "core mechanic"],
                            "observations": [],
                            "preferences": [],
                            "reference_examples": [
                                {
                                    "example": "MAFIA42-REFERENCE-ONLY",
                                    "authorized_use": "comparison_only",
                                }
                            ],
                            "ambiguous_authority": [],
                        }
                    )
                    return
                yield from super().stream(messages)

        class PathDependentPalamedes(FakePalamedes):
            def load_plan(self):
                plan = super().load_plan()
                plan.update(
                    {
                        "selected_option": "LOCKED-IN-DETECTIVE-GAME",
                        "view_transitions": [
                            {"to": "BOTTOM-UP-ROLE-TREE", "reason": "implementation"}
                        ],
                        "development_probes": [
                            {"probe": "BOTTOM-UP-VOTING-API", "status": "open"}
                        ],
                        "plan_tasks": ["BOTTOM-UP-ROLE-PLAN"],
                        "execution_tasks": ["BOTTOM-UP-VOTE-COMPONENT"],
                        "phase_plan": ["BOTTOM-UP-IMPLEMENTATION-PHASE"],
                    }
                )
                return plan

        with tempfile.TemporaryDirectory() as tempdir:
            fake = PathDependentPalamedes(Path(tempdir))
            provider = ExampleClassifyingProvider()
            result = palamedes_chat.run_cognition_cycle(
                provider=provider,
                palamedes_module=fake,
                context=(
                    "Originate a mini-game autonomously; "
                    "MAFIA42-REFERENCE-ONLY may be worth benchmarking"
                ),
                cycle_store=palamedes_chat.CognitionCycleStore(
                    fake.STATE_DIR / "missions" / "cognition"
                ),
            )

        prompts = {
            call[-1]["content"].splitlines()[0]: call[-1]["content"]
            for call in provider.calls
        }
        self.assertNotIn("LOCKED-IN-DETECTIVE-GAME", prompts["ROLE: interpreter"])
        self.assertNotIn("LOCKED-IN-DETECTIVE-GAME", prompts["ROLE: inventor"])
        self.assertIn("LOCKED-IN-DETECTIVE-GAME", prompts["ROLE: adversary"])
        self.assertNotIn("BOTTOM-UP-ROLE-PLAN", prompts["ROLE: interpreter"])
        self.assertNotIn("BOTTOM-UP-VOTE-COMPONENT", prompts["ROLE: inventor"])
        self.assertIn("BOTTOM-UP-IMPLEMENTATION-PHASE", prompts["ROLE: adversary"])
        self.assertNotIn("MAFIA42-REFERENCE-ONLY", prompts["ROLE: interpreter"])
        self.assertNotIn("MAFIA42-REFERENCE-ONLY", prompts["ROLE: inventor"])
        self.assertIn("MAFIA42-REFERENCE-ONLY", prompts["ROLE: adversary"])
        cycle = result["cycle"]
        self.assertEqual(
            cycle["context_isolation_version"], "palamedes-context-isolation/1"
        )
        self.assertNotIn("selected_option", cycle["plan_context"])
        self.assertEqual(
            cycle["path_dependent_context"]["selected_option"],
            "LOCKED-IN-DETECTIVE-GAME",
        )

    def test_context_governor_cannot_leak_optional_example_into_clean_room(self):
        class LeakingGovernorProvider(StaticChatProvider):
            def stream(self, messages):
                if messages[-1]["content"].startswith("ROLE: context_governor"):
                    self.calls.append(messages)
                    yield json.dumps(
                        {
                            "hard_requirements": ["Originate a mini-game"],
                            "success_criteria": [],
                            "constraints": [],
                            "autonomous_decisions": ["Genre"],
                            "observations": ["Build around MAFIA42-OPTIONAL-EXAMPLE"],
                            "preferences": [],
                            "reference_examples": [
                                {
                                    "example": "MAFIA42-OPTIONAL-EXAMPLE",
                                    "authorized_use": "comparison_only",
                                }
                            ],
                            "ambiguous_authority": [],
                        }
                    )
                    return
                yield from super().stream(messages)

        with tempfile.TemporaryDirectory() as tempdir:
            fake = FakePalamedes(Path(tempdir))
            with self.assertRaisesRegex(ValueError, "leaked non-required reference"):
                palamedes_chat.run_cognition_cycle(
                    provider=LeakingGovernorProvider(),
                    palamedes_module=fake,
                    context="Use MAFIA42-OPTIONAL-EXAMPLE only as a possible reference",
                    cycle_store=palamedes_chat.CognitionCycleStore(
                        fake.STATE_DIR / "missions" / "cognition"
                    ),
                    schema_retry_limit=0,
                )

    def test_context_ablation_runs_independent_arms_and_blinded_judgment(self):
        class PathPalamedes(FakePalamedes):
            def load_plan(self):
                plan = super().load_plan()
                plan["selected_option"] = "existing implementation path"
                plan["development_probes"] = [
                    {"probe": "finish current component", "status": "open"}
                ]
                return plan

        with tempfile.TemporaryDirectory() as tempdir:
            fake = PathPalamedes(Path(tempdir))
            provider = StaticChatProvider()
            store = palamedes_chat.CognitionCycleStore(
                fake.STATE_DIR / "missions" / "cognition"
            )
            cycle_result = palamedes_chat.run_cognition_cycle(
                provider=provider,
                palamedes_module=fake,
                context="Find a mission worth planning",
                cycle_store=store,
            )
            calls_before = len(provider.calls)
            record = palamedes_chat.run_context_ablation(
                provider=provider,
                cycle_store=store,
                cycle_id=cycle_result["cycle"]["cognition_cycle_id"],
                record_root=fake.STATE_DIR / "missions" / "context-ablations",
            )
            saved = json.loads(
                next(
                    (fake.STATE_DIR / "missions" / "context-ablations").glob(
                        "ablation-*.json"
                    )
                ).read_text(encoding="utf-8")
            )
            second_record = palamedes_chat.run_context_ablation(
                provider=provider,
                cycle_store=store,
                cycle_id=cycle_result["cycle"]["cognition_cycle_id"],
                record_root=fake.STATE_DIR / "missions" / "context-ablations",
            )
            summary = json.loads(
                (
                    fake.STATE_DIR
                    / "missions"
                    / "context-ablations"
                    / f"summary-{cycle_result['cycle']['cognition_cycle_id']}.json"
                ).read_text(encoding="utf-8")
            )

        ablation_prompts = [
            call[-1]["content"].splitlines()[0]
            for call in provider.calls[calls_before:]
        ]
        self.assertEqual(
            ablation_prompts,
            [
                "ROLE: clean_room_ablation_arm",
                "ROLE: continuity_ablation_arm",
                "ROLE: blinded_ablation_judge",
                "ROLE: clean_room_ablation_arm",
                "ROLE: continuity_ablation_arm",
                "ROLE: blinded_ablation_judge",
            ],
        )
        self.assertTrue(record["material_direction_shift"])
        self.assertTrue(record["suspected_path_dependence"])
        self.assertEqual(
            record["continuity_lower_abstraction"],
            record["blinded_judgment"]["lower_abstraction_arm"]
            == record["blinded_labels"]["continuity"],
        )
        self.assertEqual(
            record["abstraction_collapse_signal"],
            record["continuity_lower_abstraction"],
        )
        self.assertFalse(record["single_pair_is_causal_proof"])
        self.assertTrue(record["replication_required"])
        self.assertEqual(saved["context_ablation_id"], record["context_ablation_id"])
        self.assertNotEqual(
            second_record["context_ablation_id"], record["context_ablation_id"]
        )
        self.assertNotEqual(
            second_record["blinded_labels"], record["blinded_labels"]
        )
        self.assertEqual(second_record["replication_number"], 2)
        self.assertEqual(summary["attempt_count"], 2)
        self.assertEqual(summary["material_direction_shift_rate"], 1.0)
        self.assertEqual(summary["minimum_interpretation"], "distributional_signal_only")

    def test_context_ablation_failure_is_preserved(self):
        with tempfile.TemporaryDirectory() as tempdir:
            provider = StaticChatProvider()
            root = Path(tempdir) / "ablations"
            record = palamedes_chat.record_context_ablation_failure(
                provider=provider,
                cycle_id="cycle-123456789abc",
                record_root=root,
                error=ValueError("invalid confidence"),
            )
            saved = json.loads(
                (root / f"{record['failure_id']}.json").read_text(encoding="utf-8")
            )

        self.assertEqual(saved["status"], "failed")
        self.assertEqual(saved["error_type"], "ValueError")
        self.assertTrue(saved["counted_in_total_attempts"])
        self.assertFalse(saved["counted_as_successful_pair"])

    def test_autonomous_invention_reopens_observation_requirements_in_next_context(self):
        with tempfile.TemporaryDirectory() as tempdir:
            mission_store = palamedes_chat.MissionStore(Path(tempdir) / "missions")
            invention_store = ProductInventionStore(Path(tempdir) / "inventions")
            requirement = invention_store.record_observation_requirement(
                source_type="candidate_disconfirmation_gap",
                observation_needed="Compare whether a new candidate family appears.",
                reason="The prior frontier could only restate its unknowns.",
            )
            returned = {
                "product_invention_id": "invention-aaaaaaaaaaaa",
                "status": "no_discovery",
            }
            with patch("palamedes_invention.run_product_invention", return_value=returned) as run:
                palamedes_chat.run_autonomous_invention(
                    provider=StaticChatProvider(),
                    mission_store=mission_store,
                    context="Improve Palamedes.",
                )
            supplied_context = run.call_args.kwargs["context"]
            self.assertIn("OPEN OBSERVATION REQUIREMENTS", supplied_context)
            self.assertIn(requirement["observation_requirement_id"], supplied_context)
            self.assertIn(requirement["observation_needed"], supplied_context)

    def test_autonomous_invention_passes_blind_judge_to_invention_engine(self):
        with tempfile.TemporaryDirectory() as tempdir:
            mission_store = palamedes_chat.MissionStore(Path(tempdir) / "missions")
            captured: dict[str, object] = {}

            def fake_run_product_invention(*, judge_ask, ask, store, context):
                captured["judge_ask"] = judge_ask
                captured["context"] = context
                return {
                    "product_invention_id": "invention-aaaaaaaaaaaa",
                    "status": "no_discovery",
                }

            def fake_provider_json(*_args, **_kwargs):
                return {
                    "covered_by_conventional_baseline": False,
                    "generic_request": True,
                    "rationale": "fixture rationale",
                }

            with patch("palamedes_invention.run_product_invention", side_effect=fake_run_product_invention):
                with patch("palamedes_chat._provider_json", side_effect=fake_provider_json) as provider_json:
                    palamedes_chat.run_autonomous_invention(
                        provider=StaticChatProvider(),
                        mission_store=mission_store,
                        context="Improve Palamedes.",
                    )

                    # judge_ask must be exercised while _provider_json is still
                    # patched; otherwise it reaches the real provider.
                    self.assertIn("judge_ask", captured)
                    self.assertIsNotNone(captured["judge_ask"])
                    judge_ask = captured["judge_ask"]
                    result = judge_ask(
                        "invention_baseline_coverage_judge",
                        "Candidate payload:\n"
                        + json.dumps(
                            {
                                "conventional_baseline": {
                                    "expected_solutions": ["sell cosmetic borders"]
                                },
                                "candidates": [
                                    {
                                        "candidate_id": "idea-1",
                                        "thesis": "새로운 연결 구조 제안",
                                    }
                                ]
                            },
                            ensure_ascii=False,
                        ),
                    )
                    self.assertEqual(
                        result,
                        {
                            "coverage_assessments": [
                                {
                                    "candidate_id": "idea-1",
                                    "covered_by_conventional_baseline": False,
                                    "generic_solution_pack": True,
                                    "reason": "fixture rationale",
                                }
                            ],
                            "empty_frontier_reason": (
                                "baseline coverage judge evaluated all candidates against the "
                                "conventional baseline"
                            ),
                        },
                    )
                    self.assertEqual(provider_json.call_count, 1)
                    self.assertEqual(captured["context"], "Improve Palamedes.")

    def test_blind_judge_prompt_declares_every_field_it_is_validated_on(self):
        with tempfile.TemporaryDirectory() as tempdir:
            mission_store = palamedes_chat.MissionStore(Path(tempdir) / "missions")
            captured: dict = {}
            prompts: list = []

            def fake_run_product_invention(*, judge_ask, ask, store, context):
                captured["judge_ask"] = judge_ask
                return {
                    "product_invention_id": "invention-aaaaaaaaaaaa",
                    "status": "no_discovery",
                }

            def fake_provider_json(*_args, **kwargs):
                prompts.append(kwargs.get("prompt", ""))
                return {
                    "covered_by_conventional_baseline": False,
                    "generic_request": True,
                    "rationale": "fixture rationale",
                }

            with patch(
                "palamedes_invention.run_product_invention",
                side_effect=fake_run_product_invention,
            ):
                with patch(
                    "palamedes_chat._provider_json", side_effect=fake_provider_json
                ):
                    palamedes_chat.run_autonomous_invention(
                        provider=StaticChatProvider(),
                        mission_store=mission_store,
                        context="Improve Palamedes.",
                    )
                    captured["judge_ask"](
                        "invention_baseline_coverage_judge",
                        "Candidate payload:\n"
                        + json.dumps(
                            {
                                "conventional_baseline": {
                                    "expected_solutions": ["sell cosmetic borders"]
                                },
                                "candidates": [
                                    {"candidate_id": "idea-1", "thesis": "구조 제안"}
                                ]
                            },
                            ensure_ascii=False,
                        ),
                    )

        # The validator rejects a judgment missing any of these, so a prompt that
        # never names them asks the model to guess its own contract.
        judge_prompt = prompts[-1]
        for field in (
            "covered_by_conventional_baseline",
            "generic_request",
            "rationale",
        ):
            self.assertIn(field, judge_prompt)

    def test_autonomous_invention_failure_becomes_observation_requirement(self):
        with tempfile.TemporaryDirectory() as tempdir:
            mission_store = palamedes_chat.MissionStore(Path(tempdir) / "missions")
            with patch(
                "palamedes_invention.run_product_invention",
                side_effect=ValueError("nested schema drift"),
            ):
                with self.assertRaisesRegex(ValueError, "nested schema drift"):
                    palamedes_chat.run_autonomous_invention(
                        provider=StaticChatProvider(),
                        mission_store=mission_store,
                        context="Improve Palamedes.",
                    )
            requirements = ProductInventionStore(
                Path(tempdir) / "inventions"
            ).open_observation_requirements()
            self.assertEqual(len(requirements), 1)
            self.assertEqual(requirements[0]["source_type"], "runtime_contract_failure")
            self.assertIn("nested schema drift", requirements[0]["observation_needed"])


if __name__ == "__main__":
    unittest.main()
