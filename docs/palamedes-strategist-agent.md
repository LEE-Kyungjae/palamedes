# Palamedes Strategist Agent

This document captures the product-intelligence agent direction for Palamedes.
It is based on the premise that a successful service is not only a problem and a solution.
It is a repeatable experience that converts desire, emotion, behavior, and timing into retention or revenue.

## Thesis

Palamedes should not become a generic planning document generator.

The stronger product direction is:

- attack weak ideas before execution
- prevent LLM agents from producing average AI wrappers
- convert ideas into monetizable user experience loops
- use external behavior references as creative raw material
- generate non-generic directions by recombining reference patterns
- adapt critique to the user's repeated planning weaknesses
- enter an already-started project without assuming a clean slate
- learn from shipped outcomes, usage signals, revenue signals, retention, and feedback
- preserve the planning state, evidence, and revision trail in Palamedes

The strategist agent is the layer that turns this into an operating loop.

## Why A Strategist Role

Planner, researcher, and reviewer are necessary but not sufficient.

- `planner` keeps direction state coherent.
- `researcher` captures evidence and references.
- `reviewer` handles human review and restore decisions.
- `strategist` judges whether an idea has product force before anyone builds it.

The strategist asks:

- Is the problem narrow and painful enough?
- Is the solution actually matched to that problem?
- Which desire or emotion creates buying or returning behavior?
- Is there a real experience loop, not just a feature list?
- Where is the monetization moment?
- Is this another generic LLM-generated service?
- What external references produced the core insight?
- What ethical, trust, community, or regulatory risk comes from the emotional loop?

## Core Evaluation Frame

The strategist evaluates ideas through these axes:

| Axis | Question |
| --- | --- |
| Problem-Solution | Who has the problem, how painful is it, what current alternative exists, and why is this solution the right response? |
| Desire-Emotion | Which desire or emotion moves the user: fear, greed, control, status, belonging, envy, anger, relief, or achievement? |
| Experience Loop | What is the trigger, emotional state, action, reward, monetization moment, and return reason? |
| Monetization Trigger | What exact moment makes payment feel natural or urgent? |
| Anti-Generic | Is this just another AI dashboard, todo app, CRM, assistant, or productivity wrapper? |
| Reference-to-Insight | Which behavior data, papers, reviews, success cases, or failure cases created the insight? |
| Creative Recombination | Which transferable behavior principles can become non-obvious product directions? |
| Personal Profile | Which repeated planning weakness should the strategist compensate for next time? |
| Project Context | Is this a new project, mid-project rescue, pivot, or continuation decision? |
| Outcome Learning | What changed after shipping or testing, and how should plan/profile change? |
| Risk Boundary | Does the loop rely on exploitation, toxic conflict, resentment, or fragile trust? |

## Product Loop

The intended loop is:

```text
idea
  -> strategist evaluation
  -> reference discovery if evidence is weak
  -> plan update if the direction is sharp
  -> review request if the decision is risky
  -> build only after the idea survives the gate
```

The strategist does not replace Palamedes's kernel.
It reads the current plan, produces a strategy report, and may request review.
It should not bypass host capabilities or mutate plan state directly.

## First AI-First Scaffold

The scaffold includes:

- role: `strategist`
- profile: `strategist_product`
- actions:
  - `evaluate_experience_strategy`
  - `generate_creative_directions`
  - `analyze_outcome_learning`
- skills:
  - `problem-solution-pressure`
  - `desire-emotion-map`
  - `experience-loop-design`
  - `anti-generic-insight`
  - `reference-to-insight`
  - `creative-recombination`
  - `personal-planning-profile`
  - `mid-project-intake`
  - `outcome-learning-loop`

Build the AI prompt bundle locally:

```bash
PYTHONPATH=scaffolds/palamedes_agents/src \
python3 -m palamedes_agents.console prompt \
  --payload-json '{"idea":"AI productivity dashboard","target_user":"solo builder","solution":"dashboard"}'
```

The host must inject an AI strategy provider before running `evaluate_experience_strategy`.
The strategist execution path should not fall back to rule-based scoring.
Deterministic code is allowed only for prompt construction, JSON schema validation, route validation, and provider mocks in tests.

Run with a real OpenAI provider:

```bash
OPENAI_API_KEY=... \
PYTHONPATH=scaffolds/palamedes_agents/src \
python3 -m palamedes_agents.console run \
  --role strategist \
  --action evaluate_experience_strategy \
  --provider openai
```

The default OpenAI model is `gpt-5.5`.
Set `--model` or `PALAMEDES_OPENAI_MODEL` to override it.
The provider uses structured JSON output and validates the result against the local strategy report schema before the host consumes it.

OpenRouter is also available through its OpenAI-compatible Chat Completions
endpoint. It reads `OPENROUTER_API_KEY` only at runtime and preserves the same
local report validation:

