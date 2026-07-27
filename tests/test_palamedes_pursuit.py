#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path

from palamedes_pursuit import PursuitStore, run_pursuit


class PursuitFixture:
    def __init__(self, domain):
        self.domain, self.calls = domain, []

    def __call__(self, role, prompt):
        self.calls.append(role)
        types = {"paper": ["discover", "explain", "evaluate", "author"], "commodity": ["predict", "explain", "decide", "author", "operate"], "ux": ["design", "evaluate"]}[self.domain]
        if role == "pursuit_intent_interpreter":
            return {"outcome": f"usable {self.domain} result", "intended_audience": "decision owner", "decision_or_change_enabled": "choose the next defensible action", "quality_bar": "traceable and falsifiable", "constraints": [], "non_goals": [], "assumptions_requiring_confirmation": []}
        if role == "epistemic_task_router":
            return {"task_types": types, "rationale_by_type": {item: "required by outcome" for item in types}, "required_claim_level": "bounded", "deliverable_form": self.domain, "update_mode": "periodic" if self.domain == "commodity" else "one-shot"}
        if role == "unknown_map_builder":
            return {"entries": [
                {"unknown_id": "u1", "class": "retrievable", "question": "What evidence exists?", "why_it_matters": "grounds claims", "evidence_needed": "primary sources", "source_time_sensitivity": "current", "decision_reversal_signal": "contradiction"},
                {"unknown_id": "u2", "class": "inferential", "question": "Which explanation survives?", "why_it_matters": "selects model", "evidence_needed": "comparative analysis", "source_time_sensitivity": "bounded", "decision_reversal_signal": "failed prediction"},
                {"unknown_id": "u3", "class": "decision_reversing", "question": "What would reverse the recommendation?", "why_it_matters": "prevents lock-in", "evidence_needed": "predeclared threshold", "source_time_sensitivity": "live", "decision_reversal_signal": "threshold crossed"},
            ]}
        if role == "capability_and_domain_composer":
            capability = {"paper": "literature-and-experiment-design", "commodity": "time-series-and-scenario-analysis", "ux": "interaction-observation-and-browser-probe"}[self.domain]
            return {"capabilities": ["source-retrieval", capability, "adversarial-authoring"], "domain_protocol_acquisition": {"authorities": ["primary sources"], "quality_rules": ["source attribution"]}, "execution_graph": [
                {"node_id": "n1", "purpose": "collect evidence", "capability": "source-retrieval", "inputs": ["objective"], "outputs": ["evidence set"], "falsifier": "no adequate sources", "cost_class": "low", "depends_on": []},
                {"node_id": "n2", "purpose": "test competing accounts", "capability": capability, "inputs": ["evidence set"], "outputs": ["analysis"], "falsifier": "no discrimination", "cost_class": "medium", "depends_on": ["n1"]},
                {"node_id": "n3", "purpose": "compile bounded deliverable", "capability": "adversarial-authoring", "inputs": ["analysis"], "outputs": ["deliverable"], "falsifier": "claims exceed evidence", "cost_class": "low", "depends_on": ["n2"]},
            ], "evidence_policy": {"citations": True, "timestamps": True, "uncertainty": True}, "deliverable_compiler": {"form": self.domain}, "autonomy_envelope": {"automatic_actions": ["read public sources", "analyze local data"], "approval_required_actions": ["purchase data", "contact people", "publish", "execute financial action"], "forbidden_actions": ["fabricate evidence", "claim unrun experiment"]}, "reobservation_policy": {"trigger": "source changes"}}
        if role == "pursuit_adversary":
            return {"critical_failures": [], "repairable_gaps": [], "minimum_disconfirming_probes": ["compare against a baseline"], "verdict": "proceed"}
        if role == "pursuit_governor":
            return {"disposition": "ready", "rationale": "bounded graph", "first_executable_nodes": ["n1"], "human_gates": ["publication"], "stop_conditions": ["evidence unavailable"], "expected_deliverable": f"traceable {self.domain} artifact", "provenance": {"objective": "human", "workflow": "palamedes"}}
        raise AssertionError(role)


class PursuitTests(unittest.TestCase):
    def test_same_kernel_composes_three_different_intellectual_jobs(self):
        cases = {
            "paper": "Find a new research direction in battery recycling and draft a paper.",
            "commodity": "Assess whether copper may rise or fall and write a committee report.",
            "ux": "Make a frequently used conversational workspace effortless without being told the UI solution.",
        }
        with tempfile.TemporaryDirectory() as temporary:
            for domain, objective in cases.items():
                fixture = PursuitFixture(domain)
                record = run_pursuit(ask=fixture, store=PursuitStore(Path(temporary) / domain), objective=objective)
                self.assertEqual(len(fixture.calls), 6)
                self.assertFalse(record["execution_started"])
                self.assertFalse(record["publication_authority_granted"])
                self.assertIn("decision_reversing", {row["class"] for row in record["unknown_map"]["entries"]})
            self.assertEqual(set(run_pursuit(ask=PursuitFixture("commodity"), store=PursuitStore(Path(temporary) / "repeat"), objective=cases["commodity"])["epistemic_routing"]["task_types"]), {"predict", "explain", "decide", "author", "operate"})

    def test_governor_cannot_start_unknown_execution_node(self):
        class Broken(PursuitFixture):
            def __call__(self, role, prompt):
                value = super().__call__(role, prompt)
                if role == "pursuit_governor":
                    value["first_executable_nodes"] = ["invented-node"]
                return value
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "existing execution nodes"):
                run_pursuit(ask=Broken("paper"), store=PursuitStore(Path(temporary)), objective="Research something.")


if __name__ == "__main__":
    unittest.main()
