#!/usr/bin/env python3
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from palamedes_cognition_v3 import (
    BLINDED_ADVERSARY_ROLE,
    CROSS_DOMAIN_ARCHITECTURE_ANALOGIST,
    FAILURE_EXPERIENCED_OPERATOR,
    INVENTOR_ROLES,
    PRODUCT_OPPORTUNITY_INVENTOR,
    SELECTOR_ROLE,
    partition_cognition_evidence_bundle,
    run_partitioned_product_cognition,
    thaw,
)
from palamedes_chat import (
    CognitionCycleStore,
    MissionStore,
    approve_mission,
    run_partitioned_product_cycle,
)
from palamedes_evidence_bundle import build_cognition_evidence_bundle
from palamedes_product_alignment import ProductAlignmentStore
from tests.test_palamedes_architecture_transfer import collect_packet


def evidence_partitions(*, failure=True, failure_status="failure"):
    return {
        PRODUCT_OPPORTUNITY_INVENTOR: [
            {
                "source_id": "signal-return-gap",
                "evidence_kind": "telemetry",
                "observation": "Players return for matches but have no cross-session progress.",
            }
        ],
        CROSS_DOMAIN_ARCHITECTURE_ANALOGIST: [
            {
                "source_id": "mapping-ledger-projection",
                "kind": "cross_domain_architecture_transfer",
                "status": "candidate",
                "epistemic_class": "hypothesis",
                "decision_authority": "advisory",
                "delivery_authority_granted": False,
                "payload": {
                    "transfer_contract_version": "palamedes-architecture-transfer/2",
                    "source_domain": "append-only financial ledgers",
                    "source_pressure": (
                        "Duplicate, late, and corrected events must not corrupt balances."
                    ),
                    "source_pattern": (
                        "Immutable facts plus idempotent, rebuildable projections"
                    ),
                    "target_pressure": (
                        "Seasonal progress and reward entitlement state must survive retries."
                    ),
                    "adaptation": (
                        "Use match IDs as idempotency keys and rebuild season views from facts."
                    ),
                    "transfer_limit": (
                        "Ledger correctness does not prove the reward loop is enjoyable."
                    ),
                    "non_transferable_assumptions": [
                        "Do not copy financial compliance complexity into the game wholesale."
                    ],
                    "same_primary_job": False,
                    "source_outcome_is_target_forecast": False,
                    "authority": "mechanism_candidate_only",
                    "decision_authority_granted": False,
                    "design_authority_granted": False,
                    "selection_authority_granted": False,
                    "delivery_authority_granted": False,
                    "code_reuse_authority_granted": False,
                },
            }
        ],
        FAILURE_EXPERIENCED_OPERATOR: (
            [
                {
                    "source_id": "failure-daily-quest",
                    "outcome_status": failure_status,
                    "observed_outcome": "A narrow daily quest raised completion but reduced mode diversity.",
                }
            ]
            if failure
            else []
        ),
    }


def common_evidence():
    return [
        {
            "source_id": "game-event-stream",
            "evidence_kind": "capability",
            "epistemic_class": "direct_observation",
            "decision_authority": "mission_citable",
            "observation": "Completed matches already emit player, mode, and result events.",
        }
    ]


def record_substantive_product_fact(state_root):
    ProductAlignmentStore(Path(state_root) / "product-alignment").record_capability(
        capability_id="capability-repeat-events",
        statement="Repeat activity events are already available for bounded cohorts.",
        source_ids=["host-observation-repeat-events"],
    )


def _packet(prompt):
    marker = "HOST_PACKET_JSON:\n"
    if marker not in prompt:
        raise AssertionError("host packet marker missing")
    return json.loads(prompt.rsplit(marker, 1)[1])


def _decision_details(mode):
    if mode == "commit":
        return {
            "commitment_scope": "Draft only; no implementation or launch authority.",
            "review_trigger": "Review after the bounded action probe.",
        }
    if mode == "bounded_exploration":
        return {
            "exploration_budget": "Two product days and one telemetry query.",
            "expires_when": "The first cohort readout is available.",
            "learning_objective": "Estimate return lift without mode crowding.",
            "stop_condition": "Stop if instrumentation or content cost exceeds the cap.",
        }
    if mode == "discriminating_probe":
        return {
            "ambiguity": "Whether the value comes from progression or event reliability.",
            "probe": "Expose two separately instrumented variants.",
            "metric": "Return rate, mode diversity, and projection corrections.",
            "budget": "One bounded cohort for two weeks.",
            "maximum_harm": "No paid exposure and no competitive advantage.",
            "stop_condition": "Stop on fairness complaints or mode concentration.",
        }
    return {
        "missing_condition": "No qualified, bounded product move remains.",
        "wake_trigger": "New observed product or adverse evidence arrives.",
        "review_at": "At the next evidence refresh.",
    }


