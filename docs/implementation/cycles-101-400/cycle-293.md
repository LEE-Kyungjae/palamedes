# Improvement Cycle 293

## Topic

Separate creativity, judgment, and memory responsibilities.

## Deficiency

When invention, selection, and continuity are blended, a candidate generator
can silently choose its favorite, a selector can invent after seeing scores, or
memory can harden precedent into authority. The contribution of each capability
then becomes impossible to evaluate.

## Improvement

Added `validate_creativity_judgment_memory_separation` and an experimental
schema.

Creativity has sole responsibility for independent mission invention, judgment
for constitutional selection, and memory for causal and normative continuity.
Each role has explicit prohibited actions and produces an artifact consumed by
the integrated decision. The selected mission must come from creativity's
candidate set, while memory supplies distinct continuity records.

## Scope boundary

Cycle 293 separates three cognitive responsibilities. Cycle 294 will distinguish
autonomous mission initiation from corrigible revision.

## Verification

- focused mission tests: 777 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes can attribute novelty to invention, legitimacy to judgment, and
coherence through time to memory without allowing any role to usurp another.
