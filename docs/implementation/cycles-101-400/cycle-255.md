# Improvement Cycle 255

## Topic

Give every non-goal a reason and reopening condition.

## Deficiency

Non-goals protect scarce attention, but an unexplained exclusion can turn a
temporary focus decision into dogma. It can suppress useful discoveries even
after the capacity or evidence condition that justified exclusion changes.

## Improvement

Added `validate_reopenable_non_goal_contract` and an experimental schema.

Every non-goal identifies its excluded scope, current reason, protected
attention resource, and evidence. It also precommits a reopening signal,
threshold, responsible authority, and action. Permanent and blanket exclusions
are forbidden. A reopened item must carry the evidence and time showing that
its threshold was actually met.

## Scope boundary

Cycle 255 governs reversible attention boundaries. Cycle 256 will add baseline
and time range requirements to success signals and earlier review for harms
that can precede benefit.

## Verification

- focused mission tests: 625 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

A Palamedes non-goal protects current attention without becoming an
unreviewable permanent prohibition on future discovery.
