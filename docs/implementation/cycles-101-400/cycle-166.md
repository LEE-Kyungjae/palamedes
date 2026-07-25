# Improvement Cycle 166

## Topic

Set review cadence by consequence type.

## Deficiency

A single review schedule could wait for lagging beneficiary benefit while early
harm accumulated, or inspect long-horizon sustainability so frequently that
noise drove premature revision.

## Improvement

Added `validate_consequence_review_cadence` and an experimental schema.

Benefit, harm, sustainability, and option preservation each receive a distinct
latency expectation, first review, recurring interval, wake trigger, evidence
source, and rationale. At least two schedules must differ, and harm must never
be reviewed later or less frequently than benefit.

## Scope boundary

Cycle 166 determines when different consequences are reviewed. Cycle 167 will
retire a successful mission when the underlying beneficiary condition has
disappeared.

## Verification

- focused mission tests: 269 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Review timing follows consequence latency and risk; early harm cannot be hidden
behind the slower observation window of intended benefit.
