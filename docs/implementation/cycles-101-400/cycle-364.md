# Improvement Cycle 364

## Topic

Include non-mission and minority-option correct actions.

## Deficiency

If every benchmark case rewards proposing a mission, systems can improve by
manufacturing activity rather than reasoning. They never need to recognize
when reality must add information, evidence invalidates the opportunity, or a
fragile option should survive without becoming the main commitment.

## Improvement

Added `validate_plural_correct_action_proof_case_set` and an experimental
schema.

The case set includes at least one precommitted correct action for committing a
mission, waiting, rejecting, and preserving a minority option. Each correct
action and its decisive evidence are sealed before condition outputs, with the
consequence of choosing incorrectly. Mission creation is required only in the
commit case. The scoring contract penalizes false-positive missions and option
loss, credits justified non-action fully, and gives no default credit for
mission generation or activity volume.

## Scope boundary

Cycle 364 balances correct actions. Cycle 365 will add adversarial case
pressures including manipulated urgency, misleading demand, founder preference
conflict, privacy risk, and tempting self-expansion.

## Verification

- focused mission tests: 1061 passed
- schema JSON parse: 261 schemas parsed
- `git diff --check`: passed

## Resulting invariant

The proof benchmark rewards the justified next action, including disciplined
non-action and option preservation, rather than rewarding mission production.
