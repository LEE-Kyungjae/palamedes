# Improvement Cycle 123

## Topic

Use workarounds and workflow violations to reframe problems.

## Deficiency

Cycle 122 grounds opportunities in real burden, but a list of friction often
leads only to incremental optimization. People who deliberately cross or evade
the intended workflow boundary may be revealing that the system framed the
problem at the wrong level.

## Improvement

Added `validate_workaround_reframe` and an experimental schema.

An anomaly now preserves the intended workflow, observed workaround, actor's
reason, incremental frame, alternative problem frame, and a distinguishing
observation. It must keep competing explanations and can neither dismiss the
anomaly as mere error nor assume the workaround is automatically correct.

## Scope boundary

Cycle 123 generates a reframe from an anomaly. Cycle 124 must distinguish a
general mechanism from a local quirk through repetition across contexts and
explicit boundary conditions.

## Verification

- focused mission tests: 97 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes treats workflow violations as evidence capable of changing the
problem frame while retaining alternative explanations and falsifiability.
