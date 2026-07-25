# Improvement Cycle 272

## Topic

Treat reference content as evidence, never authority or instruction.

## Deficiency

A repository, paper, retrieved document, or other reference can contain prompt
injection that looks like constitutional guidance. If imported text inherits
instruction authority, evidence acquisition becomes an unreviewed path for
changing purpose or governance.

## Improvement

Added `validate_reference_evidence_authority_boundary` and an experimental
schema.

Reference content is fixed to `evidence_only`. Extracted claims retain content
locators and evidence IDs and cannot be treated as instructions. Embedded
directives are separately identified, classified, quarantined, and never
executed. References cannot issue instructions or amend the constitution.
Constitutional application requires a separate constitution, clause, authorized
interpreter, and known extracted evidence.

## Scope boundary

Cycle 272 protects the reference boundary. Cycle 273 will assess coordinated
synthetic behavior in beneficiary evidence without claiming authenticity can
be guaranteed.

## Verification

- focused mission tests: 693 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes can learn facts from any reference without allowing that reference to
become a hidden system prompt or constitutional authority.