```bash
OPENROUTER_API_KEY=... \
PYTHONPATH=scaffolds/palamedes_agents/src \
python3 -m palamedes_agents.console llm \
  --action generate_creative_directions \
  --provider openrouter \
  --model <provider/model>
```

Deterministic tests use an injected client and do not require an API call.

For creative direction generation:

```bash
PYTHONPATH=scaffolds/palamedes_agents/src \
python3 -m palamedes_agents.console prompt \
  --action generate_creative_directions
```

This action is for zero-to-one ideation and mid-project rescue or pivot work.
It accepts `entry_mode`, `project_stage`, `existing_artifacts`, `current_plan`, `constraints`, `pivot_signals`, references, behavior signals, and a `personal_profile`.

Run creative direction generation with a real provider:

```bash
OPENAI_API_KEY=... \
PYTHONPATH=scaffolds/palamedes_agents/src \
python3 -m palamedes_agents.console run \
  --role strategist \
  --action generate_creative_directions \
  --provider openai
```

Run outcome learning after a project has shipped, pivoted, or collected usage signals:

```bash
OPENAI_API_KEY=... \
PYTHONPATH=scaffolds/palamedes_agents/src \
python3 -m palamedes_agents.console run \
  --role strategist \
  --action analyze_outcome_learning \
  --provider openai
```

Expected behavior:

- generic service patterns are detected
- weak problem-solution structure is flagged
- missing emotional demand and repeat loop are called out
- missing evidence is converted into concrete research questions
- the agent proposes a sharper positioning rewrite
- monetization is tied to a specific trigger and emotional state
- negative emotional loops are surfaced as risk boundaries
- output recommends `revise_before_build` or `stop_and_research`

## Strategy Report Shape

The AI strategist must return a structured report with these fields:

- `overall_score`
- `decision`
- `axes`
- `emotion_drivers`
- `risk_boundaries`
- `generic_patterns`
- `missing_fields`
- `risks`
- `recommendations`
- `research_questions`
- `next_actions`
- `positioning_rewrite`
- `monetization_moment`
- `reference_insights`
- `creative_directions`
- `personal_profile_updates`
- `project_context`
- `outcome_learning`

The model owns judgment quality.
Hosts own deterministic validation of the report shape, next-action routes, and capability boundaries.

`reference_insights` is the key creativity bridge.
Each item converts a source into observed behavior, emotion driver, monetization moment, repeat loop, transferable principle, and application to the current plan.

`creative_directions` recombines those principles into non-generic product directions.
This is where Palamedes should fight the common LLM failure mode of producing the same dashboard, assistant, todo, CRM, or productivity shell.

`personal_profile_updates` lets Palamedes adapt over time to the user's planning pattern, such as repeatedly starting from implementation, skipping reference evidence, or overusing dashboard-shaped solutions.

`project_context` keeps Palamedes useful after a project has already started.
Mid-project analysis should use current artifacts, constraints, traction, pivot signals, and sunk-cost pressure instead of pretending the user is at day zero.

`outcome_learning` closes the loop after work has happened.
It should convert shipped changes, usage, revenue, retention, feedback, failed assumptions, and new constraints into plan adjustments, next evidence, and personal profile implications.

`next_actions` is the bridge from judgment to execution.
The strategist does not execute actions directly.
It recommends host-understood actions such as:

- `update_plan` when an idea should be sharpened or preserved
- `capture_evidence_cycle` when research is required before build
- `request_review` when a risk boundary needs human judgment

Each next action includes:

- `target_role`: the agent role that should execute it
- `action`: the host action name
- `priority`: `low`, `medium`, or `high`
- `reason`
- `payload`

## AI Reasoning Contract

The scaffold includes a provider-neutral prompt bundle for the strategist:

- system prompt: `scaffolds/palamedes_agents/src/palamedes_agents/prompts/strategist-system.md`
- output schema: `scaffolds/palamedes_agents/src/palamedes_agents/schemas/strategy-report.schema.json`
- prompt builder: `scaffolds/palamedes_agents/src/palamedes_agents/strategy_prompt.py`
- provider boundary: `scaffolds/palamedes_agents/src/palamedes_agents/strategy_llm.py`

The prompt bundle includes:

- the idea payload
- the current Palamedes snapshot
- a deterministic `reference_retrieval` result when `reference_corpus` or `reference_store_path` is supplied
- the required JSON schema

### Insight RAG contract

Strategy actions may receive a `reference_corpus` array directly or a `reference_store_path` pointing to a persistent SQLite store. Each entry is a structured pattern rather than an arbitrary text chunk:

```json
{
  "reference_id": "failed-wrapper-01",
  "source": "Founder postmortem",
  "source_url": "https://example.com/postmortem",
  "source_type": "failure_case",
  "context": "Solo builders shipping AI wrappers",
  "problem": "Demand was assumed before repeated behavior was observed",
  "mechanism": "Feature novelty replaced a durable user loop",
  "outcome": "Initial trials did not convert into retention",
  "failure_boundary": "The pattern may not transfer when distribution is already proven",
  "evidence_quotes": ["Users tried the demo but did not return."],
  "applicable_axes": ["differentiation", "risk_signal"],
  "confidence": 78
}
```

