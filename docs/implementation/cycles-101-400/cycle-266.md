# Improvement Cycle 266

## Topic

Warn on semantically repeated thought without suppressing legitimate revisits.

## Deficiency

Action idempotency leaves repeated reasoning untouched, but treating semantic
similarity as a hard duplicate key can suppress necessary reconsideration when
evidence, context, or the validity period has changed.

## Improvement

Added `validate_semantic_repetition_review` and an experimental schema.

Similarity and its threshold compute a repetition warning, never automatic
suppression. A warned thought without a revisit ground must be revised or
merged. A revisit remains allowed with the warning when it names new evidence,
changed context, or an expired conclusion and provides both evidence and the
material difference from prior thought. Below threshold, new thought proceeds.

## Scope boundary

Cycle 266 governs duplicate-thought review. Cycle 267 will allocate a bounded
cognitive budget using uncertainty, consequence, irreversibility, opportunity
expiry, and expected information gain.

## Verification

- focused mission tests: 669 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes notices when it may be thinking the same thought again without
turning similarity into censorship of evidence-based reconsideration.
