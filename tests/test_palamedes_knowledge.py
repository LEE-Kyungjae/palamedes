#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

import palamedes_knowledge
import palamedes_thought
import palamedes_epistemics


def context():
    return {
        "observation_id": "observation-123456789abc",
        "observed_at": "2026-07-26T00:00:00+00:00",
        "documents": [
            {
                "path": "README.md",
                "content_sha256": "internal-sha",
            }
        ],
        "reference_root": {
            "repositories": [
                {
                    "name": "outside-pattern",
                    "head": "external-head",
                    "knowledge_document": {
                        "path": "/ref/outside-pattern/README.md",
                        "content_sha256": "external-sha",
                        "excerpt": "A documented external pattern",
                    },
                }
            ]
        },
        "experiences": [],
    }


def claim(
    *,
    domain,
    text,
    source,
    perspective,
    supersedes=None,
    claim_type="interpretation",
):
    return {
        "domain": domain,
        "claim_type": claim_type,
        "claim": text,
        "scope": "the currently observed product and source",
        "source_ids": [source],
        "confidence": 65,
        "valid_from": "2026-07-26T00:00:00+00:00",
        "perspective": perspective,
        "affected_stakeholders": ["current users", "people not represented"],
        "normative_assumptions": ["observed use should not define rightful use"],
        "known_exclusions": ["unobserved future users"],
        "supersedes": supersedes or [],
        "epistemic_profile": {
            "evidence_layer": "expression",
            "generality": "bounded_group",
            "salience": 40,
            "representativeness": 20,
            "relevance": 70,
            "independence": 40,
            "persistence": 20,
            "behavioral_support": 0,
            "base_rate": {
                "available": False,
                "observations": 0,
                "denominator": 0,
                "window": "",
                "source_ids": [],
            },
            "allowed_inference": "The source presents this claim",
            "forbidden_inferences": [
                "The claim is general",
                "The described practice is legitimate",
            ],
        },
    }


