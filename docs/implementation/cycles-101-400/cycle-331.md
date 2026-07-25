# Improvement Cycle 331

## Topic

Minimize repository context and prevent prior-conclusion leakage.

## Deficiency

Giving an inventor the entire repository and conversation history increases
token volume while diluting relevant evidence. Worse, old candidates and
selection conclusions can anchor an allegedly independent generation run.

## Improvement

Added `validate_bounded_context_leakage_guard` and an experimental schema.

Independent generation now uses a token-bounded context manifest containing
only observations, constitution clauses, causal evidence, and active
constraints with fingerprints, provenance, token counts, and inclusion reasons.
Full repository/history dumps, prior candidates and conclusions, persuasive
history, and raw reasoning are excluded. A fingerprint-bound leakage scan must
find no prior conclusion or forbidden category, and manifest token accounting
must be exact.

## Scope boundary

Cycle 331 prevents context flooding and answer leakage. Cycle 332 will define
the positive assembly anchors used to select the bounded context.

## Verification

- focused mission tests: 929 passed
- schema JSON parse: 228 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Independent mission generation receives enough governed evidence to reason,
but not the repository-scale noise or prior answers that would predetermine it.
