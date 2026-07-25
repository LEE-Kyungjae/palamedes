# Improvement Cycle 287

## Topic

Evaluate consequence and causal coherence before novelty.

## Deficiency

A surprising mission can appear creative while imposing unacceptable
consequences or relying on a mechanism unrelated to the observed situation.
Blending novelty into one score lets spectacle compensate for unusability.

## Improvement

Added `validate_coherence_before_novelty_evaluation` and an experimental schema.

Evaluation now runs as strict eligibility gates: consequence first, causal
coherence second, and novelty only for candidates passing both. Ineligible
candidates receive no novelty score or rationale, and novelty can never override
their exclusion. The selected mission must come from the eligible set.

## Scope boundary

Cycle 287 protects selection from unusable surprise. Cycle 288 will measure the
human upstream labor required to obtain each viable mission.

## Verification

- focused mission tests: 753 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes treats novelty as a differentiator among consequentially acceptable,
causally coherent purposes—not as compensation for failure on either dimension.
