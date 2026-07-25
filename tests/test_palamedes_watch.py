#!/usr/bin/env python3
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import palamedes_watch


def snapshot(*reasons):
    return {
        "observation_id": "observation-test",
        "observed_at": "2026-07-25T00:00:00+00:00",
        "snapshot_fingerprint": "snapshot-fingerprint",
        "change": {
            "baseline_available": True,
            "changed": bool(reasons),
            "reasons": list(reasons),
        },
        "signals": {
            "documents": {"documents": [], "document_count": 0},
            "git": {
                "available": True,
                "head": "abc",
                "status": [],
                "diff_stat": [],
                "recent_commits": [],
            },
            "todos": {"items": [], "truncated": False},
            "palamedes_state": {
                "plan": {"available": False},
                "outcomes": {"available": False},
            },
            "reference_root": {"available": False, "repositories": []},
            "test": {"executed": "test_failed" in reasons, "returncode": 1},
        },
    }


class StaticWakeProvider:
    provider_name = "static"
    model = "fixture"

    def __init__(self):
        self.calls = []

    def stream(self, messages):
        self.calls.append(messages)
        role = messages[-1]["content"].splitlines()[0].split(": ", 1)[1]
        payloads = {
            "noticer": {
                "thoughts": [
                    {
                        "kind": "anomaly",
                        "content": "Users revisit an output without editing it",
                        "unexplained_residue": "Revisits do not match the editing model",
                        "why_unresolved": "The observation has no user intent data",
                        "wake_conditions": ["A second revisit signal appears"],
                    },
                    {
                        "kind": "possibility",
                        "content": "Stored outputs may act as reusable judgment",
                        "unexplained_residue": "Reuse may be more valuable than creation",
                        "why_unresolved": "No reuse outcome is measured",
                        "wake_conditions": ["Reuse correlates with retention"],
                    },
                ]
            },
            "connector": {"discoveries": []},
            "interpreter": {
                "observations": ["The test failed"],
                "interpretations": ["A contract drifted"],
                "missing_evidence": ["Failure trace"],
            },
            "inventor": {
                "candidate_missions": ["Restore the violated contract"],
                "mechanism_transfers": ["Use boundary assertions"],
                "next_probes": ["Reproduce one failure"],
            },
            "adversary": {
                "falsifiers": ["The failure is unrelated"],
                "hidden_harms": ["A narrow patch hides drift"],
                "shared_assumptions": ["The test encodes intended behavior"],
            },
            "selector": {
                "recommendation": "reopen",
                "rationale": "The plan conflicts with evidence",
                "reversal_triggers": ["The failure cannot reproduce"],
            },
            "outcome_analyst": {
                "belief_updates": ["The forecast was wrong"],
                "attribution_hypotheses": ["Implementation mismatch"],
                "next_probe": "Separate implementation from mission failure",
            },
        }
        if role == "connector":
            thought_ids = list(
                dict.fromkeys(
                    re.findall(r"thought-[a-f0-9]{12}", messages[-1]["content"])
                )
            )
            if len(thought_ids) >= 2:
                payloads["connector"] = {
                    "discoveries": [
                        {
                            "connected_thought_ids": thought_ids[:2],
                            "thesis": "The product may preserve judgment, not merely produce output",
                            "old_framing": "A one-shot creation tool",
                            "new_framing": "A reusable judgment memory",
                            "assumption_replaced": "Creation is the primary retained value",
                            "changed_decision": "Measure reuse before adding creation features",
                            "smallest_probe": "Count return use of unchanged outputs",
                            "disconfirmation": "Revisits do not predict reuse or retention",
                            "why_non_obvious": "It connects navigation residue to product identity",
                        }
                    ]
                }
        yield json.dumps(payloads[role])


class FakePalamedes:
    def __init__(self, root):
        self.ROOT = root
        self.STATE_DIR = root / ".palamedes"

    def ensure_state(self):
        self.STATE_DIR.mkdir(parents=True, exist_ok=True)

    def load_plan(self):
        return {
            "goal": "Find valuable product direction",
            "success_metric": "",
            "selected_option": "",
            "constraints": ["plan-only"],
            "hypothesis_log": [],
            "view_transitions": [],
            "open_questions": [],
            "development_probes": [],
        }


