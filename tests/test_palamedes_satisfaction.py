#!/usr/bin/env python3
import hashlib
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from palamedes_satisfaction import (
    SatisfactionStore,
    assess_satisfaction,
    assessment_is_current,
    workspace_snapshot,
)


class SatisfactionTests(unittest.TestCase):
    def repo(self, root):
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(
            ["git", "-C", str(root), "config", "user.email", "test@example.com"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(root), "config", "user.name", "Test"], check=True
        )
        (root / "feature.py").write_text(
            "def route():\n    return build()\n\ndef build():\n    return 1\n"
        )
        subprocess.run(["git", "-C", str(root), "add", "feature.py"], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)

    def request(self, root, claim_type="integration"):
        snapshot = workspace_snapshot(root)
        sha = hashlib.sha256((root / "feature.py").read_bytes()).hexdigest()
        return {
            "requirement_id": "req-route",
            "requirement": "The route reaches the builder",
            "claim_type": claim_type,
            "surface_key": "core-routing",
            "purpose_alignment": "aligned",
            "snapshot": snapshot,
            "observed_at": "2026-07-30T00:00:00+00:00",
            "ttl_days": 30,
            "evidence": [
                {
                    "kind": "symbol",
                    "path": "feature.py",
                    "contains": "def build",
                    "sha256": sha,
                    "custody": "host_observed",
                },
                {
                    "kind": "call_path",
                    "path": "feature.py",
                    "contains": "return build()",
                    "sha256": sha,
                    "custody": "host_observed",
                },
                {
                    "kind": "integration_test",
                    "path": "feature.py",
                    "contains": "return build()",
                    "sha256": sha,
                    "custody": "host_observed",
                },
            ],
        }

    def test_current_aligned_complete_evidence_is_already_satisfied(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            self.repo(root)
            result = assess_satisfaction(
                root, self.request(root), now=datetime(2026, 7, 30, tzinfo=timezone.utc)
            )
        self.assertEqual(result["evidence_state"], "verified_current_snapshot")
        self.assertEqual(result["disposition"], "already_satisfied")

    def test_snapshot_drift_makes_prior_evidence_stale(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            self.repo(root)
            request = self.request(root)
            (root / "feature.py").write_text(
                (root / "feature.py").read_text() + "\n# drift\n"
            )
            result = assess_satisfaction(
                root, request, now=datetime(2026, 7, 30, tzinfo=timezone.utc)
            )
        self.assertEqual(result["evidence_state"], "verified_stale")
        self.assertEqual(result["disposition"], "refresh_evidence")
        self.assertTrue(result["rejected_evidence"])

    def test_fun_claim_cannot_be_proven_by_code_or_tests(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            self.repo(root)
            request = self.request(root, claim_type="fun")
            result = assess_satisfaction(
                root, request, now=datetime(2026, 7, 30, tzinfo=timezone.utc)
            )
        self.assertEqual(result["disposition"], "evidence_needed")
        self.assertEqual(result["missing_evidence_kinds"], ["human_playtest"])

    def test_alignment_conflict_never_returns_already_satisfied(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            self.repo(root)
            request = self.request(root)
            request["purpose_alignment"] = "conflicts"
            result = assess_satisfaction(
                root, request, now=datetime(2026, 7, 30, tzinfo=timezone.utc)
            )
        self.assertEqual(result["evidence_state"], "misaligned_implementation")
        self.assertEqual(result["disposition"], "misaligned_mission")

    def test_host_can_assess_current_snapshot_without_caller_fingerprints(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            self.repo(root)
            request = self.request(root)
            request.pop("snapshot")
            request.pop("observed_at")
            result = assess_satisfaction(
                root, request, now=datetime(2026, 7, 30, tzinfo=timezone.utc)
            )
        self.assertTrue(result["evidence_snapshot_matches"])
        self.assertTrue(result["evidence_fresh"])
        self.assertEqual(result["disposition"], "already_satisfied")

    def test_persisted_assessment_becomes_stale_after_worktree_change(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            self.repo(root)
            request = self.request(root)
            request.pop("snapshot")
            request.pop("observed_at")
            result = assess_satisfaction(root, request)
            self.assertTrue(assessment_is_current(root, result))
            (root / "new-file.txt").write_text("changed")
            self.assertFalse(assessment_is_current(root, result))

    def test_latest_uses_assessment_time_not_random_id_filename_order(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = SatisfactionStore(Path(tempdir))
            store.save(
                {
                    "assessment_id": "satisfaction-ffffffffffffffff",
                    "requirement_id": "req-order",
                    "assessed_at": "2026-07-29T00:00:00+00:00",
                    "disposition": "refresh_evidence",
                }
            )
            store.save(
                {
                    "assessment_id": "satisfaction-0000000000000000",
                    "requirement_id": "req-order",
                    "assessed_at": "2026-07-30T00:00:00+00:00",
                    "disposition": "already_satisfied",
                }
            )
            latest = store.latest()
        self.assertEqual(latest[0]["assessment_id"], "satisfaction-0000000000000000")


if __name__ == "__main__":
    unittest.main()
