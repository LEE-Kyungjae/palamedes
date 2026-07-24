# palamedes-agents scaffold

This scaffold is a minimal starting point for a separate `palamedes-agents` repo.

It is intentionally small.
It demonstrates:

- role/profile/capability alignment against a local host action contract
- checked-in skill manifests
- prompt asset references
- deterministic desired-vs-actual skill resolution
- a runnable `palamedes-agents` console for immediate local agent steps
- a minimal Palamedes adapter surface
- one-step planner / researcher / reviewer loops
- AI-provider-backed strategist loop for problem-solution, emotion, experience, monetization, reference-insight, creative direction, personal profile, outcome learning, and anti-generic evaluation
- OpenAI Responses and OpenRouter Chat Completions provider boundaries for
  structured JSON strategy reports
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

Pass a structured `reference_corpus` to `evaluate_experience_strategy` or `generate_creative_directions`, or ingest references into the default `.palamedes/references.sqlite3` store. The scaffold uses field-weighted BM25, accepts optional semantic scores for hybrid ranking, selects diverse success/failure/counter-view evidence, preserves source IDs, URLs, and quotes, and requires `stop_and_research` when evidence is too thin. Generated insights can be persisted into the canonical Palamedes evidence, insight, and revision state with `insight-apply`.

## Quick start

Run directly from the scaffold without installing:

```bash
PYTHONPATH=scaffolds/palamedes_agents/src python3 -m palamedes_agents.console agents
PYTHONPATH=scaffolds/palamedes_agents/src python3 -m palamedes_agents.console snapshot
PYTHONPATH=scaffolds/palamedes_agents/src python3 -m palamedes_agents.console provider-health

OPENROUTER_API_KEY=... \
PYTHONPATH=scaffolds/palamedes_agents/src \
python3 -m palamedes_agents.console provider-health --provider openrouter
PYTHONPATH=scaffolds/palamedes_agents/src python3 -m palamedes_agents.console run --role planner --action update_plan
PYTHONPATH=scaffolds/palamedes_agents/src python3 -m palamedes_agents.console prompt
PYTHONPATH=scaffolds/palamedes_agents/src python3 -m palamedes_agents.console retrieve --payload-file reference-query.json
OPENAI_API_KEY=... PYTHONPATH=scaffolds/palamedes_agents/src python3 -m palamedes_agents.console --embedding-provider openai retrieve --payload-file reference-query.json
PYTHONPATH=scaffolds/palamedes_agents/src python3 -m palamedes_agents.console reference-ingest --input-file scaffolds/palamedes_agents/examples/reference-patterns.json
PYTHONPATH=scaffolds/palamedes_agents/src python3 -m palamedes_agents.console reference-list
PYTHONPATH=scaffolds/palamedes_agents/src python3 -m palamedes_agents.console reference-health
PYTHONPATH=scaffolds/palamedes_agents/src python3 -m palamedes_agents.console reference-eval --dataset-file scaffolds/palamedes_agents/evals/reference-retrieval.json
PYTHONPATH=scaffolds/palamedes_agents/src python3 -m palamedes_agents.console insight-apply --report-file strategy-report.json
PYTHONPATH=scaffolds/palamedes_agents/src python3 -m palamedes_agents.console prompt --action generate_creative_directions
PYTHONPATH=scaffolds/palamedes_agents/src python3 -m palamedes_agents.console run --role researcher --action capture_evidence_cycle --session-id local --step-id research-1
PYTHONPATH=scaffolds/palamedes_agents/src python3 -m palamedes_agents.console run --role reviewer --action request_review --session-id local --step-id review-1
```

Strategist execution requires an AI provider:

OpenRouter uses the same local strategy schema and validation boundary. Select
an OpenRouter model explicitly or set `PALAMEDES_OPENROUTER_MODEL`:

```bash
OPENROUTER_API_KEY=... \
PYTHONPATH=scaffolds/palamedes_agents/src \
python3 -m palamedes_agents.console llm \
  --action generate_creative_directions \
  --provider openrouter \
  --model <provider/model>
```

