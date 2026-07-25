#!/usr/bin/env python3
import io
import json
import os
import tempfile
import unittest
from argparse import Namespace
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
        if "Required shape:" in messages[-1]["content"]:
            payload = {
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
            yield json.dumps(payload)
            return
        yield "A falsifiable "
        yield "mission."


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
