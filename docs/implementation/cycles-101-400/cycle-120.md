# Improvement Cycle 120

## Topic

Center missions on human capability or condition change.

## Deficiency

Cycles 111–119 construct a generative and empirical desire model, but Palamedes
had no mission-level gate requiring that model to shape what it originates.
Demand, revenue, or an implementation mechanism could still become the mission
by default.

## Improvement

Added `validate_desire_centered_mission` and an experimental schema.

A mission now states the beneficiary's current and desired condition, the
capability change and mechanism, links its value constitution and desire model,
defines multiple beneficiary-change signals and safeguards, and includes a
disconfirming condition. Demand may be absent or used as evidence, but cannot
define the mission; revenue cannot define success.

## Scope boundary

Cycle 120 integrates the desire thesis. Cycle 121 begins opportunity discovery
by searching for mismatches between new capabilities and old institutions
rather than following established trends.

## Verification

- focused mission tests: 85 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes originates missions around defensible changes in human capability or
condition, with demand retained as evidence rather than the objective.
