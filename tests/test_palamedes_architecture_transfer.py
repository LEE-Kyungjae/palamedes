#!/usr/bin/env python3

import copy
import json
import tempfile
import unittest
from pathlib import Path

from palamedes_architecture_transfer import (
    AUTHORITY_FIELDS,
    CommandResult,
    EvidenceLimits,
    GitNexusEvidenceAdapter,
    propose_mechanism_queries,
    validate_architecture_transfers,
    validate_gitnexus_evidence_packet,
)


REVISION = "a" * 40


def mechanism_queries():
    return [{
        "query_id": "mechanism-1",
        "mechanism": "Recoverable entitlement state transitions",
        "target_pressure": "Observed progress events may be replayed or claimed twice.",
        "target_evidence_ids": ["fact-events"],
        "search_terms": [
            "idempotent failure retry recovery",
            "ledger consistency checkpoint invariant",
            "rollback reversible migration replay",
            "authority entitlement ownership permission",
        ],
    }]


def definition(number, *, content=None):
    return {
        "id": f"Method:src/ledger.py:Ledger.claim#{number}",
        "name": f"claim_{number}",
        "filePath": "src/ledger.py",
        "startLine": 10 + number,
        "endLine": 14 + number,
        "content": content or f"def claim_{number}(key): ensure_idempotent(key)",
        # These must not affect semantic identity or appear in the packet.
        "priority": 1000 - number,
    }


class FakeRunner:
    def __init__(self, root, *, definitions=None, reverse=False, unavailable=False, query_error=False):
        self.root = Path(root)
        self.current = self.root / "target"
        self.source = self.root / "payments"
        self.current.mkdir(exist_ok=True)
        self.source.mkdir(exist_ok=True)
        self.definitions = list(definitions or [definition(1), definition(2), definition(3)])
        self.reverse = reverse
        self.unavailable = unavailable
        self.query_error = query_error
        self.calls = []

    def __call__(self, args, *, cwd, timeout):
        self.calls.append((list(args), Path(cwd), timeout))
        if args[-1] == "list":
            if self.unavailable:
                raise FileNotFoundError("gitnexus is unavailable")
            rows = [
                {"name": "Target", "path": str(self.current), "lastCommit": REVISION},
                {"name": "Payments", "path": str(self.source), "lastCommit": REVISION},
            ]
            if self.reverse:
                rows.reverse()
            return CommandResult(0, json.dumps({"repositories": rows}))
        if args[0] == "git":
            if "rev-parse" in args:
                return CommandResult(0, REVISION + "\n")
            if "status" in args:
                return CommandResult(0, "")
            if "show" in args:
                lines = [""] * 40
                for row in self.definitions:
                    start = int(row.get("startLine", 1)) - 1
                    lines[start] = str(row.get("content", ""))
                return CommandResult(
                    0,
                    "\n".join(lines),
                )
        if "query" in args:
            if self.query_error:
                return CommandResult(2, "", "query crashed")
            rows = list(reversed(self.definitions)) if self.reverse else self.definitions
            return CommandResult(0, json.dumps({
                "processes": [],
                "process_symbols": [copy.deepcopy(self.definitions[0])],
                "definitions": copy.deepcopy(rows),
                "timing": {"wall": 999 if self.reverse else 1},
            }))
        raise AssertionError(args)


def collect_packet(root, *, reverse=False, limits=None, definitions=None):
    runner = FakeRunner(root, reverse=reverse, definitions=definitions)
    adapter = GitNexusEvidenceAdapter(
        runner, cli_prefix=["gitnexus"], limits=limits or EvidenceLimits()
    )
    return adapter.collect(mechanism_queries(), current_repo_path=runner.current), runner


def valid_transfer(source_ids):
    row = {
        "transfer_id": "transfer-ledger",
        "source_ids": source_ids[:2],
        "source_domain": "payment fulfillment",
        "target_domain": "live service game",
        "same_primary_job": False,
        "source_pressure": "A payment callback can arrive more than once after failure.",
        "source_pattern": "An append-only entitlement ledger separates recording from idempotent fulfillment.",
        "source_invariant": "One external idempotency key produces at most one entitlement transition.",
        "source_causal_chain": [
            "callback identity is persisted before fulfillment",
            "replay observes the prior transition instead of granting again",
        ],
        "failure_prevented": "Duplicate fulfillment after retry.",
        "target_pressure": "Recorded activity can be replayed while a reward claim is retried.",
        "target_evidence_ids": ["fact-events"],
        "responsibility_mapping": [{
            "source_role": "payment callback identity",
            "target_role": "activity event identity",
            "uncertainty": "The target event producer's stability is unverified.",
        }],
        "adaptation": "Record progress and claims separately, with a stable event key and claim ledger.",
        "material_differences": {
            "timing": "Payments are immediate; progress accumulates across a season.",
            "institution": "A processor supplies payment IDs; the game owns activity IDs.",
            "scale": "One purchase maps to one grant; many events map to one threshold.",
            "beneficiary_power": "A payer can dispute; a player has weaker reversal rights.",
            "authority_and_data": "Payment authority is external; reward authority stays server-side.",
        },
        "non_transferable_assumptions": [
            "Payment completion does not prove that players desire a progression track."
        ],
        "transfer_limit": "This transfers integrity mechanics, not demand, retention, or willingness to pay.",
        "disconfirming_evidence": [
            "Activity event IDs change during replay or offline reconciliation."
        ],
        "local_probe": "Shadow-write event and claim ledgers without granting rewards.",
        "local_falsifier": "Reconciliation cannot deterministically reproduce one progress balance.",
        "source_outcome_is_target_forecast": False,
    }
    row.update({field: False for field in AUTHORITY_FIELDS})
    return row


