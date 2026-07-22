# DeepPlan Plan State

This document specifies the canonical plan state stored by the current DeepPlan repository.

## Scope

DeepPlan MUST keep its authoritative planning state in a single repo-local JSON object at `.deeplan/plan.json`.
DeepPlan MUST treat the plan as the source of truth for planning direction, evidence, hypotheses, references, and revisionable decision context.

## Storage Layout

The repo-local state directory MUST be `.deeplan/`.

The current implementation uses these files:

- `.deeplan/plan.json`
- `.deeplan/decisions.jsonl`
- `.deeplan/risks.jsonl`
- `.deeplan/events.jsonl`
- `.deeplan/revisions.jsonl`

Hosts MAY keep a derived reference retrieval index at `.deeplan/references.sqlite3`.
That index is non-authoritative: it MUST NOT replace `plan.json`, evidence, reference-discovery records, or revision history as the source of planning truth. It MAY be rebuilt from collected reference-pattern inputs, and its integrity/schema health SHOULD be checked independently before retrieval.

`plan.json` MUST contain the current mutable plan.
The `.jsonl` files MUST be treated as append-only logs.

## Required Plan Fields

`plan.json` MUST be a JSON object with all of the following top-level keys:

- `schema_version`
- `version`
- `updated_at`
- `goal`
- `success_metric`
- `deadline`
- `planning_horizon`
- `review_cadence`
- `phase_plan`
- `constraints`
- `assumptions`
- `options`
- `selected_option`
- `plan_tasks`
- `execution_tasks`
- `dependencies`
- `experiments`
- `risks`
- `references`
- `insights`
- `direction_insights`
- `market_insights`
- `timing_insights`
- `differentiation_insights`
- `monetization_insights`
- `constraint_insights`
- `risk_signal_insights`
- `evolution_insights`
- `definition_of_done`
- `evidence`
- `hypothesis_log`
- `reference_discoveries`

## Field Types

The current implementation requires these types:

- `schema_version`, `version`, `updated_at`, `goal`, `success_metric`, `deadline`, `planning_horizon`, `review_cadence`, and `selected_option` MUST be strings.
- `phase_plan`, `constraints`, `assumptions`, `options`, `plan_tasks`, `execution_tasks`, `dependencies`, `experiments`, `references`, `insights`, `direction_insights`, `market_insights`, `timing_insights`, `differentiation_insights`, `monetization_insights`, `constraint_insights`, `risk_signal_insights`, `evolution_insights`, `definition_of_done`, `evidence`, `hypothesis_log`, and `reference_discoveries` MUST be arrays.
- `risks` MUST be an array of strings or objects.

For nested records:

- A string `risk` entry MUST be non-empty.
- A risk object MUST include `risk`, `signal`, and `mitigation` as non-empty strings.
- An evidence string entry MUST be non-empty.
- An evidence object MUST include `claim`, `source`, and `date` as non-empty strings, and `confidence` as an integer from 0 to 100.
- A hypothesis object MUST include `ts`, `hypothesis`, and `status` as non-empty strings.
- A reference-discovery object MUST include `ts`, `question`, and `search_mode` as non-empty strings.

## Structured Extension Conventions

The current runtime schema intentionally leaves `additionalProperties` enabled at the top level and on nested evidence, risk, hypothesis, and reference-discovery objects.
Consumers MUST preserve unknown fields when possible and MUST NOT reject a plan only because it carries recognized extension records that are outside the minimal canonical core.

This permissive envelope is the compatibility mechanism for richer provenance and escalation state until those fields are promoted into the stricter runtime validator.

### Structured Evidence Extensions

Evidence objects SHOULD continue using the canonical required fields:

- `claim`
- `source`
- `confidence`
- `date`

When richer provenance is available, evidence objects SHOULD prefer these conventional optional fields:

