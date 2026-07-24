# Palamedes HTTP API

This document specifies the current local HTTP service exposed by `palamedes_server.py`.

## Transport Rules

- The service MUST speak JSON over HTTP.
- Request bodies for write operations MUST be JSON objects.
- Responses MUST use `Content-Type: application/json; charset=utf-8`.
- JSON request and response bodies MUST be UTF-8.

## Read Endpoints

### `GET /plan`

Returns the current plan envelope.

The response MUST include:

- `plan`
- `summary`
- `validation`
- `fingerprint`
- `contract_version`
- `implementation_version`

If a fingerprint is available, the response MUST also include `ETag: "<fingerprint>"`.

### `GET /qa`

Returns the current QA report.

### `GET /health`

Returns storage health and recovery diagnostics.

If the storage status is `error`, the HTTP status MUST be `503`.
Otherwise the HTTP status MUST be `200`.

### `GET /doctor`

Returns aggregated contract readiness diagnostics.

The response SHOULD include:

- storage health
- schema drift status
- tool schema contract status
- host action contract loadability
- conformance manifest status
- `checks`
- `check_summary`

Each check SHOULD expose:

- `id`
- `status` with one of `pass`, `warn`, or `fail`
- `summary`
- `hint`

If any check fails, the aggregated doctor status MUST be `error` and the HTTP status MUST be `503`.
Otherwise the HTTP status MUST be `200`.

### `GET /cycle?limit=<n>`

Returns a combined read snapshot.

The response MUST include:

- `ok`
- `result_type` with value `cycle`
- `plan`
- `summary`
- `validation`
- `fingerprint`
- `contract_version`
- `implementation_version`
- `qa`
- `health`
- `history`
- `history_limit`

`limit` MUST be a non-negative integer when provided.

### `GET /history`

Returns recent revision entries.

### `GET /reviews?status=<status>&scope=<scope>&assigned_to=<assignee>&sort_by=<field>&order=<dir>&limit=<n>`

Returns human-review escalation records from current plan state.

The response MUST include:

- `ok`
- `tool_name` with value `list_reviews`
- `result_type` with value `reviews`
- `reviews`
- `count`
- `filters`

`limit` MUST be an integer when provided.
`sort_by` MUST be one of `requested_at`, `priority`, `status`, or `stale_after` when provided.
`order` MUST be one of `asc` or `desc` when provided.

### `GET /reviews/inbox?assignee=<assignee>&limit=<n>`

Returns the reviewer inbox preset as an opinionated alias over review listing semantics.

The server MUST execute this endpoint as if it called `list_reviews` with:

- `status` set to `open`
- `sort_by` set to `priority`
- `order` set to `desc`

If `assignee` is provided, the server MUST map it to `assigned_to`.

The response MUST include:

- `ok`
- `tool_name` with value `list_reviews`
- `result_type` with value `reviews`
- `reviews`
- `count`
- `filters`

The returned `filters` object MUST reflect the enforced inbox preset.
`limit` MUST be an integer when provided.

### `GET /reviews/<request_id>`

Returns one human-review escalation record by identifier.

The response MUST include:

- `ok`
- `tool_name` with value `get_review`
- `result_type` with value `review`
- `review`

If the request identifier is unknown, the HTTP status MUST be `404`.

### `POST /reviews/<request_id>`

Updates triage fields on an existing human-review escalation record.

The request body MAY include:

- `priority`
- `assigned_to`
- `stale_after`
- `sla_bucket`
- `review_recommendation`
- `review_reason`
- `resolution`
- `idempotency_key`

The request body MUST NOT target a different `request_id` than the resource path.

The response MUST include:

- `ok`
- `tool_name` with value `update_review`
- `result_type` with value `mutation`
- `review_request`
- `plan`
- `summary`
- `validation`
- `fingerprint`
- `qa`

If a fingerprint is available, the response MUST also include `ETag: "<fingerprint>"`.