class GitNexusEvidenceAdapterTests(unittest.TestCase):
    def test_collect_is_revision_pinned_deterministic_and_excludes_current_repo(self):
        with tempfile.TemporaryDirectory() as first:
            # Paths are part of the snapshot identity, so use two runs over the
            # same fixture root when comparing shuffled provider output.
            packet_a, runner_a = collect_packet(first)
            runner_b = FakeRunner(first, reverse=True)
            packet_b = GitNexusEvidenceAdapter(
                runner_b, cli_prefix=["gitnexus"]
            ).collect(mechanism_queries(), current_repo_path=runner_b.current)

            self.assertEqual(packet_a, packet_b)
            self.assertEqual(packet_a["status"], "ready")
            self.assertEqual([row["repository"] for row in packet_a["repositories"]], ["Payments"])
            self.assertTrue(all(row["revision"] == REVISION for row in packet_a["sources"]))
            self.assertTrue(all(row[field] is False for row in packet_a["sources"] for field in AUTHORITY_FIELDS))
            validate_gitnexus_evidence_packet(packet_a)
            query_call = next(args for args, _, _ in runner_a.calls if "query" in args)
            self.assertIn("--limit", query_call)
            self.assertNotIn("--content", query_call)
            self.assertTrue(
                any(args[0] == "git" and "show" in args for args, _, _ in runner_a.calls)
            )

    def test_host_enforces_result_excerpt_and_total_bounds(self):
        limits = EvidenceLimits(
            max_repositories=1,
            max_queries=1,
            max_results_per_query=2,
            max_sources_total=2,
            max_excerpt_chars=80,
            max_total_excerpt_chars=1000,
        )
        definitions = [definition(index, content="x" * 400) for index in range(1, 8)]
        with tempfile.TemporaryDirectory() as root:
            packet, _ = collect_packet(root, limits=limits, definitions=definitions)
            self.assertEqual(len(packet["sources"]), 2)
            self.assertTrue(all(len(row["excerpt"]) == 80 for row in packet["sources"]))
            self.assertTrue(all(row["excerpt_truncated"] for row in packet["sources"]))

    def test_gitnexus_unavailable_returns_valid_non_authoritative_degradation(self):
        with tempfile.TemporaryDirectory() as root:
            runner = FakeRunner(root, unavailable=True)
            packet = GitNexusEvidenceAdapter(
                runner, cli_prefix=["gitnexus"]
            ).collect(mechanism_queries(), current_repo_path=runner.current)
            self.assertEqual(packet["status"], "unavailable")
            self.assertEqual(packet["sources"], [])
            self.assertEqual(packet["degradations"][0]["code"], "gitnexus_unavailable")
            self.assertFalse(packet["delivery_authority_granted"])
            validate_gitnexus_evidence_packet(packet)

    def test_query_failure_degrades_one_repo_instead_of_fabricating_empty_success(self):
        with tempfile.TemporaryDirectory() as root:
            runner = FakeRunner(root, query_error=True)
            packet = GitNexusEvidenceAdapter(
                runner, cli_prefix=["gitnexus"]
            ).collect(mechanism_queries(), current_repo_path=runner.current)
            self.assertEqual(packet["status"], "degraded")
            self.assertEqual(packet["sources"], [])
            self.assertEqual(packet["repository_results"][0]["status"], "degraded")

    def test_packet_validator_rejects_fabricated_revision_path_and_source(self):
        with tempfile.TemporaryDirectory() as root:
            packet, _ = collect_packet(root)
            fabricated = copy.deepcopy(packet)
            fabricated["sources"][0]["revision"] = "b" * 40
            with self.assertRaisesRegex(ValueError, "unavailable repository snapshot"):
                validate_gitnexus_evidence_packet(fabricated)

            fabricated = copy.deepcopy(packet)
            fabricated["sources"][0]["file_path"] = "../escape.py"
            with self.assertRaisesRegex(ValueError, "safe repository-relative"):
                validate_gitnexus_evidence_packet(fabricated)

            fabricated = copy.deepcopy(packet)
            fabricated["sources"][0]["source_id"] = "gitnexus-source:" + "0" * 64
            with self.assertRaisesRegex(ValueError, "source_id"):
                validate_gitnexus_evidence_packet(fabricated)


