# Improvement Cycle 146

## Topic

Prevent delegated agents from expanding mission scope.

## Deficiency

Cycle 145 governs Palamedes publication, but downstream agents pursuing a valid
mission may reinterpret the objective, add beneficiaries, spend more resources,
or publish externally. Parent authority does not automatically constrain every
implementation choice.

## Improvement

Added `validate_downstream_agent_scope` and an experimental schema.

Every downstream delegation binds an agent to a parent mission, authority,
sealed scope hash, assigned outcome, resource slice, and expiration. It lists
allowed decisions and forbidden actions. Changes to thesis, beneficiaries,
authority, resources, or publication must return to Palamedes. Redelegation and
scope expansion are forbidden.

## Scope boundary

Cycle 146 constrains downstream expansion. Cycle 147 must give Palamedes
authority to stop its own mission when pre-registered disconfirmation occurs.

## Verification

- focused mission tests: 189 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

No downstream agent may convert implementation discretion into a broader
mission or authority mandate.
