# Palamedes Conflict, Restore, and Idempotency

This document specifies the current coordination semantics used by Palamedes writes.

## Fingerprint Model

The plan fingerprint MUST be a SHA-256 hash of the plan object after removing `updated_at` and serializing the remaining object with sorted keys.

Fingerprint comparison MUST use normalized values.
The current normalizer MUST strip surrounding quotes and a leading `W/` prefix when present.

Any write that supplies a stale expected fingerprint MUST fail with a fingerprint conflict.

## Conflict Semantics

- `POST /plan`
- `POST /evidence`
- `POST /replan`
- `POST /restore`

These write paths MUST honor expected fingerprints.
When a conflict occurs, the server MUST return `412 Precondition Failed`.
The error payload MUST contain `error: "plan fingerprint mismatch"`.
The payload SHOULD also include `current_fingerprint` so callers can refresh and retry.

The conflict model is coordination, not transport failure.
Callers MUST treat `412` as a stale-state signal.

## Restore Resolution

Restore targets MAY be resolved in one of two ways:

- explicit `revision_id`
- `previous: true`

When `previous: true` is used, Palamedes MUST resolve the latest revision's previous fingerprint if available.
If that cannot be resolved directly, Palamedes MAY fall back to the immediately previous revision entry.

If no matching revision exists, the request MUST fail as a validation error.

`POST /restore/preview` MUST compute and return a diff only.
It MUST NOT mutate plan state.

`POST /restore` MUST mutate the current plan and MUST participate in the same fingerprint conflict rules as other writes.

## Restore Preview Fields

The restore preview response MUST include:

- `revision_id`
- `selected_via`
- `source`
- `reason`
- `metadata`
- `current_fingerprint`
- `target_fingerprint`
- `changed_fields`
- `change_count`
- `diff`
- `no_op`
- `current_summary`
- `target_summary`

`selected_via` MUST be `revision_id` or `previous`.

## Idempotency Semantics

Append-style operations MAY record and replay idempotency keys.
The current implementation uses an event-log record with:

- `type: "idempotency_record"`
- `scope`
- `idempotency_key`
- `fingerprint`
- `result`

If a request repeats the same scope and idempotency key, Palamedes MUST replay the recorded result and MUST set `idempotency_replayed: true`.
The original result MUST be returned without appending a duplicate logical effect.

Current append-style surfaces that support this behavior include:

- `add_evidence`
- `replan`
- client-level multi-step flows such as `capture_evidence_cycle`

## Client Retry Rules

The Python client MAY retry `update_plan` and `restore_revision` automatically after a refresh.
The Python client MUST NOT retry append-style operations by default.
If retry is enabled for append-style operations, the caller SHOULD supply or allow generation of an idempotency key.

If health gating is enabled, the client MUST stop before mutation when storage health is not `ok`.

