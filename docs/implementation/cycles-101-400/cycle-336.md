# Improvement Cycle 336

## Topic

Minimize sensitive signal exposure with controlled provenance.

## Deficiency

Omitting sensitive evidence can hide beneficiary harm, while copying raw
records into model context expands exposure and retention. Provenance is still
needed for authorized audit and correction.

## Improvement

Added `validate_sensitive_signal_minimized_context` and an experimental schema.

Sensitive context uses only a bounded summary, redacted text, or local embedding.
The raw original remains behind an access policy with locator, fingerprint,
custodian, and provenance ID but is not embedded or dereferenceable by the
model. Representations exclude raw and reidentifying fields. Role access is
purpose-limited, logged, expiring, deletion-triggered, and non-redistributable.
Local embeddings cannot leave the local boundary.

## Scope boundary

Cycle 336 minimizes sensitive exposure while keeping audit lineage. Cycle 337
will attach identifier-and-hash context manifests to every generated artifact
so evidence change can be separated from model change.

## Verification

- focused mission tests: 949 passed
- schema JSON parse: 233 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Palamedes can reason about sensitive consequences without exporting their raw
source material or losing the controlled path back to the original.
