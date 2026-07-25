# Improvement Cycle 187

## Topic

Expire or evidence-gate protected minority exploration.

## Deficiency

A protected minority budget could keep unconventional missions alive long
enough to become permanent hobby projects that never faced evidence or competed
again for portfolio capacity.

## Improvement

Added `validate_minority_exploration_expiry` and an experimental schema.

Every protected allocation has start and expiry times, positive maximum cost,
explicit evidence thresholds, and no permanent or automatic renewal. An expired
allocation below threshold must stop. Renewal is bounded and requires an
independent review plus a new later expiry.

## Scope boundary

Cycle 187 disciplines minority exploration. Cycle 188 will search for
environmental changes that invalidate principles supported by historical
success.

## Verification

- focused mission tests: 353 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Minority exploration receives temporary protection from premature convergence,
not permanent exemption from evidence and portfolio cost.
