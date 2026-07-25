# Empirical Improvement Cycle 401

## Topic

Block low-confidence or task-irrelevant reference guidance before it reaches a
treatment agent.

## Deficiency

The first prospective Insight-RAG run indexed four real reference scopes and
returned five repository-backed candidates. All were low confidence. The
selected OpenClaw component lacked positive correlation-ID evidence, while the
generated implementation guidance included cache keys, duplicate-request
collapse, TTL, invalidation, cache misses, and stale values.

A confidence label alone did not remove the executable handoff. Passing that
packet to a coding agent would confound the paired experiment and could make an
irrelevant retrieved capability act as an instruction.

## Improvement

Added `validate_reference_treatment_packet_gate` and
`reference-treatment-packet-gate.schema.json`.

The gate separates packet validity from treatment eligibility. It requires:

- explicit task-required and allowed supporting capabilities;
- a selected candidate with positive evidence for every required capability;
- medium or high packet and candidate confidence;
- every guidance step to name its capability and source evidence;
- guidance evidence to belong to the selected candidate;
- every guidance capability to be task-allowed and positively evidenced;
- unrelated guidance to remain blocked.

An insufficient packet can be valid only when it honestly records
`handoff_authorized: false` and
`treatment_status: unavailable_insufficient_evidence`.

## Scope boundary

Cycle 401 does not repair Insight-RAG ranking or guidance generation and does
not run the paired coding trial. It prevents a known-invalid treatment from
contaminating that trial. The next probe must improve or narrow retrieval until
the packet passes this gate without forged evidence.

## Verification

- focused treatment-gate tests: 4 passed
- full mission suite: 1,209 passed
- actual case-001 packet: validly blocked with 9 explicit reasons
- experimental schema parse: 298 schemas parsed
- planning QA: 143/143
- `git diff --check`: passed

## Resulting invariant

No retrieved reference packet may become an executable experimental treatment
merely because it contains a candidate and a handoff prompt; task-relevant
positive evidence must authorize every guidance step.
