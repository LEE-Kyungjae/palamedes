# Improvement Cycle 273

## Topic

Assess beneficiary authenticity without claiming it can be guaranteed.

## Deficiency

Coordinated synthetic behavior can poison a beneficiary model while appearing
numerous, persistent, and urgent. A binary authenticity gate either accepts a
sophisticated attack as genuine or excludes legitimate people who cannot meet
a rigid identity standard.

## Improvement

Added `validate_beneficiary_authenticity_assessment` and an experimental
schema.

The assessment requires identity continuity, costly behavior, recurrence over
time, and independent context, each with evidence strength and an explicit
limitation. Their mean strength is discounted by evidenced coordinated
synthetic behavior risk to produce only provisional confidence. That confidence
controls weighting or further probing. Authenticity can never be marked
guaranteed, and residual uncertainty plus a monitoring trigger always remain.

## Scope boundary

Cycle 273 protects beneficiary inference from coordinated behavior without
pretending detection is perfect. Cycle 274 will protect outcome learning from
selective downstream reporting.

## Verification

- focused mission tests: 697 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes can cautiously weight beneficiary behavior using several independent
signals while preserving the possibility that even strong-looking behavior was
coordinated or synthetic.
