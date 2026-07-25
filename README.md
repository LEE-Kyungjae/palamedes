# Palamedes

<p align="center">
  <strong>English</strong> · <a href="README.ko.md">한국어</a>
</p>

<p align="center">
  <img src="assets/palamedes.png" alt="Palamedes" width="100%">
</p>

> **Palamedes decides what mission is worth planning before execution agents
> decide how to implement it.**

Palamedes is a research-alpha autonomous pre-planner and plan-state kernel. It
works before the familiar `planner -> task -> implementation` pipeline:
noticing what matters, forming competing interpretations, originating a
justified mission, attempting to falsify it, and handing only the surviving
mission to downstream agents.

It treats a plan as revisionable state rather than disposable text. Alongside
goals, evidence, hypotheses, and restore points, Palamedes can preserve
`view_transitions`: what was previously believed, what changed the view, what
became visible, what the new frame may hide, and which probe should follow.
It also distinguishes inquiry from commitment, reference collection from
reference influence, and ordinary tasks from development steps intended to
produce new information.

Palamedes began with a question: if language models tend toward likely,
average answers, where can originality come from? Its working answer is not
"one brilliant generation." Originality can emerge through accumulated changes
of view: many partial discoveries, explicit disagreement, contact with outside
evidence, and a new frame that makes a previously invisible move possible.
Retrieval, debate, and multi-agent competition are useful only when they change
or challenge a decision—not when they merely add more text.

Palamedes does not claim to manufacture originality or guarantee startup
success. It aims to automate more of the judgment that still precedes planning,
but treats that authority as something to earn empirically rather than assume.
It makes the reasoning before execution inspectable and testable without
silently rewriting the path taken. The current inquiry, including counterpoints
and unresolved tensions, is preserved in
[`PALAMEDES_INQUIRY.md`](PALAMEDES_INQUIRY.md).

The current pre-planner hypothesis and the mission contract passed to downstream
agents are defined in
[`docs/palamedes-pre-planner-contract.md`](docs/palamedes-pre-planner-contract.md).
The first 400 dependent reasoning moves developed and pressure-tested this
view. Cycle 401 then applied real retrieval pressure and exposed a concrete
failure rather than declaring success. The records are
available as [separate cycle records](docs/inquiry/reasoning-cycles/README.md).

```text
world signals and accumulated references
  -> competing interpretations
  -> candidate missions
  -> evidence, criticism, and falsification
  -> selected mission contract + non-goals
  -> planner -> tasks -> implementation
  -> outcome signals back to Palamedes
```

## Current Status

**Research Alpha.** The planning kernel is implemented and heavily tested. The
autonomous pre-planner is an active, falsifiable product hypothesis.

- `core` contract surfaces such as persisted plan state, fingerprint conflict semantics, restore behavior, and documented HTTP envelopes are treated as stable according to `STABILITY.md`
- `reference` surfaces such as host orchestration contracts, reference adapters, and example integrations are still experimental
- `inquiry` surfaces such as view-transition lineage and longitudinal evaluation are active product hypotheses, not settled doctrine
- the repository currently ships a canonical Python reference surface plus a thin TypeScript HTTP consumer

| Evidence level | Current result |
| --- | --- |
| Stable plan-state kernel | Implemented with revision, restore, conflict, QA, and conformance surfaces |
| Bounded pre-planner contracts | Implemented and covered by 1,209 mission tests and 298 experimental schemas |
| Internal reasoning development | 401 recorded dependent cycles |
| First real retrieval contact | 1,624 evidence records and 837 components indexed |
| Reference-treatment safety | Correctly blocked the first packet with 9 explicit reasons |
| Equal-information baseline vs treatment | `proof-002`: Palamedes won 8/9 blinded model-review votes and all 3 case majorities |
| Generation cost | Palamedes used 4.26x baseline input tokens; cost-adjusted superiority is not proven |
| Equal-call strong comparator | `proof-003`: Palamedes won 7/9 votes and 2/3 cases with 12 calls each and 1.045x input tokens |
| Attributable downstream choice | 1 recorded: `proof-002` mission caused the `proof-003` equal-call experiment before feature expansion |
| Owner labor retirement | Not yet owner-attested |

The first cross-repository case targets `insight-rag`. Palamedes selected a
counterfactual action-choice benchmark instead of immediately expanding its
analyzer or corpus. Its first real treatment packet was low-confidence and
contained unrelated cache/TTL/dedup guidance for a voice-turn tracing task.
Palamedes therefore blocked the packet rather than laundering retrieval into
authority. See the [preregistration](experiments/case-001-insight-rag/preregistration.md),
[paired pilot task](experiments/case-001-insight-rag/pilot-task.md), and
[cycle 401 record](docs/inquiry/reasoning-cycles/cycle-401.md).

