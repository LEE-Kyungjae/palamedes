#!/usr/bin/env python3
import io
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

import palamedes
from palamedes_host_contract import host_action_contract, required_capabilities_for_action, role_has_action_capabilities
from palamedes_sdk import PalamedesClient as PackagedPalamedesClient
from palamedes_client import PalamedesClient, PalamedesClientError, PalamedesClientOperationError, PalamedesConflictError, PalamedesHealthGateError
from palamedes_server import PalamedesHandler


EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"
if str(EXAMPLES_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLES_DIR))
_PLANNER_HOST_SPEC = importlib.util.spec_from_file_location("palamedes_planner_host_example", EXAMPLES_DIR / "palamedes_planner_host.py")
assert _PLANNER_HOST_SPEC and _PLANNER_HOST_SPEC.loader
_PLANNER_HOST_MODULE = importlib.util.module_from_spec(_PLANNER_HOST_SPEC)
_PLANNER_HOST_SPEC.loader.exec_module(_PLANNER_HOST_MODULE)
PlannerHostStep = _PLANNER_HOST_MODULE.PlannerHostStep


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


def build_handler(method: str, path: str, body: bytes = b"", headers=None) -> PalamedesHandler:
    handler = PalamedesHandler.__new__(PalamedesHandler)
    handler.command = method
    handler.path = path
    handler.headers = {"Content-Length": str(len(body)), **(headers or {})}
    handler.rfile = io.BytesIO(body)
    handler.wfile = io.BytesIO()
    handler._status = None
    handler._sent_headers = {}
    handler.send_response = lambda status, message=None: setattr(handler, "_status", status)
    handler.send_header = lambda key, value: handler._sent_headers.__setitem__(key, value)
    handler.end_headers = lambda: None
    return handler


def handler_transport(method: str, path: str, body=None, headers=None):
    raw_body = json.dumps(body).encode("utf-8") if body is not None else b""
    handler = build_handler(method, path, body=raw_body, headers=headers)
    if method == "GET":
        handler.do_GET()
    else:
        handler.do_POST()
    payload = json.loads(handler.wfile.getvalue().decode("utf-8"))
    return handler._status, payload, handler._sent_headers


