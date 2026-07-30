# Palamedes

<p align="center">
  <strong>English</strong> · <a href="README.ko.md">한국어</a>
</p>

<p align="center">
  <img src="assets/palamedes.png" alt="Palamedes" width="100%">
</p>

> **Palamedes decides what mission is worth planning before execution agents
> decide how to implement it.**

# Palamedes

Palamedes is an open-source Goal Discovery and Goal Synthesis Engine that generates novel, detailed, and actionable missions before planning begins.
It operates before the traditional `planner → task → implementation` pipeline by discovering opportunities, generating competing goal hypotheses, refining them into justified missions, attempting to falsify them, and passing only the surviving mission to downstream planners and agents.
Palamedes is currently a research-beta project exploring autonomous goal generation, mission synthesis, and pre-planning reasoning.

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

**Research Beta.** The planning kernel is implemented and heavily tested, the
1:1 pre-planner has repeated production use, and two preregistered comparisons
provide initial evidence beyond an internal prototype. This is not a claim that
Palamedes improves startup or downstream business outcomes.

- `core` contract surfaces such as persisted plan state, fingerprint conflict semantics, restore behavior, and documented HTTP envelopes are treated as stable according to `STABILITY.md`
- `reference` surfaces such as host orchestration contracts, reference adapters, and example integrations are still experimental
- `inquiry` surfaces such as view-transition lineage and longitudinal evaluation are active product hypotheses, not settled doctrine
- the repository currently ships a canonical Python reference surface plus a thin TypeScript HTTP consumer

| Evidence level | Current result |
| --- | --- |
| Stable plan-state kernel | Implemented with revision, restore, conflict, QA, and conformance surfaces |
| Bounded pre-planner contracts | Implemented and covered by 1,209 mission tests and 304 experimental schemas |
| Mission-quality proof | `proof-002` and `proof-003` provide initial blinded evidence against one-shot and equal-call strong comparators |
| 1:1 Codex collaboration | Repeated live implementation cycles produced validated product improvements; Palamedes's causal increment over Codex alone is not yet isolated |
| Local 1:N team cognition | Alpha: implemented with provenance, stale-world protection, competing hypotheses, mission ownership, bounded context, and blind commit–reveal exploration |
| 1:N incremental advantage | Not yet proven over the working 1:1 Codex plus Palamedes loop |
| Distributed team operation | Not implemented; the current ledger is a same-host transactional file surface |
| Internal reasoning development | 401 recorded dependent cycles |
| First real retrieval contact | 1,624 evidence records and 837 components indexed |
| Reference-treatment safety | Correctly blocked the first packet with 9 explicit reasons |
| Equal-information baseline vs treatment | `proof-002`: Palamedes won 8/9 blinded model-review votes and all 3 case majorities |
| Generation cost | Palamedes used 4.26x baseline input tokens; cost-adjusted superiority is not proven |
| Equal-call strong comparator | `proof-003`: Palamedes won 7/9 votes and 2/3 cases with 12 calls each and 1.045x input tokens |
| Attributable downstream choice | 1 recorded: `proof-002` mission caused the `proof-003` equal-call experiment before feature expansion |
| Owner labor retirement | Not yet owner-attested |
| Autonomous upstream origination | Vision Genesis and low-cost Vision Scout implemented; a real-project Scout originated an unsupplied founder prompt |
| Independent human/behavioral evidence | Blind review and preregistered behavioral-probe paths implemented; no completed independent evidence yet |

## Live Project Demo

[![Yut quality-cycle demo produced with Palamedes and Codex](assets/demo/yut-gameplay-demo.jpg)](assets/demo/yut-gameplay-demo.mp4)

Click the image to open a 35-second MP4. This Yut game is a concrete artifact of repeated
1:1 Palamedes-plus-Codex quality cycles across rendered behavior, rules boundaries,
accessibility, motion, and regression evidence. It is not proof that Palamedes guarantees
product success or even initial product alignment. A later audit found that this polished
local game diverged from the original online-multiplayer intent. The case therefore shows
both local quality depth and why upstream product invariants must constrain that depth.

Outcome semantics are separated rather than collapsed into one success or stop
label:

```text
observed outcome
  -> probe completion
  -> finding (defect, null, expected, adverse, inconclusive)
  -> current mission disposition
  -> required successor scope, if any
```

A probe may therefore complete successfully and stop while still producing a
qualifying defect that requires a bounded production successor. An unrelated
mission may proceed after acknowledging that result, but it does not silently
close the required follow-up gate.

Outcome analysis also records a surface-independent `causal_signature` and
`mechanism_summary`. When the same signature recurs twice, Palamedes stops
treating the outcomes as isolated rows and opens a bounded prompt-architecture
cycle:

