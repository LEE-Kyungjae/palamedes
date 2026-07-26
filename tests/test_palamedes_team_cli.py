#!/usr/bin/env python3
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import palamedes


class PalamedesTeamCliTests(unittest.TestCase):
    def run_command(self, arguments):
        args = palamedes.build_parser().parse_args(arguments)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            args.func(args)
        return json.loads(output.getvalue())

    def test_official_cli_records_and_reads_shared_team_state(self):
        with tempfile.TemporaryDirectory() as tempdir:
            state = str(Path(tempdir) / "team.json")
            observed = self.run_command(
                [
                    "team",
                    "observe",
                    "--state",
                    state,
                    "--payload-json",
                    json.dumps(
                        {
                            "observation_id": "obs-cli-core",
                            "agent_id": "research-agent",
                            "agent_role": "researcher",
                            "content": "Observed implementation behavior.",
                            "source": "repository",
                            "observation_surface": "current commit",
                        }
                    ),
                ]
            )
            claimed = self.run_command(
                [
                    "team",
                    "claim",
                    "--state",
                    state,
                    "--mission-id",
                    "mission-core-cli",
                    "--agent-id",
                    "implementation-agent",
                ]
            )
            snapshot = self.run_command(["team", "snapshot", "--state", state])

        self.assertTrue(observed["ok"])
        self.assertEqual(claimed["record"]["agent_id"], "implementation-agent")
        self.assertEqual(snapshot["state"]["world_version"], 2)
        self.assertEqual(snapshot["state"]["observations"][0]["observation_id"], "obs-cli-core")

    def test_official_cli_runs_blind_commit_reveal_round(self):
        with tempfile.TemporaryDirectory() as tempdir:
            state = str(Path(tempdir) / "team.json")
            self.run_command(
                [
                    "team",
                    "round-begin",
                    "--state",
                    state,
                    "--payload-json",
                    json.dumps(
                        {
                            "round_id": "round-cli",
                            "question": "What should we notice next?",
                            "participant_ids": ["agent-a", "agent-b"],
                        }
                    ),
                ]
            )
            candidates = {
                "agent-a": ({"mission": "Explore silent users"}, "nonce-a"),
                "agent-b": ({"mission": "Explore hand-off rituals"}, "nonce-b"),
            }
            for agent_id, (candidate, nonce) in candidates.items():
                hashed = self.run_command(
                    [
                        "team",
                        "candidate-hash",
                        "--state",
                        state,
                        "--payload-json",
                        json.dumps({"candidate": candidate, "nonce": nonce}),
                    ]
                )
                self.run_command(
                    [
                        "team",
                        "candidate-commit",
                        "--state",
                        state,
                        "--payload-json",
                        json.dumps(
                            {
                                "round_id": "round-cli",
                                "agent_id": agent_id,
                                "commitment": hashed["commitment"],
                            }
                        ),
                    ]
                )
            for agent_id, (candidate, nonce) in candidates.items():
                self.run_command(
                    [
                        "team",
                        "candidate-reveal",
                        "--state",
                        state,
                        "--payload-json",
                        json.dumps(
                            {
                                "round_id": "round-cli",
                                "agent_id": agent_id,
                                "candidate": candidate,
                                "nonce": nonce,
                            }
                        ),
                    ]
                )
            snapshot = self.run_command(["team", "snapshot", "--state", state])

        round_state = snapshot["state"]["exploration_rounds"][0]
        self.assertEqual(round_state["phase"], "ready")
        self.assertEqual(len(round_state["reveals"]), 2)


if __name__ == "__main__":
    unittest.main()
