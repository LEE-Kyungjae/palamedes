# deepplan-agents scaffold

This scaffold is a minimal starting point for a separate `deepplan-agents` repo.

It is intentionally small.
It demonstrates:

- role/profile/capability alignment against a local host action contract
- checked-in skill manifests
- prompt asset references
- deterministic desired-vs-actual skill resolution
- a runnable `deepplan-agents` console for immediate local agent steps
- a minimal DeepPlan adapter surface
- one-step planner / researcher / reviewer loops
- AI-provider-backed strategist loop for problem-solution, emotion, experience, monetization, reference-insight, creative direction, personal profile, outcome learning, and anti-generic evaluation
- OpenAI Responses provider boundary for structured JSON strategy reports
- shared runtime decision gates for `qa` and `health`
- runtime idempotency key and stale conflict retry policies
- host-facing event envelopes for workflow outputs
- a role-aware `host_step` dispatcher over local action contracts
- provenance-preserving Insight RAG with diverse reference-pattern retrieval and a deterministic sufficiency gate

This scaffold does not include:

- queue workers
- network services
- execution runtimes

## Insight RAG

Pass a structured `reference_corpus` to `evaluate_experience_strategy` or `generate_creative_directions`, or ingest references into the default `.deeplan/references.sqlite3` store. The scaffold uses field-weighted BM25, accepts optional semantic scores for hybrid ranking, selects diverse success/failure/counter-view evidence, preserves source IDs, URLs, and quotes, and requires `stop_and_research` when evidence is too thin. Generated insights can be persisted into the canonical DeepPlan evidence, insight, and revision state with `insight-apply`.

## Quick start

Run directly from the scaffold without installing:

```bash
PYTHONPATH=scaffolds/deepplan_agents/src python3 -m deepplan_agents.console agents
PYTHONPATH=scaffolds/deepplan_agents/src python3 -m deepplan_agents.console snapshot
PYTHONPATH=scaffolds/deepplan_agents/src python3 -m deepplan_agents.console provider-health
PYTHONPATH=scaffolds/deepplan_agents/src python3 -m deepplan_agents.console run --role planner --action update_plan
PYTHONPATH=scaffolds/deepplan_agents/src python3 -m deepplan_agents.console prompt
PYTHONPATH=scaffolds/deepplan_agents/src python3 -m deepplan_agents.console retrieve --payload-file reference-query.json
OPENAI_API_KEY=... PYTHONPATH=scaffolds/deepplan_agents/src python3 -m deepplan_agents.console --embedding-provider openai retrieve --payload-file reference-query.json
PYTHONPATH=scaffolds/deepplan_agents/src python3 -m deepplan_agents.console reference-ingest --input-file scaffolds/deepplan_agents/examples/reference-patterns.json
PYTHONPATH=scaffolds/deepplan_agents/src python3 -m deepplan_agents.console reference-list
PYTHONPATH=scaffolds/deepplan_agents/src python3 -m deepplan_agents.console reference-health
PYTHONPATH=scaffolds/deepplan_agents/src python3 -m deepplan_agents.console reference-eval --dataset-file scaffolds/deepplan_agents/evals/reference-retrieval.json
PYTHONPATH=scaffolds/deepplan_agents/src python3 -m deepplan_agents.console insight-apply --report-file strategy-report.json
PYTHONPATH=scaffolds/deepplan_agents/src python3 -m deepplan_agents.console prompt --action generate_creative_directions
PYTHONPATH=scaffolds/deepplan_agents/src python3 -m deepplan_agents.console run --role researcher --action capture_evidence_cycle --session-id local --step-id research-1
PYTHONPATH=scaffolds/deepplan_agents/src python3 -m deepplan_agents.console run --role reviewer --action request_review --session-id local --step-id review-1
```

Strategist execution requires an AI provider:

```bash
OPENAI_API_KEY=... \
PYTHONPATH=scaffolds/deepplan_agents/src \
python3 -m deepplan_agents.console run \
  --role strategist \
  --action evaluate_experience_strategy \
  --provider openai

OPENAI_API_KEY=... \
PYTHONPATH=scaffolds/deepplan_agents/src \
python3 -m deepplan_agents.console run \
  --role strategist \
  --action generate_creative_directions \
  --provider openai

OPENAI_API_KEY=... \
PYTHONPATH=scaffolds/deepplan_agents/src \
python3 -m deepplan_agents.console run \
  --role strategist \
  --action analyze_outcome_learning \
  --provider openai
```

Or install the package and use the console script:

```bash
python3 -m pip install -e scaffolds/deepplan_agents
deepplan-agents agents
deepplan-agents run --role planner --action update_plan
```

Install the optional OpenAI SDK when using the strategy or embedding providers:

```bash
python3 -m pip install -e 'scaffolds/deepplan_agents[openai]'
```

By default the console runs in-process against the current DeepPlan workspace.
To target a running HTTP service instead:

```bash
python3 deepplan_server.py --host 127.0.0.1 --port 8787
deepplan-agents --base-url http://127.0.0.1:8787 run --role planner --action update_plan
```

Each command emits a JSON event envelope with:

- `ok`
- `type`
- `role`
- `summary`
- `gate`
- `session`
- `result`
- `error`

Suggested next files to extend:

- `src/deepplan_agents/adapters/deepplan_adapter.py`
- `src/deepplan_agents/console.py`
- `src/deepplan_agents/workflows/planner_loop.py`
- `src/deepplan_agents/workflows/strategy_loop.py`
- `src/deepplan_agents/strategy_prompt.py`
- `src/deepplan_agents/strategy_llm.py`
- `src/deepplan_agents/strategy_routes.py`
- `src/deepplan_agents/workflows/research_loop.py`
- `src/deepplan_agents/workflows/review_loop.py`
- `src/deepplan_agents/runtime/decision_gate.py`
- `src/deepplan_agents/runtime/policies.py`
- `src/deepplan_agents/runtime/host_events.py`
- `src/deepplan_agents/runtime/host_step.py`
- a real `deepplan_sdk.DeepPlanClient` bootstrap in your application repo