```text
repeated causal signature
  -> prompt architect: competing higher-abstraction research prompts
  -> prompt adversary: TODO repetition, confirmation, and scope attacks
  -> prompt selector: at most one decision-changing agenda
  -> next cognition cycle receives the selected agenda
```

The generated prompt may change the research question, perspective, comparison,
role sequence, and stopping logic. It cannot modify authority, evidence,
privacy, approval, budget, or falsification rules and grants no delivery
authority. Selected agendas are stored under
`.palamedes/missions/prompt-intelligence/prompt-agendas/`.

Outcome interpretation also records its zoom level and lane. Five consecutive
`micro` outcomes on one surface force a component-or-product fresh-eyes agenda
before more local optimization. A missing correctness contract no longer means
that a plausible idea must disappear: it can be stored as a bounded
`design_hypothesis` with no correctness claim and no mission authority, while a
true null candidate still stops. Legacy outcomes remain immutable and can be
mapped into these meta-learning fields in bounded batches with
`/backfill-outcomes N` (maximum 24).

Reference intelligence is local-first rather than collection-dependent. Running
`/reference-intelligence` builds a provenance-bearing project self-model from
the current workspace, records unknown boundaries, and selects at most one
research question. With no configured reference root it may emit only
`knowledge_gap` hypotheses, never invented competitor comparisons. An optional
path argument or `PALAMEDES_REF_ROOT` adds bounded external observations; every
capability, hypothesis, and agenda must cite an observed source ID. The stored
agenda can steer a later cognition cycle but always has
`delivery_authority_granted: false`.

On projects with at least five recorded outcomes, `/cycle` now wakes bounded
meta-learning automatically: it maps at most 12 legacy outcomes per cycle,
creates a first source-bounded self/reference model when absent, and turns a
five-outcome same-surface micro streak into a required fresh-eyes agenda. A
selected zoom agenda is an approval gate, not advisory prose: another `micro`
mission cannot address it. The next approved mission must explicitly cite the
agenda and operate at component or higher scale, after which the agenda is
closed with mission lineage. Provider scalar drift such as `"confidence":"90"`
is repaired only for known typed fields; ambiguous content remains invalid.

Product alignment now precedes local quality optimization. Source-bearing
product invariants, reusable capabilities, temporary constraints, open
integration gaps, and required product-stage journeys live in the append-only
`.palamedes/product-alignment/events.jsonl` ledger and are injected into `/cycle`.
`state.json` is only a regenerable projection.
Mission approval blocks conflict with an active product invariant, greenfield
construction without evaluating an existing capability, silent reuse of an
expired constraint, and stage advancement without configured journey evidence.
The model supplies the source-linked interpretation; the deterministic gate
checks IDs and declared effects rather than guessing product meaning from
keywords.

### Vision Genesis: origination before elaboration

Palamedes now separates inventing a product world from compiling an implementation
mission. On the first `/cycle`, and again when its evidence-based investment envelope is
exhausted, an autonomous vision wake runs seven isolated roles:

```text
self-authored exploration-agenda architect
  → latent desire and affect interpreter
  → distant-domain analogy explorer
  → forced mechanism-fusion inventor
  → three-world product-world builder
  → maniac critic and natural-language vision author
  → reality and opportunity-cost governor
```

The first role writes four to six upstream research prompts that the user did not supply
and selects two or three. Its default adaptive condition must compare frontier questions
that reverse assumptions, conventional questions grounded in current product journeys,
and bridge questions that connect a distant human mechanism to a concrete product engine.
It spans at least six territories but may not seed named solution patterns, answer its own
prompts, or grant authority. The selected agenda is passed as advisory data to later roles. This makes
prompt origination an inspectable artifact rather than hiding it inside a fixed system
prompt or pretending that a downstream feature list was an original question.
`/vision-agenda-ablation <case> <challenger> <comparator>` compares any two distinct
`adaptive|frontier|conventional` strategies; its default is adaptive against a strong
conventional product-question agenda. Both conditions receive identical context,
use the same model family and the same seven generation roles, and are origin-blinded to a
judge. The record reports condition order, call counts, score deltas, and custody. A challenger win
supports only same-model equal-call machine preference; it is not equal-token or human
evidence, and a peer/conventional result grants no advantage claim.
An ablation pair has a one-attempt preregistered budget. Palamedes appends `started`
before the first provider call; malformed JSON, provider failure, and judge failure are
stored as `failed`, preserve available usage custody, consume the pair, and cannot be
retried into a favorable result. Successful attempts are linked to the ablation record.
Provider JSON custody records the raw SHA-256, length, and parse mode for every call.
Recovery is limited to meaning-preserving lexical operations: extracting one balanced
object from a fenced/text envelope and removing structural trailing commas. Ambiguous
damage such as missing commas, quotes, or fields is never guessed or model-repaired; it
fails and still consumes provider usage and the ablation attempt. Raw response content is
not duplicated into custody.

