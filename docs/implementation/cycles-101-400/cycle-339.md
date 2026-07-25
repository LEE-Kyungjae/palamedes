# Improvement Cycle 339

## Topic

Treat summaries as interpretations in high-consequence selection.

## Deficiency

Summaries compress evidence by choosing what to group, emphasize, and omit.
Treating them as observations can hide the interpretation layer, especially
when a consequential mission choice rests on the compressed claim.

## Improvement

Added `validate_summary_interpretation_evidence_boundary` and an experimental
schema.

A summary records its sources, hashes, controlled locators, transform and
summarizer runtime, interpretive choices, omitted details, and uncertainties.
Its epistemic type is always `interpretation`, never raw-equivalent evidence.
Every decisive citation in a high-consequence selection must resolve to a
source evidence ID and fingerprint, include a logged original-access receipt,
and attest that the original was verified. A summary cannot be the sole
decisive evidence.

## Scope boundary

Cycle 339 protects the evidence/interpretation boundary. Cycle 340 will
integrate role-specific, hash-addressed context packets with opposition and
explicit absence.

## Verification

- focused mission tests: 961 passed
- schema JSON parse: 236 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Compression remains useful for cognition without acquiring the epistemic
authority of the observations it summarizes.