The first preregistered comparison now provides initial evidence that Palamedes
produces more useful upstream missions: three fresh-session, origin-blinded
Codex reviewers cast 8 of 9 votes for Palamedes, giving it the majority in all
three cases. This is model-review evidence, not independent human validation.
It also cost 4.26 times the baseline input tokens, so cost-adjusted superiority
and downstream outcome improvement remain unproven. A second preregistered run
then compared Palamedes with a strong four-call candidate tournament. Palamedes
won 7 of 9 votes and two of three cases while using 1.045 times the input
tokens. This demonstrates the narrow same-model, equal-call claim, not
independent human or downstream outcome superiority. See the
[`proof-002`](experiments/proof-runs/proof-002/RESULT.md) and
[`proof-003`](experiments/proof-runs/proof-003/RESULT.md) results.

The executable three-project proof program is documented in
[`experiments/PROOF.md`](experiments/PROOF.md). It freezes equal information
packets before generation, separates a one-shot baseline from the four-role
Palamedes condition, blinds origin during review, reports compute and token
asymmetry, and refuses to promote mission preference into a product claim
without an attributable downstream choice and an owner labor-retirement record.

Use it when:

- you have ideas but do not know what to validate first
- AI is helping you build fast, but direction keeps drifting
- you need a clear reason to choose one path and kill others
- you want evidence, failure criteria, and replanning history in one place

It keeps planning state in your repo with:

- one current plan
- explicit evidence and hypotheses
- traceable changes of view
- revision history
- restore points
- a defined moment to replan

It is intentionally `plan-only`. Palamedes does not run tasks, schedule workflows, or own delivery.

## Architecture

Palamedes is organized around one planning kernel with a few integration surfaces around it.

```text
palamedes/
├── palamedes.py                    # Core planning kernel and CLI
├── palamedes_chat.py               # AI terminal and cognition cycle
├── palamedes_observe.py            # Bounded, redacted workspace observation
├── palamedes_watch.py              # Event-driven autonomous observation loop
├── palamedes_thought.py            # Pre-mission thought and discovery incubation
├── palamedes_knowledge.py          # Temporal self/world claims and unknown boundaries
├── palamedes_mission.py            # Experimental pre-planner contracts and gates
├── palamedes_server.py             # Local HTTP transport
├── palamedes_sdk/                  # Packaged Python client surface
├── palamedes_reference_adapter.py  # Canonical Python reference adapter
├── palamedes_reference_host.py     # Canonical Python reference host
├── palamedes_reference_consumer.ts # Thin TypeScript HTTP consumer
├── schemas/experimental/           # Machine-checkable research contracts
├── experiments/                    # Preregistered empirical cases
├── docs/inquiry/reasoning-cycles/  # Dependent reasoning lineage
├── spec/                           # Public contract entrypoints
└── tests/contracts/                # Fixture-backed conformance cases
```

Separation of concerns:

| Layer | Responsibility |
| --- | --- |
| `core` | Persisted plan state, evidence, hypothesis log, revision history, QA, conflict and restore semantics |
| `mission` | Candidate generation, criticism, falsification, selection, non-goals, and handoff contracts |
| `transport` | CLI, HTTP, and agent wrapper access to the same planning kernel |
| `reference` | Python host/adapter and TypeScript consumer for real integration examples |
| `experiment` | Preregistration, paired comparison, evidence lineage, and outcome evaluation |
| `conformance` | Contract fixtures and runners that verify stable adopter-facing behavior |

The important design choice is that a mission must earn the right to become a
plan. Once accepted, the plan becomes the source of truth. Everything else
exists to challenge the mission, improve the plan, mutate it safely, or verify
that another implementation behaves the same way.

## Planning Flow

The experimental pre-planner loop is:

```text
notice signal -> frame interpretations -> generate rival missions
      ↑                                      ↓
outcomes <- learn from execution <- falsify and select
```

The stable plan-state loop is:

```text
accept mission contract
    ↓
write plan state
    ↓
add evidence, hypotheses, and view transitions
    ↓
review plan quality
    ↓
replan or restore when the evidence changes
```

In transport terms, the same loop looks like this:

```text
client/tool writes plan
    ↓
fingerprint guard checks stale writes
    ↓
plan revision is recorded
    ↓
QA and health surfaces stay inspectable
    ↓
history / restore / conformance stay available to other consumers
```

## Why Use It

Palamedes is for the layer before execution:

- what to build
- why now
- what evidence supports it
- what would invalidate it
- when to replan

In the AI era, execution is getting cheaper while direction is not.

More systems can generate code, content, tasks, and workflows.
That does not solve the harder problem:

- choosing the right direction
- rejecting weak directions early
- finding better evidence before execution hardens the wrong path
- keeping product and business intent coherent over time

Palamedes exists to reduce that failure mode.

## Product Boundary

Palamedes is `plan-only` by design.

Palamedes should own:

- signal interpretation and idea discovery
- competing frames and candidate missions
- criticism, falsification, and direction selection
- mission contracts, non-goals, and planning logic
- success and failure criteria
- evidence-backed replanning
- revision-aware recovery

Palamedes should not own:

- task execution orchestration
- delivery automation
- general agent runtime concerns
- workflow scheduling
- channel or chat surfaces

Those layers can be built around Palamedes, but they should not blur the purpose of this repo.

