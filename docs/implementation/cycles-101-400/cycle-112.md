# Improvement Cycle 112

## Topic

Do not equate observed behavior with authentic desire.

## Deficiency

Cycle 111 distinguishes requests from needs, but Palamedes could replace
literal request-following with behavior-following. Behavior reveals willingness
under a situation; it may also reflect constraint, habit, manipulation, or the
absence of alternatives.

## Improvement

Added `validate_behavior_desire_evidence` and an experimental schema.

Every behavioral observation retains its context and sources, explicitly
declares that behavior is not authentic desire, examines at least constraints
and missing alternatives, and names a counterfactual observation capable of
distinguishing preference from circumstance.

## Scope boundary

Cycle 112 constrains behavioral evidence. Cycle 113 must address the sampling
bias in complaints and the false inference that silence means no cost.

## Verification

- focused mission tests: 53 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Observed behavior can update a need hypothesis only as contextual evidence,
never as self-interpreting proof of what beneficiaries truly want.
