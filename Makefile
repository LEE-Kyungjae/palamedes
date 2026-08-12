PYTHON ?= python3
PYCACHE_PREFIX ?= /tmp/pycache

.PHONY: test scaffold-test compile scaffold-compile reasoning-cycles-check check schema-check package-check

test:
	PYTHONPYCACHEPREFIX=$(PYCACHE_PREFIX) $(PYTHON) -m unittest tests.test_palamedes_opportunity tests.test_palamedes_architecture_transfer tests.test_palamedes_cognition_v3 tests.test_palamedes_evidence_bundle tests.test_palamedes_product_cognition_contract_fixture
	PYTHONPYCACHEPREFIX=$(PYCACHE_PREFIX) $(PYTHON) -m unittest tests.test_palamedes tests.test_palamedes_chat tests.test_palamedes_lifecycle tests.test_palamedes_gate_resolution tests.test_palamedes_satisfaction tests.test_palamedes_cost_router tests.test_palamedes_product_alignment tests.test_palamedes_storage tests.test_palamedes_observe tests.test_palamedes_observatory tests.test_palamedes_invention tests.test_palamedes_pursuit tests.test_palamedes_workspace tests.test_palamedes_watch tests.test_palamedes_knowledge tests.test_palamedes_prompt tests.test_palamedes_reference_intelligence tests.test_palamedes_proof tests.test_palamedes_server tests.test_palamedes_client tests.test_contracts tests.test_ref_library tests.test_palamedes_mission

scaffold-test:
	PYTHONPYCACHEPREFIX=$(PYCACHE_PREFIX) $(PYTHON) -m unittest scaffolds.palamedes_agents.tests.test_registry scaffolds.palamedes_agents.tests.test_adapter_and_planner_loop scaffolds.palamedes_agents.tests.test_agent_cycle scaffolds.palamedes_agents.tests.test_strategy_benchmark scaffolds.palamedes_agents.tests.test_console scaffolds.palamedes_agents.tests.test_strategy_prompt scaffolds.palamedes_agents.tests.test_strategy_llm scaffolds.palamedes_agents.tests.test_strategy_routes

compile:
	PYTHONPYCACHEPREFIX=$(PYCACHE_PREFIX) $(PYTHON) -m py_compile palamedes_opportunity.py palamedes_architecture_transfer.py palamedes_cognition_v3.py palamedes_evidence_bundle.py tests/test_palamedes_opportunity.py tests/test_palamedes_architecture_transfer.py tests/test_palamedes_cognition_v3.py tests/test_palamedes_evidence_bundle.py tests/test_palamedes_product_cognition_contract_fixture.py
	PYTHONPYCACHEPREFIX=$(PYCACHE_PREFIX) $(PYTHON) -m py_compile palamedes.py palamedes_store.py palamedes_agent.py palamedes_chat.py palamedes_lifecycle.py palamedes_gate_resolution.py palamedes_satisfaction.py palamedes_cost_router.py palamedes_storage.py palamedes_observe.py palamedes_observatory.py palamedes_invention.py palamedes_pursuit.py palamedes_workspace.py palamedes_watch.py palamedes_thought.py palamedes_knowledge.py palamedes_epistemics.py palamedes_prompt.py palamedes_reference_intelligence.py palamedes_product_alignment.py palamedes_vision.py palamedes_vision_scout.py palamedes_vision_benchmark.py palamedes_proof.py palamedes_server.py palamedes_client.py palamedes_mission/*.py palamedes_sdk/__init__.py palamedes_sdk/client.py scripts/ref_library.py scripts/materialize_reasoning_cycles.py examples/palamedes_kernel_adapter.py examples/palamedes_planner_host.py tests/test_palamedes.py tests/test_palamedes_chat.py tests/test_palamedes_lifecycle.py tests/test_palamedes_gate_resolution.py tests/test_palamedes_satisfaction.py tests/test_palamedes_cost_router.py tests/test_palamedes_product_alignment.py tests/test_palamedes_storage.py tests/test_palamedes_observe.py tests/test_palamedes_observatory.py tests/test_palamedes_invention.py tests/test_palamedes_pursuit.py tests/test_palamedes_workspace.py tests/test_palamedes_watch.py tests/test_palamedes_knowledge.py tests/test_palamedes_prompt.py tests/test_palamedes_reference_intelligence.py tests/test_palamedes_proof.py tests/test_palamedes_server.py tests/test_palamedes_client.py tests/test_contracts.py tests/test_ref_library.py tests/test_palamedes_mission.py

scaffold-compile:
	PYTHONPYCACHEPREFIX=$(PYCACHE_PREFIX) PYTHONPATH=scaffolds/palamedes_agents/src $(PYTHON) -m py_compile scaffolds/palamedes_agents/src/palamedes_agents/console.py scaffolds/palamedes_agents/src/palamedes_agents/runtime/agent_cycle.py scaffolds/palamedes_agents/src/palamedes_agents/runtime/host_step.py scaffolds/palamedes_agents/src/palamedes_agents/workflows/planner_loop.py scaffolds/palamedes_agents/src/palamedes_agents/workflows/strategy_loop.py scaffolds/palamedes_agents/src/palamedes_agents/workflows/research_loop.py scaffolds/palamedes_agents/src/palamedes_agents/workflows/review_loop.py scaffolds/palamedes_agents/src/palamedes_agents/skills/registry.py scaffolds/palamedes_agents/src/palamedes_agents/strategy_prompt.py scaffolds/palamedes_agents/src/palamedes_agents/strategy_llm.py scaffolds/palamedes_agents/src/palamedes_agents/strategy_routes.py scaffolds/palamedes_agents/src/palamedes_agents/strategy_benchmark.py

reasoning-cycles-check:
	$(PYTHON) scripts/materialize_reasoning_cycles.py --check

check: compile scaffold-compile reasoning-cycles-check test scaffold-test

schema-check:
	$(PYTHON) palamedes.py schema --check

package-check:
	PYTHONPYCACHEPREFIX=$(PYCACHE_PREFIX) $(PYTHON) -m py_compile palamedes_sdk/__init__.py palamedes_sdk/client.py
