#!/usr/bin/env python3

import json
import tempfile
import unittest
from pathlib import Path

from palamedes_observe import collect_observation
from palamedes_reference_intelligence import (
    ReferenceIntelligenceStore,
    run_reference_intelligence,
)


class StaticProvider:
    provider_name = "static"
    model = "fixture"

    def __init__(self, *, comparative=False, unsupported=False):
        self.comparative = comparative
        self.unsupported = unsupported

    def stream(self, messages):
        source_id = (
            "external-reference-1" if self.comparative else "workspace-document-1"
        )
        yield json.dumps(
            {
                "self_model": {
                    "capabilities": [
                        {
                            "claim": "The workspace records bounded evidence.",
                            "evidence_source_ids": ["workspace-document-1"],
                            "confidence": 78,
                        }
                    ],
                    "unknowns": ["External adoption evidence is absent."],
                },
                "hypotheses": [
                    {
                        "kind": (
                            "complement"
                            if self.comparative or self.unsupported
                            else "knowledge_gap"
                        ),
                        "claim": "An adjacent comparison may expose a missing runtime boundary.",
                        "supporting_source_ids": [source_id],
                        "missing_evidence": "No controlled comparison has run.",
                        "falsifier": "The compared runtime boundary is already present.",
                        "exploration_value": 72,
                    }
                ],
                "selected_agenda": {
                    "status": "selected",
                    "prompt": "Compare one bounded runtime boundary without changing code.",
                    "rationale": "The answer can change research direction.",
                    "grounding_source_ids": [source_id],
                    "external_research_required": not self.comparative,
                    "stop_conditions": ["No attributable difference exists."],
                },
            }
        )


class ReferenceIntelligenceTests(unittest.TestCase):
    def _workspace(self, root):
        workspace = root / "workspace"
        workspace.mkdir()
        (workspace / "README.md").write_text(
            "# Product\nBounded evidence and missions.\n", encoding="utf-8"
        )
        return workspace

    def test_workspace_only_mode_emits_knowledge_gap_without_reference_requirement(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            workspace = self._workspace(root)
            snapshot = collect_observation(workspace, persist=False)
            store = ReferenceIntelligenceStore(root / "intelligence")
            record = run_reference_intelligence(
                provider=StaticProvider(), store=store, snapshot=snapshot
            )

            self.assertEqual(record["reference_mode"], "workspace_only")
            self.assertEqual(record["hypotheses"][0]["kind"], "knowledge_gap")
            self.assertTrue(
                record["selected_agenda"]["external_research_required"]
            )
            self.assertFalse(record["selected_agenda"]["delivery_authority_granted"])
            self.assertEqual(len(store.active_agendas()), 1)

    def test_optional_reference_produces_source_bounded_comparison(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            workspace = self._workspace(root)
            references = root / "references"
            project = references / "runtime-project"
            project.mkdir(parents=True)
            (project / "README.md").write_text(
                "# Runtime\nMulti-session isolation.\n", encoding="utf-8"
            )
            snapshot = collect_observation(
                workspace, ref_root=references, persist=False
            )
            record = run_reference_intelligence(
                provider=StaticProvider(comparative=True),
                store=ReferenceIntelligenceStore(root / "intelligence"),
                snapshot=snapshot,
            )

            self.assertEqual(
                record["reference_mode"], "workspace_plus_optional_references"
            )
            self.assertEqual(record["hypotheses"][0]["kind"], "complement")
            self.assertEqual(
                record["selected_agenda"]["grounding_source_ids"],
                ["external-reference-1"],
            )

    def test_workspace_only_mode_rejects_unsupported_comparative_claim(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            workspace = self._workspace(root)
            snapshot = collect_observation(workspace, persist=False)
            with self.assertRaisesRegex(ValueError, "knowledge_gap"):
                run_reference_intelligence(
                    provider=StaticProvider(unsupported=True),
                    store=ReferenceIntelligenceStore(root / "intelligence"),
                    snapshot=snapshot,
                )


if __name__ == "__main__":
    unittest.main()
