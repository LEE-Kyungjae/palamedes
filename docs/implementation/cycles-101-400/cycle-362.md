# Improvement Cycle 362

## Topic

Control information and counterfactuals in proof cases.

## Deficiency

Fully real cases offer ecological validity but sparse counterfactuals and
uncontrolled information. Historical replays offer controlled information and
known alternative branches but do not prove prospective behavior under real
time pressure. Either alone supports an incomplete claim.

## Improvement

Added `validate_historical_live_proof_case_portfolio` and an experimental
schema.

The proof portfolio contains both replayable historical cases and
prospectively registered live cases under one evaluation contract. Historical
cases keep outcomes sealed, make information replayable, and expose multiple
counterfactual branches. Live cases keep outcomes pending and log external
information events as they occur. A complementarity contract states which
validity each type contributes, the residual limitation, and forbids treating
either type as sufficient alone.

## Scope boundary

Cycle 362 establishes the complementary portfolio. Cycle 363 will specify
original-order event reveal and future-framing concealment for replay cases.

## Verification

- focused mission tests: 1053 passed
- schema JSON parse: 259 schemas parsed
- `git diff --check`: passed

## Resulting invariant

External proof combines controlled counterfactual replay with prospectively
registered real-world behavior instead of pretending one case type supplies
every form of validity.