## Works With Execution Agents

Palamedes is not a replacement for agent runtimes. LangGraph, Microsoft Agent
Framework, CrewAI, GitHub Agentic Workflows, Codex, Claude, or other execution
systems can consume a Palamedes mission contract and decide how to plan and
implement it.

```text
Palamedes
  mission / rationale / evidence / falsifiers / non-goals
      ↓
external planner or agent runtime
  plan / tasks / tools / implementation
      ↓
observable outcomes returned to Palamedes
```

Its authority ends at the mission boundary. It may recommend, reject, or reopen
a direction; it does not silently acquire delivery authority.

## What Makes It Different

Palamedes is not:

- a note-taking app
- a generic project manager
- a workflow orchestrator
- an execution agent runtime
- a loose PRD template

Palamedes is:

- a mission-origin and falsification layer before planning
- a structured decision state in your repo
- an evidence-backed planning loop
- a versioned history of why the plan changed
- a safe replan and restore system for direction changes

The core unit is the current `plan`.
Everything else exists to improve plan quality over time:

- `evidence` tests whether the plan is grounded
- `hypothesis_log` tracks bets and outcomes
- `view_transitions` preserves why the current frame changed, what the new
  frame may hide, and which probe should follow
- `revisions` show how the plan changed
- `restore` lets you safely recover a better prior direction

## Access Surfaces

Palamedes currently ships four access surfaces around the same planning core:

| Surface | Purpose |
| --- | --- |
| CLI | Local-first planning workflows in the repo |
| HTTP service | Local integration for editors, sidecars, and non-Python consumers |
| Agent wrapper | Slash-command and natural-language planning control |
| Python client | Typed integration with conflict/retry handling |

The core guarantees across these surfaces are:

- a consistent plan schema
- explicit contract and implementation versions
- revision history and safe restore preview
- stale-write protection with fingerprints
- storage health and recovery diagnostics
- fixture-backed conformance checks for stable public behavior

## First Empirical Case

The first case did not produce a triumph. It produced a useful refusal:

- signal: `insight-rag` had ranking benchmarks but no evidence that its output improved an action choice
- rival missions: deepen the analyzer, expand the corpus, or test the causal link between retrieved insight and action
- selected mission: build a counterfactual action-choice benchmark
- treatment result: the retrieved guidance lacked positive task correlation and drifted into unrelated implementation advice
- decision: block the treatment packet with 9 recorded reasons
- next probe: repair or narrow retrieval before claiming decision value

This is the intended behavior: references are not “internalized” merely because
they were collected. Their influence must be recorded, relevant, challengeable,
and removable. A blocked packet is a better result than a confident but
unsupported mission.

## Who It Is For

Palamedes is strongest for:

- solo builders working with AI
- early-stage founders
- developers in 0->1 exploration
- small teams running many direction changes and experiments

It is a weaker fit for:

- teams that mainly need task tracking
- execution-heavy automation pipelines
- organizations already centered on a rigid PM stack

## Core Concepts

Palamedes centers on one mutable plan plus supporting logs.

- `plan`: the current structured planning state
- `evidence`: concrete signals tied to planning axes
- `hypothesis_log`: testable bets and outcomes
- `reference_discoveries`: logged reference-search questions, criteria, and shortlisted candidates
- `view_transitions`: traceable changes from a previous view to a new view
- `inquiry_items`: statements classified by intent and commitment
- `reference_encounters`: why a reference mattered and what effect it had
- `development_probes`: build steps defined by what they should reveal
- `open_questions`: unresolved questions with multiple views and blind spots
- `risks`: failure modes, early signals, mitigation
- `revisions`: immutable plan snapshots over time
- `events`: operational history such as auto-replan activity

Long-horizon planning is first-class:

- `planning_horizon`
- `review_cadence`
- `phase_plan`

Insight coverage is organized across eight axes:

1. `direction_insights`
2. `market_insights`
3. `timing_insights`
4. `differentiation_insights`
5. `monetization_insights`
6. `constraint_insights`
7. `risk_signal_insights`
8. `evolution_insights`

## State Model

Palamedes stores repo-local state in `.palamedes/`:

- `plan.json`: current plan
- `decisions.jsonl`: decision log
- `risks.jsonl`: risk log
- `events.jsonl`: operational events
- `revisions.jsonl`: plan revision history

The runtime also tracks:

- `schema_version`: canonical contract version for persisted plan state
- `version`: compatibility alias for older consumers of the same contract version
- `fingerprint`: stale-write protection token for the current plan
- revision history for restore and audit
- storage health, recovery candidates, and retention windows

## Contract Surface

Palamedes now separates implementation release cadence from the persisted planning contract.

- `plan.schema_version` is the canonical contract version for persisted state
- `plan.version` is kept as a compatibility alias during the transition
- contract policy lives in `STABILITY.md` and `CONTRACT_VERSIONING.md`
- normative contract docs live in `spec/`
- fixture-backed contract tests live in `tests/contracts/`
- aggregated contract/readiness surfaces are available at `GET /contracts` and `GET /doctor`
- the conformance runner is available through `python3 palamedes.py conformance`