class MechanismQueryTests(unittest.TestCase):
    def test_provider_queries_cite_target_facts_and_cover_operational_pressures(self):
        calls = []

        def ask(role, prompt):
            calls.append((role, prompt))
            return {"mechanism_queries": mechanism_queries()}

        rows = propose_mechanism_queries(
            ask,
            [{"fact_id": "fact-events", "fact": "The server already records activity events."}],
            max_queries=1,
        )
        self.assertEqual(rows[0]["target_evidence_ids"], ["fact-events"])
        self.assertEqual(calls[0][0], "architecture_transfer_mechanism_query_designer")

    def test_provider_repairs_topic_name_search_and_unknown_target_id(self):
        responses = [
            {"mechanism_queries": [{
                **mechanism_queries()[0],
                "target_evidence_ids": ["invented-fact"],
                "search_terms": ["battle pass implementation", "reward track"],
            }]},
            {"mechanism_queries": mechanism_queries()},
        ]

        def ask(_role, _prompt):
            return responses.pop(0)

        rows = propose_mechanism_queries(
            ask,
            [{"fact_id": "fact-events", "fact": "Activity events are recorded."}],
            max_queries=1,
        )
        self.assertEqual(rows, mechanism_queries())


class ArchitectureTransferContractTests(unittest.TestCase):
    def packet_and_transfer(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        packet, _ = collect_packet(temporary.name)
        transfer = valid_transfer([row["source_id"] for row in packet["sources"]])
        return packet, transfer

    def test_valid_cross_domain_mapping_is_source_and_target_bounded(self):
        packet, transfer = self.packet_and_transfer()
        rows = validate_architecture_transfers(
            {"transfers": [transfer]},
            evidence_packet=packet,
            target_fact_ids={"fact-events"},
            target_domain="live service game",
        )
        self.assertEqual(rows[0]["authority"], "mechanism_candidate_only")
        self.assertEqual(rows[0]["source_revisions"], [REVISION])
        self.assertFalse(rows[0]["source_outcome_is_target_forecast"])

    def test_rejects_source_fabrication(self):
        packet, transfer = self.packet_and_transfer()
        transfer["source_ids"][0] = "gitnexus-source:" + "f" * 64
        with self.assertRaisesRegex(ValueError, "unavailable source IDs"):
            validate_architecture_transfers(
                [transfer], evidence_packet=packet, target_fact_ids={"fact-events"}
            )

    def test_rejects_topic_copy_without_local_target_pressure(self):
        packet, transfer = self.packet_and_transfer()
        transfer["target_pressure"] = transfer["source_pressure"]
        transfer["source_pattern"] = "A battle pass reward track"
        with self.assertRaisesRegex(ValueError, "copied source pressure"):
            validate_architecture_transfers(
                [transfer], evidence_packet=packet, target_fact_ids={"fact-events"}
            )

    def test_rejects_missing_transfer_limit_and_target_fabrication(self):
        packet, transfer = self.packet_and_transfer()
        del transfer["transfer_limit"]
        with self.assertRaisesRegex(ValueError, "transfer_limit"):
            validate_architecture_transfers(
                [transfer], evidence_packet=packet, target_fact_ids={"fact-events"}
            )
        transfer = valid_transfer([row["source_id"] for row in packet["sources"]])
        transfer["target_evidence_ids"] = ["invented-target"]
        with self.assertRaisesRegex(ValueError, "unavailable target evidence"):
            validate_architecture_transfers(
                [transfer], evidence_packet=packet, target_fact_ids={"fact-events"}
            )

    def test_rejects_forecast_authority_and_same_primary_job_coercions(self):
        packet, transfer = self.packet_and_transfer()
        for field, bad_value, message in (
            ("source_outcome_is_target_forecast", 0, "source_outcome_is_target_forecast"),
            ("delivery_authority_granted", 0, "delivery_authority_granted"),
            ("same_primary_job", 0, "same_primary_job"),
        ):
            invalid = copy.deepcopy(transfer)
            invalid[field] = bad_value
            with self.assertRaisesRegex(ValueError, message):
                validate_architecture_transfers(
                    [invalid], evidence_packet=packet, target_fact_ids={"fact-events"}
                )

    def test_rejects_same_domain_and_requires_material_differences(self):
        packet, transfer = self.packet_and_transfer()
        transfer["source_domain"] = transfer["target_domain"]
        with self.assertRaisesRegex(ValueError, "same-domain"):
            validate_architecture_transfers(
                [transfer], evidence_packet=packet, target_fact_ids={"fact-events"}
            )
        transfer = valid_transfer([row["source_id"] for row in packet["sources"]])
        del transfer["material_differences"]["authority_and_data"]
        with self.assertRaisesRegex(ValueError, "authority_and_data"):
            validate_architecture_transfers(
                [transfer], evidence_packet=packet, target_fact_ids={"fact-events"}
            )


if __name__ == "__main__":
    unittest.main()
