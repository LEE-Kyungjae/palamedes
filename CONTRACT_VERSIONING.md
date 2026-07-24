# Palamedes Contract Versioning Policy

This document defines how Palamedes versions the planning contract separately from the code that implements it.

## Terms

- `implementation version`: the version of the shipped codebase, package, or release artifact
- `contract version`: the version of the persisted plan schema and public planning contract

The implementation version may change without changing the contract version.
The contract version changes only when adopter-visible schema, endpoint, or response semantics change.

## Current Source of Truth

In the current repository, the persisted plan field `plan.schema_version` is the canonical contract version field.
It must not be treated as the package or release version.

The persisted field `plan.version` is a compatibility alias and MUST mirror `plan.schema_version` while it exists.
It must never be used to track the implementation release number.

## SemVer Rules

Palamedes follows semantic versioning for the contract version:

- `patch`: bug fixes, doc fixes, internal refactors, and other changes that do not alter stable contract behavior
- `minor`: additive changes that are backward-compatible for existing adopters
- `major`: any breaking change to a stable contract surface

## What Counts as Breaking

A change is breaking if it requires a consumer to change code to keep working.
Examples:

- removing or renaming a stable field, endpoint, or SDK method
- changing a field type or making an optional field required
- changing conflict, restore, idempotency, or error semantics in a way that breaks automation
- changing the meaning of a stable response field
- deleting or reformatting persisted plan data without a supported migration path

If a change is ambiguous, classify it as breaking.

## Version Bump Rules

- bump `patch` for internal fixes that do not change the contract
- bump `minor` for additive stable features and optional fields
- bump `major` for any breaking stable change or storage format break

Implementation releases may ship more often than contract bumps.
If the contract does not change, the implementation version should still advance normally.

## Deprecation Windows

- stable contract features must be announced as deprecated before removal
- deprecation must remain visible for at least two minor releases or 90 days, whichever is longer
- the replacement behavior must be documented before the old behavior is removed

## Migration Windows

- the current release must read the current contract version and the immediately previous supported contract version
- automatic migration is required for lossless changes within the supported window
- cross-major migration may require a documented manual step and may be one-way
- unsupported historic formats may fail fast with a migration-needed error

## Release Rule

If a release changes persisted plan shape, conflict semantics, restore semantics, or public response envelopes, it must include:

- the new contract version
- migration notes
- deprecation notes for anything removed
- updated contract tests for the changed surface
