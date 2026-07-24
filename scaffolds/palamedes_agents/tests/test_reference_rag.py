#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path


SCAFFOLD_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = SCAFFOLD_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from palamedes_agents.reference_rag import build_reference_rag_context, normalize_reference_pattern, retrieve_reference_context, validate_reference_grounding


CORPUS = [
    {
        "reference_id": "success-activation",
        "source": "Activation case",
        "source_url": "https://example.com/activation",
        "source_type": "success_case",
        "context": "Solo builders evaluating product ideas before coding",
        "problem": "Generic product ideas consume build time",
        "mechanism": "A decision checkpoint exposes weak demand before implementation",
        "outcome": "Builders abandon weak ideas earlier",
        "failure_boundary": "Fails when the user has no concrete product hypothesis",
        "evidence_quotes": ["Teams stopped weak ideas before implementation."],
        "applicable_axes": ["direction", "differentiation"],
        "confidence": 82,
    },
    {
        "reference_id": "failure-dashboard",
        "source": "Dashboard failure review",
        "source_type": "failure_case",
        "context": "AI product strategy dashboards",
        "problem": "Users receive generic advice",
        "mechanism": "Feature summaries replace product judgment",
        "outcome": "Users do not return after the first report",
        "failure_boundary": "A dashboard can work when monitoring is the primary job",
        "evidence_quotes": [],
        "applicable_axes": ["risk_signal", "differentiation"],
        "confidence": 70,
    },
    {
        "reference_id": "counter-speed",
        "source": "Speed-first counterargument",
        "source_type": "counter_view",
        "context": "Experienced teams with cheap experiments",
        "problem": "Planning gates can delay learning",
        "mechanism": "Ship a reversible experiment instead of extending analysis",
        "outcome": "Behavior evidence arrives sooner",
        "failure_boundary": "Unsafe when implementation is expensive or irreversible",
        "evidence_quotes": [],
        "applicable_axes": ["constraint", "timing"],
        "confidence": 65,
    },
]


class ReferenceRagTests(unittest.TestCase):
    def test_normalize_reference_pattern_preserves_provenance(self):
        pattern = normalize_reference_pattern(CORPUS[0])
        self.assertEqual(pattern["reference_id"], "success-activation")
        self.assertEqual(pattern["source_url"], "https://example.com/activation")
        self.assertEqual(pattern["evidence_quotes"][0], "Teams stopped weak ideas before implementation.")

    def test_retrieval_selects_multiple_viewpoints_and_passes_gate(self):
        result = retrieve_reference_context("generic product ideas builders differentiation implementation", CORPUS)
        self.assertEqual(result["quality_gate"]["status"], "sufficient")
        self.assertGreaterEqual(len(result["source_types"]), 2)
        ids = {item["reference_id"] for item in result["patterns"]}
        self.assertIn("success-activation", ids)
        self.assertIn("failure-dashboard", ids)
        self.assertTrue(all(item["retrieval_score"] > 0 for item in result["patterns"]))

    def test_retrieval_stops_when_evidence_is_too_thin(self):
        result = retrieve_reference_context("generic product ideas", [CORPUS[1]])
        self.assertEqual(result["quality_gate"]["status"], "insufficient")
        self.assertEqual(result["quality_gate"]["recommended_decision"], "stop_and_research")
        self.assertIn("insufficient_viewpoint_diversity", result["quality_gate"]["reasons"])
        self.assertIn("missing_citable_evidence", result["quality_gate"]["reasons"])

    def test_payload_context_builds_strategy_ready_retrieval(self):
        context = build_reference_rag_context(
            {
                "idea": "Prevent solo builders from shipping generic product ideas",
                "target_user": "solo builders",
                "reference_corpus": CORPUS,
            }
        )
        self.assertEqual(context["corpus_size"], 3)
        self.assertIn("quality_gate", context)
        self.assertIn("patterns", context)

    def test_grounding_rejects_lost_provenance(self):
        retrieval = retrieve_reference_context("generic product ideas builders differentiation implementation", CORPUS)
        report = {
            "decision": "continue",
            "reference_insights": [
                {
                    "reference_ids": ["success-activation"],
                    "source_urls": [],
                    "evidence_quotes": [],
                }
            ],
        }
        errors = validate_reference_grounding(report, retrieval)
        self.assertIn("reference_insights[0] does not preserve cited source URLs", errors)
        self.assertIn("reference_insights[0] does not preserve cited evidence quotes", errors)

    def test_semantic_scores_can_augment_bm25_ranking(self):
        result = retrieve_reference_context(
            "generic product ideas",
            CORPUS,
            semantic_scores={"counter-speed": 50.0},
        )
        self.assertEqual(result["retrieval_method"], "hybrid_bm25_semantic_with_type_diversity")
        self.assertEqual(result["patterns"][0]["reference_id"], "counter-speed")


if __name__ == "__main__":
    unittest.main()
