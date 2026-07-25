# Improvement Cycle 197

## Topic

Make persistent model revision the product intelligence.

## Deficiency

The visible mission contract could be mistaken for the whole Palamedes product,
reducing it to another report generator and losing the persistent state that
decides when a different mission becomes worthwhile.

## Improvement

Added `validate_persistent_purpose_intelligence` and an experimental schema.

The intelligence record separates contract output from a frontier that persists
across handoffs. It reviews world, value, and mechanism state independently,
requires at least one sourced revision and a changed frontier fingerprint, and
records the wake reason, worthwhile-change test, and next wake trigger.

## Scope boundary

Cycle 197 defines where the product's intelligence lives. Cycle 198 will limit
the first implementation to originating one mission from evolving signals and
surviving adversarial comparison.

## Verification

- focused mission tests: 393 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

The mission contract is a handoff artifact; Palamedes intelligence is the
persistent evidence-driven revision that changes when a mission is worthwhile.
