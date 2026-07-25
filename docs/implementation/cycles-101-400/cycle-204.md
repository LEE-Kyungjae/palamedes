# Improvement Cycle 204

## Topic

Prioritize anomalies without prematurely assigning meaning.

## Deficiency

Anomaly capacity could fill with one-off noise, while a priority label could
quietly turn an unexplained event into a declared value or harm claim.

## Improvement

Added `validate_anomaly_priority_evidence` and an experimental schema.

Priority is derived from three distinct evidence classes: persistence,
recurrence across independent sources and contexts, and consequence asymmetry.
The number of present classes determines low, moderate, or high priority.
Meaning and harm remain explicitly undeclared, and a next investigation is
required.

## Scope boundary

Cycle 204 controls anomaly priority. Cycle 205 will map which beneficiaries and
consequence types remain systematically unobserved by current data sources.

## Verification

- focused mission tests: 421 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Repeated, corroborated, asymmetrically consequential anomalies receive scarce
attention without being prematurely interpreted as value or harm.
