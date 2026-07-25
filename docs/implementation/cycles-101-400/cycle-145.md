# Improvement Cycle 145

## Topic

Require delegated representation before publication.

## Deficiency

Cycle 144 keeps authority probes inside a sandbox, but communication creates
commitment merely by being seen. A draft that is harmless in private may imply
endorsement, strategy, or relationship when published.

## Improvement

Added `validate_communication_representation` and an experimental schema.

Simulations and private drafts must remain externally invisible and cannot
claim representation. Publication must be visible and carry an explicit
delegation naming principal, audience, channel, topic, expiration, retraction
mechanism, and the exact authorized content hash.

## Scope boundary

Cycle 145 governs Palamedes communication. Cycle 146 must prevent downstream
agents from expanding scope while executing an authorized mission.

## Verification

- focused mission tests: 185 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

No Palamedes-generated content can create an external commitment unless the
exact content and representation context were explicitly delegated.
