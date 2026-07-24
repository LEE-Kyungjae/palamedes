#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import tempfile
import unittest
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional

import palamedes
from palamedes_conformance import build_http_transport, build_inprocess_transport, load_case, load_manifest, run_case, run_manifest
from palamedes_server import PalamedesHandler


CONTRACTS_DIR = Path(__file__).resolve().parent / "contracts"
CODE_ROOT = Path(__file__).resolve().parent.parent
TS_CONSUMER_PATH = CODE_ROOT / "palamedes_reference_consumer.ts"


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


class PalamedesHTTPServerIsolation:
    def __init__(self) -> None:
        self.server: Optional[ThreadingHTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self.base_url = ""

    def __enter__(self):
        try:
            self.server = ThreadingHTTPServer(("127.0.0.1", 0), PalamedesHandler)
        except PermissionError as exc:
            raise unittest.SkipTest(f"socket bind not permitted in this environment: {exc}") from exc
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
        if self.thread is not None:
            self.thread.join(timeout=2)


class ContractFixtureTests(unittest.TestCase):
    def test_manifest_lists_expected_cases(self):
        manifest = load_manifest()
        self.assertEqual(manifest["version"], "0.1.0")
        self.assertEqual([case["id"] for case in manifest["cases"]], [
            "plan-envelope",
            "etag-fingerprint",
            "stale-write-conflict",
            "restore-roundtrip",
            "idempotent-evidence-dedupe",
        ])

    def test_plan_envelope_contract(self):
        case = load_case("plan-envelope.json")
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            report = run_case(build_inprocess_transport(), case)

        self.assertTrue(report["ok"])
        self.assertEqual(report["id"], "plan-envelope")

    def test_etag_fingerprint_contract(self):
        case = load_case("etag-fingerprint.json")
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            report = run_case(build_inprocess_transport(), case)

        self.assertTrue(report["ok"])
        self.assertEqual(report["id"], "etag-fingerprint")

    def test_stale_write_conflict_contract(self):
        case = load_case("stale-write-conflict.json")
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            report = run_case(build_inprocess_transport(), case)

        self.assertTrue(report["ok"])
        self.assertEqual(report["id"], "stale-write-conflict")

    def test_restore_roundtrip_contract(self):
        case = load_case("restore-roundtrip.json")
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            report = run_case(build_inprocess_transport(), case)

        self.assertTrue(report["ok"])
        self.assertEqual(report["id"], "restore-roundtrip")

    def test_idempotent_evidence_dedupe_contract(self):
        case = load_case("idempotent-evidence-dedupe.json")
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            report = run_case(build_inprocess_transport(), case)

        self.assertTrue(report["ok"])
        self.assertEqual(report["id"], "idempotent-evidence-dedupe")

    def test_runner_returns_machine_readable_json_report(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            report = run_manifest(
                build_inprocess_transport(),
                reset_state=lambda: (shutil.rmtree(palamedes.STATE_DIR, ignore_errors=True), palamedes.ensure_state()),
            )
            encoded = json.dumps(report, sort_keys=True)

        parsed = json.loads(encoded)
        self.assertTrue(parsed["ok"])
        self.assertEqual(parsed["passed"], parsed["case_count"])

    def test_runner_supports_external_http_base_url(self):
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            with PalamedesHTTPServerIsolation() as server:
                transport = build_http_transport(server.base_url)
                report = run_manifest(transport)

        self.assertTrue(report["ok"])
        self.assertEqual(report["passed"], report["case_count"])

    def test_node_ts_reference_consumer_smoke_against_http_surface(self):
        if not shutil.which("node"):
            raise unittest.SkipTest("node is not available")
        with PalamedesStateIsolation():
            palamedes.ensure_state()
            with PalamedesHTTPServerIsolation() as server:
                completed = subprocess.run(
                    ["node", str(TS_CONSUMER_PATH), "--base-url", server.base_url, "--mode", "smoke"],
                    cwd=str(CODE_ROOT),
                    capture_output=True,
                    text=True,
                    env={**os.environ, "NO_COLOR": "1"},
                    check=False,
                )

        if completed.returncode != 0:
            self.fail(f"node ts consumer failed: {completed.stderr or completed.stdout}")
        report = json.loads(completed.stdout)
        self.assertTrue(report["ok"])
        self.assertEqual(report["consumer"], "palamedes_reference_consumer")
        self.assertEqual(report["runtime"], "node_typescript_strip")
        check_names = [item["name"] for item in report["checks"]]
        self.assertEqual(
            check_names,
            ["plan_envelope", "etag_write", "cycle_snapshot", "stale_conflict", "contracts_catalog"],
        )
