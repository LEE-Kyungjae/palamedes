#!/usr/bin/env python3
import io
import json
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from pathlib import Path

import palamedes
import palamedes_agent


class PalamedesStateIsolation:
    def __init__(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.state_dir = self.root / ".palamedes"
        self.originals = {}

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
        self.tempdir.cleanup()


class PalamedesRegressionTests(unittest.TestCase):
    def test_default_plan_exposes_schema_version_and_legacy_alias(self):
        plan = palamedes.default_plan()

        self.assertEqual(plan["schema_version"], palamedes.CONTRACT_VERSION)
        self.assertEqual(plan["version"], plan["schema_version"])

    def test_migrate_plan_backfills_schema_version_from_legacy_version(self):
        migrated = palamedes.migrate_plan({"version": "0.4.0"})

        self.assertEqual(migrated["schema_version"], "0.4.0")
        self.assertEqual(migrated["version"], "0.4.0")
        self.assertEqual(migrated["view_transitions"], [])

    def test_view_transition_validation_requires_traceable_change(self):
        plan = palamedes.default_plan()
        plan["view_transitions"] = [
            {
                "ts": "2026-07-25T00:00:00+00:00",
                "previous_view": "Generic LLM output is the primary problem.",
                "trigger": "RAG and agent systems improved.",
                "new_view": "Convergence can reappear across the whole system.",
                "new_blind_spots": "May overvalue process.",
                "opened_paths": ["Compare current systems"],
                "next_probe": "Run one live longitudinal case.",
                "source": "owner-codex-inquiry",
                "references": ["PALAMEDES_INQUIRY.md"],
                "plan_effect": "add_probe",
                "plan_effect_reason": "The new view warrants a bounded comparison.",
            }
        ]

        self.assertTrue(palamedes.validate_plan_shape(plan)["valid"])
        plan["view_transitions"][0]["next_probe"] = ""
        report = palamedes.validate_plan_shape(plan)
        self.assertFalse(report["valid"])
        self.assertIn(
            "view_transitions[0].next_probe must be a non-empty string",
            report["errors"],
        )

    def test_epistemic_records_validate_as_distinct_state(self):
        plan = palamedes.default_plan()
        plan["inquiry_items"] = [{
            "ts": "2026-07-25T00:00:00+00:00",
            "statement": "Would fine-tuning help?",
            "kind": "thought_experiment",
            "status": "closed",
            "intent": "Widen reasoning rather than propose a roadmap.",
            "commitment": "none",
            "source": "owner",
            "opened_questions": ["Where is the actual bottleneck?"],
            "references": [],
        }]
        plan["reference_encounters"] = [{
            "ts": "2026-07-25T00:00:00+00:00",
            "reference": "repo-a",
            "encountered_while": "Studying agent memory",
            "initial_interest": "It preserves provenance.",
            "relation": "Could inform Palamedes memory.",
            "effect": "opened_question",
            "adoption": "not_decided",
            "later_outcome": "",
            "source": "manual",
        }]
        plan["development_probes"] = [{
            "id": "probe-1",
            "ts": "2026-07-25T00:00:00+00:00",
            "step": "Run one live cycle.",
            "expected_learning": "Whether view memory adds value.",
            "expected_result": "",
            "status": "planned",
            "actual_observation": "",
            "unexpected_observation": "",
            "view_transition_id": "",
            "next_step": "",
            "source": "manual",
            "references": [],
        }]
        plan["open_questions"] = [{
            "id": "question-1",
            "ts": "2026-07-25T00:00:00+00:00",
            "question": "Should creativity and success be combined?",
            "perspectives": [
                {"view": "creativity", "reveals": ["possibility"], "hides": ["viability"]},
                {"view": "success", "reveals": ["reality"], "hides": ["fragile novelty"]},
            ],
            "resolution": "intentionally_open",
            "revisit_when": "After three live cases.",
            "source": "conversation",
            "references": [],
        }]

        self.assertTrue(palamedes.validate_plan_shape(plan)["valid"])
        plan["inquiry_items"][0]["kind"] = "roadmap_by_assumption"
        self.assertFalse(palamedes.validate_plan_shape(plan)["valid"])

    def test_cmd_view_records_transition_event_and_revision(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            args = Namespace(
                previous_view="Palamedes should generate the best answer.",
                trigger="Development revealed that building changes what can be seen.",
                new_view="Palamedes should preserve why views change.",
                new_blind_spots="Process can become an excuse for drift.",
                opened_paths="record transitions,compare baselines",
                next_probe="Use it through one live development cycle.",
                source="conversation",
                references="PALAMEDES_INQUIRY.md",
                json=False,
            )
            with redirect_stdout(io.StringIO()):
                palamedes.cmd_view(args)
            plan = palamedes.load_plan()
            events = palamedes.read_jsonl(palamedes.EVENTS_PATH)
            revisions = palamedes.list_revisions(limit=1)

        self.assertEqual(len(plan["view_transitions"]), 1)
        self.assertEqual(plan["view_transitions"][0]["opened_paths"], ["record transitions", "compare baselines"])
        self.assertEqual(events[-1]["type"], "view_transition_recorded")
        self.assertEqual(revisions[0]["source"], "cmd_view")

    def test_slash_command_mapping_covers_restore_preview(self):
        tool_name, payload = palamedes_agent.slash_to_tool("/palamedes.restore-preview revision_id=rev-123")

        self.assertEqual(tool_name, "preview_restore")
        self.assertEqual(payload, {"revision_id": "rev-123"})

    def test_natural_language_mapping_covers_restore_revision(self):
        tool_name, payload = palamedes_agent.natural_language_to_tool("restore revision revision_id=rev-456")

        self.assertEqual(tool_name, "restore_revision")
        self.assertEqual(payload, {"revision_id": "rev-456"})

    def test_natural_language_mapping_covers_previous_revision_shortcuts(self):
        preview_tool, preview_payload = palamedes_agent.natural_language_to_tool("preview previous revision")
        restore_tool, restore_payload = palamedes_agent.natural_language_to_tool("restore previous revision")

        self.assertEqual(preview_tool, "preview_restore")
        self.assertEqual(preview_payload, {"previous": True})
        self.assertEqual(restore_tool, "restore_revision")
        self.assertEqual(restore_payload, {"previous": True})

    def test_slash_command_mapping_covers_reference_discovery(self):
        tool_name, payload = palamedes_agent.slash_to_tool("/palamedes.discover question=design-agent references=repo-a,repo-b")

        self.assertEqual(tool_name, "run_reference_discovery")
        self.assertEqual(payload, {"question": "design-agent", "references": ["repo-a", "repo-b"]})

    def test_view_transition_tool_replays_without_duplicate_append(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            payload = {
                "previous_view": "A single strategist should find the answer.",
                "trigger": "Implementation exposed a new constraint.",
                "new_view": "The changed view should be preserved.",
                "new_blind_spots": "May overvalue process.",
                "opened_paths": ["longitudinal evaluation"],
                "next_probe": "Run one live cycle.",
                "source": "conversation",
                "references": ["PALAMEDES_INQUIRY.md"],
                "idempotency_key": "view-1",
            }
            first = palamedes_agent.execute_tool("record_view_transition", payload)
            second = palamedes_agent.execute_tool("record_view_transition", payload)

        self.assertFalse(first["idempotency_replayed"])
        self.assertTrue(second["idempotency_replayed"])
        self.assertEqual(len(second["plan"]["view_transitions"]), 1)
        self.assertEqual(first["fingerprint"], second["fingerprint"])

    def test_slash_command_mapping_covers_view_transition_arrays(self):
        tool_name, payload = palamedes_agent.slash_to_tool(
            '/palamedes.view previous_view="old" trigger="signal" '
            'new_view="new" opened_paths="path-a,path-b" '
            'next_probe="probe" references="ref-a,ref-b"'
        )

        self.assertEqual(tool_name, "record_view_transition")
        self.assertEqual(payload["opened_paths"], ["path-a", "path-b"])
        self.assertEqual(payload["references"], ["ref-a", "ref-b"])

    def test_epistemic_agent_tools_append_distinct_records(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            inquiry = palamedes_agent.execute_tool("record_inquiry_item", {
                "statement": "Would fine-tuning help?",
                "kind": "thought_experiment",
                "status": "closed",
                "intent": "Widen the reasoning space.",
                "commitment": "none",
                "idempotency_key": "inquiry-1",
            })
            encounter = palamedes_agent.execute_tool("record_reference_encounter", {
                "reference": "repo-a",
                "encountered_while": "Studying agent memory",
                "initial_interest": "Provenance",
                "relation": "Could inform Palamedes",
                "effect": "opened_question",
                "idempotency_key": "encounter-1",
            })
            probe = palamedes_agent.execute_tool("record_development_probe", {
                "step": "Run one live cycle",
                "expected_learning": "Whether the memory is useful",
                "idempotency_key": "probe-1",
            })
            question = palamedes_agent.execute_tool("record_open_question", {
                "question": "How should creativity and success interact?",
                "perspectives": [
                    {"view": "creativity", "reveals": ["possibility"], "hides": ["viability"]},
                    {"view": "success", "reveals": ["reality"], "hides": ["fragile novelty"]},
                ],
                "revisit_when": "After three cases",
                "idempotency_key": "question-1",
            })

        self.assertEqual(len(question["plan"]["inquiry_items"]), 1)
        self.assertEqual(len(question["plan"]["reference_encounters"]), 1)
        self.assertEqual(len(question["plan"]["development_probes"]), 1)
        self.assertEqual(len(question["plan"]["open_questions"]), 1)
        self.assertEqual(inquiry["record"]["commitment"], "none")
        self.assertEqual(encounter["record"]["effect"], "opened_question")
        self.assertTrue(probe["record"]["id"].startswith("probe-"))

    def test_add_evidence_idempotency_key_replays_without_duplicate_append(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            first = palamedes_agent.execute_tool(
                "add_evidence",
                {
                    "claim": "Repeated buyer pain",
                    "source": "pilot-call",
                    "confidence": 74,
                    "idempotency_key": "evt-1",
                },
            )
            second = palamedes_agent.execute_tool(
                "add_evidence",
                {
                    "claim": "Repeated buyer pain",
                    "source": "pilot-call",
                    "confidence": 74,
                    "idempotency_key": "evt-1",
                },
            )

        self.assertFalse(first["idempotency_replayed"])
        self.assertTrue(second["idempotency_replayed"])
        self.assertEqual(len(second["plan"]["evidence"]), 1)
        self.assertEqual(first["fingerprint"], second["fingerprint"])

    def test_request_review_tool_appends_human_escalation_and_replays_idempotently(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            base = palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "Need review path",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-30",
                },
            )
            payload = {
                "scope": "reference_discovery",
                "reason": "Shortlist adoption changes Palamedes boundary decisions.",
                "requested_by": "planner",
                "priority": "high",
                "assigned_to": "owner",
                "stale_after": "2026-05-01T09:00:00Z",
                "sla_bucket": "24h",
                "review_recommendation": "owner_decision_required",
                "related_references": ["paperclip", "airflow"],
                "idempotency_key": "review-1",
            }
            first = palamedes_agent.execute_tool(
                "request_review",
                {**payload, "expected_fingerprint": base["fingerprint"]},
            )
            second = palamedes_agent.execute_tool(
                "request_review",
                payload,
            )

        self.assertFalse(first["idempotency_replayed"])
        self.assertTrue(second["idempotency_replayed"])
        self.assertEqual(len(second["plan"]["human_escalations"]), 1)
        self.assertEqual(second["review_request"]["scope"], "reference_discovery")
        self.assertEqual(second["review_request"]["priority"], "high")
        self.assertEqual(second["review_request"]["assigned_to"], "owner")
        self.assertEqual(second["review_request"]["stale_after"], "2026-05-01T09:00:00Z")
        self.assertEqual(second["review_request"]["sla_bucket"], "24h")
        self.assertEqual(second["plan"]["human_escalations"][0]["review_recommendation"], "owner_decision_required")
        self.assertEqual(first["fingerprint"], second["fingerprint"])

    def test_list_reviews_tool_filters_open_review_records(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            base = palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "Need review listing",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-30",
                },
            )
            requested = palamedes_agent.execute_tool(
                "request_review",
                {
                    "scope": "plan",
                    "reason": "Need owner review.",
                    "requested_by": "planner",
                    "expected_fingerprint": base["fingerprint"],
                },
            )
            palamedes_agent.execute_tool(
                "resolve_review",
                {
                    "request_id": requested["review_request"]["id"],
                    "status": "resolved",
                    "resolution": "Reviewed.",
                    "resolved_by": "owner",
                    "assigned_to": "reviewer",
                    "expected_fingerprint": requested["fingerprint"],
                },
            )
            open_result = palamedes_agent.execute_tool("list_reviews", {"status": "open"})
            resolved_result = palamedes_agent.execute_tool("list_reviews", {"status": "resolved", "assigned_to": "reviewer"})

        self.assertEqual(open_result["count"], 0)
        self.assertEqual(resolved_result["count"], 1)
        self.assertEqual(resolved_result["reviews"][0]["status"], "resolved")
        self.assertEqual(resolved_result["reviews"][0]["assigned_to"], "reviewer")

    def test_list_reviews_tool_sorts_by_priority_and_requested_at(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            base = palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "Need review sorting",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-30",
                },
            )
            first = palamedes_agent.execute_tool(
                "request_review",
                {
                    "scope": "plan",
                    "reason": "Low priority queue item.",
                    "requested_by": "planner",
                    "priority": "low",
                    "request_id": "review-low",
                    "expected_fingerprint": base["fingerprint"],
                },
            )
            second = palamedes_agent.execute_tool(
                "request_review",
                {
                    "scope": "plan",
                    "reason": "High priority queue item.",
                    "requested_by": "planner",
                    "priority": "high",
                    "request_id": "review-high",
                    "expected_fingerprint": first["fingerprint"],
                },
            )
            priority_sorted = palamedes_agent.execute_tool(
                "list_reviews",
                {"sort_by": "priority", "order": "desc"},
            )
            requested_sorted = palamedes_agent.execute_tool(
                "list_reviews",
                {"sort_by": "requested_at", "order": "asc"},
            )

        self.assertEqual([item["id"] for item in priority_sorted["reviews"][:2]], ["review-high", "review-low"])
        self.assertEqual([item["id"] for item in requested_sorted["reviews"][:2]], ["review-low", "review-high"])

    def test_list_reviews_tool_sorts_by_stale_after_and_leaves_missing_deadlines_last(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            base = palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "Need stale-after review sorting",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-30",
                },
            )
            first = palamedes_agent.execute_tool(
                "request_review",
                {
                    "scope": "plan",
                    "reason": "Later deadline queue item.",
                    "requested_by": "planner",
                    "request_id": "review-late",
                    "stale_after": "2026-05-03T09:00:00Z",
                    "expected_fingerprint": base["fingerprint"],
                },
            )
            second = palamedes_agent.execute_tool(
                "request_review",
                {
                    "scope": "plan",
                    "reason": "Soon deadline queue item.",
                    "requested_by": "planner",
                    "request_id": "review-soon",
                    "stale_after": "2026-04-26T09:00:00Z",
                    "expected_fingerprint": first["fingerprint"],
                },
            )
            third = palamedes_agent.execute_tool(
                "request_review",
                {
                    "scope": "plan",
                    "reason": "No deadline queue item.",
                    "requested_by": "planner",
                    "request_id": "review-none",
                    "expected_fingerprint": second["fingerprint"],
                },
            )
            stale_sorted = palamedes_agent.execute_tool(
                "list_reviews",
                {"sort_by": "stale_after", "order": "asc"},
            )

        self.assertEqual([item["id"] for item in stale_sorted["reviews"][:3]], ["review-soon", "review-late", "review-none"])
        self.assertEqual(stale_sorted["filters"]["sort_by"], "stale_after")

    def test_get_review_and_update_review_tools_return_and_modify_one_record(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            base = palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "Need review detail path",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-30",
                },
            )
            requested = palamedes_agent.execute_tool(
                "request_review",
                {
                    "scope": "plan",
                    "reason": "Need triage owner.",
                    "requested_by": "planner",
                    "expected_fingerprint": base["fingerprint"],
                },
            )
            detail = palamedes_agent.execute_tool(
                "get_review",
                {"request_id": requested["review_request"]["id"]},
            )
            updated = palamedes_agent.execute_tool(
                "update_review",
                {
                    "request_id": requested["review_request"]["id"],
                    "priority": "high",
                    "assigned_to": "reviewer",
                    "stale_after": "2026-05-03T09:00:00Z",
                    "sla_bucket": "72h",
                    "review_recommendation": "human_review",
                    "expected_fingerprint": requested["fingerprint"],
                },
            )

        self.assertEqual(detail["review"]["id"], requested["review_request"]["id"])
        self.assertEqual(updated["review_request"]["priority"], "high")
        self.assertEqual(updated["review_request"]["assigned_to"], "reviewer")
        self.assertEqual(updated["review_request"]["stale_after"], "2026-05-03T09:00:00Z")
        self.assertEqual(updated["review_request"]["sla_bucket"], "72h")
        self.assertEqual(updated["review_request"]["review_recommendation"], "human_review")

    def test_resolve_review_tool_updates_existing_human_escalation_and_replays_idempotently(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            base = palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "Need review resolution path",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-30",
                },
            )
            requested = palamedes_agent.execute_tool(
                "request_review",
                {
                    "scope": "plan",
                    "reason": "Owner must choose whether to continue this branch.",
                    "requested_by": "planner",
                    "idempotency_key": "review-open-1",
                    "expected_fingerprint": base["fingerprint"],
                },
            )
            payload = {
                "request_id": requested["review_request"]["id"],
                "status": "resolved",
                "resolution": "Owner approved continuing the branch.",
                "resolved_by": "owner",
                "idempotency_key": "review-resolve-1",
            }
            first = palamedes_agent.execute_tool(
                "resolve_review",
                {**payload, "expected_fingerprint": requested["fingerprint"]},
            )
            second = palamedes_agent.execute_tool("resolve_review", payload)

        self.assertFalse(first["idempotency_replayed"])
        self.assertTrue(second["idempotency_replayed"])
        self.assertEqual(second["review_request"]["status"], "resolved")
        self.assertEqual(second["review_request"]["resolution"], "Owner approved continuing the branch.")
        self.assertEqual(second["review_request"]["resolved_by"], "owner")
        self.assertEqual(first["fingerprint"], second["fingerprint"])

    def test_replan_idempotency_key_replays_without_duplicate_task_append(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            first = palamedes_agent.execute_tool(
                "replan",
                {
                    "plan_task": "Refine activation hypothesis",
                    "idempotency_key": "replan-1",
                },
            )
            second = palamedes_agent.execute_tool(
                "replan",
                {
                    "plan_task": "Refine activation hypothesis",
                    "idempotency_key": "replan-1",
                },
            )

        self.assertFalse(first["idempotency_replayed"])
        self.assertTrue(second["idempotency_replayed"])
        self.assertEqual(second["plan"]["plan_tasks"], ["Refine activation hypothesis"])
        self.assertEqual(first["fingerprint"], second["fingerprint"])

    def test_qa_autoreplan_upgrades_thin_plan_to_pass(self):
        plan = palamedes.default_plan()
        plan["goal"] = "Test goal"
        plan["success_metric"] = "Reach 3 pilot users"
        plan["deadline"] = "2026-04-10"

        with PalamedesStateIsolation():
            result = palamedes.qa_autoreplan_result(plan)

        self.assertTrue(result["auto_replan"]["triggered"])
        self.assertEqual(result["auto_replan"]["blocked"], [])
        self.assertEqual(result["qa"]["result"], "PASS")
        self.assertEqual(result["qa"]["result"], "PASS")
        self.assertGreaterEqual(result["qa"]["score"], result["qa"]["threshold"])
        self.assertTrue(result["plan"]["planning_horizon"])
        self.assertTrue(result["plan"]["review_cadence"])
        self.assertGreaterEqual(len(result["plan"]["references"]), 3)

    def test_qa_autoreplan_blocks_manual_core_fields(self):
        plan = palamedes.default_plan()

        with PalamedesStateIsolation():
            result = palamedes.qa_autoreplan_result(plan)

        self.assertTrue(result["auto_replan"]["triggered"])
        self.assertIn("goal_clarity", result["auto_replan"]["blocked"])
        self.assertIn("measurability", result["auto_replan"]["blocked"])
        self.assertEqual(result["qa"]["result"], "CRITICAL_FAILURE")

    def test_update_plan_tool_returns_autoreplan_metadata(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            result = palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "Thin plan test",
                    "success_metric": "Hit 2 pilots",
                    "deadline": "2026-04-01",
                    "constraints": [],
                    "assumptions": [],
                    "options": [],
                    "plan_tasks": [],
                    "execution_tasks": [],
                    "dependencies": [],
                    "experiments": [],
                    "risks": [],
                    "references": [],
                    "insights": [],
                    "direction_insights": [],
                    "market_insights": [],
                    "timing_insights": [],
                    "differentiation_insights": [],
                    "monetization_insights": [],
                    "constraint_insights": [],
                    "risk_signal_insights": [],
                    "evolution_insights": [],
                    "definition_of_done": [],
                },
            )
            event_lines = palamedes.EVENTS_PATH.read_text(encoding="utf-8").strip().splitlines()
            auto_replan_events = [json.loads(line) for line in event_lines if '"type": "auto_replan"' in line]
            summary = palamedes.plan_summary(result["plan"])

        self.assertIn("auto_replan", result)
        self.assertTrue(result["ok"])
        self.assertEqual(result["tool_name"], "update_plan")
        self.assertEqual(result["result_type"], "mutation")
        self.assertTrue(result["auto_replan"]["triggered"])
        self.assertEqual(result["auto_replan"]["blocked"], [])
        self.assertEqual(result["qa"]["result"], "PASS")
        self.assertEqual(result["validation"], {"valid": True, "errors": []})
        self.assertEqual(result["fingerprint"], palamedes.plan_fingerprint(result["plan"]))
        self.assertTrue(auto_replan_events)
        self.assertIn("final_score", auto_replan_events[-1])
        self.assertIn("score_delta", auto_replan_events[-1])
        self.assertIsNotNone(summary["recent_auto_replan"])
        self.assertEqual(summary["recent_auto_replan"]["final_result"], "PASS")
        self.assertTrue(summary["recent_auto_replan"]["actions"])

    def test_mutate_plan_state_rejects_stale_expected_fingerprint(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            initial = palamedes.load_plan()
            initial_fingerprint = palamedes.plan_fingerprint(initial)
            updated = palamedes.mutate_plan_state(lambda plan: plan.update({"goal": "first"}))
            self.assertEqual(updated["goal"], "first")

            with self.assertRaises(palamedes.PlanConflictError) as ctx:
                palamedes.mutate_plan_state(
                    lambda plan: plan.update({"goal": "second"}),
                    expected_fingerprint=initial_fingerprint,
                )

        self.assertEqual(ctx.exception.current_fingerprint, palamedes.plan_fingerprint(updated))

    def test_update_plan_tool_rejects_stale_expected_fingerprint(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            first = palamedes_agent.execute_tool("get_plan", {})
            palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "fresh write",
                    "expected_fingerprint": first["fingerprint"],
                },
            )
            with self.assertRaisesRegex(palamedes.PlanConflictError, "plan fingerprint mismatch"):
                palamedes_agent.execute_tool(
                    "update_plan",
                    {
                        "goal": "stale write",
                        "expected_fingerprint": first["fingerprint"],
                    },
                )

    def test_replan_tool_validates_confidence_type(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            with self.assertRaisesRegex(ValueError, "evidence_confidence must be an integer"):
                palamedes_agent.execute_tool(
                    "replan",
                    {
                        "evidence": "pilot feedback",
                        "evidence_confidence": "high",
                    },
                )

    def test_replan_tool_persists_incremental_fields_and_metadata(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "Seed plan",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                    "constraints": [],
                    "assumptions": [],
                    "options": [],
                    "plan_tasks": [],
                    "execution_tasks": [],
                    "dependencies": [],
                    "experiments": [],
                    "risks": [],
                    "references": [],
                    "insights": [],
                    "direction_insights": [],
                    "market_insights": [],
                    "timing_insights": [],
                    "differentiation_insights": [],
                    "monetization_insights": [],
                    "constraint_insights": [],
                    "risk_signal_insights": [],
                    "evolution_insights": [],
                    "definition_of_done": [],
                },
            )
            result = palamedes_agent.execute_tool(
                "replan",
                {
                    "evidence": "pilot users returned after week one",
                    "evidence_confidence": 71,
                    "evidence_axis": "market",
                    "plan_task": "Refine segment definition",
                    "execution_task": "Interview three pilot users",
                    "reference": "pilot:week-1",
                },
            )

        self.assertIn("summary", result)
        self.assertIn("validation", result)
        self.assertIn("auto_replan", result)
        self.assertEqual(result["validation"], {"valid": True, "errors": []})
        self.assertEqual(result["qa"]["result"], "PASS")
        self.assertIn("Refine segment definition", result["plan"]["plan_tasks"])
        self.assertIn("Interview three pilot users", result["plan"]["execution_tasks"])
        self.assertIn("pilot:week-1", result["plan"]["references"])
        self.assertTrue(
            any(
                isinstance(item, dict) and item.get("claim") == "pilot users returned after week one"
                for item in result["plan"]["evidence"]
            )
        )

    def test_blocked_autoreplan_event_has_no_final_score(self):
        plan = palamedes.default_plan()

        with PalamedesStateIsolation():
            result = palamedes.qa_autoreplan_result(plan)
            events = [json.loads(line) for line in palamedes.EVENTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertTrue(result["auto_replan"]["triggered"])
        self.assertTrue(result["auto_replan"]["blocked"])
        auto_replan_events = [event for event in events if event.get("type") == "auto_replan"]
        self.assertEqual(len(auto_replan_events), 1)
        self.assertNotIn("final_score", auto_replan_events[0])
        self.assertNotIn("score_delta", auto_replan_events[0])

    def test_no_autoreplan_does_not_emit_autoreplan_event(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            plan = palamedes.load_plan()
            plan.update(
                {
                    "goal": "Complete plan",
                    "success_metric": "Reach 3 pilots",
                    "deadline": "2026-04-05",
                    "planning_horizon": "3 weeks",
                    "review_cadence": "weekly",
                    "constraints": ["time: 1h/day"],
                    "assumptions": ["Target users have recurring pain."],
                    "options": ["Option A", "Option B"],
                    "selected_option": "Option A",
                    "plan_tasks": ["Define references", "Choose strategy"],
                    "execution_tasks": ["Run pilot", "Track outcomes"],
                    "dependencies": ["Agent runtime support"],
                    "experiments": ["Run one pilot loop."],
                    "risks": [{"risk": "Scope drift", "signal": "new requests", "mitigation": "freeze scope"}],
                    "references": ["ref-a", "ref-b", "ref-c"],
                    "insights": ["Planning matters", "Evidence matters", "Replan from signals"],
                    "direction_insights": ["why now", "decision leverage", "deprioritize distractions"],
                    "market_insights": ["target segment pain", "high-frequency need", "switching pain"],
                    "timing_insights": ["window is open", "delay costs learning", "market timing matters"],
                    "differentiation_insights": ["distinct angle", "visible first-session difference", "clear tradeoff"],
                    "monetization_insights": ["value to revenue path", "early pricing proxy", "paid signal"],
                    "constraint_insights": ["time limited", "resource cap", "scope cap"],
                    "risk_signal_insights": ["early churn signal", "false momentum metric", "replan trigger"],
                    "evolution_insights": ["weekly plan review", "review evidence", "compound learning"],
                    "definition_of_done": ["QA passes", "pilot is measured"],
                    "evidence": [
                        {"claim": "Users repeated pain weekly", "source": "interviews", "confidence": 72, "axis": "market", "date": "2026-03-20"},
                        {"claim": "Alternatives fail core workflow", "source": "competitor-review", "confidence": 70, "axis": "differentiation", "date": "2026-03-20"},
                        {"claim": "Users pay for time savings", "source": "pricing-survey", "confidence": 66, "axis": "monetization", "date": "2026-03-20"},
                    ],
                    "hypothesis_log": [
                        {"ts": "2026-03-20T00:00:00+00:00", "hypothesis": "Narrow segment returns weekly", "metric": "wau", "target": ">=3", "window": "7 days", "status": "open", "outcome": ""}
                    ],
                    "phase_plan": ["Phase 1", "Phase 2", "Phase 3"],
                }
            )
            palamedes.save_validated_plan(plan)
            result = palamedes.qa_autoreplan_result(plan)
            events = [json.loads(line) for line in palamedes.EVENTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertFalse(result["auto_replan"]["triggered"])
        self.assertFalse(any(event.get("type") == "auto_replan" for event in events))

    def test_critical_failure_can_still_trigger_autoreplan_when_score_is_high(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            plan = palamedes.load_plan()
            plan.update(
                {
                    "goal": "High score critical failure",
                    "success_metric": "Reach 3 pilots",
                    "deadline": "2026-04-05",
                    "planning_horizon": "3 weeks",
                    "review_cadence": "weekly",
                    "constraints": ["time: 1h/day"],
                    "assumptions": ["Users have recurring pain."],
                    "options": ["Option A", "Option B"],
                    "selected_option": "Option A",
                    "plan_tasks": ["Define references", "Choose strategy"],
                    "execution_tasks": ["Run pilot", "Track outcomes"],
                    "dependencies": ["Agent runtime support"],
                    "experiments": ["Run one pilot loop."],
                    "risks": [{"risk": "Scope drift", "signal": "new requests", "mitigation": "freeze scope"}],
                    "references": ["ref-a", "ref-b", "ref-c"],
                    "insights": ["Planning matters", "Evidence matters", "Replan from signals"],
                    "direction_insights": ["why now", "decision leverage", "deprioritize distractions"],
                    "market_insights": ["target segment pain", "high-frequency need", "switching pain"],
                    "timing_insights": ["window is open", "delay costs learning", "market timing matters"],
                    "differentiation_insights": ["distinct angle", "visible first-session difference", "clear tradeoff"],
                    "monetization_insights": ["value to revenue path", "early pricing proxy", "paid signal"],
                    "constraint_insights": ["time limited", "resource cap", "scope cap"],
                    "risk_signal_insights": ["early churn signal", "false momentum metric", "replan trigger"],
                    "evolution_insights": ["weekly plan review", "review evidence", "compound learning"],
                    "definition_of_done": [],
                    "evidence": [
                        {"claim": "Users repeated pain weekly", "source": "interviews", "confidence": 72, "axis": "market", "date": "2026-03-20"},
                        {"claim": "Alternatives fail core workflow", "source": "competitor-review", "confidence": 70, "axis": "differentiation", "date": "2026-03-20"},
                        {"claim": "Users pay for time savings", "source": "pricing-survey", "confidence": 66, "axis": "monetization", "date": "2026-03-20"},
                    ],
                    "hypothesis_log": [
                        {"ts": "2026-03-20T00:00:00+00:00", "hypothesis": "Narrow segment returns weekly", "metric": "wau", "target": ">=3", "window": "7 days", "status": "open", "outcome": ""}
                    ],
                    "phase_plan": ["Phase 1", "Phase 2", "Phase 3"],
                }
            )
            result = palamedes.qa_autoreplan_result(plan)

        self.assertTrue(result["auto_replan"]["triggered"])
        self.assertEqual(result["auto_replan"]["blocked"], [])
        self.assertEqual(result["qa"]["result"], "PASS")
        self.assertTrue(result["plan"]["definition_of_done"])

    def test_plan_summary_ignores_stale_autoreplan_event(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "Summary freshness",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                    "constraints": [],
                    "assumptions": [],
                    "options": [],
                    "plan_tasks": [],
                    "execution_tasks": [],
                    "dependencies": [],
                    "experiments": [],
                    "risks": [],
                    "references": [],
                    "insights": [],
                    "direction_insights": [],
                    "market_insights": [],
                    "timing_insights": [],
                    "differentiation_insights": [],
                    "monetization_insights": [],
                    "constraint_insights": [],
                    "risk_signal_insights": [],
                    "evolution_insights": [],
                    "definition_of_done": [],
                },
            )
            plan = palamedes.load_plan()
            plan["goal"] = "Manual follow-up edit"
            palamedes.save_validated_plan(plan)
            summary = palamedes.plan_summary(plan)

        self.assertIsNone(summary["recent_auto_replan"])

    def test_show_prints_recent_auto_replan_summary(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "Show summary test",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                    "constraints": [],
                    "assumptions": [],
                    "options": [],
                    "plan_tasks": [],
                    "execution_tasks": [],
                    "dependencies": [],
                    "experiments": [],
                    "risks": [],
                    "references": [],
                    "insights": [],
                    "direction_insights": [],
                    "market_insights": [],
                    "timing_insights": [],
                    "differentiation_insights": [],
                    "monetization_insights": [],
                    "constraint_insights": [],
                    "risk_signal_insights": [],
                    "evolution_insights": [],
                    "definition_of_done": [],
                },
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                palamedes.cmd_show(None)
            output = stdout.getvalue()

        self.assertIn("Recent Auto Replan:", output)
        self.assertIn("Recent Auto Replan Actions:", output)

    def test_update_plan_records_revision_history_and_restore_revision_tool(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            first = palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "first goal",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                },
            )
            second = palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "second goal",
                    "expected_fingerprint": first["fingerprint"],
                },
            )
            history = palamedes_agent.execute_tool("get_history", {"limit": 10})
            restored = palamedes_agent.execute_tool(
                "restore_revision",
                {
                    "revision_id": history["revisions"][-1]["revision_id"],
                    "expected_fingerprint": second["fingerprint"],
                },
            )

        self.assertGreaterEqual(len(history["revisions"]), 2)
        self.assertEqual(history["revisions"][0]["source"], "update_plan")
        self.assertIn("metadata", history["revisions"][0])
        self.assertEqual(history["revisions"][0]["metadata"]["qa_result"], "PASS")
        self.assertEqual(restored["restored_revision_id"], history["revisions"][-1]["revision_id"])
        self.assertEqual(restored["plan"]["goal"], "first goal")
        self.assertEqual(restored["fingerprint"], palamedes.plan_fingerprint(restored["plan"]))

    def test_cmd_history_and_restore_print_revision_info(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "history print test",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                },
            )
            revisions = palamedes.list_revisions(limit=1)
            history_stdout = io.StringIO()
            with redirect_stdout(history_stdout):
                palamedes.cmd_history(type("Args", (), {"limit": 5, "json": False})())
            restore_stdout = io.StringIO()
            with redirect_stdout(restore_stdout):
                palamedes.cmd_restore(
                    type(
                        "Args",
                        (),
                        {
                            "revision_id": revisions[0]["revision_id"],
                            "expected_fingerprint": "",
                        },
                    )()
                )

        self.assertIn(revisions[0]["revision_id"], history_stdout.getvalue())
        self.assertIn("Restored revision", restore_stdout.getvalue())
        self.assertIn("qa=", history_stdout.getvalue())

    def test_preview_restore_reports_changed_fields_without_mutation(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            first = palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "preview first goal",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                },
            )
            second = palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "preview second goal",
                    "expected_fingerprint": first["fingerprint"],
                },
            )
            history = palamedes_agent.execute_tool("get_history", {"limit": 10})
            preview = palamedes_agent.execute_tool(
                "preview_restore",
                {
                    "revision_id": history["revisions"][-1]["revision_id"],
                },
            )
            current_plan = palamedes.load_plan()

        self.assertFalse(preview["no_op"])
        self.assertIn("goal", preview["changed_fields"])
        self.assertIn("metadata", preview)
        self.assertEqual(preview["metadata"]["goal"], "preview first goal")
        self.assertTrue(preview["diff"])
        goal_diff = next(item for item in preview["diff"] if item["field"] == "goal")
        self.assertEqual(goal_diff["before"]["type"], "scalar")
        self.assertEqual(goal_diff["after"]["type"], "scalar")
        self.assertEqual(current_plan["goal"], "preview second goal")
        self.assertEqual(preview["current_fingerprint"], second["fingerprint"])

    def test_restore_revision_tool_emits_plan_restored_event(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            first = palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "restore source goal",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                },
            )
            second = palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "restore target goal",
                    "expected_fingerprint": first["fingerprint"],
                },
            )
            history = palamedes_agent.execute_tool("get_history", {"limit": 10})
            palamedes_agent.execute_tool(
                "restore_revision",
                {
                    "revision_id": history["revisions"][-1]["revision_id"],
                    "expected_fingerprint": second["fingerprint"],
                },
            )
            events = [json.loads(line) for line in palamedes.EVENTS_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]

        self.assertTrue(any(event.get("type") == "plan_restored" and event.get("source") == "restore_revision" for event in events))

    def test_restore_previous_revision_without_revision_id(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            first = palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "previous first",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                },
            )
            second = palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "previous second",
                    "expected_fingerprint": first["fingerprint"],
                },
            )
            restored = palamedes_agent.execute_tool(
                "restore_revision",
                {
                    "previous": True,
                    "expected_fingerprint": second["fingerprint"],
                },
            )

        self.assertEqual(restored["plan"]["goal"], "previous first")

    def test_preview_previous_revision_without_revision_id(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            first = palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "preview previous first",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                },
            )
            palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "preview previous second",
                    "expected_fingerprint": first["fingerprint"],
                },
            )
            preview = palamedes_agent.execute_tool("preview_restore", {"previous": True})

        self.assertEqual(preview["selected_via"], "previous")
        self.assertEqual(preview["metadata"]["goal"], "preview previous first")

    def test_storage_health_report_detects_invalid_event_lines(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            palamedes.EVENTS_PATH.write_text('{"type":"ok"}\nnot-json\n', encoding="utf-8")
            report = palamedes.storage_health_report()

        self.assertEqual(report["status"], "degraded")
        self.assertEqual(report["logs"]["events"]["invalid_lines"], 1)
        self.assertTrue(any(issue.startswith("events_invalid_lines:1") for issue in report["issues"]))

    def test_revision_retention_prunes_to_latest_window(self):
        with PalamedesStateIsolation():
            palamedes.REVISION_RETENTION_LIMIT = 2
            palamedes.ensure_state()
            first = palamedes.mutate_plan_state(
                lambda plan: plan.update(
                    {
                        "goal": "retained first",
                        "success_metric": "Reach 2 pilots",
                        "deadline": "2026-04-03",
                    }
                ),
                revision_source="test_retention",
            )
            second = palamedes.mutate_plan_state(
                lambda plan: plan.update({"goal": "retained second"}),
                expected_fingerprint=palamedes.plan_fingerprint(first),
                revision_source="test_retention",
            )
            palamedes.mutate_plan_state(
                lambda plan: plan.update({"goal": "retained third"}),
                expected_fingerprint=palamedes.plan_fingerprint(second),
                revision_source="test_retention",
            )
            revisions = palamedes.list_revisions(limit=0)

        self.assertEqual(len(revisions), 2)
        self.assertEqual([item["metadata"]["goal"] for item in revisions], ["retained third", "retained second"])

    def test_restore_previous_survives_revision_pruning_floor(self):
        with PalamedesStateIsolation():
            palamedes.REVISION_RETENTION_LIMIT = 1
            palamedes.ensure_state()
            first = palamedes.mutate_plan_state(
                lambda plan: plan.update(
                    {
                        "goal": "restore floor first",
                        "success_metric": "Reach 2 pilots",
                        "deadline": "2026-04-03",
                    }
                ),
                revision_source="test_restore_floor",
            )
            second = palamedes.mutate_plan_state(
                lambda plan: plan.update({"goal": "restore floor second"}),
                expected_fingerprint=palamedes.plan_fingerprint(first),
                revision_source="test_restore_floor",
            )
            palamedes.mutate_plan_state(
                lambda plan: plan.update({"goal": "restore floor third"}),
                expected_fingerprint=palamedes.plan_fingerprint(second),
                revision_source="test_restore_floor",
            )
            restored = palamedes_agent.execute_tool(
                "restore_revision",
                {
                    "previous": True,
                    "expected_fingerprint": palamedes.plan_fingerprint(palamedes.load_plan()),
                },
            )

        self.assertEqual(restored["plan"]["goal"], "restore floor second")

    def test_event_retention_prunes_to_latest_window(self):
        with PalamedesStateIsolation():
            palamedes.EVENT_RETENTION_LIMIT = 2
            palamedes.ensure_state()
            palamedes.append_jsonl(palamedes.EVENTS_PATH, {"type": "evt1"})
            palamedes.append_jsonl(palamedes.EVENTS_PATH, {"type": "evt2"})
            palamedes.append_jsonl(palamedes.EVENTS_PATH, {"type": "evt3"})
            events = palamedes.read_jsonl(palamedes.EVENTS_PATH)

        self.assertEqual([event["type"] for event in events], ["evt2", "evt3"])

    def test_storage_health_report_tracks_latest_recoverable_revision(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            result = palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "health revision test",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                },
            )
            report = palamedes.storage_health_report()

        self.assertTrue(report["recovery_candidate_available"])
        self.assertTrue(report["latest_recoverable_revision_id"])
        self.assertEqual(report["latest_recoverable_revision_fingerprint"], result["fingerprint"])
        self.assertTrue(report["current_matches_latest_revision"])

    def test_storage_health_report_flags_divergence_from_latest_revision(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "divergence baseline",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                },
            )
            plan = palamedes.load_plan()
            plan["goal"] = "manual divergence"
            palamedes.save_validated_plan(plan)
            report = palamedes.storage_health_report()

        self.assertFalse(report["current_matches_latest_revision"])
        self.assertIn("current_plan_differs_from_latest_revision", report["issues"])

    def test_storage_health_report_includes_retention_limits_after_prune(self):
        with PalamedesStateIsolation():
            palamedes.EVENT_RETENTION_LIMIT = 2
            palamedes.REVISION_RETENTION_LIMIT = 2
            palamedes.ensure_state()
            first = palamedes.mutate_plan_state(
                lambda plan: plan.update(
                    {
                        "goal": "health retention first",
                        "success_metric": "Reach 2 pilots",
                        "deadline": "2026-04-03",
                    }
                ),
                revision_source="test_health_retention",
            )
            second = palamedes.mutate_plan_state(
                lambda plan: plan.update({"goal": "health retention second"}),
                expected_fingerprint=palamedes.plan_fingerprint(first),
                revision_source="test_health_retention",
            )
            palamedes.mutate_plan_state(
                lambda plan: plan.update({"goal": "health retention third"}),
                expected_fingerprint=palamedes.plan_fingerprint(second),
                revision_source="test_health_retention",
            )
            palamedes.append_jsonl(palamedes.EVENTS_PATH, {"type": "evt1"})
            palamedes.append_jsonl(palamedes.EVENTS_PATH, {"type": "evt2"})
            palamedes.append_jsonl(palamedes.EVENTS_PATH, {"type": "evt3"})
            report = palamedes.storage_health_report()

        self.assertEqual(report["status"], "ok")
        self.assertEqual(report["logs"]["events"]["retention_limit"], 2)
        self.assertEqual(report["logs"]["events"]["line_count"], 2)
        self.assertEqual(report["logs"]["revisions"]["retention_limit"], 2)
        self.assertEqual(report["logs"]["revisions"]["line_count"], 2)
        self.assertEqual(report["retention"]["logs"]["events"]["line_count"], 2)

    def test_cmd_health_prints_storage_diagnostics(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                palamedes.cmd_health(type("Args", (), {"json": False})())
            output = stdout.getvalue()

        self.assertIn("Status:", output)
        self.assertIn("Revision Count:", output)
        self.assertIn("Writable:", output)
        self.assertIn("Latest Recoverable Revision:", output)
        self.assertIn("Events Retention:", output)

    def test_runtime_schema_matches_checked_in_schema(self):
        report = palamedes.schema_drift_report()

        self.assertTrue(report["matches"])
        self.assertEqual(report["runtime_required_count"], report["file_required_count"])
        self.assertEqual(report["runtime_property_count"], report["file_property_count"])

    def test_plan_shape_accepts_structured_evidence_provenance_extensions(self):
        plan = palamedes.default_plan()
        plan["evidence"] = [
            {
                "claim": "Activation improved after guided onboarding.",
                "source": "experiment:guided-onboarding",
                "confidence": 82,
                "axis": "market",
                "date": "2026-04-24",
                "evidence_type": "experiment_result",
                "reference": "guided-onboarding-notes",
                "reference_id": "ref-guided-onboarding",
                "field": "activation_rate",
                "observed_value": "0.42",
                "expected_value": "0.30",
                "selector": "metrics.activation_rate",
                "source_url": "https://example.com/reports/guided-onboarding",
                "artifact": "notebook://activation/2026-04-24",
                "quote": "Participants completed setup more often with guided steps.",
                "note": "Preliminary uplift only.",
                "review_recommendation": "confirm_experiment_validity",
                "review_reason": "Treatment sample is still small.",
                "provenance": {
                    "method": "notebook_export",
                    "captured_at": "2026-04-24T09:30:00+00:00",
                    "collected_by": "growth-analyst",
                    "artifact": "notebook://activation/2026-04-24",
                    "locator": "cell://summary/4",
                },
                "escalation": {
                    "status": "open",
                    "reason": "Need manual review before adopting onboarding as the default path.",
                    "requested_at": "2026-04-24T10:00:00+00:00",
                    "requested_by": "palamedes-reviewer",
                },
            }
        ]

        validation = palamedes.validate_plan_shape(plan)

        self.assertEqual(validation, {"valid": True, "errors": []})

    def test_plan_shape_accepts_reference_discovery_and_human_escalation_extensions(self):
        plan = palamedes.default_plan()
        plan["human_escalations"] = [
            {
                "id": "esc-001",
                "status": "open",
                "reason": "Choose whether the shortlisted agent runtimes fit Palamedes's repo boundary.",
                "scope": "plan",
                "requested_at": "2026-04-24T11:00:00+00:00",
                "requested_by": "palamedes",
                "related_references": ["paperclip", "airflow"],
            }
        ]
        plan["reference_discoveries"] = [
            {
                "ts": "2026-04-24T11:05:00+00:00",
                "question": "Which external agent patterns should Palamedes borrow?",
                "context": "Compare runtime orchestration and tool contracts.",
                "search_mode": "comparative_repo_review",
                "trigger_signals": ["Need clearer escalation boundaries."],
                "selection_criteria": ["Prefer server-authoritative tool contracts.", "Avoid embedding runtime orchestration in Palamedes core."],
                "candidate_queries": ["airflow agent tools", "paperclip agent runtime", "palamedes escalation contract"],
                "shortlisted_references": ["airflow", "paperclip"],
                "rejected_references": ["generic chat agents"],
                "decision": "Adopt contract patterns, not runtime orchestration.",
                "notes": "Runtime/session management should live outside the core repo.",
                "decision_ref": "rev-2026-04-24-01",
                "decision_status": "needs_review",
                "source_urls": [
                    "https://example.com/repos/airflow",
                    "https://example.com/repos/paperclip",
                ],
                "follow_up_question": "What is the minimal escalation contract Palamedes should persist?",
                "selected_reference_records": [
                    {
                        "reference": "airflow",
                        "why_selected": "It exposes tool discovery and human review as explicit server contracts.",
                        "pattern": "authoritative_tool_catalog",
                        "evidence_links": ["ev-001"],
                    }
                ],
                "provenance": {
                    "provider": "local_repo_scan",
                    "captured_at": "2026-04-24T11:04:00+00:00",
                    "collector": "codex",
                },
                "review_recommendation": "owner_decision_required",
                "review_reason": "Shortlist adoption affects repo boundary decisions.",
                "escalation": {
                    "status": "open",
                    "reason": "Final shortlist adoption needs owner approval.",
                    "requested_at": "2026-04-24T11:06:00+00:00",
                },
            }
        ]

        validation = palamedes.validate_plan_shape(plan)

        self.assertEqual(validation, {"valid": True, "errors": []})

    def test_schema_keeps_extension_points_open_for_evidence_reference_and_plan_level_escalations(self):
        schema = palamedes.load_plan_schema()
        evidence_schema = schema["properties"]["evidence"]["items"]["oneOf"][1]
        reference_schema = schema["properties"]["reference_discoveries"]["items"]

        self.assertTrue(schema["additionalProperties"])
        self.assertTrue(evidence_schema["additionalProperties"])
        self.assertTrue(reference_schema["additionalProperties"])
        self.assertNotIn("human_escalations", schema["required"])

    def test_cmd_schema_check_prints_contract_status(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            palamedes.cmd_schema(type("Args", (), {"check": True, "write": False, "json": False})())
        output = stdout.getvalue()

        self.assertIn("Schema Match: yes", output)

    def test_cmd_conformance_returns_machine_readable_report(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                palamedes.cmd_conformance(type("Args", (), {"base_url": "", "in_process": True})())
            payload = json.loads(stdout.getvalue())

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["passed"], payload["case_count"])
        self.assertEqual(payload["failed"], 0)

    def test_cmd_run_dry_run_returns_restore_preview_envelope(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            palamedes_agent.cmd_run(
                type(
                    "Args",
                    (),
                    {
                        "input": "/palamedes.restore-preview revision_id=rev-789",
                        "dry_run": True,
                    },
                )()
            )
        payload = json.loads(stdout.getvalue())

        self.assertEqual(payload["tool"], "preview_restore")
        self.assertEqual(payload["input"], {"revision_id": "rev-789"})

    def test_cmd_discover_apply_persists_reference_discovery(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                palamedes.cmd_discover(
                    type(
                        "Args",
                        (),
                        {
                            "question": "design agent examples",
                            "context": "Need GitHub references for product UX hierarchy",
                            "references": "repo-a,repo-b",
                            "rejected": "repo-c",
                            "json": False,
                            "apply": True,
                        },
                    )()
                )
            plan = palamedes.load_plan()
            output = stdout.getvalue()

        self.assertIn("Reference discovery applied to current plan.", output)
        self.assertEqual(len(plan["reference_discoveries"]), 1)
        self.assertEqual(plan["reference_discoveries"][0]["search_mode"], "github-pattern-scan")
        self.assertIn("repo-a", plan["references"])
        self.assertTrue(any(item.get("source") == "reference-discovery" for item in palamedes.evidence_objects(plan)))

    def test_tool_schema_contract_report_matches_runtime_expectations(self):
        report = palamedes_agent.tool_schema_contract_report()

        self.assertTrue(report["matches"])
        self.assertEqual(report["missing"], [])
        self.assertEqual(report["unexpected"], [])
        self.assertEqual(report["missing_validators"], [])
        self.assertEqual(report["additional_properties_true"], [])
        self.assertEqual(report["mutation_tools_missing_expected_fingerprint"], [])

    def test_get_plan_returns_normalized_result_fields(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            result = palamedes_agent.execute_tool("get_plan", {})

        self.assertTrue(result["ok"])
        self.assertEqual(result["tool_name"], "get_plan")
        self.assertEqual(result["result_type"], "plan")

    def test_preview_restore_returns_normalized_result_fields(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            first = palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "normalized preview first",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                },
            )
            palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "normalized preview second",
                    "expected_fingerprint": first["fingerprint"],
                },
            )
            result = palamedes_agent.execute_tool("preview_restore", {"previous": True})

        self.assertTrue(result["ok"])
        self.assertEqual(result["tool_name"], "preview_restore")
        self.assertEqual(result["result_type"], "restore_preview")

    def test_run_reference_discovery_tool_can_apply_and_return_plan_state(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            result = palamedes_agent.execute_tool(
                "run_reference_discovery",
                {
                    "question": "design agent examples",
                    "context": "Need GitHub references for product UX hierarchy",
                    "references": ["repo-a"],
                    "apply": True,
                },
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["tool_name"], "run_reference_discovery")
        self.assertEqual(result["result_type"], "reference_discovery")

    def test_capture_evidence_cycle_tool_returns_typed_multi_step_result(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            palamedes_agent.execute_tool(
                "update_plan",
                {
                    "goal": "agent cycle baseline",
                    "success_metric": "Reach 3 pilots",
                    "deadline": "2026-04-10",
                },
            )
            result = palamedes_agent.execute_tool(
                "capture_evidence_cycle",
                {
                    "evidence": {
                        "claim": "Pilot users repeat the same activation blocker",
                        "source": "pilot-call",
                        "confidence": 76,
                    },
                    "replan": {
                        "plan_task": "Refine onboarding diagnosis",
                    },
                    "idempotency_key": "agent-cycle-1",
                    "history_limit": 2,
                },
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["tool_name"], "capture_evidence_cycle")
        self.assertEqual(result["result_type"], "planning_cycle")
        self.assertEqual(result["operation"], "capture_evidence_cycle")
        self.assertEqual(result["idempotency_key"], "agent-cycle-1")
        self.assertIn("evidence_result", result)
        self.assertIn("replan_result", result)
        self.assertIn("post_cycle", result)
        self.assertEqual(result["post_cycle"]["history_limit"], 2)
        self.assertEqual(result["step_results"]["add_evidence"]["tool_name"], "add_evidence")
        self.assertEqual(result["step_results"]["replan"]["tool_name"], "replan")

    def test_capture_evidence_cycle_tool_reuses_substep_idempotency_keys(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            payload = {
                "evidence": {
                    "claim": "Same evidence cycle",
                    "source": "pilot-call",
                    "confidence": 70,
                },
                "replan": {
                    "plan_task": "Keep cycle stable",
                },
                "idempotency_key": "agent-cycle-replay",
            }
            first = palamedes_agent.execute_tool("capture_evidence_cycle", payload)
            second = palamedes_agent.execute_tool("capture_evidence_cycle", payload)

        self.assertFalse(first["evidence_result"]["idempotency_replayed"])
        self.assertFalse(first["replan_result"]["idempotency_replayed"])
        self.assertTrue(second["evidence_result"]["idempotency_replayed"])
        self.assertTrue(second["replan_result"]["idempotency_replayed"])
        self.assertEqual(first["post_fingerprint"], second["post_fingerprint"])


if __name__ == "__main__":
    unittest.main()
