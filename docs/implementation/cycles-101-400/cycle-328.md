# Improvement Cycle 328

## Topic

Fail closed without rule-based purpose scoring.

## Deficiency

When a model call fails, falling back to deterministic purpose scores appears
robust but silently transfers semantic authority to code. Retrying forever is
also unsafe and unbounded.

## Improvement

Added `validate_semantic_judgment_failure_recovery` and an experimental schema.

A failed semantic call may use only a bounded, ordered sequence of retry,
provider switch, or context narrowing. Recovery requires a valid structured
judgment linked to its attempt. If no valid judgment emerges, Palamedes creates
an explicit unavailable-judgment state with the pending operation, wake trigger,
and review time. The prior state remains unchanged. Rule scoring and any other
deterministic semantic substitute are forbidden.

## Scope boundary

Cycle 328 governs failures without faking judgment. Cycle 329 will disclose
shared-model dependence when one model fills several cognitive roles.

## Verification

- focused mission tests: 917 passed
- schema JSON parse: 225 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Lack of model judgment remains visible as lack of judgment; it cannot be hidden
behind a mechanically produced purpose decision.
