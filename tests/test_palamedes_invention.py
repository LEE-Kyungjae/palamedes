#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

from palamedes_invention import PLAYABLE_FIELDS, STRUCTURAL_AXES, ProductInventionStore, run_product_invention


class InventionFixture:
    def __init__(self, selected_id="world-3"):
        self.calls, self.selected_id = [], selected_id

    def __call__(self, role, prompt):
        self.calls.append(role)
        if role == "affect_dependency_mapper":
            return {"desired_emotions": ["team pride"], "uncomfortable_emotions": ["rivalry"], "social_dependencies": ["partners expose different strengths"], "explicitly_supplied_mechanics": ["online yut game"]}
        if role == "genre_rule_inventor":
            return {"candidates": [self.candidate(i) for i in range(1, 6)]}
        if role == "playable_contract_compiler":
            return {"playable_contracts": [self.contract(i) for i in range(1, 6)]}
        if role == "invention_adversary":
            return {"candidate_assessments": [{"candidate_id": f"world-{i}", "possibility": "open", "investment": "test", "attack": f"risk {i}"} for i in range(1, 6)], "minimum_disconfirming_probe": "ten-minute blind paper match"}
        if role == "invention_selector":
            return {"decision": "probe", "selected_candidate_id": self.selected_id, "rationale": "strong social dependency", "candidate_fates": [{"candidate_id": f"world-{i}", "fate": "probe" if i == 3 else "incubate"} for i in range(1, 6)], "smallest_prototype": "Four people play two rounds with cards and six tokens.", "provenance": {"origin": "mixed", "decisive_seed": "partner dependency", "palamedes_contribution": "originated", "conceptual_distance": "victory and agency restructured", "would_exist_without_user_seed": False, "derivation_trace": ["online yut", "shared uncertainty", "asymmetric partners"]}}
        raise AssertionError(role)

    @staticmethod
    def candidate(index):
        return {"candidate_id": f"world-{index}", "concept": f"Distant world {index}", "core_tension": f"tension {index}", "harm_boundary": "no coercive monetization", "conceptual_distance": f"axis set {index}", "independently_originated_mechanics": [f"mechanic-{index}"], "derivation_trace": ["emotion", f"rule-{index}"], "structural_mechanics": {axis: f"{axis}-{index}" for axis in STRUCTURAL_AXES}}

    @staticmethod
    def contract(index):
        row = {field: f"{field}-{index}" for field in PLAYABLE_FIELDS}
        row.update({"candidate_id": f"world-{index}", "allowed_actions": ["choose", "counter"], "resources": ["pieces"], "exploit_risks": ["kingmaking"]})
        return row


class ProductInventionTests(unittest.TestCase):
    def test_originates_playable_candidates_with_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = InventionFixture()
            store = ProductInventionStore(Path(temporary) / "inventions")
            record = run_product_invention(ask=fixture, store=store, context="Increase repeat play and team immersion in online yut.")
            self.assertEqual(fixture.calls, ["affect_dependency_mapper", "genre_rule_inventor", "playable_contract_compiler", "invention_adversary", "invention_selector"])
            self.assertEqual(len(record["candidates"]), 5)
            self.assertEqual(len(record["playable_contracts"]), 5)
            self.assertEqual(record["selected_candidate_id"], "world-3")
            self.assertEqual(record["provenance"]["origin"], "mixed")
            self.assertFalse(record["delivery_authority_granted"])
            self.assertEqual(store.latest()["product_invention_id"], record["product_invention_id"])

    def test_selector_cannot_smuggle_in_new_candidate(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "existing candidate"):
                run_product_invention(ask=InventionFixture("new-world"), store=ProductInventionStore(Path(temporary) / "inventions"), context="Invent a game.")


if __name__ == "__main__":
    unittest.main()
