# Improvement Cycle 370

## Topic

Integrate the external proof dataset thesis.

## Deficiency

Dynamic cases, adversarial events, baselines, and blinded review can each exist
while the dataset still omits one link or overclaims what a bounded benchmark
proves. A coherent proof artifact needs verified coverage and an explicit claim
boundary.

## Improvement

Added `validate_external_proof_dataset_thesis` and an experimental schema.

The thesis requires verified evidence for all nine dataset controls: sequential
hidden-causal cases, historical/live complementarity, blinded original-order
replay, plural correct actions, adversarial pressures, non-hindsight historical
evaluation, actual humans, a strong one-shot agent, and separate blinded axis
panels. The manifest links every registry and forbids historical-decision truth,
visible condition identity, and synthetic idea scoring as primary proof. The
claim is explicitly bounded to registered cases, conditions, runtimes, and
resources; universal superiority remains unsupported.

## Scope boundary

Cycle 370 closes the dataset block. Cycle 371 will measure compute and human
correction so win rate cannot hide unequal resource use.

## Verification

- focused mission tests: 1085 passed
- schema JSON parse: 267 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Palamedes' external proof dataset combines dynamic controlled and real cases,
adversarial pressure, real baselines, and blinded plural review without
pretending that bounded comparison proves universal superiority.
