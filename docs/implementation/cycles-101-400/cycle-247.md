# Improvement Cycle 247

## Topic

Choose the least harmful, fastest unanswered separating probe.

## Deficiency

Admitting a probe as a tournament winner does not make every probe equally
useful. A probe may duplicate existing evidence, fail to distinguish the
leading missions, impose avoidable harm, or delay the observation despite an
equally safe faster alternative.

## Improvement

Added `validate_competing_probe_selection` and an experimental schema.

The contract requires at least two probe candidates and an explicit review of
existing evidence. Only probes that cannot already be answered and that
separate every leading mission enter the ranking. Eligible probes are ranked
lexicographically by harm first and time to observation second. A unique best
probe must be selected; an exact harm-and-time tie remains unresolved rather
than being broken by an arbitrary identifier.

## Scope boundary

Cycle 247 governs competition among evidence-producing probes. Cycle 248 will
govern bounded exploration of a high-upside minority mission whose option
would be destroyed by dominant commitment.

## Verification

- focused mission tests: 593 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes does not run a probe merely because it can produce data; it chooses
the safest quickest new observation that can actually change mission
selection.
