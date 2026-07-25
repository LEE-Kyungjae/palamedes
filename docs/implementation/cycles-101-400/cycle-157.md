# Improvement Cycle 157

## Topic

Separate evidence preparation from independent certification.

## Deficiency

Cycle 156 protects holdouts, but a self-evaluating Palamedes could still choose
which outputs are compared, preserve identifying clues, or assign favorable
outcome labels.

## Improvement

Added `validate_independent_evaluation_custody` and an experimental schema.

Palamedes may prepare evidence, but independent identities control packet
randomization and outcome labels. Packet and label manifests are sealed under a
documented custody chain and blinding protocol. Palamedes cannot modify packets
after sealing or assign outcome labels.

## Scope boundary

Cycle 157 defines independent certification. Cycle 158 must mark claims
unverified when independent processes are unavailable rather than treating
internal coherence as validation.

## Verification

- focused mission tests: 233 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes cannot certify the benchmark evidence or labels used to establish its
own performance.