The API key is read only from `OPENROUTER_API_KEY`; it is not persisted by the
scaffold.

```bash
OPENAI_API_KEY=... \
PYTHONPATH=scaffolds/palamedes_agents/src \
python3 -m palamedes_agents.console run \
  --role strategist \
  --action evaluate_experience_strategy \
  --provider openai

OPENAI_API_KEY=... \
PYTHONPATH=scaffolds/palamedes_agents/src \
python3 -m palamedes_agents.console run \
  --role strategist \
  --action generate_creative_directions \
  --provider openai

OPENAI_API_KEY=... \
PYTHONPATH=scaffolds/palamedes_agents/src \
python3 -m palamedes_agents.console run \
  --role strategist \
  --action analyze_outcome_learning \
  --provider openai
```

Run one bounded agent cycle that observes Palamedes state, asks the strategist
provider for a report, persists grounded reference insights, validates and
executes allowed `next_actions`, and returns the post-cycle state:

```bash
OPENAI_API_KEY=... \
PYTHONPATH=scaffolds/palamedes_agents/src \
python3 -m palamedes_agents.console cycle \
  --action evaluate_experience_strategy \
  --provider openai \
  --session-id local-trial \
  --wake-id first-pass
```

The cycle stops on provider failure, capability denial, action failure, its
action limit, or a human-review request. Palamedes remains the plan-state
kernel; the cycle runner owns bounded orchestration.

Prepare and score the three-case blinded comparison after baseline and
Palamedes reports have been written as `<case-id>.json` files:

```bash
PYTHONPATH=scaffolds/palamedes_agents/src \
python3 -m palamedes_agents.console benchmark-prepare \
  --dataset-file scaffolds/palamedes_agents/evals/agent-cycle-cases.json \
  --baseline-dir eval-results/baseline \
  --candidate-dir eval-results/palamedes \
  --packet-file eval-results/blind-packet.json \
  --key-file eval-results/answer-key.json \
  --seed "$BENCHMARK_SECRET"

PYTHONPATH=scaffolds/palamedes_agents/src \
python3 -m palamedes_agents.console benchmark-score \
  --packet-file eval-results/blind-packet.json \
  --key-file eval-results/answer-key.json \
  --reviews-file eval-results/reviews.json \
  --output-file eval-results/result.json
```

Do not give `answer-key.json` to reviewers. The scorer enforces the plan gate:
three reviewed cases, at least two Palamedes wins, and at least one attributable
planning decision.

Or install the package and use the console script:

```bash
python3 -m pip install -e scaffolds/palamedes_agents
palamedes-agents agents
palamedes-agents run --role planner --action update_plan
```

Install the optional OpenAI SDK when using the strategy or embedding providers:

```bash
python3 -m pip install -e 'scaffolds/palamedes_agents[openai]'
```

By default the console runs in-process against the current Palamedes workspace.
To target a running HTTP service instead:

```bash
python3 palamedes_server.py --host 127.0.0.1 --port 8787
palamedes-agents --base-url http://127.0.0.1:8787 run --role planner --action update_plan
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

- `src/palamedes_agents/adapters/palamedes_adapter.py`
- `src/palamedes_agents/console.py`
- `src/palamedes_agents/workflows/planner_loop.py`
- `src/palamedes_agents/workflows/strategy_loop.py`
- `src/palamedes_agents/strategy_prompt.py`
- `src/palamedes_agents/strategy_llm.py`
- `src/palamedes_agents/strategy_routes.py`
- `src/palamedes_agents/workflows/research_loop.py`
- `src/palamedes_agents/workflows/review_loop.py`
- `src/palamedes_agents/runtime/decision_gate.py`
- `src/palamedes_agents/runtime/policies.py`
- `src/palamedes_agents/runtime/host_events.py`
- `src/palamedes_agents/runtime/host_step.py`
- a real `palamedes_sdk.PalamedesClient` bootstrap in your application repo
