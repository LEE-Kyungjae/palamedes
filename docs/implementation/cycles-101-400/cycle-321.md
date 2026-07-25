# Improvement Cycle 321

## Topic

Measure the single-model versus multi-model tradeoff.

## Deficiency

One full-context model can anchor interpretation, invention, criticism, and
selection to one frame. Multiple models may increase frame diversity, but that
benefit is easily overstated when extra cost or unstable reproduction is
ignored.

## Improvement

Added `validate_model_multiplicity_tradeoff` and an experimental schema.

The comparison freezes the same case input and non-model budget across exactly
one single-model and one multi-model condition. Both preserve model-call,
prompt, response, token, cost, and assignment-manifest provenance. Diversity
and cross-run reproducibility are measured explicitly, and a declared selection
rule trades diversity gain against cost and reproducibility thresholds.

## Scope boundary

Cycle 321 makes the tradeoff measurable without deciding that multiple
providers are required. Cycle 322 will define provider-neutral cognitive roles.

## Verification

- focused mission tests: 889 passed
- schema JSON parse: 218 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Palamedes cannot call model multiplicity an improvement unless measured frame
gain survives explicit resource and reproducibility accounting.
