# Palamedes Contract Stability Policy

This document defines what adopters can depend on and what may change without notice.

## Stability Levels

Palamedes has two stability levels:

- `stable`: documented public contract surface
- `experimental`: anything not explicitly listed as stable

Stable means the surface follows the versioning and deprecation rules in `CONTRACT_VERSIONING.md`.
Experimental means the surface can change, move, or disappear in a minor release without a deprecation window.

## Stable Surfaces

The following are stable when documented in the README or spec files:

- the persisted plan shape in `plan.json`
- the meaning of `plan.schema_version` as the canonical persisted contract version
- the `fingerprint` conflict token and `412` conflict behavior
- the core HTTP endpoints documented in the README and integration guides
- the public SDK methods exported by `palamedes_sdk`
- the primary CLI commands described in the README
- the meanings of `ok`, `tool_name`, `result_type`, and `current_fingerprint` in public responses
- the additive response fields `contract_version` and `implementation_version` when present in public envelopes

Stable fields and endpoints may gain new optional fields, but existing required fields, names, and semantics must remain compatible within a major version.

## Experimental Surfaces

The following are experimental unless explicitly promoted to stable:

- internal helper functions and module-private APIs
- undocumented CLI flags and response fields
- example integrations and scaffolding in `examples/`
- generated prompts, templates, and host-side adapter sketches
- new endpoints, fields, or tool wrappers not yet covered by the README or a spec file

Experimental surfaces are allowed to evolve quickly. Adopters should not build production dependencies on them.

## Change Rules

- additive changes to stable surfaces are allowed when they do not break existing adopters
- removal, rename, type change, or semantic redefinition of a stable field or endpoint is a breaking change
- any change that forces a consumer to rewrite its parsing, retry, restore, or conflict logic is breaking
- a new feature starts experimental and only becomes stable after it is documented and covered by contract tests

## Deprecation Policy

- stable surfaces must not be removed without prior deprecation notice
- deprecation notice must appear in the docs and release notes
- deprecated stable behavior remains available for at least two minor releases or 90 days, whichever is longer
- when a stable surface is deprecated, the replacement surface must be documented at the same time

## Migration Support

- the current release must be able to read the immediately previous supported contract version
- automatic migration is required when the old format can be converted losslessly and deterministically
- if automatic migration is not safe, Palamedes must fail with a clear migration-needed error and document the manual steps
- stored plan data should never be silently rewritten into a breaking shape

## Adopter Rule

If a surface is not named here as stable, treat it as provisional.
If a change looks like it could alter persisted data or client behavior, assume it is breaking until proven otherwise.
