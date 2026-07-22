#!/usr/bin/env python3
import copy
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Dict


REPO_ROOT = Path(__file__).resolve().parents[3]
SCAFFOLD_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = SCAFFOLD_ROOT / "src"
for path in [REPO_ROOT, SRC_ROOT]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import deepplan
from deepplan_agents.adapters.deepplan_adapter import DeepPlanAdapter
from deepplan_agents.bootstrap import ClientConfig, build_client
from deepplan_agents.insight_persistence import insight_write_payload, persist_reference_insights
from deepplan_agents.reference_rag import build_reference_rag_context
from deepplan_agents.reference_store import ReferenceStore
from deepplan_agents.strategy_llm import StaticStrategyProvider, run_strategy_llm
from scaffolds.deepplan_agents.tests.test_strategy_llm import VALID_REPORT


class DeepPlanStateIsolation:
    def __init__(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.originals: Dict[str, Any] = {}

    def __enter__(self):
        for name in ["ROOT", "STATE_DIR", "PLAN_PATH", "DECISIONS_PATH", "RISKS_PATH", "EVENTS_PATH", "REVISIONS_PATH"]:
            self.originals[name] = getattr(deepplan, name)
        deepplan.ROOT = self.root
        deepplan.STATE_DIR = self.root / ".deeplan"
        deepplan.PLAN_PATH = deepplan.STATE_DIR / "plan.json"
        deepplan.DECISIONS_PATH = deepplan.STATE_DIR / "decisions.jsonl"
        deepplan.RISKS_PATH = deepplan.STATE_DIR / "risks.jsonl"
        deepplan.EVENTS_PATH = deepplan.STATE_DIR / "events.jsonl"
        deepplan.REVISIONS_PATH = deepplan.STATE_DIR / "revisions.jsonl"
        deepplan._sync_store_paths()
        deepplan.ensure_state()
        return self

    def __exit__(self, exc_type, exc, tb):
        for name, value in self.originals.items():
            setattr(deepplan, name, value)
        deepplan._sync_store_paths()
        self.tempdir.cleanup()


class InsightPersistenceTests(unittest.TestCase):
    def test_payload_preserves_reference_provenance_and_disconfirmation(self):
        payload = insight_write_payload(VALID_REPORT["reference_insights"][0])
        self.assertEqual(payload["evidence"]["evidence_type"], "reference_extraction")
        self.assertEqual(payload["evidence"]["source_url"], "https://example.com/failed-ai-wrapper-launches")
        self.assertIn("Disconfirming signal", payload["evidence"]["note"])
        self.assertTrue(payload["idempotency_key"].startswith("reference-insight-"))

    def test_persist_reference_insights_updates_core_state_idempotently(self):
        with DeepPlanStateIsolation():
            adapter = DeepPlanAdapter(build_client(ClientConfig(mode="in-process")), require_healthy_writes=False)
            report = copy.deepcopy(VALID_REPORT)
            first = persist_reference_insights(adapter, report)
            second = persist_reference_insights(adapter, report)

            self.assertEqual(first["applied_count"], 1)
            evidence = second["post_cycle"]["plan"]["evidence"]
            matching = [item for item in evidence if isinstance(item, dict) and item.get("evidence_type") == "reference_extraction"]
            self.assertEqual(len(matching), 1)
            self.assertIn(report["reference_insights"][0]["transferable_principle"], second["post_cycle"]["plan"]["insights"])

    def test_store_retrieval_strategy_and_core_persistence_e2e(self):
        with DeepPlanStateIsolation() as isolated:
            store_path = isolated.root / "references.sqlite3"
            ReferenceStore(store_path).ingest(
                [
                    {
                        "reference_id": "s1",
                        "source": "Success case",
                        "source_url": "https://example.com/s1",
                        "source_type": "success_case",
                        "problem": "generic product ideas waste implementation time",
                        "mechanism": "pre-build decision gate",
                        "evidence_quotes": ["Weak ideas stopped before implementation."],
                    },
                    {
                        "reference_id": "f1",
                        "source": "Failure case",
                        "source_type": "failure_case",
                        "problem": "generic product ideas produce dashboard advice",
                        "mechanism": "features replace evidence",
                    },
                ]
            )
            payload = {
                "idea": "prevent generic product ideas before implementation",
                "reference_store_path": str(store_path),
                "reference_semantic_scores": {"s1": 0.9, "f1": 0.4},
            }
            retrieval = build_reference_rag_context(payload)
            self.assertEqual(retrieval["quality_gate"]["status"], "sufficient")
            self.assertEqual(retrieval["retrieval_method"], "hybrid_bm25_semantic_with_type_diversity")

            report = copy.deepcopy(VALID_REPORT)
            insight = report["reference_insights"][0]
            insight["source"] = "Success case"
            insight["reference_ids"] = ["s1"]
            insight["source_urls"] = ["https://example.com/s1"]
            insight["evidence_quotes"] = ["Weak ideas stopped before implementation."]
            generated = run_strategy_llm(StaticStrategyProvider(report), payload=payload, snapshot={})

            adapter = DeepPlanAdapter(build_client(ClientConfig(mode="in-process")), require_healthy_writes=False)
            persisted = persist_reference_insights(adapter, generated["report"])
            self.assertEqual(persisted["applied_count"], 1)
            self.assertEqual(persisted["post_cycle"]["plan"]["evidence"][-1]["reference"], "s1")


if __name__ == "__main__":
    unittest.main()
