# Improvement Cycle 399

## Topic

Stop after one case and inspect before generalizing.

## Deficiency

One successful-looking vertical slice can trigger premature schema
generalization and an agent-company runtime before its newly visible failure
boundaries are understood. More implementation then hides rather than tests
what contact with reality exposed.

## Improvement

Added `inspect_one_case_before_generalization`,
`validate_one_case_stop_and_inspect`, and an experimental schema.

The gate accepts exactly one completed end-to-end case and requires
evidence-backed findings across semantic state, cognition order, adversarial
pressure, planner handoff, and outcome intake. Schema generalization,
agent-company runtime, and an autonomous daemon remain blocked with explicit
release evidence. Only registered case-specific probes are authorized next.

## Scope boundary

Cycle 399 enforces the learning pause. Cycle 400 will state the current
implementation conclusion as five bounded artifacts in required order.

## Verification

- focused mission tests: 1,201 passed
- schema JSON parse: 296 schemas parsed
- `git diff --check`: passed

## Resulting invariant

After the first end-to-end case, implementation pauses until the evidence it
made visible has changed or confirmed the design.
