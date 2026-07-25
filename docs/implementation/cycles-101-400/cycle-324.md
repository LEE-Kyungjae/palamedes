# Improvement Cycle 324

## Topic

Route causal interpretation by prediction separability.

## Deficiency

Generating several causal sketches in one response can produce cosmetic
paraphrases anchored to one explanation. Requiring independent calls in every
case, however, spends resources even when one pass produces genuinely
distinguishable predictions.

## Improvement

Added `validate_causal_sketch_interpretation_routing` and an experimental schema.

Every sketch must register falsifiable predictions and a unique discriminating
observation before outcomes. A single call is valid only when prediction sets
remain pairwise distinct. Otherwise routing uses one isolated call per sketch
with no cross-sketch visibility. The routing decision is frozen before
interpretation and cannot relabel collapsed paraphrases as plurality.

## Scope boundary

Cycle 324 controls interpretation independence. Cycle 325 will blind the
adversary to author identity and persuasive discussion history.

## Verification

- focused mission tests: 901 passed
- schema JSON parse: 221 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Plural causal interpretation means empirically distinguishable expectations,
not merely several phrasings returned in one model response.