- `axis`: planning axis or insight family tied to the claim.
- `evidence_type`: evidence class such as `user_quote`, `metric_snapshot`, `experiment_result`, or `reference_extraction`.
- `reference`: short linked reference label when a full reference record is not available.
- `reference_id`: stable identifier for the linked reference or discovery record.
- `source_url`: canonical URL for the underlying source when one URL is sufficient.
- `quote`: short supporting excerpt or observation text.
- `field`: metric name, attribute, or inspected field being asserted.
- `observed_value`: measured or observed scalar value.
- `expected_value`: baseline, target, or comparison scalar value.
- `selector`: field name, metric key, DOM selector, notebook cell, or other extraction locator.
- `artifact`: URI, file path, issue key, doc URL, or capture identifier for the underlying source artifact.
- `note`: short operator note that gives review context without replacing the canonical claim.
- `provenance`: object carrying capture metadata such as `method`, `captured_at`, `collected_by`, `artifact`, and `locator`.
- `review_recommendation`: short recommendation for the human reviewer.
- `review_reason`: short explanation for why automated handling should stop or defer.
- `escalation`: object carrying richer reviewer handoff metadata when the claim needs human adjudication.

These extension fields are conventions, not new required core schema fields.
Writers SHOULD prefer stable machine-readable identifiers over free-form prose when both are available.

### Structured Reference Discovery Extensions

Reference discovery records MUST still include the canonical required arrays and strings.
When a discovery pass produces more than a shortlist, writers SHOULD prefer these conventional optional fields:

- `decision_ref`: stable identifier for the downstream decision, review, or revision that consumed the discovery.
- `decision_status`: short lifecycle value such as `proposed`, `adopted`, `rejected`, or `needs_review`.
- `source_urls`: canonical URLs or file paths consulted during the discovery pass.
- `selected_reference_records`: array of structured per-reference summaries, typically including `reference`, `why_selected`, `pattern`, and `evidence_links`.
- `follow_up_question`: next unresolved question created by the discovery pass.
- `provenance`: object carrying search metadata such as `provider`, `query_hash`, `run_id`, `captured_at`, and `collector`.
- `review_recommendation`: short recommendation for the human reviewer.
- `review_reason`: short explanation for why automated handling should stop or defer.
- `escalation`: object carrying richer reviewer handoff metadata when shortlist selection or interpretation requires human review.

Reference-discovery extensions SHOULD link back to `references`, `evidence`, hypotheses, or decision logs via stable identifiers when available.

### Human Escalation Contract

The plan MAY carry human-review state at the top level through conventional extension fields such as `human_escalations` or `human_review`.
These records are not part of the minimal canonical required-key set, but they are valid plan state because top-level additional properties are allowed.

When present, human escalation records SHOULD include:

- `id`: stable escalation identifier.
- `status`: lifecycle value such as `open`, `acknowledged`, `resolved`, or `dismissed`.
- `reason`: concise explanation of why automated planning stopped or deferred.
- `scope`: the affected planning surface, for example `plan`, `evidence`, `reference_discovery`, or `decision`.
- `requested_at`
- `requested_by`
- `resolution`
- `resolved_at`
- `related_evidence`
- `related_references`

Nested `escalation` objects on evidence or reference-discovery records SHOULD use the same lifecycle vocabulary where practical.

## Mutation Rules

- `updated_at` MUST change on each persisted save.
- Consumers MUST NOT use `updated_at` as a stable identity token.
- The plan fingerprint MUST ignore `updated_at`.
- The canonical task split is `plan_tasks` plus `execution_tasks`; legacy `tasks` input may be migrated, but `tasks` is not part of the canonical state shape.
- `schema_version` MUST be present and MUST be a string. Current new plans use `0.5.0`.
- `version` MUST be present as a compatibility alias and MUST equal `schema_version`.
- Writers SHOULD preserve recognized structured extension fields on evidence, reference-discovery, and human-escalation records during read-modify-write cycles even when the current runtime ignores them.

## Revision Logs

- `revisions.jsonl` MUST store immutable plan snapshots.
- Each revision entry MUST include a revision identifier, timestamp, source, fingerprint, previous fingerprint, and plan snapshot.
- `events.jsonl` MAY store operational events such as idempotency records and auto-replan metadata.
- `decisions.jsonl` and `risks.jsonl` are append-only logs for decision and risk records.

## Retention

Event and revision logs are subject to bounded retention.
Pruning MUST preserve the newest entries first and MUST be best effort.
Retention settings are implementation-controlled and MAY vary by environment.