The affect model is valence-neutral: belonging, delight, anger, rivalry, anxiety,
status, habit, and mediated community emotion may all be relevant, while harm and
exploitation boundaries remain explicit. The analogy role must leave adjacent software
features, the fusion role must combine multiple mechanisms, and the world builder must
produce a repeated emotional/behavioral loop with identity, social consequences, and a
multi-year content or rule engine. A selected vision is stored under
`.palamedes/visions/`, injected into later cognition as a hypothesis, and always retains
`delivery_authority_granted: false`. `/vision <context>` forces a wake and `/visions`
shows the latest authored proposal.

The selecting role writes a 180–1200 character `founder_prompt` separately from the
detailed `vision_brief`. It must itself introduce an unsupplied human tension, product
mechanism, affective or behavioral loop, and durable expansion direction, without internal
role/vision IDs or narration of the generation process. A generic request to make the
product more engaging does not qualify.

Both forced and automatic wakes use one structured vision-context contract. It combines
the user context and bounded workspace observation with source-bearing product purposes,
existing capabilities, temporary constraints, open integration gaps, product stage, and
open outcome gates. Product invariants outrank a polished local implementation, and an
existing capability must be considered before greenfield invention. The selected vision
carries a product-ground-truth fingerprint into mission lineage; approval rejects that
lineage if alignment changes and requires a fresh vision wake. An aligned successor is not
blocked: it can proceed when it advances the recorded purpose, reuses or explicitly rejects
relevant capabilities, and responds to open integration gaps.

Three blinded origination cases distinguish creation from elaboration. The generator sees
only product context; a separate judge sees the hidden human reference afterward. The
collection case hides discovery, collection, avatar, and cultural-source concepts. The
rule-fusion case hides the human pattern exemplified by cross-genre competitive puzzle
fusion. The social case hides the charged combination of group belonging, bounded anger,
a low-cost expression economy, and anti-harassment repair constraints.
`/vision-benchmark collection`, `/vision-benchmark fusion`, or
`/vision-benchmark social` records seven axes:
origination, conceptual distance, affective depth, mechanism fusion, world coherence,
three-year generativity, and likely human approval value. These fixtures prove the
blindness and evaluation contract; live-model scores remain empirical evidence, not a
claim guaranteed by the architecture.

`/vision-benchmark-suite all 3` repeats all blinded cases three times (bounded to
1–5 runs per case), gives every trial and human-review packet a distinct identity, and
persists a suite manifest. `/vision-benchmark-summary` reports pass rate, mean axis
scores, reference relation, judge custody, case coverage, and selected-title diversity.
A suite isolates each trial's vision memory so earlier novelty exclusions cannot make a
later sample look more diverse.
A high pass rate with low diversity is therefore visible as convergence, not promoted to
stable creative ability. Repeated model judgment is still not human evidence.
High originality also cannot compensate for omitting the input's core product objective.
Vision Genesis carries source-bearing context requirements through world construction and
criticism; selection requires every core item to be satisfied. Benchmark gate v3 separates
Model roles select deterministic source-anchor IDs rather than reproducing exact source
quotes. Palamedes attaches immutable source text itself and recovers one attributable core
anchor from a malformed array without paying for a schema-repair call.
detailed-vision quality from founder-prompt origination. A second blind judge scores problem
reframing, an unsupplied mechanism, affective thesis, product-world seed, and whether the
text could substitute for a human's upstream prompt. If the central solution was already
present in generator input, or the generated text is a generic request, the benchmark fails
regardless of the polished vision score. Human A/B packets compare the `founder_prompt`, not
the downstream full brief, with the hidden human founder text. The existing
`core_requirements_satisfied` and empty `unmet_core_requirements` checks remain mandatory.

The first gate-v3 live sample, `vision-benchmark-edf12f163696`, did not see the hidden
collection reference and originated **The Caravan of Living Games**, a different world of
temporary stewardship, rule mutation, relinquishment, and rediscovery through descendant
games. The same Codex judge scored the five founder-prompt axes 94–98, which is correlated
machine evidence only. Nine calls consumed 176,536 total tokens, so cost efficiency is also
unproven. The CLI therefore reports
`MACHINE PASS (correlated same-provider judge)` rather than a bare PASS.

