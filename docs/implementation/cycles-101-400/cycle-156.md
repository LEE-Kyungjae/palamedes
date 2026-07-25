# Improvement Cycle 156

## Topic

Prevent benchmark preference gaming.

## Deficiency

Cycle 155 proves upstream cognition on a comparison, but a persistent system can
learn the evaluators' preferred language and artifact shape. It may win visible
pairwise preference without improving unseen missions or beneficiary outcomes.

## Improvement

Added `validate_anti_gaming_evaluation` and an experimental schema.

Evaluation now freezes the system before independently custodied hidden future
cases are sampled, seals holdout identities, and tracks beneficiary outcomes
over an explicit window. Hidden-case quality and tracked outcomes are mandatory
primary criteria. Palamedes cannot access holdouts, and style or preference
scores cannot override outcomes.

## Scope boundary

Cycle 156 resists benchmark gaming. Cycle 157 must prevent Palamedes from
certifying its own evidence packets and outcome labels.

## Verification

- focused mission tests: 229 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes performance is earned on unseen future cases and real beneficiary
effects, not evaluator-recognizable style.
