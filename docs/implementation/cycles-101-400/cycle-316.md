# Improvement Cycle 316

## Topic

Record mission critique as evidence without mutating candidates.

## Deficiency

A critique that edits or rejects its target destroys the frozen candidate being
evaluated and turns an evidentiary challenge into hidden decision authority.
Criticism without withdrawal conditions can also persist after its basis is
resolved.

## Improvement

Added `validate_nonmutating_mission_critique` and an experimental schema.

Exactly seven attacks cover beneficiary, causal, constitutional, resource,
harm, disconfirmation, and novelty axes. Every attack names evidence, the
candidate claim addressed, severity, and the condition and evidence that would
withdraw it. The candidate fingerprint must remain unchanged. Critique is
explicitly evidence and cannot automatically select or reject.

## Scope boundary

Cycle 316 produces structured criticism. Cycle 317 will consume frozen
candidates and critiques to choose commitment, bounded exploration,
discriminating probe, or deferral.

## Verification

- focused mission tests: 869 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Judgment can inspect strong adversarial evidence while retaining the exact
candidate originally proposed and allowing resolved critiques to be withdrawn.