Current stability boundary:

| Surface | Status |
| --- | --- |
| persisted plan state | stable |
| fingerprint conflict and restore semantics | stable |
| documented HTTP envelopes | stable |
| fixture-backed conformance cases | stable |
| host action contract | experimental |
| reference adapters and example integrations | experimental |

## Quick Start

This quick start exercises the stable plan-state kernel. It does not by itself
run or prove the full autonomous pre-planner; empirical mission origination is
currently represented by the experimental contracts and preregistered cases.

### Interactive AI terminal

Install the local console entry point:

```bash
python3 -m pip install -e .
```

Start Palamedes with OpenRouter:

```bash
export OPENROUTER_API_KEY="<new-key>"
palamedes chat \
  --provider openrouter \
  --model <provider/model> \
  --workspace /path/to/project
```

Or use the OpenAI Responses API:

```bash
export OPENAI_API_KEY="<new-key>"
palamedes chat \
  --provider openai \
  --model gpt-5.6
```

Or reuse an authenticated Codex CLI session without configuring a provider API
key:

```bash
codex login
palamedes chat \
  --provider codex \
  --workspace /path/to/project
```

Without installation, the equivalent command is:

```bash
python3 palamedes.py chat --provider openrouter --model <provider/model>
```

The terminal is a persistent, streaming REPL:

```text
Palamedes Research Alpha
workspace: /path/to/project
provider: openrouter
model: <provider/model>
session: local-trial

palamedes> /observe
palamedes> /think What important question are we failing to ask?
palamedes> /challenge Our current product direction
palamedes> /research What evidence is missing before commitment?
palamedes> /mission Produce the strongest mission worth planning
palamedes> /cycle Find a mission through independent cognitive pressure
palamedes> /preview
palamedes> /approve
palamedes> /handoff
palamedes> /outcome success The probe produced the precommitted result
```

Available commands:

- `/observe`: snapshot bounded project, Git, TODO, plan-state, and central-ref signals
- `/think`: choose and perform the missing mode of thought
- `/challenge`: attack assumptions and state falsifiers
- `/research`: identify the minimum missing external evidence
- `/mission`: generate and validate a structured draft without changing the plan
- `/cycle`: run independent interpreter, inventor, adversary, and selector calls
- `/preview`: inspect the latest pending mission contract
- `/approve`: project the draft into plan, evidence, hypotheses, and a probe
- `/reject`: preserve and reject a draft with an explicit reason
- `/handoff`: inspect the immutable planner-facing mission handoff
- `/outcome`: append an observed result and update linked hypothesis/probe state
- `/status`, `/history`, `/sessions`, `/new`, `/help`, `/quit`

The current directory is the default workspace; `--workspace` selects another
project explicitly. Sessions are stored locally as JSONL under that project's
`.palamedes/chat/`. API keys are read only from environment variables and are
not written to session state. OpenRouter and the OpenAI Responses API use
provider API keys and provider-side API billing. The `codex` provider instead
invokes an installed, authenticated Codex CLI and can reuse its saved
ChatGPT-managed Codex authentication.

The chat surface is deliberately plan-only. Model output can recommend a
mission or plan change, but it cannot silently mutate a plan or claim that
delivery work occurred.

### Workspace observation

Observe a project without calling an AI provider:

```bash
palamedes observe --workspace /path/to/project
```

Run an explicitly selected test command as part of the observation:

```bash
palamedes observe \
  --workspace /path/to/project \
  --test-command "python3 -m unittest" \
  --test-timeout 300
```

Machine-readable output is available with `--json`. The central reference root
defaults to `/Users/ze/work/ref` and can be changed with `--ref-root` or
`PALAMEDES_REF_ROOT`.

Each observation records:

- bounded excerpts and hashes for README, AGENTS, build manifests, and selected top-level docs
- Git HEAD, branch, working-tree status, diff stat, and five recent commits
- bounded TODO/FIXME/HACK markers with file and line provenance
- plan fingerprint and counts for evidence, open hypotheses, and planned probes
- central reference repository paths, revisions, symlink state, and dirty flags
- explicit test command, exit status, timeout, and bounded output tails
- changes from the previous observation, such as a new commit, document change,
  plan change, ref revision, or test failure

Snapshots are stored under `.palamedes/observations/`. Collection excludes
common credential filenames, redacts API-key/token/password/private-key
patterns, limits file counts and bytes, never executes a test command unless it
was explicitly supplied, and invokes commands without a shell.

`/cycle` automatically captures a fresh bounded observation and supplies its
provenance-bearing context to the interpreter. This grounds the cognition cycle
in project state rather than only the user's phrasing.

### Bounded autonomous watch

Run one policy-only wake without calling a model:

```bash
palamedes watch --workspace /path/to/project --once
```

Keep watching and permit bounded cognition:

```bash
palamedes watch \
  --workspace /path/to/project \
  --interval 30 \
  --auto-cognition \
  --provider openrouter \
  --model <provider/model> \
  --max-calls-per-wake 4 \
  --max-calls-total 20
```