class PalamedesKnowledgeTests(unittest.TestCase):
    def test_temporal_claims_preserve_scope_perspective_and_unknowns(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = palamedes_knowledge.KnowledgeStore(
                Path(tempdir) / "knowledge"
            )
            result = palamedes_knowledge.persist_knowledge_updates(
                store=store,
                context=context(),
                output={
                    "knowledge_claims": [
                        claim(
                            domain="internal_product",
                            text="Users currently reuse saved outputs",
                            source="document:README.md@internal-sha",
                            perspective="the product team's documentation",
                        )
                    ],
                    "unknown_boundaries": [
                        {
                            "subject": "future users",
                            "missing_knowledge": "Their workflows are not observed",
                            "decision_consequence": "Current use cannot define the whole product",
                            "needed_source": "Research with non-users",
                            "wake_condition": "A new user segment appears",
                        }
                    ],
                },
            )

            stored = store.active_claims()[0]
            unknown = store.open_unknowns()[0]
            coverage = palamedes_epistemics.EpistemicStore(
                store.root.parent / "epistemics"
            ).load_coverage()

        self.assertEqual(len(result["claims"]), 1)
        self.assertEqual(stored["domain"], "internal_product")
        self.assertEqual(
            stored["perspective"], "the product team's documentation"
        )
        self.assertEqual(stored["known_exclusions"], ["unobserved future users"])
        self.assertEqual(stored["valid_to"], "")
        self.assertEqual(unknown["status"], "open")
        self.assertFalse(coverage["ambient_baseline_available"])
        self.assertFalse(coverage["general_population_inference_allowed"])
        self.assertIn("silent users and non-users", coverage["missing_populations"])

    def test_claim_cannot_cite_unobserved_evidence(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = palamedes_knowledge.KnowledgeStore(
                Path(tempdir) / "knowledge"
            )
            with self.assertRaisesRegex(ValueError, "unavailable source"):
                palamedes_knowledge.persist_knowledge_updates(
                    store=store,
                    context=context(),
                    output={
                        "knowledge_claims": [
                            claim(
                                domain="external_world",
                                text="The market has changed",
                                source="news:not-actually-observed",
                                perspective="unknown",
                            )
                        ],
                        "unknown_boundaries": [],
                    },
                )

    def test_salient_exposure_cannot_be_promoted_to_population_claim(self):
        viral = claim(
            domain="external_world",
            text="A conflict post was viewed widely",
            source="ref:outside-pattern@external-head",
            perspective="public posts selected by a platform",
        )
        viral["epistemic_profile"].update(
            {
                "evidence_layer": "exposure",
                "generality": "population",
                "salience": 95,
                "representativeness": 20,
                "allowed_inference": "A highly visible post exists",
                "forbidden_inferences": [
                    "The population agrees",
                    "The underlying event is common",
                ],
            }
        )
        with tempfile.TemporaryDirectory() as tempdir:
            with self.assertRaisesRegex(
                ValueError, "population claim requires"
            ):
                palamedes_knowledge.persist_knowledge_updates(
                    store=palamedes_knowledge.KnowledgeStore(
                        Path(tempdir) / "knowledge"
                    ),
                    context=context(),
                    output={
                        "knowledge_claims": [viral],
                        "unknown_boundaries": [],
                    },
                )

    def test_quiet_behavioral_baseline_can_support_population_claim(self):
        grounded_context = context()
        grounded_context["declared_surfaces"] = [
            {
                "source_id": "analytics:quiet-retention-90d",
                "origin_id": "warehouse:retention-events-v2",
                "surface_type": "analytics_baseline",
                "collection_method": "all eligible sessions over 90 days",
                "selection_process": ["eligibility rules", "event instrumentation"],
                "observed_population": "all instrumented active users",
                "missing_population": ["users blocked before instrumentation"],
                "visibility_bias": "measured behavior is visible; motives are not",
            }
        ]
        behavioral = claim(
            domain="internal_product",
            text="Three percent of eligible users quietly reuse saved outputs",
            source="analytics:quiet-retention-90d",
            perspective="instrumented user behavior",
        )
        behavioral["epistemic_profile"].update(
            {
                "evidence_layer": "behavior",
                "generality": "population",
                "salience": 10,
                "representativeness": 85,
                "behavioral_support": 90,
                "base_rate": {
                    "available": True,
                    "observations": 30,
                    "denominator": 1000,
                    "window": "90 days",
                    "source_ids": ["analytics:quiet-retention-90d"],
                },
                "allowed_inference": "3% of the instrumented eligible population reused outputs",
                "forbidden_inferences": ["The behavior explains user motives"],
            }
        )
        with tempfile.TemporaryDirectory() as tempdir:
            store = palamedes_knowledge.KnowledgeStore(
                Path(tempdir) / "knowledge"
            )
            result = palamedes_knowledge.persist_knowledge_updates(
                store=store,
                context=grounded_context,
                output={
                    "knowledge_claims": [behavioral],
                    "unknown_boundaries": [],
                },
            )

        profile = result["claims"][0]["epistemic_profile"]
        self.assertTrue(profile["base_rate"]["verified"])
        self.assertTrue(result["coverage"]["ambient_baseline_available"])

    def test_republished_sources_do_not_count_as_independent_evidence(self):
        copied_context = context()
        copied_context["declared_surfaces"] = [
            {
                "source_id": source_id,
                "origin_id": "wire:single-original-report",
                "surface_type": "news",
                "collection_method": "publisher feed",
                "selection_process": ["editor selection", "wire republication"],
                "observed_population": "published reports",
                "missing_population": ["unreported ordinary events"],
                "visibility_bias": "conflict and novelty are overvisible",
            }
            for source_id in ("news:publisher-a", "news:publisher-b")
        ]
        copied = claim(
            domain="external_world",
            text="Two publishers reported the same conflict",
            source="news:publisher-a",
            perspective="republished news coverage",
        )
        copied["source_ids"] = ["news:publisher-a", "news:publisher-b"]
        copied["epistemic_profile"]["independence"] = 100
        with tempfile.TemporaryDirectory() as tempdir:
            with self.assertRaisesRegex(
                ValueError, "distinct origin lineage"
            ):
                palamedes_knowledge.persist_knowledge_updates(
                    store=palamedes_knowledge.KnowledgeStore(
                        Path(tempdir) / "knowledge"
                    ),
                    context=copied_context,
                    output={
                        "knowledge_claims": [copied],
                        "unknown_boundaries": [],
                    },
                )

    def test_new_claim_supersedes_but_does_not_erase_old_worldview(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = palamedes_knowledge.KnowledgeStore(
                Path(tempdir) / "knowledge"
            )
            first = palamedes_knowledge.persist_knowledge_updates(
                store=store,
                context=context(),
                output={
                    "knowledge_claims": [
                        claim(
                            domain="external_world",
                            text="A practice is currently treated as normal",
                            source="ref:outside-pattern@external-head",
                            perspective="the historically dominant institution",
                        )
                    ],
                    "unknown_boundaries": [],
                },
            )["claims"][0]
            changed = claim(
                domain="external_world",
                text="Affected people contest that practice as harmful",
                source="ref:outside-pattern@external-head",
                perspective="people affected by the practice",
                supersedes=[first["knowledge_id"]],
            )
            changed["valid_from"] = "2026-08-01T00:00:00+00:00"
            second = palamedes_knowledge.persist_knowledge_updates(
                store=store,
                context=context(),
                output={
                    "knowledge_claims": [changed],
                    "unknown_boundaries": [],
                },
            )["claims"][0]
            old_record = (
                store.claims_root / f"{first['knowledge_id']}.json"
            ).read_text()

        self.assertIn('"status": "superseded"', old_record)
        self.assertIn('"valid_to": "2026-08-01T00:00:00+00:00"', old_record)
        self.assertEqual(second["supersedes"], [first["knowledge_id"]])

    def test_cross_domain_discovery_requires_both_knowledge_domains(self):
        internal = {
            "knowledge_id": "knowledge-internal1",
            "domain": "internal_product",
            "epistemic_profile": {
                "evidence_layer": "behavior",
                "generality": "bounded_group",
                "base_rate": {"available": True, "verified": True},
            },
        }
        external = {
            "knowledge_id": "knowledge-external1",
            "domain": "external_world",
            "epistemic_profile": {
                "evidence_layer": "expression",
                "generality": "bounded_group",
                "base_rate": {"available": False},
            },
        }
        discovery = {
            "connected_thought_ids": ["thought-one", "thought-two"],
            "thesis": "An external pattern may reframe retained product value",
            "old_framing": "Output creation",
            "new_framing": "Reusable judgment",
            "assumption_replaced": "Creation is the sole value",
            "changed_decision": "Measure reuse before adding breadth",
            "smallest_probe": "Measure unchanged reuse",
            "disconfirmation": "Reuse does not predict retained value",
            "why_non_obvious": "It crosses product behavior and another domain",
            "discovery_mode": "cross_domain",
            "grounding_knowledge_ids": ["knowledge-internal1"],
            "descriptive_observation": "Some users return to stored outputs",
            "normative_judgment": "Observed behavior should not define rightful access",
            "excluded_stakeholders": ["future users", "non-users"],
            "rights_risk": "Optimization may exclude people absent from current data",
            "time_sensitivity": "The user population and social expectations can change",
        }
        with tempfile.TemporaryDirectory() as tempdir:
            store = palamedes_thought.ThoughtStore(Path(tempdir))
            with self.assertRaisesRegex(
                ValueError, "requires internal and external"
            ):
                palamedes_thought.persist_discoveries(
                    store=store,
                    output={"discoveries": [discovery]},
                    available_thought_ids={"thought-one", "thought-two"},
                    available_knowledge={
                        internal["knowledge_id"]: internal,
                        external["knowledge_id"]: external,
                    },
                )

            discovery["grounding_knowledge_ids"].append("knowledge-external1")
            persisted = palamedes_thought.persist_discoveries(
                store=store,
                output={"discoveries": [discovery]},
                available_thought_ids={"thought-one", "thought-two"},
                available_knowledge={
                    internal["knowledge_id"]: internal,
                    external["knowledge_id"]: external,
                },
            )

        self.assertEqual(persisted[0]["discovery_mode"], "cross_domain")
        self.assertEqual(len(persisted[0]["grounding_knowledge_ids"]), 2)
        self.assertEqual(
            persisted[0]["promotion_state"], "cross_check_required"
        )

        discovery["promotion_state"] = "mission_eligible"
        with tempfile.TemporaryDirectory() as tempdir:
            with self.assertRaisesRegex(
                ValueError, "behavioral base-rate baseline"
            ):
                palamedes_thought.persist_discoveries(
                    store=palamedes_thought.ThoughtStore(Path(tempdir)),
                    output={"discoveries": [discovery]},
                    available_thought_ids={"thought-one", "thought-two"},
                    available_knowledge={
                        internal["knowledge_id"]: internal,
                        external["knowledge_id"]: external,
                    },
                )
        discovery["baseline_knowledge_ids"] = ["knowledge-internal1"]
        discovery["opposing_sample_knowledge_ids"] = ["knowledge-external1"]
        with tempfile.TemporaryDirectory() as tempdir:
            promoted = palamedes_thought.persist_discoveries(
                store=palamedes_thought.ThoughtStore(Path(tempdir)),
                output={"discoveries": [discovery]},
                available_thought_ids={"thought-one", "thought-two"},
                available_knowledge={
                    internal["knowledge_id"]: internal,
                    external["knowledge_id"]: external,
                },
            )
        self.assertEqual(promoted[0]["promotion_state"], "mission_eligible")


if __name__ == "__main__":
    unittest.main()
