#!/usr/bin/env python3
import unittest

from palamedes_cost_router import (
    MODE_BUDGETS,
    enforced_budget,
    infer_route_request,
    route_cycle,
)


class CostRouterTests(unittest.TestCase):
    def test_already_satisfied_routes_to_zero_call_lookup(self):
        route = route_cycle(
            {
                "objective": "Rebuild an existing feature",
                "estimated_files": 4,
                "surface_keys": ["core"],
                "risk_flags": [],
                "satisfaction": {"disposition": "already_satisfied"},
            }
        )
        self.assertEqual(route["mode"], "lookup")
        self.assertEqual(route["budget"]["provider_calls_max"], 0)

    def test_small_local_change_routes_micro(self):
        route = route_cycle(
            {
                "objective": "Fix one parser boundary",
                "estimated_files": 1,
                "surface_keys": ["parser"],
                "risk_flags": [],
            }
        )
        self.assertEqual(route["mode"], "micro")
        self.assertLessEqual(route["budget"]["provider_calls_max"], 2)

    def test_high_risk_never_routes_below_component(self):
        for risk in ("security", "payment", "migration", "storage_binding"):
            with self.subTest(risk=risk):
                route = route_cycle(
                    {
                        "objective": "Change one risky boundary",
                        "estimated_files": 1,
                        "surface_keys": ["core"],
                        "risk_flags": [risk],
                    }
                )
                self.assertIn(route["mode"], {"component", "product"})

    def test_cross_surface_and_unknown_risk_fail_closed_to_product(self):
        cross = route_cycle(
            {
                "objective": "Change mobile and realtime",
                "estimated_files": 2,
                "surface_keys": ["mobile", "realtime"],
                "risk_flags": [],
            }
        )
        unknown = route_cycle(
            {
                "objective": "Do something novel",
                "estimated_files": 1,
                "surface_keys": ["core"],
                "risk_flags": ["unclassified_future_risk"],
            }
        )
        self.assertEqual(cross["mode"], "product")
        self.assertEqual(unknown["mode"], "product")

    def test_natural_language_preflight_is_conservative_and_finds_requirement(self):
        assessment = {
            "requirement_id": "req-existing",
            "disposition": "already_satisfied",
        }
        existing = route_cycle(
            infer_route_request("Check req-existing again", [assessment])
        )
        ambiguous = route_cycle(infer_route_request("Improve the parser"))
        risky = route_cycle(infer_route_request("Change DB storage migration"))
        self.assertEqual(existing["mode"], "lookup")
        self.assertEqual(ambiguous["mode"], "component")
        self.assertIn(risky["mode"], {"component", "product"})

    def test_every_mode_declares_a_schema_retry_allowance(self):
        for mode, budget in MODE_BUDGETS.items():
            with self.subTest(mode=mode):
                ceilings = enforced_budget(budget)
                self.assertEqual(
                    ceilings["provider_calls_max"],
                    budget["provider_calls_max"]
                    + budget["schema_retry_calls_allowance"],
                )
                self.assertEqual(
                    ceilings["token_budget_high"],
                    budget["token_budget_high"]
                    + budget["schema_retry_token_allowance"],
                )
                self.assertGreater(budget["schema_retry_calls_allowance"], 0)
                self.assertGreater(budget["schema_retry_token_allowance"], 0)

    def test_component_budget_covers_measured_audit_cycles(self):
        budget = MODE_BUDGETS["component"]
        # Five-role and retry-inclusive totals measured on this repository.
        measured_roles = (120685, 125161, 135130)
        measured_totals = (145289, 147991, 160342)
        self.assertGreater(budget["token_budget_high"], max(measured_roles))
        self.assertGreater(
            enforced_budget(budget)["token_budget_high"], max(measured_totals)
        )

    def test_enforced_budget_rejects_a_malformed_allowance(self):
        with self.assertRaises(ValueError):
            enforced_budget(
                {"provider_calls_max": 5, "schema_retry_calls_allowance": -1}
            )
        with self.assertRaises(ValueError):
            enforced_budget({"provider_calls_max": "5"})


if __name__ == "__main__":
    unittest.main()
