# Improvement Cycle 254

## Topic

Preserve essential causal mechanisms while leaving implementation form open.

## Deficiency

A causal thesis that does not distinguish mechanism from form is either too
weak to guide planning or so concrete that it silently dictates tools. A
planner may remove the function that was expected to cause beneficiary change,
or mistake one implementation for the mission itself.

## Improvement

Added `validate_essential_mechanism_open_form_contract` and an experimental
schema.

Each essential mechanism now states its predicted effect, evidence,
falsification condition, and that removing it breaks the causal thesis. At
least two negotiable implementation forms demonstrate that the mechanism is
not identical to one technical shape, and every form must preserve every
essential mechanism. Prescribing a form or denying planner substitution is
forbidden.

## Scope boundary

Cycle 254 defines functional invariants and implementation freedom. Cycle 255
will make every attention-protecting non-goal explainable and reopenable.

## Verification

- focused mission tests: 621 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes constrains planners only where the mission's causal account depends
on a mechanism; tools, channels, and technical forms remain replaceable.
