#!/usr/bin/env python3
import json
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
        yield json.dumps(payloads[role])


class FakePalamedes:
    def __init__(self, root):
        self.ROOT = root
        self.STATE_DIR = root / ".palamedes"


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
                snapshot("document_set_or_content_changed")
            )["roles"],
            ["interpreter"],
        )
        self.assertEqual(
            palamedes_watch.select_wake_policy(
                snapshot("reference_repository_set_or_head_changed")
            )["roles"],
            ["interpreter", "inventor"],
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
                    max_calls_total=20,
                )

        self.assertEqual(first["policy"]["operation"], "reinterpret_document_change")
        self.assertEqual(first["execution"]["status"], "policy_only")
        self.assertEqual(second["policy"]["operation"], "wait")
        self.assertTrue(second["duplicate_signal_suppressed"])

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
                    max_calls_total=20,
                )

            state = store.load_state()

        self.assertEqual(wake["execution"]["status"], "failed")
        self.assertEqual(wake["execution"]["model_call_count"], 1)
        self.assertEqual(state["total_model_calls"], 1)

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
