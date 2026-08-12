# Cognition Workflows

<p align="center">
  <strong>English</strong> · <a href="cognition-workflows.ko.md">한국어</a>
</p>

Palamedes exposes separate workflows because discovery, evaluation, commitment,
and execution authority are different operations.

## Four-role cognition cycle

```text
/cycle <context>
```

The cycle runs context governor, interpreter, inventor, adversary, and selector
roles. It preserves candidate fates and produces a mission draft. `/approve`
persists the draft; `/reject <reason>` records rejection. Bounded cycles prefer
small, reversible actions over review documents when safe action is possible.

## Opportunity Scout

```text
/opportunity <product context>
/opportunities
```

The scout rotates through user desire, repeat behavior, monetization, content
economy, social dynamics, live operations, distribution, platform expansion,
and risk. It then applies senior architecture lenses for coupling and invariants,
failure precedent, second-order feedback, operating cost, migration and rollback,
authority and incentives, changed constraints, and unused capability. A lens can
explicitly report `no_signal`; coverage never grants permission to manufacture an
insight.

Each opportunity must trace the perspective findings and reframes that changed
its conclusion. It records a computed two-hop consequence path, a design response
to a downstream effect, migration and operating reality, and a reversible action
probe that reaches an observable response. A review document cannot masquerade as
validation. Familiar patterns such as subscriptions, seasons, battle passes,
bundles, and marketplaces remain valid when product-specific causal fit is
present.

Mission outcomes are supplied as a bounded experience archive. Immutable observed
results remain separate from later interpretation. A direct failure lesson must
cite an available adverse, mixed, failed, or blocked outcome; analogies and
inferences cannot claim direct experience. Every lesson includes a guardrail and
transfer limit.

The initial product-structure map is still a model extraction from bounded context,
not a host-attested claim ledger. The record marks that boundary explicitly; any
decision-relevant repository or market claim still requires host or human
verification before commitment.

## Product Invention

```text
/invent <context>
/inventions
/invent-commit <candidate-id> <human rationale>
```

Product Invention maps the conventional baseline, explores structural changes,
and attacks cosmetic novelty. It preserves a frontier rather than choosing or
implementing a winner. Observation gaps can be listed with
`/invent-observations` and resolved with `/invent-observe`.

## Vision Genesis and Vision Scout

```text
/vision <context>
/vision-scout <context>
/visions
```

Vision Genesis explores desire, distant analogy, mechanism fusion, product
worlds, and critique. Vision Scout is a lower-cost path that originates and
filters founder prompts before full Genesis. Promotion requires bounded human
or behavioral evidence and never grants delivery authority.

Benchmark commands include:

```text
/vision-benchmark collection
/vision-benchmark-suite all 3
/vision-scout-benchmark fusion
```

## Domain-general pursuits

```text
/pursue <objective>
/pursuits
```

Pursuits compose an evidence-producing knowledge-work graph for research,
analysis, or writing. External action, publication, and financial authority
remain separate.

## Observation and watch

```bash
palamedes observe
palamedes watch --once
```

Observation collects bounded workspace facts. Watch evaluates whether a change
justifies cognition under configured call and token budgets. Neither repository
presence nor model confidence proves user value.

## Outcome learning

Approved missions can receive outcome records. Outcome analysis separates
reported results, attribution hypotheses, causal signatures, and follow-up
gates. Ambiguous or adverse outcomes constrain later approval instead of being
silently overwritten.

Use `/help` in the chat terminal for the complete command list.
