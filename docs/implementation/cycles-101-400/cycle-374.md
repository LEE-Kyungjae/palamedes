# Improvement Cycle 374

## Topic

Measure planner reconstruction and clarification burden.

## Deficiency

A concise handoff may appear efficient while forcing the planner to rediscover
beneficiary meaning, causal assumptions, boundaries, or authority. Satisfaction
scores and final strategy quality do not reveal that hidden reconstruction
work.

## Improvement

Added `validate_planner_semantic_reconstruction_burden_report` and an
experimental schema.

Human, one-shot-agent, and Palamedes handoffs are measured separately from
receipt until strategy readiness. For beneficiary, invariant meaning, causal
thesis, success/harm signals, non-goals, and authority, the planner records
whether the element was directly understood, reconstructed, clarified, or
corrected. Minutes, clarification questions, source lookups, and semantic
corrections must match status-specific rules and exact declared totals.
Satisfaction cannot substitute for measurement and unlogged work cannot become
zero.

## Scope boundary

Cycle 374 measures planner burden. Cycle 375 will measure beneficiary change,
side effects, sustainability, and option preservation across defined outcome
horizons.

## Verification

- focused mission tests: 1101 passed
- schema JSON parse: 271 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Planner burden is the measured semantic work required after handoff and before
strategy, not a subjective impression or hidden downstream cost.
