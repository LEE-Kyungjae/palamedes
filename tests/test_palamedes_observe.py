#!/usr/bin/env python3
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import palamedes_observe


def git(workspace: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=str(workspace),
        capture_output=True,
        text=True,
        check=True,
    )


class PalamedesObserveTests(unittest.TestCase):
    def test_observation_is_bounded_redacted_and_provenance_bearing(self):
        with tempfile.TemporaryDirectory() as tempdir:
            workspace = Path(tempdir) / "project"
            workspace.mkdir()
            (workspace / "README.md").write_text(
                "# Product\n\nTODO: prove the decision\n"
                "OPENROUTER_API_KEY=example-secret-value-123456\n",
                encoding="utf-8",
            )
            (workspace / "PALAMEDES_INQUIRY.md").write_text(
                "# Inquiry\n" + ("bounded context\n" * 4_000),
                encoding="utf-8",
            )
            ref_root = Path(tempdir) / "ref"
            (ref_root / "repo-a").mkdir(parents=True)

            snapshot = palamedes_observe.collect_observation(
                workspace, ref_root=ref_root
            )

        documents = snapshot["signals"]["documents"]["documents"]
        combined = "\n".join(item["excerpt"] for item in documents)
        self.assertNotIn("example-secret-value-123456", combined)
        self.assertIn("[REDACTED]", combined)
        self.assertLessEqual(
            snapshot["signals"]["documents"]["excerpt_bytes"],
            palamedes_observe.MAX_TOTAL_DOCUMENT_BYTES,
        )
        self.assertTrue(any(item["excerpt_truncated"] for item in documents))
        self.assertTrue(all(item["content_sha256"] for item in documents))
        self.assertEqual(len(snapshot["signals"]["todos"]["items"]), 1)
        self.assertEqual(
            snapshot["signals"]["reference_root"]["repository_count"], 1
        )

    def test_second_observation_reports_document_and_git_change(self):
        with tempfile.TemporaryDirectory() as tempdir:
            workspace = Path(tempdir) / "project"
            workspace.mkdir()
            (workspace / "README.md").write_text("# Initial\n", encoding="utf-8")
            git(workspace, "init")
            git(workspace, "config", "user.email", "test@example.com")
            git(workspace, "config", "user.name", "Test")
            git(workspace, "add", "README.md")
            git(workspace, "commit", "-m", "initial")
            first = palamedes_observe.collect_observation(
                workspace, ref_root=None
            )
            (workspace / "README.md").write_text("# Changed\n", encoding="utf-8")
            second = palamedes_observe.collect_observation(
                workspace, ref_root=None
            )

        self.assertFalse(first["change"]["baseline_available"])
        self.assertTrue(second["change"]["baseline_available"])
        self.assertTrue(second["change"]["changed"])
        self.assertIn(
            "document_set_or_content_changed", second["change"]["reasons"]
        )
        self.assertIn("git_status_changed", second["change"]["reasons"])

    def test_explicit_test_command_failure_is_observed_without_shell(self):
        with tempfile.TemporaryDirectory() as tempdir:
            workspace = Path(tempdir)
            snapshot = palamedes_observe.collect_observation(
                workspace,
                ref_root=None,
                test_command='python3 -c "raise SystemExit(7)"',
            )

        test = snapshot["signals"]["test"]
        self.assertTrue(test["executed"])
        self.assertFalse(test["passed"])
        self.assertEqual(test["returncode"], 7)
        self.assertIn("test_failed", snapshot["change"]["reasons"])
        self.assertEqual(test["command"][0], "python3")

    def test_observation_context_excludes_full_internal_snapshot_metadata(self):
        with tempfile.TemporaryDirectory() as tempdir:
            workspace = Path(tempdir)
            (workspace / "README.md").write_text("# Context\n", encoding="utf-8")
            snapshot = palamedes_observe.collect_observation(
                workspace, ref_root=None
            )
            context = palamedes_observe.observation_context(snapshot)

        self.assertEqual(context["observation_id"], snapshot["observation_id"])
        self.assertNotIn("collection_limits", context)
        self.assertNotIn("snapshot_fingerprint", context)


if __name__ == "__main__":
    unittest.main()
