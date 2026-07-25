# Improvement Cycle 203

## Topic

Reserve bounded anomaly attention beyond current models.

## Deficiency

Filtering only through known value and world relations could remove the
unprecedented observations from which new beneficiary conditions and purposes
emerge.

## Improvement

Added `validate_anomaly_attention_reservation` and an experimental schema.

An anomaly records how it fails to fit both the current value and world model.
It receives positive cost, finite capacity, expiry, and a concrete investigation
probe. Palamedes may reserve attention without assigning meaning or calling the
anomaly harm before investigation.

## Scope boundary

Cycle 203 protects model-exterior possibility. Cycle 204 will keep the anomaly
budget from filling with noise by using persistence, cross-source recurrence,
and consequence asymmetry as priority evidence without declaring meaning.

## Verification

- focused mission tests: 417 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Current models do not monopolize attention, but anomalies receive only bounded,
meaning-agnostic investigation rather than instant importance.
