#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

import palamedes_knowledge
import palamedes_thought


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
                {"name": "outside-pattern", "head": "external-head"}
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
    }


class PalamedesKnowledgeTests(unittest.TestCase):
    def test_temporal_claims_preserve_scope_perspective_and_unknowns(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = palamedes_knowledge.KnowledgeStore(Path(tempdir))
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

        self.assertEqual(len(result["claims"]), 1)
        self.assertEqual(stored["domain"], "internal_product")
        self.assertEqual(
            stored["perspective"], "the product team's documentation"
        )
        self.assertEqual(stored["known_exclusions"], ["unobserved future users"])
        self.assertEqual(stored["valid_to"], "")
        self.assertEqual(unknown["status"], "open")

    def test_claim_cannot_cite_unobserved_evidence(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = palamedes_knowledge.KnowledgeStore(Path(tempdir))
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

    def test_new_claim_supersedes_but_does_not_erase_old_worldview(self):
        with tempfile.TemporaryDirectory() as tempdir:
            store = palamedes_knowledge.KnowledgeStore(Path(tempdir))
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
        }
        external = {
            "knowledge_id": "knowledge-external1",
            "domain": "external_world",
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


if __name__ == "__main__":
    unittest.main()