### `GET /validate`

Returns structural validation for the current plan.

### `GET /tools`

Returns the tool schema catalogue.

The response MUST include:

- `ok`
- `result_type` with value `tool_catalog`
- `contract_version`
- `implementation_version`
- `catalog`
- `tools`

The `catalog` object SHOULD include:

- `authoritative` with value `true`
- `transport`
- `list_endpoint`
- `detail_endpoint_template`
- `execute_endpoint`
- `legacy_execute_endpoint_template`
- `tool_count`
- `read_tool_count`
- `mutation_tool_count`

Each tool descriptor SHOULD include:

- `name`
- `description`
- `input_schema`
- `kind`
- `execute_via`

### `GET /tools/<tool_name>`

Returns the authoritative descriptor for one tool.

The response MUST include:

- `ok`
- `result_type` with value `tool_detail`
- `contract_version`
- `implementation_version`
- `tool`

### `GET /contracts`

Returns the current contract catalogue for this implementation.

The response SHOULD include:

- contract version
- implementation version
- spec entrypoint
- `summary`
- `stability_levels`
- host action contract metadata
- conformance manifest metadata
- tool catalogue count
- profile/capability summary for host action contracts

### `GET /host/action-contract?role=<role>`

Returns the role-specific host action contract derived from the shared host action contract artifact.

## Write Endpoints

### `POST /plan`

Updates the plan.

The request body MUST be a JSON object.
If `If-Match` is present, the server MUST treat it as the expected fingerprint.
On success, the server MUST return the updated tool result and SHOULD emit an `ETag` header for the new fingerprint.

### `POST /evidence`

Appends one evidence item.

The request MAY include `idempotency_key`.
If a matching idempotency record exists, the server MUST replay the stored result instead of appending a duplicate evidence entry.

### `POST /replan`

Applies a planning delta, may append evidence, and runs QA/autoreplan behavior.

The request MAY include `idempotency_key`.

### `POST /restore/preview`

Returns a restore preview without mutating plan state.

The request body MAY contain `revision_id` or `previous`.
This endpoint MUST NOT require `If-Match`.

### `POST /restore`

Restores the plan to a previously recorded revision.

The request body MAY contain `revision_id` or `previous`.
If `If-Match` is present, the server MUST use it as the expected fingerprint.

### `POST /agent/act`

Accepts `{"input": "<prompt>"}` and maps the prompt to a tool call.

The response MUST include:

- `tool`
- `input`
- `result`

### `POST /tools/<tool_name>`

Executes the named tool wrapper.

The request body MUST be a JSON object.
If the body contains `input`, that object MUST be used as the tool input.
Otherwise the entire request body MUST be treated as the tool input.

### `POST /tools/execute`

Executes a tool through the authoritative generic tool endpoint.

The request body MUST be a JSON object and MUST include:

- `tool`
- `input`

`input` MUST be a JSON object.
If `If-Match` is present and `input.expected_fingerprint` is absent, the server MUST inject the normalized fingerprint into `input.expected_fingerprint`.

The response MUST include:

- `tool`
- `input`
- `result`

`POST /tools/<tool_name>` remains supported as a legacy wrapper and MUST preserve its existing request semantics.

## Error Semantics

The service MUST use JSON error envelopes.

The current implementation emits these error cases:

- `400` for invalid JSON, empty bodies, non-object bodies, or validation failures
- `404` for unknown paths
- `412` for fingerprint conflicts
- `500` for unexpected internal errors

Each error envelope MUST include:

- `error`
- `type`
- `error_code`
- `retryable`

The service SHOULD include `operation` and `step` when the failing stage is known.
On fingerprint conflicts, the error payload MUST include `error: "plan fingerprint mismatch"`, MUST include `error_code: "plan_fingerprint_mismatch"`, MUST include `retryable: true`, and SHOULD include `current_fingerprint`.
