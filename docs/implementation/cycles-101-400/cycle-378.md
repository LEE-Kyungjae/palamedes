# Improvement Cycle 378

## Topic

Treat creativity as diagnostic frame distance and opened action.

## Deficiency

Optimizing a creativity score rewards unusual language and lets novelty offset
harm, constitutional failure, or causal incoherence. Frame distance alone also
does not show that thought changed what can actually be asked or done.

## Improvement

Added `validate_creativity_diagnostic_report` and an experimental schema.

The report measures distance from the source frame across beneficiary, causal
model, option structure, and evaluation question. It also requires a concrete
action that was unreachable under the source frame, explains the new relation
that opened it, and attaches a probe. Creativity remains diagnostic:
constitutional validity, causal coherence, and harm boundaries are
non-compensable gates.

## Scope boundary

Cycle 378 defines creativity evidence. Cycle 379 will define the smallest
initial empirical claim Palamedes can make without worsening constitutional
violations or proxy harm.

## Verification

- focused mission tests: 1,117 passed
- schema JSON parse: 275 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Creativity is evidenced by useful frame movement that opens a testable action;
it is never a reward that can purchase permission to be harmful or incoherent.
