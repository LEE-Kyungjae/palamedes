# Improvement Cycle 380

## Topic

Integrate the mission metric thesis.

## Deficiency

Separate proof artifacts can still be summarized selectively. A composite
score can hide excess compute or human correction, let benefit net away harm,
and omit whether a simpler replacement retains most of the value.

## Improvement

Added `validate_integrated_mission_metric_thesis` and an experimental schema.

The scorecard requires seven separately evidenced dimensions: mission
consequence, retired cognition, compute, total human labor, calibration, harm,
and replaceability. It is eligible only under equal information, with no
constitutional violation or disqualifying dimension. No composite score is
authoritative, and resources, harm, or replaceability cannot be hidden.

## Scope boundary

Cycle 380 integrates the empirical metric thesis. Cycle 381 will ensure that
these experimental schemas cannot corrupt the existing stable plan state.

## Verification

- focused mission tests: 1,125 passed
- schema JSON parse: 277 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Mission evidence remains a seven-dimensional, resource-normalized,
safety-bounded comparison rather than an optimizable scalar.
