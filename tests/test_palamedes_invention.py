#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

from palamedes_invention import ProductInventionStore, run_product_invention


class InventionFixture:
    def __init__(self, *, empty=False, bad_assessment_id=""):
        self.calls = []
        self.empty = empty
        self.bad_assessment_id = bad_assessment_id

    def __call__(self, role, prompt):
        self.calls.append(role)
        if role == "invention_context_observer":
            return {
                "input_mode": "idea_seeded",
                "stated_intent": "make identity meaningful across the service",
                "supplied_ideas": ["profile borders"],
                "observed_facts": ["avatars appear in several contexts"],
                "inferences": ["one decoration may carry conflicting meanings"],
                "unknowns": ["which contexts need role over personality"],
                "constraints": ["do not imply permanent rank"],
                "scale": "supporting_system",
            }
        if role == "conventional_baseline_mapper":
            return {
                "expected_solutions": ["sell cosmetic borders"],
                "shared_mechanisms": ["one globally equipped decoration"],
                "dominant_assumptions": ["identity is context independent"],
                "forbidden_cosmetic_variations": ["renaming borders as auras"],
            }
        if role == "counterweighted_inventor":
            if self.empty:
                return {"candidates": [], "search_notes": ["no grounded delta"], "no_discovery_reason": "Only renamed cosmetics survived."}
            return {"candidates": [self.candidate()], "search_notes": ["shifted from decoration to contextual identity"], "no_discovery_reason": ""}
        if role == "structural_novelty_adversary":
            candidate_id = self.bad_assessment_id or "idea-1"
            return {
                "candidate_assessments": [] if self.empty else [{
                    "candidate_id": candidate_id,
                    "verdict": "survives",
                    "tests": {
                        "name_removal": "mechanism remains",
                        "compositional_emergence": "known roles, borders, and surface context combine into dynamic identity resolution unavailable from each alone",
                        "service_specificity": "depends on cross-surface role contexts",
                        "causal_coherence": "context selects the relevant identity signal",
                        "independent_contribution": "context policy was not supplied",
                    },
                    "strongest_attack": "visual overload",
                    "surviving_delta": "identity becomes contextual",
                    "evidence_gap": "role recognition accuracy",
                    "minimum_disconfirming_observation": "people misread roles more often",
                }],
                "empty_frontier_reason": "Do not manufacture novelty." if self.empty else "",
            }
        if role == "invention_frontier_curator":
            return {
                "discovery_status": "no_discovery" if self.empty else "discovered",
                "frontier": [] if self.empty else [{"candidate_id": "idea-1", "disposition": "deepen", "reason": "structural delta survived", "next_question": "Which surface needs which signal?"}],
                "synthesis": "No grounded invention." if self.empty else "Treat identity presentation as contextual policy.",
                "human_decision_required": "Choose whether to deepen the discovery.",
                "presentation_outline": ["why", "non-obvious discovery", "uncertainty"],
            }
        raise AssertionError(role)

    @staticmethod
    def candidate():
        return {
            "candidate_id": "idea-1",
            "thesis": "Identity presentation should change with the interaction context.",
            "observed_basis": ["avatars appear in chat, approval, and organization surfaces"],
            "hidden_opportunity": "use one identity policy to separate personality, authority, and status",
            "transformation_lenses": ["center_object_shift", "information_or_value_flow_change"],
            "structural_delta": {
                "baseline_structure": "one user equips one global cosmetic border",
                "proposed_structure": "the surface resolves an eligible identity signal for its context",
                "changed_dimensions": ["actors_and_authority", "information_creation_and_ownership"],
                "causal_chain": ["surface declares its identity need", "policy resolves the relevant signal", "viewer receives less ambiguous context"],
                "newly_possible_outcome": "the same person can express personality in chat and responsibility in approval without conflation",
            },
            "composition": {
                "known_components": ["profile border", "project role", "surface context"],
                "novel_relation_or_condition": "the viewing surface, rather than the user alone, participates in resolving the displayed identity signal",
                "emergent_outcome": "one identity can communicate different truthful meanings without forcing one global decoration to carry all semantics",
                "irreducibility_test": "remove contextual resolution and the result collapses back to a global cosmetic plus separate role labels",
            },
            "origin": {"type": "mixed", "palamedes_contribution": "separated contextual identity from the supplied border object"},
            "falsification_condition": "contextual signals do not improve role recognition or increase confusion",
        }


