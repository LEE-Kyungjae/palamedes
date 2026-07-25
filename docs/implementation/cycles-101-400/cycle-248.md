# Improvement Cycle 248

## Topic

Preserve bounded high-upside minority mission exploration.

## Deficiency

A dominant tournament winner can consume a channel or resource that a
non-winning mission needs to remain testable. Rejecting every minority mission
therefore confuses current rank with option value, but protecting every
minority mission would evade selection entirely.

## Improvement

Added `validate_bounded_minority_mission_exploration` and an experimental
schema.

Protection qualifies only when the minority mission's evidenced expected
upside reaches an explicit high-upside threshold and dominant commitment would
destroy its option through a named, evidenced mechanism. The allocation must
fit inside the exploration portfolio, expire, prohibit permanent protection,
name its learning question and stop/graduation triggers, and remain subject to
an identified review authority.

## Scope boundary

Cycle 248 controls admission to protected exploration. The earlier Cycle 187
controls expiry and evidence-gated continuation after admission. Cycle 249 will
define the complete selection record.

## Verification

- focused mission tests: 597 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes may preserve a losing mission as a bounded option, but only when its
upside is high, dominant commitment would erase it, and the exception remains
budgeted, expiring, testable, and governed.
