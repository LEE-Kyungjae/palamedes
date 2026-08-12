#!/usr/bin/env python3
"""Deterministic protocol fixtures, not evidence of autonomous model insight.

The provider below deliberately returns known-good static objects so these tests
can exercise isolation, freezing, selector custody, and positive/control routing.
Semantic capability is evaluated separately with a live provider whose outputs
are not supplied by this module.
"""

import copy
import json
import unittest
from pathlib import Path

from palamedes_cognition_v3 import (
    CROSS_DOMAIN_ARCHITECTURE_ANALOGIST,
    FAILURE_EXPERIENCED_OPERATOR,
    PRODUCT_OPPORTUNITY_INVENTOR,
    SELECTOR_ROLE,
    run_partitioned_product_cognition,
    thaw,
)
from tests.test_palamedes_cognition_v3 import CognitionFixture


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "product-cognition"
FORBIDDEN_SOLUTION_PHRASES = (
    "battle pass",
    "season pass",
    "seasonal progression",
    "seasonal track",
    "seasonal journey",
    "paid track",
    "premium track",
    "reward track",
)


def load_case(name):
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def host_packet(prompt):
    marker = "HOST_PACKET_JSON:\n"
    if marker not in prompt:
        raise AssertionError("host packet marker missing")
    return json.loads(prompt.rsplit(marker, 1)[1])


def normalized_text(value):
    if not isinstance(value, str):
        value = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return " ".join(value.lower().replace("-", " ").replace("_", " ").split())


def contains_all(value, terms):
    text = normalized_text(value)
    return all(term in text for term in terms)


def candidate_for(result, role):
    return next(row for row in result["frozen_candidates"] if row["inventor_role"] == role)


class ContractFixtureProvider:
    """Static schema fixture; it must never be reported as a semantic evaluator."""

    REQUIRED_POSITIVE_IDS = {
        "signal-repeat-behavior",
        "signal-value-capture-gap",
        "signal-mode-breadth",
    }

    def __init__(self):
        self.fixture = CognitionFixture(candidate_mutator=self._strengthen_transfer)

    @staticmethod
    def _strengthen_transfer(role, candidate, packet):
        if role != CROSS_DOMAIN_ARCHITECTURE_ANALOGIST:
            return
        mapping_record = packet["exclusive_evidence"][0]
        mapping = mapping_record["payload"]
        limits = [
            mapping["transfer_limit"],
            *mapping["non_transferable_assumptions"],
        ]
        candidate["architecture_transfer"] = {
            "source": mapping["source_domain"],
            "source_ids": [mapping_record["source_id"]],
            "pressure": mapping["source_pressure"],
            "mechanism": mapping["source_pattern"],
            "target": mapping["target_pressure"],
            "adaptation": mapping["adaptation"],
            "limits": limits,
        }
        candidate["product_mechanism"] = mapping["adaptation"]
        candidate["product_opportunity_lineage"]["mechanism"] = mapping[
            "adaptation"
        ]
        candidate["failure_basis"]["transfer_limit"] = limits[0]

    def _record_and_abstain(self, role, prompt):
        packet = host_packet(prompt)
        self.fixture.calls.append(role)
        self.fixture.prompts.append((role, prompt))
        self.fixture.packets.append((role, copy.deepcopy(packet)))
        return {
            "status": "abstain",
            "abstention": {
                "reason": "The bounded evidence does not support a durable repeat-use opportunity.",
                "missing_evidence": "Observed returning behavior, persistent account value, and operating capacity.",
                "wake_condition": "Reconsider only after those product signals are observed.",
            },
        }

    def __call__(self, role, prompt):
        packet = host_packet(prompt)
        if role == PRODUCT_OPPORTUNITY_INVENTOR:
            exclusive_ids = {
                row["source_id"] for row in packet.get("exclusive_evidence", [])
            }
            if not self.REQUIRED_POSITIVE_IDS.issubset(exclusive_ids):
                return self._record_and_abstain(role, prompt)
        if role == SELECTOR_ROLE:
            self.fixture.selector_mode = (
                "commit" if packet["sanitized_frozen_candidates"] else "defer"
            )
        return self.fixture(role, prompt)


def run_case(case):
    provider = ContractFixtureProvider()
    result = run_partitioned_product_cognition(
        ask=provider,
        common_evidence=case["common_evidence"],
        partitions=case["partitions"],
        constitution=case["constitution"],
    )
    return provider, thaw(result)


