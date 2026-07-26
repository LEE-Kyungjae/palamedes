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

    def __init__(self) -> None:
        self.calls = []

    def stream(self, messages):
        self.calls.append(messages)
        prompt = messages[-1]["content"]
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
        self.assertEqual(plan["hypothesis_log"][-1]["status"], "validated")
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
                            "/cycle find a mission worth planning\n"
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
            ["interpreter", "inventor", "adversary", "selector"],
        )
        self.assertEqual(len(cycle["outcome_analyses"]), 1)
        self.assertEqual(
            cycle["outcome_analyses"][0]["role"], "outcome_analyst"
        )
        self.assertEqual(cycle["live_model_call_count"], 5)
        self.assertFalse(cycle["outcome_analyst_runs_before_outcome"])
        self.assertEqual(
            [call[-1]["content"].splitlines()[0] for call in provider.calls],
            [
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
        self.assertEqual(experience["probe_status"], "completed")
        self.assertEqual(experience["finding"], "expected_result")
        self.assertFalse(experience["followup_required"])
        self.assertEqual(experience["followup_kind"], "none")

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
        self.assertEqual(cycle["live_model_call_count"], 3)

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
                palamedes_chat.approve_mission(
                    isolated, mission_store, response, "gate-test"
                )

        self.assertEqual(mission_store.open_outcome_gates(), [])

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
                independent_payload["outcome_response"] = {
                    "related_outcome_ids": [outcome["outcome_id"]],
                    "action": "independent",
                    "rationale": "This does not claim to resolve the guidance defect.",
                }
                independent = palamedes_chat.validate_mission_draft(
                    independent_payload
                )
                palamedes_chat.approve_mission(
                    isolated, mission_store, independent, "semantic-test"
                )
                still_open = mission_store.open_outcome_gates()

                resolving_payload = StaticChatProvider._mission_payload()
                resolving_payload["mission"] = (
                    "Correct guidance precedence for the reproduced trace"
                )
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

        self.assertEqual(gate["probe_status"], "completed")
        self.assertEqual(gate["finding"], "qualifying_defect")
        self.assertEqual(gate["mission_disposition"], "stop")
        self.assertTrue(gate["followup_required"])
        self.assertEqual(gate["followup_kind"], "production_correction")
        self.assertEqual(stored_contract["latest_finding"], "qualifying_defect")
        self.assertTrue(stored_contract["latest_followup_required"])
        self.assertEqual(interpretations[0]["finding"], "qualifying_defect")
        self.assertEqual(experience["probe_status"], "completed")
        self.assertEqual(experience["finding"], "qualifying_defect")
        self.assertTrue(experience["followup_required"])
        self.assertEqual(experience["followup_kind"], "production_correction")
        self.assertEqual(
            experience["successor_scope"],
            "Correct guidance precedence for the reproduced trace",
        )
        self.assertEqual(len(still_open), 1)
        self.assertTrue(still_open[0]["followup_still_required"])
        self.assertEqual(mission_store.open_outcome_gates(), [])

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
            ["interpreter", "inventor"],
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


if __name__ == "__main__":
    unittest.main()
