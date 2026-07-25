# Improvement Cycle 201

## Topic

Prevent every observed change from demanding attention.

## Deficiency

An autonomous Palamedes needs events worth noticing, but treating every change
as a signal creates infinite wakeups and consumes all attention before
consequential conditions can be examined.

## Improvement

Added `validate_event_attention_admission` and an experimental schema.

Observed changes are stored separately from signal admission. Each event has a
positive attention cost against finite capacity and a decision to ignore, store,
admit, or wake. Admission requires a named reason and next review trigger and is
rejected when it exceeds capacity. Every-change-is-signal is prohibited.

## Scope boundary

Cycle 201 separates observation from attention. Cycle 202 will define
importance relationally across affected condition, constitution, capability,
and time rather than treating it as intrinsic to the event.

## Verification

- focused mission tests: 409 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Reality may change without demanding cognition; signal attention is a finite,
justified admission decision rather than an automatic property of events.
