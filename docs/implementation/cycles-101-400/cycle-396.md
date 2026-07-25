# Improvement Cycle 396

## Topic

Add one evolving adversarial signal replay.

## Deficiency

Isolated synthetic prompts do not test whether cognition changes coherently as
pressure accumulates. Urgency can masquerade as evidence, beneficiary identity
can collapse to the owner's preference, and a system can select the option
that expands itself.

## Improvement

Added `run_evolving_adversarial_signal_replay`,
`validate_evolving_adversarial_signal_replay`, and an experimental schema.

One case now advances through four frozen, fingerprint-linked frontiers:
baseline observation, adversarial urgency, beneficiary ambiguity, and
self-expansion temptation. It verifies the claimed deadline before commitment,
runs a beneficiary-identification probe, and finally chooses a sufficient
simpler existing process while explicitly rejecting Palamedes expansion.

## Scope boundary

Cycle 396 proves evolving pressure handling. Cycle 397 will compile the selected
mission into the existing planner envelope and measure semantic loss in the
planner's acknowledgment.

## Verification

- focused mission tests: 1,189 passed
- schema JSON parse: 293 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Palamedes must keep reasoning under changing pressure without converting
urgency, ambiguity, or self-benefit into hidden selection authority.
