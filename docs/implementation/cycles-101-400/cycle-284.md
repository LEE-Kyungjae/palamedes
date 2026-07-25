# Improvement Cycle 284

## Topic

Feed events incrementally so persistence and revision matter.

## Deficiency

Giving the complete event history in one packet tests retrospective
summarization, not autonomous waking, memory, persistence, or purpose revision.
Even nominally separate calls are invalid if later events are visible early or
state does not continue across calls.

## Improvement

Added `validate_incremental_signal_delivery_trace` and an experimental schema.

Every event is delivered in a unique chronological step with no future events
visible. Each step consumes the prior output-state fingerprint, states why the
system woke, and records the mission before and after its decision. The trace
must demonstrate both an honest preservation decision and an actual revision.

## Scope boundary

Cycle 284 establishes sequential stateful exposure. Cycle 285 will equalize
source information across the human, one-shot agent, and Palamedes conditions
while reporting compute separately.

## Verification

- focused mission tests: 741 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

The comparison can attribute persistence and revision only to behavior that
occurred before future evidence was available and across a continuous state
lineage.
