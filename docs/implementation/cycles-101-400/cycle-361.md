# Improvement Cycle 361

## Topic

Reject synthetic idea scoring as external proof.

## Deficiency

One-shot synthetic startup ideas are easy to rate for novelty or plausibility,
but they do not test whether Palamedes interprets weak signals, revises purpose,
preserves uncertainty, or selects a better next action as reality unfolds.

## Improvement

Added `validate_sequential_hidden_causal_proof_case` and an experimental schema.

A proof case now contains at least three ordered evidence reveals. After each
event, signal interpretation, current purpose state, uncertainty, and selected
next action are fingerprinted and frozen before the next reveal. The underlying
causal structure and ground truth are sealed before case start, unavailable to
participants, and revealed only after the final checkpoint. Evaluation targets
interpretation, purpose change, next action, and uncertainty rather than idea
appeal.

## Scope boundary

Cycle 361 defines dynamic case structure. Cycle 362 will address the sparse
counterfactuals and uncontrolled information of fully real cases.

## Verification

- focused mission tests: 1049 passed
- schema JSON parse: 258 schemas parsed
- `git diff --check`: passed

## Resulting invariant

External proof cases test accountable state change under sequential evidence
and hidden causal structure, not the presentational quality of synthetic ideas.
