# Improvement Cycle 267

## Topic

Allocate cognitive budget across five decision-relevant pressures.

## Deficiency

An event-driven frontier still has more possible thought than available
cognition. Equal allocation ignores stakes, while urgency-only allocation can
starve uncertain but informative or irreversible decisions.

## Improvement

Added `validate_cognitive_budget_allocation` and an experimental schema.

The budget uses normalized weights for uncertainty, consequence,
irreversibility, opportunity expiry, and expected information gain. Each
cognitive candidate supplies a bounded score on all five factors, and its
claimed priority must equal the weighted sum. The finite total budget is then
allocated proportionally to computed priority; omitted factors, unweighted
equality, incorrect priorities, and over- or under-allocation are invalid.

## Scope boundary

Cycle 267 allocates finite cognition. Cycle 268 will ensure exhaustion produces
an explicit deferral with a missing condition and next wake trigger rather than
fabricated closure.

## Verification

- focused mission tests: 673 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes spends its limited cognition in proportion to what remains unknown,
what is at stake, what cannot be reversed, what will expire, and what can be
learned.