class PalamedesWatchTests(unittest.TestCase):
    def test_wake_policy_selects_least_sufficient_operation(self):
        self.assertEqual(
            palamedes_watch.select_wake_policy(
                snapshot("initial_observation")
            )["operation"],
            "wait",
        )
        self.assertEqual(
            palamedes_watch.select_wake_policy(
                snapshot("initial_observation"), wake_initial=True
            )["roles"],
            ["interpreter"],
        )
        self.assertEqual(
            palamedes_watch.select_wake_policy(
                snapshot("document_set_or_content_changed")
            )["roles"],
            ["noticer", "connector"],
        )
        self.assertEqual(
            palamedes_watch.select_wake_policy(
                snapshot("reference_repository_set_or_head_changed")
            )["roles"],
            ["noticer", "connector"],
        )
        self.assertEqual(
            palamedes_watch.select_wake_policy(
                snapshot("test_failed", "document_set_or_content_changed")
            )["roles"],
            ["interpreter", "adversary"],
        )
        self.assertEqual(
            palamedes_watch.select_wake_policy(
                snapshot(
                    "git_head_changed",
                    "document_set_or_content_changed",
                    "palamedes_plan_changed",
                )
            )["operation"],
            "full_cycle",
        )

    def test_partial_operation_calls_only_selected_roles(self):
        provider = StaticWakeProvider()
        policy = palamedes_watch.select_wake_policy(
            snapshot("test_failed")
        )

        result = palamedes_watch.run_partial_operation(
            provider=provider,
            policy=policy,
            snapshot=snapshot("test_failed"),
        )

        self.assertEqual(
            [item["role"] for item in result["artifacts"]],
            ["interpreter", "adversary"],
        )
        self.assertEqual(result["model_call_count"], 2)
        self.assertFalse(result["mission_draft_issued"])
        self.assertEqual(len(provider.calls), 2)

    def test_watch_suppresses_duplicate_signal_state(self):
        current = snapshot("document_set_or_content_changed")
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            store = palamedes_watch.WatchStore(root / "watch")
            fake = FakePalamedes(root)
            with patch(
                "palamedes_watch.collect_observation", return_value=current
            ):
                first = palamedes_watch.watch_once(
                    workspace=root,
                    store=store,
                    palamedes_module=fake,
                    ref_root=None,
                    test_command="",
                    test_timeout=10,
                    provider=None,
                    auto_cognition=False,
                    wake_initial=False,
                    max_calls_per_wake=4,
                    max_calls_per_day=10,
                    max_calls_total=20,
                )
                second = palamedes_watch.watch_once(
                    workspace=root,
                    store=store,
                    palamedes_module=fake,
                    ref_root=None,
                    test_command="",
                    test_timeout=10,
                    provider=None,
                    auto_cognition=False,
                    wake_initial=False,
                    max_calls_per_wake=4,
                    max_calls_per_day=10,
                    max_calls_total=20,
                )

        self.assertEqual(first["policy"]["operation"], "incubate_discovery")
        self.assertEqual(first["execution"]["status"], "policy_only")
        self.assertEqual(second["policy"]["operation"], "wait")
        self.assertTrue(second["duplicate_signal_suppressed"])

    def test_discovery_wake_persists_pre_mission_lineage(self):
        current = snapshot("document_set_or_content_changed")
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            wake = palamedes_watch.execute_wake(
                policy=palamedes_watch.select_wake_policy(current),
                snapshot=current,
                provider=StaticWakeProvider(),
                palamedes_module=FakePalamedes(root),
            )
            thought_files = list(
                (root / ".palamedes" / "thoughts" / "thoughts").glob("*.json")
            )
            discovery_files = list(
                (root / ".palamedes" / "thoughts" / "discoveries").glob("*.json")
            )
            discovery = json.loads(discovery_files[0].read_text())

        self.assertEqual(wake["model_call_count"], 2)
        self.assertEqual(len(thought_files), 2)
        self.assertEqual(len(discovery_files), 1)
        self.assertFalse(wake["mission_draft_issued"])
        self.assertFalse(discovery["mission_authority_granted"])
        self.assertEqual(len(discovery["connected_thought_ids"]), 2)

    def test_full_cycle_carries_incubated_discovery_into_mission(self):
        from palamedes_thought import ThoughtStore
        from tests.test_palamedes_chat import StaticChatProvider

        class DiscoveryAwareProvider(StaticChatProvider):
            def stream(self, messages):
                if "ROLE: selector" in messages[-1]["content"]:
                    payload = json.loads("".join(super().stream(messages)))
                    payload["source_discovery_ids"] = [
                        "discovery-123456789abc"
                    ]
                    yield json.dumps(payload)
                    return
                yield from super().stream(messages)

        current = snapshot(
            "git_head_changed",
            "document_set_or_content_changed",
            "palamedes_plan_changed",
        )
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            fake = FakePalamedes(root)
            thought_store = ThoughtStore(fake.STATE_DIR / "thoughts")
            discovery = {
                "discovery_version": "palamedes-discovery/1",
                "discovery_id": "discovery-123456789abc",
                "connected_thought_ids": [
                    "thought-123456789abc",
                    "thought-abcdef123456",
                ],
                "thesis": "The product may preserve reusable judgment",
                "old_framing": "Creation tool",
                "new_framing": "Judgment memory",
                "assumption_replaced": "Creation is the retained value",
                "changed_decision": "Measure reuse before feature breadth",
                "smallest_probe": "Measure unchanged output reuse",
                "disconfirmation": "Reuse does not predict retention",
                "why_non_obvious": "It connects navigation to product identity",
                "status": "candidate",
                "created_at": "2026-07-26T00:00:00+00:00",
                "mission_authority_granted": False,
            }
            thought_store.save_discovery(discovery)

            wake = palamedes_watch.execute_wake(
                policy=palamedes_watch.select_wake_policy(current),
                snapshot=current,
                provider=DiscoveryAwareProvider(),
                palamedes_module=fake,
            )
            contract_path = next(
                (fake.STATE_DIR / "missions").glob("mission-*.json")
            )
            contract = json.loads(contract_path.read_text())

        self.assertTrue(wake["mission_draft_issued"])
        self.assertEqual(
            contract["source_discovery_ids"], ["discovery-123456789abc"]
        )
        self.assertEqual(contract["status"], "draft")

    def test_repeated_residue_reinforces_thought_across_wakes(self):
        first = snapshot("document_set_or_content_changed")
        second = snapshot("reference_repository_set_or_head_changed")
        second["observation_id"] = "observation-later"
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            fake = FakePalamedes(root)
            for current in (first, second):
                palamedes_watch.execute_wake(
                    policy=palamedes_watch.select_wake_policy(current),
                    snapshot=current,
                    provider=StaticWakeProvider(),
                    palamedes_module=fake,
                )
            thought = json.loads(
                next(
                    (fake.STATE_DIR / "thoughts" / "thoughts").glob("*.json")
                ).read_text()
            )

        self.assertEqual(thought["status"], "reinforced")
        self.assertEqual(thought["reinforcement_count"], 2)
        self.assertEqual(
            thought["source_observation_ids"],
            ["observation-test", "observation-later"],
        )

    def test_stale_incubation_revisits_thoughts_without_new_signal(self):
        from palamedes_thought import ThoughtStore

        current = snapshot()
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            fake = FakePalamedes(root)
            thought_store = ThoughtStore(fake.STATE_DIR / "thoughts")
            thought_store.save_thought(
                {
                    "thought_version": "palamedes-thought/1",
                    "thought_id": "thought-123456789abc",
                    "kind": "question",
                    "content": "Why do users return to unchanged outputs?",
                    "unexplained_residue": "Return behavior has no current explanation",
                    "why_unresolved": "No longitudinal measure exists",
                    "source_observation_ids": ["observation-old"],
                    "wake_conditions": ["A day passes without resolution"],
                    "strength": 0.4,
                    "reinforcement_count": 1,
                    "status": "incubating",
                    "created_at": "2026-07-24T00:00:00+00:00",
                    "last_revisited_at": "2026-07-24T00:00:00+00:00",
                    "mission_authority_granted": False,
                }
            )
            store = palamedes_watch.WatchStore(fake.STATE_DIR / "watch")
            store.save_state(
                {
                    "watch_state_version": "palamedes-watch-state/1",
                    "last_incubation_at": "2026-07-24T00:00:00+00:00",
                    "total_model_calls": 0,
                    "iteration_count": 0,
                    "last_wake_key": "",
                }
            )
            with patch(
                "palamedes_watch.collect_observation", return_value=current
            ):
                wake = palamedes_watch.watch_once(
                    workspace=root,
                    store=store,
                    palamedes_module=fake,
                    ref_root=None,
                    test_command="",
                    test_timeout=10,
                    provider=StaticWakeProvider(),
                    auto_cognition=True,
                    wake_initial=False,
                    max_calls_per_wake=2,
                    max_calls_per_day=10,
                    max_calls_total=20,
                )

        self.assertEqual(wake["policy"]["operation"], "revisit_incubation")
        self.assertEqual(wake["execution"]["status"], "completed")
        self.assertEqual(wake["execution"]["model_call_count"], 2)

    def test_budget_blocks_cognition_before_provider_call(self):
        current = snapshot("test_failed")
        provider = StaticWakeProvider()
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            with patch(
                "palamedes_watch.collect_observation", return_value=current
            ):
                wake = palamedes_watch.watch_once(
                    workspace=root,
                    store=palamedes_watch.WatchStore(root / "watch"),
                    palamedes_module=FakePalamedes(root),
                    ref_root=None,
                    test_command="",
                    test_timeout=10,
                    provider=provider,
                    auto_cognition=True,
                    wake_initial=False,
                    max_calls_per_wake=1,
                    max_calls_per_day=10,
                    max_calls_total=20,
                )

        self.assertEqual(wake["execution"]["status"], "budget_blocked")
        self.assertEqual(provider.calls, [])

    def test_failed_provider_call_is_charged_to_total_budget(self):
        class FailingProvider(StaticWakeProvider):
            def stream(self, messages):
                self.calls.append(messages)
                raise RuntimeError("provider failed after accepting the call")
                yield

        current = snapshot("document_set_or_content_changed")
        provider = FailingProvider()
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            store = palamedes_watch.WatchStore(root / "watch")
            with patch(
                "palamedes_watch.collect_observation", return_value=current
            ):
                wake = palamedes_watch.watch_once(
                    workspace=root,
                    store=store,
                    palamedes_module=FakePalamedes(root),
                    ref_root=None,
                    test_command="",
                    test_timeout=10,
                    provider=provider,
                    auto_cognition=True,
                    wake_initial=False,
                    max_calls_per_wake=4,
                    max_calls_per_day=10,
                    max_calls_total=20,
                )

            state = store.load_state()

        self.assertEqual(wake["execution"]["status"], "failed")
        self.assertEqual(wake["execution"]["model_call_count"], 1)
        self.assertEqual(state["total_model_calls"], 1)

    def test_provider_token_usage_is_persisted(self):
        class MeteredProvider(StaticWakeProvider):
            last_usage = None

            def stream(self, messages):
                yield from super().stream(messages)
                self.last_usage = {
                    "input_tokens": 120,
                    "cached_input_tokens": 80,
                    "output_tokens": 10,
                }

        current = snapshot("document_set_or_content_changed")
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            store = palamedes_watch.WatchStore(root / "watch")
            with patch(
                "palamedes_watch.collect_observation", return_value=current
            ):
                wake = palamedes_watch.watch_once(
                    workspace=root,
                    store=store,
                    palamedes_module=FakePalamedes(root),
                    ref_root=None,
                    test_command="",
                    test_timeout=10,
                    provider=MeteredProvider(),
                    auto_cognition=True,
                    wake_initial=False,
                    max_calls_per_wake=2,
                    max_calls_per_day=10,
                    max_calls_total=20,
                )
            state = store.load_state()

        self.assertEqual(wake["execution"]["token_usage"]["input_tokens"], 240)
        self.assertEqual(state["total_tokens"], 260)
        self.assertEqual(state["daily_tokens"], 260)

    def test_daily_budget_blocks_cognition(self):
        current = snapshot("document_set_or_content_changed")
        provider = StaticWakeProvider()
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            store = palamedes_watch.WatchStore(root / "watch")
            store.save_state(
                {
                    "watch_state_version": "palamedes-watch-state/1",
                    "budget_date": palamedes_watch.utc_now()[:10],
                    "daily_model_calls": 10,
                    "total_model_calls": 10,
                    "iteration_count": 1,
                    "last_wake_key": "",
                }
            )
            with patch(
                "palamedes_watch.collect_observation", return_value=current
            ):
                wake = palamedes_watch.watch_once(
                    workspace=root,
                    store=store,
                    palamedes_module=FakePalamedes(root),
                    ref_root=None,
                    test_command="",
                    test_timeout=10,
                    provider=provider,
                    auto_cognition=True,
                    wake_initial=False,
                    max_calls_per_wake=2,
                    max_calls_per_day=10,
                    max_calls_total=20,
                )

        self.assertEqual(wake["execution"]["status"], "budget_blocked")
        self.assertEqual(wake["budget"]["daily_calls_remaining_before"], 0)
        self.assertEqual(provider.calls, [])

    def test_watch_lock_rejects_second_live_process(self):
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "watch.lock"
            with palamedes_watch.WatchLock(path):
                with self.assertRaises(ValueError):
                    with palamedes_watch.WatchLock(path):
                        pass
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
