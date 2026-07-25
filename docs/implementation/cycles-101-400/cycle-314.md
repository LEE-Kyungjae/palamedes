# Improvement Cycle 314

## Topic

Record competing causal sketches without selecting truth.

## Deficiency

Recording one interpretation as truth collapses uncertainty before alternatives
can be compared. Implicit signal references also make it impossible to audit
which observation supports or opposes a particular causal edge.

## Improvement

Added `validate_record_competing_causal_sketches` and an experimental schema.

At least two unique sketches independently pass the Cycle 306 validator. Every
supporting and opposing signal on every edge is materialized as an exact typed
link. Each sketch remains `plausible_unresolved`; truth and selected-sketch
fields stay empty. Rival visibility is disabled during recording so one sketch
cannot imitate another.

## Scope boundary

Cycle 314 preserves plural causal interpretation. Cycle 315 will freeze mission
forecasts before a candidate can inspect rivals.

## Verification

- focused mission tests: 861 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes can retain several falsifiable explanations of the same signals
without allowing recording order or hidden evidence links to manufacture a
premature truth.