class CognitionFixture:
    def __init__(
        self,
        *,
        candidate_mutator=None,
        disqualify_titles=(),
        selector_mode="commit",
        select_disqualified=False,
        mutate_selector_copy=False,
    ):
        self.calls = []
        self.prompts = []
        self.packets = []
        self.candidate_mutator = candidate_mutator
        self.disqualify_titles = set(disqualify_titles)
        self.selector_mode = selector_mode
        self.select_disqualified = select_disqualified
        self.mutate_selector_copy = mutate_selector_copy

    def __call__(self, role, prompt):
        packet = _packet(prompt)
        self.calls.append(role)
        self.prompts.append((role, prompt))
        self.packets.append((role, copy.deepcopy(packet)))
        if role in INVENTOR_ROLES:
            candidate = self.candidate(role, packet)
            if self.candidate_mutator is not None:
                self.candidate_mutator(role, candidate, packet)
            return {"status": "candidate", "candidate": candidate}
        if role == BLINDED_ADVERSARY_ROLE:
            title = packet["candidate"]["title"]
            verdict = "disqualified" if title in self.disqualify_titles else "qualified"
            return {
                "review_subject_id": packet["review_subject_id"],
                "verdict": verdict,
                "disqualification_reasons": (
                    ["The proposed mechanism exceeds the stated authority boundary."]
                    if verdict == "disqualified"
                    else []
                ),
                "constitutional_tension": "No fatal tension after applying the stated authority boundary.",
                "causal_weakness": "Retention causality could be confounded by novelty.",
                "business_viability_attack": "Content cost may exceed incremental value.",
                "second_order_risk": "Extrinsic rewards may crowd out preferred modes.",
                "operating_failure_mode": "Seasonal ownership may become an unfunded obligation.",
                "probe_weakness": "A short window may overestimate durable return behavior.",
                "strongest_surviving_case": "The event seam permits a reversible real-user test.",
            }
        if role == SELECTOR_ROLE:
            candidates = packet["sanitized_frozen_candidates"]
            critiques = packet["sanitized_blinded_critiques"]
            if self.mutate_selector_copy and candidates:
                candidates[0]["content"]["title"] = "selector-authored mutation"
                candidates[0]["content"]["product_mechanism"] = "selector rewrite"
            qualified = {
                row["candidate_id"]
                for row in critiques
                if row["verdict"] == "qualified"
            }
            disqualified = [
                row["candidate_id"]
                for row in critiques
                if row["verdict"] == "disqualified"
            ]
            if self.select_disqualified:
                selected = disqualified[:1]
            elif self.selector_mode == "commit":
                selected = [next(row["candidate_id"] for row in candidates if row["candidate_id"] in qualified)]
            elif self.selector_mode == "bounded_exploration":
                selected = [next(row["candidate_id"] for row in candidates if row["candidate_id"] in qualified)]
            elif self.selector_mode == "discriminating_probe":
                selected = [
                    row["candidate_id"]
                    for row in candidates
                    if row["candidate_id"] in qualified
                ][:2]
            else:
                selected = []
            return {
                "mode": self.selector_mode,
                "selected_candidate_ids": selected,
                "rationale": "Use only qualified frozen substance and its blinded attacks.",
                "unresolved_conflicts": ["Durable value and ongoing content cost remain uncertain."],
                "decision_details": _decision_details(self.selector_mode),
            }
        raise AssertionError(role)

    @staticmethod
    def candidate(role, packet):
        allowed = list(packet["allowed_source_ids"])
        exclusive = [row["source_id"] for row in packet["exclusive_evidence"]]
        mechanism = {
            PRODUCT_OPPORTUNITY_INVENTOR: (
                "A free seasonal track credits healthy play across modes before a paid track is tested."
            ),
            CROSS_DOMAIN_ARCHITECTURE_ANALOGIST: (
                "Use match IDs as idempotency keys and rebuild season views from facts."
            ),
            FAILURE_EXPERIENCED_OPERATOR: (
                "Let broad outcome goals earn progress while capping narrow daily pressure."
            ),
        }[role]
        behavior = {
            PRODUCT_OPPORTUNITY_INVENTOR: "Players gain a cross-session reason to return and explore modes.",
            CROSS_DOMAIN_ARCHITECTURE_ANALOGIST: "Players trust progress despite retries, corrections, and late events.",
            FAILURE_EXPERIENCED_OPERATOR: "Players can progress without concentrating into one rewarded mode.",
        }[role]
        revenue = {
            PRODUCT_OPPORTUNITY_INVENTOR: "A validated optional paid track can create recurring seasonal revenue.",
            CROSS_DOMAIN_ARCHITECTURE_ANALOGIST: "Reliable entitlement state reduces support loss and protects paid-season trust.",
            FAILURE_EXPERIENCED_OPERATOR: "Preserving mode diversity protects retention while seasonal value is monetized.",
        }[role]
        title = {
            PRODUCT_OPPORTUNITY_INVENTOR: "Cross-mode seasonal journey",
            CROSS_DOMAIN_ARCHITECTURE_ANALOGIST: "Ledger-grade progression projection",
            FAILURE_EXPERIENCED_OPERATOR: "Choice-preserving progression boundary",
        }[role]
        if role == FAILURE_EXPERIENCED_OPERATOR:
            claim_ids = [allowed[0], packet["adverse_source_ids"][0]]
            failure_basis = {
                "basis_type": "direct",
                "source_ids": [packet["adverse_source_ids"][0]],
                "lesson": "Completion can rise while the healthier ecosystem signal deteriorates.",
                "missing_viability_condition": "Progress goals must preserve meaningful mode choice.",
                "guardrail": "Cap narrow task pressure and stop on material diversity loss.",
                "transfer_limit": "One failed daily loop does not prove all seasonal progression is harmful.",
            }
        else:
            claim_ids = list(allowed)
            failure_basis = {
                "basis_type": "no_signal",
                "source_ids": [],
                "lesson": "No failure-earned claim is available in this evidence slice.",
                "missing_viability_condition": "Durable behavior and operating economics remain unverified.",
                "guardrail": "Use a reversible unpaid probe before commitment.",
                "transfer_limit": "Inference does not establish willingness to pay or long-run retention.",
            }
        candidate = {
            "output_kind": "product_opportunity",
            "title": title,
            "opportunity_thesis": f"{title} converts an existing seam into bounded product value.",
            "beneficiary": "Repeat players and the product operator",
            "observed_signal": "Match events exist while cross-session value remains incomplete.",
            "product_mechanism": mechanism,
            "behavior_change": behavior,
            "business_effect": {
                "revenue_or_value_effect": revenue,
                "causal_chain": [
                    "The mechanism creates reliable cross-session value.",
                    "Higher durable value improves retention or paid-season trust.",
                ],
                "leading_indicator": "Cohort return rises without mode diversity loss.",
                "countervailing_risk": "Reward and operating cost may exceed incremental value.",
            },
            "product_opportunity_lineage": {
                "source_signal_ids": claim_ids,
                "signal": "Existing events expose an unused product seam.",
                "latent_need": "Progress should remain meaningful across sessions and corrections.",
                "mechanism": mechanism,
                "behavior_change": behavior,
                "business_effect": revenue,
                "non_obvious_leap": "Treat event reliability and player choice as product economics, not plumbing.",
            },
            "second_order_effects": [
                {
                    "stakeholder": "Players who prefer one mode",
                    "horizon": "Second season",
                    "valence": "risk",
                    "first_order_effect": "Progress gives players a return reason.",
                    "second_order_effect": "Reward tuning can redirect attention away from preferred play.",
                    "feedback_or_externality": "Optimizing completion can concentrate the mode ecosystem.",
                    "early_signal": "Task completion rises while mode diversity falls.",
                }
            ],
            "operating_burden": {
                "recurring_work": "Tune goals, rewards, corrections, and player communications.",
                "owner": "Product operations with economy and data support",
                "cadence": "Weekly monitoring and seasonal refresh",
                "capacity_or_cost_limit": "One bounded content lane before expansion",
                "failure_mode": "The feature becomes an unfunded live-operations promise.",
            },
            "authority": {
                "decision_owner": "Product owner",
                "required_approvals": ["economy review", "live-operations capacity review"],
                "prohibited_without_authority": "No paid launch or competitive reward change.",
                "escalation_trigger": "Fairness harm, entitlement mismatch, or capacity overrun.",
            },
            "action_probe": {
                "kind": "behavioral_exposure",
                "reversible": True,
                "terminal_output_kind": "observed_actor_response",
                "intervention": "Expose an optional free track to one bounded cohort.",
                "target_actor": "Repeat players",
                "observation_window": "Four weeks",
                "metric": "Return rate, mode diversity, and correction rate",
                "baseline_or_counterfactual": "Matched players without the track",
                "falsifier": "Return stays flat, diversity falls, or correction burden breaches the cap.",
                "rollback": "Disable the track without changing match state.",
                "stop_condition": "Stop on fairness complaints or material diversity decline.",
                "authority_preconditions": ["product approval", "economy review"],
                "branches": {
                    "if_supported": "Test willingness to pay separately.",
                    "if_refuted": "Retire the mechanism and preserve the event seam.",
                    "if_inconclusive": "Run a longer, still unpaid observation window.",
                },
            },
            "failure_basis": failure_basis,
            "evidence_scope": {
                "received_source_ids": allowed,
                "claim_source_ids": claim_ids,
            },
        }
        if role == PRODUCT_OPPORTUNITY_INVENTOR:
            candidate["spontaneous_opportunity"] = {
                "unasked_opportunity": "A cross-mode seasonal journey with a separately gated paid track.",
                "why_signal_implies_it": "Repeat play and reusable events can support persistent progress.",
                "why_not_obvious": "The local code seam looks like telemetry until viewed as a value loop.",
                "existing_capability_reused": "Match completion events and mode identity",
                "product_boundary": "Fair core competition remains independent of payment.",
            }
        elif role == CROSS_DOMAIN_ARCHITECTURE_ANALOGIST:
            candidate["architecture_transfer"] = {
                "source": "append-only financial ledgers",
                "source_ids": exclusive,
                "pressure": "Duplicate, late, and corrected events must not corrupt balances.",
                "mechanism": "Immutable facts plus idempotent, rebuildable projections",
                "target": "Seasonal progress and reward entitlement state must survive retries.",
                "adaptation": "Use match IDs as idempotency keys and rebuild season views from facts.",
                "limits": [
                    "Ledger correctness does not prove the reward loop is enjoyable.",
                    "Do not copy financial compliance complexity into the game wholesale.",
                ],
            }
            candidate["failure_basis"]["transfer_limit"] = (
                "Ledger correctness does not prove the reward loop is enjoyable."
            )
        else:
            candidate["failure_earned_boundary"] = {
                "source_failure_ids": [packet["adverse_source_ids"][0]],
                "failed_assumption": "More task completion implied a healthier engagement loop.",
                "observed_adverse_outcome": "Completion rose while mode diversity declined.",
                "missing_viability_condition": "Players must retain meaningful choice of mode.",
                "boundary": "No narrow recurring task may dominate progression velocity.",
                "guardrail": "Cap narrow task pressure and monitor mode diversity.",
                "transfer_limit": "The boundary does not establish a season price or content cadence.",
            }
        return candidate


