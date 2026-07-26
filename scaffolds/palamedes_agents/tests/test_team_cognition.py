#!/usr/bin/env python3
import sys
import tempfile
import threading
import unittest
from pathlib import Path


SCAFFOLD_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = SCAFFOLD_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from palamedes_agents.team_cognition import TeamCognitionConflict, TeamCognitionStore


class TeamCognitionStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.store = TeamCognitionStore(Path(self.temporary.name) / "team.json")

    def tearDown(self):
        self.temporary.cleanup()

    def observation(self, agent_id="ux-agent", observation_id="obs-ux"):
        return self.store.record_observation(
            {
                "observation_id": observation_id,
                "agent_id": agent_id,
                "agent_role": "researcher",
                "kind": "fact",
                "content": "Hot-seat players pass one phone between turns.",
                "source": "repository:yut_game_screen.dart",
                "observation_surface": "current product implementation",
                "confidence": 85,
                "coverage": {
                    "observed_population": "implemented local game flow",
                    "missing_perspectives": ["real family play"],
                    "selection_bias": "code shows capability, not user behavior",
                },
            }
        )

    def test_preserves_agent_provenance_and_observation_bias(self):
        result = self.observation()
        snapshot = self.store.snapshot()

        self.assertEqual(result["world_version"], 1)
        self.assertEqual(snapshot["observations"][0]["agent_id"], "ux-agent")
        self.assertEqual(
            snapshot["observations"][0]["coverage"]["missing_perspectives"],
            ["real family play"],
        )

    def test_stale_world_write_is_rejected(self):
        self.observation()

        with self.assertRaises(TeamCognitionConflict):
            self.store.record_observation(
                {
                    "agent_id": "market-agent",
                    "agent_role": "researcher",
                    "content": "A second observation",
                    "source": "market scan",
                    "observation_surface": "public competitors",
                },
                expected_world_version=0,
            )

    def test_competing_hypotheses_remain_separate(self):
        self.observation()
        first = self.store.propose_hypothesis(
            {
                "hypothesis_id": "hyp-ritual",
                "agent_id": "ux-agent",
                "statement": "Phone hand-off can become a turn ritual.",
                "mechanism": "A private hand-off moment increases ownership clarity.",
                "prediction": "Wrong-player actions decline in a bounded play test.",
                "falsifier": "Players find the hand-off slower without fewer mistakes.",
                "evidence_ids": ["obs-ux"],
            }
        )
        self.store.propose_hypothesis(
            {
                "hypothesis_id": "hyp-friction",
                "agent_id": "skeptic-agent",
                "statement": "A hand-off screen adds needless friction.",
                "mechanism": "Extra confirmation interrupts a lightweight game.",
                "prediction": "Turn completion time rises.",
                "falsifier": "Completion time stays flat while ownership errors fall.",
                "evidence_ids": ["obs-ux"],
                "conflicts_with": ["hyp-ritual"],
            },
            expected_world_version=first["world_version"],
        )

        snapshot = self.store.snapshot()
        self.assertEqual(len(snapshot["hypotheses"]), 2)
        self.assertEqual(snapshot["hypotheses"][1]["conflicts_with"], ["hyp-ritual"])
        self.assertEqual({item["status"] for item in snapshot["hypotheses"]}, {"open"})

    def test_exploration_candidates_stay_blind_until_every_agent_commits(self):
        self.store.begin_exploration(
            {
                "round_id": "round-hot-seat",
                "question": "What experience is missing?",
                "participant_ids": ["ux-agent", "business-agent"],
                "evidence_boundary": ["obs-ux"],
            }
        )
        ux_candidate = {"mission": "Turn phone hand-off into a private ritual"}
        business_candidate = {"mission": "Turn decisive plays into shareable memories"}
        ux_hash = self.store.candidate_commitment(ux_candidate, "ux-secret")
        business_hash = self.store.candidate_commitment(business_candidate, "business-secret")

        self.store.commit_candidate("round-hot-seat", "ux-agent", ux_hash)
        after_one = self.store.snapshot()["exploration_rounds"][0]
        self.assertEqual(after_one["phase"], "commit")
        self.assertEqual(after_one["reveals"], [])
        self.assertNotIn("candidate", after_one["commitments"][0])

        self.store.commit_candidate("round-hot-seat", "business-agent", business_hash)
        self.store.reveal_candidate(
            "round-hot-seat", "ux-agent", ux_candidate, "ux-secret"
        )
        with self.assertRaises(TeamCognitionConflict):
            self.store.reveal_candidate(
                "round-hot-seat",
                "business-agent",
                {"mission": "A changed candidate"},
                "business-secret",
            )
        self.store.reveal_candidate(
            "round-hot-seat",
            "business-agent",
            business_candidate,
            "business-secret",
        )

        completed = self.store.snapshot()["exploration_rounds"][0]
        self.assertEqual(completed["phase"], "ready")
        self.assertEqual(
            [item["candidate"]["mission"] for item in completed["reveals"]],
            [ux_candidate["mission"], business_candidate["mission"]],
        )

    def test_mission_has_one_owner_but_idempotent_same_owner_claim(self):
        first = self.store.claim_mission("mission-turn-handoff", "implementation-agent")
        repeated = self.store.claim_mission("mission-turn-handoff", "implementation-agent")

        self.assertEqual(first["record"], repeated["record"])
        self.assertEqual(first["world_version"], repeated["world_version"])
        with self.assertRaises(TeamCognitionConflict):
            self.store.claim_mission("mission-turn-handoff", "second-agent")

        released = self.store.release_mission(
            "mission-turn-handoff",
            "implementation-agent",
            status="completed",
        )
        self.assertEqual(released["record"]["status"], "completed")
        reclaimed = self.store.claim_mission("mission-turn-handoff", "second-agent")
        self.assertEqual(reclaimed["record"]["agent_id"], "second-agent")

    def test_outcome_requires_explicit_complete_attribution(self):
        self.store.claim_mission("mission-1", "implementation-agent")
        with self.assertRaises(ValueError):
            self.store.record_outcome(
                {
                    "mission_id": "mission-1",
                    "result": "mixed",
                    "attribution": [
                        {"agent_id": "palamedes", "contribution": "mission selection", "share": 60}
                    ],
                }
            )

        result = self.store.record_outcome(
            {
                "mission_id": "mission-1",
                "result": "mixed",
                "evidence": ["widget tests passed", "human outcome absent"],
                "attribution": [
                    {"agent_id": "palamedes", "contribution": "mission selection", "share": 35},
                    {"agent_id": "codex", "contribution": "implementation and verification", "share": 65},
                ],
            }
        )

        self.assertEqual(result["record"]["attribution"][0]["share"], 35)
        self.assertEqual(sum(item["share"] for item in result["record"]["attribution"]), 100)

    def test_concurrent_observations_are_not_lost(self):
        errors = []

        def record(index):
            try:
                self.observation(
                    agent_id=f"agent-{index}",
                    observation_id=f"obs-{index}",
                )
            except Exception as exc:  # pragma: no cover - asserted below
                errors.append(exc)

        threads = [threading.Thread(target=record, args=(index,)) for index in range(12)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(errors, [])
        snapshot = self.store.snapshot()
        self.assertEqual(snapshot["world_version"], 12)
        self.assertEqual(len(snapshot["observations"]), 12)
        self.assertEqual(
            {item["observation_id"] for item in snapshot["observations"]},
            {f"obs-{index}" for index in range(12)},
        )

    def test_concurrent_mission_claims_produce_one_owner(self):
        winners = []
        conflicts = []

        def claim(agent_id):
            try:
                winners.append(
                    self.store.claim_mission("mission-race", agent_id)["record"]["agent_id"]
                )
            except TeamCognitionConflict as exc:
                conflicts.append(str(exc))

        threads = [
            threading.Thread(target=claim, args=(f"agent-{index}",))
            for index in range(8)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(len(winners), 1)
        self.assertEqual(len(conflicts), 7)
        snapshot = self.store.snapshot()
        self.assertEqual(len(snapshot["missions"]), 1)
        self.assertEqual(snapshot["missions"][0]["agent_id"], winners[0])

    def test_reasoning_context_is_bounded_without_discarding_full_history(self):
        for index in range(25):
            self.observation(
                agent_id=f"agent-{index}",
                observation_id=f"obs-context-{index}",
            )

        context = self.store.context_snapshot(observation_limit=4)
        full = self.store.snapshot()

        self.assertEqual(context["counts"]["observations"], 25)
        self.assertEqual(len(context["recent_observations"]), 4)
        self.assertEqual(context["recent_observations"][0]["observation_id"], "obs-context-21")
        self.assertEqual(len(full["observations"]), 25)


if __name__ == "__main__":
    unittest.main()
