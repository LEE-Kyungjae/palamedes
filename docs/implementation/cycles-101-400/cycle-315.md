# Improvement Cycle 315

## Topic

Freeze mission forecasts before rival inspection.

## Deficiency

Candidate generators that share context or see rivals can converge, imitate,
and revise forecasts after learning what will compare favorably. The tournament
then measures strategic adaptation rather than independent mission invention.

## Improvement

Added `validate_pre_rival_mission_forecast_freeze` and an experimental schema.

At least three unique generation contexts receive the same fingerprinted source
bundle and no rival IDs. Every independently valid Cycle 307 candidate commits
expected outcome, probability, horizon, resource, harm, disconfirmation,
fingerprint, and freeze time. All forecasts precede one rival-reveal time and
remain immutable afterward.

## Scope boundary

Cycle 315 protects independent proposal and forecasting. Cycle 316 will record
axis-specific critique as evidence without mutating the candidate.

## Verification

- focused mission tests: 865 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Mission comparison begins from independent, precommitted candidates and
forecasts rather than rivals that copied each other or moved their claims after
reveal.
