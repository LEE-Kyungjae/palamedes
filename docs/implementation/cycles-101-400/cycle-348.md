# Improvement Cycle 348

## Topic

Bound exploration without disrupting the dominant commitment.

## Deficiency

An exploration budget can become an open-ended second strategy that consumes
the resources or degrades the outcome of the mission already justified by
evidence.

## Improvement

Added `validate_non_disruptive_exploration_allocation` and an experimental
schema.

Exploration now has a positive maximum and allocated cost with owner and ledger,
start, expiry, expiration action, and no automatic renewal. Its evidence target
names the uncertainty, question, qualifying and disqualifying observations, and
completion criterion. The protected dominant mission is fingerprinted and has
one or more monitored non-disruption constraints naming protected resources or
metrics, maximum interference, measurement, and stop trigger. Exploration is
reversible and cannot preempt or obtain unbounded shared resources.

## Scope boundary

Cycle 348 protects committed delivery from exploration. Cycle 349 will require
selection to issue downstream authority and reversal triggers together with the
winner.

## Verification

- focused mission tests: 997 passed
- schema JSON parse: 245 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Palamedes can preserve a rival option only inside a finite evidence-seeking
allocation that cannot silently weaken the dominant mission.
