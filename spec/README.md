# Palamedes Contract Index

This directory contains the canonical adopter-facing contract entrypoints for Palamedes.

Read these files in this order:

1. `plan-state.md`
   The persisted planning state contract. This is the source of truth for the shape stored in `.palamedes/plan.json` and the revision log.
2. `conflict-and-restore.md`
   The concurrency, fingerprint, conflict, preview, and restore semantics.
3. `http-api.md`
   The local HTTP transport contract and public endpoint behavior.
4. `host-action-contract.json`
   The current host-side orchestration contract for role-aware action execution.
5. `conformance.md`
   The current contract fixtures and what an implementation must prove to be considered compatible.

Related policy documents:

- `../STABILITY.md`
- `../CONTRACT_VERSIONING.md`

Interpretation rules:

- Files in `spec/` describe public contracts unless they explicitly say otherwise.
- If a behavior is only described in code or examples and not documented in `spec/` or the policy docs, treat it as provisional.
- Canonical reference surfaces live in `palamedes_reference_adapter.py` and `palamedes_reference_host.py`.
- The canonical non-Python reference consumer lives in `palamedes_reference_consumer.ts`.
- Compatibility shims remain in `examples/` for walkthroughs and sample imports, but they are not the normative contract.

Current stable contract surfaces:

- persisted plan state
- fingerprint conflict semantics
- restore preview and restore behavior
- documented HTTP endpoints
- fixture-backed conformance cases in `tests/contracts/`

Current experimental contract surfaces:

- host action orchestration contract
- example host/runtime adapters
- any endpoint or field not documented in `spec/` or policy docs
