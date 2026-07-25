# Improvement Cycle 163

## Topic

Pre-structure failure attribution and allow shared causal responsibility.

## Deficiency

Separating failure layers after an outcome still allowed Palamedes to protect its
upstream judgment by inventing a favorable diagnostic structure and blaming
downstream execution.

## Improvement

Added `validate_prestructured_failure_attribution` and an experimental schema.

Attribution questions must be frozen before the outcome is observed. Mission
selection cannot be exempt and execution cannot be the presumed cause. Every
layer records evidence for and against contribution. Responsibility can be
sole, shared, or underdetermined; shared mode requires multiple causal layers
without forcing false numerical precision.

## Scope boundary

Cycle 163 governs the structure and plurality of causal responsibility. Cycle
164 will constrain retrospective stories using alternative forecasts recorded
before mission selection.

## Verification

- focused mission tests: 257 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes cannot defend upstream judgment by blaming execution after the fact;
the attribution questions precede outcomes and may assign shared responsibility.
