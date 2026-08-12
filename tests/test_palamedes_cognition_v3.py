#!/usr/bin/env python3
import copy
import json
import tempfile
import unittest
from pathlib import Path

from palamedes_cognition_v3 import (
    BLINDED_ADVERSARY_ROLE,
    CROSS_DOMAIN_ARCHITECTURE_ANALOGIST,
    FAILURE_EXPERIENCED_OPERATOR,
    INVENTOR_ROLES,
    PRODUCT_OPPORTUNITY_INVENTOR,
    SELECTOR_ROLE,
    run_partitioned_product_cognition,
    thaw,
)
from palamedes_chat import CognitionCycleStore, run_partitioned_product_cycle
from palamedes_evidence_bundle import build_cognition_evidence_bundle


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
                "source_id": "source-ledger-log",
                "evidence_kind": "external_architecture",
                "source_domain": "append-only financial ledgers",
                "target_domain": "seasonal game progression",
                "pressure": "late and duplicate events must not corrupt derived balances",
                "mechanism": "immutable events plus idempotent projection",
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
            "evidence_kind": "observed_system_fact",
            "observation": "Completed matches already emit player, mode, and result events.",
        }
    ]


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
                "Append match events immutably and project idempotent seasonal progress."
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
                "source": "Append-only financial ledger projection",
                "source_ids": exclusive,
                "pressure": "Duplicate, late, and corrected events must not corrupt balances.",
                "mechanism": "Immutable facts plus idempotent, rebuildable projections",
                "target": "Seasonal progress and reward entitlement state",
                "adaptation": "Use match IDs as idempotency keys and rebuild season views from facts.",
                "limits": [
                    "Ledger correctness does not prove the reward loop is enjoyable.",
                    "Do not copy financial compliance complexity into the game wholesale.",
                ],
            }
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
            self.assertEqual(set(packet), {"constitution", "review_subject_id", "candidate"})
            serialized = json.dumps(packet, ensure_ascii=False, sort_keys=True)
            self.assertNotIn("candidate_id", serialized)
            self.assertNotIn("candidate_fingerprint", serialized)
            self.assertNotIn("inventor_role", serialized)
            self.assertNotIn("source_id", serialized)
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

    def test_public_result_can_be_explicitly_thawed_for_serialization(self):
        _, result = self.run_fixture()
        mutable = thaw(result)
        json.dumps(mutable, ensure_ascii=False)
        mutable["frozen_candidates"][0]["title"] = "local mutable copy"
        self.assertNotEqual(
            mutable["frozen_candidates"][0]["title"],
            result["frozen_candidates"][0]["title"],
        )

    def test_chat_product_wrapper_persists_v3_and_compiles_only_host_selected_substance(self):
        fixture = CognitionFixture()

        class Provider:
            provider_name = "fixture"
            model = "product-v3"
            last_usage = None

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
                yield json.dumps(fixture(role, prompt))

        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
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
                provider=Provider(),
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


if __name__ == "__main__":
    unittest.main()
