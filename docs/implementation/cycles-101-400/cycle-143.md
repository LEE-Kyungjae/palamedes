# Improvement Cycle 143

## Topic

Classify novel actions through exposed analogical precedent.

## Deficiency

Cycle 142 defines consequence classes, but genuinely novel actions will not
match every predefined boundary or example. Silent guessing creates authority
expansion; automatic escalation exposes no useful reasoning.

## Improvement

Added `validate_analogical_authority_precedent` and an experimental schema.

Novel-action reasoning now names prior precedents, material similarities and
differences, an inferred class, analogy strength, confidence, and the analogy's
limit. Weak analogies have a confidence ceiling and cannot establish that an
action lies within authority.

## Scope boundary

Cycle 143 exposes uncertain analogical classification. Cycle 144 must let
Palamedes gather evidence through a safe sandbox rather than escalating every
weak analogy.

## Verification

- focused mission tests: 177 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes may generalize authority from precedent only through inspectable
analogy whose differences and weakness remain visible.