def positive_rubric(result):
    product = candidate_for(result, PRODUCT_OPPORTUNITY_INVENTOR)
    architecture = candidate_for(result, CROSS_DOMAIN_ARCHITECTURE_ANALOGIST)
    failure = candidate_for(result, FAILURE_EXPERIENCED_OPERATOR)
    spontaneous = product["spontaneous_opportunity"]
    business = product["business_effect"]
    burden = product["operating_burden"]
    probe = product["action_probe"]
    boundary = product["authority"]
    second_order = product["second_order_effects"]
    source_ids = set(product["product_opportunity_lineage"]["source_signal_ids"])
    transfer = architecture["architecture_transfer"]
    failure_basis = failure["failure_basis"]

    return {
        "grounded_in_product_signals": {
            "fact-activity-events",
            "fact-appearance-entitlements",
            "fact-account-history-gap",
            "fact-content-capacity",
            "fact-fairness-boundary",
            "signal-repeat-behavior",
            "signal-value-capture-gap",
            "signal-mode-breadth",
        }.issubset(source_ids),
        "unasked_time_bounded_progression": (
            contains_all(spontaneous["unasked_opportunity"], ("seasonal", "journey"))
            and contains_all(product["product_mechanism"], ("seasonal", "track"))
        ),
        "behavior_change_is_return_and_choice": contains_all(
            product["behavior_change"], ("return", "modes")
        ),
        "business_effect_is_optional_repeat_revenue": contains_all(
            business["revenue_or_value_effect"],
            ("optional", "paid", "recurring", "revenue"),
        ),
        "causal_chain_has_multiple_hops": len(business["causal_chain"]) >= 2,
        "fairness_boundary_separates_payment_from_power": contains_all(
            spontaneous["product_boundary"], ("competition", "payment")
        ),
        "second_order_mode_crowding_is_explicit": any(
            row["valence"] in {"risk", "mixed"}
            and contains_all(row["early_signal"], ("mode diversity", "falls"))
            for row in second_order
        ),
        "operating_burden_has_owner_cadence_and_capacity": all(
            burden[field]
            for field in (
                "recurring_work",
                "owner",
                "cadence",
                "capacity_or_cost_limit",
                "failure_mode",
            )
        ),
        "authority_blocks_unapproved_paid_launch": contains_all(
            boundary["prohibited_without_authority"], ("paid", "launch")
        ),
        "probe_reaches_reversible_behavior": (
            probe["kind"] == "behavioral_exposure"
            and probe["reversible"] is True
            and probe["terminal_output_kind"] == "observed_actor_response"
            and contains_all(probe["intervention"], ("optional", "free", "cohort"))
            and contains_all(probe["metric"], ("return", "mode diversity"))
            and bool(probe["falsifier"])
            and bool(probe["rollback"])
            and bool(probe["stop_condition"])
        ),
        "failure_boundary_is_direct_and_bounded": (
            failure_basis["basis_type"] == "direct"
            and failure_basis["source_ids"] == ["failure-narrow-daily-goals"]
            and contains_all(
                failure["failure_earned_boundary"]["guardrail"],
                ("mode diversity",),
            )
        ),
        "architecture_transfer_is_mechanism_complete": (
            transfer["source_ids"] == ["validated-transfer-workflow-history"]
            and contains_all(
                transfer["adaptation"],
                (
                    "immutable activity facts",
                    "idempotency key",
                    "immutable version",
                    "active version pointer",
                    "rebuild",
                    "rollback",
                ),
            )
            and any("does not prove player demand" in item.lower() for item in transfer["limits"])
        ),
        "host_surfaces_a_bounded_result": (
            result["host_issued_result"]["result_kind"] == "draft"
            and result["host_issued_result"]["issued_by"] == "product_cognition_host"
        ),
    }


class ProductCognitionContractFixtureTests(unittest.TestCase):
    def test_static_fixture_and_actual_product_prompt_do_not_name_the_answer(self):
        case = load_case("case-pc-001.input.json")
        visible_input = {
            "request": case["request"],
            "constitution": case["constitution"],
            "common_evidence": case["common_evidence"],
            "exclusive_evidence": case["partitions"][PRODUCT_OPPORTUNITY_INVENTOR],
        }
        provider, _ = run_case(case)
        product_prompt = next(
            prompt
            for role, prompt in provider.fixture.prompts
            if role == PRODUCT_OPPORTUNITY_INVENTOR
        )
        for surface in (visible_input, product_prompt):
            normalized = normalized_text(surface)
            for forbidden in FORBIDDEN_SOLUTION_PHRASES:
                with self.subTest(surface=type(surface).__name__, forbidden=forbidden):
                    self.assertNotIn(forbidden, normalized)

    def test_static_outputs_survive_the_full_product_contract(self):
        case = load_case("case-pc-001.input.json")
        _, first = run_case(case)
        _, second = run_case(case)
        self.assertEqual(
            first["audit"]["candidate_set_fingerprint"],
            second["audit"]["candidate_set_fingerprint"],
        )
        checks = positive_rubric(first)
        for name, passed in checks.items():
            with self.subTest(rubric=name):
                self.assertTrue(passed)

    def test_control_routes_to_host_abstention_without_a_candidate(self):
        positive = load_case("case-pc-001.input.json")
        control = load_case("case-pc-001.control.json")
        _, positive_result = run_case(positive)
        control_provider, control_result = run_case(control)

        self.assertTrue(all(positive_rubric(positive_result).values()))
        self.assertEqual(control_result["frozen_candidates"], [])
        self.assertEqual(control_result["host_issued_result"]["result_kind"], "defer")
        self.assertEqual(
            [row["reason_code"] for row in control_result["abstentions"]],
            [
                "inventor_abstention",
                "no_validated_cross_domain_evidence",
                "no_adverse_evidence",
            ],
        )
        self.assertIn(PRODUCT_OPPORTUNITY_INVENTOR, control_provider.fixture.calls)
        serialized = normalized_text(control_result)
        for forbidden in FORBIDDEN_SOLUTION_PHRASES:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, serialized)


if __name__ == "__main__":
    unittest.main()