class PalamedesClientTests(unittest.TestCase):
    def test_palamedes_sdk_package_exports_client_surface(self):
        self.assertIs(PackagedPalamedesClient, PalamedesClient)

    def test_get_plan_tracks_fingerprint(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            result = client.get_plan()

        self.assertTrue(result["ok"])
        self.assertEqual(client.tracked_fingerprint, result["fingerprint"])

    def test_get_cycle_returns_integrated_snapshot_and_tracks_fingerprint(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            seed = palamedes.mutate_plan_state(
                lambda plan: plan.update(
                    {
                        "goal": "client cycle",
                        "success_metric": "Reach 2 pilots",
                        "deadline": "2026-04-03",
                    }
                ),
                revision_source="test_client_cycle",
            )
            client = PalamedesClient(transport=handler_transport)
            result = client.get_cycle(history_limit=1)

        self.assertEqual(result["result_type"], "cycle")
        self.assertEqual(result["plan"]["goal"], "client cycle")
        self.assertIn("score", result["qa"])
        self.assertIn("status", result["health"])
        self.assertEqual(result["history_limit"], 1)
        self.assertEqual(len(result["history"]), 1)
        self.assertEqual(client.tracked_fingerprint, palamedes.plan_fingerprint(seed))

    def test_get_host_action_contract_returns_shared_contract(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            result = client.get_host_action_contract(role="researcher")

        self.assertEqual(result["role"], "researcher")
        self.assertEqual(result["profile"], "researcher_capture")
        self.assertEqual(result["allowed_actions"], host_action_contract("researcher")["allowed_actions"])
        self.assertEqual(result["capabilities"], host_action_contract("researcher")["capabilities"])
        self.assertEqual(result["actions"], host_action_contract("researcher")["actions"])
        self.assertIn("contract_path", result)
        action_map = {item["action"]: item for item in result["actions"]}
        self.assertEqual(action_map["capture_evidence_cycle"]["required_capabilities"], ["evidence.append_and_replan"])

    def test_host_contract_capability_helpers_reflect_role_permissions(self):
        self.assertEqual(required_capabilities_for_action("planner", "update_plan"), ["plan.write"])
        self.assertEqual(required_capabilities_for_action("planner", "request_review"), ["review.request"])
        self.assertTrue(role_has_action_capabilities("planner", "update_plan"))
        self.assertFalse(role_has_action_capabilities("reviewer", "update_plan"))
        self.assertTrue(role_has_action_capabilities("reviewer", "preview_restore_previous"))
        self.assertTrue(role_has_action_capabilities("reviewer", "resolve_review"))

    def test_get_contracts_returns_catalog(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            result = client.get_contracts()

        self.assertTrue(result["ok"])
        self.assertEqual(result["result_type"], "contracts")
        self.assertEqual(result["contract_version"], palamedes.CONTRACT_VERSION)
        self.assertIn("stability_levels", result)
        self.assertIn("summary", result)
        self.assertGreaterEqual(result["summary"]["experimental_contract_count"], 1)
        self.assertIn("http_api", result["contracts"])
        self.assertIn("profile_summary", result["contracts"]["host_action_contract"])
        self.assertIn("conformance_manifest", result["contracts"])

    def test_get_tools_and_get_tool_return_authoritative_catalog_views(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            catalog = client.get_tools()
            detail = client.get_tool("request_review")

        self.assertTrue(catalog["ok"])
        self.assertEqual(catalog["result_type"], "tool_catalog")
        self.assertEqual(catalog["catalog"]["execute_endpoint"], "/tools/execute")
        self.assertTrue(any(item["name"] == "request_review" for item in catalog["tools"]))
        self.assertTrue(detail["ok"])
        self.assertEqual(detail["tool"]["name"], "request_review")
        self.assertEqual(detail["tool"]["kind"], "mutation")

    def test_list_reviews_returns_filtered_review_records(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            seed = client.update_plan(
                {
                    "goal": "client review listing",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-05-01",
                }
            )
            requested = client.request_review(
                {
                    "scope": "plan",
                    "reason": "Need owner confirmation.",
                    "requested_by": "client-test",
                    "priority": "high",
                    "assigned_to": "owner",
                    "stale_after": "2026-05-01T09:00:00Z",
                    "sla_bucket": "24h",
                },
                expected_fingerprint=seed["fingerprint"],
            )
            client.resolve_review(
                {
                    "request_id": requested["review_request"]["id"],
                    "status": "resolved",
                    "resolution": "Confirmed.",
                    "resolved_by": "owner",
                    "assigned_to": "reviewer",
                },
                expected_fingerprint=requested["fingerprint"],
            )
            result = client.list_reviews(status="resolved", assigned_to="reviewer")
            direct = client.get_reviews(status="resolved", assigned_to="reviewer")

        self.assertEqual(result["count"], 1)
        self.assertEqual(result["reviews"][0]["status"], "resolved")
        self.assertEqual(result["reviews"][0]["assigned_to"], "reviewer")
        self.assertEqual(direct["count"], 1)
        self.assertEqual(direct["reviews"][0]["priority"], "high")
        self.assertEqual(direct["reviews"][0]["stale_after"], "2026-05-01T09:00:00Z")
        self.assertEqual(direct["reviews"][0]["sla_bucket"], "24h")

    def test_list_reviews_and_get_reviews_support_sorting(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            seed = client.update_plan(
                {
                    "goal": "client review sorting",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-05-01",
                }
            )
            first = client.request_review(
                {
                    "scope": "plan",
                    "reason": "Low priority queue item.",
                    "requested_by": "client-test",
                    "priority": "low",
                    "request_id": "review-low",
                },
                expected_fingerprint=seed["fingerprint"],
            )
            client.request_review(
                {
                    "scope": "plan",
                    "reason": "High priority queue item.",
                    "requested_by": "client-test",
                    "priority": "high",
                    "request_id": "review-high",
                },
                expected_fingerprint=first["fingerprint"],
            )
            sorted_tool = client.list_reviews(sort_by="priority", order="desc")
            sorted_http = client.get_reviews(sort_by="priority", order="desc")

        self.assertEqual([item["id"] for item in sorted_tool["reviews"][:2]], ["review-high", "review-low"])
        self.assertEqual([item["id"] for item in sorted_http["reviews"][:2]], ["review-high", "review-low"])

    def test_list_reviews_and_get_reviews_support_stale_after_sorting(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            seed = client.update_plan(
                {
                    "goal": "client review stale sorting",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-05-01",
                }
            )
            first = client.request_review(
                {
                    "scope": "plan",
                    "reason": "Later deadline queue item.",
                    "requested_by": "client-test",
                    "request_id": "review-late",
                    "stale_after": "2026-05-03T09:00:00Z",
                },
                expected_fingerprint=seed["fingerprint"],
            )
            second = client.request_review(
                {
                    "scope": "plan",
                    "reason": "Soon deadline queue item.",
                    "requested_by": "client-test",
                    "request_id": "review-soon",
                    "stale_after": "2026-04-26T09:00:00Z",
                },
                expected_fingerprint=first["fingerprint"],
            )
            client.request_review(
                {
                    "scope": "plan",
                    "reason": "No deadline queue item.",
                    "requested_by": "client-test",
                    "request_id": "review-none",
                },
                expected_fingerprint=second["fingerprint"],
            )
            sorted_tool = client.list_reviews(sort_by="stale_after", order="asc")
            sorted_http = client.get_reviews(sort_by="stale_after", order="asc")

        self.assertEqual([item["id"] for item in sorted_tool["reviews"][:3]], ["review-soon", "review-late", "review-none"])
        self.assertEqual([item["id"] for item in sorted_http["reviews"][:3]], ["review-soon", "review-late", "review-none"])

    def test_get_review_and_update_review_use_direct_review_resource_paths(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            seed = client.update_plan(
                {
                    "goal": "client review detail",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-05-01",
                }
            )
            requested = client.request_review(
                {
                    "scope": "plan",
                    "reason": "Need triage assignment.",
                    "requested_by": "client-test",
                },
                expected_fingerprint=seed["fingerprint"],
            )
            request_id = requested["review_request"]["id"]
            detail = client.get_review(request_id)
            updated = client.update_review(
                request_id,
                {"priority": "high", "assigned_to": "reviewer", "stale_after": "2026-05-02T09:00:00Z", "sla_bucket": "24h"},
                expected_fingerprint=requested["fingerprint"],
            )

        self.assertEqual(detail["tool_name"], "get_review")
        self.assertEqual(detail["review"]["id"], request_id)
        self.assertEqual(updated["tool_name"], "update_review")
        self.assertEqual(updated["review_request"]["priority"], "high")
        self.assertEqual(updated["review_request"]["assigned_to"], "reviewer")
        self.assertEqual(updated["review_request"]["stale_after"], "2026-05-02T09:00:00Z")
        self.assertEqual(updated["review_request"]["sla_bucket"], "24h")
        self.assertEqual(client.tracked_fingerprint, updated["fingerprint"])

    def test_get_reviewer_inbox_uses_direct_inbox_endpoint_with_queue_defaults(self):
        calls = []

        def transport(method: str, path: str, body=None, headers=None):
            calls.append((method, path, body, headers))
            return 200, {"ok": True, "reviews": [{"id": "review-1"}], "count": 1}, {}

        client = PalamedesClient(transport=transport)
        result = client.get_reviewer_inbox("reviewer@example.com")

        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 1)
        self.assertEqual(
            calls,
            [("GET", "/reviews/inbox?assignee=reviewer%40example.com&limit=20", None, None)],
        )

    def test_get_review_inbox_alias_supports_custom_limit(self):
        calls = []

        def transport(method: str, path: str, body=None, headers=None):
            calls.append((method, path, body, headers))
            return 200, {"ok": True, "reviews": [], "count": 0}, {}

        client = PalamedesClient(transport=transport)
        result = client.get_review_inbox("owner", limit=7)

        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 0)
        self.assertEqual(calls, [("GET", "/reviews/inbox?assignee=owner&limit=7", None, None)])

    def test_get_doctor_returns_readiness_report(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            result = client.get_doctor()

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["contract_version"], palamedes.CONTRACT_VERSION)
        self.assertIn("checks", result)
        self.assertIn("check_summary", result)
        self.assertEqual(result["check_summary"]["fail"], 0)
        self.assertGreaterEqual(result["check_summary"]["warn"], 1)
        self.assertIn("schema_drift", result)
        self.assertIn("tool_schema", result)
        self.assertIn("host_action_contract", result)

    def test_update_plan_uses_tracked_fingerprint(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            client.get_plan()
            result = client.update_plan(
                {
                    "goal": "client update",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                }
            )

        self.assertEqual(result["plan"]["goal"], "client update")
        self.assertEqual(client.tracked_fingerprint, result["fingerprint"])

    def test_restore_previous_works_through_client(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            first = client.update_plan(
                {
                    "goal": "client previous first",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                }
            )
            second = client.update_plan({"goal": "client previous second"})
            preview = client.preview_restore(previous=True)
            restored = client.restore_revision(previous=True, expected_fingerprint=second["fingerprint"])

        self.assertEqual(preview["selected_via"], "previous")
        self.assertEqual(preview["metadata"]["goal"], "client previous first")
        self.assertEqual(restored["plan"]["goal"], "client previous first")
        self.assertNotEqual(first["fingerprint"], second["fingerprint"])

    def test_request_review_uses_generic_tool_execute_surface(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            seed = client.update_plan(
                {
                    "goal": "client review request",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-05-01",
                }
            )
            result = client.request_review(
                {
                    "scope": "plan",
                    "reason": "Need owner confirmation before committing to the next branch.",
                    "requested_by": "client-test",
                    "related_references": ["airflow", "paperclip"],
                },
                expected_fingerprint=seed["fingerprint"],
                idempotency_key="client-review-1",
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["tool_name"], "request_review")
        self.assertEqual(result["review_request"]["scope"], "plan")
        self.assertEqual(result["plan"]["human_escalations"][0]["requested_by"], "client-test")
        self.assertEqual(client.tracked_fingerprint, result["fingerprint"])

    def test_resolve_review_uses_generic_tool_execute_surface(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            seed = client.update_plan(
                {
                    "goal": "client review resolution",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-05-01",
                }
            )
            requested = client.request_review(
                {
                    "scope": "plan",
                    "reason": "Need owner confirmation before committing to the next branch.",
                    "requested_by": "client-test",
                },
                expected_fingerprint=seed["fingerprint"],
                idempotency_key="client-review-open-1",
            )
            result = client.resolve_review(
                {
                    "request_id": requested["review_request"]["id"],
                    "status": "resolved",
                    "resolution": "Owner approved continuing the branch.",
                    "resolved_by": "owner",
                },
                expected_fingerprint=requested["fingerprint"],
                idempotency_key="client-review-resolve-1",
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["tool_name"], "resolve_review")
        self.assertEqual(result["review_request"]["status"], "resolved")
        self.assertEqual(result["review_request"]["resolved_by"], "owner")
        self.assertEqual(client.tracked_fingerprint, result["fingerprint"])

    def test_capture_evidence_cycle_returns_typed_multi_step_result(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            client.update_plan(
                {
                    "goal": "client evidence cycle",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                }
            )
            result = client.capture_evidence_cycle(
                {
                    "claim": "Repeated pilot friction",
                    "source": "pilot-call",
                    "confidence": 74,
                    "axis": "market",
                },
                replan_payload={"plan_task": "Tighten onboarding loop"},
                history_limit=2,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["operation"], "capture_evidence_cycle")
        self.assertEqual(result["result_type"], "planning_cycle")
        self.assertNotEqual(result["pre_fingerprint"], result["post_fingerprint"])
        self.assertIn("evidence", result["changed_fields"])
        self.assertIn("plan_tasks", result["changed_fields"])
        self.assertEqual(result["evidence_result"]["plan"]["evidence"][-1]["claim"], "Repeated pilot friction")
        self.assertEqual(result["replan_result"]["plan"]["plan_tasks"][-1], "Tighten onboarding loop")
        self.assertEqual(result["post_cycle"]["plan"]["evidence"][-1]["source"], "pilot-call")
        self.assertEqual(result["post_cycle"]["history_limit"], 2)
        self.assertEqual(client.tracked_fingerprint, result["post_fingerprint"])
        self.assertIn("add_evidence", result["step_results"])
        self.assertIn("replan", result["step_results"])

    def test_capture_evidence_cycle_reuses_idempotency_key_without_duplicate_steps(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            client.update_plan(
                {
                    "goal": "idempotent capture evidence cycle",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                }
            )
            first = client.capture_evidence_cycle(
                {
                    "claim": "Repeated onboarding dropoff",
                    "source": "pilot-call",
                    "confidence": 76,
                    "axis": "market",
                },
                replan_payload={"plan_task": "Tighten onboarding loop"},
                history_limit=2,
                idempotency_key="capture-1",
            )
            second = client.capture_evidence_cycle(
                {
                    "claim": "Repeated onboarding dropoff",
                    "source": "pilot-call",
                    "confidence": 76,
                    "axis": "market",
                },
                replan_payload={"plan_task": "Tighten onboarding loop"},
                history_limit=2,
                idempotency_key="capture-1",
            )

        self.assertEqual(first["idempotency_key"], "capture-1")
        self.assertEqual(second["idempotency_key"], "capture-1")
        self.assertFalse(first["evidence_result"]["idempotency_replayed"])
        self.assertFalse(first["replan_result"]["idempotency_replayed"])
        self.assertTrue(second["evidence_result"]["idempotency_replayed"])
        self.assertTrue(second["replan_result"]["idempotency_replayed"])
        self.assertEqual(first["post_fingerprint"], second["post_fingerprint"])
        evidence_claims = [item["claim"] for item in second["post_cycle"]["plan"]["evidence"] if item.get("claim") == "Repeated onboarding dropoff"]
        self.assertEqual(len(evidence_claims), 1)
        self.assertEqual(second["post_cycle"]["plan"]["plan_tasks"].count("Tighten onboarding loop"), 1)

    def test_apply_and_get_cycle_wraps_update_plan_with_post_cycle_snapshot(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            result = client.apply_and_get_cycle(
                "update_plan",
                {
                    "goal": "wrapped update",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                },
                history_limit=1,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["operation"], "update_plan")
        self.assertEqual(result["mutation_result"]["plan"]["goal"], "wrapped update")
        self.assertEqual(result["post_cycle"]["plan"]["goal"], "wrapped update")
        self.assertEqual(result["post_cycle"]["history_limit"], 1)
        self.assertEqual(client.tracked_fingerprint, result["post_fingerprint"])

    def test_apply_and_get_cycle_wraps_restore_revision_with_post_cycle_snapshot(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            first = client.update_plan(
                {
                    "goal": "wrapped restore first",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                }
            )
            second = client.update_plan({"goal": "wrapped restore second"})
            result = client.apply_and_get_cycle(
                "restore_revision",
                {"previous": True},
                expected_fingerprint=second["fingerprint"],
                history_limit=1,
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["operation"], "restore_revision")
        self.assertEqual(result["mutation_result"]["plan"]["goal"], "wrapped restore first")
        self.assertEqual(result["post_cycle"]["plan"]["goal"], "wrapped restore first")
        self.assertEqual(result["post_cycle"]["history_limit"], 1)
        self.assertEqual(client.tracked_fingerprint, result["post_fingerprint"])
        self.assertNotEqual(first["fingerprint"], second["fingerprint"])

    def test_apply_and_get_cycle_surfaces_typed_operation_error(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            with self.assertRaises(PalamedesClientOperationError) as ctx:
                client.apply_and_get_cycle("add_evidence", {"claim": " "})

        self.assertEqual(ctx.exception.operation, "add_evidence")
        self.assertEqual(ctx.exception.step, "mutation")
        self.assertEqual(ctx.exception.status, 400)
        self.assertEqual(ctx.exception.payload["error"], "claim is required")
        self.assertEqual(ctx.exception.payload["error_code"], "invalid_request")
        self.assertFalse(ctx.exception.cause.retryable)

    def test_stale_fingerprint_raises_typed_conflict_error(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            first = client.get_plan()
            client.update_plan(
                {
                    "goal": "fresh write",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                }
            )
            with self.assertRaises(PalamedesConflictError) as ctx:
                client.update_plan({"goal": "stale write"}, expected_fingerprint=first["fingerprint"])

        self.assertEqual(ctx.exception.status, 412)
        self.assertEqual(ctx.exception.payload["error"], "plan fingerprint mismatch")
        self.assertEqual(ctx.exception.error_code, "plan_fingerprint_mismatch")
        self.assertEqual(ctx.exception.expected_fingerprint, first["fingerprint"])
        self.assertTrue(ctx.exception.current_fingerprint)
        self.assertTrue(ctx.exception.can_refresh)

    def test_apply_and_get_cycle_surfaces_typed_conflict_error_with_operation_context(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            initial = client.get_plan()
            client.update_plan(
                {
                    "goal": "conflict baseline",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                }
            )
            with self.assertRaises(PalamedesConflictError) as ctx:
                client.apply_and_get_cycle(
                    "update_plan",
                    {"goal": "stale wrapped update"},
                    expected_fingerprint=initial["fingerprint"],
                )

        self.assertEqual(ctx.exception.operation, "update_plan")
        self.assertEqual(ctx.exception.step, "mutation")
        self.assertEqual(ctx.exception.status, 412)
        self.assertEqual(ctx.exception.error_code, "plan_fingerprint_mismatch")
        self.assertEqual(ctx.exception.expected_fingerprint, initial["fingerprint"])
        self.assertTrue(ctx.exception.current_fingerprint)

    def test_apply_and_get_cycle_with_retry_recovers_from_stale_fingerprint_once(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            initial = client.get_plan()
            client.update_plan(
                {
                    "goal": "retry baseline",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                }
            )
            result = client.apply_and_get_cycle_with_retry(
                "update_plan",
                {"goal": "retry recovered"},
                expected_fingerprint=initial["fingerprint"],
                history_limit=1,
            )

        self.assertTrue(result["ok"])
        self.assertTrue(result["retried"])
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(result["operation"], "update_plan")
        self.assertEqual(result["post_cycle"]["plan"]["goal"], "retry recovered")
        self.assertEqual(result["retry_from_fingerprint"], initial["fingerprint"])
        self.assertTrue(result["retry_to_fingerprint"])
        self.assertEqual(client.tracked_fingerprint, result["post_fingerprint"])

    def test_apply_and_get_cycle_with_retry_recovers_restore_revision_once(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            initial = client.get_plan()
            client.update_plan(
                {
                    "goal": "retry restore first",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                }
            )
            latest = client.update_plan({"goal": "retry restore second"})
            result = client.apply_and_get_cycle_with_retry(
                "restore_revision",
                {"previous": True},
                expected_fingerprint=initial["fingerprint"],
                history_limit=1,
            )

        self.assertTrue(result["ok"])
        self.assertTrue(result["retried"])
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(result["operation"], "restore_revision")
        self.assertEqual(result["post_cycle"]["plan"]["goal"], "retry restore first")
        self.assertEqual(result["retry_from_fingerprint"], initial["fingerprint"])
        self.assertTrue(result["retry_to_fingerprint"])
        self.assertNotEqual(latest["fingerprint"], result["post_fingerprint"])

    def test_apply_and_get_cycle_with_retry_does_not_retry_validation_error(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            with self.assertRaises(PalamedesClientOperationError) as ctx:
                client.apply_and_get_cycle_with_retry("add_evidence", {"claim": " "})

        self.assertEqual(ctx.exception.operation, "add_evidence")
        self.assertEqual(ctx.exception.step, "mutation")
        self.assertEqual(ctx.exception.status, 400)

    def test_apply_and_get_cycle_with_retry_does_not_retry_add_evidence_by_default(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            initial = client.get_plan()
            client.update_plan(
                {
                    "goal": "retry add evidence baseline",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                }
            )
            with self.assertRaises(PalamedesConflictError) as ctx:
                client.apply_and_get_cycle_with_retry(
                    "add_evidence",
                    {"claim": "Pilot friction repeated", "source": "pilot-call", "confidence": 74},
                    expected_fingerprint=initial["fingerprint"],
                )

        self.assertEqual(ctx.exception.operation, "add_evidence")
        self.assertEqual(ctx.exception.step, "mutation")
        self.assertEqual(ctx.exception.expected_fingerprint, initial["fingerprint"])

    def test_apply_and_get_cycle_with_retry_can_opt_in_for_add_evidence(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            initial = client.get_plan()
            client.update_plan(
                {
                    "goal": "retry add evidence opt-in",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                }
            )
            result = client.apply_and_get_cycle_with_retry(
                "add_evidence",
                {"claim": "Opt-in retry evidence", "source": "pilot-call", "confidence": 74},
                expected_fingerprint=initial["fingerprint"],
                allow_non_idempotent_retry=True,
            )

        self.assertTrue(result["ok"])
        self.assertTrue(result["retried"])
        self.assertEqual(result["operation"], "add_evidence")
        self.assertEqual(result["post_cycle"]["plan"]["evidence"][-1]["claim"], "Opt-in retry evidence")
        self.assertTrue(result["mutation_result"]["idempotency_key"].startswith("add_evidence_"))

    def test_add_evidence_idempotency_key_replays_without_duplicate_write(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            first = client.add_evidence(
                {"claim": "Idempotent evidence", "source": "pilot-call", "confidence": 71},
                idempotency_key="client-evidence-1",
            )
            second = client.add_evidence(
                {"claim": "Idempotent evidence", "source": "pilot-call", "confidence": 71},
                idempotency_key="client-evidence-1",
            )

        self.assertFalse(first["idempotency_replayed"])
        self.assertTrue(second["idempotency_replayed"])
        self.assertEqual(len(second["plan"]["evidence"]), 1)
        self.assertEqual(first["fingerprint"], second["fingerprint"])

    def test_apply_and_get_cycle_with_retry_injects_idempotency_key_for_add_evidence_opt_in(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client = PalamedesClient(transport=handler_transport)
            initial = client.update_plan(
                {
                    "goal": "auto key evidence retry",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                }
            )
            palamedes.mutate_plan_state(
                lambda plan: plan.update({"review_cadence": "weekly"}),
                expected_fingerprint=initial["fingerprint"],
                revision_source="test_auto_key_conflict",
            )
            result = client.apply_and_get_cycle_with_retry(
                "add_evidence",
                {"claim": "Auto-key evidence", "source": "pilot-call", "confidence": 70},
                expected_fingerprint=initial["fingerprint"],
                allow_non_idempotent_retry=True,
            )

        self.assertTrue(result["retried"])
        self.assertTrue(result["mutation_result"]["idempotency_key"].startswith("add_evidence_"))
        matching_claims = [item for item in result["post_cycle"]["plan"]["evidence"] if item.get("claim") == "Auto-key evidence"]
        self.assertEqual(len(matching_claims), 1)

    def test_apply_and_get_cycle_can_block_on_degraded_health(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            palamedes.EVENTS_PATH.write_text('{"type":"ok"}\nnot-json\n', encoding="utf-8")
            client = PalamedesClient(transport=handler_transport)
            with self.assertRaises(PalamedesHealthGateError) as ctx:
                client.apply_and_get_cycle(
                    "update_plan",
                    {
                        "goal": "blocked by health",
                        "success_metric": "Reach 2 pilots",
                        "deadline": "2026-04-03",
                    },
                    require_healthy=True,
                )
            plan = palamedes.load_plan()

        self.assertEqual(ctx.exception.operation, "update_plan")
        self.assertEqual(ctx.exception.step, "preflight")
        self.assertEqual(ctx.exception.status, "degraded")
        self.assertEqual(plan["goal"], "")

    def test_apply_and_get_cycle_allows_write_when_health_gate_disabled(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            palamedes.EVENTS_PATH.write_text('{"type":"ok"}\nnot-json\n', encoding="utf-8")
            client = PalamedesClient(transport=handler_transport)
            result = client.apply_and_get_cycle(
                "update_plan",
                {
                    "goal": "allowed on degraded health",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                },
            )

        self.assertTrue(result["ok"])
        self.assertEqual(result["post_cycle"]["plan"]["goal"], "allowed on degraded health")

    def test_capture_evidence_cycle_with_retry_recovers_multi_agent_conflict(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            writer = PalamedesClient(transport=handler_transport)
            stale_actor = PalamedesClient(transport=handler_transport)
            initial = stale_actor.update_plan(
                {
                    "goal": "multi-agent cycle baseline",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                }
            )
            writer.update_plan({"review_cadence": "weekly"})
            result = stale_actor.capture_evidence_cycle(
                {
                    "claim": "Shared customer blocker",
                    "source": "pilot-call",
                    "confidence": 75,
                },
                replan_payload={"plan_task": "Revisit onboarding path"},
                expected_fingerprint=initial["fingerprint"],
                allow_retry=True,
            )

        self.assertTrue(result["ok"])
        self.assertTrue(result["retried"])
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(result["retry_from_fingerprint"], initial["fingerprint"])
        self.assertTrue(result["retry_to_fingerprint"])
        self.assertEqual(result["post_cycle"]["plan"]["evidence"][-1]["claim"], "Shared customer blocker")
        self.assertEqual(result["post_cycle"]["plan"]["plan_tasks"][-1], "Revisit onboarding path")
        self.assertEqual(stale_actor.tracked_fingerprint, result["post_fingerprint"])

    def test_planner_host_exposes_action_contract(self):
        host = PlannerHostStep(adapter=None)  # type: ignore[arg-type]

        contract = host.action_contract()

        self.assertEqual(contract["version"], "v1")
        self.assertEqual(contract["role"], "planner")
        self.assertEqual(contract["profile"], "planner_full")
        self.assertIn("input_schema", contract)
        self.assertIn("allowed_actions", contract)
        self.assertIn("capabilities", contract)
        action_names = [item["action"] for item in contract["actions"]]
        self.assertIn("update_plan", action_names)
        self.assertIn("capture_evidence_cycle", action_names)
        self.assertIn("request_review", action_names)
        self.assertIn("resolve_review", action_names)
        self.assertIn("restore_previous", action_names)
        self.assertIn("update_plan", contract["allowed_actions"])
        self.assertIn("plan.write", contract["capabilities"])
        self.assertIn("review.request", contract["capabilities"])

    def test_planner_host_update_plan_action_can_retry_stale_conflict(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            client_a = PalamedesClient(transport=handler_transport)
            client_b = PalamedesClient(transport=handler_transport)
            host = PlannerHostStep(adapter=_PLANNER_HOST_MODULE.PalamedesKernelAdapter(client_b))
            initial = client_a.get_plan()
            client_a.update_plan(
                {
                    "goal": "fresh host baseline",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                }
            )
            event = host.run(
                {
                    "action": "update_plan",
                    "payload": {"goal": "host recovered update"},
                    "options": {
                        "expected_fingerprint": initial["fingerprint"],
                        "allow_retry": True,
                        "history_limit": 1,
                    },
                }
            )

        self.assertEqual(event["type"], "plan_update_applied")
        self.assertEqual(event["action"], "update_plan")
        self.assertTrue(event["result"]["retried"])
        self.assertEqual(event["result"]["post_cycle"]["plan"]["goal"], "host recovered update")
        self.assertEqual(event["summary"]["retried"], True)

    def test_planner_host_capture_evidence_cycle_can_retry_stale_conflict(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            writer = PalamedesClient(transport=handler_transport)
            actor = PalamedesClient(transport=handler_transport)
            host = PlannerHostStep(adapter=_PLANNER_HOST_MODULE.PalamedesKernelAdapter(actor))
            initial = actor.update_plan(
                {
                    "goal": "host cycle baseline",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                }
            )
            writer.update_plan({"review_cadence": "weekly"})
            event = host.run(
                {
                    "action": "capture_evidence_cycle",
                    "payload": {
                        "evidence": {
                            "claim": "Planner host recovered evidence",
                            "source": "pilot-call",
                            "confidence": 74,
                        },
                        "replan": {"plan_task": "Retune follow-up flow"},
                    },
                    "options": {
                        "expected_fingerprint": initial["fingerprint"],
                        "allow_retry": True,
                        "history_limit": 1,
                    },
                }
            )

        self.assertEqual(event["type"], "evidence_cycle_applied")
        self.assertEqual(event["action"], "capture_evidence_cycle")
        self.assertTrue(event["result"]["retried"])
        self.assertEqual(event["result"]["post_cycle"]["plan"]["evidence"][-1]["claim"], "Planner host recovered evidence")
        self.assertEqual(event["result"]["post_cycle"]["plan"]["plan_tasks"][-1], "Retune follow-up flow")

    def test_reviewer_host_can_resolve_review(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            planner = PlannerHostStep(adapter=_PLANNER_HOST_MODULE.PalamedesKernelAdapter(PalamedesClient(transport=handler_transport)), role="planner")
            reviewer = PlannerHostStep(adapter=_PLANNER_HOST_MODULE.PalamedesKernelAdapter(PalamedesClient(transport=handler_transport)), role="reviewer")

            plan_event = planner.run_event(
                {
                    "action": "update_plan",
                    "payload": {
                        "goal": "Need reviewer action",
                        "success_metric": "Reach 3 retained pilots",
                        "deadline": "2026-04-30",
                    },
                }
            )
            request_event = planner.run_event(
                {
                    "action": "request_review",
                    "payload": {
                        "scope": "plan",
                        "reason": "Owner or reviewer must close the planning branch decision.",
                        "requested_by": "planner",
                    },
                    "options": {"expected_fingerprint": plan_event["result"]["post_fingerprint"]},
                }
            )
            resolve_event = reviewer.run_event(
                {
                    "action": "resolve_review",
                    "payload": {
                        "request_id": request_event["result"]["mutation_result"]["review_request"]["id"],
                        "status": "resolved",
                        "resolution": "Reviewer closed the branch decision.",
                        "resolved_by": "reviewer",
                    },
                    "options": {"expected_fingerprint": request_event["result"]["post_fingerprint"]},
                }
            )

        self.assertTrue(resolve_event["ok"])
        self.assertEqual(resolve_event["type"], "review_resolved")
        self.assertEqual(resolve_event["result"]["post_cycle"]["plan"]["human_escalations"][0]["status"], "resolved")
        self.assertEqual(resolve_event["result"]["post_cycle"]["plan"]["human_escalations"][0]["resolved_by"], "reviewer")

    def test_planner_host_run_event_returns_invalid_action_taxonomy(self):
        host = PlannerHostStep(adapter=_PLANNER_HOST_MODULE.PalamedesKernelAdapter(PalamedesClient(transport=handler_transport)))

        event = host.run_event({"action": "unknown_action"})

        self.assertFalse(event["ok"])
        self.assertEqual(event["type"], "invalid_action")
        self.assertEqual(event["action"], "unknown_action")
        self.assertEqual(event["error"]["type"], "invalid_action")
        self.assertEqual(event["error"]["error_code"], "invalid_action")
        self.assertFalse(event["error"]["retryable"])

    def test_planner_host_run_event_returns_permission_denied_taxonomy(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            host = PlannerHostStep(
                adapter=_PLANNER_HOST_MODULE.PalamedesKernelAdapter(PalamedesClient(transport=handler_transport)),
                role="researcher",
            )
            event = host.run_event(
                {
                    "action": "restore_previous",
                    "options": {"history_limit": 1},
                }
            )

        self.assertFalse(event["ok"])
        self.assertEqual(event["type"], "permission_denied")
        self.assertEqual(event["action"], "restore_previous")
        self.assertEqual(event["error"]["type"], "permission_denied")
        self.assertEqual(event["error"]["error_code"], "permission_denied")
        self.assertFalse(event["error"]["retryable"])
        self.assertIn("needs plan.restore", event["error"]["message"])

    def test_planner_host_run_event_returns_health_gate_taxonomy(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            palamedes.EVENTS_PATH.write_text('{"type":"ok"}\nnot-json\n', encoding="utf-8")
            host = PlannerHostStep(adapter=_PLANNER_HOST_MODULE.PalamedesKernelAdapter(PalamedesClient(transport=handler_transport)))
            event = host.run_event(
                {
                    "action": "update_plan",
                    "payload": {
                        "goal": "blocked host update",
                        "success_metric": "Reach 2 pilots",
                        "deadline": "2026-04-03",
                    },
                    "options": {"require_healthy": True},
                }
            )

        self.assertFalse(event["ok"])
        self.assertEqual(event["type"], "health_gate")
        self.assertEqual(event["error"]["type"], "health_gate")
        self.assertEqual(event["error"]["error_code"], "health_gate_blocked")
        self.assertFalse(event["error"]["retryable"])
        self.assertEqual(event["error"]["operation"], "update_plan")

    def test_planner_host_run_event_returns_conflict_taxonomy(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            writer = PalamedesClient(transport=handler_transport)
            actor = PalamedesClient(transport=handler_transport)
            host = PlannerHostStep(adapter=_PLANNER_HOST_MODULE.PalamedesKernelAdapter(actor))
            initial = actor.update_plan(
                {
                    "goal": "host conflict baseline",
                    "success_metric": "Reach 2 pilots",
                    "deadline": "2026-04-03",
                }
            )
            writer.update_plan({"review_cadence": "weekly"})
            event = host.run_event(
                {
                    "action": "capture_evidence_cycle",
                    "payload": {
                        "evidence": {
                            "claim": "stale host evidence",
                            "source": "pilot-call",
                            "confidence": 72,
                        },
                        "replan": {"plan_task": "stale host follow-up"},
                    },
                    "options": {"expected_fingerprint": initial["fingerprint"]},
                }
            )

        self.assertFalse(event["ok"])
        self.assertEqual(event["type"], "conflict")
        self.assertEqual(event["error"]["type"], "conflict")
        self.assertEqual(event["error"]["error_code"], "plan_fingerprint_mismatch")
        self.assertTrue(event["error"]["retryable"])
        self.assertEqual(event["error"]["operation"], "capture_evidence_cycle")
        self.assertEqual(event["error"]["step"], "add_evidence")
        self.assertEqual(event["error"]["expected_fingerprint"], initial["fingerprint"])
        self.assertTrue(event["error"]["current_fingerprint"])

    def test_planner_host_multi_role_sequence_preserves_shared_plan_state(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            planner = PlannerHostStep(adapter=_PLANNER_HOST_MODULE.PalamedesKernelAdapter(PalamedesClient(transport=handler_transport)), role="planner")
            researcher = PlannerHostStep(adapter=_PLANNER_HOST_MODULE.PalamedesKernelAdapter(PalamedesClient(transport=handler_transport)), role="researcher")
            reviewer = PlannerHostStep(adapter=_PLANNER_HOST_MODULE.PalamedesKernelAdapter(PalamedesClient(transport=handler_transport)), role="reviewer")

            plan_event = planner.run_event(
                {
                    "action": "update_plan",
                    "payload": {
                        "goal": "Narrow onboarding bottleneck",
                        "success_metric": "Reach 3 retained pilots",
                        "deadline": "2026-04-30",
                    },
                }
            )
            evidence_event = researcher.run_event(
                {
                    "action": "capture_evidence_cycle",
                    "payload": {
                        "evidence": {
                            "claim": "Pilot calls show the same activation blocker",
                            "source": "pilot-call",
                            "confidence": 78,
                        },
                        "replan": {
                            "plan_task": "Test a tighter activation walkthrough",
                        },
                        "idempotency_key": "sequence-1",
                    },
                    "options": {
                        "expected_fingerprint": plan_event["result"]["post_fingerprint"],
                        "allow_retry": True,
                        "history_limit": 2,
                    },
                }
            )
            preview_event = reviewer.run_event({"action": "preview_restore_previous"})

        self.assertTrue(plan_event["ok"])
        self.assertEqual(plan_event["type"], "plan_update_applied")
        self.assertTrue(evidence_event["ok"])
        self.assertEqual(evidence_event["type"], "evidence_cycle_applied")
        self.assertEqual(evidence_event["result"]["post_cycle"]["plan"]["evidence"][-1]["claim"], "Pilot calls show the same activation blocker")
        self.assertIn("Test a tighter activation walkthrough", evidence_event["result"]["post_cycle"]["plan"]["plan_tasks"])
        self.assertTrue(preview_event["ok"])
        self.assertEqual(preview_event["type"], "restore_preview")
        self.assertIn("changed_fields", preview_event["preview"])

    def test_reviewer_role_cannot_update_plan(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            reviewer = PlannerHostStep(
                adapter=_PLANNER_HOST_MODULE.PalamedesKernelAdapter(PalamedesClient(transport=handler_transport)),
                role="reviewer",
            )
            event = reviewer.run_event(
                {
                    "action": "update_plan",
                    "payload": {
                        "goal": "reviewer should not write plan",
                    },
                }
            )

        self.assertFalse(event["ok"])
        self.assertEqual(event["type"], "permission_denied")
        self.assertEqual(event["error"]["type"], "permission_denied")
        self.assertIn("needs plan.write", event["error"]["message"])


if __name__ == "__main__":
    unittest.main()
