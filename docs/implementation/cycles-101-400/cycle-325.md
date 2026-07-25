# Improvement Cycle 325

## Topic

Blind adversaries to author identity and persuasive history.

## Deficiency

Criticism can inherit prestige, provider, personality, or discussion-order bias
when the adversary sees who authored a candidate or the rhetoric that produced
it. Removing all context would also prevent constitutional and causal review.

## Improvement

Added `validate_blinded_adversary_review_packet` and an experimental schema.

The adversary receives only the constitution and eight structured
decision-relevant candidate fields. Author, inventor, model, provider,
discussion history, raw reasoning, and popularity are withheld under a
fingerprint-linked redaction attestation. The resulting critique must address
constitutional tension, causal weakness, beneficiary harm, and a
disconfirming observation without guessing authorship or mutating the candidate.

## Scope boundary

Cycle 325 protects adversarial review from identity and persuasion cues. Cycle
326 will similarly restrict the selector to structured candidates and critiques
instead of raw chain-of-thought.

## Verification

- focused mission tests: 905 passed
- schema JSON parse: 222 schemas parsed
- `git diff --check`: passed

## Resulting invariant

A candidate is criticized for its governed substance and predicted
consequences, not for who or what model produced the argument.
