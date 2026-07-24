#!/usr/bin/env python3
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch


SCAFFOLD_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = SCAFFOLD_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

import palamedes
from palamedes_agents.console import main
from scaffolds.palamedes_agents.tests.test_strategy_llm import VALID_REPORT


class PalamedesStateIsolation:
    def __init__(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.state_dir = self.root / ".palamedes"
        self.originals: Dict[str, Any] = {}

    def __enter__(self):
        self.originals = {
            "ROOT": palamedes.ROOT,
            "STATE_DIR": palamedes.STATE_DIR,
            "PLAN_PATH": palamedes.PLAN_PATH,
            "DECISIONS_PATH": palamedes.DECISIONS_PATH,
            "RISKS_PATH": palamedes.RISKS_PATH,
            "EVENTS_PATH": palamedes.EVENTS_PATH,
            "REVISIONS_PATH": palamedes.REVISIONS_PATH,
            "EVENT_RETENTION_LIMIT": palamedes.EVENT_RETENTION_LIMIT,
            "REVISION_RETENTION_LIMIT": palamedes.REVISION_RETENTION_LIMIT,
        }
        palamedes.ROOT = self.root
        palamedes.STATE_DIR = self.state_dir
        palamedes.PLAN_PATH = self.state_dir / "plan.json"
        palamedes.DECISIONS_PATH = self.state_dir / "decisions.jsonl"
        palamedes.RISKS_PATH = self.state_dir / "risks.jsonl"
        palamedes.EVENTS_PATH = self.state_dir / "events.jsonl"
        palamedes.REVISIONS_PATH = self.state_dir / "revisions.jsonl"
        palamedes._sync_store_paths()
        return self

    def __exit__(self, exc_type, exc, tb):
        palamedes.ROOT = self.originals["ROOT"]
        palamedes.STATE_DIR = self.originals["STATE_DIR"]
        palamedes.PLAN_PATH = self.originals["PLAN_PATH"]
        palamedes.DECISIONS_PATH = self.originals["DECISIONS_PATH"]
        palamedes.RISKS_PATH = self.originals["RISKS_PATH"]
        palamedes.EVENTS_PATH = self.originals["EVENTS_PATH"]
        palamedes.REVISIONS_PATH = self.originals["REVISIONS_PATH"]
        palamedes.EVENT_RETENTION_LIMIT = self.originals["EVENT_RETENTION_LIMIT"]
        palamedes.REVISION_RETENTION_LIMIT = self.originals["REVISION_RETENTION_LIMIT"]
        palamedes._sync_store_paths()
        self.tempdir.cleanup()


def run_console(argv):
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        code = main(argv)
    return code, json.loads(stdout.getvalue())


class PalamedesAgentsConsoleTests(unittest.TestCase):
    def test_agents_lists_runnable_roles(self):
        code, payload = run_console(["agents"])

        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])
        roles = {item["role"]: item for item in payload["roles"]}
        self.assertIn("planner", roles)
        self.assertIn("strategist", roles)
        self.assertIn("researcher", roles)
        self.assertIn("reviewer", roles)
        self.assertIn("update_plan", roles["planner"]["allowed_actions"])
        self.assertIn("evaluate_experience_strategy", roles["strategist"]["allowed_actions"])
        self.assertIn("capture_evidence_cycle", roles["researcher"]["allowed_actions"])
        self.assertIn("run_reference_discovery", roles["researcher"]["allowed_actions"])

    def test_snapshot_and_planner_run_against_in_process_workspace(self):
        with PalamedesStateIsolation():
            snapshot_code, snapshot = run_console(["snapshot"])
            run_code, event = run_console(
                [
                    "run",
                    "--role",
                    "planner",
                    "--action",
                    "update_plan",
                    "--payload-json",
                    '{"goal":"console test goal","success_metric":"console test metric","deadline":"2026-05-31"}',
                ]
            )

        self.assertEqual(snapshot_code, 0)
        self.assertEqual(snapshot["type"], "snapshot")
        self.assertEqual(run_code, 0)
        self.assertTrue(event["ok"])
        self.assertEqual(event["type"], "planner_step")
        self.assertEqual(event["summary"]["operation"], "update_plan")
        self.assertIn("goal", event["summary"]["changed_fields"])

    def test_strategist_run_requires_ai_provider(self):
        with PalamedesStateIsolation():
            code, event = run_console(
                [
                    "run",
                    "--role",
                    "strategist",
                    "--action",
                    "evaluate_experience_strategy",
                    "--payload-json",
                    '{"idea":"AI productivity dashboard","target_user":"solo builder","solution":"dashboard"}',
                ]
            )

        self.assertEqual(code, 1)
        self.assertFalse(event["ok"])
        self.assertEqual(event["type"], "host_step_failed")
        self.assertIn("requires an AI strategy provider", event["error"]["message"])

    def test_strategist_run_accepts_injected_static_provider(self):
        with PalamedesStateIsolation():
            code, event = run_console(
                [
                    "run",
                    "--role",
                    "strategist",
                    "--action",
                    "generate_creative_directions",
                    "--provider",
                    "static",
                    "--static-report-json",
                    json.dumps(VALID_REPORT),
                ]
            )

        self.assertEqual(code, 0)
        self.assertTrue(event["ok"])
        self.assertEqual(event["type"], "strategy_step")
        self.assertEqual(event["summary"]["operation"], "generate_creative_directions")
        self.assertEqual(event["result"]["strategy"]["creative_directions"][0]["name"], "Pre-build Strategy Gate")

    def test_prompt_builds_strategy_llm_bundle_without_provider_call(self):
        with PalamedesStateIsolation():
            code, payload = run_console(["prompt"])

        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["type"], "strategy_prompt")
        messages = payload["bundle"]["messages"]
        schema = payload["bundle"]["schema"]
        self.assertEqual(messages[0]["role"], "system")
        self.assertIn("Palamedes strategist agent", messages[0]["content"])
        self.assertEqual(schema["title"], "PalamedesStrategyReport")
        self.assertIn("overall_score", schema["required"])
        self.assertIn("next_actions", schema["required"])

    def test_provider_health_reports_readiness(self):
        with patch(
            "palamedes_agents.console.openai_provider_health",
            return_value={"status": "ok", "issues": [], "sdk_available": True, "api_key_set": True},
        ):
            code, payload = run_console(["provider-health"])
        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])

    def test_openrouter_provider_health_reports_readiness(self):
        with patch(
            "palamedes_agents.console.openrouter_provider_health",
            return_value={"status": "ok", "issues": [], "api_key_set": True},
        ):
            code, payload = run_console(["provider-health", "--provider", "openrouter"])
        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])

    def test_prompt_builds_creative_directions_bundle(self):
        with PalamedesStateIsolation():
            code, payload = run_console(["prompt", "--action", "generate_creative_directions"])

        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])
        self.assertIn("generate_creative_directions", payload["bundle"]["messages"][1]["content"])
        self.assertIn("mid_project", payload["bundle"]["messages"][1]["content"])

    def test_retrieve_exposes_reference_quality_gate_without_provider(self):
        corpus = [
            {
                "reference_id": "success-1",
                "source": "Success case",
                "source_url": "https://example.com/success",
                "source_type": "success_case",
                "problem": "generic product direction",
                "mechanism": "product strategy gate",
            },
            {
                "reference_id": "failure-1",
                "source": "Failure case",
                "source_type": "failure_case",
                "problem": "generic product direction",
                "mechanism": "dashboard advice without evidence",
            },
        ]
        code, payload = run_console(
            [
                "retrieve",
                "--payload-json",
                json.dumps({"idea": "generic product direction", "reference_corpus": corpus}),
            ]
        )

        self.assertEqual(code, 0)
        self.assertEqual(payload["type"], "reference_retrieval")
        self.assertEqual(payload["retrieval"]["quality_gate"]["status"], "sufficient")

    def test_reference_store_cli_ingests_lists_and_retrieves(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "references.sqlite3"
            input_path = root / "references.json"
            input_path.write_text(
                json.dumps(
                    [
                        {
                            "reference_id": "stored-success",
                            "source": "Stored success",
                            "source_url": "https://example.com/stored-success",
                            "source_type": "success_case",
                            "problem": "generic product direction",
                            "mechanism": "strategy gate",
                        },
                        {
                            "reference_id": "stored-failure",
                            "source": "Stored failure",
                            "source_type": "failure_case",
                            "problem": "generic product direction",
                            "mechanism": "dashboard without evidence",
                        },
                    ]
                ),
                encoding="utf-8",
            )
            code, ingested = run_console(
                ["--reference-db", str(database), "reference-ingest", "--input-file", str(input_path)]
            )
            self.assertEqual(code, 0)
            self.assertEqual(ingested["counts"]["created"], 2)

            code, listed = run_console(["--reference-db", str(database), "reference-list"])
            self.assertEqual(code, 0)
            self.assertEqual(listed["count"], 2)

            code, health = run_console(["--reference-db", str(database), "reference-health"])
            self.assertEqual(code, 0)
            self.assertEqual(health["health"]["reference_count"], 2)

            code, retrieved = run_console(
                [
                    "--reference-db",
                    str(database),
                    "retrieve",
                    "--payload-json",
                    json.dumps({"idea": "generic product direction"}),
                ]
            )
            self.assertEqual(code, 0)
            self.assertEqual(retrieved["retrieval"]["corpus_size"], 2)

    def test_reference_eval_cli_runs_checked_in_baseline(self):
        dataset = SCAFFOLD_ROOT / "evals" / "reference-retrieval.json"
        code, payload = run_console(["reference-eval", "--dataset-file", str(dataset)])
        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["metrics"]["gate_accuracy"], 1.0)

    def test_insight_apply_cli_persists_report_into_plan_state(self):
        with tempfile.TemporaryDirectory() as directory, PalamedesStateIsolation():
            report_path = Path(directory) / "strategy-report.json"
            report_path.write_text(json.dumps(VALID_REPORT), encoding="utf-8")
            code, payload = run_console(["--allow-unhealthy-writes", "insight-apply", "--report-file", str(report_path)])

            self.assertEqual(code, 0)
            self.assertEqual(payload["applied_count"], 1)
            plan = payload["post_cycle"]["plan"]
            self.assertIn(VALID_REPORT["reference_insights"][0]["transferable_principle"], plan["insights"])
            self.assertEqual(plan["evidence"][-1]["evidence_type"], "reference_extraction")

    def test_llm_runs_static_strategy_provider(self):
        with PalamedesStateIsolation():
            code, payload = run_console(
                [
                    "llm",
                    "--provider",
                    "static",
                    "--static-report-json",
                    json.dumps(VALID_REPORT),
                ]
            )

        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["type"], "strategy_llm_report")
        self.assertEqual(payload["report"]["decision"], "revise_before_build")

    def test_llm_runs_static_creative_strategy_provider(self):
        with PalamedesStateIsolation():
            code, payload = run_console(
                [
                    "llm",
                    "--action",
                    "generate_creative_directions",
                    "--provider",
                    "static",
                    "--static-report-json",
                    json.dumps(VALID_REPORT),
                ]
            )

        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["report"]["creative_directions"][0]["name"], "Pre-build Strategy Gate")

    def test_route_validates_strategy_next_actions(self):
        with PalamedesStateIsolation():
            code, payload = run_console(
                [
                    "route",
                    "--report-json",
                    json.dumps(VALID_REPORT),
                ]
            )

        self.assertEqual(code, 0)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["type"], "strategy_action_routes")
        self.assertTrue(payload["routes"][0]["executable"])

    def test_reviewer_cannot_run_planner_write(self):
        with PalamedesStateIsolation():
            code, event = run_console(
                [
                    "run",
                    "--role",
                    "reviewer",
                    "--action",
                    "update_plan",
                    "--payload-json",
                    '{"goal":"denied"}',
                ]
            )

        self.assertEqual(code, 1)
        self.assertFalse(event["ok"])
        self.assertEqual(event["error"]["type"], "permission_denied")


if __name__ == "__main__":
    unittest.main()
