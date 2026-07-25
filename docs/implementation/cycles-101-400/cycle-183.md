# Improvement Cycle 183

## Topic

Require resource renewal or an explicit subsidy mandate.

## Deficiency

Rejecting revenue as the sole selector could let Palamedes choose admirable but
unsupported missions whose resource demands were hidden until failure.

## Improvement

Added `validate_mission_resource_renewal` and an experimental schema.

Every mission states its resource envelope, runway, renewal review, and stop
condition. Earned-revenue missions require a payer, payer benefit, renewal
mechanism, pricing evidence, and causal thesis. Subsidized missions require an
authorized, scoped, limited, expiring mandate with external renewal authority.
Good intentions alone never establish sustainability.

## Scope boundary

Cycle 183 makes resource support explicit. Cycle 184 will distinguish growth
caused by durable voluntary benefit from switching friction, compulsion, or
acquired distribution.

## Verification

- focused mission tests: 337 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

No mission enters the portfolio without a testable path to renewed resources or
a bounded, authorized subsidy mandate.
