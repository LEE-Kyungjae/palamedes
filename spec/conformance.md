# Palamedes Conformance

This document describes the current compatibility checks for public Palamedes surfaces.

## Purpose

Palamedes conformance is intended to answer one question:

Can another implementation expose the same contract behavior expected by current adopters?

Conformance is narrower than implementation correctness.
It checks stable public behavior, not every internal helper or storage detail.

## Current Fixture Suite

The checked-in fixture manifest lives at:

- `tests/contracts/manifest.json`

The current fixture cases live in:

- `tests/contracts/plan-envelope.json`
- `tests/contracts/etag-fingerprint.json`
- `tests/contracts/stale-write-conflict.json`
- `tests/contracts/restore-roundtrip.json`
- `tests/contracts/idempotent-evidence-dedupe.json`

These fixtures are exercised by:

- `tests/test_contracts.py`
- `palamedes_conformance.py`
- `scripts/palamedes_conformance.py`
- `palamedes_reference_consumer.ts` for a non-Python HTTP consumer smoke path

## Runner Contract

The runner MUST be able to execute the current fixture suite against either:

- the in-process HTTP handler used by the repository tests
- an external HTTP base URL

The runner MUST emit a machine-readable JSON report with at least:

- `ok`
- `manifest_version`
- `case_count`
- `passed`
- `failed`
- `results`
- `failures`

The external CLI entrypoint is:

- `python3 scripts/palamedes_conformance.py`
- `python3 palamedes.py conformance`

To target an external HTTP server:

- `python3 scripts/palamedes_conformance.py --base-url http://127.0.0.1:8787`
- `python3 palamedes.py conformance --base-url http://127.0.0.1:8787`

## Current Covered Surfaces

The current suite verifies:

- `GET /plan` returns a stable plan envelope
- accepted writes return a fresh fingerprint and matching `ETag`
- stale writes fail with `412` and expose the current fingerprint
- restore preview plus restore round-trip to the intended revision content
- evidence idempotency keys replay without duplicate writes
- a thin TypeScript consumer can read, write, detect conflicts, and inspect the contracts catalog over HTTP

## Conformance Rules

An implementation should be considered compatible with the current Palamedes contract only if:

- all fixture-backed contract cases pass
- documented required fields remain present
- fingerprint and restore semantics remain behaviorally compatible
- public error envelopes remain machine-readable and compatible with existing automation

## Current Gap

The current conformance runner is still repository-local.
It is a strong regression baseline, but it is not yet packaged as an external certification harness for third-party implementations.

That means the current state is:

- suitable for internal contract regression
- partially suitable for reference implementations
- not yet sufficient as a standalone certification program