class ProductInventionTests(unittest.TestCase):
    def test_preserves_domain_general_discovery_without_selecting_or_compiling(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = InventionFixture()
            store = ProductInventionStore(Path(temporary) / "inventions")
            record = run_product_invention(ask=fixture, store=store, context="프로필 테두리를 서비스에 구축하고 싶다.")
            self.assertEqual(fixture.calls, [
                "invention_context_observer",
                "conventional_baseline_mapper",
                "counterweighted_inventor",
                "structural_novelty_adversary",
                "invention_frontier_curator",
            ])
            self.assertEqual(record["product_invention_version"], "palamedes-product-invention/2")
            self.assertEqual(len(record["candidates"]), 1)
            self.assertEqual(record["status"], "discovered")
            self.assertEqual(record["selected_candidate_id"], "")
            self.assertEqual(record["playable_contracts"], [])
            self.assertEqual(len(record["observation_requirements"]), 1)
            self.assertEqual(
                record["observation_requirements"][0]["source_candidate_id"],
                "idea-1",
            )
            self.assertTrue(record["human_commit_required"])
            self.assertFalse(record["design_authority_granted"])
            self.assertFalse(record["delivery_authority_granted"])
            self.assertEqual(
                record["candidates"][0]["composition"]["known_components"],
                ["profile border", "project role", "surface context"],
            )
            self.assertEqual(store.latest()["product_invention_id"], record["product_invention_id"])

    def test_allows_honest_no_discovery_instead_of_forcing_candidate_count(self):
        with tempfile.TemporaryDirectory() as temporary:
            record = run_product_invention(
                ask=InventionFixture(empty=True),
                store=ProductInventionStore(Path(temporary) / "inventions"),
                context="새 이름을 붙여줘.",
            )
            self.assertEqual(record["status"], "no_discovery")
            self.assertEqual(record["candidates"], [])
            self.assertEqual(record["frontier"], [])

    def test_adversary_cannot_assess_an_unoriginated_candidate(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "originated candidate"):
                run_product_invention(
                    ask=InventionFixture(bad_assessment_id="invented-by-adversary"),
                    store=ProductInventionStore(Path(temporary) / "inventions"),
                    context="Invent a service capability.",
                )

    def test_human_can_commit_only_an_existing_frontier_candidate(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = ProductInventionStore(Path(temporary) / "inventions")
            record = run_product_invention(
                ask=InventionFixture(), store=store, context="프로필 테두리를 확장하자."
            )
            commitment = store.commit("idea-1", "맥락별 정체성 방향을 더 검토한다.")
            self.assertEqual(commitment["product_invention_id"], record["product_invention_id"])
            self.assertEqual(commitment["committed_by"], "human")
            self.assertFalse(commitment["design_authority_granted"])
            self.assertFalse(commitment["delivery_authority_granted"])
            self.assertTrue((store.root / "commitments.jsonl").is_file())
            with self.assertRaisesRegex(ValueError, "existing invention candidate"):
                store.commit("idea-404", "없는 후보를 선택한다.")

    def test_disconfirmation_gap_becomes_deduplicated_resolvable_observation(self):
        with tempfile.TemporaryDirectory() as temporary:
            store = ProductInventionStore(Path(temporary) / "inventions")
            first = run_product_invention(
                ask=InventionFixture(), store=store, context="같은 탐색 문맥"
            )
            second = run_product_invention(
                ask=InventionFixture(), store=store, context="같은 탐색 문맥"
            )
            self.assertEqual(
                first["observation_requirements"][0]["observation_requirement_id"],
                second["observation_requirements"][0]["observation_requirement_id"],
            )
            self.assertEqual(len(store.open_observation_requirements()), 1)
            requirement_id = store.open_observation_requirements()[0]["observation_requirement_id"]
            resolved = store.resolve_observation_requirement(
                requirement_id, "사용자 역할 인식 비교에서 혼동이 줄었다."
            )
            self.assertEqual(resolved["status"], "resolved")
            self.assertEqual(resolved["evidence_status"], "human_report")
            self.assertFalse(resolved["authority_granted"])
            self.assertEqual(store.open_observation_requirements(), [])
            rows = (store.root / "observation-requirements.jsonl").read_text().splitlines()
            self.assertEqual(len(rows), 2)


if __name__ == "__main__":
    unittest.main()
