# Improvement Cycle 162

## Topic

Separate mission selection, planning, execution, environment, and measurement
failures.

## Deficiency

A missing beneficiary outcome could still be interpreted as direct
falsification of the mission, even when the plan, implementation, environment,
or measurement process had broken.

## Improvement

Added `validate_failure_layer_diagnosis` and an experimental schema.

Every failure diagnosis now evaluates mission selection, planning, execution,
environment, and measurement exactly once. Each layer records its expected and
observed condition, evidence, and a discriminator. A single-layer conclusion
must agree with the assessments and cannot ignore another failed layer. Mission
thesis falsification is permitted only when mission selection failed and every
downstream layer was adequate.

## Scope boundary

Cycle 162 separates the possible failure locations. Cycle 163 will prevent
strategic blame shifting by pre-structuring attribution and representing shared
causal responsibility.

## Verification

- focused mission tests: 253 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Failure of an observed outcome does not falsify purpose until mission selection
has been distinguished from planning, execution, environment, and measurement.