A low-cost `Vision Scout` path addresses the cost of applying full Genesis to every idea.
`/vision-scout-benchmark collection|fusion|social` uses three roles to originate three
causally distinct candidates, falsify and select at most one, and let a reality governor
choose only discard or blind human review. One separate judge then sees the hidden human
text, so the normal path is three generation calls plus one evaluation call. A machine
pass can create only a human A/B packet. Scout records
`full_genesis_authorized=false` and `delivery_authority_granted=false`; it cannot promote
itself into full Genesis or implementation without later independent human or behavioral
renewal evidence. Review packets identify whether their source artifact is a
`vision_scout` or `vision_genesis`, rather than presenting a cheap draft as a completed
vision.
The same case and context are preregistered in a one-attempt ledger before generation;
failed responses also consume the attempt, preventing retries that hide weak ideas.

The first live Scout sample, `vision-scout-benchmark-5661177d748b`, originated a direction
different from the hidden collection reference: actions across small games alter one
persistent world's future possibilities. The correlated same-Codex judge scored its five
axes 93–97 and called it stronger, which remains machine evidence only. Four calls consumed
71,495 tokens—59.5% fewer tokens and 55.6% fewer calls than the nine-call, 176,536-token
full baseline. One sample proves neither expected cost nor human-level creativity; blind
human packet `vision-review-9db2913d3906` remains unreviewed.

Use `/vision-scout <context>` for a real project rather than a fixed benchmark. Palamedes
combines current product ground truth and bounded workspace observation, then screens a
founder prompt in two or three calls. Unresolved core requirements produce a deterministic
discard after two calls; only aligned candidates receive the third governor call. Identical user requests reuse the prior Scout despite
timestamp or state-file changes, using a separate request fingerprint. The full original
context is retained in a private local context record while the public Scout record carries
its fingerprint, allowing a later evidence-backed Genesis to continue from the same
information boundary.

`/vision-scout-promote <vision-scout-id>` runs the seven-role Genesis at most once and only
after two distinct independent human reviewers, confidence at least 60, unanimous generated
preference or peer judgment, and no mean axis deficit below -5. Model reviewers and team
reviewers do not count toward the quorum. Promotion still grants no delivery authority.
For a project Scout, a behavioral path is also available. `/vision-scout-probe <id> <JSON>`
preregisters one hypothesis, metric, comparison operator and threshold, sample size of at
least five, duration up to 30 days, and data source before observing a result.
`/vision-scout-probe-outcome <id> <JSON>` records exactly one attributable measured or
external-dataset result. Support is computed mechanically from the preregistered operator;
a failed outcome cannot be replaced. A passing probe can renew full Genesis instead of the
human quorum, but still cannot grant delivery authority.

Project Scout generation is also preregistered once per request fingerprint in an
append-only ledger. JSON or contract failures retain provider-token custody and block a
same-version retry. Source quotations allow only whitespace normalization across wrapped
lines; semantic rewrites remain invalid.

Real-project validation has reached V4. V3 originated an upstream decision environment in
which persuasive prose cannot acquire authority by itself: small claims are placed at risk
in the world, changing one's mind becomes competent progress rather than defeat, and
contradictions alter what may be asked next. This was not a restatement of a supplied
feature list, but it cost 122,709 tokens across three calls. V4 compacted the source-bearing
project context below 10 KB and targeted roughly 75k tokens for a successful run. Its
originator and critic completed, but the governor provider call failed. Palamedes now stores
immutable per-role checkpoints and permits bounded infrastructure resume, so completed
creative outputs are reused rather than regenerated or cherry-picked. Because V4 predates
that checkpoint surface, it is not retroactively rescued. V5 began with checkpoints active
and preserved all three role outputs and 72,401 tokens. It originated an expiring project-
identity hypothesis, but the critic marked core cost, duration, and remediation bounds
partial; the governor nevertheless requested human review, so the deterministic gate
blocked it. The rejection was correct, but it appeared as a contract failure and spent an
unnecessary third call. V6 now closes an all-rejected or core-misaligned critique as a
deterministic two-call `discarded` outcome without invoking the governor. This preserves the
gate while correcting outcome semantics and waste.

The first V6 live one-shot, `vision-scout-2a657a5bfc10`, satisfied every core requirement,
therefore invoked the governor, and used 70,736 tokens. It proposed that Palamedes infer the
builder identity a project is becoming from decisions, sacrifices, reversals, and
beneficiaries, then originate missions that either express or deliberately challenge that
identity. Its repeated affect includes recognition, belonging, and pride as well as
discomfort, anger, and grief when work contradicts professed values. Identity remains an
expiring hypothesis exposed to counterevidence and private dissent. The governor opened
blind human review only. This is a second live origination example, not human-preference or
behavioral-effect evidence.