For a lower-consumption Codex-backed loop, use the defaults explicitly:

```bash
palamedes watch \
  --workspace /path/to/project \
  --interval 300 \
  --auto-cognition \
  --provider codex \
  --max-calls-per-wake 2 \
  --max-calls-per-day 10 \
  --max-calls-total 20
```

Each Codex wake runs as an ephemeral, read-only, non-interactive process in an
isolated temporary directory. It receives the bounded observation rather than
the repository as working context and is instructed not to inspect files or
run commands. Codex JSONL usage is captured into wake and watch state records,
including input, cached-input, output, and reasoning token fields reported by
the CLI. This keeps Codex in the reasoning role, makes consumption auditable,
and prevents repeated whole-repository exploration from becoming the default.

`watch` turns observed changes into the least sufficient cognitive operation:

| Observed signal | Wake operation |
| --- | --- |
| No new signal, duplicate signal, or initial baseline | Wait |
| Unresolved thought not incubated for 24 hours | Noticer + connector revisit |
| Primary document changed | Noticer + connector incubation |
| Central reference revision changed | Noticer + connector incubation |
| Plan changed | Adversary + selector |
| Git implementation changed | Interpreter + adversary |
| Explicit test failed | Interpreter + adversary |
| Mission outcome appended | Outcome analyst |
| Three or more independent signal classes changed | Full four-role cycle |

Autonomous cognition is off unless `--auto-cognition` is supplied. The watcher
never runs tests unless `--test-command` is explicitly supplied, never gains
delivery authority, and never approves a mission into the plan. A full wake may
save a mission as a reviewable draft only. Per-wake and lifetime call budgets
are enforced before provider access, with an additional daily budget; attempted
calls are charged even if the provider fails. Repeated identical signal states
are suppressed. The defaults are a five-minute interval, two calls per wake,
ten calls per UTC day, and twenty calls over the stored watch lifetime. Because
a full cognition cycle needs four independent calls, it remains blocked at the
default per-wake budget; opt into it with `--max-calls-per-wake 4`.

Watch state is local and inspectable under `.palamedes/watch/`: `state.json`
holds the current cursor and budget total, `events.jsonl` is append-only, and
`wakes/` preserves each decision and its artifacts. A PID lock prevents two
watchers from acting on the same workspace. Use `--wake-initial` only when the
first baseline itself should trigger cognition, and `--max-iterations` for a
bounded foreground run.

Document and reference changes now stop before mission formation. A `noticer`
extracts at least two unresolved residues rather than advice, and a `connector`
may relate distant thoughts only when the relationship replaces an assumption,
reframes the product, and changes a possible decision. Thoughts persist across
wakes under `.palamedes/thoughts/thoughts/`; candidate discoveries live under
`.palamedes/thoughts/discoveries/`. Neither grants mission or delivery
authority. A later full cognition wake receives these candidates and, if its
existing adversarial selector issues a draft, records their IDs on the mission.

Mission outcomes are also compressed into
`.palamedes/thoughts/experiences/` as decision-time reason, forecast, observed
result, prediction gap, belief update, and next probe. Later noticer wakes can
therefore reason over decision-to-outcome experience rather than raw logs
alone. This is an initial traceable discovery loop, not evidence that the
system already produces human-level insight or business outcomes.

An unresolved thought can trigger one bounded reconsideration after 24 hours
even when no new workspace signal arrives. Revisited residues gain strength;
thoughts omitted from successive incubation lose strength and are eventually
archived. The same daily and lifetime model-call budgets still apply, so
incubation cannot become an unbounded self-conversation.

The noticer also maintains a bounded, revisable knowledge layer under
`.palamedes/knowledge/`. Claims distinguish `internal_product` from
`external_world`, and fact, interpretation, norm, capability, and constraint.
Every claim carries observed sources, confidence, validity time, scope,
perspective, affected stakeholders, normative assumptions, and known
exclusions. Product or primary-document changes must produce an explicit
unknown boundary; the mere presence of new code is not treated as knowledge of
its purpose, users, or value.

Central references are no longer revision signals only. Observation includes a
redacted, 4 KB representative README excerpt from at most eight ref
repositories, while retaining the existing repository-count bound. A knowledge
claim may cite only source identifiers actually present in the bounded
observation. A `cross_domain` discovery must cite at least one active internal
claim and one active external claim. It must also separate descriptive
observation from normative judgment and name excluded stakeholders, rights
risk, and time sensitivity. Common, legal, profitable, or historically
accepted behavior is therefore not automatically treated as legitimate.

Mission authority follows an explicit vertical contract:

```text
/mission
  -> schema-validated draft
  -> /preview
  -> /approve
  -> plan + evidence + hypothesis + probe
  -> planner handoff (delivery authority still false)
  -> /outcome
  -> append-only outcome + linked state update
```

`/cycle` adds the full pre-planning cognition path:

```text
interpreter
  observations + rival frames
      ↓ frozen artifact
inventor
  three or more competing missions; no selection authority
      ↓ frozen artifact
adversary
  candidate attacks + shared-assumption pressure; no selection authority
      ↓ frozen artifact
selector
  select / defer / reject from frozen candidates only
  + causal role, authority scope, selection type, and every candidate's fate
      ↓
schema-validated mission draft

actual /outcome
      ↓
outcome analyst
  observed-vs-expected + separated attribution + belief update
  + an operational evidence gate when disposition is not continue
```

The four pre-outcome roles are separate provider calls even when one model
performs every role. Each artifact records its role, call index, provider,
model, prompt fingerprint, output fingerprint, and completion time. Partial
artifacts survive a later-role failure, but no mission is issued. The fifth
role, outcome analyst, cannot run until an observed outcome has been appended.
Therefore one successful `/cycle` uses four model calls, with one additional
call for each analyzed `/outcome`.

Drafts and approved contracts live under `.palamedes/missions/`; planner
handoffs live under `.palamedes/missions/handoffs/`; returned outcomes are
appended to `.palamedes/missions/outcomes.jsonl`; role artifacts live under
`.palamedes/missions/cognition/`. Repeating `/approve` cannot approve a contract
that has already left `draft` status. Outcome attribution is recorded as
unresolved first and only then examined by the outcome analyst.

A cycle cannot claim that it originated work already marked complete: completed
work must be classified as an `audited` cycle with `audit_only` scope. Selection
also distinguishes an exclusive decision from sequencing, conditional,
portfolio, and probe decisions, so an unselected candidate is not silently
treated as permanently rejected. Every frozen candidate receives a persisted
fate and reason.

`revise`, `stop`, and `insufficient_evidence` outcome dispositions create an
open record in `.palamedes/missions/outcome-gates.jsonl`. A later mission cannot
be approved until its `outcome_response` names each open outcome and declares
whether it resolves the evidence gap, is genuinely independent, or consciously
carries the debt. This makes outcome analysis constrain the next action rather
than serving as commentary only. User-entered `/outcome` observations are
labelled `implementer_claim`; they do not become independent evidence merely
because Palamedes recorded them.

The first 5 to 10 minutes should produce:

1. one chosen direction
2. weak directions you did not choose
3. a testable plan with metric, deadline, and review cadence
4. evidence and hypotheses that can change the plan later

Start with the default loop:

1. initialize local planning state
2. generate a few directions
3. choose one plan
4. add one evidence item
5. review whether to continue or replan

```bash
python3 palamedes.py init
python3 palamedes.py ideate --profile "solo builder" --interests "automation,founder tools" --count 3
python3 palamedes.py plan \
  --goal "Validate an AI planning tool for founders" \
  --success-metric "5 founder users complete one weekly planning review by 2026-04-30" \
  --deadline "2026-04-30" \
  --planning-horizon "4 weeks" \
  --review-cadence "weekly" \
  --phase-plan "phase1 interviews,phase2 weekly review test,phase3 tighten positioning" \
  --constraints "single developer, local repo only" \
  --direction-insights "Founders have execution help but weak planning support" \
  --market-insights "Founder-led teams feel repeated direction drift" \
  --timing-insights "AI lowered build cost, making direction errors more expensive" \
  --differentiation-insights "Decision state with evidence and replanning, not task execution" \
  --monetization-insights "Paid weekly planning workflow for founder teams" \
  --constraint-insights "Need a narrow user and local-first scope" \
  --risk-signal-insights "If founders mainly ask for task automation, positioning is wrong" \
  --evolution-insights "Start with founder planning, expand only after repeated validation"
python3 palamedes.py evidence --claim "3 founders said direction drift is worse than shipping speed" --source "interviews" --confidence 72 --axis market
python3 palamedes.py hypothesis --hypothesis "Founders will return weekly for plan review" --metric "weekly review completions" --target ">=5" --window "14 days" --status open
python3 palamedes.py view \
  --previous-view "A better strategist report is the primary product value" \
  --trigger "Building and model progress exposed a wider viewpoint-evolution problem" \
  --new-view "Preserve why views change across references, implementation, and outcomes" \
  --new-blind-spots "Process language can excuse drift or delay closure" \
  --opened-paths "longitudinal comparison,reference influence history" \
  --next-probe "Run one live project through repeated view-build-observe cycles" \
  --source "owner inquiry" \
  --references "PALAMEDES_INQUIRY.md"
python3 palamedes.py inquiry \
  --statement "Would a fine-tuned model help?" \
  --kind thought_experiment \
  --status closed \
  --intent "Widen the reasoning space, not propose a roadmap" \
  --commitment none
python3 palamedes.py encounter \
  --reference "/Users/ze/work/ref" \
  --encountered-while "Studying collected repository patterns" \
  --initial-interest "Collection history may expose direction" \
  --relation "Reference influence may be stronger evidence than clone presence" \
  --effect opened_question
python3 palamedes.py probe \
  --step "Run one live view-build-observe cycle" \
  --expected-learning "Whether the record exposes a meaningful view change"
python3 palamedes.py question \
  --question "How should creativity and success interact?" \
  --perspectives-json '[{"view":"creativity","reveals":["possibility"],"hides":["viability"]},{"view":"success","reveals":["reality"],"hides":["fragile novelty"]}]' \
  --revisit-when "After three live cases"
python3 palamedes.py show
python3 palamedes.py review
```

