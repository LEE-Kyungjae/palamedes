# Improvement Cycle 263

## Topic

Select one cognitive operation from the observed insufficiency.

## Deficiency

A valid wake can still trigger a fixed observe-interpret-generate-compare
pipeline. This repeats adequate reasoning, expands the state unnecessarily, and
can change unrelated mission decisions.

## Improvement

Added `validate_wake_cognitive_operation_selection` and an experimental schema.

The selection record states the observed insufficiency and its evidence, then
compares at least two cognitive operations. Exactly one must directly address
the insufficiency; every other option records why it is not selected. The
selected operation must match that unique fit, and the execution sequence may
contain only that one operation. Restarting a fixed pipeline is forbidden.

## Scope boundary

Cycle 263 selects a bounded response to one wake. Cycle 264 will detect repeated
null updates and force a change in evidence source, causal model, or stakeholder
representation after a threshold.

## Verification

- focused mission tests: 657 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes wakes to repair the specific insufficiency that was observed rather
than replaying all cognition and disturbing decisions that remain adequate.
