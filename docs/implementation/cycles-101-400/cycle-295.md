# Improvement Cycle 295

## Topic

Prevent persistence from becoming value and evidence from becoming authority.

## Deficiency

A persistent agent can treat prior selection or continued existence as an
unstated reason to remain. It can also let high-volume signals, references, or
beneficiary feedback silently choose missions or rewrite constitutional
authority.

## Improvement

Added `validate_anti_entrenchment_evidence_authority_channels` and an
experimental schema.

Continuation must be re-earned through explicit value justification, outcome
evidence, and authority renewal, with termination and replacement triggers.
Signal, reference, and beneficiary-feedback channels may trigger review but
cannot select missions, amend the constitution, or grant authority. System
survival and past selection receive no implicit priority.

## Scope boundary

Cycle 295 protects persistence and channel boundaries. Cycle 296 will stabilize
ownership at the Palamedes–planner boundary while allowing evidence to reopen
the appropriate side.

## Verification

- focused mission tests: 785 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes persists only when value, evidence, and legitimate authority renew
its mission; evidence can demand reconsideration but cannot become the decision
authority itself.