class PartitionedProductProvider:
    last_usage = None

    def __init__(
        self,
        fixture,
        *,
        provider_name="fixture",
        model="product-v3",
        fail_role="",
    ):
        self.fixture = fixture
        self.provider_name = provider_name
        self.model = model
        self.fail_role = fail_role
        self.failed = False

    def stream(self, messages):
        prompt = messages[-1]["content"]
        if prompt.startswith("ROLE_ASSIGNMENT:"):
            role = prompt.splitlines()[0].split(":", 1)[1].strip()
        elif prompt.startswith("ROLE: origin-blinded"):
            role = BLINDED_ADVERSARY_ROLE
        elif prompt.startswith("ROLE: product cognition selector"):
            role = SELECTOR_ROLE
        else:
            raise AssertionError(prompt[:120])
        if role == self.fail_role and not self.failed:
            self.failed = True
            raise RuntimeError("simulated partitioned product provider failure")
        yield json.dumps(self.fixture(role, prompt))


class PartitionedProductCognitionTests(unittest.TestCase):
    def run_fixture(self, fixture=None, *, partitions=None):
        fixture = fixture or CognitionFixture()
        result = run_partitioned_product_cognition(
            ask=fixture,
            common_evidence=common_evidence(),
            partitions=partitions or evidence_partitions(),
            constitution={
                "purpose": "Increase durable player value without pay-to-win pressure.",
                "authority": "Draft and probe only; no launch authority.",
            },
        )
        return fixture, result

    def test_runs_three_independent_roles_and_host_issues_exact_selected_copy(self):
        fixture, result = self.run_fixture()
        self.assertEqual(fixture.calls[:3], list(INVENTOR_ROLES))
        self.assertEqual(len(result["frozen_candidates"]), 3)
        self.assertEqual(len(result["blinded_critiques"]), 3)
        self.assertEqual(result["host_issued_result"]["issued_by"], "product_cognition_host")
        selected_id = result["selector_decision"]["selected_candidate_ids"][0]
        selected = next(
            row for row in result["frozen_candidates"] if row["candidate_id"] == selected_id
        )
        self.assertEqual(result["host_issued_result"]["draft"], selected)
        self.assertTrue(selected["candidate_id"].startswith("candidate-"))
        self.assertTrue(selected["candidate_fingerprint"].startswith("sha256:"))
        self.assertTrue(selected["frozen"])
        self.assertIn("revenue_or_value_effect", selected["business_effect"])
        self.assertTrue(selected["second_order_effects"])
        self.assertTrue(selected["action_probe"]["reversible"])

    def test_candidate_ids_and_fingerprints_are_stable_for_same_inputs(self):
        _, first = self.run_fixture()
        _, second = self.run_fixture()
        self.assertEqual(
            [row["candidate_id"] for row in first["frozen_candidates"]],
            [row["candidate_id"] for row in second["frozen_candidates"]],
        )
        self.assertEqual(
            [row["candidate_fingerprint"] for row in first["frozen_candidates"]],
            [row["candidate_fingerprint"] for row in second["frozen_candidates"]],
        )

    def test_rejects_overlapping_partitions_before_any_model_call(self):
        partitions = evidence_partitions()
        partitions[CROSS_DOMAIN_ARCHITECTURE_ANALOGIST][0]["source_id"] = "signal-return-gap"
        fixture = CognitionFixture()
        with self.assertRaisesRegex(ValueError, "globally disjoint"):
            self.run_fixture(fixture, partitions=partitions)
        self.assertEqual(fixture.calls, [])

    def test_rejects_fabricated_source_ids(self):
        def mutate(role, candidate, _packet):
            if role == PRODUCT_OPPORTUNITY_INVENTOR:
                candidate["evidence_scope"]["claim_source_ids"].append("source-invented")

        with self.assertRaisesRegex(ValueError, "fabricated source IDs"):
            self.run_fixture(CognitionFixture(candidate_mutator=mutate))

    def test_candidate_must_cite_the_substantive_source_not_only_generic_metadata(self):
        partitions = evidence_partitions()
        partitions[PRODUCT_OPPORTUNITY_INVENTOR].insert(
            0,
            {
                "source_id": "workspace-generic",
                "kind": "workspace_observation",
                "status": "observed",
                "epistemic_class": "direct_observation",
                "decision_authority": "mission_citable",
                "observation": "Git metadata exists.",
            },
        )

        def mutate(role, candidate, _packet):
            if role == PRODUCT_OPPORTUNITY_INVENTOR:
                candidate["evidence_scope"]["claim_source_ids"] = [
                    "workspace-generic"
                ]
                candidate["product_opportunity_lineage"]["source_signal_ids"] = [
                    "workspace-generic"
                ]

        with self.assertRaisesRegex(ValueError, "substantive non-generic"):
            self.run_fixture(
                CognitionFixture(candidate_mutator=mutate), partitions=partitions
            )

    def test_rejects_generic_code_review_output(self):
        def mutate(role, candidate, _packet):
            if role == PRODUCT_OPPORTUNITY_INVENTOR:
                candidate["output_kind"] = "code_review"

        with self.assertRaisesRegex(ValueError, "generic code-review output"):
            self.run_fixture(CognitionFixture(candidate_mutator=mutate))

    def test_requires_a_structured_business_or_revenue_effect(self):
        def mutate(role, candidate, _packet):
            if role == PRODUCT_OPPORTUNITY_INVENTOR:
                candidate["business_effect"]["revenue_or_value_effect"] = ""

        with self.assertRaisesRegex(ValueError, "revenue_or_value_effect"):
            self.run_fixture(CognitionFixture(candidate_mutator=mutate))

    def test_requires_complete_cross_domain_transfer_and_nonempty_limits(self):
        def mutate(role, candidate, _packet):
            if role == CROSS_DOMAIN_ARCHITECTURE_ANALOGIST:
                candidate["architecture_transfer"]["limits"] = []

        with self.assertRaisesRegex(ValueError, "limits"):
            self.run_fixture(CognitionFixture(candidate_mutator=mutate))

    def test_rejects_architecture_content_mutation_behind_a_valid_mapping_id(self):
        def mutate(role, candidate, _packet):
            if role == CROSS_DOMAIN_ARCHITECTURE_ANALOGIST:
                transfer = candidate["architecture_transfer"]
                self.assertEqual(
                    transfer["source_ids"], ["mapping-ledger-projection"]
                )
                transfer["pressure"] = "Invented pressure behind a valid source ID."
                transfer["mechanism"] = "Invented mechanism behind a valid source ID."
                transfer["adaptation"] = "Invented target architecture."
                transfer["limits"] = ["Invented and weakened transfer limit."]

        with self.assertRaisesRegex(
            ValueError, "must exactly copy the host-validated transfer mapping"
        ):
            self.run_fixture(CognitionFixture(candidate_mutator=mutate))

    def test_rejects_omitting_any_host_validated_transfer_limit(self):
        def mutate(role, candidate, _packet):
            if role == CROSS_DOMAIN_ARCHITECTURE_ANALOGIST:
                candidate["architecture_transfer"]["limits"] = [
                    "Ledger correctness does not prove the reward loop is enjoyable."
                ]

        with self.assertRaisesRegex(ValueError, "exactly preserve"):
            self.run_fixture(CognitionFixture(candidate_mutator=mutate))

    def test_unversioned_architecture_mapping_forces_host_abstention(self):
        partitions = evidence_partitions()
        partitions[CROSS_DOMAIN_ARCHITECTURE_ANALOGIST][0]["payload"].pop(
            "transfer_contract_version"
        )
        fixture, result = self.run_fixture(partitions=partitions)
        self.assertNotIn(CROSS_DOMAIN_ARCHITECTURE_ANALOGIST, fixture.calls)
        abstention = next(
            row
            for row in result["abstentions"]
            if row["role"] == CROSS_DOMAIN_ARCHITECTURE_ANALOGIST
        )
        self.assertEqual(
            abstention["reason_code"], "no_validated_cross_domain_evidence"
        )

    def test_inventor_prompt_names_exact_probe_enums_without_solution_catalog(self):
        fixture, _ = self.run_fixture()
        prompt = next(
            prompt
            for role, prompt in fixture.prompts
            if role == PRODUCT_OPPORTUNITY_INVENTOR
        )
        self.assertIn("behavioral_exposure", prompt)
        self.assertIn("observed_actor_response", prompt)
        self.assertIn("lineage.business_effect", prompt)

    def test_missing_failure_archive_forces_host_abstention_without_calling_role(self):
        fixture, result = self.run_fixture(partitions=evidence_partitions(failure=False))
        self.assertNotIn(FAILURE_EXPERIENCED_OPERATOR, fixture.calls)
        abstention = result["abstentions"][0]
        self.assertEqual(abstention["reason_code"], "no_adverse_evidence")
        self.assertEqual(abstention["failure_basis"]["basis_type"], "no_signal")
        self.assertEqual(abstention["failure_basis"]["source_ids"], ())
        self.assertEqual(len(result["frozen_candidates"]), 2)

    def test_missing_architecture_evidence_forces_host_abstention(self):
        partitions = evidence_partitions()
        partitions[CROSS_DOMAIN_ARCHITECTURE_ANALOGIST] = []
        fixture, result = self.run_fixture(partitions=partitions)
        self.assertNotIn(CROSS_DOMAIN_ARCHITECTURE_ANALOGIST, fixture.calls)
        abstention = next(
            row
            for row in result["abstentions"]
            if row["role"] == CROSS_DOMAIN_ARCHITECTURE_ANALOGIST
        )
        self.assertEqual(
            abstention["reason_code"], "no_validated_cross_domain_evidence"
        )
        self.assertEqual(len(result["frozen_candidates"]), 2)

    def test_raw_gitnexus_excerpts_without_validated_mapping_force_abstention(self):
        with tempfile.TemporaryDirectory() as tempdir:
            packet, _ = collect_packet(tempdir)
            from palamedes_architecture_transfer import (
                validate_gitnexus_evidence_packet,
            )

            with patch(
                "palamedes_architecture_transfer.reverify_gitnexus_evidence_packet",
                side_effect=lambda value: validate_gitnexus_evidence_packet(value),
            ):
                bundle = build_cognition_evidence_bundle(
                    state_root=Path(tempdir) / ".palamedes",
                    snapshot={
                        "observation_id": "observation-raw-reference-only",
                        "snapshot_fingerprint": "snapshot-raw-reference-only",
                        "signals": {
                            "git": {"head": "abc123", "branch": "main"},
                            "change": {"summary": "activity is observable"},
                            "test": {},
                        },
                    },
                    user_request="Find a bounded product opportunity.",
                    mode="product",
                    architecture_packet=packet,
                    transfer_mappings=[],
                )
            _, partitions, _ = partition_cognition_evidence_bundle(bundle)

        self.assertEqual(partitions[CROSS_DOMAIN_ARCHITECTURE_ANALOGIST], [])

    def test_nonadverse_archive_cannot_be_promoted_to_failure_experience(self):
        fixture, result = self.run_fixture(
            partitions=evidence_partitions(failure=True, failure_status="success")
        )
        self.assertNotIn(FAILURE_EXPERIENCED_OPERATOR, fixture.calls)
        self.assertEqual(result["abstentions"][0]["reason_code"], "no_adverse_evidence")

    def test_disqualified_candidate_cannot_be_selected(self):
        fixture = CognitionFixture(
            disqualify_titles={"Cross-mode seasonal journey"},
            select_disqualified=True,
        )
        with self.assertRaisesRegex(ValueError, "disqualified candidate cannot be selected"):
            self.run_fixture(fixture)

    def test_selector_can_mutate_only_its_detached_packet_not_frozen_candidates(self):
        fixture, result = self.run_fixture(
            CognitionFixture(mutate_selector_copy=True)
        )
        selected_id = result["selector_decision"]["selected_candidate_ids"][0]
        selected = next(
            row for row in result["frozen_candidates"] if row["candidate_id"] == selected_id
        )
        self.assertNotEqual(selected["title"], "selector-authored mutation")
        self.assertEqual(result["host_issued_result"]["draft"]["title"], selected["title"])
        with self.assertRaises(TypeError):
            result["host_issued_result"]["draft"]["title"] = "mutation"
        with self.assertRaises(TypeError):
            result["frozen_candidates"][0]["business_effect"]["causal_chain"][0] = "mutation"

    def test_prompts_prove_generation_isolation_adversary_blinding_and_selector_sanitization(self):
        fixture, _ = self.run_fixture()
        inventor_prompts = {
            role: prompt for role, prompt in fixture.prompts if role in INVENTOR_ROLES
        }
        for prompt in inventor_prompts.values():
            self.assertIn(
                "does not turn observed_signal", prompt
            )
        self.assertNotIn(
            "Cross-mode seasonal journey",
            inventor_prompts[CROSS_DOMAIN_ARCHITECTURE_ANALOGIST],
        )
        self.assertNotIn(
            "Ledger-grade progression projection",
            inventor_prompts[FAILURE_EXPERIENCED_OPERATOR],
        )
        for role in INVENTOR_ROLES:
            packet = next(packet for packet_role, packet in fixture.packets if packet_role == role)
            self.assertFalse(packet["rival_candidates_visible"])
            self.assertNotIn("candidate", packet)

        adversary_packets = [
            packet for role, packet in fixture.packets if role == BLINDED_ADVERSARY_ROLE
        ]
        all_titles = {
            "Cross-mode seasonal journey",
            "Ledger-grade progression projection",
            "Choice-preserving progression boundary",
        }
        self.assertEqual(len(adversary_packets), 3)
        for packet in adversary_packets:
            self.assertEqual(
                set(packet),
                {"constitution", "review_subject_id", "candidate", "host_claims"},
            )
            serialized = json.dumps(packet, ensure_ascii=False, sort_keys=True)
            self.assertNotIn("candidate_id", serialized)
            self.assertNotIn("candidate_fingerprint", serialized)
            self.assertNotIn("inventor_role", serialized)
            self.assertNotIn("source_id", serialized)
            self.assertTrue(packet["host_claims"])
            self.assertTrue(
                all(
                    row["custody"] == "host_supplied_evidence"
                    for row in packet["host_claims"]
                )
            )
            visible_title = packet["candidate"]["title"]
            for rival_title in all_titles - {visible_title}:
                self.assertNotIn(rival_title, serialized)

        selector_packet = next(
            packet for role, packet in fixture.packets if role == SELECTOR_ROLE
        )
        self.assertEqual(
            set(selector_packet),
            {
                "constitution",
                "sanitized_frozen_candidates",
                "sanitized_blinded_critiques",
            },
        )
        serialized_selector = json.dumps(selector_packet, ensure_ascii=False, sort_keys=True)
        self.assertNotIn("inventor_role", serialized_selector)
        self.assertNotIn("source_id", serialized_selector)
        self.assertTrue(
            all(row["frozen"] is True for row in selector_packet["sanitized_frozen_candidates"])
        )

    def test_product_inventor_prompt_does_not_seed_the_named_solution(self):
        fixture, _ = self.run_fixture()
        prompt = next(
            prompt
            for role, prompt in fixture.prompts
            if role == PRODUCT_OPPORTUNITY_INVENTOR
        )
        normalized = " ".join(
            prompt.lower().replace("-", " ").replace("_", " ").split()
        )
        for forbidden in (
            "battle pass",
            "season pass",
            "seasonal progression",
            "seasonal track",
            "seasonal journey",
            "paid track",
            "premium track",
            "reward track",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, normalized)

    def test_all_four_selector_modes_produce_host_issued_results(self):
        expected_kind = {
            "commit": "draft",
            "bounded_exploration": "bounded_exploration",
            "discriminating_probe": "discriminating_probe",
            "defer": "defer",
        }
        for mode in expected_kind:
            with self.subTest(mode=mode):
                _, result = self.run_fixture(CognitionFixture(selector_mode=mode))
                self.assertEqual(result["selector_decision"]["mode"], mode)
                self.assertEqual(result["host_issued_result"]["result_kind"], expected_kind[mode])
                self.assertEqual(result["host_issued_result"]["issued_by"], "product_cognition_host")

    def test_selector_prompt_distinguishes_probe_draft_from_product_launch(self):
        fixture, _ = self.run_fixture(CognitionFixture(selector_mode="defer"))
        prompt = next(
            prompt for role, prompt in fixture.prompts if role == SELECTOR_ROLE
        )
        self.assertIn("next bounded epistemic action", prompt)
        self.assertIn("does not approve the product thesis", prompt)
        self.assertIn("Do not demand the evidence", prompt)

    def test_public_result_can_be_explicitly_thawed_for_serialization(self):
        _, result = self.run_fixture()
        mutable = thaw(result)
        json.dumps(mutable, ensure_ascii=False)
        mutable["frozen_candidates"][0]["title"] = "local mutable copy"
        self.assertNotEqual(
            mutable["frozen_candidates"][0]["title"],
            result["frozen_candidates"][0]["title"],
        )

    def test_generic_metadata_and_empty_document_force_abstention_and_host_defer(self):
        with tempfile.TemporaryDirectory() as tempdir:
            bundle = build_cognition_evidence_bundle(
                state_root=Path(tempdir) / ".palamedes",
                snapshot={
                    "observation_id": "observation-generic-only",
                    "snapshot_fingerprint": "snapshot-generic-only",
                    "signals": {
                        "git": {"head": "abc123", "branch": "main"},
                        "change": {"summary": "repository activity is observable"},
                        "test": {"status": "passing"},
                        "documents": [
                            {
                                "path": "README.md",
                                "content_sha256": "a" * 64,
                                "headings": [],
                                "excerpt": "",
                                "excerpt_truncated": False,
                            }
                        ],
                    },
                },
                user_request=(
                    "Invent a recurring seasonal product opportunity from this repository."
                ),
                mode="product",
            )
            common, partitions, constitution = partition_cognition_evidence_bundle(
                bundle
            )
            fixture = CognitionFixture()
            result = run_partitioned_product_cognition(
                ask=fixture,
                common_evidence=common,
                partitions=partitions,
                constitution=constitution,
            )

        self.assertEqual(fixture.calls, [])
        self.assertEqual(result["frozen_candidates"], ())
        self.assertEqual(result["host_issued_result"]["result_kind"], "defer")
        self.assertFalse(result["audit"]["selector_called"])
        product_abstention = next(
            row
            for row in result["abstentions"]
            if row["role"] == PRODUCT_OPPORTUNITY_INVENTOR
        )
        self.assertEqual(
            product_abstention["reason_code"], "no_substantive_product_evidence"
        )
        self.assertIn("host-citable product fact", product_abstention["wake_condition"])

    def test_chat_product_wrapper_persists_v3_and_compiles_only_host_selected_substance(self):
        fixture = CognitionFixture()

        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            record_substantive_product_fact(root / ".palamedes")
            bundle = build_cognition_evidence_bundle(
                state_root=root / ".palamedes",
                snapshot={
                    "observation_id": "observation-wrapper",
                    "snapshot_fingerprint": "snapshot-wrapper",
                    "signals": {
                        "git": {"head": "abc123", "branch": "main"},
                        "change": {"summary": "repeat activity is already observable"},
                        "test": {},
                    },
                },
                user_request=(
                    "Find an unasked product opportunity from repeat use, reusable "
                    "events, an incomplete return loop, and unused value capture."
                ),
                mode="product",
            )
            result = run_partitioned_product_cycle(
                provider=PartitionedProductProvider(fixture),
                context="Bounded product context",
                cycle_store=CognitionCycleStore(
                    root / ".palamedes" / "missions" / "cognition"
                ),
                evidence_bundle=bundle,
            )

        cycle = result["cycle"]
        contract = result["contract"]
        self.assertEqual(
            cycle["cognition_cycle_version"], "palamedes-product-cognition-cycle/3"
        )
        self.assertEqual(cycle["status"], "selected")
        self.assertNotIn(CROSS_DOMAIN_ARCHITECTURE_ANALOGIST, fixture.calls)
        self.assertNotIn(FAILURE_EXPERIENCED_OPERATOR, fixture.calls)
        self.assertEqual(contract["status"], "draft")
        self.assertEqual(contract["work_scale"], "component")
        self.assertFalse(
            contract["product_cognition_lineage"]["selector_mutation_authority"]
        )
        self.assertTrue(
            contract["product_cognition_lineage"]["host_issuance_authority"]
        )
        selected = cycle["partitioned_cognition"]["host_issued_result"]["draft"]
        self.assertEqual(contract["selected_candidate_id"], selected["candidate_id"])
        self.assertIn(selected["action_probe"]["intervention"], contract["next_probe"]["step"])
        self.assertNotIn("context_governor", [row["role"] for row in cycle["artifacts"]])
        self.assertNotEqual(
            contract["evidence"][0]["claim"], selected["observed_signal"]
        )
        evidence_custody = contract["product_cognition_lineage"][
            "mission_evidence_custody"
        ]
        self.assertEqual(
            evidence_custody[0]["source"], contract["evidence"][0]["source"]
        )
        self.assertEqual(evidence_custody[0]["custody"]["owner"], "host")
        self.assertFalse(
            evidence_custody[0]["custody"]["candidate_language_certified"]
        )
        self.assertEqual(contract["surface_key"], "")
        self.assertEqual(contract["scope_keys"], [])
        self.assertEqual(contract["scope_custody"]["scope_status"], "unknown")
        self.assertFalse(contract["scope_custody"]["candidate_scope_accepted"])
        gate_contract = contract["specialized_authority_gates"]
        self.assertEqual(gate_contract["status"], "unresolved")
        self.assertFalse(gate_contract["generic_mission_approval_satisfies"])
        self.assertEqual(
            {row["source_path"] for row in gate_contract["gates"]},
            {
                "candidate.authority.required_approvals",
                "candidate.action_probe.authority_preconditions",
            },
        )
        self.assertEqual(
            [row["status"] for row in gate_contract["gates"]],
            ["unresolved"] * 4,
        )
        with self.assertRaisesRegex(
            ValueError,
            "Generic /approve cannot satisfy them.*no specialized resolution command",
        ):
            approve_mission(
                object(),
                MissionStore(root / ".palamedes" / "missions"),
                contract,
                "product-gate-test",
            )

    def test_product_contract_scope_comes_only_from_trusted_bundle_alignment(self):
        fixture = CognitionFixture()
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            state_root = root / ".palamedes"
            ProductAlignmentStore(state_root / "product-alignment").record_capability(
                capability_id="capability-match-events",
                statement="Match completion events are already available.",
                source_ids=["host-observation-1"],
                surface_key="game:yut",
            )
            bundle = build_cognition_evidence_bundle(
                state_root=state_root,
                snapshot={
                    "observation_id": "observation-scoped",
                    "snapshot_fingerprint": "snapshot-scoped",
                    "signals": {
                        "git": {"head": "abc123", "branch": "main"},
                        "change": {"summary": "repeat activity is observable"},
                        "test": {},
                    },
                },
                user_request="Find a bounded product opportunity.",
                mode="product",
            )
            result = run_partitioned_product_cycle(
                provider=PartitionedProductProvider(fixture),
                context="The model receives no authority to name the execution scope.",
                cycle_store=CognitionCycleStore(
                    state_root / "missions" / "cognition"
                ),
                evidence_bundle=bundle,
            )

        contract = result["contract"]
        self.assertEqual(contract["surface_key"], "game:yut")
        self.assertEqual(contract["scope_keys"], ["surface:game:yut"])
        self.assertEqual(
            contract["scope_custody"]["scope_status"],
            "derived_from_trusted_bundle",
        )
        self.assertTrue(contract["scope_custody"]["source_ids"])
        self.assertFalse(contract["scope_custody"]["candidate_scope_accepted"])

    def test_product_resume_rejects_provider_or_model_change_without_relabeling(self):
        fixture = CognitionFixture()
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            state_root = root / ".palamedes"
            record_substantive_product_fact(state_root)
            bundle = build_cognition_evidence_bundle(
                state_root=state_root,
                snapshot={
                    "observation_id": "observation-resume",
                    "snapshot_fingerprint": "snapshot-resume",
                    "signals": {
                        "git": {"head": "abc123", "branch": "main"},
                        "change": {"summary": "repeat activity is observable"},
                        "test": {},
                    },
                },
                user_request="Find a bounded product opportunity.",
                mode="product",
            )
            cycle_store = CognitionCycleStore(
                state_root / "missions" / "cognition"
            )
            original_provider = PartitionedProductProvider(
                fixture,
                provider_name="original-provider",
                model="original-model",
                fail_role=SELECTOR_ROLE,
            )
            with self.assertRaisesRegex(RuntimeError, "simulated partitioned"):
                run_partitioned_product_cycle(
                    provider=original_provider,
                    context="Preserve product-cycle identity across retries.",
                    cycle_store=cycle_store,
                    evidence_bundle=bundle,
                    schema_retry_limit=0,
                )
            cycle_path = next(cycle_store.root.glob("cycle-*.json"))
            failed_cycle = json.loads(cycle_path.read_text(encoding="utf-8"))
            cycle_id = failed_cycle["cognition_cycle_id"]
            artifact_count = len(failed_cycle["artifacts"])

            changed_provider = PartitionedProductProvider(
                CognitionFixture(),
                provider_name="replacement-provider",
                model="replacement-model",
            )
            with self.assertRaisesRegex(
                ValueError,
                "provider and model must match the original product cycle",
            ):
                run_partitioned_product_cycle(
                    provider=changed_provider,
                    context="A caller-supplied replacement context.",
                    cycle_store=cycle_store,
                    evidence_bundle=bundle,
                    resume_cycle_id=cycle_id,
                )

            preserved = cycle_store.load(cycle_id)
            self.assertEqual(preserved["provider"], "original-provider")
            self.assertEqual(preserved["model"], "original-model")
            self.assertEqual(len(preserved["artifacts"]), artifact_count)
            self.assertEqual(changed_provider.fixture.calls, [])

    def test_product_resume_rejects_mixed_checkpoint_provider_identity(self):
        fixture = CognitionFixture()
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            state_root = root / ".palamedes"
            record_substantive_product_fact(state_root)
            bundle = build_cognition_evidence_bundle(
                state_root=state_root,
                snapshot={
                    "observation_id": "observation-mixed-resume",
                    "snapshot_fingerprint": "snapshot-mixed-resume",
                    "signals": {
                        "git": {"head": "abc123", "branch": "main"},
                        "change": {"summary": "repeat activity is observable"},
                        "test": {},
                    },
                },
                user_request="Find a bounded product opportunity.",
                mode="product",
            )
            cycle_store = CognitionCycleStore(
                state_root / "missions" / "cognition"
            )
            provider = PartitionedProductProvider(
                fixture,
                provider_name="original-provider",
                model="original-model",
                fail_role=SELECTOR_ROLE,
            )
            with self.assertRaises(RuntimeError):
                run_partitioned_product_cycle(
                    provider=provider,
                    context="Detect mixed provider checkpoints.",
                    cycle_store=cycle_store,
                    evidence_bundle=bundle,
                    schema_retry_limit=0,
                )
            cycle_path = next(cycle_store.root.glob("cycle-*.json"))
            stored = json.loads(cycle_path.read_text(encoding="utf-8"))
            stored["artifacts"][0]["model"] = "foreign-model"
            cycle_store.save(stored)

            with self.assertRaisesRegex(ValueError, "mixed or malformed"):
                run_partitioned_product_cycle(
                    provider=PartitionedProductProvider(
                        CognitionFixture(),
                        provider_name="original-provider",
                        model="original-model",
                    ),
                    context="Detect mixed provider checkpoints.",
                    cycle_store=cycle_store,
                    evidence_bundle=bundle,
                    resume_cycle_id=stored["cognition_cycle_id"],
                )

    def test_product_cycle_budgets_and_reports_architecture_preparation_calls(self):
        with tempfile.TemporaryDirectory() as tempdir:
            state_root = Path(tempdir) / ".palamedes"
            record_substantive_product_fact(state_root)
            bundle = build_cognition_evidence_bundle(
                state_root=state_root,
                snapshot={
                    "observation_id": "observation-precycle-usage",
                    "snapshot_fingerprint": "snapshot-precycle-usage",
                    "signals": {
                        "git": {"head": "abc123", "branch": "main"},
                        "change": {"summary": "repeat activity is observable"},
                        "test": {},
                    },
                },
                user_request="Find a bounded product opportunity.",
                mode="product",
            )
            provider = PartitionedProductProvider(CognitionFixture())
            result = run_partitioned_product_cycle(
                provider=provider,
                context="Count preparation and partitioned cognition together.",
                cycle_store=CognitionCycleStore(
                    state_root / "missions" / "cognition"
                ),
                evidence_bundle=bundle,
                budget={"provider_calls_max": 5, "token_budget_high": 1000},
                precycle_provider_usage={
                    "provider": provider.provider_name,
                    "model": provider.model,
                    "attempted_calls": 2,
                    "metered_calls": 1,
                    "unmetered_calls": 1,
                    "totals": {"total_tokens": 21},
                    "roles": [
                        {
                            "role": "architecture_transfer_mechanism_query_designer",
                            "custody": "provider_reported",
                            "usage": {"total_tokens": 21},
                        },
                        {
                            "role": "cross_domain_architecture_transfer_inventor",
                            "custody": "unmetered",
                            "usage": {},
                        },
                    ],
                },
            )

        cycle = result["cycle"]
        self.assertEqual(cycle["live_model_call_count"], 5)
        self.assertEqual(cycle["provider_usage"]["attempted_calls"], 5)
        self.assertEqual(len(cycle["precycle_artifacts"]), 2)
        self.assertEqual(cycle["provider_usage"]["totals"]["total_tokens"], 21)

    def test_failed_product_provider_call_is_persisted_and_budgeted(self):
        with tempfile.TemporaryDirectory() as tempdir:
            state_root = Path(tempdir) / ".palamedes"
            record_substantive_product_fact(state_root)
            bundle = build_cognition_evidence_bundle(
                state_root=state_root,
                snapshot={
                    "observation_id": "observation-paid-failure",
                    "snapshot_fingerprint": "snapshot-paid-failure",
                    "signals": {
                        "git": {"head": "abc123", "branch": "main"},
                        "change": {"summary": "repeat activity is observable"},
                        "test": {},
                    },
                },
                user_request="Find a bounded product opportunity.",
                mode="product",
            )
            store = CognitionCycleStore(state_root / "missions" / "cognition")
            provider = PartitionedProductProvider(
                CognitionFixture(), fail_role=PRODUCT_OPPORTUNITY_INVENTOR
            )
            with self.assertRaisesRegex(RuntimeError, "simulated partitioned"):
                run_partitioned_product_cycle(
                    provider=provider,
                    context="Preserve failed-call custody.",
                    cycle_store=store,
                    evidence_bundle=bundle,
                    schema_retry_limit=0,
                )
            cycle = json.loads(
                next(store.root.glob("cycle-*.json")).read_text(encoding="utf-8")
            )

        self.assertEqual(cycle["live_model_call_count"], 1)
        self.assertEqual(cycle["provider_usage"]["attempted_calls"], 1)
        self.assertEqual(cycle["artifacts"], [])
        self.assertEqual(len(cycle["rejected_artifacts"]), 1)
        self.assertTrue(cycle["rejected_artifacts"][0]["attempted"])
        self.assertIn("simulated partitioned", cycle["rejected_artifacts"][0]["failure"])

    def test_product_resume_restores_original_budget_after_failed_call(self):
        with tempfile.TemporaryDirectory() as tempdir:
            state_root = Path(tempdir) / ".palamedes"
            record_substantive_product_fact(state_root)
            bundle = build_cognition_evidence_bundle(
                state_root=state_root,
                snapshot={
                    "observation_id": "observation-resume-budget",
                    "snapshot_fingerprint": "snapshot-resume-budget",
                    "signals": {
                        "git": {"head": "abc123", "branch": "main"},
                        "change": {"summary": "repeat activity is observable"},
                        "test": {},
                    },
                },
                user_request="Find a bounded product opportunity.",
                mode="product",
            )
            store = CognitionCycleStore(state_root / "missions" / "cognition")
            provider = PartitionedProductProvider(
                CognitionFixture(), fail_role=SELECTOR_ROLE
            )
            with self.assertRaisesRegex(RuntimeError, "simulated partitioned"):
                run_partitioned_product_cycle(
                    provider=provider,
                    context="Keep the original product-cycle budget on resume.",
                    cycle_store=store,
                    evidence_bundle=bundle,
                    budget={"provider_calls_max": 3, "token_budget_high": 1000},
                    schema_retry_limit=0,
                )
            cycle_id = next(store.root.glob("cycle-*.json")).stem
            with self.assertRaisesRegex(ValueError, "budget exhausted"):
                run_partitioned_product_cycle(
                    provider=provider,
                    context="Ignored replacement context.",
                    cycle_store=store,
                    evidence_bundle=bundle,
                    resume_cycle_id=cycle_id,
                )
            preserved_budget = store.load(cycle_id)["budget"]

        self.assertEqual(preserved_budget["provider_calls_max"], 3)


if __name__ == "__main__":
    unittest.main()
