# Improvement Cycle 388

## Topic

Policy-gate and redact sensitive prompt context.

## Deficiency

Context assembly can leak sensitive material into a provider prompt before any
policy check. A later redaction log cannot undo that disclosure, and a simple
“filtered” flag does not show which rule authorized, transformed, or denied
each item.

## Improvement

Added `build_policy_gated_prompt_context`,
`validate_sensitive_prompt_context_policy_gate`, and an experimental schema.

Every context item is classified and receives exactly one pre-assembly policy
decision with a rule and rationale. Confidential input must use a separately
fingerprinted sanitized artifact; restricted input is denied. Prompt context
contains artifact references only, denied items are absent, and the complete
allow/redact/deny audit remains attached to the operation.

## Scope boundary

Cycle 388 controls model disclosure. Cycle 389 will make kill switches stop
external actions while preserving state needed for reconstruction.

## Verification

- focused mission tests: 1,157 passed
- schema JSON parse: 285 schemas parsed
- `git diff --check`: passed

## Resulting invariant

No context enters a model operation before an auditable policy decision, and
sensitive originals never masquerade as redacted prompt material.
