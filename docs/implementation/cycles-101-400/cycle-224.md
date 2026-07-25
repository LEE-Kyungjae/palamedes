# Improvement Cycle 224

## Topic

Lower authority and prefer probes under correlational evidence.

## Deficiency

Correlation can reveal a valuable mission area while leaving the causal
mechanism unresolved. Allowing it to authorize commitment lets a plausible
story choose an intervention before competing explanations can lose.

## Improvement

Added `validate_correlational_mission_authority` and an experimental schema.

Correlational evidence can produce only a hypothesis-level mission suggestion.
It cannot authorize commitment. At least two competing mechanisms must remain,
and the selected action must be an intervention probe whose manipulation and
outcome distinguish every declared mechanism within a stated window.

## Scope boundary

Cycle 224 governs correlation. Cycle 225 will treat historical analogies as
mechanism candidates while preserving differences in timing, institutions,
scale, and beneficiary power.

## Verification

- focused mission tests: 501 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes can use correlation to find where to investigate, but only
mechanism-discriminating intervention can raise causal mission authority.