When a real-project Scout selects `blind_human_review`, Palamedes now creates a standalone
blind packet rather than inventing a human comparator. `/vision-scout-review-next` exposes
the authorship-hidden founder prompt, seven absolute axes, and its packet fingerprint;
`/vision-scout-review-submit <packet-id> <JSON>` records a review. The human path requires
two distinct independent humans with confidence at least 60, every axis at least 60, mean
score at least 70, and unanimous `advance`. Model, team, author, and unknown reviews remain
auditable but do not count. Standalone review does not establish non-inferiority to a hidden
human reference and is not merged with A/B benchmark evidence.

Every newly selected vision also passes a reality governor before it can influence
delivery. It compares `full_build`, `minimal_probe`, `manual_probe`, `reuse_or_buy`,
`do_nothing`, and `alternative_opportunity` with engineering, AI, infrastructure,
maintenance, reversibility, learning, and opportunity-cost ranges. A speculative vision
cannot select `full_build`, and its lineage cannot approve a product/service/portfolio
delivery mission before the selected probe produces renewal evidence. Debt, scale, and
kill guards travel with the later mission contract. Cost estimates also become an
enforceable outcome horizon: speculative, behavioral, demand, and revenue evidence permit
1, 2, 3, and 5 outcomes respectively before a fresh vision and investment review is
mandatory.

Benchmark custody is explicit. Generator and judge callables and identities may differ;
the record says whether independent-provider evaluation is actually claimed. Every run
also emits a randomized A/B human-review packet under
`.palamedes/vision-benchmarks/human-review/`, while authorship keys are stored separately
under `answer-keys/`. Same-provider judging is correlated evidence, never independent
proof. Set `PALAMEDES_VISION_JUDGE_PROVIDER` (and optionally
`PALAMEDES_VISION_JUDGE_MODEL`) to use a genuinely separate configured judge. Submit a
completed blinded packet with `/vision-review-submit <packet-id> <JSON>`; authorship is
revealed only into a separate resolution record, duplicate reviewer submissions are
rejected, and `/vision-review-summary` aggregates human preference and score deltas.
`/vision-review-next` prints the least-reviewed blinded packet without its answer key.
Every response declares `reviewer_kind: human|model`; model and unattested records remain
available for audit but are excluded from human-evidence totals.
It also declares `reviewer_relationship: independent|team|author|unknown`; self-attested
human reviews and independent-human reviews are reported separately.
`/vision-review-bundle` creates a self-contained offline review page containing no
answer keys. It downloads a response JSON carrying the exact packet fingerprint;
`/vision-review-import <response.json>` rejects stale or mismatched packets before
resolving authorship.
`/vision-review-gate` applies cross-case independent-human quorum and non-inferiority
thresholds. A pass permits only the narrow claim
`repeated_blind_human_founder_prompt_support`; it never permits a human-level-creativity or
market-success claim.

The three repository cases are calibration, not generalization proof. Import a private,
externally human-authored holdout with `/vision-holdout-import <case.json>`, then run it via
`/vision-benchmark holdout:<case-id>`. The imported reference lives under local
`.palamedes/vision-benchmarks/holdout-cases/`, is fingerprinted, and is never inserted into
the generator prompt. The evidence gate ignores builtin calibration reviews and requires
three external holdout cases. `independent` authorship remains self-attested, not identity-
verified or cryptographically sealed. Local storage is recorded, but whether the imported
source file was ever committed elsewhere remains explicitly unverified.
The author identifier stays in the private answer key, never the blinded packet; a reviewer
using the same stable ID is rejected. Promotion also requires three distinct holdout
fingerprints, so renaming one case cannot manufacture coverage.
Each imported holdout preregisters `evaluation_trial_count` (1-3). Palamedes appends a
`started` attempt before calling the generator, so a crash or weak generation consumes the
declared budget instead of disappearing. The promotion gate treats every imported case and
every preregistered trial as the evaluation cohort, requires a completed attributable
attempt plus reviewer quorum for each trial, and therefore cannot pass by reviewing only
the best run or quietly omitting an unfavorable imported case. The append-only local ledger
prevents ordinary single-process cherry-picking; it is not a remote timestamp authority or
concurrency-safe cryptographic registry.

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
├── palamedes_epistemics.py         # Observation surfaces, coverage, and base-rate gates
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

For a 1:N Paperclip-style team, Palamedes can also expose a shared epistemic
ledger without becoming the scheduler. It preserves agent provenance,
observation-surface bias, competing hypotheses, one-owner mission claims,
stale-world conflicts, blind commit–reveal exploration, and explicit outcome
attribution. The host still owns wakes, budgets, permissions, queues, and
process lifecycle. See the
[multi-agent team integration](docs/integration-agent-teams.md).

```bash
palamedes team snapshot --state .palamedes/team-cognition.json
palamedes chat --provider codex --team-state .palamedes/team-cognition.json \
  --agent-id palamedes-main --agent-role strategist
```

