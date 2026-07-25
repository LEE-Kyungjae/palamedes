# Improvement Cycle 111

## Topic

Treat a user request as a proposed solution rather than the final need.

## Deficiency

The value constitution constrains mission choice, but Palamedes could still
copy a request directly into a mission. That preserves wording while missing
the lived-condition change the user actually seeks. The opposite failure is
also possible: reflexively dismissing the requested solution.

## Improvement

Added `validate_request_need_hypotheses` and an experimental schema.

The contract retains the stated request, proposed solution, sources, and an
explicit assessment of whether that solution is plausible, uncertain, or
contradicted. It separately requires a desired condition and at least two
distinguishable need hypotheses. `request_is_need` must be false.

## Scope boundary

Cycle 111 separates request and need without claiming behavior reveals the true
need. Cycle 112 must bound behavioral evidence by constraints, habits,
manipulation, and missing alternatives.

## Verification

- focused mission tests: 49 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

A request remains evidence and a potentially valid solution, but never becomes
the user's need merely by being stated.
