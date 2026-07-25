# Improvement Cycle 188

## Topic

Invalidate successful principles when their environment changes.

## Deficiency

Organizational memory could make a historically successful principle
authoritative even after the institutional, technical, or social assumptions
that supported it disappeared.

## Improvement

Added `validate_environmental_principle_review` and an experimental schema.

Every successful principle records its original environmental assumptions and
must undergo an active invalidation search. Current changes identify the
affected assumption, evidence, and impact. The strongest current impact
determines whether the principle is retained, scope-limited, or retired; past
success cannot override current conditions.

## Scope boundary

Cycle 188 makes principles environmentally defeasible. Cycle 189 will version
the company constitution itself and attach dissent and observed outcomes to its
amendments.

## Verification

- focused mission tests: 357 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Historical success grants a principle evidence, not permanent authority after
its enabling environment changes.