Team cognition flow:

| Command | Purpose |
| --- | --- |
| `palamedes team observe` | Record an agent observation with source, surface, confidence, and coverage bias |
| `palamedes team hypothesis` | Preserve a falsifiable interpretation without overwriting rivals |
| `palamedes team round-begin` | Freeze participants, question, and evidence boundary for independent exploration |
| `candidate-hash` → `candidate-commit` → `candidate-reveal` | Prevent early proposals from anchoring later agents |
| `palamedes team claim` / `release` | Give a mission one active owner without moving scheduling into Palamedes |
| `palamedes team outcome` | Record observed results with explicit contribution attribution totaling 100% |
| `palamedes team snapshot` | Inspect the complete durable team ledger |

Every write may provide `--expected-world-version`; stale writers must reread
instead of silently replacing another agent's observation. Full history remains
durable, while AI prompts receive a bounded context containing recent evidence,
open hypotheses, active missions, outcomes, and only fully revealed exploration
rounds. This team layer is a local-host Alpha surface within the Research Beta.
Distributed teams should
put the same schema and version contract behind transactional storage.

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
Palamedes Research Beta
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
palamedes> /outcome mission-012345abcdef success The result arrived in a new chat session
palamedes> /outcome-json {"status":"mixed","observation":"Probe result","actual_investment":{"engineering_days":0.5,"ai_cost":3,"input_tokens":12000,"output_tokens":1800,"monthly_infrastructure":0,"evidence_source":"measured","notes":"time log + provider export"}}
palamedes> /wait-external mission-012345abcdef Three independent human responses
palamedes> /external-evidence gate-012345abcdef Three responses were collected
```

Available commands:

- `/observe`: snapshot bounded project, Git, TODO, plan-state, and central-ref signals
- `/reference-intelligence [path]`: build a local-first self-model and bounded research agenda; references are optional
- `/reconcile` audits immutable handoffs, outcomes, gates, and lifecycle events and
  prints a dry-run projection report. Applying requires `/reconcile --apply
  <proposal-fingerprint>` with the exact fingerprint emitted by a fresh dry-run. It
  appends only deterministic, idempotent lifecycle repair events, never rewrites source
  handoffs or outcomes, and leaves conflicts or missing references unresolved.
- `python3 palamedes.py lifecycle-audit` independently replays lifecycle event meaning
  from immutable sources. `lifecycle-reconcile` is dry-run by default and accepts only
  the exact fresh proposal fingerprint for `--apply`.
- `python3 palamedes.py gate-resolution --request request.json` verifies evidence hashes
  and creates a read-only closure proposal. Only its exact fresh fingerprint may append
  a resolution event and gate revision. Approving a successor alone never closes a gate.
- `python3 palamedes.py storage` reports retention classes, unique content, and duplicate
  bytes without deleting or rewriting artifacts.
- `/satisfaction-json <JSON>` host-verifies a requirement against the current Git and
  worktree fingerprint, bounded source/call-path artifacts, claim-specific evidence,
  purpose alignment, and freshness. `/satisfactions` shows the latest assessment for
  each requirement. A current aligned `already_satisfied` assessment blocks another
  implementation mission with the same `requirement_id`.
- `/alignment-candidate-json <JSON>` appends a proposed purpose, capability,
  constraint, integration gap, or surface stage without changing active product truth.
  `/alignment-approve <candidate-id>` records human approval and merges sources and
  statement variants without erasing history; `/alignment` shows the surface projection.
  Approval events are authoritative and the projection can be rebuilt from them.
- Outcomes preserve an honest `outcome_type`: `validated_improvement`, `null_finding`,
  `already_satisfied`, `adverse_result`, `insufficient_evidence`,
  `blocked_by_environment`, `misaligned_mission`, or `prototype_only`.
- `/think`: choose and perform the missing mode of thought
- `/challenge`: attack assumptions and state falsifiers
- `/research`: identify the minimum missing external evidence
- `/mission`: generate and validate a structured draft without changing the plan
- `/cycle`: run independent interpreter, inventor, adversary, and selector calls; resume
  completed immutable roles after a provider-runtime interruption
- `/cycle --mode audit <context>` (alias: `--skip-vision`): run only those four
  cognition roles for a bounded audit. It suppresses automatic Vision Genesis and
  meta-learning provider calls, omits selected-vision influence, and emits run-scoped
  role progress, elapsed time, and token custody without changing ordinary `/cycle`.
- `/cycle --resume <cycle-id>`: resume one failed or interrupted cognition run
  from its preserved context and verified role checkpoints. The provider and model
  must match; completed roles are not called again, and tampered checkpoints fail closed.
- Plain `/cycle <context>` now runs a deterministic cost preflight before any provider
  call. Lookup uses 0 calls for a host-verified `already_satisfied` requirement; Micro
  uses one mission-compiler call with at most one schema repair; Component uses the four
  independent roles without Vision/meta-learning; Product may use the full research
  path. `/cycle --mode lookup|micro|component|product <context>` is an explicit override.
  Ambiguous natural-language scope defaults to Component, while security, privacy,
  payment, deletion, migration, public API, deployment, storage binding, irreversibility,
  cross-surface work, and product-invariant conflicts escalate rather than down-route.
- `/preview`: inspect the latest pending mission contract
- `/approve`: project the draft into plan, evidence, hypotheses, and a probe
- `/reject`: preserve and reject a draft with an explicit reason
- `/handoff`: inspect the immutable planner-facing mission handoff
- `/outcome`: append an observed result and update linked hypothesis/probe state; an explicit
  mission ID permits attribution from another chat session
- `/outcome-json`: record the same result with attributable engineering days, AI cost,
  token usage, monthly infrastructure, and measurement provenance
- `/wait-external`: open a structured no-local-action evidence gate for an approved mission
- `/external-evidence`: attach a user-attested observation and resolve that gate
- `/status`, `/history`, `/sessions`, `/new`, `/help`, `/quit`

The current directory is the default workspace; `--workspace` selects another
project explicitly. Sessions are stored locally as JSONL under that project's
`.palamedes/chat/`. API keys are read only from environment variables and are
not written to session state. OpenRouter and the OpenAI Responses API use
provider API keys and provider-side API billing. The `codex` provider instead
invokes an installed, authenticated Codex CLI and can reuse its saved
ChatGPT-managed Codex authentication.

When a provider reports token usage, every cognition role artifact preserves normalized
input, cached-input, output, and total-token counts. Vision Genesis aggregates its six
role calls and records metered versus unmetered custody. OpenRouter explicitly requests
streaming usage; OpenAI response-completed and Codex JSONL usage are normalized to the same
fields. Missing provider usage remains `unmetered` rather than being recorded as zero cost.
The next automatic vision receives these provider totals beside the prior delivery spend
and investment envelope.

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
| Uncommitted implementation changed | Interpreter + adversary |
| Completed Git revision changed | Stakeholder/future-scenario noticer + adjacent connector |
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

Document, reference, and completed implementation changes stop before mission
formation. A `noticer` extracts at least two unresolved residues rather than
advice. Each residue must place a named stakeholder in a concrete future
operating scene with a goal and a constraint—for example developer absence,
failure recovery, scale, regulation, repeated operation, or ownership transfer.
A `connector` then traverses one adjacent possibility and records the important
question not already asked, a nearby product or business opportunity, and
separate novelty, value, uncertainty, and scope-risk scores. It may relate
distant thoughts only when the relationship replaces an assumption, reframes
the product, and changes a possible decision. Thoughts persist across
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

Palamedes also records the observation surface that made a claim visible:
collection method, selection process, observed and missing populations, and
visibility bias. An epistemic profile separates salience from
representativeness, relevance, independence, persistence, behavioral support,
and base-rate support. It also distinguishes expression, exposure, behavior,
and outcome evidence and freezes the narrowest allowed inference plus
forbidden generalizations.
Each surface also records an `origin_id`; multiple publishers or posts derived
from one original report cannot claim more independence than their distinct
origin ratio permits.

Population-level claims are rejected unless they have representative,
denominator-bearing behavior or outcome evidence; a vivid exposure signal
cannot satisfy this gate. `.palamedes/epistemics/coverage.json` records
overrepresented surfaces, missing populations, and whether an ambient baseline
exists. Discoveries remain `surface_anomaly`, `representativeness_unknown`,
`cross_check_required`, or `bounded_opportunity` until a behavioral base-rate
baseline makes them `mission_eligible`. Only mission-eligible discovery IDs may
be claimed by the autonomous selector, although lower states remain visible as
questions worth investigating.
Mission eligibility additionally requires an opposing-sample claim, preventing
a supporting baseline from becoming its own unchallenged confirmation loop.

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
validated artifacts survive a later-role runtime failure and are reused on the
next identical `/cycle`; a contract-invalid role is discarded and never promoted.
Vision Genesis uses the same immutable per-role checkpoint rule. No mission is
issued from a partial cycle. The fifth
role, outcome analyst, cannot run until an observed outcome has been appended.
Therefore one successful `/cycle` uses four model calls, with one additional
call for each analyzed `/outcome`.

Drafts and approved contracts live under `.palamedes/missions/`; planner
handoffs live under `.palamedes/missions/handoffs/`; returned outcomes are
appended to `.palamedes/missions/outcomes.jsonl`; role artifacts live under
`.palamedes/missions/cognition/`. Repeating `/approve` cannot approve a contract
that has already left `draft` status. Outcome attribution is recorded as
unresolved first and only then examined by the outcome analyst.
When `/outcome` includes a mission ID, attribution is mission-addressable rather
than tied to the chat session that approved it. A structured external-evidence
gate returns `WAITING_FOR_EXTERNAL_EVIDENCE` with `provider_calls: 0`, preventing
repeated Vision and cognition spending when only outside evidence can change the
decision.

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

## One installation, multiple workspaces

Install or upgrade Palamedes once instead of cloning it into every project:

```bash
pipx install --force git+https://github.com/LEE-Kyungjae/Palamedes.git
# or, while developing Palamedes itself:
pipx install --force -e /path/to/Palamedes
```

Register each existing project. Registration preserves its current `.palamedes`
history in place and writes only `.palamedes/workspace.json` plus a global name
mapping under `${PALAMEDES_HOME:-~/.local/share/palamedes}/workspaces.json`:

```bash
palamedes workspace init /work/greedy --name greedy
palamedes workspace init /work/zaeze --name zaeze
palamedes workspace list
```

The single installed CLI can then operate on any isolated project from anywhere:

```bash
palamedes -w greedy show
palamedes -w greedy chat --provider codex
palamedes -w zaeze observatory --limit 100
palamedes-server -w greedy --port 8787
```

A literal directory is also accepted in place of a registered name. Running
without `-w` binds to the current directory. `workspace remove <name>` removes
only the global mapping; it never deletes the project or its `.palamedes` state.
After verifying all five registrations, old per-project `ref/palamedes` clones
may be removed separately; do not remove any project `.palamedes` directory.

## HTTP API

Start the local service:

```bash
python3 palamedes_server.py --host 127.0.0.1 --port 8787
```

Open `http://127.0.0.1:8787/observatory/view` for the read-only Palamedes
Observatory. It refreshes every five seconds and combines Vision Genesis, Vision
Scout, Product Invention, cognition decisions, candidate fates, mission contracts, outcomes,
evidence gates, and plan revisions into one filterable timeline. Each event can
be expanded to inspect the planning content that produced it. The UI writes no
state and uses the same persisted artifacts as the CLI:

