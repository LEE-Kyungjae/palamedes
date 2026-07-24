PYTHON ?= python3
PYCACHE_PREFIX ?= /tmp/pycache

.PHONY: test scaffold-test compile scaffold-compile check schema-check package-check

test:
	PYTHONPYCACHEPREFIX=$(PYCACHE_PREFIX) $(PYTHON) -m unittest tests.test_palamedes tests.test_palamedes_server tests.test_palamedes_client tests.test_contracts tests.test_ref_library

scaffold-test:
	PYTHONPYCACHEPREFIX=$(PYCACHE_PREFIX) $(PYTHON) -m unittest scaffolds.palamedes_agents.tests.test_registry scaffolds.palamedes_agents.tests.test_adapter_and_planner_loop scaffolds.palamedes_agents.tests.test_agent_cycle scaffolds.palamedes_agents.tests.test_strategy_benchmark scaffolds.palamedes_agents.tests.test_console scaffolds.palamedes_agents.tests.test_strategy_prompt scaffolds.palamedes_agents.tests.test_strategy_llm scaffolds.palamedes_agents.tests.test_strategy_routes

compile:
	PYTHONPYCACHEPREFIX=$(PYCACHE_PREFIX) $(PYTHON) -m py_compile palamedes.py palamedes_store.py palamedes_agent.py palamedes_server.py palamedes_client.py palamedes_sdk/__init__.py palamedes_sdk/client.py scripts/ref_library.py examples/palamedes_kernel_adapter.py examples/palamedes_planner_host.py tests/test_palamedes.py tests/test_palamedes_server.py tests/test_palamedes_client.py tests/test_contracts.py tests/test_ref_library.py

scaffold-compile:
	PYTHONPYCACHEPREFIX=$(PYCACHE_PREFIX) PYTHONPATH=scaffolds/palamedes_agents/src $(PYTHON) -m py_compile scaffolds/palamedes_agents/src/palamedes_agents/console.py scaffolds/palamedes_agents/src/palamedes_agents/runtime/agent_cycle.py scaffolds/palamedes_agents/src/palamedes_agents/runtime/host_step.py scaffolds/palamedes_agents/src/palamedes_agents/workflows/planner_loop.py scaffolds/palamedes_agents/src/palamedes_agents/workflows/strategy_loop.py scaffolds/palamedes_agents/src/palamedes_agents/workflows/research_loop.py scaffolds/palamedes_agents/src/palamedes_agents/workflows/review_loop.py scaffolds/palamedes_agents/src/palamedes_agents/skills/registry.py scaffolds/palamedes_agents/src/palamedes_agents/strategy_prompt.py scaffolds/palamedes_agents/src/palamedes_agents/strategy_llm.py scaffolds/palamedes_agents/src/palamedes_agents/strategy_routes.py scaffolds/palamedes_agents/src/palamedes_agents/strategy_benchmark.py

check: compile scaffold-compile test scaffold-test

schema-check:
	$(PYTHON) palamedes.py schema --check

package-check:
	PYTHONPYCACHEPREFIX=$(PYCACHE_PREFIX) $(PYTHON) -m py_compile palamedes_sdk/__init__.py palamedes_sdk/client.py
