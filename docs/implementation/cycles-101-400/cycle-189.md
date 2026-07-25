# Improvement Cycle 189

## Topic

Version the company constitution with dissent and outcomes.

## Deficiency

The company constitution could remain an invisible frozen founder preference
even while missions, evidence, and the environment evolved around it.

## Improvement

Added `validate_company_constitution_governance` and an experimental schema.

Amendments create sequential versions with explicit authority, separate
ratification, reason, activation, and outcome review. Founder preference is not
implicit authority. Dissent remains recorded with evidence and disposition,
while changed clauses link predicted and observed outcomes to future update
triggers.

## Scope boundary

Cycle 189 makes company values governable and corrigible. Cycle 190 will
integrate the company objective around durable beneficiary change and renewable
option capacity under constitutional constraints.

## Verification

- focused mission tests: 361 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Upstream cognition is governed by a versioned, contested, outcome-linked
constitution rather than an invisible frozen founder.