Then expand only if needed:

- `replan`: change direction from new evidence
- `discover`: structure external reference search before copying patterns
- `history`: inspect revision history
- `restore --preview`: inspect a previous revision safely
- `health`: inspect storage and recovery status

## Planning Commands

Palamedes is designed around explicit planning loops:

- `plan`: define or overwrite core direction
- `evidence`: add structured market/product signal
- `discover`: structure reference search before adopting external patterns
- `hypothesis`: track testable assumptions
- `replan`: change the plan from new evidence
- `review`: inspect plan quality and next questions
- `restore`: recover an earlier plan snapshot safely

QA is built into plan updates and can trigger auto-replan when the plan is thin but recoverable.

## Concurrency, Restore, and Retry

### Fingerprints

Every current plan state has a `fingerprint`.

- Writes can include `expected_fingerprint`
- HTTP callers use `If-Match: "<fingerprint>"`
- stale writes return `412 Precondition Failed` instead of silently overwriting the plan

### Restore

Restore is treated as a normal write:

- preview via `restore --preview` or `POST /restore/preview`
- restore via `restore` or `POST /restore`
- restore uses the same concurrency contract as other writes

### Retry Policy

The Python client has typed conflict and retry semantics:

- `PalamedesConflictError`: stale fingerprint conflict
- `PalamedesClientOperationError`: higher-level multi-step failure
- `PalamedesHealthGateError`: optional write blocked by degraded storage health
- append-style operations can carry `idempotency_key` to safely dedupe retries

Default retry policy is conservative:

- automatic refresh-and-retry is enabled for `update_plan`
- `restore_revision` is also treated as safe overwrite-style retry
- append-style operations such as `add_evidence` and `replan` require `allow_non_idempotent_retry=True`
- when opt-in retry is enabled for append-style operations, the client injects an `idempotency_key` if one is missing
- multi-step write flows can require healthy storage with `require_healthy=True`

## CLI

Main commands:

- `init`: create `.palamedes/` state files
- `plan`: create or overwrite core plan fields
- `replan`: update the plan from new evidence
- `decide`: append a decision record
- `risk`: append a risk record
- `evidence`: append structured evidence
- `discover`: generate or apply a reference-discovery pass
- `hypothesis`: append structured hypothesis entries
- `qa`: run QA checks manually
- `validate`: validate plan structure and nested records
- `schema`: inspect or rewrite `schemas/plan.schema.json`
- `health`: print storage health and recovery diagnostics
- `maintenance`: inspect or apply bounded log maintenance
- `show`: print current plan summary
- `history`: print revision history
- `restore`: preview or restore a prior revision
- `ideate`: generate option seeds from lightweight context
- `insight`: generate viewpoint-expansion insight packs
- `view`: record a traceable change of view without declaring it final
- `inquiry`: classify a statement without promoting it to a plan
- `encounter`: record a reference's actual influence
- `probe`: record a development step by its expected learning
- `question`: preserve unresolved perspectives and blind spots
- `review`: run cycle-based review with recommendations
- `observe`: capture a bounded, redacted workspace snapshot without an AI call
- `watch`: map workspace changes to budgeted, duplicate-suppressed cognition

Development checks:

```bash
make check
make test
make compile
make schema-check
```

## HTTP API

Start the local service:

```bash
python3 palamedes_server.py --host 127.0.0.1 --port 8787
```

Available endpoints:

- `GET /plan`: current plan, summary, validation, fingerprint
- `GET /qa`: QA report
- `GET /health`: storage health and recovery diagnostics
- `GET /cycle`: plan + QA + health + recent history snapshot
- `GET /history`: revision history
- `GET /validate`: structural validation
- `GET /tools`: agent tool schemas
- `POST /plan`: update plan fields
- `POST /evidence`: append one evidence item
- `POST /replan`: append plan deltas and rerun QA
- `POST /restore/preview`: preview restore target directly
- `POST /restore`: restore a revision directly
- `POST /tools/<tool_name>`: execute one tool wrapper
- `POST /agent/act`: map slash/natural-language input to a tool call

Example:

```bash
curl http://127.0.0.1:8787/cycle?limit=5
curl http://127.0.0.1:8787/plan
curl http://127.0.0.1:8787/qa
curl http://127.0.0.1:8787/health
curl http://127.0.0.1:8787/history
curl -X POST http://127.0.0.1:8787/plan \
  -H 'Content-Type: application/json' \
  -H 'If-Match: "<fingerprint-from-get-plan>"' \
  -d '{"goal":"Ship local agent layer"}'
curl -X POST http://127.0.0.1:8787/restore/preview \
  -H 'Content-Type: application/json' \
  -d '{"previous":true}'
```

## Agent Wrapper

The local wrapper exposes slash-style and lightweight natural-language control:

```bash
python3 palamedes_agent.py tools
python3 palamedes_agent.py run --input '/palamedes.show'
python3 palamedes_agent.py run --input '/palamedes.health'
python3 palamedes_agent.py run --input '/palamedes.history'
python3 palamedes_agent.py run --input '/palamedes.restore-preview revision_id=<revision-id>'
python3 palamedes_agent.py run --input 'preview previous revision'
python3 palamedes_agent.py run --input '/palamedes.plan goal="Ship local agent layer" planning_horizon="4 weeks" review_cadence=weekly'
python3 palamedes_agent.py run --input '/palamedes.replan evidence="Pilot retention improved" evidence_confidence=70 evidence_axis=market'
python3 palamedes_agent.py run --input '/palamedes.evidence claim="Repeated planning pain" source=interviews confidence=72 axis=market'
python3 palamedes_agent.py run --input 'show plan'
```

Supported slash commands:

- `/palamedes`
- `/palamedes.plan`
- `/palamedes.replan`
- `/palamedes.show`
- `/palamedes.health`
- `/palamedes.history`
- `/palamedes.restore`
- `/palamedes.restore-preview`
- `/palamedes.qa`
- `/palamedes.validate`
- `/palamedes.evidence`
- `/palamedes.hypothesis`

Tool responses use stable `ok`, `tool_name`, and `result_type` fields.

## Python Client

The repo includes a lightweight client in `palamedes_sdk/`.

```python
from palamedes_sdk import (
    PalamedesClient,
    PalamedesClientOperationError,
    PalamedesConflictError,
    PalamedesHealthGateError,
)

client = PalamedesClient.from_http("127.0.0.1", 8787)

cycle = client.get_cycle(history_limit=5)
updated = client.update_plan({"goal": "Ship local agent layer"})

wrapped = client.apply_and_get_cycle(
    "update_plan",
    {"goal": "Ship local agent layer", "success_metric": "Reach 2 pilots", "deadline": "2026-04-03"},
    history_limit=3,
)

restored = client.apply_and_get_cycle(
    "restore_revision",
    {"previous": True},
    history_limit=3,
)

retried = client.apply_and_get_cycle_with_retry(
    "update_plan",
    {"goal": "Ship local agent layer"},
    expected_fingerprint="stale-fingerprint",
)

cycle_result = client.capture_evidence_cycle(
    {"claim": "Pilot friction repeated", "source": "pilot-call", "confidence": 74, "axis": "market"},
    replan_payload={"plan_task": "Tighten onboarding loop"},
    idempotency_key="pilot-friction-cycle-1",
)
```

Use the client when another repo needs Palamedes planning state without re-implementing:

- stale-write handling
- refresh-and-retry policy
- post-write cycle snapshots
- restore preview / restore flows
- optional health-gated writes

See also:

- `STABILITY.md`
- `CONTRACT_VERSIONING.md`
- `spec/plan-state.md`
- `spec/http-api.md`
- `spec/conflict-and-restore.md`
- `docs/integration-agentscope.md`
- `docs/palamedes-agents-bootstrap.md`
- `palamedes_reference_adapter.py`
- `palamedes_reference_host.py`
- `palamedes_reference_consumer.ts`
- `examples/palamedes_kernel_adapter.py`
- `examples/palamedes_planner_host.py`
- `examples/palamedes_reference_consumer.ts`
- `examples/palamedes_agents_skills/registry.py`
- `scaffolds/palamedes_agents/`
- `palamedes_client.py` remains as a compatibility import path

Install the SDK surface locally from this repo:

```bash
python3 -m pip install -e .
```

## Design Principles

Palamedes favors:

1. A worthwhile mission before a larger task list
2. Competing interpretations before premature convergence
3. References with recorded influence, not collection for its own sake
4. View transitions that preserve what became visible and what may now be hidden
5. Explicit falsifiers, non-goals, uncertainty, and reversible probes
6. Reality pressure through paired comparisons and observable outcomes
7. The simplest mechanism that survives the evidence, whether prompting, retrieval, debate, code, or a model
8. Bounded authority: recommendation strength must not exceed evidence strength

The project rejects a false choice between “the human is right” and “the model
is right.” Both are provisional participants in a longer chain of discovery.
Development is part of the inquiry: each implementation step should reveal
something that can alter the next step. AI should eventually originate and
challenge direction—not merely generate more tasks—but that capability must be
demonstrated against baselines and outcomes.

## 📈 Star History

<a href="https://star-history.com/#LEE-Kyungjae/Palamedes&Date">
  <picture>
    <source
      media="(prefers-color-scheme: dark)"
      srcset="https://api.star-history.com/svg?repos=LEE-Kyungjae/Palamedes&type=Date&theme=dark"
    />
    <source
      media="(prefers-color-scheme: light)"
      srcset="https://api.star-history.com/svg?repos=LEE-Kyungjae/Palamedes&type=Date"
    />
    <img
      alt="Star History Chart"
      src="https://api.star-history.com/svg?repos=LEE-Kyungjae/Palamedes&type=Date"
    />
  </picture>
</a>
