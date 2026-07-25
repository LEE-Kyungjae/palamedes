# Improvement Cycle 150

## Topic

Gate authority on bounded delegation, safe probes, and genuine power gaps.

## Deficiency

Cycles 141–149 provide authority components, but a caller could still escalate
ordinary in-scope work or act directly through an unresolved analogy.

## Improvement

Added `validate_authority_thesis_gate` and an experimental schema.

The gate has three outcomes. `act` requires verified bounded delegation,
consequence classification, action lineage, and no ambiguity. `sandbox_probe`
requires resolvable ambiguity and a named safe probe. `escalate` requires
genuinely ungranted power, no safe probe, and a stated reason.

## Scope boundary

Cycle 150 completes the authority thesis. Cycle 151 begins persistence
governance by addressing missions that increase Palamedes' own resources or
relevance.

## Verification

- focused mission tests: 205 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes acts autonomously within consequence-bounded authority, investigates
safe ambiguity itself, and asks humans only for power that was never granted.
