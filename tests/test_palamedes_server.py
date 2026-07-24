#!/usr/bin/env python3
import io
import json
import tempfile
import unittest
from pathlib import Path

import palamedes
from palamedes_host_contract import host_action_contract
from palamedes_server import PalamedesHandler


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


def decode_response(handler: PalamedesHandler):
    payload = json.loads(handler.wfile.getvalue().decode("utf-8"))
    return handler._status, payload, handler._sent_headers


class PalamedesServerTests(unittest.TestCase):
    def test_get_plan_returns_fingerprint_and_etag(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            handler = build_handler("GET", "/plan")
            handler.do_GET()
            status, payload, headers = decode_response(handler)

        self.assertEqual(status, 200)
        self.assertIn("fingerprint", payload)
        self.assertEqual(headers.get("ETag"), f'"{payload["fingerprint"]}"')

    def test_post_plan_if_match_succeeds_and_updates_etag(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            first = build_handler("GET", "/plan")
            first.do_GET()
            _, initial_payload, headers = decode_response(first)

            body = json.dumps({"goal": "http update"}).encode("utf-8")
            handler = build_handler(
                "POST",
                "/plan",
                body=body,
                headers={"Content-Type": "application/json", "If-Match": headers["ETag"]},
            )
            handler.do_POST()
            status, payload, response_headers = decode_response(handler)

        self.assertEqual(status, 200)
        self.assertEqual(payload["plan"]["goal"], "http update")
        self.assertNotEqual(payload["fingerprint"], initial_payload["fingerprint"])
        self.assertEqual(response_headers.get("ETag"), f'"{payload["fingerprint"]}"')

    def test_post_plan_rejects_stale_if_match(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            first = build_handler("GET", "/plan")
            first.do_GET()
            _, initial_payload, headers = decode_response(first)

            fresh_body = json.dumps({"goal": "first update"}).encode("utf-8")
            fresh = build_handler(
                "POST",
                "/plan",
                body=fresh_body,
                headers={"Content-Type": "application/json", "If-Match": headers["ETag"]},
            )
            fresh.do_POST()

            stale_body = json.dumps({"goal": "stale update"}).encode("utf-8")
            stale = build_handler(
                "POST",
                "/plan",
                body=stale_body,
                headers={"Content-Type": "application/json", "If-Match": f'"{initial_payload["fingerprint"]}"'},
            )
            stale.do_POST()
            status, payload, response_headers = decode_response(stale)

        self.assertEqual(status, 412)
        self.assertEqual(payload["error"], "plan fingerprint mismatch")
        self.assertEqual(payload["error_code"], "plan_fingerprint_mismatch")
        self.assertTrue(payload["retryable"])
        self.assertEqual(payload["operation"], "update_plan")
        self.assertEqual(payload["step"], "mutation")
        self.assertIn("current_fingerprint", payload)

    def test_post_evidence_reuses_idempotency_key_without_duplicate_append(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            body = json.dumps(
                {
                    "claim": "Server idempotent evidence",
                    "source": "pilot-call",
                    "confidence": 73,
                    "idempotency_key": "http-evidence-1",
                }
            ).encode("utf-8")
            first = build_handler("POST", "/evidence", body=body, headers={"Content-Type": "application/json"})
            first.do_POST()
            first_status, first_payload, _ = decode_response(first)

            second = build_handler("POST", "/evidence", body=body, headers={"Content-Type": "application/json"})
            second.do_POST()
            second_status, second_payload, _ = decode_response(second)

        self.assertEqual(first_status, 200)
        self.assertEqual(second_status, 200)
        self.assertFalse(first_payload["idempotency_replayed"])
        self.assertTrue(second_payload["idempotency_replayed"])
        self.assertEqual(len(second_payload["plan"]["evidence"]), 1)
        self.assertEqual(first_payload["fingerprint"], second_payload["fingerprint"])

    def test_post_plan_rejects_empty_body(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            handler = build_handler("POST", "/plan", body=b"", headers={"Content-Type": "application/json"})
            handler.do_POST()
            status, payload, _headers = decode_response(handler)

        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "empty_body")
        self.assertEqual(payload["error_code"], "empty_body")
        self.assertFalse(payload["retryable"])
        self.assertEqual(payload["operation"], "request_body")
        self.assertEqual(payload["step"], "read")

    def test_get_history_returns_revision_entries(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            update = build_handler(
                "POST",
                "/plan",
                body=json.dumps({"goal": "history endpoint"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            update.do_POST()
            handler = build_handler("GET", "/history")
            handler.do_GET()
            status, payload, _headers = decode_response(handler)

        self.assertEqual(status, 200)
        self.assertTrue(payload["revisions"])
        self.assertEqual(payload["revisions"][0]["source"], "update_plan")
        self.assertIn("metadata", payload["revisions"][0])

    def test_get_reviews_filters_direct_http_endpoint(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            seed = build_handler(
                "POST",
                "/plan",
                body=json.dumps({"goal": "reviews endpoint", "success_metric": "Reach 2 pilots", "deadline": "2026-05-01"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            seed.do_POST()
            _seed_status, _seed_payload, seed_headers = decode_response(seed)

            request = build_handler(
                "POST",
                "/tools/execute",
                body=json.dumps(
                    {
                        "tool": "request_review",
                        "input": {
                            "scope": "plan",
                            "reason": "Owner needs to approve the next planning branch.",
                            "requested_by": "palamedes-server-test",
                            "priority": "high",
                            "assigned_to": "owner",
                        },
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json", "If-Match": seed_headers["ETag"]},
            )
            request.do_POST()

            handler = build_handler("GET", "/reviews?status=open&assigned_to=owner&limit=5")
            handler.do_GET()
            status, payload, _headers = decode_response(handler)

        self.assertEqual(status, 200)
        self.assertEqual(payload["tool_name"], "list_reviews")
        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["reviews"][0]["priority"], "high")
        self.assertEqual(payload["reviews"][0]["assigned_to"], "owner")

    def test_get_reviews_supports_priority_sorting(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            seed = build_handler(
                "POST",
                "/plan",
                body=json.dumps({"goal": "reviews sorting endpoint", "success_metric": "Reach 2 pilots", "deadline": "2026-05-01"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            seed.do_POST()
            _seed_status, _seed_payload, seed_headers = decode_response(seed)

            low = build_handler(
                "POST",
                "/tools/execute",
                body=json.dumps(
                    {
                        "tool": "request_review",
                        "input": {
                            "scope": "plan",
                            "reason": "Low priority queue item.",
                            "requested_by": "palamedes-server-test",
                            "priority": "low",
                            "request_id": "review-low",
                        },
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json", "If-Match": seed_headers["ETag"]},
            )
            low.do_POST()
            _low_status, _low_payload, low_headers = decode_response(low)

            high = build_handler(
                "POST",
                "/tools/execute",
                body=json.dumps(
                    {
                        "tool": "request_review",
                        "input": {
                            "scope": "plan",
                            "reason": "High priority queue item.",
                            "requested_by": "palamedes-server-test",
                            "priority": "high",
                            "request_id": "review-high",
                        },
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json", "If-Match": low_headers["ETag"]},
            )
            high.do_POST()

            handler = build_handler("GET", "/reviews?sort_by=priority&order=desc&limit=5")
            handler.do_GET()
            status, payload, _headers = decode_response(handler)

        self.assertEqual(status, 200)
        self.assertEqual(payload["filters"]["sort_by"], "priority")
        self.assertEqual(payload["filters"]["order"], "desc")
        self.assertEqual([item["id"] for item in payload["reviews"][:2]], ["review-high", "review-low"])

    def test_get_reviews_supports_stale_after_sorting_and_missing_deadlines_last(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            seed = build_handler(
                "POST",
                "/plan",
                body=json.dumps({"goal": "reviews stale sorting endpoint", "success_metric": "Reach 2 pilots", "deadline": "2026-05-01"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            seed.do_POST()
            _seed_status, _seed_payload, seed_headers = decode_response(seed)

            late = build_handler(
                "POST",
                "/tools/execute",
                body=json.dumps(
                    {
                        "tool": "request_review",
                        "input": {
                            "scope": "plan",
                            "reason": "Later deadline queue item.",
                            "requested_by": "palamedes-server-test",
                            "request_id": "review-late",
                            "stale_after": "2026-05-03T09:00:00Z",
                        },
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json", "If-Match": seed_headers["ETag"]},
            )
            late.do_POST()
            _late_status, _late_payload, late_headers = decode_response(late)

            soon = build_handler(
                "POST",
                "/tools/execute",
                body=json.dumps(
                    {
                        "tool": "request_review",
                        "input": {
                            "scope": "plan",
                            "reason": "Soon deadline queue item.",
                            "requested_by": "palamedes-server-test",
                            "request_id": "review-soon",
                            "stale_after": "2026-04-26T09:00:00Z",
                        },
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json", "If-Match": late_headers["ETag"]},
            )
            soon.do_POST()
            _soon_status, _soon_payload, soon_headers = decode_response(soon)

            no_deadline = build_handler(
                "POST",
                "/tools/execute",
                body=json.dumps(
                    {
                        "tool": "request_review",
                        "input": {
                            "scope": "plan",
                            "reason": "No deadline queue item.",
                            "requested_by": "palamedes-server-test",
                            "request_id": "review-none",
                        },
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json", "If-Match": soon_headers["ETag"]},
            )
            no_deadline.do_POST()

            handler = build_handler("GET", "/reviews?sort_by=stale_after&order=asc&limit=5")
            handler.do_GET()
            status, payload, _headers = decode_response(handler)

        self.assertEqual(status, 200)
        self.assertEqual(payload["filters"]["sort_by"], "stale_after")
        self.assertEqual(payload["filters"]["order"], "asc")
        self.assertEqual([item["id"] for item in payload["reviews"][:3]], ["review-soon", "review-late", "review-none"])

    def test_get_reviews_inbox_applies_open_priority_desc_preset(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            seed = build_handler(
                "POST",
                "/plan",
                body=json.dumps({"goal": "reviews inbox endpoint", "success_metric": "Reach 2 pilots", "deadline": "2026-05-01"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            seed.do_POST()
            _seed_status, _seed_payload, seed_headers = decode_response(seed)

            open_low = build_handler(
                "POST",
                "/tools/execute",
                body=json.dumps(
                    {
                        "tool": "request_review",
                        "input": {
                            "scope": "plan",
                            "reason": "Low priority inbox item.",
                            "requested_by": "palamedes-server-test",
                            "priority": "low",
                            "assigned_to": "owner",
                            "stale_after": "2026-05-03T09:00:00Z",
                            "sla_bucket": "72h",
                            "request_id": "review-open-low",
                        },
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json", "If-Match": seed_headers["ETag"]},
            )
            open_low.do_POST()
            _open_low_status, _open_low_payload, open_low_headers = decode_response(open_low)

            open_high = build_handler(
                "POST",
                "/tools/execute",
                body=json.dumps(
                    {
                        "tool": "request_review",
                        "input": {
                            "scope": "plan",
                            "reason": "High priority inbox item.",
                            "requested_by": "palamedes-server-test",
                            "priority": "high",
                            "assigned_to": "owner",
                            "stale_after": "2026-04-26T09:00:00Z",
                            "sla_bucket": "4h",
                            "request_id": "review-open-high",
                        },
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json", "If-Match": open_low_headers["ETag"]},
            )
            open_high.do_POST()
            _open_high_status, _open_high_payload, open_high_headers = decode_response(open_high)

            closed = build_handler(
                "POST",
                "/tools/execute",
                body=json.dumps(
                    {
                        "tool": "request_review",
                        "input": {
                            "scope": "plan",
                            "reason": "This item should be filtered because it is closed.",
                            "requested_by": "palamedes-server-test",
                            "priority": "critical",
                            "assigned_to": "owner",
                            "request_id": "review-closed",
                        },
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json", "If-Match": open_high_headers["ETag"]},
            )
            closed.do_POST()
            _closed_status, _closed_payload, closed_headers = decode_response(closed)

            resolve = build_handler(
                "POST",
                "/tools/execute",
                body=json.dumps(
                    {
                        "tool": "resolve_review",
                        "input": {
                            "request_id": "review-closed",
                            "status": "resolved",
                            "resolution": "Already handled.",
                        },
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json", "If-Match": closed_headers["ETag"]},
            )
            resolve.do_POST()

            handler = build_handler("GET", "/reviews/inbox?assignee=owner&limit=5")
            handler.do_GET()
            status, payload, _headers = decode_response(handler)

        self.assertEqual(status, 200)
        self.assertEqual(payload["tool_name"], "list_reviews")
        self.assertEqual(payload["filters"]["status"], "open")
        self.assertEqual(payload["filters"]["assigned_to"], "owner")
        self.assertEqual(payload["filters"]["sort_by"], "priority")
        self.assertEqual(payload["filters"]["order"], "desc")
        self.assertEqual([item["id"] for item in payload["reviews"]], ["review-open-high", "review-open-low"])
        self.assertEqual(payload["reviews"][0]["stale_after"], "2026-04-26T09:00:00Z")
        self.assertEqual(payload["reviews"][0]["sla_bucket"], "4h")

    def test_get_review_detail_and_post_review_update_direct_http_endpoint(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            seed = build_handler(
                "POST",
                "/plan",
                body=json.dumps({"goal": "review detail endpoint", "success_metric": "Reach 2 pilots", "deadline": "2026-05-01"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            seed.do_POST()
            _seed_status, _seed_payload, seed_headers = decode_response(seed)

            request = build_handler(
                "POST",
                "/tools/execute",
                body=json.dumps(
                    {
                        "tool": "request_review",
                        "input": {
                            "scope": "plan",
                            "reason": "Owner needs to triage the review queue.",
                            "requested_by": "palamedes-server-test",
                        },
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json", "If-Match": seed_headers["ETag"]},
            )
            request.do_POST()
            _request_status, request_payload, request_headers = decode_response(request)
            request_id = request_payload["result"]["review_request"]["id"]

            detail = build_handler("GET", f"/reviews/{request_id}")
            detail.do_GET()
            detail_status, detail_payload, _detail_headers = decode_response(detail)

            update = build_handler(
                "POST",
                f"/reviews/{request_id}",
                body=json.dumps({"priority": "high", "assigned_to": "reviewer", "stale_after": "2026-05-02T09:00:00Z", "sla_bucket": "24h"}).encode("utf-8"),
                headers={"Content-Type": "application/json", "If-Match": request_headers["ETag"]},
            )
            update.do_POST()
            update_status, update_payload, update_headers = decode_response(update)

        self.assertEqual(detail_status, 200)
        self.assertEqual(detail_payload["tool_name"], "get_review")
        self.assertEqual(detail_payload["review"]["id"], request_id)
        self.assertEqual(update_status, 200)
        self.assertEqual(update_payload["tool_name"], "update_review")
        self.assertEqual(update_payload["review_request"]["priority"], "high")
        self.assertEqual(update_payload["review_request"]["assigned_to"], "reviewer")
        self.assertEqual(update_payload["review_request"]["stale_after"], "2026-05-02T09:00:00Z")
        self.assertEqual(update_payload["review_request"]["sla_bucket"], "24h")
        self.assertEqual(update_headers.get("ETag"), f'"{update_payload["fingerprint"]}"')

    def test_get_health_returns_storage_diagnostics(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            handler = build_handler("GET", "/health")
            handler.do_GET()
            status, payload, _headers = decode_response(handler)

        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["tool_name"], "get_health")
        self.assertEqual(payload["result_type"], "health")
        self.assertEqual(payload["status"], "ok")
        self.assertIn("logs", payload)
        self.assertIn("revisions", payload["logs"])
        self.assertIn("recovery_candidate_available", payload)

    def test_get_doctor_returns_contract_readiness_report(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            handler = build_handler("GET", "/doctor")
            handler.do_GET()
            status, payload, _headers = decode_response(handler)

        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["contract_version"], palamedes.CONTRACT_VERSION)
        self.assertIn("checks", payload)
        self.assertIn("check_summary", payload)
        self.assertGreaterEqual(len(payload["checks"]), 5)
        self.assertEqual(payload["check_summary"]["fail"], 0)
        self.assertGreaterEqual(payload["check_summary"]["warn"], 1)
        self.assertIn("schema_drift", payload)
        self.assertIn("tool_schema", payload)
        self.assertIn("host_action_contract", payload)
        self.assertIn("conformance", payload)

    def test_get_contracts_returns_catalog(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            handler = build_handler("GET", "/contracts")
            handler.do_GET()
            status, payload, _headers = decode_response(handler)

        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["result_type"], "contracts")
        self.assertEqual(payload["contract_version"], palamedes.CONTRACT_VERSION)
        self.assertIn("stability_levels", payload)
        self.assertIn("summary", payload)
        self.assertGreaterEqual(payload["summary"]["experimental_contract_count"], 1)
        self.assertIn("spec_entrypoint", payload)
        self.assertIn("host_action_contract", payload["contracts"])
        self.assertIn("profile_summary", payload["contracts"]["host_action_contract"])
        self.assertIn("conformance_manifest", payload["contracts"])

    def test_get_cycle_returns_plan_qa_health_and_history(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            update = build_handler(
                "POST",
                "/plan",
                body=json.dumps(
                    {
                        "goal": "cycle endpoint",
                        "success_metric": "Reach 2 pilots",
                        "deadline": "2026-04-03",
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            update.do_POST()
            handler = build_handler("GET", "/cycle?limit=1")
            handler.do_GET()
            status, payload, headers = decode_response(handler)

        self.assertEqual(status, 200)
        self.assertEqual(payload["result_type"], "cycle")
        self.assertEqual(payload["plan"]["goal"], "cycle endpoint")
        self.assertIn("score", payload["qa"])
        self.assertIn("status", payload["health"])
        self.assertEqual(payload["history_limit"], 1)
        self.assertEqual(len(payload["history"]), 1)
        self.assertEqual(headers.get("ETag"), f'"{payload["fingerprint"]}"')

    def test_get_tools_returns_authoritative_catalog_metadata(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            handler = build_handler("GET", "/tools")
            handler.do_GET()
            status, payload, _headers = decode_response(handler)

        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["result_type"], "tool_catalog")
        self.assertEqual(payload["contract_version"], palamedes.CONTRACT_VERSION)
        self.assertEqual(payload["implementation_version"], palamedes.IMPLEMENTATION_VERSION)
        self.assertTrue(payload["catalog"]["authoritative"])
        self.assertEqual(payload["catalog"]["execute_endpoint"], "/tools/execute")
        self.assertEqual(payload["catalog"]["legacy_execute_endpoint_template"], "/tools/{tool_name}")
        self.assertGreater(payload["catalog"]["tool_count"], 0)
        self.assertEqual(len(payload["tools"]), payload["catalog"]["tool_count"])
        update_plan = next(item for item in payload["tools"] if item["name"] == "update_plan")
        self.assertEqual(update_plan["kind"], "mutation")
        self.assertEqual(update_plan["execute_via"]["generic"], "/tools/execute")
        self.assertEqual(update_plan["execute_via"]["legacy_wrapper"], "/tools/update_plan")

    def test_get_tool_detail_returns_single_tool_descriptor(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            handler = build_handler("GET", "/tools/get_plan")
            handler.do_GET()
            status, payload, _headers = decode_response(handler)

        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["result_type"], "tool_detail")
        self.assertEqual(payload["tool"]["name"], "get_plan")
        self.assertEqual(payload["tool"]["kind"], "read")
        self.assertEqual(payload["tool"]["execute_via"]["legacy_wrapper"], "/tools/get_plan")

    def test_post_tools_execute_runs_generic_endpoint_without_breaking_legacy_wrapper(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            generic = build_handler(
                "POST",
                "/tools/execute",
                body=json.dumps({"tool": "update_plan", "input": {"goal": "generic execute"}}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            generic.do_POST()
            generic_status, generic_payload, generic_headers = decode_response(generic)

            legacy = build_handler(
                "POST",
                "/tools/update_plan",
                body=json.dumps({"goal": "legacy wrapper"}).encode("utf-8"),
                headers={"Content-Type": "application/json", "If-Match": generic_headers["ETag"]},
            )
            legacy.do_POST()
            legacy_status, legacy_payload, legacy_headers = decode_response(legacy)

        self.assertEqual(generic_status, 200)
        self.assertEqual(generic_payload["tool"], "update_plan")
        self.assertEqual(generic_payload["input"]["goal"], "generic execute")
        self.assertEqual(generic_payload["result"]["plan"]["goal"], "generic execute")
        self.assertEqual(generic_headers.get("ETag"), f'"{generic_payload["result"]["fingerprint"]}"')
        self.assertEqual(legacy_status, 200)
        self.assertEqual(legacy_payload["tool"], "update_plan")
        self.assertEqual(legacy_payload["input"]["goal"], "legacy wrapper")
        self.assertEqual(legacy_payload["input"]["expected_fingerprint"], generic_payload["result"]["fingerprint"])
        self.assertEqual(legacy_payload["result"]["plan"]["goal"], "legacy wrapper")
        self.assertEqual(legacy_headers.get("ETag"), f'"{legacy_payload["result"]["fingerprint"]}"')

    def test_post_tools_execute_can_request_human_review(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            seed = build_handler(
                "POST",
                "/plan",
                body=json.dumps({"goal": "review seed", "success_metric": "Reach 2 pilots", "deadline": "2026-05-01"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            seed.do_POST()
            _seed_status, seed_payload, seed_headers = decode_response(seed)

            handler = build_handler(
                "POST",
                "/tools/execute",
                body=json.dumps(
                    {
                        "tool": "request_review",
                        "input": {
                            "scope": "plan",
                            "reason": "Owner needs to approve the next planning branch.",
                            "requested_by": "palamedes-server-test",
                            "related_references": ["paperclip"],
                        },
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json", "If-Match": seed_headers["ETag"]},
            )
            handler.do_POST()
            status, payload, response_headers = decode_response(handler)

        self.assertEqual(status, 200)
        self.assertEqual(payload["tool"], "request_review")
        self.assertEqual(payload["input"]["expected_fingerprint"], seed_payload["fingerprint"])
        self.assertEqual(payload["result"]["review_request"]["scope"], "plan")
        self.assertEqual(payload["result"]["plan"]["human_escalations"][0]["requested_by"], "palamedes-server-test")
        self.assertEqual(response_headers.get("ETag"), f'"{payload["result"]["fingerprint"]}"')

    def test_post_tools_execute_can_resolve_human_review(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            seed = build_handler(
                "POST",
                "/plan",
                body=json.dumps({"goal": "review resolve seed", "success_metric": "Reach 2 pilots", "deadline": "2026-05-01"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            seed.do_POST()
            _seed_status, _seed_payload, seed_headers = decode_response(seed)

            request = build_handler(
                "POST",
                "/tools/execute",
                body=json.dumps(
                    {
                        "tool": "request_review",
                        "input": {
                            "scope": "plan",
                            "reason": "Owner needs to approve the next planning branch.",
                            "requested_by": "palamedes-server-test",
                        },
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json", "If-Match": seed_headers["ETag"]},
            )
            request.do_POST()
            _request_status, request_payload, request_headers = decode_response(request)

            resolve = build_handler(
                "POST",
                "/tools/execute",
                body=json.dumps(
                    {
                        "tool": "resolve_review",
                        "input": {
                            "request_id": request_payload["result"]["review_request"]["id"],
                            "status": "resolved",
                            "resolution": "Owner approved continuing the branch.",
                            "resolved_by": "owner",
                        },
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json", "If-Match": request_headers["ETag"]},
            )
            resolve.do_POST()
            status, payload, response_headers = decode_response(resolve)

        self.assertEqual(status, 200)
        self.assertEqual(payload["tool"], "resolve_review")
        self.assertEqual(payload["result"]["review_request"]["status"], "resolved")
        self.assertEqual(payload["result"]["review_request"]["resolved_by"], "owner")
        self.assertEqual(response_headers.get("ETag"), f'"{payload["result"]["fingerprint"]}"')

    def test_post_tools_execute_can_list_filtered_reviews(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            seed = build_handler(
                "POST",
                "/plan",
                body=json.dumps({"goal": "review list seed", "success_metric": "Reach 2 pilots", "deadline": "2026-05-01"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            seed.do_POST()
            _seed_status, _seed_payload, seed_headers = decode_response(seed)

            request = build_handler(
                "POST",
                "/tools/execute",
                body=json.dumps(
                    {
                        "tool": "request_review",
                        "input": {
                            "scope": "plan",
                            "reason": "Owner needs to approve the next planning branch.",
                            "requested_by": "palamedes-server-test",
                        },
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json", "If-Match": seed_headers["ETag"]},
            )
            request.do_POST()
            _request_status, request_payload, request_headers = decode_response(request)

            resolve = build_handler(
                "POST",
                "/tools/execute",
                body=json.dumps(
                    {
                        "tool": "resolve_review",
                        "input": {
                            "request_id": request_payload["result"]["review_request"]["id"],
                            "status": "resolved",
                            "resolution": "Owner approved continuing the branch.",
                            "resolved_by": "owner",
                        },
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json", "If-Match": request_headers["ETag"]},
            )
            resolve.do_POST()

            list_handler = build_handler(
                "POST",
                "/tools/execute",
                body=json.dumps({"tool": "list_reviews", "input": {"status": "resolved"}}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            list_handler.do_POST()
            status, payload, _headers = decode_response(list_handler)

        self.assertEqual(status, 200)
        self.assertEqual(payload["tool"], "list_reviews")
        self.assertEqual(payload["result"]["count"], 1)
        self.assertEqual(payload["result"]["reviews"][0]["status"], "resolved")

    def test_get_health_reports_retained_log_counts_after_prune(self):
        with PalamedesStateIsolation():
            palamedes.EVENT_RETENTION_LIMIT = 2
            palamedes.REVISION_RETENTION_LIMIT = 2
            palamedes.ensure_state()
            first = palamedes.mutate_plan_state(
                lambda plan: plan.update(
                    {
                        "goal": "server prune first",
                        "success_metric": "Reach 2 pilots",
                        "deadline": "2026-04-03",
                    }
                ),
                revision_source="test_server_prune",
            )
            second = palamedes.mutate_plan_state(
                lambda plan: plan.update({"goal": "server prune second"}),
                expected_fingerprint=palamedes.plan_fingerprint(first),
                revision_source="test_server_prune",
            )
            palamedes.mutate_plan_state(
                lambda plan: plan.update({"goal": "server prune third"}),
                expected_fingerprint=palamedes.plan_fingerprint(second),
                revision_source="test_server_prune",
            )
            palamedes.append_jsonl(palamedes.EVENTS_PATH, {"type": "evt1"})
            palamedes.append_jsonl(palamedes.EVENTS_PATH, {"type": "evt2"})
            palamedes.append_jsonl(palamedes.EVENTS_PATH, {"type": "evt3"})
            handler = build_handler("GET", "/health")
            handler.do_GET()
            status, payload, _headers = decode_response(handler)

        self.assertEqual(status, 200)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["logs"]["events"]["line_count"], 2)
        self.assertEqual(payload["logs"]["revisions"]["line_count"], 2)

    def test_preview_restore_tool_wrapper_returns_diff_summary(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            update = build_handler(
                "POST",
                "/plan",
                body=json.dumps({"goal": "preview baseline"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            update.do_POST()
            history = build_handler("GET", "/history")
            history.do_GET()
            _status, history_payload, _headers = decode_response(history)
            second = build_handler(
                "POST",
                "/plan",
                body=json.dumps({"goal": "preview changed"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            second.do_POST()
            handler = build_handler(
                "POST",
                "/tools/preview_restore",
                body=json.dumps({"input": {"revision_id": history_payload["revisions"][-1]["revision_id"]}}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            handler.do_POST()
            status, payload, _headers = decode_response(handler)

        self.assertEqual(status, 200)
        self.assertTrue(payload["result"]["ok"])
        self.assertEqual(payload["result"]["tool_name"], "preview_restore")
        self.assertEqual(payload["result"]["result_type"], "restore_preview")
        self.assertIn("changed_fields", payload["result"])
        self.assertIn("goal", payload["result"]["changed_fields"])
        self.assertIn("metadata", payload["result"])
        self.assertIn("diff", payload["result"])

    def test_restore_preview_endpoint_returns_direct_result(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            update = build_handler(
                "POST",
                "/plan",
                body=json.dumps({"goal": "preview endpoint baseline"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            update.do_POST()
            history = build_handler("GET", "/history")
            history.do_GET()
            _status, history_payload, _headers = decode_response(history)
            second = build_handler(
                "POST",
                "/plan",
                body=json.dumps({"goal": "preview endpoint changed"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            second.do_POST()
            handler = build_handler(
                "POST",
                "/restore/preview",
                body=json.dumps({"revision_id": history_payload["revisions"][-1]["revision_id"]}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            handler.do_POST()
            status, payload, _headers = decode_response(handler)

        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["tool_name"], "preview_restore")
        self.assertEqual(payload["result_type"], "restore_preview")
        self.assertIn("goal", payload["changed_fields"])

    def test_restore_revision_tool_wrapper_rejects_stale_fingerprint(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            first_get = build_handler("GET", "/plan")
            first_get.do_GET()
            _status, initial_payload, initial_headers = decode_response(first_get)

            first_update = build_handler(
                "POST",
                "/plan",
                body=json.dumps({"goal": "first restore baseline"}).encode("utf-8"),
                headers={"Content-Type": "application/json", "If-Match": initial_headers["ETag"]},
            )
            first_update.do_POST()

            history = build_handler("GET", "/history")
            history.do_GET()
            _status, history_payload, _headers = decode_response(history)

            second_update = build_handler(
                "POST",
                "/plan",
                body=json.dumps({"goal": "second restore baseline"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            second_update.do_POST()

            stale_restore = build_handler(
                "POST",
                "/tools/restore_revision",
                body=json.dumps({"input": {"revision_id": history_payload["revisions"][-1]["revision_id"]}}).encode("utf-8"),
                headers={"Content-Type": "application/json", "If-Match": f'"{initial_payload["fingerprint"]}"'},
            )
            stale_restore.do_POST()
            status, payload, response_headers = decode_response(stale_restore)

        self.assertEqual(status, 412)
        self.assertEqual(payload["error"], "plan fingerprint mismatch")
        self.assertEqual(payload["error_code"], "plan_fingerprint_mismatch")
        self.assertTrue(payload["retryable"])
        self.assertEqual(payload["operation"], "restore_revision")
        self.assertEqual(payload["step"], "mutation")
        self.assertIn("current_fingerprint", payload)
        self.assertEqual(response_headers.get("ETag"), f'"{payload["current_fingerprint"]}"')

    def test_restore_endpoint_rejects_stale_fingerprint(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            first_get = build_handler("GET", "/plan")
            first_get.do_GET()
            _status, initial_payload, initial_headers = decode_response(first_get)

            first_update = build_handler(
                "POST",
                "/plan",
                body=json.dumps({"goal": "first restore endpoint baseline"}).encode("utf-8"),
                headers={"Content-Type": "application/json", "If-Match": initial_headers["ETag"]},
            )
            first_update.do_POST()

            history = build_handler("GET", "/history")
            history.do_GET()
            _status, history_payload, _headers = decode_response(history)

            second_update = build_handler(
                "POST",
                "/plan",
                body=json.dumps({"goal": "second restore endpoint baseline"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            second_update.do_POST()

            stale_restore = build_handler(
                "POST",
                "/restore",
                body=json.dumps({"revision_id": history_payload["revisions"][-1]["revision_id"]}).encode("utf-8"),
                headers={"Content-Type": "application/json", "If-Match": f'"{initial_payload["fingerprint"]}"'},
            )
            stale_restore.do_POST()
            status, payload, response_headers = decode_response(stale_restore)

        self.assertEqual(status, 412)
        self.assertEqual(payload["error"], "plan fingerprint mismatch")
        self.assertEqual(payload["error_code"], "plan_fingerprint_mismatch")
        self.assertTrue(payload["retryable"])
        self.assertEqual(payload["operation"], "restore_revision")
        self.assertEqual(payload["step"], "mutation")
        self.assertIn("current_fingerprint", payload)
        self.assertEqual(response_headers.get("ETag"), f'"{payload["current_fingerprint"]}"')

    def test_invalid_cycle_limit_returns_machine_readable_error_envelope(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            handler = build_handler("GET", "/cycle?limit=nope")
            handler.do_GET()
            status, payload, _headers = decode_response(handler)

        self.assertEqual(status, 400)
        self.assertEqual(payload["error"], "limit must be an integer")
        self.assertEqual(payload["error_code"], "invalid_request")
        self.assertFalse(payload["retryable"])
        self.assertEqual(payload["operation"], "cycle_snapshot")
        self.assertEqual(payload["step"], "query")

    def test_agent_act_maps_restore_preview_command(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            update = build_handler(
                "POST",
                "/plan",
                body=json.dumps({"goal": "agent act preview"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            update.do_POST()
            history = build_handler("GET", "/history")
            history.do_GET()
            _status, history_payload, _headers = decode_response(history)
            handler = build_handler(
                "POST",
                "/agent/act",
                body=json.dumps({"input": f"/palamedes.restore-preview revision_id={history_payload['revisions'][-1]['revision_id']}"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            handler.do_POST()
            status, payload, _headers = decode_response(handler)

        self.assertEqual(status, 200)
        self.assertEqual(payload["tool"], "preview_restore")
        self.assertIn("changed_fields", payload["result"])

    def test_tools_preview_restore_accepts_previous_shortcut(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            first = build_handler(
                "POST",
                "/plan",
                body=json.dumps({"goal": "server previous first"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            first.do_POST()
            second = build_handler(
                "POST",
                "/plan",
                body=json.dumps({"goal": "server previous second"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            second.do_POST()
            handler = build_handler(
                "POST",
                "/tools/preview_restore",
                body=json.dumps({"input": {"previous": True}}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            handler.do_POST()
            status, payload, _headers = decode_response(handler)

        self.assertEqual(status, 200)
        self.assertEqual(payload["result"]["selected_via"], "previous")

    def test_capture_evidence_cycle_tool_wrapper_returns_planning_cycle(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            handler = build_handler(
                "POST",
                "/tools/capture_evidence_cycle",
                body=json.dumps(
                    {
                        "input": {
                            "evidence": {
                                "claim": "Server cycle evidence",
                                "source": "pilot-call",
                                "confidence": 74,
                            },
                            "replan": {
                                "plan_task": "Update activation follow-up",
                            },
                            "idempotency_key": "server-cycle-1",
                            "history_limit": 1,
                        }
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            handler.do_POST()
            status, payload, headers = decode_response(handler)

        self.assertEqual(status, 200)
        self.assertEqual(payload["tool"], "capture_evidence_cycle")
        self.assertEqual(payload["result"]["result_type"], "planning_cycle")
        self.assertEqual(payload["result"]["operation"], "capture_evidence_cycle")
        self.assertEqual(payload["result"]["post_cycle"]["history_limit"], 1)
        self.assertIn("evidence_result", payload["result"])
        self.assertIn("replan_result", payload["result"])
        self.assertEqual(headers.get("ETag"), f'"{payload["result"]["post_fingerprint"]}"')

    def test_get_host_action_contract_returns_shared_contract(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            handler = build_handler("GET", "/host/action-contract?role=reviewer")
            handler.do_GET()
            status, payload, _headers = decode_response(handler)

        self.assertEqual(status, 200)
        self.assertEqual(payload["role"], "reviewer")
        self.assertEqual(payload["profile"], "reviewer_restore")
        self.assertEqual(payload["allowed_actions"], ["request_review", "resolve_review", "preview_restore_previous", "restore_previous"])
        self.assertEqual(payload["capabilities"], ["plan.read", "review.request", "review.resolve", "plan.restore"])
        self.assertEqual(payload["actions"], host_action_contract("reviewer")["actions"])
        self.assertIn("input_schema", payload)
        action_map = {item["action"]: item for item in payload["actions"]}
        self.assertEqual(action_map["request_review"]["required_capabilities"], ["review.request"])
        self.assertEqual(action_map["resolve_review"]["required_capabilities"], ["review.resolve"])
        self.assertEqual(action_map["restore_previous"]["required_capabilities"], ["plan.restore"])
        self.assertEqual(action_map["preview_restore_previous"]["required_capabilities"], ["plan.read"])

    def test_get_host_action_contract_rejects_unknown_role(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            handler = build_handler("GET", "/host/action-contract?role=ghost")
            handler.do_GET()
            status, payload, _headers = decode_response(handler)

        self.assertEqual(status, 400)
        self.assertEqual(payload["type"], "error")
        self.assertEqual(payload["error"], "unknown host role: ghost")


if __name__ == "__main__":
    unittest.main()