```bash
python3 palamedes.py observatory --limit 50
python3 palamedes.py observatory --limit 200 --json
```

## Product Invention

`/cycle` remains the bounded product-audit and mission-selection path. Use
`/invent <context>` when Palamedes must originate the product mechanic itself:

```text
/invent 온라인 윷놀이의 반복 플레이와 팀 몰입도를 높여라. 현재 규칙과 구현을 유지할 필요는 없다.
/inventions
```

The invention pipeline maps direct and socially mediated emotion, originates at
least five structurally distant worlds, compiles every world into a playable
contract, attacks fun/harm/balance/content/infrastructure risk, and selects only
an already-originated candidate for a small probe. Candidate distance is explicit
across player relationship, victory, information, resources, time, risk ownership,
emotion source, and repeat motive. Provenance records whether the decisive seed
was human-, reference-, Palamedes-, or jointly originated. An invention never
grants mission approval or delivery authority; implementation still requires the
normal mission gate.

## Domain-general pursuits

`/pursue <objective>` sits above product-specific modes. The user states the
outcome, not the research method or tool sequence:

```text
/pursue 폐배터리 재활용에서 논문으로 만들 새로운 연구를 찾아 원고를 작성하라.
/pursue 향후 12개월 구리 가격의 상승·하락 조건을 조사해 위원회 보고서를 작성하라.
/pursue 반복 사용자가 대화 작업에 집중할 수 있는 경험을 만들어라.
/pursuits
```

Palamedes composes `discover`, `explain`, `predict`, `invent`, `design`,
`decide`, `evaluate`, `author`, and `operate` rather than selecting a hard-coded
industry template. It produces an Unknown Map, dynamically acquired domain
protocol, capability graph, evidence and re-observation policy, deliverable
compiler, and autonomy envelope. The stored pursuit is deliberately marked
`execution_started: false`: composing a rigorous workflow is not evidence that
retrieval, experiments, prediction, or writing occurred. Purchases, human
contact, publication, sensitive data, and real financial actions remain explicit
human gates. Pursuits and their full decision history appear in Observatory.

Available endpoints:

- `GET /plan`: current plan, summary, validation, fingerprint
- `GET /qa`: QA report
- `GET /health`: storage health and recovery diagnostics
- `GET /cycle`: plan + QA + health + recent history snapshot
- `GET /history`: revision history
- `GET /observatory?limit=200`: combined read-only planning and evidence timeline
- `GET /observatory/view`: dependency-free live Observatory UI
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
