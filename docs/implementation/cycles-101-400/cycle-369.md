# Improvement Cycle 369

## Topic

Separate blinded judges by evaluation dimension.

## Deficiency

A single reviewer can let fluent prose, condition identity, or one strong
dimension contaminate every score. Beneficiary outcome, constitutional
reasoning, originality, planner burden, and proxy risk are non-substitutable
and require different evidence and expertise.

## Improvement

Added `validate_blinded_separate_axis_judging` and an experimental schema.

At least three condition outputs are normalized without semantic change,
randomized, and stripped of condition identity. Each of the five axes has a
distinct panel of at least two judges, a frozen rubric, and an axis-specific
evidence packet. Judge identities cannot cross panels; condition identity and
other-axis scores remain hidden. The identity map stays sealed through all
scores. Axis results remain separate and no holistic or global-impression score
is allowed.

## Scope boundary

Cycle 369 defines multi-axis blinded review. Cycle 370 will integrate the
sequential replay/live dataset, adversarial cases, real baselines, blinded
contracts, and outcome-aware review.

## Verification

- focused mission tests: 1081 passed
- schema JSON parse: 266 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Each proof dimension is judged by an independent blinded panel using only its
relevant evidence, so fluency or one favorable axis cannot substitute for the
others.
