# Improvement Cycle 117

## Topic

Represent possibility-enabled latent desires.

## Deficiency

Cycle 116 prevents manufactured engagement from masquerading as benefit, but
Palamedes still risked limiting discovery to preferences people can already
state. Some valuable changes become conceivable only after a new capability or
way of living appears.

## Improvement

Added `validate_latent_desire_possibility` and an experimental schema.

A latent-desire possibility names the beneficiary, possible condition change,
enabling capability, reason it is not currently expressible, a non-demand value
basis, sources, and a disconfirming condition. Current demand is recorded but
cannot define value.

## Scope boundary

Cycle 117 permits generative possibilities. Cycle 118 must identify whose
imagined future each possibility encodes and design an inexpensive exposure
that can elicit informed preference.

## Verification

- focused mission tests: 73 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes can originate missions beyond current demand while keeping their
value basis and falsifiability explicit.