`palamedes_agents.reference_rag` normalizes these records, applies field-weighted BM25, optionally combines host-provided semantic scores, selects across success, failure, counter-view, behavior, review, and research categories, and returns a quality gate. The ranking boundary remains replaceable by an embedding provider or reranker without changing the prompt contract.

The console can generate semantic scores with OpenAI embeddings and combine them with BM25:

```bash
python3 -m pip install -e 'scaffolds/palamedes_agents[openai]'

OPENAI_API_KEY=... \
PYTHONPATH=scaffolds/palamedes_agents/src \
python3 -m palamedes_agents.console \
  --embedding-provider openai \
  --embedding-model text-embedding-3-small \
  retrieve \
  --payload-json '{"idea":"prevent generic product directions"}'
```

The adapter sends the query and reference-pattern texts as one embeddings batch, calculates cosine similarity locally, and injects only the resulting scores into hybrid ranking. Raw corpus contents and the local store path are removed from the strategist's `idea_payload`; only selected retrieval context reaches the model. The embeddings request follows the official create-embeddings contract: an array of input strings returns ordered embedding vectors. See the [OpenAI embeddings API reference](https://developers.openai.com/api/reference/resources/embeddings/methods/create).

The quality gate is deterministic:

- at least two relevant references
- at least two source types
- at least one source URL or evidence quote

If the gate is insufficient, the provider must return `stop_and_research`. If it is sufficient, every `reference_insights` item must cite retrieved `reference_ids`; citations outside the retrieved context are rejected. Each insight also carries source URLs, evidence quotes, transfer assumptions, a disconfirming signal, and confidence.

### Persistent ingestion and evaluation

The console persists references in `.palamedes/references.sqlite3` by default. JSON and JSONL inputs preserve structured fields. Text and HTTP(S) inputs are collected as provenance-bearing raw patterns for later AI extraction.

```bash
PYTHONPATH=scaffolds/palamedes_agents/src \
python3 -m palamedes_agents.console reference-ingest \
  --input-file references.json

PYTHONPATH=scaffolds/palamedes_agents/src \
python3 -m palamedes_agents.console reference-ingest \
  --url https://example.com/postmortem \
  --source-type failure_case

PYTHONPATH=scaffolds/palamedes_agents/src \
python3 -m palamedes_agents.console retrieve \
  --payload-json '{"idea":"prevent generic product directions"}'
```

Content hashes prevent duplicate records while stable reference IDs support updates. The checked-in evaluation set measures recall@k, reciprocal rank, source-type coverage, and sufficiency-gate accuracy:

```bash
PYTHONPATH=scaffolds/palamedes_agents/src \
python3 -m palamedes_agents.console reference-eval \
  --dataset-file scaffolds/palamedes_agents/evals/reference-retrieval.json
```

After a provider returns a grounded strategy report, persist its reference insights into canonical Palamedes state:

```bash
PYTHONPATH=scaffolds/palamedes_agents/src \
python3 -m palamedes_agents.console insight-apply \
  --report-file strategy-report.json
```

Each insight write uses a stable idempotency key and creates linked `reference_extraction` evidence plus insight/replan revision history.

Generate the prompt bundle without calling a model:

```bash
PYTHONPATH=scaffolds/palamedes_agents/src \
python3 -m palamedes_agents.console prompt
```

This keeps provider integration separate from the product reasoning contract.
Any OpenAI, local model, or hosted agent adapter should preserve the same report shape.

The provider boundary is intentionally small:

```python
class StrategyLLMProvider(Protocol):
    def complete_json(self, *, messages, schema) -> dict:
        ...
```

That means a real adapter only needs to:

1. receive the prompt messages and report schema
2. call the model with structured JSON output
3. return a JSON object
4. let `run_strategy_llm` validate the report shape before the host consumes it

The scaffold includes a static provider only for tests and local contract checks.
It is a provider mock, not a product judgment fallback.

## Routing Next Actions

The scaffold also includes a route validator:

- route helper: `scaffolds/palamedes_agents/src/palamedes_agents/strategy_routes.py`
- console command: `palamedes-agents route`

It checks each `next_actions` item against the local host action contract.
For example, a `target_role` of `researcher` can receive `capture_evidence_cycle`, but a `reviewer` cannot receive `update_plan`.

This keeps LLM output useful without letting it bypass role capabilities.

## Design Rule

Palamedes should not make the user feel that planning is paperwork.
It should make the user feel that weak ideas are being attacked before they waste build time.

The emotional promise of the product is:

- less anxiety about building the wrong thing
- more confidence that the direction has market and emotional force
- higher odds of finding non-generic service ideas
- a stronger sense of control over AI-driven execution
